#!/bin/bash

# Setup GitHub Authentication for Automated Pushes
# This stores your token securely in macOS Keychain

echo "========================================="
echo "GitHub Authentication Setup"
echo "========================================="
echo ""
echo "This will configure git to use your token automatically."
echo ""

# Option 1: macOS Keychain (most secure)
echo "Setting up macOS Keychain credential helper..."
git config --global credential.helper osxkeychain

echo "✅ Credential helper configured!"
echo ""
echo "Now, the next time you push, git will ask for your token ONCE"
echo "and store it securely in macOS Keychain."
echo ""
echo "After that, all future pushes will be automatic!"
echo ""
echo "To test, run:"
echo "  cd /Users/sourabh.ghose/claude_projects/alinta-energy-assistant"
echo "  git push"
echo ""
echo "You'll be prompted for:"
echo "  Username: sourabhghose"
echo "  Password: [your GitHub token]"
echo ""
echo "After entering it once, you won't need to enter it again!"
