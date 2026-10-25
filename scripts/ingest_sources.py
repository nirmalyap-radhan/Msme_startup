#!/usr/bin/env python3
"""
CLI Script for Ingesting Official Government Scheme Documents into Udyog Sathi.
Enforces domain allowlists, SHA-256 provenance tracking, PyMuPDF extraction,
Tesseract OCR fallback, and structured field normalization.
"""

import argparse
import os
import sys
from datetime import datetime

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from services.scheme_ingestion.config import ingestion_config
from services.scheme_ingestion.extractor import DocumentExtractor
from services.scheme_ingestion.fetcher import DocumentFetcher, DocumentFetchError
from services.scheme_ingestion.models import IngestionJobRecord, IngestionJobStatus
from services.scheme_ingestion.normalizer import SchemeNormalizer
from services.scheme_ingestion.storage import SchemeStorageRepository


def run_ingestion(url: str = None, local_file: str = None, title: str = None, dry_run: bool = False):
    print("=" * 80)
    print("UDYOG SATHI — OFFICIAL SCHEME DATA INGESTION PIPELINE")
    print("=" * 80)

    fetcher = DocumentFetcher()
    extractor = DocumentExtractor()
    normalizer = SchemeNormalizer()
    repository = SchemeStorageRepository() if not dry_run else None

    target_source = url or local_file
    print(f"Target Source: {target_source}")
    print(f"Dry Run Mode: {dry_run}")
    print(f"OCR Languages Configured: {ingestion_config.tesseract_lang_string}")

    job = IngestionJobRecord(source_url=target_source or "local_import")
    if repository:
        repository.save_ingestion_job(job)

    try:
        # Step 1: Retrieval & Checksum
        print("\n[Step 1/4] Retrieving document and computing SHA-256 hash...")
        if url:
            doc_schema = fetcher.fetch_url(url=url, title=title)
        elif local_file:
            doc_schema = fetcher.import_local_file(
                local_path=local_file,
                official_url=url or f"https://msme.odisha.gov.in/sites/default/files/{os.path.basename(local_file)}",
                title=title or os.path.basename(local_file),
            )
        else:
            raise ValueError("Either --url or --local-file must be provided.")

        print(f"✓ Retrieved: {doc_schema.title}")
        print(f"  Source URL: {doc_schema.source_url}")
        print(f"  Local Vault: {doc_schema.local_path}")
        print(f"  File Size: {doc_schema.file_size_bytes:,} bytes")
        print(f"  SHA-256: {doc_schema.sha256_hash}")

        # Step 2: Extraction & OCR
        print("\n[Step 2/4] Parsing PDF pages and detecting scanned content...")
        doc_schema, passages = extractor.extract_document(doc_schema)
        print(f"✓ Total Pages Processed: {doc_schema.page_count}")
        print(f"  Scanned Document Detected: {doc_schema.is_scanned}")
        print(f"  Tesseract OCR Applied: {doc_schema.ocr_applied}")

        ocr_passages = [p for p in passages if p.is_ocr]
        print(f"  Pages requiring OCR: {len(ocr_passages)} / {len(passages)}")

        # Step 3: Candidate Field Normalization
        print("\n[Step 3/4] Normalizing candidate eligibility conditions, benefits, and checklists...")
        candidate_scheme = normalizer.normalize(doc_schema, passages)

        print(f"✓ Official Scheme Name: {candidate_scheme.official_name}")
        print(f"  Department: {candidate_scheme.department}")
        print(f"  Implementing Agency: {candidate_scheme.implementing_agency}")
        print(f"  Effective Date: {candidate_scheme.effective_date or 'Not specified'}")
        print(f"  Expiry Date: {candidate_scheme.expiry_date or 'Not specified'}")
        print(f"  Candidate Eligibility Conditions: {len(candidate_scheme.candidate_eligibility)}")
        for idx, cond in enumerate(candidate_scheme.candidate_eligibility[:5], 1):
            print(f"    {idx}. [{cond.attribute_name} {cond.operator} {cond.value}] (Clause: {cond.source_clause}, Page {cond.source_page})")

        print(f"  Candidate Benefits / Subsidies: {len(candidate_scheme.candidate_benefits)}")
        for idx, ben in enumerate(candidate_scheme.candidate_benefits[:5], 1):
            limit_str = f"Max ₹{ben.max_limit_inr:,.0f}" if ben.max_limit_inr else "Formula-based"
            pct_str = f"{ben.subsidy_percentage}%" if ben.subsidy_percentage else "N/A"
            print(f"    {idx}. {ben.benefit_type}: {pct_str} ({limit_str}) - Clause: {ben.source_clause}, Page {ben.source_page}")

        print(f"  Document Checklist: {len(candidate_scheme.required_documents)} proofs identified")
        for idx, d in enumerate(candidate_scheme.required_documents[:5], 1):
            print(f"    {idx}. {d}")

        # Step 4: Storage & Review Queue
        if dry_run:
            print("\n[Step 4/4] DRY RUN MODE: Skipping database persistence.")
        else:
            print("\n[Step 4/4] Persisting document, passages, and candidate scheme to repository...")
            repository.save_source_document(doc_schema)
            repository.save_passages(passages)
            saved_scheme = repository.save_candidate_scheme(candidate_scheme)

            job.status = IngestionJobStatus.COMPLETED
            job.completed_at = datetime.utcnow()
            job.document_id = doc_schema.document_id
            job.scheme_id = saved_scheme.id
            job.extraction_stats = {
                "pages": doc_schema.page_count,
                "conditions": len(candidate_scheme.candidate_eligibility),
                "benefits": len(candidate_scheme.candidate_benefits),
                "documents": len(candidate_scheme.required_documents),
                "ocr_applied": doc_schema.ocr_applied,
            }
            repository.save_ingestion_job(job)

            print(f"✓ Successfully stored in repository.")
            print(f"  Scheme ID: {saved_scheme.id}")
            print(f"  Status: {saved_scheme.status} (Awaiting Reviewer Sign-Off)")
            print(f"\nNext Action: Run 'python3 scripts/verify_source_records.py --inspect {saved_scheme.id}' to inspect and publish.")

        print("=" * 80)
        return candidate_scheme

    except Exception as e:
        print(f"\n❌ INGESTION FAILED: {str(e)}")
        if repository:
            job.status = IngestionJobStatus.FAILED
            job.completed_at = datetime.utcnow()
            job.error_message = str(e)
            repository.save_ingestion_job(job)
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest official government scheme document into Udyog Sathi.")
    parser.add_argument("--url", type=str, help="Official approved government source URL.")
    parser.add_argument("--local-file", type=str, help="Path to locally imported official PDF file.")
    parser.add_argument("--title", type=str, help="Human-readable scheme title (optional).")
    parser.add_argument("--dry-run", action="store_true", help="Perform extraction without persisting to database.")

    args = parser.parse_args()
    if not args.url and not args.local_file:
        parser.print_help()
        sys.exit(1)

    run_ingestion(url=args.url, local_file=args.local_file, title=args.title, dry_run=args.dry_run)
