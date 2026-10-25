"""
User-Managed Scheme Application Tracking Router.
Enables entrepreneurs to record application progress, track reference numbers,
and manage submission notes. Strictly user-managed; no fake government syncing.
"""

from typing import List
from uuid import uuid4
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from apps.api.schemas.applications import (
    ApplicationTrackingCreate,
    ApplicationTrackingResponse,
    ApplicationTrackingUpdate,
)
from apps.api.security.dependencies import get_current_user, get_db
from services.scheme_ingestion.models import (
    ApplicationTrackingModel,
    SchemeModel,
    UserProfileModel,
)

router = APIRouter(prefix="/applications", tags=["Application Tracking"])


@router.get("", response_model=List[ApplicationTrackingResponse])
def list_my_applications(
    current_user: UserProfileModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Lists tracked scheme applications for the authenticated user."""
    records = db.query(ApplicationTrackingModel).filter(
        ApplicationTrackingModel.user_id == current_user.id
    ).all()

    response = []
    for r in records:
        scheme_name = r.scheme.official_name if r.scheme else "Official Scheme"
        response.append(
            ApplicationTrackingResponse(
                id=r.id,
                user_id=r.user_id,
                scheme_id=r.scheme_id,
                scheme_name=scheme_name,
                status=r.status,
                acknowledgement_ref=r.acknowledgement_ref,
                submitted_portal_url=r.submitted_portal_url,
                filing_date=r.filing_date,
                notes=r.notes,
                created_at=r.created_at,
                updated_at=r.updated_at,
            )
        )
    return response


@router.post("", response_model=ApplicationTrackingResponse, status_code=status.HTTP_201_CREATED)
def create_application_tracking(
    payload: ApplicationTrackingCreate,
    current_user: UserProfileModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Creates a user-managed tracking record for an application filed on an official portal.
    """
    scheme = db.query(SchemeModel).filter(SchemeModel.id == payload.scheme_id).first()
    if not scheme:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scheme '{payload.scheme_id}' does not exist."
        )

    record_id = f"APP-{uuid4().hex[:8].upper()}"
    tracking_record = ApplicationTrackingModel(
        id=record_id,
        user_id=current_user.id,
        scheme_id=payload.scheme_id,
        status=payload.status,
        acknowledgement_ref=payload.acknowledgement_ref,
        submitted_portal_url=payload.submitted_portal_url or scheme.official_portal_url,
        filing_date=payload.filing_date,
        notes=payload.notes,
    )
    db.add(tracking_record)
    db.commit()
    db.refresh(tracking_record)

    return ApplicationTrackingResponse(
        id=tracking_record.id,
        user_id=tracking_record.user_id,
        scheme_id=tracking_record.scheme_id,
        scheme_name=scheme.official_name,
        status=tracking_record.status,
        acknowledgement_ref=tracking_record.acknowledgement_ref,
        submitted_portal_url=tracking_record.submitted_portal_url,
        filing_date=tracking_record.filing_date,
        notes=tracking_record.notes,
        created_at=tracking_record.created_at,
        updated_at=tracking_record.updated_at,
    )


@router.put("/{tracking_id}", response_model=ApplicationTrackingResponse)
def update_application_tracking(
    tracking_id: str,
    payload: ApplicationTrackingUpdate,
    current_user: UserProfileModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Updates an existing application tracking record owned by the user."""
    record = db.query(ApplicationTrackingModel).filter(
        ApplicationTrackingModel.id == tracking_id,
        ApplicationTrackingModel.user_id == current_user.id
    ).first()

    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application tracking record not found or access denied."
        )

    update_data = payload.model_dump(exclude_unset=True)
    for field, val in update_data.items():
        setattr(record, field, val)

    db.commit()
    db.refresh(record)

    scheme_name = record.scheme.official_name if record.scheme else "Official Scheme"
    return ApplicationTrackingResponse(
        id=record.id,
        user_id=record.user_id,
        scheme_id=record.scheme_id,
        scheme_name=scheme_name,
        status=record.status,
        acknowledgement_ref=record.acknowledgement_ref,
        submitted_portal_url=record.submitted_portal_url,
        filing_date=record.filing_date,
        notes=record.notes,
        created_at=record.created_at,
        updated_at=record.updated_at,
    )
