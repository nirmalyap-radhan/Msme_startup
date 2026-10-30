# Udyog Sathi — Unified MSME Scheme Platform

Real-world AI-powered government scheme discovery and assistance platform for MSMEs in Odisha, India.

---

## 📁 Two-Folder Project Structure

The entire application is organized into two self-contained directories:

```
Msme_startup/
├── frontend/             # Frontend Client (Vite, Vanilla JS/CSS, Odia/Hindi i18n)
│   ├── public/           # Static assets (images, css, js)
│   ├── index.html        # Main web application entry point
│   ├── package.json      # Frontend dependencies & npm scripts
│   ├── vite.config.js    # Dev server configuration with backend proxy
│   └── Dockerfile        # Production static build & Nginx container
│
├── backend/              # Backend API & Services (FastAPI, SQLite, OCR, AI Gateway)
│   ├── app/              # FastAPI application (main.py, routers, schemas, security)
│   ├── services/         # Core MSME intelligence (ingestion, eligibility, RAG, deadline)
│   ├── data/             # Verified SQLite database & document vault
│   ├── migrations/       # Alembic database migrations
│   ├── scripts/          # Ingestion, audit, and backup utilities
│   ├── tests/            # Test suite (pytest)
│   ├── requirements.txt  # Python dependencies
│   ├── .env              # Backend configuration & AI credentials
│   └── Dockerfile        # Containerized backend service
│
└── docker-compose.yml    # Unified multi-container deployment
```

---

## 🚀 Running the Application

### 1. Backend (FastAPI + Uvicorn)

In a terminal, navigate to `backend`:

```powershell
cd backend
uvicorn app.main:app --reload
```
- **Backend URL**: [http://127.0.0.1:8000](http://127.0.0.1:8000)
- **API Documentation (Swagger UI)**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **Health / Readiness Endpoint**: [http://127.0.0.1:8000/health/ready](http://127.0.0.1:8000/health/ready)

### 2. Frontend (Vite)

In a second terminal, navigate to `frontend`:

```powershell
cd frontend
npm run dev
```
- **Web App**: [http://localhost:3000](http://localhost:3000)
- The frontend dev server automatically proxies all `/api` and `/health` requests to `http://127.0.0.1:8000`.

---

## 🧪 Running Tests

To run the automated test suite in the backend:

```powershell
cd backend
python -m pytest
```

---

## 🐳 Running with Docker Compose

To run both `frontend` and `backend` in containerized production mode:

```bash
docker compose up --build
```
- Frontend: `http://localhost:3000`
- Backend API: `http://localhost:8000`
