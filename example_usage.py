#!/usr/bin/env python3
"""
Example usage of the Customer Support Agent.

This script demonstrates how to:
1. Initialize the agent
2. Process customer queries
3. Test different scenarios
4. Evaluate responses

Before running, ensure you have:
1. Installed requirements: pip install -r requirements.txt
2. Set ANTHROPIC_API_KEY environment variable
"""

from src.agent.core import CustomerSupportAgent
import os
import json
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file FIRST
load_dotenv()


def test_basic_queries():
    """Test the agent with basic customer queries."""
    print("="*60)
    print("TESTING BASIC QUERIES")
    print("="*60)

    try:
        # Initialize agent
        print("\n🤖 Initializing Customer Support Agent...")
        agent = CustomerSupportAgent(verbose=True)
        print("✅ Agent initialized successfully!\n")

        # Test queries
        test_queries = [
            {
                "query": "What is CloudSync and what does it do?",
                "metadata": None
            },
            {
                "query": "How much does the Professional plan cost?",
                "metadata": None
            },
            {
                "query": "I can't log into my account, can you help?",
                "metadata": {"customer_email": "john.doe@example.com"}
            },
            {
                "query": "Check my billing information",
                "metadata": {"customer_email": "jane.smith@company.com"}
            },
            {
                "query": "Is the file sync service working properly right now?",
                "metadata": None
            }
        ]

        for i, test in enumerate(test_queries, 1):
            print(f"\n{'='*60}")
            print(f"Query {i}: {test['query']}")
            if test['metadata']:
                print(f"Metadata: {test['metadata']}")
            print("-"*60)

            response = agent.query(test['query'], test['metadata'])
            print(f"Response:\n{response}")

            # Reset memory between unrelated queries
            if i < len(test_queries):
                agent.reset_memory()

    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nMake sure you have set the ANTHROPIC_API_KEY environment variable:")
        print("  export ANTHROPIC_API_KEY='your-key-here'")
        return False

    return True


def test_sample_conversations():
    """Test the agent with sample conversation data."""
    print("\n" + "="*60)
    print("TESTING SAMPLE CONVERSATIONS")
    print("="*60)

    # Load sample data
    sample_path = Path("src/data/sample_conversations.json")
    with open(sample_path, 'r') as f:
        data = json.load(f)

    try:
        agent = CustomerSupportAgent(verbose=False)

        # Test a few conversations from different categories
        test_convs = [
            data["conversations"][0],  # Easy billing query
            data["conversations"][1],  # Medium technical issue
            data["conversations"][5],  # General question
        ]

        for conv in test_convs:
            print(f"\n{'='*60}")
            print(f"Conversation ID: {conv['id']}")
            print(f"Category: {conv['category']}")
            print(f"Difficulty: {conv['difficulty']}")
            print(f"Query: {conv['query']}")
            print("-"*60)

            metadata = {}
            if "customer_email" in conv:
                metadata["customer_email"] = conv["customer_email"]

            response = agent.query(conv['query'], metadata)
            print(f"Response:\n{response[:500]}...")  # Show first 500 chars

            print(f"\nExpected actions: {conv['expected_actions']}")
            print(f"Expected elements: {conv['expected_response_elements']}")

            agent.reset_memory()

    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False

    return True


def test_tools_directly():
    """Test the custom tools directly."""
    print("\n" + "="*60)
    print("TESTING TOOLS DIRECTLY")
    print("="*60)

    from src.agent.tools import (
        BillingLookupTool,
        TicketCreationTool,
        SystemStatusTool
    )

    # Test Billing Tool
    print("\n📊 Testing Billing Lookup Tool:")
    billing_tool = BillingLookupTool()
    result = billing_tool.lookup(customer_email="john.doe@example.com")
    print(f"Result: {json.dumps(result, indent=2)}")

    # Test Ticket Creation Tool
    print("\n🎫 Testing Ticket Creation Tool:")
    ticket_tool = TicketCreationTool()
    result = ticket_tool.create(
        subject="Test Issue",
        description="This is a test ticket from the example script",
        customer_email="test@example.com",
        priority="medium",
        category="technical"
    )
    print(f"Result: {json.dumps(result, indent=2)}")

    # Test System Status Tool
    print("\n🔍 Testing System Status Tool:")
    status_tool = SystemStatusTool()
    result = status_tool.check()
    print(f"Overall Status: {result['overall_status']}")
    print(f"Services: {list(result['services'].keys())}")

    return True


def main():
    """Run all example tests."""
    print("\n" + "🚀 CloudSync Customer Support Agent - Example Usage 🚀")
    print("="*60)

    # Check for API key
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("\n⚠️  WARNING: ANTHROPIC_API_KEY not set!")
        print("The agent requires an Anthropic API key to function.")
        print("\nYou can still test the tools directly without an API key.")

        response = input("\nDo you want to test the tools? (y/n): ")
        if response.lower() == 'y':
            test_tools_directly()
        else:
            print("\nTo set your API key:")
            print("  export ANTHROPIC_API_KEY='your-key-here'")
        return

    # Run tests
    print("\n1️⃣  Testing basic queries...")
    if test_basic_queries():
        print("\n✅ Basic queries test passed!")

    print("\n2️⃣  Testing sample conversations...")
    if test_sample_conversations():
        print("\n✅ Sample conversations test passed!")

    print("\n3️⃣  Testing tools directly...")
    if test_tools_directly():
        print("\n✅ Tools test passed!")

    print("\n" + "="*60)
    print("🎉 All tests completed!")
    print("="*60)
    print("\nNext steps for evaluation:")
    print("1. Review and improve the prompts in src/agent/prompts.py")
    print("2. Implement an evaluation framework")
    print("3. Test with more complex scenarios")
    print("4. Measure and optimize performance metrics")


if __name__ == "__main__":
    main()
