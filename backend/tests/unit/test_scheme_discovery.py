"""
Unit Tests for the Automated Scheme Discovery Engine.
Verifies source registry, connector parsing, idempotent document handling,
and persistent discovery audit trails.
"""

import pytest
from services.scheme_discovery.connectors.html_directory import HtmlDirectoryConnector
from services.scheme_discovery.models import (
    DiscoveryMethod,
    SourceRegistryConfig,
    SourceType,
)
from services.scheme_discovery.registry import SourceRegistryService, DEFAULT_SOURCE_SEEDS
from services.scheme_ingestion.storage import SchemeStorageRepository


def test_source_registry_seeding_and_retrieval():
    """Verify registry correctly seeds default central, state, and bank sources."""
    service = SourceRegistryService()
    seeded = service.seed_default_sources()
    assert seeded >= 0

    sources = service.list_sources()
    assert len(sources) >= len(DEFAULT_SOURCE_SEEDS)

    source_ids = [s.id for s in sources]
    assert "src-odisha-msme-schemes" in source_ids
    assert "src-central-msme-schemes" in source_ids
    assert "src-sidbi-msme-schemes" in source_ids
    assert "src-cgtmse-guarantee" in source_ids
    assert "src-sbi-sme-products" in source_ids


def test_html_connector_category_and_regex_parsing():
    """Verify category classification and notification regex extraction from document text."""
    dummy_config = SourceRegistryConfig(
        id="test-source",
        name="Test Directorate",
        source_type=SourceType.ODISHA_GOVT,
        base_url="https://msme.odisha.gov.in",
        discovery_endpoint="https://msme.odisha.gov.in/en/schemes",
    )
    connector = HtmlDirectoryConnector(dummy_config)

    # Test category determination
    assert connector._determine_category("Reimbursement of Interest on Working Capital") == "finance_credit"
    assert connector._determine_category("Capital Investment Subsidy under IPR 2022") == "subsidy_incentives"
    assert connector._determine_category("Reimbursement of Trade Mark Registration and GI") == "technology_innovation"
    assert connector._determine_category("Export Market Promotion & Trade Fair Participation") == "market_access"
    assert connector._determine_category("MSME Industrial Park Cluster Infrastructure") == "infrastructure_support"

    # Test notification extraction
    sample_text = "Government of Odisha Notification No. 7946/MSME Bhubaneswar dated 04.11.2023"
    notif = connector._extract_notification_no(sample_text)
    assert notif is not None
    assert "7946/MSME" in notif

    date_str = connector._extract_date(sample_text)
    assert date_str is not None
    assert "04.11.2023" in date_str
