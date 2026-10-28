"""
Application settings and constants for the AICTE Approval Validation Platform.

Centralizes all configuration values including file paths, thresholds,
document types, application categories, and status enumerations used
throughout the platform.
"""

import os
from typing import List


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
_PROJECT_ROOT: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

APP_TITLE: str = "AICTE Approval Validation Platform"
APP_ICON: str = "🏛️"
DATABASE_PATH: str = os.path.join(_PROJECT_ROOT, "data", "aicte_validation.db")
UPLOAD_DIR: str = os.path.join(_PROJECT_ROOT, "uploads")

# ---------------------------------------------------------------------------
# File handling
# ---------------------------------------------------------------------------
MAX_FILE_SIZE_MB: int = 50
SUPPORTED_EXTENSIONS: List[str] = [".pdf", ".jpg", ".jpeg", ".png"]

# ---------------------------------------------------------------------------
# OCR
# ---------------------------------------------------------------------------
OCR_LANGUAGE: str = "eng"
CONFIDENCE_THRESHOLD: float = 0.7


# ---------------------------------------------------------------------------
# Document types — namespace class + module-level constants
# ---------------------------------------------------------------------------
class DocumentTypes:
    """Constants for document types."""
    AFFIDAVIT: str = "AFFIDAVIT"
    NOC: str = "NOC"
    ACCREDITATION_CERT: str = "ACCREDITATION_CERT"
    FIRE_SAFETY_CERT: str = "FIRE_SAFETY_CERT"
    LAND_DOCUMENT: str = "LAND_DOCUMENT"
    BUILDING_PLAN: str = "BUILDING_PLAN"
    FACULTY_LIST: str = "FACULTY_LIST"
    FINANCIAL_STATEMENT: str = "FINANCIAL_STATEMENT"
    EOA_CERTIFICATE: str = "EOA_CERTIFICATE"
    UNDERTAKING: str = "UNDERTAKING"

# Also expose at module level for convenience
AFFIDAVIT = DocumentTypes.AFFIDAVIT
NOC = DocumentTypes.NOC
ACCREDITATION_CERT = DocumentTypes.ACCREDITATION_CERT
FIRE_SAFETY_CERT = DocumentTypes.FIRE_SAFETY_CERT
LAND_DOCUMENT = DocumentTypes.LAND_DOCUMENT
BUILDING_PLAN = DocumentTypes.BUILDING_PLAN
FACULTY_LIST = DocumentTypes.FACULTY_LIST
FINANCIAL_STATEMENT = DocumentTypes.FINANCIAL_STATEMENT
EOA_CERTIFICATE = DocumentTypes.EOA_CERTIFICATE
UNDERTAKING = DocumentTypes.UNDERTAKING

DOCUMENT_TYPES: List[str] = [
    AFFIDAVIT, NOC, ACCREDITATION_CERT, FIRE_SAFETY_CERT,
    LAND_DOCUMENT, BUILDING_PLAN, FACULTY_LIST, FINANCIAL_STATEMENT,
    EOA_CERTIFICATE, UNDERTAKING,
]

DOCUMENT_DISPLAY_NAMES: dict = {
    AFFIDAVIT: "Affidavit",
    NOC: "No Objection Certificate",
    ACCREDITATION_CERT: "Accreditation Certificate",
    FIRE_SAFETY_CERT: "Fire Safety Certificate",
    LAND_DOCUMENT: "Land Document",
    BUILDING_PLAN: "Building Plan Approval",
    FACULTY_LIST: "Faculty List",
    FINANCIAL_STATEMENT: "Financial Statement",
    EOA_CERTIFICATE: "Extension of Approval Certificate",
    UNDERTAKING: "Undertaking",
}


# ---------------------------------------------------------------------------
# Application categories
# ---------------------------------------------------------------------------
class ApplicationCategories:
    """Constants for application categories."""
    EOA: str = "EOA"
    NEW_INSTITUTION: str = "NEW_INSTITUTION"
    CHANGE_OF_SITE: str = "CHANGE_OF_SITE"
    CLOSURE: str = "CLOSURE"
    ADD_PROGRAMME: str = "ADD_PROGRAMME"

