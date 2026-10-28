"""
Unit tests for Rectification Workflow Module (modules/rectification_service.py).
Tests bilingual notices, version diffing, and self-check mode.
"""

import pytest
from modules.rectification_service import RectificationService


@pytest.fixture
def service():
    return RectificationService()


def test_bilingual_notice_generation(service):
    inst_info = {
        "name": "Aryabhatta Institute of Technology",
        "case_id": "APP-2026-1042",
        "aicte_id": "1-3329182910"
    }
    deficiencies = [
        {
            "rule_name": "Fire Safety NOC Validity",
            "cited_clause": "APH 2024-27 Clause 4.1.2",
            "message": "Certificate expired on 2026-03-14",
            "computed_values": {"expiry_date": "2026-03-14"}
        }
    ]
    notice = service.generate_deficiency_notice_bilingual(inst_info, deficiencies)
    assert "english" in notice
    assert "hindi" in notice
    assert "Aryabhatta Institute" in notice["english"]
    assert "अखिल भारतीय तकनीकी शिक्षा परिषद" in notice["hindi"]
    assert "10(k)" in notice["english"]
    assert "10(k)" in notice["hindi"]


def test_validation_diff(service):
    prior = [
        {"rule_id": "R1", "status": "deficiency", "rule_name": "Fire NOC"},
        {"rule_id": "R2", "status": "deficiency", "rule_name": "Faculty Ratio"}
    ]
    current = [
        {"rule_id": "R1", "status": "pass", "rule_name": "Fire NOC", "message": "Renewed NOC verified"},
        {"rule_id": "R2", "status": "deficiency", "rule_name": "Faculty Ratio", "message": "Shortfall remains"}
    ]
    diff = service.compute_validation_diff(prior, current)
    assert diff["resolved_count"] == 1
    assert diff["persisting_count"] == 1
    r1_diff = next(d for d in diff["diff_items"] if d["rule_id"] == "R1")
    assert r1_diff["transition"] == "RESOLVED"


def test_self_check_mode(service):
    app_data = {
        "total_students": 600,
        "total_faculty": 45,
        "built_up_area_sqm": 4000.0,
        "land_area_acres": 8.0,
        "location_type": "RURAL",
        "fire_noc_expiry_date": "2028-12-31",
        "uploaded_documents": ["AFFIDAVIT", "FIRE_SAFETY_CERT", "FACULTY_LIST", "FINANCIAL_STATEMENT"],
        "category": "EOA"
    }
    res = service.run_self_check_mode(app_data, [])
    assert "readiness_score" in res
    assert res["readiness_score"] >= 80
    assert "advisory_disclaimer" in res
