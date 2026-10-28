"""
PDF Processing Module using PyMuPDF (fitz).

Handles text extraction, image extraction, metadata retrieval,
and page rendering for both text-based and scanned PDFs.
"""

import os
from typing import List, Dict, Optional, Tuple
from datetime import datetime

try:
    import pymupdf as fitz  # PyMuPDF >= 1.24
except ImportError:
    import fitz  # PyMuPDF legacy
import numpy as np

try:
    from PIL import Image
except ImportError:
    Image = None


class PDFProcessor:
    """Processes PDF documents for text extraction, image extraction, and metadata analysis."""

    def __init__(self, file_path: str) -> None:
        """
        Initialize the PDF processor with a file path.

        Args:
            file_path: Path to the PDF file to process.

        Raises:
            FileNotFoundError: If the PDF file does not exist.
            ValueError: If the file is not a valid PDF.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"PDF file not found: {file_path}")

        self.file_path = file_path
        self.file_size = os.path.getsize(file_path)

        try:
            self._doc = fitz.open(file_path)
        except Exception as e:
            raise ValueError(f"Failed to open PDF file: {e}")

    def __del__(self) -> None:
        """Close the PDF document on cleanup."""
        if hasattr(self, "_doc") and self._doc:
            try:
                self._doc.close()
            except Exception:
                pass

    def extract_text(self) -> str:
        """
        Extract all text from the PDF document.

        Returns:
            Concatenated text from all pages.
        """
        full_text = []
        for page_num in range(len(self._doc)):
            page = self._doc[page_num]
            text = page.get_text("text")
            if text.strip():
                full_text.append(text)
        return "\n".join(full_text)

    def extract_pages(self) -> List[Dict]:
        """
        Extract text from each page individually.

        Returns:
            List of dicts with page_number, text, word_count, and has_images keys.
        """
        pages = []
        for page_num in range(len(self._doc)):
            page = self._doc[page_num]
            text = page.get_text("text")
            image_list = page.get_images(full=True)
            pages.append({
                "page_number": page_num + 1,
                "text": text,
                "word_count": len(text.split()) if text.strip() else 0,
                "has_images": len(image_list) > 0,
                "image_count": len(image_list),
                "width": page.rect.width,
                "height": page.rect.height,
            })
        return pages

    def extract_images(self) -> List:
        """
        Extract embedded images from the PDF.

        Returns:
            List of PIL Image objects extracted from the document.
        """
        if Image is None:
            return []

        images = []
        for page_num in range(len(self._doc)):
            page = self._doc[page_num]
            image_list = page.get_images(full=True)

            for img_index, img_info in enumerate(image_list):
                xref = img_info[0]
                try:
                    base_image = self._doc.extract_image(xref)
                    if base_image:
                        image_bytes = base_image["image"]
                        import io
                        pil_image = Image.open(io.BytesIO(image_bytes))
                        images.append(pil_image)
                except Exception:
                    continue
        return images

    def get_metadata(self) -> Dict:
        """
        Extract metadata from the PDF document.

        Returns:
            Dictionary containing title, author, creation_date, modification_date,
            producer, page_count, file_size, and other metadata fields.
        """
        meta = self._doc.metadata
        metadata = {
            "title": meta.get("title", "") or "",
            "author": meta.get("author", "") or "",
            "subject": meta.get("subject", "") or "",
            "keywords": meta.get("keywords", "") or "",
            "creator": meta.get("creator", "") or "",
            "producer": meta.get("producer", "") or "",
            "creation_date": self._parse_pdf_date(meta.get("creationDate", "")),
            "modification_date": self._parse_pdf_date(meta.get("modDate", "")),
            "page_count": len(self._doc),
            "file_size": self.file_size,
            "file_size_formatted": self._format_size(self.file_size),
            "format": meta.get("format", ""),
            "encryption": meta.get("encryption", ""),
            "is_encrypted": self._doc.is_encrypted,
        }
        return metadata

    def render_page_as_image(self, page_num: int, dpi: int = 200) -> np.ndarray:
        """
        Render a PDF page as an image array suitable for OCR.

        Args:
            page_num: Page number (0-indexed).
            dpi: Resolution for rendering (default 200).

        Returns:
            NumPy array (BGR format) of the rendered page.

        Raises:
            IndexError: If page_num is out of range.
        """
        if page_num < 0 or page_num >= len(self._doc):
            raise IndexError(
                f"Page {page_num} out of range. Document has {len(self._doc)} pages."
            )

        page = self._doc[page_num]
        zoom = dpi / 72.0
        mat = fitz.Matrix(zoom, zoom)
        pixmap = page.get_pixmap(matrix=mat)

        # Convert to numpy array
        img_array = np.frombuffer(pixmap.samples, dtype=np.uint8).reshape(
            pixmap.height, pixmap.width, pixmap.n
        )

        # Convert RGB to BGR for OpenCV compatibility
        if pixmap.n == 4:  # RGBA
            import cv2
            img_array = cv2.cvtColor(img_array, cv2.COLOR_RGBA2BGR)
        elif pixmap.n == 3:  # RGB
            import cv2
            img_array = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)

        return img_array

    def render_all_pages_as_images(self, dpi: int = 200) -> List[np.ndarray]:
        """
        Render all pages as image arrays.

        Args:
            dpi: Resolution for rendering.

        Returns:
            List of NumPy arrays for each page.
        """
        images = []
        for page_num in range(len(self._doc)):
            try:
                img = self.render_page_as_image(page_num, dpi)
                images.append(img)
            except Exception:
                continue
        return images

    def get_page_count(self) -> int:
        """
        Get the total number of pages in the PDF.

        Returns:
            Number of pages.
        """
        return len(self._doc)

    def is_scanned_pdf(self, text_threshold: int = 50) -> bool:
        """
        Determine if the PDF is likely a scanned document (image-based).

        A PDF is considered scanned if it has very little extractable text
        relative to its page count.

        Args:
            text_threshold: Minimum characters per page to consider text-based.

        Returns:
            True if the PDF appears to be scanned, False otherwise.
        """
        total_text = self.extract_text()
        chars_per_page = len(total_text.strip()) / max(len(self._doc), 1)
        return chars_per_page < text_threshold

    def get_text_by_area(self, page_num: int, rect: Tuple[float, float, float, float]) -> str:
        """
        Extract text from a specific rectangular area of a page.

        Args:
            page_num: Page number (0-indexed).
            rect: Tuple of (x0, y0, x1, y1) defining the rectangle.

        Returns:
            Text found within the specified area.
        """
        if page_num < 0 or page_num >= len(self._doc):
            return ""
        page = self._doc[page_num]
        clip_rect = fitz.Rect(rect)
        return page.get_text("text", clip=clip_rect)

    def search_text(self, query: str) -> List[Dict]:
        """
        Search for text across all pages.

        Args:
            query: Text string to search for.

        Returns:
            List of dicts with page_number and instances (list of rects) where found.
        """
        results = []
        for page_num in range(len(self._doc)):
            page = self._doc[page_num]
            instances = page.search_for(query)
            if instances:
                results.append({
                    "page_number": page_num + 1,
                    "instances": [
                        {
                            "x0": inst.x0,
                            "y0": inst.y0,
                            "x1": inst.x1,
                            "y1": inst.y1,
                        }
                        for inst in instances
                    ],
                    "count": len(instances),
                })
        return results

    @staticmethod
    def _parse_pdf_date(date_str: str) -> Optional[str]:
        """
        Parse a PDF date string (D:YYYYMMDDHHmmSS format) to ISO format.

        Args:
            date_str: PDF date string.

        Returns:
            ISO formatted date string or None.
        """
        if not date_str:
            return None
        try:
            # Remove D: prefix and timezone info
            cleaned = date_str.replace("D:", "").split("+")[0].split("-")[0]
            if len(cleaned) >= 8:
                year = cleaned[0:4]
                month = cleaned[4:6] if len(cleaned) >= 6 else "01"
                day = cleaned[6:8] if len(cleaned) >= 8 else "01"
                return f"{year}-{month}-{day}"
        except (ValueError, IndexError):
            pass
        return None

    @staticmethod
    def _format_size(size_bytes: int) -> str:
        """Format bytes into human-readable file size."""
        for unit in ["B", "KB", "MB", "GB"]:
            if size_bytes < 1024:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.1f} TB"
