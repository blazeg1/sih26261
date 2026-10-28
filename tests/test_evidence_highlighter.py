"""
Unit tests for Evidence Highlighter & Explainable Risk Score (modules/evidence_highlighter.py).
"""

import pytest
from modules.evidence_highlighter import compute_explainable_risk_score, highlight_evidence_on_page


def test_explainable_risk_score_clean():
    clean_findings = [
        {"rule_name": "Faculty Student Ratio", "status": "Verified", "severity": "LOW"},
        {"rule_name": "Built-up Area", "status": "pass", "severity": "LOW"}
    ]
    res = compute_explainable_risk_score(clean_findings)
    assert res["final_score"] == 100
    assert res["category"] == "LOW_RISK"
    assert len(res["deductions"]) == 0
    assert "ADVISORY NOTICE" in res["advisory_notice"]


def test_explainable_risk_score_with_deficiencies():
    deficient_findings = [
        {
            "rule_name": "Fire Safety NOC Validity",
            "status": "Deficiency",
            "severity": "CRITICAL",
            "message": "Fire NOC expired on 2026-03-14",
            "cited_clause": "APH 2024-27 Clause 4.1.2"
        },
        {
            "rule_name": "Faculty Cadre Proportion",
            "status": "Possible anomaly - needs human verification",
            "severity": "MEDIUM",
            "message": "Shortage of 2 Associate Professors",
            "cited_clause": "APH 2024-27 Clause 2.3.4"
        }
    ]
    res = compute_explainable_risk_score(deficient_findings)
    assert res["final_score"] < 100
    assert len(res["deductions"]) == 2

    # Check that each deduction has reason and clause
    d1 = res["deductions"][0]
    assert d1["deduction"] == -25
    assert "Fire NOC expired" in d1["reason"]
    assert "Clause 4.1.2" in d1["clause"]


def test_highlight_evidence_on_page_fallback(tmp_path):
    # Non-existent file gracefully returns fallback preview
    img = highlight_evidence_on_page("nonexistent.pdf", page_number=1, search_text="Fire Safety")
    assert img is not None
    assert img.size[0] > 0
