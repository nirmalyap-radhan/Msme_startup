# Prioritized Implementation Roadmap

> **Project:** Udyog Sathi  
> **Architecture Plan:** Phased Rollout (Phases 2 through 6)  
> **Status:** Approved for Implementation (Awaiting Phase 2 Initiation)  

---

## 1. Roadmap Overview & Milestones

Following the baseline audit in Phase 1, development proceeds in five sequential, test-driven phases. Each phase builds upon the verified deliverables of the preceding phase, with strict exit criteria that prevent premature progression or mock data contamination.

```text
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│     PHASE 1     │     │     PHASE 2     │     │     PHASE 3     │
│ Repository      │────▶│ Data Ingestion  │────▶│ Backend, DB &   │
│ Audit & Plan    │     │ & Verification  │     │ Eligibility     │
│   [COMPLETED]   │     │  [READY TO GO]  │     │                 │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                                                         │
                                                         ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│     PHASE 6     │     │     PHASE 5     │     │     PHASE 4     │
│ Testing, Sec &  │◀────│ Frontend Product│◀────│ RAG Citations   │
│ Deployment      │     │ Flows (ZeroMock)│     │ & AI Gateway    │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

---

## 2. Phase-by-Phase Work Breakdown

### Phase 2: Official Scheme Data Ingestion and Verification
*Reference:* `02_PHASE_DATA_INGESTION.md`

#### Objectives
Build a reusable, verifiable data ingestion pipeline that retrieves real government scheme documents from official Odisha/Central portals, extracts text (digital PDF + Tesseract OCR), preserves provenance, and provides an admin verification workflow.

#### Detailed Tasks
1. **Repository Layout Initialization:**
   - Initialize local git repository with `.gitignore.additions`.
   - Create directories: `services/scheme_ingestion/`, `data/raw/`, `data/processed/`, `scripts/`.
2. **Environment & Dependency Setup:**
   - Create `.env.example` with documented placeholders.
   - Install missing Python libraries: `pytesseract`, `psycopg[binary]`, `asyncpg`, `alembic`, `pgvector`.
3. **Document Ingestion Engine:**
   - Build `services/scheme_ingestion/fetcher.py`: Respects allowlisted government domains, downloads documents, logs HTTP headers, and computes SHA-256 hashes.
   - Build `services/scheme_ingestion/extractor.py`: Uses `pymupdf` to extract text, tables, and page metadata; detects scanned pages and routes to Tesseract OCR with `-l ori+eng`.
   - Build `services/scheme_ingestion/normalizer.py`: Standardizes dates, currency amounts (INR / Lakhs / Crores), and contact details.
4. **Data Models & Storage:**
   - Define schema for `source_documents`, `scheme_drafts`, `verification_events`.
   - Store raw downloaded PDFs securely in `data/raw/` (excluded from git).
5. **Admin Review & Publication CLI/API:**
   - Implement `scripts/verify_source_records.py` and CLI commands for reviewers to inspect extracted fields alongside original PDF text and promote records to `verified` and `published`.
6. **Provenance Registration:**
   - Ingest at least 1–3 official Odisha MSME schemes (e.g., *Odisha MSME Development Policy 2022 / Capital Investment Subsidy*).
   - Log entries in `DATA_SOURCE_REGISTER.md`.

#### Exit Criteria
- Ingestion pipeline successfully executes against at least one real official Odisha MSME document.
- Extracted text preserves page numbers, source URL, and SHA-256 hash.
- Scanned text extraction verified with Tesseract `ori` language model.
- Admin verification workflow promotes draft to published status.
- Zero mock or synthetic schemes inserted into data stores.

---

### Phase 3: Backend, Database, Profiles and Deterministic Eligibility
*Reference:* `03_PHASE_BACKEND_ELIGIBILITY.md`

#### Objectives
Implement the core relational database schema with migrations, FastAPI REST endpoints, enterprise profile management, and the deterministic 3-valued eligibility rules engine.

#### Detailed Tasks
1. **Database & Migrations:**
   - Setup Alembic configuration in `migrations/`.
   - Define SQLAlchemy models for `schemes`, `scheme_versions`, `eligibility_rules`, `benefit_formulas`, `user_profiles`, `application_tracking`, `audit_logs`.
   - Apply migration scripts creating all tables and constraints.
2. **Deterministic Rules Engine (`services/eligibility/`):**
   - Implement 3-valued rule evaluator (`evaluator.py`) supporting `True`, `False`, `Unknown`.
   - Operators: `=`, `!=`, `>`, `>=`, `<`, `<=`, `IN`, `NOT IN`, `EXCLUDES`.
   - Link each rule condition to its legal clause citation (e.g., Clause 4.2 of IPR 2022).
   - Implement `benefit_calculator.py` with formula validation (caps, percentages, tenures).
3. **FastAPI Application (`apps/api/`):**
   - Implement typed Pydantic v2 schemas for request/response contracts.
   - `GET /api/v1/schemes`: Filtered search over published schemes (empty state when no records match).
   - `GET /api/v1/schemes/{id}`: Full scheme details with source citations and verification history.
   - `POST /api/v1/eligibility/evaluate`: Deterministic evaluation with line-by-line reasoning trace.
   - `POST /api/v1/profiles`: User profile persistence.
   - `GET /api/v1/schemes/{id}/checklist`: Document requirements checklist.
   - `POST /api/v1/admin/schemes/{id}/verify`: Protected endpoint for admin sign-off.
4. **Security & Input Validation:**
   - Add rate limiting, CORS configuration, and security headers.
   - Add RBAC role validation dependencies (`RoleChecker`).

#### Exit Criteria
- Database migrations execute cleanly forward and backward.
- All public scheme queries return only verified, published records.
- Deterministic rules engine passes 100% of unit tests covering `True`, `False`, and `Unknown` conditions.
- Benefit calculator strictly requires verified formulas and valid inputs.
- API documentation generated via OpenAPI `/docs`.

---

### Phase 4: Grounded RAG, Citations and AI Provider Gateway
*Reference:* `04_PHASE_RAG_AI_INTEGRATIONS.md`

#### Objectives
Implement grounded question-answering using the verified scheme corpus, multi-provider LLM adapters with bounded fallbacks, and strict citation preservation.

#### Detailed Tasks
1. **Multi-Provider AI Gateway (`apps/api/ai/`):**
   - Define abstract `LLMProvider` interface.
   - Implement `GroqAdapter` (Llama 3.3 70B, low latency).
   - Implement `GeminiAdapter` (Google GenAI SDK, high context).
   - Implement `SarvamAdapter` (Odia translation and speech API integration).
   - Implement `MistralAdapter` (backup completion provider).
   - Add request timeouts (15s), bounded retries (max 2), error classification, and usage tracking.
   - Enforce **zero-mock fallback**: if all providers fail or are unconfigured, return honest HTTP 503 (`service_unavailable`).
2. **Retrieval Pipeline:**
   - Chunk verified documents into passages preserving page, section, and scheme IDs.
   - Generate embeddings using local `sentence-transformers` (`paraphrase-multilingual-MiniLM-L12-v2` or `BGE-M3`).
   - Store in PostgreSQL `pgvector` or hybrid lexical-dense search index.
   - Retrieval query filters strictly to `published` status and relevant jurisdiction.
3. **Grounded Generation & Citation Enforcement:**
   - Prompt engineering: constrain LLM to retrieved context only; mandate citations `[Scheme, Document, Page, URL]`.
   - Detect unanswerable queries and output explicit disclaimers directing user to official authorities.
   - DPDP privacy filter: redact phone numbers, Aadhaar, PAN from prompts before transmission.
4. **RAG Evaluation Suite:**
   - Build golden test set (`data/evaluation/rag_golden_set.json`) based on actual Odisha policies.
   - Evaluate answer faithfulness, citation accuracy, and abstention behavior.

#### Exit Criteria
- Grounded answers cite verified source documents, pages, and URLs.
- Provider gateway safely handles missing keys, timeouts, and quota errors without mock data.
- Odia query handling evaluated and documented.
- Evaluation script passes with zero hallucinated scheme facts.

---

### Phase 5: Frontend and End-to-End Product Flows
*Reference:* `05_PHASE_FRONTEND_PRODUCT.md`

#### Objectives
Develop an accessible, high-performance web interface and PWA connected to the real FastAPI backend, featuring native Odia language support, clear empty states, and zero fake metrics.

#### Detailed Tasks
1. **Frontend Project Scaffolding (`apps/web/`):**
   - Initialize Next.js / React application with TypeScript.
   - Implement lightweight, responsive design system optimized for mobile devices and low-bandwidth connections.
   - Configure internationalization (i18next) for Odia, Hindi, and English.
2. **Core User Journeys:**
   - **Scheme Catalogue & Search:** Real-time search and filtering against `/api/v1/schemes`. Truthful empty state when no schemes match.
   - **Scheme Details View:** Displays official department, benefits, eligibility criteria, and clickable official PDF links.
   - **Smart Eligibility Wizard:** Multi-step profile intake calculating real-time deterministic eligibility with reasoning traces.
   - **Grounded Assistant Chat:** Conversational interface with citation badges linking to source documents.
   - **Document Checklist:** Clear checklist of required proofs derived directly from scheme rules.
   - **User-Managed Tracker:** Tracking interface with clear disclaimers that submissions occur on official portals.
   - **Admin Review Console:** Protected interface for department reviewers to inspect drafts and approve schemes.
3. **Zero-Mock UI Validation:**
   - Remove any sample cards, static counters, or dummy charts.
   - Verify all buttons and forms trigger real backend operations.

#### Exit Criteria
- Frontend runs cleanly and connects to backend API.
- All 15 core flows function end-to-end against database records.
- Odia typography renders correctly using Noto Sans Odia.
- Zero mock or placeholder data rendered in production UI.

---

### Phase 6: Quality, Security, Deployment and Release
*Reference:* `06_PHASE_TESTING_SECURITY_DEPLOYMENT.md`

#### Objectives
Execute end-to-end testing, perform a comprehensive security audit, package the application for zero-cost deployment, and produce reproducible runbooks.

#### Detailed Tasks
1. **Comprehensive Test Suite Execution:**
   - Run unit, integration, RAG evaluation, and frontend E2E tests.
   - Execute `scripts/check_no_production_fixtures.py` to ensure test data does not leak into production.
2. **Security & Privacy Audit:**
   - Secret scan to verify no credentials exist in repository history.
   - Verify CORS, CSRF, security headers, rate limiting, and SQL injection protections.
   - Verify RBAC role boundaries and data isolation across users.
3. **Deployment Configuration:**
   - Create multi-stage `Dockerfile` and `docker-compose.yml`.
   - Prepare deployment manifests for free-tier hosting (Render / Supabase / Vercel).
   - Document environment setup, health check endpoints, and rollback procedures.
4. **Documentation & Release Sign-Off:**
   - Complete `docs/quality/test-report.md`, `docs/security/security-review.md`, `docs/deployment/runbook.md`.
   - Update `STATUS.md`, `DEFINITION_OF_DONE.md`.

#### Exit Criteria
- All release acceptance gates in `06_PHASE_TESTING_SECURITY_DEPLOYMENT.md` satisfied.
- Clean automated test run across all layers.
- Free-tier deployment verified or reproducible deployment runbook provided.
