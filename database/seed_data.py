"""
Seed Data Module.

Populates the SQLite database with realistic synthetic data
for demonstration and testing purposes.
"""

import hashlib
import json
import sqlite3
from datetime import datetime, timedelta
import random

from database.db import DatabaseManager
from config.settings import (
    ApplicationCategories, DocumentTypes, VerificationStatuses,
    ValidationStatuses, DATABASE_PATH
)


def seed_database(db_path: str = DATABASE_PATH) -> None:
    """
    Populate the database with comprehensive synthetic data.

    Args:
        db_path: Path to the SQLite database file.
    """
    db = DatabaseManager(db_path)
    db.init_db()

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Check if already seeded
    cursor.execute("SELECT COUNT(*) FROM institutions")
    if cursor.fetchone()[0] > 0:
        conn.close()
        return

    # ── Users ──────────────────────────────────────────────────────────
    users = [
        ("admin", hashlib.sha256("admin123".encode()).hexdigest(),
         "Dr. Rajesh Kumar", "ADMIN", "AICTE HQ"),
        ("reviewer1", hashlib.sha256("review123".encode()).hexdigest(),
         "Priya Sharma", "REVIEWER", "Regional Office - North"),
        ("reviewer2", hashlib.sha256("review123".encode()).hexdigest(),
         "Ankit Verma", "REVIEWER", "Regional Office - South"),
        ("viewer1", hashlib.sha256("viewer123".encode()).hexdigest(),
         "Sneha Patel", "VIEWER", "Documentation Cell"),
    ]
    cursor.executemany(
        "INSERT INTO users (username, password_hash, full_name, role, department, is_active, created_at) "
        "VALUES (?, ?, ?, ?, ?, 1, ?)",
        [(u[0], u[1], u[2], u[3], u[4], datetime.now().isoformat()) for u in users],
    )

    # ── Institutions ───────────────────────────────────────────────────
    institutions = [
        ("Maharaja Institute of Technology", "1-9347281", "Rajasthan Technical University",
         "Rajasthan", "Jaipur", "NH-48, Kukas, Jaipur - 302028", 2005),
        ("Srinivasa College of Engineering", "2-4821095", "Anna University",
         "Tamil Nadu", "Chennai", "Perangalathur, Chennai - 600127", 1998),
        ("Northern Institute of Engineering & Technology", "1-7362810", "Dr. APJ Abdul Kalam Technical University",
         "Uttar Pradesh", "Lucknow", "Sitapur Road, Lucknow - 226020", 2010),
        ("Deccan School of Management", "3-5193724", "Osmania University",
         "Telangana", "Hyderabad", "Begumpet, Hyderabad - 500016", 2008),
        ("Western College of Pharmacy", "4-6284015", "Mumbai University",
         "Maharashtra", "Pune", "Wakad, Pune - 411057", 2012),
    ]

    inst_ids = []
    for inst in institutions:
        cursor.execute(
            "INSERT INTO institutions (name, aicte_id, university, state, city, address, established_year, status, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, 'ACTIVE', ?, ?)",
            (*inst, datetime.now().isoformat(), datetime.now().isoformat()),
        )
        inst_ids.append(cursor.lastrowid)

    # ── Applications ───────────────────────────────────────────────────
    applications_data = [
        (inst_ids[0], ApplicationCategories.EOA, "2025-26", "UNDER_REVIEW",
         "2025-03-15", "reviewer1", "Initial review pending"),
        (inst_ids[0], ApplicationCategories.ADD_PROGRAMME, "2025-26", "SUBMITTED",
         "2025-04-01", None, None),
        (inst_ids[1], ApplicationCategories.EOA, "2025-26", "APPROVED",
         "2025-02-20", "admin", "All documents verified"),
        (inst_ids[1], ApplicationCategories.EOA, "2024-25", "APPROVED",
         "2024-03-10", "admin", "Approved after inspection"),
        (inst_ids[2], ApplicationCategories.NEW_INSTITUTION, "2025-26", "UNDER_REVIEW",
         "2025-05-10", "reviewer2", "Awaiting land document verification"),
        (inst_ids[2], ApplicationCategories.EOA, "2024-25", "REJECTED",
         "2024-02-28", "admin", "Faculty shortage, non-compliance on infrastructure"),
        (inst_ids[3], ApplicationCategories.EOA, "2025-26", "SUBMITTED",
         "2025-06-01", None, None),
        (inst_ids[4], ApplicationCategories.CHANGE_OF_SITE, "2025-26", "UNDER_REVIEW",
         "2025-04-20", "reviewer1", "Site inspection scheduled"),
    ]

    app_ids = []
    for app_data in applications_data:
        cursor.execute(
            "INSERT INTO applications (institution_id, category, academic_year, status, submitted_at, reviewed_by, review_notes, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (*app_data, datetime.now().isoformat(), datetime.now().isoformat()),
        )
        app_ids.append(cursor.lastrowid)

    # ── Documents ──────────────────────────────────────────────────────
    doc_types = [
        DocumentTypes.AFFIDAVIT, DocumentTypes.NOC, DocumentTypes.ACCREDITATION_CERT,
        DocumentTypes.FIRE_SAFETY_CERT, DocumentTypes.LAND_DOCUMENT, DocumentTypes.BUILDING_PLAN,
        DocumentTypes.FACULTY_LIST, DocumentTypes.FINANCIAL_STATEMENT, DocumentTypes.EOA_CERTIFICATE,
        DocumentTypes.UNDERTAKING,
    ]

    documents_data = []
    for app_id in app_ids:
        # Each application gets a random subset of documents
        selected_docs = random.sample(doc_types, k=random.randint(5, 10))
        for doc_type in selected_docs:
            filename = f"{doc_type.lower().replace('_', '-')}-{app_id}-{random.randint(1000,9999)}.pdf"
            file_hash = hashlib.sha256(f"{filename}{app_id}".encode()).hexdigest()
            upload_date = (datetime(2025, 1, 1) + timedelta(days=random.randint(0, 180))).strftime("%Y-%m-%d")
            expiry_date = (datetime(2025, 1, 1) + timedelta(days=random.randint(200, 730))).strftime("%Y-%m-%d")

            # Some documents should be expired
            if random.random() < 0.15:
                expiry_date = (datetime(2024, 1, 1) + timedelta(days=random.randint(0, 200))).strftime("%Y-%m-%d")

            ocr_text = _generate_sample_ocr_text(doc_type, app_id)
            extracted = json.dumps({"doc_type": doc_type, "auto_extracted": True})
            status = random.choice([
                ValidationStatuses.VALID, ValidationStatuses.VALID, ValidationStatuses.VALID,
                ValidationStatuses.INVALID, ValidationStatuses.INCOMPLETE,
                ValidationStatuses.EXPIRED, ValidationStatuses.PENDING_REVIEW,
            ])
            anomaly_score = round(random.uniform(0.0, 0.3), 2) if status == ValidationStatuses.VALID else round(random.uniform(0.3, 0.9), 2)

            documents_data.append((
                app_id, doc_type, filename, f"uploads/{filename}", file_hash,
                upload_date, expiry_date, ocr_text, extracted, status, anomaly_score, ""
            ))

    doc_ids = []
    for doc in documents_data:
        cursor.execute(
            "INSERT INTO documents (application_id, doc_type, filename, file_path, file_hash, upload_date, expiry_date, ocr_text, extracted_data, validation_status, anomaly_score, notes) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            doc,
        )
        doc_ids.append(cursor.lastrowid)

    # ── Validation Results ─────────────────────────────────────────────
    validation_rules = [
        ("REQUIRED_DOCUMENT_CHECK", "DOCUMENT", "Checks if all required documents are uploaded"),
        ("FIELD_COMPLETENESS", "FIELD", "Checks if all mandatory fields are filled"),
        ("DOCUMENT_EXPIRY_CHECK", "DOCUMENT", "Checks if any documents have expired"),
        ("INSTITUTION_NAME_CONSISTENCY", "CONSISTENCY", "Cross-checks institution name across documents"),
        ("AICTE_ID_CONSISTENCY", "CONSISTENCY", "Verifies AICTE ID is consistent across documents"),
        ("DATE_LOGIC_CHECK", "DATE", "Validates logical consistency of dates"),
        ("FACULTY_RATIO_CHECK", "COMPLIANCE", "Checks faculty-student ratio"),
        ("INFRASTRUCTURE_AREA_CHECK", "COMPLIANCE", "Checks land and built-up area requirements"),
    ]

    for doc_id in doc_ids:
        num_rules = random.randint(3, 6)
        selected_rules = random.sample(validation_rules, k=min(num_rules, len(validation_rules)))
        for rule_name, rule_cat, detail_tmpl in selected_rules:
            status = random.choice(["PASS", "PASS", "PASS", "FAIL", "WARNING"])
            confidence = round(random.uniform(0.7, 1.0), 2)
            cursor.execute(
                "INSERT INTO validation_results (document_id, application_id, rule_name, rule_category, status, details, evidence, confidence_score, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (doc_id, documents_data[doc_ids.index(doc_id)][0], rule_name, rule_cat,
                 status, detail_tmpl, f"Automated check on document #{doc_id}", confidence,
                 datetime.now().isoformat()),
            )

    # ── Anomaly Alerts ─────────────────────────────────────────────────
    anomaly_types = [
        ("METADATA_INCONSISTENCY", "Creation date newer than modification date", "HIGH"),
        ("DUPLICATE_CONTENT", "Document text >90% similar to another submission", "CRITICAL"),
        ("SUSPICIOUS_ALTERATION", "Potential text editing detected in PDF producer metadata", "HIGH"),
        ("DATE_ANOMALY", "Issue date appears to be in the future", "MEDIUM"),
        ("FONT_INCONSISTENCY", "Multiple font types detected suggesting edits", "MEDIUM"),
        ("MISMATCHED_IDENTIFIER", "AICTE ID in document differs from application", "HIGH"),
        ("IRREGULAR_FORMAT", "Document format inconsistent with expected template", "LOW"),
        ("MISSING_SIGNATURE", "Expected signature/stamp area appears blank", "MEDIUM"),
        ("EXPIRED_VALIDITY", "Document validity period has expired", "HIGH"),
        ("QUALITY_ISSUE", "Document image quality too low for reliable OCR", "LOW"),
    ]

    anomaly_doc_ids = random.sample(doc_ids, k=min(15, len(doc_ids)))
    for doc_id in anomaly_doc_ids:
        atype, desc, severity = random.choice(anomaly_types)
        is_resolved = random.choice([0, 0, 0, 1])
        cursor.execute(
            "INSERT INTO anomaly_alerts (document_id, application_id, alert_type, severity, description, evidence, is_resolved, resolved_by, resolved_at, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (doc_id, documents_data[doc_ids.index(doc_id)][0], atype, severity, desc,
             f"Automated analysis flagged document #{doc_id}",
             is_resolved, "admin" if is_resolved else None,
             datetime.now().isoformat() if is_resolved else None,
             datetime.now().isoformat()),
        )

    # ── Verification Records ──────────────────────────────────────────
    verification_sources = [
        ("NBA Portal", "API", VerificationStatuses.VERIFIED),
        ("NAAC Database", "PORTAL", VerificationStatuses.VERIFIED),
        ("State Fire Department", "PORTAL", VerificationStatuses.VERIFICATION_PENDING),
        ("Land Registry Portal", "API", VerificationStatuses.MISMATCH_DETECTED),
        ("University Affiliation Portal", "API", VerificationStatuses.VERIFIED),
        ("AICTE Internal Records", "DATABASE", VerificationStatuses.VERIFIED),
        ("Sub-Registrar Office", "PORTAL", VerificationStatuses.SOURCE_UNAVAILABLE),
        ("Digital Locker / DigiLocker", "API", VerificationStatuses.VERIFIED),
        ("State Government Portal", "PORTAL", VerificationStatuses.MANUAL_REVIEW_REQUIRED),
        ("QR Code Verification", "QR_CODE", VerificationStatuses.VERIFIED),
    ]

    verify_doc_ids = random.sample(doc_ids, k=min(12, len(doc_ids)))
    for doc_id in verify_doc_ids:
        src_name, src_type, ver_status = random.choice(verification_sources)
        cursor.execute(
            "INSERT INTO verification_records (document_id, source_name, source_type, verification_status, submitted_data, source_response, verified_at, notes) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (doc_id, src_name, src_type, ver_status,
             json.dumps({"doc_id": doc_id, "type": "auto"}),
             json.dumps({"status": ver_status, "source": src_name}),
             datetime.now().isoformat(),
             f"Verification via {src_name}"),
        )

    # ── Compliance Checks ─────────────────────────────────────────────
    compliance_items = [
        ("Affidavit Submission", "DOCUMENT", "Required", "COMPLIANT"),
        ("NOC from State Government", "DOCUMENT", "Required", "COMPLIANT"),
        ("Fire Safety Certificate", "DOCUMENT", "Required", "NON_COMPLIANT"),
        ("Land Area Requirement", "INFRASTRUCTURE", "2.5 acres", "COMPLIANT"),
        ("Built-up Area", "INFRASTRUCTURE", "5000 sq.ft per programme", "PARTIAL"),
        ("Library Books Count", "INFRASTRUCTURE", "Min 5000 titles", "COMPLIANT"),
        ("Computer Labs", "INFRASTRUCTURE", "Min 1 per programme", "COMPLIANT"),
        ("Faculty-Student Ratio", "FACULTY", "1:15", "NON_COMPLIANT"),
        ("PhD Faculty Percentage", "FACULTY", "Min 20%", "PARTIAL"),
        ("FDR Amount", "FINANCIAL", "Rs. 25 Lakh", "COMPLIANT"),
        ("Corpus Fund", "FINANCIAL", "Rs. 50 Lakh", "COMPLIANT"),
        ("NBA Accreditation", "ACCREDITATION", "Recommended", "NOT_APPLICABLE"),
        ("NAAC Grade", "ACCREDITATION", "Min B+", "COMPLIANT"),
        ("Anti-Ragging Committee", "COMPLIANCE", "Required", "COMPLIANT"),
        ("Grievance Redressal", "COMPLIANCE", "Required", "COMPLIANT"),
        ("TER Payment Status", "FINANCIAL", "Paid", "COMPLIANT"),
        ("Internal Quality Assurance", "COMPLIANCE", "Required", "PARTIAL"),
    ]

    for app_id in app_ids:
        selected_items = random.sample(compliance_items, k=random.randint(10, len(compliance_items)))
        for item_name, category, required_val, _ in selected_items:
            status = random.choice(["COMPLIANT", "COMPLIANT", "COMPLIANT", "NON_COMPLIANT", "PARTIAL", "NOT_APPLICABLE"])
            actual_val = required_val if status == "COMPLIANT" else ("Partial" if status == "PARTIAL" else "Missing")
            cursor.execute(
                "INSERT INTO compliance_checks (application_id, checklist_name, check_item, category, status, required_value, actual_value, evidence, notes, checked_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (app_id, "EoA Checklist 2025-26", item_name, category, status,
                 required_val, actual_val, f"Auto-checked for application #{app_id}", "",
                 datetime.now().isoformat()),
            )

    # ── Audit Trail ───────────────────────────────────────────────────
    audit_actions = [
        ("APPLICATION_SUBMITTED", "admin", "Application submitted for review"),
        ("DOCUMENT_UPLOADED", "admin", "Document uploaded and classified"),
        ("VALIDATION_RUN", "reviewer1", "Automated validation executed"),
        ("ANOMALY_DETECTED", "system", "Anomaly detection flagged issues"),
        ("VERIFICATION_INITIATED", "reviewer1", "Document verification started"),
        ("VERIFICATION_COMPLETED", "system", "Verification completed via API"),
        ("COMPLIANCE_CHECK_RUN", "reviewer2", "Compliance check executed"),
        ("REVIEW_NOTE_ADDED", "reviewer1", "Reviewer added observation notes"),
        ("STATUS_UPDATED", "admin", "Application status changed"),
        ("ALERT_RESOLVED", "admin", "Anomaly alert marked as resolved"),
        ("DOCUMENT_REPLACED", "admin", "Resubmission accepted"),
        ("INSPECTION_SCHEDULED", "admin", "Physical inspection scheduled"),
    ]

    for app_id in app_ids:
        num_entries = random.randint(4, 10)
        selected_actions = [random.choice(audit_actions) for _ in range(num_entries)]
        for i, (action, actor, detail) in enumerate(selected_actions):
            ts = (datetime(2025, 1, 1) + timedelta(days=random.randint(0, 180), hours=random.randint(0, 23))).isoformat()
            cursor.execute(
                "INSERT INTO audit_trail (application_id, action, actor, details, ip_address, timestamp) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (app_id, action, actor, f"{detail} (App #{app_id})",
                 f"192.168.1.{random.randint(10, 250)}", ts),
            )

    conn.commit()
    conn.close()


