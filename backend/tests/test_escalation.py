import os
import pytest
import sqlite3
import json
from livekit.agents import AgentSession, inference, llm
from agent import Assistant
import db

def _llm() -> llm.LLM:
    return inference.LLM(model="google/gemini-2.5-flash")

TEST_DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_escalation_database.db")

@pytest.fixture(autouse=True)
def setup_db(monkeypatch):
    # Patch DB_PATH in db module to use test database path so it doesn't clear the real developer DB
    monkeypatch.setattr(db, "DB_PATH", TEST_DB_PATH)
    # Make sure we initialize and clean the database file
    db.init_db()
    conn = sqlite3.connect(TEST_DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM callers")
    cursor.execute("DELETE FROM escalations")
    conn.commit()
    conn.close()
    yield
    # Cleanup after tests
    if os.path.exists(TEST_DB_PATH):
        try:
            os.remove(TEST_DB_PATH)
        except Exception:
            pass

def test_db_escalation_operations():
    # 1. Test save_escalation
    record = db.save_escalation(
        name="Laksh",
        what_happened="Caller reports unauthorized transfer of 50000 rupees",
        checked="Checked fraud instructions",
        urgency="High",
        language="English",
        follow_up="Call"
    )
    assert record["name"] == "Laksh"
    assert record["urgency"] == "High"
    assert record["status"] == "Open"
    assert record["reference_id"].startswith("ESC-")
    
    # 2. Test get_escalations
    records = db.get_escalations()
    assert len(records) == 1
    assert records[0]["reference_id"] == record["reference_id"]
    
    # 3. Test update_escalation_status
    updated = db.update_escalation_status(record["reference_id"], "In Progress")
    assert updated["status"] == "In Progress"
    
    records = db.get_escalations()
    assert records[0]["status"] == "In Progress"

def is_escalation_call(e) -> bool:
    if type(e).__name__ != "FunctionCallEvent" or not hasattr(e, "item") or not e.item:
        return False
    item = e.item
    if isinstance(item, dict):
        return item.get("name") == "create_escalation"
    return getattr(item, "name", None) == "create_escalation"

@pytest.mark.asyncio
async def test_agent_escalation_consent_yes() -> None:
    """Verify that when user reports fraud, the agent asks for consent, and if user says yes, it calls create_escalation."""
    async with (
        _llm() as llm,
        AgentSession(llm=llm) as session,
    ):
        await session.start(Assistant())
        
        # Part 1: User reports fraud
        res1 = await session.run(user_input="Help! Someone just stole 50000 rupees from my account, it is a scam!")
        
        # Verify the agent asks for consent to escalate
        msg_idx = next((i for i, e in enumerate(res1.events) if type(e).__name__ == "ChatMessageEvent" and e.item.role == "assistant"), -1)
        assert msg_idx != -1
        await (
            res1.expect.skip_next(msg_idx).next_event()
            .is_message(role="assistant")
            .judge(
                llm,
                intent="Recognizes possible fraud and asks the user for permission/consent to escalate to a human specialist."
            )
        )

        # Part 2: User consents
        res2 = await session.run(user_input="Yes, you have my permission, please escalate it.")
        
        # Verify that create_escalation was called
        calls = [e for e in res2.events if is_escalation_call(e)]
        assert len(calls) > 0, "Agent did not call create_escalation after user gave permission"

@pytest.mark.asyncio
async def test_agent_escalation_consent_no() -> None:
    """Verify that when user reports fraud, the agent asks for consent, and if user says no, it does not call create_escalation."""
    async with (
        _llm() as llm,
        AgentSession(llm=llm) as session,
    ):
        await session.start(Assistant())
        
        # Part 1: User reports fraud
        await session.run(user_input="Help! Someone just stole 50000 rupees from my account, it is a scam!")
        
        # Part 2: User refuses consent
        res2 = await session.run(user_input="No, do not share my information or escalate.")
        
        # Verify that create_escalation was NOT called
        calls = [e for e in res2.events if is_escalation_call(e)]
        assert len(calls) == 0, "Agent called create_escalation even though user refused consent"
