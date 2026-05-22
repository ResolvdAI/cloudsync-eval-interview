#!/usr/bin/env python3
"""
Eval runner for the CloudSync Customer Support Agent.

Loads test cases from tests/eval_dataset.json, runs each through the agent,
captures the full conversation trace (system prompt, tool calls, tool responses,
final response), and writes structured results to test_outputs/.
"""

import json
import time
import asyncio
import argparse
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

from dotenv import load_dotenv

load_dotenv()

import sys
sys.path.insert(0, str(Path(__file__).parent))

from src.agent.core import CustomerSupportAgent
from src.agent.prompts import SYSTEM_PROMPT


def load_eval_dataset(path: str = "tests/eval_dataset.json") -> Dict[str, Any]:
    with open(path, "r") as f:
        return json.load(f)


def run_single_case(agent: CustomerSupportAgent, test_case: Dict[str, Any]) -> Dict[str, Any]:
    """
    Run a single eval test case and capture the full trace.

    Returns a result dict with query, response, tool calls, timing, etc.
    """
    query = test_case["query"]
    customer_email = test_case.get("customer_email")

    metadata = {}
    if customer_email:
        metadata["customer_email"] = customer_email

    start_time = time.time()

    # Run the agent and capture the AgentOutput (not just str)
    agent_output = _run_agent_raw(agent, query, metadata or None)

    response_time = time.time() - start_time

    # Extract tool calls from the AgentOutput
    tool_calls_trace = _extract_tool_calls(agent_output)
    tools_used = [tc["tool_name"] for tc in tool_calls_trace]
    final_response = str(agent_output)

    # Store exchange in agent memory (matching core.py behavior)
    from llama_index.core.llms import ChatMessage, MessageRole
    agent.memory.put(ChatMessage(role=MessageRole.USER, content=query))
    agent.memory.put(ChatMessage(role=MessageRole.ASSISTANT, content=final_response))

    return {
        "test_id": test_case["id"],
        "category": test_case["category"],
        "subcategory": test_case.get("subcategory"),
        "difficulty": test_case.get("difficulty"),
        "query": query,
        "customer_email": customer_email,
        "system_prompt": SYSTEM_PROMPT,
        "ground_truth": test_case.get("ground_truth"),
        "expected_tools": test_case.get("expected_tools", []),
        "expected_tool_args": test_case.get("expected_tool_args", {}),
        "expected_response_contains": test_case.get("expected_response_contains", []),
        "expected_response_excludes": test_case.get("expected_response_excludes", []),
        "trace": {
            "tool_calls": tool_calls_trace,
            "tools_used": tools_used,
            "final_response": final_response,
        },
        "response_time": response_time,
    }


def _run_agent_raw(agent: CustomerSupportAgent, query: str, metadata: Optional[Dict] = None):
    """
    Run the agent and return the raw AgentOutput instead of a string.

    Mirrors the async handling in CustomerSupportAgent.query() but skips
    the str() conversion so we can inspect tool_calls.
    """
    from llama_index.core.llms import ChatMessage, MessageRole

    conversation_history = agent.memory.get()
    formatted_query = agent._format_query_with_history(query, metadata, conversation_history)

    async def _run():
        return await agent.agent.run(formatted_query)

    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, _run())
                return future.result()
        else:
            return loop.run_until_complete(_run())
    except RuntimeError:
        return asyncio.run(_run())


def _extract_tool_calls(agent_output) -> List[Dict[str, Any]]:
    """
    Extract tool call info from the AgentOutput.

    AgentOutput.tool_calls is a list of ToolSelection objects with
    tool_name, tool_kwargs, and tool_id fields.
    """
    tool_calls = []
    raw_calls = getattr(agent_output, "tool_calls", [])

    for tc in raw_calls:
        entry = {
            "tool_name": getattr(tc, "tool_name", str(tc)),
            "tool_kwargs": getattr(tc, "tool_kwargs", {}),
        }
        # If it's a ToolCallResult (has tool_output), capture the output too
        tool_output = getattr(tc, "tool_output", None)
        if tool_output is not None:
            entry["tool_output"] = str(tool_output)
        tool_calls.append(entry)

    return tool_calls


