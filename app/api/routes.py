"""
API Routes - FastAPI endpoint definitions.

This module defines all REST API endpoints for the document QA service.
"""

import time
import logging
from pathlib import Path
from datetime import datetime

from fastapi import APIRouter, HTTPException, UploadFile, File, status

from app.config import settings
from app.models.schemas import (
    HealthResponse,
    AskRequest,
    AskResponse,
    SourceDocument,
    UploadResponse,
    DocumentInfo,
    DocumentListResponse,
    ErrorResponse,
)
from app.services.llm_service import get_llm_service
from app.services.document_service import get_document_service
from app.services.vector_service import get_vector_service

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health Check",
    description="Check service health and component status"
)
async def health_check() -> HealthResponse:
    """
    Check the health status of the service.
    
    Returns information about the service status,
    LLM connection, and indexed documents.
    """
    llm_service = get_llm_service()
    vector_service = get_vector_service()
    
    llm_connected = llm_service.check_connection()
    doc_count = vector_service.get_document_count()
    
    return HealthResponse(
        status="healthy" if llm_connected else "degraded",
        version="1.0.0",
        llm_status="connected" if llm_connected else "disconnected",
        documents_count=doc_count
    )


@router.post(
    "/ask",
    response_model=AskResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid request"},
        503: {"model": ErrorResponse, "description": "LLM service unavailable"}
    },
    summary="Ask a Question",
    description="Ask a question about the indexed documents"
)
async def ask_question(request: AskRequest) -> AskResponse:
    """
    Process a question against the indexed documents using RAG.
    
    1. Searches for relevant document chunks
    2. Sends the question with context to LLM
    3. Returns the generated answer with sources
    """
    start_time = time.time()
    
    # Validate question
    question = request.question.strip()
    if not question:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Soru boş olamaz"
        )
    
    try:
        # Get services
        llm_service = get_llm_service()
        vector_service = get_vector_service()
        
        # Check LLM availability
        if not llm_service.check_connection():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="LLM servisi şu anda kullanılamıyor. Ollama'nın çalıştığından emin olun."
            )
        
        # Check if we have documents
        if vector_service.get_document_count() == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Henüz hiç doküman yüklenmemiş. Önce /upload endpoint'i ile doküman yükleyin."
            )
        
        # Search for relevant documents
        search_results = vector_service.search(question, top_k=request.top_k)
        
        # Build context from search results
        context_parts = []
        sources = []
        
        for result in search_results:
            context_parts.append(f"[{result['source']}]: {result['content']}")
            sources.append(SourceDocument(
                content=result['content'][:200] + "..." if len(result['content']) > 200 else result['content'],
                source=result['source'],
                score=round(result['score'], 3)
            ))
        
        context = "\n\n".join(context_parts) if context_parts else "Bağlam bulunamadı."
        
        # Generate response from LLM
        answer = llm_service.generate_response(question, context)
        
        processing_time = time.time() - start_time
        
        return AskResponse(
            answer=answer,
            sources=sources,
            processing_time=round(processing_time, 2)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing question: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Soru işlenirken hata oluştu: {str(e)}"
        )


@router.post(
    "/upload",
    response_model=UploadResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid file"},
        413: {"model": ErrorResponse, "description": "File too large"}
    },
    summary="Upload Document",
    description="Upload a document for indexing"
)
async def upload_document(file: UploadFile = File(...)) -> UploadResponse:
    """
    Upload and index a document.
    
    Supported formats: PDF, TXT, MD, DOCX
    The document will be chunked and stored in the vector database.
    """
    doc_service = get_document_service()
    vector_service = get_vector_service()
    
    # Read file content
    content = await file.read()
    file_size = len(content)
    
    # Validate file
    is_valid, error_msg = doc_service.validate_file(file.filename, file_size)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
        )
    
    try:
        # Save file to documents directory
        file_path = Path(settings.documents_directory) / file.filename
        with open(file_path, "wb") as f:
            f.write(content)
        
        # Extract text
        text = doc_service.extract_text(file_path)
        
        if not text.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Dosyadan metin çıkarılamadı. Dosyanın boş olmadığından emin olun."
            )
        
        # Delete existing chunks for this source (if re-uploading)
        vector_service.delete_by_source(file.filename)
        
        # Split into chunks
        chunks = doc_service.split_into_chunks(text, file.filename)
        
        # Add to vector database
        chunks_added = vector_service.add_chunks(chunks)
        
        logger.info(f"Uploaded and indexed document: {file.filename} ({chunks_added} chunks)")
        
        return UploadResponse(
            message="Doküman başarıyla yüklendi ve indekslendi",
            filename=file.filename,
            chunks_created=chunks_added
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading document: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Doküman yüklenirken hata oluştu: {str(e)}"
        )


@router.get(
    "/documents",
    response_model=DocumentListResponse,
    summary="List Documents",
    description="Get list of indexed documents"
)
async def list_documents() -> DocumentListResponse:
    """
    Get a list of all indexed documents.
    """
    doc_service = get_document_service()
    vector_service = get_vector_service()
    
    stored_docs = doc_service.get_stored_documents()
    sources = vector_service.get_sources()
    
    documents = []
    for doc in stored_docs:
        # Count chunks for this document
        chunks_count = 0
        if doc['filename'] in sources:
            # This is approximate - we'd need to query ChromaDB for exact count
            chunks_count = 1  # Placeholder
        
        documents.append(DocumentInfo(
            filename=doc['filename'],
            size_bytes=doc['size_bytes'],
            uploaded_at=datetime.fromtimestamp(doc['modified_at']),
            chunks_count=chunks_count
        ))
    
    return DocumentListResponse(
        documents=documents,
        total_count=len(documents)
    )


@router.delete(
    "/documents/{filename}",
    summary="Delete Document",
    description="Delete a document from the index"
)
async def delete_document(filename: str) -> dict:
    """
    Delete a specific document from the index.
    """
    vector_service = get_vector_service()
    doc_service = get_document_service()
    
    # Delete from vector store
    deleted_count = vector_service.delete_by_source(filename)
    
    # Delete file from disk
    file_path = Path(settings.documents_directory) / filename
    if file_path.exists():
        file_path.unlink()
    
    if deleted_count > 0 or file_path.exists():
        return {"message": f"Doküman silindi: {filename}", "chunks_deleted": deleted_count}
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Doküman bulunamadı: {filename}"
        )
