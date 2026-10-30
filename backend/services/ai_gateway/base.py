"""
Base AI Provider Interface and Data Models for Udyog Sathi.
Standardizes LLM completions, translation, and speech synthesis across providers.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class CitationReference:
    source_title: str
    source_url: str
    page_number: Optional[int] = None
    section_heading: Optional[str] = None
    clause: Optional[str] = None
    document_sha256: Optional[str] = None


@dataclass
class ProviderResponse:
    content: str
    provider_name: str
    model_name: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    latency_ms: float = 0.0
    citations: List[CitationReference] = field(default_factory=list)
    raw_response: Optional[Dict[str, Any]] = None
    status: str = "success"  # "success", "error", "rate_limited", "quota_exceeded"
    error_message: Optional[str] = None


@dataclass
class TranslationResponse:
    original_text: str
    translated_text: str
    source_language: str
    target_language: str
    provider_name: str
    latency_ms: float = 0.0
    request_id: Optional[str] = None


@dataclass
class AudioSynthesisResponse:
    text: str
    audio_base64: str
    language_code: str
    speaker: str
    provider_name: str
    latency_ms: float = 0.0


@dataclass
class ProviderStatus:
    name: str
    is_configured: bool
    is_available: bool
    preferred_model: Optional[str]
    capabilities: List[str]
    last_checked_at: str
    error_category: Optional[str] = None


class BaseAIProvider(ABC):
    """Abstract base class for all external AI and Indian language provider integrations."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Name of the provider (e.g. 'groq', 'sarvam', 'gemini')."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Returns True if the provider is configured and passes liveness probe."""
        pass

    @abstractmethod
    def generate_chat_completion(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = 1024,
        temperature: float = 0.2,
        model: Optional[str] = None,
        timeout_seconds: float = 15.0,
    ) -> ProviderResponse:
        """Executes a chat completion request with strict timeouts and error categorization."""
        pass

    def translate_text(
        self,
        text: str,
        source_language: str,
        target_language: str,
    ) -> TranslationResponse:
        """Optional translation method. Raises NotImplementedError if unsupported."""
        raise NotImplementedError(f"Provider '{self.provider_name}' does not support text translation.")

    def synthesize_speech(
        self,
        text: str,
        language_code: str = "od-IN",
        speaker: str = "ritu",
    ) -> AudioSynthesisResponse:
        """Optional text-to-speech method. Raises NotImplementedError if unsupported."""
        raise NotImplementedError(f"Provider '{self.provider_name}' does not support text-to-speech synthesis.")
