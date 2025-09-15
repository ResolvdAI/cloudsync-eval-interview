"""
System prompts and templates for the Customer Support Agent.

These prompts define the agent's personality, capabilities, and response patterns.
"""

# Main system prompt that defines the agent's role and behavior
SYSTEM_PROMPT = """You are a CloudSync customer support assistant. Help users quickly.

Use available tools to resolve issues. Create support tickets when needed.

Keep responses concise and efficient."""

# Template for formatting user queries with context
QUERY_PROMPT_TEMPLATE = """
Customer Inquiry: {query}

Context Information:
{context}

Provide assistance for this customer inquiry.
"""

# Prompt for evaluating response quality
EVALUATION_PROMPT = """Evaluate the following customer support interaction:

Customer Query: {query}
Agent Response: {response}

Please evaluate based on these criteria:
1. **Accuracy**: Is the information provided correct and relevant?
2. **Completeness**: Does the response fully address the customer's inquiry?
3. **Tone**: Is the response professional, friendly, and appropriate?
4. **Tool usage**: Were appropriate tools used and actions taken?
"""
