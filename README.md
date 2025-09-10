# AI Agent Evaluation & Prompt Optimization Challenge

## Overview

You've been tasked with building an evaluation system and implementing prompt improvements for our customer support AI agent. The agent is built using LlamaIndex and handles customer inquiries by leveraging both a knowledge base and external tools.

**Time Allocation**: 1 hour  
**Focus**: System design, evaluation methodology, and prompt optimization

## Problem Statement

Our customer support agent is deployed but we need to:
1. **Evaluate its performance** systematically across different types of customer inquiries
2. **Identify prompt improvement opportunities** and implement iterations
3. **Measure key metrics** around task completion and response quality

The agent currently handles inquiries about our fictional SaaS product "CloudSync" - a file synchronization and backup service.

## Repository Structure

```
├── README.md                 # This file
├── requirements.txt          # Python dependencies
├── src/
│   ├── agent/
│   │   ├── __init__.py
│   │   ├── core.py          # Main agent implementation
│   │   ├── tools.py         # Custom tools (billing lookup, ticket creation, etc.)
│   │   └── prompts.py       # Current system prompts
│   ├── knowledge_base/
│   │   ├── __init__.py
│   │   └── documents/       # FAQ docs, troubleshooting guides, etc.
│   └── data/
│       └── sample_conversations.json  # Example customer interactions
├── tests/
│   └── test_agent.py        # Basic agent tests
└── config/
    └── settings.py          # Configuration (API keys, etc.)
```

## Current Agent Capabilities

The customer support agent can:
- **Answer questions** using the knowledge base (FAQs, troubleshooting, pricing info)
- **Look up billing information** using customer email/ID
- **Create support tickets** for complex issues
- **Check system status** for service outages
- **Provide account management** guidance

## Your Task

Build an evaluation system that:

### Core Requirements (Must Complete)
1. **Evaluation Framework**
   - Design a system to test the agent against various customer inquiry types
   - Implement metrics for task completion accuracy and response quality
   - Include both automated and human-evaluable components

2. **Prompt Improvement**
   - Analyze current prompts for weaknesses
   - Implement and test prompt iterations
   - Document your reasoning and results

### Success Metrics
- **Task Completion Accuracy**: Does the agent successfully resolve/route the customer inquiry?
- **Response Quality**: Is the response helpful, accurate, and appropriately toned?
- **Tool Usage**: Were the appropriate tools for a given request used?

### Bonus Points
- Automated prompt optimization
- Failure mode analysis
- Scalable evaluation infrastructure
- Integration testing

## Technical Stack

- **LLM Provider**: Anthropic Claude (via API)
- **Agent Framework**: LlamaIndex
- **Python Version**: 3.9+
- **Key Libraries**: LlamaIndex, pandas, pytest

## Getting Started

1. **Setup Environment**
   ```bash
   pip install -r requirements.txt
   export ANTHROPIC_API_KEY="your-key-here"
   ```

2. **Test the Agent Interactively**
   ```bash
   # Run interactive CLI to manually test queries
   python run_cli.py
   
   # Or test programmatically
   python example_usage.py
   ```

3. **Generate Test Data**
   ```bash
   # Generate test dataset from sample queries (outputs to test_outputs/ directory)
   python generate_test_data.py
   
   # Generate with specific options
   python generate_test_data.py --max-queries 10
   python generate_test_data.py --output test_outputs/my_test.json
   
   # Control logging verbosity
   python generate_test_data.py --quiet    # Suppress agent internal logs
   python generate_test_data.py            # Normal mode (INFO level)
   python generate_test_data.py --verbose  # Show detailed DEBUG logs
   ```

4. **Evaluate Agent Performance**
   ```bash
   # Generate test data first
   python generate_test_data.py --max-queries 5
   
   # Evaluate against answer key
   python evaluate_responses.py test_outputs/test_data_*.json --verbose
   ```
   
5. **Build Your Own Evaluation System**
   - Use `answer_key.json` as reference for expected behavior
   - Review `evaluate_responses.py` for evaluation logic example
   - Check knowledge base in `src/knowledge_base/documents/`

## Evaluation Considerations

Think about:
- **Diverse inquiry types**: billing, technical issues, account management, general questions
- **Edge cases**: ambiguous requests, out-of-scope questions, multi-step problems
- **Quality dimensions**: accuracy, helpfulness, tone, completeness
- **Failure modes**: hallucination, tool misuse, incomplete responses

## Resources

- [LlamaIndex Documentation](https://docs.llamaindex.ai/)
- [Anthropic API Reference](https://docs.anthropic.com/)
- [LLM Evaluation Best Practices](https://humanloop.com/blog/llm-evaluation-guide)

## Deliverables

At the end of the hour, be prepared to:
1. **Demo your evaluation system** running against the agent
2. **Present your findings** on current prompt performance
3. **Show prompt improvements** and their measured impact
4. **Discuss your system architecture** and design decisions

---

**Note**: Focus on building something functional rather than perfect. We value clear thinking, good architectural decisions, and practical evaluation approaches over polished code.
