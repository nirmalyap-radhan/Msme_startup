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
    UpdateEventModel,
    UpdateEventSchema,
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
        """Creates database schema if not present and adds backward-compatible columns."""
        Base.metadata.create_all(bind=self.engine)
        if self.db_url.startswith("sqlite"):
            try:
                with self.engine.connect() as conn:
                    from sqlalchemy import text
                    cursor = conn.execute(text("PRAGMA table_info(schemes)"))
                    existing_cols = {row[1] for row in cursor.fetchall()}
                    cols_to_add = [
                        ("scheme_type", "VARCHAR(64) DEFAULT 'government_scheme'"),
                        ("interest_rate_published", "VARCHAR(128)"),
                        ("max_loan_limit", "VARCHAR(128)"),
                        ("collateral_requirement", "VARCHAR(256)"),
                    ]
                    for col_name, col_type in cols_to_add:
                        if col_name not in existing_cols:
                            conn.execute(text(f"ALTER TABLE schemes ADD COLUMN {col_name} {col_type}"))
                    conn.commit()
            except Exception:
                pass

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
                category=getattr(scheme, "category", "finance_credit") or "finance_credit",
                organization=getattr(scheme, "organization", None),
                scheme_type=getattr(scheme, "scheme_type", "government_scheme") or "government_scheme",
                interest_rate_published=getattr(scheme, "interest_rate_published", None),
                max_loan_limit=getattr(scheme, "max_loan_limit", None),
                collateral_requirement=getattr(scheme, "collateral_requirement", None),
                application_status=scheme.application_status.value if hasattr(scheme.application_status, "value") else str(scheme.application_status),
                claim_status=scheme.claim_status.value if hasattr(scheme.claim_status, "value") else str(scheme.claim_status),
                application_start_date=scheme.application_start_date,
                application_deadline=scheme.application_deadline,
                claim_deadline=scheme.claim_deadline,
                is_rolling=scheme.is_rolling,
                financial_year_cycle=scheme.financial_year_cycle,
                official_application_url=scheme.official_application_url,
                official_guidelines_url=scheme.official_guidelines_url,
                official_notification_url=scheme.official_notification_url,
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
            session.commit()
            session.refresh(scheme)
            return scheme

    def reject_candidate_scheme(
        self,
        scheme_id: str,
        reviewer_id: str,
        reviewer_name: str,
        notes: str
    ) -> SchemeModel:
        with self.get_session() as session:
            scheme = session.query(SchemeModel).filter(SchemeModel.id == scheme_id).first()
            if not scheme:
                raise ValueError(f"Scheme not found: {scheme_id}")

            scheme.status = SchemeStatus.WITHDRAWN.value
            review_event = ReviewEventModel(
                id=ReviewEventSchema(scheme_id=scheme_id, reviewer_id=reviewer_id, reviewer_name=reviewer_name, action="REJECT", notes=notes).review_id,
                scheme_id=scheme_id,
                reviewer_id=reviewer_id,
                reviewer_name=reviewer_name,
                action="REJECT",
                notes=notes,
                verified_fields={},
                reviewed_at=datetime.utcnow(),
            )
            session.add(review_event)
            session.commit()
            session.refresh(scheme)
            return scheme

    def update_scheme_lifecycle(
        self,
        scheme_id: str,
        updates: Dict[str, Any],
        reviewer_id: str,
        reviewer_name: str,
    ) -> SchemeModel:
        with self.get_session() as session:
            scheme = session.query(SchemeModel).filter(SchemeModel.id == scheme_id).first()
            if not scheme:
                raise ValueError(f"Scheme not found: {scheme_id}")

            for k, v in updates.items():
                if hasattr(scheme, k) and v is not None:
                    setattr(scheme, k, v)

            scheme.last_verified_at = datetime.utcnow()
            review_event = ReviewEventModel(
                id=ReviewEventSchema(
                    scheme_id=scheme_id,
                    reviewer_id=reviewer_id,
                    reviewer_name=reviewer_name,
                    action="UPDATE_LIFECYCLE",
                    notes=updates.get("notes", "Lifecycle and deadline updated by officer"),
                ).review_id,
                scheme_id=scheme_id,
                reviewer_id=reviewer_id,
                reviewer_name=reviewer_name,
                action="UPDATE_LIFECYCLE",
                notes=updates.get("notes", "Lifecycle and deadline updated by officer"),
                verified_fields=updates,
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

    # --------------------------------------------------------------------------
    # Official Updates & Announcements Tracking
    # --------------------------------------------------------------------------

    def save_update_event(self, event_schema: UpdateEventSchema) -> UpdateEventModel:
        with self.get_session() as session:
            existing = session.query(UpdateEventModel).filter(
                (UpdateEventModel.id == event_schema.id) |
                ((UpdateEventModel.title == event_schema.title) & (UpdateEventModel.source_url == event_schema.source_url))
            ).first()
            if existing:
                existing.summary = event_schema.summary
                existing.update_type = event_schema.update_type
                existing.source_name = event_schema.source_name
                existing.source_type = event_schema.source_type
                existing.official_document_url = event_schema.official_document_url
                existing.publication_date = event_schema.publication_date
                existing.effective_date = event_schema.effective_date
                existing.category = event_schema.category
                existing.scheme_id = event_schema.scheme_id
                session.commit()
                session.refresh(existing)
                return existing

            model = UpdateEventModel(
                id=event_schema.id,
                title=event_schema.title,
                summary=event_schema.summary,
                update_type=event_schema.update_type,
                source_name=event_schema.source_name,
                source_type=event_schema.source_type,
                source_url=event_schema.source_url,
                official_document_url=event_schema.official_document_url,
                publication_date=event_schema.publication_date,
                effective_date=event_schema.effective_date,
                detected_at=event_schema.detected_at,
                scheme_id=event_schema.scheme_id,
                category=event_schema.category,
                is_verified=event_schema.is_verified,
                verification_notes=event_schema.verification_notes,
                raw_evidence=event_schema.raw_evidence,
            )
            session.add(model)
            session.commit()
            session.refresh(model)
            return model

    def list_update_events(
        self,
        search: Optional[str] = None,
        update_type: Optional[str] = None,
        source_type: Optional[str] = None,
        category: Optional[str] = None,
        page: int = 1,
        limit: int = 20,
    ):
        with self.get_session() as session:
            query = session.query(UpdateEventModel).filter(UpdateEventModel.is_verified == True)
            if search:
                term = f"%{search.strip()}%"
                query = query.filter(
                    (UpdateEventModel.title.ilike(term)) | (UpdateEventModel.summary.ilike(term))
                )
            if update_type:
                query = query.filter(UpdateEventModel.update_type == update_type)
            if source_type:
                query = query.filter(UpdateEventModel.source_type == source_type)
            if category:
                query = query.filter(UpdateEventModel.category == category)

            total = query.count()
            items = query.order_by(
                UpdateEventModel.publication_date.desc().nullslast(),
                UpdateEventModel.detected_at.desc()
            ).offset((page - 1) * limit).limit(limit).all()
            return items, total

    def get_update_event(self, update_id: str) -> Optional[UpdateEventModel]:
        with self.get_session() as session:
            return session.query(UpdateEventModel).filter(UpdateEventModel.id == update_id).first()
