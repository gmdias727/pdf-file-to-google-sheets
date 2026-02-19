"""FastAPI app for PDF bank statement parsing."""

from fastapi import FastAPI, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.parsers import parse_pdf

app = FastAPI(
    title="PDF Extrato Parser",
    description="Parse Brazilian bank statement PDFs into structured transaction data",
    version="0.1.0",
)

# Allow SvelteKit dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:4173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/api/parse")
async def parse_statement(file: UploadFile):
    """
    Upload a bank statement PDF and get structured transaction data back.

    Returns a JSON object with:
    - bank: detected bank name
    - transactions: list of transaction objects
    - total_transactions: count of transactions
    """
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted.")

    contents = await file.read()

    if len(contents) == 0:
        raise HTTPException(status_code=400, detail="Empty file.")

    try:
        transactions = parse_pdf(contents)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error parsing PDF: {str(e)}")

    bank = transactions[0].bank if transactions else "unknown"

    return {
        "bank": bank,
        "transactions": [t.to_dict() for t in transactions],
        "total_transactions": len(transactions),
    }


@app.get("/api/health")
async def health():
    return {"status": "ok"}
