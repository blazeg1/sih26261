"""
PRAMAAN — प्रमाण से विश्वास
Institutional Verification & Regulatory Compliance Intelligence Platform
AICTE / Ministry of Education, Government of India.
"""

import os
import sys
import sqlite3
from pathlib import Path

import streamlit as st
import pandas as pd

# Ensure project root is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from config.settings import APP_TITLE, APP_ICON, DATABASE_PATH, UPLOAD_DIR
from database.db import DatabaseManager
from database.seed_data import seed_database
from utils.auth import login_form, check_auth, get_current_user, logout
from utils.helpers import ensure_dir
from utils.theme import apply_pramaan_theme, render_top_gov_banner, render_pramaan_header, render_sahayak_copilot

# ── Page Configuration ─────────────────────────────────────────────────
st.set_page_config(
    page_title="PRAMAAN — AICTE Regulatory Compliance Intelligence Platform",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Inject PRAMAAN Theme ───────────────────────────────────────────────
apply_pramaan_theme()

# ── Initialize Database & Seed ─────────────────────────────────────────
@st.cache_resource
def init_pramaan_app():
    """Ensure database and seed data are ready."""
    ensure_dir(os.path.dirname(DATABASE_PATH))
    ensure_dir(UPLOAD_DIR)
    db = DatabaseManager(DATABASE_PATH)
    db.init_db()
    seed_database(DATABASE_PATH, force=False)
    return True

init_pramaan_app()

# Auto-login demo user if not logged in
if not check_auth():
    st.session_state["user"] = {
        "username": "rajeshwar.pant",
        "full_name": "Dr. Rajeshwar Pant",
        "role": "ADMIN",
        "department": "Bureau of Approval & Regulatory Compliance",
    }

user = get_current_user()

# ── Sidebar: Operational Modules ───────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="display:flex; align-items:center; gap:10px; padding: 10px 0 16px 0; border-bottom: 1px solid #1E293B;">
        <span style="font-size:2rem;">🏛️</span>
        <div>
            <div style="font-size:1.15rem; font-weight:800; color:#F8FAFC; letter-spacing:-0.5px;">PRAMAAN</div>
            <div style="font-size:0.7rem; color:#60A5FA; font-weight:600;">AICTE REGULATORY PLATFORM</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<p style='font-size:0.7rem; font-weight:700; color:#64748B; text-transform:uppercase; margin-top:1rem; letter-spacing:0.8px;'>OPERATIONAL MODULES (10 ACTIVE)</p>", unsafe_allow_html=True)

    st.markdown("""
    <div style="background:#2563EB; border-radius:8px; padding:8px 12px; margin-bottom:4px; font-weight:600; color:white; display:flex; justify-content:space-between; align-items:center;">
        <span>📊 Dashboard</span>
        <span style="font-size:0.75rem; background:rgba(255,255,255,0.25); padding:1px 6px; border-radius:4px;">DESK</span>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div style="color:#CBD5E1; font-size:0.85rem; padding: 6px 10px; display:flex; justify-content:space-between; align-items:center;">
        <span>📋 My Applications</span>
        <span style="background:#334155; color:#94A3B8; font-size:0.7rem; padding:1px 6px; border-radius:4px;">12</span>
    </div>
    <div style="color:#CBD5E1; font-size:0.85rem; padding: 6px 10px; display:flex; justify-content:space-between; align-items:center;">
        <span>🔍 Document Intelligence</span>
        <span style="background:#1E3A8A; color:#93C5FD; font-size:0.7rem; padding:1px 6px; border-radius:4px;">OCR</span>
    </div>
    <div style="color:#CBD5E1; font-size:0.85rem; padding: 6px 10px; display:flex; justify-content:space-between; align-items:center;">
        <span>🔗 Source Verification</span>
        <span style="background:#064E3B; color:#6EE7B7; font-size:0.7rem; padding:1px 6px; border-radius:4px;">DIGILOCKER</span>
    </div>
    <div style="color:#CBD5E1; font-size:0.85rem; padding: 6px 10px; display:flex; justify-content:space-between; align-items:center;">
        <span>⚖️ Compliance Review</span>
        <span style="background:#334155; color:#94A3B8; font-size:0.7rem; padding:1px 6px; border-radius:4px;">7</span>
    </div>
    <div style="color:#CBD5E1; font-size:0.85rem; padding: 6px 10px; display:flex; justify-content:space-between; align-items:center;">
        <span>🏗️ Infrastructure Review</span>
        <span style="background:#78350F; color:#FDE68A; font-size:0.7rem; padding:1px 6px; border-radius:4px;">CV</span>
    </div>
    <div style="color:#CBD5E1; font-size:0.85rem; padding: 6px 10px; display:flex; justify-content:space-between; align-items:center;">
        <span>🤖 AI-Assisted Findings</span>
        <span style="background:#881337; color:#FDA4AF; font-size:0.7rem; padding:1px 6px; border-radius:4px;">4 FLAG</span>
    </div>
    <div style="color:#CBD5E1; font-size:0.85rem; padding: 6px 10px; display:flex; justify-content:space-between; align-items:center;">
        <span>⏱️ Review Queue</span>
        <span style="background:#7F1D1D; color:#FECACA; font-size:0.7rem; padding:1px 6px; border-radius:4px;">2 CRITICAL</span>
    </div>
    <div style="color:#CBD5E1; font-size:0.85rem; padding: 6px 10px; display:flex; justify-content:space-between; align-items:center;">
        <span>📝 Audit Trail</span>
        <span style="background:#334155; color:#94A3B8; font-size:0.7rem; padding:1px 6px; border-radius:4px;">17</span>
    </div>
    <div style="color:#CBD5E1; font-size:0.85rem; padding: 6px 10px; display:flex; justify-content:space-between; align-items:center;">
        <span>📈 Analytics & Reports</span>
        <span style="background:#334155; color:#94A3B8; font-size:0.7rem; padding:1px 6px; border-radius:4px;">PLOTLY</span>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    if st.button("🚪 Sign Out", use_container_width=True):
        logout()
        st.rerun()

# ── Main Content Area ──────────────────────────────────────────────────
render_top_gov_banner()
render_pramaan_header(user)
render_sahayak_copilot()

# ── Operational Desk Welcome Banner ───────────────────────────────────
st.markdown("""
<div style="background:white; border-radius:12px; padding:20px 24px; margin-bottom:1.5rem; border:1px solid #E2E8F0; box-shadow:0 1px 4px rgba(0,0,0,0.03);">
    <div style="display:flex; justify-content:space-between; align-items:center;">
        <div>
            <div style="font-size:0.75rem; font-weight:700; color:#2563EB; letter-spacing:0.8px; text-transform:uppercase;">
                REGULATORY WORKSPACE · PRAMAAN Operational Desk
            </div>
            <div style="font-size:1.6rem; font-weight:800; color:#0F172A; margin: 4px 0 2px 0;">
                Welcome back, Dr. Rajeshwar Pant
            </div>
            <div style="font-size:0.88rem; color:#64748B;">
                Senior Scrutiny Officer · Bureau of Approval & Regulatory Compliance
            </div>
        </div>
        <div style="text-align:right;">
            <div style="font-size:0.72rem; color:#94A3B8; font-weight:700; text-transform:uppercase;">TODAY'S SCRUTINY STATUS</div>
            <div style="display:inline-flex; align-items:center; gap:6px; color:#059669; font-weight:700; font-size:0.95rem; margin-top:2px;">
                🟢 12 Active Case Dossiers in Jurisdiction
            </div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ── Hero Action Cards (Continue Last Case + Today's Triage Priorities) ──
col_case, col_triage = st.columns([1, 1])

with col_case:
    st.markdown("""
    <div class="hero-case-card" style="border-left: 4px solid #2563EB;">
        <div style="display:flex; justify-content:space-between; align-items:flex-start;">
            <div>
                <div class="hero-case-tag">📑 CONTINUE LAST CASE · <span style="color:#64748B; font-weight:400;">Saved: 11:19:15 PM IST</span></div>
                <div class="hero-case-title">APP-2026-1042 — Aryabhatta Institute of Technology</div>
                <div class="hero-case-meta">Stage: <span style="background:#FEF3C7; color:#92400E; padding:2px 8px; border-radius:4px; font-weight:600;">Under Scrutiny</span> · 8 Documents Evaluated</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    if st.button("Resume Case →", key="btn_resume_hero", type="primary"):
        st.session_state["selected_app_id"] = 1
        st.info("Navigating to Application Dossier APP-2026-1042 (Aryabhatta Institute)... Select 'Document Intelligence' or 'Compliance Review' in the sidebar.")

with col_triage:
    st.markdown("""
    <div class="hero-case-card" style="border-left: 4px solid #DC2626;">
        <div style="display:flex; justify-content:space-between; align-items:flex-start;">
            <div>
                <div class="hero-case-tag" style="color:#DC2626;">⏰ TODAY'S TRIAGE PRIORITIES · <span style="color:#DC2626; font-weight:700;">2 Critical Items Due</span></div>
                <div class="hero-case-title" style="font-size:1.05rem;">APP-2026-1042 Fire NOC check · APP-2026-1087 Rectification...</div>
                <div class="hero-case-meta">4 total officer tasks pending statutory action before regulatory cut-off</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    if st.button("View Tasks (4)", key="btn_view_tasks"):
        st.session_state["active_tab"] = "tasks"

# ── Operational Workload & Priority Triage (6 Metric Cards) ───────────
st.markdown("<p style='font-size:0.8rem; font-weight:700; color:#475569; text-transform:uppercase; letter-spacing:0.8px; margin: 1.5rem 0 0.75rem 0;'>OPERATIONAL WORKLOAD & PRIORITY TRIAGE</p>", unsafe_allow_html=True)

conn = sqlite3.connect(DATABASE_PATH)
cursor = conn.cursor()

# Query counts
cursor.execute("SELECT COUNT(*) FROM applications")
assigned_cases = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM applications WHERE status = 'UNDER_REVIEW'")
awaiting_review = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM anomaly_alerts WHERE severity IN ('HIGH', 'CRITICAL') AND is_resolved = 0")
high_attention = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM verification_records")
source_verifications = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM tasks WHERE status = 'PENDING'")
pending_tasks_count = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM infrastructure_evidence WHERE status = 'FLAGGED'")
inspection_flagged = cursor.fetchone()[0]

conn.close()

c1, c2, c3, c4, c5, c6 = st.columns(6)

with c1:
    st.markdown(f"""
    <div class="triage-card">
        <div class="triage-label">ASSIGNED CASES</div>
        <div class="triage-value">{assigned_cases}</div>
        <div class="triage-sub">Full Jurisdiction</div>
    </div>
    """, unsafe_allow_html=True)

with c2:
    st.markdown(f"""
    <div class="triage-card">
        <div class="triage-label">AWAITING MY REVIEW</div>
        <div class="triage-value val-primary">{awaiting_review}</div>
        <div class="triage-sub">Preliminary scrutiny</div>
    </div>
    """, unsafe_allow_html=True)

with c3:
    st.markdown(f"""
    <div class="triage-card">
        <div class="triage-label">CLARIFICATIONS / DEF.</div>
        <div class="triage-value val-warning">1</div>
        <div class="triage-sub">Institution responses</div>
    </div>
    """, unsafe_allow_html=True)

with c4:
    st.markdown(f"""
    <div class="triage-card">
        <div class="triage-label">HIGH ATTENTION</div>
        <div class="triage-value val-danger">{high_attention}</div>
        <div class="triage-sub">Statutory discrepancies</div>
    </div>
    """, unsafe_allow_html=True)

with c5:
    st.markdown(f"""
    <div class="triage-card">
        <div class="triage-label">SOURCE VERIFICATION</div>
        <div class="triage-value val-success">{source_verifications}</div>
        <div class="triage-sub">External API checks</div>
    </div>
    """, unsafe_allow_html=True)

with c6:
    st.markdown(f"""
    <div class="triage-card">
        <div class="triage-label">INSPECTION FLAGGED</div>
        <div class="triage-value val-warning">{inspection_flagged}</div>
        <div class="triage-sub">EVC physical visit</div>
    </div>
    """, unsafe_allow_html=True)

# ── Split Workspace: Dossier Docket vs Live Audit Activity ─────────────
st.markdown("<br>", unsafe_allow_html=True)
col_docket, col_audit = st.columns([7, 3])

with col_docket:
    tab_docket, tab_tasks = st.tabs([
        f"📂 Assigned Applications Docket ({assigned_cases})",
        f"⚡ Actionable Tasks ({pending_tasks_count} Pending) 🔴",
    ])

    with tab_docket:
        conn = sqlite3.connect(DATABASE_PATH)
        docket_df = pd.read_sql_query("""
            SELECT a.id, 'APP-2026-' || (1000 + a.id) as case_id, i.name as institution, 
                   i.state, a.category, a.academic_year, a.status,
                   (SELECT COUNT(*) FROM anomaly_alerts aa WHERE aa.application_id = a.id AND aa.is_resolved = 0) as flags
            FROM applications a
            JOIN institutions i ON a.institution_id = i.id
            ORDER BY a.id ASC
            LIMIT 12
        """, conn)
        conn.close()

        if not docket_df.empty:
            docket_df.columns = ["DB ID", "Case Dossier", "Institution Name", "State", "Category", "Year", "Stage", "Active Flags"]
            st.dataframe(docket_df, use_container_width=True, hide_index=True)
        else:
            st.info("No applications in docket.")

    with tab_tasks:
        conn = sqlite3.connect(DATABASE_PATH)
        tasks_df = pd.read_sql_query("""
            SELECT t.id, t.title, t.priority, t.due_date, t.status, t.notes
            FROM tasks t
            ORDER BY CASE t.priority WHEN 'CRITICAL' THEN 1 WHEN 'HIGH' THEN 2 ELSE 3 END
        """, conn)
        conn.close()

        if not tasks_df.empty:
            tasks_df.columns = ["Task ID", "Action Required", "Priority", "Due Date", "Status", "Notes"]
            st.dataframe(tasks_df, use_container_width=True, hide_index=True)
        else:
            st.success("All officer tasks completed! 🎉")

with col_audit:
    st.markdown("""
    <div style="background:white; border-radius:10px; border:1px solid #E2E8F0; padding:16px; box-shadow:0 1px 4px rgba(0,0,0,0.03);">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
            <div style="font-size:0.75rem; font-weight:700; color:#0F172A; text-transform:uppercase; letter-spacing:0.5px;">RECENT REGULATORY ACTIVITY</div>
            <span style="font-size:0.68rem; color:#059669; font-weight:600;">🟢 Live Stream</span>
        </div>
    """, unsafe_allow_html=True)

    conn = sqlite3.connect(DATABASE_PATH)
    recent_logs = pd.read_sql_query("""
        SELECT action, actor, details, timestamp
        FROM audit_trail
        ORDER BY timestamp DESC
        LIMIT 6
    """, conn)
    conn.close()

    if not recent_logs.empty:
        for _, log in recent_logs.iterrows():
            st.markdown(f"""
            <div style="border-bottom:1px solid #F1F5F9; padding:8px 0;">
                <div style="font-size:0.78rem; font-weight:700; color:#1E293B;">{log['action']}</div>
                <div style="font-size:0.72rem; color:#475569;">{log['details']}</div>
                <div style="font-size:0.68rem; color:#94A3B8; margin-top:2px;">By {log['actor']}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

# ── Footer ─────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("""
<div style="display:flex; justify-content:space-between; align-items:center; font-size:0.75rem; color:#64748B;">
    <div>🏛️ <strong>PRAMAAN Platform</strong> · All India Council for Technical Education (AICTE), New Delhi</div>
    <div>Strictly Confidential · For Authorized AICTE Scrutiny Officers Only</div>
</div>
""", unsafe_allow_html=True)
