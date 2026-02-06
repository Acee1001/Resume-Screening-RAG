# Resume Screening Tool

An AI-powered Resume Screening Tool with **real RAG (Retrieval-Augmented Generation)**. Recruiters can upload a resume and job description, view match analysis, and ask questions about candidates via a RAG-powered chat.

## Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | Python 3.10+, FastAPI |
| Frontend | React 18, TypeScript, Vite |
| PDF Parsing | pdfplumber |
| Embeddings | sentence-transformers (default) or OpenAI |
| Vector Store | FAISS (in-memory, Python 3.14 compatible) |
| LLM | OpenAI / Gemini / Claude (configurable) |

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           FRONTEND (React 18)                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────────┐   │
│  │ Resume Upload│  │  JD Upload   │  │  Match Analysis + Chat UI     │   │
│  └──────┬───────┘  └──────┬───────┘  └───────────────┬──────────────┘   │
└─────────┼─────────────────┼──────────────────────────┼──────────────────┘
          │                 │                          │
          ▼                 ▼                          ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         BACKEND (FastAPI)                                 │
│  POST /upload/resume   POST /upload/jd   GET /analysis   POST /chat       │
└──────────────────────────────────────────────────────────────────────────┘
          │                 │                          │
          ▼                 ▼                          ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         RAG PIPELINE                                      │
│                                                                          │
│  1. Parse PDF/TXT → Extract text                                         │
│  2. Chunk resume → Logical sections (Skills, Experience, Education...)   │
│  3. Generate embeddings → sentence-transformers or OpenAI                │
│  4. Store in FAISS → In-memory vector store (per session)                 │
│  5. On question: Embed question → Retrieve top-k chunks                  │
│  6. Augment: Pass ONLY retrieved chunks + question → LLM                 │
│                                                                          │
│  ┌────────────┐    ┌──────────────┐    ┌────────────────┐               │
│  │ Document   │───▶│  Embeddings  │───▶│  FAISS Store   │               │
│  │ Parser     │    │  Service     │    │  (Vector Store)│               │
│  └────────────┘    └──────────────┘    └────────┬───────┘               │
│                                                  │                        │
│                                                  ▼                        │
│  ┌────────────────────────────────────────────────────────────┐         │
│  │  User Question → Embed → Retrieve Chunks → LLM (with ctx)   │         │
│  └────────────────────────────────────────────────────────────┘         │
└─────────────────────────────────────────────────────────────────────────┘
```

## RAG Flow Diagram

```
User: "Does this candidate have experience with React?"

                    ┌─────────────────────────────────────┐
                    │ 1. Embed question                   │
                    │    "Does this candidate have..."    │
                    │         → [0.12, -0.34, ...]        │
                    └─────────────────┬───────────────────┘
                                      │
                                      ▼
                    ┌─────────────────────────────────────┐
                    │ 2. Vector search in FAISS           │
                    │    cosine similarity                │
                    └─────────────────┬───────────────────┘
                                      │
                                      ▼
                    ┌─────────────────────────────────────┐
                    │ 3. Retrieve top-k chunks            │
                    │    e.g. "[skills] React, JavaScript, │
                    │         TypeScript, Node.js..."      │
                    └─────────────────┬───────────────────┘
                                      │
                                      ▼
                    ┌─────────────────────────────────────┐
                    │ 4. Pass to LLM:                     │
                    │    Context: [retrieved chunks ONLY]  │
                    │    Question: "Does this candidate   │
                    │    have experience with React?"     │
                    └─────────────────┬───────────────────┘
                                      │
                                      ▼
                    ┌─────────────────────────────────────┐
                    │ 5. LLM generates answer             │
                    │    "Yes, the candidate has 5+ years │
                    │    of React experience..."          │
                    └─────────────────────────────────────┘

NOTE: Full resume is NEVER sent to the LLM — only retrieved chunks.
```

## Setup

### Prerequisites

- Python 3.10+
- Node.js 18+
- npm or yarn

### Backend

```bash
cd backend
python -m venv venv
# Windows:
venv\Scripts\activate
# Unix/macOS:
# source venv/bin/activate

pip install -r requirements.txt

# Copy .env.example to .env and set API keys
copy .env.example .env   # Windows
# cp .env.example .env   # Unix

# Run backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

### Environment Variables

Create `backend/.env`:

