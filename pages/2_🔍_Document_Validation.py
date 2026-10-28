"""
Page 2: Document Validation

Runs automated validation checks on application documents including
completeness, expiry, field consistency, and cross-document verification.
"""

import os
import sys
import json
import sqlite3
from pathlib import Path

import streamlit as st
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config.settings import APP_TITLE, DATABASE_PATH, ApplicationCategories
from utils.auth import check_auth, get_current_user
from utils.helpers import get_timestamp, status_icon

st.set_page_config(page_title=f"Document Validation — {APP_TITLE}", page_icon="🔍", layout="wide")

if not check_auth():
    st.warning("🔒 Please log in from the main page.")
    st.stop()

user = get_current_user()

# Import validation modules
try:
    from modules.validation_engine import ValidationEngine
    VALIDATION_AVAILABLE = True
except ImportError as e:
    VALIDATION_AVAILABLE = False
    st.warning(f"⚠️ Validation modules unavailable: {e}")

st.markdown("""
<style>
    .val-pass { color: #155724; background: #d4edda; padding: 0.3rem 0.8rem; border-radius: 8px; display: inline-block; margin: 2px; }
    .val-fail { color: #721c24; background: #f8d7da; padding: 0.3rem 0.8rem; border-radius: 8px; display: inline-block; margin: 2px; }
    .val-warn { color: #856404; background: #fff3cd; padding: 0.3rem 0.8rem; border-radius: 8px; display: inline-block; margin: 2px; }
    .score-card { text-align: center; padding: 1.5rem; border-radius: 12px; }
</style>
""", unsafe_allow_html=True)

st.title("🔍 Document Validation")

# ── Select Application ─────────────────────────────────────────────────
conn = sqlite3.connect(DATABASE_PATH)
apps = pd.read_sql_query(
    "SELECT a.id, i.name, a.category, a.academic_year, a.status "
    "FROM applications a JOIN institutions i ON a.institution_id = i.id "
    "ORDER BY a.submitted_at DESC", conn
)
conn.close()

if apps.empty:
    st.info("No applications found. Please upload an application first.")
    st.stop()

app_options = {f"App #{r['id']} — {r['name']} ({r['category']}, {r['academic_year']})": r["id"] for _, r in apps.iterrows()}
selected = st.selectbox("Select Application", list(app_options.keys()))
app_id = app_options[selected]

# Get application details and documents
conn = sqlite3.connect(DATABASE_PATH)
app_row = pd.read_sql_query(
    "SELECT a.*, i.name as inst_name, i.aicte_id, i.university, i.state, i.city "
    "FROM applications a JOIN institutions i ON a.institution_id = i.id WHERE a.id = ?",
    conn, params=(app_id,)
)
docs_df = pd.read_sql_query(
    "SELECT * FROM documents WHERE application_id = ? ORDER BY doc_type", conn, params=(app_id,)
)
conn.close()

# ── Application Info ───────────────────────────────────────────────────
if not app_row.empty:
    app_info = app_row.iloc[0]
    ci1, ci2, ci3, ci4 = st.columns(4)
    with ci1:
        st.metric("Institution", app_info.get("inst_name", "N/A"))
    with ci2:
        st.metric("AICTE ID", app_info.get("aicte_id", "N/A"))
    with ci3:
        st.metric("Category", app_info.get("category", "N/A"))
    with ci4:
        st.metric("Status", app_info.get("status", "N/A"))
else:
    app_info = {}

st.markdown("---")

# ── Documents List ─────────────────────────────────────────────────────
st.markdown("### 📄 Application Documents")

if docs_df.empty:
    st.info("No documents found for this application.")
    st.stop()

# Display document cards
for _, doc in docs_df.iterrows():
    icon = status_icon(str(doc.get("validation_status", "")))
    with st.expander(f"{icon} {doc['doc_type']} — {doc['filename']} ({doc['validation_status']})"):
        dc1, dc2, dc3 = st.columns(3)
        with dc1:
            st.markdown(f"**Type:** {doc['doc_type']}")
            st.markdown(f"**Upload Date:** {doc.get('upload_date', 'N/A')}")
        with dc2:
            st.markdown(f"**Expiry Date:** {doc.get('expiry_date', 'N/A')}")
            st.markdown(f"**Validation:** {doc['validation_status']}")
        with dc3:
            st.markdown(f"**Anomaly Score:** {doc.get('anomaly_score', 0.0):.2f}")
            st.markdown(f"**Hash:** `{str(doc.get('file_hash', ''))[:16]}...`")

        # Show extracted text
        ocr_text = doc.get("ocr_text")
        if ocr_text:
            with st.expander("📝 Extracted Text"):
                st.text(str(ocr_text)[:2000])

        # Show extracted data
        extracted = doc.get("extracted_data")
        if extracted:
            try:
                ext_data = json.loads(extracted) if isinstance(extracted, str) else extracted
                with st.expander("📊 Extracted Fields"):
                    st.json(ext_data)
            except (json.JSONDecodeError, TypeError):
                pass

st.markdown("---")

# ── Run Validation ─────────────────────────────────────────────────────
st.markdown("### 🔬 Run Validation Checks")

