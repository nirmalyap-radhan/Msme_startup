"""
Google Gemini AI Provider Integration.
Secondary provider adapter for document reasoning and extraction.
Correctly handles quota exhaustion (429) without fabricating mock responses.
"""

import os
import time
from typing import Any, Dict, List, Optional
import httpx

from services.ai_gateway.base import BaseAIProvider, ProviderResponse


class GeminiProvider(BaseAIProvider):
    BASE_URL = "https://generativelanguage.googleapis.com/v1beta"
    PREFERRED_MODELS = [
        "gemini-flash-latest",
        "gemini-pro-latest",
        "gemini-2.5-flash-lite",
    ]

    def __init__(self, api_key: Optional[str] = None):
        self._api_key = api_key or os.getenv("GEMINI_API_KEY", "")

    @property
    def provider_name(self) -> str:
        return "gemini"

    def is_available(self) -> bool:
        if not self._api_key or self._api_key.startswith("your_"):
            return False
        try:
            url = f"{self.BASE_URL}/models?key={self._api_key}"
            resp = httpx.get(url, timeout=5.0)
            return resp.status_code == 200
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
        start_time = time.time()
        if not self._api_key:
            return ProviderResponse(
                content="",
                provider_name=self.provider_name,
                model_name=model or self.PREFERRED_MODELS[0],
                status="error",
                error_message="GEMINI_API_KEY is not configured.",
                latency_ms=(time.time() - start_time) * 1000.0,
            )

        chosen_model = model or self.PREFERRED_MODELS[0]

        # Convert OpenAI-style messages to Gemini contents structure
        contents = []
        for m in messages:
            role = "user" if m.get("role") in ("user", "system") else "model"
            contents.append({"role": role, "parts": [{"text": m.get("content", "")}]})

        url = f"{self.BASE_URL}/models/{chosen_model}:generateContent?key={self._api_key}"
        payload = {
            "contents": contents,
            "generationConfig": {
                "maxOutputTokens": max_tokens,
                "temperature": temperature,
            }
        }

        try:
            resp = httpx.post(url, json=payload, timeout=timeout_seconds)
            latency = (time.time() - start_time) * 1000.0

            if resp.status_code == 200:
                data = resp.json()
                candidates = data.get("candidates", [])
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    text = parts[0].get("text", "") if parts else ""
                    return ProviderResponse(
                        content=text.strip(),
                        provider_name=self.provider_name,
                        model_name=chosen_model,
                        latency_ms=latency,
                        status="success",
                    )
                return ProviderResponse(
                    content="",
                    provider_name=self.provider_name,
                    model_name=chosen_model,
                    status="error",
                    error_message="Gemini returned no candidates.",
                    latency_ms=latency,
                )
            elif resp.status_code == 429:
                return ProviderResponse(
                    content="",
                    provider_name=self.provider_name,
                    model_name=chosen_model,
                    status="quota_exceeded",
                    error_message="Gemini API quota exceeded or rate limit reached.",
                    latency_ms=latency,
                )
            else:
                return ProviderResponse(
                    content="",
                    provider_name=self.provider_name,
                    model_name=chosen_model,
                    status="error",
                    error_message=f"Gemini API returned status {resp.status_code}: {resp.text[:120]}",
                    latency_ms=latency,
                )

        except Exception as e:
            return ProviderResponse(
                content="",
                provider_name=self.provider_name,
                model_name=chosen_model,
                status="error",
                error_message=f"Gemini connection error: {str(e)}",
                latency_ms=(time.time() - start_time) * 1000.0,
            )
