"""
Page 3: Anomaly Detection

Analyzes documents for suspicious alterations, duplicates,
metadata inconsistencies, and other anomalies.
"""

import sys
import json
import sqlite3
from pathlib import Path

import streamlit as st
import pandas as pd
import plotly.graph_objects as go

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config.settings import APP_TITLE, DATABASE_PATH
from utils.auth import check_auth, get_current_user
from utils.helpers import get_timestamp, severity_color

st.set_page_config(page_title=f"Anomaly Detection — {APP_TITLE}", page_icon="⚠️", layout="wide")

if not check_auth():
    st.warning("🔒 Please log in from the main page.")
    st.stop()

user = get_current_user()

try:
    from modules.anomaly_detector import AnomalyDetector
    ANOMALY_AVAILABLE = True
except ImportError:
    ANOMALY_AVAILABLE = False

st.markdown("""
<style>
    .alert-critical { background: #f8d7da; border-left: 5px solid #dc3545; padding: 1rem; border-radius: 8px; margin: 0.5rem 0; }
    .alert-high { background: #fff3cd; border-left: 5px solid #fd7e14; padding: 1rem; border-radius: 8px; margin: 0.5rem 0; }
    .alert-medium { background: #fff9e6; border-left: 5px solid #ffc107; padding: 1rem; border-radius: 8px; margin: 0.5rem 0; }
    .alert-low { background: #cce5ff; border-left: 5px solid #007bff; padding: 1rem; border-radius: 8px; margin: 0.5rem 0; }
</style>
""", unsafe_allow_html=True)

st.title("⚠️ Anomaly & Forgery Detection")
st.markdown("Detect suspicious alterations, duplicate documents, metadata inconsistencies, and other anomalies.")

# ── Select Application ─────────────────────────────────────────────────
conn = sqlite3.connect(DATABASE_PATH)
apps = pd.read_sql_query(
    "SELECT a.id, i.name, a.category, a.academic_year "
    "FROM applications a JOIN institutions i ON a.institution_id = i.id "
    "ORDER BY a.submitted_at DESC", conn
)
conn.close()

if apps.empty:
    st.info("No applications found.")
    st.stop()

app_options = {f"App #{r['id']} — {r['name']} ({r['category']})": r["id"] for _, r in apps.iterrows()}
selected = st.selectbox("Select Application", list(app_options.keys()))
app_id = app_options[selected]

# Get documents
conn = sqlite3.connect(DATABASE_PATH)
docs_df = pd.read_sql_query(
    "SELECT id, doc_type, filename, ocr_text, validation_status, anomaly_score, file_hash "
    "FROM documents WHERE application_id = ?", conn, params=(app_id,)
)
conn.close()

if docs_df.empty:
    st.info("No documents found for this application.")
    st.stop()

st.markdown(f"**{len(docs_df)} documents** available for analysis")

# ── Run Anomaly Detection ──────────────────────────────────────────────
st.markdown("---")

