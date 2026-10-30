"""
Scheme Catalogue & Document Provenance API Router.
Enforces zero-mock production data: returns only verified, published government scheme records.
"""

import math
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import and_, cast, String
from sqlalchemy.orm import Session

from app.schemas.schemes import (
    DocumentChecklistResponse,
    PaginatedSchemesResponse,
    SchemeDetailResponse,
    SchemeSummaryResponse,
    VerifiedBenefitResponse,
    VerifiedRuleResponse,
)
from app.security.dependencies import get_db
from services.scheme_ingestion.models import (
    BenefitRuleModel,
    EligibilityRuleModel,
    SchemeModel,
    SchemeStatus,
    SourceDocumentModel,
)

router = APIRouter(prefix="/schemes", tags=["Schemes"])


def _build_schemes_query(
    db: Session,
    search: Optional[str] = None,
    sector: Optional[str] = None,
    enterprise_class: Optional[str] = None,
    category: Optional[str] = None,
    jurisdiction: Optional[str] = None,
    scheme_type: Optional[str] = None,
    application_status: Optional[str] = None,
    claim_status: Optional[str] = None,
    organization: Optional[str] = None,
    is_rolling: Optional[bool] = None,
):
    query = db.query(SchemeModel).filter(SchemeModel.status == SchemeStatus.PUBLISHED.value)

    if search:
        search_term = f"%{search.strip()}%"
        query = query.filter(
            (SchemeModel.official_name.ilike(search_term)) |
            (SchemeModel.summary.ilike(search_term))
        )

    if category:
        query = query.filter(SchemeModel.category == category)

    if jurisdiction and jurisdiction.lower() != "all":
        query = query.filter(SchemeModel.jurisdiction.ilike(f"%{jurisdiction.strip()}%"))

    if scheme_type and scheme_type.lower() != "all":
        query = query.filter(SchemeModel.scheme_type == scheme_type.strip())

    if application_status:
        query = query.filter(SchemeModel.application_status == application_status)

    if claim_status:
        query = query.filter(SchemeModel.claim_status == claim_status)

    if organization:
        query = query.filter(SchemeModel.organization.ilike(f"%{organization}%"))

    if is_rolling is not None:
        query = query.filter(SchemeModel.is_rolling == is_rolling)

    if sector:
        sec_clean = sector.lower().strip()
        is_service = ("service" in sec_clean or sec_clean in (
            "it_services", "hospitality", "healthcare", "education",
            "logistics", "retail_trade", "repair_services", "handicrafts",
            "professional_services", "beauty_wellness", "food_services",
            "construction_services", "renewable_services", "agro_allied_services",
            "printing_media", "automobile_services", "other"
        ))
        if is_service:
            query = query.filter(SchemeModel.eligibility_rules.any(and_(
                EligibilityRuleModel.attribute_name == "sector",
                (
                    cast(EligibilityRuleModel.value_json, String).ilike("%service%") |
                    cast(EligibilityRuleModel.value_json, String).ilike(f"%{sec_clean}%")
                )
            )))
        else:
            query = query.filter(SchemeModel.eligibility_rules.any(and_(
                EligibilityRuleModel.attribute_name == "sector",
                cast(EligibilityRuleModel.value_json, String).ilike(f"%{sec_clean}%")
            )))

    if enterprise_class:
        cls_clean = enterprise_class.lower().strip()
        is_micro_hierarchy = cls_clean in ("nano", "nano_sub50k", "ultra_micro", "tiny", "micro_tiny", "cottage", "micro")
        if is_micro_hierarchy:
            query = query.filter(SchemeModel.eligibility_rules.any(and_(
                EligibilityRuleModel.attribute_name == "enterprise_class",
                (
                    cast(EligibilityRuleModel.value_json, String).ilike("%micro%") |
                    cast(EligibilityRuleModel.value_json, String).ilike(f"%{cls_clean}%")
                )
            )))
        else:
            query = query.filter(SchemeModel.eligibility_rules.any(and_(
                EligibilityRuleModel.attribute_name == "enterprise_class",
                cast(EligibilityRuleModel.value_json, String).ilike(f"%{cls_clean}%")
            )))

    return query


def _serialize_scheme_summary(s: SchemeModel) -> SchemeSummaryResponse:
    return SchemeSummaryResponse(
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
        category=s.category or "finance_credit",
        organization=s.organization,
        scheme_type=s.scheme_type or "government_scheme",
        interest_rate_published=s.interest_rate_published,
        max_loan_limit=s.max_loan_limit,
        collateral_requirement=s.collateral_requirement,
        application_status=s.application_status or "unknown",
        claim_status=s.claim_status or "unknown",
        application_start_date=s.application_start_date,
        application_deadline=s.application_deadline,
        claim_deadline=s.claim_deadline,
        is_rolling=s.is_rolling or False,
        financial_year_cycle=s.financial_year_cycle,
        last_verified_at=s.last_verified_at,
        official_application_url=s.official_application_url,
        official_guidelines_url=s.official_guidelines_url,
        official_notification_url=s.official_notification_url,
        confidence_score=s.confidence_score or 1.0,
        source_url=s.source_url,
        document_sha256=s.document_sha256,
        published_at=s.published_at,
    )


