"""
Centralized Styling and UI Component Helpers for PRAMAAN / AICTE Validator.

Loads static/styles.css, handles the light/dark theme toggle, and provides
standardized component renderers for KPI cards, badges, progress trackers, and footers.
All HTML renderers are formatted to avoid Markdown 4-space code block pitfalls.
"""

import os
from pathlib import Path
import streamlit as st

CSS_PATH = Path(__file__).resolve().parent.parent / "static" / "styles.css"


def load_css() -> str:
    """Read and return static/styles.css content."""
    if CSS_PATH.exists():
        with open(CSS_PATH, "r", encoding="utf-8") as f:
            return f.read()
    return ""


def apply_custom_styles():
    """Inject centralized CSS and apply dark mode overrides if enabled."""
    css_content = load_css()
    is_dark = st.session_state.get("dark_mode", False)

    dark_css = ""
    if is_dark:
        dark_css = """
        html, body, .stApp, [data-testid="stAppViewContainer"], .main {
            background-color: #070E1E !important;
            background: #070E1E !important;
            color: #F1F5F9 !important;
        }
        header[data-testid="stHeader"] {
            background-color: #070E1E !important;
        }
        .kpi-card, .gov-card, .score-ring-box, .check-item, .alert-card, .aicte-hero-bar,
        div[style*="background:#FFFFFF"], div[style*="background: #FFFFFF"],
        div[style*="background:#F8FAFC"], div[style*="background: #F8FAFC"],
        div[style*="background:white"] {
            background: #0D1B36 !important;
            border-color: #1E2E52 !important;
            color: #F1F5F9 !important;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3) !important;
        }
        h1, h2, h3, h4, h5, h6, .kpi-value, .sidebar-title, .aicte-title {
            color: #FFFFFF !important;
        }
        .kpi-title, .step-label, .text-muted {
            color: #94A3B8 !important;
        }
        .step-circle {
            background: #0D1B36 !important;
            border-color: #1E2E52 !important;
            color: #94A3B8 !important;
        }
        .tracker-step.completed .step-circle {
            background: #10B981 !important;
            border-color: #10B981 !important;
            color: #FFFFFF !important;
        }
        .tracker-step.active .step-circle {
            background: #FF9933 !important;
            border-color: #FF9933 !important;
            color: #FFFFFF !important;
        }
        div[data-baseweb="select"] > div,
        div[data-baseweb="input"] > div,
        input, textarea, select {
            background-color: #0A152B !important;
            color: #F8FAFC !important;
            border-color: #1E2E52 !important;
        }
        div[data-testid="stDataFrame"], table {
            background-color: #0D1B36 !important;
            color: #F1F5F9 !important;
            border-color: #1E2E52 !important;
        }
        th {
            background-color: #070E1E !important;
            color: #FFFFFF !important;
        }
        tr {
            background-color: #0D1B36 !important;
            border-bottom-color: #1E2E52 !important;
        }
        td {
            color: #F1F5F9 !important;
        }
        div[data-testid="stExpander"] {
            background-color: #0D1B36 !important;
            border-color: #1E2E52 !important;
            color: #F1F5F9 !important;
        }
        div[data-testid="stExpander"] summary {
            color: #F1F5F9 !important;
        }
        div[style*="background:#EFF6FF"],
        div[style*="background:#F0FDF4"],
        div[style*="background:#FFFBEB"],
        div[style*="background:#FEF2F2"] {
            background: #0A172F !important;
            color: #E2E8F0 !important;
        }
        div[data-testid="stSidebar"] {
            background: linear-gradient(180deg, #050B17 0%, #0A1428 100%) !important;
            border-right-color: #1E2E52 !important;
        }
        """

    st.markdown(
        f'<style>\n{css_content}\n{dark_css}\n</style>',
        unsafe_allow_html=True
    )


def render_gov_header():
    """Render the official Government of India & AICTE top header bar."""
    st.markdown(
        '<div class="gov-header-strip">'
        '<div>🇮🇳 <strong>Government of India</strong> · Ministry of Education · All India Council for Technical Education (AICTE)</div>'
        '<div style="display:flex; align-items:center; gap:16px;">'
        '<span class="badge-tls">🟢 Secure Session · TLS 1.3</span>'
        '<span style="color:#CBD5E1;">Bureau of Approval</span>'
        '</div>'
        '</div>',
        unsafe_allow_html=True
    )


