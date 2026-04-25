"""Shared LLM-as-Judge harness — Group.

Used by all four eval_*.py scripts. Calls the local Ollama model to score
a candidate output against a rubric and returns a structured result.

Usage:
    from evals.llm_judge import judge

    result = judge(
        rubric="The output must contain a valid date and venue name.",
        candidate_output="The event is on May 15 at TRACE Expert City Hall.",
    )
    assert result.passed
    print(result.score, result.reasoning)
"""

from __future__ import annotations

import os
from dataclasses import dataclass

from event_planner.llm.client import LLMError, get_llm_response

_JUDGE_SYSTEM_PROMPT = """\
You are an impartial evaluator assessing AI-generated event planning outputs.

You will be given a RUBRIC describing what a good output should contain or avoid,
and a CANDIDATE OUTPUT to evaluate.

Respond with a JSON object containing exactly these three keys:
  "passed":    boolean — true if the output satisfies the rubric, false otherwise
  "score":     integer from 0 to 10 — overall quality score
  "reasoning": string — 1-3 sentences explaining your verdict

Be strict but fair. Do not award partial credit for outputs that violate hard constraints.
"""


@dataclass
class JudgeResult:
    passed: bool
    score: int
    reasoning: str


def judge(
    rubric: str,
    candidate_output: str,
    *,
    judge_model: str | None = None,
) -> JudgeResult:
    """Evaluate a candidate output against a rubric using the LLM as judge.

    Args:
        rubric: Plain-English description of what the output must satisfy.
        candidate_output: The text to evaluate.
        judge_model: Ollama model to use as judge. Defaults to OLLAMA_MODEL
            env var or llama3.1:8b.

    Returns:
        JudgeResult with passed, score (0-10), and reasoning.

    Raises:
        LLMError: If the Ollama call fails or returns invalid JSON.
    """
    model = judge_model or os.getenv("OLLAMA_MODEL", "llama3.1:8b")

    user_prompt = (
        f"RUBRIC:\n{rubric}\n\n"
        f"CANDIDATE OUTPUT:\n{candidate_output}\n\n"
        "Evaluate the candidate output against the rubric and respond with JSON."
    )

    raw: dict = get_llm_response(  # type: ignore[assignment]
        system_prompt=_JUDGE_SYSTEM_PROMPT,
        user_prompt=user_prompt,
        model=model,
        json_mode=True,
        temperature=0.0,
    )

    try:
        return JudgeResult(
            passed=bool(raw["passed"]),
            score=int(raw["score"]),
            reasoning=str(raw["reasoning"]),
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise LLMError(
            f"Judge returned unexpected JSON structure: {raw!r}"
        ) from exc
