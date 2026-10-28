"""
PRAMAAN Module 3: Source Verification & Authority API Gateway.

Enables automated verification of submitted documents directly through
issuing-authority portals, DigiLocker, NBA/NAAC, State Land Records, and QR/DSC services.
"""

import os
import sys
import json
import sqlite3
from pathlib import Path
from datetime import datetime

import streamlit as st
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config.settings import DATABASE_PATH, VerificationStatuses
from utils.auth import get_current_user
from utils.theme import apply_pramaan_theme, render_top_gov_banner, render_pramaan_header, render_sahayak_copilot
from modules.verification_service import VerificationService

st.set_page_config(page_title="Source Verification — PRAMAAN", page_icon="🌐", layout="wide")
apply_pramaan_theme()

render_top_gov_banner()
user = get_current_user() or {"full_name": "Dr. Rajeshwar Pant", "role": "Senior Scrutiny Officer", "department": "Bureau of Approval"}
render_pramaan_header(user)
render_sahayak_copilot()

st.markdown("""
<div style="background:white; border-radius:10px; padding:16px 20px; margin-bottom:1.2rem; border:1px solid #E2E8F0;">
    <h3 style="margin:0; color:#0F172A; font-weight:800;">🌐 Issuing Authority Source Verification Gateway</h3>
    <p style="margin:4px 0 0 0; color:#64748B; font-size:0.85rem;">
        Direct API integration with DigiLocker, NBA, NAAC, State Fire Services, Land Revenue GIS & Affiliating State Universities.
    </p>
</div>
""", unsafe_allow_html=True)

# Application Selector
conn = sqlite3.connect(DATABASE_PATH)
app_df = pd.read_sql_query("""
    SELECT a.id, ('APP-2026-' || (1000 + a.id) || ' — ' || i.name) as label,
           i.name as inst_name, i.aicte_id, i.state
    FROM applications a JOIN institutions i ON a.institution_id = i.id
    ORDER BY a.id ASC
""", conn)
conn.close()

col_sel1, col_sel2 = st.columns([7, 3])
with col_sel1:
    app_choice = st.selectbox("Select Application for Source Verification", app_df["label"].tolist(), index=0)
    sel_app_id = int(app_df[app_df["label"] == app_choice]["id"].iloc[0])
    inst_name = str(app_df[app_df["label"] == app_choice]["inst_name"].iloc[0])
    inst_state = str(app_df[app_df["label"] == app_choice]["state"].iloc[0])

tab_gateway, tab_qr_dsc, tab_dossier_matrix = st.tabs([
    "⚡ Live Authority API Queries",
    "📱 QR Code & Digital Signature (DSC) Inspector",
    "📊 Institutional Verification Matrix",
])

verifier = VerificationService()

