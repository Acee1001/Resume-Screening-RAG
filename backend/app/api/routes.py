"""
API Routes - FastAPI endpoints for resume screening.

Endpoints:
- POST /upload/resume
- POST /upload/jd
- GET  /analysis
- POST /chat
- GET  /ask
"""

import os
import uuid
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse

from app.models import (
    AnalysisResponse,
    ChatMessage,
    ChatRequest,
    ChatResponse,
    MatchAnalysis,
    UploadResponse,
)

from app.services.parser import DocumentParser
from app.services.rag import RAGService
from app.services.llm import LLMService
from app.services.scoring import MatchScoringService
from app.llm.gemini import ask_llm  # Import Gemini LLM function

# ----------------------------
# Initialize router and services
# ----------------------------
router = APIRouter()

_storage: dict = {
    "resume_text": None,
    "jd_text": None,
    "session_id": None,
}

_parser = DocumentParser()
_rag = RAGService()
_llm = LLMService()
_scoring = MatchScoringService()

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


def _get_session_id() -> str:
    """Get or create session ID."""
    if _storage["session_id"] is None:
        _storage["session_id"] = str(uuid.uuid4())
    return _storage["session_id"]


def _save_upload(file: UploadFile) -> str:
    """Save uploaded file and return path."""
    ext = Path(file.filename or "file").suffix.lower()
    if ext not in (".pdf", ".txt"):
        raise HTTPException(400, "Only PDF and TXT files allowed")
    path = UPLOAD_DIR / f"{uuid.uuid4()}{ext}"
    with open(path, "wb") as f:
        f.write(file.file.read())
    return str(path)

# ----------------------------
# Gemini LLM endpoint
# ----------------------------
@router.get("/ask")
def ask(prompt: str):
    """
    Send a prompt to Gemini LLM and return the response.
    Example: /ask?prompt=Hello
    """
    return {"response": ask_llm(prompt)}

# ----------------------------
# Resume/JD upload endpoints
# ----------------------------
@router.post("/upload/resume", response_model=UploadResponse)
async def upload_resume(file: UploadFile = File(...)):
    path = _save_upload(file)
    try:
        text = _parser.extract_text(path)
    except Exception as e:
        os.remove(path)
        raise HTTPException(400, str(e))

    _storage["resume_text"] = text
    session_id = _get_session_id()
    num_chunks = _rag.index_resume(text, session_id)

    os.remove(path)
    return UploadResponse(
        success=True,
        message=f"Resume uploaded. Indexed {num_chunks} chunks for RAG.",
        filename=file.filename,
        text_length=len(text),
    )


@router.post("/upload/jd", response_model=UploadResponse)
async def upload_jd(file: UploadFile = File(...)):
    path = _save_upload(file)
    try:
        text = _parser.extract_text(path)
    except Exception as e:
        os.remove(path)
        raise HTTPException(400, str(e))

    _storage["jd_text"] = text
    os.remove(path)
    return UploadResponse(
        success=True,
        message="Job description uploaded.",
        filename=file.filename,
        text_length=len(text),
    )

# ----------------------------
# Analysis endpoint
# ----------------------------
@router.get("/analysis", response_model=AnalysisResponse)
async def get_analysis():
    resume = _storage.get("resume_text")
    jd = _storage.get("jd_text")

    if not resume:
        return AnalysisResponse(success=False, error="Upload a resume first.")
    if not jd:
        return AnalysisResponse(success=False, error="Upload a job description first.")

    try:
        score, strengths, gaps, insights, skill_overlap, missing_skills = _scoring.compute_analysis(resume, jd)
        analysis = MatchAnalysis(
            match_score=score,
            strengths=strengths,
            gaps=gaps,
            key_insights=insights,
            skill_overlap=skill_overlap,
            missing_skills=missing_skills,
        )
        return AnalysisResponse(success=True, analysis=analysis)
    except Exception as e:
        return AnalysisResponse(success=False, error=str(e))

# ----------------------------
# Chat endpoint
# ----------------------------
@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    resume = _storage.get("resume_text")
    if not resume:
        return ChatResponse(success=False, answer="", error="Upload a resume first.")

    session_id = _get_session_id()
    chunks = _rag.retrieve(request.question, session_id)
    history = [{"role": m.role, "content": m.content} for m in request.history]

    try:
        answer = _llm.generate(
            question=request.question,
            context_chunks=chunks,
            conversation_history=history,
        )
        return ChatResponse(success=True, answer=answer)
    except Exception as e:
        return ChatResponse(success=False, answer="", error=str(e))
