"""
Unit tests for Deterministic Three-Valued Logic Scheme Eligibility Evaluator.
"""

import pytest
from services.eligibility.evaluator import DeterministicEligibilityEvaluator
from services.eligibility.rules import (
    EligibilityOutcome,
    ThreeValuedResult,
)
from services.scheme_ingestion.models import (
    CandidateBenefit,
    CandidateEligibilityCondition,
    CandidateSchemeRecord,
    SchemeStatus,
)


def test_three_valued_condition_operators():
    evaluator = DeterministicEligibilityEvaluator()

    # 1. Equality operator
    c1 = CandidateEligibilityCondition(
        attribute_name="state",
        operator="=",
        value="Odisha",
        description="Must be located in Odisha",
        source_clause="Clause 2.1",
        source_page=1,
    )
    # Passed
    res1 = evaluator.evaluate_condition(c1, {"state": "Odisha"})
    assert res1.result == ThreeValuedResult.TRUE
    assert "matches required 'Odisha'" in res1.reasoning

    # Case insensitive string equality
    res1_ci = evaluator.evaluate_condition(c1, {"state": "odisha"})
    assert res1_ci.result == ThreeValuedResult.TRUE

    # Failed
    res2 = evaluator.evaluate_condition(c1, {"state": "West Bengal"})
    assert res2.result == ThreeValuedResult.FALSE
    assert "does not match" in res2.reasoning
    assert res2.source_clause == "Clause 2.1"

    # Unknown (missing profile attribute)
    res3 = evaluator.evaluate_condition(c1, {})
    assert res3.result == ThreeValuedResult.UNKNOWN
    assert res3.followup_question is not None
    assert "is your enterprise plant or registered office located in the state of odisha?" in res3.followup_question.lower()

    # 2. IN operator
    c_in = CandidateEligibilityCondition(
        attribute_name="enterprise_class",
        operator="IN",
        value=["micro", "small"],
        description="Micro or small enterprise",
        source_clause="Clause 3.2",
        source_page=2,
    )
    assert evaluator.evaluate_condition(c_in, {"enterprise_class": "micro"}).result == ThreeValuedResult.TRUE
    assert evaluator.evaluate_condition(c_in, {"enterprise_class": "small"}).result == ThreeValuedResult.TRUE
    assert evaluator.evaluate_condition(c_in, {"enterprise_class": "medium"}).result == ThreeValuedResult.FALSE
    assert evaluator.evaluate_condition(c_in, {}).result == ThreeValuedResult.UNKNOWN

    # 3. Numeric comparison operators
    c_num = CandidateEligibilityCondition(
        attribute_name="investment_plant_machinery",
        operator="<=",
        value=10000000.0,  # 1 Crore
        description="Investment must not exceed 1 Crore",
        source_clause="Clause 5.1",
        source_page=4,
    )
    assert evaluator.evaluate_condition(c_num, {"investment_plant_machinery": 5000000.0}).result == ThreeValuedResult.TRUE
    assert evaluator.evaluate_condition(c_num, {"investment_plant_machinery": 10000000.0}).result == ThreeValuedResult.TRUE
    assert evaluator.evaluate_condition(c_num, {"investment_plant_machinery": 15000000.0}).result == ThreeValuedResult.FALSE
    assert evaluator.evaluate_condition(c_num, {}).result == ThreeValuedResult.UNKNOWN


def test_full_scheme_evaluation_outcomes():
    evaluator = DeterministicEligibilityEvaluator()

    # Create mock scheme record with 3 conditions
    scheme = CandidateSchemeRecord(
        scheme_id="OD-TEST-001",
        official_name="Odisha Agro-Processing Incentive Scheme",
        department="Department of MSME, Government of Odisha",
        source_url="https://msme.odisha.gov.in/policy.pdf",
        source_document_id="doc-123",
        document_sha256="abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890",
        summary="Test scheme for agro MSMEs in Odisha.",
        status=SchemeStatus.PUBLISHED,
        candidate_eligibility=[
            CandidateEligibilityCondition(
                attribute_name="enterprise_class",
                operator="IN",
                value=["micro", "small"],
                description="Must be micro or small.",
                source_clause="Clause 4.1",
                source_page=2,
            ),
            CandidateEligibilityCondition(
                attribute_name="sector",
                operator="IN",
                value=["agro-processing", "food processing"],
                description="Must be agro-processing or food processing.",
                source_clause="Clause 4.2",
                source_page=2,
            ),
            CandidateEligibilityCondition(
                attribute_name="state",
                operator="=",
                value="Odisha",
                description="Must be located in Odisha.",
                source_clause="Clause 4.3",
                source_page=3,
            ),
        ],
        candidate_benefits=[
            CandidateBenefit(
                benefit_type="capital_investment_subsidy",
                formula_description="30% subsidy up to Rs. 25 Lakh",
                subsidy_percentage=30.0,
                max_limit_inr=2500000.0,
                source_clause="Clause 6.1",
                source_page=5,
            )
        ]
    )

    # 1. Full Match (Potential Match)
    profile_eligible = {
        "enterprise_class": "micro",
        "sector": "agro-processing",
        "state": "Odisha",
        "investment_plant_machinery": 2000000.0,
    }
    assessment_1 = evaluator.evaluate_scheme(scheme, profile_eligible)
    assert assessment_1.outcome == EligibilityOutcome.POTENTIAL_MATCH
    assert len(assessment_1.conditions_passed) == 3
    assert len(assessment_1.conditions_failed) == 0
    assert len(assessment_1.conditions_unknown) == 0
    assert len(assessment_1.benefit_estimates) == 1
    assert assessment_1.benefit_estimates[0].status == "calculated"
    assert assessment_1.benefit_estimates[0].estimated_amount_inr == 600000.0  # 30% of 20L

    # 2. Definitively Ineligible
    profile_ineligible = {
        "enterprise_class": "medium",  # Medium not allowed
        "sector": "agro-processing",
        "state": "Odisha",
    }
    assessment_2 = evaluator.evaluate_scheme(scheme, profile_ineligible)
    assert assessment_2.outcome == EligibilityOutcome.NOT_ELIGIBLE_UNDER_VERIFIED_RULES
    assert len(assessment_2.conditions_failed) == 1
    assert assessment_2.conditions_failed[0].attribute_name == "enterprise_class"
    assert assessment_2.conditions_failed[0].source_clause == "Clause 4.1"
    assert "Ineligible under verified rules" in assessment_2.summary_reason

    # 3. Missing Attributes (More Information Required)
    profile_incomplete = {
        "state": "Odisha",
        # enterprise_class and sector are missing
    }
    assessment_3 = evaluator.evaluate_scheme(scheme, profile_incomplete)
    assert assessment_3.outcome == EligibilityOutcome.MORE_INFORMATION_REQUIRED
    assert len(assessment_3.conditions_passed) == 1
    assert len(assessment_3.conditions_unknown) == 2
    assert len(assessment_3.targeted_followup_questions) == 2
    attrs_asked = [q["attribute_name"] for q in assessment_3.targeted_followup_questions]
    assert "enterprise_class" in attrs_asked
    assert "sector" in attrs_asked

    # 4. Unverified Scheme Status Gate
    scheme.status = SchemeStatus.PENDING_REVIEW
    assessment_4 = evaluator.evaluate_scheme(scheme, profile_eligible)
    assert assessment_4.outcome == EligibilityOutcome.RULES_UNVERIFIED
    assert "pending reviewer verification" in assessment_4.summary_reason
