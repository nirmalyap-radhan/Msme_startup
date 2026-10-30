"""
Scheme Discovery & Deadline Monitoring API Router.
Exposes source registry status, manual sync triggers, active deadline alerts,
and discovery audit logs.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.security.dependencies import get_current_user, get_db
from services.deadline_monitoring.deadline_service import DeadlineMonitoringService
from services.deadline_monitoring.models import (
    DeadlineAlertItem,
    DeadlineMonitoringCycleSummary,
)
from services.scheme_discovery.discovery_engine import SchemeDiscoveryEngine
from services.scheme_discovery.models import DiscoveryJobSummary
from services.scheme_discovery.registry import SourceRegistryService
from services.scheme_ingestion.models import (
    DiscoveredSourceRegistryModel,
    DiscoveryAuditLogModel,
    SchemeDeadlineAlertModel,
)

router = APIRouter(prefix="/discovery", tags=["Discovery & Deadlines"])


@router.get("/sources")
def list_monitored_sources(
    enabled_only: bool = Query(False, description="Filter for active sources only"),
    db: Session = Depends(get_db)
):
    """Retrieves all registered government, banking, and agency sources and their health status."""
    registry = SourceRegistryService(db_session=db)
    registry.seed_default_sources()
    sources = registry.list_sources(enabled_only=enabled_only)
    return [
        {
            "id": s.id,
            "name": s.name,
            "source_type": s.source_type,
            "base_url": s.base_url,
            "discovery_endpoint": s.discovery_endpoint,
            "discovery_method": s.discovery_method,
            "polling_frequency_hours": s.polling_frequency_hours,
            "last_checked_at": s.last_checked_at,
            "last_successful_at": s.last_successful_at,
            "health_status": s.health_status,
            "error_count": s.error_count,
            "last_error_message": s.last_error_message,
            "is_enabled": s.is_enabled,
        }
        for s in sources
    ]


@router.post("/sources/{source_id}/poll", response_model=DiscoveryJobSummary)
def poll_source_on_demand(
    source_id: str,
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):
    """Triggers immediate on-demand polling and reconciliation for a single source."""
    registry = SourceRegistryService(db_session=db)
    source = registry.get_source_by_id(source_id)
    if not source:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Source with ID '{source_id}' was not found in the registry."
        )

    engine = SchemeDiscoveryEngine(db_session=db)
    return engine.discover_source(source)


@router.post("/run", response_model=List[DiscoveryJobSummary])
def run_all_source_discovery(
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):
    """Triggers automated discovery across all enabled official sources."""
    engine = SchemeDiscoveryEngine(db_session=db)
    return engine.run_all_discovery()


@router.get("/alerts", response_model=List[DeadlineAlertItem])
def list_deadline_alerts(
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db)
):
    """Returns active upcoming application and claim deadline alerts."""
    deadline_svc = DeadlineMonitoringService(db_session=db)
    return deadline_svc.list_active_alerts(limit=limit)


@router.post("/alerts/{alert_id}/dismiss")
def dismiss_deadline_alert(
    alert_id: str,
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):
    """Dismisses an active deadline alert."""
    alert = db.query(SchemeDeadlineAlertModel).filter(
        SchemeDeadlineAlertModel.id == alert_id
    ).first()
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Alert with ID '{alert_id}' was not found."
        )
    alert.is_dismissed = True
    db.commit()
    return {"message": "Alert dismissed successfully", "alert_id": alert_id}


@router.post("/deadlines/recheck", response_model=DeadlineMonitoringCycleSummary)
def trigger_deadline_recheck(
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):
    """Executes deadline evaluation cycle and generates window alerts."""
    deadline_svc = DeadlineMonitoringService(db_session=db)
    return deadline_svc.run_monitoring_cycle()


@router.get("/audit-logs")
def list_discovery_audit_logs(
    limit: int = Query(50, ge=1, le=200),
    scheme_id: Optional[str] = Query(None),
    event_type: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Returns the persistent audit log of discoveries, status changes, and deadline alerts."""
    query = db.query(DiscoveryAuditLogModel)
    if scheme_id:
        query = query.filter(DiscoveryAuditLogModel.scheme_id == scheme_id)
    if event_type:
        query = query.filter(DiscoveryAuditLogModel.event_type == event_type)

    logs = query.order_by(DiscoveryAuditLogModel.created_at.desc()).limit(limit).all()
    return [
        {
            "id": l.id,
            "scheme_id": l.scheme_id,
            "source_id": l.source_id,
            "event_type": l.event_type,
            "previous_state": l.previous_state,
            "new_state": l.new_state,
            "supporting_evidence": l.supporting_evidence,
            "source_clause_or_url": l.source_clause_or_url,
            "created_at": l.created_at,
        }
        for l in logs
    ]
