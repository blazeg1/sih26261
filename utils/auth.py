"""
Simple role-based authentication for the AICTE Validation Platform (Streamlit).

Uses hashlib SHA-256 for password hashing and Streamlit session_state for
session management.  User credentials are stored in the SQLite database.
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
    """Render a Streamlit login form and handle authentication.

    On successful login the user dict is stored in
    ``st.session_state["user"]`` and the page is rerun.
    """
    with st.form("login_form", clear_on_submit=False):
        username = st.text_input("Username", placeholder="Enter your username")
        password = st.text_input("Password", type="password", placeholder="Enter your password")
        submitted = st.form_submit_button("Login", use_container_width=True)

    if submitted:
        if not username or not password:
            st.warning("Please enter both username and password.")
            return
        user = _authenticate(username, password)
        if user is None:
            st.error("Invalid username or password.")
        else:
            st.session_state["user"] = user
            st.rerun()

    st.markdown("---")
    st.caption("**Demo:** admin / admin123 · reviewer1 / review123 · viewer1 / viewer123")


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
    """Clear the current session."""
    for key in list(st.session_state.keys()):
        del st.session_state[key]


def get_current_user() -> Optional[Dict]:
    """Return the currently logged-in user dict, if any.

    Returns:
        A dict with keys username, full_name, role, department — or ``None``.
    """
    user = st.session_state.get("user")
    if isinstance(user, dict) and "username" in user:
        return user
    return None
