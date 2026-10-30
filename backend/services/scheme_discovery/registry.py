"""
Official Source Registry for Udyog Sathi Automated Scheme Discovery.
Seeds authoritative sources across Central Government, Odisha Government,
Public/Private Banks, and Credit Guarantee Trusts.
"""

from typing import List, Optional
from sqlalchemy.orm import Session

from services.scheme_discovery.models import (
    DiscoveryMethod,
    SourceRegistryConfig,
    SourceType,
)
from services.scheme_ingestion.models import DiscoveredSourceRegistryModel
from services.scheme_ingestion.storage import SchemeStorageRepository


DEFAULT_SOURCE_SEEDS: List[SourceRegistryConfig] = [
    # --------------------------------------------------------------------------
    # A. ODISHA GOVERNMENT (Primary State Authority)
    # --------------------------------------------------------------------------
    SourceRegistryConfig(
        id="src-odisha-msme-schemes",
        name="Odisha MSME Department Schemes Catalogue",
        source_type=SourceType.ODISHA_GOVT,
        base_url="https://msme.odisha.gov.in",
        discovery_endpoint="https://msme.odisha.gov.in/en/schemes/msme-schemes",
        discovery_method=DiscoveryMethod.HTML_DIRECTORY,
        polling_frequency_hours=12,
        notes="Primary authoritative state catalogue for Odisha MSME incentives and subsidies.",
    ),
    SourceRegistryConfig(
        id="src-odisha-msme-policies",
        name="Odisha MSME Policy Notifications & Gazettes",
        source_type=SourceType.ODISHA_GOVT,
        base_url="https://msme.odisha.gov.in",
        discovery_endpoint="https://msme.odisha.gov.in/en/notification/policies",
        discovery_method=DiscoveryMethod.HTML_DIRECTORY,
        polling_frequency_hours=12,
        notes="Authoritative gazette notifications, operational guidelines, and policy amendments.",
    ),
    SourceRegistryConfig(
        id="src-odisha-invest-ipr",
        name="Invest Odisha Industrial Policy Resolution (IPR 2022) Guidelines",
        source_type=SourceType.ODISHA_GOVT,
        base_url="https://investodisha.gov.in",
        discovery_endpoint="https://investodisha.gov.in/policy-framework/industrial-policy-resolution-2022",
        discovery_method=DiscoveryMethod.HTML_DIRECTORY,
        polling_frequency_hours=24,
        notes="IPR 2022 capital investment subsidies, SGST reimbursement, and infrastructure incentives.",
    ),

    # --------------------------------------------------------------------------
    # B. CENTRAL GOVERNMENT (Union Ministries & Schemes)
    # --------------------------------------------------------------------------
    SourceRegistryConfig(
        id="src-central-msme-schemes",
        name="Ministry of MSME, Government of India - Schemes & Programmes",
        source_type=SourceType.CENTRAL_GOVT,
        base_url="https://msme.gov.in",
        discovery_endpoint="https://msme.gov.in/schemes-programmes",
        discovery_method=DiscoveryMethod.HTML_DIRECTORY,
        polling_frequency_hours=24,
        notes="Central MSME Ministry schemes including PMEGP, PM Vishwakarma, CGTMSE, and Champions.",
    ),
    SourceRegistryConfig(
        id="src-central-myscheme-msme",
        name="myScheme National Directory - Business & Entrepreneurship",
        source_type=SourceType.CENTRAL_GOVT,
        base_url="https://www.myscheme.gov.in",
        discovery_endpoint="https://www.myscheme.gov.in/schemes",
        discovery_method=DiscoveryMethod.HTML_DIRECTORY,
        polling_frequency_hours=24,
        notes="National open scheme discovery platform (NeGD/MeitY). Secondary discovery requiring primary verification.",
    ),

    # --------------------------------------------------------------------------
    # C. DEVELOPMENT FINANCIAL INSTITUTIONS & GUARANTEE TRUSTS
    # --------------------------------------------------------------------------
    SourceRegistryConfig(
        id="src-sidbi-msme-schemes",
        name="Small Industries Development Bank of India (SIDBI) Direct Lending",
        source_type=SourceType.DEVELOPMENT_FINANCIAL_INSTITUTION,
        base_url="https://www.sidbi.in",
        discovery_endpoint="https://www.sidbi.in/en/home-product",
        discovery_method=DiscoveryMethod.HTML_DIRECTORY,
        polling_frequency_hours=48,
        notes="Apex MSME development financial institution offering direct loan schemes (SPEED, 48-Hour Assist, PRATHAM).",
    ),
    SourceRegistryConfig(
        id="src-cgtmse-guarantee",
        name="Credit Guarantee Fund Trust for Micro and Small Enterprises (CGTMSE)",
        source_type=SourceType.CREDIT_GUARANTEE_TRUST,
        base_url="https://www.cgtmse.in",
        discovery_endpoint="https://www.cgtmse.in/About-Us.aspx",
        discovery_method=DiscoveryMethod.HTML_DIRECTORY,
        polling_frequency_hours=48,
        notes="Credit guarantee coverage circulars for collateral-free MSME bank loans up to ₹5 Crore.",
    ),

    # --------------------------------------------------------------------------
    # D. PUBLIC SECTOR BANKS (Credit Facilities, Working Capital & Term Loans)
    # --------------------------------------------------------------------------
    SourceRegistryConfig(
        id="src-sbi-sme-products",
        name="State Bank of India (SBI) SME Banking & MSME Loan Schemes",
        source_type=SourceType.BANK_PSU,
        base_url="https://sbi.co.in",
        discovery_endpoint="https://sbi.co.in/web/business/sme/sme-loans",
        discovery_method=DiscoveryMethod.HTML_DIRECTORY,
        polling_frequency_hours=48,
        notes="Public sector bank MSME working capital, term loans, Stand-Up India, Mudra, and MSME Sahaj.",
    ),
    SourceRegistryConfig(
        id="src-bob-msme-products",
        name="Bank of Baroda MSME Banking Loans & Credit Products",
        source_type=SourceType.BANK_PSU,
        base_url="https://www.bankofbaroda.in",
        discovery_endpoint="https://www.bankofbaroda.in/business-banking/msme-banking/loans-and-advances",
        discovery_method=DiscoveryMethod.HTML_DIRECTORY,
        polling_frequency_hours=48,
        notes="Baroda SME Loan Pack, Digital MSME loans, Mahila Swavalamban, and CGTMSE covered term facilities.",
    ),
    SourceRegistryConfig(
        id="src-pnb-msme-products",
        name="Punjab National Bank (PNB) MSME Schemes & Working Capital",
        source_type=SourceType.BANK_PSU,
        base_url="https://www.pnbindia.in",
        discovery_endpoint="https://www.pnbindia.in/msme.html",
        discovery_method=DiscoveryMethod.HTML_DIRECTORY,
        polling_frequency_hours=48,
        notes="PNB GST Express, Digi MSME Loan, Growth Plus, and PM Vishwakarma bank credit facilities.",
    ),
]


