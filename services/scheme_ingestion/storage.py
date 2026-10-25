"""
Persistent Storage Repository for Scheme Documents, Extracted Records, and Review Events.
Supports SQLite (local development and isolated tests) and PostgreSQL.
Strictly isolates draft/pending records from public published queries.
"""

import json
from datetime import datetime
from typing import Any, Dict, List, Optional
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker, Session

from services.scheme_ingestion.config import ingestion_config
from services.scheme_ingestion.models import (
    Base,
    BenefitRuleModel,
    CandidateBenefit,
    CandidateEligibilityCondition,
    CandidateSchemeRecord,
    DocumentPassageModel,
    EligibilityRuleModel,
    ExtractedPassageSchema,
    IngestionJobModel,
    IngestionJobRecord,
    ReviewEventModel,
    ReviewEventSchema,
    SchemeModel,
    SchemeStatus,
    SourceDocumentModel,
    SourceDocumentSchema,
)


class SchemeStorageRepository:
    def __init__(self, db_url: Optional[str] = None):
        chosen_url = db_url or ingestion_config.database_url
        if chosen_url.startswith("postgresql+asyncpg://"):
            chosen_url = chosen_url.replace("postgresql+asyncpg://", "postgresql+psycopg://")

        try:
            connect_args = {"check_same_thread": False} if chosen_url.startswith("sqlite") else {}
            test_engine = create_engine(chosen_url, connect_args=connect_args)
            with test_engine.connect() as conn:
                pass
            self.db_url = chosen_url
            self.engine = test_engine
        except Exception:
            # Fallback to local SQLite when external PostgreSQL host is offline
            self.db_url = "sqlite:///./data/udyog_sathi.db"
            self.engine = create_engine(self.db_url, connect_args={"check_same_thread": False})

        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self.create_tables()

    def create_tables(self):
        """Creates database schema if not present."""
        Base.metadata.create_all(bind=self.engine)

    def get_session(self) -> Session:
        return self.SessionLocal()

    # --------------------------------------------------------------------------
    # Document Storage
    # --------------------------------------------------------------------------

    def save_source_document(self, doc_schema: SourceDocumentSchema) -> SourceDocumentModel:
        with self.get_session() as session:
            existing = session.query(SourceDocumentModel).filter(
                SourceDocumentModel.sha256_hash == doc_schema.sha256_hash
            ).first()

            if existing:
                return existing

            doc_model = SourceDocumentModel(
                id=doc_schema.document_id,
                title=doc_schema.title,
                source_url=doc_schema.source_url,
                local_path=doc_schema.local_path,
                sha256_hash=doc_schema.sha256_hash,
                mime_type=doc_schema.mime_type,
                file_size_bytes=doc_schema.file_size_bytes,
                retrieved_at_utc=doc_schema.retrieved_at_utc,
                page_count=doc_schema.page_count,
                is_scanned=doc_schema.is_scanned,
                ocr_applied=doc_schema.ocr_applied,
            )
            session.add(doc_model)
            session.commit()
            session.refresh(doc_model)
            return doc_model

    def save_passages(self, passages: List[ExtractedPassageSchema]):
        with self.get_session() as session:
            for p in passages:
                existing = session.query(DocumentPassageModel).filter(
                    DocumentPassageModel.id == p.passage_id
                ).first()
                if not existing:
                    model = DocumentPassageModel(
                        id=p.passage_id,
                        document_id=p.document_id,
                        page_number=p.page_number,
                        section_heading=p.section_heading,
                        text_content=p.text_content,
                        character_count=p.character_count,
                        is_ocr=p.is_ocr,
                        ocr_confidence=p.ocr_confidence,
                    )
                    session.add(model)
            session.commit()

    # --------------------------------------------------------------------------
    # Candidate & Scheme Storage
    # --------------------------------------------------------------------------

    def save_candidate_scheme(self, scheme: CandidateSchemeRecord) -> SchemeModel:
        with self.get_session() as session:
            existing = session.query(SchemeModel).filter(SchemeModel.id == scheme.scheme_id).first()
            if existing:
                return existing

            scheme_model = SchemeModel(
                id=scheme.scheme_id,
                official_name=scheme.official_name,
                official_name_odia=scheme.official_name_odia,
                department=scheme.department,
                implementing_agency=scheme.implementing_agency,
                jurisdiction=scheme.jurisdiction,
                source_url=scheme.source_url,
                source_document_id=scheme.source_document_id,
                document_sha256=scheme.document_sha256,
                summary=scheme.summary,
                status=scheme.status.value,
                version=scheme.version,
                effective_date=scheme.effective_date,
                expiry_date=scheme.expiry_date,
                required_documents=scheme.required_documents,
                application_process=scheme.application_process,
                official_portal_url=scheme.official_portal_url,
                created_at=scheme.extracted_at,
                updated_at=datetime.utcnow(),
            )
            session.add(scheme_model)

            # Add candidate eligibility conditions
            for cond in scheme.candidate_eligibility:
                rule_model = EligibilityRuleModel(
                    id=cond.condition_id,
                    scheme_id=scheme.scheme_id,
                    attribute_name=cond.attribute_name,
                    operator=cond.operator,
                    value_json={"value": cond.value},
                    description=cond.description,
                    source_clause=cond.source_clause,
                    source_page=cond.source_page,
                    is_verified=False,
                )
                session.add(rule_model)

            # Add candidate benefits
            for ben in scheme.candidate_benefits:
                ben_model = BenefitRuleModel(
                    id=ben.benefit_id,
                    scheme_id=scheme.scheme_id,
                    benefit_type=ben.benefit_type,
                    formula_description=ben.formula_description,
                    subsidy_percentage=ben.subsidy_percentage,
                    max_limit_inr=ben.max_limit_inr,
                    duration_years=ben.duration_years,
                    source_clause=ben.source_clause,
                    source_page=ben.source_page,
                    is_verified=False,
                )
                session.add(ben_model)

            session.commit()
            session.refresh(scheme_model)
            return scheme_model

    def get_scheme(self, scheme_id: str) -> Optional[SchemeModel]:
        with self.get_session() as session:
            return session.query(SchemeModel).filter(SchemeModel.id == scheme_id).first()

    def list_schemes_pending_review(self) -> List[Dict[str, Any]]:
        """Returns schemes awaiting human verification."""
        with self.get_session() as session:
            schemes = session.query(SchemeModel).filter(
                SchemeModel.status == SchemeStatus.PENDING_REVIEW.value
            ).all()
            return [
                {
                    "scheme_id": s.id,
                    "official_name": s.official_name,
                    "department": s.department,
                    "source_url": s.source_url,
                    "document_sha256": s.document_sha256,
                    "status": s.status,
                    "created_at": s.created_at.isoformat() if s.created_at else None,
                }
                for s in schemes
            ]

    def list_published_schemes(self) -> List[Dict[str, Any]]:
        """
        CRITICAL NO-MOCK RULE: Returns ONLY records where status == 'published'.
        Unverified, draft, or failed records are strictly excluded from public queries.
        """
        with self.get_session() as session:
            schemes = session.query(SchemeModel).filter(
                SchemeModel.status == SchemeStatus.PUBLISHED.value
            ).all()
            return [
                {
                    "scheme_id": s.id,
                    "official_name": s.official_name,
                    "department": s.department,
                    "implementing_agency": s.implementing_agency,
                    "jurisdiction": s.jurisdiction,
                    "source_url": s.source_url,
                    "document_sha256": s.document_sha256,
                    "summary": s.summary,
                    "version": s.version,
                    "effective_date": s.effective_date,
                    "expiry_date": s.expiry_date,
                    "status": s.status,
                    "published_at": s.published_at.isoformat() if s.published_at else None,
                    "verified_by_reviewer": s.verified_by_reviewer,
                }
                for s in schemes
            ]

    # --------------------------------------------------------------------------
    # Verification & Review
    # --------------------------------------------------------------------------

    def publish_verified_scheme(
        self,
        scheme_id: str,
        reviewer_id: str,
        reviewer_name: str,
        notes: str,
        verified_fields: Dict[str, Any]
    ) -> SchemeModel:
        """
        Promotes a pending scheme to PUBLISHED status after verified reviewer sign-off.
        Records an immutable audit event in review_events table.
        """
        with self.get_session() as session:
            scheme = session.query(SchemeModel).filter(SchemeModel.id == scheme_id).first()
            if not scheme:
                raise ValueError(f"Scheme not found: {scheme_id}")

            # Mark rules verified
            for rule in scheme.eligibility_rules:
                rule.is_verified = True

            for benefit in scheme.benefits:
                benefit.is_verified = True

            # Update scheme status
            scheme.status = SchemeStatus.PUBLISHED.value
            scheme.published_at = datetime.utcnow()
            scheme.verified_by_reviewer = f"{reviewer_name} ({reviewer_id})"
            scheme.verification_notes = notes

            # Create immutable audit review event
            review_event = ReviewEventModel(
                id=ReviewEventSchema(scheme_id=scheme_id, reviewer_id=reviewer_id, reviewer_name=reviewer_name, action="APPROVE_PUBLICATION", notes=notes).review_id,
                scheme_id=scheme_id,
                reviewer_id=reviewer_id,
                reviewer_name=reviewer_name,
                action="APPROVE_PUBLICATION",
                notes=notes,
                verified_fields=verified_fields,
                reviewed_at=datetime.utcnow(),
            )
            session.add(review_event)
            session.commit()
            session.refresh(scheme)
            return scheme

    # --------------------------------------------------------------------------
    # Ingestion Job Tracking
    # --------------------------------------------------------------------------

    def save_ingestion_job(self, job: IngestionJobRecord):
        with self.get_session() as session:
            existing = session.query(IngestionJobModel).filter(IngestionJobModel.id == job.job_id).first()
            if existing:
                existing.status = job.status.value
                existing.completed_at = job.completed_at
                existing.error_message = job.error_message
                existing.document_id = job.document_id
                existing.scheme_id = job.scheme_id
                existing.extraction_stats = job.extraction_stats
            else:
                model = IngestionJobModel(
                    id=job.job_id,
                    source_url=job.source_url,
                    status=job.status.value,
                    started_at=job.started_at,
                    completed_at=job.completed_at,
                    error_message=job.error_message,
                    document_id=job.document_id,
                    scheme_id=job.scheme_id,
                    extraction_stats=job.extraction_stats,
                )
                session.add(model)
            session.commit()
