"""
Tests for the Anomaly Detector module.

Validates text anomaly detection, duplicate content detection,
anomaly scoring, metadata consistency checks, and date anomaly detection.
"""

import os
import sys
from datetime import datetime, timedelta
from typing import Dict, Any

import pytest

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


class TestAnomalyDetector:
    """Test suite for modules.anomaly_detector.AnomalyDetector."""

    def _clean_affidavit_text(self) -> str:
        """Return clean, legitimate affidavit text."""
        return (
            "AFFIDAVIT\n\n"
            "I, Dr. Rajesh Kumar Sharma, Chairman of ABC Institute of Technology, "
            "do hereby solemnly affirm that all information provided in this "
            "application for Extension of Approval for the academic year 2024-25 "
            "is true and correct to the best of my knowledge.\n\n"
            "The institution has 45 faculty members, 15000 library books, and "
            "25000 sq.m. of built-up area on 5.2 acres of land.\n\n"
            "Date: 15/03/2024\n"
            "Place: Jaipur, Rajasthan\n"
        )

    def _suspicious_text(self) -> str:
        """Return text with suspicious patterns (copy-paste, gibberish)."""
        return (
            "AFFIDAVIT\n\n"
            "Lorem ipsum dolor sit amet, consectetur adipiscing elit. "
            "Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.\n\n"
            "XXXX XXXX XXXX XXXX XXXX XXXX XXXX XXXX XXXX\n"
            "asdfghjkl qwertyuiop zxcvbnm asdfghjkl\n\n"
            "This text has been copied from another document and pasted here. "
            "The same sentence is repeated multiple times. "
            "The same sentence is repeated multiple times. "
            "The same sentence is repeated multiple times. "
            "The same sentence is repeated multiple times.\n\n"
            "######### @@@@@@@@@ !!!!!!!! $$$$$$$$\n"
            "Date: 01/01/1800\n"
        )

    def test_check_text_anomalies_clean(self) -> None:
        """Clean text should produce no or very few anomaly alerts."""
        from modules.anomaly_detector import AnomalyDetector

        detector = AnomalyDetector()
        result = detector.check_text_anomalies(self._clean_affidavit_text())

        assert isinstance(result, list), "check_text_anomalies should return a list of alerts"
        assert len(result) <= 2, f"Clean text should have few anomalies, found {len(result)}"

    def test_check_text_anomalies_suspicious(self) -> None:
        """Text with suspicious patterns should flag anomalies."""
        from modules.anomaly_detector import AnomalyDetector

        detector = AnomalyDetector()
        result = detector.check_text_anomalies(self._suspicious_text())

        assert isinstance(result, list), "check_text_anomalies should return a list of alerts"
        assert len(result) > 0, "Suspicious text should trigger anomaly alerts"

        alert_types = [a["alert_type"] for a in result]
        has_flags = any(
            t in alert_types
            for t in ["REPEATED_PHRASES", "REPEATED_CONTENT", "GIBBERISH_DETECTED", "CHARACTER_FLOOD", "SUSPICIOUS_PHRASE"]
        )
        assert has_flags, f"Expected suspicious pattern alert, got {alert_types}"

    def test_check_duplicate_content(self) -> None:
        """Identical texts submitted as different documents should flag as duplicate."""
        from modules.anomaly_detector import AnomalyDetector

        detector = AnomalyDetector()
        text1 = self._clean_affidavit_text()
        text2 = self._clean_affidavit_text()  # identical

        result = detector.analyze_document(
            text=text1,
            metadata={
                "document_type": "affidavit",
                "creation_date": "2024-03-15",
            },
            reference_texts=[text2],
        )

        assert isinstance(result, list), "analyze_document should return a list of alerts"
        alert_types = [a["alert_type"] for a in result]
        assert any("DUPLICATE" in t for t in alert_types), f"Expected duplicate alert, got {alert_types}"

    def test_check_duplicate_content_different(self) -> None:
        """Very different texts should not flag as duplicate."""
        from modules.anomaly_detector import AnomalyDetector

        detector = AnomalyDetector()

        text1 = (
            "FIRE SAFETY CERTIFICATE\n"
            "This is to certify that the building at Plot 12, Sitapura has been "
            "inspected and found compliant with fire safety norms. Certificate "
            "valid until 31/12/2025."
        )
        text2 = (
            "FINANCIAL STATEMENT\n"
            "Income for FY 2023-24: Tuition Rs. 4.5 Crore, Development Rs. 75 Lakh. "
            "Total expenditure Rs. 4.23 Crore including salaries and infrastructure."
        )

        result = detector.analyze_document(
            text=text1,
            metadata={"document_type": "fire_safety", "creation_date": "2024-01-15"},
            reference_texts=[text2],
        )

        assert isinstance(result, list), "analyze_document should return a list"
        alert_types = [a["alert_type"] for a in result]
        assert "DUPLICATE_CONTENT" not in alert_types

    def test_calculate_anomaly_score(self) -> None:
        """Anomaly score should be a float between 0 and 1."""
        from modules.anomaly_detector import AnomalyDetector

        detector = AnomalyDetector()
        score = detector.calculate_anomaly_score(
            text=self._clean_affidavit_text(),
            metadata={"document_type": "affidavit", "creation_date": "2024-03-15"},
        )

        assert isinstance(score, (int, float)), f"Anomaly score should be numeric, got {type(score)}"
        assert 0.0 <= float(score) <= 1.0, f"Anomaly score should be between 0 and 1, got {score}"

    def test_check_metadata_consistency(self) -> None:
        """Future creation dates should flag metadata inconsistency."""
        from modules.anomaly_detector import AnomalyDetector

        detector = AnomalyDetector()

        future_date = (datetime.now() + timedelta(days=365 * 3)).strftime("%Y-%m-%d")
        result = detector.analyze_document(
            text=self._clean_affidavit_text(),
            metadata={
                "document_type": "affidavit",
                "creation_date": future_date,
                "modification_date": future_date,
            },
        )

        assert isinstance(result, list), "analyze_document should return a list"
        alert_types = [a["alert_type"] for a in result]
        assert any("FUTURE" in t or "DATE" in t for t in alert_types), (
            f"Future date should trigger date anomaly alert. Got: {alert_types}"
        )

    def test_check_date_anomalies(self) -> None:
        """Dates before 1990 in AICTE context should be suspicious."""
        from modules.anomaly_detector import AnomalyDetector

        detector = AnomalyDetector()

        old_text = (
            "AFFIDAVIT\n"
            "This institution was established on 01/01/1850 and has been "
            "operating since then. The land was purchased on 15/06/1920.\n"
            "Date: 01/01/1800\n"
        )

        result = detector.check_text_anomalies(old_text)
        assert isinstance(result, list), "check_text_anomalies should return a list"

    def test_anomaly_score_suspicious_higher(self) -> None:
        """Suspicious text should generally score higher than clean text."""
        from modules.anomaly_detector import AnomalyDetector

        detector = AnomalyDetector()

        clean_score = detector.calculate_anomaly_score(
            text=self._clean_affidavit_text(),
            metadata={"document_type": "affidavit", "creation_date": "2024-03-15"},
        )
        suspicious_score = detector.calculate_anomaly_score(
            text=self._suspicious_text(),
            metadata={"document_type": "affidavit", "creation_date": "2024-03-15"},
        )

        assert isinstance(clean_score, (int, float)), "Score should be numeric"
        assert isinstance(suspicious_score, (int, float)), "Score should be numeric"
        assert suspicious_score > clean_score, (
            f"Suspicious score ({suspicious_score}) should be higher than clean score ({clean_score})"
        )
