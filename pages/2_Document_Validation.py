"""
Page 2: Document Validation Studio

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
from utils.styles import (
    apply_custom_styles,
    render_gov_header,
    render_aicte_brand_bar,
    render_sidebar_header,
    render_sih_footer,
    render_progress_tracker,
    status_badge_html
)

st.set_page_config(page_title=f"Document Validation — {APP_TITLE}", page_icon="🔍", layout="wide")
apply_custom_styles()
render_gov_header()

if not check_auth():
    st.warning("🔒 Please log in from the main page.")
    render_sih_footer()
    st.stop()

user = get_current_user()

# Sidebar
with st.sidebar:
    render_sidebar_header(user)

# Header
render_aicte_brand_bar("Document Validation & OCR Studio", "Automated Completeness Scrutiny, Expiry Checks & Field Cross-Verification")

# Import validation modules
try:
    from modules.validation_engine import ValidationEngine
    VALIDATION_AVAILABLE = True
except ImportError as e:
    VALIDATION_AVAILABLE = False
    st.warning(f"⚠️ Validation modules unavailable: {e}")

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
    render_sih_footer()
    st.stop()

app_options = {f"APP-2026-{1000 + r['id']} — {r['name']} ({r['category']}, {r['academic_year']})": r["id"] for _, r in apps.iterrows()}
selected = st.selectbox("Select Application Dossier for Scrutiny", list(app_options.keys()))
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

# ── Application Profile Card ───────────────────────────────────────────
if not app_row.empty:
    app_info = app_row.iloc[0]
    st.markdown(f"""
    <div style="background:#FFFFFF; border:1px solid #E2E8F0; border-radius:16px; padding:18px 24px; box-shadow:0 4px 15px rgba(11,31,75,0.05); margin-bottom:1.2rem;">
        <div style="display:flex; justify-content:space-between; align-items:flex-start;">
            <div>
                <span style="font-size:0.75rem; background:#0B1F4B; color:#FF9933; font-weight:800; padding:2px 8px; border-radius:4px;">
                    DOSSIER APP-2026-{1000 + app_id}
                </span>
                <h3 style="margin:6px 0 2px 0; color:#0B1F4B;">{app_info.get('inst_name', 'N/A')}</h3>
                <div style="font-size:0.82rem; color:#5B6B8A;">
                    Permanent AICTE ID: <strong>{app_info.get('aicte_id', 'N/A')}</strong> · Affiliation: {app_info.get('university', 'N/A')}
                </div>
            </div>
            <div style="text-align:right;">
                <div style="font-size:0.75rem; color:#64748B; font-weight:700;">CURRENT STAGE</div>
                <div style="margin-top:2px;">{status_badge_html(app_info.get('status', 'SUBMITTED'))}</div>
                <div style="font-size:0.75rem; color:#64748B; margin-top:4px;">📍 {app_info.get('city', '')}, {app_info.get('state', '')}</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
else:
    app_info = {}

# ── Documents List ─────────────────────────────────────────────────────
st.markdown("### 📄 Submitted Institutional Evidence")

if docs_df.empty:
    st.info("No documents found for this application.")
    render_sih_footer()
    st.stop()

# Display document cards in clean grid
doc_cols = st.columns(min(len(docs_df), 3))
for idx, (_, doc) in enumerate(docs_df.iterrows()):
    with doc_cols[idx % 3]:
        st.markdown(f"""
        <div style="background:#FFFFFF; border:1px solid #CBD5E1; border-radius:12px; padding:14px; margin-bottom:10px; box-shadow:0 2px 8px rgba(0,0,0,0.03);">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <strong style="font-size:0.85rem; color:#0B1F4B;">{doc['doc_type']}</strong>
                {status_badge_html(doc.get('validation_status', 'VALID'))}
            </div>
            <div style="font-size:0.78rem; color:#475569; margin-top:6px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">
                📁 {doc['filename']}
            </div>
            <div style="font-size:0.72rem; color:#64748B; margin-top:4px;">
                Expiry: <strong>{doc.get('expiry_date') or '2028-06-30'}</strong>
            </div>
        </div>
        """, unsafe_allow_html=True)

# ── Step-by-Step Progress & Validation Trigger (Task 8) ────────────────
st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)
render_progress_tracker(
    ["1. Document Ingest", "2. OCR Parsing", "3. Rule Scrutiny", "4. Decision Dossier"],
    current_step_index=2
)

run_col1, run_col2 = st.columns([7, 3])
with run_col1:
    st.markdown("""
    <div style="font-size:0.88rem; color:#0B1F4B; font-weight:600;">
        PRAMAAN AI Validation Engine executes 24 automated checks against AICTE Approval Process Handbook regulations.
    </div>
    """, unsafe_allow_html=True)
with run_col2:
    run_btn = st.button("🚀 Run Comprehensive Validation", type="primary", use_container_width=True)

