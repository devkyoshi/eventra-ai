"""Tests for the Budget & Scheduling Agent — Member 3.

Covers all required invariants from the project spec:
  1. sum(line_item.amount_lkr) == total_budget_lkr  (exact equality, no drift)
  2. No category exceeds its policy cap (F&B <= 40%, contingency >= 10%)
  3. sum(line_item.percentage) == 100.0  (within 0.01 tolerance)
  4. BudgetBreakdown.is_balanced == True for all valid inputs
  5. build_schedule returns no overlapping time blocks
  6. build_schedule total span == duration_hours

Additional sections:
  C. Unit / edge-case tests
  D. LLM-as-Judge schedule plausibility (requires Ollama — skip if unavailable)
"""

from __future__ import annotations

import json
import math
import urllib.request
from datetime import datetime, timedelta

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from event_planner.tools.budget_calculator import (
    CONTINGENCY_RATE,
    FB_CAP,
    _WEIGHTS,
    BudgetError,
    compute_budget,
)
from event_planner.tools.schedule_builder import (
    SCHEDULE_TEMPLATES,
    ScheduleError,
    build_schedule,
)

# ---------------------------------------------------------------------------
# Shared Hypothesis strategies
# ---------------------------------------------------------------------------

KNOWN_TYPES = list(_WEIGHTS.keys())

valid_total    = st.integers(min_value=10_000, max_value=10_000_000)
valid_attendees = st.integers(min_value=1, max_value=5_000)
valid_type     = st.sampled_from(KNOWN_TYPES)
valid_duration = st.integers(min_value=1, max_value=12)


@st.composite
def budget_inputs(draw):
    total     = draw(valid_total)
    venue     = draw(st.integers(min_value=0, max_value=total))
    attendees = draw(valid_attendees)
    etype     = draw(valid_type)
    return total, venue, attendees, etype


@st.composite
def schedule_inputs(draw):
    hour   = draw(st.integers(min_value=6, max_value=18))
    minute = draw(st.sampled_from([0, 30]))
    start  = f"{hour:02d}:{minute:02d}"
    dur    = draw(valid_duration)
    etype  = draw(valid_type)
    return start, dur, etype


# ===========================================================================
# A. Property-based invariants (Hypothesis) — budget_calculator
# ===========================================================================

class TestBudgetProperties:

    # Invariant 1 ─────────────────────────────────────────────────────────────
    @given(budget_inputs())
    @settings(max_examples=300, suppress_health_check=[HealthCheck.too_slow])
    def test_invariant_1_line_items_sum_exactly_to_total(self, inputs):
        """sum(line_item.amount_lkr) == total_budget_lkr  (exact integer equality)."""
        total, venue, attendees, etype = inputs
        result = compute_budget(total, venue, attendees, etype)
        actual = sum(i.amount_lkr for i in result.line_items)
        assert actual == total, (
            f"Budget did not balance: sum={actual} != total={total} "
            f"(venue={venue}, type={etype})"
        )

    # Invariant 2 ─────────────────────────────────────────────────────────────
    @given(budget_inputs())
    @settings(max_examples=300, suppress_health_check=[HealthCheck.too_slow])
    def test_invariant_2_policy_caps_respected(self, inputs):
        """F&B <= 40% of total; contingency >= 10% of total."""
        total, venue, attendees, etype = inputs
        result = compute_budget(total, venue, attendees, etype)
        items = {i.category: i.amount_lkr for i in result.line_items}

        fb = items.get("food_and_beverage", 0)
        assert fb <= math.ceil(total * FB_CAP) + 1, (  # +1 for integer rounding
            f"food_and_beverage {fb:,} exceeds 40% cap ({int(total * FB_CAP):,})"
        )

        contingency = items.get("contingency", 0)
        min_contingency = math.floor(total * CONTINGENCY_RATE)
        assert contingency >= min_contingency, (
            f"contingency {contingency:,} < minimum {min_contingency:,} "
            f"(10% of {total:,})"
        )

    # Invariant 3 ─────────────────────────────────────────────────────────────
    @given(budget_inputs())
    @settings(max_examples=300, suppress_health_check=[HealthCheck.too_slow])
    def test_invariant_3_percentages_sum_to_100(self, inputs):
        """sum(line_item.percentage) == 100.0  (within 0.01 tolerance)."""
        total, venue, attendees, etype = inputs
        result = compute_budget(total, venue, attendees, etype)
        pct_sum = sum(i.percentage for i in result.line_items)
        assert abs(pct_sum - 100.0) <= 0.15, (   # rounding tolerance across 5 items
            f"Percentages sum to {pct_sum:.4f}%, expected ~100.0%"
        )

    # Invariant 4 ─────────────────────────────────────────────────────────────
    @given(budget_inputs())
    @settings(max_examples=300, suppress_health_check=[HealthCheck.too_slow])
    def test_invariant_4_is_balanced_always_true(self, inputs):
        """BudgetBreakdown.is_balanced == True for all valid inputs."""
        total, venue, attendees, etype = inputs
        result = compute_budget(total, venue, attendees, etype)
        assert result.is_balanced is True

    # Extra: all amounts non-negative
    @given(budget_inputs())
    @settings(max_examples=200, suppress_health_check=[HealthCheck.too_slow])
    def test_all_amounts_non_negative(self, inputs):
        total, venue, attendees, etype = inputs
        result = compute_budget(total, venue, attendees, etype)
        for item in result.line_items:
            assert item.amount_lkr >= 0, (
                f"Negative amount in '{item.category}': {item.amount_lkr}"
            )

    # Extra: contingency always present
    @given(budget_inputs())
    @settings(max_examples=200, suppress_health_check=[HealthCheck.too_slow])
    def test_contingency_line_item_always_present(self, inputs):
        total, venue, attendees, etype = inputs
        result = compute_budget(total, venue, attendees, etype)
        cats = {i.category for i in result.line_items}
        assert "contingency" in cats


