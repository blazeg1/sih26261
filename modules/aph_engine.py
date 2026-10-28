"""
APH-as-Code Compliance Engine for AICTE Approval Process Handbook (2024-2027).

Stores norms in external data files (config/norms.json) and provides
deterministic, unit-tested rule functions for regulatory scrutiny.

CORE PRINCIPLE: The AI is advisory only. It never approves or rejects.
It finds, explains and cites; the AICTE scrutiny officer decides.
"""

import os
import json
from pathlib import Path
from datetime import datetime, date
from typing import Dict, List, Optional, Any, Tuple


NORMS_FILE_PATH = Path(__file__).resolve().parent.parent / "config" / "norms.json"


def load_norms() -> Dict[str, Any]:
    """Load regulatory norms from external JSON data file."""
    if NORMS_FILE_PATH.exists():
        try:
            with open(NORMS_FILE_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    # Built-in fallback norms if file missing
    return {
        "faculty_student_ratio": {
            "ENGINEERING_UG": {"prescribed_ratio": 15, "max_acceptable_ratio": 20, "clause": "APH 2024-27 Clause 2.3.1"},
            "ENGINEERING_PG": {"prescribed_ratio": 12, "max_acceptable_ratio": 15, "clause": "APH 2024-27 Clause 2.3.2"},
            "MANAGEMENT_MBA": {"prescribed_ratio": 12, "max_acceptable_ratio": 15, "clause": "APH 2024-27 Clause 2.3.3"},
        },
        "land_norms_acres": {
            "MEGA_METRO": {"min_acres": 1.5, "clause": "APH 2024-27 Appendix 4 Table 4.1"},
            "URBAN": {"min_acres": 2.5, "clause": "APH 2024-27 Appendix 4 Table 4.1"},
            "RURAL": {"min_acres": 7.5, "clause": "APH 2024-27 Appendix 4 Table 4.1"},
        },
        "lease_norms": {"min_years": 30, "clause": "APH 2024-27 Clause 1.4.2"},
        "builtup_area_norms": {"sqm_per_student_intake": 4.5, "clause": "APH 2024-27 Clause 1.4.3"},
        "safety_norms": {"fire_noc_mandatory": True, "clause": "APH 2024-27 Clause 4.1.2"},
        "computing_norms": {"students_per_terminal": 4, "min_internet_bandwidth_mbps": 100, "clause": "APH 2024-27 Clause 3.2.1"},
        "intake_increase_conditions": {"min_nba_accredited_percentage": 50.0, "clause": "APH 2024-27 Clause 2.14.3"},
        "mandatory_documents": {
            "EOA": ["AFFIDAVIT", "FIRE_SAFETY_CERT", "FACULTY_LIST", "FINANCIAL_STATEMENT"],
            "NEW_INSTITUTION": ["AFFIDAVIT", "LAND_DOCUMENT", "BUILDING_PLAN", "FIRE_SAFETY_CERT", "NOC", "FINANCIAL_STATEMENT"]
        }
    }


class APHEngine:
    """
    AICTE Approval Process Handbook (APH) Rule Execution Engine.
    Executes modular unit-tested rules and returns evidence-linked findings.
    """

    def __init__(self, norms: Optional[Dict[str, Any]] = None):
        self.norms = norms or load_norms()

    # ──────────────────────────────────────────────────────────────────────────
    # Rule 1: Faculty-Student Ratio (SFR)
    # ──────────────────────────────────────────────────────────────────────────
    def check_sfr(self, total_students: int, total_faculty: int, programme: str = "ENGINEERING_UG") -> Dict[str, Any]:
        """
        Evaluate Faculty-to-Student Ratio (SFR).
        Clause: APH 2024-27 Clause 2.3.1 / 2.3.2.
        """
        prog_norm = self.norms.get("faculty_student_ratio", {}).get(programme, {
            "prescribed_ratio": 15, "max_acceptable_ratio": 20, "clause": "APH 2024-27 Clause 2.3.1"
        })
        prescribed_sfr = prog_norm.get("prescribed_ratio", 15)
        max_acceptable_sfr = prog_norm.get("max_acceptable_ratio", 20)
        clause = prog_norm.get("clause", "APH 2024-27 Clause 2.3.1")
        unverified = prog_norm.get("unverified_threshold", False)

        required_faculty = int(round(total_students / prescribed_sfr)) if prescribed_sfr > 0 else 0
        actual_sfr = round(total_students / max(total_faculty, 1), 2)
        deficit_faculty = max(0, required_faculty - total_faculty)
        deficit_pct = round((deficit_faculty / max(required_faculty, 1)) * 100, 1)

        if total_faculty <= 0:
            status = "deficiency"
            msg = f"Zero faculty reported on roster. Required: {required_faculty} faculty members."
        elif actual_sfr <= prescribed_sfr:
            status = "pass"
            msg = f"Faculty strength complies with norm 1:{prescribed_sfr} (Actual: 1:{actual_sfr})."
        elif actual_sfr <= max_acceptable_sfr:
            status = "needs_review"
            msg = f"Marginal faculty deficit of {deficit_faculty} positions ({deficit_pct}%). Actual SFR 1:{actual_sfr} exceeds prescribed 1:{prescribed_sfr}."
        else:
            status = "deficiency"
            msg = f"Substantial faculty deficit of {deficit_faculty} positions ({deficit_pct}%). Actual SFR 1:{actual_sfr} exceeds ceiling 1:{max_acceptable_sfr}."

        res = {
            "rule_id": "RULE_SFR",
            "rule_name": "Faculty-Student Ratio (SFR)",
            "status": status,
            "computed_values": {
                "total_students": total_students,
                "total_faculty": total_faculty,
                "actual_sfr": f"1:{actual_sfr}",
                "prescribed_sfr": f"1:{prescribed_sfr}",
                "required_faculty": required_faculty,
                "deficit_count": deficit_faculty,
                "deficit_percentage": f"{deficit_pct}%"
            },
            "cited_clause": clause,
            "message": msg,
            "unverified_threshold": unverified
        }
        if unverified:
            res["unverified_note"] = prog_norm.get("verification_note", "to verify against APH 2024-27")
        return res

    # ──────────────────────────────────────────────────────────────────────────
    # Rule 2: Cadre Ratio
    # ──────────────────────────────────────────────────────────────────────────
    def check_cadre_ratio(self, professors: int, assoc_professors: int, asst_professors: int, programme: str = "ENGINEERING_UG") -> Dict[str, Any]:
        """
        Evaluate Cadre Ratio (1 Professor : 2 Associate Professors : 6 Assistant Professors).
        Clause: APH 2024-27 Clause 2.3.4.
        """
        prog_norm = self.norms.get("faculty_student_ratio", {}).get(programme, {})
        cadre_spec = prog_norm.get("cadre_ratio", [1, 2, 6])
        clause = "APH 2024-27 Clause 2.3.4"
        total = professors + assoc_professors + asst_professors

        if total <= 0:
            return {
                "rule_id": "RULE_CADRE_RATIO",
                "rule_name": "Faculty Cadre Proportion",
                "status": "deficiency",
                "computed_values": {"professors": 0, "assoc_professors": 0, "asst_professors": 0},
                "cited_clause": clause,
                "message": "No faculty members on record to evaluate cadre distribution.",
                "unverified_threshold": False
            }

        # Cadre baseline for 9 positions: 1 Prof, 2 Assoc, 6 Asst
        norm_sum = sum(cadre_spec)
        req_prof = int(round(total * (cadre_spec[0] / norm_sum)))
        req_assoc = int(round(total * (cadre_spec[1] / norm_sum)))
        req_asst = total - (req_prof + req_assoc)

        prof_deficit = max(0, req_prof - professors)
        assoc_deficit = max(0, req_assoc - assoc_professors)

        if professors >= req_prof and assoc_professors >= req_assoc:
            status = "pass"
            msg = f"Cadre distribution meets 1:2:6 proportion ({professors} Prof, {assoc_professors} Assoc, {asst_professors} Asst)."
        elif (professors == 0 and req_prof > 0 and assoc_professors == 0) or (prof_deficit + assoc_deficit >= 3):
            status = "deficiency"
            msg = f"Significant cadre deficiency: Shortfall of {prof_deficit} Professor and {assoc_deficit} Assoc Professor positions."
        else:
            status = "needs_review"
            msg = f"Minor cadre imbalance: Shortfall of {prof_deficit} Professor and {assoc_deficit} Assoc Professor positions."

        return {
            "rule_id": "RULE_CADRE_RATIO",
            "rule_name": "Faculty Cadre Proportion",
            "status": status,
            "computed_values": {
                "submitted_cadre": f"{professors}:{assoc_professors}:{asst_professors}",
                "prescribed_proportion": f"{cadre_spec[0]}:{cadre_spec[1]}:{cadre_spec[2]}",
                "required_professors": req_prof,
                "required_assoc_professors": req_assoc,
                "required_asst_professors": req_asst,
                "professor_shortfall": prof_deficit,
                "assoc_professor_shortfall": assoc_deficit
            },
            "cited_clause": clause,
            "message": msg,
            "unverified_threshold": False
        }

    # ──────────────────────────────────────────────────────────────────────────
    # Rule 3: Built-up Area vs Student Intake
    # ──────────────────────────────────────────────────────────────────────────
    def check_builtup_area(self, declared_sqm: float, total_students: int, programme: str = "ENGINEERING_UG") -> Dict[str, Any]:
        """
        Evaluate instructional and overall built-up area carpet vs student strength.
        Clause: APH 2024-27 Clause 1.4.3.
        """
        norms = self.norms.get("builtup_area_norms", {})
        sqm_per_student = norms.get("sqm_per_student_intake", 4.5)
        clause = norms.get("clause", "APH 2024-27 Clause 1.4.3")
        required_sqm = round(total_students * sqm_per_student, 2)
        deficit_sqm = max(0.0, round(required_sqm - declared_sqm, 2))

        if declared_sqm >= required_sqm:
            status = "pass"
            msg = f"Built-up area of {declared_sqm:,.1f} sq.m complies with prescribed {required_sqm:,.1f} sq.m."
        elif deficit_sqm <= (required_sqm * 0.10):
            status = "needs_review"
            msg = f"Built-up area shows minor deficit of {deficit_sqm:,.1f} sq.m ({round(deficit_sqm/required_sqm*100, 1)}%)."
        else:
            status = "deficiency"
            msg = f"Built-up area shows critical deficiency of {deficit_sqm:,.1f} sq.m ({round(deficit_sqm/required_sqm*100, 1)}%)."

        return {
            "rule_id": "RULE_BUILTUP_AREA",
            "rule_name": "Built-up Carpet Area",
            "status": status,
            "computed_values": {
                "declared_sqm": declared_sqm,
                "required_sqm": required_sqm,
                "deficit_sqm": deficit_sqm,
                "norm_factor": f"{sqm_per_student} sq.m / student"
            },
            "cited_clause": clause,
            "message": msg,
            "unverified_threshold": False
        }

    # ──────────────────────────────────────────────────────────────────────────
    # Rule 4: Land Area Requirement
    # ──────────────────────────────────────────────────────────────────────────
    def check_land_area(self, declared_acres: float, location_type: str = "RURAL") -> Dict[str, Any]:
        """
        Evaluate contiguous land area based on campus geographical terrain.
        Clause: APH 2024-27 Appendix 4 Table 4.1.
        """
        land_norms = self.norms.get("land_norms_acres", {})
        norm = land_norms.get(location_type.upper(), land_norms.get("RURAL", {"min_acres": 7.5, "clause": "APH 2024-27 Appendix 4"}))
        min_acres = norm.get("min_acres", 7.5)
        clause = norm.get("clause", "APH 2024-27 Appendix 4 Table 4.1")
        unverified = norm.get("unverified_threshold", False)
        deficit = max(0.0, round(min_acres - declared_acres, 2))

        if declared_acres >= min_acres:
            status = "pass"
            msg = f"Declared land of {declared_acres:.2f} acres complies with minimum {min_acres:.2f} acres for {location_type} classification."
        else:
            status = "deficiency"
            msg = f"Land area deficiency: {declared_acres:.2f} acres declared vs {min_acres:.2f} acres required for {location_type} category."

        res = {
            "rule_id": "RULE_LAND_AREA",
            "rule_name": "Contiguous Land Area",
            "status": status,
            "computed_values": {
                "declared_acres": declared_acres,
                "required_min_acres": min_acres,
                "location_type": location_type,
                "deficit_acres": deficit
            },
            "cited_clause": clause,
            "message": msg,
            "unverified_threshold": unverified
        }
        if unverified:
            res["unverified_note"] = "to verify against APH 2024-27"
        return res

    # ──────────────────────────────────────────────────────────────────────────
    # Rule 5: Lease Duration
    # ──────────────────────────────────────────────────────────────────────────
    def check_lease_duration(self, lease_years: int, title_type: str = "REGISTERED_LEASE") -> Dict[str, Any]:
        """
        Check that land ownership or lease agreement has >= 30 years remaining.
        Clause: APH 2024-27 Clause 1.4.2.
        """
        lease_norms = self.norms.get("lease_norms", {})
        min_years = lease_norms.get("min_years", 30)
        clause = lease_norms.get("clause", "APH 2024-27 Clause 1.4.2")

        if title_type.upper() in ("OWNED", "FREEHOLD", "CLEAR_TITLE"):
            return {
                "rule_id": "RULE_LEASE_DURATION",
                "rule_name": "Land Title & Lease Duration",
                "status": "pass",
                "computed_values": {"title_type": title_type, "lease_years": "PERPETUAL_OWNED"},
                "cited_clause": clause,
                "message": "Land title is freehold / owned by sponsoring Trust.",
                "unverified_threshold": False
            }

        if lease_years >= min_years:
            status = "pass"
            msg = f"Registered lease duration of {lease_years} years satisfies minimum {min_years}-year mandate."
        elif lease_years >= 25:
            status = "needs_review"
            msg = f"Lease duration is {lease_years} years (Marginally below {min_years} years requirement; renewal affidavit required)."
        else:
            status = "deficiency"
            msg = f"Non-compliant lease duration: {lease_years} years (Minimum {min_years} years required under regulations)."

        return {
            "rule_id": "RULE_LEASE_DURATION",
            "rule_name": "Land Title & Lease Duration",
            "status": status,
            "computed_values": {
                "title_type": title_type,
                "lease_years": lease_years,
                "min_prescribed_years": min_years
            },
            "cited_clause": clause,
            "message": msg,
            "unverified_threshold": False
        }

    # ──────────────────────────────────────────────────────────────────────────
    # Rule 6: Fire Safety NOC Validity
    # ──────────────────────────────────────────────────────────────────────────
    def check_fire_noc_validity(self, expiry_date_str: Optional[str], submission_date_str: Optional[str] = None) -> Dict[str, Any]:
        """
        Validate that Fire Safety Certificate has not expired before submission date.
        Clause: APH 2024-27 Clause 4.1.2.
        """
        clause = self.norms.get("safety_norms", {}).get("clause", "APH 2024-27 Clause 4.1.2")

        if not expiry_date_str:
            return {
                "rule_id": "RULE_FIRE_NOC",
                "rule_name": "Fire & Life Safety NOC Validity",
                "status": "deficiency",
                "computed_values": {"expiry_date": None},
                "cited_clause": clause,
                "message": "Fire Safety Certificate is missing or expiry date is unparseable.",
                "unverified_threshold": False
            }

        try:
            sub_date = datetime.strptime(submission_date_str, "%Y-%m-%d").date() if submission_date_str else date.today()
            exp_date = datetime.strptime(expiry_date_str, "%Y-%m-%d").date()
        except ValueError:
            return {
                "rule_id": "RULE_FIRE_NOC",
                "rule_name": "Fire & Life Safety NOC Validity",
                "status": "needs_review",
                "computed_values": {"expiry_raw": expiry_date_str},
                "cited_clause": clause,
                "message": f"Irregular expiry date format '{expiry_date_str}' requires manual scrutinizer verification.",
                "unverified_threshold": False
            }

        days_remaining = (exp_date - sub_date).days

        if days_remaining > 30:
            status = "pass"
            msg = f"Fire Safety Certificate is valid until {exp_date} ({days_remaining} days remaining)."
        elif days_remaining >= 0:
            status = "needs_review"
            msg = f"Fire Safety Certificate expiring soon ({exp_date}, {days_remaining} days remaining). Renewal undertaking advised."
        else:
            status = "deficiency"
            msg = f"Fire Safety Certificate expired on {exp_date} (Expired {abs(days_remaining)} days prior to scrutiny)."

        return {
            "rule_id": "RULE_FIRE_NOC",
            "rule_name": "Fire & Life Safety NOC Validity",
            "status": status,
            "computed_values": {
                "expiry_date": str(exp_date),
                "evaluation_date": str(sub_date),
                "days_relative": days_remaining
            },
            "cited_clause": clause,
            "message": msg,
            "unverified_threshold": False
        }

    # ──────────────────────────────────────────────────────────────────────────
    # Rule 7: Mandatory Documents per Application Category
    # ──────────────────────────────────────────────────────────────────────────
    def check_mandatory_documents(self, uploaded_doc_types: List[str], application_type: str = "EOA") -> Dict[str, Any]:
        """
        Verify presence of mandatory documents according to application category.
        Clause: APH 2024-27 Annexure 1.
        """
        mand_dict = self.norms.get("mandatory_documents", {})
        required_list = mand_dict.get(application_type.upper(), mand_dict.get("EOA", []))
        clause = "APH 2024-27 Annexure 1 Checklist"

        uploaded_set = set(str(d).upper() for d in uploaded_doc_types)
        missing_docs = [req for req in required_list if req not in uploaded_set]

        if not missing_docs:
            status = "pass"
            msg = f"All {len(required_list)} statutory documents uploaded for category {application_type}."
        else:
            status = "deficiency"
            msg = f"Missing {len(missing_docs)} mandatory document(s) for {application_type}: {', '.join(missing_docs)}."

        return {
            "rule_id": "RULE_MANDATORY_DOCS",
            "rule_name": "Mandatory Statutory Documents",
            "status": status,
            "computed_values": {
                "application_category": application_type,
                "required_documents": required_list,
                "uploaded_documents": list(uploaded_set),
                "missing_documents": missing_docs
            },
            "cited_clause": clause,
            "message": msg,
            "unverified_threshold": False
        }

    # ──────────────────────────────────────────────────────────────────────────
    # Rule 8: Intake Increase Eligibility Conditions
    # ──────────────────────────────────────────────────────────────────────────
    def check_intake_increase_eligibility(self, nba_accredited_pct: float, years_in_existence: int, prior_deficiencies: bool = False) -> Dict[str, Any]:
        """
        Check prerequisites for Extension of Approval with increase in intake.
        Clause: APH 2024-27 Clause 2.14.3.
        """
        inc_norms = self.norms.get("intake_increase_conditions", {})
        min_nba = inc_norms.get("min_nba_accredited_percentage", 50.0)
        min_years = inc_norms.get("min_years_existence", 3)
        clause = inc_norms.get("clause", "APH 2024-27 Clause 2.14.3")

        reasons = []
        if years_in_existence < min_years:
            reasons.append(f"Institution must have operated for at least {min_years} years (current: {years_in_existence} yrs)")
        if nba_accredited_pct < min_nba:
            reasons.append(f"Minimum {min_nba}% of eligible programs must have valid NBA accreditation (current: {nba_accredited_pct}%)")
        if prior_deficiencies:
            reasons.append("Unresolved regulatory deficiencies from preceding academic year")

        if not reasons:
            status = "pass"
            msg = f"Institution satisfies statutory prerequisites for increase in student intake ({nba_accredited_pct}% NBA accreditation)."
        else:
            status = "deficiency"
            msg = "Intake increase conditions not satisfied: " + "; ".join(reasons) + "."

        return {
            "rule_id": "RULE_INTAKE_INCREASE",
            "rule_name": "Intake Expansion Eligibility",
            "status": status,
            "computed_values": {
                "nba_accredited_percentage": f"{nba_accredited_pct}%",
                "min_nba_required": f"{min_nba}%",
                "years_in_existence": years_in_existence,
                "prior_deficiencies": prior_deficiencies,
                "rejection_grounds": reasons
            },
            "cited_clause": clause,
            "message": msg,
            "unverified_threshold": False
        }

    # ──────────────────────────────────────────────────────────────────────────
    # Rule 9: Affidavit Format & Notarization
    # ──────────────────────────────────────────────────────────────────────────
    def check_affidavit(self, affidavit_uploaded: bool, has_notary_seal: bool, format_type: str = "FORMAT_A") -> Dict[str, Any]:
        """
        Check submission of statutory affidavit on stamp paper sworn before Notary.
        Clause: APH 2024-27 Appendix 3.
        """
        clause = "APH 2024-27 Appendix 3"

        if not affidavit_uploaded:
            status = "deficiency"
            msg = f"Statutory Undertaking Affidavit ({format_type}) is missing."
        elif not has_notary_seal:
            status = "needs_review"
            msg = f"Affidavit uploaded but Notary / Oath Commissioner seal requires officer manual inspection."
        else:
            status = "pass"
            msg = f"Affidavit ({format_type}) verified with notarized seal and non-judicial stamp compliance."

        return {
            "rule_id": "RULE_AFFIDAVIT",
            "rule_name": "Statutory Affidavit Compliance",
            "status": status,
            "computed_values": {
                "uploaded": affidavit_uploaded,
                "notary_seal_detected": has_notary_seal,
                "format_specification": format_type
            },
            "cited_clause": clause,
            "message": msg,
            "unverified_threshold": False
        }

    # ──────────────────────────────────────────────────────────────────────────
    # Rule 10: Barrier-Free Access for Divyangjan
    # ──────────────────────────────────────────────────────────────────────────
    def check_barrier_free_access(self, has_ramps: bool, has_lifts: bool, has_accessible_toilets: bool, building_floors: int = 2) -> Dict[str, Any]:
        """
        Check disabled-friendly facilities (ramps, lifts, special toilets).
        Clause: APH 2024-27 Clause 4.5.1.
        """
        clause = self.norms.get("accessibility_norms", {}).get("clause", "APH 2024-27 Clause 4.5.1")
        lift_floors_req = self.norms.get("accessibility_norms", {}).get("lift_mandatory_floors", 3)

        missing = []
        if not has_ramps:
            missing.append("Barrier-free ramps (<= 1:12 slope)")
        if not has_accessible_toilets:
            missing.append("Designated Divyangjan toilets")
        if building_floors >= lift_floors_req and not has_lifts:
            missing.append(f"Passenger elevator for multi-story buildings ({building_floors} floors)")

        if not missing:
            status = "pass"
            msg = "Barrier-free accessibility norms satisfied across instructional blocks."
        else:
            status = "deficiency"
            msg = f"Accessibility deficits: {', '.join(missing)}."

        return {
            "rule_id": "RULE_BARRIER_FREE",
            "rule_name": "Divyangjan Accessibility Facilities",
            "status": status,
            "computed_values": {
                "has_ramps": has_ramps,
                "has_lifts": has_lifts,
                "has_accessible_toilets": has_accessible_toilets,
                "building_floors": building_floors,
                "missing_facilities": missing
            },
            "cited_clause": clause,
            "message": msg,
            "unverified_threshold": False
        }

    # ──────────────────────────────────────────────────────────────────────────
    # Rule 11: Computing Terminal Ratio & Internet Bandwidth
    # ──────────────────────────────────────────────────────────────────────────
    def check_computing_facilities(self, terminal_count: int, total_students: int, bandwidth_mbps: int) -> Dict[str, Any]:
        """
        Check computing infrastructure (1 terminal per 4 students, min 100 Mbps).
        Clause: APH 2024-27 Clause 3.2.1.
        """
        c_norms = self.norms.get("computing_norms", {})
        ratio_term = c_norms.get("students_per_terminal", 4)
        min_bw = c_norms.get("min_internet_bandwidth_mbps", 100)
        clause = c_norms.get("clause", "APH 2024-27 Clause 3.2.1")

        req_terminals = int(round(total_students / ratio_term)) if ratio_term > 0 else 0
        term_deficit = max(0, req_terminals - terminal_count)
        bw_deficit = max(0, min_bw - bandwidth_mbps)

        if term_deficit == 0 and bw_deficit == 0:
            status = "pass"
            msg = f"Computing facilities compliant ({terminal_count} terminals vs {req_terminals} required; {bandwidth_mbps} Mbps bandwidth)."
        elif term_deficit <= (req_terminals * 0.10) and bw_deficit == 0:
            status = "needs_review"
            msg = f"Minor computing terminal shortfall: {terminal_count} available vs {req_terminals} required."
        else:
            status = "deficiency"
            msg = f"Computing deficiency: Shortfall of {term_deficit} terminals and/or {bw_deficit} Mbps internet bandwidth."

        return {
            "rule_id": "RULE_COMPUTING",
            "rule_name": "Computing Terminals & Internet Bandwidth",
            "status": status,
            "computed_values": {
                "available_terminals": terminal_count,
                "required_terminals": req_terminals,
                "bandwidth_mbps": bandwidth_mbps,
                "min_prescribed_bandwidth": min_bw
            },
            "cited_clause": clause,
            "message": msg,
            "unverified_threshold": False
        }

    # ──────────────────────────────────────────────────────────────────────────
    # Rule 12: Statutory & Mandatory Committees
    # ──────────────────────────────────────────────────────────────────────────
    def check_statutory_committees(self, constituted_committees: List[str]) -> Dict[str, Any]:
        """
        Check constitution of Anti-Ragging, ICC, and Grievance committees.
        Clause: APH 2024-27 Clause 5.1 & 5.2.
        """
        mandatory_list = [
            "Anti-Ragging Committee",
            "Internal Complaints Committee (ICC/POSH)",
            "Student Grievance Redressal Committee (SGRC)",
            "SC/ST Prevention of Atrocities Committee"
        ]
        clause = "APH 2024-27 Chapter V Clauses 5.1-5.4"

        aliases = {
            "Anti-Ragging Committee": ["anti-ragging", "antiragging", "ragging"],
            "Internal Complaints Committee (ICC/POSH)": ["icc", "posh", "internal complaints", "internal complaint"],
            "Student Grievance Redressal Committee (SGRC)": ["sgrc", "grievance", "redressal"],
            "SC/ST Prevention of Atrocities Committee": ["sc/st", "sc-st", "sc / st", "sc/st cell"]
        }

        constituted_text = " ".join(str(c).strip().lower() for c in constituted_committees)
        missing = []
        for m, keys in aliases.items():
            if not any(k in constituted_text for k in keys):
                missing.append(m)

        if not missing:
            status = "pass"
            msg = "All statutory governance committees duly constituted and notified."
        else:
            status = "deficiency"
            msg = f"Statutory committee non-compliance: {', '.join(missing)} not verified on institutional record."

        return {
            "rule_id": "RULE_COMMITTEES",
            "rule_name": "Statutory Governance Committees",
            "status": status,
            "computed_values": {
                "mandatory_committees": mandatory_list,
                "constituted_count": len(mandatory_list) - len(missing),
                "missing_committees": missing
            },
            "cited_clause": clause,
            "message": msg,
            "unverified_threshold": False
        }

    # ──────────────────────────────────────────────────────────────────────────
    # Run All Rules in Sequence
    # ──────────────────────────────────────────────────────────────────────────
    def evaluate_dossier(self, dossier: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Execute full battery of 12 regulatory checks against dossier facts.
        """
        results = []

        total_students = dossier.get("total_students", dossier.get("sanctioned_intake", 420) * 4)
        total_faculty = dossier.get("total_faculty", 0)
        prog = dossier.get("programme", "ENGINEERING_UG")

        # 1. SFR
        results.append(self.check_sfr(total_students, total_faculty, programme=prog))

        # 2. Cadre
        results.append(self.check_cadre_ratio(
            dossier.get("cadre_professors", 0),
            dossier.get("cadre_assoc_professors", 0),
            dossier.get("cadre_asst_professors", 0),
            programme=prog
        ))

        # 3. Built-up Area
        results.append(self.check_builtup_area(
            dossier.get("built_up_area_sqm", 0.0),
            total_students,
            programme=prog
        ))

        # 4. Land Area
        results.append(self.check_land_area(
            dossier.get("land_area_acres", 0.0),
            location_type=dossier.get("location_type", "RURAL")
        ))

        # 5. Lease Duration
        results.append(self.check_lease_duration(
            dossier.get("lease_duration_years", 30),
            title_type=dossier.get("title_type", "REGISTERED_LEASE")
        ))

        # 6. Fire NOC
        results.append(self.check_fire_noc_validity(
            dossier.get("fire_noc_expiry_date"),
            submission_date_str=dossier.get("submission_date")
        ))

        # 7. Mandatory Docs
        results.append(self.check_mandatory_documents(
            dossier.get("uploaded_documents", []),
            application_type=dossier.get("category", "EOA")
        ))

        # 8. Intake Increase
        if dossier.get("request_intake_increase", False):
            results.append(self.check_intake_increase_eligibility(
                dossier.get("nba_accredited_percentage", 0.0),
                dossier.get("years_in_existence", 5),
                prior_deficiencies=dossier.get("prior_deficiencies", False)
            ))

        # 9. Affidavit
        results.append(self.check_affidavit(
            dossier.get("affidavit_uploaded", True),
            dossier.get("affidavit_notarized", True)
        ))

        # 10. Barrier-Free
        results.append(self.check_barrier_free_access(
            dossier.get("has_ramps", True),
            dossier.get("has_lifts", True),
            dossier.get("has_accessible_toilets", True),
            building_floors=dossier.get("building_floors", 2)
        ))

        # 11. Computing
        results.append(self.check_computing_facilities(
            dossier.get("computer_terminals", 0),
            total_students,
            dossier.get("internet_bandwidth_mbps", 100)
        ))

        # 12. Committees
        results.append(self.check_statutory_committees(
            dossier.get("constituted_committees", [
                "Anti-Ragging Committee",
                "Internal Complaints Committee",
                "Student Grievance Redressal Committee",
                "SC/ST Cell"
            ])
        ))

        return results
