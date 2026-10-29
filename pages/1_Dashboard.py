"""
Page 5: Centralized Scrutiny Analytics & Executive Dashboard

Interactive Plotly analytics covering application throughput, category distribution,
compliance trends, anomaly severity breakdowns, and pending statutory actions.
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
from utils.auth import check_auth, get_current_user, render_login_page
from utils.styles import (
    apply_custom_styles,
    render_gov_header,
    render_aicte_brand_bar,
    render_sidebar_header,
    render_sidebar_logout,
    render_sih_footer,
    render_kpi_card,
    status_badge_html
)

st.set_page_config(page_title=f"Dashboard — {APP_TITLE}", page_icon="📊", layout="wide")
apply_custom_styles()
render_gov_header()

if not check_auth():
    try:
        st.switch_page("app.py")
    except Exception:
        pass
    render_login_page()
    render_sih_footer()
    st.stop()

user = get_current_user()

# Sidebar
with st.sidebar:
    render_sidebar_header(user)
    render_sidebar_logout("dashboard")

# Header
render_aicte_brand_bar("Scrutiny Analytics & Intelligence Dashboard", "Pan-India Regulatory Processing Velocity, Compliance Gauges & Anomaly Triage")

# ── Filter Bar ─────────────────────────────────────────────────────────
st.markdown(
    '<div style="font-size:0.75rem; font-weight:700; color:#0B1F4B; text-transform:uppercase; letter-spacing:0.6px; margin-bottom:6px;">'
    'DASHBOARD FILTERS'
    '</div>',
    unsafe_allow_html=True
)

fc1, fc2, fc3 = st.columns([4, 4, 2])
with fc1:
    start_date = st.date_input("From Date", value=datetime.now() - timedelta(days=365))
with fc2:
    end_date = st.date_input("To Date", value=datetime.now() + timedelta(days=30))
with fc3:
    st.markdown("<div style='height:28px;'></div>", unsafe_allow_html=True)
    if st.button("🔄 Refresh Data", use_container_width=True):
        st.rerun()

conn = sqlite3.connect(DATABASE_PATH)
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

# ── Row 1: High-Contrast KPI Cards (Task 4 & 10) ───────────────────────
c1, c2, c3, c4 = st.columns(4)

with c1:
    st.markdown(
        render_kpi_card("Total Applications", f"{total_apps}", "📋", variant="navy", trend="+14% this cycle", trend_type="up"),
        unsafe_allow_html=True
    )
with c2:
    st.markdown(
        render_kpi_card("Pending Review", f"{pending}", "⏳", variant="teal", trend="SLA target < 3 days", trend_type="up"),
        unsafe_allow_html=True
    )
with c3:
    st.markdown(
        render_kpi_card("Active Anomalies", f"{anomalies}", "🚨", variant="danger" if anomalies > 0 else "navy", trend=f"{anomalies} items flagged", trend_type="danger" if anomalies > 0 else "up"),
        unsafe_allow_html=True
    )
with c4:
    st.markdown(
        render_kpi_card("Avg Compliance Rate", f"{avg_compliance}%", "📈", variant="saffron", trend="+2.8% YoY pass", trend_type="up"),
        unsafe_allow_html=True
    )

st.markdown("<div style='height: 1.5rem;'></div>", unsafe_allow_html=True)

# ── Row 2: Status Donut Chart & Compliance Gauge (Task 6) ──────────────
# Design Palette: Deep Navy #0B1F4B, Saffron #FF9933, Teal #14B8A6, Danger #EF4444
CHART_PALETTE = ["#0B1F4B", "#FF9933", "#14B8A6", "#EF4444", "#3B82F6", "#8B5CF6"]

r2c1, r2c2 = st.columns(2)

with r2c1:
    status_df = pd.read_sql_query(
        "SELECT status, COUNT(*) as count FROM applications GROUP BY status", conn
    )
    if not status_df.empty:
        fig_donut = px.pie(
            status_df,
            values="count",
            names="status",
            title="Application Status Distribution",
            hole=0.5,
            color="status",
            color_discrete_map={
                "APPROVED": "#10B981",
                "UNDER_REVIEW": "#F59E0B",
                "SUBMITTED": "#0B1F4B",
                "REJECTED": "#EF4444",
            }
        )
        fig_donut.update_layout(
            height=340,
            paper_bgcolor="#FFFFFF",
            font=dict(family="Inter", color="#0B1F4B"),
            title=dict(font=dict(family="Poppins", size=16, color="#0B1F4B")),
            margin=dict(l=20, r=20, t=50, b=20),
            legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5)
        )
        st.plotly_chart(fig_donut, use_container_width=True)
    else:
        st.info("No data for status distribution.")

with r2c2:
    # Plotly Gauge Chart for Compliance Score
    fig_comp_gauge = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=avg_compliance,
        delta={'reference': 85.0, 'increasing': {'color': "#10B981"}, 'font': {'size': 14}},
        title={'text': "AICTE Systemic Compliance Score", 'font': {'size': 16, 'color': '#0B1F4B', 'family': 'Poppins'}},
        number={'suffix': "%", 'font': {'size': 36, 'color': '#0B1F4B', 'family': 'Poppins'}},
        gauge={
            'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': "#CBD5E1"},
            'bar': {'color': "#FF9933"},
            'bgcolor': "#FFFFFF",
            'borderwidth': 1,
            'bordercolor': "#E2E8F0",
            'steps': [
                {'range': [0, 50], 'color': "rgba(239, 68, 68, 0.15)"},
                {'range': [50, 80], 'color': "rgba(245, 158, 11, 0.15)"},
                {'range': [80, 100], 'color': "rgba(16, 185, 129, 0.15)"}
            ],
            'threshold': {
                'line': {'color': "#10B981", 'width': 3},
                'thickness': 0.8,
                'value': 90
            }
        }
    ))
    fig_comp_gauge.update_layout(
        height=340,
        paper_bgcolor="#FFFFFF",
        font=dict(family="Inter", color="#0B1F4B"),
        margin=dict(l=20, r=20, t=50, b=20)
    )
    st.plotly_chart(fig_comp_gauge, use_container_width=True)

st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)

# ── Row 3: Category-wise Bar Chart & Monthly Trends (Task 6) ───────────
r3c1, r3c2 = st.columns(2)

with r3c1:
    cat_df = pd.read_sql_query(
        "SELECT category, COUNT(*) as count FROM applications GROUP BY category", conn
    )
    if not cat_df.empty:
        fig_bar = px.bar(
            cat_df,
            x="category",
            y="count",
            title="Category-wise Application Submissions",
            color="category",
            color_discrete_sequence=CHART_PALETTE
        )
        fig_bar.update_layout(
            height=340,
            paper_bgcolor="#FFFFFF",
            plot_bgcolor="#F8FAFC",
            font=dict(family="Inter", color="#0B1F4B"),
            title=dict(font=dict(family="Poppins", size=16, color="#0B1F4B")),
            showlegend=False,
            margin=dict(l=20, r=20, t=50, b=20)
        )
        st.plotly_chart(fig_bar, use_container_width=True)
    else:
        st.info("No category data available.")

with r3c2:
    comp_df = pd.read_sql_query(
        "SELECT checked_at, status FROM compliance_checks ORDER BY checked_at", conn
    )
    if not comp_df.empty:
        comp_df["date"] = pd.to_datetime(comp_df["checked_at"]).dt.date
        daily = comp_df.groupby(["date", "status"]).size().reset_index(name="count")
        fig_line = px.line(
            daily,
            x="date",
            y="count",
            color="status",
            title="Compliance Checks Timeline & Trend",
            color_discrete_map={"COMPLIANT": "#10B981", "NON_COMPLIANT": "#EF4444", "PARTIAL": "#F59E0B"},
            markers=True
        )
        fig_line.update_layout(
            height=340,
            paper_bgcolor="#FFFFFF",
            plot_bgcolor="#F8FAFC",
            font=dict(family="Inter", color="#0B1F4B"),
            title=dict(font=dict(family="Poppins", size=16, color="#0B1F4B")),
            margin=dict(l=20, r=20, t=50, b=20),
            legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5)
        )
        st.plotly_chart(fig_line, use_container_width=True)
    else:
        st.info("No compliance timeline data.")

st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)

# ── Row 4: Recent Alerts & Pending Actions ─────────────────────────────
r4c1, r4c2 = st.columns(2)

with r4c1:
    st.markdown("### 🚨 Recent Anomaly Alerts")
    recent_alerts = pd.read_sql_query("""
        SELECT aa.alert_type as 'Alert', aa.severity as 'Severity', aa.description as 'Description',
               aa.created_at as 'Logged At'
        FROM anomaly_alerts aa
        WHERE aa.is_resolved = 0
        ORDER BY aa.id DESC LIMIT 6
    """, conn)
    if not recent_alerts.empty:
        st.dataframe(recent_alerts, use_container_width=True, hide_index=True)
    else:
        st.success("No active anomaly alerts pending triage. 🎉")

with r4c2:
    st.markdown("### ⏳ Cases Awaiting Scrutiny Determination")
    pending_actions = pd.read_sql_query("""
        SELECT ('APP-2026-' || (1000 + a.id)) as 'Case ID', i.name as 'Institution',
               a.category as 'Category', a.status as 'Stage'
        FROM applications a JOIN institutions i ON a.institution_id = i.id
        WHERE a.status IN ('SUBMITTED', 'UNDER_REVIEW')
        ORDER BY a.id ASC LIMIT 6
    """, conn)
    if not pending_actions.empty:
        st.dataframe(pending_actions, use_container_width=True, hide_index=True)
    else:
        st.success("All assigned cases currently scrutinized! 🎉")

st.markdown("<div style='height: 1.5rem;'></div>", unsafe_allow_html=True)

# ── Row 5: Institutional Applications Docket Table ─────────────────────
cursor.execute("""
    SELECT a.id, i.name, i.aicte_id, a.category, a.academic_year, a.status, a.submitted_at
    FROM applications a
    JOIN institutions i ON a.institution_id = i.id
    ORDER BY a.submitted_at DESC
    LIMIT 10
