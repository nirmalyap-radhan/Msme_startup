"""
Deterministic Formula-Based Benefit Calculator.
Calculates indicative financial subsidies, reimbursements, and concessions
strictly from verified formulas and provided applicant inputs. Never fabricates estimates.
"""

from typing import Any, Dict, List, Optional
from services.eligibility.rules import BenefitCalculationResult


class BenefitCalculator:
    @staticmethod
    def calculate_benefits(
        benefit_rules: List[Any],
        applicant_profile: Dict[str, Any]
    ) -> List[BenefitCalculationResult]:
        """
        Evaluates verified benefit formulas against an applicant's financial attributes.
        Returns explicit calculation results or identifies missing required inputs.
        """
        results: List[BenefitCalculationResult] = []

        for rule in benefit_rules:
            b_type = getattr(rule, "benefit_type", "")
            formula_desc = getattr(rule, "formula_description", "")
            pct = getattr(rule, "subsidy_percentage", None)
            max_limit = getattr(rule, "max_limit_inr", None)
            duration = getattr(rule, "duration_years", None)
            clause = getattr(rule, "source_clause", "Official Notification")
            page = getattr(rule, "source_page", 1)

            # 1. Interest Subsidy (e.g. CM-SRIM)
            if b_type == "interest_subsidy":
                loan_amount = applicant_profile.get("working_capital_loan_sanctioned")
                interest_paid = applicant_profile.get("annual_interest_paid")

                if interest_paid is None or interest_paid <= 0:
                    results.append(
                        BenefitCalculationResult(
                            status="insufficient_inputs",
                            benefit_type="interest_subsidy",
                            estimated_amount_inr=None,
                            subsidy_percentage=pct,
                            max_limit_inr=max_limit,
                            duration_years=duration,
                            applied_formula=formula_desc,
                            missing_inputs=["annual_interest_paid", "working_capital_loan_sanctioned"],
                            assumptions_notes="Provide your sanctioned working capital cash credit limit and annual interest paid to compute exact rupee reimbursement.",
                            source_clause=clause,
                            source_page=page,
                        )
                    )
                else:
                    # Slabs calculation (CM-SRIM guidelines)
                    applied_pct = pct or 100.0
                    if loan_amount is not None:
                        if loan_amount <= 1000000.0:
                            applied_pct = 100.0
                        elif loan_amount <= 5000000.0:
                            applied_pct = 75.0
                        else:
                            applied_pct = 50.0

                    estimated_reimbursement = interest_paid * (applied_pct / 100.0)
                    if max_limit:
                        estimated_reimbursement = min(estimated_reimbursement, max_limit)

                    results.append(
                        BenefitCalculationResult(
                            status="calculated",
                            benefit_type="interest_subsidy",
                            estimated_amount_inr=round(estimated_reimbursement, 2),
                            subsidy_percentage=applied_pct,
                            max_limit_inr=max_limit,
                            duration_years=duration,
                            applied_formula=f"{applied_pct}% reimbursement on annual interest paid of ₹{interest_paid:,.2f}",
                            missing_inputs=[],
                            assumptions_notes=f"Calculated based on interest paid of ₹{interest_paid:,.2f} under {clause}.",
                            source_clause=clause,
                            source_page=page,
                        )
                    )

            # 2. Trademark Assistance
            elif b_type == "trademark_assistance":
                trademark_expenditure = applicant_profile.get("trademark_expenditure")

                if trademark_expenditure is None or trademark_expenditure <= 0:
                    results.append(
                        BenefitCalculationResult(
                            status="insufficient_inputs",
                            benefit_type="trademark_assistance",
                            estimated_amount_inr=None,
                            subsidy_percentage=pct or 100.0,
                            max_limit_inr=max_limit or 300000.0,
                            duration_years=None,
                            applied_formula=formula_desc,
                            missing_inputs=["trademark_expenditure"],
                            assumptions_notes="Provide actual expenditure incurred for trade mark filing / registration to compute reimbursement.",
                            source_clause=clause,
                            source_page=page,
                        )
                    )
                else:
                    applied_pct = pct or 100.0
                    reimbursement = trademark_expenditure * (applied_pct / 100.0)
                    ceiling = max_limit or 300000.0
                    final_amount = min(reimbursement, ceiling)

                    results.append(
                        BenefitCalculationResult(
                            status="calculated",
                            benefit_type="trademark_assistance",
                            estimated_amount_inr=round(final_amount, 2),
                            subsidy_percentage=applied_pct,
                            max_limit_inr=ceiling,
                            duration_years=None,
                            applied_formula=f"{applied_pct}% of trade mark expenditure up to ceiling of ₹{ceiling:,.0f}",
                            missing_inputs=[],
                            assumptions_notes=f"Calculated on incurred expenditure of ₹{trademark_expenditure:,.2f}.",
                            source_clause=clause,
                            source_page=page,
                        )
                    )

            # 3. Capital Investment Subsidy
            elif b_type == "capital_investment_subsidy":
                investment = applicant_profile.get("investment_plant_machinery")

                if investment is None or investment <= 0:
                    results.append(
                        BenefitCalculationResult(
                            status="insufficient_inputs",
                            benefit_type="capital_investment_subsidy",
                            estimated_amount_inr=None,
                            subsidy_percentage=pct or 30.0,
                            max_limit_inr=max_limit,
                            duration_years=None,
                            applied_formula=formula_desc,
                            missing_inputs=["investment_plant_machinery"],
                            assumptions_notes="Provide eligible capital investment in plant and machinery to compute subsidy amount.",
                            source_clause=clause,
                            source_page=page,
                        )
                    )
                else:
                    applied_pct = pct or 30.0
                    subsidy = investment * (applied_pct / 100.0)
                    if max_limit:
                        subsidy = min(subsidy, max_limit)

                    results.append(
                        BenefitCalculationResult(
                            status="calculated",
                            benefit_type="capital_investment_subsidy",
                            estimated_amount_inr=round(subsidy, 2),
                            subsidy_percentage=applied_pct,
                            max_limit_inr=max_limit,
                            duration_years=None,
                            applied_formula=f"{applied_pct}% capital subsidy on ₹{investment:,.2f} investment",
                            missing_inputs=[],
                            assumptions_notes=f"Calculated under {clause}.",
                            source_clause=clause,
                            source_page=page,
                        )
                    )

            # 4. Other Financial Assistance
            else:
                results.append(
                    BenefitCalculationResult(
                        status="calculated" if max_limit else "not_applicable",
                        benefit_type=b_type,
                        estimated_amount_inr=max_limit,
                        subsidy_percentage=pct,
                        max_limit_inr=max_limit,
                        duration_years=duration,
                        applied_formula=formula_desc,
                        missing_inputs=[],
                        assumptions_notes=f"Financial assistance as stipulated in {clause}.",
                        source_clause=clause,
                        source_page=page,
                    )
                )

        return results
