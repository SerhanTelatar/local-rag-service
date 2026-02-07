"""
Unit tests for the LLM Service.

Tests Ollama connection and response generation.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock

from app.services.llm_service import LLMService


class TestLLMService:
    """Test suite for LLMService class."""
    
    @pytest.fixture
    def mock_ollama_client(self):
        """Create a mock Ollama client."""
        with patch('app.services.llm_service.Client') as mock_client:
            yield mock_client
    
    # ===========================
    # Connection Tests
    # ===========================
    
    def test_check_connection_success(self, mock_ollama_client):
        """Test successful connection check."""
        mock_instance = MagicMock()
        mock_instance.list.return_value = {"models": []}
        mock_ollama_client.return_value = mock_instance
        
        service = LLMService()
        assert service.check_connection() is True
    
    def test_check_connection_failure(self, mock_ollama_client):
        """Test connection check when server is down."""
        mock_instance = MagicMock()
        mock_instance.list.side_effect = Exception("Connection refused")
        mock_ollama_client.return_value = mock_instance
        
        service = LLMService()
        assert service.check_connection() is False
    
    # ===========================
    # Model Availability Tests
    # ===========================
    
    def test_is_model_available_true(self, mock_ollama_client):
        """Test model availability when model exists."""
        mock_instance = MagicMock()
        mock_instance.list.return_value = {
            "models": [
                {"name": "llama3.1:8b"},
                {"name": "mistral:7b"}
            ]
        }
        mock_ollama_client.return_value = mock_instance
        
        service = LLMService()
        assert service.is_model_available() is True
    
    def test_is_model_available_false(self, mock_ollama_client):
        """Test model availability when model doesn't exist."""
        mock_instance = MagicMock()
        mock_instance.list.return_value = {
            "models": [{"name": "other-model:latest"}]
        }
        mock_ollama_client.return_value = mock_instance
        
        service = LLMService()
        assert service.is_model_available() is False
    
    def test_is_model_available_error(self, mock_ollama_client):
        """Test model availability when server errors."""
        mock_instance = MagicMock()
        mock_instance.list.side_effect = Exception("Server error")
        mock_ollama_client.return_value = mock_instance
        
        service = LLMService()
        assert service.is_model_available() is False
    
    # ===========================
    # Response Generation Tests
    # ===========================
    
    def test_generate_response_success(self, mock_ollama_client):
        """Test successful response generation."""
        mock_instance = MagicMock()
        mock_instance.chat.return_value = {
            "message": {
                "content": "The answer to this question is found in the document."
            }
        }
        mock_ollama_client.return_value = mock_instance
        
        service = LLMService()
        response = service.generate_response(
            question="Test question",
            context="Test context"
        )
        
        assert "found in the document" in response
    
    def test_generate_response_with_custom_prompt(self, mock_ollama_client):
        """Test response generation with custom system prompt."""
        mock_instance = MagicMock()
        mock_instance.chat.return_value = {
            "message": {"content": "Custom response"}
        }
        mock_ollama_client.return_value = mock_instance
        
        service = LLMService()
        response = service.generate_response(
            question="Test",
            context="Context",
            system_prompt="Custom system message"
        )
        
        # Verify chat was called with custom prompt
        call_args = mock_instance.chat.call_args
        messages = call_args[1]['messages']
        assert messages[0]['content'] == "Custom system message"
    
    def test_generate_response_error(self, mock_ollama_client):
        """Test response generation when LLM fails."""
        mock_instance = MagicMock()
        mock_instance.chat.side_effect = Exception("LLM error")
        mock_ollama_client.return_value = mock_instance
        
        service = LLMService()
        
        with pytest.raises(Exception) as exc_info:
            service.generate_response(
                question="Test question",
                context="Test context"
            )
        assert "LLM error" in str(exc_info.value)
    
    # ===========================
    # Prompt Formatting Tests
    # ===========================
    
    def test_format_user_message(self, mock_ollama_client):
        """Test user message formatting."""
        mock_instance = MagicMock()
        mock_ollama_client.return_value = mock_instance
        
        service = LLMService()
        message = service._format_user_message(
            question="What is this?",
            context="Context information"
        )
        
        assert "What is this?" in message
        assert "Context information" in message
        assert "Context" in message
    
    def test_default_system_prompt_exists(self, mock_ollama_client):
        """Test that default system prompt is not empty."""
        mock_instance = MagicMock()
        mock_ollama_client.return_value = mock_instance
        
        service = LLMService()
        prompt = service._get_default_system_prompt()
        
        assert len(prompt) > 50
        assert "context" in prompt.lower()
