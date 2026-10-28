"""
Rectification Workflow Module for AICTE Approval Validation Platform.

Generates bilingual statutory deficiency notices (English & Hindi) using rule-computed figures,
computes result-by-result validation diffs across document version resubmissions,
and provides an Applicant Self-Check Mode for pre-submission compliance audit.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple


class RectificationService:
    """Manages Section 10(k) notice drafting, version diffing, and applicant self-checks."""

    def __init__(self):
        pass

    def generate_deficiency_notice_bilingual(
        self,
        institution_info: Dict[str, Any],
        flagged_deficiencies: List[Dict[str, Any]],
        officer_name: str = "Dr. Rajeshwar Pant",
        officer_role: str = "Senior Scrutiny Officer",
        deadline_days: int = 10
    ) -> Dict[str, str]:
        """
        Draft formal AICTE statutory notice in English and Hindi using computed figures.
        """
        inst_name = institution_info.get("name", "Aryabhatta Institute of Technology")
        aicte_id = institution_info.get("aicte_id", "1-3329182910")
        app_id = institution_info.get("case_id", "APP-2026-1042")
        address = institution_info.get("address", "Knowledge Park III, Greater Noida, Uttar Pradesh")
        today_str = datetime.now().strftime("%d-%m-%Y")
        deadline_str = (datetime.now() + timedelta(days=deadline_days)).strftime("%d-%m-%Y")

        # Build deficiency points in English and Hindi
        en_points = []
        hi_points = []

        for idx, d in enumerate(flagged_deficiencies, 1):
            rule = d.get("rule_name") or d.get("check") or d.get("finding", "Norm Requirement")
            clause = d.get("cited_clause", "APH 2024-27")
            msg = d.get("message") or d.get("reason", "Deficiency observed")
            vals = d.get("computed_values", {})

            en_points.append(
                f"[{idx}] {rule.upper()} ({clause}):\n"
                f"    Observation: {msg}\n"
                f"    Computed Assessment: {vals}\n"
            )

            hi_points.append(
                f"[{idx}] {rule} ({clause}):\n"
                f"    अवलोकन: {msg}\n"
                f"    संगणित मान: {vals}\n"
            )

        en_body = "\n".join(en_points) if en_points else "No major deficiencies recorded.\n"
        hi_body = "\n".join(hi_points) if hi_points else "कोई मुख्य कमी दर्ज नहीं की गई।\n"

        # English Notice
        english_notice = f"""========================================================================================
                      ALL INDIA COUNCIL FOR TECHNICAL EDUCATION
                       (A STATUTORY BODY OF THE GOVT. OF INDIA)
                   Nelson Mandela Marg, Vasant Kunj, New Delhi-110070
========================================================================================

F.No. AICTE/AB/NRC/{app_id}/DEF-NOTICE-2026                              Date: {today_str}

To,
The Chairman / Member Secretary,
{inst_name}
AICTE Permanent Institute ID: {aicte_id}
Address: {address}

SUBJECT: STATUTORY DEFICIENCY RECTIFICATION NOTICE UNDER REGULATION 10(k) OF AICTE
         APPROVAL PROCESS HANDBOOK (APH 2024-27) FOR ACADEMIC YEAR 2026-27.

Sir / Madam,

1. This is with reference to your application {app_id} submitted for Extension of Approval (EoA)
   / Institutional Changes for the Academic Session 2026-27.

2. On preliminary AICTE scrutiny through the PRAMAAN Verification Platform, the following
   deficiencies / discrepancies have been identified against prescribed regulatory norms:

{en_body}

3. Under Regulation 10(k) of the AICTE Approval Process Regulations, the Competent Authority
   hereby grants you a statutory opportunity to rectify the aforementioned deficiencies by
   uploading verified supporting documents on the AICTE Portal on or before:

                     MANDATORY RECTIFICATION DEADLINE: {deadline_str} (5:00 PM IST)

4. Failure to rectify the deficiencies within the prescribed deadline may lead to regulatory
   actions including reduction in sanctioned student intake or referral to the Standing Hearing Committee.

By Order of Competent Authority,

({officer_name})
{officer_role}
Bureau of Approval, AICTE, New Delhi
Digitally Signed through PRAMAAN Decision Support Platform
========================================================================================"""

        # Hindi Notice
        hindi_notice = f"""========================================================================================
                           अखिल भारतीय तकनीकी शिक्षा परिषद
                             (भारत सरकार का एक सांविधिक निकाय)
                         नेल्सन मंडेला मार्ग, वसंत कुंज, नई दिल्ली-110070
========================================================================================

फा. सं. एआईसीटीई/अनुमोदन/एनआरसी/{app_id}/कमी-सूचना-2026                         दिनांक: {today_str}

सेवा में,
अध्यक्ष / सचिव,
{inst_name}
एआईसीटीई स्थायी संस्थान आईडी: {aicte_id}
पता: {address}

