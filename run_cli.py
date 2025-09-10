#!/usr/bin/env python3
"""
Interactive CLI for testing the CloudSync Customer Support Agent.

This tool allows candidates to:
- Test custom queries interactively
- Use different customer contexts
- Toggle verbose mode to see agent reasoning
- Test prompt variations
- Save conversation history

Usage:
    python run_cli.py
"""

from src.agent.prompts import PROMPT_VARIATIONS
from src.agent.core import CustomerSupportAgent
import os
import sys
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))


class CloudSyncCLI:
    """Interactive CLI for testing the CloudSync agent."""

    def __init__(self):
        """Initialize the CLI."""
        self.agent = None
        self.verbose = False
        self.current_customer = None
        self.conversation_history = []
        self.prompt_mode = "default"

    def print_header(self):
        """Print the welcome header."""
        print("\n" + "="*60)
        print("🤖 CloudSync Customer Support Agent - Interactive CLI")
        print("="*60)
        print("\nCommands:")
        print("  /help            - Show all commands")
        print("  /quit or /exit   - Exit the CLI")
        print("  /reset           - Clear conversation memory")
        print("  /verbose         - Toggle verbose mode (see agent thinking)")
        print("  /customer <email>- Set customer context")
        print("  /prompt <type>   - Switch prompt style")
        print("  /test <id>       - Test sample conversation by ID")
        print("  /save            - Save conversation to file")
        print("  /tools           - Test tools directly")
        print("\nJust type your question to get started!\n")

    def print_help(self):
        """Print detailed help information."""
        print("\n" + "="*60)
        print("📚 HELP - Available Commands")
        print("="*60)

        commands = [
            ("/help", "Show this help message"),
            ("/quit or /exit", "Exit the CLI"),
            ("/reset", "Clear conversation memory (start fresh)"),
            ("/verbose", "Toggle verbose mode to see agent's reasoning"),
            ("/customer <email>",
             "Set customer context (e.g., /customer john.doe@example.com)"),
            ("/customer clear", "Clear customer context"),
            ("/prompt list", "List available prompt variations"),
            ("/prompt <type>", "Switch prompt (e.g., /prompt empathetic)"),
            ("/test <id>", "Test sample conversation (e.g., /test conv_001)"),
            ("/test list", "List all available test conversations"),
            ("/save", "Save conversation history to file"),
            ("/tools", "Test individual tools (billing, tickets, status)"),
            ("/status", "Show current settings and context"),
        ]

        for cmd, desc in commands:
            print(f"  {cmd:<20} - {desc}")

        print("\n💡 Tips:")
        print("  - Use /verbose to understand how the agent thinks")
        print("  - Set customer context to test billing lookups")
        print("  - Try different prompts to see how responses change")
        print("  - Test edge cases from sample conversations\n")

    def initialize_agent(self):
        """Initialize or reinitialize the agent."""
        print("Initializing agent", end="")
        if self.verbose:
            print(" (verbose mode ON)...")
        else:
            print("...")

        try:
            self.agent = CustomerSupportAgent(verbose=self.verbose)

            # Apply custom prompt if selected
            if self.prompt_mode != "default" and self.prompt_mode in PROMPT_VARIATIONS:
                self.agent.agent.system_prompt = PROMPT_VARIATIONS[self.prompt_mode]
                print(f"Using '{self.prompt_mode}' prompt style")

            print("✅ Agent ready!\n")
            return True
        except Exception as e:
            print(f"❌ Failed to initialize agent: {e}")
            print("\nMake sure you have:")
            print("  1. Set ANTHROPIC_API_KEY in your .env file")
            print("  2. Installed all requirements: pip install -r requirements.txt")
            return False

    def set_customer(self, email: str):
        """Set the current customer context."""
        if email.lower() == "clear":
            self.current_customer = None
            print("✅ Customer context cleared")
        else:
            self.current_customer = email
            print(f"✅ Customer context set to: {email}")

    def toggle_verbose(self):
        """Toggle verbose mode."""
        self.verbose = not self.verbose
        print(f"Verbose mode: {'ON' if self.verbose else 'OFF'}")
        # Reinitialize agent with new verbose setting
        self.initialize_agent()

    def list_prompts(self):
        """List available prompt variations."""
        print("\n📝 Available Prompt Styles:")
        print("-" * 40)
        print(f"  default - Standard system prompt")
        for name in PROMPT_VARIATIONS:
            print(f"  {name} - {name.replace('_', ' ').title()} style")
        print(f"\nCurrent: {self.prompt_mode}")

    def switch_prompt(self, prompt_type: str):
        """Switch to a different prompt variation."""
        if prompt_type == "list":
            self.list_prompts()
        elif prompt_type == "default":
            self.prompt_mode = "default"
            self.initialize_agent()
            print(f"✅ Switched to default prompt")
        elif prompt_type in PROMPT_VARIATIONS:
            self.prompt_mode = prompt_type
            self.initialize_agent()
            print(f"✅ Switched to '{prompt_type}' prompt style")
        else:
            print(f"❌ Unknown prompt type: {prompt_type}")
            self.list_prompts()

    def test_sample_conversation(self, conv_id: str):
        """Test a specific sample conversation."""
        if conv_id == "list":
            self.list_sample_conversations()
            return

        try:
            with open('src/data/sample_conversations.json', 'r') as f:
                data = json.load(f)

            # Find the conversation
            conv = next(
                (c for c in data['conversations'] if c['id'] == conv_id), None)
            if not conv:
                print(f"❌ Conversation '{conv_id}' not found")
                print("Use '/test list' to see available conversations")
                return

            print(f"\n{'='*60}")
            print(f"📋 Testing: {conv['id']}")
            print(
                f"Category: {conv['category']} | Difficulty: {conv['difficulty']}")
            print(f"{'='*60}")
            print(f"Query: {conv['query']}")
            print("-"*60)

            # Set up metadata
            metadata = {}
            if 'customer_email' in conv:
                metadata['customer_email'] = conv['customer_email']
                print(f"Customer: {conv['customer_email']}")

            # Get response
            response = self.agent.query(conv['query'], metadata)
            print(f"\n🤖 Response:\n{response}")

            # Show expected elements
            print(f"\n📊 Expected Actions: {conv['expected_actions']}")
            print(f"📊 Expected Elements: {conv['expected_response_elements']}")

        except Exception as e:
            print(f"❌ Error testing conversation: {e}")

    def list_sample_conversations(self):
        """List all available sample conversations."""
        try:
            with open('src/data/sample_conversations.json', 'r') as f:
                data = json.load(f)

            print("\n📚 Available Test Conversations:")
            print("-" * 60)

            # Group by category
            categories = {}
            for conv in data['conversations']:
                cat = conv['category']
                if cat not in categories:
                    categories[cat] = []
                categories[cat].append(conv)

            for category, convs in sorted(categories.items()):
                print(f"\n{category.upper()}:")
                for conv in convs:
                    print(
                        f"  {conv['id']:<12} - {conv['difficulty']:<8} - {conv['query'][:50]}...")

        except Exception as e:
            print(f"❌ Error loading conversations: {e}")

    def test_tools(self):
        """Test individual tools directly."""
        from src.agent.tools import BillingLookupTool, TicketCreationTool, SystemStatusTool

        print("\n🔧 Testing Tools Directly")
        print("="*60)

        # Test billing
        print("\n1. Billing Lookup Tool:")
        billing = BillingLookupTool()
        result = billing.lookup(customer_email="john.doe@example.com")
        print(f"   Plan: {result['data']['plan']}")
        print(f"   Status: {result['data']['status']}")
        print(f"   Next billing: {result['data']['next_billing_date']}")

        # Test ticket creation
        print("\n2. Ticket Creation Tool:")
        ticket = TicketCreationTool()
        result = ticket.create(
            subject="Test from CLI",
            description="Testing ticket creation from interactive CLI",
            priority="low"
        )
        print(f"   Ticket ID: {result['data']['ticket_id']}")
        print(f"   Response time: {result['data']['estimated_response_time']}")

        # Test system status
        print("\n3. System Status Tool:")
        status = SystemStatusTool()
        result = status.check()
        print(f"   Overall: {result['overall_status']}")
        for service, info in result['services'].items():
            print(f"   - {service}: {info['status']}")

    def save_conversation(self):
        """Save the conversation history to a file."""
        if not self.conversation_history:
            print("No conversation to save")
            return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"conversation_{timestamp}.json"

        try:
            with open(filename, 'w') as f:
                json.dump({
                    "timestamp": timestamp,
                    "prompt_mode": self.prompt_mode,
                    "verbose": self.verbose,
                    "conversation": self.conversation_history
                }, f, indent=2)
            print(f"✅ Conversation saved to: {filename}")
        except Exception as e:
            print(f"❌ Error saving conversation: {e}")

    def show_status(self):
        """Show current CLI status and settings."""
        print("\n📊 Current Status")
        print("-" * 40)
        print(f"Verbose Mode: {'ON' if self.verbose else 'OFF'}")
        print(f"Prompt Style: {self.prompt_mode}")
        print(f"Customer Context: {self.current_customer or 'None'}")
        print(
            f"Conversation Length: {len(self.conversation_history)} messages")
        print(f"Agent Memory: {'Active' if self.agent else 'Not initialized'}")

    def process_query(self, query: str):
        """Process a user query."""
        # Build metadata
        metadata = {}
        if self.current_customer:
            metadata['customer_email'] = self.current_customer

        try:
            # Show thinking indicator
            if not self.verbose:
                print("\n🤔 Thinking...", end="\r")

            # Get response
            response = self.agent.query(query, metadata)

            # Clear thinking indicator and show response
            if not self.verbose:
                print(" " * 50, end="\r")  # Clear the line

            print(f"\n🤖 Agent:\n{response}")

            # Save to history
            self.conversation_history.append({
                "role": "user",
                "content": query,
                "metadata": metadata
            })
            self.conversation_history.append({
                "role": "assistant",
                "content": response
            })

        except Exception as e:
            print(f"\n❌ Error: {e}")
            if "credit balance" in str(e).lower():
                print("\n💡 Your Anthropic API account has insufficient credits.")
                print("   Please add credits at: https://console.anthropic.com/")

    def run(self):
        """Run the interactive CLI."""
        self.print_header()

        # Initialize agent
        if not self.initialize_agent():
            return

        # Main loop
        while True:
            try:
                # Get user input
                user_input = input("\n💬 You: ").strip()

                if not user_input:
                    continue

                # Handle commands
                if user_input.startswith('/'):
                    parts = user_input.split(maxsplit=1)
                    command = parts[0].lower()
                    args = parts[1] if len(parts) > 1 else ""

                    if command in ['/quit', '/exit']:
                        print("\n👋 Goodbye!")
                        break
                    elif command == '/help':
                        self.print_help()
                    elif command == '/reset':
                        self.agent.reset_memory()
                        self.conversation_history = []
                        print("✅ Memory cleared")
                    elif command == '/verbose':
                        self.toggle_verbose()
                    elif command == '/customer':
                        if args:
                            self.set_customer(args)
                        else:
                            print("Usage: /customer <email> or /customer clear")
                    elif command == '/prompt':
                        if args:
                            self.switch_prompt(args)
                        else:
                            self.list_prompts()
                    elif command == '/test':
                        if args:
                            self.test_sample_conversation(args)
                        else:
                            print("Usage: /test <conversation_id> or /test list")
                    elif command == '/save':
                        self.save_conversation()
                    elif command == '/tools':
                        self.test_tools()
                    elif command == '/status':
                        self.show_status()
                    else:
                        print(f"Unknown command: {command}")
                        print("Type /help for available commands")
                else:
                    # Process as query
                    self.process_query(user_input)

            except KeyboardInterrupt:
                print("\n\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"\n❌ Unexpected error: {e}")
                import traceback
                traceback.print_exc()


if __name__ == "__main__":
    cli = CloudSyncCLI()
    cli.run()
