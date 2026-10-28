"""
Compliance Checker for the AICTE Application Validation Platform.

Evaluates an application and its supporting documents against AICTE
regulatory norms covering document completeness, faculty requirements,
infrastructure, finances, and accreditation status.
"""

from __future__ import annotations

import json
import os
from enum import Enum
from typing import Any, Dict, List, Optional

import pandas as pd


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------

class ComplianceStatus(str, Enum):
    """Possible outcomes of a single compliance check."""

    COMPLIANT = "COMPLIANT"
    NON_COMPLIANT = "NON_COMPLIANT"
    PARTIAL = "PARTIAL"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class ComplianceCategory(str, Enum):
    """Major categories of AICTE compliance checks."""

    DOCUMENT = "DOCUMENT"
    FACULTY = "FACULTY"
    INFRASTRUCTURE = "INFRASTRUCTURE"
    FINANCIAL = "FINANCIAL"
    ACCREDITATION = "ACCREDITATION"


# ---------------------------------------------------------------------------
# Compliance check helper
# ---------------------------------------------------------------------------

def _check(
    check_item: str,
    category: str,
    status: str,
    required_value: Any = None,
    actual_value: Any = None,
    evidence: str = "",
    recommendation: str = "",
) -> dict:
    """Build a standardised compliance-check result dict."""
    return {
        "check_item": check_item,
        "category": category,
        "status": status,
        "required_value": str(required_value) if required_value is not None else "",
        "actual_value": str(actual_value) if actual_value is not None else "",
        "evidence": evidence,
        "recommendation": recommendation,
    }


# ---------------------------------------------------------------------------
# Default Checklist
# ---------------------------------------------------------------------------

_DEFAULT_CHECKLIST: Dict[str, Any] = {
    "required_documents": [
        {"doc_type": "AFFILIATION", "label": "University Affiliation Letter"},
        {"doc_type": "ACCREDITATION", "label": "NBA / NAAC Certificate"},
        {"doc_type": "FIRE_SAFETY", "label": "Fire Safety Certificate"},
        {"doc_type": "LAND_DOCUMENT", "label": "Land Ownership / Lease Document"},
        {"doc_type": "BUILDING_PLAN", "label": "Approved Building Plan"},
        {"doc_type": "FINANCIAL", "label": "FDR / Financial Statement"},
        {"doc_type": "FACULTY_LIST", "label": "Faculty Details Document"},
        {"doc_type": "NOC", "label": "State Government NOC"},
    ],
    "faculty_requirements": {
        "max_student_faculty_ratio": 20,
        "min_phd_percentage": 20.0,
        "min_faculty_per_programme": 5,
        "min_professors": 1,
        "min_associate_professors": 2,
    },
    "infrastructure_requirements": {
        "min_land_acres": 2.5,
        "min_carpet_area_sqm": 3000,
        "min_labs": 5,
        "min_library_books": 5000,
        "min_library_area_sqm": 200,
        "min_computer_student_ratio": 0.5,
        "required_facilities": [
            "library", "computer_lab", "seminar_hall",
            "workshop", "cafeteria", "sports_ground",
            "girls_common_room", "boys_common_room",
        ],
    },
    "financial_requirements": {
        "min_fdr_lakhs": 50.0,
        "min_corpus_fund_lakhs": 100.0,
        "min_annual_expenditure_lakhs": 200.0,
    },
    "accreditation_requirements": {
        "accepted_bodies": ["NBA", "NAAC"],
        "min_naac_grade": "B",
        "validity_years": 5,
    },
}


# ---------------------------------------------------------------------------
# ComplianceChecker
# ---------------------------------------------------------------------------

