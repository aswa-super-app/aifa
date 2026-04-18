"""PDF extraction tools for AIFA.

Provides ADK-compatible tool functions for extracting text from PDF files
and structured data fields from Malaysian insurance/takaful documents.
"""

import os
import re

try:
    import PyPDF2
except ImportError:  # pragma: no cover
    PyPDF2 = None  # type: ignore[assignment]


# ---------------------------------------------------------------------------
# Low-level text extraction
# ---------------------------------------------------------------------------

def extract_text_from_pdf(pdf_path: str) -> dict:
    """Extract all text from a PDF file.

    Args:
        pdf_path: Absolute or relative path to the PDF file.

    Returns:
        A dict with keys:
          - ``text`` (str): Combined text of all pages.
          - ``page_count`` (int): Number of pages.
          - ``error`` (str | None): Error message if extraction failed.
    """
    if PyPDF2 is None:
        return {"text": "", "page_count": 0, "error": "PyPDF2 is not installed."}

    if not os.path.exists(pdf_path):
        return {
            "text": "",
            "page_count": 0,
            "error": f"File not found: {pdf_path}",
        }

    try:
        all_text = ""
        with open(pdf_path, "rb") as fh:
            reader = PyPDF2.PdfReader(fh)
            page_count = len(reader.pages)
            for page in reader.pages:
                page_text = page.extract_text() or ""
                all_text += page_text + "\n"
        return {"text": all_text.strip(), "page_count": page_count, "error": None}
    except Exception as exc:  # noqa: BLE001
        return {"text": "", "page_count": 0, "error": str(exc)}


# ---------------------------------------------------------------------------
# DocumentExtractor — regex-based field extraction
# ---------------------------------------------------------------------------

