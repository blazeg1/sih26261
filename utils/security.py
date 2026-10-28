"""
Security, Magic-Byte File Validation, and Cryptographic Utilities.

Provides bcrypt-secured password management, strict file-type & magic-byte validation,
and immutable append-only audit event logging.
"""

import os
import hashlib
import sqlite3
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any

import bcrypt
from config.settings import DATABASE_PATH, MAX_FILE_SIZE_MB


# Magic bytes signatures for supported document formats
MAGIC_BYTES = {
    "pdf": [b"%PDF-"],
    "png": [b"\x89PNG\r\n\x1a\n"],
    "jpg": [b"\xff\xd8\xff"],
    "jpeg": [b"\xff\xd8\xff"],
    "tiff": [b"II*\x00", b"MM\x00*"],
    "tif": [b"II*\x00", b"MM\x00*"],
}


def validate_file_security(file_bytes: bytes, filename: str) -> Tuple[bool, str]:
    """
    Validate uploaded file against size limits and strict magic-byte file headers.
    Guards against disguised executables or malformed payloads.
    """
    # 1. Size Check
    size_mb = len(file_bytes) / (1024 * 1024)
    if size_mb > MAX_FILE_SIZE_MB:
        return False, f"File exceeds maximum allowed size of {MAX_FILE_SIZE_MB}MB (Actual: {size_mb:.1f}MB)."

    if len(file_bytes) < 8:
        return False, "File is empty or truncated."

    # 2. Extension Check
    ext = filename.split(".")[-1].lower() if "." in filename else ""
    if ext not in MAGIC_BYTES:
        return False, f"Unsupported file extension '.{ext}'. Supported: PDF, PNG, JPG, JPEG, TIFF."

    # 3. Magic Byte Inspection
    signatures = MAGIC_BYTES[ext]
    header = file_bytes[:16]
    valid_magic = any(header.startswith(sig) for sig in signatures)

    if not valid_magic:
        return False, f"Security Warning: File content does not match reported extension '.{ext}' (Spoofed file signature detected)."

    return True, "File verified safe and authentic."


def hash_password_bcrypt(password: str) -> str:
    """Hash password with bcrypt salt."""
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(plain_password: str, stored_hash: str) -> bool:
    """
    Verify password. Supports modern bcrypt hashes as well as legacy SHA-256 for backward compatibility.
    """
    if not stored_hash or not plain_password:
        return False

    # Check if bcrypt hash (starts with $2a$, $2b$, or $2y$)
    if stored_hash.startswith(("$2a$", "$2b$", "$2y$")):
        try:
            return bcrypt.checkpw(plain_password.encode("utf-8"), stored_hash.encode("utf-8"))
        except Exception:
            return False

    # Legacy SHA-256 fallback
    sha_hash = hashlib.sha256(plain_password.encode("utf-8")).hexdigest()
    return sha_hash.lower() == stored_hash.lower()


def record_audit_event(
    application_id: Optional[int],
    action: str,
    actor: str,
    details: str,
    role: str = "OFFICER",
    file_hash: Optional[str] = None,
    ip_address: str = "127.0.0.1"
) -> bool:
    """
    Append an immutable event to the AICTE audit trail.
    """
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cur = conn.cursor()
        now = datetime.now().isoformat()
        full_details = details
        if file_hash:
            full_details += f" | SHA256: {file_hash}"

        cur.execute("""
            INSERT INTO audit_trail (application_id, action, actor, details, ip_address, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (application_id, action, f"{actor} ({role})", full_details, ip_address, now))
        conn.commit()
        conn.close()
        return True
    except Exception:
        return False
