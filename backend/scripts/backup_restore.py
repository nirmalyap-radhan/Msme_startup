"""
Udyog Sathi Database Backup & Recovery Utility.
Provides atomic backup creation, SHA-256 checksum verification,
PRAGMA integrity checks, and verified recovery procedures for SQLite/PostgreSQL.
"""

import argparse
import hashlib
import json
import os
import shutil
import sqlite3
import sys
from datetime import datetime
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "udyog_sathi.db"
BACKUP_DIR = DATA_DIR / "backups"


def calculate_sha256(file_path: Path) -> str:
    """Computes SHA-256 hash of a file."""
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def create_backup(target_dir: Path = BACKUP_DIR) -> Path:
    """Creates an atomic backup of the database using SQLite online backup API."""
    if not DB_PATH.exists():
        raise FileNotFoundError(f"Source database not found at {DB_PATH}")

    target_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    backup_file = target_dir / f"udyog_sathi_backup_{timestamp}.db"
    meta_file = target_dir / f"udyog_sathi_backup_{timestamp}.json"

    # Use SQLite online backup API to ensure write consistency
    src_conn = sqlite3.connect(str(DB_PATH))
    dst_conn = sqlite3.connect(str(backup_file))
    with dst_conn:
        src_conn.backup(dst_conn, pages=100)
    dst_conn.close()
    src_conn.close()

    # Calculate checksum
    sha256 = calculate_sha256(backup_file)

    # Count records
    check_conn = sqlite3.connect(str(backup_file))
    cur = check_conn.cursor()
    cur.execute("SELECT count(*) FROM schemes WHERE status = 'published'")
    schemes_count = cur.fetchone()[0]
    check_conn.close()

    metadata = {
        "backup_file": backup_file.name,
        "created_at": datetime.utcnow().isoformat() + "Z",
        "sha256": sha256,
        "size_bytes": backup_file.stat().st_size,
        "verified_published_schemes": schemes_count,
    }

    with open(meta_file, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    print(f"✓ Backup created successfully: {backup_file.name}")
    print(f"  SHA-256: {sha256}")
    print(f"  Published Schemes: {schemes_count}")
    return backup_file


def verify_backup(backup_file: Path) -> bool:
    """Verifies SHA-256 checksum against metadata and checks SQLite structural integrity."""
    if not backup_file.exists():
        raise FileNotFoundError(f"Backup file not found at {backup_file}")

    meta_file = backup_file.with_suffix(".json")
    if meta_file.exists():
        with open(meta_file, "r", encoding="utf-8") as f:
            meta = json.load(f)
        expected_sha = meta.get("sha256")
        actual_sha = calculate_sha256(backup_file)
        if expected_sha and expected_sha != actual_sha:
            print(f"✗ Checksum mismatch! Expected {expected_sha}, got {actual_sha}", file=sys.stderr)
            return False

    # Check structural integrity
    conn = sqlite3.connect(str(backup_file))
    cur = conn.cursor()
    cur.execute("PRAGMA integrity_check;")
    status = cur.fetchone()[0]
    conn.close()

    if status != "ok":
        print(f"✗ SQLite PRAGMA integrity_check failed: {status}", file=sys.stderr)
        return False

    print(f"✓ Backup integrity verified: {backup_file.name} (integrity: {status})")
    return True


def restore_backup(backup_file: Path, target_db: Path = DB_PATH) -> bool:
    """Restores database from verified backup."""
    if not verify_backup(backup_file):
        raise ValueError("Cannot restore from corrupted backup.")

    # Create safety backup of current target if it exists
    if target_db.exists():
        safety_path = target_db.with_suffix(".db.pre_restore")
        shutil.copy2(target_db, safety_path)
        print(f"✓ Created safety snapshot of current DB: {safety_path.name}")

    shutil.copy2(backup_file, target_db)
    print(f"✓ Database restored successfully from {backup_file.name} to {target_db.name}")
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Udyog Sathi Database Backup & Recovery Utility")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("backup", help="Create new atomic backup")

    verify_p = subparsers.add_parser("verify", help="Verify backup integrity")
    verify_p.add_argument("file", help="Path to backup .db file")

    restore_p = subparsers.add_parser("restore", help="Restore database from backup")
    restore_p.add_argument("file", help="Path to backup .db file")

    args = parser.parse_args()

    if args.command == "backup":
        create_backup()
    elif args.command == "verify":
        verify_backup(Path(args.file))
    elif args.command == "restore":
        restore_backup(Path(args.file))
