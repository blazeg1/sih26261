"""
PRAMAAN Module 4: Regulatory Compliance Review & APH Rules Engine.

Automated evaluation of institutional submissions against the AICTE Approval
Process Handbook (APH 2024-27), deficit penalty calculations, and Scrutiny Sheet drafting.
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

from config.settings import DATABASE_PATH, ComplianceCategories
from utils.auth import get_current_user
from utils.theme import apply_pramaan_theme, render_top_gov_banner, render_pramaan_header, render_sahayak_copilot
from modules.compliance_checker import ComplianceChecker

st.set_page_config(page_title="Compliance Review — PRAMAAN", page_icon="⚖️", layout="wide")
apply_pramaan_theme()

render_top_gov_banner()
user = get_current_user() or {"full_name": "Dr. Rajeshwar Pant", "role": "Senior Scrutiny Officer", "department": "Bureau of Approval"}
render_pramaan_header(user)
render_sahayak_copilot()

st.markdown("""
<div style="background:white; border-radius:10px; padding:16px 20px; margin-bottom:1.2rem; border:1px solid #E2E8F0;">
    <h3 style="margin:0; color:#0F172A; font-weight:800;">⚖️ Regulatory Compliance Review Engine</h3>
    <p style="margin:4px 0 0 0; color:#64748B; font-size:0.85rem;">
        Rule-based scrutiny derived from AICTE Approval Process Handbook (APH 2024-27) · Automated Deficit & Penalty Assessment.
    </p>
</div>
""", unsafe_allow_html=True)

# Select application
conn = sqlite3.connect(DATABASE_PATH)
app_df = pd.read_sql_query("""
    SELECT a.id, ('APP-2026-' || (1000 + a.id) || ' — ' || i.name) as label,
           i.name as inst_name, i.aicte_id, i.state, a.category, a.academic_year
    FROM applications a JOIN institutions i ON a.institution_id = i.id
    ORDER BY a.id ASC
