# Definition of Done — Udyog Sathi

## Data integrity
- [ ] No fictional or demo records in production.
- [ ] Every published scheme has traceable official source evidence.
- [ ] Material eligibility/benefit/date facts have passed review.
- [ ] Versioning, supersession and expiry states are implemented.
- [ ] Empty catalogue and ingestion failure states are honest.
- [ ] Data refresh and review responsibilities are documented.

## Product behavior
- [ ] Search queries actual published records.
- [ ] Scheme details display real provenance and verification status.
- [ ] Eligibility uses deterministic, versioned rules.
- [ ] Unknown/missing information is represented explicitly.
- [ ] Benefits are calculated only from verified formulas and required inputs.
- [ ] RAG answers use retrieved evidence and real citations.
- [ ] Every visible action is connected to a real operation or honestly unavailable.
- [ ] No fake dashboard metrics, testimonials, activity feeds or success notifications.

## AI and integrations
- [ ] Provider credentials are server-side and not exposed in logs or client bundles.
- [ ] Model/endpoint/quota access is verified for every claimed integration.
- [ ] Provider errors and limits are handled safely.
- [ ] No mock fallback is reachable in production.
- [ ] Unsupported questions result in an honest uncertainty response.
- [ ] Odia and other language claims are evaluated on actual examples.

## Security and privacy
- [ ] Authentication and admin authorization tested.
- [ ] User data isolation tested.
- [ ] Secrets excluded from version control.
- [ ] Input validation, rate limits and safe errors implemented.
- [ ] Sensitive data minimized and redacted from logs.
- [ ] Consent, retention, storage access and backup practices documented.

## Quality
- [ ] Tests and build/lint/type checks actually run.
- [ ] Failures are fixed or documented with an accepted mitigation.
- [ ] Production DB cannot be seeded from test fixtures.
- [ ] Deployment configuration and rollback/recovery steps documented.
- [ ] Actual free-tier limits and cost risks documented.
- [ ] `STATUS.md` reflects evidence and known limitations.

## Release decision

- **Decision:** Not assessed / Limited pilot / Production release
- **Date:**
- **Evidence:**
- **Outstanding blockers:**
- **Approved by:**
