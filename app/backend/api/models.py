"""Pydantic models for API request/response schemas."""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict


class ChatMessage(BaseModel):
    """Individual chat message."""

    role: str = Field(..., description="Message role: 'user' or 'assistant'")
    content: str = Field(..., description="Message content")

    class Config:
        json_schema_extra = {
            "example": {
                "role": "user",
                "content": "What electricity plans are available in WA?"
            }
        }


class ChatRequest(BaseModel):
    """Request body for chat endpoint."""

    question: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="User's question"
    )
    conversation_history: Optional[List[ChatMessage]] = Field(
        default=[],
        description="Previous conversation messages"
    )
    top_k: Optional[int] = Field(
        default=None,
        ge=1,
        le=10,
        description="Number of documents to retrieve (1-10)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "question": "How do I pay my energy bill online?",
                "conversation_history": [
                    {
                        "role": "user",
                        "content": "What plans are available?"
                    },
                    {
                        "role": "assistant",
                        "content": "Alinta Energy offers several plans..."
                    }
                ]
            }
        }


class Source(BaseModel):
    """Source citation for a response."""

    title: str = Field(..., description="Document title")
    url: str = Field(..., description="Source URL")

    class Config:
        json_schema_extra = {
            "example": {
                "title": "Electricity Plans | Alinta Energy",
                "url": "https://www.alintaenergy.com.au/plans/electricity"
            }
        }


class ChatResponse(BaseModel):
    """Response body for chat endpoint."""

    answer: str = Field(..., description="Generated answer")
    sources: List[Source] = Field(
        default=[],
        description="Source documents used"
    )
    metadata: Optional[Dict] = Field(
        default={},
        description="Additional metadata (tokens used, etc.)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "answer": "To pay your energy bill online, you can log in to My Account...",
                "sources": [
                    {
                        "title": "Payment Options | Alinta Energy",
                        "url": "https://www.alintaenergy.com.au/help/payments"
                    }
                ],
                "metadata": {
                    "retrieved_chunks": 3,
                    "tokens_used": 450
                }
            }
        }


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = Field(..., description="Service status")
    service: str = Field(..., description="Service name")
    version: str = Field(..., description="Service version")
    components: Optional[Dict[str, bool]] = Field(
        default={},
        description="Component health status"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "service": "alinta-energy-assistant",
                "version": "1.0.0",
                "components": {
                    "vector_search": True,
                    "llm": True
                }
            }
        }


class ErrorResponse(BaseModel):
    """Error response."""

    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Detailed error information")

    class Config:
        json_schema_extra = {
            "example": {
                "error": "Failed to process request",
                "detail": "Vector search endpoint is unavailable"
            }
        }


class StarterQuestionsResponse(BaseModel):
    """Response for starter questions endpoint."""

    questions: List[str] = Field(..., description="List of suggested starter questions")

    class Config:
        json_schema_extra = {
            "example": {
                "questions": [
                    "What electricity plans are available in my state?",
                    "How do I pay my energy bill?",
                    "What is a solar feed-in tariff?"
                ]
            }
        }
