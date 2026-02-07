"""
LLM Service - Handles communication with Ollama LLM.

This module provides an interface to interact with a locally running
Ollama server for generating responses to user queries.
"""

import logging
from typing import Optional
import ollama
from ollama import Client

from app.config import settings

logger = logging.getLogger(__name__)


class LLMService:
    """
    Service class for LLM operations using Ollama.
    
    This class handles all communication with the Ollama server,
    including health checks and text generation.
    """
    
    def __init__(self):
        """Initialize the LLM service with Ollama client."""
        self.client = Client(host=settings.ollama_base_url)
        self.model = settings.ollama_model
        self.timeout = settings.ollama_timeout
    
    def check_connection(self) -> bool:
        """
        Check if Ollama server is running and accessible.
        
        Returns:
            bool: True if connected, False otherwise.
        """
        try:
            self.client.list()
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Ollama: {e}")
            return False
    
    def is_model_available(self) -> bool:
        """
        Check if the configured model is available.
        
        Returns:
            bool: True if model is available, False otherwise.
        """
        try:
            models = self.client.list()
            model_names = [m['name'].split(':')[0] for m in models.get('models', [])]
            return self.model.split(':')[0] in model_names
        except Exception as e:
            logger.error(f"Failed to check model availability: {e}")
            return False
    
    def generate_response(
        self,
        question: str,
        context: str,
        system_prompt: Optional[str] = None
    ) -> str:
        """
        Generate a response using the LLM based on question and context.
        
        Args:
            question: User's question.
            context: Retrieved document context for RAG.
            system_prompt: Optional custom system prompt.
            
        Returns:
            str: Generated response from the LLM.
            
        Raises:
            Exception: If LLM generation fails.
        """
        if system_prompt is None:
            system_prompt = self._get_default_system_prompt()
        
        user_message = self._format_user_message(question, context)
        
        try:
            response = self.client.chat(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                options={"timeout": self.timeout}
            )
            return response['message']['content']
        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            raise
    
    def _get_default_system_prompt(self) -> str:
        """Get the default system prompt for RAG."""
        return """Sen yardımcı bir asistansın. Sana verilen bağlam (context) bilgilerini kullanarak soruları cevapla.

Kurallar:
1. Sadece verilen bağlamdaki bilgileri kullan.
2. Eğer cevap bağlamda yoksa, "Bu bilgi verilen dokümanlarda bulunmuyor." de.
3. Cevaplarını açık ve net tut.
4. Kaynak belirtirken hangi dokümandan bilgi aldığını söyle."""
    
    def _format_user_message(self, question: str, context: str) -> str:
        """Format the user message with context and question."""
        return f"""Bağlam (Context):
{context}

Soru: {question}

Lütfen yukarıdaki bağlamı kullanarak soruyu cevapla."""


# Singleton instance
_llm_service: Optional[LLMService] = None


def get_llm_service() -> LLMService:
    """Get or create the LLM service singleton."""
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service
