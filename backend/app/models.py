"""Unified transaction model for all bank parsers."""

from dataclasses import dataclass, asdict


@dataclass
class Transaction:
    date: str  # DD/MM/YYYY
    description: str
    amount: float  # negative = withdrawal, positive = deposit
    transaction_type: str  # PIX, TED, BOLETO, TARIFA, RENDIMENTO, SALARIO, etc.
    operation_type: str  # "deposit" or "withdrawal"
    bank: str  # "itau", "nubank", "inter"

    def to_dict(self) -> dict:
        return asdict(self)
