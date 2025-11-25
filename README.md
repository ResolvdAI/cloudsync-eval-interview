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

# Set API keys
export ANTHROPIC_API_KEY="your-key"
# Optional: export OPENAI_API_KEY="your-key" for better embeddings

# Verify setup
python verify_setup.py

# Try the agent
python run_cli.py

# Generate test data from sample conversations in src/data/sample_conversations.json
python generate_test_data.py --max-queries 5
```

## The Challenge

In your system design interview, you discussed how to evaluate and monitor AI agents in production. Now implement a practical evaluation system that can:

1. **Measure** agent performance systematically
2. **Identify** specific failure modes and weaknesses  
3. **Enable** iterative improvements with confidence

This is an **open-ended implementation challenge** - we want to see your engineering judgment on what matters most.

### Core Requirements

**1. Evaluation Framework** (`src/evals/`)
- Implement code that can evaluate agent responses
- Choose appropriate metrics for different aspects (accuracy, helpfulness, tool usage, etc.)
- Make it easy to run evaluations repeatedly

**2. Test Dataset**
- Create or curate a set of test cases
- Include diverse query types and difficulty levels
- Document what each test case is evaluating

**3. Baseline Performance Analysis**
- Run your evaluation on the current agent
- Document performance: what works well, what doesn't
- Identify specific failure modes

### Deliverables

1. **Code**: Evaluation system implementation (clean, documented, runnable)
2. **Documentation** (`SOLUTION_NOTES.md`): 
   - How your evaluation system works
   - Baseline performance metrics
   - Trade-offs and design decisions
   - Any assumptions you made
3. **Test Results**: Output from running your evaluation with clear evidence of findings

## Evaluation Criteria

### Technical Quality (35%)
- **Eval design:** Are your metrics meaningful? Do they actually measure quality?
- **Code quality:** Clean, well-structured, properly handles edge cases
- **Reproducibility:** Can we run your evaluation and see the same results?

### Problem-Solving (30%)
- **Issue identification:** Did you find real weaknesses in the agent?
- **Improvement quality:** Are your improvements well-targeted and effective?
- **Trade-off awareness:** Do you understand the costs/benefits of your choices?

### Communication (25%)
- **Documentation:** Clear explanation of your approach and findings
- **Metrics presentation:** Easy to understand performance results
- **Decision rationale:** Why did you focus on X vs Y?

### Development Practices (10%)
- **Git hygiene:** Clear, logical commit messages and history
- **Incremental progress:** Commits show your work progression
- **Code organization:** Sensible file structure and separation of concerns

## Constraints

**Time:** 2-4 hours for a complete submission. We value focus and prioritization over exhaustive work. Use whatever AI tools you need.

**Prioritize:** Practical over perfect. Working eval system > theoretically optimal but complex solution. Evidence over claims.

**Out of Scope:** Production infrastructure, real-time dashboards, extensive ML Ops pipelines, massive test datasets (10-50 good test cases >> 1000 mediocre ones)

## Submission

Create a new private GitHub repo and add `samuel-casey` as a collaborator with:
- All code (evaluation framework + any improvements) in the `evals/` directory. Do not include any code or documentation outside of the `evals/` directory. This may not be realistic but it is for the sake of the challenge.
- `evals/SOLUTION_NOTES.md` with your findings and assumptions
- Any tests and test outputs demonstrating results
- Instructions for running your evaluation
  
Use any tools you need to help you complete the challenge. This includes development tools, LLMs, etc. as well as any packages you want to install to help you complete the challenge. If you need to install a package, please add it to the requirements.txt file.

**Note on Git Practices:** We'll review your commit history as part of the evaluation. Use clear commit messages and make incremental commits as you work through the challenge. Your git history should tell the story of your development process.

## Questions?

If anything is unclear about the CloudSync product, agent capabilities, or the challenge itself, document your assumptions in your report and proceed. We're interested in seeing how you handle ambiguity.

---

Good luck! We're excited to see your approach to this problem.