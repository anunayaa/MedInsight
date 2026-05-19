"""
OCR Engine — Extracts text from PDF and image lab reports.

Supports:
- PyMuPDF (fitz) for native PDF text extraction
- pdf2image + pytesseract fallback for scanned PDFs
- PIL + pytesseract for image files
"""

import os
import io
import logging
from pathlib import Path
from typing import Dict, Any, Optional

import fitz  # PyMuPDF
from PIL import Image, ImageFilter, ImageEnhance
import pytesseract

logger = logging.getLogger(__name__)

# Allow override of Tesseract path via env var (Windows)
tesseract_cmd = os.getenv("TESSERACT_CMD")
if tesseract_cmd:
    pytesseract.pytesseract.tesseract_cmd = tesseract_cmd

# Poppler path for pdf2image (Windows)
POPPLER_PATH = os.getenv("POPPLER_PATH", None)


class OCREngine:
    """Handles text extraction from PDF and image lab reports."""

    SUPPORTED_IMAGE_FORMATS = {".png", ".jpg", ".jpeg", ".tiff", ".tif", ".bmp", ".webp"}
    SUPPORTED_PDF_FORMAT = {".pdf"}
    MIN_TEXT_LENGTH = 50  # chars — below this we assume scanned/image-based PDF

    def extract(self, file_bytes: bytes, filename: str) -> Dict[str, Any]:
        """
        Main entry point. Routes to PDF or image extractor based on extension.

        Args:
            file_bytes: Raw file bytes
            filename: Original filename (used to detect extension)

        Returns:
            dict with keys: raw_text, page_count, method, confidence, error
        """
        ext = Path(filename).suffix.lower()

        try:
            if ext in self.SUPPORTED_PDF_FORMAT:
                return self._extract_pdf(file_bytes, filename)
            elif ext in self.SUPPORTED_IMAGE_FORMATS:
                return self._extract_image(file_bytes, filename)
            else:
                return self._error_result(f"Unsupported file format: {ext}")
        except Exception as e:
            logger.exception(f"OCR extraction failed for {filename}")
            return self._error_result(str(e))

    # ─────────────────────────────────────────────
    # PDF Extraction
    # ─────────────────────────────────────────────

    def _extract_pdf(self, file_bytes: bytes, filename: str) -> Dict[str, Any]:
        """Try native text extraction; fall back to OCR for scanned PDFs."""
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        page_count = len(doc)

        # Attempt native text extraction first (fast, accurate for digital PDFs)
        full_text = ""
        for page in doc:
            full_text += page.get_text("text") + "\n"

        doc.close()

        if len(full_text.strip()) >= self.MIN_TEXT_LENGTH:
            logger.info(f"PDF native extraction: {len(full_text)} chars from {page_count} pages")
            return {
                "raw_text": full_text.strip(),
                "page_count": page_count,
                "method": "pymupdf_native",
                "confidence": 99,
                "error": None,
            }

        # Fallback: render pages to images and run Tesseract OCR
        logger.info("PDF appears scanned — falling back to OCR")
        return self._extract_pdf_via_ocr(file_bytes, page_count)

    def _extract_pdf_via_ocr(self, file_bytes: bytes, page_count: int) -> Dict[str, Any]:
        """Render PDF pages to images and OCR each one."""
        try:
            from pdf2image import convert_from_bytes

            kwargs = {"dpi": 300}
            if POPPLER_PATH:
                kwargs["poppler_path"] = POPPLER_PATH

            images = convert_from_bytes(file_bytes, **kwargs)
            all_text = ""
            confidences = []

            for img in images:
                preprocessed = self._preprocess_image(img)
                data = pytesseract.image_to_data(
                    preprocessed,
                    output_type=pytesseract.Output.DICT,
                    config="--psm 6",
                )
                text = pytesseract.image_to_string(preprocessed, config="--psm 6")
                all_text += text + "\n"

                # Calculate average confidence for non-empty words
                page_confs = [int(c) for c, w in zip(data["conf"], data["text"])
                              if w.strip() and int(c) >= 0]
                if page_confs:
                    confidences.append(sum(page_confs) / len(page_confs))

            avg_conf = round(sum(confidences) / len(confidences), 1) if confidences else 0

            return {
                "raw_text": all_text.strip(),
                "page_count": page_count,
                "method": "tesseract_pdf_ocr",
                "confidence": avg_conf,
                "error": None,
            }

        except ImportError:
            return self._error_result(
                "pdf2image not installed or Poppler not found. "
                "Install Poppler and set POPPLER_PATH in .env"
            )
        except Exception as e:
            logger.exception("PDF OCR fallback failed")
            return self._error_result(str(e))

    # ─────────────────────────────────────────────
    # Image Extraction
    # ─────────────────────────────────────────────

    def _extract_image(self, file_bytes: bytes, filename: str) -> Dict[str, Any]:
        """OCR a single image file."""
        try:
            img = Image.open(io.BytesIO(file_bytes))
            preprocessed = self._preprocess_image(img)

            data = pytesseract.image_to_data(
                preprocessed,
                output_type=pytesseract.Output.DICT,
                config="--psm 6",
            )
            text = pytesseract.image_to_string(preprocessed, config="--psm 6")

            page_confs = [int(c) for c, w in zip(data["conf"], data["text"])
                          if w.strip() and int(c) >= 0]
            avg_conf = round(sum(page_confs) / len(page_confs), 1) if page_confs else 0

            logger.info(f"Image OCR: {len(text)} chars, confidence {avg_conf}%")

            return {
                "raw_text": text.strip(),
                "page_count": 1,
                "method": "tesseract_image",
                "confidence": avg_conf,
                "error": None,
            }

        except Exception as e:
            logger.exception(f"Image OCR failed for {filename}")
            return self._error_result(str(e))

    # ─────────────────────────────────────────────
    # Image Preprocessing
    # ─────────────────────────────────────────────

    def _preprocess_image(self, img: Image.Image) -> Image.Image:
        """
        Enhance image quality for better OCR accuracy:
        1. Convert to grayscale
        2. Boost contrast
        3. Sharpen edges
        4. Upscale if small
        """
        # Convert to grayscale
        if img.mode != "L":
            img = img.convert("L")

        # Upscale small images (DPI too low)
        w, h = img.size
        if w < 1200 or h < 1600:
            scale = max(1200 / w, 1600 / h)
            img = img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)

        # Enhance contrast
        img = ImageEnhance.Contrast(img).enhance(2.0)

        # Sharpen
        img = img.filter(ImageFilter.SHARPEN)

        return img

    # ─────────────────────────────────────────────
    # Helpers
    # ─────────────────────────────────────────────

    @staticmethod
    def _error_result(message: str) -> Dict[str, Any]:
        return {
            "raw_text": "",
            "page_count": 0,
            "method": "failed",
            "confidence": 0,
            "error": message,
        }

    @staticmethod
    def is_supported_file(filename: str) -> bool:
        """Return True if the file extension is supported."""
        ext = Path(filename).suffix.lower()
        return ext in OCREngine.SUPPORTED_PDF_FORMAT | OCREngine.SUPPORTED_IMAGE_FORMATS
