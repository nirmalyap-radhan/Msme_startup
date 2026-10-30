"""
System Health and Readiness Router.
"""

from datetime import datetime
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import api_config
from app.security.dependencies import get_db
from services.scheme_ingestion.models import SchemeModel, SchemeStatus

router = APIRouter(tags=["Health"])


@router.get("/health/live")
def liveness_check():
    """Liveness probe indicating API process is responding."""
    return {
        "status": "live",
        "app_name": api_config.app_name,
        "version": api_config.app_version,
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/health/ready")
def readiness_check(db: Session = Depends(get_db)):
    """Readiness probe checking database connectivity and published catalogue metrics."""
    db_status = "unhealthy"
    published_count = 0

    try:
        db.execute(text("SELECT 1"))
        db_status = "healthy"
        published_count = db.query(SchemeModel).filter(
            SchemeModel.status == SchemeStatus.PUBLISHED.value
        ).count()
    except Exception as e:
        db_status = f"error: {str(e)}"

    is_ready = (db_status == "healthy")

    return {
        "status": "ready" if is_ready else "not_ready",
        "database": db_status,
        "published_schemes_count": published_count,
        "environment": api_config.app_env,
        "timestamp": datetime.utcnow().isoformat(),
    }
