"""LangGraph wiring — connects all four agent nodes into a compiled graph.

Build the graph once at startup and reuse the compiled object for all runs.
"""

from __future__ import annotations

from langgraph.graph import END, StateGraph

from event_planner.agents.budget import budget_node
from event_planner.agents.communications import communications_node
from event_planner.agents.coordinator import coordinator_node
from event_planner.agents.venue import venue_node
from event_planner.state.event_state import EventState


def _needs_clarification(state: EventState) -> str:
    """Route after coordinator: stop if clarification is required."""
    if state.get("clarification_needed"):
        return "end"
    return "venue"


def build_graph() -> object:
    """Build and compile the event-planning StateGraph.

    Returns:
        A compiled LangGraph runnable ready to invoke with an initial EventState.
    """
    graph: StateGraph = StateGraph(EventState)

    graph.add_node("coordinator", coordinator_node)
    graph.add_node("venue", venue_node)
    graph.add_node("budget", budget_node)
    graph.add_node("communications", communications_node)

    graph.set_entry_point("coordinator")

    graph.add_conditional_edges(
        "coordinator",
        _needs_clarification,
        {"end": END, "venue": "venue"},
    )
    graph.add_edge("venue", "budget")
    graph.add_edge("budget", "communications")
    graph.add_edge("communications", END)

    return graph.compile()