def render_aicte_brand_bar(title="Approval Validation Platform", subtitle="AI-Powered Decision Support System for Technical Institutions"):
    """Render the main AICTE brand hero bar with synchronized Dark Mode toggle."""
    col_brand, col_theme = st.columns([8, 2])
    with col_brand:
        st.markdown(
            f'<div class="aicte-hero-bar" style="margin-bottom:0;">'
            f'<div class="aicte-brand">'
            f'<div class="aicte-emblem">🏛️</div>'
            f'<div>'
            f'<h2 class="aicte-title">AICTE {title}</h2>'
            f'<p class="aicte-sub">{subtitle} · <strong>Smart India Hackathon 2026</strong></p>'
            f'</div>'
            f'</div>'
            f'</div>',
            unsafe_allow_html=True
        )

    with col_theme:
        def _toggle_dark():
            st.session_state["dark_mode"] = st.session_state["dark_mode_toggle_val"]

        current_dark = st.session_state.get("dark_mode", False)
        st.toggle(
            "🌙 Dark Mode",
            value=current_dark,
            key="dark_mode_toggle_val",
            on_change=_toggle_dark
        )

    st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)


def render_sidebar_header(user=None):
    """Render the styled sidebar brand header and user profile block."""
    st.sidebar.markdown(
        '<div class="sidebar-brand-block">'
        '<div class="sidebar-brand-icon">🏛️</div>'
        '<div>'
        '<div class="sidebar-title">AICTE PRAMAAN</div>'
        '<div class="sidebar-subtitle">Validation Platform</div>'
        '</div>'
        '</div>',
        unsafe_allow_html=True
    )

    if user:
        initials = "".join([part[0] for part in user.get("full_name", "Officer").split()[:2]]).upper()
        role = user.get("role", "REVIEWER")
        st.sidebar.markdown(
            f'<div class="user-profile-badge">'
            f'<div class="user-avatar-circle">{initials}</div>'
            f'<div style="overflow:hidden;">'
            f'<div style="font-weight:700; font-size:0.85rem; color:#FFFFFF; white-space:nowrap; text-overflow:ellipsis;">'
            f'{user.get("full_name", "Authorized Officer")}'
            f'</div>'
            f'<div style="display:flex; align-items:center; gap:6px; margin-top:3px;">'
            f'<span class="user-role-pill">{role}</span>'
            f'<span style="font-size:0.7rem; color:#94A3B8;">{user.get("username", "")}</span>'
            f'</div>'
            f'</div>'
            f'</div>',
            unsafe_allow_html=True
        )


def render_kpi_card(title: str, value: str, icon: str, variant="navy", trend="+12% vs last cycle", trend_type="up"):
    """
    Generate an accessible, high-contrast KPI card.
    variant: 'navy' | 'saffron' | 'teal' | 'danger'
    trend_type: 'up' | 'warn' | 'danger'
    """
    trend_class = "trend-up" if trend_type == "up" else "trend-warn" if trend_type == "warn" else "trend-danger"
    trend_icon = "▲" if trend_type == "up" else "⚠️" if trend_type == "warn" else "▼"

    return (
        f'<div class="kpi-card kpi-{variant}">'
        f'<div class="kpi-header">'
        f'<span class="kpi-title">{title}</span>'
        f'<span class="kpi-icon">{icon}</span>'
        f'</div>'
        f'<div class="kpi-value">{value}</div>'
        f'<div class="kpi-trend {trend_class}">{trend_icon} {trend}</div>'
        f'</div>'
    )


def render_progress_tracker(steps: list, current_step_index: int):
    """
    Render a modern step-by-step progress tracker without markdown indentation artifacts.
    steps: list of string labels
    current_step_index: 0-indexed int
    """
    items = []
    for idx, label in enumerate(steps):
        if idx < current_step_index:
            step_state = "completed"
            symbol = "✓"
        elif idx == current_step_index:
            step_state = "active"
            symbol = str(idx + 1)
        else:
            step_state = ""
            symbol = str(idx + 1)

        items.append(
            f'<div class="tracker-step {step_state}">'
            f'<div class="step-circle">{symbol}</div>'
            f'<div class="step-label">{label}</div>'
            f'</div>'
        )

    html = f'<div class="progress-tracker">{"".join(items)}</div>'
    st.markdown(html, unsafe_allow_html=True)


def status_badge_html(status: str) -> str:
    """Return color-coded status badge HTML string."""
    stat = str(status).upper()
    if stat in ("APPROVED", "VALID", "COMPLIANT"):
        return f'<span class="status-badge badge-approved">● {stat}</span>'
    elif stat in ("UNDER_REVIEW", "PARTIAL", "WARNING"):
        return f'<span class="status-badge badge-review">● {stat}</span>'
    elif stat in ("REJECTED", "INVALID", "NON_COMPLIANT"):
        return f'<span class="status-badge badge-rejected">● {stat}</span>'
    else:
        return f'<span class="status-badge badge-submitted">● {stat}</span>'


def render_sih_footer():
    """Render the official SIH 2026 footer."""
    st.markdown(
        '<div class="sih-footer">'
        '🏛️ <strong>AICTE Approval Validation Platform</strong> · Built for <strong>Smart India Hackathon 2026 | PS 26261</strong><br>'
        '<span style="color:#94A3B8; font-size:0.72rem;">Decision Support Tool for Application Processing, Document Authentication & Regulatory Scrutiny</span>'
        '</div>',
        unsafe_allow_html=True
    )