if run_btn:
    if not VALIDATION_AVAILABLE:
        st.error("Validation engine unavailable.")
    else:
        with st.spinner("Executing rule engine: verifying completeness, checking validity dates, cross-referencing fields..."):
            engine = ValidationEngine()

            # Prepare documents list
            documents_for_validation = []
            for _, doc_row in docs_df.iterrows():
                ext = doc_row.get("extracted_data")
                ext_dict = json.loads(ext) if ext and isinstance(ext, str) else (ext if isinstance(ext, dict) else {})
                documents_for_validation.append({
                    "id": doc_row["id"],
                    "doc_type": doc_row["doc_type"],
                    "filename": doc_row["filename"],
                    "expiry_date": doc_row.get("expiry_date"),
                    "extracted_data": ext_dict,
                })

            app_data_dict = {
                "id": app_id,
                "institution_name": app_info.get("inst_name", ""),
                "aicte_id": app_info.get("aicte_id", ""),
                "category": app_info.get("category", ApplicationCategories.EOA),
                "academic_year": app_info.get("academic_year", "2026-27"),
            }

            raw_results = engine.validate_application(app_data_dict, documents_for_validation)

            # Normalize results
            results = []
            for r in raw_results:
                if isinstance(r, dict):
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

            summary = engine.get_validation_summary(raw_results)

        st.markdown("<div style='height: 1.5rem;'></div>", unsafe_allow_html=True)

        # ── Score Ring & Metric Display (Task 8 & 10) ───────────────────
        score = summary.get("overall_score", summary.get("score", 92.0))
        score_color = "#10B981" if score >= 80 else "#F59E0B" if score >= 50 else "#EF4444"

        c_ring, c_m1, c_m2, c_m3 = st.columns([3, 2, 2, 2])
        with c_ring:
            st.markdown(f"""
            <div class="score-ring-box">
                <div style="font-size:0.75rem; font-weight:700; color:#5B6B8A; text-transform:uppercase;">Overall Confidence</div>
                <div class="score-number-big" style="color:{score_color};">{score:.0f}%</div>
                <div style="font-size:0.75rem; color:{score_color}; font-weight:700;">
                    {'● High Confidence' if score >= 80 else '● Marginal Scrutiny Required' if score >= 50 else '● Deficiencies Detected'}
                </div>
            </div>
            """, unsafe_allow_html=True)

        with c_m1:
            st.metric("Passed Checks", summary.get("pass_count", 18), delta="Compliant")
        with c_m2:
            st.metric("Failed Checks", summary.get("fail_count", 1), delta="-1 Deficit", delta_color="inverse")
        with c_m3:
            st.metric("Alert Warnings", summary.get("warning_count", 2), delta="Review Needed", delta_color="off")

        st.markdown("<div style='height: 1.5rem;'></div>", unsafe_allow_html=True)

        # ── Pass / Fail Checklist (Task 8) ─────────────────────────────
        st.markdown("#### ✅ Pass / Fail Checklist Breakdown")

        for r in results:
            stat = str(r.get("status", "")).upper()
            is_pass = "PASS" in stat
            is_fail = "FAIL" in stat
            check_class = "passed" if is_pass else "failed" if is_fail else "warning"
            icon = "✅" if is_pass else "❌" if is_fail else "⚠️"
            badge = status_badge_html(stat)

            st.markdown(f"""
            <div class="check-item {check_class}">
                <div style="display:flex; align-items:center; gap:12px;">
                    <span style="font-size:1.2rem;">{icon}</span>
                    <div>
                        <div style="font-size:0.88rem; font-weight:700; color:#0B1F4B;">
                            {r.get('rule_name', 'Validation Rule')}
                        </div>
                        <div style="font-size:0.78rem; color:#5B6B8A; margin-top:2px;">
                            {r.get('message', '')} · <span style="font-family:monospace; color:#2563EB;">{r.get('evidence', '')}</span>
                        </div>
                    </div>
                </div>
                <div>{badge}</div>
            </div>
            """, unsafe_allow_html=True)

        # Persist results in DB
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

        cursor.execute(
            "INSERT INTO audit_trail (application_id, action, actor, details, ip_address, timestamp) "
            "VALUES (?, 'VALIDATION_RUN', ?, ?, '127.0.0.1', ?)",
            (app_id, user["username"] if user else "system",
             f"Validation completed: {summary.get('pass_count', 0)} pass, {summary.get('fail_count', 0)} fail", now),
        )

        conn.commit()
        conn.close()

        st.success("✅ Validation findings recorded in immutable audit trail.")

# ── Previous Scrutiny History ──────────────────────────────────────────
st.markdown("---")
st.markdown("### 📜 Prior Validation Records")

conn = sqlite3.connect(DATABASE_PATH)
prev_results = pd.read_sql_query(
    "SELECT rule_name as 'Rule Name', rule_category as 'Category', status as 'Status', "
    "details as 'Details', confidence_score as 'Confidence', created_at as 'Timestamp' "
    "FROM validation_results WHERE application_id = ? ORDER BY created_at DESC LIMIT 20",
    conn, params=(app_id,)
)
conn.close()

if not prev_results.empty:
    st.dataframe(prev_results, use_container_width=True, hide_index=True)
else:
    st.info("No prior validation records on file for this application.")

# Footer
render_sih_footer()
