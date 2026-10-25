# Phase 6 — Quality, Security, Deployment and Release

## Instructions

Read `00_MASTER_PROMPT.md` and all previous phase reports. Do not call the application production-ready unless the release gates below are evidenced.

## Objectives

Verify the complete system, remediate critical issues and prepare a repeatable deployment within the authorized budget.

## Testing

Run and report actual results for:
- Unit tests.
- Eligibility rules and benefit formulas.
- Database migration and integration tests.
- Ingestion, duplicate/version and review workflow tests.
- RAG retrieval and citation correctness.
- Provider timeouts, quota limits and missing credentials.
- Authentication and authorization.
- Cross-user data access/isolation.
- Input validation and upload safety.
- Frontend build, lint and type checking.
- Critical end-to-end user journeys.
- Production-data contamination check for fixtures/mock adapters.
- Backup/restore process if configured.

Never fabricate passing results. Clearly distinguish tests run locally, tests run in CI and tests not run.

## Security review

Review:
- Secret exposure and repository history.
- Authentication/session handling.
- Role checks on admin operations.
- Database access and row-level isolation.
- CORS, TLS and security headers.
- Rate limiting and abuse prevention.
- File upload validation and access control.
- PII redaction in logs and model prompts.
- Prompt injection and unsafe retrieved content.
- Dependency vulnerabilities.
- Data retention and consent.
- Error messages and stack trace exposure.
- Backup access and restore procedures.

Do not run destructive or production-affecting tests without authorization.

## Deployment

1. Select a deployment target based on current free-tier terms and the actual application.
2. Document sleep, quota, database expiry, storage, bandwidth and commercial-use restrictions.
3. Configure secrets through the host's secret manager/dashboard.
4. Apply migrations in a controlled way.
5. Configure health/readiness checks and logs.
6. Configure allowed origins, TLS, CORS and rate limits.
7. Verify that frontend and backend communicate correctly.
8. Verify real scheme search, scheme detail, eligibility, RAG citations and admin permissions in the deployed environment.
9. Confirm that the deployed database contains only genuinely ingested and approved production data.
10. Record rollback and backup/recovery instructions.
11. Do not enable paid billing or purchase a domain/service without explicit permission.

If the agent lacks deployment credentials, produce exact steps and state clearly that deployment has not been performed.

## Release acceptance gates

Release is blocked if:
- Any fabricated scheme or fake metric is exposed in production.
- Secrets are committed or exposed.
- Unverified scheme records are publicly presented as authoritative.
- Eligibility results have no traceable rules/evidence.
- AI citations are fabricated or untraceable.
- Critical authorization/data-isolation defects remain.
- Critical tests fail without an accepted documented mitigation.
- Deployment is described as successful without verification.

## Final deliverables

- `docs/quality/test-report.md`
- `docs/security/security-review.md`
- `docs/deployment/runbook.md`
- `docs/deployment/rollback-and-recovery.md`
- Updated `STATUS.md`, `DATA_SOURCE_REGISTER.md`, `ENVIRONMENT.md` and `DEFINITION_OF_DONE.md`.

## Final report

List what was actually tested and deployed, what remains incomplete, any known risks, actual source counts, provider availability, budget implications and the exact steps to run/operate the application.

## Exit criteria

All release gates are satisfied or the application is explicitly labeled a limited pilot/not production-ready, with the remaining blockers and remediation steps documented.
