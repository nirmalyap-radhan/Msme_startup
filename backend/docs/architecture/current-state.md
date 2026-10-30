# Current State Architecture & Repository Audit

> **Audit Date:** October 24, 2026  
> **Phase:** Phase 1 — Repository Audit & Implementation Plan  
> **Auditor:** Principal Software Architect & Lead Engineer Agent  
> **Status:** Completed Baseline Audit  

---

## 1. Executive Summary

Udyog Sathi is an AI-powered government scheme discovery and assistance platform for Micro, Small, and Medium Enterprises (MSMEs) in Odisha, India.

This repository audit evaluated the current state of the workspace (`/Users/nirmalyapradhan/Downloads/udyog_sathi_dev_prompts`), verified local system toolchains and runtimes, established baseline test and build metrics, inspected environment variables, and analyzed the solution specifications defined in `prompts/00_MASTER_PROMPT.md` and the architectural whitepaper `Udyog_Sathi_MSME_Odisha_Solution.pdf`.

### Key Findings
1. **Clean Baseline / Green-Field Implementation State:** The workspace contains the project development prompt pack and governance files. No application code (`apps/`, `services/`, `packages/`, `migrations/`, `data/`, `scripts/`, `tests/`) has been created yet.
2. **Zero Mock Data Contamination:** Audit confirmed no fictional schemes, synthetic beneficiaries, fake metrics, or hardcoded API mocks exist in the workspace. The development starts from a pristine zero-mock baseline, fully complying with Rule 2 of `00_MASTER_PROMPT.md`.
3. **Robust Local AI & NLP Runtime:** The host system has Python 3.11.15 with essential data and AI libraries pre-installed (`fastapi`, `pydantic`, `SQLAlchemy`, `sentence-transformers`, `torch`, `pymupdf`, `groq`, `google-genai`). Tesseract OCR 5.5.3 is installed with 163 language packages, notably including **`ori` (Oriya/Odia)**, `hin` (Hindi), and `eng` (English).
4. **Tooling & Infrastructure Gaps:** Docker daemon is currently inactive; database drivers (`psycopg` / `asyncpg`, `pgvector`, `alembic`) are not yet installed in the Python environment; API credentials (`GROQ_API_KEY`, `SARVAM_API_KEY`, `GEMINI_API_KEY`, etc.) are not yet configured in local environment variables.
5. **Architectural Specification Ready:** A 16-page solution design document (`Udyog_Sathi_MSME_Odisha_Solution.pdf`) provides exhaustive architectural definitions for 15 core features (F1–F15), 3-valued deterministic eligibility logic, and multi-lingual Odia support.

---

## 2. Workspace File Inventory & Directory Tree

### 2.1 File Tree
```text
/Users/nirmalyapradhan/Downloads/udyog_sathi_dev_prompts/
├── .gitignore.additions
├── 00_MASTER_PROMPT.md
├── 01_PHASE_REPOSITORY_AUDIT.md
├── 02_PHASE_DATA_INGESTION.md
├── 03_PHASE_BACKEND_ELIGIBILITY.md
├── 04_PHASE_RAG_AI_INTEGRATIONS.md
├── 05_PHASE_FRONTEND_PRODUCT.md
├── 06_PHASE_TESTING_SECURITY_DEPLOYMENT.md
├── AGENT_WORKFLOW.md
├── DATA_SOURCE_REGISTER.md
├── DECISIONS.md
├── DEFINITION_OF_DONE.md
├── ENVIRONMENT.md
├── PROJECT_STRUCTURE.md
├── README.md
├── STATUS.md
├── docs/
│   └── architecture/
└── prompts/
    ├── 00_MASTER_PROMPT.md
    ├── 01_PHASE_REPOSITORY_AUDIT.md
    ├── 02_PHASE_DATA_INGESTION.md
    ├── 03_PHASE_BACKEND_ELIGIBILITY.md
    ├── 04_PHASE_RAG_AI_INTEGRATIONS.md
    ├── 05_PHASE_FRONTEND_PRODUCT.md
    ├── 06_PHASE_TESTING_SECURITY_DEPLOYMENT.md
    ├── AGENT_WORKFLOW.md
    ├── DATA_SOURCE_REGISTER.md
    ├── DECISIONS.md
    ├── DEFINITION_OF_DONE.md
    ├── ENVIRONMENT.md
    ├── README.md
    └── STATUS.md
```

