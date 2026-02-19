# 📄 Extrato PDF Parser

Open-source tool to extract transaction data from Brazilian bank statement PDFs.

## Supported Banks

| Bank | Status |
|------|--------|
| Itaú | ✅ Supported |
| Nubank | ✅ Supported |
| Banco Inter | ✅ Supported |

## Extracted Fields

- **Date** — Transaction date (DD/MM/YYYY)
- **Description** — Transaction description
- **Amount** — Value (positive = deposit, negative = withdrawal)
- **Transaction Type** — PIX, TED, FATURA, SALARIO, RENDIMENTO, TARIFA, etc.
- **Operation Type** — `deposit` or `withdrawal`

## Setup

### Prerequisites

- Python 3.11+
- Node.js 18+

### Backend

```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate    # Linux/Mac
# .venv\Scripts\activate     # Windows

# Install dependencies
pip install -e "backend[dev]"

# Run
cd backend
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:5173](http://localhost:5173)

### Running Tests

```bash
cd backend
../.venv/bin/python -m pytest tests/ -v
```

## How It Works

1. Upload a PDF bank statement through the web UI
2. The SvelteKit server forwards it to the Python backend
3. `pdfplumber` extracts text from the PDF
4. Bank is auto-detected from content keywords
5. Bank-specific parser extracts structured transaction data
6. Results are displayed in a table with export options

## Tech Stack

- **Backend**: Python, FastAPI, pdfplumber
- **Frontend**: SvelteKit, TypeScript
- **No external APIs** — all processing is local

## License

MIT
# pdf-file-to-google-sheets
