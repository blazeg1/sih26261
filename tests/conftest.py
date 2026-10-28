"""
Pytest configuration and shared fixtures for the AICTE Validation Platform test suite.

Provides reusable fixtures for:
- Sample OCR text from affidavits
- Institution, application, and document data dictionaries
- Temporary SQLite databases
- Synthetic test images
- Checklist file paths
"""

import os
import sys
import tempfile
import shutil
from datetime import datetime, timedelta
from typing import Generator, Dict, Any

import pytest
import numpy as np

# ---------------------------------------------------------------------------
# Path setup — ensure project root is importable regardless of invocation dir
# ---------------------------------------------------------------------------
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


# ---------------------------------------------------------------------------
# Helper: check Tesseract availability
# ---------------------------------------------------------------------------
def _tesseract_available() -> bool:
    """Return True if Tesseract OCR binary is reachable."""
    try:
        import pytesseract
        pytesseract.get_tesseract_version()
        return True
    except Exception:
        return False


# Expose as a pytest marker helper
requires_tesseract = pytest.mark.skipif(
    not _tesseract_available(),
    reason="Tesseract OCR is not installed or not on PATH",
)


# =====================================================================
# Fixture: sample_ocr_text
# =====================================================================
@pytest.fixture
def sample_ocr_text() -> str:
    """Realistic OCR-extracted text from an AICTE affidavit document."""
    return (
        "AFFIDAVIT\n\n"
        "I, Dr. Rajesh Kumar Sharma, S/o Shri Mohan Lal Sharma, aged about 58 years, "
        "residing at 45, Civil Lines, Jaipur, Rajasthan - 302006, do hereby solemnly "
        "affirm and declare as under:\n\n"
        "1. That I am the Chairman/Director of ABC Institute of Technology "
        "(AICTE ID: 1-9234567890), situated at Plot No. 12, RIICO Industrial Area, "
        "Sitapura, Jaipur, Rajasthan - 302022.\n\n"
        "2. That the institution was established in the year 2005 and has been "
        "granted approval by AICTE since 2005-06 for conducting the following "
        "technical programmes:\n"
        "   a) B.Tech in Computer Science & Engineering - Intake 120\n"
        "   b) B.Tech in Electronics & Communication Engineering - Intake 60\n"
        "   c) B.Tech in Mechanical Engineering - Intake 60\n"
        "   d) MBA - Intake 60\n\n"
        "3. That the total built-up area of the institution is 25,000 sq. meters "
        "on a land area of 5.2 acres.\n\n"
        "4. That the institution has adequate infrastructure, laboratory facilities, "
        "library with 15,000 books, and qualified faculty as per AICTE norms.\n\n"
        "5. That the institution has a student-faculty ratio of 15:1 and employs "
        "45 full-time faculty members, of which 12 hold Ph.D. degrees.\n\n"
        "6. That all information furnished in the application dated 15/03/2024 for "
        "Extension of Approval (EOA) for the academic year 2024-25 is true and "
        "correct to the best of my knowledge and belief.\n\n"
        "Date: 15/03/2024\n"
        "Place: Jaipur\n\n"
        "Deponent\n"
        "Dr. Rajesh Kumar Sharma\n"
        "Chairman, ABC Institute of Technology\n\n"
        "Verified at Jaipur on this 15th day of March, 2024.\n"
        "Contact: director@abctech.edu.in | Phone: +91-9876543210\n"
    )


# =====================================================================
# Fixture: sample_institution_data
# =====================================================================
@pytest.fixture
def sample_institution_data() -> Dict[str, Any]:
    """Dictionary representing a sample AICTE-registered institution."""
    return {
        "institution_id": "INST-2024-001",
        "name": "ABC Institute of Technology",
        "aicte_id": "1-9234567890",
        "address": "Plot No. 12, RIICO Industrial Area, Sitapura, Jaipur",
        "city": "Jaipur",
        "state": "Rajasthan",
        "pincode": "302022",
        "institution_type": "Private-Self Financing",
        "established_year": 2005,
        "website": "https://www.abctech.edu.in",
        "email": "director@abctech.edu.in",
        "phone": "+91-9876543210",
        "total_intake": 300,
        "land_area_acres": 5.2,
        "built_up_area_sqm": 25000,
        "total_faculty": 45,
        "faculty_with_phd": 12,
        "total_programmes": 4,
        "status": "Active",
    }


# =====================================================================
# Fixture: sample_application_data
# =====================================================================
@pytest.fixture
def sample_application_data() -> Dict[str, Any]:
    """Dictionary representing a sample EOA application."""
    return {
        "application_id": "APP-2024-001",
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
                "name": "B.Tech Electronics & Communication Engineering",
                "level": "UG",
                "intake": 60,
                "faculty_count": 8,
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
        "total_intake": 300,
        "total_faculty": 45,
        "faculty_with_phd": 12,
        "land_area_acres": 5.2,
        "built_up_area_sqm": 25000,
        "library_books": 15000,
        "student_faculty_ratio": "15:1",
        "documents_submitted": [
            "affidavit",
            "noc",
            "fire_safety",
            "faculty_list",
            "financial_statement",
            "land_document",
            "building_plan",
        ],
    }


