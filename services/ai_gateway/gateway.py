"""
Unified AI Gateway for Udyog Sathi.
Coordinates multi-provider dispatch, health probes, fallback routing, and zero-mock error handling.
"""

from datetime import datetime
import os
from typing import Dict, List, Optional

from dotenv import load_dotenv

load_dotenv()

from services.ai_gateway.base import BaseAIProvider, ProviderStatus
from services.ai_gateway.gemini_provider import GeminiProvider
from services.ai_gateway.groq_provider import GroqProvider
from services.ai_gateway.mistral_provider import MistralProvider
from services.ai_gateway.nvidia_provider import NvidiaProvider
from services.ai_gateway.sarvam_provider import SarvamProvider


class AIGateway:
    def __init__(self):
        self.groq = GroqProvider()
        self.sarvam = SarvamProvider()
        self.gemini = GeminiProvider()
        self.mistral = MistralProvider()
        self.nvidia = NvidiaProvider()

        self._providers: Dict[str, BaseAIProvider] = {
            "groq": self.groq,
            "sarvam": self.sarvam,
            "gemini": self.gemini,
            "mistral": self.mistral,
            "nvidia": self.nvidia,
        }

    def get_provider(self, name: str) -> Optional[BaseAIProvider]:
        return self._providers.get(name.lower())

    def get_primary_text_provider(self) -> BaseAIProvider:
        """Returns the primary validated text generation provider (Groq)."""
        if self.groq.is_available():
            return self.groq
        # Safe secondary check if Groq is temporarily down
        if self.gemini.is_available():
            return self.gemini
        if self.nvidia.is_available():
            return self.nvidia
        # Default back to groq so it handles errors explicitly
        return self.groq

    def get_language_provider(self) -> SarvamProvider:
        """Returns the specialized Indian language & voice provider (Sarvam)."""
        return self.sarvam

    def get_all_provider_statuses(self) -> List[ProviderStatus]:
        """Audits the live configuration and connectivity status of all 5 providers."""
        statuses = []

        # 1. Groq
        groq_cfg = bool(os.getenv("GROQ_API_KEY") and not os.getenv("GROQ_API_KEY", "").startswith("your_"))
        groq_avail = self.groq.is_available()
        statuses.append(
            ProviderStatus(
                name="groq",
                is_configured=groq_cfg,
                is_available=groq_avail,
                preferred_model=self.groq.DEFAULT_MODEL,
                capabilities=["text_generation", "grounded_chat", "rag_reasoning"],
                last_checked_at=datetime.utcnow().isoformat(),
                error_category=None if groq_avail else ("missing_key" if not groq_cfg else "api_unavailable"),
            )
        )

        # 2. Sarvam AI
        sarvam_cfg = bool(os.getenv("SARVAM_API_KEY") and not os.getenv("SARVAM_API_KEY", "").startswith("your_"))
        sarvam_avail = self.sarvam.is_available()
        statuses.append(
            ProviderStatus(
                name="sarvam",
                is_configured=sarvam_cfg,
                is_available=sarvam_avail,
                preferred_model="bulbul:v3",
                capabilities=["odia_translation", "hindi_translation", "odia_tts_voice"],
                last_checked_at=datetime.utcnow().isoformat(),
                error_category=None if sarvam_avail else ("missing_key" if not sarvam_cfg else "api_unavailable"),
            )
        )

        # 3. Gemini
        gemini_cfg = bool(os.getenv("GEMINI_API_KEY") and not os.getenv("GEMINI_API_KEY", "").startswith("your_"))
        gemini_avail = self.gemini.is_available()
        statuses.append(
            ProviderStatus(
                name="gemini",
                is_configured=gemini_cfg,
                is_available=gemini_avail,
                preferred_model="gemini-flash-latest",
                capabilities=["document_understanding", "multimodal_extraction"],
                last_checked_at=datetime.utcnow().isoformat(),
                error_category=None if gemini_avail else ("missing_key" if not gemini_cfg else "quota_exceeded_or_unavailable"),
            )
        )

        # 4. Mistral
        mistral_cfg = bool(os.getenv("MISTRAL_API_KEY") and not os.getenv("MISTRAL_API_KEY", "").startswith("your_"))
        mistral_avail = self.mistral.is_available()
        statuses.append(
            ProviderStatus(
                name="mistral",
                is_configured=mistral_cfg,
                is_available=mistral_avail,
                preferred_model=self.mistral.DEFAULT_MODEL,
                capabilities=["text_generation"],
                last_checked_at=datetime.utcnow().isoformat(),
                error_category=None if mistral_avail else ("missing_key" if not mistral_cfg else "rate_limited_or_unfunded"),
            )
        )

        # 5. NVIDIA
        nvidia_cfg = bool(os.getenv("NVIDIA_API_KEY") and not os.getenv("NVIDIA_API_KEY", "").startswith("your_"))
        nvidia_avail = self.nvidia.is_available()
        statuses.append(
            ProviderStatus(
                name="nvidia",
                is_configured=nvidia_cfg,
                is_available=nvidia_avail,
                preferred_model=self.nvidia.DEFAULT_MODEL,
                capabilities=["open_model_inference"],
                last_checked_at=datetime.utcnow().isoformat(),
                error_category=None if nvidia_avail else ("missing_key" if not nvidia_cfg else "endpoint_timeout_or_deprecated"),
            )
        )

        return statuses


ai_gateway = AIGateway()
