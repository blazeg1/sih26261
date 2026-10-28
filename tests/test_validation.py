"""
Tests for the Validation Engine module.

Validates application-level checks including completeness, document expiry,
field consistency, date logic, and summary generation.
"""

import os
import sys
from datetime import datetime, timedelta
from typing import Dict, Any

import pytest

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from modules.validation_engine import ValidationEngine, ValidationStatus, ValidationResult


class TestValidationEngine:
    """Test suite for modules.validation_engine.ValidationEngine."""

    def _make_complete_application(self) -> Dict[str, Any]:
        """Build a fully valid application dict for testing."""
        return {
            "application_id": "APP-2024-TEST",
            "institution": {
                "name": "ABC Institute of Technology",
                "aicte_id": "1-9347281",
                "university": "State Technical University",
                "state": "Rajasthan",
                "city": "Jaipur",
                "address": "Sitapura Industrial Area, Jaipur",
                "established_year": 2005,
                "contact_email": "director@abcinstitute.edu.in",
                "contact_phone": "+91-9876543210",
            },
            "category": "EOA",
            "academic_year": "2024-25",
            "faculty_count": 30,
            "student_count": 450,
            "programmes": [
                {
                    "name": "B.Tech Computer Science & Engineering",
                    "level": "UG",
                    "intake": 120,
                    "approved_intake": 120,
                    "faculty_count": 15,
                },
                {
                    "name": "B.Tech Mechanical Engineering",
                    "level": "UG",
                    "intake": 60,
                    "approved_intake": 60,
                    "faculty_count": 10,
                },
            ],
            "documents": [
                {
                    "doc_type": "AFFILIATION",
                    "filename": "affiliation_2026.pdf",
                    "issue_date": "2026-01-10",
                    "expiry_date": "2028-06-30",
                    "issuing_authority": "State Technical University",
                    "reference_number": "STU/AFF/2026/101",
                },
                {
                    "doc_type": "ACCREDITATION",
                    "filename": "nba_cert.pdf",
                    "issue_date": "2025-07-01",
                    "expiry_date": "2028-06-30",
                    "issuing_authority": "NBA",
                    "reference_number": "NBA/2025/55",
                },
                {
                    "doc_type": "FIRE_SAFETY",
                    "filename": "fire_noc.pdf",
                    "issue_date": "2026-02-01",
                    "expiry_date": "2028-01-31",
                    "issuing_authority": "Chief Fire Officer",
                    "reference_number": "CFO/2026/889",
                },
                {
                    "doc_type": "LAND_DOCUMENT",
                    "filename": "land_deed.pdf",
                    "issue_date": "2005-05-15",
                    "expiry_date": "2099-12-31",
                    "issuing_authority": "Sub-Registrar",
                    "reference_number": "REG/2005/4567",
                },
                {
                    "doc_type": "BUILDING_PLAN",
                    "filename": "building_plan.pdf",
                    "issue_date": "2005-08-20",
                    "expiry_date": "2099-12-31",
                    "issuing_authority": "Municipal Corp",
                    "reference_number": "BP/2005/890",
                },
                {
                    "doc_type": "FINANCIAL",
                    "filename": "audit_report.pdf",
                    "issue_date": "2026-03-31",
                    "expiry_date": "2027-09-30",
                    "issuing_authority": "Chartered Accountant",
                    "reference_number": "CA/2026/112",
                },
                {
                    "doc_type": "FACULTY_LIST",
                    "filename": "faculty_list.pdf",
                    "issue_date": "2026-03-01",
                    "expiry_date": "2027-06-30",
                    "issuing_authority": "Director",
                    "reference_number": "INST/FAC/2026",
                },
                {
                    "doc_type": "NOC",
                    "filename": "state_noc.pdf",
                    "issue_date": "2026-01-15",
                    "expiry_date": "2028-03-31",
                    "issuing_authority": "Govt of Rajasthan",
                    "reference_number": "NOC/2026/99",
                },
            ],
        }

    def _make_document(
        self,
        doc_type: str = "AFFILIATION",
        expiry_date: str | None = None,
        filename: str = "doc_test.pdf",
    ) -> Dict[str, Any]:
        """Build a sample document dict."""
        doc = {
            "doc_type": doc_type,
            "filename": filename,
            "issue_date": "2024-01-15",
            "expiry_date": expiry_date or "2026-06-30",
            "issuing_authority": "Authorized Authority",
            "reference_number": "REF-2024-001",
        }
        return doc

    def test_validate_complete_application(self) -> None:
        """All fields present — validation should produce passing results."""
        engine = ValidationEngine()
        application = self._make_complete_application()
        results = engine.validate_application(application)

        assert isinstance(results, list), "validate_application should return a list of ValidationResults"
        assert len(results) > 0, "Results list should not be empty"

        summary = engine.get_validation_summary(results)
        assert summary["pass_count"] > 0, "Complete application should have passing rules"
        assert summary["overall_score"] >= 80.0, f"Expected high overall score, got {summary['overall_score']}"

    def test_validate_missing_documents(self) -> None:
        """Application missing required documents should flag missing docs."""
        engine = ValidationEngine()
        application = self._make_complete_application()
        application["documents"] = [self._make_document("AFFILIATION")]

        results = engine.validate_application(application)
        fail_results = [r for r in results if r.status == ValidationStatus.FAIL and "MISSING" in r.message]
        assert len(fail_results) > 0, "Missing documents should produce FAIL results"

    def test_validate_expired_document(self) -> None:
        """Should detect documents with expiry dates in the past."""
        engine = ValidationEngine()

        past_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
        application = self._make_complete_application()
        application["documents"][0]["expiry_date"] = past_date

        results = engine.validate_application(application)
        expiry_fails = [r for r in results if r.status == ValidationStatus.FAIL and "expired" in r.message.lower()]
        assert len(expiry_fails) > 0, f"Expired document should produce FAIL rule. Results: {results}"

    def test_validate_field_consistency(self) -> None:
        """Checks cross-field consistency validation."""
        engine = ValidationEngine()
        application = self._make_complete_application()
        results = engine.validate_application(application)

        consistency_results = [r for r in results if r.category == "CONSISTENCY"]
        assert len(consistency_results) > 0, "Should include consistency checks"

    def test_validation_summary(self) -> None:
        """Validation summary should return structured counts and overall score."""
        engine = ValidationEngine()
        application = self._make_complete_application()
        results = engine.validate_application(application)
        summary = engine.get_validation_summary(results)

        assert isinstance(summary, dict), "Summary should be a dict"
        assert "pass_count" in summary
        assert "fail_count" in summary
        assert "warning_count" in summary
        assert "overall_score" in summary
        assert "by_category" in summary

    def test_date_logic_validation(self) -> None:
        """Future issue dates or expiry before issue should be flagged."""
        engine = ValidationEngine()
        application = self._make_complete_application()

        # Set an inverted date: expiry before issue
        application["documents"][0]["issue_date"] = "2025-01-01"
        application["documents"][0]["expiry_date"] = "2024-01-01"

        results = engine.validate_application(application)
        date_fails = [r for r in results if r.status == ValidationStatus.FAIL and "date" in r.message.lower()]
        assert len(date_fails) > 0, "Invalid date sequence should be flagged"

    def test_validate_document_basic(self) -> None:
        """Basic document validation should return ValidationResult items."""
        engine = ValidationEngine()
        document = self._make_document("AFFILIATION")
        results = engine.validate_document(document)

        assert isinstance(results, list), "validate_document should return a list"
        assert len(results) > 0, "Results should not be empty"
        assert all(isinstance(r, ValidationResult) for r in results)
