"""LLM-as-Judge evaluation for the Coordinator Agent — Member 1.

Run with:
    python -m evals.eval_coordinator

Evaluates 15 scripted prompts ranging from clear to deliberately ambiguous.
Reference: PROJECT-BOOTSTRAP.md § 7.1 step 6
"""

# TODO: Member 1 — implement evaluation scenarios
# Each scenario should test one of:
#   (a) Correct field extraction from a clear request
#   (b) Appropriate clarification_needed flag on missing info
#   (c) Absence of hallucinated values (especially date/budget)
# Target: >= 12/15 pass rate

from __future__ import annotations

import sys

# Placeholder scenarios — replace with real ones
SCENARIOS: list[dict] = [
    # {"prompt": "...", "rubric": "..."},
]


def main() -> None:
    if not SCENARIOS:
        print("eval_coordinator: no scenarios defined yet. Member 1: implement these.")
        sys.exit(0)

    # TODO: Member 1 — loop over SCENARIOS, call coordinator_node, then judge()
    print("eval_coordinator: not yet implemented.")


if __name__ == "__main__":
    main()
