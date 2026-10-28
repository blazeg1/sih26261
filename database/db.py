"""
Database manager for the AICTE Validation Platform.

Provides SQLite-based storage for institutions, applications, documents,
validation results, anomaly alerts, compliance checks, and audit trails.
Uses integer auto-increment primary keys throughout.
"""

import os
import sqlite3
from contextlib import contextmanager
from typing import Generator

from config.settings import DATABASE_PATH


class DatabaseManager:
    """Central database manager using SQLite with integer auto-increment IDs."""

    def __init__(self, db_path: str = DATABASE_PATH) -> None:
        """
        Initialize with an optional custom DB path.

        Args:
            db_path: Path to the SQLite database file.
        """
        self.db_path = str(db_path)
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

    @contextmanager
    def get_connection(self) -> Generator[sqlite3.Connection, None, None]:
        """Yield a sqlite3 connection with row_factory set to Row."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA foreign_keys=ON;")
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def init_db(self) -> None:
        """Create all tables if they do not exist."""
        with self.get_connection() as conn:
            conn.executescript(_SCHEMA_SQL)


# ────────────────────────────────────────────────────────────────────── #
# Schema SQL — integer IDs, consistent column names
# ────────────────────────────────────────────────────────────────────── #
_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    full_name TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'VIEWER',
    department TEXT DEFAULT '',
    is_active INTEGER DEFAULT 1,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS institutions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    aicte_id TEXT UNIQUE,
    university TEXT DEFAULT '',
    state TEXT DEFAULT '',
    city TEXT DEFAULT '',
    address TEXT DEFAULT '',
    established_year INTEGER,
    status TEXT DEFAULT 'ACTIVE',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS applications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    institution_id INTEGER NOT NULL,
    category TEXT NOT NULL,
    academic_year TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'SUBMITTED',
    submitted_at TEXT,
    reviewed_by TEXT,
    review_notes TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (institution_id) REFERENCES institutions(id)
);

CREATE TABLE IF NOT EXISTS documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    application_id INTEGER NOT NULL,
    doc_type TEXT NOT NULL,
    filename TEXT NOT NULL,
    file_path TEXT DEFAULT '',
    file_hash TEXT DEFAULT '',
    upload_date TEXT,
    expiry_date TEXT,
    ocr_text TEXT DEFAULT '',
    extracted_data TEXT DEFAULT '{}',
    validation_status TEXT DEFAULT 'PENDING_REVIEW',
    anomaly_score REAL DEFAULT 0.0,
    notes TEXT DEFAULT '',
    FOREIGN KEY (application_id) REFERENCES applications(id)
);

CREATE TABLE IF NOT EXISTS validation_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER,
    application_id INTEGER,
    rule_name TEXT NOT NULL,
    rule_category TEXT DEFAULT '',
    status TEXT NOT NULL,
    details TEXT DEFAULT '',
    evidence TEXT DEFAULT '',
    confidence_score REAL DEFAULT 0.0,
    created_at TEXT NOT NULL,
    FOREIGN KEY (document_id) REFERENCES documents(id),
    FOREIGN KEY (application_id) REFERENCES applications(id)
);

CREATE TABLE IF NOT EXISTS anomaly_alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER,
    application_id INTEGER,
    alert_type TEXT NOT NULL,
    severity TEXT NOT NULL DEFAULT 'LOW',
    description TEXT DEFAULT '',
    evidence TEXT DEFAULT '',
    is_resolved INTEGER DEFAULT 0,
    resolved_by TEXT,
    resolved_at TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY (document_id) REFERENCES documents(id),
    FOREIGN KEY (application_id) REFERENCES applications(id)
);

CREATE TABLE IF NOT EXISTS verification_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER NOT NULL,
    source_name TEXT NOT NULL,
    source_type TEXT DEFAULT '',
    verification_status TEXT NOT NULL DEFAULT 'PENDING',
    submitted_data TEXT DEFAULT '{}',
    source_response TEXT DEFAULT '{}',
    verified_at TEXT,
    notes TEXT DEFAULT '',
    FOREIGN KEY (document_id) REFERENCES documents(id)
);

CREATE TABLE IF NOT EXISTS compliance_checks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    application_id INTEGER NOT NULL,
    checklist_name TEXT DEFAULT '',
    check_item TEXT NOT NULL,
    category TEXT NOT NULL,
    status TEXT NOT NULL,
    required_value TEXT DEFAULT '',
    actual_value TEXT DEFAULT '',
    evidence TEXT DEFAULT '',
    notes TEXT DEFAULT '',
    checked_at TEXT NOT NULL,
    FOREIGN KEY (application_id) REFERENCES applications(id)
);

CREATE TABLE IF NOT EXISTS audit_trail (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    application_id INTEGER,
    action TEXT NOT NULL,
    actor TEXT NOT NULL,
    details TEXT DEFAULT '',
    ip_address TEXT DEFAULT '',
    timestamp TEXT NOT NULL,
    FOREIGN KEY (application_id) REFERENCES applications(id)
);
"""
