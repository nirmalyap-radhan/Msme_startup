"""
Unit tests for Source Document Fetcher and Provenance Verification.
"""

import os
import tempfile
import pytest

from services.scheme_ingestion.fetcher import DocumentFetcher, DocumentFetchError
from services.scheme_ingestion.config import IngestionConfig


@pytest.fixture
def temp_fetcher():
    with tempfile.TemporaryDirectory() as tmp_dir:
        config = IngestionConfig(
            DOCUMENT_STORAGE_PATH=os.path.join(tmp_dir, "raw"),
            PROCESSED_STORAGE_PATH=os.path.join(tmp_dir, "processed"),
            SCHEME_SOURCE_ALLOWLIST="msme.odisha.gov.in,odishamsme.nic.in,msme.gov.in,myscheme.gov.in",
        )
        yield DocumentFetcher(config=config)


def test_domain_allowlist_enforcement(temp_fetcher):
    # Approved official domains
    assert temp_fetcher.is_url_allowed("https://msme.odisha.gov.in/sites/default/files/test.pdf") is True
    assert temp_fetcher.is_url_allowed("https://odishamsme.nic.in/scheme.pdf") is True
    assert temp_fetcher.is_url_allowed("https://www.msme.gov.in/guidelines.pdf") is True
    assert temp_fetcher.is_url_allowed("https://www.myscheme.gov.in/details") is True

    # Unauthorized third-party or hostile domains
    assert temp_fetcher.is_url_allowed("https://fakeschemes.com/download.pdf") is False
    assert temp_fetcher.is_url_allowed("https://msme.odisha.gov.in.attacker.com/evil.pdf") is False
    assert temp_fetcher.is_url_allowed("http://169.254.169.254/latest/meta-data") is False
    assert temp_fetcher.is_url_allowed("invalid-url") is False


def test_import_local_file_provenance(temp_fetcher):
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
        f.write(b"%PDF-1.4 Official Odisha Government MSME Policy Document Test Content")
        temp_file_path = f.name

    try:
        doc = temp_fetcher.import_local_file(
            local_path=temp_file_path,
            official_url="https://msme.odisha.gov.in/en/notification/policies/test.pdf",
            title="Test Official Policy"
        )

        assert doc.title == "Test Official Policy"
        assert doc.source_url == "https://msme.odisha.gov.in/en/notification/policies/test.pdf"
        assert len(doc.sha256_hash) == 64
        assert doc.file_size_bytes > 0
        assert os.path.exists(doc.local_path)
        assert doc.local_path.endswith(f"{doc.sha256_hash}.pdf")
    finally:
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)


def test_import_nonexistent_file_raises_error(temp_fetcher):
    with pytest.raises(DocumentFetchError, match="Local file not found"):
        temp_fetcher.import_local_file(
            local_path="/nonexistent/path/to/scheme.pdf",
            official_url="https://msme.odisha.gov.in/scheme.pdf",
            title="Nonexistent"
        )


def test_unauthorized_url_fetch_raises_error(temp_fetcher):
    with pytest.raises(DocumentFetchError, match="violates domain allowlist"):
        temp_fetcher.fetch_url("https://unapproved-thirdparty-site.com/scheme.pdf")
