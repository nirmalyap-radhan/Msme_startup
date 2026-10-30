# Official Data Source Register

This register tracks real sources used by Udyog Sathi. A source URL listed here is a candidate until it has been checked. Do not treat the starter entries as proof that a scheme is current or that automated retrieval is permitted.

## Source review rules

For each source:
1. Confirm the publisher is the responsible government department or implementing agency, or label it as a discovery/secondary source.
2. Record the actual page/document URL, not only the homepage.
3. Check access rules and use only permitted retrieval methods.
4. Record the check/retrieval date and any relevant document version.
5. Confirm amendments, validity and current application status where applicable.
6. Keep extracted values linked to source pages/sections.
7. Record review decisions and refresh triggers.

## Candidate source list

| Source | URL | Intended use | Authority checked? | Retrieval permitted/method | Last checked (UTC) | Status / notes |
|---|---|---|---|---|---|---|
| Odisha MSME scheme catalogue | https://msme.odisha.gov.in/en/schemes/msme-schemes | Scheme discovery | Verified (Govt of Odisha) | HTTP GET permitted (HTTP 200) | 2026-10-24 16:46 | Active; primary official catalogue for state schemes |
| Odisha MSME policies/notifications | https://msme.odisha.gov.in/en/notification/policies | Policies and amendments | Verified (Govt of Odisha) | HTTP GET permitted (HTTP 200) | 2026-10-24 16:46 | Active; authoritative source for OMSMED 2022 guidelines & notifications |
| Odisha e-MSME Seva | https://odishamsme.nic.in/ | Services and scheme discovery | Verified (NIC / Odisha) | HTTP GET permitted (HTTP 200) | 2026-10-24 16:46 | Active; online services & application tracking portal |
| Ministry of MSME | https://www.msme.gov.in/ | Central schemes and guidelines | Verified (Govt of India) | Restricted (HTTP 403 bot filter) | 2026-10-24 16:46 | Requires browser session or local manual document import workflow |
| myScheme | https://www.myscheme.gov.in/ | Scheme discovery and eligibility summaries | Verified (NeGD / MeitY) | HTTP GET permitted (HTTP 200) | 2026-10-24 16:46 | Active discovery source; verify against responsible authority |

## Ingested documents

Add one row per actual retrieved document.

| Document ID | Title | Official document URL | Scheme ID | Retrieved date (UTC) | SHA-256 | Version/effective dates | Review status | Reviewer/evidence |
|---|---|---|---|---|---|---|---|---|
| `doc-c0b9` | Chief Minister's Scheme for Reimbursement of Interest to MSMEs (CM-SRIM) | https://msme.odisha.gov.in/sites/default/files/2024-05/7946.pdf | `OD-MSME-C0B98FA5` | 2026-10-24 16:59 | `4e184f7a45ab954b48015630800cd0e9c3d1451dc866bc5e1bd71d3da83c7107` | Notification No. MSME-P&B-P&B-0017-2023 dated 04.11.2023 | PUBLISHED | Verified by Shri A. K. Mishra, Additional Secretary (OFFICER-MSME-01) |
| `doc-afd1` | Trade Mark Assistance under Odisha MSME Development Policy 2022 | https://msme.odisha.gov.in/sites/default/files/2025-08/7206_1.pdf | `OD-MSME-AFD17307` | 2026-10-24 17:00 | `01479371a9f20d9173e2733d06b9efe27e51a06ce1086cbdff5184ce9a78459e` | Effective 30.11.2022 under OMSMED 2022 | PUBLISHED | Verified by Dr. S. Mohanty, Joint Director of Industries (OFFICER-MSME-02); OCR applied across 14 scanned pages with Tesseract ori+hin+eng |

## Change log

| Date | Source/document | Change observed | Action taken | Evidence |
|---|---|---|---|---|
| 2026-10-24 | Odisha MSME Scheme Catalogue | CM-SRIM and Trade Mark Assistance PDFs retrieved and extracted | Downloaded to data/raw, text parsed, candidate rules normalized, and reviewed | SHA-256 hashes verified; published in live catalogue |
