"""
Embedding Service - Generates vector embeddings for RAG.

RAG Flow Step 3: Convert text chunks to embeddings for vector similarity search.
Supports: sentence-transformers (local) or OpenAI embeddings.
"""

from typing import List, Optional

from app.config import get_settings


class EmbeddingService:
    """Generate embeddings for text chunks."""

    def __init__(self):
        self._settings = get_settings()
        self._model = None
        self._openai_client = None
        self._use_openai = self._settings.use_openai_embeddings

    def _get_sentence_transformer(self):
        """Lazy load sentence-transformers model."""
        if self._model is None:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer("all-MiniLM-L6-v2")
        return self._model

    def _get_openai_client(self):
        """Lazy load OpenAI client."""
        if self._openai_client is None:
            from openai import OpenAI
            self._openai_client = OpenAI(api_key=self._settings.openai_api_key)
        return self._openai_client

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a list of texts.
        
        RAG Flow: Each resume chunk and user question is converted to a vector
        for similarity search in the vector store.
        """
        if not texts:
            return []

        if self._use_openai:
            return self._embed_openai(texts)
        return self._embed_sentence_transformer(texts)

    def _embed_sentence_transformer(self, texts: List[str]) -> List[List[float]]:
        """Use sentence-transformers (local, no API key needed)."""
        model = self._get_sentence_transformer()
        embeddings = model.encode(texts)
        return embeddings.tolist()

    def _embed_openai(self, texts: List[str]) -> List[List[float]]:
        """Use OpenAI text-embedding-3-small."""
        client = self._get_openai_client()
        response = client.embeddings.create(
            model="text-embedding-3-small",
            input=texts,
        )
        return [e.embedding for e in response.data]

    def embed_single(self, text: str) -> List[float]:
        """Embed a single text (e.g., user question)."""
        return self.embed_texts([text])[0]
