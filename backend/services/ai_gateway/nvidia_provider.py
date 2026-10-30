"""
NVIDIA NIM AI Provider Integration.
Secondary provider adapter for hosted open models on NVIDIA API catalog.
"""

import os
import time
from typing import Any, Dict, List, Optional
import httpx

from services.ai_gateway.base import BaseAIProvider, ProviderResponse


class NvidiaProvider(BaseAIProvider):
    BASE_URL = "https://integrate.api.nvidia.com/v1"
    DEFAULT_MODEL = "deepseek-ai/deepseek-v4.1-flash"

    def __init__(self, api_key: Optional[str] = None):
        self._api_key = api_key or os.getenv("NVIDIA_API_KEY", "")

    @property
    def provider_name(self) -> str:
        return "nvidia"

    def is_available(self) -> bool:
        if not self._api_key or self._api_key.startswith("your_"):
            return False
        try:
            resp = httpx.get(
                f"{self.BASE_URL}/models",
                headers={"Authorization": f"Bearer {self._api_key}"},
                timeout=5.0
            )
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
                model_name=model or self.DEFAULT_MODEL,
                status="error",
                error_message="NVIDIA_API_KEY is not configured.",
                latency_ms=(time.time() - start_time) * 1000.0,
            )

        chosen_model = model or self.DEFAULT_MODEL
        url = f"{self.BASE_URL}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": chosen_model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }

        try:
            resp = httpx.post(url, headers=headers, json=payload, timeout=timeout_seconds)
            latency = (time.time() - start_time) * 1000.0

            if resp.status_code == 200:
                data = resp.json()
                content = data["choices"][0]["message"]["content"]
                return ProviderResponse(
                    content=content.strip(),
                    provider_name=self.provider_name,
                    model_name=chosen_model,
                    latency_ms=latency,
                    status="success",
                )
            else:
                return ProviderResponse(
                    content="",
                    provider_name=self.provider_name,
                    model_name=chosen_model,
                    status="error",
                    error_message=f"NVIDIA API returned status {resp.status_code}: {resp.text[:120]}",
                    latency_ms=latency,
                )
        except Exception as e:
            return ProviderResponse(
                content="",
                provider_name=self.provider_name,
                model_name=chosen_model,
                status="error",
                error_message=f"NVIDIA connection error: {str(e)}",
                latency_ms=(time.time() - start_time) * 1000.0,
            )
