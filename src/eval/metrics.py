"""
Metrics classes for evaluating the CloudSync Customer Support Agent.

Two main classes:
- ResponseMetrics: measures response quality via LLM judge, latency, etc.
- ToolMetrics: measures tool selection accuracy and argument correctness.
"""

import json
import logging
from difflib import SequenceMatcher
from typing import Dict, Any, List, Optional
from collections import defaultdict

from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

LLM_JUDGE_PROMPT = """You are evaluating a customer support agent's response.

The agent was given this query from a customer:
{query}

The agent responded with:
{response}

The ideal (ground truth) response is:
{ground_truth}

Note: The ground truth may contain {{placeholders}} like {{plan}} or {{amount}} which represent dynamic values. The agent's response should contain actual values in place of these placeholders. Do NOT penalize the agent for using specific values instead of placeholders.

Also note: The agent may have received actual data from tool calls. If the agent faithfully reports tool data, that is correct even if the specific values differ from the ground truth template.

Compare the agent's response to the ground truth and determine: was this response helpful in answering the user's question?

A response is helpful (1) if it:
- Addresses the user's question or request
- Provides accurate information consistent with the ground truth
- Gives the user what they need to move forward

A response is NOT helpful (0) if it:
- Fails to answer the question asked
- Contains incorrect or misleading information
- Misses critical information that the ground truth covers
- Takes an inappropriate action (e.g. creates a ticket when it should ask for clarification)

Respond ONLY with valid JSON in this exact format, no other text:
{{"helpful": <1 or 0>, "reasoning": "<brief explanation of why the response was or was not helpful>"}}"""


