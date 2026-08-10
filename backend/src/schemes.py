import os
import json
import urllib.request
import urllib.error
import logging

logger = logging.getLogger("schemes")

LOCAL_DATA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "schemes_data.json")
# Remote API fallback URL
REMOTE_URL = "https://raw.githubusercontent.com/laks-h/murf-livekit-starter/main/backend/src/schemes_data.json"

def fetch_schemes_data() -> tuple[dict, bool, str]:
    """
    Attempts to fetch the schemes data from the remote URL.
    Falls back to local file if the remote call fails or times out.
    
    Returns:
        tuple containing:
        - dict: schemes data
        - bool: is_live (True if fetched from remote, False if fallback)
        - str: last updated timestamp
    """
    try:
        logger.info(f"Attempting to fetch scheme details from remote: {REMOTE_URL}")
        # Set 2.0s timeout to handle slow/offline connections gracefully
        with urllib.request.urlopen(REMOTE_URL, timeout=2.0) as response:
            if response.status == 200:
                data = json.loads(response.read().decode("utf-8"))
                logger.info("Successfully fetched scheme details from remote API.")
                return data, True, data.get("last_updated", "unknown")
            else:
                logger.warning(f"Failed to fetch remote scheme details. Status code: {response.status}")
    except urllib.error.URLError as e:
        logger.warning(f"Network error trying to fetch scheme details from remote: {e}")
    except TimeoutError as e:
        logger.warning(f"Timeout trying to fetch scheme details from remote: {e}")
    except Exception as e:
        logger.warning(f"Unexpected error trying to fetch scheme details from remote: {e}")
        
    # Fallback to local
    logger.info(f"Falling back to local cached scheme details: {LOCAL_DATA_PATH}")
    try:
        with open(LOCAL_DATA_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data, False, data.get("last_updated", "unknown")
    except Exception as e:
        logger.error(f"Failed to load local fallback scheme details: {e}")
        # Emergency backup structure if local file is missing/corrupted
        backup_data = {
            "last_updated": "2026-08-10 (emergency-fallback)",
            "schemes": {
                "PM Kisan": {
                    "name": "Pradhan Mantri Kisan Samman Nidhi",
                    "description": "Income support of Rs. 6000 per year in three equal installments to all landholding farmer families.",
                    "eligibility": {"owns_land": true, "is_income_tax_payer": false},
                    "documents": ["Aadhaar Card", "Land ownership documents (Khatauni/Patta)", "Bank Account details", "Mobile number"]
                }
            }
        }
        return backup_data, False, backup_data["last_updated"]

def get_supported_schemes_list() -> dict:
    """
    Returns names and descriptions of supported schemes.
    """
    data, is_live, last_updated = fetch_schemes_data()
    schemes_info = {}
    for key, val in data.get("schemes", {}).items():
        schemes_info[key] = {
            "name": val.get("name"),
            "description": val.get("description")
        }
    return {
        "schemes": schemes_info,
        "is_live": is_live,
        "last_updated": last_updated
    }

def evaluate_eligibility(scheme_key: str, answers: dict) -> dict:
    """
    Evaluates eligibility for a scheme based on caller's answers.
    """
    data, is_live, last_updated = fetch_schemes_data()
    
    # Normalise scheme key search
    matched_key = None
    for k in data.get("schemes", {}).keys():
        if k.lower() == scheme_key.lower():
            matched_key = k
            break
            
    if not matched_key:
        return {
            "scheme": scheme_key,
            "eligible": "undetermined",
            "reasons": [f"Scheme '{scheme_key}' is not recognized or supported."],
            "missing_info": [],
            "documents": [],
            "is_live": is_live,
            "last_updated": last_updated
        }
        
    scheme = data["schemes"][matched_key]
    req_eligibility = scheme.get("eligibility", {})
    documents = scheme.get("documents", [])
    
    eligible = True
    reasons = []
    missing_info = []
    
    # Evaluate checks based on the rules in the schema
    for criterion, expected_val in req_eligibility.items():
        if criterion == "min_age":
            if "age" not in answers or answers["age"] is None:
                missing_info.append("age")
                eligible = "undetermined"
            elif int(answers["age"]) < expected_val:
                eligible = False
                reasons.append(f"Age {answers['age']} is below minimum requirement of {expected_val} years.")
            else:
                reasons.append(f"Age {answers['age']} meets minimum requirement of {expected_val} years.")
                
        elif criterion == "max_age":
            if "age" not in answers or answers["age"] is None:
                if "age" not in missing_info:
                    missing_info.append("age")
                eligible = "undetermined"
            elif int(answers["age"]) > expected_val:
                eligible = False
                reasons.append(f"Age {answers['age']} is above maximum limit of {expected_val} years.")
            else:
                reasons.append(f"Age {answers['age']} is within maximum limit of {expected_val} years.")
                
        elif criterion == "max_monthly_income":
            if "monthly_income" not in answers or answers["monthly_income"] is None:
                missing_info.append("monthly_income")
                eligible = "undetermined"
            elif float(answers["monthly_income"]) > expected_val:
                eligible = False
                reasons.append(f"Monthly income Rs. {answers['monthly_income']} exceeds limit of Rs. {expected_val}.")
            else:
                reasons.append(f"Monthly income Rs. {answers['monthly_income']} is within limit of Rs. {expected_val}.")
                
        # Boolean criteria
        else:
            if criterion not in answers or answers[criterion] is None:
                missing_info.append(criterion)
                if eligible != False:
                    eligible = "undetermined"
            else:
                user_val = bool(answers[criterion])
                if user_val != expected_val:
                    eligible = False
                    reasons.append(f"Criterion '{criterion}' is {user_val}, but scheme requires {expected_val}.")
                else:
                    reasons.append(f"Criterion '{criterion}' matches scheme requirement.")

    if eligible == "undetermined":
        status_text = "undetermined"
    elif eligible:
        status_text = "eligible"
    else:
        status_text = "ineligible"
        
    return {
        "scheme": matched_key,
        "eligible": status_text,
        "reasons": reasons,
        "missing_info": missing_info,
        "documents": documents if status_text != "ineligible" else [],
        "is_live": is_live,
        "last_updated": last_updated
    }
