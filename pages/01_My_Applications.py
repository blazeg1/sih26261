"""
PRAMAAN Module 1: My Applications & Case Dossiers.

Enables regulatory scrutiny officers to manage jurisdiction case dossiers,
inspect application records, track scrutiny stages, and ingest new filings.
"""

import os
import sys
import json
import sqlite3
import hashlib
from pathlib import Path
from datetime import datetime

import streamlit as st
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config.settings import DATABASE_PATH, UPLOAD_DIR, ApplicationCategories, DocumentTypes
from utils.auth import check_auth, get_current_user
from utils.helpers import ensure_dir, get_timestamp
from utils.theme import apply_pramaan_theme, render_top_gov_banner, render_pramaan_header, render_sahayak_copilot

st.set_page_config(page_title="My Applications — PRAMAAN", page_icon="📋", layout="wide")
apply_pramaan_theme()

render_top_gov_banner()
user = get_current_user() or {"full_name": "Dr. Rajeshwar Pant", "role": "Senior Scrutiny Officer", "department": "Bureau of Approval"}
render_pramaan_header(user)
render_sahayak_copilot()

st.markdown("""
<div style="background:white; border-radius:10px; padding:16px 20px; margin-bottom:1.2rem; border:1px solid #E2E8F0;">
    <h3 style="margin:0; color:#0F172A; font-weight:800;">📋 My Applications Docket & Case Dossiers</h3>
    <p style="margin:4px 0 0 0; color:#64748B; font-size:0.85rem;">
        Jurisdiction: Northern Regional Committee & Central University Institutions · 12 Active Case Dossiers
    </p>
</div>
""", unsafe_allow_html=True)

tab_docket, tab_dossier, tab_ingest = st.tabs([
    "📂 Active Applications Docket (12)",
    "📑 Detailed Case Dossier Inspector",
    "➕ Ingest / Resubmit Application",
])

# ── TAB 1: Docket Overview ─────────────────────────────────────────────
with tab_docket:
    fc1, fc2, fc3 = st.columns(3)
    with fc1:
        stat_filter = st.selectbox("Filter Stage", ["All Stages", "UNDER_REVIEW", "SUBMITTED", "APPROVED", "REJECTED"])
    with fc2:
        cat_filter = st.selectbox("Category", ["All Categories", "EOA", "NEW_INSTITUTION", "ADD_PROGRAMME", "CHANGE_OF_SITE"])
    with fc3:
        search_query = st.text_input("Search Institute or Case ID", placeholder="e.g. Aryabhatta or 1042")

    conn = sqlite3.connect(DATABASE_PATH)
    query = """
        SELECT a.id, 'APP-2026-' || (1000 + a.id) as case_id, i.name as institution,
               i.aicte_id, i.state, a.category, a.academic_year, a.status,
               (SELECT COUNT(*) FROM documents d WHERE d.application_id = a.id) as doc_count,
               (SELECT COUNT(*) FROM anomaly_alerts aa WHERE aa.application_id = a.id AND aa.is_resolved = 0) as flags
        FROM applications a
        JOIN institutions i ON a.institution_id = i.id
        WHERE 1=1
    """
    params = []
    if stat_filter != "All Stages":
        query += " AND a.status = ?"
        params.append(stat_filter)
    if cat_filter != "All Categories":
        query += " AND a.category = ?"
        params.append(cat_filter)
    if search_query:
        query += " AND (i.name LIKE ? OR a.id LIKE ?)"
        params.extend([f"%{search_query}%", f"%{search_query}%"])
    query += " ORDER BY a.id ASC"

    df = pd.read_sql_query(query, conn, params=params)
    conn.close()

    if not df.empty:
        df.columns = ["DB ID", "Case ID", "Institution", "AICTE ID", "State", "Category", "A.Y.", "Stage", "Docs", "Active Flags"]
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("No applications match the search criteria.")

