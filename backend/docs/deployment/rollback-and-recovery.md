# Rollback and Disaster Recovery Procedures (Phase 6)

## 1. Rollback Architecture

In the event of an operational failure, corrupted deployment, or breaking migration, Udyog Sathi supports two distinct rollback procedures:
1. **Application Code Rollback:** Reverting the running container or application commit to the previous known good release.
2. **Database State Recovery:** Restoring the persistent state from a verified, atomic backup.

```
                    [ Incident Detected ]
                              │
               ┌──────────────┴──────────────┐
               ▼                             ▼
     [ Application Fault ]         [ Database Corruption ]
               │                             │
    Revert Container Image /       Verify Backup Checksum
    Git Commit to Previous Tag     via scripts/backup_restore.py
               │                             │
    Restart Uvicorn Service        Execute Atomic Restore
               │                             │
               └──────────────┬──────────────┘
                              ▼
                Run Post-Recovery Verification
               (/health/ready, verify_source_records.py)
```

---

## 2. Application Code Rollback

### Container Deployment Rollback (Docker / Render / Railway)
1. **Identify Previous Image Tag:**
   ```bash
   docker images | grep udyog-sathi
   ```
2. **Deploy Previous Stable Tag:**
   - In the PaaS dashboard (Render/Railway), select **Deployments** -> choose previous successful deployment -> click **Rollback to this revision**.
   - If using local Docker:
     ```bash
     docker stop udyog_sathi_app
     docker rm udyog_sathi_app
     docker run -d -p 8000:8000 --name udyog_sathi_app \
       -v $(pwd)/data:/app/data \
       udyog-sathi:<previous-stable-tag>
     ```

### Git Commit Rollback (Direct Host)
```bash
cd /home/udyogsathi/app
git log --oneline -n 5
git checkout <previous-stable-commit-hash>
source .venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart udyogsathi
```

---

## 3. Database Backup & Disaster Recovery

Udyog Sathi includes an automated backup and verification utility: [`scripts/backup_restore.py`](file:///Users/nirmalyapradhan/Downloads/udyog_sathi_dev_prompts/scripts/backup_restore.py).

### 3.1 Creating Scheduled Atomic Backups
To create an atomic, write-consistent backup:
```bash
python3.11 scripts/backup_restore.py backup
```
- Uses SQLite online backup API to ensure write consistency during active queries.
- Creates `data/backups/udyog_sathi_backup_<YYYYMMDD_HHMMSS>.db`.
- Automatically computes SHA-256 hash and writes metadata JSON `data/backups/udyog_sathi_backup_<timestamp>.json`.
- Excluded from git via `.gitignore`.

### 3.2 Verifying Backup File Integrity
Before restoring any backup, verify its cryptographic checksum and SQLite structural integrity:
```bash
python3.11 scripts/backup_restore.py verify data/backups/udyog_sathi_backup_20261025_023450.db
```
- Compares SHA-256 against recorded metadata.
- Executes `PRAGMA integrity_check;`.
- Returns `✓ Backup integrity verified (integrity: ok)`.

### 3.3 Executing Safe Database Restoration
To restore the database:
```bash
# 1. Stop web service to prevent incoming writes
sudo systemctl stop udyogsathi # or docker stop udyog_sathi_app

# 2. Execute verified restoration
python3.11 scripts/backup_restore.py restore data/backups/udyog_sathi_backup_20261025_023450.db

# 3. Start web service
sudo systemctl start udyogsathi # or docker start udyog_sathi_app
```

> [!NOTE]
> The restoration procedure automatically creates a safety snapshot of the active database before overwriting (`data/udyog_sathi.db.pre_restore`), preventing accidental data loss if the restore operation is aborted.

---

## 4. Post-Rollback Verification

Immediately following a rollback or restore, execute the following verification commands:

1. **Verify Database Consistency:**
   ```bash
   python3.11 scripts/verify_source_records.py
   ```
   *Expected:* 2 published schemes, verified SHA-256 hashes, 27 extracted passages.

2. **Verify Zero-Mock Compliance:**
   ```bash
   python3.11 scripts/check_no_production_fixtures.py
   ```
   *Expected:* 100% compliant with Rule 2.

3. **Verify Health Endpoint:**
   ```bash
   curl -s http://localhost:8000/health/ready
   ```
   *Expected:* `{"status": "ready", "database": "healthy", "published_schemes_count": 2}`.

4. **Execute Core Pytest Suite:**
   ```bash
   python3.11 -m pytest tests/unit/test_api_endpoints.py tests/unit/test_security_and_isolation.py
   ```
   *Expected:* All tests passing.
