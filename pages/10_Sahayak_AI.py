"""
PRAMAAN Module 10: Sahayak AI — AICTE Regulatory Copilot.

Conversational regulatory assistant grounded in the AICTE Approval Process Handbook
(APH 2024-27), case dossier anomaly summarization, and statutory drafting.
"""

import os
import sys
import json
import sqlite3
from pathlib import Path
from datetime import datetime

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config.settings import DATABASE_PATH
from utils.auth import get_current_user
from utils.theme import apply_pramaan_theme, render_top_gov_banner, render_pramaan_header

st.set_page_config(page_title="Sahayak AI Copilot — PRAMAAN", page_icon="🤖", layout="wide")
apply_pramaan_theme()

render_top_gov_banner()
user = get_current_user() or {"full_name": "Dr. Rajeshwar Pant", "role": "Senior Scrutiny Officer", "department": "Bureau of Approval"}
render_pramaan_header(user)

st.markdown("""
<div style="background:white; border-radius:10px; padding:16px 20px; margin-bottom:1.2rem; border:1px solid #E2E8F0;">
    <h3 style="margin:0; color:#0F172A; font-weight:800;">🤖 Sahayak AI — AICTE Regulatory Copilot (सहायक)</h3>
    <p style="margin:4px 0 0 0; color:#64748B; font-size:0.85rem;">
        Intelligent Scrutiny Assistant grounded in AICTE Approval Process Handbook (APH 2024-27) & Statutory Regulations.
    </p>
</div>
""", unsafe_allow_html=True)

# Initialize chat session history
if "sahayak_messages" not in st.session_state:
    st.session_state.sahayak_messages = [
        {
            "role": "assistant",
            "content": f"Namaste **{user.get('full_name', 'Dr. Rajeshwar Pant')}**! I am **Sahayak AI**, your AICTE regulatory assistant. I can help you evaluate dossiers against APH 2024-27 norms, calculate cadre penalties, verify issuing authority policies, or draft official notices."
        }
    ]

# Preset quick prompts
st.markdown("##### ⚡ Quick Scrutiny Prompts")
q1, q2, q3, q4 = st.columns(4)
clicked_prompt = None
with q1:
    if st.button("📋 Dossier APP-2026-1042 Audit", use_container_width=True):
        clicked_prompt = "Summarize the active deficiencies and anomalies for case dossier APP-2026-1042 (Aryabhatta Institute of Technology)."
with q2:
    if st.button("⚖️ Faculty Deficit Penalty Norm", use_container_width=True):
        clicked_prompt = "What are the statutory penalties under APH Chapter VIII if faculty deficit is 15% vs >20%?"
with q3:
    if st.button("🚒 Expired Fire NOC Regulation", use_container_width=True):
        clicked_prompt = "Can an Extension of Approval (EoA) be granted if the Fire Safety NOC expired prior to submission?"
with q4:
    if st.button("🏛️ Land Area Norms (Rural vs Metro)", use_container_width=True):
        clicked_prompt = "What is the minimum land requirement for an Engineering & Technology degree institution in Mega/Metro vs Rural areas?"

# Display chat history
for msg in st.session_state.sahayak_messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

