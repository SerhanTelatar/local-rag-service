"""
Vector Service - Handles vector database operations with ChromaDB.

This module provides functionality for storing document embeddings
and performing similarity searches for RAG.
"""

import logging
from typing import Optional
from pathlib import Path

import chromadb
from chromadb.config import Settings as ChromaSettings
from sentence_transformers import SentenceTransformer

from app.config import settings
from app.services.document_service import DocumentChunk

logger = logging.getLogger(__name__)


class VectorService:
    """
    Service class for vector database operations.
    
    This class handles embedding generation, storage in ChromaDB,
    and similarity search for document retrieval.
    """
    
    def __init__(self):
        """Initialize the vector service with ChromaDB and embedding model."""
        # Initialize ChromaDB
        self.client = chromadb.PersistentClient(
            path=settings.chroma_persist_directory,
            settings=ChromaSettings(anonymized_telemetry=False)
        )
        
        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name=settings.chroma_collection_name,
            metadata={"hnsw:space": "cosine"}
        )
        
        # Initialize embedding model
        logger.info(f"Loading embedding model: {settings.embedding_model}")
        self.embedding_model = SentenceTransformer(settings.embedding_model)
        logger.info("Embedding model loaded successfully")
    
    def add_chunks(self, chunks: list[DocumentChunk]) -> int:
        """
        Add document chunks to the vector database.
        
        Args:
            chunks: List of DocumentChunk objects to add.
            
        Returns:
            int: Number of chunks added.
        """
        if not chunks:
            return 0
        
        # Prepare data for ChromaDB
        documents = []
        metadatas = []
        ids = []
        
        for chunk in chunks:
            doc_id = f"{chunk.source}_{chunk.chunk_index}"
            documents.append(chunk.content)
            metadatas.append({
                "source": chunk.source,
                "chunk_index": chunk.chunk_index,
                **chunk.metadata
            })
            ids.append(doc_id)
        
        # Generate embeddings
        embeddings = self.embedding_model.encode(documents).tolist()
        
        # Add to collection
        self.collection.add(
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas,
            ids=ids
        )
        
        logger.info(f"Added {len(chunks)} chunks to vector database")
        return len(chunks)
    
    def search(
        self,
        query: str,
        top_k: int = 3
    ) -> list[dict]:
        """
        Search for similar documents based on query.
        
        Args:
            query: Search query string.
            top_k: Number of results to return.
            
        Returns:
            List of dictionaries with content, source, and score.
        """
        if self.collection.count() == 0:
            return []
        
        # Generate query embedding
        query_embedding = self.embedding_model.encode([query]).tolist()
        
        # Search in ChromaDB
        results = self.collection.query(
            query_embeddings=query_embedding,
            n_results=min(top_k, self.collection.count())
        )
        
        # Format results
        formatted_results = []
        
        if results['documents'] and results['documents'][0]:
            for i, doc in enumerate(results['documents'][0]):
                formatted_results.append({
                    "content": doc,
                    "source": results['metadatas'][0][i].get('source', 'unknown'),
                    "score": 1 - results['distances'][0][i] if results['distances'] else 0.0
                })
        
        return formatted_results
    
    def get_document_count(self) -> int:
        """
        Get the total number of chunks in the collection.
        
        Returns:
            int: Number of stored chunks.
        """
        return self.collection.count()
    
    def get_sources(self) -> list[str]:
        """
        Get list of unique source documents.
        
        Returns:
            List of source filenames.
        """
        if self.collection.count() == 0:
            return []
        
        # Get all metadata
        results = self.collection.get()
        
        if results['metadatas']:
            sources = set(m.get('source', '') for m in results['metadatas'])
            return list(sources)
        
        return []
    
    def delete_by_source(self, source: str) -> int:
        """
        Delete all chunks from a specific source.
        
        Args:
            source: Source filename to delete.
            
        Returns:
            int: Number of chunks deleted.
        """
        # Get IDs for the source
        results = self.collection.get(
            where={"source": source}
        )
        
        if results['ids']:
            count = len(results['ids'])
            self.collection.delete(ids=results['ids'])
            logger.info(f"Deleted {count} chunks from source: {source}")
            return count
        
        return 0
    
    def clear_all(self) -> int:
        """
        Clear all documents from the collection.
        
        Returns:
            int: Number of chunks deleted.
        """
        count = self.collection.count()
        
        if count > 0:
            # Delete the collection and recreate it
            self.client.delete_collection(settings.chroma_collection_name)
            self.collection = self.client.create_collection(
                name=settings.chroma_collection_name,
                metadata={"hnsw:space": "cosine"}
            )
            logger.info(f"Cleared {count} chunks from vector database")
        
        return count


# Singleton instance
_vector_service: Optional[VectorService] = None


def get_vector_service() -> VectorService:
    """Get or create the vector service singleton."""
    global _vector_service
    if _vector_service is None:
        _vector_service = VectorService()
    return _vector_service
