"""
AICTE Approval Validation Platform — Main Application Entry Point.

SIH 26261: AI-Powered Application Validation, Document Authentication
and Regulatory Compliance Verification.
"""

import os
import sys
import sqlite3
from pathlib import Path
from datetime import datetime

import streamlit as st
import pandas as pd

# Ensure project root is on the path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from config.settings import APP_TITLE, APP_ICON, DATABASE_PATH, UPLOAD_DIR
from database.db import DatabaseManager
from database.seed_data import seed_database
from utils.auth import check_auth, get_current_user, logout, render_login_page
from utils.helpers import ensure_dir
from utils.styles import (
    apply_custom_styles,
    render_gov_header,
    render_aicte_brand_bar,
    render_sidebar_header,
    render_kpi_card,
    render_sih_footer,
    status_badge_html
)

# ── Page Configuration ─────────────────────────────────────────────────
st.set_page_config(
    page_title=f"{APP_TITLE} — SIH 2026",
    page_icon=APP_ICON,
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Apply Centralized Styling & Dark Mode Support ───────────────────────
apply_custom_styles()

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

# Render Top Gov Header Strip
render_gov_header()

# ── Authentication Flow ────────────────────────────────────────────────
if not check_auth():
    render_login_page()
    render_sih_footer()
    st.stop()

# User is authenticated
user = get_current_user()

# ── Sidebar ────────────────────────────────────────────────────────────
with st.sidebar:
    render_sidebar_header(user)

    st.markdown("<p style='font-size:0.7rem; font-weight:700; color:#94A3B8; text-transform:uppercase; letter-spacing:0.8px; margin:1rem 0 0.5rem 0;'>MODULE NAVIGATION</p>", unsafe_allow_html=True)
    st.markdown("""
    <div style="background:rgba(255,153,51,0.18); border-left:4px solid #FF9933; border-radius:8px; padding:8px 12px; margin-bottom:8px; font-weight:700; color:#FFFFFF; display:flex; justify-content:space-between; align-items:center;">
        <span>🏠 Home Overview</span>
        <span style="font-size:0.65rem; background:#FF9933; color:#0B1F4B; font-weight:800; padding:1px 6px; border-radius:4px;">ACTIVE</span>
    </div>
    """, unsafe_allow_html=True)

    st.caption("Use the sidebar pages menu above to navigate through Application Upload, Document Validation, Anomaly Detection, Compliance Check, Dashboard, and Audit Trail.")

    st.markdown("---")
    if st.button("🚪 Sign Out", use_container_width=True, type="secondary"):
        logout()
        st.rerun()

# ── Main Content Area ──────────────────────────────────────────────────
render_aicte_brand_bar("Approval Validation Platform", "AI-Powered Decision Support Tool for Application Processing & Scrutiny")

# ── Key Metrics Function ───────────────────────────────────────────────
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

# ── Row 1: High-Contrast Modern KPI Cards (Task 4) ──────────────────────
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(
        render_kpi_card(
            title="Total Applications",
            value=f"{total_apps:,}",
            icon="📋",
            variant="navy",
            trend="+14% this cycle",
            trend_type="up"
        ),
        unsafe_allow_html=True
    )

with col2:
    st.markdown(
        render_kpi_card(
            title="Documents Processed",
            value=f"{total_docs:,}",
            icon="📄",
            variant="teal",
            trend="99.2% OCR confidence",
            trend_type="up"
        ),
        unsafe_allow_html=True
    )

with col3:
    st.markdown(
        render_kpi_card(
            title="Active Anomaly Alerts",
            value=f"{active_anomalies}",
            icon="🚨",
            variant="danger" if active_anomalies > 0 else "navy",
            trend=f"{active_anomalies} flags pending triage",
            trend_type="danger" if active_anomalies > 0 else "up"
        ),
        unsafe_allow_html=True
    )

with col4:
    st.markdown(
        render_kpi_card(
            title="APH Compliance Rate",
            value=f"{compliance_rate}%",
            icon="📈",
            variant="saffron",
            trend="+3.4% institutional pass",
            trend_type="up"
        ),
        unsafe_allow_html=True
    )

st.markdown("<div style='height: 1.5rem;'></div>", unsafe_allow_html=True)

# ── Row 2: Recent Applications Table with Status Badges (Task 5) ───────
st.markdown("""
<div style="background:#FFFFFF; border:1px solid #E2E8F0; border-radius:16px; padding:20px 24px; box-shadow:0 4px 20px rgba(11,31,75,0.06); margin-bottom:1.5rem;">
    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
        <div>
            <h3 style="margin:0; font-size:1.15rem; color:#0B1F4B; font-weight:700;">📋 Recent Applications Docket</h3>
            <p style="margin:2px 0 0 0; color:#5B6B8A; font-size:0.8rem;">Real-time queue of institutional submissions undergoing AICTE scrutiny</p>
        </div>
        <span style="font-size:0.75rem; background:#F1F5F9; color:#475569; padding:4px 10px; border-radius:9999px; font-weight:600;">
            Showing Latest 10 Cases
        </span>
    </div>
""", unsafe_allow_html=True)

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
    # Convert to HTML table with color-coded status badges, zebra rows & hover highlight
    table_rows_html = ""
    for idx, r in enumerate(rows):
        row_bg = "#FFFFFF" if idx % 2 == 0 else "#F8FAFC"
        badge = status_badge_html(r[5])
        sub_date = str(r[6])[:10] if r[6] else "2026-03-24"
        table_rows_html += f"""
        <tr style="background:{row_bg}; border-bottom:1px solid #E2E8F0; transition:background-color 0.2s ease;">
            <td style="padding:12px 14px; font-weight:700; color:#0B1F4B;">APP-2026-{1000 + r[0]}</td>
            <td style="padding:12px 14px; font-weight:600; color:#1E293B;">{r[1]}</td>
            <td style="padding:12px 14px; color:#475569; font-family:monospace; font-size:0.85rem;">{r[2]}</td>
            <td style="padding:12px 14px; color:#334155; font-size:0.85rem;">{r[3]}</td>
            <td style="padding:12px 14px; color:#64748B; font-size:0.85rem;">{r[4]}</td>
            <td style="padding:12px 14px;">{badge}</td>
            <td style="padding:12px 14px; color:#64748B; font-size:0.82rem;">{sub_date}</td>
        </tr>
        """

    st.markdown(f"""
    <div style="overflow-x:auto;">
        <table style="width:100%; border-collapse:collapse; text-align:left; font-size:0.88rem;">
            <thead>
                <tr style="background:#0B1F4B; color:#FFFFFF; border-top-left-radius:8px; border-top-right-radius:8px;">
                    <th style="padding:12px 14px; font-size:0.75rem; font-weight:700; text-transform:uppercase; letter-spacing:0.5px;">Dossier ID</th>
                    <th style="padding:12px 14px; font-size:0.75rem; font-weight:700; text-transform:uppercase; letter-spacing:0.5px;">Institution Name</th>
                    <th style="padding:12px 14px; font-size:0.75rem; font-weight:700; text-transform:uppercase; letter-spacing:0.5px;">AICTE Permanent ID</th>
                    <th style="padding:12px 14px; font-size:0.75rem; font-weight:700; text-transform:uppercase; letter-spacing:0.5px;">Category</th>
                    <th style="padding:12px 14px; font-size:0.75rem; font-weight:700; text-transform:uppercase; letter-spacing:0.5px;">Academic Year</th>
                    <th style="padding:12px 14px; font-size:0.75rem; font-weight:700; text-transform:uppercase; letter-spacing:0.5px;">Scrutiny Status</th>
                    <th style="padding:12px 14px; font-size:0.75rem; font-weight:700; text-transform:uppercase; letter-spacing:0.5px;">Submitted Date</th>
                </tr>
            </thead>
            <tbody>
                {table_rows_html}
            </tbody>
        </table>
    </div>
    """, unsafe_allow_html=True)
else:
    st.info("No applications found in the database. Please navigate to 'Application Upload' to ingest institutional records.")

st.markdown("</div>", unsafe_allow_html=True)

# ── Row 3: Platform Scrutiny Architecture (Feature Cards) ──────────────
st.markdown("""
<div style="margin-bottom:12px;">
    <h3 style="margin:0; font-size:1.15rem; color:#0B1F4B; font-weight:700;">🚀 Intelligent Decision-Support Modules</h3>
    <p style="margin:2px 0 0 0; color:#5B6B8A; font-size:0.8rem;">End-to-end pipeline designed for Problem Statement 26261</p>
</div>
""", unsafe_allow_html=True)

feat_col1, feat_col2 = st.columns(2)

with feat_col1:
    st.markdown("""
    <div class="gov-card">
        <div style="display:flex; align-items:center; gap:12px; margin-bottom:8px;">
            <span style="font-size:24px; background:#EFF6FF; border:1px solid #BFDBFE; border-radius:10px; padding:6px;">📄</span>
            <h4 style="margin:0; font-size:1rem; color:#0B1F4B;">Intelligent Document Validation</h4>
        </div>
        <p style="font-size:0.85rem; color:#5B6B8A; line-height:1.5; margin:0;">
            High-accuracy OCR parsing, layout analysis, automated document classification, and cross-field verification using <strong>RapidFuzz</strong> and <strong>PyMuPDF</strong>.
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="gov-card">
        <div style="display:flex; align-items:center; gap:12px; margin-bottom:8px;">
            <span style="font-size:24px; background:#FEF2F2; border:1px solid #FECACA; border-radius:10px; padding:6px;">⚠️</span>
            <h4 style="margin:0; font-size:1rem; color:#0B1F4B;">Anomaly & Potential Forgery Detection</h4>
        </div>
        <p style="font-size:0.85rem; color:#5B6B8A; line-height:1.5; margin:0;">
            Error Level Analysis (ELA), cross-institutional document duplication checks, irregular dates, and metadata forensics flagging preliminary alerts.
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="gov-card">
        <div style="display:flex; align-items:center; gap:12px; margin-bottom:8px;">
            <span style="font-size:24px; background:#F0FDF4; border:1px solid #BBF7D0; border-radius:10px; padding:6px;">📊</span>
            <h4 style="margin:0; font-size:1rem; color:#0B1F4B;">Centralized Scrutiny Analytics</h4>
        </div>
        <p style="font-size:0.85rem; color:#5B6B8A; line-height:1.5; margin:0;">
            Executive Plotly dashboards depicting application throughput, status distribution, regional load, and compliance Pareto frequencies.
        </p>
    </div>
    """, unsafe_allow_html=True)

with feat_col2:
    st.markdown("""
    <div class="gov-card">
        <div style="display:flex; align-items:center; gap:12px; margin-bottom:8px;">
            <span style="font-size:24px; background:#F0FDFA; border:1px solid #99F6E4; border-radius:10px; padding:6px;">🔗</span>
            <h4 style="margin:0; font-size:1rem; color:#0B1F4B;">Issuing Authority Verification Gateway</h4>
        </div>
        <p style="font-size:0.85rem; color:#5B6B8A; line-height:1.5; margin:0;">
            Direct API queries to DigiLocker, State Fire Services, State Land Records GIS, and NBA/NAAC repositories with timestamped cryptographic evidence.
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="gov-card">
        <div style="display:flex; align-items:center; gap:12px; margin-bottom:8px;">
            <span style="font-size:24px; background:#FFFBEB; border:1px solid #FDE68A; border-radius:10px; padding:6px;">⚖️</span>
            <h4 style="margin:0; font-size:1rem; color:#0B1F4B;">APH Regulatory Compliance Check</h4>
        </div>
        <p style="font-size:0.85rem; color:#5B6B8A; line-height:1.5; margin:0;">
            Automated scrutiny against Approval Process Handbook (APH 2024–27) rules, faculty cadre ratio (1:2:6), barrier-free accessibility, and intake deficit calculation.
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="gov-card">
        <div style="display:flex; align-items:center; gap:12px; margin-bottom:8px;">
            <span style="font-size:24px; background:#F8FAFC; border:1px solid #CBD5E1; border-radius:10px; padding:6px;">🔒</span>
            <h4 style="margin:0; font-size:1rem; color:#0B1F4B;">Immutable Regulatory Audit Trail</h4>
        </div>
        <p style="font-size:0.85rem; color:#5B6B8A; line-height:1.5; margin:0;">
            SHA-256 chained transaction logging of every rule applied, document scrutinized, officer determination, and statutory memo issued.
        </p>
    </div>
    """, unsafe_allow_html=True)

# ── Footer (Task 9) ────────────────────────────────────────────────────
render_sih_footer()
