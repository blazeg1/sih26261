"""
Seed Data Module for PRAMAAN Platform.

Populates SQLite database with comprehensive institutional records,
application dossiers (including Aryabhatta Institute APP-2026-1042),
tasks, verification records, infrastructure evidence, and audit logs.
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


def seed_database(db_path: str = DATABASE_PATH, force: bool = False) -> None:
    """Populate the database with PRAMAAN demo data."""
    db = DatabaseManager(db_path)
    db.init_db()

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    if not force:
        cursor.execute("SELECT COUNT(*) FROM institutions")
        if cursor.fetchone()[0] > 0:
            conn.close()
            return

    # Clear existing if force
    for tbl in ["users", "institutions", "applications", "documents",
                "validation_results", "anomaly_alerts", "verification_records",
                "compliance_checks", "audit_trail", "tasks", "infrastructure_evidence"]:
        cursor.execute(f"DELETE FROM {tbl}")

    now_iso = datetime.now().isoformat()
    pwd_hash = hashlib.sha256("admin123".encode()).hexdigest()

    # ── Users ──────────────────────────────────────────────────────────
    users = [
        ("rajeshwar.pant", pwd_hash, "Dr. Rajeshwar Pant", "ADMIN", "Bureau of Approval & Regulatory Compliance"),
        ("admin", pwd_hash, "Dr. Rajeshwar Pant", "ADMIN", "Bureau of Approval & Regulatory Compliance"),
        ("reviewer1", hashlib.sha256("review123".encode()).hexdigest(), "Priya Sharma", "REVIEWER", "Northern Regional Office"),
        ("reviewer2", hashlib.sha256("review123".encode()).hexdigest(), "Ankit Verma", "REVIEWER", "Southern Regional Office"),
        ("viewer1", hashlib.sha256("viewer123".encode()).hexdigest(), "Sneha Patel", "VIEWER", "Documentation Cell"),
    ]
    cursor.executemany(
        "INSERT INTO users (username, password_hash, full_name, role, department, is_active, created_at) "
        "VALUES (?, ?, ?, ?, ?, 1, ?)",
        [(u[0], u[1], u[2], u[3], u[4], now_iso) for u in users],
    )

    # ── Institutions ───────────────────────────────────────────────────
    institutions = [
        # 1. Aryabhatta Institute (Hero Case Dossier)
        ("Aryabhatta Institute of Technology", "1-2026-1042", "Delhi Technological University",
         "Delhi", "New Delhi", "Sector 22, Rohini, Institutional Area, New Delhi - 110085", 2008),
        # 2. Saraswati College (Deficiency / Rectification)
        ("Saraswati College of Engineering", "1-2026-1087", "University of Mumbai",
         "Maharashtra", "Navi Mumbai", "Plot No. 46, Sector 5, Kharghar, Navi Mumbai - 410210", 2004),
        # 3. Ramanujan Institute (Awaiting Review)
        ("Ramanujan Institute of Advanced Computing", "1-2026-1015", "Anna University",
         "Tamil Nadu", "Chennai", "IT Highway, OMR, Navalur, Chennai - 600130", 2011),
        # 4. Nalanda Global (Inspection Flagged EVC)
        ("Nalanda Global Institute of Technology", "1-2026-1099", "AKTU Lucknow",
         "Uttar Pradesh", "Greater Noida", "Knowledge Park III, Greater Noida - 201308", 2015),
        # 5. Maharaja Institute
        ("Maharaja Institute of Technology", "1-9347281", "Rajasthan Technical University",
         "Rajasthan", "Jaipur", "NH-48, Kukas, Jaipur - 302028", 2005),
        # 6. Srinivasa Engineering
        ("Srinivasa College of Engineering", "2-4821095", "Anna University",
         "Tamil Nadu", "Chennai", "Perangalathur, Chennai - 600127", 1998),
        # 7. Deccan School of Management
        ("Deccan School of Management", "3-5193724", "Osmania University",
         "Telangana", "Hyderabad", "Begumpet, Hyderabad - 500016", 2008),
        # 8. Western College of Pharmacy
        ("Western College of Pharmacy", "4-6284015", "Mumbai University",
         "Maharashtra", "Pune", "Wakad, Pune - 411057", 2012),
    ]

    inst_ids = []
    for inst in institutions:
        cursor.execute(
            "INSERT INTO institutions (name, aicte_id, university, state, city, address, established_year, status, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, 'ACTIVE', ?, ?)",
            (*inst, now_iso, now_iso),
        )
        inst_ids.append(cursor.lastrowid)

    # ── Applications ───────────────────────────────────────────────────
    # Exactly matching PRAMAAN operational triage numbers:
    # 12 Assigned Cases in Docket, 5 Awaiting Review, 1 Clarifications/Deficiency,
    # 5 High Attention (Statutory Discrepancies), 4 Inspection Flagged (EVC)
    applications_data = [
        # APP-1: Hero case dossier from screenshot
        (inst_ids[0], "EOA", "2026-27", "UNDER_REVIEW", "2026-03-15", "rajeshwar.pant", "Under Scrutiny — Fire NOC verification pending"),
        # APP-2: Rectification due
        (inst_ids[1], "EOA", "2026-27", "UNDER_REVIEW", "2026-03-12", "rajeshwar.pant", "Deficiency Notice Issued — Awaiting Institution Rectification"),
        # APP-3: Preliminary Scrutiny
        (inst_ids[2], "ADD_PROGRAMME", "2026-27", "UNDER_REVIEW", "2026-03-18", "rajeshwar.pant", "Preliminary Scrutiny in progress"),
        # APP-4: EVC Inspection Flagged
        (inst_ids[3], "NEW_INSTITUTION", "2026-27", "UNDER_REVIEW", "2026-03-05", "rajeshwar.pant", "Flagged for Physical EVC Inspection — Land discrepancy"),
        # APP-5: High attention EVC
        (inst_ids[4], "EOA", "2026-27", "UNDER_REVIEW", "2026-03-10", "rajeshwar.pant", "Faculty-student deficit >35% flagged"),
        # APP-6: Approved
        (inst_ids[5], "EOA", "2026-27", "APPROVED", "2026-02-15", "rajeshwar.pant", "Verified through DigiLocker & State Portal"),
        # APP-7: Approved
        (inst_ids[6], "EOA", "2026-27", "APPROVED", "2026-02-20", "rajeshwar.pant", "All statutory checklists compliant"),
        # APP-8: Submitted
        (inst_ids[7], "CHANGE_OF_SITE", "2026-27", "SUBMITTED", "2026-03-22", None, "Fresh submission in queue"),
        # APP-9: Under review
        (inst_ids[0], "ADD_PROGRAMME", "2026-27", "UNDER_REVIEW", "2026-03-20", "rajeshwar.pant", "M.Tech AI & Data Science approval request"),
        # APP-10: Clarification / Deficiency response received
        (inst_ids[2], "EOA", "2025-26", "UNDER_REVIEW", "2026-03-14", "rajeshwar.pant", "Clarification reply received from institution"),
        # APP-11: EVC inspection visit
        (inst_ids[3], "CHANGE_OF_SITE", "2026-27", "UNDER_REVIEW", "2026-03-01", "rajeshwar.pant", "EVC physical inspection visit scheduled"),
        # APP-12: High Attention discrepancy
        (inst_ids[4], "NEW_INSTITUTION", "2026-27", "UNDER_REVIEW", "2026-02-28", "rajeshwar.pant", "Suspicious alteration detected in Sanctioned Plan"),
    ]

    app_ids = []
    for app_data in applications_data:
        cursor.execute(
            "INSERT INTO applications (institution_id, category, academic_year, status, submitted_at, reviewed_by, review_notes, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (*app_data, now_iso, now_iso),
        )
        app_ids.append(cursor.lastrowid)

    # ── Actionable Tasks (Today's Triage Priorities) ───────────────────
    tasks_data = [
        (app_ids[0], "State Fire NOC API cross-check discrepancy", "CRITICAL", "2026-10-28", "PENDING", "rajeshwar.pant", "API returned MISMATCH on NOC ref number FSC/2026/892"),
        (app_ids[1], "Institution rectification verification dossier", "CRITICAL", "2026-10-28", "PENDING", "rajeshwar.pant", "Verify resubmitted affidavit and faculty appointment orders"),
        (app_ids[2], "NBA Tier-1 accreditation validity confirmation", "HIGH", "2026-10-29", "PENDING", "rajeshwar.pant", "Cross-verify accreditation period on NBA web portal API"),
        (app_ids[3], "Land deed boundary coordinates satellite cross-check", "HIGH", "2026-10-30", "PENDING", "rajeshwar.pant", "EVC team report requires verification against municipal masterplan"),
    ]
    for t in tasks_data:
        cursor.execute(
            "INSERT INTO tasks (application_id, title, priority, due_date, status, assigned_to, notes, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (*t, now_iso),
        )

    # ── Documents for Applications ─────────────────────────────────────
    doc_catalog = [
        (DocumentTypes.AFFIDAVIT, "affidavit_notarized.pdf", "VALID", 0.05),
        (DocumentTypes.FIRE_SAFETY_CERT, "fire_safety_noc.pdf", "ANOMALY_DETECTED", 0.78),
        (DocumentTypes.NOC, "state_government_noc.pdf", "VALID", 0.02),
        (DocumentTypes.ACCREDITATION_CERT, "nba_accreditation.pdf", "VALID", 0.12),
        (DocumentTypes.LAND_DOCUMENT, "land_deed_registry.pdf", "VALID", 0.08),
        (DocumentTypes.BUILDING_PLAN, "sanctioned_building_plan.pdf", "ANOMALY_DETECTED", 0.65),
        (DocumentTypes.FACULTY_LIST, "approved_faculty_list.pdf", "VALID", 0.15),
        (DocumentTypes.FINANCIAL_STATEMENT, "audited_ca_balance_sheet.pdf", "VALID", 0.04),
        (DocumentTypes.EOA_CERTIFICATE, "previous_eoa_letter.pdf", "VALID", 0.01),
        (DocumentTypes.UNDERTAKING, "anti_ragging_undertaking.pdf", "VALID", 0.02),
    ]

    all_doc_ids = []
    for a_id in app_ids:
        # Sample 5-9 documents per application
        for doc_type, fname_base, val_stat, anom_val in doc_catalog[:random.randint(6, 10)]:
            fname = f"{fname_base.split('.')[0]}_{a_id}.pdf"
            fhash = hashlib.sha256(f"{fname}{a_id}".encode()).hexdigest()
            up_date = "2026-03-15"
            exp_date = "2028-06-30"

            ocr_text = _generate_pramaan_ocr(doc_type, a_id)
            ext_data = json.dumps({
                "institution_name": "Aryabhatta Institute of Technology" if a_id == app_ids[0] else "Technical Institution",
                "aicte_id": "1-2026-1042" if a_id == app_ids[0] else f"1-{a_id * 111111}",
                "doc_type": doc_type,
                "verified_digital_signature": True,
            })

            cursor.execute(
                "INSERT INTO documents (application_id, doc_type, filename, file_path, file_hash, upload_date, expiry_date, ocr_text, extracted_data, validation_status, anomaly_score, notes) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (a_id, doc_type, fname, f"uploads/{fname}", fhash, up_date, exp_date, ocr_text, ext_data, val_stat, anom_val, "PRAMAAN Ingested"),
            )
            all_doc_ids.append((cursor.lastrowid, a_id, doc_type))

    # ── Source Verification Records (10 Active Checks) ────────────────
    sources = [
        ("DigiLocker Regulatory Vault", "API", VerificationStatuses.VERIFIED, "Official Digital Signature Validated"),
        ("State Fire Services Portal API", "API", VerificationStatuses.MISMATCH_DETECTED, "NOC reference number FSC/2026/892 expired 14 days ago"),
        ("NBA Accreditation Master DB", "API", VerificationStatuses.VERIFIED, "Tier-1 Accreditation Active till June 2028"),
        ("State Land Registry GIS Portal", "PORTAL", VerificationStatuses.VERIFIED, "Khasra 45/A title deed in name of Educational Trust"),
        ("Municipal Corporation Sanctions", "PORTAL", VerificationStatuses.MANUAL_REVIEW_REQUIRED, "Floor layout requires structural engineer vetting"),
        ("University Affiliation Portal", "API", VerificationStatuses.VERIFIED, "Affiliation renewed for academic year 2026-27"),
        ("DigiLocker Trustee e-Aadhaar", "API", VerificationStatuses.VERIFIED, "Deponent KYC verified"),
        ("Chartered Accountants Registry", "API", VerificationStatuses.VERIFIED, "UDIN 26189284CA validated on ICAI portal"),
        ("Ministry of Home Affairs FCRA", "API", VerificationStatuses.VERIFIED, "No statutory foreign contribution violation"),
        ("State Pollution Control Board", "PORTAL", VerificationStatuses.VERIFICATION_PENDING, "Effluent treatment certificate renewal in progress"),
    ]

    for idx, s in enumerate(sources):
        target_doc = all_doc_ids[idx % len(all_doc_ids)]
        cursor.execute(
            "INSERT INTO verification_records (document_id, source_name, source_type, verification_status, submitted_data, source_response, verified_at, notes) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                target_doc[0], s[0], s[1], s[2],
                json.dumps({"app_id": target_doc[1], "doc_type": target_doc[2]}),
                json.dumps({"status": s[2], "source": s[0], "message": s[3]}),
                now_iso, s[3],
            ),
        )

    # ── Infrastructure Evidence (Computer Vision & Geo) ───────────────
    infra_items = [
        (app_ids[0], "CLASSROOM", "Smart Classroom Block A", 66.0, 72.5, 28.7041, 77.1025, 0.98, "VERIFIED", "AI verified: Desks, projector, natural ventilation norms met"),
        (app_ids[0], "COMPUTER_LAB", "Advanced AI & Supercomputing Lab", 150.0, 165.0, 28.7043, 77.1029, 0.96, "VERIFIED", "AI detected 75 terminals, UPS backup, fire suppression"),
        (app_ids[0], "CENTRAL_LIBRARY", "Central Digital Library & Reading Hall", 400.0, 420.0, 28.7039, 77.1022, 0.99, "VERIFIED", "AI detected automated RFID turnstiles and >15,000 titles"),
        (app_ids[0], "FIRE_SAFETY", "Hydrant & Fire Extinguisher Grid", 50.0, 50.0, 28.7040, 77.1024, 0.72, "FLAGGED", "Pressure gauge reading requires physical EVC verification"),
        (app_ids[1], "WORKSHOP", "Central Mechanical Machine Workshop", 250.0, 210.0, 19.0330, 73.0297, 0.65, "FLAGGED", "Deficit: Carpet area is 40 sqm below APH minimum norm"),
        (app_ids[3], "LAND_BOUNDARY", "Campus Boundary Perimeter", 21000.0, 18500.0, 28.4744, 77.5040, 0.58, "FLAGGED", "Satellite boundary overlay shows discrepancy with master deed"),
    ]
    for inf in infra_items:
        cursor.execute(
            "INSERT INTO infrastructure_evidence (application_id, facility_type, title, required_area_sqm, reported_area_sqm, geo_lat, geo_lng, ai_confidence, status, notes, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (*inf, now_iso),
        )

    # ── Anomaly Alerts (5 High Attention) ──────────────────────────────
    anomalies = [
        (all_doc_ids[1][0], app_ids[0], "METADATA_DATE_INCONSISTENCY", "CRITICAL", "Creation date is in future / modified after stamp date", "Producer: Sejda Online PDF Editor", 0.94),
        (all_doc_ids[5][0], app_ids[0], "ELA_ANOMALY", "HIGH", "Error Level Analysis shows digital splicing on architect seal", "Bright ELA variance detected in signature box", 0.88),
        (all_doc_ids[2][0], app_ids[1], "DUPLICATE_CONTENT", "CRITICAL", "Affidavit text 96% identical to submitted document from previous year", "Cross-dossier hash match on body text", 0.96),
        (all_doc_ids[6][0], app_ids[4], "FACULTY_DUPLICATION", "HIGH", "Faculty Dr. A. K. Sen listed simultaneously in two institutes", "Aadhaar seed matched across APP-1042 and APP-1099", 0.99),
        (all_doc_ids[4][0], app_ids[3], "LAND_SURVEY_MISMATCH", "HIGH", "Khasra number 45/A in deed differs from municipal GIS coordinates", "Coordinate mismatch delta: 120 meters", 0.85),
    ]
    for anom in anomalies:
        cursor.execute(
            "INSERT INTO anomaly_alerts (document_id, application_id, alert_type, severity, description, evidence, is_resolved, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, 0, ?)",
            (*anom[:6], now_iso),
        )

    # ── Compliance Checks ─────────────────────────────────────────────
    comp_items = [
        (app_ids[0], "APH 2026-27 Norms", "Affidavit on Rs. 100 Stamp Paper", "DOCUMENT", "COMPLIANT", "Prescribed format", "Valid", "Verified by DigiLocker"),
        (app_ids[0], "APH 2026-27 Norms", "State Fire NOC Validity", "DOCUMENT", "NON_COMPLIANT", "Valid through academic year", "Expired 14 days ago", "Discrepancy flagged"),
        (app_ids[0], "APH 2026-27 Norms", "Student-Faculty Ratio (SFR)", "FACULTY", "COMPLIANT", "≤ 1:15", "1:13.8", "45 approved faculty for 620 students"),
        (app_ids[0], "APH 2026-27 Norms", "PhD Faculty Cadre Ratio", "FACULTY", "COMPLIANT", "≥ 20% Cadre", "38.5% PhDs", "18 faculty with doctoral qualification"),
        (app_ids[0], "APH 2026-27 Norms", "Land Area (Urban Metro)", "INFRASTRUCTURE", "COMPLIANT", "≥ 2.5 Acres", "5.2 Acres", "Registered in Trust Name"),
        (app_ids[0], "APH 2026-27 Norms", "Computer Terminal Ratio", "INFRASTRUCTURE", "COMPLIANT", "1:4 Students", "1:3.2 Students", "210 networked systems"),
        (app_ids[0], "APH 2026-27 Norms", "Fixed Deposit Reserve (FDR)", "FINANCIAL", "COMPLIANT", "Rs. 100 Lakh", "Rs. 125 Lakh", "Lien marked with AICTE"),
        (app_ids[1], "APH 2026-27 Norms", "Mechanical Workshop Area", "INFRASTRUCTURE", "NON_COMPLIANT", "≥ 250 sqm", "210 sqm", "40 sqm deficit reported"),
        (app_ids[3], "APH 2026-27 Norms", "Title Deed Survey Alignment", "INFRASTRUCTURE", "PARTIAL", "Clear contiguous title", "Overlapping plot boundary", "EVC scrutiny required"),
    ]
    for c in comp_items:
        cursor.execute(
            "INSERT INTO compliance_checks (application_id, checklist_name, check_item, category, status, required_value, actual_value, evidence, checked_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (*c, now_iso),
        )

    # ── Live Audit Trail ───────────────────────────────────────────────
    audit_events = [
        (app_ids[0], "CASE_DOSSIER_OPENED", "Dr. Rajeshwar Pant", "Case dossier APP-2026-1042 opened for regulatory scrutiny", "10.14.22.8"),
        (app_ids[0], "SOURCE_VERIFICATION_MISMATCH", "PRAMAAN Bot", "State Fire NOC API returned MISMATCH on ref number FSC/2026/892", "127.0.0.1"),
        (app_ids[0], "DIGILOCKER_VERIFIED", "PRAMAAN Bot", "Trustee Affidavit e-Aadhaar & Digital Signature validated", "127.0.0.1"),
        (app_ids[1], "DEFICIENCY_NOTICE_ISSUED", "Dr. Rajeshwar Pant", "Official Section 10(k) Deficiency Memo generated and transmitted", "10.14.22.8"),
        (app_ids[3], "EVC_INSPECTION_ORDERED", "Dr. Rajeshwar Pant", "Expert Visiting Committee (EVC) mandated for campus physical inspection", "10.14.22.8"),
        (app_ids[2], "NBA_API_VERIFIED", "PRAMAAN Bot", "Tier-1 Accreditation confirmed for B.Tech Computer Science", "127.0.0.1"),
        (app_ids[4], "FRAUD_ALERT_FLAGGED", "PRAMAAN Bot", "Multiple affiliation detected for Dr. A.K. Sen across 2 institutions", "127.0.0.1"),
    ]
    for ev in audit_events:
        cursor.execute(
            "INSERT INTO audit_trail (application_id, action, actor, details, ip_address, timestamp) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (*ev, now_iso),
        )

    conn.commit()
    conn.close()


def _generate_pramaan_ocr(doc_type: str, app_id: int) -> str:
    """Generate realistic regulatory OCR text."""
    if doc_type == DocumentTypes.AFFIDAVIT:
        return (
            "BEFORE THE ALL INDIA COUNCIL FOR TECHNICAL EDUCATION (AICTE)\n"
            "AFFIDAVIT ON NON-JUDICIAL STAMP PAPER OF RS. 100/-\n\n"
            "I, Dr. Arvind Swaminathan, Chairman, Aryabhatta Educational Trust, "
            "do solemnly affirm and state as follows:\n"
            "1. That the information submitted in Application APP-2026-1042 for Extension of Approval "
            "is authentic, complete and verified.\n"
            "2. That the institution strictly follows AICTE Approval Process Handbook (APH) regulations.\n"
            "AICTE Permanent ID: 1-2026-1042\n"
            "Digitally Signed: 15/03/2026 | Notary Reg: DL-8891/2012"
        )
    elif doc_type == DocumentTypes.FIRE_SAFETY_CERT:
        return (
            "DELHI FIRE SERVICE : GOVT OF NCT OF DELHI\n"
            "FIRE SAFETY NOC CERTIFICATE\n"
            "Ref No: FSC/2026/892\n"
            "Premises: Aryabhatta Institute of Technology, Rohini, New Delhi\n"
            "Validity: Expired on 14/03/2026 [RENEWAL APPLICATION PENDING]\n"
            "Chief Fire Officer, Delhi Fire Service."
        )
    return f"Official PRAMAAN Document Content for {doc_type} under Application #{app_id}"


if __name__ == "__main__":
    seed_database(force=True)
    print("PRAMAAN Database seeded successfully with hero dossier APP-2026-1042!")
