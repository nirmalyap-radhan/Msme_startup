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

## AI providers
- `GROQ_API_KEY` — Groq secret.
- `GROQ_MODEL` — model verified as available to the account.
- `SARVAM_API_KEY` — Sarvam secret.
- `SARVAM_MODEL_OR_PIPELINE` — only if required by the selected endpoint.
- `GEMINI_API_KEY` — Google Gemini secret.
- `GEMINI_MODEL` — model verified as available to the account.
- `NVIDIA_API_KEY` — NVIDIA inference secret, if the selected product uses one.
- `NVIDIA_BASE_URL` — only use an official endpoint verified for the account/product.
- `MISTRAL_API_KEY` — Mistral secret.
- `MISTRAL_MODEL` — model verified as available to the account.
- `AI_PRIMARY_PROVIDER` — selected provider.
- `AI_REQUEST_TIMEOUT_SECONDS` — bounded request timeout.
- `AI_MAX_RETRIES` — bounded retries.
- `AI_DAILY_BUDGET` — optional internal usage guard; must not be mistaken for provider billing controls.

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
