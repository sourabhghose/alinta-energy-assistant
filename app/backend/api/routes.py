"""API routes for Alinta Energy Assistant."""

from fastapi import APIRouter, HTTPException, status
from typing import Dict
import logging

from .models import (
    ChatRequest,
    ChatResponse,
    HealthResponse,
    ErrorResponse,
    StarterQuestionsResponse,
    Source
)
from ..rag.retrieval import AlintaRetriever
from ..rag.generation import AlintaGenerator, RAGPipeline
from ..rag.prompts import ERROR_MESSAGES, STARTER_QUESTIONS
from ..config import settings

logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter()

# Initialize RAG components (singleton pattern)
try:
    retriever = AlintaRetriever()
    generator = AlintaGenerator()
    rag_pipeline = RAGPipeline(retriever=retriever, generator=generator)
    logger.info("RAG pipeline initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize RAG pipeline: {str(e)}")
    # Allow app to start even if RAG initialization fails
    retriever = None
    generator = None
    rag_pipeline = None


@router.post(
    "/chat",
    response_model=ChatResponse,
    responses={
        500: {"model": ErrorResponse, "description": "Internal server error"},
        400: {"model": ErrorResponse, "description": "Invalid request"}
    },
    summary="Chat with AI Assistant",
    description="Send a question to the AI assistant and receive an answer with sources"
)
async def chat(request: ChatRequest) -> ChatResponse:
    """
    Main chat endpoint for the Alinta Energy Assistant.

    Processes user questions using RAG pipeline:
    1. Retrieves relevant content from vector search
    2. Generates answer using LLM with retrieved context
    3. Returns answer with source citations

    Args:
        request: ChatRequest with question and optional conversation history

    Returns:
        ChatResponse with answer and sources

    Raises:
        HTTPException: If request is invalid or processing fails
    """
    # Validate RAG pipeline is initialized
    if not rag_pipeline:
        logger.error("RAG pipeline not initialized")
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

        # Convert conversation history to dict format
        history = None
        if request.conversation_history:
            history = [
                {"role": msg.role, "content": msg.content}
                for msg in request.conversation_history
            ]

        # Run RAG pipeline
        result = rag_pipeline.answer_question(
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

        # Return user-friendly error
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ERROR_MESSAGES["generation_failed"]
        )


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health Check",
    description="Check service health and component status"
)
async def health() -> HealthResponse:
    """
    Health check endpoint.

    Returns overall service health and status of individual components
    (Vector Search, LLM endpoint).

    Returns:
        HealthResponse with service status
    """
    components = {}

    # Check Vector Search
    if retriever:
        try:
            components["vector_search"] = retriever.health_check()
        except:
            components["vector_search"] = False
    else:
        components["vector_search"] = False

    # Check LLM
    if generator:
        try:
            components["llm"] = generator.health_check()
        except:
            components["llm"] = False
    else:
        components["llm"] = False

    # Overall status
    overall_healthy = all(components.values()) and rag_pipeline is not None
    status_str = "healthy" if overall_healthy else "degraded"

    return HealthResponse(
        status=status_str,
        service=settings.app_name,
        version=settings.app_version,
        components=components
    )


@router.get(
    "/starter-questions",
    response_model=StarterQuestionsResponse,
    summary="Get Starter Questions",
    description="Get a list of suggested questions to help users get started"
)
async def get_starter_questions() -> StarterQuestionsResponse:
    """
    Get suggested starter questions.

    Returns a list of example questions that users can ask to explore
    the assistant's capabilities.

    Returns:
        StarterQuestionsResponse with list of questions
    """
    return StarterQuestionsResponse(questions=STARTER_QUESTIONS)


@router.get(
    "/",
    summary="API Root",
    description="Get API information"
)
async def root() -> Dict:
    """
    API root endpoint.

    Returns basic API information.

    Returns:
        Dictionary with API details
    """
    return {
        "service": settings.app_name,
        "version": settings.app_version,
        "status": "running",
        "endpoints": {
            "chat": "/api/chat",
            "health": "/api/health",
            "starter_questions": "/api/starter-questions",
            "docs": "/docs"
        }
    }
