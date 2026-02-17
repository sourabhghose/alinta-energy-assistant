#!/bin/bash

# Complete Databricks Deployment Script
# This script guides you through deploying the Alinta Energy Assistant

set -e

echo "════════════════════════════════════════════════════════════"
echo "🚀 ALINTA ENERGY ASSISTANT - DATABRICKS DEPLOYMENT"
echo "════════════════════════════════════════════════════════════"
echo ""

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Navigate to project directory
cd "$(dirname "$0")"

echo "📍 Workspace: https://e2-demo-west.cloud.databricks.com"
echo "📍 User: sourabh.ghose@databricks.com"
echo ""

# ============================================================================
# STEP 1: Check Token in Secret
# ============================================================================

echo "═══════════════════════════════════════════════════════════"
echo "STEP 1: Verify Databricks Token"
echo "═══════════════════════════════════════════════════════════"
echo ""

if databricks secrets list-secrets alinta-app-secrets 2>&1 | grep -q "databricks-token"; then
    echo "✅ Token found in secrets"
else
    echo "⚠️  Token not found in secrets"
    echo ""
    echo "You need to add your Databricks token to the secret."
    echo ""
    echo "Run this command and paste your token when prompted:"
    echo "  ${BLUE}databricks secrets put-secret alinta-app-secrets databricks-token${NC}"
    echo ""
    echo "Or create a token at:"
    echo "  https://e2-demo-west.cloud.databricks.com/#setting/account"
    echo ""
    read -p "Press Enter after adding the token, or Ctrl+C to exit..."
fi

echo ""

# ============================================================================
# STEP 2: Run Data Pipeline Notebooks
# ============================================================================

echo "═══════════════════════════════════════════════════════════"
echo "STEP 2: Data Pipeline (Must be run manually in UI)"
echo "═══════════════════════════════════════════════════════════"
echo ""

echo "⚠️  IMPORTANT: You need to run the data pipeline notebooks manually."
echo ""
echo "Why manual? The notebooks require:"
echo "  • Cluster/warehouse selection"
echo "  • Interactive feedback"
echo "  • Visual verification"
echo ""
echo "📍 Notebooks location:"
echo "   /Workspace/Users/sourabh.ghose@databricks.com/alinta-data-pipeline/"
echo ""
echo "🔗 Open in browser:"
echo "   https://e2-demo-west.cloud.databricks.com/#workspace/Users/sourabh.ghose@databricks.com/alinta-data-pipeline"
echo ""
echo "Run these notebooks IN ORDER (click 'Run All' in each):"
echo ""
echo "  1️⃣  01_web_scraper.py        (~3 min)"
echo "      Creates: main.alinta.bronze_scraped_content"
echo ""
echo "  2️⃣  02_process_bronze.py     (~2 min)"
echo "      Creates: main.alinta.silver_clean_content"
echo ""
echo "  3️⃣  03_create_chunks.py      (~2 min)"
echo "      Creates: main.alinta.gold_content_chunks"
echo ""
echo "  4️⃣  04_setup_vector_search.py (~10-15 min)"
echo "      Creates: Vector Search index"
echo "      ⚠️  WAIT until you see: '✅ Index is ready!'"
echo ""
echo "═══════════════════════════════════════════════════════════"
echo ""

read -p "Have you completed all 4 notebooks? (y/n) " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo "Please run the notebooks first, then run this script again."
    echo ""
    echo "Quick link:"
    echo "  open 'https://e2-demo-west.cloud.databricks.com/#workspace/Users/sourabh.ghose@databricks.com/alinta-data-pipeline'"
    exit 0
fi

echo ""

# ============================================================================
# STEP 3: Verify Data Pipeline
# ============================================================================

echo "═══════════════════════════════════════════════════════════"
echo "STEP 3: Verifying Data Pipeline"
echo "═══════════════════════════════════════════════════════════"
echo ""

echo "Checking if tables were created..."
echo ""

# Note: We can't easily verify tables from CLI without SQL warehouse access
# So we'll provide verification commands for the user

cat << 'EOF'
To verify the data pipeline worked, you can run this in a Databricks notebook:

# Check tables
spark.sql("SHOW TABLES IN main.alinta").show()

# Expected: bronze_scraped_content, silver_clean_content, gold_content_chunks

# Check Vector Search index
from databricks.vector_search.client import VectorSearchClient
client = VectorSearchClient()
index = client.get_index(
    endpoint_name="alinta_support_endpoint",
    index_name="main.alinta.content_vector_index"
)
print(index.describe())

# Expected: Status should be "ONLINE" or "ONLINE_NO_PENDING_UPDATE"
EOF

echo ""
read -p "Did you verify the tables and Vector Search index? (y/n) " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo "Please verify the data pipeline completed successfully."
    echo "Run the verification commands above in a Databricks notebook."
    exit 0
fi

echo ""

# ============================================================================
# STEP 4: Build Frontend
# ============================================================================

echo "═══════════════════════════════════════════════════════════"
echo "STEP 4: Building Frontend"
echo "═══════════════════════════════════════════════════════════"
echo ""

if [ -d "app/dist" ]; then
    echo "✅ Frontend already built"
else
    echo "Building frontend..."
    cd app/frontend
    npm install
    npm run build
    cd ../..
    echo "✅ Frontend built successfully"
fi

echo ""

# ============================================================================
# STEP 5: Deploy to Databricks Apps
# ============================================================================

echo "═══════════════════════════════════════════════════════════"
echo "STEP 5: Deploying to Databricks Apps"
echo "═══════════════════════════════════════════════════════════"
echo ""

cd app

echo "Running deployment script..."
echo ""

./deploy.sh

echo ""
echo "════════════════════════════════════════════════════════════"
echo "🎉 DEPLOYMENT COMPLETE!"
echo "════════════════════════════════════════════════════════════"
echo ""
echo "Get your app URL:"
echo "  ${BLUE}databricks apps get alinta-energy-assistant${NC}"
echo ""
echo "View logs:"
echo "  ${BLUE}databricks apps logs alinta-energy-assistant${NC}"
echo ""
echo "Check status:"
echo "  ${BLUE}databricks apps list | grep alinta${NC}"
echo ""
echo "════════════════════════════════════════════════════════════"
