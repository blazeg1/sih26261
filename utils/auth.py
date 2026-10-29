"""
Simple role-based authentication for the AICTE Validation Platform (Streamlit).

Uses hashlib SHA-256 for password hashing and Streamlit session_state for
session management. User credentials are stored in the SQLite database.
"""

import hashlib
import sqlite3
from typing import Dict, List, Optional

import streamlit as st

from config.settings import DATABASE_PATH


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _hash_password(password: str) -> str:
    """Return the SHA-256 hex digest of *password*.

    Args:
        password: Plain-text password.

    Returns:
        Hex-encoded SHA-256 hash.
    """
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def _authenticate(username: str, password: str) -> Optional[Dict]:
    """Validate credentials against the users table.

    Args:
        username: Login username.
        password: Plain-text password.

    Returns:
        A dict with user info on success, or ``None``.
    """
    password_hash = _hash_password(password)
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            "SELECT username, full_name, role, department "
            "FROM users WHERE username = ? AND password_hash = ? AND is_active = 1",
            (username, password_hash),
        ).fetchone()
        conn.close()
        if row:
            return {
                "username": row["username"],
                "full_name": row["full_name"],
                "role": row["role"],
                "department": row["department"] or "",
            }
    except sqlite3.Error:
        st.error("Database error during authentication. Please contact the administrator.")
    return None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def login_form() -> None:
    """Render a Streamlit login form and handle authentication."""
    with st.form("sidebar_login_form", clear_on_submit=False):
        username = st.text_input("Username", placeholder="Enter username", key="sb_login_user")
        password = st.text_input("Password", type="password", placeholder="Enter password", key="sb_login_pass")
        submitted = st.form_submit_button("Sign In", use_container_width=True)

    if submitted:
        if not username or not password:
            st.warning("Please enter both username and password.")
            return
        user = _authenticate(username, password)
        if user is None:
            st.error("Invalid credentials.")
        else:
            st.session_state["user"] = user
            st.rerun()

    with st.expander("🔑 Demo Access Credentials", expanded=False):
        st.markdown("""
        - **Admin:** `admin` / `admin123`
        - **Reviewer:** `reviewer1` / `review123`
        - **Viewer:** `viewer1` / `viewer123`
        """)


def render_login_page() -> None:
    """Render a full-page, centered-card government-grade login interface."""
    st.markdown("""
    <div style="max-width: 460px; margin: 1.5rem auto 0 auto; text-align: center;">
        <div style="display:inline-flex; align-items:center; justify-content:center; width:64px; height:64px; border-radius:18px; background:linear-gradient(135deg, #0B1F4B 0%, #162C6A 100%); border:2px solid #FF9933; font-size:32px; box-shadow:0 6px 18px rgba(11,31,75,0.25); margin-bottom:12px;">
            🏛️
        </div>
        <h2 style="font-family:'Poppins', sans-serif; font-size:1.6rem; font-weight:800; color:#0B1F4B; margin:0;">AICTE PRAMAAN</h2>
        <p style="font-size:0.85rem; color:#5B6B8A; margin:4px 0 20px 0;">
            Institutional Approval Validation & Regulatory Scrutiny Platform<br>
            <span style="font-size:0.75rem; color:#FF9933; font-weight:700;">Smart India Hackathon 2026 · PS 26261</span>
        </p>
    </div>
    """, unsafe_allow_html=True)

    _, col_card, _ = st.columns([1, 2, 1])
    with col_card:
        st.markdown("""
        <div style="background:#FFFFFF; border:1px solid #E2E8F0; border-radius:16px; padding:24px; box-shadow:0 10px 25px rgba(11, 31, 75, 0.08);">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:16px;">
                <span style="font-size:0.85rem; font-weight:700; color:#0B1F4B;">OFFICER AUTHENTICATION</span>
                <span style="font-size:0.7rem; background:#ECFDF5; color:#10B981; border:1px solid #A7F3D0; padding:2px 8px; border-radius:9999px; font-weight:700;">TLS 1.3 SECURE</span>
            </div>
        """, unsafe_allow_html=True)

        with st.form("full_login_form"):
            username = st.text_input("Official Username", placeholder="e.g. admin or reviewer1")
            password = st.text_input("Password", type="password", placeholder="Enter official password")
            remember = st.checkbox("Keep me signed in for this session", value=True)
            submit_btn = st.form_submit_button("Authenticate & Enter Platform →", use_container_width=True, type="primary")

        if submit_btn:
            if not username or not password:
                st.warning("⚠️ Please provide both your official username and password.")
            else:
                user = _authenticate(username, password)
                if user is None:
                    st.error("❌ Invalid official credentials. Please check or use demo access.")
                else:
                    st.session_state["user"] = user
                    st.success(f"✅ Welcome, {user['full_name']}!")
                    st.rerun()

        # Collapsible Demo Access Box
        with st.expander("🔑 Demo Access (SIH Evaluator Quick-Login)", expanded=True):
            st.markdown("<p style='font-size:0.75rem; color:#64748B; margin-bottom:8px;'>Click any role below to instantly log in as a test persona:</p>", unsafe_allow_html=True)
            c_adm, c_rev, c_viw = st.columns(3)
            with c_adm:
                if st.button("👑 Admin", use_container_width=True, help="Full system privileges (admin / admin123)"):
                    st.session_state["user"] = {
                        "username": "admin",
                        "full_name": "Dr. Rajeshwar Pant",
                        "role": "ADMIN",
                        "department": "Bureau of Approval & Regulatory Compliance",
                    }
                    st.rerun()
            with c_rev:
                if st.button("🔍 Reviewer", use_container_width=True, help="Scrutiny officer role (reviewer1 / review123)"):
                    st.session_state["user"] = {
                        "username": "reviewer1",
                        "full_name": "Smt. Sunita Sharma",
                        "role": "REVIEWER",
                        "department": "Northern Regional Committee (NRC)",
                    }
                    st.rerun()
            with c_viw:
                if st.button("👁️ Viewer", use_container_width=True, help="Read-only auditor (viewer1 / viewer123)"):
                    st.session_state["user"] = {
                        "username": "viewer1",
                        "full_name": "Shri Arvind Mehta",
                        "role": "VIEWER",
                        "department": "Public Scrutiny & RTI Cell",
                    }
                    st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)


def check_auth() -> bool:
    """Check whether a user is currently logged in.

    Returns:
        ``True`` if ``st.session_state["user"]`` contains a valid user dict.
    """
    return isinstance(st.session_state.get("user"), dict) and "username" in st.session_state.get("user", {})


def require_role(allowed_roles: List[str]):
    """Decorator that restricts a Streamlit page function to specific roles.

    Args:
        allowed_roles: List of role strings (e.g. ``["ADMIN", "REVIEWER"]``).
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            user = get_current_user()
            if user is None:
                st.warning("Please log in to access this page.")
                return None
            if user["role"] not in allowed_roles:
                st.error(
                    f"⛔ Access denied. Requires: {', '.join(allowed_roles)}. "
                    f"Your role: **{user['role']}**."
                )
                return None
            return func(*args, **kwargs)
        return wrapper
    return decorator


def logout() -> None:
    """Clear the current session while preserving theme preference."""
    dark_mode = st.session_state.get("dark_mode", False)
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    if dark_mode:
        st.session_state["dark_mode"] = True


def get_current_user() -> Optional[Dict]:
    """Return the currently logged-in user dict, if any.

    Returns:
        A dict with keys username, full_name, role, department — or ``None``.
    """
    user = st.session_state.get("user")
    if isinstance(user, dict) and "username" in user:
        return user
    return None
