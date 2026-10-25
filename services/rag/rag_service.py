"""
End-to-End Grounded Retrieval-Augmented Generation Service for Udyog Sathi.
Orchestrates retrieval, citation mapping, AI gateway dispatch, translation, and voice synthesis.
"""

import time
from typing import List, Optional
from sqlalchemy.orm import Session

from services.ai_gateway.gateway import ai_gateway
from services.rag.models import Citation, RAGQueryRequest, RAGResponse, RetrievedPassage
from services.rag.prompts import (
    SYSTEM_RAG_PROMPT,
    format_evidence_context,
    format_insufficient_evidence_response,
)
from services.rag.retriever import HybridSchemeRetriever


class RAGService:
    def __init__(self, db_session: Optional[Session] = None):
        self.retriever = HybridSchemeRetriever(db_session=db_session)
        self.gateway = ai_gateway

    def _is_odia_text(self, text: str) -> bool:
        """Checks if string contains Odia Unicode script characters (U+0B00 to U+0B7F)."""
        return any("\u0b00" <= char <= "\u0b7f" for char in text)

    def ask(self, request: RAGQueryRequest) -> RAGResponse:
        start_time = time.time()
        query = request.query.strip()
        target_lang = request.target_language.lower()

        # Auto-detect Odia language if query is written in Odia script
        if self._is_odia_text(query):
            target_lang = "od"

        # 1. Translate Odia query to English for optimal lexical retrieval against English policy texts
        retrieval_query = query
        if target_lang == "od" and self.gateway.sarvam.is_available():
            try:
                trans_res = self.gateway.sarvam.translate_text(
                    text=query,
                    source_language="od-IN",
                    target_language="en-IN"
                )
                if trans_res.translated_text:
                    retrieval_query = f"{query} {trans_res.translated_text}"
            except Exception:
                pass  # Fall back to raw query

        # 2. Retrieve verified evidence passages
        passages, has_sufficient_evidence = self.retriever.retrieve(
            query=retrieval_query,
            scheme_id=request.scheme_id,
            top_k=request.top_k,
        )

        # 3. Handle Insufficient Evidence Gate (Anti-Hallucination)
        if not has_sufficient_evidence or not passages:
            latency = (time.time() - start_time) * 1000.0
            fallback_answer = format_insufficient_evidence_response(query, target_lang)

            audio_b64 = None
            if request.include_audio and target_lang == "od" and self.gateway.sarvam.is_available():
                try:
                    audio_res = self.gateway.sarvam.synthesize_speech(fallback_answer)
                    audio_b64 = audio_res.audio_base64
                except Exception:
                    pass

            return RAGResponse(
                query=query,
                answer=fallback_answer,
                target_language=target_lang,
                has_sufficient_evidence=False,
                citations=[],
                passages_retrieved=passages,
                provider_used="system",
                model_used="deterministic-evidence-gate",
                latency_ms=round(latency, 2),
                audio_base64=audio_b64,
            )

        # 4. Construct Grounded LLM Prompt
        evidence_block = format_evidence_context(passages)
        user_message_content = (
            f"CITIZEN QUESTION: {query}\n\n"
            f"VERIFIED EVIDENCE PASSAGES:\n{evidence_block}\n\n"
            f"Provide an accurate, grounded answer citing the exact passages above."
        )

        messages = [
            {"role": "system", "content": SYSTEM_RAG_PROMPT},
            {"role": "user", "content": user_message_content},
        ]

        # 5. Dispatch to Primary AI Provider (Groq)
        llm_provider = self.gateway.get_primary_text_provider()
        llm_response = llm_provider.generate_chat_completion(
            messages=messages,
            max_tokens=800,
            temperature=0.1,  # Low temperature for strict factual grounding
        )

        raw_answer = llm_response.content
        if llm_response.status != "success" or not raw_answer:
            raw_answer = (
                f"Notice: AI inference encountered an issue ({llm_response.error_message or 'provider unavailable'}). "
                f"However, verified government passages were retrieved below for your reference."
            )

        # 6. Build Structured Citations from Retrieved Passages
        citations = []
        for p in passages:
            snippet = p.text_content[:180].replace("\n", " ").strip() + "..."
            citations.append(
                Citation(
                    scheme_id=p.scheme_id,
                    scheme_name=p.scheme_name,
                    source_url=p.source_url,
                    page_number=p.page_number,
                    section_heading=p.section_heading,
                    document_sha256=p.document_sha256,
                    quoted_snippet=snippet,
                )
            )

        # 7. Odia Translation & Audio Synthesis if Requested
        final_answer = raw_answer
        if target_lang == "od" and self.gateway.sarvam.is_available() and llm_response.status == "success":
            try:
                trans_resp = self.gateway.sarvam.translate_text(
                    text=raw_answer,
                    source_language="en-IN",
                    target_language="od-IN"
                )
                if trans_resp.translated_text:
                    final_answer = trans_resp.translated_text
            except Exception:
                pass  # Preserve English answer if translation fails

        audio_b64 = None
        if request.include_audio and target_lang == "od" and self.gateway.sarvam.is_available():
            try:
                # Synthesize first 300 characters of Odia answer for audio preview
                tts_text = final_answer[:300]
                audio_res = self.gateway.sarvam.synthesize_speech(tts_text)
                audio_b64 = audio_res.audio_base64
            except Exception:
                pass

        total_latency = (time.time() - start_time) * 1000.0

        return RAGResponse(
            query=query,
            answer=final_answer,
            target_language=target_lang,
            has_sufficient_evidence=True,
            citations=citations,
            passages_retrieved=passages,
            provider_used=llm_provider.provider_name,
            model_used=llm_response.model_name,
            latency_ms=round(total_latency, 2),
            audio_base64=audio_b64,
        )
