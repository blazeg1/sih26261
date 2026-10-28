"""
Utility helper functions for the AICTE Approval Validation Platform.

Provides common operations such as file hashing, date parsing, formatting,
and status-to-visual-indicator mappings used across the application.
"""

import hashlib
import os
import re
import unicodedata
from datetime import datetime
from typing import Optional


def compute_file_hash(file_path: str) -> str:
    """Compute the SHA-256 hash of a file.

    Args:
        file_path: Absolute or relative path to the file.

    Returns:
        Hex-encoded SHA-256 digest string.

    Raises:
        FileNotFoundError: If *file_path* does not exist.
    """
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as fh:
        for chunk in iter(lambda: fh.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def format_file_size(size_bytes: int) -> str:
    """Return a human-friendly file-size string.

    Args:
        size_bytes: File size in bytes.

    Returns:
        Formatted string such as ``"1.23 MB"`` or ``"456 KB"``.
    """
    if size_bytes < 0:
        return "0 B"
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if abs(size_bytes) < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0  # type: ignore[assignment]
    return f"{size_bytes:.2f} PB"


def safe_filename(filename: str) -> str:
    """Sanitize a filename by removing or replacing unsafe characters.

    Args:
        filename: Original filename string.

    Returns:
        A filesystem-safe filename string.
    """
    # Normalize unicode
    filename = unicodedata.normalize("NFKD", filename)
    # Keep only alphanumerics, hyphens, underscores, dots
    filename = re.sub(r"[^\w.\-]", "_", filename)
    # Collapse consecutive underscores
    filename = re.sub(r"_+", "_", filename)
    # Strip leading/trailing underscores and dots
    filename = filename.strip("_.")
    return filename if filename else "unnamed_file"


def get_timestamp() -> str:
    """Return the current UTC timestamp in ISO-8601 format.

    Returns:
        Timestamp string, e.g. ``"2025-06-15T14:30:00"``.
    """
    return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S")


def parse_date(date_string: str) -> Optional[datetime]:
    """Attempt to parse a date string using several common formats.

    Args:
        date_string: A date string to parse.

    Returns:
        A :class:`datetime` object on success, or ``None`` if parsing fails.
    """
    formats = [
        "%Y-%m-%d",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
        "%d-%m-%Y",
        "%d/%m/%Y",
        "%m/%d/%Y",
        "%d %b %Y",
        "%d %B %Y",
        "%Y%m%d",
    ]
    for fmt in formats:
        try:
            return datetime.strptime(date_string.strip(), fmt)
        except (ValueError, AttributeError):
            continue
    return None


def is_expired(expiry_date: str) -> bool:
    """Check whether a date string represents a date in the past.

    Args:
        expiry_date: Date string in any format accepted by :func:`parse_date`.

    Returns:
        ``True`` if the date is in the past, ``False`` otherwise or if parsing fails.
    """
    parsed = parse_date(expiry_date)
    if parsed is None:
        return False
    return parsed < datetime.utcnow()


def severity_color(severity: str) -> str:
    """Map a severity label to a hex colour code.

    Args:
        severity: One of ``LOW``, ``MEDIUM``, ``HIGH``, ``CRITICAL``.

    Returns:
        Hex colour string (e.g. ``"#e74c3c"``).
    """
    mapping = {
        "LOW": "#2ecc71",
        "MEDIUM": "#f39c12",
        "HIGH": "#e67e22",
        "CRITICAL": "#e74c3c",
    }
    return mapping.get(severity.upper(), "#95a5a6")


def status_icon(status: str) -> str:
    """Return an emoji icon corresponding to a validation / verification status.

    Args:
        status: Status string such as ``VALID``, ``INVALID``, ``EXPIRED``, etc.

    Returns:
        An emoji character.
    """
    mapping = {
        "VALID": "✅",
        "VERIFIED": "✅",
        "INVALID": "❌",
        "MISMATCH_DETECTED": "⚠️",
        "INCOMPLETE": "📝",
        "EXPIRED": "⏰",
        "ANOMALY_DETECTED": "🔍",
        "PENDING_REVIEW": "🕐",
        "VERIFICATION_PENDING": "🕐",
        "SOURCE_UNAVAILABLE": "🔗",
        "MANUAL_REVIEW_REQUIRED": "👁️",
        "APPROVED": "✅",
        "REJECTED": "❌",
        "UNDER_REVIEW": "🔄",
        "SUBMITTED": "📤",
        "DRAFT": "📋",
    }
    return mapping.get(status.upper(), "❓")


def truncate_text(text: str, max_length: int = 100) -> str:
    """Truncate text to a maximum length, appending an ellipsis if needed.

    Args:
        text: The input string.
        max_length: Maximum number of characters to keep.

    Returns:
        The (possibly truncated) string.
    """
    if len(text) <= max_length:
        return text
    return text[: max_length - 3].rstrip() + "..."


def ensure_dir(path: str) -> None:
    """Create a directory (and parents) if it does not already exist.

    Args:
        path: Directory path to create.
    """
    os.makedirs(path, exist_ok=True)
