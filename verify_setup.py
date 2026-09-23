#!/usr/bin/env python3
"""
Quick verification script to check the project setup.

This script checks that all necessary files and directories are in place
without requiring any dependencies to be installed.
"""

import os
import json
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


def verify_project_structure():
    """Verify the project structure is complete."""
    print("🔍 Verifying Project Structure...")
    print("="*50)

    base_path = Path(__file__).parent

    # Check directories
    required_dirs = [
        "src/agent",
        "src/knowledge_base/documents",
        "src/data",
        "tests",
        "config",
    ]

    for dir_path in required_dirs:
        full_path = base_path / dir_path
        if full_path.exists():
            print(f"✅ {dir_path}/")
        else:
            print(f"❌ {dir_path}/ - MISSING")

    print("\n📄 Checking Core Files...")
    print("-"*50)

    # Check core files
    required_files = [
        ("requirements.txt", "Dependencies list"),
        ("config/settings.py", "Configuration settings"),
        ("src/agent/core.py", "Main agent implementation"),
        ("src/agent/tools.py", "Custom tools"),
        ("src/agent/prompts.py", "System prompts"),
        ("src/data/sample_conversations.json", "Test data"),
        ("tests/test_agent.py", "Test suite"),
        ("run_sample_conversations.py", "Sample conversation runner"),
    ]

    for file_path, description in required_files:
        full_path = base_path / file_path
        if full_path.exists():
            size = full_path.stat().st_size
            print(f"✅ {file_path} ({size:,} bytes) - {description}")
        else:
            print(f"❌ {file_path} - MISSING - {description}")

    print("\n📚 Checking Knowledge Base...")
    print("-"*50)

    # Check knowledge base documents
    kb_path = base_path / "src/knowledge_base/documents"
    if kb_path.exists():
        kb_files = list(kb_path.glob("*.md"))
        if kb_files:
            print(f"✅ Found {len(kb_files)} knowledge base documents:")
            for kb_file in kb_files:
                size = kb_file.stat().st_size
                print(f"   - {kb_file.name} ({size:,} bytes)")
        else:
            print("⚠️  No knowledge base documents found")
    else:
        print("❌ Knowledge base directory missing")

    print("\n🎯 Checking Sample Conversations...")
    print("-"*50)

    # Check sample conversations
    sample_path = base_path / "src/data/sample_conversations.json"
    if sample_path.exists():
        with open(sample_path, 'r') as f:
            data = json.load(f)

        num_conversations = len(data.get("conversations", []))
        has_emails = sum(1 for conv in data.get("conversations", [])
                         if conv.get("customer_email"))

        print(f"✅ {num_conversations} sample conversations loaded")
        print(f"   {has_emails} with customer emails")
        print(f"   {num_conversations - has_emails} anonymous queries")

    else:
        print("❌ Sample conversations file missing")

    print("\n⚙️  Checking Python Environment...")
    print("-"*50)

    import sys
    print(f"Python version: {sys.version}")
    print(f"Python executable: {sys.executable}")

    # Check if required environment variables are set
    print("\n🔑 Checking Environment Variables...")
    print("-"*50)

    openai_key = os.environ.get("OPENAI_API_KEY")
    if openai_key:
        print(f"✅ OPENAI_API_KEY is set (length: {len(openai_key)})")
    else:
        print("ℹ️  OPENAI_API_KEY not set (optional, for embeddings)")

    print("\n" + "="*50)
    print("📋 Setup Verification Complete!")
    print("="*50)

    print("\nYou can safely begin testing the agent and building your solution.\n")

    return True


if __name__ == "__main__":
    verify_project_structure()
