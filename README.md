# Alinta Energy AI Customer Support Assistant

A production-grade Retrieval Augmented Generation (RAG) chatbot for Alinta Energy customers, providing 24/7 AI-powered support for questions about electricity and gas plans, billing, payments, and general energy topics.

![Alinta Energy Assistant](https://img.shields.io/badge/Databricks-Powered-red)
![Python](https://img.shields.io/badge/Python-3.10+-blue)
![React](https://img.shields.io/badge/React-18-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green)

## 🎯 Overview

This chatbot uses **Retrieval Augmented Generation (RAG)** to provide accurate, up-to-date answers grounded in official Alinta Energy website content. By combining vector search with large language models, it delivers factually correct responses while preventing hallucination.

### Key Features

- 🤖 **AI-Powered Responses**: Natural language understanding using GPT-OSS 120B
- 📚 **Grounded Answers**: All responses backed by official Alinta Energy content
- 🔍 **Smart Retrieval**: Vector search with Mosaic AI for relevant document retrieval
- 💬 **Conversational**: Maintains context across multiple turns
- 📱 **Modern UI**: Clean, responsive interface matching Alinta Energy branding
- 🔗 **Source Citations**: Every answer includes links to original sources
- ⚡ **Fast & Scalable**: Serverless architecture on Databricks

### Business Value

- **24/7 Availability**: Always-on customer support
- **Consistent Information**: Accurate answers from authoritative sources
- **Reduced Support Load**: Handles common queries automatically
- **Improved CX**: Instant responses to customer questions
- **Scalable**: Handles unlimited concurrent users

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                  alintaenergy.com.au                         │
└────────────────────┬────────────────────────────────────────┘
                     │ Daily scraping
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              Delta Lake (Unity Catalog)                      │
│  Bronze: Raw HTML → Silver: Clean text → Gold: Chunks       │
└────────────────────┬────────────────────────────────────────┘
                     │ Delta Sync
                     ▼
┌─────────────────────────────────────────────────────────────┐
│          Vector Search Index (embeddings)                    │
└────────────────────┬────────────────────────────────────────┘
                     │
        ┌────────────┴────────────┐
        │   Query at runtime      │
        ▼                         ▼
┌──────────────────┐      ┌──────────────────┐
│  React Frontend  │◄────►│  FastAPI Backend │
│  • Chat UI       │      │  • Retrieval     │
│  • History       │      │  • Generation    │
└──────────────────┘      └──────────────────┘
```

## 🛠️ Technology Stack

### Data Pipeline
- **Web Scraping**: BeautifulSoup for content extraction
- **Data Storage**: Delta Lake with medallion architecture (Bronze/Silver/Gold)
- **Orchestration**: Databricks Jobs with scheduled notebooks
- **Processing**: Apache Spark for distributed data processing

### AI/ML
- **Vector Search**: Mosaic AI Vector Search with Delta Sync
- **Embeddings**: `databricks-gte-large-en` model
- **LLM**: GPT-OSS 120B (128K context window)
- **Framework**: Custom RAG pipeline

### Application
- **Backend**: FastAPI (Python 3.10+)
- **Frontend**: React 18 + TypeScript + Vite
- **Styling**: Alinta Energy orange branding (#FF6B35) with Inter font
- **Deployment**: Databricks Apps (serverless hosting)
- **Authentication**: Service principal (OAuth)

## 📁 Project Structure

```
alinta-energy-assistant/
├── data_pipeline/
│   ├── notebooks/
│   │   ├── 01_web_scraper.py           # Scrape website
│   │   ├── 02_process_bronze.py        # Clean HTML
│   │   ├── 03_create_chunks.py         # Chunk content
│   │   └── 04_setup_vector_search.py   # Create Vector Search index
│   └── config/
│       └── scraping_config.yaml        # Scraping configuration
├── app/
│   ├── backend/
│   │   ├── main.py                     # FastAPI app
│   │   ├── config.py                   # Configuration
│   │   ├── api/
│   │   │   ├── routes.py              # API endpoints
│   │   │   └── models.py              # Pydantic models
│   │   └── rag/
│   │       ├── retrieval.py           # Vector Search integration
│   │       ├── generation.py          # LLM logic
│   │       └── prompts.py             # System prompts
│   ├── frontend/
│   │   └── src/
│   │       ├── components/            # React components
│   │       └── styles/                # CSS styling
│   ├── requirements.txt
│   ├── app.yaml                       # Databricks Apps config
│   └── deploy.sh                      # Deployment script
├── tests/
│   ├── test_retrieval.py              # Retrieval tests
│   ├── test_generation.py             # Generation tests
│   └── evaluation_dataset.json        # Evaluation questions
└── README.md
```

## 🚀 Getting Started

> **📝 Deployment Guide**: For detailed deployment instructions, troubleshooting, and production best practices, see **[DEPLOYMENT_NOTES.md](DEPLOYMENT_NOTES.md)**

### Prerequisites

- Databricks Workspace (AWS/Azure/GCP)
- Unity Catalog enabled
- Personal Access Token
- Python 3.10+
- Node.js 18+ (for frontend development)

### Step 1: Data Pipeline Setup

1. **Upload notebooks to Databricks Workspace**

```bash
databricks workspace import-dir data_pipeline/notebooks /Workspace/Users/<your-email>/alinta-data-pipeline
```

2. **Run notebooks in order:**

```python
# 1. Scrape website
%run ./01_web_scraper

# 2. Process bronze data
%run ./02_process_bronze

# 3. Create chunks
%run ./03_create_chunks

# 4. Setup Vector Search (see note below)
%run ./04_setup_vector_search_alternative
```

> **⚠️ Important Note on Vector Search:**
> The Vector Search Python SDK may not be available in all Databricks runtimes. If you encounter import errors with `databricks.vector_search`, you'll need to create the Vector Search index via the Databricks UI instead.
>
> **See [DEPLOYMENT_NOTES.md](DEPLOYMENT_NOTES.md#vector-search-setup)** for detailed UI-based setup instructions or use the helper script: `./check-vector-search-status.sh`

3. **Schedule daily scraping (optional)**

Create a Databricks Job to run `01_web_scraper.py` daily at 2 AM.

### Step 2: Application Setup

1. **Clone repository**

```bash
git clone <your-repo-url>
cd alinta-energy-assistant
```

2. **Configure environment**

```bash
cd app
cp .env.example .env
```

Edit `.env`:
```bash
DATABRICKS_HOST=https://your-workspace.cloud.databricks.com
DATABRICKS_TOKEN=your_token_here
```

3. **Build frontend**

```bash
cd frontend
npm install
npm run build
cd ..
```

4. **Test locally**

```bash
pip install -r requirements.txt
uvicorn backend.main:app --reload
```

Visit http://localhost:8000

### Step 3: Deploy to Databricks Apps

1. **Update app.yaml** with your workspace URL

2. **Deploy**

```bash
chmod +x deploy.sh
./deploy.sh
```

3. **Access your app**

```bash
databricks apps get alinta-energy-assistant
```

The command will output your app URL.

## 🧪 Testing

### Run Unit Tests

```bash
cd tests
pip install -r requirements.txt
pytest -v
```

### Run Specific Test Suite

```bash
pytest tests/test_retrieval.py -v
pytest tests/test_generation.py -v
```

### Evaluate on Test Dataset

```bash
python tests/run_evaluation.py
```

## 📊 Monitoring

### Check App Health

```bash
curl https://your-app-url/api/health
```

### View Logs

```bash
databricks apps logs alinta-energy-assistant
```

### Vector Search Metrics

```python
from databricks.vector_search.client import VectorSearchClient

client = VectorSearchClient()
index = client.get_index(
    endpoint_name="alinta_support_endpoint",
    index_name="main.sgh.content_vector_index"
)

print(index.describe())
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABRICKS_HOST` | Workspace URL | Required |
| `DATABRICKS_TOKEN` | PAT token | Optional (service principal in Apps) |
| `VECTOR_SEARCH_ENDPOINT` | Vector Search endpoint | `alinta_support_endpoint` |
| `VECTOR_SEARCH_INDEX` | Index name | `main.sgh.content_vector_index` |
| `LLM_MODEL` | Model to use | `databricks-gpt-oss-120b` |
| `TOP_K_RESULTS` | Documents to retrieve | `3` |
| `DEBUG` | Debug mode | `false` |

### Customizing Prompts

Edit `app/backend/rag/prompts.py` to customize:
- System prompt
- RAG prompt template
- Error messages
- Starter questions

### Adjusting Chunking

Edit `data_pipeline/config/scraping_config.yaml`:

```yaml
chunking:
  chunk_size: 400      # words per chunk
  overlap_size: 50     # words overlap
  min_chunk_size: 50   # minimum chunk size
```

## 📈 Performance

### Expected Metrics

- **Retrieval Latency**: < 200ms (p95)
- **Generation Latency**: 1-2s (p95)
- **End-to-End Latency**: < 3s (p95)
- **Retrieval Precision**: > 80%
- **Answer Faithfulness**: > 85%

### Optimization Tips

1. **Reduce latency**: Decrease `top_k` from 3 to 2
2. **Improve relevance**: Adjust chunk size and overlap
3. **Better answers**: Tune system prompt and temperature
4. **Cost optimization**: Use continuous sync only if needed

## 🔒 Security

### Best Practices

- ✅ Store tokens in Databricks Secrets
- ✅ Use Unity Catalog for access control
- ✅ Enable audit logging
- ✅ Restrict Vector Search endpoint access
- ✅ Validate user inputs
- ✅ Rate limit API endpoints (if public-facing)

### Access Control

```sql
-- Grant access to index
GRANT SELECT ON VECTOR_INDEX main.sgh.content_vector_index TO `app-users`;

-- Grant access to tables
GRANT SELECT ON TABLE main.sgh.gold_content_chunks TO `app-users`;
```

## 🐛 Troubleshooting

### Common Issues

**Q: Vector Search returns no results**
- Verify index is built: Check status in Databricks UI
- Trigger manual sync: `index.sync()`
- Check source table has data: `spark.table("main.sgh.gold_content_chunks").count()`

**Q: LLM endpoint unavailable**
- Verify model endpoint exists: `databricks apps list`
- Check permissions on Model Serving endpoint
- Verify `DATABRICKS_TOKEN` is valid

**Q: Frontend not loading**
- Ensure frontend is built: `cd frontend && npm run build`
- Check `dist` directory exists
- Verify FastAPI is serving static files

**Q: Deployment fails**
- Check `app.yaml` has correct workspace URL
- Verify Databricks CLI is configured: `databricks auth login`
- Ensure sufficient workspace permissions

## 🎓 Learning Resources

- [Databricks RAG Documentation](https://docs.databricks.com/aws/en/generative-ai/retrieval-augmented-generation)
- [Mosaic AI Vector Search](https://docs.databricks.com/aws/en/vector-search/vector-search)
- [Foundation Model APIs](https://docs.databricks.com/aws/en/machine-learning/foundation-model-apis/)
- [Databricks Apps Cookbook](https://github.com/databricks-solutions/databricks-apps-cookbook)

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📝 License

This project is licensed under the MIT License - see LICENSE file for details.

## 👥 Authors

- **Your Name** - Initial work

## 🙏 Acknowledgments

- Alinta Energy for use case inspiration
- Databricks for RAG platform and documentation
- FastAPI and React communities

## 📞 Support

For questions or issues:

- 📧 Email: your-email@example.com
- 🐛 Issues: [GitHub Issues](https://github.com/your-repo/issues)
- 💬 Discussions: [GitHub Discussions](https://github.com/your-repo/discussions)

---

**Built with ❤️ using Databricks, FastAPI, and React**
