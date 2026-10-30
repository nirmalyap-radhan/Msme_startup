"""
Administrator Scheme Verification & Governance Workflow.
Enables designated department officers to inspect candidate scheme extractions alongside source evidence,
verify eligibility conditions, benefit limits, and application links, and promote verified records to PUBLISHED.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from services.scheme_ingestion.models import (
    CandidateBenefit,
    CandidateEligibilityCondition,
    PublishedSchemeRecord,
    ReviewEventSchema,
    SchemeStatus,
)
from services.scheme_ingestion.storage import SchemeStorageRepository


class ReviewError(Exception):
    """Raised when review or verification validation fails."""
    pass


class SchemeReviewWorkflow:
    def __init__(self, repository: Optional[SchemeStorageRepository] = None):
        self.repository = repository or SchemeStorageRepository()

    def list_pending_schemes(self) -> List[Dict[str, Any]]:
        """Returns all schemes awaiting verification."""
        return self.repository.list_schemes_pending_review()

    def get_review_dossier(self, scheme_id: str) -> Dict[str, Any]:
        """
        Retrieves the complete verification dossier for a scheme:
        candidate metadata, eligibility rules, benefits, document provenance, and source passages.
        """
        with self.repository.get_session() as session:
            from services.scheme_ingestion.models import (
                DocumentPassageModel,
                SchemeModel,
                SourceDocumentModel,
            )

            scheme = session.query(SchemeModel).filter(SchemeModel.id == scheme_id).first()
            if not scheme:
                raise ReviewError(f"Scheme with ID '{scheme_id}' does not exist.")

            doc = session.query(SourceDocumentModel).filter(
                SourceDocumentModel.id == scheme.source_document_id
            ).first()

            passages = session.query(DocumentPassageModel).filter(
                DocumentPassageModel.document_id == scheme.source_document_id
            ).order_by(DocumentPassageModel.page_number).all()

            return {
                "scheme_id": scheme.id,
                "official_name": scheme.official_name,
                "department": scheme.department,
                "implementing_agency": scheme.implementing_agency,
                "jurisdiction": scheme.jurisdiction,
                "status": scheme.status,
                "version": scheme.version,
                "effective_date": scheme.effective_date,
                "expiry_date": scheme.expiry_date,
                "summary": scheme.summary,
                "source_url": scheme.source_url,
                "document": {
                    "document_id": doc.id if doc else None,
                    "title": doc.title if doc else None,
                    "sha256": doc.sha256_hash if doc else scheme.document_sha256,
                    "page_count": doc.page_count if doc else 0,
                    "is_scanned": doc.is_scanned if doc else False,
                    "ocr_applied": doc.ocr_applied if doc else False,
                    "retrieved_at": doc.retrieved_at_utc.isoformat() if doc and doc.retrieved_at_utc else None,
                },
                "candidate_eligibility": [
                    {
                        "condition_id": r.id,
                        "attribute": r.attribute_name,
                        "operator": r.operator,
                        "value": r.value_json.get("value") if isinstance(r.value_json, dict) else r.value_json,
                        "description": r.description,
                        "source_clause": r.source_clause,
                        "source_page": r.source_page,
                        "is_verified": r.is_verified,
                    }
                    for r in scheme.eligibility_rules
                ],
                "candidate_benefits": [
                    {
                        "benefit_id": b.id,
                        "type": b.benefit_type,
                        "formula": b.formula_description,
                        "percentage": b.subsidy_percentage,
                        "max_inr": b.max_limit_inr,
                        "duration_years": b.duration_years,
                        "source_clause": b.source_clause,
                        "source_page": b.source_page,
                        "is_verified": b.is_verified,
                    }
                    for b in scheme.benefits
                ],
                "required_documents": scheme.required_documents or [],
                "application_process": scheme.application_process,
                "official_portal_url": scheme.official_portal_url,
                "passages_count": len(passages),
            }

    def verify_and_publish(
        self,
        scheme_id: str,
        reviewer_id: str,
        reviewer_name: str,
        notes: str,
        verified_fields: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Officially approves and publishes an extracted scheme record.
        Requires reviewer identity and verification notes.
        """
        if not reviewer_id or not reviewer_name:
            raise ReviewError("Reviewer ID and Reviewer Name are required for publication sign-off.")

        if not notes or len(notes.strip()) < 10:
            raise ReviewError("Verification notes must provide audit evidence of review (min 10 characters).")

        verified_data = verified_fields or {}

        updated_scheme = self.repository.publish_verified_scheme(
            scheme_id=scheme_id,
            reviewer_id=reviewer_id,
            reviewer_name=reviewer_name,
            notes=notes,
            verified_fields=verified_data,
        )

        return {
            "scheme_id": updated_scheme.id,
            "official_name": updated_scheme.official_name,
            "status": updated_scheme.status,
            "published_at": updated_scheme.published_at.isoformat() if updated_scheme.published_at else None,
            "verified_by_reviewer": updated_scheme.verified_by_reviewer,
            "verification_notes": updated_scheme.verification_notes,
        }

    def reject_scheme(
        self,
        scheme_id: str,
        reviewer_id: str,
        reviewer_name: str,
        reason: str
    ) -> Dict[str, Any]:
        """Rejects an irrelevant or unverified document with audit trail."""
        if not reason or len(reason.strip()) < 5:
            raise ReviewError("A rejection reason of at least 5 characters is required.")

        updated = self.repository.reject_candidate_scheme(
            scheme_id=scheme_id,
            reviewer_id=reviewer_id,
            reviewer_name=reviewer_name,
            notes=reason,
        )
        return {
            "scheme_id": updated.id,
            "official_name": updated.official_name,
            "status": updated.status,
            "rejected_by": reviewer_name,
            "rejection_reason": reason,
        }

    def update_scheme_lifecycle(
        self,
        scheme_id: str,
        updates: Dict[str, Any],
        reviewer_id: str,
        reviewer_name: str,
    ) -> Dict[str, Any]:
        """Updates deadlines, rolling status, or URLs with reviewer audit trail."""
        updated = self.repository.update_scheme_lifecycle(
            scheme_id=scheme_id,
            updates=updates,
            reviewer_id=reviewer_id,
            reviewer_name=reviewer_name,
        )
        return {
            "scheme_id": updated.id,
            "official_name": updated.official_name,
            "application_status": updated.application_status,
            "claim_status": updated.claim_status,
            "application_deadline": updated.application_deadline.isoformat() if updated.application_deadline else None,
            "claim_deadline": updated.claim_deadline.isoformat() if updated.claim_deadline else None,
            "is_rolling": updated.is_rolling,
            "last_verified_at": updated.last_verified_at.isoformat() if updated.last_verified_at else None,
        }

    def get_monitoring_dashboard_stats(self) -> Dict[str, Any]:
        """Computes comprehensive scheme monitoring statistics for the admin dashboard."""
        with self.repository.get_session() as session:
            from services.scheme_ingestion.models import (
                DiscoveredSourceRegistryModel,
                IngestionJobModel,
                SchemeDeadlineAlertModel,
                SchemeModel,
                SchemeStatus,
            )

            total_discovered = session.query(SchemeModel).count()
            total_verified = session.query(SchemeModel).filter(SchemeModel.status == SchemeStatus.PUBLISHED.value).count()
            awaiting_review = session.query(SchemeModel).filter(SchemeModel.status.in_([SchemeStatus.EXTRACTED.value, SchemeStatus.PENDING_REVIEW.value])).count()
            open_applications = session.query(SchemeModel).filter(
                SchemeModel.status == SchemeStatus.PUBLISHED.value,
                SchemeModel.application_status == "open"
            ).count()
            closing_soon = session.query(SchemeModel).filter(
                SchemeModel.status == SchemeStatus.PUBLISHED.value,
                SchemeModel.application_status == "closing_soon"
            ).count()
            claims_accepting = session.query(SchemeModel).filter(
                SchemeModel.status == SchemeStatus.PUBLISHED.value,
                SchemeModel.claim_status.in_(["claims_open", "rolling_claims"])
            ).count()
            closed_or_discontinued = session.query(SchemeModel).filter(
                SchemeModel.application_status.in_(["closed", "discontinued", "suspended"])
            ).count()
            unknown_availability = session.query(SchemeModel).filter(
                SchemeModel.application_status.in_(["unknown", "verification_required"])
            ).count()

            active_alerts_count = session.query(SchemeDeadlineAlertModel).filter(
                SchemeDeadlineAlertModel.is_dismissed == False
            ).count()

            failed_jobs_count = session.query(IngestionJobModel).filter(
                IngestionJobModel.status == "failed"
            ).count()

            failed_sources_count = session.query(DiscoveredSourceRegistryModel).filter(
                DiscoveredSourceRegistryModel.health_status != "healthy"
            ).count()

            sources = session.query(DiscoveredSourceRegistryModel).all()
            sync_per_source = [
                {
                    "source_id": s.id,
                    "source_name": s.name,
                    "last_successful_at": s.last_successful_at.isoformat() if s.last_successful_at else None,
                    "health_status": s.health_status,
                }
                for s in sources
            ]

            return {
                "total_schemes_discovered": total_discovered,
                "total_verified_schemes": total_verified,
                "currently_open_applications": open_applications,
                "schemes_accepting_claims": claims_accepting,
                "deadlines_approaching": closing_soon,
                "awaiting_review_count": awaiting_review,
                "closed_or_discontinued_count": closed_or_discontinued,
                "schemes_with_unknown_availability": unknown_availability,
                "active_deadline_alerts": active_alerts_count,
                "failed_ingestion_jobs": failed_jobs_count,
                "failed_source_checks": failed_sources_count,
                "last_successful_sync_per_source": sync_per_source,
            }
