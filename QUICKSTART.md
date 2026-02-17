# Alinta Energy Assistant - Quick Start Guide

This guide will get you up and running in **30 minutes**.

## 🎯 Prerequisites Checklist

Before starting, ensure you have:

- [ ] Databricks Workspace (AWS/Azure/GCP)
- [ ] Unity Catalog enabled in your workspace
- [ ] Personal Access Token (PAT) - [How to create](https://docs.databricks.com/dev-tools/auth.html#databricks-personal-access-tokens)
- [ ] Python 3.10+ installed locally
- [ ] Node.js 18+ installed (for frontend)
- [ ] Databricks CLI configured (`databricks configure`)

## 📋 Step-by-Step Setup

### Phase 1: Data Pipeline (15 minutes)

#### 1.1 Upload Notebooks to Workspace

```bash
# Navigate to project directory
cd alinta-energy-assistant

# Upload data pipeline notebooks
databricks workspace import-dir \
  data_pipeline/notebooks \
  /Workspace/Users/<your-email>/alinta-data-pipeline
```

#### 1.2 Create Unity Catalog Schema

In Databricks SQL Editor or notebook:

```sql
-- Create catalog (if needed)
CREATE CATALOG IF NOT EXISTS main;

-- Create schema
CREATE SCHEMA IF NOT EXISTS main.alinta;

-- Verify
SHOW SCHEMAS IN main;
```

#### 1.3 Run Data Pipeline Notebooks

Open Databricks Workspace and run notebooks in order:

1. **01_web_scraper.py**
   - Scrapes Alinta Energy website
   - Creates `main.alinta.bronze_scraped_content`
   - Expected runtime: ~3-5 minutes

2. **02_process_bronze.py**
   - Cleans HTML content
   - Creates `main.alinta.silver_clean_content`
   - Expected runtime: ~2 minutes

3. **03_create_chunks.py**
   - Chunks content for RAG
   - Creates `main.alinta.gold_content_chunks`
   - Expected runtime: ~2 minutes

4. **04_setup_vector_search.py**
   - Creates Vector Search endpoint and index
   - Expected runtime: ~5-10 minutes (endpoint provisioning)
   - ⚠️ **Wait for index to be ONLINE before proceeding**

#### 1.4 Verify Data Pipeline

```python
# In Databricks notebook
display(spark.table("main.alinta.gold_content_chunks"))

# Expected: 50-200 chunks depending on website content
```

### Phase 2: Application Setup (10 minutes)

#### 2.1 Configure Environment

```bash
cd app

# Copy environment template
cp .env.example .env

# Edit .env with your credentials
nano .env
```

Update `.env`:
```bash
DATABRICKS_HOST=https://your-workspace-id.cloud.databricks.com
DATABRICKS_TOKEN=dapi1234567890abcdef  # Your PAT token
```

#### 2.2 Install Dependencies

```bash
# Backend dependencies
pip install -r requirements.txt

# Frontend dependencies
cd frontend
npm install
cd ..
```

#### 2.3 Build Frontend

```bash
cd frontend
npm run build
cd ..

# Verify build
ls -lh dist/
```

### Phase 3: Testing Locally (5 minutes)

#### 3.1 Start Backend Server

```bash
# From app/ directory
uvicorn backend.main:app --reload --port 8000
```

Expected output:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete
```

#### 3.2 Test API

Open new terminal:

```bash
# Health check
curl http://localhost:8000/api/health

# Expected response:
# {"status":"healthy","service":"Alinta Energy Assistant",...}

# Test chat
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What electricity plans are available?",
    "conversation_history": []
  }'
```

#### 3.3 Test Frontend

Open browser: http://localhost:8000

- Should see Alinta Energy Assistant interface
- Try asking: "What electricity plans are available?"
- Verify sources are displayed

### Phase 4: Deploy to Databricks (5 minutes)

#### 4.1 Update Deployment Configuration

Edit `app.yaml`:
```yaml
env:
  - name: DATABRICKS_HOST
    value: "https://your-actual-workspace.cloud.databricks.com"  # ← Update this
```

#### 4.2 Store Secrets

```bash
# Create secret scope (one-time)
databricks secrets create-scope alinta-app-secrets

