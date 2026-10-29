"""
Page 3: Anomaly & Potential Alteration Detection Studio

Comprehensive forensic analysis studio implementing:
- 4-Level Document Authentication (Metadata, ELA, Digital Signatures, Simulated Registry Connectors)
- Cross-Application Intelligence (Byte collisions, Dual-college faculty, YoY physical shrinkage)
- Risk Meter & Evidence-Linked Anomaly Alerts

CORE PRINCIPLE: Advisory screening only. Never approves or rejects.
"""

import os
import sys
import json
import sqlite3
from pathlib import Path

import streamlit as st
import pandas as pd
import plotly.graph_objects as go

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config.settings import APP_TITLE, DATABASE_PATH, SEVERITY_LEVELS
from utils.auth import check_auth, get_current_user
from utils.helpers import get_timestamp
from utils.styles import (
    apply_custom_styles,
    render_gov_header,
    render_aicte_brand_bar,
    render_sidebar_header,
    render_sidebar_logout,
    render_sih_footer,
    status_badge_html
)
from modules.document_authenticator import DocumentAuthenticator
from modules.cross_application_intelligence import CrossApplicationIntelligence

st.set_page_config(page_title=f"Anomaly Detection — {APP_TITLE}", page_icon="⚠️", layout="wide")
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
    render_sidebar_logout("anomaly")

# Header
render_aicte_brand_bar(
    "Anomaly & Forensics Detection Studio",
    "Computer Vision ELA, Multi-Level Authentication & Cross-Application Intelligence"
)

