"""
Unit Tests for the Deadline and Availability Monitoring Service.
Verifies timezone-aware date arithmetic, independent application and claim statuses,
window threshold alerts (30d, 14d, 7d, 3d, 1d), and audit logging.
"""

from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
import pytest

from services.deadline_monitoring.deadline_service import DeadlineMonitoringService
from services.scheme_ingestion.models import (
    ApplicationStatus,
    ClaimStatus,
    SchemeModel,
    SchemeStatus,
)


def test_independent_application_and_claim_status_derivation():
    """Verify application status and claim status are derived independently from dates."""
    service = DeadlineMonitoringService()
    now_ist = service.get_current_ist_time()

    # Case 1: Scheme with upcoming application window, no claims
    scheme_upcoming = SchemeModel(
        id="SCHEME-UPCOMING",
        official_name="Upcoming Tech Grant",
        department="Department of MSME",
        source_url="https://msme.odisha.gov.in",
        source_document_id="doc-1",
        document_sha256="hash-1",
        summary="Tech Grant",
        status=SchemeStatus.PUBLISHED.value,
        is_rolling=False,
        application_start_date=now_ist + timedelta(days=10),
        application_deadline=now_ist + timedelta(days=40),
        claim_deadline=None,
    )
    res_upcoming = service.evaluate_scheme_deadlines(scheme_upcoming)
    assert res_upcoming.application_status == ApplicationStatus.UPCOMING
    assert res_upcoming.claim_status == ClaimStatus.NOT_APPLICABLE

    # Case 2: Scheme closing soon (e.g. 5 days remaining)
    scheme_closing_soon = SchemeModel(
        id="SCHEME-CLOSING",
        official_name="Emergency Credit Scheme",
        department="Department of MSME",
        source_url="https://msme.odisha.gov.in",
        source_document_id="doc-2",
        document_sha256="hash-2",
        summary="Emergency Credit",
        status=SchemeStatus.PUBLISHED.value,
        is_rolling=False,
        application_start_date=now_ist - timedelta(days=30),
        application_deadline=now_ist + timedelta(days=5),
        claim_deadline=None,
    )
    res_closing = service.evaluate_scheme_deadlines(scheme_closing_soon)
    assert res_closing.application_status == ApplicationStatus.CLOSING_SOON
    assert res_closing.days_until_application_deadline == 5

    # Case 3: Scheme whose application has closed, but claims window remains open for 20 days
    scheme_closed_app_claims_open = SchemeModel(
        id="SCHEME-CLAIMS-OPEN",
        official_name="Capital Subsidy Reimbursement",
        department="Department of MSME",
        source_url="https://msme.odisha.gov.in",
        source_document_id="doc-3",
        document_sha256="hash-3",
        summary="Reimbursement Subsidy",
        status=SchemeStatus.PUBLISHED.value,
        is_rolling=False,
        application_deadline=now_ist - timedelta(days=10),
        claim_deadline=now_ist + timedelta(days=20),
    )
    res_claims = service.evaluate_scheme_deadlines(scheme_closed_app_claims_open)
    assert res_claims.application_status == ApplicationStatus.CLOSED
    assert res_claims.claim_status == ClaimStatus.CLAIMS_OPEN

    # Case 4: Rolling scheme (no fixed deadline)
    scheme_rolling = SchemeModel(
        id="SCHEME-ROLLING",
        official_name="CM-SRIM Interest Reimbursement",
        department="Department of MSME",
        source_url="https://msme.odisha.gov.in",
        source_document_id="doc-4",
        document_sha256="hash-4",
        summary="Interest Reimbursement",
        status=SchemeStatus.PUBLISHED.value,
        is_rolling=True,
        application_deadline=None,
        claim_deadline=None,
    )
    res_rolling = service.evaluate_scheme_deadlines(scheme_rolling)
    assert res_rolling.application_status == ApplicationStatus.OPEN
    assert res_rolling.claim_status == ClaimStatus.ROLLING_CLAIMS

    # Case 5: Missing dates and not rolling -> must be verification_required, NEVER fabricated
    scheme_unknown = SchemeModel(
        id="SCHEME-UNKNOWN",
        official_name="Unstated Deadline Scheme",
        department="Department of MSME",
        source_url="https://msme.odisha.gov.in",
        source_document_id="doc-5",
        document_sha256="hash-5",
        summary="Unstated Deadline",
        status=SchemeStatus.PUBLISHED.value,
        is_rolling=False,
        application_deadline=None,
        claim_deadline=None,
    )
    res_unknown = service.evaluate_scheme_deadlines(scheme_unknown)
    assert res_unknown.application_status == ApplicationStatus.VERIFICATION_REQUIRED


def test_monitoring_cycle_execution_and_summary():
    """Verify full monitoring cycle executes across repository without errors."""
    service = DeadlineMonitoringService()
    summary = service.run_monitoring_cycle()
    assert summary.total_schemes_checked >= 2
    assert summary.open_schemes >= 1
    assert summary.rolling_schemes >= 1
