"""
Page 4: Regulatory Compliance Review Studio

Evaluates institutional submissions against the AICTE Approval Process Handbook
(APH 2024–27), calculates faculty cadre ratios, and flags regulatory deficits.
"""

import sys
import sqlite3
from pathlib import Path

import streamlit as st
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config.settings import APP_TITLE, DATABASE_PATH
from modules.compliance_checker import ComplianceCategory
from utils.auth import check_auth, get_current_user
from utils.helpers import get_timestamp
from utils.styles import (
    apply_custom_styles,
    render_gov_header,
    render_aicte_brand_bar,
    render_sidebar_header,
    render_sidebar_logout,
    render_sih_footer,
    render_progress_tracker,
    status_badge_html
)

st.set_page_config(page_title=f"Compliance Review — {APP_TITLE}", page_icon="✅", layout="wide")
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
    render_sidebar_logout("compliance")

# Header
render_aicte_brand_bar("Regulatory Compliance Review Engine", "Rule Scrutiny Derived from AICTE Approval Process Handbook (APH 2024-27)")

try:
    from modules.compliance_checker import ComplianceChecker
    CHECKER_AVAILABLE = True
except ImportError as e:
    CHECKER_AVAILABLE = False
    st.warning(f"⚠️ Compliance checker module unavailable: {e}")

# ── Select Application ─────────────────────────────────────────────────
conn = sqlite3.connect(DATABASE_PATH)
apps = pd.read_sql_query(
    "SELECT a.id, ('APP-2026-' || (1000 + a.id)) as case_id, i.name as inst_name, a.category, a.academic_year "
    "FROM applications a JOIN institutions i ON a.institution_id = i.id "
    "ORDER BY a.id ASC", conn
)
conn.close()

if apps.empty:
    st.info("No applications found in the database.")
    render_sih_footer()
    st.stop()

app_choices = {f"{r['case_id']} — {r['inst_name']}": r["id"] for _, r in apps.iterrows()}
selected_label = st.selectbox("Select Target Application Dossier", list(app_choices.keys()), index=0)
app_id = app_choices[selected_label]

# Step Progress Tracker (Task 8)
render_progress_tracker(
    ["1. Application Ingest", "2. Norms Checklist", "3. Deficit Assessment", "4. Statutory Order"],
    current_step_index=2
)

# Application Data & Mock Inspection Numbers
app_data = {
    "institution_name": selected_label.split("—")[-1].strip(),
    "category": "EOA",
    "land_area_acres": 7.5,
    "built_up_area_sqm": 12850,
    "total_faculty": 65,
    "sanctioned_intake": 420,
    "student_count": 900,
    "cadre_professors": 6,
    "cadre_assoc_professors": 14,
    "cadre_asst_professors": 45,
    "computer_terminals": 250,
    "internet_bandwidth_mbps": 300,
    "fire_noc_valid": False if app_id == 1 else True,
    "barrier_free_built": True,
    "anti_ragging_committee": True,
    "grievance_committee": True,
    "icc_committee": True,
    "joint_fdr_submitted": True,
    "ter_fee_paid": True,
}

checker = ComplianceChecker()
raw_checks = checker.check_compliance(app_data)
result = checker.get_compliance_summary(raw_checks)
score = result.get("compliance_score", checker.get_compliance_score(raw_checks))
score_color = "#10B981" if score >= 80 else "#F59E0B" if score >= 50 else "#EF4444"

# ── Overall Score Ring & Overview Metrics (Task 8 & 10) ────────────────
c_ring, c_p1, c_p2, c_p3 = st.columns([3, 2, 2, 2])

with c_ring:
    st.markdown(
        f'<div class="score-ring-box">'
        f'<div style="font-size:0.75rem; font-weight:700; color:#5B6B8A; text-transform:uppercase;">Overall Compliance</div>'
        f'<div class="score-number-big" style="color:{score_color};">{score:.1f}%</div>'
        f'<div style="font-size:0.75rem; color:{score_color}; font-weight:700;">'
        f'{"● High Regulatory Compliance" if score >= 80 else "● Deficit Notice Required"}'
        f'</div>'
        f'</div>',
        unsafe_allow_html=True
    )

with c_p1:
    st.metric("Total Rules Tested", result.get("total_rules", 18), delta="Handbook Norms")
with c_p2:
    st.metric("Compliant Rules", result.get("passed_rules", 16), delta="Passed")
with c_p3:
    st.metric("Deficiencies Flagged", result.get("failed_rules", 2), delta="-2 Deficits", delta_color="inverse")

st.markdown("<div style='height: 1.5rem;'></div>", unsafe_allow_html=True)

# ── Pass / Fail Checklist Breakdown (Task 8) ───────────────────────────
st.markdown("### 📋 AICTE Approval Process Handbook (APH) Rule Checklist")

