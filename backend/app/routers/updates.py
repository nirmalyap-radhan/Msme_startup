"""
Official Updates, Gazette Notifications & Announcements API Router.
Provides verified official updates synchronized from Odisha Government gazettes,
Central Ministries, and Public/Private Banking portals.
"""

import math
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.schemas.updates import PaginatedUpdatesResponse, UpdateEventResponse
from app.security.dependencies import get_db
from services.scheme_ingestion.models import UpdateEventModel

router = APIRouter(prefix="/updates", tags=["Updates & Announcements"])


@router.get("", response_model=PaginatedUpdatesResponse)
def list_verified_updates(
    response: Response,
    search: Optional[str] = Query(None, description="Search term in title or summary"),
    update_type: Optional[str] = Query(None, description="Filter by update type, e.g. 'new_scheme', 'amendment', 'policy_gazette', 'bank_product'"),
    source_type: Optional[str] = Query(None, description="Filter by source type, e.g. 'odisha_govt', 'central_govt', 'bank_psu', 'dfi'"),
    category: Optional[str] = Query(None, description="Filter by scheme category"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db)
):
    """
    Retrieves verified scheme updates, notifications, circulars, and amendments.
    Strict Zero-Mock Policy: Returns only verified records backed by official sources.
    Provides server-side pagination, search, category, and source filters.
    """
    query = db.query(UpdateEventModel).filter(UpdateEventModel.is_verified == True)

    if search:
        search_term = f"%{search.strip()}%"
        query = query.filter(
            (UpdateEventModel.title.ilike(search_term)) |
            (UpdateEventModel.summary.ilike(search_term))
        )

    if update_type:
        query = query.filter(UpdateEventModel.update_type == update_type)

    if source_type:
        query = query.filter(UpdateEventModel.source_type == source_type)

    if category:
        query = query.filter(UpdateEventModel.category == category)

    total_count = query.count()
    total_pages = max(1, math.ceil(total_count / limit)) if total_count > 0 else 1

    items = query.order_by(
        UpdateEventModel.publication_date.desc().nullslast(),
        UpdateEventModel.detected_at.desc()
    ).offset((page - 1) * limit).limit(limit).all()

    # Set pagination response headers
    response.headers["X-Total-Count"] = str(total_count)
    response.headers["X-Total-Pages"] = str(total_pages)
    response.headers["X-Current-Page"] = str(page)
    response.headers["X-Page-Size"] = str(limit)

    return PaginatedUpdatesResponse(
        items=[
            UpdateEventResponse(
                id=u.id,
                title=u.title,
                summary=u.summary,
                update_type=u.update_type,
                source_name=u.source_name,
                source_type=u.source_type,
                source_url=u.source_url,
                official_document_url=u.official_document_url,
                publication_date=u.publication_date,
                effective_date=u.effective_date,
                detected_at=u.detected_at,
                scheme_id=u.scheme_id,
                category=u.category or "finance_credit",
                is_verified=u.is_verified,
                verification_notes=u.verification_notes,
            )
            for u in items
        ],
        total=total_count,
        page=page,
        page_size=limit,
        total_pages=total_pages,
        pages=total_pages,
    )


@router.get("/{update_id}", response_model=UpdateEventResponse)
def get_update_detail(
    update_id: str,
    db: Session = Depends(get_db)
):
    """Retrieves full details and provenance for a single verified update record."""
    item = db.query(UpdateEventModel).filter(UpdateEventModel.id == update_id).first()
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Update record '{update_id}' was not found in the verified register."
        )
    return UpdateEventResponse(
        id=item.id,
        title=item.title,
        summary=item.summary,
        update_type=item.update_type,
        source_name=item.source_name,
        source_type=item.source_type,
        source_url=item.source_url,
        official_document_url=item.official_document_url,
        publication_date=item.publication_date,
        effective_date=item.effective_date,
        detected_at=item.detected_at,
        scheme_id=item.scheme_id,
        category=item.category or "finance_credit",
        is_verified=item.is_verified,
        verification_notes=item.verification_notes,
    )