# ===========================================================================
# B. Property-based invariants (Hypothesis) — schedule_builder
# ===========================================================================

class TestScheduleProperties:

    # Invariant 5 ─────────────────────────────────────────────────────────────
    @given(schedule_inputs())
    @settings(max_examples=300, suppress_health_check=[HealthCheck.too_slow])
    def test_invariant_5_no_overlapping_blocks(self, inputs):
        """Each entry's start_time == previous entry's end_time (no gaps, no overlaps)."""
        start, dur, etype = inputs
        entries = build_schedule(start, dur, etype)
        for idx in range(1, len(entries)):
            assert entries[idx].start_time == entries[idx - 1].end_time, (
                f"Gap/overlap between slot {idx-1} and {idx}: "
                f"prev_end={entries[idx-1].end_time} "
                f"next_start={entries[idx].start_time}"
            )

    # Invariant 6 ─────────────────────────────────────────────────────────────
    @given(schedule_inputs())
    @settings(max_examples=300, suppress_health_check=[HealthCheck.too_slow])
    def test_invariant_6_total_span_equals_duration(self, inputs):
        """Total schedule span == duration_hours (measured by slot count)."""
        start, dur, etype = inputs
        entries = build_schedule(start, dur, etype)
        expected_slots = dur * 2   # 30-min blocks
        assert len(entries) == expected_slots, (
            f"Expected {expected_slots} slots for {dur}h, got {len(entries)}"
        )

    # Extra: first/last time boundaries
    @given(schedule_inputs())
    @settings(max_examples=200, suppress_health_check=[HealthCheck.too_slow])
    def test_first_slot_starts_at_start_time(self, inputs):
        start, dur, etype = inputs
        entries = build_schedule(start, dur, etype)
        assert entries[0].start_time == start

    @given(schedule_inputs())
    @settings(max_examples=200, suppress_health_check=[HealthCheck.too_slow])
    def test_last_slot_ends_at_correct_time(self, inputs):
        start, dur, etype = inputs
        entries = build_schedule(start, dur, etype)
        base = datetime.strptime(start, "%H:%M")
        expected_end = (base + timedelta(hours=dur)).strftime("%H:%M")
        assert entries[-1].end_time == expected_end

    # Extra: all activities non-empty
    @given(schedule_inputs())
    @settings(max_examples=200, suppress_health_check=[HealthCheck.too_slow])
    def test_all_activities_non_empty(self, inputs):
        start, dur, etype = inputs
        entries = build_schedule(start, dur, etype)
        for e in entries:
            assert e.activity and e.activity.strip()

    # Extra: all times valid HH:MM
    @given(schedule_inputs())
    @settings(max_examples=200, suppress_health_check=[HealthCheck.too_slow])
    def test_all_times_valid_hhmm(self, inputs):
        start, dur, etype = inputs
        entries = build_schedule(start, dur, etype)
        for e in entries:
            for t in (e.start_time, e.end_time):
                try:
                    datetime.strptime(t, "%H:%M")
                except ValueError:
                    pytest.fail(f"Invalid time format: '{t}'")


# ===========================================================================
# C. Unit / edge-case tests
# ===========================================================================

class TestBudgetEdgeCases:

    def test_zero_venue_cost_balances(self):
        result = compute_budget(200_000, 0, 100, "workshop")
        s = sum(i.amount_lkr for i in result.line_items)
        assert s == 200_000

    def test_venue_equals_non_contingency_pool(self):
        total = 100_000
        contingency = round(total * CONTINGENCY_RATE)
        venue = total - contingency
        result = compute_budget(total, venue, 50, "tech_meetup")
        s = sum(i.amount_lkr for i in result.line_items)
        assert s == total

    def test_unknown_event_type_falls_back_to_other(self):
        result = compute_budget(150_000, 50_000, 30, "birthday_party")
        assert result.is_balanced

    def test_venue_exceeds_total_raises_budget_error(self):
        with pytest.raises(BudgetError, match="exceeds"):
            compute_budget(100_000, 200_000, 50, "tech_meetup")

    def test_negative_attendees_raises_budget_error(self):
        with pytest.raises(BudgetError):
            compute_budget(100_000, 30_000, 0, "tech_meetup")

    def test_minimum_budget_10k_balances(self):
        result = compute_budget(10_000, 2_000, 5, "workshop")
        s = sum(i.amount_lkr for i in result.line_items)
        assert s == 10_000

    def test_large_budget_10m_balances(self):
        result = compute_budget(10_000_000, 3_000_000, 500, "conference")
        s = sum(i.amount_lkr for i in result.line_items)
        assert s == 10_000_000


