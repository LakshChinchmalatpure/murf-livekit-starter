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
    """Initializes the database and creates the callers table if it does not exist."""
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
    conn.commit()
    conn.close()
    logger.info(f"Database initialized at: {DB_PATH}")

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
