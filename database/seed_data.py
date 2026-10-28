"""
Seed Data Module for AICTE Validation Platform (SIH 2026 - PS 26261).

Populates SQLite database with 15 synthetic applications (APP-2026-1042 to APP-2026-1056):
- 11 applications with known planted defects (expired cert, name mismatch, dual faculty, shrunk area, etc.)
- 4 clean applications (fully compliant controls)
"""

import os
import json
import sqlite3
import hashlib
from datetime import datetime, timedelta

from database.db import DatabaseManager
from config.settings import (
    ApplicationCategories, DocumentTypes, DATABASE_PATH, UPLOAD_DIR
)


# Definition of Ground Truth Planted Problems for SIH Evaluation Benchmark
PLANTED_GROUND_TRUTH = {
    1: {"case_id": "APP-2026-1042", "name": "Aryabhatta Institute of Technology", "is_clean": False, "planted_issue": "Expired Fire Safety NOC (2026-03-14) & ELA modification"},
    2: {"case_id": "APP-2026-1043", "name": "Vidyapeeth College of Engineering", "is_clean": False, "planted_issue": "Missing mandatory Affidavit in Format A"},
    3: {"case_id": "APP-2026-1044", "name": "Chanakya Technical Campus", "is_clean": False, "planted_issue": "Shrunk built-up area YoY (14,000 sqm down to 9,800 sqm)"},
    4: {"case_id": "APP-2026-1045", "name": "Bose Institute of Technology", "is_clean": False, "planted_issue": "Institution name mismatch across land title and application"},
    5: {"case_id": "APP-2026-1046", "name": "Saraswati Engineering Academy", "is_clean": False, "planted_issue": "Reused byte-identical Fire NOC from APP-1042"},
    6: {"case_id": "APP-2026-1047", "name": "Vikramshila Polytechnic", "is_clean": False, "planted_issue": "Severe Faculty-Student Ratio deficit (1:28 vs 1:15)"},
    7: {"case_id": "APP-2026-1048", "name": "Nalanda College of Engineering", "is_clean": False, "planted_issue": "Dual-institution faculty collision (Shares Professor with APP-1042)"},
    8: {"case_id": "APP-2026-1049", "name": "Takshashila Institute of Technology", "is_clean": False, "planted_issue": "Registered land lease duration < 30 years (only 14 years remaining)"},
    9: {"case_id": "APP-2026-1050", "name": "Kalinga Institute of Technology", "is_clean": False, "planted_issue": "Tampered PDF metadata (Producer Adobe Photoshop 2024)"},
    10: {"case_id": "APP-2026-1051", "name": "Maurya Institute of Management", "is_clean": False, "planted_issue": "Land survey number mismatch between deed (Khasra 999/X) and declared (492/1)"},
    11: {"case_id": "APP-2026-1052", "name": "Ashoka College of Engineering", "is_clean": False, "planted_issue": "Intake increase requested without required 50% NBA accreditation"},
    12: {"case_id": "APP-2026-1053", "name": "Ramanujan Institute of Advanced Tech", "is_clean": True, "planted_issue": "None (Clean Compliant Benchmark Application)"},
    13: {"case_id": "APP-2026-1054", "name": "Homi Bhabha Technical Campus", "is_clean": True, "planted_issue": "None (Clean Compliant Benchmark Application)"},
    14: {"case_id": "APP-2026-1055", "name": "Visvesvaraya College of Engineering", "is_clean": True, "planted_issue": "None (Clean Compliant Benchmark Application)"},
    15: {"case_id": "APP-2026-1056", "name": "APJ Abdul Kalam Institute of Tech", "is_clean": True, "planted_issue": "None (Clean Compliant Benchmark Application)"},
}


