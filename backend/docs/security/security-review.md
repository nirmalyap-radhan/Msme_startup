# Comprehensive Security & Threat Review (Phase 6)

## 1. Security Architecture Overview

Udyog Sathi is designed to provide public scheme advisory while safeguarding enterprise identity and business financials. The platform implements defense-in-depth across the application lifecycle:

```
[ Incoming Request ]
        │
        ▼
[ Security Headers Middleware ] ──► Nosniff, Deny Framing, XSS Block, Process-Time
        │
        ▼
[ CORS Origin Gate ] ─────────────► Origin Allowlist Enforcement
        │
        ▼
[ Authentication & RBAC ] ────────► PBKDF2 Password Verifier, Tamper-Resistant JWTs
        │
        ▼
[ Input Validation (Pydantic) ] ──► Type enforcement, Enum constraints (HTTP 422)
        │
        ▼
[ Business Domain Logic ]
        ├── Data Isolation: Row-level tenant filtering by User ID
        ├── Deterministic Engine: Sandboxed math, no dynamic code execution
        └── Grounded RAG: Keyword coverage gate, prompt injection sanitization
```

---

## 2. Threat Analysis & Audit Findings

### 2.1 Secret Exposure & Repository Hygiene
- **Finding:** Git status and history inspected. `.env` file containing live API keys is excluded via `.gitignore` (`.env`, `.env.*`, `!.env.example`).
- **Template Hygiene:** `.env.example` contains only placeholder instructions and zero active credentials.
- **Risk Level:** **LOW / VERIFIED CLEAN**.

### 2.2 Authentication & Session Security
- **Password Storage:** Uses PBKDF2-HMAC-SHA256 with 100,000 iterations and unique 16-byte cryptographically secure random salts. Raw passwords are never persisted.
- **Tokens:** Stateless JSON Web Tokens (JWT) signed with HMAC-SHA256. Expired or tampered tokens are rejected immediately.
- **Session Duration:** Access tokens expire after 60 minutes (`ACCESS_TOKEN_EXPIRE_MINUTES = 60`).
- **Risk Level:** **LOW / VERIFIED CLEAN**.

### 2.3 Role-Based Access Control (RBAC) & Privilege Separation
- **Enforcement:** Enforced via FastAPI dependency injection (`require_role(["scheme_reviewer", "platform_admin"])`).
- **Reviewer Endpoints:** `/api/v1/admin/schemes/pending`, `/api/v1/admin/schemes/{id}/dossier`, `/api/v1/admin/schemes/{id}/verify`.
- **Audit Verification:** Regular entrepreneur accounts and unauthenticated users receive HTTP 403 Forbidden and HTTP 401 Unauthorized respectively, verified in `test_auth_rbac.py` and `test_api_endpoints.py`.
- **Risk Level:** **LOW / VERIFIED CLEAN**.

### 2.4 Database Access & Row-Level Data Isolation
- **Tenant Isolation:** The application tracking router (`apps/api/routers/applications.py`) filters all queries by `user_id == current_user.id`.
- **Cross-User Tampering:** Verified via `test_cross_user_application_isolation`: User B attempting to view or modify User A's application receives HTTP 404 (Not Found / Access Denied).
- **Risk Level:** **LOW / VERIFIED CLEAN**.

### 2.5 Security Headers & CORS
- **Middleware:** Implemented in `apps/api/main.py`:
  - `X-Content-Type-Options: nosniff` (prevents MIME type sniffing)
  - `X-Frame-Options: DENY` (prevents clickjacking)
  - `X-XSS-Protection: 1; mode=block` (legacy browser XSS filter)
  - `X-Process-Time` (transparent latency reporting)
- **CORS Policy:** Restricts origins to configured domain list (`cors_origins`).
- **Risk Level:** **LOW / VERIFIED CLEAN**.

### 2.6 Input Validation & Upload Safety
- **Validation Engine:** Strict Pydantic models validate all request payloads.
- **Status Constraints:** `ApplicationStatus` Literal restricts status changes to: `draft`, `submitted`, `submitted_to_department`, `under_scrutiny`, `query_raised`, `queried`, `approved`, `rejected`, `disbursed`.
- **File Upload Safety:** Ingestion pipelines (`services/scheme_ingestion/fetcher.py`) enforce domain allowlists (`msme.odisha.gov.in`, `odishamsme.nic.in`) and strictly reject arbitrary URL inputs.
- **Risk Level:** **LOW / VERIFIED CLEAN**.

### 2.7 Prompt Injection & Untrusted Content Defense
- **Retrieval Gating:** Queries pass through a stopword-aware keyword coverage gate ($\ge 35\%$ content token overlap required) before executing generation.
- **Injection Sanitization:** The anti-hallucination fallback suppresses untrusted user queries from echoing verbatim into outputs.
- **Evidence Provenance:** System prompts instruct the LLM to refuse queries when context is missing, outputting structured citations with verified SHA-256 hashes.
- **Risk Level:** **LOW / VERIFIED CLEAN**.

### 2.8 PII Handling & Data Retention
- **Operational Data:** Collects minimal business information (enterprise class, sector, turnover, loan values).
- **Consent Notice:** The interface prominently alerts users that tracking is user-managed and advisory.
- **Sanitization:** Log outputs do not print passwords or Bearer tokens.

### 2.9 Error Messages & Stack Trace Suppression
- **Error Responses:** FastAPI standard error handlers return structured JSON (`{"detail": "..."}`) without exposing internal file paths or Python traceback frames to end users.
- **404/422/403 Handling:** Clean status codes and messages returned consistently.

### 2.10 Backup Security & Structural Integrity
- **Utility:** `scripts/backup_restore.py` uses SQLite online backup API to ensure write consistency during active traffic.
- **Checksum Verification:** Every backup generates a companion JSON metadata record containing the SHA-256 hash.
- **Structural Integrity:** Restores require passing `PRAGMA integrity_check;` and automatically capture a pre-restore safety snapshot (`*.pre_restore`).

---

## 3. Security Recommendations for Future Scale (Phase 7+)
1. **Production Rate Limiting:** Implement token bucket rate limiting (e.g. `slowapi` or Redis-backed rate limiter) on `/api/v1/rag/ask` and `/api/v1/profiles/login` to prevent distributed denial-of-service or credit depletion.
2. **PostgreSQL Migration:** Transition from SQLite to managed PostgreSQL with Row Level Security (RLS) policies when scaling beyond single-container instances.
3. **Automated Secret Scanning:** Enable GitHub Secret Scanning / GitGuardian in CI pipelines to guard against accidental commits.
