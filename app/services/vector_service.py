"""
Vector Service - Handles embeddings and ChromaDB operations.

This module provides functionality for generating embeddings,
storing vectors, and performing similarity search.
"""

import logging
from typing import Optional
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer

from app.config import settings
from app.services.document_service import DocumentChunk

logger = logging.getLogger(__name__)


class VectorService:
    """
    Service class for vector database operations.
    
    This class handles embedding generation, vector storage,
    and similarity search using ChromaDB.
    """
    
    def __init__(self):
        """Initialize the vector service with ChromaDB and embedding model."""
        # Initialize embedding model
        logger.info(f"Loading embedding model: {settings.embedding_model}")
        self.embedding_model = SentenceTransformer(settings.embedding_model)
        logger.info(f"Embedding model loaded successfully")
        
        # Initialize ChromaDB
        self.client = chromadb.PersistentClient(
            path=settings.chroma_persist_directory,
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name=settings.chroma_collection_name,
            metadata={"hnsw:space": "cosine"}
        )
        
        logger.info(f"ChromaDB initialized. Documents in index: {self.collection.count()}")
    
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
        
        # Generate embeddings for all chunks
        texts = [chunk.content for chunk in chunks]
        embeddings = self.embedding_model.encode(texts).tolist()
        
        # Prepare data for ChromaDB
        ids = [f"{chunks[0].source}_{i}" for i in range(len(chunks))]
        metadatas = [
            {
                "source": chunk.source,
                "chunk_index": chunk.chunk_index,
                **chunk.metadata
            }
            for chunk in chunks
        ]
        
        # Add to collection
        self.collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas
        )
        
        logger.info(f"Added {len(chunks)} chunks from {chunks[0].source}")
        return len(chunks)
    
    def search(
        self,
        query: str,
        top_k: int = 3
    ) -> list[dict]:
        """
        Search for similar documents using the query.
        
        Args:
            query: The search query.
            top_k: Number of top results to return.
            
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
    
    def delete_by_source(self, source: str) -> int:
        """
        Delete all chunks for a specific source document.
        
        Args:
            source: The source filename to delete.
            
        Returns:
            int: Number of chunks deleted.
        """
        try:
            # Get IDs for this source
            results = self.collection.get(
                where={"source": source}
            )
            
            if results['ids']:
                self.collection.delete(ids=results['ids'])
                logger.info(f"Deleted {len(results['ids'])} chunks for source: {source}")
                return len(results['ids'])
            
            return 0
        except Exception as e:
            logger.error(f"Error deleting chunks: {e}")
            return 0
    
    def get_document_count(self) -> int:
        """Get total number of document chunks in the database."""
        return self.collection.count()
    
    def get_sources(self) -> list[str]:
        """Get unique source document names."""
        try:
            results = self.collection.get()
            sources = set()
            
            if results['metadatas']:
                for metadata in results['metadatas']:
                    if 'source' in metadata:
                        sources.add(metadata['source'])
            
            return list(sources)
        except Exception as e:
            logger.error(f"Error getting sources: {e}")
            return []
    
    def clear_all(self) -> None:
        """Clear all documents from the database."""
        self.client.delete_collection(settings.chroma_collection_name)
        self.collection = self.client.get_or_create_collection(
            name=settings.chroma_collection_name,
            metadata={"hnsw:space": "cosine"}
        )
        logger.info("Cleared all documents from the database")


# Singleton instance
_vector_service: Optional[VectorService] = None


def get_vector_service() -> VectorService:
    """Get or create the vector service singleton."""
    global _vector_service
    if _vector_service is None:
        _vector_service = VectorService()
    return _vector_service
