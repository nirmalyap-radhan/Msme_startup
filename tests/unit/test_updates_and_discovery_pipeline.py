"""
Unit and Integration Tests for Official Updates Engine, Multi-Source Discovery,
and Expanded Unified MSME Catalogue.
Validates:
- Real data retrieval from /api/v1/updates with pagination and headers
- Strict Zero-Mock compliance (honest empty state on non-matching query)
- Update type, source type, and category filtering
- Expanded catalogue pagination (/api/v1/schemes/paginated)
- Differentiation of bank commercial products from government schemes
- Central vs Odisha jurisdiction filtering
- Multi-source registry seeds for Central, Odisha, and Public Banks
- Independence of application and claim statuses
"""

import pytest
from fastapi.testclient import TestClient
from apps.api.main import app
from services.scheme_discovery.registry import DEFAULT_SOURCE_SEEDS, SourceRegistryService
from services.scheme_discovery.connectors.bank_connector import BankProductConnector
from services.scheme_discovery.connectors.odisha_gazette import OdishaGazetteConnector

client = TestClient(app)


def test_list_verified_updates_pagination_and_headers():
    response = client.get("/api/v1/updates?page=1&limit=5")
    assert response.status_code == 200

    data = response.json()
    assert "items" in data
    assert "total" in data
    assert "pages" in data
    assert data["page"] == 1
    assert data["page_size"] == 5

    # Check pagination headers
    assert "x-total-count" in response.headers or "X-Total-Count" in response.headers
    assert int(response.headers.get("x-total-count", response.headers.get("X-Total-Count"))) >= 10

    # Ensure zero synthetic data
    for item in data["items"]:
        assert item["is_verified"] is True
        assert item["source_url"].startswith("http")
        assert len(item["title"]) > 5
        assert item["source_type"] in ["odisha_govt", "central_govt", "bank_psu", "dfi"]


def test_updates_honest_empty_state_zero_mock():
    # Strict Zero-Mock Policy: querying a non-existent announcement must return empty list, never fabricated records
    response = client.get("/api/v1/updates?search=FabricatedNonExistentUpdate999")
    assert response.status_code == 200

    data = response.json()
    assert data["items"] == []
    assert data["total"] == 0
    assert data["pages"] == 1


def test_updates_filter_by_type_and_source():
    # Filter by policy_gazette
    res_gazette = client.get("/api/v1/updates?update_type=policy_gazette")
    assert res_gazette.status_code == 200
    gazette_items = res_gazette.json()["items"]
    assert len(gazette_items) >= 1
    for u in gazette_items:
        assert u["update_type"] == "policy_gazette"

    # Filter by bank_product
    res_bank = client.get("/api/v1/updates?update_type=bank_product")
    assert res_bank.status_code == 200
    bank_items = res_bank.json()["items"]
    assert len(bank_items) >= 1
    for u in bank_items:
        assert u["update_type"] == "bank_product"
        assert u["source_type"] in ["bank_psu", "dfi"]


def test_paginated_schemes_endpoint():
    response = client.get("/api/v1/schemes/paginated?page=1&limit=6")
    assert response.status_code == 200

    data = response.json()
    assert "items" in data
    assert "total" in data
    assert data["total"] >= 10
    assert data["page"] == 1
    assert data["page_size"] == 6
    assert len(data["items"]) <= 6


def test_bank_commercial_product_distinction():
    response = client.get("/api/v1/schemes/paginated?scheme_type=bank_product")
    assert response.status_code == 200

    data = response.json()
    assert data["total"] >= 3
    for s in data["items"]:
        assert s["scheme_type"] == "bank_product"
        assert s["organization"] in ["State Bank of India", "Bank of Baroda", "Punjab National Bank", "SIDBI"]
        # Bank products should have loan details captured
        assert s["interest_rate_published"] is not None or s["max_loan_limit"] is not None


def test_central_vs_odisha_jurisdiction_filtering():
    # Central government schemes
    res_central = client.get("/api/v1/schemes?jurisdiction=Central")
    assert res_central.status_code == 200
    central_schemes = res_central.json()
    assert len(central_schemes) >= 3
    central_names = [s["official_name"].lower() for s in central_schemes]
    assert any("pmegp" in n or "prime minister" in n for n in central_names)
    assert any("vishwakarma" in n for n in central_names)
    assert any("cgtmse" in n or "credit guarantee" in n for n in central_names)

    # Odisha state schemes
    res_odisha = client.get("/api/v1/schemes?jurisdiction=Odisha")
    assert res_odisha.status_code == 200
    odisha_schemes = res_odisha.json()
    assert len(odisha_schemes) >= 2
    odisha_ids = [s["scheme_id"] for s in odisha_schemes]
    assert "OD-MSME-C0B98FA5" in odisha_ids  # CM-SRIM


def test_application_and_claim_status_independence():
    response = client.get("/api/v1/schemes")
    assert response.status_code == 200
    schemes = response.json()

    # Verify CM-SRIM has independent application and claim statuses
    cm_srim = next((s for s in schemes if s["scheme_id"] == "OD-MSME-C0B98FA5"), None)
    assert cm_srim is not None
    assert cm_srim["application_status"] == "open"
    assert cm_srim["claim_status"] == "rolling_claims"
    assert cm_srim["is_rolling"] is True


def test_source_registry_seeds_coverage():
    seeds = DEFAULT_SOURCE_SEEDS
    assert len(seeds) >= 9

    names = [s.name for s in seeds]
    assert any("Odisha MSME" in n for n in names)
    assert any("Invest Odisha" in n for n in names)
    assert any("Ministry of MSME" in n for n in names)
    assert any("State Bank of India" in n for n in names)
    assert any("Bank of Baroda" in n for n in names)
    assert any("Punjab National Bank" in n for n in names)
    assert any("SIDBI" in n for n in names)
    assert any("CGTMSE" in n for n in names)


def test_bank_connector_logic():
    sbi_seed = next(s for s in DEFAULT_SOURCE_SEEDS if "sbi" in s.id)
    connector = BankProductConnector(sbi_seed)
    results = connector.discover_documents()
    assert len(results) >= 1
    for r in results:
        assert r.scheme_type == "bank_product"
        assert r.source_url.startswith("https://")
        assert r.max_loan_limit is not None or r.interest_rate_published is not None
