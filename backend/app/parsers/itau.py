"""Parser for Itaú bank statements (Extrato Conta / Lançamentos)."""

import re
from app.models import Transaction


def _parse_amount(value_str: str) -> float:
    """Parse Brazilian currency string like '-1.883,12' to float."""
    cleaned = value_str.strip()
    cleaned = cleaned.replace(".", "").replace(",", ".")
    return float(cleaned)


def _infer_transaction_type(description: str) -> str:
    """Infer transaction type from Itaú description keywords."""
    desc_upper = description.upper()

    if desc_upper.startswith("PIX TRANSF"):
        return "PIX"
    elif desc_upper.startswith("PIX QRS"):
        return "PIX"
    elif desc_upper.startswith("DEV PIX"):
        return "PIX_DEVOLUCAO"
    elif "FATURA PAGA" in desc_upper:
        return "FATURA"
    elif "REND PAGO APLIC" in desc_upper or "REMUNERACAO" in desc_upper:
        return "RENDIMENTO"
    elif "REMUNERACAO/SALARIO" in desc_upper or "SISPAG" in desc_upper:
        return "SALARIO"
    elif desc_upper.startswith("TAR "):
        return "TARIFA"
    elif "TED" in desc_upper:
        return "TED"
    elif "DOC" in desc_upper:
        return "DOC"
    else:
        return "OUTRO"


# Matches lines like: DD/MM/YYYY DESCRIPTION VALUE
# where VALUE looks like -1.883,12 or 2.546,68
_TRANSACTION_LINE_RE = re.compile(
    r"^(\d{2}/\d{2}/\d{4})\s+"  # date
    r"(.+?)\s+"                  # description (non-greedy)
    r"(-?[\d.,]+)$"              # amount
)


def parse_itau(text: str) -> list[Transaction]:
    """Parse full text from an Itaú bank statement PDF."""
    transactions: list[Transaction] = []

    for line in text.split("\n"):
        line = line.strip()
        if not line:
            continue

        # Skip balance lines (SALDO DO DIA)
        if "SALDO DO DIA" in line:
            continue

        match = _TRANSACTION_LINE_RE.match(line)
        if not match:
            continue

        date_str = match.group(1)
        description = match.group(2).strip()
        amount_str = match.group(3)

        try:
            amount = _parse_amount(amount_str)
        except ValueError:
            continue

        # Determine transaction type - re-check for salary since
        # _infer_transaction_type checks for SISPAG too
        tx_type = _infer_transaction_type(description)

        # Override: if REMUNERACAO/SALARIO is in desc, it's salary
        if "REMUNERACAO/SALARIO" in description.upper():
            tx_type = "SALARIO"

        operation = "deposit" if amount >= 0 else "withdrawal"

        transactions.append(Transaction(
            date=date_str,
            description=description,
            amount=amount,
            transaction_type=tx_type,
            operation_type=operation,
            bank="itau",
        ))

    return transactions
