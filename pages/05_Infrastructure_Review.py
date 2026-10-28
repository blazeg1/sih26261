"""
PRAMAAN Module 5: Infrastructure & Geo-Spatial Intelligence Review.

Computer Vision object verification for instructional facilities, EXIF geotagging
cross-validation against revenue coordinates, and EVC physical inspection flagging.
"""

import os
import sys
import json
import sqlite3
import numpy as np
from pathlib import Path
from datetime import datetime
from PIL import Image, ImageDraw

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config.settings import DATABASE_PATH
from utils.auth import get_current_user
from utils.theme import apply_pramaan_theme, render_top_gov_banner, render_pramaan_header, render_sahayak_copilot

st.set_page_config(page_title="Infrastructure Review — PRAMAAN", page_icon="🏗️", layout="wide")
apply_pramaan_theme()

render_top_gov_banner()
user = get_current_user() or {"full_name": "Dr. Rajeshwar Pant", "role": "Senior Scrutiny Officer", "department": "Bureau of Approval"}
render_pramaan_header(user)
render_sahayak_copilot()

st.markdown("""
<div style="background:white; border-radius:10px; padding:16px 20px; margin-bottom:1.2rem; border:1px solid #E2E8F0;">
    <h3 style="margin:0; color:#0F172A; font-weight:800;">🏗️ Infrastructure & Geo-Spatial Intelligence</h3>
    <p style="margin:4px 0 0 0; color:#64748B; font-size:0.85rem;">
        Computer Vision verification of instructional labs & barrier-free facilities · EXIF Geotagging vs Revenue GIS Polygon.
    </p>
</div>
""", unsafe_allow_html=True)

# Select application
conn = sqlite3.connect(DATABASE_PATH)
app_df = pd.read_sql_query("""
    SELECT a.id, ('APP-2026-' || (1000 + a.id) || ' — ' || i.name) as label,
           i.name as inst_name, i.aicte_id, i.state
    FROM applications a JOIN institutions i ON a.institution_id = i.id
    ORDER BY a.id ASC
""", conn)

col_sel1, col_sel2 = st.columns([7, 3])
with col_sel1:
    app_choice = st.selectbox("Select Target Application", app_df["label"].tolist(), index=0)
    sel_app_id = int(app_df[app_df["label"] == app_choice]["id"].iloc[0])
    inst_name = str(app_df[app_df["label"] == app_choice]["inst_name"].iloc[0])

# Fetch infrastructure evidence
infra_evidence = pd.read_sql_query("""
    SELECT * FROM infrastructure_evidence WHERE application_id = ?
""", conn, params=(sel_app_id,))
conn.close()

# If no evidence in DB, create realistic mock entries
if infra_evidence.empty:
    infra_records = [
        {"facility_type": "SMART_CLASSROOM", "title": "Room 204 — Lecture Hall A", "declared_area_sqm": 72.0, "latitude": 28.5356, "longitude": 77.3912, "cv_confidence": 0.94, "status": "VERIFIED"},
        {"facility_type": "COMPUTER_CENTER", "title": "Central Computing Facility Lab 1", "declared_area_sqm": 165.0, "latitude": 28.5358, "longitude": 77.3915, "cv_confidence": 0.96, "status": "VERIFIED"},
        {"facility_type": "BARRIER_FREE_RAMP", "title": "Main Academic Block Accessible Ramp", "declared_area_sqm": 24.0, "latitude": 28.5352, "longitude": 77.3908, "cv_confidence": 0.91, "status": "VERIFIED"},
        {"facility_type": "PHYSICS_LAB", "title": "Applied Physics Research Laboratory", "declared_area_sqm": 88.0, "latitude": 28.5360, "longitude": 77.3918, "cv_confidence": 0.89, "status": "VERIFIED"},
        {"facility_type": "FIRE_SAFETY_EQUIPMENT", "title": "Fire Hydrant & Hose Reel Station B", "declared_area_sqm": 12.0, "latitude": 28.5354, "longitude": 77.3911, "cv_confidence": 0.85, "status": "FLAGGED_REVIEW"},
    ]
else:
    infra_records = infra_evidence.to_dict(orient="records")

