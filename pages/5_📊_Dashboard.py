"""
Page 5: Dashboard

Centralized view of application status, validation results,
anomaly alerts, compliance scores, and verification outcomes.
"""

import sys
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config.settings import APP_TITLE, DATABASE_PATH
from utils.auth import check_auth

st.set_page_config(page_title=f"Dashboard — {APP_TITLE}", page_icon="📊", layout="wide")

if not check_auth():
    st.warning("🔒 Please log in from the main page.")
    st.stop()

st.title("📊 Validation Dashboard")

# ── Date Filter ────────────────────────────────────────────────────────
fc1, fc2 = st.columns(2)
with fc1:
    start_date = st.date_input("From", value=datetime.now() - timedelta(days=365))
with fc2:
    end_date = st.date_input("To", value=datetime.now() + timedelta(days=30))

conn = sqlite3.connect(DATABASE_PATH)

# ── Row 1: Key Metrics ────────────────────────────────────────────────
st.markdown("---")

cursor = conn.cursor()

cursor.execute("SELECT COUNT(*) FROM applications")
total_apps = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM applications WHERE status = 'UNDER_REVIEW'")
pending = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM anomaly_alerts WHERE is_resolved = 0")
anomalies = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM compliance_checks WHERE status = 'COMPLIANT'")
compliant = cursor.fetchone()[0]
cursor.execute("SELECT COUNT(*) FROM compliance_checks")
total_checks = cursor.fetchone()[0]
avg_compliance = round((compliant / max(total_checks, 1)) * 100, 1)

mc1, mc2, mc3, mc4 = st.columns(4)
with mc1:
    st.metric("📋 Total Applications", total_apps)
with mc2:
    st.metric("⏳ Pending Review", pending)
with mc3:
    st.metric("🚨 Active Anomalies", anomalies)
with mc4:
    st.metric("📈 Avg Compliance", f"{avg_compliance}%")

# ── Row 2: Status Distribution + Anomaly Severity ─────────────────────
st.markdown("---")
r2c1, r2c2 = st.columns(2)

with r2c1:
    status_df = pd.read_sql_query(
        "SELECT status, COUNT(*) as count FROM applications GROUP BY status", conn
    )
    if not status_df.empty:
        fig = px.pie(status_df, values="count", names="status",
                     title="Application Status Distribution",
                     color_discrete_sequence=px.colors.qualitative.Set2)
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No data for status distribution.")

with r2c2:
    sev_df = pd.read_sql_query(
        "SELECT severity, COUNT(*) as count FROM anomaly_alerts GROUP BY severity", conn
    )
    if not sev_df.empty:
        color_map = {"CRITICAL": "#dc3545", "HIGH": "#fd7e14", "MEDIUM": "#ffc107", "LOW": "#007bff"}
        fig = px.bar(sev_df, x="severity", y="count", title="Anomaly Alerts by Severity",
                     color="severity", color_discrete_map=color_map)
        fig.update_layout(height=400, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No anomaly alert data.")

# ── Row 3: Compliance Trends + Document Validation ─────────────────────
st.markdown("---")
r3c1, r3c2 = st.columns(2)

with r3c1:
    comp_df = pd.read_sql_query(
        "SELECT checked_at, status FROM compliance_checks ORDER BY checked_at", conn
    )
    if not comp_df.empty:
        comp_df["date"] = pd.to_datetime(comp_df["checked_at"]).dt.date
        daily = comp_df.groupby(["date", "status"]).size().reset_index(name="count")
        fig = px.line(daily, x="date", y="count", color="status",
                      title="Compliance Check Trends",
                      color_discrete_map={"COMPLIANT": "#28a745", "NON_COMPLIANT": "#dc3545", "PARTIAL": "#ffc107"})
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No compliance data available.")

with r3c2:
    val_df = pd.read_sql_query(
        "SELECT validation_status, COUNT(*) as count FROM documents GROUP BY validation_status", conn
    )
    if not val_df.empty:
        fig = px.bar(val_df, x="validation_status", y="count",
                     title="Document Validation Status",
                     color="validation_status",
                     color_discrete_sequence=px.colors.qualitative.Pastel)
        fig.update_layout(height=400, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No document validation data.")

# ── Row 4: Applications by Category + Verification Results ─────────────
st.markdown("---")
r4c1, r4c2 = st.columns(2)

with r4c1:
    cat_df = pd.read_sql_query(
        "SELECT category, COUNT(*) as count FROM applications GROUP BY category", conn
    )
    if not cat_df.empty:
        fig = px.bar(cat_df, x="category", y="count",
                     title="Applications by Category",
                     color="category",
                     color_discrete_sequence=px.colors.qualitative.Bold)
        fig.update_layout(height=400, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No category data.")

with r4c2:
    ver_df = pd.read_sql_query(
        "SELECT verification_status, COUNT(*) as count FROM verification_records GROUP BY verification_status", conn
    )
    if not ver_df.empty:
        fig = px.pie(ver_df, values="count", names="verification_status",
                     title="Verification Results Summary",
                     color_discrete_sequence=px.colors.qualitative.Vivid)
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No verification data.")

# ── Row 5: Recent Alerts + Pending Actions ─────────────────────────────
st.markdown("---")
r5c1, r5c2 = st.columns(2)

with r5c1:
    st.markdown("### 🚨 Recent Anomaly Alerts")
    recent_alerts = pd.read_sql_query(
        "SELECT aa.alert_type, aa.severity, aa.description, aa.created_at, d.filename "
        "FROM anomaly_alerts aa "
        "LEFT JOIN documents d ON aa.document_id = d.id "
        "WHERE aa.is_resolved = 0 "
        "ORDER BY aa.created_at DESC LIMIT 10", conn
    )
    if not recent_alerts.empty:
        st.dataframe(recent_alerts, use_container_width=True, hide_index=True)
    else:
        st.success("No active anomaly alerts! 🎉")

with r5c2:
    st.markdown("### ⏳ Pending Actions")
    pending_actions = pd.read_sql_query(
        "SELECT a.id as app_id, i.name as institution, a.category, a.status "
        "FROM applications a JOIN institutions i ON a.institution_id = i.id "
        "WHERE a.status IN ('SUBMITTED', 'UNDER_REVIEW') "
        "ORDER BY a.submitted_at ASC LIMIT 10", conn
    )
    if not pending_actions.empty:
        st.dataframe(pending_actions, use_container_width=True, hide_index=True)
    else:
        st.success("No pending actions! All caught up. 🎉")

conn.close()

# Footer
st.markdown("---")
st.caption(f"Dashboard last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
