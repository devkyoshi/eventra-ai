"""Coordinator / Requirements Agent — Member 1.

Parses the user's natural-language event request into a validated
EventRequirements object and writes it to state.requirements.

If mandatory fields are missing or the request is implausible, writes
state.clarification_needed instead, and the pipeline stops.
"""

# TODO: Member 1 — implement this agent
# Reference: PROJECT-BOOTSTRAP.md § 7.1

from event_planner.state.event_state import EventState


def coordinator_node(state: EventState) -> EventState:
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
        Updated EventState with requirements or clarification_needed set.

    Raises:
        NotImplementedError: Until Member 1 implements this agent.
    """
    raise NotImplementedError(
        "coordinator_node is not yet implemented. "
        "Member 1: see PROJECT-BOOTSTRAP.md § 7.1 for the full implementation guide."
    )
