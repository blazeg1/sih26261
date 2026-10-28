"""
Tests for Data Extractor module.

Validates extraction of dates, AICTE IDs, emails, phone numbers,
amounts, pincodes, and structured entities from OCR text.
"""

import os
import sys
import pytest

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from modules.data_extractor import DataExtractor


class TestDataExtractor:
    """Test suite for DataExtractor."""

    @pytest.fixture
    def extractor(self):
        return DataExtractor()

    def test_extract_dates(self, extractor):
        text = "Meeting held on 15/03/2025 and approval granted on 2026-06-30. Previous was 10-01-2024."
        dates = extractor._extract_dates(text)
        assert len(dates) >= 2
        assert any("15/03/2025" in d for d in dates)
        assert any("2026-06-30" in d for d in dates)

    def test_extract_aicte_id(self, extractor):
        text = "All India Council for Technical Education. AICTE ID: 1-9347281 approved."
        aicte_id = extractor._extract_aicte_id(text)
        assert aicte_id is not None
        assert "1-9347281" in aicte_id

    def test_extract_email(self, extractor):
        text = "Contact the principal at principal@college.edu.in or registrar@college.org"
        emails = extractor._extract_email_addresses(text)
        assert "principal@college.edu.in" in emails
        assert "registrar@college.org" in emails

    def test_extract_phone(self, extractor):
        text = "Helpline number: 9876543210 or call office +91 9123456780"
        phones = extractor._extract_phone_numbers(text)
        assert len(phones) >= 1
        assert any("9876543210" in p for p in phones)

    def test_extract_amounts(self, extractor):
        text = "FDR deposited: Rs. 50,00,000 (INR 50 lakh) in SBI branch."
        amounts = extractor._extract_amounts(text)
        assert len(amounts) >= 1
        assert amounts[0]["amount"] > 0

    def test_extract_pincode(self, extractor):
        text = "Located at Kukas, Jaipur, Rajasthan, Pin Code: 302028."
        pin = extractor._extract_pincode(text)
        assert pin == "302028"

    def test_extract_fields_general(self, extractor):
        text = """
        Name of Institution: Maharaja Institute of Technology
        AICTE ID: 1-9347281
        Date: 15/03/2025
        Contact: admin@mit.edu.in
        Pin Code: 302028
        Total FDR: Rs. 25,00,000
        """
        fields = extractor.extract_fields(text, "AFFIDAVIT")
        assert isinstance(fields, dict)
        assert "dates" in fields
        assert "aicte_id" in fields
        assert fields["aicte_id"] == "1-9347281"
