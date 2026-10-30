"""
Sarvam AI Provider Integration.
Indian language translation and voice synthesis adapter, specialized in Odia (od-IN) and Hindi (hi-IN).
"""

import os
import time
from typing import Any, Dict, List, Optional
import httpx
from dotenv import load_dotenv

load_dotenv()

from services.ai_gateway.base import (
    AudioSynthesisResponse,
    BaseAIProvider,
    ProviderResponse,
    TranslationResponse,
)


class SarvamProvider(BaseAIProvider):
    BASE_URL = "https://api.sarvam.ai"
    TTS_MODEL = "bulbul:v3"
    DEFAULT_SPEAKER = "ritu"

    def __init__(self, api_key: Optional[str] = None):
        self._api_key = api_key or os.getenv("SARVAM_API_KEY", "")

    @property
    def provider_name(self) -> str:
        return "sarvam"

    def is_available(self) -> bool:
        if not self._api_key or self._api_key.startswith("your_"):
            return False
        try:
            # Probe with a fast translation check
            res = self.translate_text(
                text="Test",
                source_language="en-IN",
                target_language="od-IN",
                timeout_seconds=5.0
            )
            return bool(res.translated_text)
        except Exception:
            return False

    def generate_chat_completion(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = 1024,
        temperature: float = 0.2,
        model: Optional[str] = None,
        timeout_seconds: float = 15.0,
    ) -> ProviderResponse:
        """Sarvam specializes in translation and speech in this platform; generation deferred to Groq."""
        return ProviderResponse(
            content="",
            provider_name=self.provider_name,
            model_name="sarvam-language",
            status="error",
            error_message="Sarvam AI is configured for Translation and TTS. Text generation is routed through Groq.",
        )

    def translate_text(
        self,
        text: str,
        source_language: str = "en-IN",
        target_language: str = "od-IN",
        timeout_seconds: float = 10.0,
    ) -> TranslationResponse:
        start_time = time.time()
        if not self._api_key:
            raise ValueError("SARVAM_API_KEY is not configured.")

        url = f"{self.BASE_URL}/translate"
        headers = {
            "api-subscription-key": self._api_key,
            "Content-Type": "application/json",
        }
        payload = {
            "input": text,
            "source_language_code": source_language,
            "target_language_code": target_language,
            "speaker_gender": "Female",
            "mode": "formal",
        }

        resp = httpx.post(url, headers=headers, json=payload, timeout=timeout_seconds)
        latency = (time.time() - start_time) * 1000.0

        if resp.status_code == 200:
            data = resp.json()
            translated = data.get("translated_text", "")
            req_id = data.get("request_id")
            return TranslationResponse(
                original_text=text,
                translated_text=translated,
                source_language=source_language,
                target_language=target_language,
                provider_name=self.provider_name,
                latency_ms=latency,
                request_id=req_id,
            )
        else:
            raise RuntimeError(f"Sarvam translation failed ({resp.status_code}): {resp.text}")

    def synthesize_speech(
        self,
        text: str,
        language_code: str = "od-IN",
        speaker: str = "ritu",
        timeout_seconds: float = 15.0,
    ) -> AudioSynthesisResponse:
        start_time = time.time()
        if not self._api_key:
            raise ValueError("SARVAM_API_KEY is not configured.")

        url = f"{self.BASE_URL}/text-to-speech"
        headers = {
            "api-subscription-key": self._api_key,
            "Content-Type": "application/json",
        }
        payload = {
            "inputs": [text],
            "target_language_code": language_code,
            "speaker": speaker or self.DEFAULT_SPEAKER,
            "model": self.TTS_MODEL,
        }

        resp = httpx.post(url, headers=headers, json=payload, timeout=timeout_seconds)
        latency = (time.time() - start_time) * 1000.0

        if resp.status_code == 200:
            data = resp.json()
            audios = data.get("audios", [])
            audio_base64 = audios[0] if audios else ""
            return AudioSynthesisResponse(
                text=text,
                audio_base64=audio_base64,
                language_code=language_code,
                speaker=speaker,
                provider_name=self.provider_name,
                latency_ms=latency,
            )
        else:
            raise RuntimeError(f"Sarvam TTS failed ({resp.status_code}): {resp.text}")
