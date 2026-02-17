#!/bin/bash
# Ultra-simple push script - one command does everything

git add -A && \
git commit -m "${1:-Update: $(date +'%Y-%m-%d %H:%M')}" && \
git push && \
echo "✅ Pushed to GitHub!"
