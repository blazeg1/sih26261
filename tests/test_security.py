"""
Unit tests for Security, Magic-Byte Validation, and Bcrypt Password Hashing (utils/security.py).
"""

import pytest
from utils.security import validate_file_security, hash_password_bcrypt, verify_password


def test_magic_byte_validation_pdf():
    valid_pdf = b"%PDF-1.7\n1 0 obj\n<<>>\nendobj\n"
    ok, msg = validate_file_security(valid_pdf, "test.pdf")
    assert ok is True

    # Renamed exe pretending to be pdf
    fake_pdf = b"MZ\x90\x00\x03\x00\x00\x00\x04\x00"
    ok, msg = validate_file_security(fake_pdf, "fake.pdf")
    assert ok is False
    assert "Spoofed" in msg


def test_magic_byte_validation_png():
    valid_png = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR"
    ok, msg = validate_file_security(valid_png, "test.png")
    assert ok is True


def test_bcrypt_password_hashing():
    pw = "AdminSecurePass2026!"
    hashed = hash_password_bcrypt(pw)
    assert hashed.startswith("$2b$")
    assert verify_password(pw, hashed) is True
    assert verify_password("WrongPassword", hashed) is False


def test_legacy_sha256_backward_compatibility():
    import hashlib
    pw = "admin123"
    legacy_hash = hashlib.sha256(pw.encode()).hexdigest()
    assert verify_password(pw, legacy_hash) is True
    assert verify_password("wrong", legacy_hash) is False
