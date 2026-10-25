"""
Deterministic Eligibility Evaluation Router.
Executes three-valued rules evaluation with line-by-line reasoning traces,
formula-based benefit calculations, and targeted follow-up question generation.
"""

from typing import List, Union
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from apps.api.schemas.eligibility import (
    BatchEligibilityResponse,
    EligibilityEvaluationRequest,
    SingleSchemeAssessmentResponse,
)
from apps.api.security.dependencies import get_db
from services.eligibility.evaluator import DeterministicEligibilityEvaluator
from services.eligibility.rules import EligibilityOutcome
from services.scheme_ingestion.models import SchemeModel, SchemeStatus

router = APIRouter(prefix="/eligibility", tags=["Eligibility Engine"])


@router.post("/evaluate", response_model=Union[SingleSchemeAssessmentResponse, BatchEligibilityResponse])
def evaluate_eligibility(
    payload: EligibilityEvaluationRequest,
    db: Session = Depends(get_db)
):
    """
    Evaluates an MSME profile against verified government schemes.
    Uses three-valued deterministic logic. If information is missing, returns MORE_INFORMATION_REQUIRED
    with targeted follow-up questions. Never fabricates eligibility or subsidy numbers.
    """
    profile_dict = payload.profile.model_dump(exclude_unset=True)

    # 1. Single Scheme Evaluation
    if payload.scheme_id:
        scheme = db.query(SchemeModel).filter(
            SchemeModel.id == payload.scheme_id,
            SchemeModel.status == SchemeStatus.PUBLISHED.value
        ).first()

        if not scheme:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Scheme '{payload.scheme_id}' was not found in the published catalogue."
            )

        assessment = DeterministicEligibilityEvaluator.evaluate_scheme(scheme, profile_dict)
        return SingleSchemeAssessmentResponse(
            scheme_id=assessment.scheme_id,
            scheme_name=assessment.scheme_name,
            department=assessment.department,
            jurisdiction=assessment.jurisdiction,
            source_url=assessment.source_url,
            outcome=assessment.outcome,
            benefit_status=assessment.benefit_status.value if hasattr(assessment.benefit_status, "value") else str(assessment.benefit_status),
            application_status=assessment.application_status,
            claim_status=assessment.claim_status,
            is_claimable=assessment.is_claimable,
            summary_reason=assessment.summary_reason,
            conditions_passed=assessment.conditions_passed,
            conditions_failed=assessment.conditions_failed,
            conditions_unknown=assessment.conditions_unknown,
            targeted_followup_questions=assessment.targeted_followup_questions,
            benefit_estimates=assessment.benefit_estimates,
        )

    # 2. Batch Evaluation across all published schemes
    published_schemes = db.query(SchemeModel).filter(
        SchemeModel.status == SchemeStatus.PUBLISHED.value
    ).all()

    assessments: List[SingleSchemeAssessmentResponse] = []
    eligible_count = 0
    more_info_count = 0
    ineligible_count = 0

    for scheme in published_schemes:
        a = DeterministicEligibilityEvaluator.evaluate_scheme(scheme, profile_dict)
        if a.outcome == EligibilityOutcome.POTENTIAL_MATCH:
            eligible_count += 1
        elif a.outcome == EligibilityOutcome.MORE_INFORMATION_REQUIRED:
            more_info_count += 1
        elif a.outcome == EligibilityOutcome.NOT_ELIGIBLE_UNDER_VERIFIED_RULES:
            ineligible_count += 1

        assessments.append(
            SingleSchemeAssessmentResponse(
                scheme_id=a.scheme_id,
                scheme_name=a.scheme_name,
                department=a.department,
                jurisdiction=a.jurisdiction,
                source_url=a.source_url,
                outcome=a.outcome,
                benefit_status=a.benefit_status.value if hasattr(a.benefit_status, "value") else str(a.benefit_status),
                application_status=a.application_status,
                claim_status=a.claim_status,
                is_claimable=a.is_claimable,
                summary_reason=a.summary_reason,
                conditions_passed=a.conditions_passed,
                conditions_failed=a.conditions_failed,
                conditions_unknown=a.conditions_unknown,
                targeted_followup_questions=a.targeted_followup_questions,
                benefit_estimates=a.benefit_estimates,
            )
        )

    return BatchEligibilityResponse(
        total_evaluated=len(assessments),
        eligible_count=eligible_count,
        more_info_count=more_info_count,
        ineligible_count=ineligible_count,
        assessments=assessments,
    )