@router.get("", response_model=List[SchemeSummaryResponse])
def list_published_schemes(
    response: Response,
    search: Optional[str] = Query(None, description="Search keyword in scheme title or summary"),
    sector: Optional[str] = Query(None, description="Filter by sector, e.g. 'manufacturing'"),
    enterprise_class: Optional[str] = Query(None, description="Filter by enterprise class ('micro', 'small', 'medium')"),
    category: Optional[str] = Query(None, description="Filter by category (e.g. 'finance_credit', 'subsidy_incentives')"),
    jurisdiction: Optional[str] = Query(None, description="Filter by jurisdiction ('Odisha', 'Central')"),
    scheme_type: Optional[str] = Query(None, description="Filter by scheme type ('government_scheme', 'bank_product')"),
    application_status: Optional[str] = Query(None, description="Filter by application status (e.g. 'open', 'closing_soon', 'closed')"),
    claim_status: Optional[str] = Query(None, description="Filter by claim status (e.g. 'claims_open', 'rolling_claims')"),
    organization: Optional[str] = Query(None, description="Filter by issuing organization (e.g. 'SBI', 'SIDBI', 'Ministry of MSME')"),
    is_rolling: Optional[bool] = Query(None, description="Filter by rolling availability"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db)
):
    """
    Retrieves published schemes from the verified government & banking catalogue.
    CRITICAL NO-MOCK RULE: Queries return only records where status == 'published'.
    Sets pagination response headers X-Total-Count, X-Total-Pages, X-Current-Page, X-Page-Size.
    """
    query = _build_schemes_query(
        db=db,
        search=search,
        sector=sector,
        enterprise_class=enterprise_class,
        category=category,
        jurisdiction=jurisdiction,
        scheme_type=scheme_type,
        application_status=application_status,
        claim_status=claim_status,
        organization=organization,
        is_rolling=is_rolling,
    )

    total_count = query.distinct().count()
    total_pages = max(1, math.ceil(total_count / limit)) if total_count > 0 else 1

    response.headers["X-Total-Count"] = str(total_count)
    response.headers["X-Total-Pages"] = str(total_pages)
    response.headers["X-Current-Page"] = str(page)
    response.headers["X-Page-Size"] = str(limit)

    records = query.distinct().offset((page - 1) * limit).limit(limit).all()
    return [_serialize_scheme_summary(s) for s in records]


@router.get("/paginated", response_model=PaginatedSchemesResponse)
def list_published_schemes_paginated(
    search: Optional[str] = Query(None, description="Search keyword in scheme title or summary"),
    sector: Optional[str] = Query(None, description="Filter by sector, e.g. 'manufacturing'"),
    enterprise_class: Optional[str] = Query(None, description="Filter by enterprise class ('micro', 'small', 'medium')"),
    category: Optional[str] = Query(None, description="Filter by category (e.g. 'finance_credit', 'subsidy_incentives')"),
    jurisdiction: Optional[str] = Query(None, description="Filter by jurisdiction ('Odisha', 'Central')"),
    scheme_type: Optional[str] = Query(None, description="Filter by scheme type ('government_scheme', 'bank_product')"),
    application_status: Optional[str] = Query(None, description="Filter by application status (e.g. 'open', 'closing_soon', 'closed')"),
    claim_status: Optional[str] = Query(None, description="Filter by claim status (e.g. 'claims_open', 'rolling_claims')"),
    organization: Optional[str] = Query(None, description="Filter by issuing organization (e.g. 'SBI', 'SIDBI', 'Ministry of MSME')"),
    is_rolling: Optional[bool] = Query(None, description="Filter by rolling availability"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db)
):
    """Returns schemes with an explicit pagination JSON envelope."""
    query = _build_schemes_query(
        db=db,
        search=search,
        sector=sector,
        enterprise_class=enterprise_class,
        category=category,
        jurisdiction=jurisdiction,
        scheme_type=scheme_type,
        application_status=application_status,
        claim_status=claim_status,
        organization=organization,
        is_rolling=is_rolling,
    )

    total_count = query.distinct().count()
    total_pages = max(1, math.ceil(total_count / limit)) if total_count > 0 else 1
    records = query.distinct().offset((page - 1) * limit).limit(limit).all()

    return PaginatedSchemesResponse(
        items=[_serialize_scheme_summary(s) for s in records],
        total=total_count,
        page=page,
        page_size=limit,
        total_pages=total_pages,
    )


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
        category=scheme.category or "finance_credit",
        organization=scheme.organization,
        scheme_type=scheme.scheme_type or "government_scheme",
        interest_rate_published=scheme.interest_rate_published,
        max_loan_limit=scheme.max_loan_limit,
        collateral_requirement=scheme.collateral_requirement,
        application_status=scheme.application_status or "unknown",
        claim_status=scheme.claim_status or "unknown",
        application_start_date=scheme.application_start_date,
        application_deadline=scheme.application_deadline,
        claim_deadline=scheme.claim_deadline,
        is_rolling=scheme.is_rolling or False,
        financial_year_cycle=scheme.financial_year_cycle,
        last_verified_at=scheme.last_verified_at,
        official_application_url=scheme.official_application_url,
        official_guidelines_url=scheme.official_guidelines_url,
        official_notification_url=scheme.official_notification_url,
        confidence_score=scheme.confidence_score or 1.0,
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
