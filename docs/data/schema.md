# Data Ingestion & Scheme Knowledge Layer Schema Documentation

> **Specification:** Udyog Sathi Data Layer  
> **Status:** Production Data Architecture  
> **Authority:** `02_PHASE_DATA_INGESTION.md` & `00_MASTER_PROMPT.md`  

---

## 1. Overview & Data Integrity Principles

The Udyog Sathi Scheme Knowledge Layer stores structured, verifiable government scheme records extracted from official State and Central publications.

### Core Non-Negotiable Constraints
1. **Provenance Traceability:** Every stored fact, eligibility condition, subsidy cap, and required document points directly to its source document ID, source page, legal clause/section, and authoritative government URL.
2. **Zero-Mock Policy:** No synthetic fixtures or demonstration records are permitted in production tables. Draft, pending, or failed extractions are strictly segregated from public search.
3. **Three-Valued Rules Representation:** Scheme eligibility conditions are stored in machine-readable format (`=, !=, >, >=, <, <=, IN, NOT IN, EXCLUDES`) to enable deterministic evaluation (`True`, `False`, `Unknown`).
4. **Immutability of Audit Trails:** Every administrative review, approval, rejection, or amendment logs a tamper-evident audit record.

---

## 2. Entity Relationship Diagram (ERD)

```mermaid
erDiagram
    SOURCE_DOCUMENT ||--o{ DOCUMENT_PASSAGE : contains
    SOURCE_DOCUMENT ||--o{ SCHEME : grounds
    SCHEME ||--o{ ELIGIBILITY_RULE : defines
    SCHEME ||--o{ BENEFIT_RULE : specifies
    SCHEME ||--o{ REVIEW_EVENT : audits
    SCHEME ||--o? SCHEME : supersedes
    INGESTION_JOB ||--o? SOURCE_DOCUMENT : produces

    SOURCE_DOCUMENT {
        string id PK
        string title
        string source_url
        string local_path
        string sha256_hash UK
        string mime_type
        int file_size_bytes
        datetime retrieved_at_utc
        int page_count
        boolean is_scanned
        boolean ocr_applied
    }

    DOCUMENT_PASSAGE {
        string id PK
        string document_id FK
        int page_number
        string section_heading
        text text_content
        int character_count
        boolean is_ocr
        float ocr_confidence
    }

    SCHEME {
        string id PK
        string official_name
        string official_name_odia
        string department
        string implementing_agency
        string jurisdiction
        string source_url
        string source_document_id FK
        string document_sha256
        text summary
        string status
        string version
        string effective_date
        string expiry_date
        json required_documents
        text application_process
        string official_portal_url
        datetime created_at
        datetime updated_at
        datetime published_at
        string verified_by_reviewer
        text verification_notes
        string supersedes_scheme_id FK
    }

    ELIGIBILITY_RULE {
        string id PK
        string scheme_id FK
        string attribute_name
        string operator
        json value_json
        text description
        string source_clause
        int source_page
        boolean is_verified
    }

    BENEFIT_RULE {
        string id PK
        string scheme_id FK
        string benefit_type
        text formula_description
        float subsidy_percentage
        float max_limit_inr
        int duration_years
        string source_clause
        int source_page
        boolean is_verified
    }

    REVIEW_EVENT {
        string id PK
        string scheme_id FK
        string reviewer_id
        string reviewer_name
        string action
        text notes
        json verified_fields
        datetime reviewed_at
    }

    INGESTION_JOB {
        string id PK
        string source_url
        string status
        datetime started_at
        datetime completed_at
        text error_message
        string document_id
        string scheme_id
        json extraction_stats
    }
```

---

## 3. Scheme Lifecycle State Machine

A scheme progresses through an explicit, controlled state machine:

```text
  [ DISCOVERED ]
        │  (HTTP Fetch & Checksum Verification)
        ▼
  [ EXTRACTED ]
        │  (PyMuPDF Text Parsing + Tesseract OCR)
        ▼
  [ PENDING_REVIEW ] ─── (Officer Review Rejection) ───▶ [ WITHDRAWN ]
        │
        │  (Officer Verification & Sign-Off)
        ▼
  [ PUBLISHED ] ◄── (Searchable on Live Platform)
        │
        ├── (New Notification / Amendment) ──▶ [ SUPERSEDED ]
        │
        └── (Validity Period Expired) ───────▶ [ EXPIRED ]
```

### State Definitions & Access Rules
- **`discovered`:** URL cataloged in source register; document not yet downloaded. (Private/Internal)
- **`extracted`:** Raw PDF text and OCR passages extracted into memory. (Private/Internal)
- **`pending_review`:** Candidate eligibility conditions, financial formulas, and checklists normalized into relational tables; awaiting department reviewer sign-off. (Private/Admin only)
- **`verified`:** Reviewer has validated the extracted clauses against the official Gazette notification.
- **`published`:** Scheme is live in the public catalogue, queryable by entrepreneurs, and active in the deterministic eligibility engine.
- **`superseded`:** Scheme has been amended or replaced by a newer policy notification (points to newer `scheme_id`).
- **`expired`:** Policy validity period has concluded.
- **`withdrawn`:** Policy officially cancelled or suspended by government order.

---

## 4. Field Provenance & Traceability Specifications

Every candidate rule and benefit item must satisfy the following schema contracts:

### Eligibility Condition Schema Contract
| Field | Type | Description | Example |
|---|---|---|---|
| `attribute_name` | string | Normalized business attribute evaluated by rules engine | `enterprise_class`, `sector`, `district`, `commencement_date` |
| `operator` | string | Deterministic comparison operator | `=`, `!=`, `>`, `>=`, `<`, `<=`, `IN`, `NOT IN`, `EXCLUDES` |
| `value_json` | JSON | Target value or value set | `{"value": ["micro", "small"]}` |
| `description` | string | Human-readable explanation in plain English/Odia | *"Enterprise must be categorized as micro or small under MSMED Act."* |
| `source_clause` | string | Legal clause identifier from official notification | `"Clause 4.1(a)"` |
| `source_page` | integer | Physical page number in source PDF | `3` |
| `is_verified` | boolean | Set to `true` only upon reviewer sign-off | `true` / `false` |

### Benefit Rule Schema Contract
| Field | Type | Description | Example |
|---|---|---|---|
| `benefit_type` | string | Taxonomy classification | `capital_investment_subsidy`, `interest_subsidy`, `patent_reimbursement` |
| `formula_description` | string | Verbatim or structured benefit formula | *"30% of investment in plant and machinery subject to ceiling of Rs. 50 Lakh"* |
| `subsidy_percentage` | float | Applicable percentage rate | `30.0` |
| `max_limit_inr` | float | Absolute monetary ceiling in Indian Rupees | `5000000.0` |
| `duration_years` | integer | Duration of incentive in years (if recurring) | `5` |
| `source_clause` | string | Source clause citation | `"Clause 6.2"` |
| `source_page` | integer | Physical page number in source PDF | `5` |
| `is_verified` | boolean | Set to `true` only upon reviewer sign-off | `true` / `false` |

---

## 5. Directory Layout & Document Vault Security

- Raw PDF files are stored in `data/raw/<sha256>.pdf` with permissions `0600`.
- The vault directory is included in `.gitignore` to prevent committing government documents or private attachments into git history.
- Extraction outputs are saved in `data/processed/` and indexed in `data/udyog_sathi.db` (or PostgreSQL in production).