### 2.2 Inspection of Existing Files
| File | Size (Bytes) | Role / Purpose | Audit Observations |
|---|---|---|---|
| `00_MASTER_PROMPT.md` | 20,154 | Project-wide master instructions & non-negotiable rules | Defines absolute no-mock rule, ₹0–₹100 budget, 3-valued logic, and 10-stage lifecycle. |
| `01_PHASE_REPOSITORY_AUDIT.md` | 2,246 | Phase 1 guidelines and exit criteria | Requires full repository audit, baseline test status, gap analysis, and roadmap. |
| `02_PHASE_DATA_INGESTION.md` | 3,975 | Phase 2 guidelines: real official data ingestion | Mandates PDF extraction, Tesseract OCR, provenance tracking, and reviewer verification. |
| `03_PHASE_BACKEND_ELIGIBILITY.md` | 3,125 | Phase 3 guidelines: backend, database, rules | Mandates deterministic rules engine, PostgreSQL schemas, and typed API endpoints. |
| `04_PHASE_RAG_AI_INTEGRATIONS.md` | 3,497 | Phase 4 guidelines: grounded RAG and AI | Specifies multi-provider adapters, citation preservation, and hallucination prevention. |
| `05_PHASE_FRONTEND_PRODUCT.md` | 3,144 | Phase 5 guidelines: frontend product flows | Requires real UI connected to backend, zero fake metrics, and Odia accessibility. |
| `06_PHASE_TESTING_SECURITY_DEPLOYMENT.md` | 3,830 | Phase 6 guidelines: security and deployment | Specifies release gates, test coverage, and deployment verification. |
| `DATA_SOURCE_REGISTER.md` | 2,155 | Register of official government portals | Identifies candidate sources: Odisha MSME, e-MSME Seva, MoMSME, myScheme. |
| `DECISIONS.md` | 987 | Architectural Decision Records (ADRs) | Initial placeholder structure ready for recording key technical decisions. |
| `DEFINITION_OF_DONE.md` | 2,323 | Quality and release acceptance gates | Rigorous checklist preventing mock releases or ungrounded assertions. |
| `ENVIRONMENT.md` | 2,901 | Safe environment variable inventory | Documents 32 variable names across app, db, storage, AI, and observability. |
| `PROJECT_STRUCTURE.md` | 2,444 | Recommended monorepo / modular layout | Reference structure (`apps/`, `services/`, `data/`, `docs/`, `scripts/`, `tests/`). |
| `STATUS.md` | 1,547 | Real-time project tracking ledger | Tracks phase progress, real data metrics, and tested integrations. |
| `.gitignore.additions` | 246 | Git ignore rules for secrets and caches | Excludes `.env*`, `data/raw/`, `data/processed/`, `node_modules/`, `*.pem`, `*.key`. |

---

## 3. Toolchain and Runtimes Audit

The host system was inspected to catalog installed software, SDKs, and capabilities:

| Component / Utility | Detected Version / Path | Availability & Status | Assessment |
|---|---|---|---|
| **OS** | macOS (Darwin 24.3.0 arm64) | Active | Host environment for local development |
| **Python Runtimes** | `/opt/homebrew/opt/python@3.11/bin/python3.11` (Python 3.11.15)<br>`/usr/bin/python3` (Python 3.9.6) | Available | Python 3.11.15 is the designated runtime for backend and AI pipelines. |
| **Node.js** | v26.12.0 | Available | Available for modern React / Next.js frontend builds. |
| **npm** | 11.20.0 | Available | Package manager ready for frontend dependencies. |
| **Docker** | Docker version 29.9.2 (build a82e528) | Daemon Not Running | Docker client installed; daemon process was inactive during audit. |
| **Tesseract OCR** | 5.5.3 (Leptonica 1.87.0) | Installed & Verified | **163 languages installed**, including `ori` (Odia), `hin` (Hindi), `eng` (English), and script models (`script/Oriya`, `script/Devanagari`). Crucial for document ingestion. |
| **PostgreSQL Client (`psql`)** | Not found in PATH | Missing CLI | Client CLI absent; Python application will use native database drivers (`psycopg`/`asyncpg`). |
| **Redis Client (`redis-cli`)** | Not found in PATH | Missing CLI | CLI absent; caching/task queues can use Python Redis client or lightweight in-process primitives for initial local dev. |

### 3.1 Key Python Packages Installed in Python 3.11
- **API & Core:** `fastapi` 0.141.1, `uvicorn` 0.52.1, `pydantic` 2.13.4, `pydantic-settings` 2.14.2, `starlette` 1.3.1
- **Database & ORM:** `SQLAlchemy` 2.0.51
- **Document Extraction & Processing:** `pymupdf` 1.28.2 (fitz), `pypdf` 6.15.0, `pypdfium2` 5.12.1, `pillow` 12.2.0, `python-docx` 1.2.0
- **AI & Embeddings:** `sentence-transformers` 5.7.0, `torch` 2.12.0, `transformers` 4.46.1, `groq` 0.37.1, `google-genai` 2.16.0, `langchain-groq` 1.1.3, `langchain-google-genai` 4.3.2
- **Testing & Tools:** `pytest` 9.1.1, `requests` 2.34.2, `httpx` (via dependencies), `rich` 15.0.0

