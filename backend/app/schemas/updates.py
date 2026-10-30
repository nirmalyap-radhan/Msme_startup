"""
Pydantic Schemas for Official Scheme Updates, Gazette Notifications, and Announcements.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class UpdateEventResponse(BaseModel):
    id: str
    title: str
    summary: str
    update_type: str
    source_name: str
    source_type: str
    source_url: str
    official_document_url: Optional[str] = None
    publication_date: Optional[datetime] = None
    effective_date: Optional[str] = None
    detected_at: datetime
    scheme_id: Optional[str] = None
    category: str = "finance_credit"
    is_verified: bool = True
    verification_notes: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class PaginatedUpdatesResponse(BaseModel):
    items: List[UpdateEventResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
    pages: Optional[int] = None
