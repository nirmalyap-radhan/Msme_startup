# Environment Configuration Inventory

This file documents variable names and purpose only. **Never put actual secret values here.** Use a local ignored `.env` file for development and the hosting provider's secret manager for deployment.

The coding agent must inspect the repository and provider docs before choosing exact variable names. These are candidate names, not a claim that the app already uses them.

## Application
- `APP_ENV` — development/staging/production.
- `APP_SECRET_KEY` — application signing/encryption secret; generate securely.
- `APP_BASE_URL` — canonical app URL.
- `API_BASE_URL` — frontend-visible backend URL where applicable.
- `CORS_ORIGINS` — explicit allowed origins.

## Database and storage
- `DATABASE_URL` — PostgreSQL connection string.
- `DATABASE_POOL_SIZE` — connection pool limit.
- `DOCUMENT_STORAGE_BUCKET` — private object storage bucket, if used.
- `DOCUMENT_STORAGE_ENDPOINT` — endpoint if supported by selected storage provider.

## AI providers & Gateway Inventory

| Variable Name | Status in `.env` | Verified Liveness | Verified Active Model / Endpoint | Notes & Quota Observations |
|---|---|---|---|---|
| `GROQ_API_KEY` | Configured | **Active / Verified** | `qwen/qwen3.8-27b` (fallback: `allam-2-7b`) | Primary low-latency text reasoning provider (~1.1s response time). Active free quota. |
| `SARVAM_API_KEY` | Configured | **Active / Verified** | `bulbul:v3` (speaker: `ritu`), `api.sarvam.ai/translate` | Specialized Indian language provider for Odia/Hindi translation and Odia speech synthesis. |
| `GEMINI_API_KEY` | Configured | Rate Limited / Quota Exceeded | `gemini-flash-latest`, `gemini-pro-latest` | Returns HTTP 429 (`You exceeded your current quota`). Provider adapter catches and reports status cleanly. |
| `MISTRAL_API_KEY` | Configured | Rate Limited / Quota Exceeded | `mistral-small-latest` | Returns HTTP 429 (`Rate limit exceeded`). Adapter reports rate-limited status. |
| `NVIDIA_API_KEY` | Configured | Endpoint Deprecated / Timeout | `deepseek-ai/deepseek-v4.1-flash` | Older models retired with HTTP 410; gateway connection times out. |
| `AI_PRIMARY_PROVIDER` | Optional | Defaults to `groq` | `groq` | Configures primary chat completion dispatch. |
| `AI_REQUEST_TIMEOUT_SECONDS`| Optional | Defaults to `15.0` | — | Bounded timeout enforcing prompt defense and responsiveness. |

## Retrieval and ingestion
- `EMBEDDING_MODEL` — exact local/API embedding model.
- `VECTOR_DIMENSIONS` — must match selected model.
- `SCHEME_SOURCE_ALLOWLIST` — approved source hosts/URLs, if implemented.
- `INGESTION_USER_AGENT` — truthful user-agent/contact where required by source policy.
- `OCR_LANGUAGE_DATA` — configured installed OCR languages.
- `ADMIN_BOOTSTRAP_EMAIL` — only if a safe bootstrap process requires it; no default password.

## Observability
- `SENTRY_DSN` — optional error monitoring.
- `LOG_LEVEL` — configured log level.
- `OTEL_EXPORTER_OTLP_ENDPOINT` — optional telemetry endpoint.

## Rules
- `.env` and secret files must be in `.gitignore`.
- `.env.example` contains empty values or obvious placeholders only.
- Never print values during diagnostics; report only configured/missing/validation status.
- Never expose server-only variables through frontend build prefixes.
- Rotate any key that has been committed or exposed.
- Do not enable paid billing without explicit authorization.
