"""
Main Application Entry Point.

This module creates and configures the FastAPI application
for the document question-answering service.
"""

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.api.routes import router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup and shutdown."""
    # Startup
    logger.info(f"Starting {settings.app_name}...")
    logger.info(f"Ollama URL: {settings.ollama_base_url}")
    logger.info(f"Model: {settings.ollama_model}")
    
    # Pre-load services (optional - can be lazy loaded)
    try:
        from app.services.vector_service import get_vector_service
        get_vector_service()
        logger.info("Vector service initialized")
    except Exception as e:
        logger.warning(f"Failed to initialize vector service: {e}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down...")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    description="""
    Local LLM Document Question-Answering Service.
    
    This service allows you to ask questions about your uploaded documents.
    Using the RAG (Retrieval-Augmented Generation) approach,
    it generates answers based on the information in your documents.
    
    ## Features
    
    - 📄 PDF, TXT, MD, DOCX file support
    - 🔍 Semantic search to find relevant sections
    - 🤖 Local LLM (Ollama) for answer generation
    - ⚡ Fast and private - your data stays local
    """,
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router, prefix="/api", tags=["API"])

# Serve static files
static_dir = Path(__file__).parent.parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


@app.get("/", include_in_schema=False)
async def root():
    """Serve the frontend application."""
    index_path = static_dir / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    return {"message": "Local RAG Service API", "docs": "/docs"}


@app.get("/health", include_in_schema=False)
async def health_redirect():
    """Redirect root health check to API health."""
    from app.api.routes import health_check
    return await health_check()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug
    )
