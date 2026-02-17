#!/bin/bash

# Quick script to push Alinta Energy Assistant to GitHub
# Run this after creating the repository on GitHub

set -e

echo "========================================="
echo "Push to GitHub - Alinta Energy Assistant"
echo "========================================="
echo ""

# Check if we're in the right directory
if [ ! -d ".git" ]; then
    echo "❌ Error: Not in a git repository"
    echo "Please run this from: /Users/sourabh.ghose/claude_projects/alinta-energy-assistant/"
    exit 1
fi

# Check remote
echo "📡 Checking remote configuration..."
REMOTE=$(git remote get-url origin 2>/dev/null || echo "")

if [ -z "$REMOTE" ]; then
    echo "⚠️  No remote configured. Adding origin..."
    git remote add origin https://github.com/sourabhghose/alinta-energy-assistant.git
    echo "✅ Remote added: https://github.com/sourabhghose/alinta-energy-assistant.git"
else
    echo "✅ Remote configured: $REMOTE"
fi

echo ""
echo "📊 Repository status:"
git log --oneline -1
echo ""

# Check if repository exists on GitHub
echo "⚠️  IMPORTANT: Make sure you've created the repository on GitHub first!"
echo "   Go to: https://github.com/new"
echo "   Repository name: alinta-energy-assistant"
echo "   (Do NOT initialize with README)"
echo ""

read -p "Have you created the repository on GitHub? (y/n) " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo "Please create the repository first, then run this script again."
    echo "Visit: https://github.com/new"
    exit 0
fi

echo ""
echo "🚀 Pushing to GitHub..."
echo ""

# Prompt for authentication method
echo "Choose authentication method:"
echo "  1) HTTPS (Personal Access Token)"
echo "  2) SSH"
echo ""
read -p "Enter choice (1 or 2): " AUTH_METHOD

if [ "$AUTH_METHOD" = "2" ]; then
    echo ""
    echo "Switching to SSH..."
    git remote set-url origin git@github.com:sourabhghose/alinta-energy-assistant.git
    echo "✅ Remote updated to use SSH"
fi

echo ""
echo "Pushing to main branch..."

if git push -u origin main; then
    echo ""
    echo "========================================="
    echo "✅ Successfully pushed to GitHub!"
    echo "========================================="
    echo ""
    echo "🎉 Your repository is now live at:"
    echo "   https://github.com/sourabhghose/alinta-energy-assistant"
    echo ""
    echo "Next steps:"
    echo "  1. View your repo: https://github.com/sourabhghose/alinta-energy-assistant"
    echo "  2. Continue with deployment: See DEPLOYMENT_GUIDE.md"
    echo "  3. Share with your team!"
    echo ""
else
    echo ""
    echo "========================================="
    echo "⚠️  Push failed"
    echo "========================================="
    echo ""
    echo "Common issues:"
    echo ""
    echo "1. Repository doesn't exist:"
    echo "   → Create it at: https://github.com/new"
    echo ""
    echo "2. Authentication failed:"
    echo "   → For HTTPS: Use Personal Access Token as password"
    echo "   → For SSH: Add your SSH key to GitHub"
    echo ""
    echo "3. Permission denied:"
    echo "   → Check you're logged in as 'sourabhghose'"
    echo "   → Verify repository permissions"
    echo ""
    echo "See GITHUB_SETUP.md for detailed instructions."
    exit 1
fi
