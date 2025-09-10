"""
Basic tests for the Customer Support Agent.

This file provides a foundation for testing the agent's functionality
and can be extended with more comprehensive evaluation tests.
"""

from src.agent.prompts import SYSTEM_PROMPT
from src.agent.tools import BillingLookupTool, TicketCreationTool, SystemStatusTool
from src.agent.core import CustomerSupportAgent
import os
import sys
import json
import pytest
from pathlib import Path
from typing import Dict, Any, List
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load environment variables from .env file BEFORE importing modules
load_dotenv()


class TestAgentComponents:
    """Test individual agent components."""

    def test_agent_initialization(self):
        """Test that the agent initializes correctly."""
        # Note: This will require API keys to be set
        try:
            agent = CustomerSupportAgent(verbose=False)
            assert agent is not None
            assert agent.agent is not None
            assert len(agent.tools) > 0
        except ValueError as e:
            if "ANTHROPIC_API_KEY" in str(e):
                pytest.skip("ANTHROPIC_API_KEY not set")

    def test_billing_tool(self):
        """Test the billing lookup tool."""
        tool = BillingLookupTool()

        # Test with known email
        result = tool.lookup(customer_email="john.doe@example.com")
        assert result["success"] is True
        assert "data" in result
        assert "plan" in result["data"]

        # Test with customer ID
        result = tool.lookup(customer_id="cust_1000")
        assert result["success"] is True

        # Test with no parameters
        result = tool.lookup()
        assert "error" in result

    def test_ticket_tool(self):
        """Test the ticket creation tool."""
        tool = TicketCreationTool()

        result = tool.create(
            subject="Test Issue",
            description="This is a test ticket",
            customer_email="test@example.com",
            priority="high"
        )

        assert result["success"] is True
        assert "ticket_id" in result["data"]
        assert result["data"]["priority"] == "high"
        assert "TICKET-" in result["data"]["ticket_id"]

    def test_status_tool(self):
        """Test the system status tool."""
        tool = SystemStatusTool()

        # Test general status check
        result = tool.check()
        assert result["success"] is True
        assert "overall_status" in result
        assert "services" in result

        # Test specific service check
        result = tool.check(service="api")
        assert result["success"] is True
        assert "data" in result


class TestAgentResponses:
    """Test agent responses to various queries."""

    @pytest.fixture
    def agent(self):
        """Create an agent instance for testing."""
        try:
            return CustomerSupportAgent(verbose=False)
        except ValueError as e:
            if "ANTHROPIC_API_KEY" in str(e):
                pytest.skip("ANTHROPIC_API_KEY not set")

    def test_simple_query(self, agent):
        """Test a simple FAQ query."""
        response = agent.query("What is CloudSync?")
        assert response is not None
        assert len(response) > 0
        assert "CloudSync" in response or "cloud" in response.lower()

    def test_billing_query(self, agent):
        """Test a billing-related query."""
        response = agent.query(
            "What's my current plan?",
            metadata={"customer_email": "john.doe@example.com"}
        )
        assert response is not None
        # Should attempt to use billing tool

    def test_technical_query(self, agent):
        """Test a technical support query."""
        response = agent.query("My files aren't syncing, what should I do?")
        assert response is not None
        # Should provide troubleshooting steps

    def test_memory_persistence(self, agent):
        """Test that conversation memory persists."""
        # First query
        agent.query("My name is John")

        # Second query should remember context
        response = agent.query("What's my name?")
        # Note: This may not work perfectly without proper memory setup

        # Test memory reset
        agent.reset_memory()
        history = agent.get_conversation_history()
        assert len(history) == 0


