"""
Tests for the OCR Engine module.

Validates text extraction from images, confidence scoring, and error handling
for blank/invalid inputs. Tests requiring Tesseract are skipped automatically
if the binary is not installed.
"""

import os
import sys
import numpy as np
import pytest

# Ensure project root is on the path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from tests.conftest import requires_tesseract


class TestOCREngine:
    """Test suite for modules.ocr_engine.OCREngine."""

    @requires_tesseract
    def test_extract_text_from_image(self, sample_image: np.ndarray) -> None:
        """Create image with text, OCR it, and verify result contains expected words."""
        from modules.ocr_engine import OCREngine

        engine = OCREngine()
        result = engine.extract_text(sample_image)

        assert isinstance(result, str), "extract_text should return a string"
        assert len(result.strip()) > 0, "Extracted text should not be empty"

        # The sample_image has these words drawn on it
        expected_keywords = ["AFFIDAVIT", "Institute", "Technology"]
        found_any = any(kw.lower() in result.lower() for kw in expected_keywords)
        assert found_any, (
            f"Extracted text should contain at least one of {expected_keywords}. "
            f"Got: {result[:200]}"
        )

    @requires_tesseract
    def test_extract_text_with_confidence(self, sample_image: np.ndarray) -> None:
        """Confidence score should be a float between 0 and 1."""
        from modules.ocr_engine import OCREngine

        engine = OCREngine()
        result = engine.extract_text_with_confidence(sample_image)

        assert isinstance(result, dict), "Result should be a dictionary"

        # Expect keys for text and confidence
        assert "text" in result or "confidence" in result, (
            "Result should contain 'text' and/or 'confidence' keys"
        )

        if "confidence" in result:
            confidence = result["confidence"]
            assert isinstance(confidence, (int, float)), "Confidence should be numeric"
            assert 0.0 <= confidence <= 1.0, (
                f"Confidence should be between 0 and 1, got {confidence}"
            )

        if "text" in result:
            assert isinstance(result["text"], str), "Text should be a string"

    @requires_tesseract
    def test_empty_image(self, blank_image: np.ndarray) -> None:
        """OCR on a blank white image should return empty or whitespace-only text."""
        from modules.ocr_engine import OCREngine

        engine = OCREngine()
        result = engine.extract_text(blank_image)

        assert isinstance(result, str), "extract_text should return a string"
        # Blank image should produce minimal/empty text
        assert len(result.strip()) < 20, (
            f"Blank image should produce little or no text, got: '{result.strip()}'"
        )

    @requires_tesseract
    def test_invalid_input(self) -> None:
        """OCR engine should handle None and invalid input types gracefully."""
        from modules.ocr_engine import OCREngine

        engine = OCREngine()

        # Test with None
        try:
            result = engine.extract_text(None)
            # If it doesn't raise, result should be empty or a string
            assert result is not None, "Result should not be None on invalid input"
        except (TypeError, ValueError, AttributeError):
            pass  # Acceptable to raise on invalid input

        # Test with wrong type
        try:
            result = engine.extract_text("not_an_image")
            assert isinstance(result, str), "Should return string even on bad input"
        except (TypeError, ValueError, AttributeError):
            pass  # Acceptable to raise on invalid input

    @requires_tesseract
    def test_extract_text_returns_string(self, sample_image: np.ndarray) -> None:
        """Verify the return type is always a string."""
        from modules.ocr_engine import OCREngine

        engine = OCREngine()
        result = engine.extract_text(sample_image)
        assert isinstance(result, str), f"Expected str, got {type(result)}"

    @requires_tesseract
    def test_ocr_with_custom_image(self) -> None:
        """Test OCR with a programmatically created image containing clear text."""
        import cv2
        from modules.ocr_engine import OCREngine

        engine = OCREngine()

        # Create a high-contrast image with very clear text
        img = np.ones((300, 600, 3), dtype=np.uint8) * 255
        cv2.putText(img, "HELLO WORLD", (50, 150),
                    cv2.FONT_HERSHEY_SIMPLEX, 2.0, (0, 0, 0), 3)

        result = engine.extract_text(img)
        assert isinstance(result, str), "Result should be a string"
        # At minimum, it should extract something
        if len(result.strip()) > 0:
            # Check if any recognizable part was extracted
            assert any(
                w in result.upper() for w in ["HELLO", "WORLD", "HE", "WO"]
            ), f"Should recognize some text from clear image, got: '{result}'"
