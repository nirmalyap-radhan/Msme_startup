"""
Groq AI Provider Integration.
Primary text reasoning and grounded chat completion adapter using high-throughput open models.
"""

import os
import time
from typing import Any, Dict, List, Optional
from groq import Groq, APIConnectionError, RateLimitError, APIStatusError

from dotenv import load_dotenv

load_dotenv()

from services.ai_gateway.base import BaseAIProvider, ProviderResponse


class GroqProvider(BaseAIProvider):
    DEFAULT_MODEL = "qwen/qwen3.8-27b"
    FALLBACK_MODEL = "allam-2-7b"

    def __init__(self, api_key: Optional[str] = None):
        self._api_key = api_key or os.getenv("GROQ_API_KEY", "")
        self._client: Optional[Groq] = None
        if self._api_key and not self._api_key.startswith("your_"):
            try:
                self._client = Groq(api_key=self._api_key)
            except Exception:
                self._client = None

    @property
    def provider_name(self) -> str:
        return "groq"

    def is_available(self) -> bool:
        if not self._client:
            return False
        try:
            # Check model list or small liveness call
            models = self._client.models.list()
            available_ids = [m.id for m in models.data]
            return self.DEFAULT_MODEL in available_ids or self.FALLBACK_MODEL in available_ids
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
        if not self._client:
            return ProviderResponse(
                content="",
                provider_name=self.provider_name,
                model_name=model or self.DEFAULT_MODEL,
                status="error",
                error_message="Groq client is not initialized or GROQ_API_KEY is not configured.",
                latency_ms=(time.time() - start_time) * 1000.0,
            )

        chosen_model = model or self.DEFAULT_MODEL

        try:
            response = self._client.chat.completions.create(
                model=chosen_model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                timeout=timeout_seconds,
            )
            latency = (time.time() - start_time) * 1000.0
            choice = response.choices[0]
            content = choice.message.content or ""

            usage = response.usage
            prompt_tokens = usage.prompt_tokens if usage else 0
            completion_tokens = usage.completion_tokens if usage else 0
            total_tokens = usage.total_tokens if usage else 0

            return ProviderResponse(
                content=content.strip(),
                provider_name=self.provider_name,
                model_name=chosen_model,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
                latency_ms=latency,
                status="success",
            )

        except RateLimitError as e:
            return ProviderResponse(
                content="",
                provider_name=self.provider_name,
                model_name=chosen_model,
                status="rate_limited",
                error_message=f"Groq rate limit exceeded: {str(e)}",
                latency_ms=(time.time() - start_time) * 1000.0,
            )
        except APIStatusError as e:
            # Try fallback model if model 404
            if e.status_code == 404 and chosen_model != self.FALLBACK_MODEL:
                return self.generate_chat_completion(
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    model=self.FALLBACK_MODEL,
                    timeout_seconds=timeout_seconds,
                )
            return ProviderResponse(
                content="",
                provider_name=self.provider_name,
                model_name=chosen_model,
                status="error",
                error_message=f"Groq API status error ({e.status_code}): {str(e)}",
                latency_ms=(time.time() - start_time) * 1000.0,
            )
        except Exception as e:
            return ProviderResponse(
                content="",
                provider_name=self.provider_name,
                model_name=chosen_model,
                status="error",
                error_message=f"Groq inference error: {str(e)}",
                latency_ms=(time.time() - start_time) * 1000.0,
            )
