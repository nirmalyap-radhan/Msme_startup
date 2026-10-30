"""
Unit tests for Deterministic Formula-Based Benefit Calculator.
Tests interest subsidies, trademark assistance, capital subsidies,
and strict non-fabrication on missing applicant inputs.
"""

import pytest
from services.eligibility.benefit_calculator import BenefitCalculator
from services.scheme_ingestion.models import CandidateBenefit


def test_interest_subsidy_slabs_calculation():
    rule = CandidateBenefit(
        benefit_type="interest_subsidy",
        formula_description="Interest subvention on working capital cash credit loan",
        subsidy_percentage=100.0,
        max_limit_inr=2000000.0,
        duration_years=5,
        source_clause="Clause 5.1",
        source_page=6,
    )

    # 1. Loan <= 10 Lakh -> 100% reimbursement
    profile_small_loan = {
        "working_capital_loan_sanctioned": 800000.0,
        "annual_interest_paid": 64000.0,
    }
    res1 = BenefitCalculator.calculate_benefits([rule], profile_small_loan)
    assert len(res1) == 1
    assert res1[0].status == "calculated"
    assert res1[0].subsidy_percentage == 100.0
    assert res1[0].estimated_amount_inr == 64000.0
    assert res1[0].source_clause == "Clause 5.1"
    assert res1[0].source_page == 6

    # 2. Loan between 10L and 50L -> 75% reimbursement
    profile_mid_loan = {
        "working_capital_loan_sanctioned": 4000000.0,
        "annual_interest_paid": 320000.0,
    }
    res2 = BenefitCalculator.calculate_benefits([rule], profile_mid_loan)
    assert len(res2) == 1
    assert res2[0].status == "calculated"
    assert res2[0].subsidy_percentage == 75.0
    assert res2[0].estimated_amount_inr == 240000.0  # 75% of 320,000

    # 3. Loan > 50L -> 50% reimbursement
    profile_large_loan = {
        "working_capital_loan_sanctioned": 8000000.0,
        "annual_interest_paid": 700000.0,
    }
    res3 = BenefitCalculator.calculate_benefits([rule], profile_large_loan)
    assert len(res3) == 1
    assert res3[0].status == "calculated"
    assert res3[0].subsidy_percentage == 50.0
    assert res3[0].estimated_amount_inr == 350000.0  # 50% of 700,000


def test_interest_subsidy_ceiling_enforcement():
    # Max limit cap at Rs. 20 Lakh
    rule = CandidateBenefit(
        benefit_type="interest_subsidy",
        formula_description="Interest subsidy capped at 20L",
        subsidy_percentage=100.0,
        max_limit_inr=2000000.0,
        duration_years=5,
        source_clause="Clause 5.2",
        source_page=6,
    )
    profile_very_high_interest = {
        "working_capital_loan_sanctioned": 1000000.0,
        "annual_interest_paid": 2500000.0,
    }
    res = BenefitCalculator.calculate_benefits([rule], profile_very_high_interest)
    assert res[0].status == "calculated"
    assert res[0].estimated_amount_inr == 2000000.0  # Capped at max_limit_inr


def test_missing_interest_paid_returns_insufficient_inputs():
    rule = CandidateBenefit(
        benefit_type="interest_subsidy",
        formula_description="Interest subsidy",
        subsidy_percentage=100.0,
        max_limit_inr=2000000.0,
        source_clause="Clause 5.1",
        source_page=6,
    )
    profile_missing_interest = {
        "working_capital_loan_sanctioned": 1500000.0,
        # annual_interest_paid missing
    }
    res = BenefitCalculator.calculate_benefits([rule], profile_missing_interest)
    assert len(res) == 1
    assert res[0].status == "insufficient_inputs"
    assert res[0].estimated_amount_inr is None
    assert "annual_interest_paid" in res[0].missing_inputs


def test_trademark_assistance_calculation_and_cap():
    rule = CandidateBenefit(
        benefit_type="trademark_assistance",
        formula_description="50% reimbursement of expenditure incurred for registration of Trade Mark",
        subsidy_percentage=50.0,
        max_limit_inr=25000.0,
        source_clause="Clause 6.1",
        source_page=4,
    )

    # Within ceiling: Rs. 30,000 spent -> 50% is Rs. 15,000 <= 25,000
    res1 = BenefitCalculator.calculate_benefits([rule], {"trademark_expenditure": 30000.0})
    assert res1[0].status == "calculated"
    assert res1[0].estimated_amount_inr == 15000.0

    # Exceeding ceiling: Rs. 80,000 spent -> 50% is Rs. 40,000 -> capped at Rs. 25,000
    res2 = BenefitCalculator.calculate_benefits([rule], {"trademark_expenditure": 80000.0})
    assert res2[0].status == "calculated"
    assert res2[0].estimated_amount_inr == 25000.0

    # Missing expenditure -> insufficient_inputs
    res3 = BenefitCalculator.calculate_benefits([rule], {})
    assert res3[0].status == "insufficient_inputs"
    assert res3[0].estimated_amount_inr is None
    assert "trademark_expenditure" in res3[0].missing_inputs


def test_capital_investment_subsidy():
    rule = CandidateBenefit(
        benefit_type="capital_investment_subsidy",
        formula_description="30% capital investment subsidy up to Rs. 25 Lakh",
        subsidy_percentage=30.0,
        max_limit_inr=2500000.0,
        source_clause="Clause 8.1",
        source_page=7,
    )

    # 1. Normal investment: Rs. 50 Lakh -> 30% = Rs. 15 Lakh
    res1 = BenefitCalculator.calculate_benefits([rule], {"investment_plant_machinery": 5000000.0})
    assert res1[0].status == "calculated"
    assert res1[0].estimated_amount_inr == 1500000.0

    # 2. Large investment: Rs. 1.5 Crore -> 30% = Rs. 45 Lakh -> capped at Rs. 25 Lakh
    res2 = BenefitCalculator.calculate_benefits([rule], {"investment_plant_machinery": 15000000.0})
    assert res2[0].status == "calculated"
    assert res2[0].estimated_amount_inr == 2500000.0

    # 3. Missing investment -> insufficient_inputs
    res3 = BenefitCalculator.calculate_benefits([rule], {})
    assert res3[0].status == "insufficient_inputs"
    assert res3[0].estimated_amount_inr is None
    assert "investment_plant_machinery" in res3[0].missing_inputs
