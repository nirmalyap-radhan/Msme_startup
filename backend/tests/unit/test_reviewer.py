"""
Unit tests for Scheme Review, Verification Workflow, and Publication Gates.
"""

import os
import tempfile
import pytest

from services.scheme_ingestion.models import (
    CandidateBenefit,
    CandidateEligibilityCondition,
    CandidateSchemeRecord,
    SchemeStatus,
    SourceDocumentSchema,
)
from services.scheme_ingestion.reviewer import ReviewError, SchemeReviewWorkflow
from services.scheme_ingestion.storage import SchemeStorageRepository


@pytest.fixture
def test_repo():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    repo = SchemeStorageRepository(db_url=f"sqlite:///{db_path}")
    yield repo

    repo.engine.dispose()
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
        except OSError:
            pass


def test_review_and_publication_workflow(test_repo):
    # 1. Store a test document and candidate scheme
    doc_schema = SourceDocumentSchema(
        document_id="doc-test-1",
        title="Odisha Technology Assistance Guidelines",
        source_url="https://msme.odisha.gov.in/sites/default/files/tech.pdf",
        local_path="/tmp/test.pdf",
        sha256_hash="11223344556677889900aabbccddeeff11223344556677889900aabbccddeeff",
        file_size_bytes=1024,
    )
    test_repo.save_source_document(doc_schema)

    candidate = CandidateSchemeRecord(
        scheme_id="OD-TECH-001",
        official_name="Technology Purchase Subsidy under OMSMED Policy 2022",
        department="Department of MSME, Government of Odisha",
        jurisdiction="Odisha",
        source_url="https://msme.odisha.gov.in/sites/default/files/tech.pdf",
        source_document_id=doc_schema.document_id,
        document_sha256=doc_schema.sha256_hash,
        summary="Assistance for technology acquisition by Odisha MSMEs.",
        status=SchemeStatus.PENDING_REVIEW,
        candidate_eligibility=[
            CandidateEligibilityCondition(
                attribute_name="enterprise_class",
                operator="IN",
                value=["micro", "small"],
                description="Enterprise must be micro or small.",
                source_clause="Clause 3.1",
                source_page=2,
            )
        ],
        candidate_benefits=[
            CandidateBenefit(
                benefit_type="technology_purchase_subsidy",
                formula_description="50% subsidy up to Rs. 10 Lakh",
                subsidy_percentage=50.0,
                max_limit_inr=1000000.0,
                source_clause="Clause 5.2",
                source_page=4,
            )
        ],
        required_documents=["Udyam Registration Certificate", "Technology Invoice"],
    )
    test_repo.save_candidate_scheme(candidate)

    # 2. Verify pending review list
    workflow = SchemeReviewWorkflow(repository=test_repo)
    pending = workflow.list_pending_schemes()
    assert len(pending) == 1
    assert pending[0]["scheme_id"] == "OD-TECH-001"
    assert pending[0]["status"] == SchemeStatus.PENDING_REVIEW.value

    # 3. CRITICAL RULE: Pending scheme must NOT appear in published catalogue
    published_before = test_repo.list_published_schemes()
    assert len(published_before) == 0

    # 4. Verify dossier inspection
    dossier = workflow.get_review_dossier("OD-TECH-001")
    assert dossier["official_name"] == "Technology Purchase Subsidy under OMSMED Policy 2022"
    assert len(dossier["candidate_eligibility"]) == 1
    assert len(dossier["candidate_benefits"]) == 1

    # 5. Invalid review (empty notes) should fail
    with pytest.raises(ReviewError, match="Verification notes must provide audit evidence"):
        workflow.verify_and_publish(
            scheme_id="OD-TECH-001",
            reviewer_id="REV-01",
            reviewer_name="Nodal Officer",
            notes="Short",
        )

    # 6. Valid approval and publication
    result = workflow.verify_and_publish(
        scheme_id="OD-TECH-001",
        reviewer_id="OFFICER-MSME-77",
        reviewer_name="Dr. P. Patnaik, Joint Director",
        notes="Verified against official Odisha MSME Gazette Notification 2022. All limits confirmed.",
    )

    assert result["status"] == SchemeStatus.PUBLISHED.value
    assert result["published_at"] is not None
    assert "Dr. P. Patnaik" in result["verified_by_reviewer"]

    # 7. CRITICAL RULE: Now published scheme MUST appear in published catalogue
    published_after = test_repo.list_published_schemes()
    assert len(published_after) == 1
    assert published_after[0]["scheme_id"] == "OD-TECH-001"
    assert published_after[0]["status"] == SchemeStatus.PUBLISHED.value

    # 8. Pending list should now be empty
    pending_after = workflow.list_pending_schemes()
    assert len(pending_after) == 0
