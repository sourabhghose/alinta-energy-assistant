#!/bin/bash

# Automatic Git Push Script
# Adds, commits, and pushes all changes to GitHub automatically

set -e

echo "🚀 Auto-Push to GitHub"
echo "======================"
echo ""

# Navigate to project directory
cd "$(dirname "$0")"

# Check if there are any changes
if git diff-index --quiet HEAD -- 2>/dev/null; then
    echo "✅ No changes to commit"
    echo ""

    # Check if local is ahead of remote
    LOCAL=$(git rev-parse @)
    REMOTE=$(git rev-parse @{u} 2>/dev/null || echo "")

    if [ -z "$REMOTE" ]; then
        echo "⚠️  No remote branch to compare with"
        exit 0
    fi

    if [ "$LOCAL" = "$REMOTE" ]; then
        echo "✅ Already up to date with GitHub"
        exit 0
    else
        echo "📤 Pushing existing commits..."
        git push
        echo "✅ Pushed to GitHub!"
    fi
else
    echo "📝 Changes detected. Creating commit..."
    echo ""

    # Show what's changed
    echo "Modified files:"
    git status --short
    echo ""

    # Add all changes
    git add -A

    # Create commit with timestamp
    TIMESTAMP=$(date +"%Y-%m-%d %H:%M:%S")

    # Get commit message from parameter or use default
    if [ -n "$1" ]; then
        COMMIT_MSG="$1"
    else
        COMMIT_MSG="Auto-update: $TIMESTAMP"
    fi

    git commit -m "$COMMIT_MSG"

    echo "✅ Changes committed"
    echo ""

    # Push to GitHub
    echo "📤 Pushing to GitHub..."
    git push

    echo ""
    echo "========================================="
    echo "✅ Successfully pushed to GitHub!"
    echo "========================================="
    echo ""
    echo "View at: https://github.com/sourabhghose/alinta-energy-assistant"
fi

echo ""
echo "Latest commits:"
git log --oneline -3
