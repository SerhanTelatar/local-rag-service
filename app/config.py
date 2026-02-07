"""
Application configuration settings.

This module contains all configuration parameters for the RAG service,
including LLM settings, vector database settings, and document processing options.
"""

import os
from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Application settings
    app_name: str = "Local RAG Service"
    debug: bool = False
    
    # Ollama LLM settings
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.1:8b"
    ollama_timeout: int = 120
    
    # Embedding settings
    embedding_model: str = "all-MiniLM-L6-v2"
    
    # ChromaDB settings
    chroma_persist_directory: str = "./chroma_db"
    chroma_collection_name: str = "documents"
    
    # Document processing settings
    chunk_size: int = 500
    chunk_overlap: int = 50
    max_file_size_mb: int = 10
    allowed_extensions: list[str] = [".pdf", ".txt", ".md", ".docx"]
    
    # RAG settings
    top_k_results: int = 3
    
    # Paths
    documents_directory: str = "./documents"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Global settings instance
settings = Settings()

# Ensure directories exist
Path(settings.chroma_persist_directory).mkdir(parents=True, exist_ok=True)
Path(settings.documents_directory).mkdir(parents=True, exist_ok=True)
