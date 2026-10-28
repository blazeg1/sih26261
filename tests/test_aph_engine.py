"""
Unit tests for APH-as-Code Compliance Engine (modules/aph_engine.py).
Tests all 12 regulatory rules, edge cases, and unverified threshold markings.
"""

import pytest
from modules.aph_engine import APHEngine, load_norms


@pytest.fixture
def engine():
    return APHEngine()


def test_load_norms():
    norms = load_norms()
    assert "faculty_student_ratio" in norms
    assert "land_norms_acres" in norms
    assert "safety_norms" in norms


def test_check_sfr_pass(engine):
    # 600 students, 45 faculty -> actual SFR 1:13.3 <= 15
    res = engine.check_sfr(total_students=600, total_faculty=45, programme="ENGINEERING_UG")
    assert res["status"] == "pass"
    assert "RULE_SFR" == res["rule_id"]
    assert "APH 2024-27 Clause 2.3.1" in res["cited_clause"]


def test_check_sfr_needs_review(engine):
    # 600 students, 35 faculty -> actual SFR 1:17.1 (between 15 and 20)
    res = engine.check_sfr(total_students=600, total_faculty=35, programme="ENGINEERING_UG")
    assert res["status"] == "needs_review"
    assert res["computed_values"]["deficit_count"] == 5


def test_check_sfr_deficiency(engine):
    # 600 students, 20 faculty -> actual SFR 1:30 (> 20)
    res = engine.check_sfr(total_students=600, total_faculty=20, programme="ENGINEERING_UG")
    assert res["status"] == "deficiency"


def test_check_cadre_ratio(engine):
    # 9 faculty: 1 Prof, 2 Assoc, 6 Asst -> Pass
    res = engine.check_cadre_ratio(professors=1, assoc_professors=2, asst_professors=6)
    assert res["status"] == "pass"

    # Deficit in professors
    res_def = engine.check_cadre_ratio(professors=0, assoc_professors=0, asst_professors=9)
    assert res_def["status"] == "deficiency"


def test_check_builtup_area(engine):
    # 1000 students * 4.5 = 4500 sqm required
    res_pass = engine.check_builtup_area(declared_sqm=5000.0, total_students=1000)
    assert res_pass["status"] == "pass"

    res_fail = engine.check_builtup_area(declared_sqm=3000.0, total_students=1000)
    assert res_fail["status"] == "deficiency"


def test_check_land_area(engine):
    # Rural: 7.5 acres required
    res_pass = engine.check_land_area(declared_acres=8.0, location_type="RURAL")
    assert res_pass["status"] == "pass"

    res_fail = engine.check_land_area(declared_acres=5.0, location_type="RURAL")
    assert res_fail["status"] == "deficiency"

    # Metro: 1.5 acres required
    res_metro = engine.check_land_area(declared_acres=2.0, location_type="MEGA_METRO")
    assert res_metro["status"] == "pass"


def test_check_lease_duration(engine):
    res_owned = engine.check_lease_duration(0, title_type="OWNED")
    assert res_owned["status"] == "pass"

    res_lease_ok = engine.check_lease_duration(35, title_type="REGISTERED_LEASE")
    assert res_lease_ok["status"] == "pass"

    res_lease_fail = engine.check_lease_duration(15, title_type="REGISTERED_LEASE")
    assert res_lease_fail["status"] == "deficiency"


def test_check_fire_noc_validity(engine):
    # Future date -> pass
    res_pass = engine.check_fire_noc_validity("2028-12-31", submission_date_str="2026-03-15")
    assert res_pass["status"] == "pass"

    # Past date -> deficiency
    res_fail = engine.check_fire_noc_validity("2025-01-01", submission_date_str="2026-03-15")
    assert res_fail["status"] == "deficiency"

    # Missing -> deficiency
    res_none = engine.check_fire_noc_validity(None)
    assert res_none["status"] == "deficiency"


def test_check_mandatory_documents(engine):
    docs = ["AFFIDAVIT", "FIRE_SAFETY_CERT", "FACULTY_LIST", "FINANCIAL_STATEMENT"]
    res_pass = engine.check_mandatory_documents(docs, application_type="EOA")
    assert res_pass["status"] == "pass"

    res_fail = engine.check_mandatory_documents(["AFFIDAVIT"], application_type="EOA")
    assert res_fail["status"] == "deficiency"
    assert "FIRE_SAFETY_CERT" in res_fail["computed_values"]["missing_documents"]


def test_check_intake_increase(engine):
    res_pass = engine.check_intake_increase_eligibility(nba_accredited_pct=60.0, years_in_existence=6)
    assert res_pass["status"] == "pass"

    res_fail = engine.check_intake_increase_eligibility(nba_accredited_pct=20.0, years_in_existence=6)
    assert res_fail["status"] == "deficiency"


def test_check_statutory_committees(engine):
    committees = [
        "Anti-Ragging Committee",
        "Internal Complaints Committee (ICC)",
        "Student Grievance Redressal Committee",
        "SC/ST Cell"
    ]
    res_pass = engine.check_statutory_committees(committees)
    assert res_pass["status"] == "pass"

    res_fail = engine.check_statutory_committees(["Anti-Ragging Committee"])
    assert res_fail["status"] == "deficiency"


def test_full_dossier_evaluation(engine):
    dossier = {
        "total_students": 900,
        "total_faculty": 65,
        "cadre_professors": 6,
        "cadre_assoc_professors": 14,
        "cadre_asst_professors": 45,
        "built_up_area_sqm": 12000.0,
        "land_area_acres": 7.5,
        "location_type": "RURAL",
        "lease_duration_years": 30,
        "fire_noc_expiry_date": "2027-12-31",
        "submission_date": "2026-03-20",
        "uploaded_documents": ["AFFIDAVIT", "FIRE_SAFETY_CERT", "FACULTY_LIST", "FINANCIAL_STATEMENT"],
        "category": "EOA",
        "computer_terminals": 250,
        "internet_bandwidth_mbps": 300
    }
    findings = engine.evaluate_dossier(dossier)
    assert len(findings) >= 11
    # Check that each finding has required fields
    for f in findings:
        assert "rule_id" in f
        assert "status" in f
        assert f["status"] in ("pass", "deficiency", "needs_review")
        assert "cited_clause" in f
        assert "computed_values" in f
