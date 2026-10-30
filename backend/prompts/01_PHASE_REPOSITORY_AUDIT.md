# Phase 1 — Repository Audit and Implementation Plan

## Instructions

Read `00_MASTER_PROMPT.md` completely and obey it. This phase is inspection and planning first. Do not perform destructive rewrites.

## Objectives

1. Inspect the repository as it exists.
2. Identify frontend/backend/database architecture and dependencies.
3. Identify current functionality, incomplete screens, existing data, API integrations, auth, tests and deployment configuration.
4. Establish a baseline test result.
5. Propose a staged implementation plan that preserves working code.

## Required work

- Print/list the repository tree, excluding dependency caches and secrets.
- Read README files and relevant dependency manifests.
- Locate environment variable names without printing their values.
- Identify all places that contain static fixtures, fake metrics, hardcoded responses, placeholder scheme records or mock service implementations.
- Identify existing database schemas/migrations and whether production and test environments are isolated.
- Run existing tests, lint, type checks and build commands when safe and available. Report missing commands honestly.
- Inspect frontend routes and connect each user-visible action to its actual handler/API.
- Inspect backend endpoints and external service adapters.
- Identify data-source provenance and whether any current scheme information has been verified.
- Review auth, authorization, secrets, file handling, logging and user data isolation at a high level.

## Deliverables

Create or update:
- `docs/architecture/current-state.md`
- `docs/architecture/target-state.md`
- `docs/architecture/gap-analysis.md`
- `docs/architecture/implementation-roadmap.md`
- `STATUS.md`
- `DECISIONS.md` for decisions that are genuinely needed.

## Restrictions

- Do not seed any data.
- Do not make UI changes just to make the application look fuller.
- Do not remove existing functionality without documenting why.
- Do not expose secrets in output.
- Do not claim a test passed if it was not run.

## Exit criteria

The audit report identifies actual files and evidence, baseline test status, major risks, and a prioritized plan. Ask the user only for genuinely blocking decisions; otherwise continue to Phase 2.