if st.button("🔍 Run Anomaly Analysis", type="primary", use_container_width=True):
    if not ANOMALY_AVAILABLE:
        st.error("Anomaly detection module not available.")
        st.stop()

    detector = AnomalyDetector()
    all_alerts = []
    doc_scores = {}

    progress = st.progress(0)

    for idx, (_, doc) in enumerate(docs_df.iterrows()):
        with st.spinner(f"Analyzing {doc['filename']}..."):
            ocr_text = doc.get("ocr_text", "") or ""

            # Run anomaly checks
            alerts = detector.analyze_document(
                doc_path=doc.get("filename", ""),
                ocr_text=str(ocr_text),
                metadata={"file_hash": doc.get("file_hash", "")},
            )

            # Check for duplicates against other docs
            other_texts = [str(d.get("ocr_text", "")) for _, d in docs_df.iterrows() if d["id"] != doc["id"] and d.get("ocr_text")]
            if other_texts:
                dup_alerts = detector.check_duplicate_content(str(ocr_text), other_texts)
                alerts.extend(dup_alerts)

            anomaly_score = detector.calculate_anomaly_score(alerts)
            doc_scores[doc["filename"]] = anomaly_score

            for alert in alerts:
                alert["document_id"] = doc["id"]
                alert["filename"] = doc["filename"]
                alert["doc_type"] = doc["doc_type"]
            all_alerts.extend(alerts)

        progress.progress((idx + 1) / len(docs_df))

    # ── Display Results ────────────────────────────────────────────────
    st.markdown("### 📊 Analysis Results")

    # Anomaly Score Gauge
    overall_score = sum(doc_scores.values()) / max(len(doc_scores), 1)

    gauge = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=overall_score * 100,
        title={"text": "Overall Anomaly Risk Score"},
        gauge={
            "axis": {"range": [0, 100]},
            "bar": {"color": "darkred" if overall_score > 0.6 else "orange" if overall_score > 0.3 else "green"},
            "steps": [
                {"range": [0, 30], "color": "#d4edda"},
                {"range": [30, 60], "color": "#fff3cd"},
                {"range": [60, 100], "color": "#f8d7da"},
            ],
            "threshold": {"line": {"color": "red", "width": 4}, "thickness": 0.75, "value": 70},
        },
    ))
    gauge.update_layout(height=300)
    st.plotly_chart(gauge, use_container_width=True)

    # Per-document scores
    st.markdown("#### 📄 Document-wise Anomaly Scores")
    score_df = pd.DataFrame([
        {"Document": k, "Anomaly Score": f"{v:.2f}", "Risk": "🔴 High" if v > 0.6 else "🟡 Medium" if v > 0.3 else "🟢 Low"}
        for k, v in doc_scores.items()
    ])
    st.dataframe(score_df, use_container_width=True, hide_index=True)

    # Alert Cards
    if all_alerts:
        st.markdown(f"### 🚨 Anomaly Alerts ({len(all_alerts)} found)")

        severity_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
        all_alerts.sort(key=lambda x: severity_order.get(x.get("severity", "LOW"), 4))

        for alert in all_alerts:
            severity = alert.get("severity", "LOW")
            css_class = f"alert-{severity.lower()}"
            icon = {"CRITICAL": "🔴", "HIGH": "🟠", "MEDIUM": "🟡", "LOW": "🔵"}.get(severity, "⚪")

            st.markdown(f"""
            <div class="{css_class}">
                <strong>{icon} [{severity}] {alert.get('alert_type', 'Unknown')}</strong> — {alert.get('filename', '')}
                <br>{alert.get('description', '')}
                <br><small>Evidence: {alert.get('evidence', 'N/A')} | Confidence: {alert.get('confidence', 0):.0%}</small>
            </div>
            """, unsafe_allow_html=True)

        # Save alerts to database
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        now = get_timestamp()

        for alert in all_alerts:
            cursor.execute(
                "INSERT INTO anomaly_alerts (document_id, application_id, alert_type, severity, description, evidence, is_resolved, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?, 0, ?)",
                (
                    alert.get("document_id"),
                    app_id,
                    alert.get("alert_type", ""),
                    alert.get("severity", "LOW"),
                    alert.get("description", ""),
                    alert.get("evidence", ""),
                    now,
                ),
            )

        cursor.execute(
            "INSERT INTO audit_trail (application_id, action, actor, details, ip_address, timestamp) "
            "VALUES (?, 'ANOMALY_DETECTED', ?, ?, '127.0.0.1', ?)",
            (app_id, user["username"] if user else "system",
             f"Anomaly analysis: {len(all_alerts)} alerts found", now),
        )

        conn.commit()
        conn.close()
        st.success(f"✅ {len(all_alerts)} anomaly alerts saved to database.")
    else:
        st.success("✅ No anomalies detected! All documents appear clean.")

# ── Active Alerts ──────────────────────────────────────────────────────
st.markdown("---")
st.markdown("### 📋 All Active Alerts")

fc1, fc2 = st.columns(2)
with fc1:
    sev_filter = st.selectbox("Filter Severity", ["All", "CRITICAL", "HIGH", "MEDIUM", "LOW"])
with fc2:
    resolved_filter = st.selectbox("Resolution Status", ["Unresolved", "Resolved", "All"])

conn = sqlite3.connect(DATABASE_PATH)
alert_query = """
    SELECT aa.id, aa.alert_type, aa.severity, aa.description, aa.is_resolved,
           aa.resolved_by, aa.created_at, d.filename
    FROM anomaly_alerts aa
    LEFT JOIN documents d ON aa.document_id = d.id
    WHERE aa.application_id = ?
"""
params = [app_id]

if sev_filter != "All":
    alert_query += " AND aa.severity = ?"
    params.append(sev_filter)
if resolved_filter == "Unresolved":
    alert_query += " AND aa.is_resolved = 0"
elif resolved_filter == "Resolved":
    alert_query += " AND aa.is_resolved = 1"

alert_query += " ORDER BY aa.created_at DESC"

alerts_df = pd.read_sql_query(alert_query, conn, params=params)
conn.close()

if not alerts_df.empty:
    st.dataframe(alerts_df, use_container_width=True, hide_index=True)

    # Resolution action
    if user and user["role"] in ("ADMIN", "REVIEWER"):
        st.markdown("#### 🔧 Resolve Alert")
        alert_ids = alerts_df[alerts_df["is_resolved"] == 0]["id"].tolist()
        if alert_ids:
            resolve_id = st.selectbox("Select Alert ID to Resolve", alert_ids)
            resolve_notes = st.text_input("Resolution Notes")
            if st.button("✅ Mark as Resolved"):
                conn = sqlite3.connect(DATABASE_PATH)
                cursor = conn.cursor()
                now = get_timestamp()
                cursor.execute(
                    "UPDATE anomaly_alerts SET is_resolved = 1, resolved_by = ?, resolved_at = ? WHERE id = ?",
                    (user["username"], now, resolve_id),
                )
                cursor.execute(
                    "INSERT INTO audit_trail (application_id, action, actor, details, ip_address, timestamp) "
                    "VALUES (?, 'ALERT_RESOLVED', ?, ?, '127.0.0.1', ?)",
                    (app_id, user["username"], f"Alert #{resolve_id} resolved: {resolve_notes}", now),
                )
                conn.commit()
                conn.close()
                st.success(f"✅ Alert #{resolve_id} marked as resolved.")
                st.rerun()
        else:
            st.info("No unresolved alerts.")
else:
    st.info("No alerts found for this application.")
