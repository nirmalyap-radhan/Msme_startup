# Phase 5 — Frontend and End-to-End Product Flows

## Instructions

Read `00_MASTER_PROMPT.md` and Phases 1–4. Inspect the current design and routing before changing it. Preserve working visual components where practical.

## Objective

Connect the user interface to real backend operations and make every visible feature truthful, accessible and useful.

## Core user flows

Implement the flows supported by the actual backend:
- Language selection and accessible navigation.
- Search and filter real published schemes.
- Scheme detail page with status, evidence, last verification date and official links.
- Business profile form that collects only needed data.
- Eligibility assessment with conditions passed/failed/unknown and source evidence.
- Document checklist based on verified scheme requirements.
- Grounded assistant chat with clickable source references and uncertainty handling.
- Saved schemes and user-managed application tracker if persistence/auth are implemented.
- Admin review queue for unverified documents and proposed scheme changes, with appropriate authorization.
- Honest empty, loading, error, permission-denied and unavailable states.

## No-mock UI rule

- Do not create fake charts, counters, activity feeds, notifications, beneficiaries, success stories or sample cards.
- Do not hardcode scheme data in components.
- Do not show success until the server confirms success.
- Do not simulate a government application submission.
- Do not use placeholder content that resembles real scheme information.
- Do not conceal an API failure behind cached fake content.
- If the database is empty, show an honest empty state and explain that verified scheme records have not yet been published.
- If a feature is not implemented, label it as unavailable/not yet available or omit it rather than making it look functional.

## UX and accessibility

Make layouts responsive and usable on low-end/mobile devices. Support keyboard navigation, clear labels, validation messages and accessible contrast. Do not make Odia support claims until it has been tested with actual content and the configured services.

## Integration requirements

Every button, filter, form and link must have a real outcome. Use typed API clients where appropriate. Handle loading, empty, timeout, authentication, validation and server-error states. Never expose provider keys in browser bundles. Do not cache sensitive user data in insecure browser storage.

## Tests

Add tests for critical routes/components and end-to-end flows where practical. Verify that no production component imports test fixtures or static sample scheme records. Run build, lint, type checks and tests that the repository supports.

## Deliverables

- Functional frontend connected to real APIs.
- Accessibility and responsive improvements.
- API error/empty states.
- Integration tests and screenshots only if they represent the actual running app.
- Update `STATUS.md`.

## Exit criteria

Core user journeys work against the actual backend and database. No fabricated production content is visible. All unimplemented or unavailable features are represented honestly.