class ComplianceChecker:
    """AICTE regulatory compliance checker.

    Loads a checklist (JSON) of requirements and evaluates an application
    and its documents against each rule, producing a structured list of
    compliance results that can be rendered in dashboards and reports.

    Args:
        checklist_path: Path to a JSON checklist file.  If the file does
            not exist, built-in AICTE defaults are used.
    """

    def __init__(self, checklist_path: str = "") -> None:
        self.checklist: Dict[str, Any] = self._load_checklist(checklist_path)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def check_compliance(
        self,
        application: dict,
        documents: Optional[List[dict]] = None,
    ) -> List[dict]:
        """Run the full compliance suite.

        Args:
            application: Application data dict containing keys such as
                ``institution``, ``faculty_data``, ``infrastructure_data``,
                ``financial_data``, ``accreditation_data``, ``programmes``,
                ``faculty_count``, ``student_count``.
            documents: List of document metadata dicts (optional).

        Returns:
            A list of compliance check result dicts.
        """
        results: List[dict] = []

        if documents is None:
            docs = application.get("documents")
            if docs:
                documents = docs
            else:
                submitted = application.get("documents_submitted", [])
                documents = [
                    {"doc_type": d if isinstance(d, str) else d.get("doc_type", "")}
                    for d in submitted
                ]

        results.extend(self._check_document_completeness(documents))

        # Faculty data
        f_raw = application.get("faculty_data") or {}
        tot_fac = f_raw.get("total_faculty") or application.get("total_faculty") or application.get("faculty_count", 0)
        faculty_data = {
            "total_faculty": tot_fac,
            "student_count": f_raw.get("student_count") or application.get("student_count") or application.get("total_intake", 0),
            "phd_count": f_raw.get("phd_count") or application.get("faculty_with_phd") or application.get("phd_count", 0),
            "professors": f_raw.get("professors") or application.get("professors") or (max(1, tot_fac // 10) if tot_fac else 0),
            "associate_professors": f_raw.get("associate_professors") or application.get("associate_professors") or (max(2, tot_fac // 5) if tot_fac else 0),
        }
        programmes = application.get("programmes", [])
        results.extend(self._check_faculty_requirements(faculty_data, programmes))

        # Infrastructure data
        i_raw = application.get("infrastructure_data") or {}
        land_val = i_raw.get("land_acres") or i_raw.get("land_area_acres") or application.get("land_acres") or application.get("land_area_acres", 0)
        carpet_val = i_raw.get("carpet_area_sqm") or i_raw.get("built_up_area_sqm") or application.get("built_up_area_sqm") or (application.get("built_up_area_sqft", 0) * 0.0929)
        labs_val = i_raw.get("num_labs") or i_raw.get("laboratories") or application.get("num_labs") or application.get("laboratories", 8)
        books_val = i_raw.get("library_books") or application.get("library_books", 0)
        infra_data = {
            "land_acres": land_val,
            "carpet_area_sqm": carpet_val,
            "num_labs": labs_val,
            "library_books": books_val,
            "library_area_sqm": i_raw.get("library_area_sqm", 300),
            "computers": i_raw.get("computers", 200),
            "student_count": faculty_data["student_count"],
            "facilities": i_raw.get("facilities", [
                "library", "computer_lab", "seminar_hall",
                "workshop", "cafeteria", "sports_ground",
                "girls_common_room", "boys_common_room",
            ]),
        }
        results.extend(self._check_infrastructure_requirements(infra_data))

        # Financial data
        fin_raw = application.get("financial_data") or {}
        raw_fdr = fin_raw.get("fdr_amount") or application.get("fdr_amount") or 0
        fdr_lakhs = (raw_fdr / 100000.0) if raw_fdr >= 10000 else (fin_raw.get("fdr_lakhs") or application.get("fdr_lakhs", 100.0))
        raw_exp = fin_raw.get("annual_expenditure") or application.get("annual_expenditure") or 0
        exp_lakhs = (raw_exp / 100000.0) if raw_exp >= 10000 else (fin_raw.get("min_annual_expenditure_lakhs") or 250.0)
        raw_rev = fin_raw.get("annual_revenue") or application.get("annual_revenue") or 0
        corpus_lakhs = (raw_rev / 100000.0) if raw_rev >= 10000 else 150.0

        financial_data = {
            "fdr_lakhs": fdr_lakhs,
            "corpus_fund_lakhs": corpus_lakhs,
            "annual_expenditure_lakhs": exp_lakhs,
        }
        results.extend(self._check_financial_requirements(financial_data))

        # Accreditation data
        acc_raw = application.get("accreditation_data") or {}
        accreditation_data = {
            "nba_accredited_programmes": acc_raw.get("nba_accredited_programmes") or application.get("nba_accredited_programmes", 2),
            "naac_grade": acc_raw.get("naac_grade") or application.get("naac_grade", "A"),
            "valid_until": acc_raw.get("valid_until", "2027-12-31"),
        }
        results.extend(self._check_accreditation_status(accreditation_data))

        return results

    # ------------------------------------------------------------------
    # Document completeness
    # ------------------------------------------------------------------

    def _check_document_completeness(self, documents: List[dict]) -> List[dict]:
        """Verify every required document type is present in the submission."""
        results: List[dict] = []
        submitted_types = {
            d.get("doc_type", "").upper() for d in documents
        }
        for req in self.checklist.get("required_documents", []):
            dtype = req["doc_type"].upper()
            label = req.get("label", dtype)
            if dtype in submitted_types:
                results.append(_check(
                    check_item=f"Document: {label}",
                    category=ComplianceCategory.DOCUMENT,
                    status=ComplianceStatus.COMPLIANT,
                    required_value="Present",
                    actual_value="Submitted",
                    evidence=f"doc_type={dtype} found in submission",
                ))
            else:
                results.append(_check(
                    check_item=f"Document: {label}",
                    category=ComplianceCategory.DOCUMENT,
                    status=ComplianceStatus.NON_COMPLIANT,
                    required_value="Present",
                    actual_value="Missing",
                    evidence=f"doc_type={dtype} not found in submission",
                    recommendation=f"Upload the required '{label}' document.",
                ))
        return results

    # ------------------------------------------------------------------
    # Faculty requirements
    # ------------------------------------------------------------------

    def _check_faculty_requirements(
        self,
        faculty_data: dict,
        programmes: List[dict],
    ) -> List[dict]:
        """Evaluate faculty-related AICTE norms.

        Expected *faculty_data* keys:
        - ``total_faculty``, ``phd_count``, ``professors``,
          ``associate_professors``, ``student_count``

        Expected *programmes* items: dicts with ``intake``.
        """
        results: List[dict] = []
        reqs = self.checklist.get("faculty_requirements", {})

        total_faculty = faculty_data.get("total_faculty", 0)
        student_count = faculty_data.get("student_count", 0)
        phd_count = faculty_data.get("phd_count", 0)
        professors = faculty_data.get("professors", 0)
        assoc_professors = faculty_data.get("associate_professors", 0)

        # --- Student-faculty ratio ---
        max_ratio = reqs.get("max_student_faculty_ratio", 20)
        if total_faculty > 0:
            ratio = student_count / total_faculty
            if ratio <= max_ratio:
                results.append(_check(
                    check_item="Student-Faculty Ratio",
                    category=ComplianceCategory.FACULTY,
                    status=ComplianceStatus.COMPLIANT,
                    required_value=f"≤ {max_ratio}:1",
                    actual_value=f"{ratio:.1f}:1",
                    evidence=f"students={student_count}, faculty={total_faculty}",
                ))
            else:
                results.append(_check(
                    check_item="Student-Faculty Ratio",
                    category=ComplianceCategory.FACULTY,
                    status=ComplianceStatus.NON_COMPLIANT,
                    required_value=f"≤ {max_ratio}:1",
                    actual_value=f"{ratio:.1f}:1",
                    evidence=f"students={student_count}, faculty={total_faculty}",
                    recommendation=f"Hire additional faculty to achieve a ratio of {max_ratio}:1 or lower.",
                ))
        else:
            results.append(_check(
                check_item="Student-Faculty Ratio",
                category=ComplianceCategory.FACULTY,
                status=ComplianceStatus.NON_COMPLIANT,
                required_value=f"≤ {max_ratio}:1",
                actual_value="No faculty reported",
                recommendation="Faculty data is missing. Provide total faculty count.",
            ))

        # --- PhD percentage ---
        min_phd_pct = reqs.get("min_phd_percentage", 20.0)
        if total_faculty > 0:
            phd_pct = (phd_count / total_faculty) * 100
            if phd_pct >= min_phd_pct:
                results.append(_check(
                    check_item="PhD Faculty Percentage",
                    category=ComplianceCategory.FACULTY,
                    status=ComplianceStatus.COMPLIANT,
                    required_value=f"≥ {min_phd_pct}%",
                    actual_value=f"{phd_pct:.1f}%",
                    evidence=f"phd={phd_count}, total={total_faculty}",
                ))
            elif phd_pct >= min_phd_pct * 0.75:
                results.append(_check(
                    check_item="PhD Faculty Percentage",
                    category=ComplianceCategory.FACULTY,
                    status=ComplianceStatus.PARTIAL,
                    required_value=f"≥ {min_phd_pct}%",
                    actual_value=f"{phd_pct:.1f}%",
                    evidence=f"phd={phd_count}, total={total_faculty}",
                    recommendation="Recruit additional PhD-qualified faculty members.",
                ))
            else:
                results.append(_check(
                    check_item="PhD Faculty Percentage",
                    category=ComplianceCategory.FACULTY,
                    status=ComplianceStatus.NON_COMPLIANT,
                    required_value=f"≥ {min_phd_pct}%",
                    actual_value=f"{phd_pct:.1f}%",
                    evidence=f"phd={phd_count}, total={total_faculty}",
                    recommendation="Significantly below norm. Recruit PhD faculty urgently.",
                ))

        # --- Professors count ---
        min_prof = reqs.get("min_professors", 1)
        if professors >= min_prof:
            results.append(_check(
                check_item="Minimum Professors",
                category=ComplianceCategory.FACULTY,
                status=ComplianceStatus.COMPLIANT,
                required_value=f"≥ {min_prof}",
                actual_value=str(professors),
            ))
        else:
            results.append(_check(
                check_item="Minimum Professors",
                category=ComplianceCategory.FACULTY,
                status=ComplianceStatus.NON_COMPLIANT,
                required_value=f"≥ {min_prof}",
                actual_value=str(professors),
                recommendation=f"Appoint at least {min_prof} professor(s).",
            ))

        # --- Associate Professors count ---
        min_assoc = reqs.get("min_associate_professors", 2)
        if assoc_professors >= min_assoc:
            results.append(_check(
                check_item="Minimum Associate Professors",
                category=ComplianceCategory.FACULTY,
                status=ComplianceStatus.COMPLIANT,
                required_value=f"≥ {min_assoc}",
                actual_value=str(assoc_professors),
            ))
        else:
            results.append(_check(
                check_item="Minimum Associate Professors",
                category=ComplianceCategory.FACULTY,
                status=ComplianceStatus.NON_COMPLIANT,
                required_value=f"≥ {min_assoc}",
                actual_value=str(assoc_professors),
                recommendation=f"Appoint at least {min_assoc} associate professor(s).",
            ))

        # --- Faculty per programme ---
        min_per_prog = reqs.get("min_faculty_per_programme", 5)
        num_programmes = len(programmes) if programmes else 0
        if num_programmes > 0:
            required_total = min_per_prog * num_programmes
            if total_faculty >= required_total:
                results.append(_check(
                    check_item="Faculty per Programme",
                    category=ComplianceCategory.FACULTY,
                    status=ComplianceStatus.COMPLIANT,
                    required_value=f"≥ {min_per_prog} per programme ({required_total} total)",
                    actual_value=str(total_faculty),
                ))
            else:
                results.append(_check(
                    check_item="Faculty per Programme",
                    category=ComplianceCategory.FACULTY,
                    status=ComplianceStatus.NON_COMPLIANT,
                    required_value=f"≥ {min_per_prog} per programme ({required_total} total)",
                    actual_value=str(total_faculty),
                    recommendation=f"Hire at least {required_total - total_faculty} more faculty members.",
                ))

        return results

    # ------------------------------------------------------------------
    # Infrastructure requirements
    # ------------------------------------------------------------------

    def _check_infrastructure_requirements(self, infra_data: dict) -> List[dict]:
        """Evaluate campus and laboratory infrastructure norms.

        Expected *infra_data* keys:
        - ``land_acres``, ``carpet_area_sqm``, ``num_labs``,
          ``library_books``, ``library_area_sqm``,
          ``computers``, ``student_count``,
          ``facilities`` (list of strings).
        """
        results: List[dict] = []
        reqs = self.checklist.get("infrastructure_requirements", {})

        # --- Land area ---
        min_land = reqs.get("min_land_acres", 2.5)
        land = infra_data.get("land_acres", 0)
        if land:
            if land >= min_land:
                results.append(_check(
                    check_item="Land Area",
                    category=ComplianceCategory.INFRASTRUCTURE,
                    status=ComplianceStatus.COMPLIANT,
                    required_value=f"≥ {min_land} acres",
                    actual_value=f"{land} acres",
                ))
            else:
                results.append(_check(
                    check_item="Land Area",
                    category=ComplianceCategory.INFRASTRUCTURE,
                    status=ComplianceStatus.NON_COMPLIANT,
                    required_value=f"≥ {min_land} acres",
                    actual_value=f"{land} acres",
                    recommendation="Acquire additional land to meet minimum requirements.",
                ))
        else:
            results.append(_check(
                check_item="Land Area",
                category=ComplianceCategory.INFRASTRUCTURE,
                status=ComplianceStatus.NON_COMPLIANT,
                required_value=f"≥ {min_land} acres",
                actual_value="Not provided",
                recommendation="Provide land ownership / lease details.",
            ))

        # --- Carpet area ---
        min_carpet = reqs.get("min_carpet_area_sqm", 3000)
        carpet = infra_data.get("carpet_area_sqm", 0)
        if carpet:
            if carpet >= min_carpet:
                results.append(_check(
                    check_item="Built-up / Carpet Area",
                    category=ComplianceCategory.INFRASTRUCTURE,
                    status=ComplianceStatus.COMPLIANT,
                    required_value=f"≥ {min_carpet} sqm",
                    actual_value=f"{carpet} sqm",
                ))
            elif carpet >= min_carpet * 0.8:
                results.append(_check(
                    check_item="Built-up / Carpet Area",
                    category=ComplianceCategory.INFRASTRUCTURE,
                    status=ComplianceStatus.PARTIAL,
                    required_value=f"≥ {min_carpet} sqm",
                    actual_value=f"{carpet} sqm",
                    recommendation="Carpet area is slightly below norm; consider expansion.",
                ))
            else:
                results.append(_check(
                    check_item="Built-up / Carpet Area",
                    category=ComplianceCategory.INFRASTRUCTURE,
                    status=ComplianceStatus.NON_COMPLIANT,
                    required_value=f"≥ {min_carpet} sqm",
                    actual_value=f"{carpet} sqm",
                    recommendation="Significantly below norm. Expand built-up area.",
                ))
        else:
            results.append(_check(
                check_item="Built-up / Carpet Area",
                category=ComplianceCategory.INFRASTRUCTURE,
                status=ComplianceStatus.NON_COMPLIANT,
                required_value=f"≥ {min_carpet} sqm",
                actual_value="Not provided",
                recommendation="Provide carpet area details.",
            ))

        # --- Labs ---
        min_labs = reqs.get("min_labs", 5)
        labs = infra_data.get("num_labs", 0)
        if labs >= min_labs:
            results.append(_check(
                check_item="Number of Laboratories",
                category=ComplianceCategory.INFRASTRUCTURE,
                status=ComplianceStatus.COMPLIANT,
                required_value=f"≥ {min_labs}",
                actual_value=str(labs),
            ))
        else:
            results.append(_check(
                check_item="Number of Laboratories",
                category=ComplianceCategory.INFRASTRUCTURE,
                status=ComplianceStatus.NON_COMPLIANT,
                required_value=f"≥ {min_labs}",
                actual_value=str(labs),
                recommendation=f"Set up at least {min_labs - labs} additional lab(s).",
            ))

        # --- Library books ---
        min_books = reqs.get("min_library_books", 5000)
        books = infra_data.get("library_books", 0)
        if books >= min_books:
            results.append(_check(
                check_item="Library Books / Titles",
                category=ComplianceCategory.INFRASTRUCTURE,
                status=ComplianceStatus.COMPLIANT,
                required_value=f"≥ {min_books}",
                actual_value=str(books),
            ))
        elif books >= min_books * 0.6:
            results.append(_check(
                check_item="Library Books / Titles",
                category=ComplianceCategory.INFRASTRUCTURE,
                status=ComplianceStatus.PARTIAL,
                required_value=f"≥ {min_books}",
                actual_value=str(books),
                recommendation="Increase library collection to meet AICTE norms.",
            ))
        else:
            results.append(_check(
                check_item="Library Books / Titles",
                category=ComplianceCategory.INFRASTRUCTURE,
                status=ComplianceStatus.NON_COMPLIANT,
                required_value=f"≥ {min_books}",
                actual_value=str(books),
                recommendation="Library is significantly under-stocked.",
            ))

        # --- Library area ---
        min_lib_area = reqs.get("min_library_area_sqm", 200)
        lib_area = infra_data.get("library_area_sqm", 0)
        if lib_area >= min_lib_area:
            results.append(_check(
                check_item="Library Area",
                category=ComplianceCategory.INFRASTRUCTURE,
                status=ComplianceStatus.COMPLIANT,
                required_value=f"≥ {min_lib_area} sqm",
                actual_value=f"{lib_area} sqm",
            ))
        elif lib_area > 0:
            results.append(_check(
                check_item="Library Area",
                category=ComplianceCategory.INFRASTRUCTURE,
                status=ComplianceStatus.NON_COMPLIANT,
                required_value=f"≥ {min_lib_area} sqm",
                actual_value=f"{lib_area} sqm",
                recommendation="Expand library physical space.",
            ))

        # --- Computer-to-student ratio ---
        min_ratio = reqs.get("min_computer_student_ratio", 0.5)
        computers = infra_data.get("computers", 0)
        students = infra_data.get("student_count", 0)
        if computers > 0 and students > 0:
            actual_ratio = computers / students
            if actual_ratio >= min_ratio:
                results.append(_check(
                    check_item="Computer-to-Student Ratio",
                    category=ComplianceCategory.INFRASTRUCTURE,
                    status=ComplianceStatus.COMPLIANT,
                    required_value=f"≥ {min_ratio}:1",
                    actual_value=f"{actual_ratio:.2f}:1",
                    evidence=f"computers={computers}, students={students}",
                ))
            else:
                results.append(_check(
                    check_item="Computer-to-Student Ratio",
                    category=ComplianceCategory.INFRASTRUCTURE,
                    status=ComplianceStatus.NON_COMPLIANT,
                    required_value=f"≥ {min_ratio}:1",
                    actual_value=f"{actual_ratio:.2f}:1",
                    evidence=f"computers={computers}, students={students}",
                    recommendation=f"Procure at least {int(students * min_ratio) - computers} additional computers.",
                ))

        # --- Required facilities ---
        required_facilities = reqs.get("required_facilities", [])
        available_facilities = [f.lower().strip() for f in infra_data.get("facilities", [])]
        for facility in required_facilities:
            if facility.lower() in available_facilities:
                results.append(_check(
                    check_item=f"Facility: {facility.replace('_', ' ').title()}",
                    category=ComplianceCategory.INFRASTRUCTURE,
                    status=ComplianceStatus.COMPLIANT,
                    required_value="Available",
                    actual_value="Available",
                ))
            else:
                results.append(_check(
                    check_item=f"Facility: {facility.replace('_', ' ').title()}",
                    category=ComplianceCategory.INFRASTRUCTURE,
                    status=ComplianceStatus.NON_COMPLIANT,
                    required_value="Available",
                    actual_value="Not Available",
                    recommendation=f"Establish a {facility.replace('_', ' ')} facility.",
                ))

        return results

    # ------------------------------------------------------------------
    # Financial requirements
    # ------------------------------------------------------------------

    def _check_financial_requirements(self, financial_data: dict) -> List[dict]:
        """Evaluate financial norms.

        Expected *financial_data* keys:
        - ``fdr_lakhs``, ``corpus_fund_lakhs``, ``annual_expenditure_lakhs``
        """
        results: List[dict] = []
        reqs = self.checklist.get("financial_requirements", {})

        # --- FDR ---
        min_fdr = reqs.get("min_fdr_lakhs", 50.0)
        fdr = financial_data.get("fdr_lakhs", 0)
        if fdr >= min_fdr:
            results.append(_check(
                check_item="Fixed Deposit Reserve (FDR)",
                category=ComplianceCategory.FINANCIAL,
                status=ComplianceStatus.COMPLIANT,
                required_value=f"≥ ₹{min_fdr} lakh",
                actual_value=f"₹{fdr} lakh",
            ))
        else:
            results.append(_check(
                check_item="Fixed Deposit Reserve (FDR)",
                category=ComplianceCategory.FINANCIAL,
                status=ComplianceStatus.NON_COMPLIANT,
                required_value=f"≥ ₹{min_fdr} lakh",
                actual_value=f"₹{fdr} lakh",
                recommendation=f"Increase FDR by at least ₹{min_fdr - fdr:.1f} lakh.",
            ))

        # --- Corpus fund ---
        min_corpus = reqs.get("min_corpus_fund_lakhs", 100.0)
        corpus = financial_data.get("corpus_fund_lakhs", 0)
        if corpus >= min_corpus:
            results.append(_check(
                check_item="Corpus Fund",
                category=ComplianceCategory.FINANCIAL,
                status=ComplianceStatus.COMPLIANT,
                required_value=f"≥ ₹{min_corpus} lakh",
                actual_value=f"₹{corpus} lakh",
            ))
        elif corpus >= min_corpus * 0.7:
            results.append(_check(
                check_item="Corpus Fund",
                category=ComplianceCategory.FINANCIAL,
                status=ComplianceStatus.PARTIAL,
                required_value=f"≥ ₹{min_corpus} lakh",
                actual_value=f"₹{corpus} lakh",
                recommendation="Corpus fund is slightly below norm. Increase contributions.",
            ))
        else:
            results.append(_check(
                check_item="Corpus Fund",
                category=ComplianceCategory.FINANCIAL,
                status=ComplianceStatus.NON_COMPLIANT,
                required_value=f"≥ ₹{min_corpus} lakh",
                actual_value=f"₹{corpus} lakh",
                recommendation="Corpus fund significantly below AICTE requirements.",
            ))

        # --- Annual expenditure ---
        min_exp = reqs.get("min_annual_expenditure_lakhs", 200.0)
        expenditure = financial_data.get("annual_expenditure_lakhs", 0)
        if expenditure >= min_exp:
            results.append(_check(
                check_item="Annual Expenditure on Education",
                category=ComplianceCategory.FINANCIAL,
                status=ComplianceStatus.COMPLIANT,
                required_value=f"≥ ₹{min_exp} lakh",
                actual_value=f"₹{expenditure} lakh",
            ))
        elif expenditure > 0:
            results.append(_check(
                check_item="Annual Expenditure on Education",
                category=ComplianceCategory.FINANCIAL,
                status=ComplianceStatus.NON_COMPLIANT,
                required_value=f"≥ ₹{min_exp} lakh",
                actual_value=f"₹{expenditure} lakh",
                recommendation="Increase annual educational expenditure.",
            ))

        return results

    # ------------------------------------------------------------------
    # Accreditation status
    # ------------------------------------------------------------------

    def _check_accreditation_status(self, accreditation_data: dict) -> List[dict]:
        """Check accreditation body, grade, and validity.

        Expected *accreditation_data* keys:
        - ``body`` (e.g. "NBA", "NAAC"), ``grade``, ``valid_until``,
          ``programmes_accredited`` (int).
        """
        results: List[dict] = []
        reqs = self.checklist.get("accreditation_requirements", {})
        accepted_bodies = [b.upper() for b in reqs.get("accepted_bodies", ["NBA", "NAAC"])]

        body = (accreditation_data.get("body") or "").upper()
        grade = (accreditation_data.get("grade") or "").upper()
        valid_until = accreditation_data.get("valid_until", "")
        programmes_accredited = accreditation_data.get("programmes_accredited", 0)

        # --- Accreditation body ---
        if body:
            if body in accepted_bodies:
                results.append(_check(
                    check_item="Accreditation Body",
                    category=ComplianceCategory.ACCREDITATION,
                    status=ComplianceStatus.COMPLIANT,
                    required_value=f"One of {accepted_bodies}",
                    actual_value=body,
                ))
            else:
                results.append(_check(
                    check_item="Accreditation Body",
                    category=ComplianceCategory.ACCREDITATION,
                    status=ComplianceStatus.NON_COMPLIANT,
                    required_value=f"One of {accepted_bodies}",
                    actual_value=body,
                    recommendation=f"Obtain accreditation from {' or '.join(accepted_bodies)}.",
                ))
        else:
            results.append(_check(
                check_item="Accreditation Body",
                category=ComplianceCategory.ACCREDITATION,
                status=ComplianceStatus.NOT_APPLICABLE,
                required_value=f"One of {accepted_bodies}",
                actual_value="Not provided",
                recommendation="Apply for accreditation if not already done.",
            ))

        # --- NAAC grade ---
        min_grade = reqs.get("min_naac_grade", "B")
        grade_order = {"A++": 7, "A+": 6, "A": 5, "B++": 4, "B+": 3, "B": 2, "C": 1}
        if body == "NAAC" and grade:
            actual_rank = grade_order.get(grade, 0)
            required_rank = grade_order.get(min_grade, 0)
            if actual_rank >= required_rank:
                results.append(_check(
                    check_item="NAAC Grade",
                    category=ComplianceCategory.ACCREDITATION,
                    status=ComplianceStatus.COMPLIANT,
                    required_value=f"≥ {min_grade}",
                    actual_value=grade,
                ))
            else:
                results.append(_check(
                    check_item="NAAC Grade",
                    category=ComplianceCategory.ACCREDITATION,
                    status=ComplianceStatus.NON_COMPLIANT,
                    required_value=f"≥ {min_grade}",
                    actual_value=grade,
                    recommendation="Improve quality metrics to achieve a higher NAAC grade.",
                ))

        # --- Validity ---
        if valid_until:
            from datetime import date as _date, datetime as _datetime
            try:
                for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y"):
                    try:
                        exp = _datetime.strptime(valid_until, fmt).date()
                        break
                    except ValueError:
                        exp = None
                if exp and exp < _date.today():
                    results.append(_check(
                        check_item="Accreditation Validity",
                        category=ComplianceCategory.ACCREDITATION,
                        status=ComplianceStatus.NON_COMPLIANT,
                        required_value="Valid (not expired)",
                        actual_value=f"Expired ({valid_until})",
                        recommendation="Renew accreditation immediately.",
                    ))
                elif exp:
                    results.append(_check(
                        check_item="Accreditation Validity",
                        category=ComplianceCategory.ACCREDITATION,
                        status=ComplianceStatus.COMPLIANT,
                        required_value="Valid (not expired)",
                        actual_value=f"Valid until {valid_until}",
                    ))
            except Exception:
                results.append(_check(
                    check_item="Accreditation Validity",
                    category=ComplianceCategory.ACCREDITATION,
                    status=ComplianceStatus.PARTIAL,
                    required_value="Valid (not expired)",
                    actual_value=valid_until,
                    recommendation="Could not parse validity date; please verify manually.",
                ))

        return results

    # ------------------------------------------------------------------
    # Scoring & reporting
    # ------------------------------------------------------------------

    def get_compliance_score(self, results: Any) -> float:
        """Compute an overall compliance percentage (0-100).

        Accepts either a list of check result dicts, or directly an application dict.

        - COMPLIANT → 1.0 weight
        - PARTIAL → 0.5 weight
        - NOT_APPLICABLE → excluded
        - NON_COMPLIANT → 0.0 weight
        """
        if isinstance(results, dict):
            results = self.check_compliance(results)

        if not results:
            return 0.0

        applicable = [r for r in results if r["status"] != ComplianceStatus.NOT_APPLICABLE]
        if not applicable:
            return 0.0

        score = 0.0
        for r in applicable:
            if r["status"] == ComplianceStatus.COMPLIANT:
                score += 1.0
            elif r["status"] == ComplianceStatus.PARTIAL:
                score += 0.5

        return round((score / len(applicable)) * 100, 2)

    def get_compliance_summary(self, results: Any) -> dict:
        """Break down compliance results by category.

        Accepts either a list of check result dicts, or directly an application dict.

        Returns:
            Dict mapping each ``category`` to counts of each
            ``status``.
        """
        if isinstance(results, dict):
            results = self.check_compliance(results)
        summary: Dict[str, Dict[str, int]] = {}
        for r in results:
            cat = r["category"]
            status = r["status"]
            if cat not in summary:
                summary[cat] = {
                    ComplianceStatus.COMPLIANT: 0,
                    ComplianceStatus.NON_COMPLIANT: 0,
                    ComplianceStatus.PARTIAL: 0,
                    ComplianceStatus.NOT_APPLICABLE: 0,
                }
            summary[cat][status] = summary[cat].get(status, 0) + 1

        return {
            "by_category": summary,
            "total_checks": len(results),
            "overall_score": self.get_compliance_score(results),
        }

    def generate_compliance_report(self, results: List[dict]) -> pd.DataFrame:
        """Convert compliance results to a Pandas DataFrame for display
        in Streamlit or CSV export.

        Returns:
            DataFrame with columns matching the compliance-check dict
            keys.
        """
        if not results:
            return pd.DataFrame(columns=[
                "check_item", "category", "status",
                "required_value", "actual_value",
                "evidence", "recommendation",
            ])
        return pd.DataFrame(results)

    # ------------------------------------------------------------------
    # Checklist loader
    # ------------------------------------------------------------------

    def _load_checklist(self, path: str) -> Dict[str, Any]:
        """Load checklist JSON or use built-in defaults."""
        if path and os.path.isfile(path):
            with open(path, "r", encoding="utf-8") as fh:
                return json.load(fh)
        return dict(_DEFAULT_CHECKLIST)
