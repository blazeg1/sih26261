"""
Page 4: Compliance Check

Compares application data against configurable regulatory checklists
and provides category-wise compliance scoring.
"""

import sys
import json
import sqlite3
from pathlib import Path

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config.settings import APP_TITLE, DATABASE_PATH, ApplicationCategories
from utils.auth import check_auth, get_current_user
from utils.helpers import get_timestamp

st.set_page_config(page_title=f"Compliance Check — {APP_TITLE}", page_icon="✅", layout="wide")

if not check_auth():
    st.warning("🔒 Please log in from the main page.")
    st.stop()

user = get_current_user()

try:
    from modules.compliance_checker import ComplianceChecker
    COMPLIANCE_AVAILABLE = True
except ImportError:
    COMPLIANCE_AVAILABLE = False

st.title("✅ Regulatory Compliance Check")
st.markdown("Compare applications against AICTE Approval Process Handbook requirements.")

# ── Select Application ─────────────────────────────────────────────────
conn = sqlite3.connect(DATABASE_PATH)
apps = pd.read_sql_query(
    "SELECT a.id, i.name, a.category, a.academic_year, a.status "
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

# Get application and docs
conn = sqlite3.connect(DATABASE_PATH)
app_row = pd.read_sql_query(
    "SELECT a.*, i.name as inst_name, i.aicte_id FROM applications a "
    "JOIN institutions i ON a.institution_id = i.id WHERE a.id = ?",
    conn, params=(app_id,)
)
docs_df = pd.read_sql_query("SELECT * FROM documents WHERE application_id = ?", conn, params=(app_id,))
conn.close()

app_info = app_row.iloc[0] if not app_row.empty else {}

# ── Run Compliance Check ──────────────────────────────────────────────
if st.button("🔬 Run Compliance Check", type="primary", use_container_width=True):
    if not COMPLIANCE_AVAILABLE:
        st.error("Compliance checker module not available.")
        st.stop()

    category = app_info.get("category", ApplicationCategories.EOA) if isinstance(app_info, dict) or hasattr(app_info, "get") else ApplicationCategories.EOA
    checklist_map = {
        ApplicationCategories.EOA: "config/checklists/eoa_checklist.json",
        ApplicationCategories.NEW_INSTITUTION: "config/checklists/new_institution_checklist.json",
    }
    checklist_path = checklist_map.get(category, "config/checklists/eoa_checklist.json")

    try:
        checker = ComplianceChecker(checklist_path)
    except Exception:
        checker = ComplianceChecker("config/checklists/eoa_checklist.json")

    with st.spinner("Running compliance checks..."):
        documents = []
        for _, doc in docs_df.iterrows():
            d = doc.to_dict()
            try:
                ed = d.get("extracted_data")
                if ed and isinstance(ed, str):
                    d["extracted_data"] = json.loads(ed)
            except (json.JSONDecodeError, TypeError):
                d["extracted_data"] = {}
            documents.append(d)

        application_data = {
            "institution_name": app_info.get("inst_name", "") if hasattr(app_info, "get") else "",
            "aicte_id": app_info.get("aicte_id", "") if hasattr(app_info, "get") else "",
            "category": category,
            "documents": documents,
            "faculty_count": 45,
            "student_count": 600,
            "land_area_acres": 5.2,
            "built_up_area_sqft": 52000,
            "fdr_amount": 12500000,
            "programmes": [
                {"name": "B.Tech CS", "level": "UG", "intake": 120},
                {"name": "B.Tech ME", "level": "UG", "intake": 60},
                {"name": "MBA", "level": "PG", "intake": 60},
            ],
        }

        results = checker.check_compliance(application_data, documents)

        # Normalize status values to strings
        for r in results:
            if hasattr(r.get("status"), "value"):
                r["status"] = r["status"].value
            if hasattr(r.get("category"), "value"):
                r["category"] = r["category"].value

        score = checker.get_compliance_score(results)
        raw_summary = checker.get_compliance_summary(results)

    # ── Display Results ────────────────────────────────────────────────
    st.markdown("### 📊 Compliance Results")

    # Gauge
    gauge = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        title={"text": "Overall Compliance Score"},
        gauge={
            "axis": {"range": [0, 100]},
            "bar": {"color": "#28a745" if score >= 80 else "#ffc107" if score >= 50 else "#dc3545"},
            "steps": [
                {"range": [0, 50], "color": "#f8d7da"},
                {"range": [50, 80], "color": "#fff3cd"},
                {"range": [80, 100], "color": "#d4edda"},
            ],
        },
    ))
    gauge.update_layout(height=300)
    st.plotly_chart(gauge, use_container_width=True)

    # Category breakdown — normalize enum keys to strings
    by_category = raw_summary.get("by_category", {})
    summary = {}
    for cat_key, status_counts in by_category.items():
        cat_name = cat_key.value if hasattr(cat_key, "value") else str(cat_key)
        normalized = {}
        for status_key, count in status_counts.items():
            status_name = status_key.value if hasattr(status_key, "value") else str(status_key)
            normalized[status_name] = count
        summary[cat_name] = normalized

    if summary:
        st.markdown("#### 📋 Category-wise Breakdown")

        cat_names = list(summary.keys())
        tabs = st.tabs(cat_names)

        for tab, cat_name in zip(tabs, cat_names):
            with tab:
                cat_data = summary[cat_name]
                cat_results = [r for r in results if str(r.get("category", "")) == cat_name]

                mc1, mc2, mc3, mc4 = st.columns(4)
                with mc1:
                    st.metric("✅ Compliant", cat_data.get("COMPLIANT", 0))
                with mc2:
                    st.metric("❌ Non-Compliant", cat_data.get("NON_COMPLIANT", 0))
                with mc3:
                    st.metric("🔶 Partial", cat_data.get("PARTIAL", 0))
                with mc4:
                    st.metric("➖ N/A", cat_data.get("NOT_APPLICABLE", 0))

                # Detailed table
                if cat_results:
                    rows = []
                    for r in cat_results:
                        status_str = str(r.get("status", ""))
                        icon = {"COMPLIANT": "✅", "NON_COMPLIANT": "❌", "PARTIAL": "🔶", "NOT_APPLICABLE": "➖"}.get(status_str, "❓")
                        rows.append({
                            "Status": f"{icon} {status_str}",
                            "Check Item": r.get("check_item", ""),
                            "Required": r.get("required_value", ""),
                            "Actual": r.get("actual_value", ""),
                            "Recommendation": r.get("recommendation", ""),
                        })
                    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

        # Category chart
        cat_chart_data = []
        for cat, data in summary.items():
            cat_chart_data.append({
                "Category": cat,
                "Compliant": data.get("COMPLIANT", 0),
                "Non-Compliant": data.get("NON_COMPLIANT", 0),
                "Partial": data.get("PARTIAL", 0),
            })

        chart_df = pd.DataFrame(cat_chart_data)
        if not chart_df.empty:
            fig = px.bar(chart_df, x="Category", y=["Compliant", "Non-Compliant", "Partial"],
                         title="Compliance by Category", barmode="group",
                         color_discrete_map={"Compliant": "#28a745", "Non-Compliant": "#dc3545", "Partial": "#ffc107"})
            st.plotly_chart(fig, use_container_width=True)

    # Save to database
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    now = get_timestamp()

    for r in results:
        cursor.execute(
            "INSERT INTO compliance_checks (application_id, checklist_name, check_item, category, status, required_value, actual_value, evidence, notes, checked_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                app_id,
                f"{category} Checklist",
                r.get("check_item", ""),
                str(r.get("category", "")),
                str(r.get("status", "")),
                str(r.get("required_value", "")),
                str(r.get("actual_value", "")),
                r.get("evidence", ""),
                r.get("recommendation", ""),
                now,
            ),
        )

    cursor.execute(
        "INSERT INTO audit_trail (application_id, action, actor, details, ip_address, timestamp) "
        "VALUES (?, 'COMPLIANCE_CHECK_RUN', ?, ?, '127.0.0.1', ?)",
        (app_id, user["username"] if user else "system", f"Compliance score: {score:.1f}%", now),
    )
    conn.commit()
    conn.close()
    st.success("✅ Compliance results saved.")

    # Export
    st.markdown("---")
    report_text = f"COMPLIANCE REPORT — Application #{app_id}\n"
    report_text += f"Score: {score:.1f}%\n\n"
    for r in results:
        report_text += f"[{r.get('status', '')}] {r.get('check_item', '')} — Required: {r.get('required_value', '')}, Actual: {r.get('actual_value', '')}\n"
    st.download_button("📥 Download Compliance Report", report_text, f"compliance_report_app{app_id}.txt", "text/plain")

# ── Previous Results ───────────────────────────────────────────────────
st.markdown("---")
st.markdown("### 📜 Previous Compliance Results")

conn = sqlite3.connect(DATABASE_PATH)
prev_comp = pd.read_sql_query(
    "SELECT check_item, category, status, required_value, actual_value, checked_at "
    "FROM compliance_checks WHERE application_id = ? ORDER BY checked_at DESC LIMIT 50",
    conn, params=(app_id,)
)
conn.close()

if not prev_comp.empty:
    st.dataframe(prev_comp, use_container_width=True, hide_index=True)
else:
    st.info("No previous compliance checks. Click 'Run Compliance Check' above.")
