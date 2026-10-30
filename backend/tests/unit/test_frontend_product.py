"""
Unit and Integration Tests for Phase 5 Frontend Product.
Verifies web page serving, static assets delivery, zero-mock UI compliance,
semantic elements, and integration with backend APIs.
"""

import os
import re
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_serve_index_html_via_app_route():
    """Verify /app serves index.html with 200 OK and HTML content type."""
    response = client.get("/app")
    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")
    assert "Udyog Sathi" in response.text
    assert "Government of Odisha" in response.text


def test_serve_index_html_via_root_when_accept_html():
    """Verify root route / serves index.html when Accept header includes text/html."""
    response = client.get("/", headers={"Accept": "text/html,application/xhtml+xml"})
    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")
    assert "Udyog Sathi" in response.text


def test_serve_json_via_root_when_accept_json():
    """Verify root route / continues to serve JSON metadata for API clients."""
    response = client.get("/", headers={"Accept": "application/json"})
    assert response.status_code == 200
    assert response.headers.get("content-type", "").startswith("application/json")
    data = response.json()
    assert data["platform"] == "Udyog Sathi"
    assert "disclaimer" in data


def test_static_css_assets_served():
    """Verify CSS stylesheets are properly served by StaticFiles mount."""
    css_files = ["styles.css", "components.css", "animations.css"]
    for f in css_files:
        response = client.get(f"/static/css/{f}")
        assert response.status_code == 200, f"Failed to serve /static/css/{f}"
        assert "text/css" in response.headers.get("content-type", "")
        assert len(response.text) > 100


def test_static_js_assets_served():
    """Verify JavaScript controllers are properly served by StaticFiles mount."""
    js_files = [
        "api.js",
        "i18n.js",
        "catalogue.js",
        "eligibility.js",
        "assistant.js",
        "tracker.js",
        "admin.js",
        "app.js",
    ]
    for f in js_files:
        response = client.get(f"/static/js/{f}")
        assert response.status_code == 200, f"Failed to serve /static/js/{f}"
        assert len(response.text) > 100


def test_index_html_semantic_structure_and_zero_mock():
    """
    Verify index.html contains all critical UI elements:
    - Language switcher
    - Navigation tabs
    - Scheme search and filters
    - Deterministic eligibility form
    - AI assistant interface
    - User-managed application tracker
    - Admin reviewer queue
    - Legal disclaimer and zero-mock notices
    """
    response = client.get("/app")
    html = response.text

    # 1. Page title & Branding
    assert "Udyog Sathi" in html
    assert "ଉଦ୍ୟୋଗ ସାଥୀ" in html
    assert "Department of MSME" in html

    # 2. Navigation tabs
    assert 'data-tab="catalogue"' in html
    assert 'data-tab="eligibility"' in html
    assert 'data-tab="assistant"' in html
    assert 'data-tab="tracker"' in html
    assert 'data-tab="admin"' in html

    # 3. Form fields in Eligibility Evaluator
    assert 'id="eligibilityForm"' in html
    assert 'id="prof_class"' in html
    assert 'id="prof_sector"' in html
    assert 'id="prof_state"' in html
    assert 'id="prof_district"' in html
    assert 'id="prof_production_status"' in html
    assert 'id="prof_investment"' in html
    assert 'id="prof_turnover"' in html
    assert 'id="prof_loan"' in html
    assert 'id="prof_interest"' in html

    # 4. Assistant UI
    assert 'id="chatForm"' in html
    assert 'id="chatInput"' in html
    assert 'id="chatMessages"' in html

    # 5. Tracker & Admin
    assert 'id="trackerListContainer"' in html
    assert 'id="adminQueueContainer"' in html

    # 6. Zero-Mock & Truthful disclaimers
    assert "User-Managed Compliance Ledger" in html
    assert "Deterministic Three-Valued Eligibility Evaluator" in html
    assert "Official Government Notification Grounded" in html
    assert "msme.odisha.gov.in" in html


def test_frontend_zero_mock_no_hardcoded_schemes():
    """
    Ensure that frontend JS files do not hardcode fake scheme lists,
    fake status syncing, or fake beneficiaries.
    """
    web_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "apps", "web")
    js_dir = os.path.join(web_dir, "static", "js")

    forbidden_patterns = [
        r"lorem ipsum",
        r"fake_scheme",
        r"sample_counter",
        r"10,000\+ happy beneficiaries",
        r"syncing with state portal\.\.\.",
    ]

    for root, _, files in os.walk(js_dir):
        for f in files:
            if f.endswith(".js"):
                path = os.path.join(root, f)
                with open(path, "r", encoding="utf-8") as file:
                    content = file.read().lower()
                    for pattern in forbidden_patterns:
                        assert not re.search(pattern, content), f"Forbidden mock pattern '{pattern}' in {f}"
