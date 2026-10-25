"""
Odisha Gazette, Policies & Notifications Connector.
Specialized parser for official Government of Odisha MSME Department tables
and Invest Odisha Industrial Policy Resolution (IPR 2022) guidelines.
Extracts notification numbers, circular titles, publication dates, and PDF documents.
"""

import re
from typing import List, Optional
from urllib.parse import urljoin
from bs4 import BeautifulSoup

from services.scheme_discovery.connectors.base import BaseSourceConnector
from services.scheme_discovery.models import (
    DiscoveredDocumentCandidate,
    SourceRegistryConfig,
    SourceType,
)


class OdishaGazetteConnector(BaseSourceConnector):
    """
    Parses structured government gazette notifications and policy amendment tables.
    Detects whether an entry is a new scheme, an amendment, or an operational guideline.
    """

    def __init__(self, source_config: SourceRegistryConfig):
        super().__init__(source_config)

    def _determine_category(self, text: str) -> str:
        text_lower = text.lower()
        if any(w in text_lower for w in ["interest", "credit", "loan", "working capital", "finance", "reimbursement of interest", "srim"]):
            return "finance_credit"
        if any(w in text_lower for w in ["subsidy", "incentive", "capital investment", "cis", "sgst", "stamp duty", "electricity duty", "power tariff", "exemption"]):
            return "subsidy_incentives"
        if any(w in text_lower for w in ["skill", "training", "employment subsidy", "employment cost"]):
            return "skill_development"
        if any(w in text_lower for w in ["trademark", "patent", "intellectual property", "gi", "technology", "quality", "zed", "technology purchase"]):
            return "technology_innovation"
        if any(w in text_lower for w in ["export", "trade fair", "marketing", "vendor", "procurement preference"]):
            return "market_access"
        if any(w in text_lower for w in ["infrastructure", "cluster", "industrial estate", "land", "park", "iimf"]):
            return "infrastructure_support"
        return "subsidy_incentives"

    def _determine_update_type(self, title: str) -> str:
        title_lower = title.lower()
        if "amendment" in title_lower:
            return "amendment"
        if any(w in title_lower for w in ["deadline", "extension", "last date", "extended"]):
            return "deadline_extension"
        if any(w in title_lower for w in ["policy", "resolution", "gazette"]):
            return "policy_gazette"
        return "new_scheme"

    def _extract_notification_no(self, text: str) -> Optional[str]:
        match = re.search(
            r'(?:Notification|Circular|Order|Resolution|Letter)\s*(?:No\.?|Number)?\s*[:\-]?\s*([A-Za-z0-9\-\./_]+(?:\s*/\s*[A-Za-z0-9\-\.]+)*)',
            text,
            re.IGNORECASE
        )
        if match:
            return match.group(0).strip()
        return None

    def _extract_date(self, text: str) -> Optional[str]:
        match = re.search(
            r'\b(\d{1,2}[\.\-\/]\d{1,2}[\.\-\/]\d{2,4}|\d{1,2}(?:st|nd|rd|th)?\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*[\s,]+\d{4})\b',
            text,
            re.IGNORECASE
        )
        if match:
            return match.group(0).strip()
        return None

    def discover_documents(self, page_limit: int = 3) -> List[DiscoveredDocumentCandidate]:
        discovered: List[DiscoveredDocumentCandidate] = []
        html_content = self.fetch_page_content(self.config.discovery_endpoint)
        if not html_content:
            return discovered

        soup = BeautifulSoup(html_content, "html.parser")

        # 1. Check for standard table rows (msme.odisha.gov.in /notification/policies format)
        table_rows = soup.find_all("tr")
        seen_urls = set()

        for tr in table_rows:
            tds = tr.find_all("td")
            if not tds or len(tds) < 2:
                continue

            # In Odisha MSME policy table: Col 0 is Index/Sl, Col 1 is Title, Col 2 is Date/Download
            title_text = tds[1].get_text(separator=" ", strip=True) if len(tds) >= 2 else ""
            if not title_text or len(title_text) < 5:
                continue

            # Find PDF links in the row
            links = tr.find_all("a", href=True)
            for a in links:
                href = a["href"].strip()
                if not href or href.startswith("#") or href.startswith("javascript:"):
                    continue

                full_url = urljoin(self.config.base_url, href)
                if not (full_url.lower().endswith(".pdf") or "/files/" in full_url.lower() or "/download/" in full_url.lower()):
                    continue

                if full_url in seen_urls:
                    continue
                seen_urls.add(full_url)

                category = self._determine_category(title_text)
                update_type = self._determine_update_type(title_text)
                notif_no = self._extract_notification_no(title_text)
                pub_date = self._extract_date(title_text)

                candidate = DiscoveredDocumentCandidate(
                    title=title_text[:512],
                    source_url=full_url,
                    official_portal_url=self.config.discovery_endpoint,
                    issuing_authority=self.config.name,
                    source_type=self.config.source_type,
                    discovery_source_id=self.config.id,
                    gazette_or_circular_no=notif_no,
                    announcement_date=pub_date,
                    category=category,
                    scheme_type="government_scheme",
                    update_type=update_type,
                    raw_metadata={
                        "table_row_title": title_text,
                        "anchor_text": a.get_text(strip=True),
                    }
                )
                discovered.append(candidate)

        # 2. Check for anchor links if not table-based (e.g. Invest Odisha IPR page)
        for a in soup.find_all("a", href=True):
            href = a["href"].strip()
            if not href or href.startswith("#") or href.startswith("javascript:"):
                continue

            full_url = urljoin(self.config.base_url, href)
            if not (full_url.lower().endswith(".pdf") or "/download/" in full_url.lower()):
                continue

            if full_url in seen_urls:
                continue
            seen_urls.add(full_url)

            link_text = a.get_text(separator=" ", strip=True)
            parent_text = a.parent.get_text(separator=" ", strip=True) if a.parent else ""
            title = link_text if len(link_text) > 12 else parent_text
            if len(title) < 5:
                title = full_url.split("/")[-1].replace(".pdf", "").replace("_", " ").title()

            combined = f"{title} {parent_text}"
            category = self._determine_category(combined)
            update_type = self._determine_update_type(combined)
            notif_no = self._extract_notification_no(combined)
            pub_date = self._extract_date(combined)

            candidate = DiscoveredDocumentCandidate(
                title=title[:512],
                source_url=full_url,
                official_portal_url=self.config.discovery_endpoint,
                issuing_authority=self.config.name,
                source_type=self.config.source_type,
                discovery_source_id=self.config.id,
                gazette_or_circular_no=notif_no,
                announcement_date=pub_date,
                category=category,
                scheme_type="government_scheme",
                update_type=update_type,
                raw_metadata={
                    "anchor_text": link_text,
                    "parent_context": parent_text[:400],
                }
            )
            discovered.append(candidate)

        return discovered
