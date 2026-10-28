"""
PRAMAAN Module 7: Review Queue & Officer Decision Workbench.

Empowers AICTE Scrutiny Officers to execute regulatory decisions, issue statutory
Section 10(k) Deficiency Memos, refer cases to Standing Hearing Committees, and order EVCs.
"""

import os
import sys
import json
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta

import streamlit as st
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config.settings import DATABASE_PATH
from utils.auth import get_current_user
from utils.theme import apply_pramaan_theme, render_top_gov_banner, render_pramaan_header, render_sahayak_copilot

st.set_page_config(page_title="Review Queue — PRAMAAN", page_icon="⚖️", layout="wide")
apply_pramaan_theme()

render_top_gov_banner()
user = get_current_user() or {"full_name": "Dr. Rajeshwar Pant", "role": "Senior Scrutiny Officer", "department": "Bureau of Approval"}
render_pramaan_header(user)
render_sahayak_copilot()

st.markdown("""
<div style="background:white; border-radius:10px; padding:16px 20px; margin-bottom:1.2rem; border:1px solid #E2E8F0;">
    <h3 style="margin:0; color:#0F172A; font-weight:800;">⚖️ Review Queue & Scrutiny Decision Workbench</h3>
    <p style="margin:4px 0 0 0; color:#64748B; font-size:0.85rem;">
        Officer Decision Desk · Statutory Section 10(k) Notice Generator · Standing Hearing Committee Referrals.
    </p>
</div>
""", unsafe_allow_html=True)

conn = sqlite3.connect(DATABASE_PATH)
queue_df = pd.read_sql_query("""
    SELECT a.id, ('APP-2026-' || (1000 + a.id)) as case_id, i.name as institution,
           i.state, a.category, a.status,
           (SELECT COUNT(*) FROM anomaly_alerts aa WHERE aa.application_id = a.id AND aa.is_resolved = 0) as flags
    FROM applications a
    JOIN institutions i ON a.institution_id = i.id
    ORDER BY flags DESC, a.id ASC
""", conn)

tasks_df = pd.read_sql_query("""
    SELECT * FROM tasks WHERE is_completed = 0 ORDER BY priority DESC
""", conn)
conn.close()

tab_workbench, tab_tasks, tab_memo_gen = st.tabs([
    "📥 Assigned Scrutiny Queue",
    "🎯 Officer Action Items (4 Critical)",
    "📜 Deficiency Memo & Notice Generator",
])

