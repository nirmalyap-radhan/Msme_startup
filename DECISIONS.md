# Architecture Decision Log

Record material decisions only after inspecting the repository and available constraints. Do not fill this file with assumed decisions.

---

## ADR-001: Modular Monolith Architecture Pattern

- **Status:** Accepted
- **Date:** 2026-10-24
- **Context:** Udyog Sathi requires coordination between document ingestion, deterministic eligibility evaluation, vector retrieval, and a multilingual web UI under a strict budget constraint of ₹0–₹100. Microservices would introduce operational complexity, container orchestration overhead, and network latency that exceed the free-tier infrastructure budget.
- **Options considered:**
  1. *Distributed Microservices* (separate services for Ingestion, RAG, Eligibility, and Auth).
  2. *Modular Monolith* (FastAPI backend with distinct service modules + Next.js frontend).
  3. *All-in-One Serverless Functions*.
- **Decision:** Adopt a **Modular Monolith** structure (`apps/api` with distinct domains in `services/scheme_ingestion`, `services/eligibility`, `apps/api/ai`, and `apps/web` for frontend).
- **Reasoning/evidence:** A modular monolith provides strict internal boundaries, shared database transactions, zero inter-service network overhead, and simplifies zero-cost single-instance deployment on Render/Railway/Fly.io.
- **Consequences and trade-offs:** Services share a runtime process and database. Scaling individual components independently is deferred until traffic mandates horizontal decomposition.
- **Security/privacy impact:** Simplifies internal data isolation, consolidated audit logging, and centralized RBAC enforcement.
- **Cost/quota impact:** ₹0.00 infrastructure cost; easily fits within single free-tier container limits.
- **Revisit when:** Platform traffic exceeds 50,000 monthly active users or individual ingestion workloads saturate CPU cores.

---

## ADR-002: Relational Database & Vector Storage Strategy

- **Status:** Accepted
- **Date:** 2026-10-24
- **Context:** The application requires strong relational integrity for scheme metadata, version history, audit logs, and deterministic eligibility rules, as well as semantic search over document chunks.
- **Options considered:**
  1. *Separate Database + Standalone Vector DB* (PostgreSQL + Pinecone / Qdrant Cloud).
  2. *Single PostgreSQL Instance with `pgvector` extension*.
  3. *SQLite with sqlite-vss*.
- **Decision:** Standardize on **PostgreSQL 16 with pgvector**.
- **Reasoning/evidence:** Eliminates the need to maintain, synchronize, and pay for a separate vector database. PostgreSQL provides ACID transactions, Row-Level Security (RLS), full-text search, and vector similarity search in a single unified system. Free tiers are readily available via Supabase, Neon, or local Docker.
- **Consequences and trade-offs:** Vector indexing on extremely large corpora (millions of chunks) requires tuning HNSW/IVFFlat indexes, but the scheme document corpus (hundreds to thousands of pages) will operate well within optimal performance thresholds.
- **Security/privacy impact:** Native PostgreSQL Row-Level Security and field-level encryption protect applicant profiles and sensitive records.
- **Cost/quota impact:** ₹0.00; supported on free cloud tiers (Supabase 500MB free tier or local Docker).
- **Revisit when:** Chunk corpus exceeds 500,000 embeddings or requires specialized hybrid ranking across millions of records.

---

## ADR-003: Deterministic Three-Valued Eligibility Engine

- **Status:** Accepted
- **Date:** 2026-10-24
- **Context:** LLMs cannot be trusted to make definitive legal eligibility determinations due to hallucination risks, non-determinism, and lack of auditable reasoning.
- **Options considered:**
  1. *Prompt-based LLM Eligibility Check* (free-form generation).
  2. *Hybrid Rule-Assisted LLM Prompting*.
  3. *Pure Deterministic Three-Valued Rules Engine* (`Eligible`, `Likely Eligible`, `Not Eligible`, `Rules Unverified`) with legal clause citations.
- **Decision:** Build a **pure deterministic rules engine** using three-valued logic. The LLM's role is strictly limited to explaining the engine's structured reasoning trace in plain English, Hindi, or Odia.
- **Reasoning/evidence:** Meets regulatory compliance, guarantees 100% reproducible outcomes, handles missing user facts gracefully with targeted follow-up prompts, and satisfies Rule 8 of `00_MASTER_PROMPT.md`.
- **Consequences and trade-offs:** Scheme rules must be structured into machine-readable conditions during the ingestion and verification phase.
- **Security/privacy impact:** Complete explainability; eliminates automated bias and black-box decision making.
- **Cost/quota impact:** ₹0.00 compute cost; executes in sub-millisecond local CPU cycles.
- **Revisit when:** Complex non-Boolean judicial conditions require formal constraint logic programming solvers.

---

## ADR-004: Multi-Provider AI Gateway with Zero-Mock Fallbacks

- **Status:** Accepted
- **Date:** 2026-10-24
- **Context:** The user holds API credentials across multiple providers (Groq, Gemini, Sarvam AI, Mistral, NVIDIA). Different providers have differing quotas, latency profiles, and regional language capabilities.
- **Options considered:**
  1. *Single Provider Lock-In* (e.g., OpenAI or Gemini only).
  2. *Pluggable Provider Gateway* with unified `LLMProvider` interface and zero-mock error handling.
