# Udyog Sathi API Specification

## 1. Overview & Architecture

The Udyog Sathi Backend API is implemented in FastAPI (`apps/api`), exposing RESTful endpoints under the versioned prefix `/api/v1`. It connects the verified government scheme database with an auditable three-valued eligibility engine, authenticated enterprise profiles, and user-managed application progress tracking.

### Core Architectural Principles
- **Strict Zero-Mock Policy (Rule 2):** In production mode, all endpoints retrieve exclusively verified, persisted records. Empty search results return empty arrays (`[]`), never synthetic or decorative scheme cards.
- **Deterministic Eligibility (Rule 8):** Eligibility calculations are governed by three-valued logic and mathematical formulas without non-deterministic AI in the critical decision loop.
- **Tenant & Row Isolation:** MSME user profiles and application tracking entries are tied strictly to authenticated user IDs (`sub` claim in signed JWT).
- **Security Headers:** The API automatically enforces security headers (`X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `X-XSS-Protection: 1; mode=block`).

---

## 2. Authentication & Authorization

Authentication utilizes signed JSON Web Tokens (HS256) with passwords hashed using `PBKDF2-HMAC-SHA256` (100,000 iterations and cryptographically random 16-byte salts).

### Roles & Access Levels
| Role | Description | Accessible Endpoints |
|---|---|---|
| `public` | Unauthenticated citizen/entrepreneur | `/health/*`, `GET /api/v1/schemes*`, `POST /api/v1/eligibility/evaluate`, `POST /api/v1/profiles/*` |
| `entrepreneur` | Registered MSME enterprise owner | Above + `GET/PUT /api/v1/profiles/me`, `/api/v1/applications*` |
| `scheme_reviewer` | Departmental officer / policy reviewer | Above + `GET /api/v1/admin/schemes/*`, `POST /api/v1/admin/schemes/{id}/verify` |
| `platform_admin` | Platform administrator | Full system access |

---

## 3. Endpoints

### 3.1 Health & Diagnostics

#### `GET /health/live`
- **Description:** Basic liveness probe confirming the server process is alive.
- **Response `200 OK`:**
```json
{
  "status": "live",
  "app_name": "Udyog Sathi API",
  "version": "1.0.0",
  "timestamp": "2026-10-24T17:15:00.000000"
}
```

#### `GET /health/ready`
- **Description:** Readiness probe confirming database connectivity and returning live published catalogue counts.
- **Response `200 OK`:**
```json
{
  "status": "ready",
  "database": "healthy",
  "published_schemes_count": 2,
  "environment": "development",
  "timestamp": "2026-10-24T17:15:00.000000"
}
```

---

### 3.2 Scheme Catalogue & Document Provenance

#### `GET /api/v1/schemes`
- **Description:** Search and filter verified, published government schemes.
- **Query Parameters:**
  - `search` (string, optional): Search term matched against scheme title and summary.
  - `sector` (string, optional): Filter by sector (`manufacturing`, `service`, `agro-processing`).
  - `enterprise_class` (string, optional): Filter by MSME class (`micro`, `small`, `medium`).
  - `page` (int, default: 1): Page number.
  - `limit` (int, default: 20, max: 100): Records per page.
- **Response `200 OK`:** Array of `SchemeSummaryResponse` objects. If no matches exist, returns `[]`.

#### `GET /api/v1/schemes/{scheme_id}`
- **Description:** Retrieve full verified scheme details, legal clause citations, mathematical benefit formulas, and official application portal URLs.
- **Response `200 OK`:**
```json
{
  "scheme_id": "OD-MSME-C0B98FA5",
  "official_name": "OPERATIONAL GUIDELINES FOR CHIEF MINISTER'S SCHEME FOR...",
  "official_name_odia": null,
  "department": "Department of MSME, Government of Odisha",
  "implementing_agency": "Directorate of Industries / RIC / DIC",
  "jurisdiction": "Odisha",
  "source_url": "https://msme.odisha.gov.in/sites/default/files/2024-05/7946.pdf",
  "document_sha256": "4e184f7a77e02e1c97a8927f8188fb8078652ae2eef3e86c12e75e9b97b057fb",
  "summary": "Interest subvention on working capital term loans...",
  "status": "published",
  "version": 1,
  "verified_eligibility_rules": [
    {
      "rule_id": "rule-c7821f95-0",
      "attribute_name": "state",
      "operator": "=",
      "value": "Odisha",
      "description": "Enterprise unit must be located within the State of Odisha",
      "source_clause": "Clause 2.1",
      "source_page": 2,
      "is_verified": true
    }
  ],
  "verified_benefits": [
    {
      "benefit_id": "ben-c7821f95-0",
      "benefit_type": "interest_subsidy",
      "formula_description": "Interest subvention up to 100% on eligible cash credit accounts up to Rs. 20 Lakh per annum",
      "subsidy_percentage": 100.0,
      "max_limit_inr": 2000000.0,
      "duration_years": 5,
      "source_clause": "Clause 5.1",
      "source_page": 6,
      "is_verified": true
    }
  ],
  "required_documents": [
    "Valid Udyam Registration Certificate",
    "Bank Sanction Letter for Working Capital Loan",
    "Interest Paid Certificate from Lending Bank"
  ],
  "application_process": "Apply online through the MSME Department portal.",
  "official_portal_url": "https://msme.odisha.gov.in",
  "published_at": "2026-10-24T17:00:00"
}
```
- **Response `404 Not Found`:** If `scheme_id` does not exist or is not published.

#### `GET /api/v1/schemes/{scheme_id}/checklist`
- **Description:** Returns the official required document proofs checklist extracted from government notifications.
- **Response `200 OK`:**
```json
{
  "scheme_id": "OD-MSME-C0B98FA5",
  "scheme_name": "OPERATIONAL GUIDELINES FOR CHIEF MINISTER'S SCHEME FOR...",
  "department": "Department of MSME, Government of Odisha",
  "required_documents": [
    "Valid Udyam Registration Certificate",
    "Bank Sanction Letter for Working Capital Loan",
    "Interest Paid Certificate from Lending Bank"
  ],
  "official_portal_url": "https://msme.odisha.gov.in"
}
```

---

### 3.3 Deterministic Scheme Eligibility Engine

#### `POST /api/v1/eligibility/evaluate`
- **Description:** Evaluates an MSME profile against verified rules using three-valued logic. Supports single scheme evaluation (providing `scheme_id`) or batch evaluation across all published schemes.
- **Request Body:**
```json
{
  "scheme_id": "OD-MSME-C0B98FA5",
  "profile": {
    "enterprise_name": "Kalinga Agro Tech Solutions",
    "enterprise_class": "micro",
    "sector": "agro-processing",
    "state": "Odisha",
    "district": "Khurda",
    "udyam_registered": true,
    "production_status": "commenced",
    "working_capital_loan_sanctioned": 2000000.0,
    "annual_interest_paid": 160000.0
  }
}
```
- **Response `200 OK` (Single Scheme Assessment):**
```json
{
  "scheme_id": "OD-MSME-C0B98FA5",
  "scheme_name": "OPERATIONAL GUIDELINES FOR CHIEF MINISTER'S SCHEME FOR...",
  "department": "Department of MSME, Government of Odisha",
  "jurisdiction": "Odisha",
  "source_url": "https://msme.odisha.gov.in/sites/default/files/2024-05/7946.pdf",
  "outcome": "potential_match",
  "summary_reason": "Fully eligible under verified government scheme guidelines.",
  "conditions_passed": [
    {
      "condition_id": "rule-1",
      "attribute_name": "state",
      "operator": "=",
      "required_value": "Odisha",
      "applicant_value": "Odisha",
      "result": "TRUE",
      "reasoning": "Applicant value 'Odisha' matches required 'Odisha'.",
      "source_clause": "Clause 2.1",
      "source_page": 2,
      "is_verified": true,
      "followup_question": null
    }
  ],
  "conditions_failed": [],
  "conditions_unknown": [],
  "targeted_followup_questions": [],
  "benefit_estimates": [
    {
      "status": "calculated",
      "benefit_type": "interest_subsidy",
      "estimated_amount_inr": 120000.0,
      "subsidy_percentage": 75.0,
      "max_limit_inr": 2000000.0,
      "duration_years": 5,
      "applied_formula": "75.0% reimbursement on annual interest paid of ₹160,000.00",
      "missing_inputs": [],
      "assumptions_notes": "Calculated based on interest paid of ₹160,000.00 under Clause 5.1.",
      "source_clause": "Clause 5.1",
      "source_page": 6
    }
  ],
  "disclaimer": "Assessment is advisory and based on verified rules. Government authorities hold sole jurisdiction over actual approval."
}
```
- **Response with Incomplete Information:** Returns `outcome: "more_information_required"`, lists unknown conditions, and provides `targeted_followup_questions` with field types and UI options.

---

### 3.4 MSME Profiles & Auth

#### `POST /api/v1/profiles/register`
- **Description:** Registers a new enterprise profile and generates an initial JWT access token.
- **Request Body:**
```json
{
  "email": "owner@kalingamsme.org",
  "password": "StrongPassword123!",
  "enterprise_name": "Kalinga Agro Tech Solutions",
  "enterprise_class": "micro",
  "sector": "agro-processing",
  "district": "Khurda",
  "udyam_registered": true,
  "production_status": "commenced",
  "investment_plant_machinery": 3500000.0,
  "annual_turnover": 8000000.0
}
```
- **Response `201 Created`:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": "USR-A1B2C3D4",
    "email": "owner@kalingamsme.org",
    "role": "entrepreneur",
    "enterprise_name": "Kalinga Agro Tech Solutions",
    "enterprise_class": "micro",
    "sector": "agro-processing",
    "district": "Khurda",
    "udyam_registered": true,
    "production_status": "commenced",
    "created_at": "2026-10-24T17:20:00"
  }
}
```

#### `POST /api/v1/profiles/login`
- **Description:** Authenticates credentials and returns a signed JWT access token.
- **Response `200 OK`:** Same as registration payload.
- **Response `401 Unauthorized`:** Invalid credentials.

#### `GET /api/v1/profiles/me`
- **Description:** Returns the profile of the currently authenticated enterprise.
- **Headers:** `Authorization: Bearer <token>`
- **Response `200 OK`:** `UserProfileResponse`.

#### `PUT /api/v1/profiles/me`
- **Description:** Updates profile attributes (e.g. updated turnover, investment, loan amounts).
- **Headers:** `Authorization: Bearer <token>`
- **Response `200 OK`:** Updated `UserProfileResponse`.

---

### 3.5 User-Managed Application Tracking

> **Important (Rule 13):** Application tracking is explicitly user-managed. The platform records filing dates, reference acknowledgement numbers, and notes entered by the entrepreneur. It does NOT claim automated two-way government integration unless an authorized API is provisioned.

#### `GET /api/v1/applications`
- **Description:** Lists tracked applications filed by the authenticated user.
- **Headers:** `Authorization: Bearer <token>`
- **Response `200 OK`:** Array of `ApplicationTrackingResponse`.

#### `POST /api/v1/applications`
- **Description:** Creates a user-managed tracking record for an application filed on an official portal.
- **Headers:** `Authorization: Bearer <token>`
- **Request Body:**
```json
{
  "scheme_id": "OD-MSME-C0B98FA5",
  "status": "submitted",
  "acknowledgement_ref": "OD-MSME-2026-987654",
  "filing_date": "2026-10-24",
  "notes": "Application submitted via MSME Odisha portal."
}
```
- **Response `201 Created`:** `ApplicationTrackingResponse`.

#### `PUT /api/v1/applications/{tracking_id}`
- **Description:** Updates tracking status (`submitted`, `under_scrutiny`, `queried`, `sanctioned`, `rejected`) and notes.
- **Headers:** `Authorization: Bearer <token>`

---

### 3.6 Privileged Admin & Reviewer Endpoints

> **Security:** Accessible only to users holding role `scheme_reviewer` or `platform_admin`. Regular users receive `HTTP 403 Forbidden`.

#### `GET /api/v1/admin/schemes/pending`
- **Description:** Lists extracted scheme drafts awaiting departmental review.

#### `GET /api/v1/admin/schemes/{scheme_id}/dossier`
- **Description:** Retrieves full extraction dossier, OCR confidence metrics, and source clause citations for reviewer inspection.

#### `POST /api/v1/admin/schemes/{scheme_id}/verify`
- **Description:** Officially signs off on extracted scheme rules and publishes them to the live catalogue.
- **Request Body:**
```json
{
  "notes": "Verified against Gazette Notification 7946 dated 2024-05-15.",
  "verified_overrides": {}
}
```
