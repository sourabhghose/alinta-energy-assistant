"""Tests for generation functionality."""

import pytest
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))

from backend.rag.retrieval import AlintaRetriever
from backend.rag.generation import AlintaGenerator, RAGPipeline


class TestGeneration:
    """Test cases for LLM generation."""

    @pytest.fixture
    def generator(self):
        """Create generator instance."""
        try:
            return AlintaGenerator()
        except Exception as e:
            pytest.skip(f"Could not initialize generator: {str(e)}")

    @pytest.fixture
    def retriever(self):
        """Create retriever instance."""
        try:
            return AlintaRetriever()
        except Exception as e:
            pytest.skip(f"Could not initialize retriever: {str(e)}")

    def test_generation_simple(self, generator):
        """Test simple generation with context."""
        query = "What are the benefits of solar energy?"
        context = """
        Solar energy offers several benefits:
        - Reduces electricity bills
        - Environmentally friendly
        - Renewable energy source
        - Feed-in tariffs available
        """

        result = generator.generate(query=query, context=context)

        assert result is not None
        assert len(result.answer) > 0, "Should generate non-empty answer"
        assert isinstance(result.answer, str)
        assert result.metadata is not None

    def test_generation_with_history(self, generator):
        """Test generation with conversation history."""
        query = "What about payment options?"
        context = "You can pay your bill online, by phone, or through direct debit."

        history = [
            {"role": "user", "content": "What plans are available?"},
            {"role": "assistant", "content": "Alinta offers several electricity plans..."}
        ]

        result = generator.generate(query=query, context=context, conversation_history=history)

        assert result is not None
        assert len(result.answer) > 0

    def test_generation_metadata(self, generator):
        """Test that metadata is returned."""
        query = "How do I move house?"
        context = "To move house, call customer service at 13 13 58."

        result = generator.generate(query=query, context=context)

        assert "model" in result.metadata
        assert result.metadata["model"] is not None


class TestRAGPipeline:
    """Test cases for end-to-end RAG pipeline."""

    @pytest.fixture
    def rag_pipeline(self):
        """Create RAG pipeline instance."""
        try:
            retriever = AlintaRetriever()
            generator = AlintaGenerator()
            return RAGPipeline(retriever=retriever, generator=generator)
        except Exception as e:
            pytest.skip(f"Could not initialize RAG pipeline: {str(e)}")

    def test_rag_pipeline_end_to_end(self, rag_pipeline):
        """Test complete RAG pipeline."""
        query = "What are the benefits of solar feed-in tariffs?"

        response = rag_pipeline.answer_question(query=query)

        assert response is not None
        assert "answer" in response
        assert "sources" in response
        assert "metadata" in response

        assert len(response["answer"]) > 0
        assert isinstance(response["sources"], list)
        assert response["metadata"]["retrieved_chunks"] > 0

    def test_rag_pipeline_with_history(self, rag_pipeline):
        """Test RAG pipeline with conversation history."""
        query = "Tell me more about that."
        history = [
            {"role": "user", "content": "What plans do you offer?"},
            {"role": "assistant", "content": "We offer electricity and gas plans."}
        ]

        response = rag_pipeline.answer_question(
            query=query,
            conversation_history=history
        )

        assert response is not None
        assert len(response["answer"]) > 0

    def test_rag_pipeline_sources_citation(self, rag_pipeline):
        """Test that sources are properly cited."""
        query = "How do I pay my bill?"

        response = rag_pipeline.answer_question(query=query, top_k=3)

        assert len(response["sources"]) > 0
        for source in response["sources"]:
            assert "title" in source
            assert "url" in source
            assert len(source["url"]) > 0

    def test_rag_pipeline_no_results(self, rag_pipeline):
        """Test handling when no relevant content is found."""
        # Use a very specific query unlikely to match
        query = "xyzabc123nonsensequery"

        response = rag_pipeline.answer_question(query=query)

        assert response is not None
        assert "answer" in response
        # Should gracefully handle no results


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
