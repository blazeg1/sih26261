"""
Cross-Application Intelligence Module.

Detects cross-institutional document reuse, perceptual image near-duplicates,
privacy-preserving dual-institution faculty collisions, and Year-over-Year (YoY)
institutional variance (shrunk built-up area, high faculty turnover, altered survey nos).
"""

import os
import hashlib
from typing import Dict, List, Optional, Any, Tuple
import cv2
import numpy as np
from PIL import Image


def compute_dhash(image_input: Any, hash_size: int = 8) -> str:
    """
    Compute 64-bit difference hash (dHash) for perceptual image similarity.
    Works on PIL Image, file path, or numpy array.
    """
    if isinstance(image_input, str):
        if not os.path.exists(image_input):
            return "0000000000000000"
        img = Image.open(image_input).convert("L")
    elif isinstance(image_input, Image.Image):
        img = image_input.convert("L")
    elif isinstance(image_input, np.ndarray):
        img = Image.fromarray(image_input).convert("L")
    else:
        return "0000000000000000"

    # Resize to (width = hash_size + 1, height = hash_size)
    resized = img.resize((hash_size + 1, hash_size), Image.Resampling.LANCZOS)
    pixels = np.array(resized)

    # Compare adjacent pixels
    diff = pixels[:, 1:] > pixels[:, :-1]
    # Flatten to integer
    decimal_value = 0
    hex_string = []
    for index, value in enumerate(diff.flatten()):
        if value:
            decimal_value += 2 ** (index % 8)
        if (index % 8) == 7:
            hex_string.append(hex(decimal_value)[2:].rjust(2, "0"))
            decimal_value = 0

    return "".join(hex_string)


def hamming_distance(hash1: str, hash2: str) -> int:
    """Calculate the Hamming distance between two hex hash strings."""
    if len(hash1) != len(hash2):
        return 64
    x = int(hash1, 16) ^ int(hash2, 16)
    return bin(x).count("1")


def hash_faculty_id(raw_identifier: str, salt: str = "AICTE_SALT_2026") -> str:
    """
    Privacy-preserving faculty identifier hash.
    Stores salted SHA-256 digest with only the last 4 characters unmasked.
    Example: 'SALTED_HASH...4920'
    """
    cleaned = str(raw_identifier).strip().replace(" ", "").upper()
    if not cleaned:
        return "ANONYMOUS"
    h = hashlib.sha256((salt + cleaned).encode("utf-8")).hexdigest()
    last4 = cleaned[-4:] if len(cleaned) >= 4 else cleaned
    return f"{h[:16]}...{last4}"


