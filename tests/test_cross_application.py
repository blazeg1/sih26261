"""
Unit tests for Cross-Application Intelligence Module (modules/cross_application_intelligence.py).
Tests SHA-256 duplicate detection, dHash perceptual similarity, dual-college faculty hashing, and YoY consistency.
"""

import pytest
from PIL import Image
from modules.cross_application_intelligence import (
    compute_dhash,
    hamming_distance,
    hash_faculty_id,
    CrossApplicationIntelligence
)


@pytest.fixture
def cross_engine():
    return CrossApplicationIntelligence(salt="TEST_SALT_SIH")


def test_dhash_and_hamming():
    # Two identical images
    img1 = Image.new("RGB", (100, 100), color=(200, 200, 200))
    img2 = Image.new("RGB", (100, 100), color=(200, 200, 200))
    h1 = compute_dhash(img1)
    h2 = compute_dhash(img2)
    assert h1 == h2
    assert hamming_distance(h1, h2) == 0

    # Slightly modified image
    img3 = Image.new("RGB", (100, 100), color=(0, 0, 0))
    h3 = compute_dhash(img3)
    dist = hamming_distance(h1, h3)
    assert isinstance(dist, int)


def test_hash_faculty_id_privacy():
    raw_pan = "ABCDE1234F"
    masked = hash_faculty_id(raw_pan, salt="TEST_SALT_SIH")
    assert "...234F" in masked
    assert "ABCDE" not in masked  # Raw identifier is never stored plain
    assert len(masked) > 10


def test_byte_duplicate_detection(cross_engine):
    docs = [
        {"filename": "Fire_NOC.pdf", "file_hash": "aaaabbbb1111", "institution_id": 1, "institution_name": "College A"},
        {"filename": "Reused_NOC.pdf", "file_hash": "aaaabbbb1111", "institution_id": 2, "institution_name": "College B"},
        {"filename": "Unique_Doc.pdf", "file_hash": "ccccdddd2222", "institution_id": 1, "institution_name": "College A"}
    ]
    findings = cross_engine.detect_byte_duplicates(docs)
    assert len(findings) == 1
    assert findings[0]["severity"] == "CRITICAL"
    assert "College A" in findings[0]["reused_across"]
    assert "College B" in findings[0]["reused_across"]


def test_dual_college_faculty(cross_engine):
    roster_a = [
        {"name": "Dr. K. Sharma", "identifier": "PAN_849201", "designation": "Professor"}
    ]
    roster_b = [
        {"name": "Dr. K. Sharma", "identifier": "PAN_849201", "designation": "Associate Professor"}
    ]
    findings = cross_engine.detect_dual_college_faculty(roster_a, roster_b, "College A", "College B")
    assert len(findings) == 1
    assert findings[0]["severity"] == "CRITICAL"
    assert "PAN_849201"[-4:] in findings[0]["masked_identifier"]


def test_year_over_year_shrunk_area(cross_engine):
    current = {"built_up_area_sqm": 10500.0, "survey_number": "492/1"}
    prior = {"built_up_area_sqm": 14000.0, "survey_number": "492/1"}  # 3,500 sqm reduction (25%)

    findings = cross_engine.check_year_over_year_consistency(current, prior)
    assert len(findings) >= 1
    area_finding = next(f for f in findings if f["type"] == "Year-over-Year Built-up Area Reduction")
    assert area_finding["status"] == "Deficiency"
    assert "shrank" in area_finding["message"]
