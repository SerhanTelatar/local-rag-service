"""
Pydantic Schemas - Request and Response models.

This module defines all data models used for API validation and serialization.
"""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


# ===========================
# Health Check Models
# ===========================

class HealthResponse(BaseModel):
    """Health check response model."""
    
    status: str = Field(..., description="Service status (healthy/degraded)")
    version: str = Field(..., description="Service version")
    llm_status: str = Field(..., description="LLM connection status (connected/disconnected)")
    documents_count: int = Field(..., description="Number of indexed documents")


# ===========================
# Ask Question Models
# ===========================

class AskRequest(BaseModel):
    """Request model for asking questions."""
    
    question: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="Question to ask about the documents"
    )
    top_k: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Number of top results to use for context"
    )


class SourceDocument(BaseModel):
    """Source document information in response."""
    
    content: str = Field(..., description="Matched content from document")
    source: str = Field(..., description="Source filename")
    score: float = Field(..., description="Relevance score (0-1)")


class AskResponse(BaseModel):
    """Response model for question answering."""
    
    answer: str = Field(..., description="Generated answer")
    sources: list[SourceDocument] = Field(
        default_factory=list,
        description="Source documents used for answer"
    )
    processing_time: float = Field(..., description="Total processing time (seconds)")


# ===========================
# Document Upload Models
# ===========================

class UploadResponse(BaseModel):
    """Response model for document upload."""
    
    message: str = Field(..., description="Operation result message")
    filename: str = Field(..., description="Uploaded filename")
    chunks_created: int = Field(..., description="Number of chunks created")


# ===========================
# Document List Models
# ===========================

class DocumentInfo(BaseModel):
    """Information about a stored document."""
    
    filename: str = Field(..., description="Document filename")
    size_bytes: int = Field(..., description="File size in bytes")
    uploaded_at: Optional[datetime] = Field(None, description="Upload timestamp")
    chunks_count: int = Field(default=0, description="Number of chunks in vector database")


class DocumentListResponse(BaseModel):
    """Response model for document listing."""
    
    documents: list[DocumentInfo] = Field(
        default_factory=list,
        description="List of documents"
    )
    total_count: int = Field(..., description="Total document count")


# ===========================
# Error Models
# ===========================

class ErrorResponse(BaseModel):
    """Standard error response model."""
    
    detail: str = Field(..., description="Error description")
    error_code: Optional[str] = Field(None, description="Error code")
