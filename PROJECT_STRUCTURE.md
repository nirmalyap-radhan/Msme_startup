# Udyog Sathi — Project Structure

```
Msme_startup/
├── frontend/
│   ├── dist/                 # Production build bundle
│   ├── node_modules/         # Node dependencies
│   ├── public/               # Public static assets (/static/css, /static/js, /static/images)
│   ├── static/               # Source static assets
│   ├── index.html            # Main web portal template
│   ├── package.json          # Node scripts ("dev": "vite", "build": "vite build")
│   ├── vite.config.js        # Vite dev server + proxy to port 8000
│   └── Dockerfile            # Frontend container (Nginx)
│
├── backend/
│   ├── app/                  # FastAPI Application
│   │   ├── __init__.py       # Package init & legacy aliases
│   │   ├── main.py           # App entry point (app = FastAPI(...))
│   │   ├── config.py         # Settings & CORS config
│   │   ├── routers/          # API endpoints (schemes, eligibility, rag, updates, health, etc.)
│   │   ├── schemas/          # Pydantic models
│   │   └── security/         # JWT, auth & RBAC
│   ├── services/             # Core Services
│   │   ├── ai_gateway/       # Multi-LLM provider gateway
│   │   ├── deadline_monitoring/# Scheduler & notification service
│   │   ├── eligibility/      # Deterministic rule evaluator & benefit calculator
│   │   ├── rag/              # Retrieval Augmented Generation & prompt pipeline
│   │   ├── scheme_discovery/ # Automated scheme web crawler & connectors
│   │   └── scheme_ingestion/ # PDF parser, OCR, storage & reviewer gate
│   ├── data/                 # SQLite database & document vault
│   ├── migrations/           # Alembic database migrations
│   ├── prompts/              # System prompts & instruction templates
│   ├── scripts/              # Ingestion, audit & recovery scripts
│   ├── tests/                # Automated unit & integration tests
│   ├── docs/                 # Architectural specifications
│   ├── requirements.txt      # Python dependencies
│   ├── .env                  # Backend environment variables
│   ├── alembic.ini           # Alembic configuration
│   └── Dockerfile            # Backend container
│
└── docker-compose.yml        # Orchestration config
```
