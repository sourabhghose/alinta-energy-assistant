"""FastAPI application for Alinta Energy Assistant with full RAG integration."""

import sys
from pathlib import Path

# Add current directory to Python path for backend imports
current_dir = Path(__file__).parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional, Dict
import logging
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Alinta Energy Assistant",
    version="1.0.0",
    description="AI-powered customer support assistant for Alinta Energy"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# Models
# ============================================================================

class ChatMessage(BaseModel):
    """Single chat message."""
    role: str  # "user" or "assistant"
    content: str

class ChatRequest(BaseModel):
    """Chat request from user."""
    question: str
    conversation_history: Optional[List[ChatMessage]] = []
    top_k: Optional[int] = 3

class Source(BaseModel):
    """Source citation."""
    title: str
    url: str

class ChatResponse(BaseModel):
    """Chat response to user."""
    answer: str
    sources: List[Source]
    metadata: Optional[Dict] = {}

class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    service: str
    version: str
    components: Optional[Dict] = {}

# ============================================================================
# RAG Components (Lazy Loading)
# ============================================================================

_rag_pipeline = None
_initialization_error = None

def get_rag_pipeline():
    """Lazy initialize and return RAG pipeline."""
    global _rag_pipeline, _initialization_error

    if _rag_pipeline is not None:
        return _rag_pipeline

    if _initialization_error is not None:
        raise _initialization_error

    try:
        logger.info("Initializing RAG pipeline...")
        logger.info(f"Python path: {sys.path[:3]}")
        logger.info(f"Current directory: {Path(__file__).parent}")

        # Import here to avoid startup failures
        logger.info("Importing backend modules...")
        from backend.rag.retrieval import AlintaRetriever
        from backend.rag.generation import AlintaGenerator, RAGPipeline
        logger.info("✅ Backend modules imported successfully")

        logger.info("Initializing retriever...")
        retriever = AlintaRetriever()
        logger.info("✅ Retriever initialized")

        logger.info("Initializing generator...")
        generator = AlintaGenerator()
        logger.info("✅ Generator initialized")

        logger.info("Creating RAG pipeline...")
        _rag_pipeline = RAGPipeline(retriever=retriever, generator=generator)

        logger.info("✅ RAG pipeline initialized successfully")
        return _rag_pipeline

    except Exception as e:
        logger.error(f"❌ Failed to initialize RAG pipeline: {str(e)}", exc_info=True)
        _initialization_error = e
        raise

# ============================================================================
# API Endpoints
# ============================================================================

@app.get("/api")
async def api_info():
    """API information endpoint."""
    return {
        "message": "Alinta Energy Assistant API",
        "status": "running",
        "version": "1.0.0",
        "endpoints": {
            "chat": "/api/chat",
            "health": "/api/health",
            "docs": "/docs"
        }
    }

@app.get("/api/health", response_model=HealthResponse)
async def health():
    """Health check endpoint."""
    components = {}

    # Try to check RAG components
    try:
        pipeline = get_rag_pipeline()
        components["rag_pipeline"] = True

        # Check retriever
        if hasattr(pipeline, 'retriever'):
            try:
                components["vector_search"] = pipeline.retriever.health_check()
            except:
                components["vector_search"] = False

        # Check generator
        if hasattr(pipeline, 'generator'):
            try:
                components["llm"] = pipeline.generator.health_check()
            except:
                components["llm"] = False

    except Exception as e:
        logger.warning(f"RAG pipeline not available: {str(e)}")
        components["rag_pipeline"] = False
        components["vector_search"] = False
        components["llm"] = False

    overall_healthy = all(components.values())
    status_str = "healthy" if overall_healthy else "degraded"

    return HealthResponse(
        status=status_str,
        service="alinta-energy-assistant",
        version="1.0.0",
        components=components
    )

@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Main chat endpoint for RAG-powered responses.

    Process user questions using:
    1. Vector Search retrieval
    2. LLM generation with context
    3. Source citations
    """
    # Get RAG pipeline
    try:
        pipeline = get_rag_pipeline()
    except Exception as e:
        logger.error(f"RAG pipeline not available: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service is initializing. Please try again in a moment."
        )

    # Validate question
    question = request.question.strip()
    if not question:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Question cannot be empty"
        )

    try:
        logger.info(f"Processing chat request: {question[:100]}...")

        # Convert conversation history
        history = None
        if request.conversation_history:
            history = [
                {"role": msg.role, "content": msg.content}
                for msg in request.conversation_history
            ]

        # Run RAG pipeline
        result = pipeline.answer_question(
            query=question,
            conversation_history=history,
            top_k=request.top_k
        )

        # Format response
        response = ChatResponse(
            answer=result["answer"],
            sources=[Source(**src) for src in result["sources"]],
            metadata=result.get("metadata", {})
        )

        logger.info("Chat request completed successfully")
        return response

    except Exception as e:
        logger.error(f"Chat request failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process your question. Please try again."
        )

@app.get("/api/v1/health", response_model=HealthResponse)
async def health_v1():
    """Health check endpoint (v1 for OAuth compatibility)."""
    return await health()

# ============================================================================
# Frontend Static Files (if built)
# ============================================================================

frontend_dist_path = Path(__file__).parent / "dist"

if frontend_dist_path.exists() and frontend_dist_path.is_dir():
    logger.info(f"Serving frontend from: {frontend_dist_path}")

    # Serve static assets
    app.mount(
        "/assets",
        StaticFiles(directory=str(frontend_dist_path / "assets")),
        name="assets"
    )

    # Serve index.html for root path
    @app.get("/")
    async def serve_root():
        """Serve React frontend at root."""
        index_path = frontend_dist_path / "index.html"
        if index_path.exists():
            return FileResponse(str(index_path))
        else:
            raise HTTPException(status_code=404, detail="Frontend not built")

    # Serve logo and other static files from dist root
    @app.get("/{filename}.{ext}")
    async def serve_static_file(filename: str, ext: str):
        """Serve static files like logo from dist root."""
        if ext in ["svg", "png", "jpg", "ico"]:
            file_path = frontend_dist_path / f"{filename}.{ext}"
            if file_path.exists():
                return FileResponse(str(file_path))
        raise HTTPException(status_code=404, detail="File not found")

    # Serve index.html for all other non-API routes (SPA support)
    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        """Serve React frontend for all non-API routes."""
        # Don't intercept API routes or docs
        if full_path.startswith("api") or full_path.startswith("docs") or full_path.startswith("redoc"):
            raise HTTPException(status_code=404, detail="Not found")

        # Serve index.html for SPA routing
        index_path = frontend_dist_path / "index.html"
        if index_path.exists():
            return FileResponse(str(index_path))
        else:
            raise HTTPException(status_code=404, detail="Frontend not built")
else:
    logger.warning(f"Frontend dist directory not found at: {frontend_dist_path}")
    logger.warning("API-only mode. Frontend not available.")

    # Fallback root endpoint when frontend is not available
    @app.get("/")
    async def root_fallback():
        """Root endpoint when frontend is not built."""
        return {
            "message": "Alinta Energy Assistant API",
            "status": "running",
            "version": "1.0.0",
            "note": "Frontend not built. API available at /api/chat",
            "endpoints": {
                "chat": "/api/chat",
                "health": "/api/health",
                "docs": "/docs"
            }
        }
