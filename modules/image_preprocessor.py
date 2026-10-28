"""
Image Preprocessing Module using OpenCV.

Provides image enhancement and preprocessing functions
to improve OCR accuracy on document images.
"""

from typing import List, Tuple, Optional

import cv2
import numpy as np


class ImagePreprocessor:
    """Preprocesses document images to improve OCR text extraction quality."""

    def __init__(self) -> None:
        """Initialize the image preprocessor."""
        pass

    def preprocess_for_ocr(self, image: np.ndarray) -> np.ndarray:
        """
        Apply a full preprocessing pipeline optimized for OCR.

        Pipeline: grayscale → denoise → enhance contrast → deskew → adaptive threshold.

        Args:
            image: Input image as a NumPy array (BGR or grayscale).

        Returns:
            Preprocessed binary image ready for OCR.
        """
        if image is None or image.size == 0:
            raise ValueError("Input image is empty or None")

        # Convert to grayscale if needed
        processed = self.to_grayscale(image)

        # Denoise
        processed = self.denoise(processed)

        # Enhance contrast
        processed = self.enhance_contrast(processed)

        # Deskew
        processed = self.deskew(processed)

        # Adaptive thresholding for clean binary output
        processed = self.adaptive_threshold(processed)

        return processed

    def to_grayscale(self, image: np.ndarray) -> np.ndarray:
        """
        Convert an image to grayscale.

        Args:
            image: Input image (BGR or already grayscale).

        Returns:
            Grayscale image.
        """
        if len(image.shape) == 2:
            return image
        if image.shape[2] == 4:
            return cv2.cvtColor(image, cv2.COLOR_BGRA2GRAY)
        return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    def denoise(self, image: np.ndarray) -> np.ndarray:
        """
        Remove noise from a grayscale image using Non-Local Means Denoising.

        Args:
            image: Grayscale input image.

        Returns:
            Denoised image.
        """
        if len(image.shape) == 3:
            return cv2.fastNlMeansDenoisingColored(image, None, 10, 10, 7, 21)
        return cv2.fastNlMeansDenoising(image, None, 10, 7, 21)

    def deskew(self, image: np.ndarray) -> np.ndarray:
        """
        Detect and correct skew angle in a document image.

        Uses the Hough Line Transform to detect dominant line angles
        and rotates the image to correct skew.

        Args:
            image: Grayscale input image.

        Returns:
            Deskewed image.
        """
        # Ensure grayscale
        if len(image.shape) == 3:
            gray = self.to_grayscale(image)
        else:
            gray = image.copy()

        # Detect edges
        edges = cv2.Canny(gray, 50, 150, apertureSize=3)

        # Detect lines using Hough Transform
        lines = cv2.HoughLinesP(
            edges, 1, np.pi / 180, threshold=100,
            minLineLength=gray.shape[1] // 4,
            maxLineGap=10
        )

        if lines is None or len(lines) == 0:
            return image

        # Calculate angles of detected lines
        angles = []
        for line in lines:
            x1, y1, x2, y2 = line[0]
            if x2 - x1 == 0:
                continue
            angle = np.degrees(np.arctan2(y2 - y1, x2 - x1))
            # Only consider near-horizontal lines (within ±30 degrees)
            if abs(angle) < 30:
                angles.append(angle)

        if not angles:
            return image

        # Use the median angle for robustness
        median_angle = np.median(angles)

        # Only deskew if the angle is significant (> 0.5 degrees)
        if abs(median_angle) < 0.5:
            return image

        # Rotate image to correct skew
        h, w = image.shape[:2]
        center = (w // 2, h // 2)
        rotation_matrix = cv2.getRotationMatrix2D(center, median_angle, 1.0)
        rotated = cv2.warpAffine(
            image, rotation_matrix, (w, h),
            flags=cv2.INTER_CUBIC,
            borderMode=cv2.BORDER_REPLICATE
        )
        return rotated

    def adaptive_threshold(self, image: np.ndarray) -> np.ndarray:
        """
        Apply adaptive thresholding to create a clean binary image.

        Args:
            image: Grayscale input image.

        Returns:
            Binary (thresholded) image.
        """
        if len(image.shape) == 3:
            image = self.to_grayscale(image)

        return cv2.adaptiveThreshold(
            image, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY, 11, 2
        )

    def resize_for_ocr(self, image: np.ndarray, target_dpi: int = 300) -> np.ndarray:
        """
        Resize image to achieve a target DPI for optimal OCR.

        Assumes the original image is at 72 DPI (standard screen resolution).

        Args:
            image: Input image.
            target_dpi: Desired DPI (default 300).

        Returns:
            Resized image.
        """
        scale_factor = target_dpi / 72.0
        h, w = image.shape[:2]
        new_w = int(w * scale_factor)
        new_h = int(h * scale_factor)

        return cv2.resize(
            image, (new_w, new_h),
            interpolation=cv2.INTER_CUBIC
        )

    def enhance_contrast(self, image: np.ndarray) -> np.ndarray:
        """
        Enhance image contrast using CLAHE (Contrast Limited Adaptive Histogram Equalization).

        Args:
            image: Grayscale input image.

        Returns:
            Contrast-enhanced image.
        """
        if len(image.shape) == 3:
            image = self.to_grayscale(image)

        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        return clahe.apply(image)

    def remove_borders(self, image: np.ndarray, border_size: int = 10) -> np.ndarray:
        """
        Remove dark borders from a document image.

        Detects and crops out the dark border areas that often appear in scanned documents.

        Args:
            image: Input image.
            border_size: Minimum border size to consider (pixels).

        Returns:
            Cropped image with borders removed.
        """
        if len(image.shape) == 3:
            gray = self.to_grayscale(image)
        else:
            gray = image.copy()

        # Threshold to find content area
        _, thresh = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY)

        # Find contours
        contours, _ = cv2.findContours(
            thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )

        if not contours:
            return image

        # Find the largest contour (assumed to be the document content)
        largest_contour = max(contours, key=cv2.contourArea)
        x, y, w, h = cv2.boundingRect(largest_contour)

        # Add small padding
        padding = 5
        x = max(0, x - padding)
        y = max(0, y - padding)
        w = min(image.shape[1] - x, w + 2 * padding)
        h = min(image.shape[0] - y, h + 2 * padding)

        return image[y:y + h, x:x + w]

    def detect_text_regions(self, image: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """
        Detect regions in the image that likely contain text.

        Uses morphological operations to find text blocks.

        Args:
            image: Input image.

        Returns:
            List of bounding boxes (x, y, w, h) for detected text regions.
        """
        if len(image.shape) == 3:
            gray = self.to_grayscale(image)
        else:
            gray = image.copy()

        # Apply threshold
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

        # Dilate to merge nearby text into blocks
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (15, 3))
        dilated = cv2.dilate(binary, kernel, iterations=2)

        # Find contours of text blocks
        contours, _ = cv2.findContours(
            dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )

        # Filter and sort bounding boxes
        regions = []
        min_area = 500  # Minimum area to be considered a text region
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            area = w * h
            if area > min_area and w > 20 and h > 10:
                regions.append((x, y, w, h))

        # Sort by vertical position (top to bottom), then horizontal (left to right)
        regions.sort(key=lambda r: (r[1], r[0]))
        return regions

    def sharpen(self, image: np.ndarray) -> np.ndarray:
        """
        Sharpen an image to make text edges more defined.

        Args:
            image: Input image.

        Returns:
            Sharpened image.
        """
        kernel = np.array([
            [0, -1, 0],
            [-1, 5, -1],
            [0, -1, 0]
        ])
        return cv2.filter2D(image, -1, kernel)

    def morphological_cleanup(self, image: np.ndarray) -> np.ndarray:
        """
        Apply morphological opening to remove small noise spots.

        Args:
            image: Binary input image.

        Returns:
            Cleaned binary image.
        """
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
        cleaned = cv2.morphologyEx(image, cv2.MORPH_OPEN, kernel, iterations=1)
        return cleaned
