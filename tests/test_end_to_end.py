"""End-to-end pipeline smoke test — Group.

Runs the full LangGraph pipeline against a known-good prompt with a real
(or mocked) Ollama instance. Implement this once all four agents are wired.
Reference: PROJECT-BOOTSTRAP.md § 8
"""

# TODO: Group — implement after all four agents are complete (Day 5)
# Steps:
#   1. Ensure Ollama is running (skip with pytest.importorskip or a fixture).
#   2. Call build_graph() and invoke with a known-good user_request.
#   3. Assert final state contains: requirements, venue_options, chosen_venue,
#      weather, budget, schedule, communications, output_files.
#   4. Assert output files exist on disk.
#   5. Assert JSONL trace file exists and has >= 4 agent_start events.

import pytest


@pytest.mark.skip(reason="Group: implement end-to-end test once all agents are complete")
def test_end_to_end_placeholder() -> None:
    pass
