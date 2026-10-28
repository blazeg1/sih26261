"""
AICTE Approval Validation Platform — Main Application Entry Point.

SIH 26261: AI-Powered Application Validation, Document Authentication
and Regulatory Compliance Verification.
"""

import os
import sys
import sqlite3
from pathlib import Path

import streamlit as st

# Ensure project root is on the path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from config.settings import APP_TITLE, APP_ICON, DATABASE_PATH, UPLOAD_DIR
from database.db import DatabaseManager
from database.seed_data import seed_database
from utils.auth import login_form, check_auth, get_current_user, logout
from utils.helpers import ensure_dir

# ── Page Configuration ─────────────────────────────────────────────────
st.set_page_config(
    page_title=APP_TITLE,
    page_icon=APP_ICON,
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ─────────────────────────────────────────────────────────
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1E3A5F;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.1rem;
        color: #555;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 12px;
        color: white;
        text-align: center;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    .metric-card h3 {
        margin: 0;
        font-size: 2rem;
        font-weight: 700;
    }
    .metric-card p {
        margin: 0.3rem 0 0 0;
        font-size: 0.9rem;
        opacity: 0.9;
    }
    .feature-card {
        background: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 4px solid #1E3A5F;
        margin-bottom: 1rem;
    }
    .feature-card h4 {
        color: #1E3A5F;
        margin-bottom: 0.5rem;
    }
    .status-badge {
        padding: 0.2rem 0.6rem;
        border-radius: 12px;
        font-size: 0.8rem;
        font-weight: 600;
    }
    .badge-approved { background: #d4edda; color: #155724; }
    .badge-review { background: #fff3cd; color: #856404; }
    .badge-submitted { background: #cce5ff; color: #004085; }
    .badge-rejected { background: #f8d7da; color: #721c24; }
    div[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1E3A5F 0%, #2C5F8A 100%);
    }
    div[data-testid="stSidebar"] .stMarkdown {
        color: white;
    }
    div[data-testid="stSidebar"] label {
        color: white !important;
    }
</style>
""", unsafe_allow_html=True)

# ── Initialize Database & Directories ──────────────────────────────────
@st.cache_resource
def init_app():
    """Initialize the application: create database and seed data."""
    ensure_dir(os.path.dirname(DATABASE_PATH))
    ensure_dir(UPLOAD_DIR)
    db = DatabaseManager(DATABASE_PATH)
    db.init_db()
    seed_database(DATABASE_PATH)
    return True

init_app()

# ── Sidebar ────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(f"## {APP_ICON} AICTE Validator")
    st.markdown("---")

    if check_auth():
        user = get_current_user()
        if user:
            st.markdown(f"👤 **{user['full_name']}**")
            st.markdown(f"🏷️ Role: `{user['role']}`")
            st.markdown(f"🏢 {user['department']}")
        st.markdown("---")
        if st.button("🚪 Logout", use_container_width=True):
            logout()
            st.rerun()
        st.markdown("---")
        st.markdown("### 📌 Navigation")
        st.markdown("""
        - 📋 Application Upload
        - 🔍 Document Validation
        - ⚠️ Anomaly Detection
        - ✅ Compliance Check
        - 📊 Dashboard
        - 📝 Audit Trail
        """)
    else:
        st.markdown("### 🔐 Login")
        login_form()

# ── Main Content ───────────────────────────────────────────────────────
if not check_auth():
    st.markdown('<p class="main-header">🏛️ AICTE Approval Validation Platform</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">AI-Powered Application Validation, Document Authentication & Regulatory Compliance Verification</p>', unsafe_allow_html=True)
    st.info("👈 Please log in using the sidebar to access the platform.\n\n**Demo Credentials:**\n- Admin: `admin` / `admin123`\n- Reviewer: `reviewer1` / `review123`\n- Viewer: `viewer1` / `viewer123`")
    st.stop()

# ── Dashboard Overview ─────────────────────────────────────────────────
st.markdown('<p class="main-header">🏛️ AICTE Approval Validation Platform</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">AI-Powered Decision Support for Application Processing & Document Verification</p>', unsafe_allow_html=True)

# Key Metrics
def get_metrics():
    """Fetch key metrics from the database."""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM applications")
    total_apps = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM documents")
    total_docs = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM anomaly_alerts WHERE is_resolved = 0")
    active_anomalies = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM compliance_checks WHERE status = 'COMPLIANT'")
    compliant = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM compliance_checks")
    total_checks = cursor.fetchone()[0]
    compliance_rate = round((compliant / max(total_checks, 1)) * 100, 1)

    conn.close()
    return total_apps, total_docs, active_anomalies, compliance_rate

total_apps, total_docs, active_anomalies, compliance_rate = get_metrics()

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(f"""
    <div class="metric-card" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);">
        <h3>{total_apps}</h3>
        <p>Total Applications</p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="metric-card" style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);">
        <h3>{total_docs}</h3>
        <p>Documents Processed</p>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div class="metric-card" style="background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);">
        <h3>{active_anomalies}</h3>
        <p>Active Anomaly Alerts</p>
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown(f"""
    <div class="metric-card" style="background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%);">
        <h3>{compliance_rate}%</h3>
        <p>Compliance Rate</p>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# Recent Applications
st.markdown("### 📋 Recent Applications")
conn = sqlite3.connect(DATABASE_PATH)
cursor = conn.cursor()
cursor.execute("""
    SELECT a.id, i.name, i.aicte_id, a.category, a.academic_year, a.status, a.submitted_at
    FROM applications a
    JOIN institutions i ON a.institution_id = i.id
    ORDER BY a.submitted_at DESC
    LIMIT 10
""")
rows = cursor.fetchall()
conn.close()

if rows:
    import pandas as pd
    df = pd.DataFrame(rows, columns=["ID", "Institution", "AICTE ID", "Category", "Academic Year", "Status", "Submitted"])
    st.dataframe(df, use_container_width=True, hide_index=True)
else:
    st.info("No applications found. Upload an application to get started.")

st.markdown("---")

# Feature Cards
st.markdown("### 🚀 Platform Features")
feat_col1, feat_col2 = st.columns(2)

with feat_col1:
    st.markdown("""
    <div class="feature-card">
        <h4>📄 Intelligent Document Validation</h4>
        <p>OCR-based extraction, document classification, completeness checks, and cross-document consistency verification.</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="feature-card">
        <h4>⚠️ Anomaly & Forgery Detection</h4>
        <p>Detect suspicious alterations, duplicate documents, metadata inconsistencies, and other anomalies with evidence-linked alerts.</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="feature-card">
        <h4>📊 Real-Time Dashboard</h4>
        <p>Centralized view of application status, deficiencies, verification results, and pending actions with interactive Plotly charts.</p>
    </div>
    """, unsafe_allow_html=True)

with feat_col2:
    st.markdown("""
    <div class="feature-card">
        <h4>🔗 Issuing Authority Verification</h4>
        <p>Verify documents through authorized APIs, official portals, QR codes, and digital signatures with recorded audit trails.</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="feature-card">
        <h4>✅ Regulatory Compliance Check</h4>
        <p>Compare applications against configurable checklists from AICTE Approval Process Handbook with category-wise scoring.</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="feature-card">
        <h4>📝 Complete Audit Trail</h4>
        <p>Full traceability of rules applied, records checked, source responses, alerts, and actions taken for accountability.</p>
    </div>
    """, unsafe_allow_html=True)

# Footer
st.markdown("---")
st.markdown(
    "<center><small>🏛️ AICTE Approval Validation Platform — SIH 26261 | "
    "AI-Powered Decision Support System</small></center>",
    unsafe_allow_html=True,
)