if st.button("🚀 Run Full Validation", type="primary", use_container_width=True):
    if not VALIDATION_AVAILABLE:
        st.error("Validation modules are not available.")
        st.stop()

    with st.spinner("Running validation checks..."):
        progress = st.progress(0)

        # Determine checklist
        category = app_info.get("category", ApplicationCategories.EOA) if app_info is not None else ApplicationCategories.EOA
        checklist_map = {
            ApplicationCategories.EOA: "config/checklists/eoa_checklist.json",
            ApplicationCategories.NEW_INSTITUTION: "config/checklists/new_institution_checklist.json",
        }
        checklist_path = checklist_map.get(category, "config/checklists/eoa_checklist.json")

        try:
            engine = ValidationEngine(checklist_path)
        except Exception:
            engine = ValidationEngine("config/checklists/eoa_checklist.json")

        # Prepare application data
        documents = []
        for _, doc in docs_df.iterrows():
            doc_dict = doc.to_dict()
            try:
                ed = doc_dict.get("extracted_data")
                if ed and isinstance(ed, str):
                    doc_dict["extracted_data"] = json.loads(ed)
            except (json.JSONDecodeError, TypeError):
                doc_dict["extracted_data"] = {}
            documents.append(doc_dict)

        application_data = {
            "institution_name": app_info.get("inst_name", "") if app_info is not None else "",
            "aicte_id": app_info.get("aicte_id", "") if app_info is not None else "",
            "category": category,
            "academic_year": app_info.get("academic_year", "") if app_info is not None else "",
            "documents": documents,
        }

        progress.progress(30)

        # Run validation — returns list of Pydantic ValidationResult objects
        raw_results = engine.validate_application(application_data)
        progress.progress(70)

        # Convert Pydantic models to dicts for easy access
        results = []
        for r in raw_results:
            if hasattr(r, "model_dump"):
                d = r.model_dump()
                # Enum values to strings
                if hasattr(d.get("status"), "value"):
                    d["status"] = d["status"].value
                elif isinstance(d.get("status"), str):
                    pass
                results.append(d)
            elif isinstance(r, dict):
                results.append(r)
            else:
                results.append({
                    "rule_name": getattr(r, "rule_name", ""),
                    "category": getattr(r, "category", ""),
                    "status": getattr(r, "status", "").value if hasattr(getattr(r, "status", ""), "value") else str(getattr(r, "status", "")),
                    "message": getattr(r, "message", ""),
                    "evidence": getattr(r, "evidence", ""),
                    "confidence": getattr(r, "confidence", 0.0),
                })

        # Get summary
        summary = engine.get_validation_summary(raw_results)
        progress.progress(100)

        # ── Display Results ────────────────────────────────────────────
        st.markdown("### 📊 Validation Results")

        # Overall Score
        score = summary.get("overall_score", summary.get("score", 0))
        sc1, sc2, sc3, sc4 = st.columns(4)
        with sc1:
            color = "#28a745" if score >= 80 else "#ffc107" if score >= 50 else "#dc3545"
            st.markdown(f"""
            <div class="score-card" style="background: {color}22; border: 2px solid {color};">
                <h2 style="color: {color}; margin: 0;">{score:.0f}%</h2>
                <p>Overall Score</p>
            </div>
            """, unsafe_allow_html=True)
        with sc2:
            st.metric("✅ Passed", summary.get("pass_count", 0))
        with sc3:
            st.metric("❌ Failed", summary.get("fail_count", 0))
        with sc4:
            st.metric("⚠️ Warnings", summary.get("warning_count", 0))

        st.markdown("---")

        # Results by category
        categories = {}
        for r in results:
            cat = r.get("category", "OTHER")
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(r)

        if categories:
            tabs = st.tabs(list(categories.keys()))
            for tab, (cat_name, cat_results) in zip(tabs, categories.items()):
                with tab:
                    for r in cat_results:
                        status = str(r.get("status", ""))
                        icon = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
                        bg = "#d4edda" if status == "PASS" else "#f8d7da" if status == "FAIL" else "#fff3cd"

                        st.markdown(f"""
                        <div style="padding: 0.5rem; margin: 0.3rem 0; border-radius: 6px; background: {bg};">
                            {icon} <strong>{r.get('rule_name', 'Unknown Rule')}</strong> — {r.get('message', '')}
                            <br><small>Evidence: {r.get('evidence', 'N/A')} | Confidence: {r.get('confidence', 0):.0%}</small>
                        </div>
                        """, unsafe_allow_html=True)

        # Save results to database
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        now = get_timestamp()

        for r in results:
            cursor.execute(
                "INSERT INTO validation_results (document_id, application_id, rule_name, rule_category, status, details, evidence, confidence_score, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    None,
                    app_id,
                    r.get("rule_name", ""),
                    r.get("category", ""),
                    str(r.get("status", "")),
                    r.get("message", ""),
                    str(r.get("evidence", "") or ""),
                    r.get("confidence", 0.0),
                    now,
                ),
            )

        # Audit trail
        cursor.execute(
            "INSERT INTO audit_trail (application_id, action, actor, details, ip_address, timestamp) "
            "VALUES (?, 'VALIDATION_RUN', ?, ?, '127.0.0.1', ?)",
            (app_id, user["username"] if user else "system",
             f"Validation completed: {summary.get('pass_count', 0)} pass, {summary.get('fail_count', 0)} fail", now),
        )

        conn.commit()
        conn.close()

        st.success("✅ Validation results saved to database.")

# ── Previous Validation Results ────────────────────────────────────────
st.markdown("---")
st.markdown("### 📜 Previous Validation Results")

conn = sqlite3.connect(DATABASE_PATH)
prev_results = pd.read_sql_query(
    "SELECT rule_name, rule_category, status, details, confidence_score, created_at "
    "FROM validation_results WHERE application_id = ? ORDER BY created_at DESC LIMIT 50",
    conn, params=(app_id,)
)
conn.close()

if not prev_results.empty:
    st.dataframe(prev_results, use_container_width=True, hide_index=True)
else:
    st.info("No previous validation results. Click 'Run Full Validation' above.")
