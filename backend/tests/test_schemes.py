import pytest
import urllib.request
import urllib.error
import schemes

def test_get_supported_schemes_list():
    res = schemes.get_supported_schemes_list()
    assert "schemes" in res
    assert "is_live" in res
    assert "last_updated" in res
    
    # Check that our four main schemes are present
    schemes_dict = res["schemes"]
    assert "PM Kisan" in schemes_dict
    assert "PM Jan Dhan Yojana" in schemes_dict
    assert "PM Shram Yogi Maandhan" in schemes_dict
    assert "PM Suraksha Bima Yojana" in schemes_dict
    
    # Check descriptions exist
    assert "income support" in schemes_dict["PM Kisan"]["description"].lower()

def test_pm_kisan_eligibility():
    # Eligible: landholder and not income tax payer
    res = schemes.evaluate_eligibility("PM Kisan", {"owns_land": True, "is_income_tax_payer": False})
    assert res["eligible"] == "eligible"
    assert "Aadhaar Card" in res["documents"]
    assert "Land ownership documents (Khatauni/Patta)" in res["documents"]
    
    # Ineligible: does not own land
    res = schemes.evaluate_eligibility("PM Kisan", {"owns_land": False, "is_income_tax_payer": False})
    assert res["eligible"] == "ineligible"
    assert len(res["documents"]) == 0
    
    # Ineligible: owns land but pays income tax
    res = schemes.evaluate_eligibility("PM Kisan", {"owns_land": True, "is_income_tax_payer": True})
    assert res["eligible"] == "ineligible"
    
    # Undetermined: missing land ownership status
    res = schemes.evaluate_eligibility("PM Kisan", {"is_income_tax_payer": False})
    assert res["eligible"] == "undetermined"
    assert "owns_land" in res["missing_info"]
    assert "Aadhaar Card" in res["documents"]

def test_pmjdy_eligibility():
    # Eligible: no other bank account and at least 10 years old
    res = schemes.evaluate_eligibility("PM Jan Dhan Yojana", {"has_other_bank_account": False, "age": 12})
    assert res["eligible"] == "eligible"
    assert "Passport size photograph" in res["documents"]
    
    # Ineligible: has other bank account
    res = schemes.evaluate_eligibility("PM Jan Dhan Yojana", {"has_other_bank_account": True, "age": 12})
    assert res["eligible"] == "ineligible"
    
    # Ineligible: below 10 years old
    res = schemes.evaluate_eligibility("PM Jan Dhan Yojana", {"has_other_bank_account": False, "age": 8})
    assert res["eligible"] == "ineligible"
    
    # Undetermined: missing bank account status
    res = schemes.evaluate_eligibility("PM Jan Dhan Yojana", {"age": 15})
    assert res["eligible"] == "undetermined"
    assert "has_other_bank_account" in res["missing_info"]

def test_pm_sym_eligibility():
    # Eligible unorganized worker, age 18-40, income <= 15000, not covered under EPF/ESIC/NPS, not paying tax
    good_answers = {
        "age": 30,
        "monthly_income": 12000,
        "is_unorganized_worker": True,
        "is_covered_under_epf_esic": False,
        "is_income_tax_payer": False
    }
    res = schemes.evaluate_eligibility("PM Shram Yogi Maandhan", good_answers)
    assert res["eligible"] == "eligible"
    
    # Ineligible: too old (45)
    too_old = good_answers.copy()
    too_old["age"] = 45
    res = schemes.evaluate_eligibility("PM Shram Yogi Maandhan", too_old)
    assert res["eligible"] == "ineligible"
    
    # Ineligible: too young (16)
    too_young = good_answers.copy()
    too_young["age"] = 16
    res = schemes.evaluate_eligibility("PM Shram Yogi Maandhan", too_young)
    assert res["eligible"] == "ineligible"
    
    # Ineligible: high income
    high_income = good_answers.copy()
    high_income["monthly_income"] = 18000
    res = schemes.evaluate_eligibility("PM Shram Yogi Maandhan", high_income)
    assert res["eligible"] == "ineligible"
    
    # Ineligible: not unorganized worker
    organized = good_answers.copy()
    organized["is_unorganized_worker"] = False
    res = schemes.evaluate_eligibility("PM Shram Yogi Maandhan", organized)
    assert res["eligible"] == "ineligible"

    # Undetermined: missing income details
    missing = good_answers.copy()
    del missing["monthly_income"]
    res = schemes.evaluate_eligibility("PM Shram Yogi Maandhan", missing)
    assert res["eligible"] == "undetermined"
    assert "monthly_income" in res["missing_info"]

def test_pmsby_eligibility():
    # Eligible: age 18-70 and has savings bank account
    res = schemes.evaluate_eligibility("PM Suraksha Bima Yojana", {"age": 50, "has_savings_bank_account": True})
    assert res["eligible"] == "eligible"
    
    # Ineligible: too old (72)
    res = schemes.evaluate_eligibility("PM Suraksha Bima Yojana", {"age": 72, "has_savings_bank_account": True})
    assert res["eligible"] == "ineligible"
    
    # Ineligible: no savings bank account
    res = schemes.evaluate_eligibility("PM Suraksha Bima Yojana", {"age": 50, "has_savings_bank_account": False})
    assert res["eligible"] == "ineligible"

def test_scheme_unrecognized():
    res = schemes.evaluate_eligibility("Fake Scheme Name", {"age": 30})
    assert res["eligible"] == "undetermined"
    assert "not recognized or supported" in res["reasons"][0]

def test_remote_fetch_fallback(monkeypatch):
    """
    Ensure that when urlopen raises a network error or times out,
    the fetch_schemes_data falls back to local data gracefully,
    and returns is_live=False and a valid dictionary.
    """
    def mock_urlopen_fail(*args, **kwargs):
        raise urllib.error.URLError("Simulated Network Connection Refused / DNS Failure")
        
    monkeypatch.setattr(urllib.request, "urlopen", mock_urlopen_fail)
    
    data, is_live, last_updated = schemes.fetch_schemes_data()
    assert is_live is False
    assert last_updated == "2026-08-13"
    assert "PM Kisan" in data["schemes"]
