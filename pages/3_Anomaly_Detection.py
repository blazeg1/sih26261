"""
Page 3: Anomaly & Potential Alteration Detection Studio

Scans documents for suspicious alterations, text duplication, inconsistent metadata,
irregular dates, and generates evidence-linked anomaly alerts for human verification.
"""

import sys
import json
import sqlite3
from pathlib import Path

import streamlit as st
import pandas as pd
import plotly.graph_objects as go

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config.settings import APP_TITLE, DATABASE_PATH, SeverityLevels
from utils.auth import check_auth, get_current_user
from utils.helpers import get_timestamp
from utils.styles import (
    apply_custom_styles,
    render_gov_header,
    render_aicte_brand_bar,
    render_sidebar_header,
    render_sih_footer,
    status_badge_html
)

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

# Header
render_aicte_brand_bar("Anomaly & Forgery Detection Studio", "Computer Vision Forensic Analysis, Compression ELA & Discrepancy Flagging")

try:
    from modules.anomaly_detector import AnomalyDetector
    DETECTOR_AVAILABLE = True
except ImportError as e:
    DETECTOR_AVAILABLE = False
    st.warning(f"⚠️ Anomaly detector module unavailable: {e}")

# ── Select Application ─────────────────────────────────────────────────
conn = sqlite3.connect(DATABASE_PATH)
apps = pd.read_sql_query(
    "SELECT a.id, ('APP-2026-' || (1000 + a.id)) as case_id, i.name as inst_name, a.category "
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

# Fetch documents and alerts
conn = sqlite3.connect(DATABASE_PATH)
docs_df = pd.read_sql_query(
    "SELECT id, doc_type, filename, ocr_text, extracted_data, anomaly_score "
    "FROM documents WHERE application_id = ?", conn, params=(app_id,)
)

alerts_df = pd.read_sql_query(
    "SELECT id, alert_type, severity, description, evidence, is_resolved, created_at "
    "FROM anomaly_alerts WHERE application_id = ? ORDER BY id DESC", conn, params=(app_id,)
)
conn.close()

# ── Anomaly Overview Metrics & Risk Gauge (Task 7 & 10) ────────────────
st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)

unresolved_alerts = alerts_df[alerts_df["is_resolved"] == 0] if not alerts_df.empty else pd.DataFrame()
critical_count = len(unresolved_alerts[unresolved_alerts["severity"] == "CRITICAL"]) if not unresolved_alerts.empty else 0
high_count = len(unresolved_alerts[unresolved_alerts["severity"] == "HIGH"]) if not unresolved_alerts.empty else 0
med_count = len(unresolved_alerts[unresolved_alerts["severity"] == "MEDIUM"]) if not unresolved_alerts.empty else 0
low_count = len(unresolved_alerts[unresolved_alerts["severity"] == "LOW"]) if not unresolved_alerts.empty else 0

# Compute risk score (0-100)
risk_score = min(100.0, (critical_count * 35.0) + (high_count * 20.0) + (med_count * 10.0) + (low_count * 4.0))

col_gauge, col_m1, col_m2, col_m3, col_m4 = st.columns([4, 2, 2, 2, 2])

with col_gauge:
    # Projector-friendly Risk Meter Gauge using Plotly
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
    st.metric("Critical Alerts", critical_count, delta="Immediate Action" if critical_count > 0 else "Clear", delta_color="inverse")
with col_m2:
    st.metric("High Severity", high_count, delta="Requires Check" if high_count > 0 else "Clear", delta_color="inverse")
with col_m3:
    st.metric("Medium Severity", med_count, delta="Review Advised" if med_count > 0 else "Clear", delta_color="off")
with col_m4:
    st.metric("Low Severity", low_count, delta="Informational", delta_color="off")

st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)

# ── Anomaly Scan Trigger ───────────────────────────────────────────────
c_act1, c_act2 = st.columns([7, 3])
with c_act1:
    st.info("⚠️ **Statutory Disclaimer**: Automated findings are preliminary indicators for human verification, not conclusive proof of misconduct.")
with c_act2:
    scan_btn = st.button("🔍 Execute Forensic Scan", type="primary", use_container_width=True)