class DocumentExtractor:
    """Regex-based extractor for Malaysian insurance/takaful PDF documents.

    All ``extract_*`` methods accept ``text`` (the raw PDF text) and return
    the extracted value as a string, or ``None`` when not found.
    """

    def __init__(self) -> None:
        # ------------------------------------------------------------------
        # Date regex — handles multiple Malaysian/ISO date formats:
        #   DD-MM-YYYY, DD/MM/YYYY, DD.MM.YYYY, YYYY-MM-DD, YYYYMMDD,
        #   DD Mon YYYY
        # ------------------------------------------------------------------
        self._date_regex_string = (
            r"(\b\d{1,2}[-/.]\d{1,2}[-/.]\d{4}\b"
            r"|\b\d{1,2}[-/.]\d{1,2}[-/.]\d{2}\b"
            r"|\b\d{4}[-/.]\d{1,2}[-/.]\d{1,2}\b"
            r"|\b(?:19|20)\d{2}(?:0[1-9]|1[0-2])(?:0[1-9]|[1-2]\d|3[0-1])\b"
            r"|\b\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{4}\b)"
        )

        self.date_pattern = self._date_regex_string

        self.quotation_date_pattern = (
            r"(?:Quotation Date|Quote Date|Date of Quotation|Issued Date"
            r"|Date of Issue|Date Created|Effective Date|Date|On)\s*:?\s*"
            + self._date_regex_string
        )

        self.transaction_date_pattern = (
            r"(?:Transaction Date|Date|On)\s*:?\s*" + self._date_regex_string
        )

        # Period of Coverage — "Period … from DATE1 To DATE2"
        _inner = self._date_regex_string[1:-1]  # strip outer capturing group
        self.period_of_coverage_two_dates_pattern = (
            r"(?:Period of Coverage|Period of Takaful"
            r"|Effective date of Commence(?:ment)? of Takaful"
            r"|Date of Commencement)\s*(?:from)?\s*("
            + _inner
            + r")\s*(?:To)?\s*("
            + _inner
            + r")"
        )

        self.amount_pattern = (
            r"(?:RM|Total Contribution(?: \(RM\))?|Amount Due|Net Premium"
            r"|Total Amount|Total|Premium|Payment|Price|Value"
            r"|Final Premium|Gross Premium|Sum Insured):?\s*([\d,]+\.\d{2}|[\d,]+)"
        )

        self.sum_covered_pattern = (
            r"(?:Sum Covered|Coverage Amount|Sum Insured|Coverage Value"
            r"|Amount Insured|Total Sum Insured)\s*:?\s*(?:RM\s*)?([\d,]+\.\d{2}|[\d,]+)"
        )

        self.total_payable_pattern = (
            r"(?:Total Due|Takaful Contribution Payable|Total Payable"
            r"|Premium Payable|Contribution Amount|Policy Fee|Total Premium"
            r"|Total Charge|Total Payment|Total Amount Payable"
            r"|Total Amount Due|Amount)\s*:?\s*(?:RM\s*)?([\d,]+\.\d{2}|[\d,]+)"
        )

        self.participant_name_pattern = (
            r"(?:Name of\s*Participant|Insured Name|Customer Name|Client Name"
            r"|Policyholder Name|Name|Proposer Name|Applicant Name|Participant"
            r"|Insured Person|Proposed Insured|Applicant|Insured|Client):?\s*"
            r"([A-Za-z\s'-]+?)"
            r"(?=\n|\b[A-Z]{2,}\s*NO\.|\b[A-Z]{2,}\s*CODE"
            r"|\bVehicle Registration No\.|\bDate|\bIC No\.|\bAddress"
            r"|\bEmail|\bPhone|\bDOB|\bGender|\bNationality|\bEffective Date)"
        )

        self.ic_number_pattern = (
            r"(?:I/C No\.|NRIC No|ID No|NRIC NUMBER|IC NUMBER"
            r"|Identification No\.|Identity Card No\.|ID Card No\."
            r"|Identity No\.|IC|NRIC|IC / Business Passport / Other Number"
            r"|Identification Card No):?\s*(\d{6}-?\d{2}-?\d{4}|\d{12})"
        )

        self.insurance_company_pattern = (
            r"(TAKAFUL IKHLAS GENERAL BERHAD"
            r"|ETIQA GENERAL TAKAFUL BERHAD"
            r"|ZURICH GENERAL TAKAFUL BERHAD"
            r"|SYARIKAT TAKAFUL MALAYSIA AM BERHAD"
            r"|ETIQA FAMILY TAKAFUL BERHAD"
            r"|AMBANK GROUP"
            r"|ALLIANZ MALAYSIA BERHAD"
            r"|PRUDENTIAL BSN TAKAFUL BERHAD"
            r"|TOKIO MARINE INSURANS \(MALAYSIA\) BERHAD"
            r"|GENERAL INSURANCE BERHAD"
            r"|AIA BERHAD"
            r"|Insurance Expert|AI Agent)"
        )

        self.engine_no_pattern = r"\bEngine No\b\.?\s*:?\s*([A-Z0-9-]+)"
        self.chassis_no_pattern = r"\bChassis No\b\.?\s*:?\s*([A-Z0-9-]+)"

        self.client_address_pattern = (
            r"(?:Address|Alamat)\s*:?\s*([\s\S]+?)"
            r"(?=No Pendaftaran Perniagaan|Business Registration No"
            r"|Perkerjaan atau berniaga|Profession or Business"
            r"|Jenis Sijil|Class of Certificate"
            r"|IC / Business Passport / Other Number|Phone Number|SCHEDULE"
            r"|Effective Date|Make & Model of Vehicle|Name"
            r"|\b[A-Z]{2,}\s*NO\.|\b[A-Z]{2,}\s*CODE"
            r"|\bDate|\bIC No\.|\bAddress|\bEmail|\bPhone"
            r"|\bDOB|\bGender|\bNationality"
            r"|Endorsement Details|Policy Period|Vehicle Information"
            r"|Details of Insured|\Z)"
        )

    # ------------------------------------------------------------------
    # Public extract methods
    # ------------------------------------------------------------------

    def extract_policy_number(self, text: str) -> str | None:
        """Extract policy / certificate / quotation reference number."""
        # Payment slip pattern
        match = re.search(
            r"ASWA ADVISORY SDN BH\s*([A-Z0-9/\\-]+)", text, re.IGNORECASE
        )
        if match:
            return match.group(1).strip()

        pattern1 = (
            r"(?:Certificate No\.|Quotation Ref No\.|Quotation No\."
            r"|Quotation ID|Reference No\.|Quote No\.|Proposal No\."
            r"|Ref\.|Doc No\.|Policy No\.|Policy Number|Quote Reference"
            r"|Quotation Number|Reference Number|Policy Number)\s*:\s*([A-Z0-9/\\-]+)"
        )
        match = re.search(pattern1, text, re.IGNORECASE)
        if match:
            return match.group(1).strip()

        pattern2 = (
            r"(?:Certificate No|Quotation Ref No|Quotation No"
            r"|Quotation ID|Reference No|Quote No|Proposal No"
            r"|Ref|Doc No|Policy No|Policy Number|Quote Reference"
            r"|Quotation Number|Reference Number|Policy Number)\s+([A-Z0-9/\\-]+)"
        )
        match = re.search(pattern2, text, re.IGNORECASE)
        if match:
            return match.group(1).strip()

        match = re.search(r"qno=([A-Z0-9]+)", text, re.IGNORECASE)
        if match:
            return match.group(1).strip()

        return None

    def extract_dates(self, text: str) -> list[str]:
        """Extract all date strings found in the text."""
        return [m.strip() for m in re.findall(self.date_pattern, text) if m]

    def extract_quotation_date(self, text: str) -> str | None:
        match = re.search(self.quotation_date_pattern, text, re.IGNORECASE)
        return match.group(1).strip() if match else None

    def extract_transaction_date(self, text: str) -> str | None:
        match = re.search(self.transaction_date_pattern, text, re.IGNORECASE)
        return match.group(1).strip() if match else None

    def extract_period_of_coverage_dates(self, text: str) -> list[str | None] | None:
        """Return ``[start_date, end_date]`` or ``None``."""
        match = re.search(
            self.period_of_coverage_two_dates_pattern, text, re.IGNORECASE
        )
        if match:
            return [match.group(1).strip(), match.group(2).strip()]

        start_match = re.search(
            r"(?:Effective date of Commence(?:ment)? of Takaful"
            r" for the purposes of the Ordinance"
            r"|Date of Commencement|Effective Date):?\s*"
            + self._date_regex_string,
            text,
            re.IGNORECASE,
        )
        end_match = re.search(
            r"(?:Date of Expiry of Takaful|Date of Expiry):?\s*"
            + self._date_regex_string,
            text,
            re.IGNORECASE,
        )

        start_date = start_match.group(1).strip() if start_match else None
        end_date = end_match.group(1).strip() if end_match else None

        if start_date or end_date:
            return [start_date, end_date]
        return None

    def extract_sum_covered(self, text: str) -> str | None:
        match = re.search(self.sum_covered_pattern, text, re.IGNORECASE)
        return match.group(1).strip() if match else None

    def extract_total_payable(self, text: str) -> str | None:
        match = re.search(self.total_payable_pattern, text, re.IGNORECASE)
        return match.group(1).strip() if match else None

    def extract_participant_name(self, text: str) -> str | None:
        match = re.search(self.participant_name_pattern, text, re.IGNORECASE)
        return match.group(1).strip() if match else None

    def extract_ic_number(self, text: str) -> str | None:
        match = re.search(self.ic_number_pattern, text, re.IGNORECASE)
        return match.group(1).strip() if match else None

    def extract_insurance_company_name(self, text: str) -> str | None:
        match = re.search(
            self.insurance_company_pattern, text, re.IGNORECASE | re.MULTILINE
        )
        return match.group(1).strip() if match else None

    def extract_vehicle_registration_no(self, text: str) -> str | None:
        match = re.search(
            r"(?:Vehicle Reg No|Vehicle Registration No"
            r"|Registration No Vehicle|Registration No)\s*:\s*([A-Z0-9]+)",
            text,
            re.IGNORECASE,
        )
        if match:
            return match.group(1).strip()

        match = re.search(
            r"Index Mark and Vehicle Registration No\.\s*([A-Z0-9]+)",
            text,
            re.IGNORECASE,
        )
        return match.group(1).strip() if match else None

    def extract_make_type(self, text: str) -> str | None:
        make_match = re.search(
            r"Make\s*:\s*([A-Z0-9\s-]+?)(?=\s*Model\s*:|\s*Engine No"
            r"|\s*Chassis No|\s*Cover Type|\s*Vehicle Type"
            r"|\s*Year of Manufacture|\n|$)",
            text,
            re.IGNORECASE,
        )
        model_match = re.search(
            r"Model\s*:\s*([A-Z0-9\s-]+?)(?=\s*Engine No|\s*Chassis No"
            r"|\s*Cover Type|\s*Vehicle Type|\s*Year of Manufacture|\n|$)",
            text,
            re.IGNORECASE,
        )
        make = make_match.group(1).strip() if make_match else None
        model = model_match.group(1).strip() if model_match else None
        if make and model:
            return f"{make} {model}"
        return make or None

    def extract_engine_no(self, text: str) -> str | None:
        match = re.search(self.engine_no_pattern, text, re.IGNORECASE)
        return match.group(1).strip() if match else None

    def extract_chassis_no(self, text: str) -> str | None:
        match = re.search(self.chassis_no_pattern, text, re.IGNORECASE)
        return match.group(1).strip() if match else None

    def extract_client_address(self, text: str) -> str | None:
        match = re.search(self.client_address_pattern, text, re.IGNORECASE)
        if match:
            address = match.group(1).strip()
            if address.startswith(":"):
                address = address[1:].strip()
            address = re.sub(r"\s*\n\s*", ", ", address)
            address = re.sub(r",\s*,", ",", address)
            address = re.sub(r"\s+", " ", address).strip()
            if address.endswith(","):
                address = address[:-1].strip()
            return address

        # Fallback: look for address block after participant name
        fallback_match = re.search(
            r"Participant\s+[A-Z\s'-]+\n([\s\S]+?)(?=Certificate No\.|Account No\.)",
            text,
        )
        if fallback_match:
            block = fallback_match.group(1).strip()
            lines = [
                ln.strip()
                for ln in block.split("\n")
                if ln.strip()
                and not re.match(
                    r"^(?:[A-Z]{2,}\s*NO\.|\bDATE|\bIC|\bNRIC|\bPHONE|\bEMAIL)",
                    ln.strip(),
                    re.IGNORECASE,
                )
                and len(ln.split()) > 1
            ]
            address = ", ".join(lines)
            address = re.sub(r",\s*,", ",", address).strip()
            address = re.sub(r"\s+", " ", address).strip()
            if address.endswith(","):
                address = address[:-1].strip()
            return address or None

        return None

    def extract_all(self, text: str) -> dict:
        """Extract all fields from ``text`` and return as a dict."""
        period = self.extract_period_of_coverage_dates(text)
        coverage_start = period[0] if period and len(period) == 2 else None
        coverage_end = period[1] if period and len(period) == 2 else None

        return {
            "document_type": classify_document_type(text),
            "policy_number": self.extract_policy_number(text),
            "quotation_date": self.extract_quotation_date(text),
            "coverage_start_date": coverage_start,
            "coverage_end_date": coverage_end,
            "sum_covered": self.extract_sum_covered(text),
            "total_payable": self.extract_total_payable(text),
            "participant_name": self.extract_participant_name(text),
            "ic_number": self.extract_ic_number(text),
            "insurance_company": self.extract_insurance_company_name(text),
            "vehicle_registration_no": self.extract_vehicle_registration_no(text),
            "make_type": self.extract_make_type(text),
            "engine_no": self.extract_engine_no(text),
            "chassis_no": self.extract_chassis_no(text),
            "client_address": self.extract_client_address(text),
        }


