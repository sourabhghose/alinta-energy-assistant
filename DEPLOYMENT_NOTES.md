# Deployment Notes

## Vector Search Setup

### Issue: Vector Search SDK Not Available
The `databricks-vector-search` package does not exist as a standalone package. The Vector Search functionality is included in `databricks-sdk`, but the Python SDK for creating indexes programmatically may not be available in all Databricks runtimes.

### Solution: Create Vector Search Index via Databricks UI

Follow these detailed steps to create the Vector Search index through the Databricks web interface:

#### Step 1: Access the Databricks Catalog

1. **Open your Databricks workspace**
   - Navigate to: `https://e2-demo-west.cloud.databricks.com` (or your workspace URL)
   - Log in with your credentials

2. **Open the Catalog**
   - In the left sidebar, click on **"Catalog"** icon (looks like a database/folder icon)
   - This opens the Unity Catalog browser

3. **Navigate to your source table**
   - Click on the catalog: **`main`**
   - Click on the schema: **`sgh`**
   - Scroll down and click on the table: **`gold_content_chunks`**

#### Step 2: Initiate Vector Search Index Creation

1. **Open the Create menu**
   - At the top of the table details page, you'll see a **"Create"** button (or "+ Create" depending on UI version)
   - Click the **"Create"** dropdown button

2. **Select Vector Search Index**
   - From the dropdown menu, select **"Vector Search Index"**
   - This opens the "Create Vector Search Index" wizard

#### Step 3: Create Vector Search Endpoint (if needed)

If you don't already have a Vector Search endpoint:

1. **In the index creation wizard**, you'll see an "Endpoint" field
2. If no endpoint exists, click **"Create new endpoint"** or **"+ New Endpoint"**
3. **Endpoint configuration:**
   - **Name**: `alinta_support_endpoint`
   - **Endpoint type**: Select **"Standard"** (recommended for production)
   - Click **"Create"**
4. Wait 2-3 minutes for the endpoint to provision (status will show "Provisioning" → "Online")

#### Step 4: Configure the Vector Search Index

Fill in the index configuration form with these exact values:

1. **Basic Settings:**
   - **Index name**: `main.sgh.content_vector_index`
     - Must be in format: `catalog.schema.index_name`
   - **Endpoint**: Select `alinta_support_endpoint` (from dropdown)
   - **Source table**: `main.sgh.gold_content_chunks`
     - Should be pre-filled if you started from the table

2. **Key Column:**
   - **Primary key**: Select `chunk_id` from dropdown
     - This uniquely identifies each chunk

3. **Sync Configuration:**
   - **Sync mode**: Select **"Triggered"** (recommended)
     - "Triggered" = Manual sync when you want
     - "Continuous" = Auto-sync on table changes (higher cost)

4. **Columns to Index:**
   - **Columns to sync**: Click **"Select all"** or manually select:
     - `chunk_id`
     - `chunk_text`
     - `url`
     - `title`
     - `section`
     - `scraped_at`
   - This ensures all metadata is available in search results

5. **Embedding Configuration:**
   - **Embedding source column**: Select `chunk_text` from dropdown
     - This is the text that will be embedded as vectors
   - **Embedding model**: Select `databricks-gte-large-en`
     - This is a high-quality English embedding model
     - Alternative: `databricks-bge-large-en` (if available)

6. **Advanced Settings** (leave as defaults):
   - **Embedding dimension**: Auto-detected (1024 for gte-large)
   - **Distance metric**: Cosine similarity (default)

#### Step 5: Create and Monitor the Index

1. **Review your configuration**
   - Double-check all fields match the values above
   - Ensure `chunk_text` is the embedding source

2. **Click "Create"**
   - The wizard will close and index creation begins
   - You'll be redirected to the index details page

3. **Monitor build progress**
   - **Status** will show:
     - "Provisioning" → "Online - Indexing" → "Online"
   - **Progress bar** shows indexing progress
   - Estimated time: 10-15 minutes for ~1000 chunks

4. **Wait for "ONLINE" status**
   - ✅ Status should eventually show: **"Online"**
   - The index is now ready to use!

#### Step 6: Verify the Index

Once the status is "Online", verify it works:

**Option A: Via UI**
1. On the index details page, click **"Query index"** button
2. Enter a test query: `"electricity plans in Western Australia"`
3. Set number of results: `3`
4. Click **"Run query"**
5. You should see relevant chunks returned with similarity scores

**Option B: Via SQL Notebook**
```sql
-- Describe the index
DESCRIBE VECTOR INDEX main.sgh.content_vector_index;

-- Query the index
SELECT * FROM VECTOR_SEARCH(
  index => 'main.sgh.content_vector_index',
  query => 'electricity plans in Western Australia',
  num_results => 3
);
```

**Option C: Via Python Notebook**
```python
from databricks.sdk import WorkspaceClient

w = WorkspaceClient()

# Query the index
results = w.vector_search_indexes.query_index(
    index_name="main.sgh.content_vector_index",
    query_text="electricity plans in Western Australia",
    num_results=3
)

# Display results
for item in results.result.data_array:
    print(f"Title: {item.get('title')}")
    print(f"Content: {item.get('chunk_text')[:100]}...")
    print(f"URL: {item.get('url')}")
    print("-" * 80)
```

#### Troubleshooting

**Issue: "Endpoint not found"**
- Solution: Create the endpoint first (see Step 3)
- Wait for endpoint status to be "Online" before creating index

**Issue: "Table not found"**
- Solution: Verify the data pipeline notebooks completed successfully
- Check that `main.sgh.gold_content_chunks` table exists

**Issue: "Embedding model not available"**
- Solution: Try alternative model: `databricks-bge-large-en`
- Contact Databricks support if no models are available