if scan_btn:
    if not DETECTOR_AVAILABLE:
        st.error("Detector module unavailable.")
    else:
        with st.spinner("Analyzing compression artifacts, typography discrepancies, and metadata anomalies..."):
            detector = AnomalyDetector()
            new_alerts = []

            for _, d in docs_df.iterrows():
                ocr_text = d.get("ocr_text", "")
                if ocr_text:
                    text_anoms = detector.check_text_anomalies(ocr_text)
                    for ta in text_anoms:
                        new_alerts.append({
                            "document_id": d["id"],
                            "alert_type": ta.get("type", "TEXT_ANOMALY"),
                            "severity": ta.get("severity", "MEDIUM"),
                            "description": ta.get("description", ""),
                            "evidence": ta.get("evidence", ""),
                        })

                # Check date anomalies
                ext = d.get("extracted_data")
                ext_dict = json.loads(ext) if ext and isinstance(ext, str) else (ext if isinstance(ext, dict) else {})
                date_anoms = detector.check_date_anomalies(ext_dict.get("dates", []))
                for da in date_anoms:
                    new_alerts.append({
                        "document_id": d["id"],
                        "alert_type": da.get("type", "DATE_ANOMALY"),
                        "severity": da.get("severity", "HIGH"),
                        "description": da.get("description", ""),
                        "evidence": da.get("evidence", ""),
                    })

            # Save to DB
            if new_alerts:
                conn = sqlite3.connect(DATABASE_PATH)
                cursor = conn.cursor()
                now = get_timestamp()
                for a in new_alerts:
                    cursor.execute("""
                        INSERT INTO anomaly_alerts (application_id, document_id, alert_type, severity, description, evidence, is_resolved, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, 0, ?)
                    """, (app_id, a["document_id"], a["alert_type"], a["severity"], a["description"], a["evidence"], now))

                cursor.execute("""
                    INSERT INTO audit_trail (application_id, action, actor, details, ip_address, timestamp)
                    VALUES (?, 'ANOMALY_SCAN_EXECUTED', ?, ?, '127.0.0.1', ?)
                """, (app_id, user["username"] if user else "system", f"Forensic scan found {len(new_alerts)} potential anomalies", now))
                conn.commit()
                conn.close()

                st.success(f"Forensic scan completed! Flagged {len(new_alerts)} items for scrutiny.")
                st.rerun()
            else:
                st.success("✅ Clean scan: No new anomalies detected across submitted documents.")

# ── Active Anomaly Alert Cards (Task 7) ────────────────────────────────
st.markdown("### 🚨 Active Regulatory Alerts")

if not alerts_df.empty:
    # Filter controls
    f_sev = st.selectbox("Filter Alerts by Severity", ["All Severities", "CRITICAL", "HIGH", "MEDIUM", "LOW"])
    filtered_alerts = alerts_df if f_sev == "All Severities" else alerts_df[alerts_df["severity"] == f_sev]

    for _, alert in filtered_alerts.iterrows():
        sev = alert["severity"].upper()
        alert_class = "alert-high" if sev in ("CRITICAL", "HIGH") else "alert-medium" if sev == "MEDIUM" else "alert-low"
        icon = "🚨" if sev in ("CRITICAL", "HIGH") else "⚠️" if sev == "MEDIUM" else "ℹ️"
        badge = status_badge_html("REJECTED" if sev in ("CRITICAL", "HIGH") else "UNDER_REVIEW" if sev == "MEDIUM" else "SUBMITTED")

        st.markdown(f"""
        <div class="alert-card {alert_class}">
            <div style="display:flex; justify-content:space-between; align-items:flex-start;">
                <div style="display:flex; align-items:center; gap:10px;">
                    <span style="font-size:1.4rem;">{icon}</span>
                    <div>
                        <div style="font-size:0.92rem; font-weight:700; color:#0B1F4B;">
                            {alert['alert_type'].replace('_', ' ')}
                        </div>
                        <div style="font-size:0.75rem; color:#64748B;">
                            Alert Ref: #ALT-0{alert['id']} · Recorded: {alert['created_at']}
                        </div>
                    </div>
                </div>
                <div>{badge}</div>
            </div>
            <div style="margin:10px 0 6px 0; font-size:0.85rem; color:#1E293B; line-height:1.5;">
                {alert['description']}
            </div>
            <div style="background:rgba(0,0,0,0.03); border:1px solid #CBD5E1; border-radius:6px; padding:6px 12px; font-family:monospace; font-size:0.78rem; color:#334155;">
                <strong>Verbatim Evidence:</strong> {alert['evidence']}
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Action row for each alert
        c_resolve, c_note, _ = st.columns([2, 4, 4])
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

# Footer
render_sih_footer()
