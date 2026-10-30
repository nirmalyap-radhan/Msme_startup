"""
Automated Scheme Discovery Engine.
Orchestrates multi-source crawling across Central Government, Odisha Government,
and Banking/DFI portals, idempotent document retrieval, passage extraction,
candidate scheme generation, update event tracking, and audit logging.
"""

from datetime import datetime
from typing import Dict, List, Optional
from uuid import uuid4
from sqlalchemy.orm import Session

from services.scheme_discovery.connectors.bank_connector import BankProductConnector
from services.scheme_discovery.connectors.html_directory import HtmlDirectoryConnector
from services.scheme_discovery.connectors.odisha_gazette import OdishaGazetteConnector
from services.scheme_discovery.models import (
    DiscoveredDocumentCandidate,
    DiscoveryJobSummary,
    DiscoveryMethod,
    SourceRegistryConfig,
    SourceType,
)
from services.scheme_discovery.registry import SourceRegistryService
from services.scheme_ingestion.extractor import DocumentExtractor
from services.scheme_ingestion.fetcher import DocumentFetcher
from services.scheme_ingestion.models import (
    ApplicationStatus,
    CandidateSchemeRecord,
    ClaimStatus,
    DiscoveredSourceRegistryModel,
    DiscoveryAuditLogModel,
    SchemeModel,
    SchemeStatus,
    SourceDocumentModel,
    UpdateEventModel,
    UpdateEventSchema,
)
from services.scheme_ingestion.normalizer import SchemeNormalizer
from services.scheme_ingestion.storage import SchemeStorageRepository


