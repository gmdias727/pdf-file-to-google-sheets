"""Parser for Nubank bank statements."""

import re
from app.models import Transaction


# Month abbreviation mapping (Portuguese)
_MONTHS_PT = {
    "JAN": "01", "FEV": "02", "MAR": "03", "ABR": "04",
    "MAI": "05", "JUN": "06", "JUL": "07", "AGO": "08",
    "SET": "09", "OUT": "10", "NOV": "11", "DEZ": "12",
}

# Matches date headers like "14 FEV 2026" (possibly followed by more text)
_DATE_HEADER_RE = re.compile(
    r"^(\d{1,2})\s+(JAN|FEV|MAR|ABR|MAI|JUN|JUL|AGO|SET|OUT|NOV|DEZ)\s+(\d{4})",
    re.IGNORECASE,
)

# Matches a transaction line ending with an amount like " 30,00" or " 83,25"
_AMOUNT_TRAIL_RE = re.compile(r"^(.+?)\s+([\d]+(?:[.,]\d+)*)\s*$")

# Footer / legal text keywords to skip
_SKIP_KEYWORDS = [
    "nu financeira", "nu pagamentos", "cnpj", "mande uma mensagem",
    "ouvidoria", "extrato gerado", "saldo líquido", "não nos responsabilizamos",
    "asseguramos", "4020 0185", "0800", "metropolitanas", "investimento pagamento",
    "disponíveis em", "sociedade de credito",
]


def _parse_amount(value_str: str) -> float:
    """Parse Brazilian currency string."""
    cleaned = value_str.strip().replace(".", "").replace(",", ".")
    return float(cleaned)


def _infer_transaction_type(description: str) -> str:
    """Infer transaction type from Nubank description."""
    desc_lower = description.lower()

    if "pix" in desc_lower or "transferência" in desc_lower:
        return "PIX"
    elif "pagamento de fatura" in desc_lower:
        return "FATURA"
    elif "rendimento" in desc_lower:
        return "RENDIMENTO"
    elif "compra no débito" in desc_lower:
        return "DEBITO"
    elif "estorno" in desc_lower or "devolução" in desc_lower:
        return "ESTORNO"
    else:
        return "OUTRO"


def _infer_operation(description: str, amount: float) -> tuple[str, float]:
    """
    Determine if a transaction is a deposit or withdrawal.
    Nubank shows amounts as positive; we use the description to decide sign.
    """
    desc_lower = description.lower()

    # Incoming money
    if any(kw in desc_lower for kw in ["recebid", "estorno", "devolução"]):
        return "deposit", abs(amount)

    # Outgoing money
    return "withdrawal", -abs(amount)


def parse_nubank(text: str) -> list[Transaction]:
    """Parse full text from a Nubank bank statement PDF.

    Nubank statements have the following structure after "Movimentações":
      - Date headers: "DD MMM YYYY"
      - Transaction lines ending with an amount: "Description 30,00"
      - Continuation lines (bank details) that belong to the PREVIOUS
        transaction — we simply discard these since they're metadata.
    """
    transactions: list[Transaction] = []
    current_date: str | None = None
    in_movements = False

    lines = text.split("\n")

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Start collecting after "Movimentações"
        if "Movimentações" in line:
            in_movements = True
            continue

        if not in_movements:
            continue

        # Skip footer/legal text
        if any(kw in line.lower() for kw in _SKIP_KEYWORDS):
            continue

        # Skip summary lines
        if line.startswith("Total de entradas") or line.startswith("Total de saídas"):
            continue

        # Check for date header (may have trailing text)
        date_match = _DATE_HEADER_RE.match(line)
        if date_match:
            day = date_match.group(1).zfill(2)
            month = _MONTHS_PT[date_match.group(2).upper()]
            year = date_match.group(3)
            current_date = f"{day}/{month}/{year}"
            continue

        if current_date is None:
            continue

        # Try to match a line ending with an amount
        amount_match = _AMOUNT_TRAIL_RE.match(line)
        if not amount_match:
            # This is a continuation line (e.g., bank details for the
            # previous transaction). We discard it since the main
            # transaction description is already captured.
            continue

        description = amount_match.group(1).strip()
        amount_str = amount_match.group(2)

        try:
            raw_amount = _parse_amount(amount_str)
        except ValueError:
            continue

        tx_type = _infer_transaction_type(description)
        operation, signed_amount = _infer_operation(description, raw_amount)

        transactions.append(Transaction(
            date=current_date,
            description=description,
            amount=signed_amount,
            transaction_type=tx_type,
            operation_type=operation,
            bank="nubank",
        ))

    return transactions
