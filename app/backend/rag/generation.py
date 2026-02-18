"""LLM generation logic for Alinta Energy RAG chatbot."""

from openai import OpenAI
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.serving import ChatMessage, ChatMessageRole
from typing import List, Dict, Optional
import logging
from ..config import settings
from .prompts import SYSTEM_PROMPT, create_rag_prompt, ERROR_MESSAGES

logger = logging.getLogger(__name__)


class GenerationResult:
    """Container for generation results."""

    def __init__(self, answer: str, metadata: Optional[Dict] = None):
        """
        Initialize generation result.

        Args:
            answer: Generated answer text
            metadata: Optional metadata (tokens used, model, etc.)
        """
        self.answer = answer
        self.metadata = metadata or {}

    def __str__(self) -> str:
        """String representation."""
        return self.answer


class AlintaGenerator:
    """Generator for Alinta Energy chatbot responses using LLM."""

    def __init__(self):
        """Initialize the generator with Databricks SDK."""
        try:
            # Use WorkspaceClient for authentication
            if settings.databricks_token:
                self.w = WorkspaceClient(host=settings.databricks_host, token=settings.databricks_token)
                logger.info("Using provided databricks_token")
            else:
                # When running inside Databricks Apps, use service principal auth
                self.w = WorkspaceClient(host=settings.databricks_host)
                logger.info("Using WorkspaceClient with service principal auth")

            self.model = settings.llm_model
            self.max_tokens = settings.llm_max_tokens
            self.temperature = settings.llm_temperature

            logger.info(f"✅ LLM client initialized with model: {self.model}")

        except Exception as e:
            logger.error(f"Failed to initialize LLM client: {str(e)}", exc_info=True)
            raise

    def generate(
        self,
        query: str,
        context: str,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> GenerationResult:
        """
        Generate an answer to a query using retrieved context.

        Args:
            query: User's question
            context: Retrieved context from vector search
            conversation_history: Optional list of previous messages
                                [{"role": "user", "content": "..."}, ...]

        Returns:
            GenerationResult with generated answer

        Raises:
            Exception if generation fails
        """
        try:
            # Build messages using SDK ChatMessage objects
            messages = [
                ChatMessage(role=ChatMessageRole.SYSTEM, content=SYSTEM_PROMPT)
            ]

            # Add conversation history if provided
            if conversation_history:
                # Limit history to last 5 turns to manage context length
                recent_history = conversation_history[-10:]  # Last 5 back-and-forth
                for msg in recent_history:
                    role = ChatMessageRole.USER if msg["role"] == "user" else ChatMessageRole.ASSISTANT
                    messages.append(ChatMessage(role=role, content=msg["content"]))

            # Add current query with context
            user_message = create_rag_prompt(query=query, context=context)
            messages.append(ChatMessage(role=ChatMessageRole.USER, content=user_message))

            logger.info(f"Generating response for query: {query[:100]}...")
            logger.debug(f"Context length: {len(context)} chars")

            # Call LLM using Databricks SDK
            response = self.w.serving_endpoints.query(
                name=self.model,
                messages=messages,
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )

            # Extract answer - handle both string and structured (list) responses
            content = response.choices[0].message.content
            if isinstance(content, list):
                # Structured response with reasoning blocks - extract text content
                answer = ""
                for block in content:
                    if isinstance(block, dict) and block.get("type") == "text":
                        answer += block.get("text", "")
                if not answer:
                    # Fallback: concatenate all text fields
                    answer = " ".join(str(block.get("text", "")) for block in content if isinstance(block, dict) and "text" in block)
            else:
                # Simple string response
                answer = str(content)

            # Extract metadata
            metadata = {
                "model": self.model,
                "tokens_used": response.usage.total_tokens if response.usage else None,
                "finish_reason": response.choices[0].finish_reason,
            }

            logger.info(f"Generated response ({len(answer)} chars, {metadata.get('tokens_used')} tokens)")

            return GenerationResult(answer=answer, metadata=metadata)

        except Exception as e:
            logger.error(f"Generation failed: {str(e)}")
            raise Exception(f"Failed to generate response: {str(e)}")

    def generate_simple(self, query: str, context: str) -> str:
        """
        Simple generation without conversation history.

        Args:
            query: User's question
            context: Retrieved context

        Returns:
            Generated answer string
        """
        result = self.generate(query=query, context=context, conversation_history=None)
        return result.answer

    def health_check(self) -> bool:
        """
        Check if LLM endpoint is accessible.

        Returns:
            True if healthy, False otherwise
        """
        try:
            # Try a simple generation using Databricks SDK
            response = self.w.serving_endpoints.query(
                name=self.model,
                messages=[
                    ChatMessage(role=ChatMessageRole.SYSTEM, content="You are a helpful assistant."),
                    ChatMessage(role=ChatMessageRole.USER, content="Say 'OK' if you can read this.")
                ],
                max_tokens=10,
                temperature=0
            )
            return response.choices[0].message.content is not None
        except Exception as e:
            logger.error(f"LLM health check failed: {str(e)}")
            return False


class RAGPipeline:
    """Complete RAG pipeline combining retrieval and generation."""

    def __init__(self, retriever, generator):
        """
        Initialize RAG pipeline.

        Args:
            retriever: AlintaRetriever instance
            generator: AlintaGenerator instance
        """
        self.retriever = retriever
        self.generator = generator
        logger.info("RAG pipeline initialized")

    def answer_question(
        self,
        query: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        top_k: Optional[int] = None
    ) -> Dict:
        """
        Answer a question using RAG pipeline.

        Args:
            query: User's question
            conversation_history: Optional conversation history
            top_k: Number of documents to retrieve

        Returns:
            Dictionary with answer and sources:
            {
                "answer": str,
                "sources": List[Dict],
                "metadata": Dict
            }

        Raises:
            Exception if pipeline fails
        """
        try:
            # Step 1: Retrieve relevant context
            logger.info(f"Processing query: {query[:100]}...")
            retrieval_result = self.retriever.retrieve(query=query, top_k=top_k)

            # Check if we got any results
            if not retrieval_result.chunks:
                logger.warning("No relevant content retrieved")
                return {
                    "answer": ERROR_MESSAGES["no_context"],
                    "sources": [],
                    "metadata": {"retrieved_chunks": 0}
                }

            # Step 2: Format context
            context = retrieval_result.get_context_string()

            # Step 3: Generate answer
            generation_result = self.generator.generate(
                query=query,
                context=context,
                conversation_history=conversation_history
            )

            # Step 4: Compile response
            response = {
                "answer": generation_result.answer,
                "sources": retrieval_result.get_sources(),
                "metadata": {
                    "retrieved_chunks": retrieval_result.num_results,
                    **generation_result.metadata
                }
            }

            logger.info("RAG pipeline completed successfully")
            return response

        except Exception as e:
            logger.error(f"RAG pipeline failed: {str(e)}")
            raise