# ---------------------------------------------------------------------------
# Document type classification
# ---------------------------------------------------------------------------

def classify_document_type(text: str) -> str:
    """Classify a document as Quotation, Policy, Receipt, Cover Note, etc.

    Classification is based on keyword signals in the raw PDF text.

    Args:
        text: Raw text extracted from a PDF.

    Returns:
        A human-readable document type string.
    """
    text_upper = text.upper()

    # Order matters — check more specific patterns first
    if re.search(r"\bCREDIT NOTE\b|\bCN\b", text_upper):
        return "Credit Note"
    if re.search(
        r"CERTIFICATE OF TAKAFUL|CERTIFICATE OF INSURANCE|E-POLICY|EPOLICY",
        text_upper,
    ):
        return "Policy / e-Policy"
    if re.search(r"MOTOR QUOTATION SLIP|QUOTATION SLIP|QUOTATION", text_upper):
        return "Quotation"
    if re.search(r"\bRECEIPT\b|\bPAYMENT RECEIPT\b", text_upper):
        return "Receipt"
    if re.search(r"\bCOVER NOTE\b|\bCOVERING NOTE\b", text_upper):
        return "Cover Note"
    if re.search(r"\bENDORSEMENT\b", text_upper):
        return "Endorsement"
    if re.search(r"\bINVOICE\b", text_upper):
        return "Invoice"
    if re.search(r"\bPROPOSAL FORM\b", text_upper):
        return "Proposal Form"
    return "Unknown"


# ---------------------------------------------------------------------------
# ADK tool wrappers (plain functions called by LlmAgent tools)
# ---------------------------------------------------------------------------

def extract_pdf_fields(pdf_path: str) -> dict:
    """Extract structured fields from a Malaysian insurance/takaful PDF.

    This is the main ADK tool function used by the document_processor agent.

    Args:
        pdf_path: Path to the PDF file on disk.

    Returns:
        A dict containing ``document_type``, ``policy_number``,
        ``quotation_date``, ``coverage_start_date``, ``coverage_end_date``,
        ``sum_covered``, ``total_payable``, ``participant_name``,
        ``ic_number``, ``insurance_company``, ``vehicle_registration_no``,
        ``make_type``, ``engine_no``, ``chassis_no``, ``client_address``,
        plus ``raw_text`` and ``error``.
    """
    result = extract_text_from_pdf(pdf_path)
    if result["error"]:
        return {"error": result["error"]}

    extractor = DocumentExtractor()
    fields = extractor.extract_all(result["text"])
    fields["raw_text"] = result["text"]
    fields["page_count"] = result["page_count"]
    fields["error"] = None
    return fields
