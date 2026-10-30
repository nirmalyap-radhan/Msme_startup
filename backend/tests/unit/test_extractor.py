"""
Unit tests for Document Extractor and Scanned Page OCR routing.
"""

import os
import tempfile
import pytest
import pymupdf

from services.scheme_ingestion.extractor import DocumentExtractor
from services.scheme_ingestion.models import SourceDocumentSchema
from services.scheme_ingestion.config import IngestionConfig


@pytest.fixture
def sample_pdf():
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
        pdf_path = f.name

    doc = pymupdf.open()
    # Page 1: Digital text with section heading
    page1 = doc.new_page()
    page1.insert_text(
        (50, 72),
        "Clause 1.0 General Provisions\n"
        "Government of Odisha, Department of MSME.\n"
        "This policy is introduced to accelerate industrial growth across Odisha.\n"
        "Udyam registration is mandatory for all participating MSMEs."
    )

    # Page 2: Digital text with eligibility clauses
    page2 = doc.new_page()
    page2.insert_text(
        (50, 72),
        "Clause 4.2 Eligibility Criteria\n"
        "All Micro and Small Enterprises engaged in Manufacturing and Agro-processing sectors\n"
        "having commenced commercial production within Odisha are eligible."
    )

    doc.save(pdf_path)
    doc.close()

    yield pdf_path

    if os.path.exists(pdf_path):
        os.remove(pdf_path)


def test_digital_pdf_extraction(sample_pdf):
    extractor = DocumentExtractor()
    doc_schema = SourceDocumentSchema(
        title="Sample Odisha Policy",
        source_url="https://msme.odisha.gov.in/policy.pdf",
        local_path=sample_pdf,
        sha256_hash="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        file_size_bytes=os.path.getsize(sample_pdf),
    )

    updated_doc, passages = extractor.extract_document(doc_schema)

    assert updated_doc.page_count == 2
    assert updated_doc.is_scanned is False
    assert len(passages) == 2

    # Verify Page 1
    assert passages[0].page_number == 1
    assert "General Provisions" in passages[0].section_heading or "Clause 1.0" in passages[0].section_heading
    assert "Udyam registration is mandatory" in passages[0].text_content
    assert passages[0].is_ocr is False

    # Verify Page 2
    assert passages[1].page_number == 2
    assert "Eligibility Criteria" in passages[1].section_heading or "Clause 4.2" in passages[1].section_heading
    assert "Micro and Small Enterprises" in passages[1].text_content
    assert passages[1].is_ocr is False


def test_heading_detector():
    extractor = DocumentExtractor()
    assert extractor.detect_section_heading("Clause 3.1 Capital Subsidy Provisions\nDetails follow") == "Clause 3.1 Capital Subsidy Provisions"
    assert extractor.detect_section_heading("SECTION 5: ELIGIBILITY CONDITIONS\nBody text") == "SECTION 5: ELIGIBILITY CONDITIONS"
    assert extractor.detect_section_heading("Standard paragraph without clause heading") == ""
