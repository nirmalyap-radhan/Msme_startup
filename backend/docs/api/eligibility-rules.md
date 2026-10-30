# Udyog Sathi Deterministic Eligibility Engine Specification

## 1. Overview & Regulatory Rationale

Government scheme eligibility assessments determine whether an enterprise can receive public capital subsidies, interest subventions, or reimbursement grants. 
Under **Rule 8 of the Master Architecture**, LLMs and generative AI are strictly forbidden from acting as black-box eligibility deciders.

Instead, Udyog Sathi employs a **Deterministic Three-Valued Logic Rules Engine** (`services/eligibility/evaluator.py`). 
Every eligibility decision is reproducible, auditable, and backed by direct citations to notification clauses and physical document page numbers.

---

## 2. Three-Valued Logic (Kleene / Łukasiewicz Logic)

Standard Boolean logic (`True` / `False`) is insufficient for real-world MSME discovery because applicant profiles are frequently incomplete upon initial interaction. 

The Udyog Sathi engine models each eligibility condition under three states:
1. **`TRUE`**: The applicant's profile attribute satisfies the verified scheme condition.
2. **`FALSE`**: The applicant's profile attribute explicitly violates the verified scheme condition.
3. **`UNKNOWN`**: The applicant profile has not yet supplied the required attribute.

```
       AND | TRUE    | FALSE   | UNKNOWN
    -------+---------+---------+---------
      TRUE | TRUE    | FALSE   | UNKNOWN
     FALSE | FALSE   | FALSE   | FALSE
   UNKNOWN | UNKNOWN | FALSE   | UNKNOWN
```

### Scheme-Level Assessment Outcomes

Evaluating all verified rules of a scheme yields one of four definitive outcomes:

| Outcome | Engine Condition | UI Interpretation |
|---|---|---|
| **`POTENTIAL_MATCH`** | $\forall c \in \text{Conditions}: c = \text{TRUE}$ | The enterprise satisfies all verified eligibility conditions. Indicative financial benefits are calculated. |
| **`MORE_INFORMATION_REQUIRED`** | $(\exists c: c = \text{UNKNOWN}) \land (\forall c: c \neq \text{FALSE})$ | The enterprise has not failed any condition, but requires additional information to confirm eligibility. The engine generates targeted follow-up questions. |
| **`NOT_ELIGIBLE_UNDER_VERIFIED_RULES`** | $\exists c: c = \text{FALSE}$ | The enterprise is definitively disqualified by one or more mandatory conditions. Direct clause citations explain why. |
| **`RULES_UNVERIFIED`** | $\text{Scheme.status} \neq \text{'published'}$ | The scheme rules are in draft or pending reviewer sign-off. Cannot render an official decision. |

---

## 3. Supported Rule Operators & Condition Evaluator

The engine supports the following deterministic operators:

| Operator | Type | Behavior | Example |
|---|---|---|---|
| `=` | String / Boolean / Number | Case-insensitive string match or exact numeric/boolean equality | `state = "Odisha"`, `udyam_registered = true` |
| `!=` | Any | Inequality check | `status != "blacklisted"` |
| `IN` | String / Array | Checks whether applicant attribute exists in an approved set | `enterprise_class IN ["micro", "small"]` |
| `NOT IN` | String / Array | Exclusion check; fails if applicant attribute is in excluded set | `sector NOT IN ["tobacco", "distilleries"]` |
| `>` | Numeric | Strict greater than comparison | `production_years > 2` |
| `>=` | Numeric | Greater than or equal to | `investment_plant_machinery >= 1000000.0` |
| `<` | Numeric | Strict less than comparison | `annual_turnover < 50000000.0` |
| `<=` | Numeric | Less than or equal to | `investment_plant_machinery <= 10000000.0` |

---

## 4. Targeted Follow-Up Question Generation

