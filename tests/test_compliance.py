"""
Tests for the Compliance Checker module.

Validates compliance checks for AICTE norms including document completeness,
faculty requirements, infrastructure requirements, and scoring.
"""

import os
import sys
from typing import Dict, Any

import pytest

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


class TestComplianceChecker:
    """Test suite for modules.compliance_checker.ComplianceChecker."""

    def _fully_compliant_application(self) -> Dict[str, Any]:
        """Build an application that meets all AICTE requirements."""
        return {
            "application_id": "APP-2024-COMPLIANT",
            "institution_id": "INST-2024-001",
            "institution_name": "ABC Institute of Technology",
            "application_type": "Extension of Approval",
            "academic_year": "2024-25",
            "date_submitted": "2024-03-15",
            "status": "Under Review",
            "programmes": [
                {
                    "name": "B.Tech Computer Science & Engineering",
                    "level": "UG",
                    "intake": 120,
                    "faculty_count": 15,
                },
                {
                    "name": "B.Tech Mechanical Engineering",
                    "level": "UG",
                    "intake": 60,
                    "faculty_count": 10,
                },
                {
                    "name": "MBA",
                    "level": "PG",
                    "intake": 60,
                    "faculty_count": 8,
                },
            ],
            "total_intake": 240,
            "total_faculty": 45,
            "faculty_with_phd": 12,
            "land_area_acres": 5.2,
            "built_up_area_sqm": 25000,
            "library_books": 15000,
            "student_faculty_ratio": "15:1",
            "documents_submitted": [
                "AFFILIATION",
                "ACCREDITATION",
                "FIRE_SAFETY",
                "LAND_DOCUMENT",
                "BUILDING_PLAN",
                "FINANCIAL",
                "FACULTY_LIST",
                "NOC",
            ],
            "fdr_amount": 10000000,
            "annual_revenue": 50000000,
            "annual_expenditure": 40000000,
        }

    def test_full_compliance(self) -> None:
        """Application meeting all requirements should pass compliance."""
        from modules.compliance_checker import ComplianceChecker, ComplianceStatus

        checker = ComplianceChecker()
        application = self._fully_compliant_application()
        results = checker.check_compliance(application)

        assert isinstance(results, list), "check_compliance should return a list of checks"
        assert len(results) > 0, "Result should not be empty"

        compliant_count = sum(1 for r in results if r["status"] == ComplianceStatus.COMPLIANT)
        assert compliant_count > 0, "Fully compliant application should have passing checks"

        score = checker.get_compliance_score(results)
        assert score >= 70.0, f"Expected high compliance score for compliant application, got {score}"

    def test_missing_documents_compliance(self) -> None:
        """Missing required documents should flag non-compliance."""
        from modules.compliance_checker import ComplianceChecker, ComplianceStatus

        checker = ComplianceChecker()
        application = self._fully_compliant_application()
        application["documents_submitted"] = ["AFFILIATION"]

        results = checker.check_compliance(application)
        assert isinstance(results, list)

        doc_checks = [r for r in results if r["category"] == "DOCUMENT"]
        non_compliant_docs = [r for r in doc_checks if r["status"] == ComplianceStatus.NON_COMPLIANT]
        assert len(non_compliant_docs) > 0, "Missing documents should produce NON_COMPLIANT checks"

    def test_faculty_requirements(self) -> None:
        """Inadequate faculty count should flag non-compliance."""
        from modules.compliance_checker import ComplianceChecker, ComplianceStatus

        checker = ComplianceChecker()
        application = self._fully_compliant_application()
        application["total_faculty"] = 2
        application["faculty_with_phd"] = 0
        application["student_count"] = 500

        results = checker.check_compliance(application)
        faculty_checks = [r for r in results if r["category"] == "FACULTY"]
        non_compliant = [r for r in faculty_checks if r["status"] == ComplianceStatus.NON_COMPLIANT]
        assert len(non_compliant) > 0, "Inadequate faculty should produce non-compliant checks"

    def test_infrastructure_requirements(self) -> None:
        """Insufficient built-up area should flag non-compliance."""
        from modules.compliance_checker import ComplianceChecker, ComplianceStatus

        checker = ComplianceChecker()
        application = self._fully_compliant_application()
        application["land_area_acres"] = 0.1
        application["built_up_area_sqm"] = 50

        results = checker.check_compliance(application)
        infra_checks = [r for r in results if r["category"] == "INFRASTRUCTURE"]
        non_compliant = [r for r in infra_checks if r["status"] == ComplianceStatus.NON_COMPLIANT]
        assert len(non_compliant) > 0, "Insufficient infrastructure should produce non-compliant checks"

    def test_compliance_score(self) -> None:
        """Compliance score should return a float between 0 and 100."""
        from modules.compliance_checker import ComplianceChecker

        checker = ComplianceChecker()
        application = self._fully_compliant_application()
        score = checker.get_compliance_score(application)

        assert isinstance(score, (int, float)), f"Score should be numeric, got {type(score)}"
        assert 0.0 <= float(score) <= 100.0, f"Score should be between 0 and 100, got {score}"

    def test_compliance_score_fully_compliant_high(self) -> None:
        """A fully compliant application should score high."""
        from modules.compliance_checker import ComplianceChecker

        checker = ComplianceChecker()
        application = self._fully_compliant_application()
        score = checker.get_compliance_score(application)

        assert float(score) >= 70.0, f"Fully compliant application should score ≥70, got {score}"

    def test_compliance_summary(self) -> None:
        """Compliance result should have a category breakdown."""
        from modules.compliance_checker import ComplianceChecker

        checker = ComplianceChecker()
        application = self._fully_compliant_application()
        results = checker.check_compliance(application)
        summary = checker.get_compliance_summary(results)

        assert isinstance(summary, dict), "Summary should be a dict"
        assert "by_category" in summary
        assert "overall_score" in summary
        assert len(summary["by_category"]) > 0

    def test_partial_compliance_lower_score(self) -> None:
        """Partially compliant application should score lower than fully compliant."""
        from modules.compliance_checker import ComplianceChecker

        checker = ComplianceChecker()

        full_app = self._fully_compliant_application()
        full_score = checker.get_compliance_score(full_app)

        partial_app = self._fully_compliant_application()
        partial_app["documents_submitted"] = ["AFFILIATION"]
        partial_app["total_faculty"] = 2
        partial_app["land_area_acres"] = 0.1
        partial_app["built_up_area_sqm"] = 50
        partial_score = checker.get_compliance_score(partial_app)

        assert float(partial_score) < float(full_score), (
            f"Partial compliance ({partial_score}) should score lower than full compliance ({full_score})"
        )