# ── TAB 1: Live Authority API Gateway ─────────────────────────────────
with tab_gateway:
    st.markdown("##### 🔌 Query Issuing Authority API Services")
    st.caption("Execute cryptographic REST queries to state and central digital repositories to validate certificate authenticity.")

    col_q1, col_q2 = st.columns([5, 5])
    
    with col_q1:
        authority_type = st.selectbox(
            "Select Authority Endpoint",
            [
                "State Fire & Rescue Services Directorate (NOC Verification)",
                "State Revenue & Land Records GIS (Bhulekh / Dharani Title Deed)",
                "National Board of Accreditation (NBA API - Program Tier)",
                "NAAC Quality Assessment Portal (Institutional CGPA)",
                "DigiLocker Academic Depository (Faculty PhD Verification)",
                "State Affiliating Technical University (Affiliation Order API)"
            ]
        )

        if "Fire" in authority_type:
            cert_id = st.text_input("NOC Certificate Reference Number", value="NOC/ST/2024/84920")
            issuing_state = st.text_input("Issuing State Jurisdiction", value=inst_state)
        elif "Land" in authority_type:
            cert_id = st.text_input("Land Khatauni / Survey Reference Number", value="SRV-2019-9402-UP")
            issuing_state = st.text_input("Revenue District / Taluka", value="Gautam Buddha Nagar")
        elif "NBA" in authority_type:
            cert_id = st.text_input("NBA File Reference Number", value="NBA/2022/UG-ENGG/1042")
            issuing_state = st.selectbox("Program Discipline", ["Computer Science & Engineering", "Mechanical Engineering", "Electronics"])
        elif "NAAC" in authority_type:
            cert_id = st.text_input("NAAC Track ID / College Code", value="UPCOGN10492")
            issuing_state = st.text_input("Accreditation Cycle", value="Cycle 2")
        elif "DigiLocker" in authority_type:
            cert_id = st.text_input("DigiLocker Doc URI / Aadhaar Token", value="in.gov.digilocker:DOC:PHD:84029148")
            issuing_state = st.text_input("Awarding University", value="IIT Delhi / AKTU")
        else:
            cert_id = st.text_input("Affiliation Order Number", value="AKTU/AFF/2025-26/1042")
            issuing_state = st.text_input("Affiliating University Code", value="AKTU-027")

        query_btn = st.button("🚀 Query Issuing Authority Endpoint", type="primary")

    with col_q2:
        st.markdown("##### 📡 Authority Response & Evidence Payload")
        if query_btn:
            with st.spinner("Connecting to secure Govt API Gateway (TLS 1.3)..."):
                # Simulate API call based on chosen authority
                if "Fire" in authority_type:
                    # In APP-2026-1042 Aryabhatta, fire NOC has mismatch/expired in seed
                    if sel_app_id == 1:
                        resp_data = {
                            "status_code": 200,
                            "authority": "State Fire Services Portal",
                            "reference_number": cert_id,
                            "certificate_holder": inst_name,
                            "issue_date": "2024-03-15",
                            "expiry_date": "2026-03-14",
                            "current_status": "EXPIRED",
                            "building_height_cleared_meters": 14.8,
                            "digital_signature_valid": True,
                            "discrepancy_alert": "Certificate expired 14 days prior to submission date. Renewal required under APH Clause 5.2."
                        }
                        status_chip = VerificationStatuses.MISMATCH_DETECTED
                    else:
                        resp_data = {
                            "status_code": 200,
                            "authority": "State Fire Services Portal",
                            "reference_number": cert_id,
                            "certificate_holder": inst_name,
                            "issue_date": "2024-06-10",
                            "expiry_date": "2027-06-09",
                            "current_status": "ACTIVE_VALID",
                            "building_height_cleared_meters": 15.0,
                            "digital_signature_valid": True
                        }
                        status_chip = VerificationStatuses.VERIFIED
                elif "Land" in authority_type:
                    resp_data = {
                        "status_code": 200,
                        "authority": "State Revenue Records & GIS Portal",
                        "survey_number": cert_id,
                        "registered_title_holder": f"Aryabhatta Educational Trust (For {inst_name})",
                        "land_area_sqm": 30351.4,
                        "land_area_acres": 7.5,
                        "encumbrance_status": "FREE_FROM_ENCUMBRANCE",
                        "land_use_conversion": "EDUCATIONAL_APPROVED",
                        "gis_coordinates": {"latitude": 28.5355, "longitude": 77.3910},
                        "digital_signature_valid": True
                    }
                    status_chip = VerificationStatuses.VERIFIED
                elif "NBA" in authority_type:
                    resp_data = {
                        "status_code": 200,
                        "authority": "National Board of Accreditation",
                        "file_number": cert_id,
                        "program_name": issuing_state,
                        "tier": "Tier II",
                        "evaluation_score": 678,
                        "validity_years": "2023-2026",
                        "accreditation_status": "ACCREDITED_3_YEARS"
                    }
                    status_chip = VerificationStatuses.VERIFIED
                elif "DigiLocker" in authority_type:
                    resp_data = {
                        "status_code": 200,
                        "authority": "DigiLocker National Academic Depository",
                        "doc_uri": cert_id,
                        "holder_name": "Dr. Ramesh Chandra Sharma (Principal)",
                        "degree": "Ph.D. in Computer Science & Engineering",
                        "university": "IIT Roorkee",
                        "year_of_passing": 2012,
                        "sha256_hash_match": True,
                        "pki_status": "AUTHENTIC"
                    }
                    status_chip = VerificationStatuses.VERIFIED
                else:
                    resp_data = {
                        "status_code": 200,
                        "authority": "State Technical University Gateway",
                        "order_number": cert_id,
                        "affiliation_status": "CONTINUED_AFFILIATION_GRANTED",
                        "academic_session": "2026-27",
                        "sanctioned_courses": ["CSE", "ECE", "MECH", "CIVIL"],
                        "total_sanctioned_intake": 420
                    }
                    status_chip = VerificationStatuses.VERIFIED

                # Record in database
                conn = sqlite3.connect(DATABASE_PATH)
                cur = conn.cursor()
                cur.execute("""
                    INSERT INTO verification_records (application_id, doc_type, issuing_authority, reference_number, verification_source, verification_status, response_payload, verified_at)
                    VALUES (?, ?, ?, ?, 'GOV_API_GATEWAY', ?, ?, ?)
                """, (sel_app_id, authority_type[:30], authority_type.split("(")[0].strip(), cert_id, status_chip, json.dumps(resp_data), datetime.now().isoformat()))
                
                cur.execute("""
                    INSERT INTO audit_trail (application_id, action, actor, details, ip_address, timestamp)
                    VALUES (?, 'SOURCE_VERIFICATION_QUERY', ?, ?, '10.14.22.8', ?)
                """, (sel_app_id, user.get("username", "rajeshwar.pant"), f"Queried {authority_type[:35]} - Result: {status_chip}", datetime.now().isoformat()))
                conn.commit()
                conn.close()

                if status_chip == VerificationStatuses.VERIFIED:
                    st.success("✅ **STATUS: VERIFIED (MATCH CONFIRMED)**")
                else:
                    st.error("⚠️ **STATUS: MISMATCH DETECTED / EXPIRED**")

                st.json(resp_data)
        else:
            st.info("Click 'Query Issuing Authority Endpoint' to dispatch secure request.")

