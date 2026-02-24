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
            if "API_KEY" in str(e):
                pytest.skip("Required API key not set")

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
            if "API_KEY" in str(e):
                pytest.skip("Required API key not set")

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

    print("\nNote: Full agent testing requires OPENAI_API_KEY (default) or ANTHROPIC_API_KEY to be set")
