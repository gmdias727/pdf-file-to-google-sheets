"""Parser for Banco Inter bank statements."""

import re
from app.models import Transaction


# Month name mapping (Portuguese, full names)
_MONTHS_PT_FULL = {
    "janeiro": "01", "fevereiro": "02", "março": "03", "abril": "04",
    "maio": "05", "junho": "06", "julho": "07", "agosto": "08",
    "setembro": "09", "outubro": "10", "novembro": "11", "dezembro": "12",
}

# Matches date headers like "1 de Fevereiro de 2026"
_DATE_HEADER_RE = re.compile(
    r"^(\d{1,2})\s+de\s+(\w+)\s+de\s+(\d{4})",
    re.IGNORECASE,
)

# Matches transaction lines like:
# Pix enviado: "Cp :44815065-PAY2ALL INSTITUICAO DE PAGAMENTO LTDA" -R$ 44,99 -R$ 29,86
# Pix recebido: "Cp :60701190-GABRIEL DIAS MAZIERI" R$ 250,00 R$ 182,74
# Aplicacao: "LCI PRE 180 BANCO INTER SA" -R$ 55,00 R$ 33,31
_TRANSACTION_RE = re.compile(
    r'^(.+?):\s+"(.+?)"\s+(-?)R\$\s*([\d.,]+)\s+(-?)R\$\s*([\d.,]+)$'
)


def _parse_amount(value_str: str) -> float:
    """Parse Brazilian currency string."""
    cleaned = value_str.strip().replace(".", "").replace(",", ".")
    return float(cleaned)


def _infer_transaction_type(action: str) -> str:
    """Infer transaction type from the action prefix."""
    action_lower = action.strip().lower()

    if "pix" in action_lower:
        return "PIX"
    elif "aplicacao" in action_lower or "aplicação" in action_lower:
        return "INVESTIMENTO"
    elif "resgate" in action_lower:
        return "RESGATE"
    elif "ted" in action_lower:
        return "TED"
    elif "boleto" in action_lower:
        return "BOLETO"
    elif "rendimento" in action_lower:
        return "RENDIMENTO"
    elif "tarifa" in action_lower or "taxa" in action_lower:
        return "TARIFA"
    else:
        return "OUTRO"


def parse_inter(text: str) -> list[Transaction]:
    """Parse full text from a Banco Inter bank statement PDF."""
    transactions: list[Transaction] = []
    current_date: str | None = None

    for line in text.split("\n"):
        line = line.strip()
        if not line:
            continue

        # Check for date header
        date_match = _DATE_HEADER_RE.match(line)
        if date_match:
            day = date_match.group(1).zfill(2)
            month_name = date_match.group(2).lower()
            year = date_match.group(3)

            month_num = _MONTHS_PT_FULL.get(month_name)
            if month_num:
                current_date = f"{day}/{month_num}/{year}"
            continue

        if current_date is None:
            continue

        # Try to match a transaction line
        tx_match = _TRANSACTION_RE.match(line)
        if not tx_match:
            continue

        action = tx_match.group(1).strip()        # e.g. "Pix enviado"
        description = tx_match.group(2).strip()    # e.g. "Cp :44815065-PAY2ALL..."
        sign = tx_match.group(3)                   # "-" or ""
        amount_str = tx_match.group(4)             # e.g. "44,99"

        try:
            amount = _parse_amount(amount_str)
        except ValueError:
            continue

        if sign == "-":
            amount = -amount

        tx_type = _infer_transaction_type(action)
        operation = "deposit" if amount >= 0 else "withdrawal"

        # Build a cleaner description combining action and target
        clean_desc = f"{action}: {description}"

        transactions.append(Transaction(
            date=current_date,
            description=clean_desc,
            amount=amount,
            transaction_type=tx_type,
            operation_type=operation,
            bank="inter",
        ))

    return transactions
