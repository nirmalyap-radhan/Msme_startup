
"""
System Health and Readiness Router.
"""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Response, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import api_config
from app.security.dependencies import get_db
from services.scheme_ingestion.models import SchemeModel, SchemeStatus

router = APIRouter(tags=["Health"])


@router.api_route(
    "/health/live",
    methods=["GET", "HEAD"]
)
def liveness_check():
    """Liveness probe indicating API process is responding."""

    return {
        "status": "live",
        "app_name": api_config.app_name,
        "version": api_config.app_version,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/health/ready")
def readiness_check(db: Session = Depends(get_db)):
    """Readiness probe checking database connectivity."""

    try:
        db.execute(text("SELECT 1"))

        published_count = db.query(SchemeModel).filter(
            SchemeModel.status == SchemeStatus.PUBLISHED.value
        ).count()

        return {
            "status": "ready",
            "database": "healthy",
            "published_schemes_count": published_count,
            "environment": api_config.app_env,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    except Exception:
        raise HTTPException(
            status_code=503,
            detail={
                "status": "not_ready",
                "database": "unhealthy",
                "environment": api_config.app_env,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )
