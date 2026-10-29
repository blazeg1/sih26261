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
            "FROM users WHERE LOWER(username) = LOWER(?) AND password_hash = ? AND is_active = 1",
            (username.strip(), password_hash),
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


def register_officer(username: str, password: str, full_name: str, role: str = "REVIEWER", department: str = "") -> tuple:
    """Register a new scrutiny officer in the users table.

    Returns:
        tuple (bool success, str message)
    """
    username = (username or "").strip().lower()
    full_name = (full_name or "").strip()
    password = (password or "").strip()
    department = (department or "").strip()

    if not username or not full_name or not password:
        return False, "Full Name, Username, and Password are all required."

    if len(username) < 3:
        return False, "Official username must be at least 3 characters."

    if len(password) < 6:
        return False, "Password must be at least 6 characters for security compliance."

    # Parse and clean role
    clean_role = role.split()[0].upper() if role else "REVIEWER"
    if clean_role not in {"ADMIN", "REVIEWER", "VIEWER"}:
        clean_role = "REVIEWER"

    password_hash = _hash_password(password)
    from datetime import datetime
    now_str = datetime.now().isoformat()

    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE LOWER(username) = ?", (username,))
        existing = cursor.fetchone()
        if existing:
            conn.close()
            return False, f"Username '{username}' is already registered in the official registry. Please choose another username."

        cursor.execute(
            """INSERT INTO users (username, password_hash, full_name, role, department, is_active, created_at)
               VALUES (?, ?, ?, ?, ?, 1, ?)""",
            (username, password_hash, full_name, clean_role, department, now_str)
        )
        conn.commit()

        # Audit log entry for CVC vigilance
        try:
            cursor.execute(
                """INSERT INTO audit_logs (entity_type, entity_id, action, performed_by, details, created_at)
                   VALUES ('USER', ?, 'OFFICER_REGISTRATION', ?, ?, ?)""",
                (username, username, f"New officer account created with cadre {clean_role}", now_str)
            )
            conn.commit()
        except Exception:
            pass

        conn.close()
        return True, f"Officer {full_name} ({username}) registered successfully with cadre {clean_role}!"
    except Exception as e:
        return False, f"Registration failed: {e}"


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
    """Render a full-page, centered-card government-grade login and officer registration interface."""
    st.markdown("""
    <div style="max-width: 520px; margin: 1.5rem auto 0 auto; text-align: center;">
        <div style="display:inline-flex; align-items:center; justify-content:center; width:64px; height:64px; border-radius:18px; background:linear-gradient(135deg, #0B1F4B 0%, #162C6A 100%); border:2px solid #FF9933; font-size:32px; box-shadow:0 6px 18px rgba(11,31,75,0.25); margin-bottom:12px;">
            🛡️
        </div>
        <h2 style="font-family:'Poppins', sans-serif; font-size:1.6rem; font-weight:800; color:#0B1F4B; margin:0;">AICTE KAVACH</h2>
        <p style="font-size:0.85rem; color:#5B6B8A; margin:4px 0 20px 0;">
            Knowledge-driven AICTE Verification, Anomaly Checking & Handbook Engine<br>
            <span style="font-size:0.75rem; color:#FF9933; font-weight:700;">Smart India Hackathon 2026 · PS 26261</span>
        </p>
    </div>
    """, unsafe_allow_html=True)

    _, col_card, _ = st.columns([1, 2, 1])
    with col_card:
        st.markdown("""
        <div style="background:#FFFFFF; border:1px solid #E2E8F0; border-radius:16px; padding:24px; box-shadow:0 10px 25px rgba(11, 31, 75, 0.08); margin-bottom:20px;">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:14px;">
                <span style="font-size:0.85rem; font-weight:700; color:#0B1F4B;">OFFICER PORTAL ACCESS</span>
                <span style="font-size:0.7rem; background:#ECFDF5; color:#10B981; border:1px solid #A7F3D0; padding:2px 8px; border-radius:9999px; font-weight:700;">TLS 1.3 SECURE</span>
            </div>
        """, unsafe_allow_html=True)

        tab_auth, tab_reg = st.tabs(["🔐 Officer Sign In", "📝 Register New Officer"])

        with tab_auth:
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
                        st.success(f"✅ Welcome, {user['full_name']}! Redirecting to Dashboard...")
                        st.switch_page("pages/1_Dashboard.py")

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
                        st.switch_page("pages/1_Dashboard.py")
                with c_rev:
                    if st.button("🔍 Reviewer", use_container_width=True, help="Scrutiny officer role (reviewer1 / review123)"):
                        st.session_state["user"] = {
                            "username": "reviewer1",
                            "full_name": "Smt. Sunita Sharma",
                            "role": "REVIEWER",
                            "department": "Northern Regional Committee (NRC)",
                        }
                        st.switch_page("pages/1_Dashboard.py")
                with c_viw:
                    if st.button("👁️ Viewer", use_container_width=True, help="Read-only auditor (viewer1 / viewer123)"):
                        st.session_state["user"] = {
                            "username": "viewer1",
                            "full_name": "Shri Arvind Mehta",
                            "role": "VIEWER",
                            "department": "Public Scrutiny & RTI Cell",
                        }
                        st.switch_page("pages/1_Dashboard.py")

        with tab_reg:
            st.markdown("<p style='font-size:0.8rem; color:#5B6B8A; margin-bottom:12px;'>Register an authorized AICTE scrutiny officer or regional assessor profile.</p>", unsafe_allow_html=True)
            with st.form("register_officer_form"):
                reg_name = st.text_input("Full Official Name", placeholder="e.g. Dr. Arvind Kumar Sharma")
                reg_user = st.text_input("Official Username", placeholder="e.g. arvind.sharma")
                reg_role = st.selectbox(
                    "Cadre / Role Privilege",
                    [
                        "REVIEWER (Scrutiny Officer - Verify, Analyze, Issue Notices)",
                        "VIEWER (Observer / Auditor - Read-Only Dossier Access)",
                        "ADMIN (Supervisory Authority - Full Bureau Privileges)"
                    ]
                )
                reg_dept = st.text_input("Regional Office / Bureau", placeholder="e.g. Bureau of Approval, New Delhi (HQ)")
                col_p1, col_p2 = st.columns(2)
                with col_p1:
                    reg_pass = st.text_input("Password", type="password", placeholder="Min 6 characters")
                with col_p2:
                    reg_pass2 = st.text_input("Confirm Password", type="password", placeholder="Re-enter password")

                reg_submit = st.form_submit_button("🛡️ Register Officer & Enter Dashboard →", use_container_width=True, type="primary")

            if reg_submit:
                if not reg_name or not reg_user or not reg_pass:
                    st.warning("⚠️ Please fill in all required fields (Full Name, Username, Password).")
                elif reg_pass != reg_pass2:
                    st.error("❌ Passwords do not match. Please verify and re-type.")
                elif len(reg_pass) < 6:
                    st.error("❌ Password must be at least 6 characters long.")
                else:
                    success, msg = register_officer(
                        username=reg_user,
                        password=reg_pass,
                        full_name=reg_name,
                        role=reg_role,
                        department=reg_dept
                    )
                    if success:
                        clean_role = reg_role.split()[0].upper()
                        st.session_state["user"] = {
                            "username": reg_user.strip().lower(),
                            "full_name": reg_name.strip(),
                            "role": clean_role,
                            "department": reg_dept.strip(),
                        }
                        st.success(f"✅ {msg} Entering Dashboard...")
                        st.switch_page("pages/1_Dashboard.py")
                    else:
                        st.error(f"❌ {msg}")

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
