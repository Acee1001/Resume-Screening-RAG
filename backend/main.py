"""
Resume Screening Tool - FastAPI Backend

RAG-powered resume screening with:
- PDF/TXT upload for resume and job description
- Match analysis (score, strengths, gaps)
- RAG-based chat (retrieve chunks -> LLM)
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router

# Create FastAPI app with metadata
app = FastAPI(
    title="Resume Screening Tool API",
    description="AI-powered resume screening with RAG",
    version="1.0.0",
)

# Add CORS middleware for frontend connections
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router, prefix="/api", tags=["resume-screening"])

# Root endpoint
@app.get("/")
def root():
    return {"message": "Resume Screening Tool API", "docs": "/docs"}

# Health check endpoint
@app.get("/health")
def health():
    return {"status": "ok"}
