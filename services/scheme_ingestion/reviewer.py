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
