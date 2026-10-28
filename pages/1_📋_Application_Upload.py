"""
Page 1: Application Upload

Handles uploading new applications and documents,
running OCR, classifying documents, and extracting data.
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
    APP_TITLE, DATABASE_PATH, UPLOAD_DIR,
    SUPPORTED_EXTENSIONS, ApplicationCategories, DocumentTypes,
)
from utils.auth import check_auth, require_role, get_current_user
from utils.helpers import ensure_dir, compute_file_hash, get_timestamp

# ── Page Config ────────────────────────────────────────────────────────
st.set_page_config(page_title=f"Application Upload — {APP_TITLE}", page_icon="📋", layout="wide")

# ── Auth Check ─────────────────────────────────────────────────────────
if not check_auth():
    st.warning("🔒 Please log in from the main page to access this section.")
    st.stop()

user = get_current_user()
if user and user["role"] not in ("ADMIN", "REVIEWER"):
    st.error("⛔ You need ADMIN or REVIEWER role to access this page.")
    st.stop()

# ── CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .upload-card {
        background: #f0f7ff;
        padding: 1.2rem;
        border-radius: 10px;
        border: 1px solid #d0e3f7;
        margin-bottom: 1rem;
    }
    .doc-preview {
        background: #fafafa;
        padding: 1rem;
        border-radius: 8px;
        border-left: 3px solid #1E3A5F;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

st.title("📋 Application Upload & Management")

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
tab_upload, tab_view = st.tabs(["📤 Upload New Application", "📋 View Applications"])

# ════════════════════════════════════════════════════════════════════════
#  TAB 1: Upload New Application
# ════════════════════════════════════════════════════════════════════════
with tab_upload:
    col_form, col_preview = st.columns([1, 1])

    with col_form:
        st.markdown("### 🏫 Institution Details")

        # Fetch existing institutions
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, aicte_id FROM institutions ORDER BY name")
        inst_rows = cursor.fetchall()
        conn.close()

        inst_options = {f"{row[1]} ({row[2]})": row[0] for row in inst_rows}
        inst_options["➕ Add New Institution"] = -1

        selected_inst = st.selectbox("Select Institution", options=list(inst_options.keys()))
        institution_id = inst_options[selected_inst]

        # New institution form
        if institution_id == -1:
            st.markdown("#### New Institution Details")
            new_name = st.text_input("Institution Name *")
            new_aicte_id = st.text_input("AICTE ID *", placeholder="e.g., 1-9347281")
            new_university = st.text_input("Affiliated University *")
            nc1, nc2 = st.columns(2)
            with nc1:
                new_state = st.text_input("State *")
            with nc2:
                new_city = st.text_input("City *")
            new_address = st.text_area("Full Address")
            new_year = st.number_input("Established Year", min_value=1900, max_value=2026, value=2010)

        st.markdown("---")
        st.markdown("### 📝 Application Details")

        categories = [
            ApplicationCategories.EOA,
            ApplicationCategories.NEW_INSTITUTION,
            ApplicationCategories.ADD_PROGRAMME,
            ApplicationCategories.CHANGE_OF_SITE,
            ApplicationCategories.CLOSURE,
        ]
        app_category = st.selectbox("Application Category *", categories)
        academic_year = st.text_input("Academic Year *", value="2025-26", placeholder="e.g., 2025-26")

        st.markdown("---")
        st.markdown("### 📁 Upload Documents")

        uploaded_files = st.file_uploader(
            "Upload PDF/Image documents",
            type=["pdf", "jpg", "jpeg", "png"],
            accept_multiple_files=True,
            help="Upload all supporting documents for this application.",
        )

        submit_btn = st.button("🚀 Submit Application", type="primary", use_container_width=True)

    # ── Process & Preview ──────────────────────────────────────────────
    with col_preview:
        st.markdown("### 📄 Document Preview")

        if uploaded_files:
            for i, uploaded_file in enumerate(uploaded_files):
                with st.expander(f"📄 {uploaded_file.name} ({uploaded_file.size / 1024:.1f} KB)", expanded=(i == 0)):
                    file_bytes = uploaded_file.read()
                    uploaded_file.seek(0)

                    file_hash = hashlib.sha256(file_bytes).hexdigest()[:16]
                    st.markdown(f"**Hash:** `{file_hash}...`")

                    if PROCESSING_AVAILABLE:
                        # Classify document
                        ext = os.path.splitext(uploaded_file.name)[1].lower()

                        # Save temporarily for processing
                        ensure_dir(UPLOAD_DIR)
                        temp_path = os.path.join(UPLOAD_DIR, f"temp_{uploaded_file.name}")
                        with open(temp_path, "wb") as f:
                            f.write(file_bytes)

                        try:
                            if ext == ".pdf":
                                proc = PDFProcessor(temp_path)
                                ocr_text = proc.extract_text()
                                metadata = proc.get_metadata()
                                st.markdown(f"**Pages:** {metadata.get('page_count', 'N/A')}")
                                if proc.is_scanned_pdf():
                                    st.info("📷 Scanned PDF detected — OCR will be applied.")
                                    ocr_text = ocr_engine.extract_from_pdf(temp_path)
                            else:
                                ocr_text = ocr_engine.extract_from_image_file(temp_path)
                                metadata = {}

                            # Classify
                            doc_type, confidence = classifier.classify(ocr_text, uploaded_file.name)
                            st.markdown(f"**Detected Type:** `{doc_type}` (confidence: {confidence:.0%})")

                            # Extract fields
                            fields = extractor.extract_fields(ocr_text, doc_type)
                            if fields.get("aicte_id"):
                                st.markdown(f"**AICTE ID:** `{fields['aicte_id']}`")
                            if fields.get("dates"):
                                st.markdown(f"**Dates Found:** {', '.join(fields['dates'][:5])}")
                            if fields.get("institution_name"):
                                st.markdown(f"**Institution:** {fields['institution_name']}")

                            # Show OCR text preview
                            with st.expander("📝 OCR Text Preview"):
                                st.text(ocr_text[:1000] + ("..." if len(ocr_text) > 1000 else ""))

                            # Store in session for submission
                            if "processed_docs" not in st.session_state:
                                st.session_state.processed_docs = {}
                            st.session_state.processed_docs[uploaded_file.name] = {
                                "doc_type": doc_type,
                                "confidence": confidence,
                                "ocr_text": ocr_text,
                                "extracted_fields": fields,
                                "metadata": metadata,
                                "file_hash": hashlib.sha256(file_bytes).hexdigest(),
                            }
                        except Exception as e:
                            st.error(f"Processing error: {e}")
                        finally:
                            if os.path.exists(temp_path):
                                try:
                                    os.remove(temp_path)
                                except OSError:
                                    pass
                    else:
                        st.info("Processing modules not available. File will be saved as-is.")
        else:
            st.info("👈 Upload documents to see preview and extracted information.")

    # ── Submit Application ─────────────────────────────────────────────
    if submit_btn:
        if not uploaded_files:
            st.error("Please upload at least one document.")
        elif not academic_year:
            st.error("Please enter the academic year.")
        else:
            try:
                conn = sqlite3.connect(DATABASE_PATH)
                cursor = conn.cursor()
                now = get_timestamp()

                # Create institution if new
                if institution_id == -1:
                    if not all([new_name, new_aicte_id, new_university, new_state, new_city]):
                        st.error("Please fill all required institution fields.")
                        st.stop()
                    cursor.execute(
                        "INSERT INTO institutions (name, aicte_id, university, state, city, address, established_year, status, created_at, updated_at) "
                        "VALUES (?, ?, ?, ?, ?, ?, ?, 'ACTIVE', ?, ?)",
                        (new_name, new_aicte_id, new_university, new_state, new_city, new_address, new_year, now, now),
                    )
                    institution_id = cursor.lastrowid

                # Create application
                cursor.execute(
                    "INSERT INTO applications (institution_id, category, academic_year, status, submitted_at, created_at, updated_at) "
                    "VALUES (?, ?, ?, 'SUBMITTED', ?, ?, ?)",
                    (institution_id, app_category, academic_year, now, now, now),
                )
                app_id = cursor.lastrowid

                # Save documents
                ensure_dir(UPLOAD_DIR)
                for uploaded_file in uploaded_files:
                    file_bytes = uploaded_file.read()
                    uploaded_file.seek(0)

                    file_hash = hashlib.sha256(file_bytes).hexdigest()
                    safe_name = f"{app_id}_{uploaded_file.name}"
                    file_path = os.path.join(UPLOAD_DIR, safe_name)

                    with open(file_path, "wb") as f:
                        f.write(file_bytes)

                    # Get processed info
                    proc_info = st.session_state.get("processed_docs", {}).get(uploaded_file.name, {})
                    doc_type = proc_info.get("doc_type", "UNKNOWN")
                    ocr_text = proc_info.get("ocr_text", "")
                    extracted = json.dumps(proc_info.get("extracted_fields", {}))

                    cursor.execute(
                        "INSERT INTO documents (application_id, doc_type, filename, file_path, file_hash, upload_date, ocr_text, extracted_data, validation_status, anomaly_score, notes) "
                        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'PENDING_REVIEW', 0.0, '')",
                        (app_id, doc_type, uploaded_file.name, file_path, file_hash, now, ocr_text, extracted),
                    )

                # Audit trail
                cursor.execute(
                    "INSERT INTO audit_trail (application_id, action, actor, details, ip_address, timestamp) "
                    "VALUES (?, 'APPLICATION_SUBMITTED', ?, ?, '127.0.0.1', ?)",
                    (app_id, user["username"] if user else "system",
                     f"Application submitted with {len(uploaded_files)} documents", now),
                )

                conn.commit()
                conn.close()

                st.session_state.pop("processed_docs", None)
                st.success(f"✅ Application #{app_id} submitted successfully with {len(uploaded_files)} documents!")
                st.balloons()

            except Exception as e:
                st.error(f"Submission failed: {e}")

# ════════════════════════════════════════════════════════════════════════
#  TAB 2: View Applications
# ════════════════════════════════════════════════════════════════════════
with tab_view:
    st.markdown("### 📋 All Applications")

    # Filters
    fc1, fc2, fc3 = st.columns(3)
    with fc1:
        filter_status = st.selectbox("Filter by Status", ["All", "SUBMITTED", "UNDER_REVIEW", "APPROVED", "REJECTED"])
    with fc2:
        filter_category = st.selectbox("Filter by Category", ["All"] + [
            ApplicationCategories.EOA, ApplicationCategories.NEW_INSTITUTION,
            ApplicationCategories.ADD_PROGRAMME, ApplicationCategories.CHANGE_OF_SITE,
            ApplicationCategories.CLOSURE,
        ])
    with fc3:
        filter_year = st.text_input("Filter by Academic Year", placeholder="e.g., 2025-26")

    # Query
    conn = sqlite3.connect(DATABASE_PATH)
    query = """
        SELECT a.id, i.name, i.aicte_id, a.category, a.academic_year, a.status,
               a.submitted_at, a.reviewed_by,
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
    if filter_year:
        query += " AND a.academic_year = ?"
        params.append(filter_year)
    query += " ORDER BY a.submitted_at DESC"

    df = pd.read_sql_query(query, conn, params=params)
    conn.close()

    if not df.empty:
        df.columns = ["App ID", "Institution", "AICTE ID", "Category", "Year", "Status", "Submitted", "Reviewer", "Docs"]

        # Color-code status
        def style_status(val):
            colors = {
                "APPROVED": "background-color: #d4edda; color: #155724",
                "UNDER_REVIEW": "background-color: #fff3cd; color: #856404",
                "SUBMITTED": "background-color: #cce5ff; color: #004085",
                "REJECTED": "background-color: #f8d7da; color: #721c24",
            }
            return colors.get(val, "")

        st.dataframe(df, use_container_width=True, hide_index=True)

        # Application Details Expander
        st.markdown("---")
        selected_app_id = st.selectbox("Select Application ID for Details", df["App ID"].tolist())

        if selected_app_id:
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT d.id, d.doc_type, d.filename, d.upload_date, d.validation_status, d.anomaly_score "
                "FROM documents d WHERE d.application_id = ? ORDER BY d.upload_date",
                (int(selected_app_id),),
            )
            docs = cursor.fetchall()
            conn.close()

            if docs:
                st.markdown(f"#### 📁 Documents for Application #{selected_app_id}")
                doc_df = pd.DataFrame(docs, columns=["Doc ID", "Type", "Filename", "Upload Date", "Validation Status", "Anomaly Score"])
                st.dataframe(doc_df, use_container_width=True, hide_index=True)
            else:
                st.info("No documents found for this application.")
    else:
        st.info("No applications match the selected filters.")