compliance_rules = [
    {"category": "Chapter I · Land & Built-up Norms", "rule": "Minimum Land Area (Rural: 7.5 Acres, Urban: 2.5 Acres)", "prescribed": "7.5 Acres", "submitted": "7.5 Acres", "status": "COMPLIANT", "clause": "APH 1.4.1"},
    {"category": "Chapter I · Land & Built-up Norms", "rule": "Total Instructional Carpet Area", "prescribed": "11,500 Sq.M", "submitted": "12,850 Sq.M", "status": "COMPLIANT", "clause": "APH 1.4.3"},
    {"category": "Chapter II · Faculty & Cadre Norms", "rule": "Faculty-Student Ratio (SFR 1:15)", "prescribed": "1:15 (60 Faculty)", "submitted": "1:13.8 (65 Faculty)", "status": "COMPLIANT", "clause": "APH 2.3.1"},
    {"category": "Chapter II · Faculty & Cadre Norms", "rule": "Cadre Ratio (1 Prof : 2 Assoc : 6 Asst)", "prescribed": "1:2:6 Ratio", "submitted": "6 : 14 : 45 (Assoc Shortage)", "status": "PARTIAL", "clause": "APH 2.3.4"},
    {"category": "Chapter III · Laboratories & IT", "rule": "Computer Terminal Ratio (1 per 4 students)", "prescribed": "225 Terminals", "submitted": "250 Terminals", "status": "COMPLIANT", "clause": "APH 3.2.1"},
    {"category": "Chapter III · Laboratories & IT", "rule": "Dedicated Leased Bandwidth", "prescribed": "100 Mbps Min", "submitted": "300 Mbps Leased", "status": "COMPLIANT", "clause": "APH 3.2.4"},
    {"category": "Chapter IV · Safety & Essential Facilities", "rule": "Valid Fire Safety Certificate (State Directorate)", "prescribed": "Unexpired NOC", "submitted": "Expired 14 days ago" if app_id == 1 else "Valid", "status": "NON_COMPLIANT" if app_id == 1 else "COMPLIANT", "clause": "APH 4.1.2"},
    {"category": "Chapter IV · Safety & Essential Facilities", "rule": "Barrier-Free Access for Divyangjan (Ramps/Lifts)", "prescribed": "Mandatory in all blocks", "submitted": "Installed & Verified", "status": "COMPLIANT", "clause": "APH 4.5.1"},
    {"category": "Chapter V · Statutory Governance", "rule": "Anti-Ragging Committee & Squad Constitution", "prescribed": "Clause 6.3 Notification", "submitted": "Constituted on Portal", "status": "COMPLIANT", "clause": "APH 5.1.1"},
    {"category": "Chapter VI · Financial & Reserve Fund", "rule": "Joint Fixed Deposit Reserve (TER / FDR)", "prescribed": "Rs. 35,00,000", "submitted": "FDR #849201 Valid", "status": "COMPLIANT", "clause": "APH 6.1.1"},
]

for item in compliance_rules:
    is_comp = item["status"] == "COMPLIANT"
    is_part = item["status"] == "PARTIAL"
    check_class = "passed" if is_comp else "warning" if is_part else "failed"
    icon = "✅" if is_comp else "⚠️" if is_part else "❌"
    badge = status_badge_html(item["status"])

    st.markdown(
        f'<div class="check-item {check_class}">'
        f'<div style="display:flex; align-items:center; gap:12px;">'
        f'<span style="font-size:1.2rem;">{icon}</span>'
        f'<div>'
        f'<div style="font-size:0.88rem; font-weight:700; color:#0B1F4B;">'
        f'{item["rule"]} <span style="font-size:0.75rem; color:#5B6B8A; font-weight:400;">({item["clause"]})</span>'
        f'</div>'
        f'<div style="font-size:0.78rem; color:#64748B; margin-top:2px;">'
        f'Prescribed: <strong>{item["prescribed"]}</strong> · Submitted: <strong>{item["submitted"]}</strong>'
        f'</div>'
        f'</div>'
        f'</div>'
        f'<div>{badge}</div>'
        f'</div>',
        unsafe_allow_html=True
    )

# ── Save Compliance Audit Action ───────────────────────────────────────
st.markdown("---")
c_btn1, c_btn2 = st.columns([7, 3])
with c_btn1:
    st.caption("Record official compliance evaluation into AICTE Master Database and update Scrutiny Ledger.")
with c_btn2:
    if st.button("💾 Persist Compliance Findings", type="primary", use_container_width=True):
        conn = sqlite3.connect(DATABASE_PATH)
        now = get_timestamp()
        for item in compliance_rules:
            conn.execute("""
                INSERT INTO compliance_checks (application_id, category, rule_id, rule_name, status, deficiency_details, checked_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (app_id, item["category"][:30], item["clause"], item["rule"], item["status"], f"Submitted: {item['submitted']}", now))

        conn.execute("""
            INSERT INTO audit_trail (application_id, action, actor, details, ip_address, timestamp)
            VALUES (?, 'COMPLIANCE_EVALUATION', ?, ?, '127.0.0.1', ?)
        """, (app_id, user["username"] if user else "system", f"Evaluated 10 APH rules. Overall compliance: {score:.1f}%", now))
        conn.commit()
        conn.close()
        st.success("✅ Compliance findings successfully recorded in official audit trail!")

# Footer
render_sih_footer()
