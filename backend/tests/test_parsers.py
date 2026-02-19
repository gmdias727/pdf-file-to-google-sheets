"""Tests for bank statement PDF parsers."""

import os
import pytest
import sys

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.parsers import parse_pdf, detect_bank
from app.models import Transaction

# Paths to test PDF files (in project root)
PROJECT_ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
ITAU_PDF = os.path.join(PROJECT_ROOT, "banco-itau_extrato_012026.pdf")
NUBANK_PDF = os.path.join(PROJECT_ROOT, "banco-NU_279929924_01FEV2026_17FEV2026.pdf")
INTER_PDF = os.path.join(PROJECT_ROOT, "banco-inter-Extrato-01-02-2026-a-18-02-2026-PDF.pdf")


def _read_pdf(path: str) -> bytes:
    with open(path, "rb") as f:
        return f.read()


# ──────────────────────────────────────────────
# Bank Detection Tests
# ──────────────────────────────────────────────

class TestBankDetection:
    def test_detects_itau(self):
        data = _read_pdf(ITAU_PDF)
        import pdfplumber, io
        with pdfplumber.open(io.BytesIO(data)) as pdf:
            text = pdf.pages[0].extract_text() or ""
        assert detect_bank(text) == "itau"

    def test_detects_nubank(self):
        data = _read_pdf(NUBANK_PDF)
        import pdfplumber, io
        with pdfplumber.open(io.BytesIO(data)) as pdf:
            text = pdf.pages[0].extract_text() or ""
        assert detect_bank(text) == "nubank"

    def test_detects_inter(self):
        data = _read_pdf(INTER_PDF)
        import pdfplumber, io
        with pdfplumber.open(io.BytesIO(data)) as pdf:
            text = pdf.pages[0].extract_text() or ""
        assert detect_bank(text) == "inter"

    def test_unknown_bank_raises(self):
        with pytest.raises(ValueError, match="Could not detect bank"):
            detect_bank("This is just some random text with no bank info.")


# ──────────────────────────────────────────────
# Itaú Parser Tests
# ──────────────────────────────────────────────

class TestItauParser:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.transactions = parse_pdf(_read_pdf(ITAU_PDF))

    def test_extracts_transactions(self):
        assert len(self.transactions) > 50

    def test_all_are_itau(self):
        for tx in self.transactions:
            assert tx.bank == "itau"

    def test_transaction_fields(self):
        tx = self.transactions[0]
        assert tx.date == "18/02/2026"
        assert "PIX TRANSF" in tx.description
        assert tx.amount == -30.00
        assert tx.transaction_type == "PIX"
        assert tx.operation_type == "withdrawal"

    def test_deposit_detection(self):
        deposits = [tx for tx in self.transactions if tx.operation_type == "deposit"]
        assert len(deposits) > 0
        for tx in deposits:
            assert tx.amount > 0

    def test_salary_detection(self):
        salaries = [tx for tx in self.transactions if tx.transaction_type == "SALARIO"]
        assert len(salaries) > 0

    def test_no_balance_rows(self):
        """SALDO DO DIA lines should be filtered out."""
        for tx in self.transactions:
            assert "SALDO DO DIA" not in tx.description


# ──────────────────────────────────────────────
# Nubank Parser Tests
# ──────────────────────────────────────────────

class TestNubankParser:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.transactions = parse_pdf(_read_pdf(NUBANK_PDF))

    def test_extracts_transactions(self):
        assert len(self.transactions) == 2

    def test_all_are_nubank(self):
        for tx in self.transactions:
            assert tx.bank == "nubank"

    def test_pix_received(self):
        pix_tx = [tx for tx in self.transactions if "Transferência recebida" in tx.description]
        assert len(pix_tx) == 1
        assert pix_tx[0].amount == 30.00
        assert pix_tx[0].operation_type == "deposit"
        assert pix_tx[0].transaction_type == "PIX"

    def test_fatura_payment(self):
        fatura_tx = [tx for tx in self.transactions if tx.transaction_type == "FATURA"]
        assert len(fatura_tx) == 1
        assert fatura_tx[0].amount == -83.25
        assert fatura_tx[0].operation_type == "withdrawal"


# ──────────────────────────────────────────────
# Banco Inter Parser Tests
# ──────────────────────────────────────────────

class TestInterParser:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.transactions = parse_pdf(_read_pdf(INTER_PDF))

    def test_extracts_transactions(self):
        assert len(self.transactions) == 16

    def test_all_are_inter(self):
        for tx in self.transactions:
            assert tx.bank == "inter"

    def test_pix_sent(self):
        pix_sent = [tx for tx in self.transactions if "Pix enviado" in tx.description]
        assert len(pix_sent) > 0
        for tx in pix_sent:
            assert tx.amount < 0
            assert tx.operation_type == "withdrawal"

    def test_pix_received(self):
        pix_recv = [tx for tx in self.transactions if "Pix recebido" in tx.description]
        assert len(pix_recv) > 0
        for tx in pix_recv:
            assert tx.amount > 0
            assert tx.operation_type == "deposit"

    def test_investment(self):
        investments = [tx for tx in self.transactions if tx.transaction_type == "INVESTIMENTO"]
        assert len(investments) == 2

    def test_date_format(self):
        for tx in self.transactions:
            assert len(tx.date) == 10  # DD/MM/YYYY
            assert tx.date[2] == "/" and tx.date[5] == "/"


# ──────────────────────────────────────────────
# Transaction Model Tests
# ──────────────────────────────────────────────

class TestTransactionModel:
    def test_to_dict(self):
        tx = Transaction(
            date="01/01/2026",
            description="Test",
            amount=-10.0,
            transaction_type="PIX",
            operation_type="withdrawal",
            bank="itau",
        )
        d = tx.to_dict()
        assert d["date"] == "01/01/2026"
        assert d["amount"] == -10.0
        assert d["bank"] == "itau"
