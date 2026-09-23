# AI Agent Evaluation System - Take-Home Challenge

## Overview

Build an evaluation system for a customer support agent for CloudSync, a file synchronization and backup service. This is a real-world problem that you would be solving on the job, but generalized for the sake of the challenge.

## Setup

```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure API keys in .env
# We provide an OpenAI key (capped at $10) so you don't have to use your own.
# See the provided .env file — it's ready to use out of the box.
# Optional: swap in your own key or set LLM_MODEL=claude-3-5-haiku-20241022 with an ANTHROPIC_API_KEY

# Verify setup
python verify_setup.py

# Try the agent
python run_cli.py

# Generate test data from sample conversations in src/data/sample_conversations.json
python run_sample_conversations.py --max-queries 5
```

## The Challenge

Implement a practical evaluation system that can:

1. **Measure** agent performance systematically
2. **Identify** specific failure modes and weaknesses  
3. **Enable** iterative improvements with confidence

This is an **open-ended implementation challenge** - we want to see your engineering judgment on what matters most.

## Core Requirements

### Evaluation Framework** (`src/evals/`)

- Implement code that can evaluate agent responses
- Choose appropriate metrics for different aspects (accuracy, helpfulness, tool usage, etc.)
- Make it easy to run evaluations repeatedly

### Test Dataset**

- Create or curate a set of test cases
- Include diverse query types and difficulty levels
- Document what each test case is evaluating

### Baseline Performance Analysis**

- Run your evaluation on the current agent
- Document performance: what works well, what doesn't
- Identify specific failure modes

## Deliverables

1. **Code**: Evaluation system implementation (clean, documented, runnable)
2. **Documentation** (`SOLUTION_NOTES.md`):
   - Any assumptions you made
   - Trade-offs and design decisions
3. **Test Results**: Output from running your evaluation with clear evidence of findings

## Evaluation Criteria and Guidelines

The goal of this interview is to see:

- How you navigate a new codebase
- What types of questions you ask
- What assumptions you make
- How well you work with your tools of choice
- What you can get done in 1 hour and how you prioritize

Focus on building a practical, working evaluation system and back up your approach with clear evidence rather than theoretical claims.

Use any tools you need to help you complete the challenge. This includes development tools, LLMs, etc. as well as any packages you want to install to help you complete the challenge. If you need to install a package, please add it to the requirements.txt file.