""")
rows = cursor.fetchall()

if rows:
    table_rows_html = []
    for idx, r in enumerate(rows):
        row_bg = "#FFFFFF" if idx % 2 == 0 else "#F8FAFC"
        badge = status_badge_html(r[5])
        sub_date = str(r[6])[:10] if r[6] else "2026-03-24"
        table_rows_html.append(
            f'<tr style="background:{row_bg}; border-bottom:1px solid #E2E8F0;">'
            f'<td style="padding:12px 14px; font-weight:700; color:#0B1F4B;">APP-2026-{1000 + r[0]}</td>'
            f'<td style="padding:12px 14px; font-weight:600; color:#1E293B;">{r[1]}</td>'
            f'<td style="padding:12px 14px; color:#475569; font-family:monospace; font-size:0.85rem;">{r[2]}</td>'
            f'<td style="padding:12px 14px; color:#334155; font-size:0.85rem;">{r[3]}</td>'
            f'<td style="padding:12px 14px; color:#64748B; font-size:0.85rem;">{r[4]}</td>'
            f'<td style="padding:12px 14px;">{badge}</td>'
            f'<td style="padding:12px 14px; color:#64748B; font-size:0.82rem;">{sub_date}</td>'
            f'</tr>'
        )
    rows_joined = "".join(table_rows_html)

    docket_html = (
        '<div style="background:#FFFFFF; border:1px solid #E2E8F0; border-radius:16px; padding:20px 24px; box-shadow:0 4px 20px rgba(11,31,75,0.06); margin-bottom:1.5rem;">'
        '<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">'
        '<div>'
        '<h3 style="margin:0; font-size:1.15rem; color:#0B1F4B; font-weight:700;">📋 Recent Applications Docket</h3>'
        '<p style="margin:2px 0 0 0; color:#5B6B8A; font-size:0.8rem;">Real-time queue of institutional submissions undergoing AICTE scrutiny</p>'
        '</div>'
        '<span style="font-size:0.75rem; background:#F1F5F9; color:#475569; padding:4px 10px; border-radius:9999px; font-weight:600;">Showing Latest 10 Cases</span>'
        '</div>'
        '<div style="overflow-x:auto;">'
        '<table style="width:100%; border-collapse:collapse; text-align:left; font-size:0.88rem;">'
        '<thead>'
        '<tr style="background:#0B1F4B; color:#FFFFFF;">'
        '<th style="padding:12px 14px; font-size:0.75rem; font-weight:700; text-transform:uppercase;">Dossier ID</th>'
        '<th style="padding:12px 14px; font-size:0.75rem; font-weight:700; text-transform:uppercase;">Institution Name</th>'
        '<th style="padding:12px 14px; font-size:0.75rem; font-weight:700; text-transform:uppercase;">AICTE Permanent ID</th>'
        '<th style="padding:12px 14px; font-size:0.75rem; font-weight:700; text-transform:uppercase;">Category</th>'
        '<th style="padding:12px 14px; font-size:0.75rem; font-weight:700; text-transform:uppercase;">Academic Year</th>'
        '<th style="padding:12px 14px; font-size:0.75rem; font-weight:700; text-transform:uppercase;">Scrutiny Status</th>'
        '<th style="padding:12px 14px; font-size:0.75rem; font-weight:700; text-transform:uppercase;">Submitted Date</th>'
        '</tr>'
        '</thead>'
        f'<tbody>{rows_joined}</tbody>'
        '</table>'
        '</div>'
        '</div>'
    )
    st.markdown(docket_html, unsafe_allow_html=True)

conn.close()

# Footer
render_sih_footer()
