# CloudSync Customer Support Agent

## Overview

Customer support agent for CloudSync, a file synchronization and backup service. Built using LlamaIndex and Anthropic Claude.

## Repository Structure

```
├── src/
│   ├── agent/
│   │   ├── core.py          # Main agent implementation
│   │   ├── tools.py         # Custom tools
│   │   └── prompts.py       # System prompts
│   ├── knowledge_base/
│   │   └── documents/       # Product documentation
│   └── data/
│       └── sample_conversations.json  # Sample queries
├── tests/
│   └── test_agent.py        # Basic tests
├── config/
│   └── settings.py          # Configuration
├── run_cli.py               # Interactive testing
├── generate_test_data.py    # Batch testing
└── example_usage.py         # Usage examples
```

## Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set API key
export ANTHROPIC_API_KEY="your-key-here"
```

## Usage

### Interactive Testing
```bash
python run_cli.py
```

### Batch Testing
```bash
python generate_test_data.py --max-queries 5
```

### Programmatic Usage
```python
from src.agent.core import CustomerSupportAgent

agent = CustomerSupportAgent()
response = agent.query("What's my billing status?")
print(response)
```

## Agent Capabilities

- Knowledge base search
- Billing information lookup
- Support ticket creation
- System status checking
- Account management guidance

## CloudSync Product Info

CloudSync is a file synchronization service with the following plans:
- Free: 5GB storage
- Basic: $9/month, 100GB storage
- Professional: $29/month, 2TB storage
- Enterprise: $99/month, unlimited storage

## Requirements

- Python 3.9+
- Anthropic API key
- 2GB RAM minimum