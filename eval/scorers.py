"""
Scoring functions: direct matching and LLM-as-Judge.
"""

import os
from pydantic import BaseModel, Field
from openai import OpenAI
from eval.models import ScoringMethod, ScoringCriteria, CriterionResult

LLM_JUDGE_PROMPT = """\
You are an evaluation judge. Score the agent's response on a 0.0–1.0 scale.

## Rubric
{rubric}

## Conversation context
{context}

## Agent response
{response}
"""


class JudgeVerdict(BaseModel):
    score: float = Field(ge=0.0, le=1.0, description="Score from 0.0 to 1.0")
    reason: str = Field(description="Short explanation for the score")


def _llm_judge(response: str, rubric: str, context: str) -> CriterionResult:
    """Call an LLM to score the response against a rubric using structured outputs."""
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    prompt = LLM_JUDGE_PROMPT.format(rubric=rubric, context=context, response=response)

    result = client.responses.parse(
        model="gpt-4o-mini",
        input=[{"role": "user", "content": prompt}],
        text_format=JudgeVerdict,
        temperature=0,
    )

    verdict = result.output_parsed

    return CriterionResult(
        field="response_quality",
        method=ScoringMethod.LLM_JUDGE,
        score=verdict.score,
        reason=verdict.reason,
    )


def score_criterion(
    criterion: ScoringCriteria,
    agent_response: str,
    tools_called: list[str],
    user_message: str,
) -> CriterionResult:
    """Score a single criterion against agent output."""

    if criterion.method == ScoringMethod.EXACT_MATCH:
        target = criterion.expected or ""
        if criterion.field == "tools_called":
            match = target in tools_called
        else:
            match = target == agent_response
        return CriterionResult(
            field=criterion.field,
            method=criterion.method,
            score=1.0 if match else 0.0,
            reason=f"exact_match {'hit' if match else 'miss'}: expected={target!r}",
        )

    if criterion.method == ScoringMethod.CONTAINS:
        target = criterion.expected or ""
        if criterion.field == "tools_called":
            found = target in tools_called
        else:
            found = target.lower() in agent_response.lower()
        return CriterionResult(
            field=criterion.field,
            method=criterion.method,
            score=1.0 if found else 0.0,
            reason=f"contains {'hit' if found else 'miss'}: looking for {target!r}",
        )

    if criterion.method == ScoringMethod.LLM_JUDGE:
        return _llm_judge(
            response=agent_response,
            rubric=criterion.rubric or "Rate overall quality.",
            context=f"User message: {user_message}",
        )

    return CriterionResult(
        field=criterion.field,
        method=criterion.method,
        score=0.0,
        reason=f"Unknown scoring method: {criterion.method}",
    )
