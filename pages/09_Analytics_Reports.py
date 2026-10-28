"""
PRAMAAN Module 9: Analytics & Executive Reports Studio.

Interactive Plotly analytics, regional compliance distribution heatmaps,
deficiency frequency Pareto charts, and officer productivity SLA tracking.
"""

import os
import sys
import json
import sqlite3
from pathlib import Path
from datetime import datetime

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config.settings import DATABASE_PATH
from utils.auth import get_current_user
from utils.theme import apply_pramaan_theme, render_top_gov_banner, render_pramaan_header, render_sahayak_copilot

st.set_page_config(page_title="Analytics & Reports — PRAMAAN", page_icon="📊", layout="wide")
apply_pramaan_theme()

render_top_gov_banner()
user = get_current_user() or {"full_name": "Dr. Rajeshwar Pant", "role": "Senior Scrutiny Officer", "department": "Bureau of Approval"}
render_pramaan_header(user)
render_sahayak_copilot()

st.markdown("""
<div style="background:white; border-radius:10px; padding:16px 20px; margin-bottom:1.2rem; border:1px solid #E2E8F0;">
    <h3 style="margin:0; color:#0F172A; font-weight:800;">📊 Bureau of Approval Executive Analytics</h3>
    <p style="margin:4px 0 0 0; color:#64748B; font-size:0.85rem;">
        Pan-India Scrutiny Intelligence · Regulatory Deficiency Patterns · Authority API Verification Velocity.
    </p>
</div>
""", unsafe_allow_html=True)

# High Level Executive KPIs
kpi1, kpi2, kpi3, kpi4 = st.columns(4)
with kpi1:
    st.metric("Total Docket Filings", "10,482", "+14.2% YoY")
with kpi2:
    st.metric("AI Auto-Verified", "8,214 (78.4%)", "+26.1% vs Manual")
with kpi3:
    st.metric("Deficiency Memos Issued", "1,842 (17.5%)", "-8.4% Deficit Rate")
with kpi4:
    st.metric("Avg Scrutiny Turnaround", "1.4 Days", "Target: < 3.0 Days")

st.markdown("---")

tab_overview, tab_deficiencies, tab_regional = st.tabs([
    "📈 Scrutiny Status & Category Distribution",
    "⚠️ Deficiency Frequency & Pareto Analysis",
    "🗺️ Regional Jurisdiction Breakdown",
])

# ── TAB 1: Scrutiny Status & Category Distribution ───────────────────
with tab_overview:
    col_c1, col_c2 = st.columns(2)
    
    with col_c1:
        # Category Pie Chart
        cat_df = pd.DataFrame({
            "Category": ["Extension of Approval (EoA)", "Increase in Intake", "New Institution", "Introduction of New Course", "Change of Site / Closure"],
            "Applications": [6840, 1520, 940, 780, 402]
        })
        fig_cat = px.pie(
            cat_df,
            values="Applications",
            names="Category",
            title="Application Influx by Approval Category (2026-27)",
            hole=0.4,
            color_discrete_sequence=["#2563EB", "#3B82F6", "#60A5FA", "#93C5FD", "#CBD5E1"]
        )
        fig_cat.update_layout(
            plot_bgcolor="#0F172A",
            paper_bgcolor="#0F172A",
            font=dict(color="#F8FAFC"),
            height=360,
            margin=dict(l=20, r=20, t=50, b=20)
        )
        st.plotly_chart(fig_cat, use_container_width=True)

    with col_c2:
        # Scrutiny Stage Funnel / Bar
        stage_df = pd.DataFrame({
            "Stage": ["Submitted", "Automated Validation", "Source Verified", "Officer Scrutiny", "Deficiency Memo", "Approved EoA"],
            "Count": [10482, 9890, 8420, 6800, 1842, 6150]
        })
        fig_stage = px.bar(
            stage_df,
            x="Stage",
            y="Count",
            title="Application Processing Progression Funnel",
            color="Count",
            color_continuous_scale="Blues"
        )
        fig_stage.update_layout(
            plot_bgcolor="#0F172A",
            paper_bgcolor="#0F172A",
            font=dict(color="#F8FAFC"),
            height=360,
            margin=dict(l=20, r=20, t=50, b=20)
        )
        st.plotly_chart(fig_stage, use_container_width=True)

# ── TAB 2: Deficiency Frequency & Pareto Analysis ────────────────────
with tab_deficiencies:
    st.markdown("##### 🔍 Most Prevalent Regulatory Deficiencies Identified")
    
    def_df = pd.DataFrame({
        "Deficiency Reason": [
            "Fire Safety NOC Expired / Not Submitted",
            "Cadre Ratio Imbalance (Associate Prof Shortage)",
            "Barrier-Free Ramps Non-compliant / Unverified",
            "Faculty-Student Ratio Exceeds 1:15 Norm",
            "Land Title Deed / Conversion Certificate Outdated",
            "Anti-Ragging / ICC Committee Not Re-notified",
            "Joint FDR / Reserve Fund Mismatch",
            "Computer Terminal Ratio Deficit"
        ],
        "Occurrences": [842, 614, 430, 395, 280, 210, 145, 98]
    }).sort_values("Occurrences", ascending=True)

    fig_def = px.bar(
        def_df,
        y="Deficiency Reason",
        x="Occurrences",
        orientation="h",
        title="Top Deficiencies Triggering Section 10(k) Notices",
        color="Occurrences",
        color_continuous_scale="Reds"
    )
    fig_def.update_layout(
        plot_bgcolor="#0F172A",
        paper_bgcolor="#0F172A",
        font=dict(color="#F8FAFC"),
        height=420,
        margin=dict(l=20, r=20, t=50, b=20)
    )
    st.plotly_chart(fig_def, use_container_width=True)

# ── TAB 3: Regional Jurisdiction Breakdown ────────────────────────────
with tab_regional:
    st.markdown("##### 🗺️ Regional Office Scrutiny Load & Clearance Rate")

    reg_df = pd.DataFrame({
        "Regional Office": ["Northern (Kanpur)", "North-Western (Chandigarh)", "Western (Mumbai)", "Central (Bhopal)", "Eastern (Kolkata)", "Southern (Chennai)", "South-Western (Bangalore)"],
        "Total Applications": [2450, 1890, 2100, 940, 810, 1420, 872],
        "Approved Clear": [1820, 1410, 1690, 780, 640, 1180, 720],
        "Deficiency Flagged": [630, 480, 410, 160, 170, 240, 152],
        "Clearance Rate (%)": [74.3, 74.6, 80.5, 83.0, 79.0, 83.1, 82.6]
    })
    st.dataframe(reg_df, use_container_width=True, hide_index=True)
    
    fig_reg = px.bar(
        reg_df,
        x="Regional Office",
        y=["Approved Clear", "Deficiency Flagged"],
        title="Clearance vs Deficiency by Regional Committee",
        barmode="stack",
        color_discrete_map={"Approved Clear": "#10B981", "Deficiency Flagged": "#EF4444"}
    )
    fig_reg.update_layout(
        plot_bgcolor="#0F172A",
        paper_bgcolor="#0F172A",
        font=dict(color="#F8FAFC"),
        height=380,
        margin=dict(l=20, r=20, t=50, b=20)
    )
    st.plotly_chart(fig_reg, use_container_width=True)
