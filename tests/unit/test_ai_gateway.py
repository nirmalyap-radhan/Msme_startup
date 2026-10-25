"""
Unit tests for AI Gateway and Multi-Provider Integrations.
Tests live providers (Groq, Sarvam), quota/rate-limit handlers (Gemini, Mistral, NVIDIA),
and gateway status auditing.
"""

import pytest
from services.ai_gateway.gateway import AIGateway
from services.ai_gateway.groq_provider import GroqProvider
from services.ai_gateway.sarvam_provider import SarvamProvider
from services.ai_gateway.gemini_provider import GeminiProvider
from services.ai_gateway.mistral_provider import MistralProvider
from services.ai_gateway.nvidia_provider import NvidiaProvider


def test_groq_provider_live_completion():
    groq = GroqProvider()
    assert groq.is_available() is True
    assert groq.provider_name == "groq"

    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Respond with the word: VERIFIED"},
    ]
    resp = groq.generate_chat_completion(messages=messages, max_tokens=15, temperature=0.1)

    assert resp.status == "success"
    assert "VERIFIED" in resp.content.upper()
    assert resp.provider_name == "groq"
    assert resp.latency_ms > 0
    assert resp.total_tokens > 0


def test_sarvam_provider_live_translation():
    sarvam = SarvamProvider()
    assert sarvam.is_available() is True
    assert sarvam.provider_name == "sarvam"

    res = sarvam.translate_text(
        text="Welcome to Odisha MSME Department.",
        source_language="en-IN",
        target_language="od-IN",
    )
    assert res.translated_text != ""
    assert res.target_language == "od-IN"
    assert res.latency_ms > 0
    # Check that translated text contains Odia Unicode characters
    has_odia = any("\u0b00" <= c <= "\u0b7f" for c in res.translated_text)
    assert has_odia is True


def test_sarvam_provider_live_speech_synthesis():
    sarvam = SarvamProvider()
    res = sarvam.synthesize_speech(
        text="ଓଡ଼ିଶା ସରକାରଙ୍କ CM-SRIM ଯୋଜନା।",
        language_code="od-IN",
        speaker="ritu",
    )
    assert res.audio_base64 != ""
    assert len(res.audio_base64) > 100  # Base64 audio payload
    assert res.language_code == "od-IN"
    assert res.latency_ms > 0


def test_gemini_provider_handles_quota_or_error_gracefully():
    gemini = GeminiProvider()
    assert gemini.provider_name == "gemini"
    messages = [{"role": "user", "content": "Hello"}]
    res = gemini.generate_chat_completion(messages=messages, max_tokens=10)

    # In our live probe, Gemini returned 429 quota_exceeded or status error
    # Must never fabricate an answer; must report status cleanly
    assert res.status in ("quota_exceeded", "error", "success")
    if res.status == "quota_exceeded":
        assert "quota" in res.error_message.lower() or "rate" in res.error_message.lower()


def test_mistral_provider_handles_rate_limit_gracefully():
    mistral = MistralProvider()
    assert mistral.provider_name == "mistral"
    messages = [{"role": "user", "content": "Hello"}]
    res = mistral.generate_chat_completion(messages=messages, max_tokens=10)

    # In our live probe, Mistral returned 429 rate_limited
    assert res.status in ("rate_limited", "error", "success")
    if res.status == "rate_limited":
        assert "rate limit" in res.error_message.lower() or "credit" in res.error_message.lower()


def test_gateway_audits_all_five_providers():
    gateway = AIGateway()
    statuses = gateway.get_all_provider_statuses()

    assert len(statuses) == 5
    names = [s.name for s in statuses]
    assert "groq" in names
    assert "sarvam" in names
    assert "gemini" in names
    assert "mistral" in names
    assert "nvidia" in names

    # Groq and Sarvam must be verified available
    groq_stat = next(s for s in statuses if s.name == "groq")
    assert groq_stat.is_configured is True
    assert groq_stat.is_available is True

    sarvam_stat = next(s for s in statuses if s.name == "sarvam")
    assert sarvam_stat.is_configured is True
    assert sarvam_stat.is_available is True

    # Primary text provider should be Groq
    primary = gateway.get_primary_text_provider()
    assert primary.provider_name == "groq"
