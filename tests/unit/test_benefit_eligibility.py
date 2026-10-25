"""
Unit Tests for the 6-State Business Benefit Discovery & Eligibility Engine.
Verifies ELIGIBLE_AND_OPEN, ELIGIBLE_AND_CLAIMABLE, POTENTIALLY_ELIGIBLE,
ELIGIBLE_BUT_CLOSED, INELIGIBLE, and STATUS_UNVERIFIED classifications.
"""

import pytest
from services.eligibility.evaluator import DeterministicEligibilityEvaluator
from services.eligibility.rules import (
    BusinessBenefitStatus,
    EligibilityOutcome,
)
from services.scheme_ingestion.models import (
    ApplicationStatus,
    ClaimStatus,
    EligibilityRuleModel,
    SchemeModel,
    SchemeStatus,
)


def _create_mock_scheme(app_status="open", claim_status="unknown", is_rolling=False, status="published"):
    scheme = SchemeModel(
        id="TEST-SCHEME-01",
        official_name="MSME Interest Subsidy",
        department="Department of MSME",
        source_url="https://msme.odisha.gov.in",
        source_document_id="doc-1",
        document_sha256="hash-1",
        summary="Interest Subsidy",
        status=status,
        application_status=app_status,
        claim_status=claim_status,
        is_rolling=is_rolling,
    )
    # Add rules: manufacturing sector, micro class
    scheme.eligibility_rules = [
        EligibilityRuleModel(
            id="r1",
            scheme_id=scheme.id,
            attribute_name="sector",
            operator="IN",
            value_json={"value": ["manufacturing"]},
            description="Manufacturing only",
            source_clause="Clause 2.1",
            source_page=1,
            is_verified=True,
        ),
        EligibilityRuleModel(
            id="r2",
            scheme_id=scheme.id,
            attribute_name="enterprise_class",
            operator="IN",
            value_json={"value": ["micro", "small"]},
            description="Micro or small only",
            source_clause="Clause 2.2",
            source_page=1,
            is_verified=True,
        ),
    ]
    return scheme


def test_benefit_status_eligible_and_open():
    scheme = _create_mock_scheme(app_status="open", claim_status="not_applicable")
    profile = {"sector": "manufacturing", "enterprise_class": "micro"}
    assessment = DeterministicEligibilityEvaluator.evaluate_scheme(scheme, profile)

    assert assessment.outcome == EligibilityOutcome.POTENTIAL_MATCH
    assert assessment.benefit_status == BusinessBenefitStatus.ELIGIBLE_AND_OPEN
    assert "disclaimer" in assessment.model_dump()


def test_benefit_status_eligible_and_claimable():
    scheme = _create_mock_scheme(app_status="open", claim_status="claims_open")
    profile = {"sector": "manufacturing", "enterprise_class": "micro"}
    assessment = DeterministicEligibilityEvaluator.evaluate_scheme(scheme, profile)

    assert assessment.outcome == EligibilityOutcome.POTENTIAL_MATCH
    assert assessment.benefit_status == BusinessBenefitStatus.ELIGIBLE_AND_CLAIMABLE
    assert assessment.is_claimable is True


def test_benefit_status_eligible_but_closed():
    scheme = _create_mock_scheme(app_status="closed", claim_status="claims_closed")
    profile = {"sector": "manufacturing", "enterprise_class": "micro"}
    assessment = DeterministicEligibilityEvaluator.evaluate_scheme(scheme, profile)

    assert assessment.outcome == EligibilityOutcome.POTENTIAL_MATCH
    assert assessment.benefit_status == BusinessBenefitStatus.ELIGIBLE_BUT_CLOSED


def test_benefit_status_ineligible():
    scheme = _create_mock_scheme(app_status="open", claim_status="not_applicable")
    profile = {"sector": "service", "enterprise_class": "micro"}  # Fails sector
    assessment = DeterministicEligibilityEvaluator.evaluate_scheme(scheme, profile)

    assert assessment.outcome == EligibilityOutcome.NOT_ELIGIBLE_UNDER_VERIFIED_RULES
    assert assessment.benefit_status == BusinessBenefitStatus.INELIGIBLE


def test_benefit_status_potentially_eligible():
    scheme = _create_mock_scheme(app_status="open", claim_status="not_applicable")
    profile = {"sector": "manufacturing"}  # Missing enterprise_class
    assessment = DeterministicEligibilityEvaluator.evaluate_scheme(scheme, profile)

    assert assessment.outcome == EligibilityOutcome.MORE_INFORMATION_REQUIRED
    assert assessment.benefit_status == BusinessBenefitStatus.POTENTIALLY_ELIGIBLE
    assert len(assessment.conditions_unknown) == 1
    assert assessment.conditions_unknown[0].attribute_name == "enterprise_class"


def test_benefit_status_unverified():
    scheme = _create_mock_scheme(app_status="unknown", status="draft")  # Draft scheme
    profile = {"sector": "manufacturing", "enterprise_class": "micro"}
    assessment = DeterministicEligibilityEvaluator.evaluate_scheme(scheme, profile)

    assert assessment.outcome == EligibilityOutcome.RULES_UNVERIFIED
    assert assessment.benefit_status == BusinessBenefitStatus.STATUS_UNVERIFIED
