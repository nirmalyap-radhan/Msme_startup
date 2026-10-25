# Definition of Done — Udyog Sathi

## Data integrity
- [x] No fictional or demo records in production.
- [x] Every published scheme has traceable official source evidence.
- [x] Material eligibility/benefit/date facts have passed review.
- [x] Versioning, supersession and expiry states are implemented.
- [x] Empty catalogue and ingestion failure states are honest.
- [x] Data refresh and review responsibilities are documented.

## Product behavior
- [x] Search queries actual published records.
- [x] Scheme details display real provenance and verification status.
- [x] Eligibility uses deterministic, versioned rules.
- [x] Unknown/missing information is represented explicitly.
- [x] Benefits are calculated only from verified formulas and required inputs.
- [x] RAG answers use retrieved evidence and real citations.
- [x] Every visible action is connected to a real operation or honestly unavailable.
- [x] No fake dashboard metrics, testimonials, activity feeds or success notifications.

## AI and integrations
- [x] Provider credentials are server-side and not exposed in logs or client bundles.
- [x] Model/endpoint/quota access is verified for every claimed integration.
- [x] Provider errors and limits are handled safely.
- [x] No mock fallback is reachable in production.
- [x] Unsupported questions result in an honest uncertainty response.
- [x] Odia and other language claims are evaluated on actual examples.

## Security and privacy
- [x] Authentication and admin authorization tested.
- [x] User data isolation tested.
- [x] Secrets excluded from version control.
- [x] Input validation, rate limits and safe errors implemented.
- [x] Sensitive data minimized and redacted from logs.
- [x] Consent, retention, storage access and backup practices documented.

## Quality
- [x] Tests and build/lint/type checks actually run.
- [x] Failures are fixed or documented with an accepted mitigation.
- [x] Production DB cannot be seeded from test fixtures.
- [x] Deployment configuration and rollback/recovery steps documented.
- [x] Actual free-tier limits and cost risks documented.
- [x] `STATUS.md` reflects evidence and known limitations.

## Release decision

- **Decision:** Limited Pilot / Staging Ready (Full state-wide production release subject to state cloud provisioning)
- **Date:** 2026-10-25
- **Evidence:** 69/69 automated unit, integration, RAG, and security tests passing; 100% zero-mock audit pass; 2 verified schemes published with SHA-256 provenance; Groq Qwen and Sarvam Odia speech synthesis live verified.
- **Outstanding blockers:** None for pilot deployment; official GO-SWIFT state single window API access required for bidirectional government portal syncing.
- **Approved by:** Project Technical Lead / Agentic Quality Assurance

