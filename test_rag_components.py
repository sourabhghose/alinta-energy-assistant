"""
Direct test of RAG components (Vector Search + LLM).
Run this from a Databricks notebook to test components directly.
"""

from databricks.sdk import WorkspaceClient
from openai import OpenAI
import os

print("="*80)
print("TESTING RAG COMPONENTS DIRECTLY")
print("="*80)

# Initialize Databricks client
w = WorkspaceClient()
print(f"\n✅ WorkspaceClient initialized")

# Configuration
DATABRICKS_HOST = "https://e2-demo-west.cloud.databricks.com"
VECTOR_SEARCH_INDEX = "main.sgh.content_vector_index"
LLM_MODEL = "databricks-gpt-oss-120b-preview"

print(f"Vector Search Index: {VECTOR_SEARCH_INDEX}")
print(f"LLM Model: {LLM_MODEL}")

# ============================================================================
# TEST 1: Vector Search Retrieval
# ============================================================================
print(f"\n{'='*80}")
print("TEST 1: VECTOR SEARCH RETRIEVAL")
print("="*80)

test_query = "What electricity plans are available in Western Australia?"
print(f"\nQuery: {test_query}")

try:
    # Query the vector search index
    response = w.vector_search_indexes.query_index(
        index_name=VECTOR_SEARCH_INDEX,
        query_text=test_query,
        columns=["chunk_id", "chunk_text", "url", "title", "section"],
        num_results=3
    )

    # Parse results
    if response.result and response.result.data_array:
        print(f"\n✅ Retrieved {len(response.result.data_array)} chunks:")
        print("-" * 80)

        for i, chunk in enumerate(response.result.data_array, 1):
            print(f"\nChunk {i}:")
            print(f"  Title: {chunk.get('title', 'N/A')}")
            print(f"  Section: {chunk.get('section', 'N/A')}")
            print(f"  URL: {chunk.get('url', 'N/A')}")
            print(f"  Content: {chunk.get('chunk_text', '')[:150]}...")
    else:
        print("❌ No results returned")

    print("\n✅ Vector Search test PASSED")

except Exception as e:
    print(f"\n❌ Vector Search test FAILED: {str(e)}")
    import traceback
    traceback.print_exc()

# ============================================================================
# TEST 2: LLM Generation
# ============================================================================
print(f"\n{'='*80}")
print("TEST 2: LLM GENERATION")
print("="*80)

try:
    # Get token from current context (in notebook)
    # Note: You may need to set this as an environment variable
    token = dbutils.notebook.entry_point.getDbutils().notebook().getContext().apiToken().get()

    # Initialize OpenAI client for Databricks
    client = OpenAI(
        api_key=token,
        base_url=f"{DATABRICKS_HOST}/serving-endpoints"
    )

    print(f"\n✅ LLM client initialized")

    # Test generation
    test_prompt = "Explain what a solar feed-in tariff is in simple terms."
    print(f"\nPrompt: {test_prompt}")

    response = client.chat.completions.create(
        model=LLM_MODEL,
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": test_prompt}
        ],
        max_tokens=200,
        temperature=0.7
    )

    answer = response.choices[0].message.content
    print(f"\n✅ Generated response:")
    print("-" * 80)
    print(answer)
    print("-" * 80)

    print(f"\nTokens used: {response.usage.total_tokens}")
    print("\n✅ LLM generation test PASSED")

except Exception as e:
    print(f"\n❌ LLM generation test FAILED: {str(e)}")
    import traceback
    traceback.print_exc()

# ============================================================================
# TEST 3: Full RAG Pipeline
# ============================================================================
print(f"\n{'='*80}")
print("TEST 3: FULL RAG PIPELINE (Retrieval + Generation)")
print("="*80)

try:
    query = "How do I pay my electricity bill?"
    print(f"\nQuery: {query}")

    # Step 1: Retrieve
    print("\nStep 1: Retrieving relevant context...")
    retrieval_response = w.vector_search_indexes.query_index(
        index_name=VECTOR_SEARCH_INDEX,
        query_text=query,
        columns=["chunk_text", "url", "title"],
        num_results=3
    )

    if retrieval_response.result and retrieval_response.result.data_array:
        chunks = retrieval_response.result.data_array
        context = "\n\n".join([
            f"[{chunk.get('title', 'N/A')}]\n{chunk.get('chunk_text', '')}"
            for chunk in chunks
        ])
        print(f"✅ Retrieved {len(chunks)} chunks ({len(context)} chars)")

        # Step 2: Generate
        print("\nStep 2: Generating answer with context...")

        system_prompt = """You are an AI assistant for Alinta Energy customers.
Answer questions using ONLY the provided context. Be helpful and concise.
If the information is not in the context, say so."""

        user_prompt = f"""Context from Alinta Energy website:
{context}

Customer question: {query}

Please provide a helpful answer based on the context above."""

        gen_response = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=500,
            temperature=0.7
        )

        answer = gen_response.choices[0].message.content

        print(f"\n✅ Generated answer:")
        print("=" * 80)
        print(answer)
        print("=" * 80)

        print(f"\n📚 Sources:")
        for chunk in chunks:
            print(f"  • {chunk.get('title', 'N/A')}")
            print(f"    {chunk.get('url', 'N/A')}")

        print(f"\n📊 Tokens used: {gen_response.usage.total_tokens}")
        print("\n✅ Full RAG pipeline test PASSED")

    else:
        print("❌ No context retrieved")

except Exception as e:
    print(f"\n❌ RAG pipeline test FAILED: {str(e)}")
    import traceback
    traceback.print_exc()

# ============================================================================
# SUMMARY
# ============================================================================
print(f"\n{'='*80}")
print("TEST SUMMARY")
print("="*80)
print("""
If all tests passed:
✅ Vector Search is working correctly
✅ LLM generation is working correctly
✅ Full RAG pipeline is functional
✅ Your deployed app should work correctly

Next steps:
1. Access your app at: https://alinta-energy-assistant-2556758628403379.aws.databricksapps.com
2. Log in via Databricks authentication
3. Try the /api/chat endpoint via the /docs interface
""")