class CrossApplicationIntelligence:
    """
    Analyzes systemic cross-institutional datasets to detect recycled submissions,
    ghost faculty appointments, and unexpected YoY structural reductions.
    """

    def __init__(self, salt: str = "AICTE_SALT_2026"):
        self.salt = salt

    def detect_byte_duplicates(self, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Detect exact byte-identical documents (same SHA-256) uploaded across different institutions.
        """
        hash_map: Dict[str, List[Dict[str, Any]]] = {}
        for d in documents:
            sha = d.get("file_hash", "")
            if sha:
                if sha not in hash_map:
                    hash_map[sha] = []
                hash_map[sha].append(d)

        findings = []
        for sha, doc_list in hash_map.items():
            # Check distinct institutions
            inst_ids = set(d.get("institution_id") for d in doc_list)
            if len(inst_ids) > 1:
                colleges = list(set(d.get("institution_name", f"Inst #{d.get('institution_id')}") for d in doc_list))
                findings.append({
                    "type": "Cross-Institution Byte-Identical File",
                    "status": "Possible anomaly - needs human verification",
                    "severity": "CRITICAL",
                    "file_hash": sha,
                    "reused_across": colleges,
                    "affected_files": [d.get("filename") for d in doc_list],
                    "message": f"Exact byte-identical document (SHA-256: {sha[:12]}...) shared between distinct institutions: {', '.join(colleges)}."
                })
        return findings

    def detect_perceptual_near_duplicates(self, image_records: List[Dict[str, Any]], max_hamming: int = 8) -> List[Dict[str, Any]]:
        """
        Detect near-duplicate visual certificates or floor plans across different colleges.
        """
        findings = []
        n = len(image_records)

        for i in range(n):
            for j in range(i + 1, n):
                rec1 = image_records[i]
                rec2 = image_records[j]
                if rec1.get("institution_id") != rec2.get("institution_id"):
                    h1 = rec1.get("dhash", "")
                    h2 = rec2.get("dhash", "")
                    if h1 and h2:
                        dist = hamming_distance(h1, h2)
                        if dist <= max_hamming:
                            findings.append({
                                "type": "Cross-Institution Near-Duplicate Image",
                                "status": "Possible anomaly - needs human verification",
                                "severity": "HIGH",
                                "hamming_distance": dist,
                                "institutions": [rec1.get("institution_name"), rec2.get("institution_name")],
                                "files": [rec1.get("filename"), rec2.get("filename")],
                                "message": f"Near-identical image/stamp detected across colleges (Distance: {dist}/64 bits). May indicate recycled documentary evidence."
                            })
        return findings

    def detect_dual_college_faculty(self, roster_a: List[Dict[str, Any]], roster_b: List[Dict[str, Any]], inst_a_name: str, inst_b_name: str) -> List[Dict[str, Any]]:
        """
        Detect same faculty member claimed simultaneously by two institutions.
        Uses salted privacy-preserving hash.
        """
        findings = []
        hashes_a = {}
        for f in roster_a:
            raw_id = f.get("identifier") or f.get("pan") or f.get("aadhaar_last4") or f.get("name")
            if raw_id:
                f_hash = hash_faculty_id(raw_id, self.salt)
                hashes_a[f_hash] = f

        for f in roster_b:
            raw_id = f.get("identifier") or f.get("pan") or f.get("aadhaar_last4") or f.get("name")
            if raw_id:
                f_hash = hash_faculty_id(raw_id, self.salt)
                if f_hash in hashes_a:
                    fac_a = hashes_a[f_hash]
                    findings.append({
                        "type": "Dual-Institution Faculty Appointment Collision",
                        "status": "Possible anomaly - needs human verification",
                        "severity": "CRITICAL",
                        "masked_identifier": f_hash,
                        "faculty_name": f.get("name", "Faculty Member"),
                        "institutions": [inst_a_name, inst_b_name],
                        "details": f"Faculty identifier matches records at both {inst_a_name} ({fac_a.get('designation', 'Faculty')}) and {inst_b_name} ({f.get('designation', 'Faculty')})."
                    })
        return findings

    def check_year_over_year_consistency(self, current_year_data: Dict[str, Any], prior_year_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Detect unexplained structural reductions or high faculty turnover between consecutive approval cycles.
        """
        findings = []

        # 1. Shrunk Built-up Area
        curr_area = current_year_data.get("built_up_area_sqm", 0.0)
        prior_area = prior_year_data.get("built_up_area_sqm", 0.0)
        if prior_area > 0 and curr_area > 0:
            reduction = prior_area - curr_area
            if reduction > (prior_area * 0.10):  # More than 10% reduction
                findings.append({
                    "type": "Year-over-Year Built-up Area Reduction",
                    "status": "Deficiency",
                    "severity": "HIGH",
                    "computed_values": {
                        "prior_year_sqm": prior_area,
                        "current_year_sqm": curr_area,
                        "reduction_sqm": round(reduction, 1),
                        "reduction_percentage": f"{round((reduction/prior_area)*100, 1)}%"
                    },
                    "message": f"Instructional built-up area shrank from {prior_area:,.1f} sq.m to {curr_area:,.1f} sq.m ({round(reduction/prior_area*100, 1)}% reduction) without approved demolition or Change of Site."
                })

        # 2. Changed Land Survey Number without Change of Site
        curr_survey = str(current_year_data.get("survey_number", "")).strip()
        prior_survey = str(prior_year_data.get("survey_number", "")).strip()
        category = current_year_data.get("category", "EOA")
        if curr_survey and prior_survey and curr_survey != prior_survey and category != "CHANGE_OF_SITE":
            findings.append({
                "type": "Unapproved Campus Survey Number Change",
                "status": "Possible anomaly - needs human verification",
                "severity": "CRITICAL",
                "computed_values": {
                    "prior_survey_no": prior_survey,
                    "current_survey_no": curr_survey,
                    "application_category": category
                },
                "message": f"Campus survey number changed from '{prior_survey}' to '{curr_survey}' under standard '{category}' application (Mandatory Change of Site filing required under APH Chapter II)."
            })

        # 3. Excessive Faculty Turnover (> 60%)
        prior_fac_set = set(prior_year_data.get("faculty_hashes", []))
        curr_fac_set = set(current_year_data.get("faculty_hashes", []))
        if prior_fac_set and curr_fac_set:
            retained = len(prior_fac_set.intersection(curr_fac_set))
            turnover_pct = round((1 - (retained / len(prior_fac_set))) * 100, 1)
            if turnover_pct > 60.0:
                findings.append({
                    "type": "High Faculty Turnover Anomaly",
                    "status": "Needs manual review",
                    "severity": "MEDIUM",
                    "computed_values": {
                        "turnover_percentage": f"{turnover_pct}%",
                        "prior_faculty_count": len(prior_fac_set),
                        "retained_count": retained
                    },
                    "message": f"Abnormal faculty turnover of {turnover_pct}% observed between academic sessions ({len(prior_fac_set) - retained} departures)."
                })

        return findings
