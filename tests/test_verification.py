"""
Tests for Verification Service module.

Validates issuing authority verification, API simulations,
and verification result status generation.
"""

import os
import sys
import pytest

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from modules.verification_service import VerificationService
from config.settings import DocumentTypes, VerificationStatuses


class TestVerificationService:
    """Test suite for VerificationService."""

    @pytest.fixture
    def service(self):
        return VerificationService()

    def test_verify_accreditation(self, service):
        doc_data = {
            "institution_name": "Maharaja Institute of Technology",
            "programme": "Computer Science & Engineering",
            "body": "NBA",
        }
        result = service.verify_document(DocumentTypes.ACCREDITATION_CERT, doc_data)
        assert isinstance(result, dict)
        assert "source_name" in result
        assert "verification_status" in result
        assert result["verification_status"] in [
            VerificationStatuses.VERIFIED,
            VerificationStatuses.MISMATCH_DETECTED,
            VerificationStatuses.VERIFICATION_PENDING,
            VerificationStatuses.MANUAL_REVIEW_REQUIRED,
        ]

    def test_verify_fire_safety(self, service):
        doc_data = {
            "certificate_number": "FSC/2025/123",
            "institution_name": "Maharaja Institute of Technology",
        }
        result = service.verify_document(DocumentTypes.FIRE_SAFETY_CERT, doc_data)
        assert isinstance(result, dict)
        assert "source_name" in result

    def test_batch_verify(self, service):
        docs = [
            {"doc_type": DocumentTypes.ACCREDITATION_CERT, "data": {"body": "NBA"}},
            {"doc_type": DocumentTypes.FIRE_SAFETY_CERT, "data": {"num": "123"}},
        ]
        results = service.batch_verify(docs)
        assert isinstance(results, list)
        assert len(results) == 2
