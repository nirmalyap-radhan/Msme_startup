"""
Privileged Administrator & Reviewer Governance Router.
Protected by RBAC: accessible only to users with role 'scheme_reviewer' or 'platform_admin'.
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from apps.api.security.dependencies import require_role
from services.scheme_ingestion.models import UserProfileModel
from services.scheme_ingestion.reviewer import SchemeReviewWorkflow

router = APIRouter(prefix="/admin", tags=["Admin & Reviewer Governance"])


class VerifySchemePayload(BaseModel):
    notes: str = Field(min_length=10, description="Audit verification notes confirming check against official notification.")
    verified_overrides: Dict[str, Any] = Field(default_factory=dict)


class RejectSchemePayload(BaseModel):
    reason: str = Field(min_length=5, description="Reason for rejecting the discovered document or candidate scheme.")


class UpdateLifecyclePayload(BaseModel):
    application_status: Optional[str] = None
    claim_status: Optional[str] = None
    application_deadline: Optional[str] = None
    claim_deadline: Optional[str] = None
    is_rolling: Optional[bool] = None
    official_application_url: Optional[str] = None
    notes: str = Field(min_length=5, description="Audit note documenting official extension or window change.")


@router.get("/dashboard/stats", response_model=Dict[str, Any])
def get_admin_dashboard_stats(
    admin_user: UserProfileModel = Depends(require_role(["scheme_reviewer", "platform_admin"]))
):
    """Returns comprehensive scheme intelligence and monitoring statistics."""
    workflow = SchemeReviewWorkflow()
    return workflow.get_monitoring_dashboard_stats()


@router.get("/schemes/pending", response_model=List[Dict[str, Any]])
def list_pending_schemes(
    admin_user: UserProfileModel = Depends(require_role(["scheme_reviewer", "platform_admin"]))
):
    """Lists extracted scheme drafts awaiting departmental officer sign-off."""
    workflow = SchemeReviewWorkflow()
    return workflow.list_pending_schemes()


@router.get("/schemes/{scheme_id}/dossier", response_model=Dict[str, Any])
def get_verification_dossier(
    scheme_id: str,
    admin_user: UserProfileModel = Depends(require_role(["scheme_reviewer", "platform_admin"]))
):
    """Retrieves full extraction dossier and legal clause references for reviewer inspection."""
    workflow = SchemeReviewWorkflow()
    try:
        return workflow.get_review_dossier(scheme_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.post("/schemes/{scheme_id}/verify", response_model=Dict[str, Any])
def verify_and_publish_scheme(
    scheme_id: str,
    payload: VerifySchemePayload,
    admin_user: UserProfileModel = Depends(require_role(["scheme_reviewer", "platform_admin"]))
):
    """Officially signs off on extracted scheme rules and publishes to live catalogue."""
    workflow = SchemeReviewWorkflow()
    try:
        result = workflow.verify_and_publish(
            scheme_id=scheme_id,
            reviewer_id=admin_user.id,
            reviewer_name=admin_user.enterprise_name or admin_user.email,
            notes=payload.notes,
            verified_fields=payload.verified_overrides,
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/schemes/{scheme_id}/reject", response_model=Dict[str, Any])
def reject_scheme(
    scheme_id: str,
    payload: RejectSchemePayload,
    admin_user: UserProfileModel = Depends(require_role(["scheme_reviewer", "platform_admin"]))
):
    """Rejects an irrelevant or duplicate candidate document with audit trail."""
    workflow = SchemeReviewWorkflow()
    try:
        return workflow.reject_scheme(
            scheme_id=scheme_id,
            reviewer_id=admin_user.id,
            reviewer_name=admin_user.enterprise_name or admin_user.email,
            reason=payload.reason,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/schemes/{scheme_id}/update-lifecycle", response_model=Dict[str, Any])
def update_scheme_lifecycle(
    scheme_id: str,
    payload: UpdateLifecyclePayload,
    admin_user: UserProfileModel = Depends(require_role(["scheme_reviewer", "platform_admin"]))
):
    """Updates scheme application or claim deadlines, rolling status, or links with audit trail."""
    workflow = SchemeReviewWorkflow()
    try:
        updates = payload.model_dump(exclude_unset=True)
        return workflow.update_scheme_lifecycle(
            scheme_id=scheme_id,
            updates=updates,
            reviewer_id=admin_user.id,
            reviewer_name=admin_user.enterprise_name or admin_user.email,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