class SchemeDiscoveryEngine:
    def __init__(self, db_session: Optional[Session] = None):
        self._db = db_session
        self.fetcher = DocumentFetcher()
        self.extractor = DocumentExtractor()
        self.normalizer = SchemeNormalizer()
        self.registry_service = SourceRegistryService(db_session=self._db)

    def _get_session(self) -> Session:
        if self._db:
            return self._db
        repo = SchemeStorageRepository()
        return repo.get_session()

    def _select_connector(self, config: SourceRegistryConfig):
        """Chooses the appropriate specialized connector based on source metadata."""
        src_id = config.id.lower()
        if "policy" in src_id or "policies" in config.discovery_endpoint or "ipr" in src_id:
            return OdishaGazetteConnector(config)
        elif config.source_type in (
            SourceType.BANK_PSU,
            SourceType.BANK_PRIVATE,
            SourceType.DEVELOPMENT_FINANCIAL_INSTITUTION,
            SourceType.CREDIT_GUARANTEE_TRUST,
        ):
            return BankProductConnector(config)
        return HtmlDirectoryConnector(config)

    def discover_source(self, source_record: DiscoveredSourceRegistryModel) -> DiscoveryJobSummary:
        """
        Executes discovery on a single configured source registry entry.
        Idempotent: skips already ingested documents and verifies existing records.
        Records update events for newly discovered schemes and announcements.
        """
        session = self._get_session()
        should_close = (self._db is None)

        config = SourceRegistryConfig(
            id=source_record.id,
            name=source_record.name,
            source_type=SourceType(source_record.source_type),
            base_url=source_record.base_url,
            discovery_endpoint=source_record.discovery_endpoint,
            discovery_method=DiscoveryMethod(source_record.discovery_method or "html_directory"),
            polling_frequency_hours=source_record.polling_frequency_hours or 24,
            is_enabled=source_record.is_enabled,
            headers_config=source_record.headers_config or {},
        )

        connector = self._select_connector(config)
        now = datetime.utcnow()
        summary = DiscoveryJobSummary(
            source_id=source_record.id,
            source_name=source_record.name,
            checked_at=now,
            documents_discovered=0,
            new_documents_imported=0,
            duplicates_skipped=0,
            schemes_updated=0,
            status="success",
        )

        storage_repo = SchemeStorageRepository(session=session)

        try:
            candidates: List[DiscoveredDocumentCandidate] = connector.discover_documents()
            summary.documents_discovered = len(candidates)

            for cand in candidates:
                is_pdf = cand.source_url.lower().endswith(".pdf") or "/files/" in cand.source_url.lower() or "/download/" in cand.source_url.lower()

                if is_pdf:
                    # ---------------------------------------------------------
                    # 1. PDF Guideline / Gazette Document Discovery
                    # ---------------------------------------------------------
                    existing_doc = session.query(SourceDocumentModel).filter(
                        SourceDocumentModel.source_url == cand.source_url
                    ).first()

                    if existing_doc:
                        summary.duplicates_skipped += 1
                        continue

                    # Fetch document & compute SHA-256
                    try:
                        doc_schema = self.fetcher.fetch_url(url=cand.source_url, title=cand.title)
                    except Exception:
                        # Non-fatal: move to next document
                        continue

                    existing_by_hash = session.query(SourceDocumentModel).filter(
                        SourceDocumentModel.sha256_hash == doc_schema.sha256_hash
                    ).first()

                    if existing_by_hash:
                        summary.duplicates_skipped += 1
                        continue

                    # Extract passages & OCR if needed
                    doc_schema, passages = self.extractor.extract_document(doc_schema)

                    # Normalize candidate scheme
                    candidate_scheme = self.normalizer.normalize(doc_schema, passages)
                    candidate_scheme.category = cand.category
                    candidate_scheme.organization = cand.issuing_authority
                    candidate_scheme.scheme_type = cand.scheme_type or "government_scheme"
                    candidate_scheme.official_portal_url = cand.official_portal_url
                    candidate_scheme.official_guidelines_url = cand.source_url
                    candidate_scheme.status = SchemeStatus.PENDING_REVIEW

                    storage_repo.save_source_document(doc_schema)
                    storage_repo.save_passages(passages)
                    saved_scheme = storage_repo.save_candidate_scheme(candidate_scheme)

                    # Create official update event
                    update_event = UpdateEventSchema(
                        id=f"UPD-{uuid4().hex[:8].upper()}",
                        title=cand.title,
                        summary=candidate_scheme.summary[:400] if candidate_scheme.summary else f"Official publication: {cand.title}",
                        update_type=cand.update_type or "new_scheme",
                        source_name=source_record.name,
                        source_type=source_record.source_type,
                        source_url=cand.official_portal_url or source_record.base_url,
                        official_document_url=cand.source_url,
                        publication_date=now,
                        effective_date=cand.effective_date,
                        detected_at=now,
                        scheme_id=saved_scheme.id,
                        category=cand.category,
                        is_verified=True,
                        verification_notes=f"Discovered from {source_record.name} (SHA-256: {doc_schema.sha256_hash[:16]}...)",
                    )
                    storage_repo.save_update_event(update_event)

                    # Audit log
                    audit_log = DiscoveryAuditLogModel(
                        id=str(uuid4()),
                        scheme_id=saved_scheme.id,
                        source_id=source_record.id,
                        event_type="scheme_discovered",
                        previous_state={},
                        new_state={
                            "scheme_id": saved_scheme.id,
                            "official_name": saved_scheme.official_name,
                            "source_url": cand.source_url,
                            "category": cand.category,
                            "sha256": doc_schema.sha256_hash,
                        },
                        supporting_evidence=f"Discovered via {source_record.name} at {cand.source_url}",
                        source_clause_or_url=cand.source_url,
                    )
                    session.add(audit_log)
                    session.commit()
                    summary.new_documents_imported += 1

                else:
                    # ---------------------------------------------------------
                    # 2. Banking Product / Financial Facility Discovery
                    # ---------------------------------------------------------
                    existing_update = session.query(UpdateEventModel).filter(
                        (UpdateEventModel.title == cand.title) &
                        (UpdateEventModel.source_name == source_record.name)
                    ).first()

                    if existing_update:
                        summary.duplicates_skipped += 1
                        continue

                    # Record verified bank facility update event
                    update_event = UpdateEventSchema(
                        id=f"UPD-{uuid4().hex[:8].upper()}",
                        title=cand.title,
                        summary=f"{cand.issuing_authority} MSME credit facility: {cand.title}. {cand.collateral_requirement or ''}. {cand.max_loan_limit or ''}.",
                        update_type=cand.update_type or "bank_product",
                        source_name=source_record.name,
                        source_type=source_record.source_type,
                        source_url=cand.source_url,
                        official_document_url=cand.source_url,
                        publication_date=now,
                        detected_at=now,
                        category=cand.category,
                        is_verified=True,
                        verification_notes=f"Discovered from official bank portal {source_record.name}",
                        raw_evidence=cand.raw_metadata,
                    )
                    storage_repo.save_update_event(update_event)

                    summary.new_documents_imported += 1

            # Update source health status
            source_record.last_checked_at = now
            source_record.last_successful_at = now
            source_record.health_status = "healthy"
            source_record.error_count = 0
            source_record.last_error_message = None
            session.commit()

        except Exception as e:
            session.rollback()
            summary.status = "failed"
            summary.error_message = str(e)

            source_record.last_checked_at = now
            source_record.health_status = "failing"
            source_record.error_count = (source_record.error_count or 0) + 1
            source_record.last_error_message = str(e)[:500]
            session.commit()

        finally:
            if should_close:
                session.close()

        return summary

    def run_all_discovery(self) -> List[DiscoveryJobSummary]:
        """Runs discovery sequentially across all active registered sources."""
        self.registry_service.seed_default_sources()
        sources = self.registry_service.list_sources(enabled_only=True)
        results: List[DiscoveryJobSummary] = []
        for src in sources:
            res = self.discover_source(src)
            results.append(res)
        return results
