"""
Document Classifier Module.

Classifies documents into predefined AICTE document types using
keyword-based matching and filename analysis.
"""

import re
from typing import Dict, Tuple, Optional, List
from collections import namedtuple

from config.settings import DocumentTypes

ClassificationResult = namedtuple("ClassificationResult", ["doc_type", "confidence"])


class DocumentClassifier:
    """Classifies document types based on text content and filename patterns."""

    def __init__(self) -> None:
        """Initialize the document classifier with keyword patterns for each document type."""
        self._keyword_patterns: Dict[str, List[str]] = {
            DocumentTypes.AFFIDAVIT: [
                "affidavit", "sworn", "notary", "deponent", "oath",
                "solemnly affirm", "notarized", "stamp paper", "judicial",
                "magistrate", "verification", "affirmation", "on oath",
                "do hereby declare", "true and correct"
            ],
            DocumentTypes.NOC: [
                "no objection", "noc", "permission", "consent",
                "no objection certificate", "hereby certify",
                "no objection to", "state government", "competent authority"
            ],
            DocumentTypes.ACCREDITATION_CERT: [
                "accreditation", "nba", "naac", "accredited", "grade",
                "national board of accreditation", "national assessment",
                "accreditation certificate", "tier", "cgpa", "institutional accreditation"
            ],
            DocumentTypes.FIRE_SAFETY_CERT: [
                "fire", "safety", "fire safety certificate", "fire department",
                "fire noc", "fire extinguisher", "fire station", "chief fire officer",
                "fire brigade", "fire fighting", "fire prevention"
            ],
            DocumentTypes.LAND_DOCUMENT: [
                "land", "deed", "title", "survey", "registration", "property",
                "sale deed", "lease deed", "land area", "acre", "hectare",
                "sub-registrar", "khasra", "khata", "land record", "conveyance"
            ],
            DocumentTypes.BUILDING_PLAN: [
                "building", "plan", "floor", "layout", "architect", "approved plan",
                "floor plan", "built-up area", "carpet area", "construction",
                "building permit", "sanctioned plan", "municipal"
            ],
            DocumentTypes.FACULTY_LIST: [
                "faculty", "professor", "teaching staff", "designation",
                "qualification", "assistant professor", "associate professor",
                "head of department", "hod", "phd", "m.tech", "lecturer",
                "faculty details", "teaching experience"
            ],
            DocumentTypes.FINANCIAL_STATEMENT: [
                "financial", "balance sheet", "income", "expenditure", "audit",
                "revenue", "chartered accountant", "fdr", "fixed deposit",
                "corpus fund", "endowment", "bank statement", "ca certificate",
                "audited statement", "profit and loss"
            ],
            DocumentTypes.EOA_CERTIFICATE: [
                "extension", "approval", "eoa", "approved", "aicte",
                "extension of approval", "approval letter", "f.no",
                "all india council", "technical education",
                "approval status", "academic year"
            ],
            DocumentTypes.UNDERTAKING: [
                "undertaking", "hereby undertake", "commit", "assurance",
                "we undertake", "i undertake", "pledge", "declaration",
                "signed undertaking", "binding", "solemnly undertake"
            ],
        }

        self._filename_patterns: Dict[str, List[str]] = {
            DocumentTypes.AFFIDAVIT: ["affidavit", "sworn"],
            DocumentTypes.NOC: ["noc", "no_objection", "permission"],
            DocumentTypes.ACCREDITATION_CERT: ["accreditation", "nba", "naac"],
            DocumentTypes.FIRE_SAFETY_CERT: ["fire", "fire_safety"],
            DocumentTypes.LAND_DOCUMENT: ["land", "deed", "property"],
            DocumentTypes.BUILDING_PLAN: ["building", "floor_plan", "layout"],
            DocumentTypes.FACULTY_LIST: ["faculty", "staff_list", "teaching"],
            DocumentTypes.FINANCIAL_STATEMENT: ["financial", "balance", "audit", "fdr"],
            DocumentTypes.EOA_CERTIFICATE: ["eoa", "approval", "extension"],
            DocumentTypes.UNDERTAKING: ["undertaking", "declaration"],
        }

    def classify(self, text: str = "", filename: str = "", *args, **kwargs) -> ClassificationResult:
        """
        Classify a document based on its text content and optionally its filename.

        Args:
            text: Extracted text from the document.
            filename: Original filename (optional, used for additional hints).

        Returns:
            ClassificationResult(document_type, confidence_score) where confidence is 0.0 to 1.0.
        """
        # Resolve positional / keyword overrides gracefully
        actual_text = kwargs.get("text", text)
        actual_filename = kwargs.get("filename", filename)

        # If a filepath was passed as first arg and keyword text was also provided
        if args and not actual_filename:
            actual_filename = str(args[0])

        # Get keyword-based scores
        text_scores = self._keyword_based_classification(actual_text)

        # Get filename hints
        filename_hint = self._filename_based_hints(actual_filename) if actual_filename else None

        # Boost the filename-hinted type if available
        if filename_hint and filename_hint in text_scores:
            text_scores[filename_hint] = text_scores[filename_hint] * 1.3 + 0.1

        if not text_scores or max(text_scores.values()) == 0:
            return ClassificationResult("UNKNOWN", 0.0)

        # Find the best match
        best_type = max(text_scores, key=text_scores.get)
        best_score = text_scores[best_type]

        # Normalize confidence to 0-1 range
        max_possible = len(self._keyword_patterns.get(best_type, [])) * 1.3 + 0.1
        confidence = min(best_score / max(max_possible * 0.4, 1), 1.0)

        return ClassificationResult(best_type, round(confidence, 3))

    def _keyword_based_classification(self, text: str) -> Dict[str, float]:
        """
        Score each document type based on keyword matches in the text.

        Args:
            text: Document text to analyze.

        Returns:
            Dictionary mapping document types to match scores.
        """
        text_lower = text.lower()
        scores: Dict[str, float] = {}

        for doc_type, keywords in self._keyword_patterns.items():
            score = 0.0
            for keyword in keywords:
                # Count occurrences of each keyword
                count = len(re.findall(re.escape(keyword), text_lower))
                if count > 0:
                    # Diminishing returns for repeated matches
                    score += 1.0 + min(count - 1, 3) * 0.2

            scores[doc_type] = score

        return scores

    def _filename_based_hints(self, filename: str) -> Optional[str]:
        """
        Determine a likely document type from the filename.

        Args:
            filename: The document's filename.

        Returns:
            Likely document type string, or None if no match found.
        """
        if not filename:
            return None

        filename_lower = filename.lower().replace(" ", "_").replace("-", "_")

        for doc_type, patterns in self._filename_patterns.items():
            for pattern in patterns:
                if pattern in filename_lower:
                    return doc_type

        return None

    def get_all_scores(self, text: str, filename: str = "") -> Dict[str, float]:
        """
        Get classification scores for all document types.

        Args:
            text: Document text to analyze.
            filename: Optional filename for additional hints.

        Returns:
            Dictionary mapping all document types to their confidence scores (0-1).
        """
        text_scores = self._keyword_based_classification(text)
        filename_hint = self._filename_based_hints(filename) if filename else None

        if filename_hint and filename_hint in text_scores:
            text_scores[filename_hint] = text_scores[filename_hint] * 1.3 + 0.1

        # Normalize all scores
        result = {}
        for doc_type, score in text_scores.items():
            max_possible = len(self._keyword_patterns.get(doc_type, [])) * 1.3 + 0.1
            normalized = min(score / max(max_possible * 0.4, 1), 1.0)
            result[doc_type] = round(normalized, 3)

        return result
