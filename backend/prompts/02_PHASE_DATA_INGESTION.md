# Phase 2 — Official Scheme Data Ingestion and Verification

## Instructions

Read `00_MASTER_PROMPT.md` and the Phase 1 audit outputs before coding. Preserve existing project conventions.

## Objective

Create a repeatable pipeline that retrieves real government scheme documents, extracts structured information, preserves provenance and supports human verification. No fictional production records.

## Source discovery

Start by checking relevant official sources, including:
- https://msme.odisha.gov.in/en/schemes/msme-schemes
- https://msme.odisha.gov.in/en/notification/policies
- https://odishamsme.nic.in/
- https://www.msme.gov.in/
- https://www.myscheme.gov.in/

Verify current accessibility, responsible authority, terms/access restrictions and source relevance. These are discovery points, not a pre-approved list of current schemes. Do not invent APIs or bypass access controls. If automated retrieval is not allowed or reliable, support a documented manual download/import workflow.

## Required implementation

1. Define database models and migrations for schemes, source documents, versions, source references, review events and ingestion jobs.
2. Build a source register with source URL, authority, permitted retrieval method, last checked date, status and notes.
3. Implement retrieval for approved URLs or administrator-uploaded official documents.
4. Preserve originals or a secure reference to them, retrieval timestamp and SHA-256 hash where practical.
5. Extract text from digital PDFs; detect low/no text and route scanned documents through OCR when configured.
6. Preserve page number, section headings and table context as far as technically possible.
7. Normalize text without destroying meaningful structure, values, units or footnotes.
8. Extract candidate fields into a validated schema. LLM use is optional and must be quota-aware.
9. Validate URLs, date formats, numeric fields, required provenance and duplicate/version conditions.
10. Require a reviewer to verify material eligibility conditions, financial benefits, dates and application URLs before publication.
11. Implement versioning and statuses: discovered, extracted, pending_review, verified, published, superseded, expired, withdrawn.
12. Ensure unverified, failed or partial imports cannot appear in public search.
13. Add safe retries, idempotency, error records and a dry-run/preview mode that does not publish.
14. Add an administrator workflow to inspect extracted content beside its source evidence and approve/reject it.
15. Provide a report of what was actually fetched and processed.

## Suggested tools

Use existing dependencies where possible. If needed, evaluate PyMuPDF for PDF extraction and Tesseract for OCR. Avoid adding an LLM dependency just to extract text that a local parser can handle.

## No-mock rule

Do not insert demo schemes or fabricate a successful ingestion. If no source can be retrieved, show the actual failure and provide an administrator import path. Never mark a scheme verified automatically merely because extraction succeeded.

## Tests

Test PDF text extraction, scanned-document detection, invalid URLs, duplicate files, changed hashes, missing metadata, reviewer permissions, version supersession and publication filtering. Test fixtures must remain isolated from production.

## Deliverables

- Migrations/models and ingestion services.
- Source register in `DATA_SOURCE_REGISTER.md`.
- Data schema documentation under `docs/data/`.
- Administrator verification workflow.
- Tests and exact run instructions.
- Update `STATUS.md` with actual imported/verified source counts.

## Exit criteria

At least one real official source has been successfully retrieved or imported with traceable evidence and passed the implemented review workflow. If external access blocks retrieval, document the blocker and prove the local import path works; do not claim the data milestone is complete until real source ingestion has been demonstrated.
