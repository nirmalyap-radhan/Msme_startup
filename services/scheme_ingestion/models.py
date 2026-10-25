"""
Data models and schemas for Government Scheme Data Ingestion & Verification.
Enforces strict provenance, three-valued eligibility conditions, and versioned lifecycles.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, HttpUrl
from sqlalchemy import (
    Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text, JSON
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class SchemeStatus(str, Enum):
    DISCOVERED = "discovered"
    EXTRACTED = "extracted"
    PENDING_REVIEW = "pending_review"
    VERIFIED = "verified"
    PUBLISHED = "published"
    SUPERSEDED = "superseded"
    EXPIRED = "expired"
    WITHDRAWN = "withdrawn"


class IngestionJobStatus(str, Enum):
    STARTED = "started"
    FETCHED = "fetched"
    EXTRACTED = "extracted"
    NORMALIZED = "normalized"
    FAILED = "failed"
    COMPLETED = "completed"


# ==============================================================================
# Pydantic Schemas (Validation, Serialization & Contracts)
# ==============================================================================

class SourceDocumentSchema(BaseModel):
    document_id: str = Field(default_factory=lambda: str(uuid4()))
    title: str
    source_url: str
    local_path: str
    sha256_hash: str
    mime_type: str = "application/pdf"
    file_size_bytes: int
    retrieved_at_utc: datetime = Field(default_factory=datetime.utcnow)
    page_count: int = 0
    is_scanned: bool = False
    ocr_applied: bool = False

    model_config = ConfigDict(from_attributes=True)


class ExtractedPassageSchema(BaseModel):
    passage_id: str = Field(default_factory=lambda: str(uuid4()))
    document_id: str
    page_number: int
    section_heading: Optional[str] = None
    text_content: str
    character_count: int
    is_ocr: bool = False
    ocr_confidence: Optional[float] = None

    model_config = ConfigDict(from_attributes=True)


class CandidateEligibilityCondition(BaseModel):
    condition_id: str = Field(default_factory=lambda: str(uuid4()))
    attribute_name: str  # e.g., 'enterprise_class', 'investment_plant_machinery', 'sector'
    operator: str  # '=', '!=', '>', '>=', '<', '<=', 'IN', 'NOT IN', 'EXCLUDES'
    value: Any
    description: str
    source_clause: str
    source_page: int


class CandidateBenefit(BaseModel):
    benefit_id: str = Field(default_factory=lambda: str(uuid4()))
    benefit_type: str  # 'interest_subsidy', 'capital_investment_subsidy', 'stamp_duty_exemption', etc.
    formula_description: str
    subsidy_percentage: Optional[float] = None
    max_limit_inr: Optional[float] = None
    duration_years: Optional[int] = None
    source_clause: str
    source_page: int


class CandidateSchemeRecord(BaseModel):
    scheme_id: str = Field(default_factory=lambda: f"OD-MSME-{uuid4().hex[:8].upper()}")
    official_name: str
    official_name_odia: Optional[str] = None
    department: str = "Department of MSME, Government of Odisha"
    implementing_agency: Optional[str] = "Directorate of Industries, Odisha / DICs"
    jurisdiction: str = "Odisha"  # 'Odisha' or 'Central'
    source_url: str
    source_document_id: str
    document_sha256: str
    summary: str
    status: SchemeStatus = SchemeStatus.EXTRACTED
    version: str = "1.0"
    effective_date: Optional[str] = None
    expiry_date: Optional[str] = None
    candidate_eligibility: List[CandidateEligibilityCondition] = Field(default_factory=list)
    candidate_benefits: List[CandidateBenefit] = Field(default_factory=list)
    required_documents: List[str] = Field(default_factory=list)
    application_process: Optional[str] = None
    official_portal_url: Optional[str] = None
    extracted_at: datetime = Field(default_factory=datetime.utcnow)
    supersedes_scheme_id: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ReviewEventSchema(BaseModel):
    review_id: str = Field(default_factory=lambda: str(uuid4()))
    scheme_id: str
    reviewer_id: str
    reviewer_name: str
    action: str  # 'APPROVE_PUBLICATION', 'REJECT', 'REQUEST_AMENDMENT'
    notes: str
    verified_fields: Dict[str, Any] = Field(default_factory=dict)
    reviewed_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = ConfigDict(from_attributes=True)


class PublishedSchemeRecord(BaseModel):
    scheme_id: str
    official_name: str
    official_name_odia: Optional[str] = None
    department: str
    implementing_agency: Optional[str]
    jurisdiction: str
    source_url: str
    source_document_id: str
    document_sha256: str
    summary: str
    status: SchemeStatus = SchemeStatus.PUBLISHED
    version: str
    effective_date: Optional[str]
    expiry_date: Optional[str]
    eligibility_rules: List[CandidateEligibilityCondition]
    benefits: List[CandidateBenefit]
    required_documents: List[str]
    application_process: Optional[str]
    official_portal_url: Optional[str]
    published_at: datetime
    last_verified_at: datetime
    verified_by_reviewer: str
    verification_notes: str

    model_config = ConfigDict(from_attributes=True)


class IngestionJobRecord(BaseModel):
    job_id: str = Field(default_factory=lambda: str(uuid4()))
    source_url: str
    status: IngestionJobStatus = IngestionJobStatus.STARTED
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    document_id: Optional[str] = None
    scheme_id: Optional[str] = None
    extraction_stats: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(from_attributes=True)


# ==============================================================================
# SQLAlchemy ORM Models (Relational Persistence)
# ==============================================================================

class SourceDocumentModel(Base):
    __tablename__ = "source_documents"

    id = Column(String(64), primary_key=True)
    title = Column(String(512), nullable=False)
    source_url = Column(Text, nullable=False)
    local_path = Column(Text, nullable=False)
    sha256_hash = Column(String(64), nullable=False, unique=True, index=True)
    mime_type = Column(String(64), default="application/pdf")
    file_size_bytes = Column(Integer, nullable=False)
    retrieved_at_utc = Column(DateTime, default=datetime.utcnow)
    page_count = Column(Integer, default=0)
    is_scanned = Column(Boolean, default=False)
    ocr_applied = Column(Boolean, default=False)

    passages = relationship("DocumentPassageModel", back_populates="document", cascade="all, delete-orphan")
    schemes = relationship("SchemeModel", back_populates="source_document")


class DocumentPassageModel(Base):
    __tablename__ = "document_passages"

    id = Column(String(64), primary_key=True)
    document_id = Column(String(64), ForeignKey("source_documents.id"), nullable=False, index=True)
    page_number = Column(Integer, nullable=False, index=True)
    section_heading = Column(String(256), nullable=True)
    text_content = Column(Text, nullable=False)
    character_count = Column(Integer, default=0)
    is_ocr = Column(Boolean, default=False)
    ocr_confidence = Column(Float, nullable=True)

    document = relationship("SourceDocumentModel", back_populates="passages")


class SchemeModel(Base):
    __tablename__ = "schemes"

    id = Column(String(64), primary_key=True)
    official_name = Column(String(512), nullable=False, index=True)
    official_name_odia = Column(String(512), nullable=True)
    department = Column(String(256), nullable=False)
    implementing_agency = Column(String(256), nullable=True)
    jurisdiction = Column(String(64), default="Odisha", index=True)
    source_url = Column(Text, nullable=False)
    source_document_id = Column(String(64), ForeignKey("source_documents.id"), nullable=False)
    document_sha256 = Column(String(64), nullable=False)
    summary = Column(Text, nullable=False)
    status = Column(String(32), default=SchemeStatus.EXTRACTED.value, index=True)
    version = Column(String(16), default="1.0")
    effective_date = Column(String(32), nullable=True)
    expiry_date = Column(String(32), nullable=True)
    required_documents = Column(JSON, default=list)
    application_process = Column(Text, nullable=True)
    official_portal_url = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    published_at = Column(DateTime, nullable=True)
    verified_by_reviewer = Column(String(128), nullable=True)
    verification_notes = Column(Text, nullable=True)
    supersedes_scheme_id = Column(String(64), nullable=True)

    source_document = relationship("SourceDocumentModel", back_populates="schemes")
    eligibility_rules = relationship("EligibilityRuleModel", back_populates="scheme", cascade="all, delete-orphan")
    benefits = relationship("BenefitRuleModel", back_populates="scheme", cascade="all, delete-orphan")
    review_events = relationship("ReviewEventModel", back_populates="scheme", cascade="all, delete-orphan")


class EligibilityRuleModel(Base):
    __tablename__ = "eligibility_rules"

    id = Column(String(64), primary_key=True)
    scheme_id = Column(String(64), ForeignKey("schemes.id"), nullable=False, index=True)
    attribute_name = Column(String(64), nullable=False, index=True)
    operator = Column(String(16), nullable=False)
    value_json = Column(JSON, nullable=False)
    description = Column(Text, nullable=False)
    source_clause = Column(String(256), nullable=False)
    source_page = Column(Integer, nullable=False)
    is_verified = Column(Boolean, default=False)

    scheme = relationship("SchemeModel", back_populates="eligibility_rules")


class BenefitRuleModel(Base):
    __tablename__ = "benefit_rules"

    id = Column(String(64), primary_key=True)
    scheme_id = Column(String(64), ForeignKey("schemes.id"), nullable=False, index=True)
    benefit_type = Column(String(64), nullable=False)
    formula_description = Column(Text, nullable=False)
    subsidy_percentage = Column(Float, nullable=True)
    max_limit_inr = Column(Float, nullable=True)
    duration_years = Column(Integer, nullable=True)
    source_clause = Column(String(256), nullable=False)
    source_page = Column(Integer, nullable=False)
    is_verified = Column(Boolean, default=False)

    scheme = relationship("SchemeModel", back_populates="benefits")


class ReviewEventModel(Base):
    __tablename__ = "review_events"

    id = Column(String(64), primary_key=True)
    scheme_id = Column(String(64), ForeignKey("schemes.id"), nullable=False, index=True)
    reviewer_id = Column(String(64), nullable=False)
    reviewer_name = Column(String(128), nullable=False)
    action = Column(String(32), nullable=False)
    notes = Column(Text, nullable=False)
    verified_fields = Column(JSON, default=dict)
    reviewed_at = Column(DateTime, default=datetime.utcnow)

    scheme = relationship("SchemeModel", back_populates="review_events")


class IngestionJobModel(Base):
    __tablename__ = "ingestion_jobs"

    id = Column(String(64), primary_key=True)
    source_url = Column(Text, nullable=False)
    status = Column(String(32), default=IngestionJobStatus.STARTED.value, index=True)
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)
    document_id = Column(String(64), nullable=True)
    scheme_id = Column(String(64), nullable=True)
    extraction_stats = Column(JSON, default=dict)


class UserProfileModel(Base):
    __tablename__ = "user_profiles"

    id = Column(String(64), primary_key=True)
    email = Column(String(128), unique=True, nullable=False, index=True)
    hashed_password = Column(String(256), nullable=False)
    role = Column(String(32), default="entrepreneur", index=True)  # entrepreneur, facilitator, scheme_reviewer, platform_admin
    enterprise_name = Column(String(256), nullable=True)
    enterprise_class = Column(String(32), nullable=True)  # micro, small, medium
    sector = Column(String(64), nullable=True)  # manufacturing, service, agro-processing, etc.
    state = Column(String(64), default="Odisha")
    district = Column(String(64), nullable=True)
    udyam_number = Column(String(64), nullable=True)
    udyam_registered = Column(Boolean, default=False)
    production_status = Column(String(32), default="commenced")
    investment_plant_machinery = Column(Float, nullable=True)
    annual_turnover = Column(Float, nullable=True)
    promoter_category = Column(String(32), default="general")
    promoter_gender = Column(String(32), default="male")
    working_capital_loan_sanctioned = Column(Float, nullable=True)
    annual_interest_paid = Column(Float, nullable=True)
    trademark_expenditure = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    saved_schemes = relationship("SavedSchemeModel", back_populates="user", cascade="all, delete-orphan")
    applications = relationship("ApplicationTrackingModel", back_populates="user", cascade="all, delete-orphan")


class SavedSchemeModel(Base):
    __tablename__ = "saved_schemes"

    id = Column(String(64), primary_key=True)
    user_id = Column(String(64), ForeignKey("user_profiles.id"), nullable=False, index=True)
    scheme_id = Column(String(64), ForeignKey("schemes.id"), nullable=False, index=True)
    saved_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("UserProfileModel", back_populates="saved_schemes")
    scheme = relationship("SchemeModel")


class ApplicationTrackingModel(Base):
    __tablename__ = "application_tracking"

    id = Column(String(64), primary_key=True)
    user_id = Column(String(64), ForeignKey("user_profiles.id"), nullable=False, index=True)
    scheme_id = Column(String(64), ForeignKey("schemes.id"), nullable=False, index=True)
    status = Column(String(32), default="draft")  # draft, submitted_to_department, under_scrutiny, query_raised, approved, rejected
    acknowledgement_ref = Column(String(128), nullable=True)
    submitted_portal_url = Column(Text, nullable=True)
    filing_date = Column(String(32), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("UserProfileModel", back_populates="applications")
    scheme = relationship("SchemeModel")

