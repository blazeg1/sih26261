"""
Page 6: Audit Trail

Complete audit history of all actions, validations, verifications,
and alerts with filtering, searching, and export capabilities.
"""

import sys
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta

import streamlit as st
import pandas as pd
import plotly.express as px

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config.settings import APP_TITLE, DATABASE_PATH
from utils.auth import check_auth, get_current_user

st.set_page_config(page_title=f"Audit Trail — {APP_TITLE}", page_icon="📝", layout="wide")

if not check_auth():
    st.warning("🔒 Please log in from the main page.")
    st.stop()

user = get_current_user()

# Only ADMIN gets full access; REVIEWER and VIEWER see limited view
is_admin = user and user["role"] == "ADMIN"

st.title("📝 Audit Trail")
st.markdown("Complete traceability of all validation activities, alerts, and actions taken.")

# ── Filters ────────────────────────────────────────────────────────────
fc1, fc2, fc3, fc4 = st.columns(4)

with fc1:
    start_date = st.date_input("From Date", value=datetime.now() - timedelta(days=365), key="audit_start")
with fc2:
    end_date = st.date_input("To Date", value=datetime.now() + timedelta(days=30), key="audit_end")
with fc3:
    conn = sqlite3.connect(DATABASE_PATH)
    actions = pd.read_sql_query("SELECT DISTINCT action FROM audit_trail ORDER BY action", conn)
    conn.close()
    action_options = ["All"] + actions["action"].tolist() if not actions.empty else ["All"]
    filter_action = st.selectbox("Action Type", action_options)
with fc4:
    filter_actor = st.text_input("Actor Username", placeholder="e.g., admin")

# Optional: Application filter
conn = sqlite3.connect(DATABASE_PATH)
app_ids_df = pd.read_sql_query(
    "SELECT DISTINCT a.application_id, i.name "
    "FROM audit_trail a "
    "LEFT JOIN applications ap ON a.application_id = ap.id "
    "LEFT JOIN institutions i ON ap.institution_id = i.id "
    "WHERE a.application_id IS NOT NULL "
    "ORDER BY a.application_id", conn
)
conn.close()

app_filter_options = {"All Applications": None}
if not app_ids_df.empty:
    for _, r in app_ids_df.iterrows():
        label = f"App #{r['application_id']} — {r['name'] or 'Unknown'}"
        app_filter_options[label] = r["application_id"]

filter_app = st.selectbox("Filter by Application", list(app_filter_options.keys()))
filter_app_id = app_filter_options[filter_app]

# ── Query Audit Trail ──────────────────────────────────────────────────
conn = sqlite3.connect(DATABASE_PATH)

query = """
    SELECT at.id, at.application_id, at.action, at.actor, at.details,
           at.ip_address, at.timestamp,
           COALESCE(i.name, '') as institution
    FROM audit_trail at
    LEFT JOIN applications a ON at.application_id = a.id
    LEFT JOIN institutions i ON a.institution_id = i.id
    WHERE at.timestamp >= ? AND at.timestamp <= ?
"""
params = [start_date.isoformat(), (end_date + timedelta(days=1)).isoformat()]

if filter_action != "All":
    query += " AND at.action = ?"
    params.append(filter_action)

if filter_actor:
    query += " AND at.actor LIKE ?"
    params.append(f"%{filter_actor}%")

if filter_app_id is not None:
    query += " AND at.application_id = ?"
    params.append(filter_app_id)

if not is_admin:
    # Non-admin users only see their own actions
    query += " AND at.actor = ?"
    params.append(user["username"] if user else "")

query += " ORDER BY at.timestamp DESC"

audit_df = pd.read_sql_query(query, conn, params=params)

# ── Activity Summary Chart ─────────────────────────────────────────────
st.markdown("### 📈 Activity Summary")

activity_query = """
    SELECT DATE(timestamp) as date, action, COUNT(*) as count
    FROM audit_trail
    WHERE timestamp >= ? AND timestamp <= ?
"""
activity_params = [start_date.isoformat(), (end_date + timedelta(days=1)).isoformat()]

if not is_admin:
    activity_query += " AND actor = ?"
    activity_params.append(user["username"] if user else "")

activity_query += " GROUP BY DATE(timestamp), action ORDER BY date"
activity_df = pd.read_sql_query(activity_query, conn, params=activity_params)

if not activity_df.empty:
    fig = px.bar(activity_df, x="date", y="count", color="action",
                 title="Actions per Day",
                 color_discrete_sequence=px.colors.qualitative.Set3)
    fig.update_layout(height=350, xaxis_title="Date", yaxis_title="Actions")
    st.plotly_chart(fig, use_container_width=True)

    # Summary metrics
    sc1, sc2, sc3 = st.columns(3)
    with sc1:
        st.metric("Total Actions", len(audit_df))
    with sc2:
        unique_actors = audit_df["actor"].nunique() if not audit_df.empty else 0
        st.metric("Unique Actors", unique_actors)
    with sc3:
        unique_apps = audit_df["application_id"].nunique() if not audit_df.empty else 0
        st.metric("Applications Affected", unique_apps)
else:
    st.info("No activity data for the selected period.")

conn.close()

# ── Audit Trail Table ──────────────────────────────────────────────────
st.markdown("---")
st.markdown("### 📋 Audit Log")

if not audit_df.empty:
    # Rename columns for display
    display_df = audit_df.rename(columns={
        "id": "ID",
        "application_id": "App ID",
        "action": "Action",
        "actor": "Actor",
        "details": "Details",
        "ip_address": "IP Address",
        "timestamp": "Timestamp",
        "institution": "Institution",
    })

    # Search
    search_term = st.text_input("🔍 Search audit log", placeholder="Type to search...")
    if search_term:
        mask = display_df.apply(lambda row: search_term.lower() in str(row).lower(), axis=1)
        display_df = display_df[mask]

    st.markdown(f"**{len(display_df)} records found**")
    st.dataframe(display_df, use_container_width=True, hide_index=True, height=500)

    # Export
    st.markdown("---")
    csv_data = display_df.to_csv(index=False)
    st.download_button(
        "📥 Export Audit Log (CSV)",
        csv_data,
        f"audit_trail_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        "text/csv",
    )

    # Detailed export with full formatting
    report = "AICTE VALIDATION PLATFORM — AUDIT TRAIL REPORT\n"
    report += f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    report += f"Period: {start_date} to {end_date}\n"
    report += f"Total Records: {len(display_df)}\n"
    report += "=" * 80 + "\n\n"

    for _, row in display_df.iterrows():
        report += f"[{row['Timestamp']}] {row['Action']}\n"
        report += f"  Actor: {row['Actor']} | App: #{row['App ID']} | IP: {row['IP Address']}\n"
        report += f"  Institution: {row['Institution']}\n"
        report += f"  Details: {row['Details']}\n"
        report += "-" * 60 + "\n"

    st.download_button(
        "📥 Export Detailed Report (TXT)",
        report,
        f"audit_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
        "text/plain",
    )
else:
    st.info("No audit trail records match the selected filters.")

# ── Action Type Summary ────────────────────────────────────────────────
if not audit_df.empty:
    st.markdown("---")
    st.markdown("### 📊 Action Type Summary")

    action_summary = audit_df["action"].value_counts().reset_index()
    action_summary.columns = ["Action", "Count"]

    fig = px.bar(action_summary, x="Action", y="Count",
                 title="Actions by Type",
                 color="Count",
                 color_continuous_scale="Blues")
    fig.update_layout(height=350)
    st.plotly_chart(fig, use_container_width=True)
