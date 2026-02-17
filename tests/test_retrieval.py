"""Tests for retrieval functionality."""

import pytest
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))

from backend.rag.retrieval import AlintaRetriever


class TestRetrieval:
    """Test cases for vector search retrieval."""

    @pytest.fixture
    def retriever(self):
        """Create retriever instance."""
        try:
            return AlintaRetriever()
        except Exception as e:
            pytest.skip(f"Could not initialize retriever: {str(e)}")

    def test_retrieval_electricity_plans(self, retriever):
        """Test retrieval for electricity plans query."""
        result = retriever.retrieve("What electricity plans are available in WA?", top_k=3)

        assert result is not None
        assert len(result.chunks) > 0, "Should retrieve at least one chunk"
        assert all("url" in chunk for chunk in result.chunks), "All chunks should have URL"
        assert all("content" in chunk for chunk in result.chunks), "All chunks should have content"

        # Check content relevance
        combined_content = " ".join([c["content"].lower() for c in result.chunks])
        assert any(keyword in combined_content for keyword in ["electricity", "plan", "wa", "western australia"]), \
            "Retrieved content should be relevant to electricity plans"

    def test_retrieval_billing(self, retriever):
        """Test retrieval for billing query."""
        result = retriever.retrieve("How do I pay my bill?", top_k=3)

        assert len(result.chunks) > 0
        combined_content = " ".join([c["content"].lower() for c in result.chunks])
        assert any(keyword in combined_content for keyword in ["billing", "payment", "pay", "bill"]), \
            "Should retrieve billing-related content"

    def test_retrieval_solar(self, retriever):
        """Test retrieval for solar query."""
        result = retriever.retrieve("What is a solar feed-in tariff?", top_k=3)

        assert len(result.chunks) > 0
        combined_content = " ".join([c["content"].lower() for c in result.chunks])
        assert any(keyword in combined_content for keyword in ["solar", "feed-in", "tariff"]), \
            "Should retrieve solar-related content"

    def test_retrieval_empty_query(self, retriever):
        """Test handling of empty query."""
        result = retriever.retrieve("", top_k=3)
        assert result.num_results == 0, "Empty query should return no results"

    def test_retrieval_top_k(self, retriever):
        """Test that top_k parameter works correctly."""
        result_3 = retriever.retrieve("energy plans", top_k=3)
        result_5 = retriever.retrieve("energy plans", top_k=5)

        assert len(result_3.chunks) <= 3
        assert len(result_5.chunks) <= 5
        assert len(result_5.chunks) >= len(result_3.chunks)

    def test_context_string_formatting(self, retriever):
        """Test context string formatting."""
        result = retriever.retrieve("electricity plans", top_k=2)

        context = result.get_context_string()
        assert isinstance(context, str)
        assert len(context) > 0

        # Check that sources are included in context
        if result.chunks:
            assert any(chunk["title"] in context for chunk in result.chunks), \
                "Context should include source titles"

    def test_sources_extraction(self, retriever):
        """Test source metadata extraction."""
        result = retriever.retrieve("energy plans", top_k=3)

        sources = result.get_sources()
        assert isinstance(sources, list)
        assert all("title" in src and "url" in src for src in sources), \
            "All sources should have title and URL"

        # Check for duplicate removal
        urls = [src["url"] for src in sources]
        assert len(urls) == len(set(urls)), "Sources should not contain duplicate URLs"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
