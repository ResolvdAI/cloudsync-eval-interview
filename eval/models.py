"""
Pydantic models for eval cases and results.
"""

from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum


class ScoringMethod(str, Enum):
    EXACT_MATCH = "exact_match"
    CONTAINS = "contains"
    LLM_JUDGE = "llm_judge"


class ConversationMessage(BaseModel):
    """A single message in conversation history."""
    role: str = Field(description="'user' or 'assistant'")
    content: str


class ExpectedAction(BaseModel):
    """An expected tool call or behavior from the agent."""
    tool_name: Optional[str] = Field(None, description="Expected tool the agent should call")
    tool_args: Optional[dict] = Field(None, description="Expected arguments (partial match)")


class ScoringCriteria(BaseModel):
    """How to score one aspect of the agent's response."""
    field: str = Field(description="What to evaluate: 'response', 'tools_called', 'response_quality'")
    method: ScoringMethod
    expected: Optional[str] = Field(None, description="Expected value for exact_match/contains")
    rubric: Optional[str] = Field(None, description="Rubric for LLM judge scoring")
    weight: float = Field(1.0, description="Weight of this criterion in overall score")


class EvalCase(BaseModel):
    """A single evaluation case."""
    id: str
    description: str
    tags: list[str] = Field(default_factory=list)
    conversation_history: Optional[list[ConversationMessage]] = Field(
        None, description="Prior conversation context to seed the agent's memory before sending user_message"
    )
    user_message: str
    metadata: Optional[dict] = Field(None, description="customer_email, customer_id, etc.")
    expected_actions: list[ExpectedAction] = Field(default_factory=list)
    scoring: list[ScoringCriteria]


class EvalSuite(BaseModel):
    """A collection of eval cases."""
    name: str
    description: str
    cases: list[EvalCase]


class CriterionResult(BaseModel):
    """Result of scoring one criterion."""
    field: str
    method: ScoringMethod
    score: float = Field(ge=0.0, le=1.0)
    reason: str


class EvalCaseResult(BaseModel):
    """Result of running one eval case."""
    case_id: str
    agent_response: str
    tools_called: list[str]
    criterion_results: list[CriterionResult]
    weighted_score: float
    error: Optional[str] = None


class EvalRunResult(BaseModel):
    """Result of running an entire eval suite."""
    suite_name: str
    total_cases: int
    avg_score: float
    results: list[EvalCaseResult]
