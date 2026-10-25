# Frontend Architecture & End-to-End Product Flows (Phase 5)

## 1. Architectural Overview

The Udyog Sathi user-facing frontend is engineered as a zero-dependency, highly performant web application integrated directly with the FastAPI backend. It provides Odisha entrepreneurs with evidence-grounded government scheme discovery, mathematical 3-valued eligibility evaluations, and multilingual AI advisory in Odia, Hindi, and English.

```
                              [ Browser / Client ]
                                        │
           ┌────────────────────────────┼────────────────────────────┐
           ▼                            ▼                            ▼
   [ Vanilla HTML5 ]            [ Vanilla CSS ]              [ Modular JS ]
   - Semantic markup            - Design Tokens              - api.js (Typed Client)
   - SEO metadata               - Components & Cards         - i18n.js (Trilingual)
   - Accessibility ARIA         - Shimmer Animations         - catalogue.js (Search)
                                - Responsive Grid            - eligibility.js (3-Valued)
                                                             - assistant.js (RAG/Voice)
                                                             - tracker.js (Compliance)
                                                             - admin.js (Governance)
                                                             - app.js (Orchestrator)
                                        │
                                        ▼
                         [ FastAPI Unified Gateway ]
                         - /app & / (HTML Viewport)
                         - /static (StaticFiles Mount)
                         - /api/v1 (REST API Endpoints)
```

---

## 2. Core User Journeys & Implementation

### Journey 1: Scheme Discovery & Legal Verification
- **Endpoint:** `GET /api/v1/schemes`
- **Controller:** `catalogue.js`
- **Features:**
  - Real-time debounced search by scheme name, keywords, and subsidy types.
  - Sector filter chips (`manufacturing`, `service`) and enterprise class filters (`micro`, `small`, `medium`).
  - Scheme cards rendering departmental issuer, verified status badges, and official PDF links.
  - Comprehensive Scheme Detail & Statutory Evidence Modal: Displays policy summary, exact legal eligibility clauses, verified financial assistance formulas, required document checklist, and departmental portal links.

### Journey 2: Deterministic Three-Valued Eligibility Evaluator
- **Endpoint:** `POST /api/v1/eligibility/evaluate`
- **Controller:** `eligibility.js`
- **Features:**
  - Form collecting operational parameters: enterprise class, sector, state, district, commercial production status, Udyam registration, plant & machinery investment, turnover, working capital loan, and interest paid.
  - Pure mathematical evaluation using Kleene 3-valued logic (`Passed`, `Failed`, `Unknown`).
  - Transparent outcome badges: `POTENTIAL MATCH`, `MORE INFORMATION REQUIRED`, or `NOT ELIGIBLE UNDER VERIFIED RULES`.
  - Financial formula derivation: e.g., computing exact 75% interest subvention for micro enterprises based on actual interest paid and statutory caps.
  - Targeted follow-up queries: If information is missing (such as Udyam status), targeted prompts appear directly with input fields allowing immediate re-evaluation.

### Journey 3: Grounded AI Sathi Advisory & Multilingual Speech
- **Endpoints:** `POST /api/v1/rag/ask`, `POST /api/v1/rag/voice/synthesize`
- **Controller:** `assistant.js`
- **Features:**
  - Hybrid BM25 retrieval across verified Odisha MSME gazette passages.
  - Strict evidence grounding via Groq Qwen 2.5 27B: Zero hallucination, refusal when evidence is inconclusive.
  - Clickable statutory legal citations on every response: document name, physical page number, verified SHA-256 hash, and PDF link.
  - Sarvam AI `bulbul:v3` text-to-speech voice synthesis in Odia (`od-IN`), providing spoken advisory for rural entrepreneurs with audio waveform controls.

### Journey 4: User-Managed Compliance Tracker
- **Endpoints:** `GET /api/v1/applications`, `POST /api/v1/applications`, `PUT /api/v1/applications/{id}`
- **Controller:** `tracker.js`
- **Features:**
  - Prominent transparency notice: strictly self-managed enterprise record ledger; no fake portal scraping or simulated state syncs.
  - Entrepreneur records acknowledgement numbers, submission dates, filing portal URLs, and internal audit notes.
  - Lifecycle milestone tracking: `draft`, `submitted`, `under_scrutiny`, `queried`, `approved`, `rejected`, `disbursed`.

### Journey 5: Departmental Reviewer Governance Queue
- **Endpoints:** `GET /api/v1/admin/schemes/pending`, `GET /api/v1/admin/schemes/{id}/dossier`, `POST /api/v1/admin/schemes/{id}/verify`
- **Controller:** `admin.js`
- **Features:**
  - Role-based access control (RBAC): restricted to `scheme_reviewer` and `platform_admin`.
  - Queue displaying extracted draft schemes pending sign-off.
  - Extraction dossier modal showing source PDF hash and extracted candidate clauses vs assistance formulas.
  - Officer sign-off with mandatory verification audit notes (min 10 characters) publishing directly to the live catalogue.

---

## 3. Zero-Mock UI Enforcement

In strict compliance with **Rule 2 of 00_MASTER_PROMPT.md**:
1. **No Synthetic Schemes:** Only official schemes retrieved by the ingestion pipeline and published in `data/udyog_sathi.db` appear (`OD-MSME-C0B98FA5` and `OD-MSME-AFD17307`).
2. **Honest Empty States:** Empty searches or missing records display informative empty states pointing directly to `https://msme.odisha.gov.in`.
3. **No Fake Status Sync:** The Application Tracker prominently explains that status tracking is self-managed by the business owner.
4. **No Placeholder Stats:** Header and hero statistics reflect live database counts (`/health/ready`).
5. **No Hallucinated Citations:** Assistant responses cite only actual document chunks stored in SQLite with page numbers and SHA-256 hashes.

---

## 4. Localization (i18n)

The interface supports three languages through `apps/web/static/js/i18n.js`:
- **English (`en`)**: Primary administrative and statutory language.
- **Odia (`od`)**: State language of Odisha (ଓଡ଼ିଆ), providing full localized UI strings and Sarvam AI voice synthesis.
- **Hindi (`hi`)**: Widely used across MSME industrial corridors.

Language switching triggers instantaneous DOM re-rendering via `data-i18n` attributes without requiring a page refresh.

---

## 5. Verification & Test Results

- **Backend Pytest Suite:** 64 tests passed (0 failures).
- **Frontend Product Tests (`test_frontend_product.py`):**
  - `test_serve_index_html_via_app_route`: Passed.
  - `test_serve_index_html_via_root_when_accept_html`: Passed.
  - `test_serve_json_via_root_when_accept_json`: Passed.
  - `test_static_css_assets_served`: Passed.
  - `test_static_js_assets_served`: Passed.
  - `test_index_html_semantic_structure_and_zero_mock`: Passed.
  - `test_frontend_zero_mock_no_hardcoded_schemes`: Passed.
- **Zero-Mock Audit (`scripts/check_no_production_fixtures.py`):** 100% compliant.
- **Live Integration:** Server launched on `127.0.0.1:8000`, successfully served `/app`, all static assets, `/health/ready`, and `/api/v1/schemes`.