class ResponseMetrics:
    """
    Measures the quality of the agent's final response.

    Uses an LLM judge to produce a binary helpful score (1 or 0) per sample
    by comparing the response to the ground truth, plus latency tracking.
    """

    def __init__(self, judge_model: str = "gpt-4o-mini"):
        self.judge_model = judge_model
        self.client = OpenAI()

    def score_single(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Score a single eval result.

        Returns:
          - helpful: 1 or 0
          - reasoning: LLM judge explanation
          - latency: response_time in seconds
        """
        ground_truth = result.get("ground_truth")
        response = result.get("trace", {}).get("final_response", "")
        query = result.get("query", "")

        if ground_truth and response:
            judge_result = self._run_llm_judge(query, response, ground_truth)
        else:
            judge_result = {
                "helpful": None,
                "reasoning": "Missing ground truth or response",
            }

        return {
            "helpful": judge_result.get("helpful"),
            "reasoning": judge_result.get("reasoning"),
            "latency": result.get("response_time"),
        }

    def score_batch(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Score all results and return per-sample, aggregate, and per-category metrics.
        """
        per_sample = {}
        for result in results:
            if "error" in result:
                continue
            per_sample[result["test_id"]] = self.score_single(result)

        aggregate = self._aggregate(per_sample)
        per_category = self._aggregate_by_category(results, per_sample)

        return {
            "per_sample": per_sample,
            "aggregate": aggregate,
            "per_category": per_category,
        }

    def _run_llm_judge(self, query: str, response: str, ground_truth: str) -> Dict[str, Any]:
        prompt = LLM_JUDGE_PROMPT.format(
            query=query, response=response, ground_truth=ground_truth
        )
        try:
            completion = self.client.chat.completions.create(
                model=self.judge_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0,
                max_tokens=300,
            )
            raw = completion.choices[0].message.content.strip()
            return json.loads(raw)
        except Exception as e:
            logger.error(f"LLM judge failed: {e}")
            return {
                "helpful": None,
                "reasoning": f"Judge error: {e}",
            }

    def _aggregate(self, per_sample: Dict[str, Dict]) -> Dict[str, Any]:
        helpful_values = [
            s["helpful"] for s in per_sample.values() if s["helpful"] is not None
        ]
        total = len(helpful_values)
        helpful_count = sum(helpful_values) if helpful_values else 0

        latencies = [s["latency"] for s in per_sample.values() if s.get("latency") is not None]

        return {
            "total_samples": len(per_sample),
            "helpful_count": helpful_count,
            "not_helpful_count": total - helpful_count,
            "helpful_rate": round(helpful_count / total, 2) if total else None,
            "avg_latency": round(sum(latencies) / len(latencies), 2) if latencies else None,
            "max_latency": round(max(latencies), 2) if latencies else None,
        }

    def _aggregate_by_category(
        self, results: List[Dict], per_sample: Dict[str, Dict]
    ) -> Dict[str, Dict]:
        category_map = defaultdict(list)
        for result in results:
            test_id = result["test_id"]
            cat = result.get("category", "unknown")
            if test_id in per_sample:
                category_map[cat].append(per_sample[test_id])

        per_category = {}
        for cat, samples in category_map.items():
            helpful_values = [s["helpful"] for s in samples if s["helpful"] is not None]
            total = len(helpful_values)
            helpful_count = sum(helpful_values) if helpful_values else 0
            latencies = [s["latency"] for s in samples if s.get("latency") is not None]

            per_category[cat] = {
                "total_samples": len(samples),
                "helpful_count": helpful_count,
                "not_helpful_count": total - helpful_count,
                "helpful_rate": round(helpful_count / total, 2) if total else None,
                "avg_latency": round(sum(latencies) / len(latencies), 2) if latencies else None,
            }

        return per_category


class ToolMetrics:
    """
    Measures tool selection accuracy and argument correctness.

    Uses fuzzy matching for tool argument comparison.
    """

    def __init__(self, similarity_threshold: float = 0.7):
        self.similarity_threshold = similarity_threshold

    def score_single(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Score a single eval result on tool usage.

        Returns:
          - tool_selection: {correct, expected, actual, missing, extra}
          - tool_args: {score, details} with fuzzy matching
        """
        expected_tools = set(result.get("expected_tools", []))
        actual_tools = set(result.get("trace", {}).get("tools_used", []))

        # Tool selection
        selection = {
            "correct": expected_tools == actual_tools,
            "expected": sorted(expected_tools),
            "actual": sorted(actual_tools),
            "missing": sorted(expected_tools - actual_tools),
            "extra": sorted(actual_tools - expected_tools),
        }

        # Tool argument matching
        expected_args = result.get("expected_tool_args", {})
        actual_calls = result.get("trace", {}).get("tool_calls", [])
        args_result = self._score_tool_args(expected_args, actual_calls)

        return {
            "tool_selection": selection,
            "tool_args": args_result,
        }

    def score_batch(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Score all results and return per-sample, aggregate, and per-category metrics.
        """
        per_sample = {}
        for result in results:
            if "error" in result:
                continue
            per_sample[result["test_id"]] = self.score_single(result)

        aggregate = self._aggregate(per_sample)
        per_category = self._aggregate_by_category(results, per_sample)

        return {
            "per_sample": per_sample,
            "aggregate": aggregate,
            "per_category": per_category,
        }

    def _score_tool_args(
        self, expected_args: Dict[str, Dict], actual_calls: List[Dict]
    ) -> Dict[str, Any]:
        if not expected_args:
            return {"score": 1.0, "details": {}}

        actual_by_tool = {}
        for call in actual_calls:
            actual_by_tool[call["tool_name"]] = call.get("tool_kwargs", {})

        details = {}
        scores = []

        for tool_name, expected_kwargs in expected_args.items():
            actual_kwargs = actual_by_tool.get(tool_name, {})
            if not actual_kwargs:
                details[tool_name] = {"score": 0.0, "reason": "tool not called"}
                scores.append(0.0)
                continue

            tool_scores = []
            arg_details = {}
            for key, expected_val in expected_kwargs.items():
                actual_val = actual_kwargs.get(key)
                if actual_val is None:
                    arg_details[key] = {"score": 0.0, "expected": expected_val, "actual": None}
                    tool_scores.append(0.0)
                else:
                    sim = self._fuzzy_match(str(expected_val), str(actual_val))
                    passed = sim >= self.similarity_threshold
                    arg_details[key] = {
                        "score": round(sim, 2),
                        "expected": expected_val,
                        "actual": actual_val,
                        "passed": passed,
                    }
                    tool_scores.append(sim)

            tool_score = sum(tool_scores) / len(tool_scores) if tool_scores else 1.0
            details[tool_name] = {"score": round(tool_score, 2), "args": arg_details}
            scores.append(tool_score)

        overall = sum(scores) / len(scores) if scores else 1.0
        return {"score": round(overall, 2), "details": details}

    def _fuzzy_match(self, expected: str, actual: str) -> float:
        expected_lower = expected.lower().strip()
        actual_lower = actual.lower().strip()
        if expected_lower == actual_lower:
            return 1.0
        return SequenceMatcher(None, expected_lower, actual_lower).ratio()

    def _aggregate(self, per_sample: Dict[str, Dict]) -> Dict[str, Any]:
        total = len(per_sample)
        if not total:
            return {}

        correct_selections = sum(
            1 for s in per_sample.values() if s["tool_selection"]["correct"]
        )
        arg_scores = [s["tool_args"]["score"] for s in per_sample.values()]

        return {
            "total_samples": total,
            "tool_selection_accuracy": round(correct_selections / total, 2),
            "tool_selection_correct": correct_selections,
            "tool_selection_incorrect": total - correct_selections,
            "avg_tool_args_score": round(sum(arg_scores) / len(arg_scores), 2) if arg_scores else None,
        }

    def _aggregate_by_category(
        self, results: List[Dict], per_sample: Dict[str, Dict]
    ) -> Dict[str, Dict]:
        category_map = defaultdict(list)
        for result in results:
            test_id = result["test_id"]
            cat = result.get("category", "unknown")
            if test_id in per_sample:
                category_map[cat].append(per_sample[test_id])

        per_category = {}
        for cat, samples in category_map.items():
            total = len(samples)
            correct = sum(1 for s in samples if s["tool_selection"]["correct"])
            arg_scores = [s["tool_args"]["score"] for s in samples]
            per_category[cat] = {
                "total_samples": total,
                "tool_selection_accuracy": round(correct / total, 2) if total else None,
                "avg_tool_args_score": round(sum(arg_scores) / len(arg_scores), 2) if arg_scores else None,
            }

        return per_category