- **Decision:** Implement a **server-side pluggable provider adapter layer** behind a common interface:
  - **Groq:** Primary low-latency generation (Llama 3.3 70B).
  - **Gemini:** Document reasoning and complex extraction.
  - **Sarvam AI:** Dedicated Odia language translation, speech-to-text, and voice synthesis.
  - **Mistral / NVIDIA:** Secondary fallback providers.
  - **Strict Failure Policy:** In case of provider failure, exhaustion, or missing credentials, return an honest HTTP 503 (`service_unavailable`) status; never fall back to fabricated mock answers.
- **Reasoning/evidence:** Prevents vendor lock-in, optimizes cost, ensures specialized Indian language processing, and strictly enforces Rule 2 and Rule 7 of `00_MASTER_PROMPT.md`.
- **Consequences and trade-offs:** Requires maintaining adapter implementations for multiple SDKs.
- **Security/privacy impact:** PII redaction layer filters all prompts before dispatching to external APIs.
- **Cost/quota impact:** Operates within user's existing free-tier API quotas and credits.
- **Revisit when:** A single provider offers superior unified Odia multilingual voice and reasoning at zero cost.

---

## ADR-005: Dual-Path Document Ingestion & Odia OCR Strategy

- **Status:** Accepted
- **Date:** 2026-10-24
- **Context:** Official Odisha MSME policy notifications are published both as clean digital vector PDFs and scanned image PDFs with complex layouts and Odia script.
- **Options considered:**
  1. *Cloud Vision APIs* (Google Cloud Vision / AWS Textract - paid).
  2. *Universal LLM Multimodal Ingestion* (expensive in tokens and prone to hallucinating numbers).
  3. *Local Dual-Path Ingestion*: PyMuPDF for digital text + Tesseract OCR 5.5.3 with `ori` (Odia) model for scanned pages, backed by human verification.
- **Decision:** Implement **Local Dual-Path Ingestion** using `pymupdf` and local `tesseract` with `-l ori+eng` / `-l hin+eng`.
- **Reasoning/evidence:** The developer host system already has Tesseract 5.5.3 installed with 163 language packs, specifically including `ori` (Oriya) and script models. This avoids external API costs (₹0 budget compliant) and operates entirely offline.
- **Consequences and trade-offs:** Complex multi-column scanned tables may require human review in the admin console before publication.
- **Security/privacy impact:** Source government documents are processed locally on the server without leaking to third-party services.
- **Cost/quota impact:** ₹0.00.
- **Revisit when:** Document volume exceeds 10,000 pages per month or complex tabular layout requires advanced vision models.

---

## ADR-006: User-Managed Application Tracking & Zero-Mock Government Sync

- **Status:** Accepted
- **Date:** 2026-10-24
- **Context:** Entrepreneurs require a ledger to monitor the lifecycle of their government scheme applications. However, official department portals (`msme.odisha.gov.in`, Single Window) do not currently provide public third-party submission APIs or open webhook integrations.
- **Options considered:**
  1. *Simulated Two-Way Sync*: Fake automated status updates via mock timers or synthetic webhook triggers.
  2. *Automated Headless Web Scraping*: Headless browser automation attempting to log into official government portals with entrepreneur credentials.
  3. *Explicitly User-Managed Ledger*: Clean, honest application tracking where the entrepreneur enters their filing date, official acknowledgement/token reference, notes, and records status transitions.
- **Decision:** Implement an **Explicitly User-Managed Application Ledger** (`ApplicationTrackingModel` and `/api/v1/applications`).
- **Reasoning/evidence:** Strictly complies with Rule 2 (No Fake Functionality) and Rule 13 of Phase 3 prompt. Never deceives the citizen with fake automated government status polling or synthetic "Syncing with Directorate..." banners. Directly links the user to official government portals for filing.
- **Consequences and trade-offs:** Status updates depend on the user updating their application milestone.
- **Security/privacy impact:** Avoids storing citizen government portal passwords or executing brittle headless scrapers against state servers.
- **Cost/quota impact:** ₹0.00.
- **Revisit when:** Government of Odisha publishes official OAuth2 citizen APIs or Open MSME webhooks.

---

## ADR-007: Cryptographic Hashing and Token-Based Tenant Isolation

- **Status:** Accepted
- **Date:** 2026-10-24
- **Context:** Enterprise financial information, turnover metrics, and application notes must be securely stored and isolated per user with robust authentication and role-based permissions.
- **Options considered:**
  1. *Third-party SaaS Auth* (Auth0, Clerk, Firebase Auth) - Introduces external dependencies, quota limits, and potential cost.
  2. *Local PBKDF2-HMAC-SHA256 with JWT (HS256)*.
- **Decision:** Implement **Local PBKDF2-HMAC-SHA256 with 100,000 iterations and 16-byte random salt**, paired with standard signed **HS256 JSON Web Tokens (JWT)**.
- **Reasoning/evidence:** Self-contained, zero-cost, runs on standard Python standard library (`hashlib`, `hmac`), and provides row-level tenant isolation using `sub` user ID claims. Enforces RBAC permissions (`entrepreneur`, `scheme_reviewer`, `platform_admin`).
- **Consequences and trade-offs:** Requires standard secret key rotation policy in production environments.
- **Security/privacy impact:** Strong resistance against rainbow table and timing attacks with `hmac.compare_digest`. Passwords are never stored in plaintext.
- **Cost/quota impact:** ₹0.00 compute/licensing cost.
- **Revisit when:** Single Sign-On (SSO) with Aadhaar e-Pramaan / MeriPehchan is officially mandated.

