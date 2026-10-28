"""
Comparison Engine for the AICTE Application Validation Platform.

Uses Pandas DataFrames and RapidFuzz to compare submitted application
fields against reference records, detect mismatches, and find duplicate
documents.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
from rapidfuzz import fuzz


# ---------------------------------------------------------------------------
# ComparisonEngine
# ---------------------------------------------------------------------------

class ComparisonEngine:
    """Field-level comparison engine powered by RapidFuzz fuzzy matching.

    All comparison results are returned as Pandas DataFrames so they can
    be easily displayed in Streamlit tables, exported to CSV, or fed into
    Plotly charts.
    """

    def __init__(self) -> None:
        """Initialise the comparison engine (stateless)."""
        pass

    # ------------------------------------------------------------------
    # Core fuzzy matching
    # ------------------------------------------------------------------

    def fuzzy_match(
        self,
        str1: str,
        str2: str,
        threshold: float = 80.0,
    ) -> Tuple[float, bool]:
        """Compute a fuzzy-match score between two strings.

        Uses ``rapidfuzz.fuzz.token_sort_ratio`` which is resilient to
        word-order differences and extra whitespace.

        Args:
            str1: First string.
            str2: Second string.
            threshold: Minimum score to consider a match.

        Returns:
            A tuple of ``(score, is_match)`` where *score* is 0–100 and
            *is_match* is ``True`` when *score* ≥ *threshold*.
        """
        s1 = str(str1).strip()
        s2 = str(str2).strip()
        if not s1 and not s2:
            return (100.0, True)
        if not s1 or not s2:
            return (0.0, False)
        score = fuzz.token_sort_ratio(s1, s2)
        return (round(score, 2), score >= threshold)

    # ------------------------------------------------------------------
    # Field-level comparison
    # ------------------------------------------------------------------

    def compare_fields(
        self,
        submitted: dict,
        reference: dict,
    ) -> pd.DataFrame:
        """Compare each key of *submitted* against the corresponding
        value in *reference*.

        Returns:
            DataFrame with columns ``field_name``, ``submitted_value``,
            ``reference_value``, ``match_score``, ``status``.
        """
        all_keys = sorted(set(list(submitted.keys()) + list(reference.keys())))
        rows: List[dict] = []
        for key in all_keys:
            sub_val = submitted.get(key, "")
            ref_val = reference.get(key, "")
            score, is_match = self.fuzzy_match(str(sub_val), str(ref_val))
            status = self._score_to_status(score)
            rows.append({
                "field_name": key,
                "submitted_value": str(sub_val),
                "reference_value": str(ref_val),
                "match_score": score,
                "status": status,
            })
        return pd.DataFrame(rows)

    # ------------------------------------------------------------------
    # Document comparison
    # ------------------------------------------------------------------

    def compare_documents(
        self,
        doc1_data: dict,
        doc2_data: dict,
    ) -> pd.DataFrame:
        """Cross-compare metadata and extracted text of two documents.

        Both *doc1_data* and *doc2_data* should be dicts with keys like
        ``doc_type``, ``filename``, ``issuing_authority``,
        ``reference_number``, ``extracted_text``, etc.

        Returns:
            DataFrame in the same shape as :meth:`compare_fields`.
        """
        compare_keys = [
            "doc_type", "issuing_authority", "reference_number",
            "issue_date", "expiry_date", "extracted_text",
        ]
        rows: List[dict] = []
        for key in compare_keys:
            val1 = str(doc1_data.get(key, ""))
            val2 = str(doc2_data.get(key, ""))
            score, _ = self.fuzzy_match(val1, val2)
            rows.append({
                "field_name": key,
                "submitted_value": val1[:200],
                "reference_value": val2[:200],
                "match_score": score,
                "status": self._score_to_status(score),
            })
        return pd.DataFrame(rows)

    # ------------------------------------------------------------------
    # Application vs institutional records
    # ------------------------------------------------------------------

    def compare_with_records(
        self,
        application_data: dict,
        institutional_records: dict,
    ) -> pd.DataFrame:
        """Compare the submitted application against stored institutional records.

        Flattens nested dicts (e.g. ``institution.name``) before comparing.

        Returns:
            DataFrame with comparison results per field.
        """
        flat_app = _flatten(application_data)
        flat_rec = _flatten(institutional_records)
        return self.compare_fields(flat_app, flat_rec)

    # ------------------------------------------------------------------
    # Duplicate detection
    # ------------------------------------------------------------------

    def find_duplicates(
        self,
        documents: List[dict],
        threshold: float = 85.0,
    ) -> List[dict]:
        """Identify potentially duplicated documents in a list.

        Uses the ``extracted_text`` field of each document for comparison.

        Args:
            documents: List of document dicts (must include ``extracted_text``).
            threshold: Minimum similarity score to flag as duplicate.

        Returns:
            A list of dicts describing each duplicate pair with keys
            ``doc1_index``, ``doc2_index``, ``doc1_type``, ``doc2_type``,
            ``similarity_score``, ``status``.
        """
        duplicates: List[dict] = []
        n = len(documents)
        for i in range(n):
            text_i = str(
                documents[i].get("extracted_text")
                or documents[i].get("text")
                or documents[i].get("ocr_text", "")
            ).strip()
            if not text_i:
                continue
            for j in range(i + 1, n):
                text_j = str(
                    documents[j].get("extracted_text")
                    or documents[j].get("text")
                    or documents[j].get("ocr_text", "")
                ).strip()
                if not text_j:
                    continue
                score = fuzz.token_sort_ratio(text_i, text_j)
                if score >= threshold:
                    duplicates.append({
                        "doc1_index": i,
                        "doc2_index": j,
                        "doc1_type": documents[i].get("doc_type", "UNKNOWN"),
                        "doc2_type": documents[j].get("doc_type", "UNKNOWN"),
                        "similarity_score": round(score, 2),
                        "similarity": round(score, 2),
                        "status": "EXACT_DUPLICATE" if score >= 98 else "NEAR_DUPLICATE",
                    })
        return duplicates

    # ------------------------------------------------------------------
    # Mismatch report
    # ------------------------------------------------------------------

    def generate_mismatch_report(self, comparison_df: pd.DataFrame) -> dict:
        """Produce a summary report from a comparison DataFrame.

        Returns:
            Dict with ``total_fields``, ``matched``, ``mismatched``,
            ``warnings``, ``overall_match_pct``, ``severity``, and
            ``mismatched_fields`` (list of field names).
        """
        if comparison_df.empty:
            return {
                "total_fields": 0,
                "matched": 0,
                "mismatched": 0,
                "warnings": 0,
                "overall_match_pct": 0.0,
                "severity": "N/A",
                "mismatched_fields": [],
            }

        total = len(comparison_df)
        matched = int((comparison_df["status"] == "MATCH").sum())
        mismatched = int((comparison_df["status"] == "MISMATCH").sum())
        warnings = int((comparison_df["status"] == "PARTIAL").sum())
        overall_pct = round(comparison_df["match_score"].mean(), 2)

        if mismatched == 0:
            severity = "NONE"
        elif mismatched <= 2:
            severity = "LOW"
        elif mismatched <= 5:
            severity = "MEDIUM"
        else:
            severity = "HIGH"

        mismatch_fields = comparison_df.loc[
            comparison_df["status"] == "MISMATCH", "field_name"
        ].tolist()

        return {
            "total_fields": total,
            "matched": matched,
            "matches": matched,
            "mismatched": mismatched,
            "mismatches": mismatched,
            "warnings": warnings,
            "overall_match_pct": overall_pct,
            "severity": severity,
            "mismatched_fields": mismatch_fields,
        }

    # ------------------------------------------------------------------
    # Batch comparison
    # ------------------------------------------------------------------

    def batch_compare(
        self,
        submitted_list: List[dict],
        reference_list: List[dict],
        key_field: str,
    ) -> pd.DataFrame:
        """Compare multiple submitted records against reference records
        matched by *key_field*.

        For each submitted record, the reference with the highest fuzzy
        match on *key_field* is selected, and a full field comparison is
        performed.

        Args:
            submitted_list: List of submitted data dicts.
            reference_list: List of reference data dicts.
            key_field: The field name used to pair records.

        Returns:
            DataFrame with an extra ``matched_key`` column indicating
            which reference record was paired.
        """
        all_rows: List[dict] = []

        for sub in submitted_list:
            sub_key = str(sub.get(key_field, ""))
            best_ref: Optional[dict] = None
            best_score = 0.0

            for ref in reference_list:
                ref_key = str(ref.get(key_field, ""))
                score, _ = self.fuzzy_match(sub_key, ref_key, threshold=0)
                if score > best_score:
                    best_score = score
                    best_ref = ref

            if best_ref is None:
                all_rows.append({
                    "field_name": key_field,
                    "submitted_value": sub_key,
                    "reference_value": "<no match>",
                    "match_score": 0.0,
                    "status": "MISMATCH",
                    "matched_key": "",
                })
                continue

            comparison = self.compare_fields(sub, best_ref)
            comparison["matched_key"] = str(best_ref.get(key_field, ""))
            all_rows.extend(comparison.to_dict("records"))

        return pd.DataFrame(all_rows) if all_rows else pd.DataFrame()

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _score_to_status(score: float) -> str:
        """Map a fuzzy-match score to a human-readable status string."""
        if score >= 95:
            return "MATCH"
        elif score >= 70:
            return "PARTIAL"
        else:
            return "MISMATCH"


# ---------------------------------------------------------------------------
# Module-level helpers
# ---------------------------------------------------------------------------

def _flatten(d: dict, parent_key: str = "", sep: str = ".") -> dict:
    """Recursively flatten a nested dict.

    Example::

        _flatten({"a": {"b": 1, "c": 2}}) → {"a.b": 1, "a.c": 2}
    """
    items: List[Tuple[str, Any]] = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(_flatten(v, new_key, sep).items())
        elif isinstance(v, list):
            # Store lists as their string representation
            items.append((new_key, str(v)))
        else:
            items.append((new_key, v))
    return dict(items)
