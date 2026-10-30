"""
Data Models and Schemas for Retrieval-Augmented Generation (RAG).
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class RetrievedPassage(BaseModel):
    passage_id: str
    document_id: str
    scheme_id: str
    scheme_name: str
    page_number: int
    section_heading: Optional[str] = None
    text_content: str
    source_url: str
    document_sha256: str
    score: float
    is_ocr: bool = False

    model_config = ConfigDict(from_attributes=True)


class Citation(BaseModel):
    scheme_id: str
    scheme_name: str
    source_url: str
    page_number: int
    section_heading: Optional[str] = None
    document_sha256: str
    quoted_snippet: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class RAGQueryRequest(BaseModel):
    query: str = Field(min_length=3, description="User question in English, Odia, or Hindi.")
    scheme_id: Optional[str] = Field(None, description="Optional filter to a specific verified scheme.")
    target_language: str = Field("en", description="Target response language ('en', 'od', 'hi').")
    include_audio: bool = Field(False, description="Whether to generate Odia speech audio via Sarvam TTS.")
    top_k: int = Field(4, ge=1, le=10, description="Number of passages to retrieve.")


class RAGResponse(BaseModel):
    query: str
    answer: str
    target_language: str
    has_sufficient_evidence: bool
    citations: List[Citation] = Field(default_factory=list)
    passages_retrieved: List[RetrievedPassage] = Field(default_factory=list)
    provider_used: str
    model_used: str
    latency_ms: float
    audio_base64: Optional[str] = None
    disclaimer: str = (
        "Advisory response generated from verified Government of Odisha policy notifications. "
        "Official sanction is subject to departmental scrutiny."
    )

    model_config = ConfigDict(from_attributes=True)