विषय: शैक्षणिक सत्र 2026-27 हेतु एआईसीटीई अनुमोदन प्रक्रिया हस्तपुस्तिका (APH 2024-27) के
      विनियम 10(k) के अंतर्गत सांविधिक कमी सुधार नोटिस।

महोदय / महोदया,

1. यह शैक्षणिक सत्र 2026-27 हेतु अनुमोदन विस्तार (EoA) / अनुमोदन परिवर्तनों के लिए आपके द्वारा
   प्रस्तुत आवेदन {app_id} के संदर्भ में है।

2. प्रमाण (PRAMAAN) सत्यापन प्रणाली द्वारा की गई प्राथमिक जांच में निम्नलिखित कमियां / विसंगतियां
   पहचानी गई हैं:

{hi_body}

3. एआईसीटीई अनुमोदन प्रक्रिया विनियमों के नियम 10(k) के अंतर्गत, सक्षम प्राधिकारी द्वारा आपको
   निम्नलिखित अंतिम तिथि तक एआईसीटीई पोर्टल पर प्रामाणिक दस्तावेज पुनः अपलोड कर कमियों को दूर
   करने का अवसर प्रदान किया जाता है:

                   कमियां सुधारने की अंतिम तिथि: {deadline_str} (शाम 5:00 बजे तक)

4. निर्धारित समय सीमा के भीतर अनुपालन न करने की स्थिति में स्वीकृत सीटों में कटौती अथवा मामले को
   स्थायी सुनवाई समिति (SHC) को संदर्भित करने जैसी विनियामक कार्रवाई की जा सकती है।

सक्षम प्राधिकारी के आदेशानुसार,

({officer_name})
{officer_role}
अनुमोदन ब्यूरो, एआईसीटीई, नई दिल्ली
डिजिटल रूप से प्रमाणित · प्रमाण (PRAMAAN) निर्णय समर्थन प्रणाली
========================================================================================"""

        return {
            "english": english_notice,
            "hindi": hindi_notice,
            "deadline": deadline_str,
            "total_deficiencies": len(flagged_deficiencies)
        }

    def compute_validation_diff(self, prior_results: List[Dict[str, Any]], new_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Compare before-and-after results following document re-upload.
        """
        prior_map = {r.get("rule_id", f"R_{i}"): r for i, r in enumerate(prior_results)}
        new_map = {r.get("rule_id", f"R_{i}"): r for i, r in enumerate(new_results)}

        diff_items = []
        resolved_count = 0
        persisting_count = 0

        for rule_id, new_r in new_map.items():
            old_r = prior_map.get(rule_id, {})
            old_status = old_r.get("status", "needs_review")
            new_status = new_r.get("status", "needs_review")

            is_resolved = ("deficiency" in old_status.lower()) and ("pass" in new_status.lower() or "verified" in new_status.lower())
            is_persisting = ("deficiency" in old_status.lower()) and ("deficiency" in new_status.lower())

            if is_resolved:
                resolved_count += 1
            if is_persisting:
                persisting_count += 1

            diff_items.append({
                "rule_id": rule_id,
                "rule_name": new_r.get("rule_name", rule_id),
                "prior_status": old_status,
                "current_status": new_status,
                "transition": "RESOLVED" if is_resolved else "PERSISTING_DEFICIENCY" if is_persisting else "UNCHANGED",
                "message": new_r.get("message", "")
            })

        return {
            "total_rules": len(new_results),
            "resolved_count": resolved_count,
            "persisting_count": persisting_count,
            "diff_items": diff_items
        }

    def run_self_check_mode(self, application_data: Dict[str, Any], documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Execute Applicant Pre-Submission Self-Check.
        Runs deterministic single-institution checks WITHOUT exposing cross-institution intelligence.
        """
        from modules.aph_engine import APHEngine
        engine = APHEngine()
        findings = engine.evaluate_dossier(application_data)

        # Filter and summarize
        deficiencies = [f for f in findings if f["status"] == "deficiency"]
        review_items = [f for f in findings if f["status"] == "needs_review"]
        passed = [f for f in findings if f["status"] == "pass"]

        readiness_score = int(round((len(passed) / max(len(findings), 1)) * 100))

        return {
            "self_check_version": "1.0-PRE-SUBMISSION",
            "readiness_score": readiness_score,
            "status": "READY_FOR_SUBMISSION" if readiness_score >= 85 and len(deficiencies) == 0 else "DEFICIENCIES_DETECTED",
            "passed_count": len(passed),
            "deficiency_count": len(deficiencies),
            "review_count": len(review_items),
            "deficiencies": deficiencies,
            "review_items": review_items,
            "advisory_disclaimer": "Self-check mode is advisory only and does not constitute formal AICTE approval."
        }
