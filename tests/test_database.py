"""
Tests for DatabaseManager module.

Validates schema initialization, connection management, and basic queries.
"""

import os
import sys
import sqlite3
import pytest

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from database.db import DatabaseManager


class TestDatabaseManager:
    """Test suite for DatabaseManager."""

    @pytest.fixture
    def test_db(self, tmp_path):
        db_file = str(tmp_path / "test_aicte.db")
        mgr = DatabaseManager(db_file)
        mgr.init_db()
        return mgr, db_file

    def test_init_db_creates_tables(self, test_db):
        mgr, db_file = test_db
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [r[0] for r in cursor.fetchall()]
        conn.close()

        expected = [
            "users", "institutions", "applications", "documents",
            "validation_results", "anomaly_alerts", "verification_records",
            "compliance_checks", "audit_trail"
        ]
        for t in expected:
            assert t in tables, f"Expected table {t} in database"

    def test_insert_and_retrieve_institution(self, test_db):
        mgr, db_file = test_db
        with mgr.get_connection() as conn:
            conn.execute(
                "INSERT INTO institutions (name, aicte_id, state, city, created_at, updated_at) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                ("Test Institute of Tech", "1-9999999", "Delhi", "New Delhi", "2026-01-01", "2026-01-01")
            )

        with mgr.get_connection() as conn:
            row = conn.execute("SELECT * FROM institutions WHERE aicte_id = ?", ("1-9999999",)).fetchone()
            assert row is not None
            assert row["name"] == "Test Institute of Tech"

    def test_audit_trail_logging(self, test_db):
        mgr, db_file = test_db
        with mgr.get_connection() as conn:
            conn.execute(
                "INSERT INTO audit_trail (action, actor, details, timestamp) "
                "VALUES (?, ?, ?, ?)",
                ("TEST_ACTION", "test_user", "Unit test action", "2026-01-01T12:00:00")
            )

        with mgr.get_connection() as conn:
            count = conn.execute("SELECT COUNT(*) FROM audit_trail WHERE action = 'TEST_ACTION'").fetchone()[0]
            assert count == 1
