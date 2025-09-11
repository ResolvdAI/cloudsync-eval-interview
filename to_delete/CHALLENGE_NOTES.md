# Challenge Notes for Candidates

## Current Agent Performance Issues

The agent currently scores around **80-88/100** (B grade) with these major problems:

### 🔴 Critical Issues to Fix

1. **Over-reliance on ticket creation** (30% of responses)
   - Agent creates tickets instead of solving problems
   - Missing proactive troubleshooting
   - Example: Query #5 about duplicate billing doesn't use billing lookup

2. **Missing tool usage** (20% failure rate)
   - Doesn't check system status when needed
   - Skips billing lookup for billing questions
   - Ignores available tools mentioned in knowledge base

3. **Poor response quality**
   - Too brief (avg 200-400 chars when should be 500-800)
   - Lacks empathy for frustrated customers
   - Missing urgency acknowledgment
   - No professional greetings

4. **Broken prompts** (`src/agent/prompts.py`)
   - Only mentions `create_ticket` tool
   - Says "Be brief. Don't waste time."
   - Missing instructions for other tools
   - No empathy or tone guidance

### 📊 Baseline Metrics

When you run the evaluation, you should see:
- Overall Score: ~80-88/100 (B grade)
- Tool Usage: ~70-80/100 (missing required tools)
- Content Quality: ~85-90/100 (too brief)
- Tone: ~90-95/100 (lacks empathy)

### 🎯 Target After Improvements

A good solution should achieve:
- Overall Score: 95+/100 (A grade)
- Tool Usage: 95+/100 
- Content Quality: 95+/100
- Tone: 98+/100

### 💡 Key Areas for Improvement

1. **Fix the system prompt** in `src/agent/prompts.py`
   - List ALL available tools with clear descriptions
   - Add empathy and urgency handling instructions
   - Provide response structure guidelines
   - Include tone and professionalism requirements

2. **Improve tool selection logic**
   - Billing queries → use `lookup_billing` first
   - System-wide issues → check `check_system_status`
   - Only create tickets for complex unresolved issues

3. **Enhance response completeness**
   - Acknowledge urgency when mentioned
   - Show empathy for frustrations
   - Provide complete solutions, not just ticket numbers
   - Include alternative solutions and workarounds

### 🔧 How to Test Your Improvements

1. Generate baseline data:
   ```bash
   python generate_test_data.py --max-queries 5
   python evaluate_responses.py test_outputs/test_data_*.json
   ```

2. Modify `src/agent/prompts.py`

3. Generate new data and compare:
   ```bash
   python generate_test_data.py --max-queries 5 --output test_outputs/improved.json
   python evaluate_responses.py test_outputs/improved.json
   ```

4. Look for score improvements in:
   - Tool usage accuracy
   - Response completeness
   - Tone appropriateness
   - Overall customer satisfaction

### ⚠️ Common Pitfalls

- Don't make prompts too verbose (slows down responses)
- Balance between completeness and conciseness
- Test with all 5 sample conversations, not just one
- Consider edge cases (no customer email, urgent requests, etc.)

Good luck! The goal is to show you can identify problems in an AI system and systematically improve them through prompt engineering.
