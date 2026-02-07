"""
Integration tests for the FastAPI API endpoints.

Tests health check, document upload, and question-answering endpoints.
"""

import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
import tempfile
import os

from app.main import app


@pytest.fixture
def client():
    """Create a test client for the FastAPI application."""
    return TestClient(app)


@pytest.fixture
def mock_services():
    """Mock all services for isolated API testing."""
    with patch('app.api.routes.get_llm_service') as mock_llm, \
         patch('app.api.routes.get_document_service') as mock_doc, \
         patch('app.api.routes.get_vector_service') as mock_vec:
        
        # Setup LLM service mock
        llm_instance = MagicMock()
        llm_instance.check_connection.return_value = True
        llm_instance.generate_response.return_value = "This is a test answer."
        mock_llm.return_value = llm_instance
        
        # Setup Document service mock
        doc_instance = MagicMock()
        doc_instance.validate_file.return_value = (True, "")
        doc_instance.extract_text.return_value = "Test text content"
        doc_instance.split_into_chunks.return_value = [
            MagicMock(content="Chunk 1", source="test.txt", chunk_index=0, metadata={})
        ]
        doc_instance.get_stored_documents.return_value = []
        mock_doc.return_value = doc_instance
        
        # Setup Vector service mock
        vec_instance = MagicMock()
        vec_instance.get_document_count.return_value = 5
        vec_instance.add_chunks.return_value = 1
        vec_instance.search.return_value = [
            {"content": "Relevant chunk", "source": "doc.pdf", "score": 0.95}
        ]
        vec_instance.get_sources.return_value = ["doc.pdf"]
        mock_vec.return_value = vec_instance
        
        yield {
            'llm': llm_instance,
            'doc': doc_instance,
            'vec': vec_instance
        }


class TestHealthEndpoint:
    """Tests for the /health endpoint."""
    
    def test_health_check_healthy(self, client, mock_services):
        """Test health check returns healthy status."""
        response = client.get("/api/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["llm_status"] == "connected"
        assert "version" in data
        assert "documents_count" in data
    
    def test_health_check_degraded(self, client, mock_services):
        """Test health check returns degraded when LLM disconnected."""
        mock_services['llm'].check_connection.return_value = False
        
        response = client.get("/api/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "degraded"
        assert data["llm_status"] == "disconnected"


class TestAskEndpoint:
    """Tests for the /ask endpoint."""
    
    def test_ask_success(self, client, mock_services):
        """Test successful question answering."""
        response = client.post("/api/ask", json={
            "question": "What is the test question?",
            "top_k": 3
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "answer" in data
        assert "sources" in data
        assert "processing_time" in data
    
    def test_ask_empty_question(self, client, mock_services):
        """Test that empty question returns error."""
        response = client.post("/api/ask", json={
            "question": "   ",
            "top_k": 3
        })
        
        assert response.status_code == 400
    
    def test_ask_no_documents(self, client, mock_services):
        """Test asking when no documents are indexed."""
        mock_services['vec'].get_document_count.return_value = 0
        
        response = client.post("/api/ask", json={
            "question": "Test question?",
            "top_k": 3
        })
        
        assert response.status_code == 400
        assert "No documents" in response.json()["detail"]
    
    def test_ask_llm_unavailable(self, client, mock_services):
        """Test asking when LLM is unavailable."""
        mock_services['llm'].check_connection.return_value = False
        
        response = client.post("/api/ask", json={
            "question": "Test question?",
            "top_k": 3
        })
        
        assert response.status_code == 503
        assert "LLM" in response.json()["detail"]
    
    def test_ask_question_too_long(self, client, mock_services):
        """Test asking with question exceeding max length."""
        long_question = "A" * 1500
        
        response = client.post("/api/ask", json={
            "question": long_question,
            "top_k": 3
        })
        
        assert response.status_code == 422  # Validation error


class TestUploadEndpoint:
    """Tests for the /upload endpoint."""
    
    def test_upload_success(self, client, mock_services):
        """Test successful document upload."""
        # Create a temporary text file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
            f.write("Test document content")
            temp_path = f.name
        
        try:
            with open(temp_path, 'rb') as f:
                response = client.post(
                    "/api/upload",
                    files={"file": ("test.txt", f, "text/plain")}
                )
            
            assert response.status_code == 200
            data = response.json()
            assert "message" in data
            assert "filename" in data
            assert "chunks_created" in data
        finally:
            os.unlink(temp_path)
    
    def test_upload_invalid_extension(self, client, mock_services):
        """Test uploading file with invalid extension."""
        mock_services['doc'].validate_file.return_value = (False, "Unsupported file type")
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.exe', delete=False) as f:
            f.write("fake content")
            temp_path = f.name
        
        try:
            with open(temp_path, 'rb') as f:
                response = client.post(
                    "/api/upload",
                    files={"file": ("test.exe", f, "application/octet-stream")}
                )
            
            assert response.status_code == 400
            assert "Unsupported" in response.json()["detail"]
        finally:
            os.unlink(temp_path)
    
    def test_upload_empty_file(self, client, mock_services):
        """Test uploading empty file."""
        mock_services['doc'].extract_text.return_value = ""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            # Empty file
            temp_path = f.name
        
        try:
            with open(temp_path, 'rb') as f:
                response = client.post(
                    "/api/upload",
                    files={"file": ("empty.txt", f, "text/plain")}
                )
            
            assert response.status_code == 400
        finally:
            os.unlink(temp_path)


class TestDocumentsEndpoint:
    """Tests for the /documents endpoint."""
    
    def test_list_documents_empty(self, client, mock_services):
        """Test listing documents when none are uploaded."""
        mock_services['doc'].get_stored_documents.return_value = []
        mock_services['vec'].get_sources.return_value = []
        
        response = client.get("/api/documents")
        
        assert response.status_code == 200
        data = response.json()
        assert data["documents"] == []
        assert data["total_count"] == 0
    
    def test_list_documents_with_files(self, client, mock_services):
        """Test listing documents when files exist."""
        mock_services['doc'].get_stored_documents.return_value = [
            {"filename": "doc1.pdf", "size_bytes": 1024, "modified_at": 1704067200}
        ]
        mock_services['vec'].get_sources.return_value = ["doc1.pdf"]
        
        response = client.get("/api/documents")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["documents"]) == 1
        assert data["documents"][0]["filename"] == "doc1.pdf"


class TestDeleteEndpoint:
    """Tests for the DELETE /documents/{filename} endpoint."""
    
    def test_delete_existing_document(self, client, mock_services):
        """Test deleting an existing document."""
        mock_services['vec'].delete_by_source.return_value = 5
        
        with patch('pathlib.Path.exists', return_value=True), \
             patch('pathlib.Path.unlink'):
            response = client.delete("/api/documents/test.pdf")
        
        assert response.status_code == 200
        assert "deleted" in response.json()["message"].lower()
    
    def test_delete_nonexistent_document(self, client, mock_services):
        """Test deleting a document that doesn't exist."""
        mock_services['vec'].delete_by_source.return_value = 0
        
        with patch('pathlib.Path.exists', return_value=False):
            response = client.delete("/api/documents/nonexistent.pdf")
        
        assert response.status_code == 404
