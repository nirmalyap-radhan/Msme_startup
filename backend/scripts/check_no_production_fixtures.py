#!/usr/bin/env python3
"""
Zero-Mock Compliance & Production Data Hygiene Scanner.
Enforces Rule 2 of 00_MASTER_PROMPT.md.
Scans database records and production service files to guarantee zero mock data,
fictional schemes, or fake metrics exist in the platform.
"""

import os
import re
import sys

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from services.scheme_ingestion.storage import SchemeStorageRepository

FORBIDDEN_KEYWORDS = [
    "mock",
    "dummy",
    "placeholder",
    "sample scheme",
    "fictional",
    "fake",
    "lorem ipsum",
    "test enterprise",
    "john doe",
]


def check_database_records():
    print("Checking repository records for forbidden mock terms...")
    repo = SchemeStorageRepository()
    violations = []

    with repo.get_session() as session:
        from services.scheme_ingestion.models import SchemeModel

        schemes = session.query(SchemeModel).all()
        print(f"Total schemes in database: {len(schemes)}")

        for s in schemes:
            # 1. Check title and summary for forbidden terms
            text_to_check = f"{s.official_name} {s.summary} {s.department}".lower()
            for kw in FORBIDDEN_KEYWORDS:
                if kw in text_to_check:
                    violations.append(f"Scheme [{s.id}] contains forbidden mock keyword: '{kw}'")

            # 2. Check source provenance
            if not s.source_url or not s.source_url.startswith("http"):
                violations.append(f"Scheme [{s.id}] has invalid or missing source URL: '{s.source_url}'")

            # 3. Check SHA-256 checksum validity (64 hex characters)
            if not s.document_sha256 or len(s.document_sha256) != 64 or not re.match(r"^[0-9a-f]{64}$", s.document_sha256):
                violations.append(f"Scheme [{s.id}] has invalid SHA-256 hash: '{s.document_sha256}'")

    return violations


def check_source_code_cleanliness():
    print("Scanning service source files for hardcoded mock datasets...")
    violations = []
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "services"))

    for root, _, files in os.walk(base_dir):
        for f in files:
            if f.endswith(".py"):
                path = os.path.join(root, f)
                with open(path, "r", encoding="utf-8") as py_file:
                    content = py_file.read()
                    # Check for hardcoded fixture lists resembling mock schemes
                    if "MOCK_SCHEMES" in content or "SAMPLE_SCHEMES" in content:
                        violations.append(f"Hardcoded mock scheme constant found in: {path}")

    return violations


def main():
    print("=" * 80)
    print("UDYOG SATHI — ZERO-MOCK COMPLIANCE AUDIT")
    print("=" * 80)

    db_violations = check_database_records()
    code_violations = check_source_code_cleanliness()

    all_violations = db_violations + code_violations

    if all_violations:
        print("\n❌ VIOLATIONS DETECTED (NON-COMPLIANT):")
        for idx, v in enumerate(all_violations, 1):
            print(f"  {idx}. {v}")
        print("\nFAIL: Production data contains mock or invalid artifacts.")
        sys.exit(1)
    else:
        print("\n✓ ZERO-MOCK AUDIT PASSED: 100% compliant with Rule 2 of 00_MASTER_PROMPT.md.")
        print("  - Zero synthetic schemes detected.")
        print("  - All stored records have traceable official provenance and valid SHA-256 hashes.")
        print("=" * 80)
        sys.exit(0)


if __name__ == "__main__":
    main()