# Module-level aliases
EOA = ApplicationCategories.EOA
NEW_INSTITUTION = ApplicationCategories.NEW_INSTITUTION
CHANGE_OF_SITE = ApplicationCategories.CHANGE_OF_SITE
CLOSURE = ApplicationCategories.CLOSURE
ADD_PROGRAMME = ApplicationCategories.ADD_PROGRAMME

APPLICATION_CATEGORIES: List[str] = [
    EOA, NEW_INSTITUTION, CHANGE_OF_SITE, CLOSURE, ADD_PROGRAMME,
]

APPLICATION_CATEGORY_NAMES: dict = {
    EOA: "Extension of Approval",
    NEW_INSTITUTION: "New Institution",
    CHANGE_OF_SITE: "Change of Site / Location",
    CLOSURE: "Closure of Institution",
    ADD_PROGRAMME: "Addition of Programme / Course",
}


# ---------------------------------------------------------------------------
# Verification statuses
# ---------------------------------------------------------------------------
class VerificationStatuses:
    """Constants for verification statuses."""
    VERIFIED: str = "VERIFIED"
    MISMATCH_DETECTED: str = "MISMATCH_DETECTED"
    EXPIRED: str = "EXPIRED"
    VERIFICATION_PENDING: str = "VERIFICATION_PENDING"
    SOURCE_UNAVAILABLE: str = "SOURCE_UNAVAILABLE"
    MANUAL_REVIEW_REQUIRED: str = "MANUAL_REVIEW_REQUIRED"

VERIFIED = VerificationStatuses.VERIFIED
MISMATCH_DETECTED = VerificationStatuses.MISMATCH_DETECTED
VERIFICATION_PENDING = VerificationStatuses.VERIFICATION_PENDING
SOURCE_UNAVAILABLE = VerificationStatuses.SOURCE_UNAVAILABLE
MANUAL_REVIEW_REQUIRED = VerificationStatuses.MANUAL_REVIEW_REQUIRED

VERIFICATION_STATUSES: List[str] = [
    VERIFIED, MISMATCH_DETECTED, VerificationStatuses.EXPIRED,
    VERIFICATION_PENDING, SOURCE_UNAVAILABLE, MANUAL_REVIEW_REQUIRED,
]


# ---------------------------------------------------------------------------
# Validation statuses
# ---------------------------------------------------------------------------
class ValidationStatuses:
    """Constants for document validation statuses."""
    VALID: str = "VALID"
    INVALID: str = "INVALID"
    INCOMPLETE: str = "INCOMPLETE"
    EXPIRED: str = "EXPIRED"
    ANOMALY_DETECTED: str = "ANOMALY_DETECTED"
    PENDING_REVIEW: str = "PENDING_REVIEW"

VALID = ValidationStatuses.VALID
INVALID = ValidationStatuses.INVALID
INCOMPLETE = ValidationStatuses.INCOMPLETE
ANOMALY_DETECTED = ValidationStatuses.ANOMALY_DETECTED
PENDING_REVIEW = ValidationStatuses.PENDING_REVIEW

VALIDATION_STATUSES: List[str] = [
    VALID, INVALID, INCOMPLETE, ValidationStatuses.EXPIRED,
    ANOMALY_DETECTED, PENDING_REVIEW,
]


# ---------------------------------------------------------------------------
# Severity levels
# ---------------------------------------------------------------------------
SEVERITY_LOW: str = "LOW"
SEVERITY_MEDIUM: str = "MEDIUM"
SEVERITY_HIGH: str = "HIGH"
SEVERITY_CRITICAL: str = "CRITICAL"

SEVERITY_LEVELS: List[str] = [SEVERITY_LOW, SEVERITY_MEDIUM, SEVERITY_HIGH, SEVERITY_CRITICAL]


# ---------------------------------------------------------------------------
# User roles
# ---------------------------------------------------------------------------
ROLE_ADMIN: str = "ADMIN"
ROLE_REVIEWER: str = "REVIEWER"
ROLE_VIEWER: str = "VIEWER"

USER_ROLES: List[str] = [ROLE_ADMIN, ROLE_REVIEWER, ROLE_VIEWER]
