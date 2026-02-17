# Databricks notebook source
# MAGIC %md
# MAGIC # Setup Vector Search Index
# MAGIC
# MAGIC This notebook creates and configures the Mosaic AI Vector Search index for RAG retrieval.
# MAGIC
# MAGIC **Input**: main.alinta.gold_content_chunks
# MAGIC **Output**: Vector Search index with embeddings

# COMMAND ----------

from databricks.vector_search.client import VectorSearchClient
from pyspark.sql import functions as F
import time

# COMMAND ----------

# MAGIC %md
# MAGIC ## Configuration

# COMMAND ----------

# Vector Search configuration
ENDPOINT_NAME = "alinta_support_endpoint"
INDEX_NAME = "main.alinta.content_vector_index"
SOURCE_TABLE = "main.alinta.gold_content_chunks"
PRIMARY_KEY = "chunk_id"
EMBEDDING_SOURCE_COLUMN = "chunk_text"
EMBEDDING_MODEL = "databricks-gte-large-en"

print("Vector Search Configuration:")
print(f"  Endpoint: {ENDPOINT_NAME}")
print(f"  Index: {INDEX_NAME}")
print(f"  Source Table: {SOURCE_TABLE}")
print(f"  Embedding Model: {EMBEDDING_MODEL}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Initialize Vector Search Client

# COMMAND ----------

client = VectorSearchClient()
print("✅ Vector Search client initialized")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Create Vector Search Endpoint

# COMMAND ----------

# Check if endpoint exists
try:
    endpoint = client.get_endpoint(ENDPOINT_NAME)
    print(f"✅ Endpoint '{ENDPOINT_NAME}' already exists")
    print(f"   Status: {endpoint.get('endpoint_status', {}).get('state', 'Unknown')}")
except Exception as e:
    print(f"Creating new endpoint '{ENDPOINT_NAME}'...")

    # Create endpoint
    client.create_endpoint(
        name=ENDPOINT_NAME,
        endpoint_type="STANDARD"
    )

    # Wait for endpoint to be ready
    print("Waiting for endpoint to be ready...")
    while True:
        endpoint = client.get_endpoint(ENDPOINT_NAME)
        state = endpoint.get('endpoint_status', {}).get('state', 'Unknown')
        print(f"  Current state: {state}")

        if state == "ONLINE":
            print("✅ Endpoint is ready!")
            break
        elif state in ["PROVISIONING", "UPDATING"]:
            time.sleep(30)
        else:
            raise Exception(f"Endpoint creation failed with state: {state}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Verify Source Table

# COMMAND ----------

# Check source table
source_df = spark.table(SOURCE_TABLE)
record_count = source_df.count()

print(f"Source table verification:")
print(f"  Total records: {record_count}")
print(f"  Schema:")
source_df.printSchema()

# Verify required columns
required_columns = [PRIMARY_KEY, EMBEDDING_SOURCE_COLUMN]
missing_columns = [col for col in required_columns if col not in source_df.columns]

if missing_columns:
    raise ValueError(f"Missing required columns: {missing_columns}")

print("✅ Source table verified")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Create Delta Sync Index

# COMMAND ----------

# Check if index exists
try:
    existing_index = client.get_index(
        endpoint_name=ENDPOINT_NAME,
        index_name=INDEX_NAME
    )
    print(f"⚠️  Index '{INDEX_NAME}' already exists")
    print(f"   Status: {existing_index.describe().get('status', {}).get('detailed_state', 'Unknown')}")

    # Optionally delete existing index
    # Uncomment to recreate:
    # print("Deleting existing index...")
    # client.delete_index(endpoint_name=ENDPOINT_NAME, index_name=INDEX_NAME)
    # time.sleep(10)
    # print("✅ Existing index deleted")

except Exception as e:
    if "does not exist" in str(e).lower():
        print(f"Creating new index '{INDEX_NAME}'...")

        # Create Delta Sync index
        index = client.create_delta_sync_index(
            endpoint_name=ENDPOINT_NAME,
            index_name=INDEX_NAME,
            source_table_name=SOURCE_TABLE,
            primary_key=PRIMARY_KEY,
            embedding_source_column=EMBEDDING_SOURCE_COLUMN,
            embedding_model_endpoint_name=EMBEDDING_MODEL,
            pipeline_type="TRIGGERED"  # Use "CONTINUOUS" for real-time sync
        )

        print("✅ Index created successfully!")
        print(f"   Index details: {index.describe()}")
    else:
        raise e

# COMMAND ----------

# MAGIC %md
# MAGIC ## Monitor Index Build

# COMMAND ----------

print("Monitoring index build status...")
print("=" * 80)

max_wait_time = 1800  # 30 minutes
start_time = time.time()

while True:
    # Get index status
    index = client.get_index(
        endpoint_name=ENDPOINT_NAME,
        index_name=INDEX_NAME
    )

    status = index.describe()
    state = status.get('status', {}).get('detailed_state', 'Unknown')
    message = status.get('status', {}).get('message', '')

    elapsed = int(time.time() - start_time)
    print(f"[{elapsed}s] State: {state} - {message}")

    if state == "ONLINE_NO_PENDING_UPDATE":
        print("=" * 80)
        print("✅ Index is ready and up-to-date!")
        break
    elif state in ["ONLINE", "PROVISIONING", "SYNCING", "ONLINE_UPDATING"]:
        if elapsed > max_wait_time:
            print(f"⚠️  Max wait time exceeded. Index state: {state}")
            break
        time.sleep(30)
    else:
        raise Exception(f"Index build failed with state: {state} - {message}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Verify Index

# COMMAND ----------

# Get final index details
index = client.get_index(
    endpoint_name=ENDPOINT_NAME,
    index_name=INDEX_NAME
)

index_info = index.describe()

print("Index Information:")
print("=" * 80)
print(f"Name: {index_info.get('name')}")
print(f"Status: {index_info.get('status', {}).get('detailed_state')}")
print(f"Endpoint: {index_info.get('endpoint_name')}")
print(f"Primary Key: {index_info.get('primary_key')}")
print(f"Pipeline Type: {index_info.get('delta_sync_index_spec', {}).get('pipeline_type')}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Test Search

# COMMAND ----------

# Test query
test_queries = [
    "What electricity plans are available in Western Australia?",
    "How do I pay my bill online?",
    "What is a solar feed-in tariff?",
    "How can I get help with paying my energy bill?"
]

print("Testing Vector Search:")
print("=" * 80)

for query in test_queries:
    print(f"\nQuery: {query}")
    print("-" * 80)

    try:
        results = index.similarity_search(
            query_text=query,
            columns=["chunk_id", "chunk_text", "url", "title", "section"],
            num_results=3
        )

        # Parse results
        data_array = results.get("result", {}).get("data_array", [])

        if data_array:
            for i, result in enumerate(data_array, 1):
                print(f"\n{i}. {result.get('title', 'N/A')} (Section: {result.get('section', 'N/A')})")
                print(f"   URL: {result.get('url', 'N/A')}")
                print(f"   Content: {result.get('chunk_text', '')[:150]}...")
        else:
            print("   No results found")

    except Exception as e:
        print(f"   Error: {str(e)}")

print("\n" + "=" * 80)
print("✅ Vector Search testing complete!")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Sync Index (Manual Trigger)

# COMMAND ----------

# For TRIGGERED pipeline type, manually sync the index
try:
    print("Triggering manual index sync...")
    index.sync()
    print("✅ Sync triggered successfully")
except Exception as e:
    print(f"Note: {str(e)}")
    print("(Sync may not be needed if index is already up-to-date)")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Summary

# COMMAND ----------

print("🎉 Vector Search Setup Complete!")
print("=" * 80)
print(f"✅ Endpoint: {ENDPOINT_NAME}")
print(f"✅ Index: {INDEX_NAME}")
print(f"✅ Source Records: {record_count}")
print(f"✅ Embedding Model: {EMBEDDING_MODEL}")
print("\nNext Steps:")
print("1. Integrate with FastAPI backend (retrieval.py)")
print("2. Test RAG pipeline end-to-end")
print("3. Deploy chatbot application")
