# CloudSync Customer Support Agent — Evaluation System

## Project Overview

This is an **AI agent evaluation challenge** for CloudSync, a file synchronization and backup SaaS product. The repo contains a working customer support agent built with LlamaIndex's ReAct framework, and the challenge is to build an evaluation system (`evals/`) that measures, identifies failures in, and improves the agent.

## Architecture

### Agent Core (`src/agent/core.py`)

**Framework:** LlamaIndex `ReActAgent` — a reasoning-and-acting loop that interleaves LLM "Thought" steps with tool calls until it reaches a final answer.

- **LLM:** Configurable via `LLM_MODEL` env var. Default `gpt-4o-mini` (OpenAI). Supports `claude-*` models via Anthropic.
- **Embeddings:** OpenAI `text-embedding-3-small` for knowledge base vector search.
- **Memory:** `ChatMemoryBuffer` with 4096-token limit for conversation history.
- **Max iterations:** 10 ReAct loops per query.
- **Temperature:** 0.3 (set in `config/settings.py`).
- **System prompt:** Minimal 3-line prompt in `src/agent/prompts.py` — deliberately sparse (likely a target for improvement).

### Agentic Capabilities

The agent operates as a **single ReAct agent** (no multi-agent orchestration, no sub-agents, no routing). On each user query it:

1. Receives the formatted query (with optional metadata: `customer_email`, `customer_id`, `account_type`)
2. Enters a Thought → Action → Observation loop (up to 10 iterations)
3. Selects tools via the ReAct prompt pattern
4. Returns a final text response

There is **no planning step, no chain-of-thought decomposition, no memory summarization, and no self-reflection/retry** beyond what ReAct provides natively.

### Tool Calls (4 tools registered)

| Tool Name | Class | Method | Description | Input | Output |
|---|---|---|---|---|---|
| `search_knowledge_base` | Lambda wrapping `VectorStoreIndex.as_query_engine` | `query_engine.query(query)` | RAG search over CloudSync docs (top-k=3 similarity) | `query: str` | String answer from retrieval QA |
| `lookup_billing` | `BillingLookupTool` | `.lookup(customer_email?, customer_id?)` | Mock billing data for 5 hardcoded customers | email or customer ID | Dict with plan, status, next billing date, payment info |
| `create_ticket` | `TicketCreationTool` | `.create(subject, description, customer_email?, priority?, category?)` | Creates a mock support ticket with auto-incrementing ID | subject, description, priority, category | Dict with ticket_id, estimated response time |
| `check_system_status` | `SystemStatusTool` | `.check(service?)` | Mock system health for 5 services (20% chance of random degradation) | optional service name | Dict with service statuses, maintenance windows, incidents |

**Important tool behaviors:**
- All tools are **mock implementations** — no real backends. BillingLookupTool uses `random.choice` for plan/status, so results are non-deterministic across instantiations.
- SystemStatusTool has a 20% random chance of injecting a degraded/outage/maintenance status, and 30% chance of a maintenance window. This makes eval results non-deterministic.
- Tools are toggled via `ENABLE_BILLING`, `ENABLE_TICKETS`, `ENABLE_STATUS` env vars (all default `True`).
- The KB tool depends on the vector index — first run builds and caches it to `storage/vector_index/`.

### Escalation Paths

The agent has **one explicit escalation path**: the `create_ticket` tool. The system prompt says "Create support tickets when needed" but provides no guidance on when to escalate vs. self-resolve. Escalation decisions are entirely up to the LLM's judgment.

Ticket priority levels: `low`, `medium`, `high`, `critical` → mapped to response time SLAs (48h, 24h, 4h, 1h respectively).

Ticket categories: `billing`, `technical`, `account`, `feature_request`, `bug_report`, `other`.

There is **no human-in-the-loop mechanism, no confidence thresholds, no fallback to a different agent, and no supervisor agent**. The agent either answers directly or creates a ticket.

### Knowledge Base (`src/knowledge_base/documents/`)

Three markdown files indexed into a vector store:

| File | Content |
|---|---|
| `faq.md` | General product FAQ — features, security, platforms, account management, storage, sharing, technical issues, mobile |
| `pricing_plans.md` | Pricing tiers (Free/Basic/$9/Professional/$29/Enterprise/$99), family/team plans, add-ons, discounts, billing policies |
| `troubleshooting.md` | Login issues, sync problems, performance, file/folder issues, mobile app issues, error codes, contacting support |

### Configuration (`config/settings.py`)

Uses `pydantic-settings` with `.env` file. Key settings:
- `LLM_MODEL`: default `gpt-4o-mini`
- `TEMPERATURE`: 0.3
- `MAX_TOKENS`: 2048
- `CHUNK_SIZE`: 512, `CHUNK_OVERLAP`: 50
- `EVAL_BATCH_SIZE`: 10, `EVAL_OUTPUT_DIR`: `evaluation_results`

## Entry Points

| Script | Purpose |
|---|---|
| `run_cli.py` | Interactive CLI with `/test`, `/tools`, `/customer`, `/verbose` commands |
| `example_usage.py` | Scripted demo running 5 basic queries + sample conversations + direct tool tests |
| `generate_test_data.py` | Runs sample conversations through agent, saves JSON output to `test_outputs/` |
| `verify_setup.py` | Checks project structure, env vars, knowledge base docs |
| `tests/test_agent.py` | Pytest suite: component tests (tools) + response tests (requires API key) |

## Sample Test Data (`src/data/sample_conversations.json`)

5 sample conversations covering:
- `conv_001`: Billing lookup (subscription + next billing date)
- `conv_002`: Urgent sync failure on Mac (time-sensitive, needs troubleshooting + possible ticket)
- `conv_003`: Plan upgrade request (Basic → Professional)
- `conv_004`: Enterprise-wide sync failure after update (complex, multi-user, escalation-worthy)
- `conv_005`: Double-charge billing dispute (no email provided — edge case)

## Known Architectural Weaknesses (eval targets)

1. **Non-deterministic tools**: `random.choice` in BillingLookupTool and SystemStatusTool means same query can produce different answers across runs
2. **Sparse system prompt**: Only 3 lines — no persona, no tone guidance, no escalation criteria, no guardrails
3. **No input validation**: Agent accepts any query with no content filtering or scope detection
4. **No tool call validation**: Agent can hallucinate tool results or call tools with wrong parameters
5. **Async complexity**: `core.py:302-322` has fragile event loop handling with thread pool fallback
6. **Memory double-write**: The ReAct agent has its own memory, but `query()` also manually pushes to memory at lines 328-330 — potential duplication
7. **No error recovery**: If a tool call fails mid-conversation, there's no retry or graceful degradation
8. **No out-of-scope detection**: Agent will attempt to answer questions unrelated to CloudSync

## Commands

```bash
# Setup
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# Run
python run_cli.py                          # Interactive CLI
python example_usage.py                    # Demo queries
python generate_test_data.py --max-queries 5  # Generate test data
python verify_setup.py                     # Verify setup

# Test
pytest tests/test_agent.py -v              # Run tests (needs API key)
```

## Challenge Deliverables

All evaluation work goes in `evals/` directory:
- Evaluation framework code
- Test dataset (10-50 cases)
- Baseline performance analysis
- `evals/SOLUTION_NOTES.md` with findings

Submission: private GitHub repo, add `samuel-casey` as collaborator.
