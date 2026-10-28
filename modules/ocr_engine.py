"""
OCR Engine Module using Tesseract (pytesseract).

Provides text extraction from images and PDFs with confidence scoring
and structured data output.
"""

import os
from typing import List, Dict, Tuple, Optional

import numpy as np
import pandas as pd

try:
    import pytesseract
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False

try:
    from PIL import Image
except ImportError:
    Image = None

from modules.pdf_processor import PDFProcessor
from modules.image_preprocessor import ImagePreprocessor


class OCREngine:
    """Extracts text from images and PDFs using Tesseract OCR."""

    def __init__(self, language: str = "eng") -> None:
        """
        Initialize the OCR engine.

        Args:
            language: Tesseract language code (default 'eng').
        """
        self.language = language
        self.preprocessor = ImagePreprocessor()

        if not TESSERACT_AVAILABLE:
            import warnings
            warnings.warn(
                "pytesseract is not installed. OCR functionality will be limited. "
                "Install with: pip install pytesseract"
            )

    def extract_text(self, image: np.ndarray) -> str:
        """
        Extract text from an image using Tesseract OCR.

        Args:
            image: Input image as NumPy array.

        Returns:
            Extracted text string.
        """
        if not TESSERACT_AVAILABLE:
            return "[OCR unavailable: pytesseract not installed]"

        if image is None or image.size == 0:
            return ""

        try:
            # Preprocess for better OCR
            processed = self.preprocessor.preprocess_for_ocr(image)
            text = pytesseract.image_to_string(processed, lang=self.language)
            return text.strip()
        except Exception as e:
            return f"[OCR Error: {str(e)}]"

    def extract_text_with_confidence(self, image: np.ndarray) -> Tuple[str, float]:
        """
        Extract text with an average confidence score.

        Args:
            image: Input image as NumPy array.

        Returns:
            Tuple of (extracted_text, average_confidence) where confidence is 0.0 to 1.0.
        """
        if not TESSERACT_AVAILABLE:
            return "[OCR unavailable: pytesseract not installed]", 0.0

        if image is None or image.size == 0:
            return "", 0.0

        try:
            processed = self.preprocessor.preprocess_for_ocr(image)
            data = pytesseract.image_to_data(
                processed, lang=self.language, output_type=pytesseract.Output.DATAFRAME
            )

            # Filter out rows without text
            text_rows = data[data["text"].notna() & (data["text"].str.strip() != "")]

            if text_rows.empty:
                return "", 0.0

            # Filter out rows with confidence -1 (no OCR confidence)
            valid_conf = text_rows[text_rows["conf"] >= 0]

            full_text = " ".join(text_rows["text"].astype(str).tolist())
            avg_confidence = valid_conf["conf"].mean() / 100.0 if not valid_conf.empty else 0.0

            return full_text.strip(), round(avg_confidence, 3)
        except Exception as e:
            return f"[OCR Error: {str(e)}]", 0.0

    def extract_structured_data(self, image: np.ndarray) -> pd.DataFrame:
        """
        Extract word-level OCR data with bounding boxes and confidence.

        Args:
            image: Input image as NumPy array.

        Returns:
            DataFrame with columns: text, conf, left, top, width, height, block_num, line_num, word_num.
        """
        if not TESSERACT_AVAILABLE:
            return pd.DataFrame()

        if image is None or image.size == 0:
            return pd.DataFrame()

        try:
            processed = self.preprocessor.preprocess_for_ocr(image)
            data = pytesseract.image_to_data(
                processed, lang=self.language, output_type=pytesseract.Output.DATAFRAME
            )

            # Filter to only rows with actual text
            result = data[data["text"].notna() & (data["text"].str.strip() != "")].copy()
            result = result[["text", "conf", "left", "top", "width", "height",
                             "block_num", "line_num", "word_num"]]
            return result.reset_index(drop=True)
        except Exception as e:
            return pd.DataFrame()

    def extract_from_pdf(self, pdf_path: str) -> str:
        """
        Extract text from a PDF file combining native text extraction and OCR.

        For text-based PDFs, extracts text directly. For scanned PDFs,
        renders pages as images and applies OCR.

        Args:
            pdf_path: Path to the PDF file.

        Returns:
            Extracted text from the PDF.
        """
        try:
            processor = PDFProcessor(pdf_path)

            # First try native text extraction
            native_text = processor.extract_text()

            if not processor.is_scanned_pdf():
                # Text-based PDF — native extraction is sufficient
                return native_text

            # Scanned PDF — use OCR on rendered pages
            ocr_texts = []
            page_count = processor.get_page_count()

            for page_num in range(page_count):
                try:
                    page_image = processor.render_page_as_image(page_num, dpi=300)
                    page_text = self.extract_text(page_image)
                    if page_text:
                        ocr_texts.append(f"--- Page {page_num + 1} ---\n{page_text}")
                except Exception:
                    ocr_texts.append(f"--- Page {page_num + 1} ---\n[OCR failed for this page]")

            # Combine native text (if any) with OCR text
            combined = native_text.strip()
            if ocr_texts:
                ocr_combined = "\n\n".join(ocr_texts)
                if combined:
                    combined += "\n\n--- OCR Extracted Text ---\n\n" + ocr_combined
                else:
                    combined = ocr_combined

            return combined
        except Exception as e:
            return f"[PDF Processing Error: {str(e)}]"

    def extract_from_image_file(self, image_path: str) -> str:
        """
        Extract text from an image file (JPG, PNG, etc.).

        Args:
            image_path: Path to the image file.

        Returns:
            Extracted text.
        """
        if not os.path.exists(image_path):
            return f"[File not found: {image_path}]"

        try:
            import cv2
            image = cv2.imread(image_path)
            if image is None:
                return f"[Failed to read image: {image_path}]"
            return self.extract_text(image)
        except Exception as e:
            return f"[Image Processing Error: {str(e)}]"

    def batch_extract(self, file_paths: List[str]) -> Dict[str, str]:
        """
        Process multiple files and extract text from each.

        Args:
            file_paths: List of file paths (PDFs or images).

        Returns:
            Dictionary mapping file paths to extracted text.
        """
        results = {}
        for file_path in file_paths:
            if not os.path.exists(file_path):
                results[file_path] = "[File not found]"
                continue

            ext = os.path.splitext(file_path)[1].lower()
            if ext == ".pdf":
                results[file_path] = self.extract_from_pdf(file_path)
            elif ext in (".jpg", ".jpeg", ".png", ".tiff", ".bmp"):
                results[file_path] = self.extract_from_image_file(file_path)
            else:
                results[file_path] = f"[Unsupported file type: {ext}]"

        return results
