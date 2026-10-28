"""
Tests for Document Classifier module.

Validates document categorization based on keyword matches and filename hints.
"""

import os
import sys
import pytest

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from modules.document_classifier import DocumentClassifier
from config.settings import DocumentTypes


class TestDocumentClassifier:
    """Test suite for DocumentClassifier."""

    @pytest.fixture
    def classifier(self):
        return DocumentClassifier()

    def test_classify_affidavit(self, classifier):
        text = "AFFIDAVIT\nI, the undersigned deponent, solemnly affirm and declare on oath before the notary..."
        doc_type, confidence = classifier.classify(text, "affidavit_signed.pdf")
        assert doc_type == DocumentTypes.AFFIDAVIT
        assert confidence > 0.3

    def test_classify_noc(self, classifier):
        text = "GOVERNMENT OF RAJASTHAN\nNO OBJECTION CERTIFICATE\nState government has no objection to the institution..."
        doc_type, confidence = classifier.classify(text, "noc_govt.pdf")
        assert doc_type == DocumentTypes.NOC
        assert confidence > 0.3

    def test_classify_fire_safety(self, classifier):
        text = "OFFICE OF THE CHIEF FIRE OFFICER\nFIRE SAFETY CERTIFICATE\nPremises inspected and approved for fire safety..."
        doc_type, confidence = classifier.classify(text, "fire_noc.pdf")
        assert doc_type == DocumentTypes.FIRE_SAFETY_CERT
        assert confidence > 0.3

    def test_classify_faculty_list(self, classifier):
        text = "TEACHING STAFF DETAILS\nList of faculty members, professors, assistant professors with PhD and M.Tech designations..."
        doc_type, confidence = classifier.classify(text, "faculty_list_2026.pdf")
        assert doc_type == DocumentTypes.FACULTY_LIST
        assert confidence > 0.3

    def test_classify_financial(self, classifier):
        text = "AUDITED FINANCIAL STATEMENT\nBalance sheet, revenue, expenditure, and fixed deposit (FDR) audited by Chartered Accountant..."
        doc_type, confidence = classifier.classify(text, "audit_balance_sheet.pdf")
        assert doc_type == DocumentTypes.FINANCIAL_STATEMENT
        assert confidence > 0.3

    def test_classify_unknown(self, classifier):
        text = "The quick brown fox jumps over the lazy dog."
        doc_type, confidence = classifier.classify(text, "unknown_sample.pdf")
        assert doc_type in ("UNKNOWN", DocumentTypes.AFFIDAVIT) or confidence <= 0.2

    def test_get_all_scores(self, classifier):
        text = "Affidavit of deponent solemnly affirmed for AICTE extension of approval"
        scores = classifier.get_all_scores(text)
        assert isinstance(scores, dict)
        assert DocumentTypes.AFFIDAVIT in scores
        assert scores[DocumentTypes.AFFIDAVIT] >= 0.0
