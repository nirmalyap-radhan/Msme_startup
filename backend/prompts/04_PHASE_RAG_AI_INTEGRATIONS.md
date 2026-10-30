# Phase 4 — RAG, Citations and AI Provider Integrations

## Instructions

Read `00_MASTER_PROMPT.md` and the outputs from Phases 1–3. Inspect provider documentation for current endpoints, supported models, pricing and account limits before implementation.

## Objectives

Implement grounded answers using the actual reviewed scheme corpus and robust provider adapters for available user-owned API credentials.

## Provider credentials

The owner reports credentials for Groq, Sarvam AI, NVIDIA, Gemini and Mistral. Check whether expected environment variables are configured without printing values. Never assume a key is valid, funded, or entitled to a model. Never request the user to paste secrets into chat or source files.

Create a server-side provider abstraction suited to the actual SDKs. Configure only providers that can be validated. Choose a primary text model based on tests, quotas, latency, language needs and cost. Add secondary fallback only when it is safe and tested. Use Sarvam for language/speech features only when the exact selected API supports the needed language and the account has access.

## RAG pipeline

1. Retrieve only published, verified and applicable documents.
2. Preserve chunk metadata: scheme/document IDs, source URL, page, section, version and effective status.
3. Implement lexical search first or alongside embeddings based on existing infrastructure.
4. Use a local multilingual embedding model if practical; evaluate retrieval for English, Hindi, Odia and code-mixed queries before relying on it.
5. Use PostgreSQL full-text search and pgvector if supported and beneficial. Do not add a separate vector database without evidence.
6. Apply filters for jurisdiction, publication status, validity and document version.
7. Deduplicate and rank retrieved passages; avoid obsolete versions.
8. Pass retrieved passages and their references to the model with instructions not to invent missing facts.
9. Return citations that point to real source documents and page/section references where available.
10. If evidence is insufficient, return an explicit uncertainty/unavailable answer.
11. Treat retrieved documents and user uploads as untrusted input; mitigate prompt injection and prevent document text from overriding system policy.
12. Log provider status, retrieval IDs, latency and error categories while redacting personal data and secrets.

## Provider reliability

Implement timeouts, bounded retries, rate-limit responses, usage limits and a clear service-unavailable state. Never fall back to a hardcoded response. Avoid cascading retries across all providers.

## Evaluation

Create a small evaluation set from verified source documents and manually checked questions. Measure retrieval relevance, citation correctness, unsupported claims, answerability handling, Odia retrieval/response quality, latency and cost/quota consumption. Report actual results, not invented scores.

## Deliverables

- Provider adapter(s) that were actually configured.
- Retrieval and citation pipeline.
- RAG evaluation script/tests.
- Environment variable inventory in `ENVIRONMENT.md`.
- Provider setup instructions and quota notes.
- Update `STATUS.md`.

## Exit criteria

A question about a real published scheme retrieves traceable evidence and produces a cited answer through a configured provider. Missing credentials, missing evidence and provider failures return honest errors. If a provider cannot be tested, mark it unverified rather than integrated.
