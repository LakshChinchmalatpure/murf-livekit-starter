import os
import pytest
import sqlite3
import json
import db

# Use a test database path for isolated testing
TEST_DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_database.db")

@pytest.fixture(autouse=True)
def setup_test_db(monkeypatch):
    # Patch DB_PATH in db module to use test database path
    monkeypatch.setattr(db, "DB_PATH", TEST_DB_PATH)
    # Ensure a fresh db is initialized
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)
    db.init_db()
    yield
    # Cleanup after test
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)

def test_init_db():
    assert os.path.exists(TEST_DB_PATH)
    conn = sqlite3.connect(TEST_DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='callers'")
    table_exists = cursor.fetchone()
    conn.close()
    assert table_exists is not None

def test_save_and_get_caller():
    user_id = "test_user_123"
    name = "Ramesh"
    lang = "Hindi"
    facts = {
        "schemes_checked": ["PM Kisan"],
        "eligible": "yes",
        "age": 45
    }
    
    # Save the caller record
    saved_record = db.save_caller(user_id, name, lang, facts)
    assert saved_record["user_id"] == user_id
    assert saved_record["name"] == name
    assert saved_record["language_preference"] == lang
    assert saved_record["facts"] == facts
    assert "last_interaction" in saved_record

    # Retrieve by user_id
    retrieved_by_id = db.get_caller(user_id=user_id)
    assert retrieved_by_id is not None
    assert retrieved_by_id["name"] == name
    assert retrieved_by_id["language_preference"] == lang
    assert retrieved_by_id["facts"] == facts

    # Retrieve by name (case-insensitive)
    retrieved_by_name = db.get_caller(name="ramesh")
    assert retrieved_by_name is not None
    assert retrieved_by_name["user_id"] == user_id
    assert retrieved_by_name["facts"] == facts

def test_upsert_caller():
    user_id = "test_user_123"
    db.save_caller(user_id, "Ramesh", "Hindi", {"age": 45})
    
    # Update same user_id with new data
    updated_record = db.save_caller(user_id, "Ramesh Kumar", "English", {"age": 46, "scheme": "PM Kisan"})
    assert updated_record["name"] == "Ramesh Kumar"
    assert updated_record["language_preference"] == "English"
    assert updated_record["facts"] == {"age": 46, "scheme": "PM Kisan"}
    
    retrieved = db.get_caller(user_id=user_id)
    assert retrieved["name"] == "Ramesh Kumar"
    assert retrieved["language_preference"] == "English"
    assert retrieved["facts"] == {"age": 46, "scheme": "PM Kisan"}

def test_validation_strips_sensitive_data():
    user_id = "test_user_456"
    name = "Suresh"
    lang = "English"
    
    # Facts with sensitive bank accounts, cards, PAN cards, Aadhaar
    facts = {
        "scheme": "PM Kisan",
        "bank_account": "123456789012",      # 12 digits (sensitive!)
        "pan_number": "ABCDE1234F",         # PAN card pattern (sensitive!)
        "credit_card": "1234-5678-9012-3456",# Credit card (sensitive!)
        "safe_number": "45"                 # Safe short number
    }
    
    saved_record = db.save_caller(user_id, name, lang, facts)
    saved_facts = saved_record["facts"]
    
    # Check that sensitive fields were stripped/ignored
    assert "scheme" in saved_facts
    assert "safe_number" in saved_facts
    assert "bank_account" not in saved_facts
    assert "pan_number" not in saved_facts
    assert "credit_card" not in saved_facts
    assert saved_facts["scheme"] == "PM Kisan"
    assert saved_facts["safe_number"] == "45"
