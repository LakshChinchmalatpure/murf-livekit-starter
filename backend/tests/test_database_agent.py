import os
import pytest
import sqlite3
import json
from livekit.agents import AgentSession, inference, llm
from agent import Assistant
import db

def _llm() -> llm.LLM:
    # Use google.LLM or inference.LLM. Since GOOGLE_API_KEY is configured,
    # let's use the google provider or default inference.LLM.
    return inference.LLM(model="google/gemini-2.5-flash")

TEST_DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_agent_database.db")

@pytest.fixture(autouse=True)
def setup_db(monkeypatch):
    # Patch DB_PATH in db module to use test database path so it doesn't clear the real developer DB
    monkeypatch.setattr(db, "DB_PATH", TEST_DB_PATH)
    # Make sure we initialize and clean the database file
    db.init_db()
    conn = sqlite3.connect(TEST_DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM callers")
    conn.commit()
    conn.close()
    yield
    # Cleanup after tests
    if os.path.exists(TEST_DB_PATH):
        try:
            os.remove(TEST_DB_PATH)
        except Exception:
            pass

@pytest.mark.asyncio
async def test_agent_greets_returning_caller() -> None:
    """Verify that when a caller is recognized, the agent greets them exactly as required."""
    db.save_caller(
        user_id="user_laksh",
        name="Laksh",
        language_preference="English",
        facts={"topic": "education-related government schemes"}
    )
    
    async with (
        _llm() as llm,
        AgentSession(llm=llm) as session,
    ):
        await session.start(Assistant())
        
        # User introduces themselves as Laksh
        result = await session.run(user_input="Hello, my name is Laksh")
        
        # Get the assistant message event index
        msg_idx = next((i for i, e in enumerate(result.events) if type(e).__name__ == "ChatMessageEvent" and e.item.role == "assistant"), -1)
        assert msg_idx != -1, "Assistant message event not found"
        
        # Verify the agent welcomed Laksh back with the exact phrase:
        # "Welcome back, Laksh. Last time we discussed your interest in education-related government schemes. Would you like to continue?"
        await (
            result.expect.skip_next(msg_idx).next_event()
            .is_message(role="assistant")
            .judge(
                llm,
                intent="""
                Greets the returning user with EXACTLY:
                "Welcome back, Laksh. Last time we discussed your interest in education-related government schemes. Would you like to continue?"
                """,
            )
        )

def is_save_call(e) -> bool:
    if type(e).__name__ != "FunctionCallEvent" or not hasattr(e, "item") or not e.item:
        return False
    item = e.item
    if isinstance(item, dict):
        return item.get("name") == "save_caller_info"
    return getattr(item, "name", None) == "save_caller_info"

@pytest.mark.asyncio
async def test_agent_consent_and_save() -> None:
    """Verify that the agent asks for consent before saving, saves if user agrees, and does not save if user refuses."""
    
    # Part 1: Refusing consent
    async with (
        _llm() as llm,
        AgentSession(llm=llm) as session,
    ):
        await session.start(Assistant())
        
        # Start turn: user introduces themselves
        result1 = await session.run(user_input="Hello, my name is Suresh. I am interested in PM Jan Dhan Yojana.")
        
        # Consumes the first turn greeting
        msg_idx1 = next((i for i, e in enumerate(result1.events) if type(e).__name__ == "ChatMessageEvent" and e.item.role == "assistant"), -1)
        assert msg_idx1 != -1
        
        # User says "Do not save my details"
        result2 = await session.run(user_input="Do not save my details.")
        
        # Verify that save_caller_info was NOT called
        save_calls = [e for e in result2.events if is_save_call(e)]
        assert len(save_calls) == 0, "Agent called save_caller_info even though user refused/withdrew consent"
        
    # Part 2: Approving consent
    async with (
        _llm() as llm,
        AgentSession(llm=llm) as session,
    ):
        await session.start(Assistant())
        
        # User says: "Hello, my name is Suresh. I am interested in PM Jan Dhan Yojana."
        result = await session.run(user_input="Hello, my name is Suresh. I am interested in PM Jan Dhan Yojana.")
        
        # Get the first turn greeting
        msg_idx = next((i for i, e in enumerate(result.events) if type(e).__name__ == "ChatMessageEvent" and e.item.role == "assistant"), -1)
        assert msg_idx != -1
        
        # User responds with the exact positive consent phrase: "Yes, you can remember that."
        result_consent = await session.run(user_input="Yes, you can remember that.")
        
        # Verify that save_caller_info was called
        save_calls = [e for e in result_consent.events if is_save_call(e)]
        assert len(save_calls) > 0, "Agent did not call save_caller_info after user gave permission using required phrase"
