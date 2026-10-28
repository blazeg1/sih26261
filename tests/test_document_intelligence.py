"""
Unit tests for Document Intelligence Module (modules/document_intelligence.py).
Tests PyMuPDF text & bbox extraction, explainable classification, and cross-document consistency.
"""

import os
import pytest
import fitz
from modules.document_intelligence import DocumentIntelligence, ExplainableClassifier, CrossDocumentConsistencyChecker


@pytest.fixture
def sample_pdf(tmp_path):
    pdf_path = str(tmp_path / "sample_noc.pdf")
    doc = fitz.open()
    page = doc.new_page(width=600, height=800)
    text = (
        "GOVERNMENT OF UTTAR PRADESH\n"
        "DIRECTORATE OF FIRE & EMERGENCY SERVICES\n"
        "FIRE SAFETY CERTIFICATE / NOC\n"
        "Permanent AICTE ID: 1-3329182910\n"
        "Institution: Aryabhatta Institute of Technology\n"
        "Survey Number: 492/1\n"
        "Land Area: 7.5 Acres\n"
        "Sponsored by: Aryabhatta Educational Trust\n"
        "Issue Date: 15/03/2024  Expiry Date: 14/03/2026\n"
    )
    page.insert_text((50, 80), text, fontsize=12)
    doc.save(pdf_path)
    doc.close()
    return pdf_path


def test_pdf_extraction_with_bbox(sample_pdf):
    doc_intel = DocumentIntelligence()
    res = doc_intel.extract_from_pdf(sample_pdf)
    assert res["num_pages"] == 1
    assert len(res["fields"]) > 0

    field_names = [f["field_name"] for f in res["fields"]]
    assert "aicte_id" in field_names

    # Check bounding box presence
    aicte_field = next(f for f in res["fields"] if f["field_name"] == "aicte_id")
    assert aicte_field["value"] == "1-3329182910"
    assert aicte_field["source_page"] == 1
    assert aicte_field["bbox"] is not None
    assert "x0" in aicte_field["bbox"]
    assert aicte_field["confidence"] >= 0.90


def test_explainable_classification():
    classifier = ExplainableClassifier()
    text = "Directorate of Fire Services NOC Fire Safety Certificate rescue hydrant"
    res = classifier.classify(text, filename="Fire_NOC.pdf")

    assert res["predicted_type"] == "FIRE_SAFETY_CERT"
    assert res["confidence"] >= 0.85
    assert len(res["explanation"]) > 0
    # Explanation shows matched keywords and their weights
    top_kw, weight = res["explanation"][0]
    assert weight > 0


def test_cross_document_consistency():
    checker = CrossDocumentConsistencyChecker()
    declared = {
        "institution_name": "Aryabhatta Institute of Technology",
        "survey_number": "492/1",
        "land_area_acres": 7.5
    }
    extracted_docs = [
        {
            "filename": "Fire_NOC.pdf",
            "extracted_name": "Aryabhatta Institute of Technology",
            "survey_number": "492/1",
            "land_area_acres": 7.5
        },
        {
            "filename": "Old_Deed.pdf",
            "extracted_name": "Aryabhatta Inst of Tech",
            "survey_number": "999/X",  # Mismatch!
            "land_area_acres": 2.5   # Mismatch!
        }
    ]
    findings = checker.check_dossier_consistency(declared, extracted_docs)
    assert len(findings) > 0

    # Look for the survey number mismatch
    survey_mismatch = [f for f in findings if f["check"] == "Land Survey Number Cross-Check" and f["status"] == "Deficiency"]
    assert len(survey_mismatch) == 1
    assert survey_mismatch[0]["document"] == "Old_Deed.pdf"