**Issue: Index stuck at "Provisioning"**
- Solution: Wait 5 more minutes (initial provisioning can be slow)
- If still stuck after 30 minutes, delete and recreate the index

**Issue: "No results returned" when querying**
- Solution: Check that the source table has data:
  ```sql
  SELECT COUNT(*) FROM main.sgh.gold_content_chunks;
  ```
- Ensure indexing completed (status = "Online", not "Online - Indexing")

### Helper Script
Use `check-vector-search-status.sh` to see instructions for checking index status.

---

## Databricks Apps Deployment

### Critical Learning: File Upload Format

**Issue**: Python files uploaded with `--format SOURCE` are stored as Databricks notebooks, which cannot be imported as regular Python modules.

**Solution**: Upload Python application files with `--format RAW`:

```bash
# CORRECT - Upload as RAW file
databricks workspace import --file app.py --format RAW /path/to/app.py

# INCORRECT - Upload as SOURCE (notebook format)
databricks workspace import --file app.py --format SOURCE --language PYTHON /path/to/app.py
```

### App Structure

The minimal working structure for a FastAPI Databricks App:

```
/Workspace/Users/{user}/apps/alinta-energy-assistant/
├── app.py              # Main FastAPI application (RAW format)
├── app.yaml            # Databricks Apps configuration
├── requirements.txt    # Python dependencies (RAW format)
└── backend/            # Additional modules
    ├── __init__.py
    ├── config.py
    └── rag/
        ├── __init__.py
        ├── retrieval.py
        └── generation.py
```

### app.yaml Configuration

**Working Configuration:**
```yaml
# Use array format for command, not shell string
command: ["uvicorn", "app:app", "--host", "0.0.0.0"]

env:
  - name: DATABRICKS_HOST
    value: "https://your-workspace.cloud.databricks.com"
  - name: DEBUG
    value: "false"
```

**Key Points:**
- Use array format: `["uvicorn", "app:app"]`
- NOT: `["sh", "-c", "python -m uvicorn ..."]`
- The PORT environment variable is automatically set by Databricks Apps
- Uvicorn will use the PORT variable if not explicitly specified

### Backend Code Changes for Databricks Apps

**1. Vector Search Client (retrieval.py)**
```python
from databricks.sdk import WorkspaceClient

# Use WorkspaceClient instead of VectorSearchClient
w = WorkspaceClient(host=settings.databricks_host, token=settings.databricks_token)

# Query index using workspace client
response = w.vector_search_indexes.query_index(
    index_name="main.sgh.content_vector_index",
    query_text=query,
    columns=["chunk_id", "chunk_text", "url", "title"],
    num_results=k
)
```

**2. Make Token Optional (config.py)**
```python
# Token is optional when running inside Databricks Apps (uses service principal)
databricks_token: Optional[str] = os.getenv("DATABRICKS_TOKEN", None)
```

**3. Lazy Loading (routes.py)**
```python
# Initialize RAG components lazily to prevent startup failures
def get_rag_pipeline():
    global _rag_pipeline
    if _rag_pipeline is None:
        _retriever = AlintaRetriever()
        _generator = AlintaGenerator()
        _rag_pipeline = RAGPipeline(_retriever, _generator)
    return _rag_pipeline
```

### Deployment Commands

```bash
# 1. Upload files (use RAW format for .py files!)
databricks workspace import --file app/app.py --format RAW \
  /Workspace/Users/{user}/apps/alinta-energy-assistant/app.py

databricks workspace import --file app/app.yaml --format RAW \
  /Workspace/Users/{user}/apps/alinta-energy-assistant/app.yaml

databricks workspace import --file app/requirements.txt --format RAW \
  /Workspace/Users/{user}/apps/alinta-energy-assistant/requirements.txt

# 2. Deploy the app
databricks apps deploy alinta-energy-assistant \
  --source-code-path /Workspace/Users/{user}/apps/alinta-energy-assistant

# 3. Check status
databricks apps get alinta-energy-assistant

# 4. View logs (if deployment fails)
# Access via UI or browser: https://your-app-url.databricksapps.com/logz
```

### Troubleshooting

**Error: "Could not import module 'app'"**
- **Cause**: Python file was uploaded with `--format SOURCE` instead of `--format RAW`
- **Solution**: Delete the file and re-upload with `--format RAW`

**Error: "app crashed unexpectedly"**
- **Solution**: Check logs at `https://your-app-url/logz`
- Common causes:
  - Import errors (wrong file format)
  - Missing dependencies in requirements.txt
  - Port configuration issues
  - Module import path problems

**Error: "Error installing packages"**
- **Cause**: Invalid package name in requirements.txt
- **Example**: `databricks-vector-search` doesn't exist (use `databricks-sdk` instead)

### Current Deployment Status

✅ **Basic FastAPI app deployed successfully**
- App URL: https://alinta-energy-assistant-2556758628403379.aws.databricksapps.com
- Status: RUNNING
- Health endpoint: `/api/health`

⏳ **Pending Integration:**
- Full RAG backend (retrieval + generation)
- React frontend with chat interface
- Secret management for API tokens
- Production error handling and monitoring

---

## Next Steps

1. **Integrate Full Backend:**
   - Upload remaining backend modules as RAW files
   - Test Vector Search connectivity
   - Test LLM endpoint connectivity
   - Implement chat endpoint

2. **Add Frontend:**
   - Build React frontend (`npm run build`)
   - Upload dist folder
   - Configure FastAPI to serve static files

3. **Production Readiness:**
   - Set up secret management for tokens
   - Configure proper error handling
   - Add monitoring and logging
   - Test end-to-end RAG pipeline

4. **Documentation:**
   - Update README with deployment instructions
   - Document API endpoints
   - Add troubleshooting guide
