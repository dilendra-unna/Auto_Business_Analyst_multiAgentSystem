# app/main.py

import json
import os
import pathlib
import shutil
import tempfile

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.agents import requirement_agent, story_agent, testcase_agent, review_agent
from app.services.document_parser import DocumentParser
from app.workflows.ba_workflow import execute

# ── App ────────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="BA Copilot API",
    version="1.0.0",
    description="Business Analysis automation powered by AI",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt"}

MERGE_SEPARATOR = (
    "\n\n"
    "=" * 60 + "\n"
    "ADDITIONAL REQUIREMENTS (typed by analyst)\n"
    "=" * 60 + "\n\n"
)


# ── Schemas ────────────────────────────────────────────────────────────────────

class DocumentRequest(BaseModel):
    document_text: str


class ElaborateRequest(BaseModel):
    requirement: dict
    extra_context: str = ""


# ── SSE helper ─────────────────────────────────────────────────────────────────

def sse_event(event: str, data: dict) -> str:
    """Format a Server-Sent Event frame."""
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


# ── Merge helper ───────────────────────────────────────────────────────────────

def merge_texts(document_text: str, extra_text: str) -> str:
    """
    Merge parsed document text with analyst-typed text.
    Either part may be empty — returns whichever is non-empty, or both joined
    with a clear separator so the LLM can distinguish the sources.
    """
    doc   = (document_text or "").strip()
    extra = (extra_text or "").strip()

    if doc and extra:
        return doc + MERGE_SEPARATOR + extra
    return doc or extra


# ── Routes ─────────────────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/analyze")
async def analyze(req: DocumentRequest):
    """
    Analyze plain text submitted by the user.
    The client is responsible for merging document text + typed text
    before calling this endpoint (the frontend does this).
    """
    if not req.document_text.strip():
        raise HTTPException(status_code=400, detail="document_text is empty.")
    return await execute(req.document_text)


@app.post("/upload")
async def upload(
    file: UploadFile = File(...),
    extra_text: str = Form(default=""),
):
    """
    Accept a PDF, DOCX, or TXT upload plus an optional typed text block.
    The two are merged (document first, then typed text) before the BA
    workflow runs. This lets analysts combine a formal document with
    hand-written requirements in a single analysis pass.
    """
    suffix = pathlib.Path(file.filename).suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{suffix}'. Allowed: {', '.join(ALLOWED_EXTENSIONS)}",
        )

    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = tmp.name

    try:
        document_text = DocumentParser.parse(tmp_path)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    finally:
        os.unlink(tmp_path)

    merged = merge_texts(document_text, extra_text)

    if not merged:
        raise HTTPException(
            status_code=422,
            detail="Could not extract text from the uploaded file and no typed text was provided.",
        )

    return await execute(merged)


@app.post("/elaborate")
async def elaborate(req: ElaborateRequest):
    """
    Deep-dive a single requirement with optional extra context.
    Streams back SSE events:
      progress → stories → tests → review → done
    """
    if not req.requirement:
        raise HTTPException(status_code=400, detail="requirement is required.")

    requirement_with_context = dict(req.requirement)
    if req.extra_context.strip():
        requirement_with_context["description"] = (
            requirement_with_context.get("description", "")
            + f"\n\nAdditional context provided by the analyst:\n{req.extra_context.strip()}"
        )

    requirements_payload = {
        "modules": [
            {
                "name": requirement_with_context.get("module", "Elaborated Requirement"),
                "requirements": [requirement_with_context],
            }
        ]
    }

    async def stream():
        try:
            yield sse_event("progress", {"step": "stories", "message": "Generating user stories…"})
            stories = await story_agent.run(requirements_payload)
            yield sse_event("stories", stories)

            yield sse_event("progress", {"step": "tests", "message": "Writing test cases…"})
            tests = await testcase_agent.run(stories)
            yield sse_event("tests", tests)

            yield sse_event("progress", {"step": "review", "message": "Running QA review…"})
            review = await review_agent.run(requirements_payload, stories, tests)
            yield sse_event("review", review)

            yield sse_event("done", {"message": "Elaboration complete."})

        except Exception as exc:
            yield sse_event("error", {"message": str(exc)})

    return StreamingResponse(
        stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
