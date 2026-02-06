"""API request and response schemas."""

from typing import List, Optional
from pydantic import BaseModel, Field


class UploadResponse(BaseModel):
    """Response after uploading a file."""
    success: bool = True
    message: str = ""
    filename: Optional[str] = None
    text_length: Optional[int] = None


class MatchAnalysis(BaseModel):
    """Match analysis result."""
    match_score: float = Field(..., ge=0, le=100, description="Match percentage 0-100")
    strengths: List[str] = Field(default_factory=list)
    gaps: List[str] = Field(default_factory=list)
    key_insights: List[str] = Field(default_factory=list)
    skill_overlap: List[str] = Field(default_factory=list)
    missing_skills: List[str] = Field(default_factory=list)


class AnalysisResponse(BaseModel):
    """Full analysis response."""
    success: bool = True
    analysis: Optional[MatchAnalysis] = None
    error: Optional[str] = None


class ChatMessage(BaseModel):
    """Single chat message."""
    role: str = Field(..., pattern="^(user|assistant)$")
    content: str


class ChatRequest(BaseModel):
    """Chat request with question and optional history."""
    question: str = Field(..., min_length=1, max_length=2000)
    history: List[ChatMessage] = Field(default_factory=list, max_length=20)


class ChatResponse(BaseModel):
    """Chat response with answer."""
    success: bool = True
    answer: str = ""
    error: Optional[str] = None
