"""
Anomaly Detector for the AICTE Application Validation Platform.

Detects suspicious patterns in uploaded documents using OCR text analysis,
metadata consistency checks, image manipulation detection (ELA), and
duplicate-content detection via RapidFuzz.
"""

from __future__ import annotations

import io
import os
import re
import statistics
from datetime import date, datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import cv2
import numpy as np
from rapidfuzz import fuzz


# ---------------------------------------------------------------------------
# Severity Enum
# ---------------------------------------------------------------------------

class Severity(str, Enum):
    """Alert severity levels."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


# ---------------------------------------------------------------------------
# Alert factory helper
# ---------------------------------------------------------------------------

def _alert(
    alert_type: str,
    severity: str,
    description: str,
    evidence: str = "",
    confidence: float = 0.5,
) -> dict:
    """Create a standardised alert dict."""
    return {
        "alert_type": alert_type,
        "severity": severity,
        "description": description,
        "evidence": evidence,
        "confidence": round(confidence, 3),
    }


# ---------------------------------------------------------------------------
# Date helper
# ---------------------------------------------------------------------------

def _try_parse_date(value: str) -> Optional[date]:
    """Try several common date formats and return a ``date`` or ``None``."""
    for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%Y/%m/%d", "%d %b %Y", "%d %B %Y"):
        try:
            return datetime.strptime(value.strip(), fmt).date()
        except (ValueError, AttributeError):
            continue
    return None


# ---------------------------------------------------------------------------
# AnomalyDetector
# ---------------------------------------------------------------------------

class AnomalyDetector:
    """Analyse documents for anomalies and potential fraud indicators.

    The detector combines several lightweight heuristic checks that can be
    run without a GPU or large ML model, making it suitable for an MVP /
    demo environment.
    """

    # Weights used by ``calculate_anomaly_score``
    _SEVERITY_WEIGHT: Dict[str, float] = {
        Severity.LOW: 0.10,
        Severity.MEDIUM: 0.25,
        Severity.HIGH: 0.50,
        Severity.CRITICAL: 1.00,
    }

    def __init__(self) -> None:
        """Initialise the anomaly detector (stateless)."""
        pass  # No persistent state needed

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    def analyze_document(
        self,
        doc_path: str = "",
        ocr_text: str = "",
        metadata: Optional[dict] = None,
        text: Optional[str] = None,
        reference_texts: Optional[List[str]] = None,
    ) -> List[dict]:
        """Run all anomaly checks against a document.

        Args:
            doc_path: File-system path to the document/image.
            ocr_text: Extracted OCR text for the document.
            metadata: Dict with keys such as ``creation_date``,
                ``modification_date``, ``producer``, ``author``,
                ``institution_established_year``, ``dates``, etc.
            text: Alias for ocr_text if provided.
            reference_texts: Optional list of other texts for duplicate checking.

        Returns:
            A list of alert dicts.
        """
        if text is not None and not ocr_text:
            ocr_text = text
        if metadata is None:
            metadata = {}

        alerts: List[dict] = []

        # Metadata consistency
        alerts.extend(self.check_metadata_consistency(metadata))

        # Text anomalies
        if ocr_text:
            alerts.extend(self.check_text_anomalies(ocr_text))

        # Date anomalies
        dates_raw: List[str] = metadata.get("dates", [])
        alerts.extend(self.check_date_anomalies(dates_raw, metadata))

        # Duplicate checking if reference texts provided
        if reference_texts and ocr_text:
            alerts.extend(self.check_duplicate_content(ocr_text, reference_texts))

        # Image manipulation (only for image files)
        if doc_path and os.path.isfile(doc_path):
            ext = os.path.splitext(doc_path)[1].lower()
            if ext in (".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif"):
                image = cv2.imread(doc_path)
                if image is not None:
                    alerts.extend(self.check_image_manipulation(image))

        return alerts

    # ------------------------------------------------------------------
    # Metadata checks
    # ------------------------------------------------------------------

    def check_metadata_consistency(self, metadata: dict) -> List[dict]:
        """Check PDF / image metadata for inconsistencies.

        Flags:
        - Modification date before creation date.
        - Suspicious producer software (e.g. online PDF editors).
        - Missing creator information.
        """
        alerts: List[dict] = []

        creation = metadata.get("creation_date")
        modification = metadata.get("modification_date")

        today = date.today()
        if creation:
            c_date = _try_parse_date(str(creation))
            if c_date and c_date > today:
                alerts.append(_alert(
                    alert_type="METADATA_FUTURE_DATE",
                    severity=Severity.HIGH,
                    description="Document creation date is in the future — possible metadata tampering.",
                    evidence=f"creation_date={c_date}, today={today}",
                    confidence=0.90,
                ))

        if creation and modification:
            c_date = _try_parse_date(str(creation))
            m_date = _try_parse_date(str(modification))
            if c_date and m_date:
                if m_date < c_date:
                    alerts.append(_alert(
                        alert_type="METADATA_DATE_INCONSISTENCY",
                        severity=Severity.HIGH,
                        description=(
                            "Modification date is earlier than creation date — "
                            "possible metadata tampering."
                        ),
                        evidence=f"creation={c_date}, modification={m_date}",
                        confidence=0.85,
                    ))

        # Suspicious producers
        producer = (metadata.get("producer") or "").lower()
        suspicious_producers = [
            "smallpdf", "ilovepdf", "sejda", "pdf candy",
            "online2pdf", "pdf24", "pdfzorro", "pdfescape",
        ]
        for sp in suspicious_producers:
            if sp in producer:
                alerts.append(_alert(
                    alert_type="SUSPICIOUS_PRODUCER",
                    severity=Severity.MEDIUM,
                    description=f"Document produced by online editor '{sp}' — may have been altered.",
                    evidence=f"producer={metadata.get('producer', '')}",
                    confidence=0.60,
                ))
                break

        # Missing author
        author = metadata.get("author", "")
        if not author:
            alerts.append(_alert(
                alert_type="MISSING_AUTHOR",
                severity=Severity.LOW,
                description="Document author metadata is empty.",
                evidence="author=<empty>",
                confidence=0.30,
            ))

        return alerts

    # ------------------------------------------------------------------
    # Text anomalies
    # ------------------------------------------------------------------

    def check_text_anomalies(self, text: str) -> List[dict]:
        """Detect suspicious text patterns that may indicate forgery.

        Checks:
        - Mixed font indicators (unusual Unicode characters).
        - Inconsistent whitespace / formatting.
        - Suspiciously short or repetitive text.
        - Non-printable or control characters.
        """
        alerts: List[dict] = []

        # 1. Non-printable / control characters (excluding standard whitespace)
        control_chars = re.findall(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", text)
        if control_chars:
            alerts.append(_alert(
                alert_type="CONTROL_CHARACTERS",
                severity=Severity.MEDIUM,
                description=f"Found {len(control_chars)} non-printable control character(s) in text.",
                evidence=f"count={len(control_chars)}",
                confidence=0.65,
            ))

        # 2. Mixed-script detection (Latin mixed with Cyrillic / Greek look-alikes)
        latin_count = len(re.findall(r"[a-zA-Z]", text))
        cyrillic_count = len(re.findall(r"[\u0400-\u04FF]", text))
        greek_count = len(re.findall(r"[\u0370-\u03FF]", text))
        if latin_count > 20 and (cyrillic_count > 0 or greek_count > 0):
            alerts.append(_alert(
                alert_type="MIXED_SCRIPT_CHARACTERS",
                severity=Severity.HIGH,
                description=(
                    "Text contains a mix of Latin and Cyrillic/Greek characters — "
                    "possible homoglyph substitution to bypass automated checks."
                ),
                evidence=f"latin={latin_count}, cyrillic={cyrillic_count}, greek={greek_count}",
                confidence=0.80,
            ))

        # 3. Excessive whitespace (many consecutive spaces or tabs)
        long_ws = re.findall(r"[ \t]{10,}", text)
        if len(long_ws) > 5:
            alerts.append(_alert(
                alert_type="INCONSISTENT_FORMATTING",
                severity=Severity.LOW,
                description=f"Document has {len(long_ws)} regions of excessive whitespace.",
                evidence=f"long_whitespace_regions={len(long_ws)}",
                confidence=0.40,
            ))

        # 4. Very short extracted text (suspicious for multi-page documents)
        if 0 < len(text.strip()) < 50:
            alerts.append(_alert(
                alert_type="INSUFFICIENT_TEXT",
                severity=Severity.MEDIUM,
                description="Very little text extracted — document may be image-only or redacted.",
                evidence=f"text_length={len(text.strip())}",
                confidence=0.55,
            ))

        # 5. Repeated phrases (copy-paste within the same document)
        sentences = [s.strip() for s in re.split(r"[.\n]", text) if len(s.strip()) > 30]
        seen: Dict[str, int] = {}
        for sentence in sentences:
            normalised = " ".join(sentence.lower().split())
            seen[normalised] = seen.get(normalised, 0) + 1
        repeats = {k: v for k, v in seen.items() if v > 2}
        if repeats:
            alerts.append(_alert(
                alert_type="REPEATED_PHRASES",
                severity=Severity.MEDIUM,
                description=f"Found {len(repeats)} phrase(s) repeated more than twice in the document.",
                evidence="; ".join(f"'{k[:60]}…' x{v}" for k, v in list(repeats.items())[:3]),
                confidence=0.55,
            ))

        return alerts

    # ------------------------------------------------------------------
    # Date anomalies
    # ------------------------------------------------------------------

    def check_date_anomalies(self, dates: List[str], metadata: dict) -> List[dict]:
        """Flag dates that are logically impossible or suspicious.

        Args:
            dates: Raw date strings extracted from the document.
            metadata: Must include ``institution_established_year`` if available.
        """
        alerts: List[dict] = []
        today = date.today()
        established_year: Optional[int] = metadata.get("institution_established_year")

        for raw in dates:
            parsed = _try_parse_date(raw)
            if parsed is None:
                continue

            # Future date
            if parsed > today:
                alerts.append(_alert(
                    alert_type="FUTURE_DATE",
                    severity=Severity.HIGH,
                    description=f"Date '{parsed}' is in the future.",
                    evidence=f"date={parsed}, today={today}",
                    confidence=0.90,
                ))

            # Date before institution established
            if established_year and parsed.year < established_year:
                alerts.append(_alert(
                    alert_type="DATE_BEFORE_ESTABLISHMENT",
                    severity=Severity.HIGH,
                    description=(
                        f"Date '{parsed}' predates institution establishment year "
                        f"({established_year})."
                    ),
                    evidence=f"date={parsed}, established={established_year}",
                    confidence=0.85,
                ))

            # Unreasonably old
            if parsed.year < 1947:
                alerts.append(_alert(
                    alert_type="UNREASONABLY_OLD_DATE",
                    severity=Severity.MEDIUM,
                    description=f"Date '{parsed}' is before 1947 — likely erroneous.",
                    evidence=f"date={parsed}",
                    confidence=0.70,
                ))

        return alerts

    # ------------------------------------------------------------------
    # Duplicate content
    # ------------------------------------------------------------------

    def check_duplicate_content(
        self,
        text: str,
        existing_texts: List[str],
    ) -> List[dict]:
        """Compare this document's text against previously seen documents.

        Uses RapidFuzz to measure similarity; high similarity between
        distinct documents is suspicious.

        Args:
            text: The extracted text of the current document.
            existing_texts: Texts of previously submitted documents.

        Returns:
            Alert dicts for each suspiciously similar match.
        """
        alerts: List[dict] = []
        if not text or not existing_texts:
            return alerts

        text_normalised = " ".join(text.lower().split())

        for idx, existing in enumerate(existing_texts):
            existing_normalised = " ".join(existing.lower().split())
            if not existing_normalised:
                continue

            # Token-sort ratio is more resilient to word-order changes
            score = fuzz.token_sort_ratio(text_normalised, existing_normalised)
            if score >= 95:
                alerts.append(_alert(
                    alert_type="NEAR_DUPLICATE_DOCUMENT",
                    severity=Severity.CRITICAL,
                    description=f"Document text is almost identical to existing document #{idx + 1} (score={score:.1f}%).",
                    evidence=f"similarity_score={score:.1f}",
                    confidence=score / 100,
                ))
            elif score >= 85:
                alerts.append(_alert(
                    alert_type="HIGHLY_SIMILAR_DOCUMENT",
                    severity=Severity.HIGH,
                    description=f"Document text is highly similar to existing document #{idx + 1} (score={score:.1f}%).",
                    evidence=f"similarity_score={score:.1f}",
                    confidence=score / 100,
                ))
            elif score >= 70:
                alerts.append(_alert(
                    alert_type="SIMILAR_DOCUMENT",
                    severity=Severity.MEDIUM,
                    description=f"Document text has notable similarity to existing document #{idx + 1} (score={score:.1f}%).",
                    evidence=f"similarity_score={score:.1f}",
                    confidence=score / 100,
                ))

        return alerts

    # ------------------------------------------------------------------
    # Image manipulation
    # ------------------------------------------------------------------

    def check_image_manipulation(self, image: np.ndarray) -> List[dict]:
        """Run basic image-forensic checks using OpenCV.

        Checks:
        - Noise-level analysis (uniform noise may indicate generation).
        - Edge-detection anomalies.
        - Error Level Analysis (ELA) for copy-paste / splicing.

        Args:
            image: BGR image loaded via ``cv2.imread``.

        Returns:
            Alert dicts for detected anomalies.
        """
        alerts: List[dict] = []

        if image is None or image.size == 0:
            return alerts

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # ----- 1. Noise analysis (Laplacian variance) -----
        laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
        if laplacian_var < 10:
            alerts.append(_alert(
                alert_type="LOW_IMAGE_DETAIL",
                severity=Severity.MEDIUM,
                description=(
                    "Image has unusually low detail / variance — "
                    "may be digitally generated or heavily processed."
                ),
                evidence=f"laplacian_variance={laplacian_var:.2f}",
                confidence=0.55,
            ))
        elif laplacian_var > 5000:
            alerts.append(_alert(
                alert_type="HIGH_NOISE_LEVEL",
                severity=Severity.LOW,
                description="Image has unusually high noise, possibly a low-quality scan.",
                evidence=f"laplacian_variance={laplacian_var:.2f}",
                confidence=0.40,
            ))

        # ----- 2. Edge-detection anomaly -----
        edges = cv2.Canny(gray, 100, 200)
        edge_ratio = np.count_nonzero(edges) / edges.size
        if edge_ratio > 0.5:
            alerts.append(_alert(
                alert_type="EXCESSIVE_EDGES",
                severity=Severity.LOW,
                description="Unusually high edge density — possible digital overlay.",
                evidence=f"edge_ratio={edge_ratio:.3f}",
                confidence=0.35,
            ))

        # ----- 3. Error Level Analysis (ELA) -----
        ela_image = self._perform_ela(image, quality=90)
        if ela_image is not None:
            ela_gray = cv2.cvtColor(ela_image, cv2.COLOR_BGR2GRAY)
            ela_mean = float(np.mean(ela_gray))
            ela_std = float(np.std(ela_gray))

            # Regions with significantly higher ELA suggest splicing
            if ela_std > 30:
                # Find bright patches in ELA
                _, thresh = cv2.threshold(ela_gray, 80, 255, cv2.THRESH_BINARY)
                bright_ratio = np.count_nonzero(thresh) / thresh.size
                if bright_ratio > 0.01:
                    alerts.append(_alert(
                        alert_type="ELA_ANOMALY",
                        severity=Severity.HIGH,
                        description=(
                            "Error Level Analysis reveals regions with inconsistent "
                            "compression — possible copy-paste or splicing."
                        ),
                        evidence=f"ela_std={ela_std:.2f}, bright_region_ratio={bright_ratio:.4f}",
                        confidence=0.70,
                    ))

        return alerts

    # ------------------------------------------------------------------
    # Scoring
    # ------------------------------------------------------------------

    def calculate_anomaly_score(
        self,
        alerts: Any = None,
        text: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> float:
        """Compute a composite anomaly score between 0.0 (clean) and 1.0 (highly suspicious).

        Accepts either a list of alert dicts, or directly text/metadata to analyze.
        """
        if alerts is None:
            alerts = self.analyze_document(ocr_text=text or "", metadata=metadata or {})
        elif isinstance(alerts, (str, dict)) and not isinstance(alerts, list):
            # Positional string argument passed
            alerts = self.analyze_document(ocr_text=str(alerts), metadata=metadata or {})

        if not alerts:
            return 0.0

        raw = 0.0
        for a in alerts:
            weight = self._SEVERITY_WEIGHT.get(a.get("severity", "LOW"), 0.1)
            conf = a.get("confidence", 0.5)
            raw += weight * conf

        # Normalise: assume ≥ 3 weighted units → 1.0
        normalised = min(raw / 3.0, 1.0)
        return round(normalised, 4)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _perform_ela(self, image: np.ndarray, quality: int = 90) -> Optional[np.ndarray]:
        """Perform Error Level Analysis on an image.

        Re-saves the image at *quality* JPEG quality and computes the
        per-pixel absolute difference with the original, amplified ×15.

        Args:
            image: Original BGR image.
            quality: JPEG quality level for re-compression.

        Returns:
            The amplified difference image, or ``None`` on failure.
        """
        try:
            encode_params = [int(cv2.IMWRITE_JPEG_QUALITY), quality]
            success, encoded = cv2.imencode(".jpg", image, encode_params)
            if not success:
                return None
            decoded = cv2.imdecode(
                np.frombuffer(encoded.tobytes(), dtype=np.uint8),
                cv2.IMREAD_COLOR,
            )
            if decoded is None:
                return None

            # Ensure same size
            if decoded.shape != image.shape:
                decoded = cv2.resize(decoded, (image.shape[1], image.shape[0]))

            diff = cv2.absdiff(image, decoded)
            # Amplify
            ela = (diff * 15).clip(0, 255).astype(np.uint8)
            return ela
        except Exception:
            return None
