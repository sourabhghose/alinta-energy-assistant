"""
Test script for Alinta Energy Assistant RAG endpoint.
Run this from a Databricks notebook where you're authenticated.
"""

import requests
import json
from databricks.sdk import WorkspaceClient

# Initialize Databricks client (uses your current authentication)
w = WorkspaceClient()

# Get your current user to build the app URL
current_user = w.current_user.me()
print(f"Testing as user: {current_user.user_name}")

# App URL
APP_URL = "https://alinta-energy-assistant-2556758628403379.aws.databricksapps.com"

print(f"\n{'='*80}")
print("TESTING ALINTA ENERGY ASSISTANT RAG ENDPOINT")
print(f"{'='*80}\n")

# Test 1: Health Check
print("Test 1: Health Check")
print("-" * 80)
try:
    # Note: In Databricks notebook, you'll need to use the appropriate auth method
    # This might require running from within the workspace
    response = requests.get(f"{APP_URL}/api/health")
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        health_data = response.json()
        print(f"Service Status: {health_data['status']}")
        print(f"Components:")
        for component, status in health_data.get('components', {}).items():
            status_emoji = "✅" if status else "❌"
            print(f"  {status_emoji} {component}: {status}")
    else:
        print(f"Response: {response.text[:200]}")
except Exception as e:
    print(f"Error: {str(e)}")

print(f"\n{'='*80}\n")

# Test 2: Chat Endpoint with Sample Questions
print("Test 2: Chat Endpoint - Sample Questions")
print("-" * 80)

test_questions = [
    "What electricity plans are available in Western Australia?",
    "How do I pay my bill online?",
    "What is a solar feed-in tariff?",
]

for i, question in enumerate(test_questions, 1):
    print(f"\nQuestion {i}: {question}")
    print("-" * 40)

    try:
        payload = {
            "question": question,
            "top_k": 3
        }

        response = requests.post(
            f"{APP_URL}/api/chat",
            json=payload,
            headers={"Content-Type": "application/json"}
        )

        print(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"\n📝 Answer:")
            print(f"{data['answer']}\n")

            if data.get('sources'):
                print(f"📚 Sources:")
                for source in data['sources']:
                    print(f"  • {source['title']}")
                    print(f"    {source['url']}")

            if data.get('metadata'):
                print(f"\n📊 Metadata:")
                for key, value in data['metadata'].items():
                    print(f"  {key}: {value}")
        else:
            print(f"Response: {response.text[:500]}")

    except Exception as e:
        print(f"Error: {str(e)}")

    print()

print(f"\n{'='*80}")
print("TEST COMPLETE")
print(f"{'='*80}\n")

# Instructions for running in Databricks notebook
print("""
INSTRUCTIONS FOR RUNNING THIS TEST:

1. Open a Databricks notebook in your workspace
2. Copy this script into a Python cell
3. Run the cell

If you get authentication errors:
- You may need to use the notebook's context for authentication
- Try accessing the app URL directly in your browser first
- Check that the app is accessible from your workspace

Alternative: Use the interactive API docs at:
https://alinta-energy-assistant-2556758628403379.aws.databricksapps.com/docs
""")
