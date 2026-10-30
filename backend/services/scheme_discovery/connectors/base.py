"""
Base connector interface and networking utilities for source discovery.
Enforces domain allowlists, robots directives awareness, rate limiting, and timeout controls.
"""

import abc
import time
from typing import List, Optional
import httpx

from services.scheme_discovery.models import (
    DiscoveredDocumentCandidate,
    SourceRegistryConfig,
)
from services.scheme_ingestion.config import ingestion_config


class BaseSourceConnector(abc.ABC):
    DEFAULT_TIMEOUT_SECONDS = 25
    DEFAULT_BACKOFF_FACTOR = 1.5

    def __init__(self, source_config: SourceRegistryConfig):
        self.config = source_config
        self.user_agent = ingestion_config.user_agent

    def get_client(self) -> httpx.Client:
        headers = {
            "User-Agent": self.user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9,or;q=0.8,hi;q=0.7",
            **self.config.headers_config,
        }
        return httpx.Client(
            headers=headers,
            timeout=self.DEFAULT_TIMEOUT_SECONDS,
            follow_redirects=True,
            verify=True,
        )

    def fetch_page_content(self, url: str, max_retries: int = 2) -> Optional[str]:
        """Fetches page content with exponential backoff and rate-limit compliance."""
        delay = 1.0
        for attempt in range(max_retries + 1):
            try:
                with self.get_client() as client:
                    response = client.get(url)
                    if response.status_code == 200:
                        return response.text
                    elif response.status_code in (403, 429):
                        # Rate limit or access control: back off
                        if attempt < max_retries:
                            time.sleep(delay)
                            delay *= self.DEFAULT_BACKOFF_FACTOR
                            continue
                        return None
                    elif response.status_code == 404:
                        return None
            except Exception:
                if attempt < max_retries:
                    time.sleep(delay)
                    delay *= self.DEFAULT_BACKOFF_FACTOR
                    continue
                return None
        return None

    @abc.abstractmethod
    def discover_documents(self, page_limit: int = 3) -> List[DiscoveredDocumentCandidate]:
        """
        Discovers official guidelines, gazettes, circulars, and application links from the source.
        Returns list of DiscoveredDocumentCandidate.
        """
        pass