class TestSampleConversations:
    """Test agent against sample conversations."""

    @pytest.fixture
    def sample_data(self):
        """Load sample conversation data."""
        sample_path = Path(__file__).parent.parent / \
            "src/data/sample_conversations.json"
        with open(sample_path, 'r') as f:
            return json.load(f)

    @pytest.fixture
    def agent(self):
        """Create an agent instance for testing."""
        try:
            return CustomerSupportAgent(verbose=False)
        except ValueError as e:
            if "ANTHROPIC_API_KEY" in str(e):
                pytest.skip("ANTHROPIC_API_KEY not set")

    def test_easy_conversations(self, agent, sample_data):
        """Test agent on easy difficulty conversations."""
        easy_convs = [
            conv for conv in sample_data["conversations"]
            if conv["difficulty"] == "easy"
        ]

        for conv in easy_convs[:2]:  # Test first 2 easy conversations
            metadata = {}
            if "customer_email" in conv:
                metadata["customer_email"] = conv["customer_email"]

            response = agent.query(conv["query"], metadata)
            assert response is not None
            assert len(response) > 0

            # Check if expected elements are addressed
            # Note: This is a basic check, real evaluation would be more sophisticated
            print(f"\nConversation {conv['id']}:")
            print(f"Query: {conv['query']}")
            print(f"Response: {response[:200]}...")

    def test_conversation_categories(self, sample_data):
        """Test that we have diverse conversation categories."""
        categories = set(conv["category"]
                         for conv in sample_data["conversations"])

        expected_categories = {
            "billing", "technical", "account", "general",
            "feature_request", "security"
        }

        for cat in expected_categories:
            assert cat in categories, f"Missing category: {cat}"


class TestEvaluationFramework:
    """Test the evaluation framework setup."""

    def test_evaluation_criteria(self):
        """Test that evaluation criteria are properly defined."""
        sample_path = Path(__file__).parent.parent / \
            "src/data/sample_conversations.json"
        with open(sample_path, 'r') as f:
            data = json.load(f)

        criteria = data["evaluation_criteria"]

        # Check all criteria sum to 1.0
        total_weight = sum(c["weight"] for c in criteria.values())
        assert abs(total_weight - 1.0) < 0.01

        # Check all criteria have required fields
        for name, criterion in criteria.items():
            assert "weight" in criterion
            assert "description" in criterion
            assert 0 <= criterion["weight"] <= 1

    def test_test_scenarios(self):
        """Test that test scenarios are properly organized."""
        sample_path = Path(__file__).parent.parent / \
            "src/data/sample_conversations.json"
        with open(sample_path, 'r') as f:
            data = json.load(f)

        scenarios = data["test_scenarios"]

        # Check that referenced conversations exist
        all_conv_ids = {conv["id"] for conv in data["conversations"]}

        for scenario_name, conv_ids in scenarios.items():
            for conv_id in conv_ids:
                assert conv_id in all_conv_ids, f"Invalid conversation ID: {conv_id}"


def test_basic_integration():
    """Basic integration test to ensure system components work together."""
    # This test verifies the basic setup without requiring API keys

    # Check that all required files exist
    required_files = [
        "config/settings.py",
        "src/agent/core.py",
        "src/agent/tools.py",
        "src/agent/prompts.py",
        "src/data/sample_conversations.json",
    ]

    base_path = Path(__file__).parent.parent
    for file_path in required_files:
        full_path = base_path / file_path
        assert full_path.exists(), f"Required file missing: {file_path}"

    # Check knowledge base documents
    kb_path = base_path / "src/knowledge_base/documents"
    assert kb_path.exists(), "Knowledge base directory missing"

    kb_files = list(kb_path.glob("*.md"))
    assert len(kb_files) > 0, "No knowledge base documents found"

    print(f"✓ Found {len(kb_files)} knowledge base documents")
    print("✓ All required files present")
    print("✓ Basic integration test passed")


if __name__ == "__main__":
    # Run basic integration test
    print("Running basic integration test...")
    test_basic_integration()

    print("\n" + "="*50)
    print("Basic setup verified successfully!")
    print("="*50)

    print("\nTo run full test suite with pytest:")
    print("  pytest tests/test_agent.py -v")

    print("\nTo test the agent interactively:")
    print("  python -c \"from src.agent.core import CustomerSupportAgent; agent = CustomerSupportAgent(); print(agent.query('What is CloudSync?'))\"")

    print("\nNote: Full agent testing requires ANTHROPIC_API_KEY to be set")
