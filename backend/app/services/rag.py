"""
RAG Service - Retrieval-Augmented Generation for resume Q&A.

Implements ACTUAL RAG flow:
1. Store resume chunks + embeddings in vector store (FAISS)
2. On user question: embed question -> retrieve relevant chunks -> pass to LLM
3. NEVER send full resume to LLM; only retrieved context + question

Uses FAISS (in-memory) for Python 3.14 compatibility instead of ChromaDB.
"""

from typing import List, Optional

from app.config import get_settings
from app.services.embeddings import EmbeddingService
from app.services.parser import DocumentParser
from app.services.vector_store import FAISSVectorStore


class RAGService:
    """
    RAG pipeline: Embed -> Store -> Retrieve -> Augment.
    
    Vector store: FAISS (in-memory, Python 3.14 compatible).
    """

    def __init__(self):
        self._settings = get_settings()
        self._parser = DocumentParser()
        self._embeddings = EmbeddingService()
        self._store = FAISSVectorStore()
        self._session_id: Optional[str] = None

    def index_resume(self, resume_text: str, session_id: str) -> int:
        """
        RAG Flow Steps 2-4: Chunk resume, generate embeddings, store in vector DB.
        
        Returns: number of chunks indexed.
        """
        chunks = self._parser.chunk_resume(resume_text)
        if not chunks:
            return 0

        texts = [f"[{sec}] {content}" for sec, content in chunks]
        embeddings = self._embeddings.embed_texts(texts)

        self._session_id = session_id
        self.clear_session(session_id)
        self._store.add(session_id, embeddings, texts)
        return len(chunks)

    def retrieve(self, question: str, session_id: str, top_k: Optional[int] = None) -> List[str]:
        """
        RAG Flow Steps 5a-5b: Embed question, retrieve relevant resume chunks.
        
        Returns: list of retrieved chunk texts (ONLY these go to LLM).
        """
        if top_k is None:
            top_k = self._settings.top_k_retrieval

        q_embedding = self._embeddings.embed_single(question)
        return self._store.search(session_id, q_embedding, top_k=min(top_k, 10))

    def clear_session(self, session_id: str):
        """Remove vector data for a session."""
        self._store.delete(session_id)