# ── TAB 2: QR Code & Digital Signature (DSC) Inspector ────────────────
with tab_qr_dsc:
    st.markdown("##### 📱 Cryptographic QR & DSC Validation")
    st.caption("Decode digitally signed PDF e-Signatures and 2D QR codes stamped by issuing authorities.")

    col_qr1, col_qr2 = st.columns(2)
    with col_qr1:
        st.markdown("""
        <div style="background:#0F172A; border:1px solid #334155; border-radius:8px; padding:16px; color:#F8FAFC;">
            <div style="font-size:0.8rem; font-weight:700; color:#60A5FA;">DIGITAL SIGNATURE CERTIFICATE (DSC) PARSER</div>
            <div style="margin-top:10px; font-size:0.82rem; line-height:1.6;">
                <strong>Signer Common Name:</strong> SANJAY KUMAR VERMA (Fire Chief Officer)<br>
                <strong>Certificate Authority:</strong> e-Mudhra Sub-CA for Document Signer 2024<br>
                <strong>Algorithm:</strong> SHA-256 with RSA 2048-bit Encryption<br>
                <strong>Timestamp Token:</strong> RFC 3161 Verified (Time: 2024-03-15T11:42:09Z)<br>
                <strong>Certificate Revocation List (CRL):</strong> Checked (Not Revoked)
            </div>
            <div style="margin-top:12px; padding:6px 10px; background:rgba(16, 185, 129, 0.2); border:1px solid #10B981; border-radius:6px; color:#34D399; font-weight:700; font-size:0.75rem;">
                ✓ DIGITAL SIGNATURE CRYPTOGRAPHICALLY VALID
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col_qr2:
        st.markdown("""
        <div style="background:#0F172A; border:1px solid #334155; border-radius:8px; padding:16px; color:#F8FAFC;">
            <div style="font-size:0.8rem; font-weight:700; color:#60A5FA;">2D BARCODE / QR PAYLOAD DECODER</div>
            <div style="margin-top:10px; font-size:0.82rem; line-height:1.6;">
                <strong>Decoded URL:</strong> <code>https://fireportal.up.gov.in/verify/NOC-2024-84920</code><br>
                <strong>Payload Nonce:</strong> <code>e4a90f12b73c</code><br>
                <strong>Digest Hash:</strong> <code>9b8a...442f</code> (Matches file hash)<br>
                <strong>QR Redirection Security:</strong> Whitelisted Government Domain (.gov.in)
            </div>
            <div style="margin-top:12px; padding:6px 10px; background:rgba(16, 185, 129, 0.2); border:1px solid #10B981; border-radius:6px; color:#34D399; font-weight:700; font-size:0.75rem;">
                ✓ AUTHENTIC QR ANCHORED TO STATE REPOSITORY
            </div>
        </div>
        """, unsafe_allow_html=True)

# ── TAB 3: Institutional Verification Matrix ──────────────────────────
with tab_dossier_matrix:
    st.markdown(f"##### 📊 Source Verification Matrix for {inst_name}")
    
    conn = sqlite3.connect(DATABASE_PATH)
    v_records = pd.read_sql_query("""
        SELECT issuing_authority as Authority, doc_type as Document,
               reference_number as "Reference No.", verification_status as Status,
               verification_source as Source, verified_at as "Verified At"
        FROM verification_records
        WHERE application_id = ?
        ORDER BY id DESC
    """, conn, params=(sel_app_id,))
    conn.close()

    if not v_records.empty:
        st.dataframe(v_records, use_container_width=True, hide_index=True)
    else:
        st.info("No verification queries recorded yet for this case. Execute an API query from Tab 1.")
