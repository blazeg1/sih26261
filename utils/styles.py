"""
Centralized Styling and UI Component Helpers for AICTE KAVACH Platform.

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
        :root {
            --bg-main: #070E1E !important;
            --bg-card: #0D1B36 !important;
            --text-main: #F1F5F9 !important;
            --text-muted: #94A3B8 !important;
            --border-light: #1E2E52 !important;
            --shadow-soft: 0 4px 20px rgba(0, 0, 0, 0.45) !important;
            --shadow-hover: 0 10px 25px rgba(0, 0, 0, 0.65) !important;
        }

        html, body,
        .stApp,
        [data-testid="stAppViewContainer"],
        [data-testid="stMain"],
        [data-testid="stMainBlockContainer"],
        .main, section.main,
        header[data-testid="stHeader"] {
            background-color: #070E1E !important;
            background: #070E1E !important;
            color: #F1F5F9 !important;
        }

        section[data-testid="stSidebar"],
        section[data-testid="stSidebar"] > div,
        [data-testid="stSidebar"],
        [data-testid="stSidebarUserContent"],
        [data-testid="stSidebarContent"],
        .stSidebar {
            background: linear-gradient(180deg, #030712 0%, #070E1E 100%) !important;
            border-right: 1px solid #1E2E52 !important;
        }

        .kpi-card,
        .gov-card,
        .score-ring-box,
        .check-item,
        .alert-card,
        .aicte-hero-bar,
        .login-hero-container,
        div[style*="background:#FFFFFF"],
        div[style*="background: #FFFFFF"],
        div[style*="background:#ffffff"],
        div[style*="background: #ffffff"],
        div[style*="background:white"],
        div[style*="background: white"],
        div[style*="background:#F8FAFC"],
        div[style*="background: #F8FAFC"],
        div[style*="background-color: #FFFFFF"],
        div[style*="background-color:#FFFFFF"],
        div[style*="background-color: white"],
        div[style*="background-color:rgb(255, 255, 255)"],
        div[style*="background-color: rgb(255, 255, 255)"],
        div[style*="background: rgb(255, 255, 255)"] {
            background-color: #0D1B36 !important;
            background: #0D1B36 !important;
            border-color: #1E2E52 !important;
            color: #F1F5F9 !important;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.45) !important;
        }

        h1, h2, h3, h4, h5, h6,
        .kpi-value,
        .sidebar-title,
        .aicte-title,
        [style*="color:#0B1F4B"],
        [style*="color: #0B1F4B"],
        [style*="color:#1E293B"],
        [style*="color: #1E293B"] {
            color: #FFFFFF !important;
        }

        .kpi-title,
        .step-label,
        .text-muted,
        .aicte-sub,
        [style*="color:#5B6B8A"],
        [style*="color: #5B6B8A"],
        [style*="color:#475569"],
        [style*="color: #475569"],
        [style*="color:#334155"],
        [style*="color: #334155"],
        [style*="color:#64748B"],
        [style*="color: #64748B"] {
            color: #94A3B8 !important;
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
            border-bottom: 1px solid #1E2E52 !important;
        }

        tr,
        tr[style*="background:#FFFFFF"],
        tr[style*="background: #FFFFFF"],
        tr[style*="background:#F8FAFC"],
        tr[style*="background: #F8FAFC"] {
            background-color: #0D1B36 !important;
            background: #0D1B36 !important;
            border-bottom: 1px solid #1E2E52 !important;
        }

        td {
            color: #F1F5F9 !important;
            border-bottom: 1px solid #1E2E52 !important;
        }

        td [style*="color:#0B1F4B"] {
            color: #FF9933 !important;
        }

        td [style*="color:#1E293B"] {
            color: #F8FAFC !important;
        }

        div[data-testid="stExpander"] {
            background-color: #0D1B36 !important;
            border-color: #1E2E52 !important;
            color: #F1F5F9 !important;
        }

        div[data-testid="stExpander"] summary {
            color: #F1F5F9 !important;
        }

        div[data-testid="stExpander"] [data-testid="stExpanderDetails"] {
            background-color: #0A152B !important;
        }

        div[style*="background:#EFF6FF"],
        div[style*="background: #EFF6FF"],
        div[style*="background:#F0FDF4"],
        div[style*="background: #F0FDF4"],
        div[style*="background:#FFFBEB"],
        div[style*="background: #FFFBEB"],
        div[style*="background:#FEF2F2"],
        div[style*="background: #FEF2F2"],
        div[style*="background:#F0FDFA"],
        div[style*="background: #F0FDFA"] {
            background: #0A172F !important;
            border-color: #1E2E52 !important;
            color: #E2E8F0 !important;
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

        .demo-account-pill {
            background: #0A152B !important;
            border-color: #1E2E52 !important;
            color: #E2E8F0 !important;
        }

        .demo-account-pill:hover {
            background: #162C6A !important;
            border-color: #FF9933 !important;
        }

        /* Sidebar Action / Logout Buttons in Dark Mode */
        section[data-testid="stSidebar"] div[data-testid="stButton"] button,
        section[data-testid="stSidebar"] div[data-testid="stButton"] button[kind="secondary"],
        section[data-testid="stSidebar"] div[data-testid="stButton"] button[kind="primary"],
        section[data-testid="stSidebar"] button[data-testid="baseButton-secondary"],
        section[data-testid="stSidebar"] button[data-testid="baseButton-primary"],
        section[data-testid="stSidebar"] .stButton > button {
            background: #DC2626 !important;
            border: 1px solid #EF4444 !important;
            border-radius: 10px !important;
            padding: 10px 16px !important;
        }

        section[data-testid="stSidebar"] div[data-testid="stButton"] button p,
        section[data-testid="stSidebar"] div[data-testid="stButton"] button span,
        section[data-testid="stSidebar"] div[data-testid="stButton"] button div,
        section[data-testid="stSidebar"] div[data-testid="stButton"] button *,
        section[data-testid="stSidebar"] .stButton > button p,
        section[data-testid="stSidebar"] .stButton > button span,
        section[data-testid="stSidebar"] .stButton > button * {
            color: #FFFFFF !important;
            font-weight: 700 !important;
            font-size: 0.95rem !important;
        }

        section[data-testid="stSidebar"] div[data-testid="stButton"] button:hover,
        section[data-testid="stSidebar"] div[data-testid="stButton"] button[kind="secondary"]:hover,
        section[data-testid="stSidebar"] .stButton > button:hover {
            background: #B91C1C !important;
            border-color: #F87171 !important;
        }

        section[data-testid="stSidebar"] div[data-testid="stButton"] button:hover p,
        section[data-testid="stSidebar"] div[data-testid="stButton"] button:hover span,
        section[data-testid="stSidebar"] div[data-testid="stButton"] button:hover div,
        section[data-testid="stSidebar"] .stButton > button:hover * {
            color: #FFFFFF !important;
        }

        /* Buttons in Main Dark View */
        div[data-testid="stButton"] button[kind="secondary"] {
            background: #0D1B36 !important;
            border-color: #1E2E52 !important;
        }

        div[data-testid="stButton"] button[kind="secondary"] p,
        div[data-testid="stButton"] button[kind="secondary"] span {
            color: #F1F5F9 !important;
        }

        .sih-footer {
            border-top-color: #1E2E52 !important;
            color: #94A3B8 !important;
        }

        .sih-footer strong {
            color: #FF9933 !important;
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
    if "dark_mode" not in st.session_state:
        st.session_state["dark_mode"] = False

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
        current_dark = st.session_state["dark_mode"]
        clean_key = f"theme_toggle_{''.join(c for c in title if c.isalnum()).lower()[:12]}"
        toggle_state = st.toggle(
            "🌙 Dark Mode",
            value=current_dark,
            key=clean_key
        )
        if toggle_state != current_dark:
            st.session_state["dark_mode"] = toggle_state
            st.rerun()

    st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)


def render_sidebar_header(user=None):
    """Render the styled sidebar brand header and user profile block."""
    st.sidebar.markdown(
        '<div class="sidebar-brand-block">'
        '<div class="sidebar-brand-icon">🛡️</div>'
        '<div>'
        '<div class="sidebar-title">AICTE KAVACH</div>'
        '<div class="sidebar-subtitle">Regulatory Shield · SIH 26261</div>'
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


def render_sidebar_logout(key_suffix=""):
    """Render a styled, prominent Sign Out button in the sidebar."""
    from utils.auth import logout
    st.sidebar.markdown("---")
    btn_key = f"sidebar_signout_btn_{key_suffix}" if key_suffix else "sidebar_signout_btn"
    if st.sidebar.button("🚪 Sign Out", key=btn_key, use_container_width=True):
        logout()
        st.rerun()


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
        '🛡️ <strong>AICTE KAVACH Platform</strong> · Built for <strong>Smart India Hackathon 2026 | PS 26261</strong><br>'
        '<span style="color:#94A3B8; font-size:0.72rem;">Knowledge-driven AICTE Verification, Anomaly Checking & Handbook Engine</span>'
        '</div>',
        unsafe_allow_html=True
    )
