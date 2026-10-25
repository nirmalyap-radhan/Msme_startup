"""
Document Text Extractor with Scanned Page Detection and Multilingual OCR.
Extracts digital text via PyMuPDF; routes scanned or low-density pages through Tesseract OCR (ori, hin, eng).
Preserves page numbers, section headers, and extraction provenance.
"""

import io
import re
from typing import List, Tuple
from PIL import Image
import pymupdf
import pytesseract

from services.scheme_ingestion.config import ingestion_config
from services.scheme_ingestion.models import ExtractedPassageSchema, SourceDocumentSchema


class ExtractionError(Exception):
    """Raised when document extraction fails."""
    pass


class DocumentExtractor:
    def __init__(self, config=ingestion_config):
        self.config = config

    def is_page_scanned(self, page_text: str, page: pymupdf.Page) -> bool:
        """
        Determines whether a page contains scanned raster content requiring OCR.
        Evaluates character count against threshold and checks for embedded raster images.
        """
        clean_text = page_text.strip()
        char_count = len(clean_text)

        # If page has fewer characters than the threshold, check if images exist
        if char_count < self.config.ocr_char_density_threshold:
            image_list = page.get_images(full=True)
            if len(image_list) > 0 or char_count < 20:
                return True

        return False

    def ocr_page(self, page: pymupdf.Page) -> str:
        """
        Renders a PDF page to a high-resolution pixmap and runs Tesseract OCR
        with configured multilingual language models (Odia, Hindi, English).
        """
        try:
            # Render page at 200 DPI for reliable OCR accuracy
            pix = page.get_pixmap(dpi=200)
            img = Image.open(io.BytesIO(pix.tobytes("png")))
            
            # Run pytesseract with configured languages
            ocr_text = pytesseract.image_to_string(
                img,
                lang=self.config.tesseract_lang_string,
                config="--psm 1"  # Automatic page segmentation with OSD
            )
            return ocr_text.strip()
        except Exception as e:
            # Fallback to single text line or default psm if psm 1 fails
            try:
                pix = page.get_pixmap(dpi=150)
                img = Image.open(io.BytesIO(pix.tobytes("png")))
                return pytesseract.image_to_string(img, lang="eng").strip()
            except Exception:
                return ""

    def detect_section_heading(self, page_text: str) -> str:
        """
        Heuristic detector for section or clause headings in official policy documents.
        """
        lines = [line.strip() for line in page_text.split("\n") if line.strip()]
        for line in lines[:5]:
            # Common patterns in Odisha/Central policies
            if re.match(r"^(Clause|Section|Chapter|Rule|Paragraph|Policy|Part)\s+[\dIVX\.\(\)]+", line, re.I):
                return line[:120]
            if line.isupper() and len(line) < 80 and not line.isdigit():
                return line[:120]
        return ""

    def extract_document(
        self,
        doc_schema: SourceDocumentSchema
    ) -> Tuple[SourceDocumentSchema, List[ExtractedPassageSchema]]:
        """
        Processes a PDF document page-by-page, extracting text and applying OCR where necessary.
        Returns the updated document schema and an ordered list of ExtractedPassageSchema objects.
        """
        try:
            pdf = pymupdf.open(doc_schema.local_path)
        except Exception as e:
            raise ExtractionError(f"Cannot open PDF file at '{doc_schema.local_path}': {str(e)}") from e

        passages: List[ExtractedPassageSchema] = []
        page_count = len(pdf)
        scanned_page_count = 0
        ocr_applied = False

        for page_idx in range(page_count):
            page_num = page_idx + 1
            page = pdf[page_idx]

            # 1. Attempt digital text extraction
            digital_text = page.get_text("text").strip()
            is_scanned = self.is_page_scanned(digital_text, page)

            if is_scanned:
                scanned_page_count += 1
                ocr_text = self.ocr_page(page)
                # Combine or use OCR text if digital text is negligible
                final_text = ocr_text if len(ocr_text) > len(digital_text) else digital_text
                is_ocr_flag = True
                ocr_applied = True
            else:
                final_text = digital_text
                is_ocr_flag = False

            heading = self.detect_section_heading(final_text)

            passage = ExtractedPassageSchema(
                document_id=doc_schema.document_id,
                page_number=page_num,
                section_heading=heading or f"Page {page_num}",
                text_content=final_text,
                character_count=len(final_text),
                is_ocr=is_ocr_flag,
            )
            passages.append(passage)

        pdf.close()

        # Update document schema with verified statistics
        doc_schema.page_count = page_count
        doc_schema.is_scanned = (scanned_page_count > (page_count / 2))
        doc_schema.ocr_applied = ocr_applied

        return doc_schema, passages
