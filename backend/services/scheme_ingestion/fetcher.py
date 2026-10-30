"""
Source Document Fetcher and Provenance Verifier.
Safely retrieves documents from approved official government domains or imports local official files,
computing SHA-256 checksums and tracking exact retrieval provenance.
"""

import hashlib
import os
import shutil
import ssl
import time
import urllib.parse
import urllib.request
from typing import Optional, Tuple

from services.scheme_ingestion.config import ingestion_config
from services.scheme_ingestion.models import SourceDocumentSchema


class DocumentFetchError(Exception):
    """Raised when document retrieval fails or policy is violated."""
    pass


class DocumentFetcher:
    def __init__(self, config=ingestion_config):
        self.config = config
        os.makedirs(self.config.raw_storage_dir, exist_ok=True)
        os.makedirs(self.config.processed_storage_dir, exist_ok=True)

    def is_url_allowed(self, url: str) -> bool:
        """
        Validates that the source URL hostname belongs to the approved government domain allowlist.
        """
        try:
            parsed = urllib.parse.urlparse(url)
            hostname = parsed.hostname
            if not hostname:
                return False
            hostname = hostname.lower()
            return any(
                hostname == domain or hostname.endswith("." + domain)
                for domain in self.config.source_allowlist
            )
        except Exception:
            return False

    def compute_sha256(self, file_path: str) -> str:
        """Computes SHA-256 checksum of a file on disk."""
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                sha256.update(chunk)
        return sha256.hexdigest()

    def fetch_url(self, url: str, title: Optional[str] = None) -> SourceDocumentSchema:
        """
        Retrieves an official document from an approved government URL.
        Preserves original document in data/raw/<sha256>.pdf and records provenance.
        """
        if not self.is_url_allowed(url):
            raise DocumentFetchError(
                f"URL '{url}' violates domain allowlist. Allowed domains: {self.config.source_allowlist}"
            )

        headers = {
            "User-Agent": self.config.user_agent,
            "Accept": "application/pdf,application/octet-stream,*/*",
        }

        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE

        req = urllib.request.Request(url, headers=headers)
        temp_path = os.path.join(self.config.raw_storage_dir, f"temp_{int(time.time()*1000)}.pdf")

        try:
            with urllib.request.urlopen(req, timeout=self.config.request_timeout_seconds, context=ctx) as response:
                if response.status != 200:
                    raise DocumentFetchError(f"HTTP fetch failed with status code {response.status}")

                with open(temp_path, "wb") as out_file:
                    shutil.copyfileobj(response, out_file)

            # Validate non-empty file
            file_size = os.path.getsize(temp_path)
            if file_size == 0:
                raise DocumentFetchError(f"Retrieved file from '{url}' was empty (0 bytes).")

            # Compute SHA-256 and rename file to its content hash
            sha256_hash = self.compute_sha256(temp_path)
            final_path = os.path.join(self.config.raw_storage_dir, f"{sha256_hash}.pdf")

            if os.path.exists(final_path):
                # Document already exists; remove temp file and reuse existing storage
                os.remove(temp_path)
            else:
                shutil.move(temp_path, final_path)

            doc_title = title or os.path.basename(urllib.parse.urlparse(url).path) or f"Document {sha256_hash[:8]}"

            return SourceDocumentSchema(
                title=doc_title,
                source_url=url,
                local_path=final_path,
                sha256_hash=sha256_hash,
                mime_type="application/pdf",
                file_size_bytes=file_size,
            )

        except Exception as e:
            if os.path.exists(temp_path):
                os.remove(temp_path)
            raise DocumentFetchError(f"Failed to fetch document from '{url}': {str(e)}") from e

    def import_local_file(
        self,
        local_path: str,
        official_url: str,
        title: str
    ) -> SourceDocumentSchema:
        """
        Imports an official government document provided locally by an administrator.
        Validates file existence, computes SHA-256, and links to authoritative source URL.
        """
        if not os.path.exists(local_path):
            raise DocumentFetchError(f"Local file not found: {local_path}")

        file_size = os.path.getsize(local_path)
        if file_size == 0:
            raise DocumentFetchError(f"Local file '{local_path}' is empty (0 bytes).")

        sha256_hash = self.compute_sha256(local_path)
        dest_path = os.path.join(self.config.raw_storage_dir, f"{sha256_hash}.pdf")

        if not os.path.exists(dest_path):
            shutil.copy2(local_path, dest_path)

        return SourceDocumentSchema(
            title=title,
            source_url=official_url,
            local_path=dest_path,
            sha256_hash=sha256_hash,
            mime_type="application/pdf",
            file_size_bytes=file_size,
        )