# ── TAB 2: Detailed Case Dossier Inspector ─────────────────────────────
with tab_dossier:
    conn = sqlite3.connect(DATABASE_PATH)
    app_choices = pd.read_sql_query("""
        SELECT a.id, ('APP-2026-' || (1000 + a.id) || ' — ' || i.name) as label
        FROM applications a JOIN institutions i ON a.institution_id = i.id
        ORDER BY a.id ASC
    """, conn)
    conn.close()

    app_dict = dict(zip(app_choices["label"], app_choices["id"]))
    selected_label = st.selectbox("Select Case Dossier for In-depth Inspection", list(app_dict.keys()), index=0)
    sel_app_id = app_dict[selected_label]

    conn = sqlite3.connect(DATABASE_PATH)
    app_meta = pd.read_sql_query("""
        SELECT a.*, i.name as inst_name, i.aicte_id, i.university, i.state, i.city, i.address, i.established_year
        FROM applications a JOIN institutions i ON a.institution_id = i.id
        WHERE a.id = ?
    """, conn, params=(sel_app_id,)).iloc[0]

    docs_in_case = pd.read_sql_query("""
        SELECT id, doc_type, filename, validation_status, anomaly_score, upload_date
        FROM documents WHERE application_id = ?
    """, conn, params=(sel_app_id,))

    alerts_in_case = pd.read_sql_query("""
        SELECT alert_type, severity, description, evidence FROM anomaly_alerts
        WHERE application_id = ? AND is_resolved = 0
    """, conn, params=(sel_app_id,))
    conn.close()

    # Dossier Banner
    st.markdown(f"""
    <div style="background:#F8FAFC; border:1px solid #CBD5E1; border-radius:10px; padding:18px; margin:1rem 0;">
        <div style="display:flex; justify-content:space-between; align-items:flex-start;">
            <div>
                <span style="font-size:0.75rem; background:#2563EB; color:white; padding:3px 8px; border-radius:4px; font-weight:700;">
                    DOSSIER APP-2026-{1000 + sel_app_id}
                </span>
                <h4 style="margin:6px 0 2px 0; color:#0F172A;">{app_meta['inst_name']}</h4>
                <div style="font-size:0.82rem; color:#64748B;">
                    Permanent AICTE ID: <strong>{app_meta['aicte_id']}</strong> · Affiliated to: {app_meta['university']} · Established: {app_meta['established_year']}
                </div>
                <div style="font-size:0.8rem; color:#475569; margin-top:4px;">
                    📍 {app_meta['address']}, {app_meta['city']}, {app_meta['state']}
                </div>
            </div>
            <div style="text-align:right;">
                <div style="font-size:0.72rem; color:#64748B; font-weight:700;">REGULATORY STAGE</div>
                <div style="background:#FEF3C7; color:#92400E; padding:4px 10px; border-radius:6px; font-weight:700; font-size:0.85rem; margin-top:2px;">
                    {app_meta['status']}
                </div>
                <div style="font-size:0.75rem; color:#64748B; margin-top:4px;">
                    Scrutiny Officer: {app_meta['reviewed_by'] or 'Assigned'}
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    c_doc, c_alt = st.columns([6, 4])
    with c_doc:
        st.markdown("##### 📄 Submitted Documentary Evidence")
        if not docs_in_case.empty:
            st.dataframe(docs_in_case, use_container_width=True, hide_index=True)
        else:
            st.warning("No documents attached to this dossier.")

    with c_alt:
        st.markdown("##### ⚠️ Active Regulatory Alerts")
        if not alerts_in_case.empty:
            for _, alt in alerts_in_case.iterrows():
                st.markdown(f"""
                <div style="background:#FEF2F2; border-left:4px solid #DC2626; padding:8px 12px; border-radius:6px; margin-bottom:8px;">
                    <div style="font-size:0.75rem; font-weight:700; color:#991B1B;">[{alt['severity']}] {alt['alert_type']}</div>
                    <div style="font-size:0.75rem; color:#7F1D1D;">{alt['description']}</div>
                    <div style="font-size:0.7rem; color:#B91C1C; margin-top:2px;">Evidence: {alt['evidence']}</div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.success("No active anomalies detected in this dossier.")

# ── TAB 3: Ingest / Upload Application ─────────────────────────────────
with tab_ingest:
    st.markdown("##### 📤 Ingest Supporting Documents for Scrutiny")
    up_col1, up_col2 = st.columns(2)

    with up_col1:
        inst_target = st.selectbox("Target Institution", list(app_dict.keys()), key="ingest_inst")
        up_cat = st.selectbox("Application Category", ["EOA", "NEW_INSTITUTION", "ADD_PROGRAMME", "CHANGE_OF_SITE"], key="ingest_cat")
        up_ay = st.text_input("Academic Year", value="2026-27")

    with up_col2:
        uploaded_files = st.file_uploader(
            "Upload Institutional Documents (PDF, PNG, JPG)",
            accept_multiple_files=True,
            type=["pdf", "png", "jpg", "jpeg"],
        )

    if st.button("🚀 Process & Ingest Into Dossier", type="primary"):
        if not uploaded_files:
            st.error("Please select at least one document.")
        else:
            target_id = app_dict[inst_target]
            ensure_dir(UPLOAD_DIR)
            conn = sqlite3.connect(DATABASE_PATH)
            cur = conn.cursor()
            for f in uploaded_files:
                f_bytes = f.read()
                f_hash = hashlib.sha256(f_bytes).hexdigest()
                save_path = os.path.join(UPLOAD_DIR, f"{target_id}_{f.name}")
                with open(save_path, "wb") as fh:
                    fh.write(f_bytes)

                # Classify based on filename heuristics
                fname_lower = f.name.lower()
                doc_type = DocumentTypes.AFFIDAVIT if "affidavit" in fname_lower else \
                           DocumentTypes.FIRE_SAFETY_CERT if "fire" in fname_lower else \
                           DocumentTypes.NOC if "noc" in fname_lower else DocumentTypes.LAND_DOCUMENT

                cur.execute("""
                    INSERT INTO documents (application_id, doc_type, filename, file_path, file_hash, upload_date, expiry_date, validation_status, anomaly_score, notes)
                    VALUES (?, ?, ?, ?, ?, ?, '2028-06-30', 'VALID', 0.05, 'Uploaded via Officer Desk')
                """, (target_id, doc_type, f.name, save_path, f_hash, datetime.now().strftime("%Y-%m-%d")))

            cur.execute("""
                INSERT INTO audit_trail (application_id, action, actor, details, ip_address, timestamp)
                VALUES (?, 'DOCUMENTS_INGESTED', ?, ?, '10.14.22.8', ?)
            """, (target_id, user.get("username", "rajeshwar.pant"), f"Ingested {len(uploaded_files)} new documents", datetime.now().isoformat()))
            conn.commit()
            conn.close()

            st.success(f"✅ Successfully ingested {len(uploaded_files)} documents into Case Dossier #{target_id}!")
