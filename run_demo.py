"""Single-command end-to-end demo runner.

Usage:
    python run_demo.py "Plan a 50-person tech meetup in Colombo with LKR 200,000 on May 15, 2026"

Initialises the tracer, builds the LangGraph, runs the full pipeline,
prints a summary, and points the user at the generated output files.
"""

from __future__ import annotations

import sys
import uuid
from datetime import datetime

from dotenv import load_dotenv

load_dotenv()


def _banner(text: str, width: int = 60) -> None:
    print("\n" + "─" * width)
    print(f"  {text}")
    print("─" * width)


def main(user_request: str) -> int:
    """Run the full event planning pipeline and return an exit code."""

    _banner("AI Event Planner — Multi-Agent System")
    print(f"  Request : {user_request}")
    print(f"  Started : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # ── Tracer ────────────────────────────────────────────────────────────
    from event_planner.observability.tracer import get_tracer

    trace_id = uuid.uuid4().hex[:12]
    tracer = get_tracer()
    tracer.start_run(trace_id)
    print(f"  Trace ID: {trace_id}")

    # ── Build graph ────────────────────────────────────────────────────────
    try:
        from event_planner.graph import build_graph
        graph = build_graph()
    except Exception as exc:
        print(f"\n[ERROR] Failed to build graph: {exc}", file=sys.stderr)
        tracer.end_run()
        return 1

    # ── Run ────────────────────────────────────────────────────────────────
    initial_state = {
        "user_request": user_request,
        "trace_id": trace_id,
    }

    _banner("Running pipeline…")

    try:
        final_state = graph.invoke(initial_state)
    except NotImplementedError as exc:
        print(f"\n[NOT IMPLEMENTED] {exc}", file=sys.stderr)
        print(
            "\nThis agent has not been implemented yet.\n"
            "See PROJECT-BOOTSTRAP.md for the implementation guide.",
            file=sys.stderr,
        )
        tracer.end_run()
        return 2
    except Exception as exc:
        tracer.log(agent="graph", event_type="error", error=str(exc))
        print(f"\n[ERROR] Pipeline failed: {exc}", file=sys.stderr)
        summary = tracer.end_run()
        _print_summary(summary)
        return 1

    # ── Clarification needed ───────────────────────────────────────────────
    if final_state.get("clarification_needed"):
        _banner("Clarification needed")
        for question in final_state["clarification_needed"]:
            print(f"  • {question}")
        tracer.end_run()
        return 0

    # ── Success ────────────────────────────────────────────────────────────
    _banner("Pipeline complete")

    if final_state.get("requirements"):
        req = final_state["requirements"]
        print(f"  Event type : {req.event_type}")
        print(f"  Attendees  : {req.attendee_count}")
        print(f"  Location   : {req.location}")
        print(f"  Date       : {req.event_date.strftime('%Y-%m-%d')}")
        print(f"  Budget     : LKR {req.budget_lkr:,}")

    if final_state.get("chosen_venue"):
        v = final_state["chosen_venue"]
        print(f"\n  Chosen venue : {v.name} ({v.location})")
        print(f"  Venue cost   : LKR {v.price_per_day_lkr:,}/day")

    if final_state.get("output_files"):
        print("\n  Output files:")
        for path in final_state["output_files"]:
            print(f"    → {path}")

    summary = tracer.end_run()
    _print_summary(summary)
    return 0


def _print_summary(summary: dict) -> None:
    _banner("Run summary")
    print(f"  Trace ID    : {summary.get('trace_id')}")
    print(f"  Log file    : {summary.get('log_path')}")
    print(f"  Agent calls : {summary.get('agent_calls', 0)}")
    print(f"  Tool calls  : {summary.get('tool_calls', 0)}")
    print(f"  Total time  : {summary.get('total_time_ms', 0):,} ms")
    errors = summary.get("error_count", 0)
    status = "OK" if errors == 0 else f"{errors} error(s)"
    print(f"  Status      : {status}")
    print()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(
            "Usage: python run_demo.py \"<event request>\"\n"
            'Example: python run_demo.py "Plan a 50-person tech meetup in Colombo '
            'with LKR 200,000 on May 15, 2026"',
            file=sys.stderr,
        )
        sys.exit(1)

    request = sys.argv[1]
    sys.exit(main(request))
