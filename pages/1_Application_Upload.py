"""
Page 1: Application Upload & Intake Studio

Handles uploading new applications and documents, running OCR,
classifying documents, and extracting structured institutional data.
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

from config.settings import (
    APP_TITLE, APP_ICON, DATABASE_PATH, UPLOAD_DIR,
    SUPPORTED_EXTENSIONS, ApplicationCategories, DocumentTypes,
)
from utils.auth import check_auth, require_role, get_current_user
from utils.helpers import ensure_dir, compute_file_hash, get_timestamp
from utils.styles import (
    apply_custom_styles,
    render_gov_header,
    render_aicte_brand_bar,
    render_sidebar_header,
    render_sih_footer,
    render_progress_tracker,
    status_badge_html
)

# ── Page Config ────────────────────────────────────────────────────────
st.set_page_config(page_title=f"Application Upload — {APP_TITLE}", page_icon="📋", layout="wide")
apply_custom_styles()
render_gov_header()

# ── Auth Check ─────────────────────────────────────────────────────────
if not check_auth():
    st.warning("🔒 Please log in from the main page to access this section.")
    render_sih_footer()
    st.stop()

user = get_current_user()
if user and user["role"] not in ("ADMIN", "REVIEWER"):
    st.error("⛔ You need ADMIN or REVIEWER role to access this page.")
    render_sih_footer()
    st.stop()

# ── Sidebar ────────────────────────────────────────────────────────────
with st.sidebar:
    render_sidebar_header(user)

# ── Header Bar ─────────────────────────────────────────────────────────
render_aicte_brand_bar("Application Upload & Intake", "Institutional Filing & Multi-Format Document OCR Ingestion Studio")

# ── Import processing modules (graceful fallback) ──────────────────────
try:
    from modules.ocr_engine import OCREngine
    from modules.document_classifier import DocumentClassifier
    from modules.data_extractor import DataExtractor
    from modules.pdf_processor import PDFProcessor
    ocr_engine = OCREngine()
    classifier = DocumentClassifier()
    extractor = DataExtractor()
    PROCESSING_AVAILABLE = True
except ImportError as e:
    PROCESSING_AVAILABLE = False
    st.warning(f"⚠️ Some processing modules unavailable: {e}. Upload will still save files.")

# ── Tabs ───────────────────────────────────────────────────────────────
tab_upload, tab_view = st.tabs(["📤 Upload New Application Dossier", "📋 View Applications Queue"])

# ════════════════════════════════════════════════════════════════════════
#  TAB 1: Upload New Application
# ════════════════════════════════════════════════════════════════════════
with tab_upload:
    # Step progress tracker
    render_progress_tracker(
        ["1. Institution Select", "2. Category & Year", "3. Document Upload", "4. AI Ingestion"],
        current_step_index=2
    )

    col_form, col_preview = st.columns([5, 5])

    with col_form:
        st.markdown("""
        <div style="background:#FFFFFF; border:1px solid #E2E8F0; border-radius:16px; padding:20px; box-shadow:0 4px 15px rgba(11,31,75,0.05); margin-bottom:1.2rem;">
            <div style="font-size:0.75rem; font-weight:700; color:#FF9933; text-transform:uppercase; letter-spacing:0.8px;">STEP 1 · INSTITUTIONAL PROFILE</div>
            <h4 style="margin:4px 0 12px 0; color:#0B1F4B;">Select or Register Technical Institute</h4>
        """, unsafe_allow_html=True)

        # Fetch existing institutions
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, aicte_id FROM institutions ORDER BY name")
        inst_rows = cursor.fetchall()
        conn.close()

        inst_options = {f"{row[1]} ({row[2]})": row[0] for row in inst_rows}
        inst_options["➕ Add New Institution to Master Register"] = -1

        selected_inst = st.selectbox("Registered Institution", options=list(inst_options.keys()), help="Select technical institution from AICTE Master Register")
        institution_id = inst_options[selected_inst]

        # New institution form
        if institution_id == -1:
            st.markdown("<p style='font-size:0.8rem; font-weight:700; color:#2563EB;'>New Institution Registration Fields:</p>", unsafe_allow_html=True)
            new_name = st.text_input("Institution Full Legal Name *", placeholder="e.g. Aryabhatta Institute of Technology")
            new_aicte_id = st.text_input("Permanent AICTE ID *", placeholder="e.g. 1-3329182910")
            new_university = st.text_input("Affiliating University *", placeholder="e.g. Dr. A.P.J. Abdul Kalam Technical University")
            nc1, nc2 = st.columns(2)
            with nc1:
                new_state = st.text_input("State *", placeholder="e.g. Uttar Pradesh")
            with nc2:
                new_city = st.text_input("City *", placeholder="e.g. Greater Noida")
            new_address = st.text_area("Campus Address", placeholder="e.g. Knowledge Park III")
            new_year = st.number_input("Established Year", min_value=1900, max_value=2026, value=2010)

        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("""
        <div style="background:#FFFFFF; border:1px solid #E2E8F0; border-radius:16px; padding:20px; box-shadow:0 4px 15px rgba(11,31,75,0.05); margin-bottom:1.2rem;">
            <div style="font-size:0.75rem; font-weight:700; color:#FF9933; text-transform:uppercase; letter-spacing:0.8px;">STEP 2 · FILING SPECIFICATIONS</div>
            <h4 style="margin:4px 0 12px 0; color:#0B1F4B;">Application Category & Academic Session</h4>
        """, unsafe_allow_html=True)

        ac1, ac2 = st.columns(2)
        with ac1:
            category = st.selectbox("Approval Category *", [
                ApplicationCategories.EOA,
                ApplicationCategories.NEW_INSTITUTION,
                ApplicationCategories.ADD_PROGRAMME,
                ApplicationCategories.CHANGE_OF_SITE,
                ApplicationCategories.CLOSURE,
            ], help="Regulatory category determines checklist requirements")
        with ac2:
            academic_year = st.text_input("Academic Session *", value="2026-27")

        st.markdown("</div>", unsafe_allow_html=True)

        # Document Upload Card
        st.markdown("""
        <div style="background:#FFFFFF; border:1px solid #E2E8F0; border-radius:16px; padding:20px; box-shadow:0 4px 15px rgba(11,31,75,0.05);">
            <div style="font-size:0.75rem; font-weight:700; color:#FF9933; text-transform:uppercase; letter-spacing:0.8px;">STEP 3 · EVIDENCE DOCUMENTS</div>
            <h4 style="margin:4px 0 12px 0; color:#0B1F4B;">Upload Institutional Supporting Documents</h4>
        """, unsafe_allow_html=True)

        uploaded_files = st.file_uploader(
            "Select PDF or Image Files (Multi-file enabled)",
            type=list(SUPPORTED_EXTENSIONS),
            accept_multiple_files=True,
            help="Supported: PDF, PNG, JPG, JPEG, TIFF (Max 50MB per file)",
        )

        st.markdown("</div>", unsafe_allow_html=True)

    with col_preview:
        st.markdown("""
        <div style="background:#FFFFFF; border:1px solid #E2E8F0; border-radius:16px; padding:20px; box-shadow:0 4px 15px rgba(11,31,75,0.05); margin-bottom:1.2rem;">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <h4 style="margin:0; font-size:1rem; color:#0B1F4B;">📑 Mandatory Documents Checklist</h4>
                <span style="font-size:0.7rem; background:#EFF6FF; color:#1D4ED8; font-weight:700; padding:2px 8px; border-radius:9999px;">APH 2024-27</span>
            </div>
            <p style="font-size:0.8rem; color:#64748B; margin:4px 0 12px 0;">Prescribed statutory documents for selected approval category</p>
            <div style="font-size:0.82rem; line-height:1.7;">
                • <strong style="color:#0B1F4B;">Affidavit in Format A</strong> (Duly notarized & stamped)<br>
                • <strong style="color:#0B1F4B;">State Fire & Safety NOC</strong> (Valid certificate from Fire Directorate)<br>
                • <strong style="color:#0B1F4B;">Land Title / Registry Deed</strong> (Clear title or 30-year lease)<br>
                • <strong style="color:#0B1F4B;">Sanctioned Building & Floor Plan</strong> (Approved by municipal authority)<br>
                • <strong style="color:#0B1F4B;">Audited Balance Sheet</strong> (Past 3 financial years)<br>
                • <strong style="color:#0B1F4B;">Faculty Roster & Cadre List</strong> (SFR 1:15 compliance)
            </div>
        </div>
        """, unsafe_allow_html=True)

        if uploaded_files:
            st.markdown(f"#### 🔍 Batch Pre-Processing ({len(uploaded_files)} files queued)")

            if st.button("⚡ Process & Classify Uploaded Documents", type="secondary", use_container_width=True):
                ensure_dir(UPLOAD_DIR)
                processed = []

                with st.spinner("Executing OCR engine, layout analysis & heuristic classification..."):
                    for uf in uploaded_files:
                        temp_path = os.path.join(UPLOAD_DIR, f"temp_{uf.name}")
                        with open(temp_path, "wb") as f:
                            f.write(uf.getbuffer())

                        file_hash = compute_file_hash(temp_path)

                        # Extract text
                        ocr_text = ""
                        if PROCESSING_AVAILABLE:
                            if uf.name.lower().endswith(".pdf"):
                                pdf_proc = PDFProcessor()
                                ocr_text = pdf_proc.extract_text(temp_path)
                            else:
                                ocr_result = ocr_engine.extract_text(temp_path)
                                ocr_text = ocr_result.get("text", "")

                            # Classify
                            cls_result = classifier.classify(temp_path, filename=uf.name, text=ocr_text)
                            doc_type = cls_result.doc_type
                            cls_conf = cls_result.confidence

                            # Extract entities
                            ext_data = extractor.extract_all(ocr_text)
                        else:
                            doc_type = DocumentTypes.OTHER
                            cls_conf = 0.5
                            ext_data = {}

                        processed.append({
                            "filename": uf.name,
                            "file_path": temp_path,
                            "file_hash": file_hash,
                            "doc_type": doc_type,
                            "confidence": cls_conf,
                            "ocr_text": ocr_text,
                            "extracted": ext_data,
                            "size": uf.size,
                        })

                st.session_state["processed_docs"] = processed
                st.success(f"Successfully processed {len(processed)} documents!")

            # Display processed previews
            if "processed_docs" in st.session_state:
                for idx, p in enumerate(st.session_state["processed_docs"]):
                    st.markdown(f"""
                    <div style="background:#F8FAFC; border:1px solid #CBD5E1; border-radius:10px; padding:12px; margin-bottom:8px;">
                        <div style="display:flex; justify-content:space-between; align-items:center;">
                            <strong style="color:#0B1F4B; font-size:0.85rem;">{p['filename']}</strong>
                            <span style="font-size:0.75rem; background:#D1FAE5; color:#065F46; padding:2px 8px; border-radius:4px; font-weight:700;">
                                {p['doc_type']} ({p['confidence']:.0%})
                            </span>
                        </div>
                        <div style="font-size:0.75rem; color:#64748B; margin-top:4px;">
                            Size: {p['size'] / 1024:.1f} KB · Hash: <code>{p['file_hash'][:12]}...</code>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.info("💡 Upload documents on the left to view automated classification and OCR previews.")

    # ── Final Submission Trigger ──────────────────────────────────────────
    st.markdown("---")
    c_sub1, c_sub2 = st.columns([7, 3])
    with c_sub1:
        st.caption("Submitting this dossier commits the documents to the AICTE SQLite Master Database and initiates automated audit tracking.")
    with c_sub2:
        submit_btn = st.button("🚀 Ingest & Finalize Dossier Submission", type="primary", use_container_width=True)

    if submit_btn:
        if not uploaded_files:
            st.error("Please upload at least one document before submitting.")
        elif institution_id == -1 and not new_name:
            st.error("Please provide the institution name.")
        else:
            try:
                conn = sqlite3.connect(DATABASE_PATH)
                cursor = conn.cursor()
                now = get_timestamp()

                # Insert new institution if needed
                if institution_id == -1:
                    cursor.execute(
                        "INSERT INTO institutions (aicte_id, name, address, state, city, university, established_year, created_at) "
                        "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                        (new_aicte_id, new_name, new_address, new_state, new_city, new_university, new_year, now),
                    )
                    institution_id = cursor.lastrowid

                # Insert application
                cursor.execute(
                    "INSERT INTO applications (institution_id, category, academic_year, status, submitted_at, created_at) "
                    "VALUES (?, ?, ?, 'SUBMITTED', ?, ?)",
                    (institution_id, category, academic_year, now, now),
                )
                app_id = cursor.lastrowid

                # Insert documents
                docs_to_insert = st.session_state.get("processed_docs", [])
                ensure_dir(UPLOAD_DIR)

                for uf in uploaded_files:
                    proc_info = next((p for p in docs_to_insert if p["filename"] == uf.name), None)
                    save_path = os.path.join(UPLOAD_DIR, f"{app_id}_{uf.name}")
                    with open(save_path, "wb") as f:
                        f.write(uf.getbuffer())

                    file_hash = compute_file_hash(save_path)
                    doc_type = proc_info["doc_type"] if proc_info else DocumentTypes.OTHER
                    ocr_text = proc_info["ocr_text"] if proc_info else ""
                    extracted = json.dumps(proc_info["extracted"]) if proc_info else "{}"

                    cursor.execute(
                        "INSERT INTO documents (application_id, doc_type, filename, file_path, file_hash, upload_date, ocr_text, extracted_data, validation_status, anomaly_score, notes) "
                        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'PENDING_REVIEW', 0.0, '')",
                        (app_id, doc_type, uf.name, save_path, file_hash, now, ocr_text, extracted),
                    )

                # Record in Audit trail
                cursor.execute(
                    "INSERT INTO audit_trail (application_id, action, actor, details, ip_address, timestamp) "
                    "VALUES (?, 'APPLICATION_SUBMITTED', ?, ?, '127.0.0.1', ?)",
                    (app_id, user["username"] if user else "system",
                     f"Application submitted with {len(uploaded_files)} documents", now),
                )

                conn.commit()
                conn.close()

                st.session_state.pop("processed_docs", None)
                st.success(f"🎉 Application Dossier APP-2026-{1000 + app_id} submitted successfully with {len(uploaded_files)} documents!")
                st.balloons()

            except Exception as e:
                st.error(f"Submission failed: {e}")

