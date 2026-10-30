"""
Schemas and types for the Deadline and Availability Monitoring Service.
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field

from services.scheme_ingestion.models import ApplicationStatus, ClaimStatus


class DeadlineStatusEvaluation(BaseModel):
    scheme_id: str
    scheme_name: str
    application_status: ApplicationStatus
    claim_status: ClaimStatus
    days_until_application_deadline: Optional[int] = None
    days_until_claim_deadline: Optional[int] = None
    is_rolling: bool = False
    status_changed: bool = False
    alerts_generated: List[str] = Field(default_factory=list)
    reconciliation_notes: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class DeadlineAlertItem(BaseModel):
    alert_id: str
    scheme_id: str
    scheme_name: str
    alert_type: str
    days_remaining: Optional[int]
    target_date: Optional[datetime]
    message: str
    is_dismissed: bool = False
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DeadlineMonitoringCycleSummary(BaseModel):
    evaluated_at: datetime
    total_schemes_checked: int
    open_schemes: int
    closing_soon_schemes: int
    closed_schemes: int
    rolling_schemes: int
    claims_open_schemes: int
    new_alerts_created: int
    status_transitions_count: int
