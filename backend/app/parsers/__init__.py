"""
Bank statement PDF parsers.

Auto-detects the bank from PDF content and routes to the correct parser.
"""

from app.parsers.itau import parse_itau
from app.parsers.nubank import parse_nubank
from app.parsers.inter import parse_inter
from app.models import Transaction

import pdfplumber


def detect_bank(text: str) -> str:
    """Detect bank from the first page text content.

    Order matters: Nubank and Inter PDFs can mention "Itaú" in transaction
    descriptions, so we check for their distinctive keywords first.
    """
    text_lower = text.lower()

    # Check Nubank first — their PDFs always contain "Nu Financeira" or "Nu Pagamentos"
    if "nu financeira" in text_lower or "nu pagamentos" in text_lower or "nubank" in text_lower:
        return "nubank"
    elif "banco inter" in text_lower:
        return "inter"
    elif "itaú" in text_lower or "itau" in text_lower:
        return "itau"
    else:
        raise ValueError(
            "Could not detect bank from PDF content. "
            "Supported banks: Itaú, Nubank, Banco Inter."
        )


def parse_pdf(file_bytes: bytes) -> list[Transaction]:
    """Parse a bank statement PDF and return a list of transactions."""
    import io

    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        if not pdf.pages:
            raise ValueError("PDF has no pages.")

        # Gather all text for bank detection
        first_page_text = pdf.pages[0].extract_text() or ""
        bank = detect_bank(first_page_text)

        # Gather full text from all pages
        full_text = "\n".join(
            page.extract_text() or "" for page in pdf.pages
        )

        if bank == "itau":
            return parse_itau(full_text)
        elif bank == "nubank":
            return parse_nubank(full_text)
        elif bank == "inter":
            return parse_inter(full_text)
        else:
            raise ValueError(f"No parser for bank: {bank}")