When a condition evaluates to `UNKNOWN`, the engine identifies the missing attribute and attaches structured follow-up question metadata. This enables the frontend to dynamically prompt the applicant for precisely the missing inputs without requiring lengthy manual forms.

### Predefined Question Templates:
- `enterprise_class`:
  - Question: *"What is your enterprise classification under the MSMED Act?"*
  - Type: `select`, Options: `["micro", "small", "medium"]`
- `production_status`:
  - Question: *"Has your enterprise commenced commercial production or business operations?"*
  - Type: `select`, Options: `["commenced", "proposed", "under_implementation"]`
- `udyam_registered`:
  - Question: *"Do you hold a valid Udyam Registration Certificate?"*
  - Type: `boolean`, Options: `[true, false]`
- `working_capital_loan_sanctioned`:
  - Question: *"What is your sanctioned Working Capital Loan (Cash Credit) limit from banks (in INR)?"*
  - Type: `number`
- `annual_interest_paid`:
  - Question: *"What is the actual annual interest paid on your Working Capital Loan (in INR)?"*
  - Type: `number`
- `trademark_expenditure`:
  - Question: *"What was the actual expenditure incurred on trade mark registration (in INR)?"*
  - Type: `number`

---

## 5. Formula-Based Benefit Calculator (`services/eligibility/benefit_calculator.py`)

Financial subsidies and reimbursements are calculated strictly from mathematical formulas and validated applicant numbers. Under the Zero-Mock Policy, the calculator **never fabricates numbers or provides ungrounded mock estimates**.

If an applicant's financial attributes are missing, the calculator outputs:
```json
{
  "status": "insufficient_inputs",
  "benefit_type": "interest_subsidy",
  "estimated_amount_inr": null,
  "missing_inputs": ["annual_interest_paid", "working_capital_loan_sanctioned"],
  "assumptions_notes": "Provide your sanctioned working capital cash credit limit and annual interest paid to compute exact rupee reimbursement."
}
```

### Verified Benefit Formulas

#### 1. Chief Minister's Scheme for Reimbursement of Interest for MSMEs (CM-SRIM)
- **Source:** Gazette Notification 7946 / MSME dated 2024-05-15, Clauses 5.1 & 5.2.
- **Formula:**
  $$\text{Reimbursement} = \min\left( \text{Interest Paid} \times \frac{\text{Slab Percentage}}{100}, \text{Annual Ceiling (₹20 Lakh)} \right)$$
- **Slab Schedule:**
  - Sanctioned Loan $\le \text{₹10 Lakh}$: $100\%$ interest subvention.
  - Sanctioned Loan $> \text{₹10 Lakh}$ and $\le \text{₹50 Lakh}$: $75\%$ interest subvention.
  - Sanctioned Loan $> \text{₹50 Lakh}$ (up to ₹1 Crore for micro): $50\%$ interest subvention.
  - Special Category Promoters (Women, SC/ST, Persons with Disabilities): Additional 2% subvention.

#### 2. Trade Mark Assistance under OMSMED 2022
- **Source:** Operational Guidelines Notification 7206 / MSME dated 2025-08-04, Clause 6.1.
- **Formula:**
  $$\text{Reimbursement} = \min\left( 0.50 \times \text{Actual Expenditure Incurred}, \text{₹25,000 Cap} \right)$$
- **Duration:** One-time grant per registered trade mark.

#### 3. Capital Investment Subsidy
- **Formula:**
  $$\text{Subsidy} = \min\left( \text{Investment in Plant \& Machinery} \times \frac{\text{Subsidy Percentage}}{100}, \text{Max Limit} \right)$$

---

## 6. Audit & Provenance Tracing

Each evaluation result carries:
- `source_clause`: Legal notification clause (e.g. `Clause 5.1`).
- `source_page`: Physical page number in the original PDF.
- `is_verified`: Boolean confirming sign-off by a reviewer.
- Mandatory legal disclaimer: *"Assessment is advisory and based on verified rules. Government authorities hold sole jurisdiction over actual approval."*