def generate_sahayak_reply(prompt_text: str) -> str:
    p_lower = prompt_text.lower()
    
    if "1042" in p_lower or "aryabhatta" in p_lower:
        return """
### 📋 Dossier Summary: APP-2026-1042 (Aryabhatta Institute of Technology)

- **Application Category:** Extension of Approval (EoA) · AY 2026-27
- **AICTE Permanent ID:** `1-3329182910`
- **Key Findings:**
  1. **Fire Safety NOC Defect (Critical):** State Fire Services Portal query confirms certificate `#NOC/ST/2024/84920` **expired on 14-03-2026**. Uploaded PDF shows suspicious compression artifacts around expiry box under Error Level Analysis (ELA).
  2. **Cadre Cadence Deficit (Marginal):** Shortage of 2 Associate Professors against 1:2:6 cadre ratio (APH Clause 2.3.4).
  3. **Land & Infrastructure (Compliant):** 7.5 Acres confirmed via State Revenue GIS survey `#SRV-2019-9402-UP`.
  4. **Instructional Facilities (Compliant):** 65 Faculty on roster (1:13.8 SFR, compliant with 1:15 norm). 250 terminals active.
- **Statutory Recommendation:** Issue **Section 10(k) Rectification Notice** with a strict 10-calendar-day deadline to submit renewed Fire NOC. Do not issue final EoA order until verified.
"""
    elif "penalty" in p_lower or "deficit" in p_lower or "ratio" in p_lower:
        return """
### ⚖️ AICTE Faculty Deficit Regulations (APH 2024-27 Chapter VIII)

Under the AICTE Approval Process Regulations:
1. **Deficit <= 10%:** Advisory warning issued to the institution; full intake permitted for current academic session.
2. **Deficit > 10% and <= 20%:** Mandatory **10% reduction in sanctioned student intake** across undergraduate engineering programs for 1 year.
3. **Deficit > 20%:** 
   - No new programs or intake increase permitted.
   - Institution placed in **'No Admission' category** for affected disciplines, or up to 50% reduction in overall intake.
   - Case automatically referred to the **Standing Hearing Committee (SHC)**.
4. **Cadre Imbalance:** If Professor or Associate Professor positions remain vacant, Assistant Professors may be accepted only temporarily with appropriate salary scale justification.
"""
    elif "fire" in p_lower or "noc" in p_lower:
        return """
### 🚒 Safety & Fire NOC Policy (APH Chapter IV Clause 4.1.2)

- **Strict Mandate:** A valid, unexpired Fire & Life Safety Certificate issued by the competent State / UT Fire Services Directorate is a **non-negotiable prerequisite** for Extension of Approval.
- **Expired Certificates:** An institution cannot be granted unconditional EoA with an expired NOC.
- **Conditional Provision:** If the institution has submitted an official renewal receipt from the State Fire Department prior to expiry, a provisional notice under Section 10(k) may be issued granting up to **30 days** for final certificate submission.
- **Physical Inspection:** If doubts persist regarding fire escape staircases or hydrant lines, an Expert Visiting Committee (EVC) should be deployed immediately.
"""
    elif "land" in p_lower:
        return """
### 🏛️ Land Requirements for Engineering & Technology (APH Appendix 4)

| Location Category | Minimum Land Requirement | Permissible Built-up FSI / FAR |
| :--- | :--- | :--- |
| **Mega / Metro Cities** (Delhi, Mumbai, Kolkata, Chennai, Bangalore, etc.) | **1.5 Acres** | As per local municipal Master Plan |
| **Urban / Municipal Corporation Areas** | **2.5 Acres** | Normative standard |
| **Rural / Other Non-Urban Areas** | **7.5 Acres** (contiguous single plot) | Minimum 30-year registered lease / free title |

*Note: For multi-story vertical campuses in Metro cities, a structural safety certificate from a certified IIT/NIT civil department is mandatory.*
"""
    elif "notice" in p_lower or "draft" in p_lower:
        return """
### 📜 Draft Statutory Notice Template

```text
F.No. AICTE/AB/NRC/APP-2026-XXXX/DEF-2026
ALL INDIA COUNCIL FOR TECHNICAL EDUCATION
Nelson Mandela Marg, Vasant Kunj, New Delhi-110070

SHOW CAUSE / DEFICIENCY NOTICE UNDER REGULATION 10(k)

WHEREAS the institution submitted an application for Extension of Approval (EoA) 2026-27;
AND WHEREAS scrutiny revealed non-compliance with APH 2024-27 Clause 4.1.2 (Mandatory Safety NOC);
NOW THEREFORE the institution is granted 10 calendar days to upload verified documentation,
failing which adverse regulatory actions including reduction of intake shall follow.
```
"""
    else:
        return f"""
### 🤖 Sahayak Regulatory Guidance

Based on **AICTE Approval Process Handbook (APH 2024-27)**:
- Regarding **'{prompt_text}'**: The competent authority requires documentary evidence to be cross-verified through issuing authority APIs (DigiLocker, State Portals) and matched with permanent institutional master records.
- Where anomalies or discrepancies are flagged by PRAMAAN AI, the scrutiny officer retains discretionary authority to:
  1. Issue a Section 10(k) Rectification Notice.
  2. Order a surprise Expert Visiting Committee (EVC).
  3. Refer the dossier to the Standing Hearing Committee (SHC).

*Need a specific regulation citation or dossier audit? Let me know!*
"""

# Process prompt from text input or button click
user_query = st.chat_input("Ask Sahayak about AICTE regulations, APH clauses, or case dossiers...")
active_query = clicked_prompt or user_query

if active_query:
    st.session_state.sahayak_messages.append({"role": "user", "content": active_query})
    with st.chat_message("user"):
        st.markdown(active_query)

    reply = generate_sahayak_reply(active_query)
    st.session_state.sahayak_messages.append({"role": "assistant", "content": reply})
    with st.chat_message("assistant"):
        st.markdown(reply)