def _generate_sample_ocr_text(doc_type: str, app_id: int) -> str:
    """Generate realistic sample OCR text for a given document type."""
    templates = {
        DocumentTypes.AFFIDAVIT: (
            "AFFIDAVIT\n\nI, Dr. Ramesh Chandra, Director of the institution, "
            "do hereby solemnly affirm and declare that:\n"
            "1. The information provided in the application is true and correct.\n"
            "2. The institution is compliant with all AICTE norms.\n"
            "3. No facts have been concealed.\n\n"
            "AICTE ID: 1-9347281\n"
            "Date: 15/03/2025\n"
            f"Application Ref: APP-{app_id}-2025\n\n"
            "Signed before Notary Public\nStamp Paper: Rs. 100/-"
        ),
        DocumentTypes.NOC: (
            "NO OBJECTION CERTIFICATE\n\n"
            "Government of Rajasthan\nDepartment of Technical Education\n\n"
            "This is to certify that the State Government has No Objection "
            "to the continuation/establishment of the institution.\n\n"
            "Institution: Maharaja Institute of Technology\n"
            "AICTE ID: 1-9347281\n"
            "Date: 10/01/2025\nValid until: 31/03/2026\n"
            "Ref No: NOC/RJ/2025/1234"
        ),
        DocumentTypes.ACCREDITATION_CERT: (
            "NATIONAL BOARD OF ACCREDITATION (NBA)\n"
            "ACCREDITATION CERTIFICATE\n\n"
            "This is to certify that the following programmes of the institution "
            "have been accredited by NBA:\n"
            "1. B.Tech in Computer Science - Tier I\n"
            "2. B.Tech in Mechanical Engineering - Tier II\n\n"
            "Grade: A\nCGPA: 3.45\n"
            "Valid until: 30/06/2027\n"
            "Certificate No: NBA/2024/3456"
        ),
        DocumentTypes.FIRE_SAFETY_CERT: (
            "FIRE SAFETY CERTIFICATE\n\n"
            "Office of the Chief Fire Officer\nJaipur Municipal Corporation\n\n"
            "Certificate No: FSC/JMC/2025/789\n"
            "Date: 05/02/2025\n\n"
            "This is to certify that the premises of Maharaja Institute of Technology "
            "at NH-48, Kukas, Jaipur has been inspected and found compliant with "
            "fire safety norms.\n\nValid until: 04/02/2026"
        ),
        DocumentTypes.LAND_DOCUMENT: (
            "SALE DEED / TITLE DOCUMENT\n\n"
            "Sub-Registrar Office, Jaipur\n"
            "Registration No: REG/JP/2005/4567\n\n"
            "Property Details:\n"
            "Land Area: 5.2 acres\n"
            "Survey No: 145/A, Village Kukas\n"
            "District: Jaipur, State: Rajasthan\n"
            "Pin Code: 302028\n\n"
            "Registered Owner: Maharaja Educational Trust\n"
            "Date: 20/06/2005"
        ),
        DocumentTypes.BUILDING_PLAN: (
            "SANCTIONED BUILDING PLAN\n\n"
            "Jaipur Development Authority\n"
            "Approval No: BPA/JDA/2005/890\n\n"
            "Built-up Area: 52,000 sq.ft\n"
            "Plinth Area: 48,000 sq.ft\n"
            "Number of Floors: 4\n\n"
            "Architect: Ar. Suresh Mehta (COA Reg: CA/2001/12345)\n"
            "Approved Date: 15/08/2005"
        ),
        DocumentTypes.FACULTY_LIST: (
            "FACULTY LIST - ACADEMIC YEAR 2025-26\n\n"
            "S.No  Name                  Designation           Qualification  Department\n"
            "1     Dr. Anil Kumar        Professor             Ph.D          Computer Science\n"
            "2     Dr. Sunita Verma      Associate Professor   Ph.D          Mechanical\n"
            "3     Mr. Rajiv Singh       Assistant Professor   M.Tech        Civil\n"
            "4     Dr. Meena Sharma      HOD                   Ph.D          Electronics\n"
            "5     Ms. Pooja Gupta       Assistant Professor   M.Tech        IT\n\n"
            "Total Faculty: 45\nPhD Faculty: 18 (40%)\n"
            "Student-Faculty Ratio: 1:15"
        ),
        DocumentTypes.FINANCIAL_STATEMENT: (
            "AUDITED FINANCIAL STATEMENT\nFinancial Year: 2024-25\n\n"
            "Certified by: CA Mukesh Agarwal (FCA-123456)\n\n"
            "Fixed Deposit (FDR): Rs. 1,25,00,000 (Rs. 1.25 Crore)\n"
            "Corpus Fund: Rs. 75,00,000 (Rs. 75 Lakh)\n"
            "Annual Revenue: Rs. 8,50,00,000\n"
            "Annual Expenditure: Rs. 7,20,00,000\n"
            "Surplus: Rs. 1,30,00,000\n\n"
            "Bank: State Bank of India, Jaipur Branch\n"
            "Date: 30/06/2025"
        ),
        DocumentTypes.EOA_CERTIFICATE: (
            "ALL INDIA COUNCIL FOR TECHNICAL EDUCATION\n"
            "EXTENSION OF APPROVAL (EoA)\n\n"
            "F.No: AICTE/EOA/2024-25/1-9347281\n"
            "Academic Year: 2024-25\n\n"
            "Institution: Maharaja Institute of Technology\n"
            "AICTE ID: 1-9347281\n\n"
            "Approved Programmes:\n"
            "1. B.Tech Computer Science - Intake: 120 seats\n"
            "2. B.Tech Mechanical - Intake: 60 seats\n"
            "3. B.Tech Civil - Intake: 60 seats\n"
            "4. MBA - Intake: 60 seats\n\n"
            "Status: APPROVED\nDate: 01/07/2024"
        ),
        DocumentTypes.UNDERTAKING: (
            "UNDERTAKING\n\n"
            "I, Dr. Ramesh Chandra, Director, Maharaja Institute of Technology, "
            "hereby undertake and assure that:\n"
            "1. The institution shall comply with all AICTE norms and regulations.\n"
            "2. No additional intake beyond approved strength shall be admitted.\n"
            "3. All faculty appointments shall meet AICTE qualification criteria.\n"
            "4. Infrastructure development shall be completed as per timeline.\n\n"
            "Date: 15/03/2025\n"
            "Place: Jaipur\n"
            "Signature: Dr. Ramesh Chandra\n"
            "Contact: director@maharajait.edu.in\nPhone: +91-9876543210"
        ),
    }
    return templates.get(doc_type, f"Sample document text for {doc_type} (Application #{app_id})")


if __name__ == "__main__":
    seed_database()
    print("Database seeded successfully!")
