"""
Public & Private Banking MSME Product Discovery Connector.
Connects directly to official bank websites (SBI, Bank of Baroda, PNB, SIDBI, CGTMSE)
to extract MSME commercial credit facilities, credit guarantees, working capital,
and term loan programs.
CRITICAL ZERO-MOCK RULE: Explicitly tags products as 'bank_product' to preserve
distinction from statutory government schemes.
"""

from typing import List, Optional
from urllib.parse import urljoin
from bs4 import BeautifulSoup

from services.scheme_discovery.connectors.base import BaseSourceConnector
from services.scheme_discovery.models import (
    DiscoveredDocumentCandidate,
    SourceRegistryConfig,
    SourceType,
)


class BankProductConnector(BaseSourceConnector):
    """
    Parses official banking SME pages for active loan products, credit ceilings,
    working capital facilities, and government-backed credit guarantees.
    """

    def __init__(self, source_config: SourceRegistryConfig):
        super().__init__(source_config)

    def _determine_category(self, text: str) -> str:
        text_lower = text.lower()
        if any(w in text_lower for w in ["working capital", "cash credit", "invoice", "od", "overdraft"]):
            return "finance_credit"
        if any(w in text_lower for w in ["term loan", "machinery", "equipment", "asset", "capex"]):
            return "finance_credit"
        if any(w in text_lower for w in ["export", "trade", "foreign currency", "packing credit"]):
            return "market_access"
        if any(w in text_lower for w in ["technology", "quality", "tequp", "tufs"]):
            return "technology_innovation"
        if any(w in text_lower for w in ["guarantee", "cgtmse", "collateral"]):
            return "finance_credit"
        return "finance_credit"

    def discover_documents(self, page_limit: int = 3) -> List[DiscoveredDocumentCandidate]:
        discovered: List[DiscoveredDocumentCandidate] = []
        html_content = self.fetch_page_content(self.config.discovery_endpoint)
        if not html_content:
            return discovered

        soup = BeautifulSoup(html_content, "html.parser")
        seen_titles = set()

        # Bank pages organize products as card headings (h3, h4, h5, or prominent a tags)
        for el in soup.find_all(["h3", "h4", "h5", "a"]):
            raw_text = el.get_text(separator=" ", strip=True)
            text_lower = raw_text.lower()

            # Filter for genuine MSME financing products
            is_relevant = any(k in text_lower for k in [
                "msme loan", "sme loan", "mudra", "stand up india", "standup india",
                "cgtmse", "working capital", "term loan", "cash credit",
                "invoice financing", "sahaj", "credit guarantee", "pratham",
                "speed", "48-hour", "growth plus", "gst express", "shaurya",
                "mahila swavalamban", "capex loan", "general credit card", "artisans credit"
            ])

            if not is_relevant:
                continue

            if len(raw_text) < 8 or len(raw_text) > 90:
                continue

            if raw_text in seen_titles:
                continue
            seen_titles.add(raw_text)

            # Find link
            href = el.get("href") if el.name == "a" else (el.find("a")["href"] if el.find("a") else None)
            product_url = urljoin(self.config.base_url, href) if href else self.config.discovery_endpoint

            # Extract nearby contextual text for loan features
            parent_text = el.parent.get_text(separator=" ", strip=True) if el.parent else ""
            category = self._determine_category(raw_text + " " + parent_text)

            # Identify loan limit or collateral hints from context
            max_limit = None
            if "5 crore" in parent_text.lower() or "5 cr" in parent_text.lower():
                max_limit = "Up to ₹5.00 Crore"
            elif "2 crore" in parent_text.lower() or "2 cr" in parent_text.lower():
                max_limit = "Up to ₹2.00 Crore"
            elif "10 lakh" in parent_text.lower() or "10 lac" in parent_text.lower():
                max_limit = "Up to ₹10.00 Lakh (Mudra Tarun)"
            elif "50 lakh" in parent_text.lower():
                max_limit = "Up to ₹50.00 Lakh"

            collateral_req = "Collateral-free up to ₹5 Cr with CGTMSE coverage" if "cgtmse" in parent_text.lower() else "Subject to Bank Credit Policy"

            candidate = DiscoveredDocumentCandidate(
                title=raw_text,
                source_url=product_url,
                official_portal_url=self.config.discovery_endpoint,
                issuing_authority=self.config.name,
                source_type=self.config.source_type,
                discovery_source_id=self.config.id,
                category=category,
                scheme_type="bank_product",
                update_type="bank_product",
                interest_rate_published="Repo Rate / EBLR Linked Competitive MSME Rates",
                max_loan_limit=max_limit,
                collateral_requirement=collateral_req,
                raw_metadata={
                    "product_name": raw_text,
                    "bank_name": self.config.name,
                    "feature_context": parent_text[:500],
                }
            )
            discovered.append(candidate)

        return discovered
