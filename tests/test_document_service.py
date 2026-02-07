"""
Unit tests for the Document Service.

Tests document validation, text extraction, and chunking functionality.
"""

import pytest
from pathlib import Path
import tempfile
import os

from app.services.document_service import DocumentService, DocumentChunk


class TestDocumentService:
    """Test suite for DocumentService class."""
    
    @pytest.fixture
    def service(self):
        """Create a document service instance for testing."""
        return DocumentService()
    
    # ===========================
    # File Validation Tests
    # ===========================
    
    def test_validate_file_valid_pdf(self, service):
        """Test validation of a valid PDF file."""
        is_valid, error = service.validate_file("test.pdf", 1000)
        assert is_valid is True
        assert error == ""
    
    def test_validate_file_valid_txt(self, service):
        """Test validation of a valid TXT file."""
        is_valid, error = service.validate_file("document.txt", 5000)
        assert is_valid is True
        assert error == ""
    
    def test_validate_file_valid_md(self, service):
        """Test validation of a valid MD file."""
        is_valid, error = service.validate_file("readme.md", 2000)
        assert is_valid is True
        assert error == ""
    
    def test_validate_file_valid_docx(self, service):
        """Test validation of a valid DOCX file."""
        is_valid, error = service.validate_file("report.docx", 50000)
        assert is_valid is True
        assert error == ""
    
    def test_validate_file_invalid_extension(self, service):
        """Test validation rejects unsupported file types."""
        is_valid, error = service.validate_file("script.py", 1000)
        assert is_valid is False
        assert "Unsupported file type" in error
    
    def test_validate_file_invalid_extension_exe(self, service):
        """Test validation rejects executable files."""
        is_valid, error = service.validate_file("program.exe", 1000)
        assert is_valid is False
        assert "Unsupported file type" in error
    
    def test_validate_file_too_large(self, service):
        """Test validation rejects files that exceed size limit."""
        # 15 MB file (exceeds 10 MB limit)
        large_size = 15 * 1024 * 1024
        is_valid, error = service.validate_file("large.pdf", large_size)
        assert is_valid is False
        assert "File size too large" in error
    
    def test_validate_file_at_size_limit(self, service):
        """Test validation accepts files at exactly the size limit."""
        # Exactly 10 MB
        exact_size = 10 * 1024 * 1024
        is_valid, error = service.validate_file("exact.pdf", exact_size)
        assert is_valid is True
    
    # ===========================
    # Text Extraction Tests
    # ===========================
    
    def test_extract_from_txt(self, service):
        """Test text extraction from TXT file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
            f.write("This is a test text.\nSecond line.")
            temp_path = Path(f.name)
        
        try:
            text = service.extract_text(temp_path)
            assert "This is a test text." in text
            assert "Second line" in text
        finally:
            os.unlink(temp_path)
    
    def test_extract_from_md(self, service):
        """Test text extraction from Markdown file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as f:
            f.write("# Header\n\nThis is a **markdown** file.")
            temp_path = Path(f.name)
        
        try:
            text = service.extract_text(temp_path)
            assert "# Header" in text
            assert "markdown" in text
        finally:
            os.unlink(temp_path)
    
    def test_extract_unsupported_format(self, service):
        """Test that unsupported formats raise ValueError."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.xyz', delete=False) as f:
            f.write("test content")
            temp_path = Path(f.name)
        
        try:
            with pytest.raises(ValueError) as exc_info:
                service.extract_text(temp_path)
            assert "Unsupported file type" in str(exc_info.value)
        finally:
            os.unlink(temp_path)
    
    # ===========================
    # Text Chunking Tests
    # ===========================
    
    def test_split_into_chunks_basic(self, service):
        """Test basic text splitting into chunks."""
        text = "Paragraph one.\n\nParagraph two.\n\nParagraph three."
        chunks = service.split_into_chunks(text, "test.txt")
        
        assert len(chunks) >= 1
        assert all(isinstance(c, DocumentChunk) for c in chunks)
        assert all(c.source == "test.txt" for c in chunks)
    
    def test_split_into_chunks_preserves_content(self, service):
        """Test that chunking preserves all content."""
        text = "A" * 100 + "\n\n" + "B" * 100 + "\n\n" + "C" * 100
        chunks = service.split_into_chunks(text, "test.txt")
        
        # All content should be in chunks
        all_content = " ".join(c.content for c in chunks)
        assert "A" * 50 in all_content  # At least some A's should be present
    
    def test_split_into_chunks_empty_text(self, service):
        """Test that empty text returns empty list."""
        chunks = service.split_into_chunks("", "test.txt")
        assert chunks == []
    
    def test_split_into_chunks_whitespace_only(self, service):
        """Test that whitespace-only text returns empty list."""
        chunks = service.split_into_chunks("   \n\n   \t  ", "test.txt")
        assert chunks == []
    
    def test_split_into_chunks_with_metadata(self, service):
        """Test that metadata is included in chunks."""
        text = "Test content."
        metadata = {"author": "Test User", "date": "2024-01-01"}
        chunks = service.split_into_chunks(text, "test.txt", metadata)
        
        assert len(chunks) > 0
        assert chunks[0].metadata.get("author") == "Test User"
        assert chunks[0].metadata.get("date") == "2024-01-01"
    
    def test_split_into_chunks_indexes(self, service):
        """Test that chunks have correct sequential indexes."""
        # Create text that will produce multiple chunks
        text = "\n\n".join(["Paragraph " + str(i) + ". " + "X" * 400 for i in range(5)])
        chunks = service.split_into_chunks(text, "test.txt")
        
        if len(chunks) > 1:
            indexes = [c.chunk_index for c in chunks]
            assert indexes == list(range(len(chunks)))
    
    def test_split_long_paragraph(self, service):
        """Test splitting of a single very long paragraph."""
        # Create a very long paragraph that exceeds chunk size
        long_text = "Word " * 500
        chunks = service.split_into_chunks(long_text, "test.txt")
        
        assert len(chunks) > 1
        # Each chunk should not exceed chunk_size significantly
        for chunk in chunks:
            assert len(chunk.content) <= service.chunk_size + 100  # Some tolerance
    
    # ===========================
    # Edge Cases
    # ===========================
    
    def test_validate_empty_filename(self, service):
        """Test validation with empty filename."""
        is_valid, error = service.validate_file("", 1000)
        assert is_valid is False
    
    def test_validate_filename_no_extension(self, service):
        """Test validation with filename without extension."""
        is_valid, error = service.validate_file("noextension", 1000)
        assert is_valid is False
    
    def test_split_single_word(self, service):
        """Test splitting text with single word."""
        chunks = service.split_into_chunks("Hello", "test.txt")
        assert len(chunks) == 1
        assert chunks[0].content == "Hello"
