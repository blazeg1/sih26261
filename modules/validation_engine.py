"""
Validation Engine for the AICTE Application Validation Platform.

Provides Pydantic v2 models for structured data validation and a
rule-based ValidationEngine that checks required documents, field
consistency, date logic, and more.
"""

from __future__ import annotations

import json
import os
import re
from datetime import date, datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------

class ValidationStatus(str, Enum):
    """Possible outcomes of a single validation rule."""

    PASS = "PASS"
    FAIL = "FAIL"
    WARNING = "WARNING"


class DocumentCategory(str, Enum):
    """Standard AICTE document categories."""

    AFFILIATION = "AFFILIATION"
    ACCREDITATION = "ACCREDITATION"
    FIRE_SAFETY = "FIRE_SAFETY"
    LAND_DOCUMENT = "LAND_DOCUMENT"
    BUILDING_PLAN = "BUILDING_PLAN"
    FINANCIAL = "FINANCIAL"
    FACULTY_LIST = "FACULTY_LIST"
    NOC = "NOC"
    OTHER = "OTHER"


# ---------------------------------------------------------------------------
# Pydantic Models
# ---------------------------------------------------------------------------

class InstitutionData(BaseModel):
    """Core identifying information for an institution."""

    name: str = Field(..., min_length=3, max_length=256)
    aicte_id: str = Field(..., min_length=4, max_length=20)
    university: str = Field(..., min_length=3)
    state: str = Field(..., min_length=2)
    city: str = Field(..., min_length=2)
    address: str = Field(..., min_length=5)
    established_year: int = Field(..., ge=1900, le=2100)
    contact_email: str = Field(...)
    contact_phone: str = Field(...)

    @field_validator("contact_email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        """Ensure the contact e-mail looks reasonable."""
        pattern = r"^[\w\.\+\-]+@[\w\-]+\.[a-zA-Z]{2,}$"
        if not re.match(pattern, v):
            raise ValueError(f"Invalid email format: {v}")
        return v.lower().strip()

    @field_validator("contact_phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        """Allow digits, spaces, dashes, plus — 7-15 characters after cleanup."""
        digits = re.sub(r"[^\d]", "", v)
        if len(digits) < 7 or len(digits) > 15:
            raise ValueError(f"Phone number must have 7-15 digits, got {len(digits)}")
        return v.strip()

    @field_validator("aicte_id")
    @classmethod
    def validate_aicte_id(cls, v: str) -> str:
        """AICTE ID should be alphanumeric with optional hyphens."""
        cleaned = v.strip().upper()
        if not re.match(r"^[A-Z0-9\-]+$", cleaned):
            raise ValueError(f"AICTE ID must be alphanumeric (with hyphens): {v}")
        return cleaned


class ProgrammeData(BaseModel):
    """A single academic programme offered by the institution."""

    programme_name: str
    level: str = Field(..., description="UG / PG / Diploma / PhD")
    intake: int = Field(..., ge=0)
    duration_years: int = Field(..., ge=1, le=7)


class ApplicationData(BaseModel):
    """Complete application submitted by an institution."""

    institution: InstitutionData
    category: str = Field(..., description="NEW / EXTENSION / CLOSURE / VARIATION")
    academic_year: str = Field(..., pattern=r"^\d{4}-\d{2,4}$")
    programmes: List[ProgrammeData] = Field(default_factory=list)
    faculty_count: int = Field(..., ge=0)
    student_count: int = Field(..., ge=0)

    @field_validator("category")
    @classmethod
    def validate_category(cls, v: str) -> str:
        allowed = {"NEW", "EXTENSION", "CLOSURE", "VARIATION"}
        upper = v.strip().upper()
        if upper not in allowed:
            raise ValueError(f"category must be one of {allowed}")
        return upper


class DocumentData(BaseModel):
    """Metadata extracted from a single uploaded document."""

    doc_type: str
    filename: str
    issue_date: Optional[str] = None
    expiry_date: Optional[str] = None
    issuing_authority: Optional[str] = None
    reference_number: Optional[str] = None
    extracted_text: Optional[str] = None


class ValidationResult(BaseModel):
    """Result of a single validation rule execution."""

    rule_name: str
    category: str
    status: ValidationStatus
    message: str
    evidence: Optional[str] = None
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)


# ---------------------------------------------------------------------------
# Default Checklist (embedded for demo / fallback)
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
    "required_fields": [
        "institution.name",
        "institution.aicte_id",
        "institution.university",
        "institution.state",
        "institution.city",
        "institution.address",
        "institution.established_year",
        "institution.contact_email",
        "institution.contact_phone",
        "category",
        "academic_year",
        "faculty_count",
        "student_count",
    ],
    "field_validation_rules": {
        "faculty_student_ratio_max": 30,
        "min_faculty_count": 5,
        "min_programmes": 1,
    },
}


# ---------------------------------------------------------------------------
# Validation Engine
# ---------------------------------------------------------------------------

class ValidationEngine:
    """Rule-based validation engine for AICTE applications and documents.

    Loads a checklist (JSON) of required documents and fields and runs
    deterministic validation rules over the submitted data.

    Args:
        checklist_path: Path to a JSON file containing the checklist.
                        If the file does not exist the built-in defaults
                        are used.
    """

    def __init__(self, checklist_path: str = "") -> None:
        self.checklist: Dict[str, Any] = self._load_checklist(checklist_path)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def validate_application(self, application: dict) -> List[ValidationResult]:
        """Run all validation rules on a full application payload.

        The *application* dict is expected to contain:
        - ``institution``: dict matching :class:`InstitutionData`
        - ``category``, ``academic_year``, ``faculty_count``, ``student_count``
        - ``programmes``: list of dicts matching :class:`ProgrammeData`
        - ``documents``: list of dicts matching :class:`DocumentData`

        Returns:
            A list of :class:`ValidationResult` objects.
        """
        results: List[ValidationResult] = []

        # 1. Required fields
        results.extend(self._check_required_fields(application))

        # 2. Pydantic structural validation
        results.extend(self._pydantic_validate(application))

        # 3. Documents
        documents = application.get("documents")
        if documents is None:
            documents = application.get("documents_submitted", [])
        results.extend(self._check_required_documents(documents))
        if isinstance(documents, list) and documents and isinstance(documents[0], dict):
            results.extend(self._check_document_expiry(documents))
            results.extend(self._check_date_logic(documents))

        # 4. Cross-checks
        results.extend(self._check_field_consistency(application, documents))

        # 5. Faculty-student ratio
        results.extend(self._check_faculty_student_ratio(application))

        # 6. Programme count
        results.extend(self._check_programme_count(application))

        return results

    def validate_document(self, document: dict, doc_type: str = "") -> List[ValidationResult]:
        """Validate a single document's metadata.

        Args:
            document: Dict with keys matching :class:`DocumentData`.
            doc_type: Expected document type, e.g. ``"AFFILIATION"``.

        Returns:
            A list of :class:`ValidationResult` objects.
        """
        results: List[ValidationResult] = []

        if not doc_type:
            doc_type = document.get("doc_type") or document.get("document_type") or ""

        # Type check
        actual_type = (document.get("doc_type") or document.get("document_type") or "").upper()
        if doc_type and actual_type != doc_type.upper():
            results.append(ValidationResult(
                rule_name="document_type_match",
                category="DOCUMENT",
                status=ValidationStatus.FAIL,
                message=f"Expected doc_type '{doc_type}', got '{actual_type}'",
                evidence=f"submitted doc_type={actual_type}",
                confidence=1.0,
            ))
        else:
            results.append(ValidationResult(
                rule_name="document_type_match",
                category="DOCUMENT",
                status=ValidationStatus.PASS,
                message=f"Document type matches expected type '{doc_type or actual_type}'",
                confidence=1.0,
            ))

        # Filename
        filename = document.get("filename", "")
        if not filename:
            results.append(ValidationResult(
                rule_name="document_filename_present",
                category="DOCUMENT",
                status=ValidationStatus.FAIL,
                message="Document filename is missing",
                confidence=1.0,
            ))
        else:
            ext = Path(filename).suffix.lower()
            allowed = {".pdf", ".jpg", ".jpeg", ".png", ".tiff", ".tif"}
            if ext not in allowed:
                results.append(ValidationResult(
                    rule_name="document_file_format",
                    category="DOCUMENT",
                    status=ValidationStatus.WARNING,
                    message=f"Unusual file extension '{ext}'; expected one of {allowed}",
                    evidence=f"filename={filename}",
                    confidence=0.8,
                ))
            else:
                results.append(ValidationResult(
                    rule_name="document_file_format",
                    category="DOCUMENT",
                    status=ValidationStatus.PASS,
                    message=f"File format '{ext}' is acceptable",
                    confidence=1.0,
                ))

        # Reference number
        ref = document.get("reference_number", "")
        if not ref:
            results.append(ValidationResult(
                rule_name="document_reference_number",
                category="DOCUMENT",
                status=ValidationStatus.WARNING,
                message="Document has no reference number — may hinder verification",
                confidence=0.7,
            ))

        # Issuing authority
        authority = document.get("issuing_authority", "")
        if not authority:
            results.append(ValidationResult(
                rule_name="document_issuing_authority",
                category="DOCUMENT",
                status=ValidationStatus.WARNING,
                message="Issuing authority not specified",
                confidence=0.7,
            ))

        # Date checks (single document)
        results.extend(self._check_date_logic([document]))

        return results

    def get_validation_summary(self, results: List[ValidationResult]) -> dict:
        """Produce a summary of validation results.

        Returns:
            Dict with ``total``, ``pass_count``, ``fail_count``,
            ``warning_count``, ``overall_score`` (0-100), and
            ``by_category``.
        """
        total = len(results)
        pass_count = sum(1 for r in results if r.status == ValidationStatus.PASS)
        fail_count = sum(1 for r in results if r.status == ValidationStatus.FAIL)
        warning_count = sum(1 for r in results if r.status == ValidationStatus.WARNING)

        score = (pass_count / total * 100) if total > 0 else 0.0

        by_category: Dict[str, Dict[str, int]] = {}
        for r in results:
            cat = r.category
            if cat not in by_category:
                by_category[cat] = {"PASS": 0, "FAIL": 0, "WARNING": 0}
            by_category[cat][r.status.value] += 1

        return {
            "total": total,
            "pass_count": pass_count,
            "fail_count": fail_count,
            "warning_count": warning_count,
            "overall_score": round(score, 2),
            "by_category": by_category,
        }

    # ------------------------------------------------------------------
    # Internal rule implementations
    # ------------------------------------------------------------------

    def _check_required_documents(self, documents: List[Any]) -> List[ValidationResult]:
        """Ensure every required document type is present."""
        results: List[ValidationResult] = []
        submitted_types = set()
        for d in documents:
            if isinstance(d, str):
                submitted_types.add(d.upper())
            elif isinstance(d, dict):
                t = (d.get("doc_type") or d.get("document_type") or "").upper()
                if t:
                    submitted_types.add(t)
                    # Also strip _test or extensions if present
                    base_t = t.replace(".PDF", "").replace("_TEST", "").replace("-", "_")
                    submitted_types.add(base_t)
        for req in self.checklist.get("required_documents", []):
            dtype = req["doc_type"].upper()
            label = req.get("label", dtype)
            if dtype in submitted_types:
                results.append(ValidationResult(
                    rule_name="required_document_present",
                    category="DOCUMENT",
                    status=ValidationStatus.PASS,
                    message=f"Required document '{label}' is present",
                    evidence=f"doc_type={dtype}",
                    confidence=1.0,
                ))
            else:
                results.append(ValidationResult(
                    rule_name="required_document_present",
                    category="DOCUMENT",
                    status=ValidationStatus.FAIL,
                    message=f"Required document '{label}' is MISSING",
                    evidence=f"Expected doc_type={dtype}",
                    confidence=1.0,
                ))
        return results

    def _check_required_fields(self, data: dict) -> List[ValidationResult]:
        """Verify that all required fields are non-empty in the application."""
        results: List[ValidationResult] = []
        for field_path in self.checklist.get("required_fields", []):
            parts = field_path.split(".")
            value: Any = data
            found = True
            for part in parts:
                if isinstance(value, dict):
                    value = value.get(part)
                    if value is None:
                        found = False
                        break
                else:
                    found = False
                    break

            # Fallback to flat keys if not found via nested path
            if not found or value in (None, "", [], {}):
                flat_candidates = [
                    field_path.replace(".", "_"),
                    parts[-1],
                ]
                if field_path == "faculty_count":
                    flat_candidates.extend(["total_faculty", "faculty"])
                elif field_path == "student_count":
                    flat_candidates.extend(["total_intake", "students", "student_intake"])

                for cand in flat_candidates:
                    if cand in data and data[cand] not in (None, "", [], {}):
                        value = data[cand]
                        found = True
                        break

            if found and value not in (None, "", [], {}):
                results.append(ValidationResult(
                    rule_name="required_field_present",
                    category="FIELD",
                    status=ValidationStatus.PASS,
                    message=f"Required field '{field_path}' is present",
                    evidence=f"{field_path}={_truncate(value)}",
                    confidence=1.0,
                ))
            else:
                results.append(ValidationResult(
                    rule_name="required_field_present",
                    category="FIELD",
                    status=ValidationStatus.FAIL,
                    message=f"Required field '{field_path}' is missing or empty",
                    evidence=f"{field_path}=<empty>",
                    confidence=1.0,
                ))
        return results

    def _check_document_expiry(self, documents: List[dict]) -> List[ValidationResult]:
        """Flag documents whose expiry date is in the past."""
        results: List[ValidationResult] = []
        today = date.today()
        for doc in documents:
            expiry_str = doc.get("expiry_date")
            if not expiry_str:
                continue
            expiry = _parse_date(expiry_str)
            if expiry is None:
                results.append(ValidationResult(
                    rule_name="document_expiry_parseable",
                    category="DOCUMENT",
                    status=ValidationStatus.WARNING,
                    message=f"Cannot parse expiry date '{expiry_str}' for {doc.get('doc_type', 'UNKNOWN')}",
                    evidence=f"expiry_date={expiry_str}",
                    confidence=0.6,
                ))
                continue
            if expiry < today:
                results.append(ValidationResult(
                    rule_name="document_not_expired",
                    category="DOCUMENT",
                    status=ValidationStatus.FAIL,
                    message=f"Document '{doc.get('doc_type', 'UNKNOWN')}' expired on {expiry.isoformat()}",
                    evidence=f"expiry_date={expiry.isoformat()}, today={today.isoformat()}",
                    confidence=1.0,
                ))
            else:
                days_remaining = (expiry - today).days
                if days_remaining < 90:
                    results.append(ValidationResult(
                        rule_name="document_not_expired",
                        category="DOCUMENT",
                        status=ValidationStatus.WARNING,
                        message=f"Document '{doc.get('doc_type', 'UNKNOWN')}' expires in {days_remaining} days",
                        evidence=f"expiry_date={expiry.isoformat()}, days_left={days_remaining}",
                        confidence=0.9,
                    ))
                else:
                    results.append(ValidationResult(
                        rule_name="document_not_expired",
                        category="DOCUMENT",
                        status=ValidationStatus.PASS,
                        message=f"Document '{doc.get('doc_type', 'UNKNOWN')}' is valid until {expiry.isoformat()}",
                        evidence=f"days_remaining={days_remaining}",
                        confidence=1.0,
                    ))
        return results

    def _check_field_consistency(
        self,
        application: dict,
        documents: List[dict],
    ) -> List[ValidationResult]:
        """Cross-check institution name and AICTE ID across documents' extracted text."""
        results: List[ValidationResult] = []
        institution = application.get("institution", {})
        inst_name = institution.get("name", "").upper().strip()
        aicte_id = institution.get("aicte_id", "").upper().strip()

        if not inst_name and not aicte_id:
            return results

        for doc in documents:
            text = (doc.get("extracted_text") or "").upper()
            doc_type = doc.get("doc_type", "UNKNOWN")
            if not text:
                results.append(ValidationResult(
                    rule_name="cross_check_institution_name",
                    category="CONSISTENCY",
                    status=ValidationStatus.WARNING,
                    message=f"No extracted text available for '{doc_type}' — cannot cross-check",
                    confidence=0.5,
                ))
                continue

            # Name check
            if inst_name:
                if inst_name in text:
                    results.append(ValidationResult(
                        rule_name="cross_check_institution_name",
                        category="CONSISTENCY",
                        status=ValidationStatus.PASS,
                        message=f"Institution name found in '{doc_type}' document",
                        evidence=f"name='{inst_name}' found in extracted text",
                        confidence=0.95,
                    ))
                else:
                    # Partial / fuzzy match attempt
                    from rapidfuzz import fuzz as _fuzz
                    best_ratio = 0.0
                    # Slide a window of the name's length across the text
                    name_len = len(inst_name)
                    for i in range(max(1, len(text) - name_len + 1)):
                        segment = text[i: i + name_len]
                        ratio = _fuzz.ratio(inst_name, segment)
                        if ratio > best_ratio:
                            best_ratio = ratio
                    if best_ratio >= 80:
                        results.append(ValidationResult(
                            rule_name="cross_check_institution_name",
                            category="CONSISTENCY",
                            status=ValidationStatus.WARNING,
                            message=f"Institution name partially matches in '{doc_type}' (score={best_ratio:.1f}%)",
                            evidence=f"fuzzy_score={best_ratio:.1f}",
                            confidence=best_ratio / 100,
                        ))
                    else:
                        results.append(ValidationResult(
                            rule_name="cross_check_institution_name",
                            category="CONSISTENCY",
                            status=ValidationStatus.FAIL,
                            message=f"Institution name NOT found in '{doc_type}' document",
                            evidence=f"best_fuzzy_score={best_ratio:.1f}",
                            confidence=0.85,
                        ))

            # AICTE ID check
            if aicte_id:
                if aicte_id in text:
                    results.append(ValidationResult(
                        rule_name="cross_check_aicte_id",
                        category="CONSISTENCY",
                        status=ValidationStatus.PASS,
                        message=f"AICTE ID '{aicte_id}' found in '{doc_type}' document",
                        confidence=0.95,
                    ))
                else:
                    results.append(ValidationResult(
                        rule_name="cross_check_aicte_id",
                        category="CONSISTENCY",
                        status=ValidationStatus.WARNING,
                        message=f"AICTE ID '{aicte_id}' not found in '{doc_type}' document",
                        evidence="AICTE ID may not be present in every document",
                        confidence=0.7,
                    ))

        return results

    def _check_date_logic(self, documents: List[dict]) -> List[ValidationResult]:
        """Validate date sanity: issue < expiry, no future issue dates, etc."""
        results: List[ValidationResult] = []
        today = date.today()

        for doc in documents:
            doc_type = doc.get("doc_type", "UNKNOWN")
            issue_str = doc.get("issue_date")
            expiry_str = doc.get("expiry_date")

            issue_date = _parse_date(issue_str) if issue_str else None
            expiry_date = _parse_date(expiry_str) if expiry_str else None

            if issue_date and expiry_date:
                if issue_date >= expiry_date:
                    results.append(ValidationResult(
                        rule_name="date_issue_before_expiry",
                        category="DATE",
                        status=ValidationStatus.FAIL,
                        message=f"Issue date ({issue_date}) is not before expiry date ({expiry_date}) in '{doc_type}'",
                        evidence=f"issue={issue_date}, expiry={expiry_date}",
                        confidence=1.0,
                    ))
                else:
                    results.append(ValidationResult(
                        rule_name="date_issue_before_expiry",
                        category="DATE",
                        status=ValidationStatus.PASS,
                        message=f"Date ordering correct for '{doc_type}'",
                        confidence=1.0,
                    ))

            if issue_date and issue_date > today:
                results.append(ValidationResult(
                    rule_name="date_not_future",
                    category="DATE",
                    status=ValidationStatus.FAIL,
                    message=f"Issue date ({issue_date}) is in the future for '{doc_type}'",
                    evidence=f"issue_date={issue_date}, today={today}",
                    confidence=1.0,
                ))

            # Very old dates (before 1947) are suspicious
            if issue_date and issue_date.year < 1947:
                results.append(ValidationResult(
                    rule_name="date_reasonable_range",
                    category="DATE",
                    status=ValidationStatus.WARNING,
                    message=f"Issue date ({issue_date}) is unusually old for '{doc_type}'",
                    evidence=f"issue_date.year={issue_date.year}",
                    confidence=0.8,
                ))

        return results

    # ------------------------------------------------------------------
    # Additional helpers
    # ------------------------------------------------------------------

    def _pydantic_validate(self, application: dict) -> List[ValidationResult]:
        """Attempt to parse the application through Pydantic models."""
        results: List[ValidationResult] = []
        try:
            ApplicationData(**{k: v for k, v in application.items() if k != "documents"})
            results.append(ValidationResult(
                rule_name="pydantic_schema_valid",
                category="SCHEMA",
                status=ValidationStatus.PASS,
                message="Application data conforms to the expected schema",
                confidence=1.0,
            ))
        except Exception as exc:
            results.append(ValidationResult(
                rule_name="pydantic_schema_valid",
                category="SCHEMA",
                status=ValidationStatus.FAIL,
                message=f"Schema validation failed: {exc}",
                evidence=str(exc)[:300],
                confidence=1.0,
            ))
        return results

    def _check_faculty_student_ratio(self, application: dict) -> List[ValidationResult]:
        """Check that the faculty-to-student ratio is within limits."""
        results: List[ValidationResult] = []
        faculty = application.get("faculty_count", 0)
        students = application.get("student_count", 0)
        max_ratio = self.checklist.get("field_validation_rules", {}).get(
            "faculty_student_ratio_max", 30
        )

        if faculty <= 0:
            results.append(ValidationResult(
                rule_name="faculty_count_positive",
                category="FIELD",
                status=ValidationStatus.FAIL,
                message="Faculty count must be greater than zero",
                evidence=f"faculty_count={faculty}",
                confidence=1.0,
            ))
            return results

        ratio = students / faculty
        if ratio > max_ratio:
            results.append(ValidationResult(
                rule_name="faculty_student_ratio",
                category="FIELD",
                status=ValidationStatus.FAIL,
                message=f"Student-to-faculty ratio ({ratio:.1f}:1) exceeds maximum ({max_ratio}:1)",
                evidence=f"students={students}, faculty={faculty}",
                confidence=0.95,
            ))
        else:
            results.append(ValidationResult(
                rule_name="faculty_student_ratio",
                category="FIELD",
                status=ValidationStatus.PASS,
                message=f"Student-to-faculty ratio ({ratio:.1f}:1) is within limits",
                evidence=f"students={students}, faculty={faculty}",
                confidence=1.0,
            ))
        return results

    def _check_programme_count(self, application: dict) -> List[ValidationResult]:
        """Ensure minimum number of programmes is declared."""
        results: List[ValidationResult] = []
        programmes = application.get("programmes", [])
        min_prog = self.checklist.get("field_validation_rules", {}).get("min_programmes", 1)
        if len(programmes) < min_prog:
            results.append(ValidationResult(
                rule_name="minimum_programmes",
                category="FIELD",
                status=ValidationStatus.FAIL,
                message=f"At least {min_prog} programme(s) required; found {len(programmes)}",
                evidence=f"programmes_count={len(programmes)}",
                confidence=1.0,
            ))
        else:
            results.append(ValidationResult(
                rule_name="minimum_programmes",
                category="FIELD",
                status=ValidationStatus.PASS,
                message=f"{len(programmes)} programme(s) declared",
                confidence=1.0,
            ))
        return results

    # ------------------------------------------------------------------
    # Checklist loader
    # ------------------------------------------------------------------

    def _load_checklist(self, path: str) -> Dict[str, Any]:
        """Load checklist from JSON or fall back to built-in defaults."""
        if path and os.path.isfile(path):
            with open(path, "r", encoding="utf-8") as fh:
                return json.load(fh)
        return dict(_DEFAULT_CHECKLIST)


# ---------------------------------------------------------------------------
# Module-level helpers
# ---------------------------------------------------------------------------

def _parse_date(value: str) -> Optional[date]:
    """Best-effort date parser supporting multiple common formats."""
    for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%Y/%m/%d", "%d %b %Y", "%d %B %Y"):
        try:
            return datetime.strptime(value.strip(), fmt).date()
        except (ValueError, AttributeError):
            continue
    return None


def _truncate(value: Any, max_len: int = 80) -> str:
    """Return a truncated string representation."""
    s = str(value)
    return s if len(s) <= max_len else s[:max_len] + "…"