def run_eval(
    dataset_path: str = "tests/eval_dataset.json",
    output_dir: str = "test_outputs",
    max_cases: Optional[int] = None,
    categories: Optional[List[str]] = None,
    verbose: bool = False,
    quiet: bool = False,
) -> str:
    """
    Run the full eval suite and write results to output_dir.

    Returns the path to the output file.
    """
    if quiet:
        logging.getLogger("src.agent.core").setLevel(logging.WARNING)
        logging.getLogger("llama_index").setLevel(logging.WARNING)
    elif not verbose:
        logging.getLogger("src.agent.core").setLevel(logging.INFO)

    dataset = load_eval_dataset(dataset_path)
    test_cases = dataset["test_cases"]

    if categories:
        test_cases = [tc for tc in test_cases if tc["category"] in categories]

    if max_cases:
        test_cases = test_cases[:max_cases]

    print(f"Loaded {len(test_cases)} test cases")

    print("Initializing agent...")
    agent = CustomerSupportAgent(verbose=verbose)

    results = []
    start_time = datetime.now()

    for i, test_case in enumerate(test_cases, 1):
        print(f"\n[{i}/{len(test_cases)}] {test_case['id']}: {test_case['query'][:60]}...")

        try:
            result = run_single_case(agent, test_case)
            tools_str = ", ".join(result["trace"]["tools_used"]) or "none"
            print(f"  Tools: {tools_str} | Time: {result['response_time']:.1f}s")
            results.append(result)
        except Exception as e:
            print(f"  ERROR: {e}")
            results.append({
                "test_id": test_case["id"],
                "category": test_case["category"],
                "query": test_case["query"],
                "error": str(e),
            })

        # Reset memory between test cases so they're independent
        agent.reset_memory()

    elapsed = (datetime.now() - start_time).total_seconds()

    # Build output
    output = {
        "metadata": {
            "created_at": datetime.now().isoformat(),
            "dataset_path": dataset_path,
            "total_cases": len(test_cases),
            "successful": sum(1 for r in results if "error" not in r),
            "failed": sum(1 for r in results if "error" in r),
            "elapsed_seconds": round(elapsed, 1),
            "agent_model": agent.llm.model,
        },
        "results": results,
    }

    # Write output
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = output_path / f"eval_results_{timestamp}.json"

    with open(output_file, "w") as f:
        json.dump(output, f, indent=2, default=str)

    print(f"\nCompleted in {elapsed:.1f}s")
    print(f"Results written to {output_file}")

    # Print summary
    _print_summary(results)

    return str(output_file)


def _print_summary(results: List[Dict[str, Any]]):
    """Print a summary table of results."""
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")

    successful = [r for r in results if "error" not in r]
    failed = [r for r in results if "error" in r]

    print(f"Total: {len(results)} | Passed: {len(successful)} | Errors: {len(failed)}")

    if not successful:
        return

    # Per-category breakdown
    categories = {}
    for r in successful:
        cat = r["category"]
        if cat not in categories:
            categories[cat] = {"total": 0, "correct_tools": 0}
        categories[cat]["total"] += 1
        actual_tools = set(r["trace"]["tools_used"])
        expected_tools = set(r.get("expected_tools", []))
        if actual_tools == expected_tools:
            categories[cat]["correct_tools"] += 1

    print(f"\n{'Category':<20} {'Total':>6} {'Tool Match':>11} {'Rate':>6}")
    print("-" * 45)
    for cat, stats in categories.items():
        rate = stats["correct_tools"] / stats["total"] * 100 if stats["total"] else 0
        print(f"{cat:<20} {stats['total']:>6} {stats['correct_tools']:>11} {rate:>5.0f}%")

    # Average response time
    times = [r["response_time"] for r in successful]
    print(f"\nAvg response time: {sum(times) / len(times):.1f}s")


def main():
    parser = argparse.ArgumentParser(description="Run eval suite for CloudSync agent")
    parser.add_argument(
        "--dataset", default="tests/eval_dataset.json", help="Path to eval dataset JSON"
    )
    parser.add_argument(
        "--output-dir", default="test_outputs", help="Output directory for results"
    )
    parser.add_argument(
        "--max-cases", type=int, help="Max number of test cases to run"
    )
    parser.add_argument(
        "--category",
        action="append",
        dest="categories",
        choices=["tool_selection", "tool_arguments", "knowledge_base"],
        help="Filter by category (can specify multiple)",
    )
    parser.add_argument("--verbose", action="store_true", help="Show agent reasoning")
    parser.add_argument("--quiet", action="store_true", help="Suppress agent logging")

    args = parser.parse_args()

    run_eval(
        dataset_path=args.dataset,
        output_dir=args.output_dir,
        max_cases=args.max_cases,
        categories=args.categories,
        verbose=args.verbose,
        quiet=args.quiet,
    )


if __name__ == "__main__":
    main()
