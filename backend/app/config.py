"""Application configuration - loads from environment variables."""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment."""
    
    # LLM Provider: openai | gemini | claude
    llm_provider: str = "openai"
    
    # API Keys (only the active provider's key is required)
    openai_api_key: str = ""
    gemini_api_key: str = ""
    anthropic_api_key: str = ""
    
    # Use OpenAI embeddings instead of sentence-transformers
    use_openai_embeddings: bool = False
    
    # RAG settings
    chunk_size: int = 512
    chunk_overlap: int = 64
    top_k_retrieval: int = 5
    
    # Chroma persistence
    chroma_persist_directory: str = "./chroma_db"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    """Cached settings instance."""
    return Settings()
