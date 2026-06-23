# app/main.py

import io

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.workflows.ba_workflow import execute
from app.services.document_parser import DocumentParser

app = FastAPI(
    title="BA Copilot API",
    version="1.0.0",
    description="Business Analysis automation powered by AI"
)

# ── CORS ──────────────────────────────────────────────────────────────────────
# Allow Streamlit (localhost:8501) and any local origin to call the API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Schemas ───────────────────────────────────────────────────────────────────
class DocumentRequest(BaseModel):
    document_text: str


# ── Routes ────────────────────────────────────────────────────────────────────
@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/analyze")
async def analyze(req: DocumentRequest):
    """Analyze plain text pasted by the user."""
    if not req.document_text.strip():
        raise HTTPException(status_code=400, detail="document_text is empty.")

    result = await execute(req.document_text)
    return result


@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    """
    Accept a PDF, DOCX, or TXT upload, parse it to text,
    then run the full BA workflow.
    """
    allowed = {".pdf", ".docx", ".txt"}
    import pathlib
    suffix = pathlib.Path(file.filename).suffix.lower()

    if suffix not in allowed:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{suffix}'. Allowed: {', '.join(allowed)}"
        )

    # Save the upload to a temp file so DocumentParser can read it
    import tempfile, shutil, os
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = tmp.name

    try:
        document_text = DocumentParser.parse(tmp_path)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    finally:
        os.unlink(tmp_path)

    if not document_text.strip():
        raise HTTPException(status_code=422, detail="Could not extract text from the uploaded file.")

    result = await execute(document_text)
    return result
