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
    """Inject centralized CSS and apply dark mode class if enabled."""
    css_content = load_css()
    is_dark = st.session_state.get("dark_mode", False)
    theme_class = "dark-theme" if is_dark else "light-theme"

    st.markdown(
        f'<style>\n{css_content}\n</style>\n<div id="theme-wrapper" class="{theme_class}"></div>',
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
    """Render the main AICTE brand hero bar."""
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
        dark_mode = st.toggle("🌙 Dark Mode", value=st.session_state.get("dark_mode", False), key="dark_mode_toggle")
        if dark_mode != st.session_state.get("dark_mode", False):
            st.session_state["dark_mode"] = dark_mode
            st.rerun()

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