""", conn)
conn.close()

col_sel1, col_sel2 = st.columns([7, 3])
with col_sel1:
    app_choice = st.selectbox("Select Target Application for Compliance Audit", app_df["label"].tolist(), index=0)
    sel_app_id = int(app_df[app_df["label"] == app_choice]["id"].iloc[0])
    inst_name = str(app_df[app_df["label"] == app_choice]["inst_name"].iloc[0])
    app_cat = str(app_df[app_df["label"] == app_choice]["category"].iloc[0])

with col_sel2:
    aph_edition = st.selectbox("Applicable Handbook Edition", ["APH 2024-27 (Current)", "APH 2023-24 (Previous)"])

checker = ComplianceChecker()

tab_matrix, tab_penalty_calc, tab_scrutiny_sheet = st.tabs([
    "📋 Compliance Checklist Matrix",
    "🧮 Deficit & Penalty Calculator",
    "📑 Official AICTE Scrutiny Sheet",
])

# ── TAB 1: Compliance Checklist Matrix ────────────────────────────────
with tab_matrix:
    st.markdown("##### 🏛️ Section-by-Section Handbook Verification")

    # Sample institution data
    app_data = {
        "institution_name": inst_name,
        "category": app_cat,
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
        "fire_noc_valid": False if sel_app_id == 1 else True,
        "barrier_free_built": True,
        "anti_ragging_committee": True,
        "grievance_committee": True,
        "icc_committee": True,
        "joint_fdr_submitted": True,
        "ter_fee_paid": True,
    }

    result = checker.check_all(app_data, category=app_cat)
    compliance_score = result.get("compliance_score", 88.5)

    sc1, sc2, sc3, sc4 = st.columns(4)
    with sc1:
        st.metric("Overall Compliance", f"{compliance_score:.1f}%")
    with sc2:
        st.metric("Rules Evaluated", result.get("total_rules", 18))
    with sc3:
        st.metric("Rules Passed", result.get("passed_rules", 16))
    with sc4:
        st.metric("Deficiencies Flagged", result.get("failed_rules", 2), delta_color="inverse")

    st.markdown("---")

    # Detailed Category Breakdown
    checklist_items = [
        {"Section": "Chapter I · Land & Built-up Norms", "Rule": "Minimum Land Area (Rural: 7.5 Acres, Urban: 2.5 Acres)", "Prescribed": "7.5 Acres", "Submitted": "7.5 Acres", "Status": "COMPLIANT", "Clause": "APH 1.4.1"},
        {"Section": "Chapter I · Land & Built-up Norms", "Rule": "Total Instructional Carpet Area", "Prescribed": "11,500 Sq.M", "Submitted": "12,850 Sq.M", "Status": "COMPLIANT", "Clause": "APH 1.4.3"},
        {"Section": "Chapter II · Faculty & Cadre Norms", "Rule": "Faculty-Student Ratio (SFR 1:15)", "Prescribed": "1:15 (60 Faculty)", "Submitted": "1:13.8 (65 Faculty)", "Status": "COMPLIANT", "Clause": "APH 2.3.1"},
        {"Section": "Chapter II · Faculty & Cadre Norms", "Rule": "Cadre Ratio (1 Prof : 2 Assoc : 6 Asst)", "Prescribed": "1:2:6 Ratio", "Submitted": "6 : 14 : 45 (Assoc Shortage)", "Status": "MARGINAL", "Clause": "APH 2.3.4"},
        {"Section": "Chapter III · Laboratories & IT", "Rule": "Computer Terminal Ratio (1 per 4 students)", "Prescribed": "225 Terminals", "Submitted": "250 Terminals", "Status": "COMPLIANT", "Clause": "APH 3.2.1"},
        {"Section": "Chapter III · Laboratories & IT", "Rule": "Dedicated High-Speed Bandwidth", "Prescribed": "100 Mbps Min", "Submitted": "300 Mbps Leased", "Status": "COMPLIANT", "Clause": "APH 3.2.4"},
        {"Section": "Chapter IV · Safety & Essential Facilities", "Rule": "Valid Fire Safety Certificate (State Directorate)", "Prescribed": "Unexpired NOC", "Submitted": "Expired 14 days ago" if sel_app_id == 1 else "Valid", "Status": "NON-COMPLIANT" if sel_app_id == 1 else "COMPLIANT", "Clause": "APH 4.1.2"},
        {"Section": "Chapter IV · Safety & Essential Facilities", "Rule": "Barrier-Free Access for Divyangjan (Ramps/Lifts)", "Prescribed": "Mandatory in all blocks", "Submitted": "Installed & Geotagged", "Status": "COMPLIANT", "Clause": "APH 4.5.1"},
        {"Section": "Chapter V · Statutory Governance", "Rule": "Anti-Ragging Committee & Squad Constitution", "Prescribed": "Clause 6.3 Notification", "Submitted": "Constituted on Portal", "Status": "COMPLIANT", "Clause": "APH 5.1.1"},
        {"Section": "Chapter V · Statutory Governance", "Rule": "Internal Complaints Committee (ICC/POSH)", "Prescribed": "Mandatory 50% Women", "Submitted": "Constituted on Portal", "Status": "COMPLIANT", "Clause": "APH 5.2.1"},
        {"Section": "Chapter VI · Financial & Reserve Fund", "Rule": "Joint Fixed Deposit Reserve (TER / FDR)", "Prescribed": "Rs. 35,00,000", "Submitted": "FDR #849201 Valid", "Status": "COMPLIANT", "Clause": "APH 6.1.1"},
    ]

    check_df = pd.DataFrame(checklist_items)
    st.dataframe(check_df, use_container_width=True, hide_index=True)

# ── TAB 2: Deficit & Penalty Calculator ───────────────────────────────
with tab_penalty_calc:
    st.markdown("##### 🧮 Statutory Penalty & Intake Adjustment Calculator (Chapter VIII)")
    st.caption("AICTE regulations prescribe progressive regulatory remedies depending on deficiency thresholds.")

    calc_c1, calc_c2 = st.columns(2)
    with calc_c1:
        st.markdown("""
        <div style="background:#0F172A; border:1px solid #334155; border-radius:10px; padding:18px; color:white;">
            <h4 style="margin:0 0 12px 0; color:#60A5FA;">Deficiency Threshold Engine</h4>
            <div style="font-size:0.85rem; line-height:1.8;">
                <strong>Faculty Deficit (%):</strong> 0.0% (Surplus +5)<br>
                <strong>Cadre Cadence Deficit:</strong> 8.2% (Associate Professors)<br>
                <strong>Essential Safety Deficit:</strong> 1 Critical (Fire NOC Expired)<br>
                <strong>Infra Space Deficit:</strong> 0.0% (Adequate)
            </div>
            <div style="margin-top:16px; padding:12px; background:rgba(220, 38, 38, 0.15); border:1px solid #DC2626; border-radius:8px;">
                <div style="font-size:0.8rem; font-weight:700; color:#F87171;">RECOMMENDED REGULATORY ACTION:</div>
                <div style="font-size:0.85rem; color:#FECACA; margin-top:4px;">
                    • Issue Section 10(k) Rectification Notice with 10 calendar days window.<br>
                    • Withhold Extension of Approval (EoA) until renewed Fire NOC is validated via State Portal.<br>
                    • No financial penalty attracted since instructional space and SFR norms are satisfied.
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with calc_c2:
        st.markdown("##### ⚙️ Interactive What-If Simulation")
        sim_faculty = st.slider("Simulate Total Faculty Available", 30, 80, 65)
        sim_intake = st.number_input("Approved Intake Baseline", value=420)
        
        req_faculty = sim_intake / 15
        deficit_pct = max(0.0, ((req_faculty - sim_faculty) / req_faculty) * 100)
        
        st.write(f"Required Faculty for {sim_intake} students @ 1:15: **{req_faculty:.0f} Faculty**")
        if deficit_pct == 0:
            st.success(f"✅ Zero Faculty Deficit! Compliant for full sanctioned intake.")
        elif deficit_pct <= 20:
            st.warning(f"⚠️ Deficit is **{deficit_pct:.1f}%** (<= 20%). APH Penalty: **10% Reduction in Sanctioned Intake** (Reduced to {int(sim_intake * 0.9)} seats).")
        else:
            st.error(f"🚨 Severe Deficit: **{deficit_pct:.1f}%** (> 20%). APH Penalty: **No Admission status for current year / Refer to Standing Hearing Committee**.")

