#!/bin/bash

# Deployment script for Alinta Energy Assistant
# This script builds the frontend and deploys to Databricks Apps

set -e  # Exit on error

echo "========================================="
echo "Alinta Energy Assistant Deployment"
echo "========================================="
echo ""

# Step 1: Build frontend
echo "📦 Building frontend..."
cd frontend
npm install
npm run build
cd ..
echo "✅ Frontend built successfully"
echo ""

# Step 2: Verify build output
if [ ! -d "dist" ]; then
    echo "❌ Error: Frontend build failed - dist directory not found"
    exit 1
fi
echo "✅ Build output verified"
echo ""

# Step 3: Get current user
echo "🔍 Getting Databricks user information..."
DATABRICKS_USER=$(databricks current-user me --output json | jq -r '.userName')
if [ -z "$DATABRICKS_USER" ]; then
    echo "❌ Error: Could not determine Databricks user. Check your authentication."
    exit 1
fi
echo "✅ Deploying as user: $DATABRICKS_USER"
echo ""

# Step 4: Create deployment package
echo "📦 Creating deployment package..."
DEPLOY_DIR="/tmp/alinta-app-deploy"
rm -rf $DEPLOY_DIR
mkdir -p $DEPLOY_DIR

# Copy files
cp -r backend $DEPLOY_DIR/
cp -r dist $DEPLOY_DIR/
cp requirements.txt $DEPLOY_DIR/
cp app.yaml $DEPLOY_DIR/

echo "✅ Deployment package created"
echo ""

# Step 5: Upload to workspace
WORKSPACE_PATH="/Workspace/Users/${DATABRICKS_USER}/apps/alinta-energy-assistant"
echo "📤 Uploading to workspace: $WORKSPACE_PATH"

# Remove old deployment (if exists)
databricks workspace delete "$WORKSPACE_PATH" --recursive 2>/dev/null || true

# Upload new deployment
databricks workspace import-dir $DEPLOY_DIR $WORKSPACE_PATH

echo "✅ Files uploaded to workspace"
echo ""

# Step 6: Deploy app
echo "🚀 Deploying Databricks App..."

# Check if app exists
if databricks apps get alinta-energy-assistant 2>/dev/null; then
    echo "⚠️  App already exists. Updating..."
    databricks apps update alinta-energy-assistant \
        --source-code-path "$WORKSPACE_PATH"
else
    echo "Creating new app..."
    databricks apps create alinta-energy-assistant \
        --description "AI customer support assistant for Alinta Energy" \
        --source-code-path "$WORKSPACE_PATH"
fi

echo "✅ App deployed successfully"
echo ""

# Step 7: Get app status
echo "📊 App Status:"
databricks apps get alinta-energy-assistant

echo ""
echo "========================================="
echo "✅ Deployment Complete!"
echo "========================================="
echo ""
echo "Next steps:"
echo "1. Check app status: databricks apps get alinta-energy-assistant"
echo "2. View logs: databricks apps logs alinta-energy-assistant"
echo "3. Access app via the URL shown above"
echo ""
