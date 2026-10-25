# Suggested Repository Structure

Adapt this structure to the existing codebase; do not force a rewrite if equivalent directories already exist.

```text
udyog-sathi/
├── README.md
├── .gitignore
├── .env.example
├── docker-compose.yml                 # only if useful for the existing setup
├── prompts/
│   ├── README.md
│   ├── 00_MASTER_PROMPT.md
│   ├── 01_PHASE_REPOSITORY_AUDIT.md
│   ├── 02_PHASE_DATA_INGESTION.md
│   ├── 03_PHASE_BACKEND_ELIGIBILITY.md
│   ├── 04_PHASE_RAG_AI_INTEGRATIONS.md
│   ├── 05_PHASE_FRONTEND_PRODUCT.md
│   ├── 06_PHASE_TESTING_SECURITY_DEPLOYMENT.md
│   ├── STATUS.md
│   ├── DATA_SOURCE_REGISTER.md
│   ├── DECISIONS.md
│   ├── DEFINITION_OF_DONE.md
│   ├── ENVIRONMENT.md
│   └── AGENT_WORKFLOW.md
├── apps/
│   ├── web/                            # actual frontend app
│   └── api/                            # actual backend app
├── services/
│   ├── scheme_ingestion/               # source retrieval, parsing, review workflow
│   ├── retrieval/                      # lexical/vector retrieval if separate
│   └── eligibility/                    # deterministic rules if separate
├── packages/
│   └── shared/                         # shared schemas/types if needed
├── migrations/                         # database migrations
├── data/
│   ├── raw/                            # local/private source documents; do not commit by default
│   ├── processed/                      # extracted data; access-controlled
│   └── evaluation/                     # verified evaluation cases; not production seed data
├── docs/
│   ├── architecture/
│   ├── data/
│   ├── api/
│   ├── security/
│   ├── quality/
│   └── deployment/
├── scripts/
│   ├── ingest_sources.py
│   ├── verify_source_records.py
│   └── check_no_production_fixtures.py
└── tests/
    ├── unit/
    ├── integration/
    ├── security/
    └── e2e/
```

The tree is a target/reference structure, not a command to create every directory immediately. Create only directories required by the inspected architecture. Keep secrets and sensitive source documents out of version control.
