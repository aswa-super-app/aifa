"""Data cleaning utilities for AIFA.

These functions normalise the raw strings returned by DocumentExtractor
before they are stored or presented to users.
"""

import re


def clean_participant_name(name: str | None) -> str | None:
    """Normalise a participant/insured name string.

    - Strips leading/trailing whitespace and internal repeated spaces.
    - Removes common honorific prefixes that may be captured by the regex
      (e.g. "Name of Participant:").
    - Returns ``None`` when the input is ``None`` or an empty string.

    Args:
        name: Raw name string from :class:`~aifa.tools.pdf_extractor.DocumentExtractor`.

    Returns:
        Cleaned name string, or ``None``.
    """
    if not name:
        return None

    # Remove leading label artefacts
    name = re.sub(
        r"^(?:Name of\s*Participant|Insured Name|Customer Name|Client Name"
        r"|Policyholder Name|Name|Proposer Name|Applicant Name|Participant"
        r"|Insured Person|Proposed Insured|Applicant|Insured|Client)\s*:?\s*",
        "",
        name,
        flags=re.IGNORECASE,
    )

    # Collapse whitespace (including tabs and newlines)
    name = re.sub(r"\s+", " ", name).strip()

    # Remove stray punctuation at the end (colon, semicolon, comma)
    name = name.rstrip(":;,")

    return name if name else None


def clean_make_type(make_type: str | None) -> str | None:
    """Normalise a vehicle make-and-model string.

    - Strips whitespace and collapses internal runs of spaces.
    - Uppercases the result for consistency.
    - Returns ``None`` when the input is ``None`` or empty.

    Args:
        make_type: Raw make/type string from
            :class:`~aifa.tools.pdf_extractor.DocumentExtractor`.

    Returns:
        Cleaned make-and-model string (uppercase), or ``None``.
    """
    if not make_type:
        return None

    make_type = re.sub(r"\s+", " ", make_type).strip().upper()
    return make_type if make_type else None


def clean_client_address(address: str | None) -> str | None:
    """Normalise a client address string.

    - Strips leading/trailing whitespace.
    - Collapses internal runs of spaces.
    - Replaces double-comma artefacts with a single comma.
    - Removes a trailing comma if present.
    - Returns ``None`` when the input is ``None`` or empty.

    Args:
        address: Raw address string from
            :class:`~aifa.tools.pdf_extractor.DocumentExtractor`.

    Returns:
        Cleaned address string, or ``None``.
    """
    if not address:
        return None

    # Normalise newlines to comma-space
    address = re.sub(r"\s*\n\s*", ", ", address)

    # Collapse repeated whitespace
    address = re.sub(r"\s+", " ", address).strip()

    # Remove double-comma artefacts
    address = re.sub(r",\s*,", ", ", address)

    # Strip trailing comma
    if address.endswith(","):
        address = address[:-1].strip()

    return address if address else None


def clean_ic_number(ic_number: str | None) -> str | None:
    """Normalise a Malaysian IC number to ``YYMMDD-XX-XXXX`` format.

    Accepts both hyphenated and plain 12-digit formats and converts to the
    standard hyphenated representation.

    Args:
        ic_number: Raw IC number string.

    Returns:
        Hyphenated IC number string, or ``None``.
    """
    if not ic_number:
        return None

    # Remove existing hyphens then reformat
    digits = re.sub(r"[^0-9]", "", ic_number)
    if len(digits) == 12:
        return f"{digits[:6]}-{digits[6:8]}-{digits[8:]}"

    return ic_number.strip() if ic_number.strip() else None


def clean_currency_amount(amount: str | None) -> str | None:
    """Normalise a Malaysian Ringgit amount string.

    Strips surrounding whitespace and ensures the format is ``x,xxx.xx``.

    Args:
        amount: Raw amount string (may include "RM" prefix or commas).

    Returns:
        Cleaned numeric string without currency symbol, or ``None``.
    """
    if not amount:
        return None

    # Remove currency symbols and excess whitespace
    amount = re.sub(r"[RrMm\s]", "", amount).strip()
    return amount if amount else None
