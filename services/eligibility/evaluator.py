"""
Deterministic Three-Valued Logic Eligibility Evaluator.
Evaluates MSME profiles against verified government scheme conditions.
Returns POTENTIAL_MATCH, MORE_INFORMATION_REQUIRED, NOT_ELIGIBLE_UNDER_VERIFIED_RULES, or RULES_UNVERIFIED.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from services.eligibility.benefit_calculator import BenefitCalculator
from services.eligibility.rules import (
    BusinessBenefitStatus,
    ConditionEvaluationResult,
    EligibilityAssessment,
    EligibilityOutcome,
    ThreeValuedResult,
)


class DeterministicEligibilityEvaluator:
    QUESTION_TEMPLATES = {
        "enterprise_class": {
            "question": "What is your enterprise classification under the MSMED Act?",
            "field_type": "select",
            "options": ["micro", "small", "medium"],
        },
        "sector": {
            "question": "What primary industrial sector does your enterprise operate in?",
            "field_type": "select",
            "options": ["manufacturing", "service", "agro-processing", "handloom", "handicrafts", "food processing"],
        },
        "udyam_registered": {
            "question": "Do you hold a valid Udyam Registration Certificate?",
            "field_type": "boolean",
            "options": [True, False],
        },
        "production_status": {
            "question": "Has your enterprise commenced commercial production or business operations?",
            "field_type": "select",
            "options": ["commenced", "proposed", "under_implementation"],
        },
        "state": {
            "question": "Is your enterprise plant or registered office located in the State of Odisha?",
            "field_type": "boolean",
            "options": [True, False],
        },
        "investment_plant_machinery": {
            "question": "What is the total investment in plant and machinery / equipment (in INR)?",
            "field_type": "number",
            "options": None,
        },
        "working_capital_loan_sanctioned": {
            "question": "What is your sanctioned Working Capital Loan (Cash Credit) limit from banks (in INR)?",
            "field_type": "number",
            "options": None,
        },
        "annual_interest_paid": {
            "question": "What is the actual annual interest paid on your Working Capital Loan (in INR)?",
            "field_type": "number",
            "options": None,
        },
        "trademark_expenditure": {
            "question": "What was the actual expenditure incurred on trade mark registration (in INR)?",
            "field_type": "number",
            "options": None,
        },
    }

    @classmethod
    def evaluate_condition(
        cls,
        condition: Any,
        applicant_profile: Dict[str, Any]
    ) -> ConditionEvaluationResult:
        """
        Evaluates a single condition using three-valued logic (True, False, Unknown).
        """
        cond_id = getattr(condition, "id", None) or getattr(condition, "condition_id", "cond-1")
        attr_name = getattr(condition, "attribute_name", "")
        operator = getattr(condition, "operator", "=")
        desc = getattr(condition, "description", "")
        clause = getattr(condition, "source_clause", "Government Notification")
        page = getattr(condition, "source_page", 1)
        is_verified = getattr(condition, "is_verified", True)

        raw_val = getattr(condition, "value_json", None)
        if isinstance(raw_val, dict) and "value" in raw_val:
            required_value = raw_val["value"]
        else:
            required_value = getattr(condition, "value", raw_val)

        applicant_value = applicant_profile.get(attr_name)

        # 1. Check for Unknown (Missing applicant profile attribute)
        if applicant_value is None:
            q_meta = cls.QUESTION_TEMPLATES.get(attr_name, {
                "question": f"Please provide your '{attr_name}' to assess this condition.",
                "field_type": "text",
                "options": None,
            })
            return ConditionEvaluationResult(
                condition_id=cond_id,
                attribute_name=attr_name,
                operator=operator,
                required_value=required_value,
                applicant_value=None,
                result=ThreeValuedResult.UNKNOWN,
                reasoning=f"Applicant attribute '{attr_name}' is not specified. More information required.",
                source_clause=clause,
                source_page=page,
                is_verified=is_verified,
                followup_question=q_meta["question"],
            )

        # 2. Evaluate operator with deterministic comparison
        res = ThreeValuedResult.FALSE
        reasoning = ""

        try:
            if operator == "=":
                if isinstance(required_value, str) and isinstance(applicant_value, str):
                    passed = (applicant_value.strip().lower() == required_value.strip().lower())
                else:
                    passed = (applicant_value == required_value)
                res = ThreeValuedResult.TRUE if passed else ThreeValuedResult.FALSE
                reasoning = (
                    f"Applicant value '{applicant_value}' matches required '{required_value}'."
                    if passed else
                    f"Applicant value '{applicant_value}' does not match required '{required_value}' under {clause}."
                )

            elif operator == "!=":
                passed = (applicant_value != required_value)
                res = ThreeValuedResult.TRUE if passed else ThreeValuedResult.FALSE
                reasoning = f"Applicant value '{applicant_value}' {'satisfies' if passed else 'fails'} != '{required_value}'."

            elif operator in ("IN", "CONTAINS"):
                # Ensure required_value is a list/set
                req_list = [str(x).lower().strip() for x in required_value] if isinstance(required_value, list) else [str(required_value).lower().strip()]
                app_val_str = str(applicant_value).lower().strip()
                passed = app_val_str in req_list
                res = ThreeValuedResult.TRUE if passed else ThreeValuedResult.FALSE
                reasoning = (
                    f"Applicant {attr_name} '{applicant_value}' is in eligible list ({', '.join(req_list)})."
                    if passed else
                    f"Applicant {attr_name} '{applicant_value}' is NOT in eligible list ({', '.join(req_list)}) under {clause}."
                )

            elif operator in ("NOT IN", "EXCLUDES"):
                req_list = [str(x).lower().strip() for x in required_value] if isinstance(required_value, list) else [str(required_value).lower().strip()]
                app_val_str = str(applicant_value).lower().strip()
                passed = app_val_str not in req_list
                res = ThreeValuedResult.TRUE if passed else ThreeValuedResult.FALSE
                reasoning = (
                    f"Applicant {attr_name} '{applicant_value}' is excluded by {clause}."
                    if not passed else
                    f"Applicant {attr_name} '{applicant_value}' is permitted (not in excluded list)."
                )

            elif operator in (">", ">=", "<", "<="):
                app_num = float(applicant_value)
                req_num = float(required_value)

                if operator == ">":
                    passed = app_num > req_num
                elif operator == ">=":
                    passed = app_num >= req_num
                elif operator == "<":
                    passed = app_num < req_num
                elif operator == "<=":
                    passed = app_num <= req_num

                res = ThreeValuedResult.TRUE if passed else ThreeValuedResult.FALSE
                reasoning = (
                    f"Applicant value {app_num} satisfies {operator} {req_num}."
                    if passed else
                    f"Applicant value {app_num} violates condition {operator} {req_num} under {clause}."
                )

        except Exception as e:
            res = ThreeValuedResult.UNKNOWN
            reasoning = f"Evaluation error: {str(e)}"

        return ConditionEvaluationResult(
            condition_id=cond_id,
            attribute_name=attr_name,
            operator=operator,
            required_value=required_value,
            applicant_value=applicant_value,
            result=res,
            reasoning=reasoning,
            source_clause=clause,
            source_page=page,
            is_verified=is_verified,
            followup_question=None,
        )

    @classmethod
    def evaluate_scheme(
        cls,
        scheme: Any,
        applicant_profile: Dict[str, Any]
    ) -> EligibilityAssessment:
        """
        Evaluates a complete scheme against an applicant profile using three-valued logic.
        """
        scheme_id = getattr(scheme, "id", None) or getattr(scheme, "scheme_id", "OD-SCHEME")
        scheme_name = getattr(scheme, "official_name", None) or "Official Scheme"
        department = getattr(scheme, "department", None) or "Department of MSME, Government of Odisha"
        jurisdiction = getattr(scheme, "jurisdiction", None) or "Odisha"
        source_url = getattr(scheme, "source_url", None) or "https://msme.odisha.gov.in"
        raw_status = getattr(scheme, "status", "published")
        status = raw_status.value if hasattr(raw_status, "value") else str(raw_status).lower()

        # 1. Unverified scheme check
        if status != "published":
            return EligibilityAssessment(
                scheme_id=scheme_id,
                scheme_name=scheme_name,
                department=department,
                jurisdiction=jurisdiction,
                source_url=source_url,
                outcome=EligibilityOutcome.RULES_UNVERIFIED,
                benefit_status=BusinessBenefitStatus.STATUS_UNVERIFIED,
                application_status="verification_required",
                claim_status="verification_required",
                is_claimable=False,
                summary_reason="Scheme rules are currently in draft or pending reviewer verification. Cannot assess official eligibility.",
                conditions_passed=[],
                conditions_failed=[],
                conditions_unknown=[],
                targeted_followup_questions=[],
                benefit_estimates=[],
            )

        rules = getattr(scheme, "eligibility_rules", None)
        if rules is None:
            rules = getattr(scheme, "candidate_eligibility", [])
        passed: List[ConditionEvaluationResult] = []
        failed: List[ConditionEvaluationResult] = []
        unknown: List[ConditionEvaluationResult] = []
        questions: List[Dict[str, Any]] = []

        for rule in rules:
            eval_res = cls.evaluate_condition(rule, applicant_profile)
            if eval_res.result == ThreeValuedResult.TRUE:
                passed.append(eval_res)
            elif eval_res.result == ThreeValuedResult.FALSE:
                failed.append(eval_res)
            else:
                unknown.append(eval_res)
                if eval_res.followup_question:
                    q_meta = cls.QUESTION_TEMPLATES.get(eval_res.attribute_name, {})
                    questions.append({
                        "attribute_name": eval_res.attribute_name,
                        "question": eval_res.followup_question,
                        "field_type": q_meta.get("field_type", "text"),
                        "options": q_meta.get("options"),
                        "source_clause": eval_res.source_clause,
                        "source_page": eval_res.source_page,
                    })

        # 2. Determine Outcome
        if failed:
            outcome = EligibilityOutcome.NOT_ELIGIBLE_UNDER_VERIFIED_RULES
            failing_clauses = [f"'{f.attribute_name}' ({f.source_clause})" for f in failed]
            summary_reason = f"Ineligible under verified rules. Failed condition(s): {', '.join(failing_clauses)}."
        elif unknown:
            outcome = EligibilityOutcome.MORE_INFORMATION_REQUIRED
            missing_attrs = [f"'{u.attribute_name}'" for u in unknown]
            summary_reason = f"Likely eligible! Please provide missing information for: {', '.join(missing_attrs)}."
        else:
            outcome = EligibilityOutcome.POTENTIAL_MATCH
            summary_reason = "Fully eligible under verified government scheme guidelines."

        # 3. Calculate indicative benefits if not definitively ineligible
        benefit_estimates = []
        if outcome in (EligibilityOutcome.POTENTIAL_MATCH, EligibilityOutcome.MORE_INFORMATION_REQUIRED):
            benefits_list = getattr(scheme, "benefits", None)
            if benefits_list is None:
                benefits_list = getattr(scheme, "candidate_benefits", [])
            benefit_estimates = BenefitCalculator.calculate_benefits(benefits_list, applicant_profile)

        # 4. Derive 6-state Business Benefit Status based on outcome + lifecycle statuses
        app_status = getattr(scheme, "application_status", "open") or "open"
        claim_status = getattr(scheme, "claim_status", "unknown") or "unknown"
        is_rolling = getattr(scheme, "is_rolling", False)
        is_claimable = claim_status in ("claims_open", "rolling_claims")

        if outcome == EligibilityOutcome.NOT_ELIGIBLE_UNDER_VERIFIED_RULES:
            benefit_status = BusinessBenefitStatus.INELIGIBLE
        elif outcome == EligibilityOutcome.MORE_INFORMATION_REQUIRED:
            benefit_status = BusinessBenefitStatus.POTENTIALLY_ELIGIBLE
        elif outcome == EligibilityOutcome.RULES_UNVERIFIED:
            benefit_status = BusinessBenefitStatus.STATUS_UNVERIFIED
        else:  # POTENTIAL_MATCH
            if is_claimable:
                benefit_status = BusinessBenefitStatus.ELIGIBLE_AND_CLAIMABLE
            elif app_status in ("open", "closing_soon") or is_rolling:
                benefit_status = BusinessBenefitStatus.ELIGIBLE_AND_OPEN
            elif app_status in ("closed", "discontinued", "suspended"):
                benefit_status = BusinessBenefitStatus.ELIGIBLE_BUT_CLOSED
            else:
                benefit_status = BusinessBenefitStatus.STATUS_UNVERIFIED

        return EligibilityAssessment(
            scheme_id=scheme_id,
            scheme_name=scheme_name,
            department=department,
            jurisdiction=jurisdiction,
            source_url=source_url,
            outcome=outcome,
            benefit_status=benefit_status,
            application_status=app_status,
            claim_status=claim_status,
            is_claimable=is_claimable,
            summary_reason=summary_reason,
            conditions_passed=passed,
            conditions_failed=failed,
            conditions_unknown=unknown,
            targeted_followup_questions=questions,
            benefit_estimates=benefit_estimates,
        )
