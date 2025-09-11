# AI Agent Evaluation Challenge

## Your Task

You've inherited a customer support agent for CloudSync, a file synchronization service. Your job is to:

1. **Evaluate** the current agent's performance
2. **Identify** areas for improvement
3. **Implement** improvements
4. **Measure** the impact of your changes

## Getting Started

1. **Setup Environment**
   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   export ANTHROPIC_API_KEY="your-key"
   ```

2. **Test the Agent**
   ```bash
   # Interactive testing
   python run_cli.py
   
   # Generate test data from samples
   python generate_test_data.py --max-queries 5
   ```

3. **Examine the System**
   - Agent code: `src/agent/`
   - Knowledge base: `src/knowledge_base/documents/`
   - Sample queries: `src/data/sample_conversations.json`

## Available Tools

The agent has access to these tools:
- `search_knowledge_base` - Search documentation
- `lookup_billing` - Check customer billing information
- `create_ticket` - Create support tickets for complex issues
- `check_system_status` - Check CloudSync service status

## Deliverables

1. **Evaluation System**: Code that measures agent performance
2. **Performance Report**: Baseline metrics and identified issues
3. **Improvements**: Modified code/prompts to enhance performance
4. **Results**: Measurable improvements with before/after comparison

## Evaluation Criteria

Your solution will be assessed on:
- Problem identification accuracy
- Quality of evaluation metrics
- Effectiveness of improvements
- Code quality and documentation
- Clear demonstration of improvements

## Time Expectation

This challenge should take 1 hour to complete.

Good luck!
