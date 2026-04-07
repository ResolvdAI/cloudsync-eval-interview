"""
Eval harness: loads JSON cases, runs the agent, scores results, writes output.
"""

import sys
import os
import json
import argparse
import logging
import functools
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Add project root to path so we can import src modules
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

load_dotenv(PROJECT_ROOT / ".env")

from eval.models import (
    EvalSuite,
    EvalCase,
    EvalCaseResult,
    EvalRunResult,
)
from eval.scorers import score_criterion
from src.agent.core import CustomerSupportAgent
from llama_index.core.llms import ChatMessage, MessageRole

logger = logging.getLogger(__name__)


def _instrument_tools(agent: CustomerSupportAgent) -> list[str]:
    """Patch agent tool functions to record calls. Returns a shared log list."""
    call_log: list[str] = []

    for tool in agent.tools:
        original_fn = tool._fn

        @functools.wraps(original_fn)
        def wrapper(*args, _name=tool.metadata.name, _orig=original_fn, **kwargs):
            call_log.append(_name)
            return _orig(*args, **kwargs)

        tool._fn = wrapper

    return call_log


def run_case(agent: CustomerSupportAgent, case: EvalCase) -> EvalCaseResult:
    """Run a single eval case against the agent and score it."""
    agent.reset_memory()

    # Instrument tools to capture calls for this case
    call_log = _instrument_tools(agent)

    # Seed conversation history into agent memory if provided
    if case.conversation_history:
        for msg in case.conversation_history:
            role = MessageRole.USER if msg.role == "user" else MessageRole.ASSISTANT
            agent.memory.put(ChatMessage(role=role, content=msg.content))

    # Run the agent
    try:
        response_str = agent.query(case.user_message, metadata=case.metadata)
        tools_called = list(call_log)
    except Exception as e:
        return EvalCaseResult(
            case_id=case.id,
            agent_response="",
            tools_called=[],
            criterion_results=[],
            weighted_score=0.0,
            error=str(e),
        )

    # Score each criterion
    criterion_results = []
    for criterion in case.scoring:
        result = score_criterion(
            criterion=criterion,
            agent_response=response_str,
            tools_called=tools_called,
            user_message=case.user_message,
        )
        criterion_results.append(result)

    # Compute weighted score
    total_weight = sum(c.weight for c in case.scoring)
    weighted_score = (
        sum(r.score * c.weight for r, c in zip(criterion_results, case.scoring)) / total_weight
        if total_weight > 0
        else 0.0
    )

    return EvalCaseResult(
        case_id=case.id,
        agent_response=response_str,
        tools_called=tools_called,
        criterion_results=criterion_results,
        weighted_score=weighted_score,
    )


def run_suite(suite: EvalSuite, verbose: bool = False) -> EvalRunResult:
    """Run all cases in an eval suite."""
    agent = CustomerSupportAgent(verbose=verbose)

    results = []
    for i, case in enumerate(suite.cases):
        logger.info(f"[{i + 1}/{len(suite.cases)}] Running case: {case.id}")
        result = run_case(agent, case)
        logger.info(f"  score={result.weighted_score:.2f}")
        results.append(result)

    avg_score = sum(r.weighted_score for r in results) / len(results) if results else 0.0

    return EvalRunResult(
        suite_name=suite.name,
        total_cases=len(results),
        avg_score=avg_score,
        results=results,
    )


def main():
    parser = argparse.ArgumentParser(description="Run eval suite against the CloudSync agent")
    parser.add_argument("suite_path", help="Path to eval suite JSON file")
    parser.add_argument("-o", "--output", help="Path to write results JSON (default: eval/results/<timestamp>.json)")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose agent output")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s", datefmt="%H:%M:%S")

    # Load suite
    with open(args.suite_path) as f:
        suite = EvalSuite.model_validate(json.load(f))

    logger.info(f"Loaded suite '{suite.name}' with {len(suite.cases)} cases")

    # Run
    run_result = run_suite(suite, verbose=args.verbose)

    # Write results
    output_dir = Path(args.output).parent if args.output else PROJECT_ROOT / "eval" / "results"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = Path(args.output) if args.output else output_dir / f"{datetime.now():%Y%m%d_%H%M%S}.json"

    with open(output_path, "w") as f:
        f.write(run_result.model_dump_json(indent=2))

    # Print summary
    print(f"\n{'=' * 50}")
    print(f"Suite: {run_result.suite_name}")
    print(f"Cases: {run_result.total_cases}")
    print(f"Avg score: {run_result.avg_score:.2f}")
    print(f"{'=' * 50}")
    for r in run_result.results:
        status = "ERR" if r.error else f"{r.weighted_score:.2f}"
        print(f"  {r.case_id}: {status}")
    print(f"\nResults written to {output_path}")


if __name__ == "__main__":
    main()
