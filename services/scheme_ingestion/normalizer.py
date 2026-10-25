"""
Candidate Scheme Field Normalizer and Validator.
Analyzes extracted document passages, extracts candidate eligibility rules, financial benefits,
and required documents using auditable deterministic patterns, and preserves exact source clause citations.
"""

import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from services.scheme_ingestion.models import (
    CandidateBenefit,
    CandidateEligibilityCondition,
    CandidateSchemeRecord,
    ExtractedPassageSchema,
    SchemeStatus,
    SourceDocumentSchema,
)


class SchemeNormalizer:
    def __init__(self):
        pass

    def split_into_sentences(self, text: str) -> List[str]:
        """
        Splits passage text into coherent sentences/statements while protecting
        Indian currency abbreviations ('Rs.', '₹') and joining wrapped lines.
        """
        # Protect common abbreviations
        norm = re.sub(r"\bRs\.\s*", "Rs_DOT_", text)
        norm = re.sub(r"\be\.g\.\s*", "eg_DOT_", norm)
        norm = re.sub(r"\bi\.e\.\s*", "ie_DOT_", norm)

        # Un-wrap lines that do not start with a new bullet or clause
        norm = re.sub(r"(?<!\n)\n(?!\n|[0-9]+\.|\([a-z0-9]+\)|Clause|Section|Para|Rule)", " ", norm)

        # Split on sentence boundaries
        parts = re.split(r"(?<=[;:])\s+|\n{2,}|\.(?=\s+[A-Z]|\s*$)", norm)

        # Restore abbreviations
        sentences = [
            p.replace("Rs_DOT_", "Rs. ").replace("eg_DOT_", "e.g. ").replace("ie_DOT_", "i.e. ").strip()
            for p in parts
            if p.strip()
        ]
        return sentences

    def parse_currency_amount(self, text: str) -> Optional[float]:
        """
        Parses Indian currency text (e.g., 'Rs. 50 Lakh', 'Rs. 2.5 Crore', '₹10,00,000') into float INR.
        """
        # Crore pattern
        crore_match = re.search(r"(?:Rs\.?|INR|₹)?\s*([0-9]+(?:\.[0-9]+)?)\s*(?:Crore|Cr\.?|crores)", text, re.I)
        if crore_match:
            return float(crore_match.group(1)) * 10000000.0

        # Lakh pattern
        lakh_match = re.search(r"(?:Rs\.?|INR|₹)?\s*([0-9]+(?:\.[0-9]+)?)\s*(?:Lakh|Lakhs|Lacs|lac)", text, re.I)
        if lakh_match:
            return float(lakh_match.group(1)) * 100000.0

        # Thousand pattern
        thousand_match = re.search(r"(?:Rs\.?|INR|₹)?\s*([0-9]+(?:\.[0-9]+)?)\s*(?:Thousand|K)", text, re.I)
        if thousand_match:
            return float(thousand_match.group(1)) * 1000.0

        # Plain numeric currency e.g. Rs. 50,000
        num_match = re.search(r"(?:Rs\.?|INR|₹)\s*([0-9,]+(?:\.[0-9]+)?)", text, re.I)
        if num_match:
            clean_str = num_match.group(1).replace(",", "")
            try:
                return float(clean_str)
            except ValueError:
                pass

        return None

    def parse_percentage(self, text: str) -> Optional[float]:
        """Parses percentage numbers (e.g., '5%', '50% of cost', 'up to 75%')."""
        match = re.search(r"([0-9]+(?:\.[0-9]+)?)\s*%", text)
        if match:
            val = float(match.group(1))
            if 0.0 <= val <= 100.0:
                return val
        return None

    def extract_dates(self, full_text: str) -> Tuple[Optional[str], Optional[str]]:
        """Extracts effective date and expiry date from policy text."""
        effective_date = None
        expiry_date = None

        eff_match = re.search(
            r"(?:with effect from|effective from|comes into force on|date of notification|notification dated)\s*:?\s*([0-9]{1,2}[\.\-\/][0-9]{1,2}[\.\-\/][0-9]{2,4}|[0-9]{1,2}(?:st|nd|rd|th)?\s+[A-Za-z]+,?\s+[0-9]{4})",
            full_text,
            re.I
        )
        if eff_match:
            effective_date = eff_match.group(1).strip()

        exp_match = re.search(
            r"(?:valid up to|remain in force till|until|expires on)\s*:?\s*([0-9]{1,2}[\.\-\/][0-9]{1,2}[\.\-\/][0-9]{2,4}|[0-9]{1,2}(?:st|nd|rd|th)?\s+[A-Za-z]+,?\s+[0-9]{4})",
            full_text,
            re.I
        )
        if exp_match:
            expiry_date = exp_match.group(1).strip()

        return effective_date, expiry_date

    def extract_candidate_eligibility(
        self,
        passages: List[ExtractedPassageSchema]
    ) -> List[CandidateEligibilityCondition]:
        """
        Extracts structured eligibility conditions from passages with exact clause and page references.
        """
        conditions: List[CandidateEligibilityCondition] = []

        for passage in passages:
            current_clause = passage.section_heading or f"Page {passage.page_number}"
            sentences = self.split_into_sentences(passage.text_content)

            for clean_line in sentences:
                if len(clean_line) < 15:
                    continue

                clause_match = re.match(r"^(Clause|Section|Para|Rule)\s+([0-9\.\(\)\w]+)", clean_line, re.I)
                if clause_match:
                    current_clause = f"{clause_match.group(1)} {clause_match.group(2)}"

                # 1. Enterprise class eligibility
                if re.search(r"\b(Micro|Small|Medium)\s+Enterprises?\b", clean_line, re.I):
                    classes = []
                    if re.search(r"\bMicro\b", clean_line, re.I):
                        classes.append("micro")
                    if re.search(r"\bSmall\b", clean_line, re.I):
                        classes.append("small")
                    if re.search(r"\bMedium\b", clean_line, re.I):
                        classes.append("medium")
                    
                    if classes:
                        conditions.append(
                            CandidateEligibilityCondition(
                                attribute_name="enterprise_class",
                                operator="IN",
                                value=classes,
                                description=f"Enterprise must be categorized as {', '.join(classes)} under MSMED Act / Udyam.",
                                source_clause=current_clause,
                                source_page=passage.page_number,
                            )
                        )

                # 2. Sector / Industry eligibility
                if re.search(r"\b(Manufacturing|Service|Agro[- ]processing|Handloom|Handicrafts|Food Processing)\b", clean_line, re.I):
                    sector_match = re.findall(r"\b(Manufacturing|Service|Agro[- ]processing|Handloom|Handicrafts|Food Processing)\b", clean_line, re.I)
                    if sector_match:
                        sectors = list(set([s.lower() for s in sector_match]))
                        conditions.append(
                            CandidateEligibilityCondition(
                                attribute_name="sector",
                                operator="IN",
                                value=sectors,
                                description=f"Eligible industrial sectors include: {', '.join(sectors)}.",
                                source_clause=current_clause,
                                source_page=passage.page_number,
                            )
                        )

                # 3. Commencement of Commercial Production date
                if re.search(r"(?:commercial production|date of commencement|commenced production)", clean_line, re.I):
                    conditions.append(
                        CandidateEligibilityCondition(
                            attribute_name="production_status",
                            operator="=",
                            value="commenced",
                            description="Enterprise must have commenced commercial production or operation within the policy period.",
                            source_clause=current_clause,
                            source_page=passage.page_number,
                        )
                    )

                # 4. Mandatory Udyam Registration
                if re.search(r"\b(Udyam Registration|UAM|Udyog Aadhaar)\b", clean_line, re.I):
                    conditions.append(
                        CandidateEligibilityCondition(
                            attribute_name="udyam_registered",
                            operator="=",
                            value=True,
                            description="Enterprise must hold a valid Udyam Registration Certificate.",
                            source_clause=current_clause,
                            source_page=passage.page_number,
                        )
                    )

                # 5. Location / Odisha state presence
                if re.search(r"\b(situated in Odisha|located in Odisha|set up in the state|District Industries Centre)\b", clean_line, re.I):
                    conditions.append(
                        CandidateEligibilityCondition(
                            attribute_name="state",
                            operator="=",
                            value="Odisha",
                            description="Enterprise unit must be physically located within the State of Odisha.",
                            source_clause=current_clause,
                            source_page=passage.page_number,
                        )
                    )

        # Deduplicate conditions
        unique_conditions: List[CandidateEligibilityCondition] = []
        seen = set()
        for c in conditions:
            key = (c.attribute_name, c.operator, str(c.value))
            if key not in seen:
                seen.add(key)
                unique_conditions.append(c)

        return unique_conditions

    def extract_candidate_benefits(
        self,
        passages: List[ExtractedPassageSchema]
    ) -> List[CandidateBenefit]:
        """
        Extracts financial incentives, subsidies, percentage caps, and durations with clause references.
        """
        benefits: List[CandidateBenefit] = []

        for passage in passages:
            current_clause = passage.section_heading or f"Page {passage.page_number}"
            sentences = self.split_into_sentences(passage.text_content)

            for clean_line in sentences:
                if len(clean_line) < 20:
                    continue

                clause_match = re.match(r"^(Clause|Section|Para|Rule)\s+([0-9\.\(\)\w]+)", clean_line, re.I)
                if clause_match:
                    current_clause = f"{clause_match.group(1)} {clause_match.group(2)}"

                # Detect benefit sentences containing subsidy, reimbursement, or exemption
                if re.search(r"\b(subsidy|reimbursement|exemption|subvention|assistance|grant)\b", clean_line, re.I):
                    pct = self.parse_percentage(clean_line)
                    limit_inr = self.parse_currency_amount(clean_line)
                    
                    # Duration in years
                    dur_match = re.search(r"([0-9]+)\s*(?:years?|yrs)", clean_line, re.I)
                    duration = int(dur_match.group(1)) if dur_match else None

                    # Classify benefit type
                    b_type = "financial_assistance"
                    if "interest" in clean_line.lower():
                        b_type = "interest_subsidy"
                    elif "patent" in clean_line.lower():
                        b_type = "patent_registration_subsidy"
                    elif "trade mark" in clean_line.lower() or "trademark" in clean_line.lower():
                        b_type = "trademark_assistance"
                    elif "technology" in clean_line.lower():
                        b_type = "technology_purchase_subsidy"
                    elif "quality certification" in clean_line.lower() or "iso" in clean_line.lower():
                        b_type = "quality_certification_subsidy"
                    elif "stamp duty" in clean_line.lower():
                        b_type = "stamp_duty_exemption"
                    elif "capital" in clean_line.lower() or "investment" in clean_line.lower():
                        b_type = "capital_investment_subsidy"

                    if pct is not None or limit_inr is not None or "reimbursement" in clean_line.lower():
                        benefits.append(
                            CandidateBenefit(
                                benefit_type=b_type,
                                formula_description=clean_line[:240],
                                subsidy_percentage=pct,
                                max_limit_inr=limit_inr,
                                duration_years=duration,
                                source_clause=current_clause,
                                source_page=passage.page_number,
                            )
                        )

        # Deduplicate benefits
        unique_benefits: List[CandidateBenefit] = []
        seen = set()
        for b in benefits:
            key = (b.benefit_type, b.subsidy_percentage, b.max_limit_inr)
            if key not in seen:
                seen.add(key)
                unique_benefits.append(b)

        return unique_benefits

    def extract_required_documents(
        self,
        passages: List[ExtractedPassageSchema]
    ) -> List[str]:
        """Extracts required documents and application checklist items."""
        docs: List[str] = []
        doc_patterns = [
            (r"Udyam\s+Registration(?:\s+Certificate)?", "Udyam Registration Certificate"),
            (r"Detailed\s+Project\s+Report|DPR", "Detailed Project Report (DPR)"),
            (r"Bank\s+Sanction\s+Letter|Loan\s+Sanction\s+Letter", "Term Loan / Bank Sanction Letter"),
            (r"Chartered\s+Accountant\s+Certificate|CA\s+Certificate", "Statutory Auditor / Chartered Accountant Certificate"),
            (r"Land\s+Allotment|Sale\s+Deed|Lease\s+Deed|Rent\s+Agreement", "Land Ownership / Lease Agreement"),
            (r"Consent\s+to\s+Establish|Consent\s+to\s+Operate|OSPCB", "Pollution Control Board Clearance (CTE / CTO)"),
            (r"Electricity\s+Bill|Power\s+Connection", "Electricity Connection / Tariff Bill"),
            (r"Aadhaar\s+(?:Card|Number)?", "Aadhaar of Promoter / Managing Partner"),
            (r"PAN\s+(?:Card)?", "PAN Card of Enterprise / Promoter"),
            (r"Patent\s+(?:Filing|Grant)\s+Receipt", "Patent Application Receipt / Grant Certificate"),
            (r"Trademark\s+Registration\s+Certificate", "Trademark Registration Certificate"),
            (r"Invoices?\s+and\s+Receipts?|Vouchers?", "Machinery / Technology Invoices and Payment Receipts"),
        ]

        full_text = "\n".join([p.text_content for p in passages])
        for pattern, doc_name in doc_patterns:
            if re.search(pattern, full_text, re.I):
                docs.append(doc_name)

        return list(dict.fromkeys(docs))

    def normalize(
        self,
        doc_schema: SourceDocumentSchema,
        passages: List[ExtractedPassageSchema]
    ) -> CandidateSchemeRecord:
        """
        Compiles extracted passages into a validated candidate scheme record.
        Status is set to PENDING_REVIEW; never published automatically without human review.
        """
        full_text = "\n".join([p.text_content for p in passages])

        title = doc_schema.title
        for p in passages[:3]:
            for line in p.text_content.split("\n")[:10]:
                line_str = line.strip()
                if 20 < len(line_str) < 140 and any(
                    k in line_str.lower()
                    for k in ["scheme", "guidelines", "policy", "assistance", "subsidy"]
                ):
                    title = line_str
                    break
            if title != doc_schema.title:
                break

        effective_date, expiry_date = self.extract_dates(full_text)
        candidate_conditions = self.extract_candidate_eligibility(passages)
        candidate_benefits = self.extract_candidate_benefits(passages)
        required_docs = self.extract_required_documents(passages)

        official_portal = None
        portal_matches = re.findall(
            r"https?://(?:odishamsme\.nic\.in|goswift\.odisha\.gov.in|msme\.odisha\.gov\.in|myscheme\.gov\.in)[\w\/\.\-]+",
            full_text
        )
        if portal_matches:
            official_portal = portal_matches[0]
        else:
            official_portal = "https://msme.odisha.gov.in"

        clean_intro = " ".join([p.text_content.replace("\n", " ").strip() for p in passages[:2]])
        summary = clean_intro[:600].strip() + ("..." if len(clean_intro) > 600 else "")

        scheme_record = CandidateSchemeRecord(
            official_name=title,
            department="Department of MSME, Government of Odisha",
            implementing_agency="Directorate of Industries, Odisha / District Industries Centres (DICs)",
            jurisdiction="Odisha",
            source_url=doc_schema.source_url,
            source_document_id=doc_schema.document_id,
            document_sha256=doc_schema.sha256_hash,
            summary=summary,
            status=SchemeStatus.PENDING_REVIEW,
            version="1.0",
            effective_date=effective_date,
            expiry_date=expiry_date,
            candidate_eligibility=candidate_conditions,
            candidate_benefits=candidate_benefits,
            required_documents=required_docs,
            application_process="Apply online through the Single Window Portal (Go-SWIFT) or submit to the General Manager, District Industries Centre (DIC).",
            official_portal_url=official_portal,
        )

        return scheme_record
