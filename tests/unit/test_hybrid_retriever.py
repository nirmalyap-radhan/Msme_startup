"""
Unit tests for Hybrid Scheme Document Retriever.
Tests BM25 lexical ranking on verified government documents,
metadata preservation, OCR tracking, filtering, and insufficient evidence gating.
"""

import pytest
from services.rag.retriever import HybridSchemeRetriever


def test_retrieve_cm_srim_interest_subvention():
    retriever = HybridSchemeRetriever()
    passages, has_sufficient_evidence = retriever.retrieve(
        query="What is the interest reimbursement on working capital loans under CM-SRIM?",
        top_k=3
    )

    assert has_sufficient_evidence is True
    assert len(passages) > 0
    assert len(passages) <= 3

    top = passages[0]
    assert top.scheme_id == "OD-MSME-C0B98FA5"
    assert "CHIEF MINISTER" in top.scheme_name or "CM-SRIM" in top.text_content
    assert top.page_number >= 1
    assert top.source_url.startswith("https://msme.odisha.gov.in")
    assert len(top.document_sha256) == 64
    assert top.score > 0.5


def test_retrieve_trademark_assistance():
    retriever = HybridSchemeRetriever()
    passages, has_sufficient_evidence = retriever.retrieve(
        query="reimbursement of expenditure incurred for registration of Trade Mark OMSMED",
        top_k=3
    )

    assert has_sufficient_evidence is True
    assert len(passages) > 0

    top = passages[0]
    assert top.scheme_id == "OD-MSME-AFD17307"
    assert "Trade Mark" in top.scheme_name or "trade mark" in top.text_content.lower()
    assert top.page_number >= 1
    # Trade Mark assistance notification is scanned and was OCR-processed
    assert top.is_ocr is True


def test_retrieve_unrelated_query_returns_insufficient_evidence():
    retriever = HybridSchemeRetriever()
    passages, has_sufficient_evidence = retriever.retrieve(
        query="cryptocurrency mining bitcoin proof-of-work hash rate rewards",
        top_k=3
    )
    # Must reject and flag insufficient evidence to prevent hallucination
    assert has_sufficient_evidence is False


def test_retrieve_with_scheme_id_filter():
    retriever = HybridSchemeRetriever()
    # Ask about trademark, but filter strictly to CM-SRIM scheme
    passages, _ = retriever.retrieve(
        query="assistance and guidelines",
        scheme_id="OD-MSME-C0B98FA5",
        top_k=4
    )
    for p in passages:
        assert p.scheme_id == "OD-MSME-C0B98FA5"


def test_empty_or_whitespace_query():
    retriever = HybridSchemeRetriever()
    passages, has_sufficient_evidence = retriever.retrieve(query="   ", top_k=3)
    assert passages == []
    assert has_sufficient_evidence is False
