"""
Pydantic API Schemas for User-Managed Scheme Application Tracking.
"""

from datetime import datetime
from typing import Literal, Optional
from pydantic import BaseModel, ConfigDict, Field

ApplicationStatus = Literal[
    "draft",
    "submitted",
    "submitted_to_department",
    "under_scrutiny",
    "query_raised",
    "queried",
    "approved",
    "rejected",
    "disbursed",
]


class ApplicationTrackingCreate(BaseModel):
    scheme_id: str
    status: ApplicationStatus = "draft"
    acknowledgement_ref: Optional[str] = None
    submitted_portal_url: Optional[str] = None
    filing_date: Optional[str] = None
    notes: Optional[str] = None


class ApplicationTrackingUpdate(BaseModel):
    status: Optional[ApplicationStatus] = None
    acknowledgement_ref: Optional[str] = None
    submitted_portal_url: Optional[str] = None
    filing_date: Optional[str] = None
    notes: Optional[str] = None


class ApplicationTrackingResponse(BaseModel):
    id: str
    user_id: str
    scheme_id: str
    scheme_name: str
    status: str
    acknowledgement_ref: Optional[str] = None
    submitted_portal_url: Optional[str] = None
    filing_date: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    disclaimer: str = "This tracking record is user-managed. Official processing occurs directly on government portals."

    model_config = ConfigDict(from_attributes=True)
