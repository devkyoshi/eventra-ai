"""Communications Agent — Member 4.

Drafts the invitation email, vendor brief, and full event plan, then
writes all three documents to disk. Also owns the observability layer.
"""

# TODO: Member 4 — implement this agent
# Reference: PROJECT-BOOTSTRAP.md § 7.4

from event_planner.state.event_state import EventState


def communications_node(state: EventState) -> EventState:
    """Draft event communications and write output files.

    Reads:
        state["requirements"]
        state["chosen_venue"]
        state["weather"]
        state["budget"]
        state["schedule"]

    Writes:
        state["communications"]  — Communications (invitation, vendor brief, plan)
        state["output_files"]    — list of absolute paths written to ./output/

    Args:
        state: Current EventState from the LangGraph runtime.

    Returns:
        Updated EventState with communications and output_files set.

    Raises:
        NotImplementedError: Until Member 4 implements this agent.
    """
    raise NotImplementedError(
        "communications_node is not yet implemented. "
        "Member 4: see PROJECT-BOOTSTRAP.md § 7.4 for the full implementation guide."
    )
