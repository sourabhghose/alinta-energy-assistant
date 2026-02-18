"""Vector search retrieval logic for Alinta Energy RAG chatbot."""

from databricks.sdk import WorkspaceClient
from databricks.sdk.service.vectorsearch import VectorSearchIndex
from typing import List, Dict, Optional
import logging
from ..config import settings

logger = logging.getLogger(__name__)


class RetrievalResult:
    """Container for retrieval results."""

    def __init__(self, chunks: List[Dict], query: str):
        """
        Initialize retrieval result.

        Args:
            chunks: List of retrieved chunks with metadata
            query: Original query text
        """
        self.chunks = chunks
        self.query = query
        self.num_results = len(chunks)

    def get_context_string(self) -> str:
        """
        Format chunks into a context string for LLM.

        Returns:
            Formatted context string
        """
        if not self.chunks:
            return "No relevant information found."

        context_parts = []
        for i, chunk in enumerate(self.chunks, 1):
            title = chunk.get("title", "Unknown")
            content = chunk.get("content", "")
            source = chunk.get("source", "")

            context_parts.append(
                f"[Source {i}: {title}]\n{content}\nURL: {source}"
            )

        return "\n\n---\n\n".join(context_parts)

    def get_sources(self) -> List[Dict[str, str]]:
        """
        Extract source metadata for citation.

        Returns:
            List of source dictionaries with title and URL
        """
        sources = []
        seen_urls = set()

        for chunk in self.chunks:
            url = chunk.get("source", "")
            if url and url not in seen_urls:
                sources.append({
                    "title": chunk.get("title", "Unknown"),
                    "url": url
                })
                seen_urls.add(url)

        return sources


class AlintaRetriever:
    """Retriever for Alinta Energy content using Vector Search."""

    def __init__(self):
        """Initialize the retriever with Vector Search client."""
        try:
            # Initialize Workspace Client
            # When running inside Databricks Apps, token can be None (uses service principal)
            if settings.databricks_token:
                self.w = WorkspaceClient(
                    host=settings.databricks_host,
                    token=settings.databricks_token
                )
            else:
                # Use default authentication (service principal in Databricks Apps)
                self.w = WorkspaceClient(host=settings.databricks_host)

            # Store index configuration
            self.endpoint_name = settings.vector_search_endpoint
            self.index_name = settings.vector_search_index

            logger.info(f"Vector Search client initialized for index: {settings.vector_search_index}")

        except Exception as e:
            logger.error(f"Failed to initialize Vector Search client: {str(e)}")
            raise

    def retrieve(
        self,
        query: str,
        top_k: Optional[int] = None,
        filters: Optional[Dict] = None
    ) -> RetrievalResult:
        """
        Retrieve relevant content chunks for a query.

        Args:
            query: User query text
            top_k: Number of results to retrieve (default from settings)
            filters: Optional filters to apply (e.g., {"section": "plans"})

        Returns:
            RetrievalResult object with chunks and metadata

        Raises:
            Exception if retrieval fails
        """
        if not query or not query.strip():
            logger.warning("Empty query provided to retrieve()")
            return RetrievalResult(chunks=[], query=query)

        try:
            # Use configured top_k if not specified
            k = top_k or settings.top_k_results

            logger.info(f"Retrieving top {k} results for query: {query[:100]}...")

            # Perform similarity search using WorkspaceClient
            response = self.w.vector_search_indexes.query_index(
                index_name=self.index_name,
                query_text=query,
                columns=["chunk_id", "chunk_text", "url", "title", "section"],
                num_results=k,
                filters=filters
            )

            # Parse results
            data_array = response.result.data_array if response.result else []

            # Format chunks
            chunks = []
            for result in data_array:
                chunk = {
                    "chunk_id": result.get("chunk_id", ""),
                    "content": result.get("chunk_text", ""),
                    "source": result.get("url", ""),
                    "title": result.get("title", ""),
                    "section": result.get("section", ""),
                }
                chunks.append(chunk)

            logger.info(f"Retrieved {len(chunks)} chunks for query")

            return RetrievalResult(chunks=chunks, query=query)

        except Exception as e:
            logger.error(f"Retrieval failed: {str(e)}")
            raise Exception(f"Failed to retrieve relevant content: {str(e)}")

    def retrieve_by_section(
        self,
        query: str,
        section: str,
        top_k: Optional[int] = None
    ) -> RetrievalResult:
        """
        Retrieve content filtered by section.

        Args:
            query: User query text
            section: Section to filter by (e.g., "plans", "help", "solar")
            top_k: Number of results to retrieve

        Returns:
            RetrievalResult object
        """
        filters = {"section": section}
        return self.retrieve(query=query, top_k=top_k, filters=filters)

    def health_check(self) -> bool:
        """
        Check if Vector Search is accessible.

        Returns:
            True if healthy, False otherwise
        """
        try:
            # Try a simple search
            self.w.vector_search_indexes.query_index(
                index_name=self.index_name,
                query_text="test",
                columns=["chunk_id"],
                num_results=1
            )
            return True
        except Exception as e:
            logger.error(f"Vector Search health check failed: {str(e)}")
            return False
