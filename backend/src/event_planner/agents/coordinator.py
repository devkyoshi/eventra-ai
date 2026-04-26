"""Coordinator / Requirements Agent — Member 1.

Parses the user's natural-language event request into a validated
EventRequirements object and writes it to state.requirements.

If mandatory fields are missing or the request is implausible, writes
state.clarification_needed instead, and the pipeline stops.
"""

from __future__ import annotations

import event_planner.llm.client as llm_client
from event_planner.llm.client import LLMError
from event_planner.observability.tracer import get_tracer
from event_planner.prompts.coordinator_prompt import COORDINATOR_SYSTEM_PROMPT
from event_planner.state.event_state import EventState
from event_planner.tools.requirements_validator import validate_requirements


def coordinator_node(state: EventState) -> dict:
    """Parse and validate the user request into structured EventRequirements.

    Reads:
        state["user_request"]
        state["trace_id"]

    Writes (success path):
        state["requirements"]  — validated EventRequirements

    Writes (clarification path):
        state["clarification_needed"]  — list of specific questions for the user

    Args:
        state: Current EventState from the LangGraph runtime.

    Returns:
        Partial state dict with either "requirements" or "clarification_needed".
    """
    tracer = get_tracer()
    user_request: str = state.get("user_request", "")  # type: ignore[assignment]

    tracer.log(
        agent="coordinator",
        event_type="agent_start",
        inputs={"user_request": user_request},
    )

    # Call the LLM to extract structured data from the natural-language request.
    try:
        raw: dict = llm_client.get_llm_response(
            COORDINATOR_SYSTEM_PROMPT,
            user_request,
            json_mode=True,
        )
    except LLMError as exc:
        tracer.log(agent="coordinator", event_type="error", error=str(exc))
        return {"clarification_needed": [f"LLM error: {exc}"]}

    tracer.log(
        agent="coordinator",
        event_type="tool_call",
        tool_called="get_llm_response",
        outputs={"raw_keys": list(raw.keys())},
    )

    # The LLM may signal that it needs more information from the user.
    if "clarification_needed" in raw:
        questions: list[str] = raw["clarification_needed"]
        tracer.log(
            agent="coordinator",
            event_type="agent_end",
            outputs={"clarification_needed": questions},
        )
        return {"clarification_needed": questions}

    # Validate the extracted fields against the EventRequirements schema.
    result = validate_requirements(raw)

    tracer.log(
        agent="coordinator",
        event_type="tool_call",
        tool_called="validate_requirements",
        inputs={"raw": raw},
        outputs={"ok": result.ok, "errors": result.errors},
    )

    if not result.ok:
        tracer.log(
            agent="coordinator",
            event_type="agent_end",
            outputs={"clarification_needed": result.errors},
        )
        return {"clarification_needed": result.errors}

    tracer.log(
        agent="coordinator",
        event_type="agent_end",
        outputs={"requirements": raw},
    )
    return {"requirements": result.data}