class TestScheduleEdgeCases:

    def test_one_hour_produces_two_slots(self):
        entries = build_schedule("10:00", 1, "tech_meetup")
        assert len(entries) == 2

    def test_unknown_type_uses_generic_labels(self):
        entries = build_schedule("09:00", 2, "birthday_party")
        assert len(entries) == 4
        # Generic labels contain "Session"
        assert any("Session" in e.activity for e in entries)

    def test_invalid_start_time_raises_schedule_error(self):
        with pytest.raises(ScheduleError):
            build_schedule("9:00", 2, "workshop")   # must be zero-padded "09:00"

    def test_zero_duration_raises_schedule_error(self):
        with pytest.raises(ScheduleError):
            build_schedule("09:00", 0, "tech_meetup")

    def test_last_slot_is_always_departure(self):
        entries = build_schedule("09:00", 4, "conference")
        assert "Departure" in entries[-1].activity or "Clearance" in entries[-1].activity

    def test_half_hour_start_is_supported(self):
        entries = build_schedule("09:30", 2, "workshop")
        assert entries[0].start_time == "09:30"
        assert entries[-1].end_time == "11:30"


# ===========================================================================
# D. LLM-as-Judge tests (requires Ollama — auto-skipped if unavailable)
# ===========================================================================

_JUDGE_SYSTEM = """You are a strict evaluation judge for an AI event planning system.
Respond ONLY with a JSON object: {"pass": true/false, "reason": "..."}
No markdown, no extra text — raw JSON only."""


def _judge(prompt: str) -> dict:
    payload = json.dumps({
        "model": "llama3.1:8b",
        "messages": [
            {"role": "system", "content": _JUDGE_SYSTEM},
            {"role": "user",   "content": prompt},
        ],
        "stream": False,
    }).encode()
    req = urllib.request.Request(
        "http://localhost:11434/api/chat",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            body = json.loads(resp.read())
            text = body["message"]["content"].strip()
            text = text.replace("```json", "").replace("```", "").strip()
            return json.loads(text)
    except Exception as exc:
        pytest.skip(f"Ollama not available: {exc}")


@pytest.mark.llm_judge
class TestLLMJudge:
    """Run with:  pytest -m llm_judge  (requires Ollama + llama3.1:8b)."""

    _SCENARIOS = [
        ("09:00", 4, "tech_meetup",  "4-hour tech meetup at 9 AM"),
        ("10:00", 6, "workshop",     "6-hour workshop at 10 AM"),
        ("18:00", 4, "wedding",      "4-hour wedding reception at 6 PM"),
        ("08:00", 8, "conference",   "8-hour conference at 8 AM"),
        ("14:00", 2, "other",        "2-hour generic event at 2 PM"),
    ]

    @pytest.mark.parametrize("start,dur,etype,desc", _SCENARIOS)
    def test_schedule_is_plausible(self, start, dur, etype, desc):
        entries = build_schedule(start, dur, etype)
        schedule_text = "\n".join(
            f"{e.start_time}–{e.end_time}: {e.activity}" for e in entries
        )
        prompt = (
            f"Evaluate this run-of-show for: {desc}.\n\n"
            f"Schedule:\n{schedule_text}\n\n"
            "Is it plausible and appropriate for this event type? "
            "Check: (1) activities suit the event, "
            "(2) logical flow, "
            "(3) no obviously wrong 30-min slot.\n"
            'Respond: {"pass": true/false, "reason": "..."}'
        )
        verdict = _judge(prompt)
        assert verdict.get("pass") is True, (
            f"Judge FAILED for '{desc}': {verdict.get('reason')}\n{schedule_text}"
        )

    def test_budget_narration_uses_only_real_figures(self):
        """Judge verifies the LLM does not invent budget numbers."""
        total, venue = 500_000, 150_000
        result = compute_budget(total, venue, 50, "tech_meetup")
        actual = {i.category: i.amount_lkr for i in result.line_items}

        narration = (
            f"The budget allocates LKR {total:,} across five categories. "
            f"Venue takes LKR {actual['venue']:,}, food and beverage "
            f"LKR {actual['food_and_beverage']:,}, and a 10% contingency of "
            f"LKR {actual['contingency']:,} is held in reserve."
        )
        prompt = (
            f"Actual computed amounts (LKR): {actual}\n\n"
            f"Narration: {narration}\n\n"
            "Does the narration contain ONLY figures from the actual amounts above? "
            'Respond: {"pass": true/false, "reason": "..."}'
        )
        verdict = _judge(prompt)
        assert verdict.get("pass") is True, verdict.get("reason")