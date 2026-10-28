"""
Tests for Comparison Engine module.

Validates RapidFuzz string matching, cross-document comparison,
field-level comparison, duplicate detection, and mismatch reports.
"""

import os
import sys
import pytest
import pandas as pd

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from modules.comparison_engine import ComparisonEngine


class TestComparisonEngine:
    """Test suite for ComparisonEngine."""

    @pytest.fixture
    def engine(self):
        return ComparisonEngine()

    def test_fuzzy_match_exact(self, engine):
        score, is_match = engine.fuzzy_match("Maharaja Institute of Technology", "Maharaja Institute of Technology")
        assert score == 100.0
        assert is_match is True

    def test_fuzzy_match_similar(self, engine):
        score, is_match = engine.fuzzy_match("Maharaja Inst of Tech", "Maharaja Institute of Technology", threshold=70.0)
        assert score > 70.0
        assert is_match is True

    def test_fuzzy_match_different(self, engine):
        score, is_match = engine.fuzzy_match("Anna University Chennai", "Jaipur Municipal Corporation", threshold=80.0)
        assert score < 50.0
        assert is_match is False

    def test_compare_fields(self, engine):
        submitted = {"institution_name": "Maharaja Institute of Tech", "aicte_id": "1-9347281", "state": "Rajasthan"}
        reference = {"institution_name": "Maharaja Institute of Technology", "aicte_id": "1-9347281", "state": "Rajasthan"}
        df = engine.compare_fields(submitted, reference)
        assert isinstance(df, pd.DataFrame)
        assert "field_name" in df.columns
        assert "match_score" in df.columns
        assert "status" in df.columns
        assert len(df) == 3

    def test_find_duplicates(self, engine):
        docs = [
            {"filename": "doc1.pdf", "text": "This is a detailed sworn affidavit for AICTE approval 2026."},
            {"filename": "doc2.pdf", "text": "This is a detailed sworn affidavit for AICTE approval 2026."},
            {"filename": "doc3.pdf", "text": "Completely unrelated fire safety inspection document."},
        ]
        dups = engine.find_duplicates(docs, threshold=85.0)
        assert isinstance(dups, list)
        assert len(dups) >= 1
        assert dups[0]["similarity"] >= 85.0

    def test_generate_mismatch_report(self, engine):
        submitted = {"name": "Test Col", "id": "1-111"}
        reference = {"name": "Test College", "id": "1-222"}
        df = engine.compare_fields(submitted, reference)
        report = engine.generate_mismatch_report(df)
        assert isinstance(report, dict)
        assert "total_fields" in report
        assert "matches" in report
        assert "mismatches" in report