# ── TAB 1: Assigned Scrutiny Queue ────────────────────────────────────
with tab_workbench:
    st.markdown("##### 📂 Priority Queue: Active Cases Requiring Officer Disposition")
    
    col_k1, col_k2 = st.columns([7, 3])
    with col_k1:
        st.dataframe(queue_df, use_container_width=True, hide_index=True)

    with col_k2:
        st.markdown("""
        <div style="background:#0F172A; border:1px solid #334155; border-radius:10px; padding:16px; color:white;">
            <div style="font-size:0.75rem; font-weight:700; color:#60A5FA;">DISPOSITION GUIDELINES (APH 2024-27)</div>
            <div style="font-size:0.8rem; line-height:1.6; margin-top:8px;">
                • <strong>Green Flag Cases:</strong> Immediate EoA Clearance.<br>
                • <strong>Deficiency in Documents:</strong> Issue Section 10(k) Rectification Notice (10 Days).<br>
                • <strong>Expired NOC / Mismatch:</strong> Withhold approval pending verified renewal.<br>
                • <strong>Suspected Forgery / Splicing:</strong> Refer to Standing Hearing Committee (SHC).
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("##### 🎯 Execute Decision on Selected Case")

    sc_col1, sc_col2 = st.columns(2)
    with sc_col1:
        target_case = st.selectbox("Select Case to Dispose", queue_df["case_id"].tolist(), index=0)
        target_app_id = int(target_case.split("-")[-1]) - 1000
        
        decision = st.selectbox(
            "Regulatory Determination",
            [
                "Issue Section 10(k) Rectification Notice (10-Day Window)",
                "Clear & Recommend for Extension of Approval (EoA)",
                "Refer to Standing Hearing Committee (SHC) for Inquiry",
                "Order Surprise Expert Visiting Committee (EVC)",
                "Reject Application (Grounds of Non-Compliance)"
            ]
        )
        officer_remarks = st.text_area(
            "Officer Scrutiny Remarks (Recorded in Audit Trail)",
            value="NOC renewal required. Discrepancy observed in Fire Safety Certificate expiry. Rectification required within 10 days."
        )

    with sc_col2:
        st.markdown("##### 🔒 Digital Authorization & Dispatch")
        st.write(f"Scrutiny Officer: **{user.get('full_name', 'Dr. Rajeshwar Pant')}**")
        st.write(f"Role: **{user.get('role', 'Senior Scrutiny Officer')}**")
        st.write(f"Timestamp: **{datetime.now().strftime('%Y-%m-%d %H:%M:%S IST')}**")

        if st.button("🚀 Sign & Dispatch Regulatory Order", type="primary"):
            conn = sqlite3.connect(DATABASE_PATH)
            new_status = "DEFICIENCY_ISSUED" if "Deficiency" in decision else \
                         "APPROVED" if "Recommend" in decision else \
                         "REFERRED_SHC" if "Hearing" in decision else "UNDER_REVIEW"

            conn.execute("UPDATE applications SET status = ?, reviewed_by = ? WHERE id = ?", (new_status, user.get("username", "rajeshwar.pant"), target_app_id))
            conn.execute("""
                INSERT INTO audit_trail (application_id, action, actor, details, ip_address, timestamp)
                VALUES (?, 'DECISION_DISPATCHED', ?, ?, '10.14.22.8', ?)
            """, (target_app_id, user.get("username", "rajeshwar.pant"), f"Disposition: {decision}. Remarks: {officer_remarks}", datetime.now().isoformat()))
            conn.commit()
            conn.close()

            st.success(f"✅ Regulatory decision executed successfully! Application {target_case} moved to stage: **{new_status}**.")

# ── TAB 2: Officer Action Items ───────────────────────────────────────
with tab_tasks:
    st.markdown("##### 🎯 Officer Operational Tasks & Daily Triage")
    if not tasks_df.empty:
        for _, t in tasks_df.iterrows():
            urgency_badge = "🔴 CRITICAL" if t["priority"] == "CRITICAL" else "🟠 HIGH" if t["priority"] == "HIGH" else "🔵 NORMAL"
            st.markdown(f"""
            <div style="background:#FFFFFF; border:1px solid #E2E8F0; border-radius:8px; padding:14px; margin-bottom:10px; color:#0F172A;">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <span style="font-size:0.75rem; font-weight:700;">{urgency_badge} · Due: {t.get('due_date', 'Today')}</span>
                    <span style="font-size:0.75rem; color:#64748B;">Task #{t['id']}</span>
                </div>
                <h4 style="margin:4px 0; color:#0F172A;">{t['title']}</h4>
                <div style="font-size:0.82rem; color:#475569;">{t['description']}</div>
            </div>
            """, unsafe_allow_html=True)

            if st.button(f"Mark Task #{t['id']} Complete", key=f"tsk_{t['id']}"):
                conn = sqlite3.connect(DATABASE_PATH)
                conn.execute("UPDATE tasks SET is_completed = 1 WHERE id = ?", (int(t['id']),))
                conn.commit()
                conn.close()
                st.rerun()
    else:
        st.success("All operational tasks completed for today.")

# ── TAB 3: Deficiency Memo & Notice Generator ─────────────────────────
with tab_memo_gen:
    st.markdown("##### 📜 Official Section 10(k) Rectification Notice Generator")

    conn = sqlite3.connect(DATABASE_PATH)
    inst_info = pd.read_sql_query("""
        SELECT a.id, ('APP-2026-' || (1000 + a.id)) as case_id, i.name, i.aicte_id, i.address, i.city, i.state
        FROM applications a JOIN institutions i ON a.institution_id = i.id
        WHERE a.id = ?
    """, conn, params=(target_app_id,)).iloc[0]
    conn.close()

    deadline_date = (datetime.now() + timedelta(days=10)).strftime("%d %B %Y")

    memo_text = f"""
========================================================================================
                      ALL INDIA COUNCIL FOR TECHNICAL EDUCATION
                       (A STATUTORY BODY OF THE GOVT. OF INDIA)
                   Nelson Mandela Marg, Vasant Kunj, New Delhi-110070
========================================================================================

F.No. AICTE/AB/NRC/{inst_info['case_id']}/DEF-NOTICE-2026                 Dated: {datetime.now().strftime("%d-%m-%Y")}

To,
The Chairman / Secretary,
{inst_info['name']}
{inst_info['address']}, {inst_info['city']}, {inst_info['state']}
AICTE Permanent Institute ID: {inst_info['aicte_id']}

SUBJECT: DEFICIENCY RECTIFICATION NOTICE UNDER REGULATION 10(k) OF AICTE APPROVAL
         PROCESS HANDBOOK (APH 2024-27) FOR ACADEMIC SESSION 2026-27.

Sir / Madam,

1. This is in reference to your application {inst_info['case_id']} submitted on the AICTE Portal
   for Extension of Approval (EoA) / Approval Changes for the Academic Session 2026-27.

2. On preliminary AICTE scrutiny through the PRAMAAN Verification Platform, the following
   regulatory deficiencies / discrepancies have been identified against prescribed norms:

   [DEFICIENCY 01 - CRITICAL]:
   • Document: Fire & Life Safety Certificate (NOC).
   • Finding: The uploaded certificate (Ref: NOC/ST/2024/84920) expired on 14-03-2026 as per
     verification with the State Fire Services Portal. An unexpired, valid NOC is mandatory
     under APH 2024-27 Chapter IV Clause 4.1.2.

   [DEFICIENCY 02 - CADRE DISCREPANCY]:
   • Norm: Cadre Ratio of 1:2:6 (Professors : Associate Professors : Assistant Professors).
   • Finding: Deficiency observed in Associate Professor cadre strength by 2 faculty members.

3. In terms of Regulation 10(k) of the AICTE Approval Process Regulations, you are hereby given
   a statutory opportunity to rectify the aforesaid deficiencies by uploading authentic supporting
   documents on the AICTE Portal on or before:

                         RECTIFICATION DEADLINE: {deadline_date} (5:00 PM IST)

4. Failure to rectify within the stipulated time may result in withholding of Extension of Approval (EoA),
   reduction in intake, or referral to the Standing Hearing Committee (SHC) without further notice.

By Order of Competent Authority,

(Dr. Rajeshwar Pant)
Senior Scrutiny Officer
Bureau of Approval, AICTE, New Delhi
Digitally Signed through PRAMAAN GovTech System
========================================================================================
    """

    st.text_area("Generated AICTE Official Notice Preview", value=memo_text, height=400)
    st.download_button(
        "📥 Download Formal Notice (AICTE_Section_10k_Notice.txt)",
        data=memo_text,
        file_name=f"AICTE_Deficiency_Notice_{inst_info['case_id']}.txt",
        mime="text/plain"
    )