# Store token
databricks secrets put-secret alinta-app-secrets databricks-token
# Paste your token when prompted
```

Update `app.yaml` to use secret:
```yaml
env:
  - name: DATABRICKS_TOKEN
    valueFrom:
      secretKeyRef:
        name: databricks-token
        key: token
```

#### 4.3 Deploy

```bash
# Make deploy script executable
chmod +x deploy.sh

# Run deployment
./deploy.sh
```

Expected output:
```
✅ Frontend built successfully
✅ Files uploaded to workspace
✅ App deployed successfully
```

#### 4.4 Get App URL

```bash
databricks apps get alinta-energy-assistant
```

Look for `url` field in output. Visit that URL to access your deployed app!

## 🎉 Success Checklist

- [ ] Data pipeline completed (Bronze → Silver → Gold)
- [ ] Vector Search index is ONLINE
- [ ] Local testing successful
- [ ] App deployed to Databricks
- [ ] Can access app via Databricks Apps URL
- [ ] Chat responses include source citations

## 🐛 Troubleshooting

### Issue: Vector Search index not ready

**Solution:**
```python
# Check index status
from databricks.vector_search.client import VectorSearchClient

client = VectorSearchClient()
index = client.get_index(
    endpoint_name="alinta_support_endpoint",
    index_name="main.alinta.content_vector_index"
)

print(index.describe())
# Wait until status = "ONLINE_NO_PENDING_UPDATE"
```

### Issue: Local backend can't connect to Databricks

**Solution:**
```bash
# Test authentication
databricks auth login

# Verify token
databricks current-user me
```

### Issue: Frontend not loading

**Solution:**
```bash
# Rebuild frontend
cd app/frontend
rm -rf dist node_modules
npm install
npm run build

# Verify dist exists
ls ../dist/
```

### Issue: App deployment fails

**Solution:**
```bash
# Check Databricks CLI configuration
databricks auth profiles

# Test workspace access
databricks workspace ls /Workspace/Users

# Check permissions
databricks apps list
```

## 📚 Next Steps

1. **Schedule Data Updates**
   - Create Databricks Job to run `01_web_scraper.py` daily
   - Set schedule: Daily at 2 AM

2. **Monitor Performance**
   - Check app logs: `databricks apps logs alinta-energy-assistant`
   - Monitor Vector Search metrics in Databricks UI

3. **Customize Content**
   - Edit system prompt: `app/backend/rag/prompts.py`
   - Update scraping URLs: `data_pipeline/config/scraping_config.yaml`
   - Customize styling: `app/frontend/src/styles/alinta-theme.css`

4. **Run Tests**
   ```bash
   cd tests
   pip install -r requirements.txt
   pytest -v
   ```

5. **Evaluate Quality**
   - Use `tests/evaluation_dataset.json` for testing
   - Collect user feedback
   - Iterate on prompts and retrieval settings

## 💡 Pro Tips

1. **Development Workflow**
   - Use local testing for fast iteration
   - Deploy to Databricks Apps when stable
   - Use `.env` for local, secrets for production

2. **Cost Optimization**
   - Use TRIGGERED sync for Vector Search (not CONTINUOUS)
   - Cache common queries
   - Monitor token usage

3. **Performance Tuning**
   - Adjust `top_k` (default: 3) for retrieval
   - Tune chunk size in scraping config
   - Experiment with temperature (0.7)

4. **Monitoring**
   - Set up alerts for app downtime
   - Track response latency
   - Monitor Vector Search index size

## 🎓 Learning Resources

- [Databricks RAG Tutorial](https://docs.databricks.com/aws/en/generative-ai/tutorials/ai-cookbook/index.html)
- [Vector Search Guide](https://docs.databricks.com/en/generative-ai/vector-search.html)
- [Databricks Apps Docs](https://docs.databricks.com/en/dev-tools/databricks-apps/index.html)

## 🆘 Getting Help

- **Documentation**: See README.md for detailed info
- **Issues**: Check GitHub Issues for known problems
- **Community**: Databricks Community Forum
- **Support**: Contact your Databricks account team

---

**Total Setup Time: ~30 minutes** ⏱️

**Congratulations!** 🎉 You now have a production RAG chatbot running on Databricks!
