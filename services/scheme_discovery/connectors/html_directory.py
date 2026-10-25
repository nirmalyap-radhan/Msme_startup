"""
HTML Directory & Gazette Document Connector for Government & Banking Portals.
Discovers scheme circulars, policy notifications, and PDF guidelines with metadata.
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


class HtmlDirectoryConnector(BaseSourceConnector):
    """
    Parses official HTML tables, scheme listings, and gazette circular repositories.
    Extracts PDF links, notification numbers, announcement dates, and category hints.
    """

    def __init__(self, source_config: SourceRegistryConfig):
        super().__init__(source_config)

    def _determine_category(self, text: str) -> str:
        text_lower = text.lower()
        if any(w in text_lower for w in ["interest", "credit", "loan", "working capital", "finance", "guarantee", "reimbursement of interest"]):
            return "finance_credit"
        if any(w in text_lower for w in ["subsidy", "incentive", "capital investment", "ipr", "exemption"]):
            return "subsidy_incentives"
        if any(w in text_lower for w in ["skill", "training", "entrepreneurship development", "capacity"]):
            return "skill_development"
        if any(w in text_lower for w in ["trademark", "patent", "intellectual property", "gi", "technology", "quality", "zed"]):
            return "technology_innovation"
        if any(w in text_lower for w in ["export", "trade fair", "exhibition", "marketing", "vendor"]):
            return "market_access"
        if any(w in text_lower for w in ["infrastructure", "cluster", "industrial estate", "land"]):
            return "infrastructure_support"
        return "finance_credit"

    def _extract_notification_no(self, text: str) -> Optional[str]:
        # Matches patterns like 'Notification No. 7946/MSME', 'No. MSME-P&B-0017-2023', 'Circular No. 12/2024'
        match = re.search(
            r'(?:Notification|Circular|Order|Resolution|Letter)\s*(?:No\.?|Number)?\s*[:\-]?\s*([A-Za-z0-9\-\./_]+(?:\s*/\s*[A-Za-z0-9\-\.]+)*)',
            text,
            re.IGNORECASE
        )
        if match:
            return match.group(0).strip()
        return None

    def _extract_date(self, text: str) -> Optional[str]:
        # Matches dates like 04.11.2023, 04/11/2023, 04-11-2023, 4th November 2023
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

        # 1. Look for all hyperlinks ending in .pdf or containing /files/ /download /notification
        seen_urls = set()
        for a_tag in soup.find_all("a", href=True):
            href = a_tag["href"].strip()
            if not href or href.startswith("javascript:") or href.startswith("#"):
                continue

            full_url = urljoin(self.config.base_url, href)
            is_pdf = full_url.lower().endswith(".pdf") or "/files/" in full_url.lower() or "/pdf/" in full_url.lower()

            if not is_pdf:
                continue

            if full_url in seen_urls:
                continue
            seen_urls.add(full_url)

            # Determine title: anchor text, title attribute, or nearby parent text
            link_text = a_tag.get_text(separator=" ", strip=True)
            parent_text = a_tag.parent.get_text(separator=" ", strip=True) if a_tag.parent else ""
            title = link_text if len(link_text) > 10 else parent_text
            if len(title) < 5:
                # Use filename as fallback title
                title = full_url.split("/")[-1].replace(".pdf", "").replace("_", " ").title()

            combined_context = f"{title} {parent_text}"
            category = self._determine_category(combined_context)
            notif_no = self._extract_notification_no(combined_context)
            notif_date = self._extract_date(combined_context)

            candidate = DiscoveredDocumentCandidate(
                title=title[:256],
                source_url=full_url,
                official_portal_url=self.config.discovery_endpoint,
                issuing_authority=self.config.name,
                source_type=self.config.source_type,
                discovery_source_id=self.config.id,
                gazette_or_circular_no=notif_no,
                announcement_date=notif_date,
                category=category,
                raw_metadata={
                    "anchor_text": link_text,
                    "parent_context": parent_text[:500],
                }
            )
            discovered.append(candidate)

        return discovered