def seed_database(db_path: str = DATABASE_PATH, force: bool = False) -> None:
    """Populate database with 15 synthetic applications and evaluation ground truths."""
    db = DatabaseManager(db_path)
    db.init_db()

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    if not force:
        cursor.execute("SELECT COUNT(*) FROM applications")
        if cursor.fetchone()[0] >= 15:
            conn.close()
            return

    # Clear tables
    for tbl in ["users", "institutions", "applications", "documents",
                "validation_results", "anomaly_alerts", "verification_records",
                "compliance_checks", "audit_trail", "tasks"]:
        cursor.execute(f"DELETE FROM {tbl}")

    now_iso = datetime.now().isoformat()
    pwd_hash = hashlib.sha256("admin123".encode()).hexdigest()

    # 1. Users
    users = [
        ("admin", pwd_hash, "Dr. Rajeshwar Pant", "ADMIN", "Bureau of Approval & Regulatory Compliance"),
        ("rajeshwar.pant", pwd_hash, "Dr. Rajeshwar Pant", "ADMIN", "Bureau of Approval & Regulatory Compliance"),
        ("reviewer1", hashlib.sha256("review123".encode()).hexdigest(), "Smt. Sunita Sharma", "REVIEWER", "Northern Regional Office (NRO)"),
        ("viewer1", hashlib.sha256("viewer123".encode()).hexdigest(), "Shri Arvind Mehta", "VIEWER", "Documentation & Scrutiny Cell"),
    ]
    cursor.executemany(
        "INSERT INTO users (username, password_hash, full_name, role, department, is_active, created_at) "
        "VALUES (?, ?, ?, ?, ?, 1, ?)",
        [(u[0], u[1], u[2], u[3], u[4], now_iso) for u in users],
    )

    # 2. 15 Synthetic Institutions & Applications
    colleges = [
        (1, "Aryabhatta Institute of Technology", "1-3329182910", "AKTU", "Uttar Pradesh", "Greater Noida", "Knowledge Park III", 2010),
        (2, "Vidyapeeth College of Engineering", "1-4492019281", "AKTU", "Uttar Pradesh", "Ghaziabad", "NH-24 Bypass", 2012),
        (3, "Chanakya Technical Campus", "1-5501928374", "RGPV", "Madhya Pradesh", "Bhopal", "Airport Road", 2011),
        (4, "Bose Institute of Technology", "1-6619283741", "MAKAUT", "West Bengal", "Kolkata", "Salt Lake Sector V", 2008),
        (5, "Saraswati Engineering Academy", "1-7729384710", "SPPU", "Maharashtra", "Pune", "Hinjewadi Phase 2", 2014),
        (6, "Vikramshila Polytechnic", "1-8839201928", "SBTE", "Bihar", "Bhagalpur", "Station Road", 2015),
        (7, "Nalanda College of Engineering", "1-9948201923", "AKU", "Bihar", "Chandi", "Nalanda Highway", 2013),
        (8, "Takshashila Institute of Technology", "1-1059283741", "VTU", "Karnataka", "Bengaluru", "Electronic City", 2009),
        (9, "Kalinga Institute of Technology", "1-1169283742", "BPUT", "Odisha", "Bhubaneswar", "Infocity", 2011),
        (10, "Maurya Institute of Management", "1-1279283743", "DTE", "Rajasthan", "Jaipur", "Sitapura Industrial Area", 2016),
        (11, "Ashoka College of Engineering", "1-1389283744", "Anna University", "Tamil Nadu", "Chennai", "OMR Road", 2010),
        (12, "Ramanujan Institute of Advanced Tech", "1-1499283745", "JNTUH", "Telangana", "Hyderabad", "Gachibowli", 2007),
        (13, "Homi Bhabha Technical Campus", "1-1509283746", "GTU", "Gujarat", "Ahmedabad", "SG Highway", 2008),
        (14, "Visvesvaraya College of Engineering", "1-1619283747", "VTU", "Karnataka", "Mysuru", "Hunsur Road", 2006),
        (15, "APJ Abdul Kalam Institute of Tech", "1-1729283748", "AKTU", "Uttar Pradesh", "Lucknow", "Sitapur Road", 2011),
    ]

    for c in colleges:
        cursor.execute("""
            INSERT INTO institutions (id, name, aicte_id, university, state, city, address, established_year, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'ACTIVE', ?, ?)
        """, (c[0], c[1], c[2], c[3], c[4], c[5], c[6], c[7], now_iso, now_iso))

        # Application Category
        cat = ApplicationCategories.ADD_PROGRAMME if c[0] == 11 else ApplicationCategories.EOA
        stage = "UNDER_REVIEW" if c[0] <= 11 else "APPROVED"
        cursor.execute("""
            INSERT INTO applications (id, institution_id, category, academic_year, status, submitted_at, reviewed_by, review_notes, created_at, updated_at)
            VALUES (?, ?, ?, '2026-27', ?, ?, 'Dr. Rajeshwar Pant', 'Preliminary scrutiny initiated', ?, ?)
        """, (c[0], c[0], cat, stage, (datetime.now() - timedelta(days=c[0])).isoformat(), now_iso, now_iso))

        # Insert Standard Documents
        shared_hash = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        # Seed byte-duplicate in APP-1046 from APP-1042
        file_hash = shared_hash if c[0] in (1, 5) else hashlib.sha256(f"DOC_{c[0]}".encode()).hexdigest()

        # Fire NOC Expiry date (Expired for APP-1042)
        fire_exp = "2026-03-14" if c[0] == 1 else "2028-06-30"

        # Missing affidavit in APP-1043
        if c[0] != 2:
            cursor.execute("""
                INSERT INTO documents (application_id, doc_type, filename, file_path, file_hash, upload_date, expiry_date, validation_status, anomaly_score)
                VALUES (?, 'AFFIDAVIT', ?, 'uploads/affidavit.pdf', ?, '2026-03-20', '2028-06-30', 'VALID', 0.0)
            """, (c[0], f"{c[1].replace(' ', '_')}_Affidavit.pdf", file_hash))

        cursor.execute("""
            INSERT INTO documents (application_id, doc_type, filename, file_path, file_hash, upload_date, expiry_date, validation_status, anomaly_score)
            VALUES (?, 'FIRE_SAFETY_CERT', ?, 'uploads/fire_noc.pdf', ?, '2026-03-20', ?, ?, ?)
        """, (c[0], f"{c[1].replace(' ', '_')}_Fire_NOC.pdf", file_hash, fire_exp, 'MISMATCH_DETECTED' if c[0] == 1 else 'VALID', 0.85 if c[0] == 1 else 0.05))

        cursor.execute("""
            INSERT INTO documents (application_id, doc_type, filename, file_path, file_hash, upload_date, expiry_date, validation_status, anomaly_score)
            VALUES (?, 'LAND_DOCUMENT', ?, 'uploads/land_deed.pdf', ?, '2026-03-20', '2035-06-30', 'VALID', 0.0)
        """, (c[0], f"{c[1].replace(' ', '_')}_Land_Deed.pdf", hashlib.sha256(f"LAND_{c[0]}".encode()).hexdigest()))

        cursor.execute("""
            INSERT INTO documents (application_id, doc_type, filename, file_path, file_hash, upload_date, expiry_date, validation_status, anomaly_score)
            VALUES (?, 'FACULTY_LIST', ?, 'uploads/faculty.pdf', ?, '2026-03-20', '2027-06-30', 'VALID', 0.0)
        """, (c[0], f"{c[1].replace(' ', '_')}_Faculty_Roster.pdf", hashlib.sha256(f"FAC_{c[0]}".encode()).hexdigest()))

        cursor.execute("""
            INSERT INTO documents (application_id, doc_type, filename, file_path, file_hash, upload_date, expiry_date, validation_status, anomaly_score)
            VALUES (?, 'FINANCIAL_STATEMENT', ?, 'uploads/financial_audit.pdf', ?, '2026-03-20', '2027-03-31', 'VALID', 0.0)
        """, (c[0], f"{c[1].replace(' ', '_')}_Financial_Audit.pdf", hashlib.sha256(f"FIN_{c[0]}".encode()).hexdigest()))

    # Seed Initial Anomaly Alerts for Planted Problems
    alerts = [
        (1, "EXPIRED_FIRE_NOC", "CRITICAL", "Fire Safety NOC expired on 2026-03-14 (Confirmed by State Fire Portal query)", "Expiry Date: 14/03/2026 vs Scrutiny Date: 20/03/2026"),
        (1, "ELA_COMPRESSION_SPLICING", "HIGH", "Error Level Analysis detected altered compression around NOC expiry box", "ELA residual difference spike: 78 in date bounding box"),
        (2, "MISSING_MANDATORY_DOCUMENT", "HIGH", "Statutory Affidavit in Format A is missing from dossier submission", "Application Category: EOA | Affidavit Status: Not Uploaded"),
        (3, "SHRUNK_BUILTUP_AREA", "HIGH", "Instructional built-up area shrank by 4,200 sq.m YoY without Change of Site", "2025: 14,000 sqm vs 2026: 9,800 sqm (30% reduction)"),
        (4, "NAME_MISMATCH_LAND_DEED", "HIGH", "Institution name on registered land title differs from AICTE portal application", "Deed: 'Bose Memorial Society' vs App: 'Bose Institute of Technology'"),
        (5, "CROSS_INSTITUTION_FILE_REUSE", "CRITICAL", "Exact byte-identical Fire NOC uploaded by both Aryabhatta Institute and Saraswati Academy", "SHA-256 Collision across Inst #1 and Inst #5"),
        (6, "FACULTY_STUDENT_RATIO_DEFICIT", "HIGH", "Faculty student ratio is 1:28 exceeding maximum prescribed ceiling of 1:20", "Students: 840, Faculty: 30 (Shortfall: 26 faculty)"),
        (7, "DUAL_COLLEGE_FACULTY_APPOINTMENT", "CRITICAL", "Same faculty identifier claimed on roster at both Aryabhatta and Nalanda colleges", "Salted Hash: SHA256(salt)...4920"),
        (8, "LEASE_DURATION_DEFICIT", "HIGH", "Registered lease duration is 14 years, failing statutory minimum 30-year mandate", "Lease: 14 years remaining (APH Clause 1.4.2)"),
        (9, "PDF_METADATA_TAMPERING", "HIGH", "Document produced with Adobe Photoshop 2024 and modified 2 years after issuance", "Producer: Adobe Photoshop 2024 | Modified: 2026-03-20"),
        (10, "LAND_SURVEY_MISMATCH", "HIGH", "Survey number on Khasra deed (999/X) contradicts declared campus land (492/1)", "Deed Survey: 999/X vs Portal Survey: 492/1"),
        (11, "INTAKE_INCREASE_WITHOUT_NBA", "HIGH", "Application requests intake increase without mandatory 50% NBA accredited programs", "NBA Accredited Percentage: 0.0% (APH Clause 2.14.3)"),
    ]
    cursor.executemany("""
        INSERT INTO anomaly_alerts (application_id, alert_type, severity, description, evidence, is_resolved, created_at)
        VALUES (?, ?, ?, ?, ?, 0, ?)
    """, [(a[0], a[1], a[2], a[3], a[4], now_iso) for a in alerts])

    # Initial Audit Trail
    cursor.execute("""
        INSERT INTO audit_trail (application_id, action, actor, details, ip_address, timestamp)
        VALUES (1, 'DOSSIER_INITIALIZED', 'Dr. Rajeshwar Pant (ADMIN)', 'Seeded 15 synthetic applications for SIH 26261 evaluation', '127.0.0.1', ?)
    """, (now_iso,))

    conn.commit()
    conn.close()
