"""
Pydantic API Schemas for Schemes and Provenance.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class SchemeSummaryResponse(BaseModel):
    scheme_id: str
    official_name: str
    official_name_odia: Optional[str] = None
    department: str
    implementing_agency: Optional[str] = None
    jurisdiction: str
    summary: str
    status: str
    version: str
    effective_date: Optional[str] = None
    expiry_date: Optional[str] = None
    category: str = "finance_credit"
    organization: Optional[str] = None
    scheme_type: str = "government_scheme"
    interest_rate_published: Optional[str] = None
    max_loan_limit: Optional[str] = None
    collateral_requirement: Optional[str] = None
    application_status: str = "unknown"
    claim_status: str = "unknown"
    application_start_date: Optional[datetime] = None
    application_deadline: Optional[datetime] = None
    claim_deadline: Optional[datetime] = None
    is_rolling: bool = False
    financial_year_cycle: Optional[str] = None
    last_verified_at: Optional[datetime] = None
    official_application_url: Optional[str] = None
    official_guidelines_url: Optional[str] = None
    official_notification_url: Optional[str] = None
    confidence_score: float = 1.0
    source_url: str
    document_sha256: str
    published_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class PaginatedSchemesResponse(BaseModel):
    items: List[SchemeSummaryResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class VerifiedRuleResponse(BaseModel):
    rule_id: str
    attribute_name: str
    operator: str
    value: Any
    description: str
    source_clause: str
    source_page: int
    is_verified: bool

    model_config = ConfigDict(from_attributes=True)


class VerifiedBenefitResponse(BaseModel):
    benefit_id: str
    benefit_type: str
    formula_description: str
    subsidy_percentage: Optional[float] = None
    max_limit_inr: Optional[float] = None
    duration_years: Optional[int] = None
    source_clause: str
    source_page: int
    is_verified: bool

    model_config = ConfigDict(from_attributes=True)


class SchemeDetailResponse(BaseModel):
    scheme_id: str
    official_name: str
    official_name_odia: Optional[str] = None
    department: str
    implementing_agency: Optional[str] = None
    jurisdiction: str
    source_url: str
    document_sha256: str
    summary: str
    status: str
    version: str
    effective_date: Optional[str] = None
    expiry_date: Optional[str] = None
    category: str = "finance_credit"
    organization: Optional[str] = None
    scheme_type: str = "government_scheme"
    interest_rate_published: Optional[str] = None
    max_loan_limit: Optional[str] = None
    collateral_requirement: Optional[str] = None
    application_status: str = "unknown"
    claim_status: str = "unknown"
    application_start_date: Optional[datetime] = None
    application_deadline: Optional[datetime] = None
    claim_deadline: Optional[datetime] = None
    is_rolling: bool = False
    financial_year_cycle: Optional[str] = None
    last_verified_at: Optional[datetime] = None
    official_application_url: Optional[str] = None
    official_guidelines_url: Optional[str] = None
    official_notification_url: Optional[str] = None
    confidence_score: float = 1.0
    verified_eligibility_rules: List[VerifiedRuleResponse] = Field(default_factory=list)
    verified_benefits: List[VerifiedBenefitResponse] = Field(default_factory=list)
    required_documents: List[str] = Field(default_factory=list)
    application_process: Optional[str] = None
    official_portal_url: Optional[str] = None
    published_at: Optional[datetime] = None
    verified_by_reviewer: Optional[str] = None
    verification_notes: Optional[str] = None
    disclaimer: str = "This information is derived from official government publications. Final eligibility and approvals are decided solely by the competent departmental authorities."

    model_config = ConfigDict(from_attributes=True)


class DocumentChecklistResponse(BaseModel):
    scheme_id: str
    scheme_name: str
    department: str
    required_documents: List[str]
    official_portal_url: Optional[str]
    disclaimer: str = "Documents must be submitted through the official government application portal."

    model_config = ConfigDict(from_attributes=True)
