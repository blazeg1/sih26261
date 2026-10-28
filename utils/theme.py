"""
PRAMAAN Theme & UI Component Library.

Provides GovTech visual styling, top header ribbons, officer profiles,
Sahayak AI Assistant, and responsive CSS for the AICTE PRAMAAN platform.
"""

import streamlit as st


def apply_pramaan_theme():
    """Inject PRAMAAN GovTech theme styles into Streamlit page."""
    st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    /* Top Gov Banner */
    .gov-banner {
        background: #060B18;
        border-bottom: 1px solid #1E293B;
        padding: 6px 16px;
        font-size: 0.78rem;
        color: #94A3B8;
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin: -4rem -4rem 1.5rem -4rem;
    }
    .gov-banner strong {
        color: #F8FAFC;
    }
    .gov-indicator {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        color: #10B981;
        font-weight: 500;
    }

    /* PRAMAAN Header Bar */
    .pramaan-header {
        background: linear-gradient(135deg, #0F172A 0%, #1E293B 100%);
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 14px 20px;
        margin-bottom: 1.5rem;
        display: flex;
        justify-content: space-between;
        align-items: center;
        box-shadow: 0 4px 20px rgba(0,0,0,0.25);
    }
    .pramaan-brand {
        display: flex;
        align-items: center;
        gap: 14px;
    }
    .pramaan-logo-icon {
        width: 44px;
        height: 44px;
        background: linear-gradient(135deg, #2563EB 0%, #1D4ED8 100%);
        border-radius: 10px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 24px;
        box-shadow: 0 0 15px rgba(37,99,235,0.4);
    }
    .pramaan-title {
        font-size: 1.35rem;
        font-weight: 800;
        color: #F8FAFC;
        letter-spacing: -0.5px;
        margin: 0;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .pramaan-title span {
        font-size: 0.95rem;
        font-weight: 500;
        color: #94A3B8;
    }
    .pramaan-subtitle {
        font-size: 0.76rem;
        color: #64748B;
        margin: 2px 0 0 0;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .officer-chip {
        background: rgba(30, 41, 59, 0.8);
        border: 1px solid #334155;
        border-radius: 30px;
        padding: 6px 14px;
        display: flex;
        align-items: center;
        gap: 10px;
    }
    .officer-avatar {
        width: 32px;
        height: 32px;
        border-radius: 50%;
        background: #2563EB;
        color: white;
        font-weight: 700;
        font-size: 0.8rem;
        display: flex;
        align-items: center;
        justify-content: center;
    }

    /* Hero Case & Triage Cards */
    .hero-case-card {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 18px 20px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.04);
        margin-bottom: 1.5rem;
        color: #0F172A;
    }
    .hero-case-tag {
        font-size: 0.72rem;
        font-weight: 700;
        letter-spacing: 0.8px;
        color: #2563EB;
        text-transform: uppercase;
        margin-bottom: 4px;
    }
    .hero-case-title {
        font-size: 1.15rem;
        font-weight: 700;
        color: #0F172A;
        margin-bottom: 4px;
    }
    .hero-case-meta {
        font-size: 0.82rem;
        color: #64748B;
    }

    /* Priority Triage 6-Card Grid */
    .triage-card {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 10px;
        padding: 14px 16px;
        transition: all 0.2s ease;
        box-shadow: 0 1px 4px rgba(0,0,0,0.03);
    }
    .triage-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
    }
    .triage-label {
        font-size: 0.72rem;
        font-weight: 700;
        color: #64748B;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 4px;
    }
    .triage-value {
        font-size: 1.85rem;
        font-weight: 800;
        color: #0F172A;
        line-height: 1.1;
    }
    .triage-sub {
        font-size: 0.75rem;
        color: #94A3B8;
        margin-top: 4px;
    }
    .val-danger { color: #DC2626 !important; }
    .val-warning { color: #EA580C !important; }
    .val-primary { color: #2563EB !important; }
    .val-success { color: #059669 !important; }

    /* Module Navigation Pills in Sidebar */
    div[data-testid="stSidebar"] {
        background-color: #0B132B !important;
        border-right: 1px solid #1E293B;
    }
    div[data-testid="stSidebar"] h1, 
    div[data-testid="stSidebar"] h2, 
    div[data-testid="stSidebar"] h3, 
    div[data-testid="stSidebar"] p,
    div[data-testid="stSidebar"] span {
        color: #F8FAFC !important;
    }

    /* Glass Panels for Dark Theme sections */
    .glass-panel {
        background: rgba(15, 23, 42, 0.75);
        border: 1px solid rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(12px);
        border-radius: 12px;
        padding: 20px;
        color: white;
    }
</style>
""", unsafe_allow_html=True)


def render_top_gov_banner():
    """Render the official Government of India header banner."""
    st.markdown("""
    <div class="gov-banner">
        <div>
            🇮🇳 <strong>Government of India</strong> · Ministry of Education · All India Council for Technical Education (AICTE) · <span style="color:#60A5FA; font-weight:600;">PRAMAAN Regulatory Platform</span>
        </div>
        <div style="display:flex; align-items:center; gap:16px;">
            <span class="gov-indicator">🟢 Secure Session · TLS 1.3</span>
            <span>🔒 Audit Logging Enabled</span>
            <span>Workspace: <strong style="color:#F8FAFC;">Bureau of Approval</strong></span>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_pramaan_header(user_info=None):
    """Render the main PRAMAAN brand and officer chip bar."""
    name = user_info.get("full_name", "Dr. Rajeshwar Pant") if user_info else "Dr. Rajeshwar Pant"
    role = user_info.get("role", "Senior Scrutiny Officer") if user_info else "Senior Scrutiny Officer"
    dept = user_info.get("department", "Bureau of Approval & Regulatory Compliance") if user_info else "Bureau of Approval & Regulatory Compliance"
    initials = "".join([part[0] for part in name.split()[:2]]).upper()

    st.markdown(f"""
    <div class="pramaan-header">
        <div class="pramaan-brand">
            <div class="pramaan-logo-icon">🏛️</div>
            <div>
                <p class="pramaan-title">PRAMAAN <span>प्रमाण से विश्वास</span></p>
                <p class="pramaan-subtitle">Institutional Verification & Regulatory Compliance Intelligence Platform</p>
            </div>
        </div>
        <div style="display:flex; align-items:center; gap:12px;">
            <div style="background:#0F172A; border:1px solid #334155; border-radius:8px; padding:6px 12px; font-size:0.8rem; color:#94A3B8;">
                🔍 Search PRAMAAN... <span style="background:#1E293B; padding:1px 6px; border-radius:4px; font-size:0.7rem;">/</span>
            </div>
            <div class="officer-chip">
                <div class="officer-avatar">{initials}</div>
                <div>
                    <div style="font-size:0.82rem; font-weight:700; color:#F8FAFC;">{name}</div>
                    <div style="font-size:0.7rem; color:#94A3B8;">{role} · {dept}</div>
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_sahayak_copilot():
    """Render the Sahayak AI Assistant floating popover/dialog."""
    with st.expander("🤖 **Sahayak AI** — AICTE Regulatory Copilot (Click to open)", expanded=False):
        st.markdown("""
        **Sahayak Copilot** is your AI-enabled scrutinizer assistant powered by AICTE Approval Process Handbook (APH) regulations.
        """)
        q = st.text_input("Ask Sahayak about APH norms, deficiency clauses, or case dossier analysis:", placeholder="e.g. What is the minimum faculty-student ratio for B.Tech CS? Or summarize APP-2026-1042 anomalies.")
        if q:
            if "1042" in q or "aryabhatta" in q.lower():
                st.info("🤖 **Sahayak Insight on APP-2026-1042 (Aryabhatta Institute):**\n- Fire Safety NOC expired 14 days ago (State Portal API mismatch).\n- Error Level Analysis flagged architect stamp box on Sanctioned Plan.\n- Faculty-Student ratio is 1:13.8 (Compliant).\n- **Suggested Action**: Issue Section 10(k) Rectification Notice with 10-day deadline.")
            elif "ratio" in q.lower() or "faculty" in q.lower():
                st.success("🤖 **AICTE Handbook Norm (Clause 6.1):**\n- Undergraduate Engineering: **1:15** SFR with min 20% PhD faculty.\n- Postgraduate MBA/MCA: **1:12** SFR with min 30% PhD faculty.\n- Deficit penalty: 10% reduction in approved intake if deficit exceeds 20%.")
            else:
                st.write(f"🤖 **Sahayak Response:** AICTE APH regulations stipulate that all documentary submissions for {q} must be verified against digital issuing authority repositories. In case of conflicting records, an Expert Visiting Committee (EVC) may be scheduled under Regulation 7.4.")
