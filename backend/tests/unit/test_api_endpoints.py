"""
Integration tests for FastAPI REST Endpoints.
Tests:
- Health and readiness probes
- Verified scheme catalogue search and details (Zero Mock Rule)
- Deterministic single and batch eligibility evaluations
- Document checklists
- MSME enterprise profiles, registration, and JWT login
- User-managed application tracking
- RBAC permissions (403 on admin routes for regular users)
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_live_endpoint():
    response = client.get("/health/live")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "live"
    assert "Udyog Sathi" in data["app_name"]


def test_health_ready_endpoint():
    response = client.get("/health/ready")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready"
    assert data["database"] == "healthy"
    assert data["published_schemes_count"] >= 2


def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["platform"] == "Udyog Sathi"
    assert "Odisha" in data["jurisdiction"]
    assert "disclaimer" in data


def test_list_published_schemes_zero_mock():
    # 1. Fetch published schemes
    response = client.get("/api/v1/schemes")
    assert response.status_code == 200
    schemes = response.json()
    assert isinstance(schemes, list)
    assert len(schemes) >= 2  # At least CM-SRIM and Trade Mark Assistance

    scheme_ids = [s["scheme_id"] for s in schemes]
    assert "OD-MSME-C0B98FA5" in scheme_ids
    assert "OD-MSME-AFD17307" in scheme_ids

    # Verify provenance fields are present
    cm_srim = next(s for s in schemes if s["scheme_id"] == "OD-MSME-C0B98FA5")
    assert cm_srim["source_url"].startswith("https://msme.odisha.gov.in")
    assert len(cm_srim["document_sha256"]) == 64
    assert cm_srim["status"] == "published"

    # 2. Honest empty search: non-matching query returns [] (never mock items)
    empty_res = client.get("/api/v1/schemes?search=NonExistentSchemeXYZ")
    assert empty_res.status_code == 200
    assert empty_res.json() == []


def test_get_scheme_details():
    # 1. Existing verified scheme
    res = client.get("/api/v1/schemes/OD-MSME-C0B98FA5")
    assert res.status_code == 200
    detail = res.json()
    assert detail["scheme_id"] == "OD-MSME-C0B98FA5"
    assert "CHIEF MINISTER" in detail["official_name"]
    assert len(detail["verified_eligibility_rules"]) > 0
    assert len(detail["verified_benefits"]) > 0
    assert len(detail["required_documents"]) > 0

    # Verify citations
    first_rule = detail["verified_eligibility_rules"][0]
    assert "source_clause" in first_rule
    assert "source_page" in first_rule

    # 2. Non-existent scheme returns 404
    missing_res = client.get("/api/v1/schemes/OD-NONEXISTENT-99")
    assert missing_res.status_code == 404
    assert "not found" in missing_res.json()["detail"].lower()


def test_get_scheme_document_checklist():
    res = client.get("/api/v1/schemes/OD-MSME-C0B98FA5/checklist")
    assert res.status_code == 200
    data = res.json()
    assert data["scheme_id"] == "OD-MSME-C0B98FA5"
    assert len(data["required_documents"]) > 0
    assert any("udyam" in doc.lower() for doc in data["required_documents"])

    # 404 for missing scheme
    assert client.get("/api/v1/schemes/OD-FAKE/checklist").status_code == 404


def test_eligibility_single_scheme_matching_and_ineligible():
    # 1. Ineligible profile (state is outside Odisha)
    res_ineligible = client.post(
        "/api/v1/eligibility/evaluate",
        json={
            "scheme_id": "OD-MSME-C0B98FA5",
            "profile": {
                "state": "West Bengal",
                "enterprise_class": "micro",
                "production_status": "commenced",
                "udyam_registered": True,
            }
        }
    )
    assert res_ineligible.status_code == 200
    data_ineligible = res_ineligible.json()
    assert data_ineligible["outcome"] == "not_eligible_under_verified_rules"
    assert len(data_ineligible["conditions_failed"]) > 0
    assert any(c["attribute_name"] == "state" for c in data_ineligible["conditions_failed"])

    # 2. Incomplete profile (missing required attributes -> more_information_required)
    res_incomplete = client.post(
        "/api/v1/eligibility/evaluate",
        json={
            "scheme_id": "OD-MSME-C0B98FA5",
            "profile": {
                "state": "Odisha",
                # Missing production_status, udyam_registered, etc.
            }
        }
    )
    assert res_incomplete.status_code == 200
    data_incomplete = res_incomplete.json()
    assert data_incomplete["outcome"] == "more_information_required"
    assert len(data_incomplete["targeted_followup_questions"]) > 0


def test_eligibility_batch_evaluation():
    res = client.post(
        "/api/v1/eligibility/evaluate",
        json={
            "profile": {
                "state": "Odisha",
                "enterprise_class": "micro",
                "production_status": "commenced",
                "udyam_registered": True,
                "trademark_expenditure": 40000.0,
                "working_capital_loan_sanctioned": 1500000.0,
                "annual_interest_paid": 120000.0,
            }
        }
    )
    assert res.status_code == 200
    batch = res.json()
    assert batch["total_evaluated"] >= 2
    assert "assessments" in batch
    assert len(batch["assessments"]) == batch["total_evaluated"]


def test_profiles_registration_login_and_me_lifecycle():
    import uuid
    unique_email = f"msme_test_{uuid.uuid4().hex[:6]}@odisha-industry.org"

    # 1. Register new user profile
    reg_payload = {
        "email": unique_email,
        "password": "SecureTestPassword123!",
        "role": "entrepreneur",
        "enterprise_name": "Kalinga Agro Tech Solutions",
        "enterprise_class": "micro",
        "sector": "agro-processing",
        "district": "Khurda",
        "udyam_registered": True,
        "production_status": "commenced",
        "investment_plant_machinery": 3500000.0,
        "annual_turnover": 8000000.0,
    }
    reg_res = client.post("/api/v1/profiles/register", json=reg_payload)
    assert reg_res.status_code == 201
    reg_data = reg_res.json()
    assert "access_token" in reg_data
    assert reg_data["user"]["email"] == unique_email
    assert reg_data["user"]["enterprise_name"] == "Kalinga Agro Tech Solutions"

    token = reg_data["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Duplicate registration fails
    dup_res = client.post("/api/v1/profiles/register", json=reg_payload)
    assert dup_res.status_code == 400

    # 3. Login with credentials
    login_res = client.post(
        "/api/v1/profiles/login",
        json={"email": unique_email, "password": "SecureTestPassword123!"}
    )
    assert login_res.status_code == 200
    assert "access_token" in login_res.json()

    # 4. Bad password login fails
    bad_login = client.post(
        "/api/v1/profiles/login",
        json={"email": unique_email, "password": "IncorrectPassword"}
    )
    assert bad_login.status_code == 401

    # 5. Get current profile (/me)
    me_res = client.get("/api/v1/profiles/me", headers=headers)
    assert me_res.status_code == 200
    assert me_res.json()["email"] == unique_email

    # 6. Update current profile
    update_res = client.put(
        "/api/v1/profiles/me",
        headers=headers,
        json={"annual_turnover": 9500000.0}
    )
    assert update_res.status_code == 200
    assert update_res.json()["annual_turnover"] == 9500000.0


def test_user_managed_application_tracking_lifecycle():
    import uuid
    unique_email = f"tracker_{uuid.uuid4().hex[:6]}@odisha-industry.org"

    # Register user
    reg = client.post(
        "/api/v1/profiles/register",
        json={
            "email": unique_email,
            "password": "Password123!",
            "enterprise_name": "Puri Artisans LLP",
        }
    )
    token = reg.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Create tracking record
    app_payload = {
        "scheme_id": "OD-MSME-C0B98FA5",
        "status": "submitted",
        "acknowledgement_ref": "OD-MSME-2026-987654",
        "notes": "Application submitted via MSME Odisha portal on 24th Oct 2026."
    }
    create_res = client.post("/api/v1/applications", headers=headers, json=app_payload)
    assert create_res.status_code == 201
    created_app = create_res.json()
    tracking_id = created_app["id"]
    assert created_app["status"] == "submitted"
    assert created_app["acknowledgement_ref"] == "OD-MSME-2026-987654"

    # 2. List applications
    list_res = client.get("/api/v1/applications", headers=headers)
    assert list_res.status_code == 200
    apps = list_res.json()
    assert len(apps) >= 1
    assert any(a["id"] == tracking_id for a in apps)

    # 3. Update application status
    update_res = client.put(
        f"/api/v1/applications/{tracking_id}",
        headers=headers,
        json={"status": "under_scrutiny", "notes": "Officer requested bank sanction letter copy."}
    )
    assert update_res.status_code == 200
    assert update_res.json()["status"] == "under_scrutiny"
    assert "bank sanction letter" in update_res.json()["notes"]


def test_admin_rbac_protection():
    import uuid
    unique_email = f"entrepreneur_{uuid.uuid4().hex[:6]}@odisha-industry.org"

    # Regular entrepreneur user
    reg = client.post(
        "/api/v1/profiles/register",
        json={
            "email": unique_email,
            "password": "Password123!",
            "role": "entrepreneur",
        }
    )
    token = reg.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Regular entrepreneur attempting to access reviewer endpoint -> 403 Forbidden
    res = client.get("/api/v1/admin/schemes/pending", headers=headers)
    assert res.status_code == 403
    assert "lacks required permissions" in res.json()["detail"].lower()

    # 2. Unauthenticated user -> 401 Unauthorized
    unauth_res = client.get("/api/v1/admin/schemes/pending")
    assert unauth_res.status_code == 401
