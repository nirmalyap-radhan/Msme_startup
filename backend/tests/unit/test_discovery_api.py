"""
Unit and Integration Tests for Discovery and Deadline Monitoring API Endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.security.auth import create_access_token

client = TestClient(app)


def _get_admin_headers():
    import uuid
    email = f"officer_{uuid.uuid4().hex[:6]}@msme.odisha.gov.in"
    reg = client.post(
        "/api/v1/profiles/register",
        json={
            "email": email,
            "password": "Password123!",
            "role": "platform_admin",
            "enterprise_name": "Directorate of MSME",
        }
    )
    token = reg.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_list_discovery_sources_endpoint():
    """Verify /discovery/sources returns configured official sources and health."""
    response = client.get("/api/v1/discovery/sources")
    assert response.status_code == 200
    sources = response.json()
    assert isinstance(sources, list)
    assert len(sources) >= 5

    names = [s["name"] for s in sources]
    assert any("Odisha MSME" in n for n in names)
    assert any("SIDBI" in n for n in names)
    assert any("State Bank of India" in n for n in names)


def test_list_deadline_alerts_endpoint():
    """Verify /discovery/alerts returns structured alert items."""
    response = client.get("/api/v1/discovery/alerts")
    assert response.status_code == 200
    alerts = response.json()
    assert isinstance(alerts, list)


def test_list_discovery_audit_logs_endpoint():
    """Verify /discovery/audit-logs returns persistent event trails."""
    response = client.get("/api/v1/discovery/audit-logs")
    assert response.status_code == 200
    logs = response.json()
    assert isinstance(logs, list)


def test_schemes_catalogue_with_lifecycle_filters():
    """Verify /schemes returns enriched lifecycle fields and respects filters."""
    # 1. Base list
    response = client.get("/api/v1/schemes")
    assert response.status_code == 200
    schemes = response.json()
    assert len(schemes) >= 2

    # Check new lifecycle attributes present
    first_scheme = schemes[0]
    assert "application_status" in first_scheme
    assert "claim_status" in first_scheme
    assert "category" in first_scheme
    assert "is_rolling" in first_scheme

    # 2. Filter by application_status=open
    res_open = client.get("/api/v1/schemes?application_status=open")
    assert res_open.status_code == 200
    assert len(res_open.json()) >= 2

    # 3. Filter by category=finance_credit
    res_cat = client.get("/api/v1/schemes?category=finance_credit")
    assert res_cat.status_code == 200
    assert len(res_cat.json()) >= 1


def test_admin_dashboard_stats_endpoint():
    """Verify /admin/dashboard/stats returns Section 10 scheme monitoring metrics."""
    headers = _get_admin_headers()
    response = client.get("/api/v1/admin/dashboard/stats", headers=headers)
    assert response.status_code == 200
    stats = response.json()

    assert "total_schemes_discovered" in stats
    assert "total_verified_schemes" in stats
    assert "currently_open_applications" in stats
    assert "schemes_accepting_claims" in stats
    assert "deadlines_approaching" in stats
    assert "awaiting_review_count" in stats
    assert "closed_or_discontinued_count" in stats
    assert "failed_ingestion_jobs" in stats
    assert "failed_source_checks" in stats
    assert "last_successful_sync_per_source" in stats
    assert stats["total_verified_schemes"] >= 2
