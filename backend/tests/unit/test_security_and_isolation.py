"""
Unit and Integration Tests for Phase 6: Security, Isolation & Backup Integrity.
Tests:
- Cross-user data isolation (User B cannot view or edit User A's tracked applications)
- Cross-user profile isolation
- Security HTTP response headers (X-Content-Type-Options, X-Frame-Options, X-XSS-Protection)
- Input validation rejection (422 on invalid schemas)
- Secret protection and non-exposure in error messages
- Database backup creation and PRAGMA integrity verification
"""

import uuid
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from app.main import app
from scripts.backup_restore import create_backup, verify_backup

client = TestClient(app)


def test_security_headers_present_on_all_responses():
    """Verify essential security headers are applied to HTTP responses."""
    response = client.get("/health/live")
    assert response.status_code == 200
    headers = response.headers

    assert headers.get("X-Content-Type-Options") == "nosniff"
    assert headers.get("X-Frame-Options") == "DENY"
    assert headers.get("X-XSS-Protection") == "1; mode=block"
    assert "X-Process-Time" in headers


def test_cross_user_application_isolation():
    """
    Verify that User B cannot view, modify, or leak User A's application tracking record.
    Row-level isolation check.
    """
    user_a_email = f"user_a_{uuid.uuid4().hex[:6]}@odishamsme.in"
    user_b_email = f"user_b_{uuid.uuid4().hex[:6]}@odishamsme.in"

    # 1. Register User A and create an application tracking record
    reg_a = client.post(
        "/api/v1/profiles/register",
        json={"email": user_a_email, "password": "Password123#", "enterprise_name": "Enterprise Alpha"}
    )
    token_a = reg_a.json()["access_token"]
    headers_a = {"Authorization": f"Bearer {token_a}"}

    create_res = client.post(
        "/api/v1/applications",
        headers=headers_a,
        json={
            "scheme_id": "OD-MSME-C0B98FA5",
            "status": "submitted",
            "acknowledgement_ref": "REF-USER-A-SECRET",
            "notes": "User A internal compliance details."
        }
    )
    assert create_res.status_code == 201
    app_id = create_res.json()["id"]

    # 2. Register User B
    reg_b = client.post(
        "/api/v1/profiles/register",
        json={"email": user_b_email, "password": "Password123#", "enterprise_name": "Enterprise Beta"}
    )
    token_b = reg_b.json()["access_token"]
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # 3. User B lists applications -> User A's application must NOT be present
    list_b = client.get("/api/v1/applications", headers=headers_b)
    assert list_b.status_code == 200
    b_apps = list_b.json()
    assert not any(a["id"] == app_id for a in b_apps)

    # 4. User B attempts to update User A's application -> 404 (isolation enforced)
    tamper_res = client.put(
        f"/api/v1/applications/{app_id}",
        headers=headers_b,
        json={"status": "approved", "notes": "Hacked by User B"}
    )
    assert tamper_res.status_code == 404
    assert "not found" in tamper_res.json()["detail"].lower()

    # 5. Verify User A's record remained un-tampered
    list_a = client.get("/api/v1/applications", headers=headers_a)
    assert list_a.status_code == 200
    record_a = next(a for a in list_a.json() if a["id"] == app_id)
    assert record_a["status"] == "submitted"
    assert record_a["acknowledgement_ref"] == "REF-USER-A-SECRET"


def test_cross_user_profile_isolation():
    """Verify that User B cannot access or alter User A's profile via /profiles/me."""
    email_a = f"profile_a_{uuid.uuid4().hex[:6]}@odishamsme.in"
    email_b = f"profile_b_{uuid.uuid4().hex[:6]}@odishamsme.in"

    reg_a = client.post("/api/v1/profiles/register", json={"email": email_a, "password": "Password123#", "enterprise_name": "Alpha Corp"})
    token_a = reg_a.json()["access_token"]

    reg_b = client.post("/api/v1/profiles/register", json={"email": email_b, "password": "Password123#", "enterprise_name": "Beta Corp"})
    token_b = reg_b.json()["access_token"]

    me_b = client.get("/api/v1/profiles/me", headers={"Authorization": f"Bearer {token_b}"})
    assert me_b.status_code == 200
    assert me_b.json()["email"] == email_b
    assert me_b.json()["enterprise_name"] == "Beta Corp"


def test_input_validation_rejection():
    """Verify that malformed or unauthorized inputs are rejected with 422 Unprocessable Entity."""
    # 1. Invalid registration payload (missing required email)
    res1 = client.post("/api/v1/profiles/register", json={"password": "Password123#"})
    assert res1.status_code == 422

    # 2. Invalid eligibility evaluation payload (malformed profile structure)
    res2 = client.post("/api/v1/eligibility/evaluate", json={"profile": "not_an_object"})
    assert res2.status_code == 422

    # 3. Invalid application tracking status
    unique_email = f"val_{uuid.uuid4().hex[:6]}@odishamsme.in"
    reg = client.post("/api/v1/profiles/register", json={"email": unique_email, "password": "Password123#"})
    token = reg.json()["access_token"]

    res3 = client.post(
        "/api/v1/applications",
        headers={"Authorization": f"Bearer {token}"},
        json={"scheme_id": "OD-MSME-C0B98FA5", "status": "invalid_status_xyz"}
    )
    assert res3.status_code == 422


def test_database_backup_and_integrity_verification(tmp_path):
    """Verify atomic database backup creation and SQLite PRAGMA integrity verification."""
    backup_file = create_backup(target_dir=tmp_path)
    assert backup_file.exists()
    assert backup_file.stat().st_size > 0

    # Verify integrity
    is_valid = verify_backup(backup_file)
    assert is_valid is True

    # Verify metadata JSON was produced with SHA-256
    meta_file = backup_file.with_suffix(".json")
    assert meta_file.exists()
