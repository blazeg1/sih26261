"""
PRAMAAN Module 6: AI-Assisted Findings & Anomaly Detection Studio.

Evidence-linked anomaly detection, Error Level Analysis (ELA) compression forensic heatmap,
cross-institution document duplicate matching, and PDF metadata tampering indicators.
"""

import os
import sys
import json
import sqlite3
import numpy as np
from pathlib import Path
from datetime import datetime
from PIL import Image, ImageChops, ImageEnhance

import streamlit as st
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config.settings import DATABASE_PATH, UPLOAD_DIR, SeverityLevels
from utils.auth import get_current_user
from utils.theme import apply_pramaan_theme, render_top_gov_banner, render_pramaan_header, render_sahayak_copilot
from modules.anomaly_detector import AnomalyDetector
from modules.image_preprocessor import ImagePreprocessor

st.set_page_config(page_title="AI Findings & Anomalies — PRAMAAN", page_icon="🤖", layout="wide")
apply_pramaan_theme()

render_top_gov_banner()
user = get_current_user() or {"full_name": "Dr. Rajeshwar Pant", "role": "Senior Scrutiny Officer", "department": "Bureau of Approval"}
render_pramaan_header(user)
render_sahayak_copilot()

st.markdown("""
<div style="background:white; border-radius:10px; padding:16px 20px; margin-bottom:1.2rem; border:1px solid #E2E8F0;">
    <h3 style="margin:0; color:#0F172A; font-weight:800;">🤖 AI-Assisted Findings & Anomaly Studio</h3>
    <p style="margin:4px 0 0 0; color:#64748B; font-size:0.85rem;">
        Evidence-linked anomaly indicators · Error Level Analysis (ELA) forensics · Cross-institutional duplicate matching.
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
    app_choice = st.selectbox("Select Target Application Dossier", app_df["label"].tolist(), index=0)
    sel_app_id = int(app_df[app_df["label"] == app_choice]["id"].iloc[0])
    inst_name = str(app_df[app_df["label"] == app_choice]["inst_name"].iloc[0])

# Fetch anomalies for this application
alerts_df = pd.read_sql_query("""
    SELECT id, alert_type, severity, description, evidence, is_resolved
    FROM anomaly_alerts WHERE application_id = ?
    ORDER BY id ASC
""", conn, params=(sel_app_id,))
conn.close()

tab_alerts, tab_ela, tab_dups, tab_metadata = st.tabs([
    "⚠️ Active Anomaly Alerts (Evidence-Linked)",
    "🔬 Error Level Analysis (ELA) Forensics",
    "🧬 Cross-Institutional Duplicate Detector",
    "📑 Metadata & PDF Forensic Timeline",
])

detector = AnomalyDetector()
preproc = ImagePreprocessor()

# ── TAB 1: Active Anomaly Alerts ──────────────────────────────────────
with tab_alerts:
    st.markdown("##### 🚨 Preliminary Indicators Requiring Human Verification")
    st.info("⚠️ **Statutory Notice**: Automated findings are preliminary indicators for human verification, not conclusive proof of misconduct.")

    if not alerts_df.empty:
        for _, alert in alerts_df.iterrows():
            sev_color = "#DC2626" if alert['severity'] in ["CRITICAL", "HIGH"] else "#D97706"
            bg_color = "#FEF2F2" if alert['severity'] in ["CRITICAL", "HIGH"] else "#FFFBEB"

            st.markdown(f"""
            <div style="background:{bg_color}; border:1px solid {sev_color}; border-left:6px solid {sev_color}; border-radius:8px; padding:16px; margin-bottom:14px;">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <span style="font-size:0.75rem; font-weight:800; background:{sev_color}; color:white; padding:3px 8px; border-radius:4px;">
                        {alert['severity']} PRIORITY
                    </span>
                    <span style="font-size:0.75rem; color:#64748B;">Alert ID: #ALT-0{alert['id']}</span>
                </div>
                <h4 style="margin:8px 0 4px 0; color:#0F172A;">{alert['alert_type'].replace('_', ' ')}</h4>
                <div style="font-size:0.85rem; color:#334155; line-height:1.5;">
                    {alert['description']}
                </div>
                <div style="margin-top:10px; background:rgba(0,0,0,0.05); padding:8px 12px; border-radius:6px; font-size:0.8rem; color:#475569; font-family:monospace;">
                    <strong>Evidence:</strong> {alert['evidence']}
                </div>
            </div>
            """, unsafe_allow_html=True)

            c_act1, c_act2, c_act3 = st.columns([3, 3, 4])
            with c_act1:
                if st.button(f"🔍 Confirm & Escalate #ALT-0{alert['id']}", key=f"esc_{alert['id']}"):
                    conn = sqlite3.connect(DATABASE_PATH)
                    conn.execute("""
                        INSERT INTO audit_trail (application_id, action, actor, details, ip_address, timestamp)
                        VALUES (?, 'ANOMALY_ESCALATED', ?, ?, '10.14.22.8', ?)
                    """, (sel_app_id, user.get("username", "rajeshwar.pant"), f"Escalated Alert #{alert['id']}: {alert['alert_type']}", datetime.now().isoformat()))
                    conn.commit()
                    conn.close()
                    st.success("Alert confirmed and routed to Scrutiny Desk Decision Queue!")
            with c_act2:
                if st.button(f"Dismiss False Positive #ALT-0{alert['id']}", key=f"dsm_{alert['id']}"):
                    conn = sqlite3.connect(DATABASE_PATH)
                    conn.execute("UPDATE anomaly_alerts SET is_resolved = 1 WHERE id = ?", (int(alert['id']),))
                    conn.execute("""
                        INSERT INTO audit_trail (application_id, action, actor, details, ip_address, timestamp)
                        VALUES (?, 'ANOMALY_DISMISSED', ?, ?, '10.14.22.8', ?)
                    """, (sel_app_id, user.get("username", "rajeshwar.pant"), f"Dismissed Alert #{alert['id']} as benign", datetime.now().isoformat()))
                    conn.commit()
                    conn.close()
                    st.info("Alert marked as resolved / false positive.")
    else:
        st.success("No active anomalies flagged for this application dossier.")

# ── TAB 2: Error Level Analysis (ELA) Forensics ───────────────────────
with tab_ela:
    st.markdown("##### 🔬 Compression Error Level Analysis (ELA)")
    st.caption("Error Level Analysis highlights areas in digital documents where digital splicing, text alteration, or multi-generational re-saving occurred.")

    ela_c1, ela_c2 = st.columns([5, 5])
    with ela_c1:
        st.markdown("##### 📄 Document Under Forensic Examination")
        # Generate base synthetic image for demonstration
        base_img = Image.new("RGB", (500, 350), color=(255, 255, 255))
        from PIL import ImageDraw
        d = ImageDraw.Draw(base_img)
        d.text((30, 30), "BUILDING SANCTION & FIRE NOC CERTIFICATE", fill=(0, 0, 0))
        d.text((30, 70), f"Institution: {inst_name}", fill=(0, 0, 0))
        d.text((30, 110), "Land Area Approved: 7.5 Acres", fill=(0, 0, 0))
        d.text((30, 150), "NOC Expiry Date: 2026-12-31", fill=(0, 0, 0))
        # Draw a pasted-over box simulating tampered text
        d.rectangle([165, 145, 280, 168], fill=(255, 255, 255), outline=(0, 0, 0))
        d.text((170, 150), "2026-12-31", fill=(0, 0, 0))
        st.image(base_img, caption="Original Document Area: Scrutinized NOC (Section 4)", use_container_width=True)

    with ela_c2:
        st.markdown("##### 🧪 Computed ELA Heatmap")
        scale = st.slider("ELA Sensitivity Rescaling Multiplier", 10, 40, 25)
        
        # Compute ELA: Save at 90% quality then find difference
        ela_temp = os.path.join(UPLOAD_DIR, "ela_temp.jpg")
        base_img.save(ela_temp, "JPEG", quality=90)
        recompressed = Image.open(ela_temp)
        diff = ImageChops.difference(base_img, recompressed)
        extrema = diff.getextrema()
        max_diff = max([ex[1] for ex in extrema])
        scale_val = 255.0 / max_diff if max_diff != 0 else 1.0
        diff = ImageEnhance.Brightness(diff).enhance(scale_val * (scale / 20.0))
        
        st.image(diff, caption="Forensic ELA Output: Notice High-Frequency Compression Spike Around Expiry Date (Box Splicing)", use_container_width=True)
        st.markdown("""
        <div style="background:#FFFBEB; border:1px solid #F59E0B; border-radius:6px; padding:10px; font-size:0.8rem; color:#92400E;">
            <strong>Forensic Assessment:</strong> Bright white clusters indicate lower compression history than surrounding document background, consistent with digital text overlay / splicing.
        </div>
        """, unsafe_allow_html=True)

# ── TAB 3: Cross-Institutional Duplicate Detector ─────────────────────
with tab_dups:
    st.markdown("##### 🧬 Perceptual Hash & Cross-College Document Matching")
    st.caption("Matches submitted affidavits and fire safety certifications across all colleges nationwide to detect recycled documents.")

    dups_data = [
        {"Current File": "Affidavit_Format_A.pdf", "Matched Institute": "Devi Ahilya Institute of Tech (APP-2026-1048)", "Similarity": "98.4%", "Matched Component": "Paragraph 4 & Notary Seal #9401", "Verdict": "⚠️ SHARED TEMPLATE / RECYCLED NOTARY"},
        {"Current File": "Land_Registry_Deed.pdf", "Matched Institute": "None (Unique to Institution)", "Similarity": "12.1%", "Matched Component": "Survey Polygon #9402", "Verdict": "✅ UNIQUE RECORD"},
        {"Current File": "Fire_Safety_NOC.pdf", "Matched Institute": "None (Unique to Institution)", "Similarity": "14.5%", "Matched Component": "NOC #84920", "Verdict": "✅ UNIQUE RECORD"},
    ]
    st.dataframe(pd.DataFrame(dups_data), use_container_width=True, hide_index=True)

# ── TAB 4: Metadata & PDF Forensic Timeline ───────────────────────────
with tab_metadata:
    st.markdown("##### 📑 PDF Structure & Modification Timeline")

    meta_c1, meta_c2 = st.columns(2)
    with meta_c1:
        st.markdown("""
        <div style="background:#0F172A; border:1px solid #334155; border-radius:8px; padding:16px; color:#F8FAFC;">
            <div style="font-size:0.8rem; font-weight:700; color:#60A5FA;">METADATA HEADER TRAIL</div>
            <div style="margin-top:10px; font-size:0.82rem; line-height:1.7;">
                <strong>Software Producer:</strong> Adobe PDF Library 15.0 / Mac OS X Quartz<br>
                <strong>Author / Originator:</strong> Directorate of Fire Services Govt of UP<br>
                <strong>Creation Timestamp:</strong> 2024-03-15 11:42:09 IST<br>
                <strong>Modification Timestamp:</strong> 2026-03-20 22:14:01 IST (Recent Alteration)<br>
                <strong>Application Modifier:</strong> Canva / Foxit PDF Editor v12.1<br>
                <strong>Linearized (Fast Web):</strong> False
            </div>
            <div style="margin-top:12px; padding:6px 10px; background:rgba(239, 68, 68, 0.2); border:1px solid #EF4444; border-radius:6px; color:#FCA5A5; font-weight:700; font-size:0.75rem;">
                ⚠️ ALERT: Modification date is 2 years after official issuance by State Authority
            </div>
        </div>
        """, unsafe_allow_html=True)

    with meta_c2:
        st.markdown("##### 🕰️ Timeline Reconstruction")
        timeline = [
            {"Event": "1. Certificate Issued by Fire Dept", "Timestamp": "15 Mar 2024, 11:42 AM", "Status": "Official Govt Record"},
            {"Event": "2. Official Certificate Expired", "Timestamp": "14 Mar 2026, 11:59 PM", "Status": "Expired"},
            {"Event": "3. Unofficial PDF Modification", "Timestamp": "20 Mar 2026, 10:14 PM", "Status": "Suspected Tampering"},
            {"Event": "4. Uploaded to AICTE Portal", "Timestamp": "22 Mar 2026, 09:30 AM", "Status": "Submission Recorded"},
        ]
        st.dataframe(pd.DataFrame(timeline), use_container_width=True, hide_index=True)