# ════════════════════════════════════════════════════════════════════════
#  TAB 2: View Applications Queue
# ════════════════════════════════════════════════════════════════════════
with tab_view:
    st.markdown("### 📋 Applications Docket & Search")

    # Filters
    fc1, fc2, fc3 = st.columns(3)
    with fc1:
        filter_status = st.selectbox("Filter Stage", ["All", "SUBMITTED", "UNDER_REVIEW", "APPROVED", "REJECTED"])
    with fc2:
        filter_category = st.selectbox("Filter Category", ["All"] + [
            ApplicationCategories.EOA, ApplicationCategories.NEW_INSTITUTION,
            ApplicationCategories.ADD_PROGRAMME, ApplicationCategories.CHANGE_OF_SITE,
            ApplicationCategories.CLOSURE,
        ])
    with fc3:
        filter_search = st.text_input("Search Institution or Case ID", placeholder="e.g. Aryabhatta or 1042")

    conn = sqlite3.connect(DATABASE_PATH)
    query = """
        SELECT a.id, ('APP-2026-' || (1000 + a.id)) as case_id, i.name, i.aicte_id,
               a.category, a.academic_year, a.status, a.submitted_at, a.reviewed_by,
               (SELECT COUNT(*) FROM documents d WHERE d.application_id = a.id) as doc_count
        FROM applications a
        JOIN institutions i ON a.institution_id = i.id
        WHERE 1=1
    """
    params = []
    if filter_status != "All":
        query += " AND a.status = ?"
        params.append(filter_status)
    if filter_category != "All":
        query += " AND a.category = ?"
        params.append(filter_category)
    if filter_search:
        query += " AND (i.name LIKE ? OR a.id LIKE ?)"
        params.extend([f"%{filter_search}%", f"%{filter_search}%"])
    query += " ORDER BY a.submitted_at DESC"

    df = pd.read_sql_query(query, conn, params=params)
    conn.close()

    if not df.empty:
        # Show styled cards or table
        st.dataframe(df, use_container_width=True, hide_index=True)

        st.markdown("---")
        app_list = df["case_id"].tolist()
        sel_case = st.selectbox("Inspect Attached Documents for Dossier", app_list)
        sel_id = int(sel_case.split("-")[-1]) - 1000

        conn = sqlite3.connect(DATABASE_PATH)
        docs_df = pd.read_sql_query("""
            SELECT id, doc_type, filename, upload_date, validation_status, anomaly_score
            FROM documents WHERE application_id = ?
        """, conn, params=(sel_id,))
        conn.close()

        if not docs_df.empty:
            st.dataframe(docs_df, use_container_width=True, hide_index=True)
        else:
            st.info("No documents currently attached to this case dossier.")
    else:
        st.info("No applications match the search criteria.")

# ── Footer ─────────────────────────────────────────────────────────────
render_sih_footer()
