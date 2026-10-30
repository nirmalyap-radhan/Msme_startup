# Production Deployment Runbook (Phase 6)

## 1. Target Infrastructure & Free-Tier Selection

Udyog Sathi is designed to run efficiently on modern container platforms or PaaS providers. For zero-budget or pilot hosting, the recommended deployment targets are:

### Recommended Target: Render / Railway / Fly.io (Container PaaS)
- **Container Runtime:** Docker (`Dockerfile` provided in repository).
- **Compute:** 512MB RAM, 0.5 vCPU (sufficient for Uvicorn + SQLite/FastAPI).
- **Persistent Volume:** Mounted at `/app/data` to persist `data/udyog_sathi.db` and backups.
- **TLS/HTTPS:** Automated Let's Encrypt certificates provided out-of-the-box.

### Free-Tier Operating Constraints & Restrictions
| Parameter | Free-Tier Policy / Limitation | Operational Mitigation |
|---|---|---|
| **Instance Inactivity / Sleep** | Render free tier spins down after 15 minutes of inactivity; initial cold start takes 30–50 seconds. | Use UptimeRobot or scheduled cron ping on `/health/live` to maintain warm state. |
| **Bandwidth & Quotas** | 100 GB egress/month (standard free tier). | Static assets (`/static/css`, `/static/js`) are lightweight vanilla files (<100KB total); gzip/brotli enabled. |
| **Database Expiry** | Managed PostgreSQL free instances often expire after 30–90 days on free tiers. | SQLite database on persistent volume has no expiry. If using managed Postgres, run automated export dumps. |
| **Commercial Use Restrictions** | Free tiers are limited to non-commercial evaluation / pilots. | State government deployment should be transitioned to NIC MeghRaj Cloud or state-owned AWS GovCloud. |

---

## 2. Environment Variables & Secret Configuration

Configure the following secrets in your deployment dashboard (e.g., Render Environment Variables, Railway Variables):

```bash
# Core Environment
APP_ENV=production
API_PREFIX=/api/v1
PORT=8000
CORS_ORIGINS=https://udyog-sathi.onrender.com,http://localhost:8000

# Authentication Secret (Generate using: openssl rand -hex 32)
APP_SECRET_KEY=replace_with_64_character_hex_string_in_dashboard

# AI Gateway Credentials (Server-side only)
AI_PRIMARY_PROVIDER=groq
GROQ_API_KEY=gsk_...
GROQ_MODEL=qwen/qwen3.8-27b

# Multilingual Voice & Translation (Sarvam AI)
SARVAM_API_KEY=...
SARVAM_MODEL_OR_PIPELINE=bulbul:v3

# Database Connection (Default is SQLite repository)
DATABASE_URL=sqlite:////app/data/udyog_sathi.db
```

> [!WARNING]
> Never hardcode secrets in repository files. Store them exclusively in the host's secret manager.

---

## 3. Step-by-Step Deployment Instructions

### Option A: Container Deployment via Docker (Recommended)

1. **Build Container Image:**
   ```bash
   docker build -t udyog-sathi:latest .
   ```

2. **Verify Container Health Locally:**
   ```bash
   docker run -d -p 8000:8000 --name udyog_sathi_test \
     -e APP_ENV=production \
     -e GROQ_API_KEY="$GROQ_API_KEY" \
     -e SARVAM_API_KEY="$SARVAM_API_KEY" \
     udyog-sathi:latest
   ```

3. **Check Liveness:**
   ```bash
   curl -f http://localhost:8000/health/live
   # Expect: {"status": "live", "app_name": "Udyog Sathi"}
   ```

4. **Deploy to Render / Cloud Run / Railway:**
   - Connect GitHub repository to Render/Railway.
   - Choose **Docker** environment.
   - Attach a persistent disk at path `/app/data` (size: 1 GB).
   - Enter environment variables in the host dashboard.
   - Trigger deployment.

---

### Option B: Direct Python / Systemd Service Deployment

1. **Install System Dependencies (Ubuntu / Debian):**
   ```bash
   sudo apt-get update && sudo apt-get install -y \
     python3.11 python3.11-venv \
     tesseract-ocr tesseract-ocr-ori tesseract-ocr-hin curl
   ```

2. **Create Application User & Virtualenv:**
   ```bash
   sudo useradd -m -s /bin/bash udyogsathi
   sudo -u udyogsathi -i
   git clone <repo-url> /home/udyogsathi/app
   cd /home/udyogsathi/app
   python3.11 -m venv .venv
   source .venv/bin/activate
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

3. **Run Database Migrations:**
   ```bash
   python3.11 -m alembic upgrade head
   ```

4. **Verify Seed Records:**
   ```bash
   python3.11 scripts/verify_source_records.py
   python3.11 scripts/check_no_production_fixtures.py
   ```

5. **Configure Systemd Service (`/etc/systemd/system/udyogsathi.service`):**
   ```ini
   [Unit]
   Description=Udyog Sathi FastAPI Application
   After=network.target

   [Service]
   User=udyogsathi
   Group=udyogsathi
   WorkingDirectory=/home/udyogsathi/app
   EnvironmentFile=/home/udyogsathi/app/.env
   ExecStart=/home/udyogsathi/app/.venv/bin/uvicorn apps.api.main:app --host 0.0.0.0 --port 8000 --workers 2
   Restart=always
   RestartSec=5

   [Install]
   WantedBy=multi-user.target
   ```

6. **Start & Enable Service:**
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable --now udyogsathi
   sudo systemctl status udyogsathi
   ```

---

## 4. Post-Deployment Verification Checklist

After the service starts, run these validation checks against the live domain:

1. **Liveness Probe:**
   `curl -s https://<domain>/health/live` returns HTTP 200 `{"status": "live"}`.
2. **Readiness Probe:**
   `curl -s https://<domain>/health/ready` returns HTTP 200 `{"status": "ready", "published_schemes_count": 2}`.
3. **Web Application Load:**
   Open `https://<domain>/` or `https://<domain>/app` in a browser. Confirm Government of Odisha insignia, Scheme Catalogue, and Odia language toggle appear.
4. **Deterministic Math Verification:**
   Submit an eligibility evaluation for a Micro enterprise with ₹1,20,000 annual interest. Confirm calculation returns 75% subvention (₹90,000) within caps.
5. **RAG Citations Verification:**
   Query: *"What is the interest subsidy under CM-SRIM?"*. Verify response includes page 3 citation, notification reference, and valid Odia voice synthesis playback.
6. **Zero-Mock Audit:**
   Ensure no placeholder text, fake schemes, or simulated live sync messages appear.
