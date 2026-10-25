"""
Hybrid Scheme Document Retriever for Udyog Sathi.
Retrieves and ranks evidence passages from verified, published government schemes
using BM25 lexical ranking and metadata filtering.
"""

import re
from typing import List, Optional, Tuple
from rank_bm25 import BM25Okapi
from sqlalchemy.orm import Session

from services.rag.models import RetrievedPassage
from services.scheme_ingestion.models import (
    DocumentPassageModel,
    SchemeModel,
    SchemeStatus,
    SourceDocumentModel,
)
from services.scheme_ingestion.storage import SchemeStorageRepository


class HybridSchemeRetriever:
    MIN_EVIDENCE_THRESHOLD = 1.0
    STOPWORDS = {
        "a", "an", "the", "and", "or", "of", "to", "in", "for", "on", "with", "by", "at",
        "from", "as", "is", "was", "are", "were", "be", "been", "that", "this", "it", "its",
        "what", "which", "who", "whom", "how", "when", "where", "why", "can", "could", "would",
        "should", "does", "do", "did", "have", "has", "had", "will", "shall", "under", "any", "about"
    }

    def __init__(self, db_session: Optional[Session] = None):
        self._db = db_session

    def _get_session(self) -> Session:
        if self._db:
            return self._db
        repo = SchemeStorageRepository()
        return repo.get_session()

    @classmethod
    def _tokenize(cls, text: str, remove_stopwords: bool = False) -> List[str]:
        """Tokenizes text preserving words, alphanumeric tokens, and regional scripts."""
        cleaned = re.sub(r"[^\w\s\u0B00-\u0B7F\u0900-\u097F₹%]", " ", text.lower())
        tokens = [t.strip() for t in cleaned.split() if len(t.strip()) > 1]
        if remove_stopwords:
            tokens = [t for t in tokens if t not in cls.STOPWORDS]
        return tokens

    def retrieve(
        self,
        query: str,
        scheme_id: Optional[str] = None,
        top_k: int = 4
    ) -> Tuple[List[RetrievedPassage], bool]:
        """
        Retrieves top relevant passages strictly from published schemes.
        Returns: (List[RetrievedPassage], has_sufficient_evidence: bool)
        """
        session = self._get_session()
        should_close = (self._db is None)

        try:
            # Join document passages with source documents and published schemes
            db_query = (
                session.query(
                    DocumentPassageModel,
                    SourceDocumentModel,
                    SchemeModel
                )
                .join(SourceDocumentModel, DocumentPassageModel.document_id == SourceDocumentModel.id)
                .join(SchemeModel, SchemeModel.source_document_id == SourceDocumentModel.id)
                .filter(SchemeModel.status == SchemeStatus.PUBLISHED.value)
            )

            if scheme_id:
                db_query = db_query.filter(SchemeModel.id == scheme_id)

            rows = db_query.all()

            if not rows:
                return [], False

            # Prepare passages and corpus for BM25
            passage_objects: List[RetrievedPassage] = []
            corpus_tokens: List[List[str]] = []

            for passage_row, doc_row, scheme_row in rows:
                p_obj = RetrievedPassage(
                    passage_id=passage_row.id,
                    document_id=doc_row.id,
                    scheme_id=scheme_row.id,
                    scheme_name=scheme_row.official_name,
                    page_number=passage_row.page_number,
                    section_heading=passage_row.section_heading,
                    text_content=passage_row.text_content,
                    source_url=doc_row.source_url,
                    document_sha256=doc_row.sha256_hash,
                    score=0.0,
                    is_ocr=passage_row.is_ocr or False,
                )
                passage_objects.append(p_obj)
                corpus_tokens.append(self._tokenize(p_obj.text_content + " " + (p_obj.section_heading or "")))

            # Execute BM25 search
            bm25 = BM25Okapi(corpus_tokens)
            query_tokens = self._tokenize(query)
            content_query_tokens = self._tokenize(query, remove_stopwords=True)
            if not content_query_tokens:
                content_query_tokens = query_tokens

            if not query_tokens:
                return [], False

            scores = bm25.get_scores(query_tokens)

            # Assign scores to passage objects
            scored_passages: List[Tuple[float, RetrievedPassage]] = []
            for score, p_obj in zip(scores, passage_objects):
                if score > 0.0:
                    p_obj.score = round(float(score), 4)
                    scored_passages.append((float(score), p_obj))

            # Sort descending by relevance score
            scored_passages.sort(key=lambda x: x[0], reverse=True)

            top_passages = [p for _, p in scored_passages[:top_k]]
            max_score = scored_passages[0][0] if scored_passages else 0.0

            # Evaluate keyword coverage on top passage
            has_sufficient_evidence = False
            if top_passages and max_score >= self.MIN_EVIDENCE_THRESHOLD:
                top_p = top_passages[0]
                top_passage_words = set(self._tokenize(top_p.text_content + " " + (top_p.section_heading or "")))
                matched_content_words = [t for t in content_query_tokens if t in top_passage_words]

                # Check if query has mixed regional script words (e.g. Odia or Hindi) alongside Latin scheme codes
                latin_tokens = list(set([t for t in content_query_tokens if re.match(r'^[a-z0-9]', t)]))
                if len(latin_tokens) >= 1 and len(latin_tokens) < len(content_query_tokens):
                    matched_latin = [t for t in latin_tokens if t in top_passage_words]
                    has_sufficient_evidence = (len(matched_latin) >= 1 and max_score >= 5.0)
                else:
                    unique_content_tokens = list(set(content_query_tokens))
                    coverage = len(set(matched_content_words)) / len(unique_content_tokens)
                    if len(unique_content_tokens) <= 2:
                        has_sufficient_evidence = (len(matched_content_words) >= 1)
                    else:
                        has_sufficient_evidence = (coverage >= 0.35 and len(matched_content_words) >= 2)

            return top_passages, has_sufficient_evidence

        finally:
            if should_close:
                session.close()
