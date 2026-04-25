"""LLM-as-Judge evaluation for the Budget & Scheduling Agent — Member 3.

Run with:
    python -m evals.eval_budget

Reference: PROJECT-BOOTSTRAP.md § 7.3 step 5
"""

# TODO: Member 3 — implement evaluation scenarios
# Key assertions for the judge:
#   (a) Schedule is chronologically valid
#   (b) Schedule is event-appropriate (e.g. wedding ≠ Q&A panel)
#   (c) LLM narration does not introduce any numbers not from budget_calculator

from __future__ import annotations

import sys

SCENARIOS: list[dict] = []


def main() -> None:
    if not SCENARIOS:
        print("eval_budget: no scenarios defined yet. Member 3: implement these.")
        sys.exit(0)

    print("eval_budget: not yet implemented.")


if __name__ == "__main__":
    main()
