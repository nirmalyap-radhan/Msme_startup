"""
Integration tests for RAG and AI Assistant REST endpoints.
Tests /api/v1/rag/ask, /api/v1/rag/providers, and /api/v1/rag/voice/synthesize.
"""

import pytest
from fastapi.testclient import TestClient
from apps.api.main import app

client = TestClient(app)


def test_api_rag_providers_audit():
    res = client.get("/api/v1/rag/providers")
    assert res.status_code == 200
    providers = res.json()
    assert isinstance(providers, list)
    assert len(providers) == 5

    names = [p["name"] for p in providers]
    assert "groq" in names
    assert "sarvam" in names
    assert "gemini" in names
    assert "mistral" in names
    assert "nvidia" in names

    groq_p = next(p for p in providers if p["name"] == "groq")
    assert groq_p["is_configured"] is True
    assert groq_p["is_available"] is True
    assert "qwen" in groq_p["preferred_model"]

    sarvam_p = next(p for p in providers if p["name"] == "sarvam")
    assert sarvam_p["is_configured"] is True
    assert sarvam_p["is_available"] is True


def test_api_rag_ask_grounded_question():
    payload = {
        "scheme_id": "OD-MSME-AFD17307",
        "query": "What is the reimbursement limit under the Trade Mark assistance scheme?",
        "top_k": 3,
        "target_language": "en",
    }
    res = client.post("/api/v1/rag/ask", json=payload)
    assert res.status_code == 200
    data = res.json()

    assert data["has_sufficient_evidence"] is True
    assert data["provider_used"] == "groq"
    assert len(data["citations"]) > 0
    assert len(data["passages_retrieved"]) > 0

    first_cit = data["citations"][0]
    assert first_cit["scheme_id"] == "OD-MSME-AFD17307"
    assert first_cit["page_number"] >= 1
    assert len(first_cit["document_sha256"]) == 64


def test_api_rag_ask_insufficient_evidence():
    payload = {
        "query": "Where can I register for orbital space satellite launch subsidies in Cuttack?",
        "top_k": 3,
        "target_language": "en",
    }
    res = client.post("/api/v1/rag/ask", json=payload)
    assert res.status_code == 200
    data = res.json()

    assert data["has_sufficient_evidence"] is False
    assert data["citations"] == []
    assert "could not be verified" in data["answer"].lower()
    assert "https://msme.odisha.gov.in" in data["answer"]


def test_api_voice_synthesize_odia():
    payload = {
        "text": "ଓଡ଼ିଶା MSME ଯୋଜନା ବିବରଣୀ।",
        "language_code": "od-IN",
        "speaker": "ritu",
    }
    res = client.post("/api/v1/rag/voice/synthesize", json=payload)
    assert res.status_code == 200
    data = res.json()

    assert data["provider_name"] == "sarvam"
    assert data["audio_base64"] != ""
    assert len(data["audio_base64"]) > 50
    assert data["latency_ms"] > 0
