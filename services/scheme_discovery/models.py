"""
Data schemas and types for the Automated Scheme Discovery Engine.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class SourceType(str, Enum):
    CENTRAL_GOVT = "central_govt"
    ODISHA_GOVT = "odisha_govt"
    BANK_PSU = "bank_psu"
    BANK_PRIVATE = "bank_private"
    DEVELOPMENT_FINANCIAL_INSTITUTION = "dfi"
    CREDIT_GUARANTEE_TRUST = "cgt"


class DiscoveryMethod(str, Enum):
    HTML_DIRECTORY = "html_directory"
    SITEMAP = "sitemap"
    RSS_ATOM = "rss_atom"
    API = "api"
    DOCUMENT_INDEX = "document_index"


class SourceHealthStatus(str, Enum):
    HEALTHY = "healthy"
    FAILING = "failing"
    UNREACHABLE = "unreachable"


class DiscoveredDocumentCandidate(BaseModel):
    title: str
    source_url: str
    official_portal_url: Optional[str] = None
    issuing_authority: str
    source_type: SourceType
    discovery_source_id: str
    discovered_at: datetime = Field(default_factory=datetime.utcnow)
    gazette_or_circular_no: Optional[str] = None
    announcement_date: Optional[str] = None
    effective_date: Optional[str] = None
    application_deadline_text: Optional[str] = None
    category: str = "finance_credit"
    scheme_type: str = "government_scheme"
    interest_rate_published: Optional[str] = None
    max_loan_limit: Optional[str] = None
    collateral_requirement: Optional[str] = None
    update_type: str = "new_scheme"
    raw_metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(from_attributes=True)


class SourceRegistryConfig(BaseModel):
    id: str
    name: str
    source_type: SourceType
    base_url: str
    discovery_endpoint: str
    discovery_method: DiscoveryMethod = DiscoveryMethod.HTML_DIRECTORY
    polling_frequency_hours: int = 24
    is_enabled: bool = True
    headers_config: Dict[str, str] = Field(default_factory=dict)
    notes: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class DiscoveryJobSummary(BaseModel):
    source_id: str
    source_name: str
    checked_at: datetime
    documents_discovered: int
    new_documents_imported: int
    duplicates_skipped: int
    schemes_updated: int
    status: str  # 'success', 'partial', 'failed'
    error_message: Optional[str] = None
