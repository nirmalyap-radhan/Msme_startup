"""
Unit tests for Scheme Normalizer and Structured Rule Extraction.
"""

import pytest
from services.scheme_ingestion.models import ExtractedPassageSchema, SourceDocumentSchema
from services.scheme_ingestion.normalizer import SchemeNormalizer


def test_currency_parser():
    normalizer = SchemeNormalizer()

    # Crores
    assert normalizer.parse_currency_amount("subsidy up to Rs. 2.5 Crore") == 25000000.0
    assert normalizer.parse_currency_amount("maximum limit of 1 Crore") == 10000000.0

    # Lakhs
    assert normalizer.parse_currency_amount("financial assistance of Rs. 50 Lakh") == 5000000.0
    assert normalizer.parse_currency_amount("reimbursement up to 10 Lakhs") == 1000000.0
    assert normalizer.parse_currency_amount("ceiling of Rs. 2.5 Lac") == 250000.0

    # Thousands
    assert normalizer.parse_currency_amount("fee of Rs. 25,000") == 25000.0
    assert normalizer.parse_currency_amount("grant of ₹50,000") == 50000.0


def test_percentage_parser():
    normalizer = SchemeNormalizer()

    assert normalizer.parse_percentage("subsidy at 50% of the cost") == 50.0
    assert normalizer.parse_percentage("interest subvention of 5%") == 5.0
    assert normalizer.parse_percentage("75.5% assistance") == 75.5
    assert normalizer.parse_percentage("invalid 150% rate") is None


def test_date_parser():
    normalizer = SchemeNormalizer()

    eff, exp = normalizer.extract_dates(
        "Notification comes into force with effect from 01.04.2022 and shall remain in force till 31.03.2027."
    )
    assert eff == "01.04.2022"
    assert exp == "31.03.2027"


def test_structured_eligibility_extraction():
    normalizer = SchemeNormalizer()

    passages = [
        ExtractedPassageSchema(
            document_id="doc-1",
            page_number=3,
            section_heading="Clause 4.1",
            text_content=(
                "Clause 4.1 Eligibility Criteria:\n"
                "All Micro and Small Enterprises situated in Odisha holding a valid Udyam Registration\n"
                "and operating in Manufacturing and Agro-processing sectors are eligible."
            ),
            character_count=210,
        )
    ]

    conditions = normalizer.extract_candidate_eligibility(passages)
    assert len(conditions) >= 3

    attrs = {c.attribute_name: c for c in conditions}

    assert "enterprise_class" in attrs
    assert attrs["enterprise_class"].operator == "IN"
    assert "micro" in attrs["enterprise_class"].value
    assert "small" in attrs["enterprise_class"].value
    assert attrs["enterprise_class"].source_clause == "Clause 4.1"
    assert attrs["enterprise_class"].source_page == 3

    assert "udyam_registered" in attrs
    assert attrs["udyam_registered"].value is True

    assert "state" in attrs
    assert attrs["state"].value == "Odisha"


def test_structured_benefits_extraction():
    normalizer = SchemeNormalizer()

    passages = [
        ExtractedPassageSchema(
            document_id="doc-1",
            page_number=5,
            section_heading="Clause 6.2",
            text_content=(
                "Clause 6.2 Capital Investment Subsidy:\n"
                "Eligible units shall be granted capital subsidy at 30% of investment\n"
                "in plant and machinery subject to a maximum limit of Rs. 50 Lakh."
            ),
            character_count=180,
        )
    ]

    benefits = normalizer.extract_candidate_benefits(passages)
    assert len(benefits) >= 1

    ben = benefits[0]
    assert ben.subsidy_percentage == 30.0
    assert ben.max_limit_inr == 5000000.0
    assert ben.source_clause == "Clause 6.2"
    assert ben.source_page == 5


def test_document_checklist_extraction():
    normalizer = SchemeNormalizer()

    passages = [
        ExtractedPassageSchema(
            document_id="doc-1",
            page_number=8,
            section_heading="Annexure-II",
            text_content=(
                "List of enclosures:\n"
                "1. Self-attested copy of Udyam Registration Certificate.\n"
                "2. Detailed Project Report (DPR) approved by financing bank.\n"
                "3. Copy of Term Loan Sanction Letter.\n"
                "4. CA Certificate verifying plant and machinery investment."
            ),
            character_count=240,
        )
    ]

    docs = normalizer.extract_required_documents(passages)
    assert "Udyam Registration Certificate" in docs
    assert "Detailed Project Report (DPR)" in docs
    assert "Term Loan / Bank Sanction Letter" in docs
    assert "Statutory Auditor / Chartered Accountant Certificate" in docs
