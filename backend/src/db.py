import os
import sqlite3
import json
import logging
import re
from datetime import datetime

logger = logging.getLogger("db")

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "database.db")

# Match account/Aadhaar/card numbers: 8 to 20 digits (possibly separated by spaces/hyphens)
DIGIT_PATTERN = re.compile(r'\b(?:\d[\s-]*){8,20}\b')

# Match PAN card numbers: 5 letters, 4 digits, 1 letter
PAN_PATTERN = re.compile(r'\b[a-zA-Z]{5}\d{4}[a-zA-Z]\b')

def init_db():
    """Initializes the database and creates the callers and escalations tables if they do not exist."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS callers (
            user_id TEXT PRIMARY KEY,
            name TEXT,
            language_preference TEXT,
            facts TEXT,
            last_interaction TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS escalations (
            reference_id TEXT PRIMARY KEY,
            name TEXT,
            what_happened TEXT,
            checked TEXT,
            urgency TEXT,
            language TEXT,
            follow_up TEXT,
            status TEXT,
            created_at TEXT
        )
    """)
    conn.commit()
    conn.close()
    logger.info(f"Database initialized at: {DB_PATH}")

def save_escalation(name: str, what_happened: str, checked: str, urgency: str, language: str, follow_up: str):
    """
    Saves a new human escalation ticket to the database and returns the record.
    """
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    import random
    # Generate unique reference ID
    for _ in range(10):
        ref_id = f"ESC-{random.randint(1000, 9999)}"
        cursor.execute("SELECT 1 FROM escalations WHERE reference_id = ?", (ref_id,))
        if not cursor.fetchone():
            break
    else:
        ref_id = f"ESC-{random.randint(10000, 99999)}"

    from datetime import timezone
    created_at = datetime.now(timezone.utc).isoformat()
    status = "Open"

    cursor.execute("""
        INSERT INTO escalations (reference_id, name, what_happened, checked, urgency, language, follow_up, status, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (ref_id, name, what_happened, checked, urgency, language, follow_up, status, created_at))
    
    conn.commit()
    conn.close()
    
    logger.info(f"Created escalation ticket for user={name}, reference_id={ref_id}")
    return {
        "reference_id": ref_id,
        "name": name,
        "what_happened": what_happened,
        "checked": checked,
        "urgency": urgency,
        "language": language,
        "follow_up": follow_up,
        "status": status,
        "created_at": created_at
    }

def get_escalations():
    """
    Retrieves all escalations sorted by creation time.
    """
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT reference_id, name, what_happened, checked, urgency, language, follow_up, status, created_at 
        FROM escalations 
        ORDER BY datetime(created_at) DESC
    """)
    rows = cursor.fetchall()
    conn.close()
    
    return [
        {
            "reference_id": row[0],
            "name": row[1],
            "what_happened": row[2],
            "checked": row[3],
            "urgency": row[4],
            "language": row[5],
            "follow_up": row[6],
            "status": row[7],
            "created_at": row[8]
        }
        for row in rows
    ]

def update_escalation_status(reference_id: str, status: str):
    """
    Updates the status of a specific escalation.
    """
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE escalations SET status = ? WHERE reference_id = ?", (status, reference_id))
    conn.commit()
    conn.close()
    logger.info(f"Updated escalation status for reference_id={reference_id} to status={status}")
    return {"reference_id": reference_id, "status": status}


def validate_facts(facts: dict) -> dict:
    """
    Cleans facts by removing potential sensitive account numbers, cards, or ID numbers.
    Returns a cleaned dictionary.
    """
    cleaned_facts = {}
    for key, val in facts.items():
        val_str = str(val)
        
        # Check for sequences of 8-20 digits (e.g. account numbers, Aadhaar, credit cards)
        if DIGIT_PATTERN.search(val_str):
            logger.warning(f"Validation warning: Removed fact key '{key}' containing potential account or ID number.")
            continue
            
        # Check for PAN card numbers
        if PAN_PATTERN.search(val_str):
            logger.warning(f"Validation warning: Removed fact key '{key}' matching PAN card pattern.")
            continue
            
        cleaned_facts[key] = val
        
    return cleaned_facts

def get_caller(user_id: str = None, name: str = None):
    """
    Retrieves a caller by user_id or name (case-insensitive).
    """
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    row = None
    if user_id:
        cursor.execute(
            "SELECT user_id, name, language_preference, facts, last_interaction FROM callers WHERE user_id = ?",
            (user_id,)
        )
        row = cursor.fetchone()
        
    if not row and name:
        cursor.execute(
            "SELECT user_id, name, language_preference, facts, last_interaction FROM callers WHERE LOWER(name) = LOWER(?)",
            (name,)
        )
        row = cursor.fetchone()
        
    conn.close()
    
    if row:
        return {
            "user_id": row[0],
            "name": row[1],
            "language_preference": row[2],
            "facts": json.loads(row[3]) if row[3] else {},
            "last_interaction": row[4]
        }
    return None

def save_caller(user_id: str, name: str, language_preference: str, facts: dict):
    """
    Saves or updates caller data. Facts are sanitized to prevent storage of sensitive ID/account numbers.
    """
    cleaned_facts = validate_facts(facts)
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    from datetime import timezone
    last_interaction = datetime.now(timezone.utc).isoformat()
    facts_json = json.dumps(cleaned_facts)
    
    cursor.execute("""
        INSERT INTO callers (user_id, name, language_preference, facts, last_interaction)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET
            name=excluded.name,
            language_preference=excluded.language_preference,
            facts=excluded.facts,
            last_interaction=excluded.last_interaction
    """, (user_id, name, language_preference, facts_json, last_interaction))
    
    conn.commit()
    conn.close()
    logger.info(f"Saved caller info for user_id={user_id}, name={name}")
    
    return {
        "user_id": user_id,
        "name": name,
        "language_preference": language_preference,
        "facts": cleaned_facts,
        "last_interaction": last_interaction
    }