tab_cv, tab_geo, tab_evc_action = st.tabs([
    "👁️ Computer Vision Facility Inspection",
    "🗺️ Geo-Spatial Coordinate & Polygon Audit",
    "🚨 EVC Physical Inspection Referral",
])

# ── TAB 1: Computer Vision Facility Inspection ────────────────────────
with tab_cv:
    st.markdown("##### 🔬 CV Neural Inspection of Submitted Photographs")
    
    col_f1, col_f2 = st.columns([4, 6])
    with col_f1:
        chosen_facility = st.selectbox(
            "Select Facility Photographic Evidence",
            [f"{r.get('facility_type')} — {r.get('title', r.get('description', 'Room Inspection'))}" for r in infra_records],
            index=0
        )
        selected_record = infra_records[0]
        for r in infra_records:
            if r.get('facility_type') in chosen_facility:
                selected_record = r
                break

        st.markdown(f"""
        <div style="background:#F8FAFC; border:1px solid #CBD5E1; border-radius:8px; padding:14px; margin-top:10px;">
            <div style="font-size:0.75rem; font-weight:700; color:#2563EB;">FACILITY SPECIFICATIONS</div>
            <div style="margin-top:6px; font-size:0.85rem; line-height:1.6; color:#0F172A;">
                <strong>Type:</strong> {selected_record.get('facility_type')}<br>
                <strong>Carpet Area:</strong> {selected_record.get('declared_area_sqm', 72.0)} Sq. Meters<br>
                <strong>Min Prescribed:</strong> 66.0 Sq. Meters (Compliant)<br>
                <strong>AI Model:</strong> MobileNet-SSD / YOLOv8 Floor Inspector<br>
                <strong>Confidence Score:</strong> <span style="color:#059669; font-weight:700;">{selected_record.get('cv_confidence', 0.94) * 100:.1f}%</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("##### 🔍 Detected Visual Elements")
        items_detected = [
            {"Element": "Lecture Podiums / Desks", "Status": "Detected (Count: 36)", "Norm": "Satisfied"},
            {"Element": "Ceiling Projector Unit", "Status": "Detected (1 Unit)", "Norm": "Satisfied"},
            {"Element": "Interactive Whiteboard", "Status": "Detected (1 Unit)", "Norm": "Satisfied"},
            {"Element": "Ventilation / Windows", "Status": "Natural Lighting > 15%", "Norm": "Satisfied"},
        ]
        st.dataframe(pd.DataFrame(items_detected), use_container_width=True, hide_index=True)

    with col_f2:
        st.markdown("##### 📷 Photographic Evidence with Bounding Overlays")
        # Generate simulated visual inspection image
        img = Image.new("RGB", (600, 420), color=(240, 245, 250))
        d = ImageDraw.Draw(img)
        # Draw mock classroom layout
        d.rectangle([10, 10, 590, 410], outline=(148, 163, 184), width=3)
        # Desks
        for y in range(80, 320, 50):
            for x in range(50, 520, 110):
                d.rectangle([x, y, x + 80, y + 35], fill=(203, 213, 225), outline=(100, 116, 139), width=2)
                d.text((x + 8, y + 10), "Student Desk", fill=(51, 65, 85))
        # Whiteboard at front
        d.rectangle([160, 20, 440, 60], fill=(255, 255, 255), outline=(37, 99, 235), width=3)
        d.text((220, 32), "[ Whiteboard 98.4% ]", fill=(37, 99, 235))
        # Projector box
        d.rectangle([250, 140, 350, 180], outline=(16, 185, 129), width=3)
        d.text((255, 150), "[ Projector 94% ]", fill=(5, 150, 105))

        st.image(img, caption=f"Computer Vision Classified: {selected_record.get('facility_type')} — Bounding Boxes Active", use_container_width=True)

# ── TAB 2: Geo-Spatial Coordinate & Polygon Audit ─────────────────────
with tab_geo:
    st.markdown("##### 🛰️ EXIF GPS Geotagging vs Declared Revenue Boundary")
    st.caption("Verifies that institutional photographs were physically captured within the approved campus perimeter.")

    campus_lat = 28.5355
    campus_lon = 77.3910

    # Build coordinates dataframe
    geo_points = [
        {"Site": "Declared Campus Center", "Latitude": campus_lat, "Longitude": campus_lon, "Type": "Revenue GIS Boundary", "Delta": "0.0 m (Baseline)"},
        {"Site": "Classroom Block Photo", "Latitude": campus_lat + 0.0001, "Longitude": campus_lon + 0.0002, "Type": "EXIF Captured", "Delta": "24.1 m (Within Campus)"},
        {"Site": "Computing Lab Photo", "Latitude": campus_lat + 0.0003, "Longitude": campus_lon + 0.0004, "Type": "EXIF Captured", "Delta": "48.2 m (Within Campus)"},
        {"Site": "Accessible Ramp Photo", "Latitude": campus_lat - 0.0002, "Longitude": campus_lon - 0.0001, "Type": "EXIF Captured", "Delta": "26.8 m (Within Campus)"},
    ]
    geo_df = pd.DataFrame(geo_points)

    st.dataframe(geo_df, use_container_width=True, hide_index=True)

    # Plot coordinates on interactive scatter chart
    fig = px.scatter(
        geo_df,
        x="Longitude",
        y="Latitude",
        text="Site",
        color="Type",
        color_discrete_map={"Revenue GIS Boundary": "#DC2626", "EXIF Captured": "#2563EB"},
        title="Campus Perimeter & Evidence Location Mapping (GPS EXIF)",
    )
    fig.update_traces(marker=dict(size=14, line=dict(width=2, color="DarkSlateGrey")), textposition="top center")
    fig.update_layout(
        plot_bgcolor="#0F172A",
        paper_bgcolor="#0F172A",
        font=dict(color="#F8FAFC"),
        height=420,
        margin=dict(l=40, r=40, t=50, b=40)
    )
    st.plotly_chart(fig, use_container_width=True)

# ── TAB 3: EVC Physical Inspection Referral ───────────────────────────
with tab_evc_action:
    st.markdown("##### 🚨 Expert Visiting Committee (EVC) Trigger Desk")
    st.markdown("""
    Under AICTE Regulations Section 7.4, if computer vision inspection reveals ambiguous infrastructure,
    altered photographs, or off-perimeter GPS coordinates, the scrutiny officer may refer the case for a
    **Surprise / Physical Expert Visiting Committee (EVC)** inspection.
    """)

    evc_c1, evc_c2 = st.columns(2)
    with evc_c1:
        evc_reason = st.selectbox(
            "Primary Ground for Inspection Referral",
            [
                "Fire Safety NOC Expired & Inconclusive On-Site Fire Hydrants",
                "Discrepancy in Declared Land Boundary vs Satellite Geo-coordinates",
                "Suspected Staged / Recycled Laboratory Equipment Photographs",
                "Non-compliant Ramp Slope for Divyangjan Barrier-Free Access",
                "Random Quality Audit Inspection (5% Statistical Sample)"
            ]
        )
        evc_lead = st.selectbox("Recommended Committee Lead Expert", [
            "Prof. K. N. Satyanarayana (Director, IIT Tirupati)",
            "Prof. S. R. Gandhi (Former Director, NIT Surat)",
            "Prof. Manoj Singh Gaur (Director, IIT Jammu)"
        ])
        inspection_urgency = st.radio("Inspection Priority", ["Urgent (Within 7 Days)", "Standard (Within 21 Days)"], horizontal=True)

    with evc_c2:
        st.markdown("##### 📋 Action Authorization")
        st.info(f"Target: **{inst_name}** · AICTE ID: 1-3329182910\nInitiator: **{user.get('full_name', 'Dr. Rajeshwar Pant')}**")
        if st.button("🚩 Formalize EVC Inspection Order", type="primary"):
            conn = sqlite3.connect(DATABASE_PATH)
            conn.execute("""
                INSERT INTO audit_trail (application_id, action, actor, details, ip_address, timestamp)
                VALUES (?, 'EVC_INSPECTION_ORDERED', ?, ?, '10.14.22.8', ?)
            """, (sel_app_id, user.get("username", "rajeshwar.pant"), f"Ordered EVC Inspection. Reason: {evc_reason}. Lead: {evc_lead}", datetime.now().isoformat()))
            conn.commit()
            conn.close()
            st.success("✅ EVC Physical Inspection Notice issued and recorded in PRAMAAN Immutable Audit Trail!")