class SourceRegistryService:
    def __init__(self, db_session: Optional[Session] = None):
        self._db = db_session

    def _get_session(self) -> Session:
        if self._db:
            return self._db
        repo = SchemeStorageRepository()
        return repo.get_session()

    def seed_default_sources(self) -> int:
        """
        Seeds default official sources into the database if not already present.
        Idempotent: updates existing source definitions without duplicate entries.
        """
        session = self._get_session()
        should_close = (self._db is None)
        seeded_count = 0

        try:
            for seed in DEFAULT_SOURCE_SEEDS:
                existing = session.query(DiscoveredSourceRegistryModel).filter(
                    DiscoveredSourceRegistryModel.id == seed.id
                ).first()

                if not existing:
                    new_source = DiscoveredSourceRegistryModel(
                        id=seed.id,
                        name=seed.name,
                        source_type=seed.source_type.value,
                        base_url=seed.base_url,
                        discovery_endpoint=seed.discovery_endpoint,
                        discovery_method=seed.discovery_method.value,
                        polling_frequency_hours=seed.polling_frequency_hours,
                        health_status="healthy",
                        is_enabled=seed.is_enabled,
                        headers_config=seed.headers_config,
                    )
                    session.add(new_source)
                    seeded_count += 1
                else:
                    # Update configurable fields
                    existing.name = seed.name
                    existing.source_type = seed.source_type.value
                    existing.base_url = seed.base_url
                    existing.discovery_endpoint = seed.discovery_endpoint
                    existing.discovery_method = seed.discovery_method.value
                    existing.polling_frequency_hours = seed.polling_frequency_hours

            session.commit()
            return seeded_count
        except Exception:
            session.rollback()
            raise
        finally:
            if should_close:
                session.close()

    def list_sources(self, enabled_only: bool = False) -> List[DiscoveredSourceRegistryModel]:
        session = self._get_session()
        should_close = (self._db is None)
        try:
            query = session.query(DiscoveredSourceRegistryModel)
            if enabled_only:
                query = query.filter(DiscoveredSourceRegistryModel.is_enabled == True)
            return query.order_by(DiscoveredSourceRegistryModel.source_type, DiscoveredSourceRegistryModel.name).all()
        finally:
            if should_close:
                session.close()

    def get_source_by_id(self, source_id: str) -> Optional[DiscoveredSourceRegistryModel]:
        session = self._get_session()
        should_close = (self._db is None)
        try:
            return session.query(DiscoveredSourceRegistryModel).filter(
                DiscoveredSourceRegistryModel.id == source_id
            ).first()
        finally:
            if should_close:
                session.close()
