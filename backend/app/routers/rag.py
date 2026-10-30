"""
FastAPI Router for Grounded RAG, AI Assistant, and Indian Language Services.
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.security.dependencies import get_db
from services.ai_gateway.base import ProviderStatus
from services.ai_gateway.gateway import ai_gateway
from services.rag.models import RAGQueryRequest, RAGResponse
from services.rag.rag_service import RAGService

router = APIRouter(prefix="/rag", tags=["AI Advisory & Grounded RAG"])


class VoiceSynthesizeRequest(BaseModel):
    text: str = Field(min_length=2, max_length=1000, description="Text to synthesize in Odia or Hindi.")
    language_code: str = Field("od-IN", description="Language code ('od-IN', 'hi-IN').")
    speaker: str = Field("ritu", description="Voice speaker identifier.")


class VoiceSynthesizeResponse(BaseModel):
    text: str
    audio_base64: str
    language_code: str
    speaker: str
    provider_name: str
    latency_ms: float


@router.post("/ask", response_model=RAGResponse)
def ask_ai_advisor(
    payload: RAGQueryRequest,
    db: Session = Depends(get_db)
):
    """
    Submits a natural language question about Odisha government schemes.
    Retrieves verified policy evidence, generates a grounded response with source citations,
    and optionally returns Odia translation and voice synthesis.
    """
    service = RAGService(db_session=db)
    return service.ask(payload)


@router.get("/providers", response_model=List[ProviderStatus])
def get_ai_providers_status():
    """
    Audits and returns the live availability and capability status of all 5 AI providers
    (Groq, Sarvam AI, Gemini, Mistral, NVIDIA NIM).
    """
    return ai_gateway.get_all_provider_statuses()


@router.post("/voice/synthesize", response_model=VoiceSynthesizeResponse)
def synthesize_odia_speech(
    payload: VoiceSynthesizeRequest
):
    """
    Synthesizes speech in Odia using Sarvam AI's bulbul:v3 voice model.
    """
    if not ai_gateway.sarvam.is_available():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Sarvam AI speech synthesis service is not available or unconfigured."
        )

    try:
        res = ai_gateway.sarvam.synthesize_speech(
            text=payload.text,
            language_code=payload.language_code,
            speaker=payload.speaker,
        )
        return VoiceSynthesizeResponse(
            text=res.text,
            audio_base64=res.audio_base64,
            language_code=res.language_code,
            speaker=res.speaker,
            provider_name=res.provider_name,
            latency_ms=round(res.latency_ms, 2),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Speech synthesis failed: {str(e)}"
        )
