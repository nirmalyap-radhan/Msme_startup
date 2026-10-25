"""
Domain rules, evaluation outcomes, and condition schemas for the Deterministic Eligibility Engine.
Enforces Three-Valued Logic (True, False, Unknown) and full clause-level traceability.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class ThreeValuedResult(str, Enum):
    TRUE = "TRUE"
    FALSE = "FALSE"
    UNKNOWN = "UNKNOWN"


class EligibilityOutcome(str, Enum):
    POTENTIAL_MATCH = "potential_match"
    MORE_INFORMATION_REQUIRED = "more_information_required"
    NOT_ELIGIBLE_UNDER_VERIFIED_RULES = "not_eligible_under_verified_rules"
    RULES_UNVERIFIED = "rules_unverified"


class ConditionEvaluationResult(BaseModel):
    condition_id: str
    attribute_name: str
    operator: str
    required_value: Any
    applicant_value: Any
    result: ThreeValuedResult
    reasoning: str
    source_clause: str
    source_page: int
    is_verified: bool = True
    followup_question: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class BenefitCalculationResult(BaseModel):
    status: str  # 'calculated', 'insufficient_inputs', 'not_applicable'
    benefit_type: str
    estimated_amount_inr: Optional[float] = None
    subsidy_percentage: Optional[float] = None
    max_limit_inr: Optional[float] = None
    duration_years: Optional[int] = None
    applied_formula: str
    missing_inputs: List[str] = Field(default_factory=list)
    assumptions_notes: str
    source_clause: str
    source_page: int

    model_config = ConfigDict(from_attributes=True)


class EligibilityAssessment(BaseModel):
    scheme_id: str
    scheme_name: str
    department: str
    jurisdiction: str
    source_url: str
    outcome: EligibilityOutcome
    summary_reason: str
    conditions_passed: List[ConditionEvaluationResult] = Field(default_factory=list)
    conditions_failed: List[ConditionEvaluationResult] = Field(default_factory=list)
    conditions_unknown: List[ConditionEvaluationResult] = Field(default_factory=list)
    targeted_followup_questions: List[Dict[str, Any]] = Field(default_factory=list)
    benefit_estimates: List[BenefitCalculationResult] = Field(default_factory=list)
    evaluated_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = ConfigDict(from_attributes=True)
