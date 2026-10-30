# Prompts Directory

Use the master prompt in every development session. Execute six phases in order:

1. `01_PHASE_REPOSITORY_AUDIT.md`
2. `02_PHASE_DATA_INGESTION.md`
3. `03_PHASE_BACKEND_ELIGIBILITY.md`
4. `04_PHASE_RAG_AI_INTEGRATIONS.md`
5. `05_PHASE_FRONTEND_PRODUCT.md`
6. `06_PHASE_TESTING_SECURITY_DEPLOYMENT.md`

Copy this file to `prompts/README.md` if the prompt pack is kept inside a `prompts/` folder.

For each phase, tell your coding agent:

> Read `prompts/00_MASTER_PROMPT.md`, `prompts/STATUS.md`, and the requested phase prompt completely. Inspect the existing repository and preserve working code. Execute this phase only, meet its exit criteria, run the relevant tests, and update the status and registers with evidence. Do not use mock/demo production data. Do not claim success without proof. If blocked, explain the actual blocker and continue with unblocked tasks.
