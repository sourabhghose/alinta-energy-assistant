# Alinta Energy Assistant - Deployment Guide

## ✅ Current Status

**Completed:**
- ✅ Configuration files updated for your workspace
- ✅ Frontend built successfully
- ✅ Data pipeline notebooks uploaded to workspace
- ✅ Secret scope created (`alinta-app-secrets`)

**Your workspace:** `https://e2-demo-west.cloud.databricks.com`
**Your email:** `sourabh.ghose@databricks.com`

---

## 🚀 Complete These Steps to Deploy

### STEP 1: Run Data Pipeline Notebooks (10 minutes)

1. **Open Databricks Workspace:**
   - Go to: https://e2-demo-west.cloud.databricks.com
   - Navigate to: Workspace → Users → sourabh.ghose@databricks.com → **alinta-data-pipeline**

2. **Run each notebook in order:**

   **① 01_web_scraper.py**
   - Open the notebook
   - Attach to "Shared Endpoint" warehouse (or any available cluster)
   - Click **"Run All"** at the top
   - Wait ~3-5 minutes for completion
   - ✅ Verify: You should see "Data saved to main.sgh.bronze_scraped_content"

   **② 02_process_bronze.py**
   - Open the notebook
   - Click **"Run All"**
   - Wait ~2 minutes
   - ✅ Verify: You should see "Data saved to main.sgh.silver_clean_content"

   **③ 03_create_chunks.py**
   - Open the notebook
   - Click **"Run All"**
   - Wait ~2 minutes
   - ✅ Verify: You should see "Data saved to main.sgh.gold_content_chunks"

   **④ 04_setup_vector_search.py** ⚠️ IMPORTANT
   - Open the notebook
   - Click **"Run All"**
   - Wait ~10-15 minutes (Vector Search index creation takes time)
   - ✅ Verify: You should see "✅ Index is ready and up-to-date!"
   - **DO NOT proceed to next step until you see this message**

---

### STEP 2: Add Token to Secret (2 minutes)

In your terminal, run:

```bash
# Get your token
# Option A: If you have a token
databricks secrets put-secret alinta-app-secrets databricks-token
# This will open an editor - paste your token and save

# Option B: Create a new token
# Go to: https://e2-demo-west.cloud.databricks.com/#setting/account/personalAccessTokens
# Click "Generate new token"
# Copy the token
# Then run the command above and paste it
```

---

### STEP 3: Deploy the Application (5 minutes)

Once Steps 1 and 2 are complete, run:

```bash
cd /Users/sourabh.ghose/claude_projects/alinta-energy-assistant/app
./deploy.sh
```

The script will:
- ✅ Verify frontend is built
- ✅ Package application
- ✅ Upload to workspace
- ✅ Deploy as Databricks App
- ✅ Provide your app URL

---

### STEP 4: Access Your Application

After deployment completes, get your app URL:

```bash
databricks apps get alinta-energy-assistant
```

Look for the `url` field in the output, then visit that URL in your browser!

---

## 🔍 Verification Checklist

After Step 1, verify tables were created:

```sql
-- Run in a SQL notebook or SQL editor
SHOW TABLES IN main.sgh;
```

Expected output: 3 tables
- `bronze_scraped_content`
- `silver_clean_content`
- `gold_content_chunks`

After Step 1.④, verify Vector Search index:

```python
# Run in a Python notebook
from databricks.vector_search.client import VectorSearchClient

client = VectorSearchClient()
index = client.get_index(
    endpoint_name="alinta_support_endpoint",
    index_name="main.sgh.content_vector_index"
)

# Should print status: ONLINE or ONLINE_NO_PENDING_UPDATE
print(index.describe())
```

---

## ⚡ Quick Reference

**Notebooks location:**
```
/Workspace/Users/sourabh.ghose@databricks.com/alinta-data-pipeline/
```

**Tables created:**
- `main.sgh.bronze_scraped_content` (raw HTML)
- `main.sgh.silver_clean_content` (clean text)
- `main.sgh.gold_content_chunks` (chunked for RAG)

**Vector Search:**
- Endpoint: `alinta_support_endpoint`
- Index: `main.sgh.content_vector_index`

**Secret scope:**
- Name: `alinta-app-secrets`
- Key: `databricks-token`

---

## 🆘 Troubleshooting

**Issue: Notebook fails with "catalog not found"**
```sql
-- Run this first:
CREATE CATALOG IF NOT EXISTS main;
CREATE SCHEMA IF NOT EXISTS main.sgh;
```

**Issue: Vector Search endpoint creation fails**
- This requires admin permissions
- Contact your workspace admin to create the endpoint
- Or use an existing Vector Search endpoint

**Issue: App deployment fails**
- Verify secret is created: `databricks secrets list-secrets alinta-app-secrets`
- Verify notebooks completed successfully
- Check Vector Search index status

**Issue: App shows errors**
- Check logs: `databricks apps logs alinta-energy-assistant`
- Verify Vector Search index is ONLINE
- Verify tables have data: `SELECT COUNT(*) FROM main.sgh.gold_content_chunks`

---

## 📞 Need Help?

Check the comprehensive guides:
- **README.md** - Full project documentation
- **QUICKSTART.md** - 30-minute setup guide
- **IMPLEMENTATION_CHECKLIST.md** - Detailed tracking

---

**Total Time:** ~20 minutes
**Status:** Ready to deploy after notebooks complete!
