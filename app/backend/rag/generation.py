"""LLM generation logic for Alinta Energy RAG chatbot."""

from openai import OpenAI
from databricks.sdk import WorkspaceClient
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
        """Initialize the generator with OpenAI-compatible client."""
        try:
            # Get proper authentication token
            if settings.databricks_token:
                api_key = settings.databricks_token
                logger.info("Using provided databricks_token")
            else:
                # When running inside Databricks Apps, get token from WorkspaceClient
                logger.info("Getting token from WorkspaceClient (service principal)")
                w = WorkspaceClient(host=settings.databricks_host)
                # Get the token from the auth provider
                api_key = w.config.authenticate()
                if hasattr(api_key, 'token'):
                    api_key = api_key.token
                elif callable(api_key):
                    api_key = api_key()
                logger.info("✅ Token obtained from WorkspaceClient")

            # Initialize OpenAI client pointing to Databricks Foundation Model APIs
            self.client = OpenAI(
                api_key=api_key,
                base_url=f"{settings.databricks_host}/serving-endpoints"
            )

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
            # Build messages
            messages = [{"role": "system", "content": SYSTEM_PROMPT}]

            # Add conversation history if provided
            if conversation_history:
                # Limit history to last 5 turns to manage context length
                recent_history = conversation_history[-10:]  # Last 5 back-and-forth
                messages.extend(recent_history)

            # Add current query with context
            user_message = create_rag_prompt(query=query, context=context)
            messages.append({"role": "user", "content": user_message})

            logger.info(f"Generating response for query: {query[:100]}...")
            logger.debug(f"Context length: {len(context)} chars")

            # Call LLM
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                top_p=0.95,
                stop=None
            )

            # Extract answer
            answer = response.choices[0].message.content

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
            # Try a simple generation
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": "Say 'OK' if you can read this."}
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
