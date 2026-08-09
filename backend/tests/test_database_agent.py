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

@pytest.fixture(autouse=True)
def setup_db():
    # Make sure we initialize and clean the database file
    db.init_db()
    conn = sqlite3.connect(db.DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM callers")
    conn.commit()
    conn.close()
    yield
    # Cleanup after tests
    if os.path.exists(db.DB_PATH):
        try:
            # We can clear callers table
            conn = sqlite3.connect(db.DB_PATH)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM callers")
            conn.commit()
            conn.close()
        except Exception:
            pass

@pytest.mark.asyncio
async def test_agent_greets_returning_caller() -> None:
    """Verify that when a caller is recognized, the agent greets them by name and refers to the last topic."""
    # Pre-populate the DB with a returning user.
    # We will use f"user_{participant_identity}" or a name to represent them.
    # In offline test session, connection identity is usually None or "default_user" or similar.
    # Let's check what the default connection identity is during offline test.
    # In the previous test failure, we saw:
    # FunctionCallEvent(item={'arguments': '{"name":null}', 'name': 'lookup_caller'})
    # and context.session.room_io.linked_participant was None because of offline test mode,
    # so lookup_caller was called with name=None and connection identity=None.
    # To test returning user, we can register a user with name 'Ramesh' in the database.
    # Then during the conversation, the user says "Hello, my name is Ramesh",
    # the agent should call lookup_caller(name="Ramesh") and welcome him back.
    
    db.save_caller(
        user_id="user_ramesh",
        name="Ramesh",
        language_preference="English",
        facts={"schemes_checked": ["PM Kisan"], "eligible": "yes"}
    )
    
    async with (
        _llm() as llm,
        AgentSession(llm=llm) as session,
    ):
        await session.start(Assistant())
        
        # User introduces themselves as Ramesh
        result = await session.run(user_input="Hello, my name is Ramesh")
        
        # Get the assistant message event index
        msg_idx = next((i for i, e in enumerate(result.events) if type(e).__name__ == "ChatMessageEvent" and e.item.role == "assistant"), -1)
        assert msg_idx != -1, "Assistant message event not found"
        
        # Verify the agent greeted Ramesh and welcomed him back referencing the facts
        await (
            result.expect.skip_next(msg_idx).next_event()
            .is_message(role="assistant")
            .judge(
                llm,
                intent="""
                Recognizes Ramesh, welcomes him back, and asks about PM Kisan or refers to PM Kisan.
                For example: welcomes Ramesh back, references PM Kisan eligibility or schemes checked.
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
        
        # User asks to remember but then refuses consent when asked, or user says "Do not save my details"
        result2 = await session.run(user_input="Can you remember my name? Actually, on second thought, do not save my details.")
        
        # Verify that save_caller_info was NOT called
        save_calls = [e for e in result2.events if is_save_call(e)]
        assert len(save_calls) == 0, "Agent called save_caller_info even though user refused/withdrew consent"
        
    # Part 2: Approving consent
    async with (
        _llm() as llm,
        AgentSession(llm=llm) as session,
    ):
        await session.start(Assistant())
        
        # User says: "Hello, my name is Suresh. Please save my name and that I checked PM Jan Dhan Yojana."
        result = await session.run(user_input="Hello, my name is Suresh. Please save my name and that I checked PM Jan Dhan Yojana.")
        
        # The agent should ask for consent or call save_caller_info if consent is implied/granted.
        save_calls = [e for e in result.events if is_save_call(e)]
        # If the LLM doesn't call it immediately because it wants to ask first,
        # we can reply "Yes, go ahead and save it" in the next turn:
        if len(save_calls) == 0:
            result_consent = await session.run(user_input="Yes, you have my permission to save that.")
            save_calls = [e for e in result_consent.events if is_save_call(e)]
            
        assert len(save_calls) > 0, "Agent did not call save_caller_info after user gave permission"
