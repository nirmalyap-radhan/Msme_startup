# Phase 3 — Backend, Database, Profiles and Eligibility

## Instructions

Read `00_MASTER_PROMPT.md` and previous phase reports. Adapt to the actual repository; do not introduce a second backend or database unnecessarily.

## Objectives

Implement persistent, secure application functionality and a deterministic eligibility engine based on verified scheme rules.

## Required work

1. Create/extend database migrations for schemes, versions, evidence, eligibility rules, user profiles, saved schemes and user-managed application tracking as needed.
2. Add constraints, indexes, foreign keys and migration rollback guidance where practical.
3. Implement validated API schemas and documented endpoints for:
   - Published scheme search and filters.
   - Scheme details and evidence/source references.
   - User profile creation/update, if authentication exists.
   - Eligibility evaluation.
   - Document checklist generation from verified requirements.
   - Saved schemes and user-managed tracking where in scope.
   - Admin review and publication, protected by role checks.
4. Keep public read-only endpoints separate from privileged admin endpoints.
5. Ensure every query filters to published/currently applicable records where appropriate.
6. Implement a rules representation that can express required facts, comparisons, exclusions and unknown values.
7. Attach evidence references and rule versions to each condition.
8. Return `potential_match`, `more_information_required`, `not_eligible_under_verified_rules`, or `rules_unverified` as appropriate.
9. Do not calculate benefit amounts unless a verified formula, applicable dates and required inputs exist.
10. Validate user inputs and avoid collecting unnecessary personal information.
11. Add authentication/authorization and row/tenant isolation appropriate to the current app. If auth is not yet configured, document protected functionality and implement a safe development setup without exposing it publicly.
12. Add pagination, filtering, rate limiting and consistent error formats appropriate to the stack.
13. Keep application tracking explicitly user-managed unless an authorized government integration genuinely submits or synchronizes applications.

## No-mock rule

All production API results must come from persisted records and actual rule execution. Empty database means empty search results, not example schemes. Never return a hardcoded “eligible” result.

## Tests

Add unit tests for each rule operator and unknown state, date boundaries, missing fields, conflicting versions, access controls, user data isolation, empty catalogues and database failures. Synthetic data may exist only in isolated tests.

## Deliverables

- Migrations and backend endpoints.
- Eligibility rules documentation.
- API contract/OpenAPI updates.
- Automated tests and commands.
- Update `STATUS.md` and `DECISIONS.md`.

## Exit criteria

Real published records can be queried through the API; eligibility evaluates stored, reviewed rules with evidence; empty states and unknown conditions behave honestly; tests and access controls pass or blockers are documented.
