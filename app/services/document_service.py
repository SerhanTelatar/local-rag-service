"""
Document Service - Handles document processing and text extraction.

This module provides functionality for reading various document formats
(PDF, TXT, MD, DOCX) and splitting them into chunks for vector storage.
"""

import logging
from pathlib import Path
from typing import Optional
from dataclasses import dataclass

import fitz  # PyMuPDF
from docx import Document

from app.config import settings

logger = logging.getLogger(__name__)


@dataclass
class DocumentChunk:
    """Represents a chunk of a document."""
    
    content: str
    source: str
    chunk_index: int
    metadata: dict


class DocumentService:
    """
    Service class for document processing operations.
    
    This class handles reading documents, extracting text,
    and splitting content into manageable chunks for embedding.
    """
    
    def __init__(self):
        """Initialize the document service."""
        self.chunk_size = settings.chunk_size
        self.chunk_overlap = settings.chunk_overlap
        self.allowed_extensions = settings.allowed_extensions
        self.max_file_size = settings.max_file_size_mb * 1024 * 1024
        self.documents_dir = Path(settings.documents_directory)
    
    def validate_file(self, filename: str, file_size: int) -> tuple[bool, str]:
        """
        Validate if a file can be processed.
        
        Args:
            filename: Name of the file.
            file_size: Size of the file in bytes.
            
        Returns:
            Tuple of (is_valid, error_message).
        """
        # Check extension
        ext = Path(filename).suffix.lower()
        if ext not in self.allowed_extensions:
            return False, f"Unsupported file type: {ext}. Allowed types: {self.allowed_extensions}"
        
        # Check file size
        if file_size > self.max_file_size:
            return False, f"File size too large. Maximum: {settings.max_file_size_mb}MB"
        
        return True, ""
    
    def extract_text(self, file_path: Path) -> str:
        """
        Extract text content from a document.
        
        Args:
            file_path: Path to the document file.
            
        Returns:
            str: Extracted text content.
            
        Raises:
            ValueError: If file type is not supported.
        """
        ext = file_path.suffix.lower()
        
        if ext == ".pdf":
            return self._extract_from_pdf(file_path)
        elif ext in [".txt", ".md"]:
            return self._extract_from_text(file_path)
        elif ext == ".docx":
            return self._extract_from_docx(file_path)
        else:
            raise ValueError(f"Unsupported file type: {ext}")
    
    def _extract_from_pdf(self, file_path: Path) -> str:
        """Extract text from PDF file."""
        try:
            doc = fitz.open(file_path)
            text_parts = []
            
            for page_num, page in enumerate(doc):
                text = page.get_text()
                if text.strip():
                    text_parts.append(text)
            
            doc.close()
            return "\n\n".join(text_parts)
        except Exception as e:
            logger.error(f"Failed to extract PDF text: {e}")
            raise ValueError(f"Could not read PDF: {str(e)}")
    
    def _extract_from_text(self, file_path: Path) -> str:
        """Extract text from TXT or MD file."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        except UnicodeDecodeError:
            # Try with different encoding
            with open(file_path, "r", encoding="latin-1") as f:
                return f.read()
    
    def _extract_from_docx(self, file_path: Path) -> str:
        """Extract text from DOCX file."""
        try:
            doc = Document(file_path)
            text_parts = []
            
            for para in doc.paragraphs:
                if para.text.strip():
                    text_parts.append(para.text)
            
            return "\n\n".join(text_parts)
        except Exception as e:
            logger.error(f"Failed to extract DOCX text: {e}")
            raise ValueError(f"Could not read DOCX: {str(e)}")
    
    def split_into_chunks(
        self,
        text: str,
        source: str,
        metadata: Optional[dict] = None
    ) -> list[DocumentChunk]:
        """
        Split text into overlapping chunks.
        
        Args:
            text: The text content to split.
            source: Source filename for reference.
            metadata: Optional additional metadata.
            
        Returns:
            List of DocumentChunk objects.
        """
        if not text.strip():
            return []
        
        if metadata is None:
            metadata = {}
        
        chunks = []
        
        # Split by paragraphs first, then by sentences if needed
        paragraphs = text.split("\n\n")
        
        current_chunk = ""
        chunk_index = 0
        
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            
            # Check if adding this paragraph exceeds chunk size
            if len(current_chunk) + len(para) + 2 <= self.chunk_size:
                current_chunk += ("\n\n" if current_chunk else "") + para
            else:
                # Save current chunk if not empty
                if current_chunk:
                    chunks.append(DocumentChunk(
                        content=current_chunk,
                        source=source,
                        chunk_index=chunk_index,
                        metadata=metadata.copy()
                    ))
                    chunk_index += 1
                    
                    # Start new chunk with overlap
                    overlap_text = self._get_overlap_text(current_chunk)
                    current_chunk = overlap_text + para if overlap_text else para
                else:
                    # Paragraph alone is too long, split it
                    para_chunks = self._split_long_text(para, source, chunk_index, metadata)
                    chunks.extend(para_chunks)
                    chunk_index += len(para_chunks)
                    current_chunk = ""
        
        # Don't forget the last chunk
        if current_chunk.strip():
            chunks.append(DocumentChunk(
                content=current_chunk,
                source=source,
                chunk_index=chunk_index,
                metadata=metadata.copy()
            ))
        
        return chunks
    
    def _get_overlap_text(self, text: str) -> str:
        """Get the overlap portion from the end of text."""
        if len(text) <= self.chunk_overlap:
            return text + "\n\n"
        return text[-self.chunk_overlap:] + "\n\n"
    
    def _split_long_text(
        self,
        text: str,
        source: str,
        start_index: int,
        metadata: dict
    ) -> list[DocumentChunk]:
        """Split a long text that exceeds chunk size."""
        chunks = []
        words = text.split()
        current_chunk = ""
        chunk_index = start_index
        
        for word in words:
            if len(current_chunk) + len(word) + 1 <= self.chunk_size:
                current_chunk += (" " if current_chunk else "") + word
            else:
                if current_chunk:
                    chunks.append(DocumentChunk(
                        content=current_chunk,
                        source=source,
                        chunk_index=chunk_index,
                        metadata=metadata.copy()
                    ))
                    chunk_index += 1
                current_chunk = word
        
        if current_chunk.strip():
            chunks.append(DocumentChunk(
                content=current_chunk,
                source=source,
                chunk_index=chunk_index,
                metadata=metadata.copy()
            ))
        
        return chunks
    
    def get_stored_documents(self) -> list[dict]:
        """
        Get list of documents in the documents directory.
        
        Returns:
            List of document info dictionaries.
        """
        documents = []
        
        if not self.documents_dir.exists():
            return documents
        
        for ext in self.allowed_extensions:
            for file_path in self.documents_dir.glob(f"*{ext}"):
                stat = file_path.stat()
                documents.append({
                    "filename": file_path.name,
                    "size_bytes": stat.st_size,
                    "modified_at": stat.st_mtime
                })
        
        return documents


# Singleton instance
_document_service: Optional[DocumentService] = None


def get_document_service() -> DocumentService:
    """Get or create the document service singleton."""
    global _document_service
    if _document_service is None:
        _document_service = DocumentService()
    return _document_service