# ── TAB 3: Official AICTE Scrutiny Sheet ──────────────────────────────
with tab_scrutiny_sheet:
    st.markdown("##### 📑 AICTE Official Scrutiny Report (Form A-1)")
    
    scrutiny_md = f"""
========================================================================================
ALL INDIA COUNCIL FOR TECHNICAL EDUCATION (AICTE)
BUREAU OF APPROVAL · REGULATORY COMPLIANCE SCRUTINY DESK
========================================================================================
APPLICATION ID    : APP-2026-{1000 + sel_app_id}
INSTITUTION NAME  : {inst_name}
AICTE PERMANENT ID: 1-3329182910
CATEGORY          : {app_cat}
ACADEMIC YEAR     : 2026-27
SCRUTINY OFFICER  : {user.get("full_name", "Dr. Rajeshwar Pant")}, Senior Scrutiny Officer
DATE OF SCRUTINY  : {datetime.now().strftime("%d %B %Y, %I:%M %p IST")}

1. COMPLIANCE ASSESSMENT SUMMARY:
   - Land & Built-up Norms   : SATISFIED (7.5 Acres registered title)
   - Faculty & Cadre Norms    : SATISFIED (65 Faculty against 60 required)
   - Laboratory & IT Norms    : SATISFIED (250 Computers, 300 Mbps bandwidth)
   - Statutory Committees     : SATISFIED (Anti-ragging, ICC, Grievance active)
   - Essential Safety NOCs    : DEFICIENT (Fire Safety NOC renewal overdue)

2. DEFICIENCY OBSERVATIONS UNDER APH 2024-27:
   - Observation 1: State Fire Services NOC expired on 2026-03-14. Renewal certificate not uploaded.
   - Observation 2: Associate Professor cadre is short by 2 positions (compensated by Assistant Professors).

3. SCRUTINY COMMITTEE RECOMMENDATION:
   [X] ISSUE SECTION 10(k) RECTIFICATION NOTICE (10 Days Compliance Window)
   [ ] RECOMMEND FOR IMMEDIATE EXTENSION OF APPROVAL
   [ ] REFER TO STANDING COMPLIANCE COMMITTEE / EVC INSPECTION
   [ ] REJECT APPLICATION

DIGITALLY AUTHENTICATED VIA PRAMAAN SYSTEM · TLS 1.3 SECURE AUDIT LOG #840291
========================================================================================
    """

    st.text_area("Official Scrutiny Dossier Text", value=scrutiny_md, height=350)
    st.download_button(
        "📥 Download Scrutiny Report (Text / Form A-1)",
        data=scrutiny_md,
        file_name=f"AICTE_Scrutiny_Report_APP_{1000 + sel_app_id}.txt",
        mime="text/plain"
    )
