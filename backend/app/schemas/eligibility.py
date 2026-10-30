"""
Pydantic API Schemas for Deterministic Eligibility Evaluation.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field

from services.eligibility.rules import (
    BenefitCalculationResult,
    ConditionEvaluationResult,
    EligibilityOutcome,
)


class ApplicantProfileInput(BaseModel):
    enterprise_name: Optional[str] = None
    enterprise_class: Optional[str] = None  # 'micro', 'small', 'medium'
    sector: Optional[str] = None  # 'manufacturing', 'service', 'agro-processing', etc.
    state: Optional[str] = "Odisha"
    district: Optional[str] = None
    udyam_registered: Optional[bool] = None
    production_status: Optional[str] = None  # 'commenced', 'proposed'
    investment_plant_machinery: Optional[float] = None
    annual_turnover: Optional[float] = None
    promoter_category: Optional[str] = "general"
    promoter_gender: Optional[str] = "male"
    working_capital_loan_sanctioned: Optional[float] = None
    annual_interest_paid: Optional[float] = None
    trademark_expenditure: Optional[float] = None

    model_config = ConfigDict(from_attributes=True)


class EligibilityEvaluationRequest(BaseModel):
    scheme_id: Optional[str] = None  # If omitted, evaluates all published schemes
    profile: ApplicantProfileInput


class SingleSchemeAssessmentResponse(BaseModel):
    scheme_id: str
    scheme_name: str
    department: str
    jurisdiction: str
    source_url: str
    outcome: EligibilityOutcome
    benefit_status: str = "status_unverified"
    application_status: str = "unknown"
    claim_status: str = "unknown"
    is_claimable: bool = False
    summary_reason: str
    conditions_passed: List[ConditionEvaluationResult] = Field(default_factory=list)
    conditions_failed: List[ConditionEvaluationResult] = Field(default_factory=list)
    conditions_unknown: List[ConditionEvaluationResult] = Field(default_factory=list)
    targeted_followup_questions: List[Dict[str, Any]] = Field(default_factory=list)
    benefit_estimates: List[BenefitCalculationResult] = Field(default_factory=list)
    disclaimer: str = "Preliminary advisory assessment based on verified scheme guidelines. Final eligibility, sanction, reimbursement, and disbursement remain subject to administering institution rules, scrutiny, and approval."

    model_config = ConfigDict(from_attributes=True)


class BatchEligibilityResponse(BaseModel):
    total_evaluated: int
    eligible_count: int
    more_info_count: int
    ineligible_count: int
    assessments: List[SingleSchemeAssessmentResponse]
