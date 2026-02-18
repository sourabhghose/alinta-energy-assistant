# Deployment Notes

## Vector Search Setup

### Issue: Vector Search SDK Not Available
The `databricks-vector-search` package does not exist as a standalone package. The Vector Search functionality is included in `databricks-sdk`, but the Python SDK for creating indexes programmatically may not be available in all Databricks runtimes.

### Solution: Create Vector Search Index via UI

**Step 1: Navigate to Databricks Catalog**
1. Go to https://e2-demo-west.cloud.databricks.com
2. Click "Catalog" in the left sidebar
3. Navigate to: `main` → `sgh` → `gold_content_chunks`

**Step 2: Create Vector Search Index**
1. Click the "gold_content_chunks" table
2. Click "Create" button at the top
3. Select "Vector Search Index"

**Step 3: Configure Index Settings**
Fill in the following configuration:
- **Index name**: `main.sgh.content_vector_index`
- **Endpoint**: `alinta_support_endpoint` (create if needed)
- **Source table**: `main.sgh.gold_content_chunks`
- **Primary key**: `chunk_id`
- **Columns to sync**: Select ALL columns
- **Embedding source column**: `chunk_text`
- **Embedding model**: `databricks-gte-large-en`
- **Sync mode**: Triggered

**Step 4: Wait for Index Build**
1. Click "Create"
2. Wait approximately 10-15 minutes for index to build
3. Status should change to "ONLINE"

**Step 5: Verify Index Status**
Check the index status via:
- **UI**: Navigate to Catalog → main → sgh → content_vector_index
- **SQL**: `DESCRIBE VECTOR INDEX main.sgh.content_vector_index;`

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