### 3.2 Missing Python Dependencies to Add
- `asyncpg` or `psycopg` (v3) for async PostgreSQL connectivity
- `pgvector` Python client for vector operations
- `alembic` for database schema migration management
- `pytesseract` for Python bindings to Tesseract 5.5.3
- `sarvam` / `mistralai` SDKs (or standard HTTP clients)

---

## 4. Baseline Test and Build Execution

Audit checks were executed to establish official baselines:

### 4.1 Pytest Baseline
- **Command:** `/opt/homebrew/opt/python@3.11/bin/python3.11 -m pytest`
- **Exit Code:** `5`
- **Output:**
  ```text
  ============================= test session starts ==============================
  platform darwin -- Python 3.11.15, pytest-9.1.1, pluggy-1.7.0
  rootdir: /Users/nirmalyapradhan/Downloads/udyog_sathi_dev_prompts
  plugins: anyio-4.13.0
  collecting ... collected 0 items
  ============================ no tests ran in 0.00s =============================
  ```
- **Finding:** No test suites exist in the workspace yet. Exit code 5 truthfully reflects 0 items collected.

### 4.2 Frontend / npm Baseline
- **Command:** `npm test`
- **Exit Code:** `254`
- **Output:**
  ```text
  npm error code ENOENT
  npm error path /Users/nirmalyapradhan/Downloads/udyog_sathi_dev_prompts/package.json
  npm error enoent Could not read package.json: Error: ENOENT: no such file or directory
  ```
- **Finding:** No `package.json` or frontend project is scaffolded yet.

### 4.3 Git Repository Status
- **Command:** `git status`
- **Output:** The workspace directory `/Users/nirmalyapradhan/Downloads/udyog_sathi_dev_prompts` does not currently have its own local `.git` repository initialized; git operations cascade to the parent home directory (`/Users/nirmalyapradhan`).
- **Finding:** A local `.git` repository should be initialized at the project root with the rules in `.gitignore.additions` before production work.

---

## 5. Security & Environment Configuration Audit

A non-destructive, safe scan of environment variables and files was conducted in strict compliance with the no-secret-exposure rule:

### 5.1 Secret Exposure Check
- **`.env` files in repository:** `None found` (No `.env`, `.env.local`, `.env.production` files exist in workspace).
- **Credentials committed:** None.
- **Git status hygiene:** Safe.

### 5.2 Environment Variable Names Check (Values Redacted)
32 candidate variables specified in `ENVIRONMENT.md` were checked in the active shell:
- `APP_ENV`: `NOT SET`
- `APP_SECRET_KEY`: `NOT SET`
- `DATABASE_URL`: `NOT SET`
- `GROQ_API_KEY`: `NOT SET`
- `SARVAM_API_KEY`: `NOT SET`
- `GEMINI_API_KEY`: `NOT SET`
- `NVIDIA_API_KEY`: `NOT SET`
- `MISTRAL_API_KEY`: `NOT SET`
- `AI_PRIMARY_PROVIDER`: `NOT SET`
- `EMBEDDING_MODEL`: `NOT SET`
- `VECTOR_DIMENSIONS`: `NOT SET`
- `SCHEME_SOURCE_ALLOWLIST`: `NOT SET`

**Finding:** The development environment is unconfigured. A template `.env.example` must be created with variable placeholders, and real keys must be placed into a local, git-ignored `.env` file during implementation.

---

## 6. Fake Data and Mock Architecture Audit

In compliance with Rule 2 ("NO MOCK DATA"), the entire workspace was examined for:
1. Synthetic scheme fixtures: **None found**.
2. Hardcoded eligibility responses: **None found**.
3. Fake dashboard metrics or charts: **None found**.
4. Mock service adapters: **None found**.

**Conclusion:** The project is starting with a 100% clean sheet. When schemas, pipelines, and UI are built in subsequent phases, every component will be wired to real data models and verified endpoints, with explicit empty and unavailable states when services or records are not present.

---

## 7. Data Provenance & Official Source Register Status

The `DATA_SOURCE_REGISTER.md` catalog lists 5 initial candidate sources:
1. **Odisha MSME Scheme Catalogue:** `https://msme.odisha.gov.in/en/schemes/msme-schemes` (State Department - Discovery)
2. **Odisha MSME Policies & Notifications:** `https://msme.odisha.gov.in/en/notification/policies` (State Department - Authoritative IPR & Notifications)
3. **Odisha e-MSME Seva:** `https://odishamsme.nic.in/` (State Implementing Agency - Services)
4. **Ministry of MSME:** `https://www.msme.gov.in/` (Central Ministry - Central Guidelines)
5. **myScheme:** `https://www.myscheme.gov.in/` (Discovery / Aggregator)

**Current Status:**
- Official source URLs checked: `0`
- Ingested source documents: `0`
- Verified published schemes: `0`

These sources will be contacted and audited for accessibility during Phase 2 (Data Ingestion).
