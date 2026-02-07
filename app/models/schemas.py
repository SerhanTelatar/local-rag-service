"""
Pydantic schemas for API request/response models.

This module defines all data models used for API validation and serialization.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Response model for health check endpoint."""
    
    status: str = Field(description="Service status", example="healthy")
    version: str = Field(description="API version", example="1.0.0")
    llm_status: str = Field(description="LLM connection status", example="connected")
    documents_count: int = Field(description="Number of indexed documents", example=5)


class AskRequest(BaseModel):
    """Request model for ask endpoint."""
    
    question: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="The question to ask about the documents",
        example="What is the main topic of the document?"
    )
    top_k: Optional[int] = Field(
        default=3,
        ge=1,
        le=10,
        description="Number of relevant document chunks to retrieve"
    )


class SourceDocument(BaseModel):
    """Model for source document information in responses."""
    
    content: str = Field(description="Document chunk content")
    source: str = Field(description="Source file name")
    score: float = Field(description="Relevance score")


class AskResponse(BaseModel):
    """Response model for ask endpoint."""
    
    answer: str = Field(description="Generated answer from LLM")
    sources: list[SourceDocument] = Field(
        description="Source documents used for the answer"
    )
    processing_time: float = Field(description="Time taken to process in seconds")


class UploadResponse(BaseModel):
    """Response model for document upload endpoint."""
    
    message: str = Field(description="Upload status message")
    filename: str = Field(description="Uploaded file name")
    chunks_created: int = Field(description="Number of chunks created from document")


class DocumentInfo(BaseModel):
    """Model for document information."""
    
    filename: str = Field(description="Document file name")
    size_bytes: int = Field(description="File size in bytes")
    uploaded_at: datetime = Field(description="Upload timestamp")
    chunks_count: int = Field(description="Number of chunks in vector store")


class DocumentListResponse(BaseModel):
    """Response model for document list endpoint."""
    
    documents: list[DocumentInfo] = Field(description="List of indexed documents")
    total_count: int = Field(description="Total number of documents")


class ErrorResponse(BaseModel):
    """Standard error response model."""
    
    error: str = Field(description="Error type")
    message: str = Field(description="Error message")
    details: Optional[str] = Field(default=None, description="Additional details")