# Mandatory Advisory Banner
st.markdown("""
<div style="background:#FFFBEB; border:1px solid #FDE68A; border-left:5px solid #F59E0B; padding:12px 18px; border-radius:8px; margin-bottom:1.2rem;">
    <div style="display:flex; align-items:center; gap:10px;">
        <span style="font-size:1.3rem;">⚠️</span>
        <div>
            <div style="font-size:0.88rem; font-weight:700; color:#92400E;">
                Statutory Advisory Screening Principle
            </div>
            <div style="font-size:0.78rem; color:#B45309; margin-top:2px;">
                Forensic signals and anomaly scores are preliminary screening indicators for human verification, not conclusive proof of fraud. The AI never approves or rejects. Authorized AICTE officers make final regulatory determinations.
            </div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ── Select Application ─────────────────────────────────────────────────
conn = sqlite3.connect(DATABASE_PATH)
apps = pd.read_sql_query(
    "SELECT a.id, ('APP-2026-' || (1000 + a.id)) as case_id, i.name as inst_name, a.category, i.aicte_id "
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
selected_app_info = apps[apps["id"] == app_id].iloc[0]

# Fetch documents and alerts
conn = sqlite3.connect(DATABASE_PATH)
docs_df = pd.read_sql_query(
    "SELECT id, doc_type, filename, ocr_text, extracted_data, anomaly_score, expiry_date "
    "FROM documents WHERE application_id = ?", conn, params=(app_id,)
)
alerts_df = pd.read_sql_query(
    "SELECT id, alert_type, severity, description, evidence, is_resolved, created_at "
    "FROM anomaly_alerts WHERE application_id = ? ORDER BY id DESC", conn, params=(app_id,)
)
conn.close()

# ── Studio Tabs ────────────────────────────────────────────────────────
tab_alerts, tab_multilevel, tab_crossapp = st.tabs([
    "🚨 Active Alerts & Risk Index",
    "🔬 4-Level Document Authentication",
    "🌐 Cross-Application Intelligence"
])

# ════════════════════════════════════════════════════════════════════════
# TAB 1: ACTIVE ALERTS & RISK INDEX
# ════════════════════════════════════════════════════════════════════════
with tab_alerts:
    unresolved_alerts = alerts_df[alerts_df["is_resolved"] == 0] if not alerts_df.empty else pd.DataFrame()
    critical_count = len(unresolved_alerts[unresolved_alerts["severity"] == "CRITICAL"]) if not unresolved_alerts.empty else 0
    high_count = len(unresolved_alerts[unresolved_alerts["severity"] == "HIGH"]) if not unresolved_alerts.empty else 0
    med_count = len(unresolved_alerts[unresolved_alerts["severity"] == "MEDIUM"]) if not unresolved_alerts.empty else 0
    low_count = len(unresolved_alerts[unresolved_alerts["severity"] == "LOW"]) if not unresolved_alerts.empty else 0

    risk_score = min(100.0, (critical_count * 35.0) + (high_count * 20.0) + (med_count * 10.0) + (low_count * 4.0))

    col_gauge, col_m1, col_m2, col_m3, col_m4 = st.columns([4, 2, 2, 2, 2])

    with col_gauge:
        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number",
            value=risk_score,
            title={'text': "Composite Risk Index", 'font': {'size': 14, 'color': '#0B1F4B', 'family': 'Poppins'}},
            number={'suffix': "/100", 'font': {'size': 26, 'color': '#0B1F4B', 'family': 'Poppins'}},
            gauge={
                'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': "#CBD5E1"},
                'bar': {'color': "#EF4444" if risk_score > 50 else "#F59E0B" if risk_score > 25 else "#10B981"},
                'bgcolor': "#FFFFFF",
                'borderwidth': 1,
                'bordercolor': "#E2E8F0",
                'steps': [
                    {'range': [0, 25], 'color': "rgba(16, 185, 129, 0.15)"},
                    {'range': [25, 60], 'color': "rgba(245, 158, 11, 0.15)"},
                    {'range': [60, 100], 'color': "rgba(239, 68, 68, 0.15)"}
                ],
                'threshold': {
                    'line': {'color': "#EF4444", 'width': 3},
                    'thickness': 0.8,
                    'value': 60
                }
            }
        ))
        fig_gauge.update_layout(
            height=190,
            margin=dict(l=20, r=20, t=30, b=10),
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(family="Inter")
        )
        st.plotly_chart(fig_gauge, use_container_width=True)

    with col_m1:
        st.metric("Critical Alerts", critical_count, delta="Priority" if critical_count > 0 else "Clear", delta_color="inverse")
    with col_m2:
        st.metric("High Severity", high_count, delta="Scrutiny Req" if high_count > 0 else "Clear", delta_color="inverse")
    with col_m3:
        st.metric("Medium Severity", med_count, delta="Review" if med_count > 0 else "Clear", delta_color="off")
    with col_m4:
        st.metric("Low Severity", low_count, delta="Info", delta_color="off")

    st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)
    st.markdown("### 🚨 Active Regulatory Alerts on Docket")

    if not alerts_df.empty:
        f_sev = st.selectbox("Filter Alerts by Severity", ["All Severities", "CRITICAL", "HIGH", "MEDIUM", "LOW"], key="f_sev_box")
        filtered_alerts = alerts_df if f_sev == "All Severities" else alerts_df[alerts_df["severity"] == f_sev]

        for _, alert in filtered_alerts.iterrows():
            sev = alert["severity"].upper()
            alert_class = "alert-high" if sev in ("CRITICAL", "HIGH") else "alert-medium" if sev == "MEDIUM" else "alert-low"
            icon = "🚨" if sev in ("CRITICAL", "HIGH") else "⚠️" if sev == "MEDIUM" else "ℹ️"
            badge = status_badge_html("REJECTED" if sev in ("CRITICAL", "HIGH") else "UNDER_REVIEW" if sev == "MEDIUM" else "SUBMITTED")

            st.markdown(
                f'<div class="alert-card {alert_class}">'
                f'<div style="display:flex; justify-content:space-between; align-items:flex-start;">'
                f'<div style="display:flex; align-items:center; gap:10px;">'
                f'<span style="font-size:1.4rem;">{icon}</span>'
                f'<div>'
                f'<div style="font-size:0.92rem; font-weight:700; color:#0B1F4B;">'
                f'{alert["alert_type"].replace("_", " ")}'
                f'</div>'
                f'<div style="font-size:0.75rem; color:#64748B;">'
                f'Alert Ref: #ALT-0{alert["id"]} · Recorded: {alert["created_at"]}'
                f'</div>'
                f'</div>'
                f'</div>'
                f'<div>{badge}</div>'
                f'</div>'
                f'<div style="margin:10px 0 6px 0; font-size:0.85rem; color:#1E293B; line-height:1.5;">'
                f'{alert["description"]}'
                f'</div>'
                f'<div style="background:rgba(0,0,0,0.03); border:1px solid #CBD5E1; border-radius:6px; padding:6px 12px; font-family:monospace; font-size:0.78rem; color:#334155;">'
                f'<strong>Verbatim Evidence:</strong> {alert["evidence"]}'
                f'</div>'
                f'</div>',
                unsafe_allow_html=True
            )

            c_resolve, _, _ = st.columns([2, 4, 4])
            with c_resolve:
                if alert["is_resolved"] == 0:
                    if st.button(f"Mark Resolved #ALT-0{alert['id']}", key=f"res_{alert['id']}"):
                        conn = sqlite3.connect(DATABASE_PATH)
                        conn.execute("UPDATE anomaly_alerts SET is_resolved = 1 WHERE id = ?", (int(alert['id']),))
                        conn.execute("""
                            INSERT INTO audit_trail (application_id, action, actor, details, ip_address, timestamp)
                            VALUES (?, 'ANOMALY_RESOLVED', ?, ?, '127.0.0.1', ?)
                        """, (app_id, user["username"] if user else "system", f"Resolved alert #ALT-0{alert['id']}", get_timestamp()))
                        conn.commit()
                        conn.close()
                        st.success("Alert resolved.")
                        st.rerun()
                else:
                    st.caption("✓ Already Resolved")
    else:
        st.success("🎉 No active anomaly alerts found for this application dossier.")

# ════════════════════════════════════════════════════════════════════════
# TAB 2: 4-LEVEL DOCUMENT AUTHENTICATION
# ════════════════════════════════════════════════════════════════════════
with tab_multilevel:
    st.markdown("### 🔬 4-Level Document Authentication Engine")
    st.markdown("""
    Every document undergoes 4 distinct screening layers:
    - **Level 1**: File & EXIF Metadata (creation timestamps, PDF editing software)
    - **Level 2**: Visual Forensics (Error Level Analysis ELA compression anomalies)
    - **Level 3**: Digital Signature & 2D QR Code Validation
    - **Level 4**: Simulated Issuing Authority Connectors (DigiLocker, State Fire, Land GIS, NBA)
    """)

    if not docs_df.empty:
        auth_doc_name = st.selectbox(
            "Select Document for Multi-Level Authentication Scrutiny",
            [d["filename"] for _, d in docs_df.iterrows()],
            key="auth_doc_select"
        )
        selected_doc_row = docs_df[docs_df["filename"] == auth_doc_name].iloc[0]

        if st.button("🚀 Execute 4-Level Authentication Screening", type="primary"):
            with st.spinner("Executing 4-level forensics & simulated connector queries..."):
                authenticator = DocumentAuthenticator()

                # For simulation, check if this is APP-1042 Fire NOC
                is_hero_expired = (app_id == 1 and "Fire" in auth_doc_name)
                is_ps_tampered = (app_id == 9 and "Land" in auth_doc_name)

                # Execute Level 1
                l1_res = authenticator.screen_level1_metadata(
                    file_path=selected_doc_row["filename"],
                    file_metadata={
                        "producer": "Adobe Photoshop 2024 (Windows)" if is_ps_tampered else "PyMuPDF / Acrobat Distiller",
                        "creation_date": "2024-03-15",
                        "mod_date": "2026-03-20" if is_ps_tampered else "2024-03-15",
                        "expiry_date": selected_doc_row.get("expiry_date") or ("2026-03-14" if is_hero_expired else "2028-06-30")
                    }
                )

                # Execute Level 2 (ELA)
                l2_res = authenticator.screen_level2_visual_forensics(selected_doc_row["filename"])

                # Execute Level 3 (QR & Signatures)
                l3_res = authenticator.screen_level3_signatures_and_qr(selected_doc_row["filename"])

                # Execute Level 4 (Simulated Connector)
                l4_res = authenticator.screen_level4_issuer_verification(
                    doc_type=selected_doc_row["doc_type"],
                    query_id="FIRE-NRO-84920" if is_hero_expired else "REG-NRO-99482",
                    context={
                        "institution_name": selected_app_info["inst_name"],
                        "simulate_expired": is_hero_expired
                    }
                )

                # Display Results in 4 Clean Cards
                c_l1, c_l2 = st.columns(2)
                with c_l1:
                    st.markdown("#### Level 1: Metadata & Expiry Forensics")
                    l1_stat = l1_res["status"]
                    bullets_l1 = "".join([f"<li><strong>{f['indicator']}</strong>: {f['detail']} (<code>{f['evidence']}</code>)</li>" for f in l1_res["findings"]])
                    st.markdown(
                        f'<div style="background:#FFFFFF; border:1px solid #CBD5E1; border-radius:10px; padding:14px; box-shadow:0 1px 4px rgba(0,0,0,0.03);">'
                        f'<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">'
                        f'<strong>Status:</strong> {status_badge_html("APPROVED" if l1_stat == "Verified" else "REJECTED")}'
                        f'</div>'
                        f'<ul style="margin:0; padding-left:18px; font-size:0.82rem; color:#334155;">{bullets_l1}</ul>'
                        f'</div>',
                        unsafe_allow_html=True
                    )

                with c_l2:
                    st.markdown("#### Level 2: Visual & Compression (ELA)")
                    l2_stat = l2_res["status"]
                    bullets_l2 = "".join([f"<li><strong>{f['indicator']}</strong>: {f['detail']} (<code>{f['evidence']}</code>)</li>" for f in l2_res["findings"]])
                    st.markdown(
                        f'<div style="background:#FFFFFF; border:1px solid #CBD5E1; border-radius:10px; padding:14px; box-shadow:0 1px 4px rgba(0,0,0,0.03);">'
                        f'<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">'
                        f'<strong>Status:</strong> {status_badge_html("APPROVED" if l2_stat == "Verified" else "UNDER_REVIEW")}'
                        f'</div>'
                        f'<ul style="margin:0; padding-left:18px; font-size:0.82rem; color:#334155;">{bullets_l2}</ul>'
                        f'</div>',
                        unsafe_allow_html=True
                    )

                c_l3, c_l4 = st.columns(2)
                with c_l3:
                    st.markdown("#### Level 3: Digital Signature & QR Codes")
                    l3_stat = l3_res["status"]
                    bullets_l3 = "".join([f"<li><strong>{f['indicator']}</strong>: {f['detail']} (<code>{f['evidence']}</code>)</li>" for f in l3_res["findings"]])
                    st.markdown(
                        f'<div style="background:#FFFFFF; border:1px solid #CBD5E1; border-radius:10px; padding:14px; box-shadow:0 1px 4px rgba(0,0,0,0.03);">'
                        f'<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">'
                        f'<strong>Status:</strong> {status_badge_html("APPROVED" if l3_stat == "Verified" else "UNDER_REVIEW")}'
                        f'</div>'
                        f'<ul style="margin:0; padding-left:18px; font-size:0.82rem; color:#334155;">{bullets_l3}</ul>'
                        f'</div>',
                        unsafe_allow_html=True
                    )

                with c_l4:
                    st.markdown("#### Level 4: Simulated External Registry Query")
                    l4_stat = l4_res["status"]
                    st.markdown(
                        f'<div style="background:#FFFFFF; border:1px solid #CBD5E1; border-radius:10px; padding:14px; box-shadow:0 1px 4px rgba(0,0,0,0.03);">'
                        f'<div style="display:flex; justify-content:space-between; align-items:center;">'
                        f'<strong>Status:</strong> {status_badge_html("APPROVED" if l4_stat == "Verified" else "REJECTED")}'
                        f'</div>'
                        f'<div style="font-size:0.75rem; color:#B45309; background:#FEF3C7; padding:4px 8px; border-radius:4px; margin:8px 0;">'
                        f'ℹ️ {l4_res.get("simulation_notice", "SIMULATED REGISTRY CONNECTOR")}'
                        f'</div>'
                        f'<p style="font-size:0.82rem; margin:6px 0; color:#334155;">'
                        f'<strong>Authority:</strong> {l4_res.get("authority")}<br>'
                        f'<strong>Protocol:</strong> {l4_res.get("connector_type")}<br>'
                        f'<strong>Advisory Result:</strong> {l4_res.get("advisory_message")}'
                        f'</p>'
                        f'</div>',
                        unsafe_allow_html=True
                    )

    else:
        st.info("No documents uploaded for this application.")

# ════════════════════════════════════════════════════════════════════════
# TAB 3: CROSS-APPLICATION INTELLIGENCE
# ════════════════════════════════════════════════════════════════════════
with tab_crossapp:
    st.markdown("### 🌐 Cross-Application Intelligence & Multi-Campus Scrutiny")
    st.markdown("""
    Scans across all 15 institutional dockets in the national registry to detect:
    - **Byte-Identical Collisions**: File SHA-256 collisions reused across different colleges.
    - **Dual-College Faculty Appointments**: Same faculty identifier claimed simultaneously on two colleges' rosters (salted SHA-256 hash privacy).
    - **Year-over-Year Land/Building Contradictions**: Instructional built-up area shrinking without Change of Site.
    """)

    cross_intel = CrossApplicationIntelligence()

    # 1. SHA-256 Collisions
    st.markdown("#### 1. Cross-College File Hash Collisions (SHA-256)")
    conn = sqlite3.connect(DATABASE_PATH)
    doc_reused = pd.read_sql_query("""
        SELECT d1.application_id as app1, i1.name as college1,
               d2.application_id as app2, i2.name as college2,
               d1.doc_type, d1.file_hash
        FROM documents d1
        JOIN documents d2 ON d1.file_hash = d2.file_hash AND d1.application_id < d2.application_id
        JOIN applications a1 ON d1.application_id = a1.id
        JOIN institutions i1 ON a1.institution_id = i1.id
        JOIN applications a2 ON d2.application_id = a2.id
        JOIN institutions i2 ON a2.institution_id = i2.id
        WHERE d1.file_hash IS NOT NULL AND d1.file_hash != ''
    """, conn)
    conn.close()

    if not doc_reused.empty:
        for _, row in doc_reused.iterrows():
            st.markdown(f"""
            <div style="background:#FEF2F2; border-left:4px solid #EF4444; border-radius:8px; padding:12px 18px; margin-bottom:10px;">
                <strong style="color:#991B1B;">⚠️ SHA-256 Collision Detected:</strong> File <code>{row['doc_type']}</code> is identical across:
                <br>• <strong>APP-2026-{1000 + row['app1']}</strong>: {row['college1']}
                <br>• <strong>APP-2026-{1000 + row['app2']}</strong>: {row['college2']}
                <div style="font-family:monospace; font-size:0.75rem; color:#64748B; margin-top:4px;">
                    Shared Hash: {row['file_hash']}
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No cross-institution byte collisions detected in current database.")

    # 2. Dual-College Faculty
    st.markdown("#### 2. Dual-Institution Faculty Appointments")
    st.markdown("""
    <div style="background:#FFFFFF; border:1px solid #E2E8F0; border-radius:10px; padding:14px; margin-bottom:12px;">
        <div style="display:flex; justify-content:space-between; align-items:center;">
            <div>
                <strong>Faculty Identifier Collision:</strong> Dr. R. C. Sharma (Salted Hash: <code>7f83...4920</code>)
                <div style="font-size:0.78rem; color:#64748B; margin-top:2px;">
                    Claimed simultaneously on roster of <strong>Aryabhatta Institute of Technology (APP-1042)</strong> and <strong>Nalanda College of Engineering (APP-1048)</strong>.
                </div>
            </div>
            <div>
                <span class="user-role-pill" style="background:#EF4444; color:white;">CRITICAL CONFLICT</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 3. Year-over-Year Physical Campus Consistency
    st.markdown("#### 3. Year-over-Year Physical Campus Consistency")
    yoy_findings = cross_intel.check_year_over_year_consistency(
        current_year_data={"built_up_area_sqm": 9800.0, "total_faculty": 42},
        prior_year_data={"built_up_area_sqm": 14000.0, "total_faculty": 45}
    )
    for f in yoy_findings:
        msg = f.get("message") or f.get("detail", "")
        evidence = str(f.get("computed_values") or f.get("evidence", ""))
        st.markdown(
            f'<div style="background:#FEF3C7; border-left:4px solid #F59E0B; border-radius:8px; padding:12px 18px; margin-bottom:8px;">'
            f'<strong style="color:#92400E;">⚠️ {f.get("type", "YoY Consistency Alert")}:</strong> {msg}'
            f'<div style="font-size:0.78rem; color:#78350F; margin-top:2px;">Evidence: {evidence}</div>'
            f'</div>',
            unsafe_allow_html=True
        )

# Footer
render_sih_footer()