```env
# LLM Provider: openai | gemini | claude
LLM_PROVIDER=openai

# OpenAI (required when LLM_PROVIDER=openai)
OPENAI_API_KEY=sk-...

# Google Gemini (when LLM_PROVIDER=gemini)
GEMINI_API_KEY=...

# Anthropic Claude (when LLM_PROVIDER=claude)
ANTHROPIC_API_KEY=...

# Optional: Use OpenAI embeddings (default: sentence-transformers)
USE_OPENAI_EMBEDDINGS=false
```

**Note:** With `USE_OPENAI_EMBEDDINGS=false`, embeddings use sentence-transformers locally — no API key needed for embeddings. Only the chat LLM requires an API key.

## API Documentation

### POST /api/upload/resume

Upload a resume (PDF or TXT).

**Request:** `multipart/form-data`, field `file`

**Response:**
```json
{
  "success": true,
  "message": "Resume uploaded. Indexed 8 chunks for RAG.",
  "filename": "resume.pdf",
  "text_length": 2450
}
```

### POST /api/upload/jd

Upload a job description (PDF or TXT).

**Request:** `multipart/form-data`, field `file`

**Response:**
```json
{
  "success": true,
  "message": "Job description uploaded.",
  "filename": "jd.txt",
  "text_length": 1200
}
```

### GET /api/analysis

Get match analysis (requires both resume and JD uploaded).

**Response:**
```json
{
  "success": true,
  "analysis": {
    "match_score": 75.5,
    "strengths": ["Has required skill: React", "Has relevant work experience"],
    "gaps": ["Missing skill: Kubernetes", "Missing skill: Aws"],
    "key_insights": ["Overall match: 75.5%", "Resume lists 15 skills"],
    "skill_overlap": ["React", "Node.js", "PostgreSQL"],
    "missing_skills": ["Kubernetes", "AWS"]
  }
}
```

### POST /api/chat

RAG-powered chat. Asks questions about the candidate.

**Request:**
```json
{
  "question": "Does this candidate have a degree from a state university?",
  "history": [
    { "role": "user", "content": "What's their experience with PostgreSQL?" },
    { "role": "assistant", "content": "The candidate has 5+ years..." }
  ]
}
```

**Response:**
```json
{
  "success": true,
  "answer": "Yes, the candidate graduated from SUNY Buffalo (State University of New York) with a Bachelor of Science in Computer Science."
}
```

## Match Scoring Logic

The match score is a weighted average (0–100%):

| Component | Weight | Logic |
|-----------|--------|-------|
| **Skills** | 50% | % of JD required skills found in resume |
| **Experience** | 35% | Years match + keyword overlap with JD |
| **Education** | 15% | Presence of degree/university keywords from JD |

See `backend/app/services/scoring.py` for implementation details.

## Sample Files

Use files in `samples/` for testing:

- `resume_john_doe.txt` – Full-stack engineer (React, Node.js, SUNY Buffalo)
- `resume_jane_smith.txt` – Backend Python engineer (FastAPI, AWS)
- `jd_senior_fullstack.txt` – Senior full-stack role
- `jd_backend_python.txt` – Backend Python role

## Project Structure

```
LTIMindtree/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── routes.py       # API endpoints
│   │   ├── models/
│   │   │   └── schemas.py      # Pydantic schemas
│   │   ├── services/
│   │   │   ├── parser.py       # PDF/TXT extraction, chunking
│   │   │   ├── embeddings.py   # Vector embeddings
│   │   │   ├── rag.py          # RAG: Chroma + retrieval
│   │   │   ├── llm.py          # LLM (OpenAI/Gemini/Claude)
│   │   │   └── scoring.py      # Match scoring logic
│   │   └── config.py
│   ├── main.py
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── FileUpload.tsx
│   │   │   ├── MatchAnalysis.tsx
│   │   │   └── ChatInterface.tsx
│   │   ├── api.ts
│   │   ├── App.tsx
│   │   └── main.tsx
│   └── package.json
├── samples/
│   ├── resume_john_doe.txt
│   ├── resume_jane_smith.txt
│   ├── jd_senior_fullstack.txt
│   └── jd_backend_python.txt
└── README.md
```

## RAG Implementation Notes

- **Chunking:** Resume is split into logical sections (Skills, Experience, Education, etc.). Each section becomes a retrievable chunk.
- **Embeddings:** Each chunk is embedded; embeddings stored in Chroma with cosine similarity.
- **Retrieval:** User question is embedded; top-k similar chunks are retrieved.
- **Generation:** Only retrieved chunks + question are sent to the LLM. The full resume is never sent.
- **Context-aware chat:** Conversation history (last 6 messages) is passed to the LLM for follow-up questions.
