"""
Verification Service for the AICTE Application Validation Platform.

Simulates external verification lookups (NBA/NAAC, Fire Dept, Land
Registry, University portals, internal AICTE database) for MVP/demo
purposes.  Returns realistic mixed results — verified, mismatch,
pending, and source-unavailable — to exercise the full UI.
"""

from __future__ import annotations

import hashlib
import os
import random
import sqlite3
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from config.settings import VerificationStatuses


# ---------------------------------------------------------------------------
# Verification-result factory
# ---------------------------------------------------------------------------

def _result(
    source_name: str,
    source_type: str,
    verification_status: str,
    submitted_data: dict,
    source_response: dict,
    notes: str = "",
) -> dict:
    """Build a standardised verification result dict."""
    return {
        "source_name": source_name,
        "source_type": source_type,
        "verification_status": verification_status,
        "submitted_data": submitted_data,
        "source_response": source_response,
        "verified_at": datetime.now().isoformat(),
        "notes": notes,
    }


# ---------------------------------------------------------------------------
# VerificationService
# ---------------------------------------------------------------------------

class VerificationService:
    """Simulated external-verification gateway for the AICTE platform.

    For each document type the service routes to an appropriate
    *_verify_** method that mimics an external API call with realistic
    latency and mixed outcomes.

    Args:
        db_path: Path to the SQLite database used for internal AICTE
            record lookups.  Created automatically with seed data if it
            does not exist.
    """

    _DOC_TYPE_ROUTER: Dict[str, str] = {
        "ACCREDITATION": "_verify_accreditation",
        "FIRE_SAFETY": "_verify_fire_safety",
        "LAND_DOCUMENT": "_verify_land_records",
        "AFFILIATION": "_verify_university_affiliation",
        "NOC": "_verify_aicte_records",
        "FINANCIAL": "_verify_aicte_records",
        "FACULTY_LIST": "_verify_aicte_records",
        "BUILDING_PLAN": "_verify_aicte_records",
    }

    def __init__(self, db_path: str = "") -> None:
        self._db_path = db_path or os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "..", "data", "aicte_records.db"
        )
        self._ensure_db()
        # Seed the RNG with a document-specific hash so results are
        # reproducible within the same run but vary across documents.
        self._rng = random.Random(42)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def verify_document(self, doc_type: str, doc_data: dict) -> dict:
        """Route to the appropriate verification method.

        Args:
            doc_type: Document type string (e.g. ``"ACCREDITATION"``).
            doc_data: Document metadata dict.

        Returns:
            A verification result dict.
        """
        method_name = self._DOC_TYPE_ROUTER.get(doc_type.upper(), "_verify_aicte_records")
        method = getattr(self, method_name)
        return method(doc_data)

    def get_verification_status(self, doc_id: int) -> str:
        """Look up the latest verification status for a document ID.

        Args:
            doc_id: Numeric document identifier.

        Returns:
            Status string — one of ``VERIFIED``, ``MISMATCH``,
            ``PENDING``, ``SOURCE_UNAVAILABLE``, ``NOT_FOUND``.
        """
        conn = sqlite3.connect(self._db_path)
        cur = conn.cursor()
        cur.execute(
            "SELECT status FROM verification_log WHERE doc_id = ? ORDER BY verified_at DESC LIMIT 1",
            (doc_id,),
        )
        row = cur.fetchone()
        conn.close()
        return row[0] if row else "NOT_FOUND"

    def batch_verify(self, documents: List[dict]) -> List[dict]:
        """Verify a list of documents sequentially.

        Args:
            documents: Each dict must contain ``doc_type`` and any
                additional keys expected by the specific verifier.

        Returns:
            A list of verification result dicts.
        """
        results: List[dict] = []
        for doc in documents:
            doc_type = doc.get("doc_type", "OTHER")
            result = self.verify_document(doc_type, doc)
            results.append(result)
        return results

    # ------------------------------------------------------------------
    # Accreditation verification (NBA / NAAC)
    # ------------------------------------------------------------------

    def _verify_accreditation(self, data: dict) -> dict:
        """Simulate NBA / NAAC accreditation portal lookup."""
        body = (data.get("accreditation_body") or data.get("issuing_authority") or "NBA").upper()
        ref = data.get("reference_number", "")
        inst_name = data.get("institution_name", data.get("name", ""))

        api_result = self._simulate_api_call(f"{body} Portal", data)

        if api_result["status"] == "success":
            # Build a realistic source response
            grade = self._rng.choice(["A++", "A+", "A", "B++", "B+", "B"])
            valid_until = (datetime.utcnow() + timedelta(days=self._rng.randint(180, 1800))).strftime("%Y-%m-%d")
            source_resp = {
                "institution_name": inst_name,
                "accreditation_body": body,
                "grade": grade,
                "certificate_number": ref or f"{body}-{self._rng.randint(10000, 99999)}",
                "valid_from": (datetime.utcnow() - timedelta(days=self._rng.randint(365, 1825))).strftime("%Y-%m-%d"),
                "valid_until": valid_until,
                "programmes_accredited": self._rng.randint(1, 8),
            }
            # Introduce occasional mismatches for demo
            if self._rng.random() < 0.25:
                source_resp["institution_name"] = inst_name + " (Autonomous)"
                return _result(
                    source_name=f"{body} Accreditation Portal",
                    source_type="PORTAL",
                    verification_status=VerificationStatuses.MISMATCH_DETECTED,
                    submitted_data=data,
                    source_response=source_resp,
                    notes=f"Institution name mismatch in {body} records.",
                )
            return _result(
                source_name=f"{body} Accreditation Portal",
                source_type="PORTAL",
                verification_status="VERIFIED",
                submitted_data=data,
                source_response=source_resp,
                notes=f"Successfully verified against {body} portal.",
            )
        elif api_result["status"] == "pending":
            return _result(
                source_name=f"{body} Accreditation Portal",
                source_type="PORTAL",
                verification_status="PENDING",
                submitted_data=data,
                source_response={"message": "Verification request queued."},
                notes="Response pending from accreditation portal.",
            )
        else:
            return _result(
                source_name=f"{body} Accreditation Portal",
                source_type="PORTAL",
                verification_status="SOURCE_UNAVAILABLE",
                submitted_data=data,
                source_response={"error": api_result.get("error", "Portal unreachable")},
                notes="Could not reach accreditation portal; retry later.",
            )

    # ------------------------------------------------------------------
    # Fire safety verification
    # ------------------------------------------------------------------

    def _verify_fire_safety(self, data: dict) -> dict:
        """Simulate fire department certificate verification."""
        ref = data.get("reference_number", "")
        api_result = self._simulate_api_call("State Fire Department", data)

        if api_result["status"] == "success":
            valid_until = (datetime.utcnow() + timedelta(days=self._rng.randint(30, 730))).strftime("%Y-%m-%d")
            source_resp = {
                "certificate_number": ref or f"FS-{self._rng.randint(1000, 9999)}-{self._rng.randint(2023, 2026)}",
                "status": "VALID",
                "issued_to": data.get("institution_name", ""),
                "valid_until": valid_until,
                "inspected_by": f"Chief Fire Officer, {data.get('city', 'Unknown')}",
            }
            if self._rng.random() < 0.15:
                source_resp["status"] = "EXPIRED"
                return _result(
                    source_name="State Fire Department",
                    source_type="API",
                    verification_status=VerificationStatuses.MISMATCH_DETECTED,
                    submitted_data=data,
                    source_response=source_resp,
                    notes="Fire safety certificate marked as EXPIRED in department records.",
                )
            return _result(
                source_name="State Fire Department",
                source_type="API",
                verification_status="VERIFIED",
                submitted_data=data,
                source_response=source_resp,
                notes="Fire safety certificate verified successfully.",
            )
        else:
            return _result(
                source_name="State Fire Department",
                source_type="API",
                verification_status="SOURCE_UNAVAILABLE",
                submitted_data=data,
                source_response={"error": "Fire department API not responding."},
                notes="Unable to reach fire department verification service.",
            )

    # ------------------------------------------------------------------
    # Land records verification
    # ------------------------------------------------------------------

    def _verify_land_records(self, data: dict) -> dict:
        """Simulate land-registry / revenue department check."""
        api_result = self._simulate_api_call("Land Revenue Department", data)

        if api_result["status"] == "success":
            survey_no = data.get("survey_number", f"SUR/{self._rng.randint(100, 9999)}")
            area_acres = data.get("land_acres", round(self._rng.uniform(1.5, 10), 2))
            source_resp = {
                "survey_number": survey_no,
                "registered_owner": data.get("trust_name", data.get("institution_name", "")),
                "area_acres": area_acres,
                "encumbrance": self._rng.choice(["Clear", "Clear", "Clear", "Mortgage registered"]),
                "district": data.get("city", ""),
                "state": data.get("state", ""),
            }
            if source_resp["encumbrance"] != "Clear":
                return _result(
                    source_name="Land Revenue Department",
                    source_type="DATABASE",
                    verification_status=VerificationStatuses.MISMATCH_DETECTED,
                    submitted_data=data,
                    source_response=source_resp,
                    notes="Land has an encumbrance (mortgage) registered against it.",
                )
            return _result(
                source_name="Land Revenue Department",
                source_type="DATABASE",
                verification_status="VERIFIED",
                submitted_data=data,
                source_response=source_resp,
                notes="Land records verified — title is clear.",
            )
        elif api_result["status"] == "pending":
            return _result(
                source_name="Land Revenue Department",
                source_type="DATABASE",
                verification_status="PENDING",
                submitted_data=data,
                source_response={"message": "Manual verification in progress."},
                notes="Land records require manual verification by revenue officer.",
            )
        else:
            return _result(
                source_name="Land Revenue Department",
                source_type="DATABASE",
                verification_status="SOURCE_UNAVAILABLE",
                submitted_data=data,
                source_response={"error": "Revenue department portal offline."},
                notes="Revenue department portal unavailable.",
            )

    # ------------------------------------------------------------------
    # University affiliation verification
    # ------------------------------------------------------------------

    def _verify_university_affiliation(self, data: dict) -> dict:
        """Simulate university portal affiliation verification."""
        university = data.get("university", data.get("issuing_authority", ""))
        api_result = self._simulate_api_call(f"{university} Portal", data)

        if api_result["status"] == "success":
            source_resp = {
                "university_name": university,
                "affiliated_institution": data.get("institution_name", ""),
                "affiliation_number": data.get("reference_number", f"AFF-{self._rng.randint(1000, 9999)}"),
                "programmes_affiliated": self._rng.randint(2, 10),
                "valid_until": (datetime.utcnow() + timedelta(days=self._rng.randint(180, 1095))).strftime("%Y-%m-%d"),
                "affiliation_type": self._rng.choice(["Permanent", "Temporary", "Autonomous"]),
            }
            if self._rng.random() < 0.20:
                source_resp["affiliated_institution"] = data.get("institution_name", "") + " — Different Campus"
                return _result(
                    source_name=f"{university} Affiliation Portal",
                    source_type="PORTAL",
                    verification_status=VerificationStatuses.MISMATCH_DETECTED,
                    submitted_data=data,
                    source_response=source_resp,
                    notes="Institution name does not exactly match university records.",
                )
            return _result(
                source_name=f"{university} Affiliation Portal",
                source_type="PORTAL",
                verification_status="VERIFIED",
                submitted_data=data,
                source_response=source_resp,
                notes="University affiliation verified successfully.",
            )
        else:
            return _result(
                source_name=f"{university} Affiliation Portal",
                source_type="PORTAL",
                verification_status="SOURCE_UNAVAILABLE",
                submitted_data=data,
                source_response={"error": "University portal did not respond."},
                notes="Could not reach university affiliation portal.",
            )

    # ------------------------------------------------------------------
    # Internal AICTE database verification
    # ------------------------------------------------------------------

    def _verify_aicte_records(self, data: dict) -> dict:
        """Check data against the internal AICTE SQLite database."""
        aicte_id = data.get("aicte_id", "")
        inst_name = data.get("institution_name", data.get("name", ""))

        conn = sqlite3.connect(self._db_path)
        cur = conn.cursor()
        cur.execute(
            "SELECT name, state, city, established_year, status FROM institutions WHERE aicte_id = ?",
            (aicte_id,),
        )
        row = cur.fetchone()
        conn.close()

        if row:
            db_name, db_state, db_city, db_year, db_status = row
            source_resp = {
                "aicte_id": aicte_id,
                "name": db_name,
                "state": db_state,
                "city": db_city,
                "established_year": db_year,
                "status": db_status,
            }
            # Check for mismatches
            mismatches: List[str] = []
            if inst_name and inst_name.upper() != db_name.upper():
                mismatches.append(f"name: submitted='{inst_name}', db='{db_name}'")
            submitted_state = data.get("state", "")
            if submitted_state and submitted_state.upper() != db_state.upper():
                mismatches.append(f"state: submitted='{submitted_state}', db='{db_state}'")

            if mismatches:
                return _result(
                    source_name="AICTE Internal Database",
                    source_type="DATABASE",
                    verification_status=VerificationStatuses.MISMATCH_DETECTED,
                    submitted_data=data,
                    source_response=source_resp,
                    notes=f"Mismatches found: {'; '.join(mismatches)}",
                )
            return _result(
                source_name="AICTE Internal Database",
                source_type="DATABASE",
                verification_status="VERIFIED",
                submitted_data=data,
                source_response=source_resp,
                notes="Record matches AICTE internal database.",
            )
        else:
            return _result(
                source_name="AICTE Internal Database",
                source_type="DATABASE",
                verification_status=VerificationStatuses.MISMATCH_DETECTED,
                submitted_data=data,
                source_response={"aicte_id": aicte_id, "found": False},
                notes=f"AICTE ID '{aicte_id}' not found in internal database.",
            )

    # ------------------------------------------------------------------
    # Simulated API call
    # ------------------------------------------------------------------

    def _simulate_api_call(self, source: str, data: dict) -> dict:
        """Simulate an external API call with realistic latency and
        occasional failures.

        Returns:
            Dict with ``status`` (``success`` / ``pending`` / ``error``)
            and optionally ``error`` message.
        """
        # Deterministic seed per source+data so repeated calls give same result
        seed = hashlib.md5(f"{source}:{sorted(data.items())}".encode()).hexdigest()
        local_rng = random.Random(seed)

        # Simulate network latency (50-500ms)
        latency = local_rng.uniform(0.05, 0.5)
        time.sleep(min(latency, 0.1))  # Cap real delay for demo

        # Outcome distribution: 70% success, 15% pending, 15% error
        roll = local_rng.random()
        if roll < 0.70:
            return {"status": "success"}
        elif roll < 0.85:
            return {"status": "pending"}
        else:
            return {
                "status": "error",
                "error": local_rng.choice([
                    "Connection timed out",
                    "HTTP 503 Service Unavailable",
                    "SSL certificate verification failed",
                    "Rate limit exceeded",
                ]),
            }

    # ------------------------------------------------------------------
    # Database setup
    # ------------------------------------------------------------------

    def _ensure_db(self) -> None:
        """Create the SQLite database and seed it with sample data if it
        does not already exist."""
        db_dir = os.path.dirname(self._db_path)
        if db_dir and not os.path.isdir(db_dir):
            os.makedirs(db_dir, exist_ok=True)

        conn = sqlite3.connect(self._db_path)
        cur = conn.cursor()

        # Institutions table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS institutions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                aicte_id TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                university TEXT,
                state TEXT,
                city TEXT,
                established_year INTEGER,
                status TEXT DEFAULT 'ACTIVE'
            )
        """)

        # Verification log table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS verification_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                doc_id INTEGER,
                doc_type TEXT,
                source_name TEXT,
                status TEXT,
                verified_at TEXT,
                notes TEXT
            )
        """)

        # Seed data (only if empty)
        cur.execute("SELECT COUNT(*) FROM institutions")
        if cur.fetchone()[0] == 0:
            seed_data = [
                ("AICTE-1-4725381", "National Institute of Technology Trichy", "Anna University", "Tamil Nadu", "Tiruchirappalli", 1964, "ACTIVE"),
                ("AICTE-1-3945672", "Indian Institute of Technology Bombay", "IIT Bombay (Deemed)", "Maharashtra", "Mumbai", 1958, "ACTIVE"),
                ("AICTE-2-8301456", "Birla Institute of Technology Mesra", "BIT Mesra (Deemed)", "Jharkhand", "Ranchi", 1955, "ACTIVE"),
                ("AICTE-1-9087234", "PSG College of Technology", "Anna University", "Tamil Nadu", "Coimbatore", 1951, "ACTIVE"),
                ("AICTE-3-5612789", "Vellore Institute of Technology", "VIT (Deemed)", "Tamil Nadu", "Vellore", 1984, "ACTIVE"),
                ("AICTE-2-1124578", "Delhi Technological University", "Delhi University", "Delhi", "New Delhi", 1941, "ACTIVE"),
                ("AICTE-4-6789012", "RV College of Engineering", "Visvesvaraya Technological University", "Karnataka", "Bengaluru", 1963, "ACTIVE"),
                ("AICTE-1-2345678", "Jadavpur University", "Jadavpur University", "West Bengal", "Kolkata", 1955, "ACTIVE"),
                ("AICTE-5-9876543", "Manipal Institute of Technology", "Manipal Academy of Higher Education", "Karnataka", "Manipal", 1957, "ACTIVE"),
                ("AICTE-3-1122334", "SRM Institute of Science and Technology", "SRM IST (Deemed)", "Tamil Nadu", "Chennai", 1985, "ACTIVE"),
                ("AICTE-WB-001", "Bengal Engineering College", "West Bengal University of Technology", "West Bengal", "Howrah", 1856, "ACTIVE"),
                ("AICTE-MH-002", "College of Engineering Pune", "Savitribai Phule Pune University", "Maharashtra", "Pune", 1854, "ACTIVE"),
                ("AICTE-KA-003", "BMS College of Engineering", "Visvesvaraya Technological University", "Karnataka", "Bengaluru", 1946, "ACTIVE"),
                ("AICTE-TN-004", "Thiagarajar College of Engineering", "Anna University", "Tamil Nadu", "Madurai", 1957, "ACTIVE"),
                ("AICTE-UP-005", "Motilal Nehru National Institute of Technology", "MNNIT (Deemed)", "Uttar Pradesh", "Allahabad", 1961, "ACTIVE"),
            ]
            cur.executemany(
                "INSERT INTO institutions (aicte_id, name, university, state, city, established_year, status) VALUES (?, ?, ?, ?, ?, ?, ?)",
                seed_data,
            )

        conn.commit()
        conn.close()
