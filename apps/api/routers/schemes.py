"""
Scheme Catalogue & Document Provenance API Router.
Enforces zero-mock production data: returns only verified, published government scheme records.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from apps.api.schemas.schemes import (
    DocumentChecklistResponse,
    SchemeDetailResponse,
    SchemeSummaryResponse,
    VerifiedBenefitResponse,
    VerifiedRuleResponse,
)
from apps.api.security.dependencies import get_db
from services.scheme_ingestion.models import (
    BenefitRuleModel,
    EligibilityRuleModel,
    SchemeModel,
    SchemeStatus,
    SourceDocumentModel,
)

router = APIRouter(prefix="/schemes", tags=["Schemes"])


@router.get("", response_model=List[SchemeSummaryResponse])
def list_published_schemes(
    search: Optional[str] = Query(None, description="Search keyword in scheme title or summary"),
    sector: Optional[str] = Query(None, description="Filter by sector, e.g. 'manufacturing'"),
    enterprise_class: Optional[str] = Query(None, description="Filter by enterprise class ('micro', 'small', 'medium')"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db)
):
    """
    Retrieves published schemes from the verified government catalogue.
    CRITICAL NO-MOCK RULE: Queries return only records where status == 'published'.
    Empty search results produce honest empty lists, never mock records.
    """
    query = db.query(SchemeModel).filter(SchemeModel.status == SchemeStatus.PUBLISHED.value)

    if search:
        search_term = f"%{search.strip()}%"
        query = query.filter(
            (SchemeModel.official_name.ilike(search_term)) |
            (SchemeModel.summary.ilike(search_term))
        )

    if sector:
        # Check if scheme has rule matching sector
        query = query.join(SchemeModel.eligibility_rules).filter(
            EligibilityRuleModel.attribute_name == "sector",
            EligibilityRuleModel.value_json.contains({"value": [sector.lower()]})
        )

    if enterprise_class:
        query = query.join(SchemeModel.eligibility_rules).filter(
            EligibilityRuleModel.attribute_name == "enterprise_class",
            EligibilityRuleModel.value_json.contains({"value": [enterprise_class.lower()]})
        )

    total_schemes = query.distinct().offset((page - 1) * limit).limit(limit).all()

    return [
        SchemeSummaryResponse(
            scheme_id=s.id,
            official_name=s.official_name,
            official_name_odia=s.official_name_odia,
            department=s.department,
            implementing_agency=s.implementing_agency,
            jurisdiction=s.jurisdiction,
            summary=s.summary,
            status=s.status,
            version=s.version,
            effective_date=s.effective_date,
            expiry_date=s.expiry_date,
            source_url=s.source_url,
            document_sha256=s.document_sha256,
            published_at=s.published_at,
        )
        for s in total_schemes
    ]


@router.get("/{scheme_id}", response_model=SchemeDetailResponse)
def get_scheme_details(
    scheme_id: str,
    db: Session = Depends(get_db)
):
    """
    Retrieves full verified scheme details, legal clause citations, and mathematical formulas.
    """
    scheme = db.query(SchemeModel).filter(
        SchemeModel.id == scheme_id,
        SchemeModel.status == SchemeStatus.PUBLISHED.value
    ).first()

    if not scheme:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Published scheme with ID '{scheme_id}' was not found in the official catalogue."
        )

    # Format verified rules
    rules = [
        VerifiedRuleResponse(
            rule_id=r.id,
            attribute_name=r.attribute_name,
            operator=r.operator,
            value=r.value_json.get("value") if isinstance(r.value_json, dict) else r.value_json,
            description=r.description,
            source_clause=r.source_clause,
            source_page=r.source_page,
            is_verified=r.is_verified,
        )
        for r in scheme.eligibility_rules
        if r.is_verified
    ]

    # Format verified benefits
    benefits = [
        VerifiedBenefitResponse(
            benefit_id=b.id,
            benefit_type=b.benefit_type,
            formula_description=b.formula_description,
            subsidy_percentage=b.subsidy_percentage,
            max_limit_inr=b.max_limit_inr,
            duration_years=b.duration_years,
            source_clause=b.source_clause,
            source_page=b.source_page,
            is_verified=b.is_verified,
        )
        for b in scheme.benefits
        if b.is_verified
    ]

    return SchemeDetailResponse(
        scheme_id=scheme.id,
        official_name=scheme.official_name,
        official_name_odia=scheme.official_name_odia,
        department=scheme.department,
        implementing_agency=scheme.implementing_agency,
        jurisdiction=scheme.jurisdiction,
        source_url=scheme.source_url,
        document_sha256=scheme.document_sha256,
        summary=scheme.summary,
        status=scheme.status,
        version=scheme.version,
        effective_date=scheme.effective_date,
        expiry_date=scheme.expiry_date,
        verified_eligibility_rules=rules,
        verified_benefits=benefits,
        required_documents=scheme.required_documents or [],
        application_process=scheme.application_process,
        official_portal_url=scheme.official_portal_url,
        published_at=scheme.published_at,
        verified_by_reviewer=scheme.verified_by_reviewer,
        verification_notes=scheme.verification_notes,
    )


@router.get("/{scheme_id}/checklist", response_model=DocumentChecklistResponse)
def get_scheme_document_checklist(
    scheme_id: str,
    db: Session = Depends(get_db)
):
    """
    Generates required document proofs checklist for application submission.
    """
    scheme = db.query(SchemeModel).filter(
        SchemeModel.id == scheme_id,
        SchemeModel.status == SchemeStatus.PUBLISHED.value
    ).first()

    if not scheme:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scheme '{scheme_id}' not found."
        )

    return DocumentChecklistResponse(
        scheme_id=scheme.id,
        scheme_name=scheme.official_name,
        department=scheme.department,
        required_documents=scheme.required_documents or [],
        official_portal_url=scheme.official_portal_url,
    )
