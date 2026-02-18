# Databricks notebook source
# MAGIC %md
# MAGIC # Setup Vector Search Index - Alternative Approach
# MAGIC
# MAGIC This notebook checks Vector Search availability and provides setup instructions.
# MAGIC
# MAGIC **Input**: main.sgh.gold_content_chunks
# MAGIC **Output**: Vector Search index with embeddings

# COMMAND ----------

# MAGIC %md
# MAGIC ## Check Vector Search Availability

# COMMAND ----------

# Check if Vector Search is available
import sys
print(f"Python version: {sys.version}")
print(f"\nDatabricks Runtime: {spark.conf.get('spark.databricks.clusterUsageTags.sparkVersion')}")

# Try to import Vector Search
try:
    from databricks.vector_search.client import VectorSearchClient
    print("\n✅ Vector Search client is available!")
    vector_search_available = True
except ImportError as e:
    print(f"\n⚠️ Vector Search client not available: {e}")
    print("\nVector Search might need to be set up via:")
    print("1. Databricks UI (Catalog > Create > Vector Search Index)")
    print("2. Or using Databricks CLI")
    print("3. Or using REST API")
    vector_search_available = False

# COMMAND ----------

# MAGIC %md
# MAGIC ## Alternative: Use Databricks Workspace Client

# COMMAND ----------

if not vector_search_available:
    print("Trying alternative import method...")
    try:
        from databricks.sdk import WorkspaceClient
        w = WorkspaceClient()
        print("✅ Workspace client available!")
        print("\nYou can create Vector Search index via:")
        print("1. Databricks UI")
        print("2. Databricks API")
        print("3. Contact your workspace admin")
    except ImportError as e:
        print(f"⚠️ Workspace client also not available: {e}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Verify Source Table

# COMMAND ----------

# Check if source table exists
source_table = "main.sgh.gold_content_chunks"

try:
    df = spark.table(source_table)
    count = df.count()
    print(f"✅ Source table exists: {source_table}")
    print(f"   Records: {count}")
    print(f"\nSample data:")
    df.select("chunk_id", "chunk_text", "url", "title").limit(3).show(truncate=50)
except Exception as e:
    print(f"❌ Error accessing source table: {e}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Manual Vector Search Setup Instructions
# MAGIC
# MAGIC Since Vector Search SDK is not available in this runtime, you can:
# MAGIC
# MAGIC ### Option 1: Use Databricks UI (Recommended)
# MAGIC
# MAGIC 1. Go to **Catalog** in the left sidebar
# MAGIC 2. Navigate to **main** → **sgh** → **gold_content_chunks**
# MAGIC 3. Click **"Create"** → **"Vector Search Index"**
# MAGIC 4. Configure:
# MAGIC    - **Index name**: `main.sgh.content_vector_index`
# MAGIC    - **Source table**: `main.sgh.gold_content_chunks`
# MAGIC    - **Primary key**: `chunk_id`
# MAGIC    - **Embedding column**: `chunk_text`
# MAGIC    - **Embedding model**: `databricks-gte-large-en`
# MAGIC    - **Sync mode**: Delta Sync (triggered)
# MAGIC 5. Click **"Create"**
# MAGIC 6. Wait for index to be **ONLINE** (~10-15 minutes)
# MAGIC
# MAGIC ### Option 2: Use Databricks CLI
# MAGIC
# MAGIC Run this from your terminal (not in notebook):
# MAGIC
# MAGIC ```bash
# MAGIC databricks vector-search-indexes create \
# MAGIC   --name "main.sgh.content_vector_index" \
# MAGIC   --endpoint-name "alinta_support_endpoint" \
# MAGIC   --primary-key "chunk_id" \
# MAGIC   --delta-sync-index-spec '{
# MAGIC     "source_table": "main.sgh.gold_content_chunks",
# MAGIC     "embedding_source_columns": [{"name": "chunk_text"}],
# MAGIC     "embedding_model_endpoint_name": "databricks-gte-large-en"
# MAGIC   }'
# MAGIC ```
# MAGIC
# MAGIC ### Option 3: Skip Vector Search (Use Alternative)
# MAGIC
# MAGIC You can deploy the app without Vector Search and use semantic search later,
# MAGIC or use a simple keyword search as a fallback.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Next Steps
# MAGIC
# MAGIC After creating the Vector Search index:
# MAGIC
# MAGIC 1. **Verify index status:**
# MAGIC    - Go to Catalog UI
# MAGIC    - Find your index: main.sgh.content_vector_index
# MAGIC    - Wait until status is **ONLINE**
# MAGIC
# MAGIC 2. **Test the index:**
# MAGIC    - Use the UI to run a test query
# MAGIC    - Example: "electricity plans"
# MAGIC
# MAGIC 3. **Continue with app deployment:**
# MAGIC    - Run the deploy script
# MAGIC    - The app will connect to the index automatically

# COMMAND ----------

print("=" * 60)
print("SUMMARY")
print("=" * 60)
print(f"\n✅ Source table ready: {source_table}")
print(f"✅ Records available: {count if 'count' in locals() else 'N/A'}")
print("\n⚠️  Vector Search index needs to be created manually")
print("\nNext: Create the index using one of the methods above")
print("Then: Continue with app deployment")
