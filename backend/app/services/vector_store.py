"""
In-memory FAISS Vector Store - Python 3.14 compatible alternative to ChromaDB.

RAG Flow: Store resume chunk embeddings and retrieve by similarity.
Uses faiss-cpu for efficient cosine similarity search.
"""

import pickle
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np

from app.config import get_settings


class FAISSVectorStore:
    """
    In-memory vector store using FAISS for cosine similarity search.
    Per-session storage (session_id -> index + documents).
    """

    def __init__(self):
        self._settings = get_settings()
        self._stores: Dict[str, tuple] = {}  # session_id -> (index, docs_list)
        self._dim: Optional[int] = None

    def _get_faiss_index(self, dim: int):
        """Lazy import and create FAISS index."""
        try:
            import faiss
            index = faiss.IndexFlatIP(dim)  # Inner product for normalized vectors = cosine
            return index
        except ImportError:
            raise ImportError("Install faiss-cpu: pip install faiss-cpu")

    def _normalize(self, vectors: np.ndarray) -> np.ndarray:
        """L2 normalize for cosine similarity via inner product."""
        norms = np.linalg.norm(vectors, axis=1, keepdims=True)
        norms = np.where(norms == 0, 1, norms)
        return vectors.astype(np.float32) / norms

    def add(self, session_id: str, embeddings: List[List[float]], documents: List[str]) -> None:
        """Add embeddings and documents for a session. Replaces existing data."""
        arr = np.array(embeddings, dtype=np.float32)
        arr = self._normalize(arr)
        self._dim = arr.shape[1]

        try:
            index = self._get_faiss_index(self._dim)
            index.add(arr)
            self._stores[session_id] = (index, documents)
        except Exception as e:
            raise RuntimeError(f"FAISS add failed: {e}") from e

    def search(self, session_id: str, query_embedding: List[float], top_k: int = 5) -> List[str]:
        """Search for top-k similar documents by query embedding."""
        if session_id not in self._stores:
            return []

        index, docs = self._stores[session_id]
        q = np.array([query_embedding], dtype=np.float32)
        q = self._normalize(q)

        scores, indices = index.search(q, min(top_k, len(docs)))

        results = []
        for i in indices[0]:
            if 0 <= i < len(docs):
                results.append(docs[i])
        return results

    def delete(self, session_id: str) -> None:
        """Remove session data."""
        if session_id in self._stores:
            del self._stores[session_id]
