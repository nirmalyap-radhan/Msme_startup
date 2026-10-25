# Udyog Sathi — Development Prompt Pack

## 🚀 Quick Run & Launch (Single Command)

To run the project instantly without re-scanning files:
```bash
./run.sh
# or
./build.sh
# or
make run
```
- **Web App**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health/ready
- **Stop Server**: `./build.sh --stop` (or `make stop`)
- **Run Tests**: `./build.sh --test` (or `make test`)

---

## Core rule

**No fabricated production data. No demo schemes. No mock API responses. No fake dashboard metrics.**
Use only source-traceable government scheme information that has passed the documented verification workflow. Empty states and honest service errors are preferable to invented content.

## How to use this pack

1. Copy this folder into the root of your existing Udyog Sathi repository.
2. Start your coding agent in the repository root.
3. Read `00_MASTER_PROMPT.md` first and follow its repository-audit instructions.
4. Execute phases in order: `01_PHASE_REPOSITORY_AUDIT.md` through `06_PHASE_DEPLOYMENT_AND_RELEASE.md`.
5. At the beginning of each phase, tell the agent to read `00_MASTER_PROMPT.md` and the relevant phase file.
6. Do not ask the agent to skip ahead while previous phase exit criteria remain unmet.
7. Update `STATUS.md` at the end of each phase with actual evidence and blockers.

## Prompt files

- `00_MASTER_PROMPT.md` — persistent rules, architecture principles, no-mock policy, security, quality gates.
- `01_PHASE_REPOSITORY_AUDIT.md` — inspect the existing project and produce an evidence-based plan.
- `02_PHASE_DATA_INGESTION.md` — real official-source ingestion, verification, versioning and scheme catalogue.
- `03_PHASE_BACKEND_ELIGIBILITY.md` — database, API, profiles, deterministic eligibility and benefit calculations.
- `04_PHASE_RAG_AI_INTEGRATIONS.md` — grounded retrieval, citations, LLM provider adapters and multilingual support.
- `05_PHASE_FRONTEND_PRODUCT.md` — real frontend flows connected to backend and data.
- `06_PHASE_TESTING_SECURITY_DEPLOYMENT.md` — integration tests, security review, deployment and release gates.
- `STATUS.md` — record progress without claiming unverified completion.
- `DATA_SOURCE_REGISTER.md` — register official sources, access method, verification and update status.
- `DECISIONS.md` — record material architecture decisions and reasons.
- `DEFINITION_OF_DONE.md` — release acceptance checklist.
- `ENVIRONMENT.md` — safe environment variable inventory; never put secrets here.
- `AGENT_WORKFLOW.md` — how to operate the coding agent safely.

## Non-negotiable execution behavior

- Inspect the actual repository before changing it.
- Preserve working code unless there is evidence it needs changing.
- Do not invent API endpoints, provider capabilities, scheme facts, or test results.
- Do not expose or print secret values. Never commit `.env`.
- Do not seed production with synthetic or placeholder records.
- Test real integrations only when credentials and permissions exist; otherwise document the blocker and implement a safe, explicit unavailable state.
- Keep synthetic fixtures strictly isolated to tests and ensure they cannot enter production.
- Do not declare a phase complete without evidence for its exit criteria.
# Msme_startup