# =====================================================================
# Fixture: sample_document_data
# =====================================================================
@pytest.fixture
def sample_document_data() -> Dict[str, Any]:
    """Dictionary representing a sample uploaded document."""
    return {
        "document_id": "DOC-2024-001",
        "application_id": "APP-2024-001",
        "document_type": "affidavit",
        "filename": "affidavit_abc_tech_2024.pdf",
        "upload_date": "2024-03-15",
        "file_size_kb": 256,
        "pages": 3,
        "status": "Verified",
        "ocr_confidence": 0.92,
        "metadata": {
            "author": "Dr. Rajesh Kumar Sharma",
            "creation_date": "2024-03-14",
            "modification_date": "2024-03-15",
            "producer": "Adobe Acrobat",
        },
        "extracted_fields": {
            "institution_name": "ABC Institute of Technology",
            "aicte_id": "1-9234567890",
            "date": "15/03/2024",
            "signatory": "Dr. Rajesh Kumar Sharma",
        },
    }


# =====================================================================
# Fixture: temp_db
# =====================================================================
@pytest.fixture
def temp_db() -> Generator[str, None, None]:
    """Create a temporary SQLite database, yield its path, and clean up."""
    tmp_dir = tempfile.mkdtemp(prefix="aicte_test_")
    db_path = os.path.join(tmp_dir, "test_aicte.db")
    yield db_path
    # Cleanup
    try:
        shutil.rmtree(tmp_dir, ignore_errors=True)
    except Exception:
        pass


# =====================================================================
# Fixture: sample_image
# =====================================================================
@pytest.fixture
def sample_image() -> np.ndarray:
    """Create a synthetic white image with black text drawn using OpenCV putText.

    Returns a BGR numpy array suitable for OCR testing.
    """
    import cv2

    # Create a white image (800x400, 3-channel BGR)
    img = np.ones((400, 800, 3), dtype=np.uint8) * 255

    # Draw text lines
    font = cv2.FONT_HERSHEY_SIMPLEX
    lines = [
        "AFFIDAVIT",
        "ABC Institute of Technology",
        "AICTE ID: 1-9234567890",
        "Date: 15/03/2024",
        "Jaipur, Rajasthan 302022",
    ]
    y_offset = 60
    for line in lines:
        cv2.putText(img, line, (30, y_offset), font, 0.9, (0, 0, 0), 2)
        y_offset += 60

    return img


# =====================================================================
# Fixture: blank_image
# =====================================================================
@pytest.fixture
def blank_image() -> np.ndarray:
    """Create a completely blank (white) image with no text."""
    return np.ones((200, 400, 3), dtype=np.uint8) * 255


# =====================================================================
# Fixture: checklist_path
# =====================================================================
@pytest.fixture
def checklist_path() -> str:
    """Return the absolute path to the EOA checklist JSON file."""
    path = os.path.join(PROJECT_ROOT, "config", "eoa_checklist.json")
    return path


# =====================================================================
# Fixture: sample_faculty_text
# =====================================================================
@pytest.fixture
def sample_faculty_text() -> str:
    """Sample text containing faculty information for extraction tests."""
    return (
        "Faculty List - ABC Institute of Technology\n\n"
        "S.No | Name | Designation | Qualification | Experience\n"
        "1 | Dr. Amit Verma | Professor | Ph.D. (CSE), M.Tech | 18 years\n"
        "2 | Dr. Priya Sharma | Associate Professor | Ph.D. (ECE), M.Tech | 14 years\n"
        "3 | Mr. Suresh Patel | Assistant Professor | M.Tech (ME) | 8 years\n"
        "4 | Dr. Kavita Singh | Professor | Ph.D. (MBA), MBA | 20 years\n"
        "5 | Ms. Neha Gupta | Assistant Professor | M.Tech (CSE) | 5 years\n"
        "6 | Dr. Rakesh Jain | Associate Professor | Ph.D. (ME), M.Tech | 12 years\n\n"
        "Total Faculty: 45\n"
        "Ph.D. Holders: 12\n"
        "Student-Faculty Ratio: 15:1\n"
    )


# =====================================================================
# Fixture: sample_financial_text
# =====================================================================
@pytest.fixture
def sample_financial_text() -> str:
    """Sample financial statement text for extraction and classification tests."""
    return (
        "FINANCIAL STATEMENT\n"
        "ABC Institute of Technology\n"
        "For the Financial Year 2023-24\n\n"
        "INCOME\n"
        "Tuition Fees: Rs. 4,50,00,000\n"
        "Development Fees: Rs. 75,00,000\n"
        "Other Income: Rs. 12,50,000\n"
        "Total Income: Rs. 5,37,50,000\n\n"
        "EXPENDITURE\n"
        "Salaries & Wages: Rs. 3,20,00,000\n"
        "Infrastructure Maintenance: Rs. 45,00,000\n"
        "Library & Books: Rs. 15,00,000\n"
        "Laboratory Equipment: Rs. 25,00,000\n"
        "Administrative Expenses: Rs. 18,00,000\n"
        "Total Expenditure: Rs. 4,23,00,000\n\n"
        "Surplus: Rs. 1,14,50,000\n\n"
        "Audited by: M/s Sharma & Associates, Chartered Accountants\n"
        "Date: 30/06/2024\n"
    )
