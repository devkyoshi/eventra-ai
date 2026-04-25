# AI Event Planning & Management System (Multi-Agent)

> **Document purpose:** This is a complete bootstrap brief for Claude Code. It contains the full project context, architecture, contracts between components, directory structure, file-by-file responsibilities, and detailed per-member implementation guides. Claude Code should use this as the source of truth when scaffolding the project.

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Workflow](#2-workflow)
3. [Technology Stack](#3-technology-stack)
4. [Global State Contract](#4-global-state-contract-the-most-important-section)
5. [Directory Structure](#5-directory-structure)
6. [File-by-File Responsibilities](#6-file-by-file-responsibilities)
7. [Per-Member Implementation Guides](#7-per-member-implementation-guides) ← **detailed per-person sections**
8. [Group-Owned Deliverables](#8-group-owned-deliverables)
9. [Per-Member Build Order](#9-per-member-build-order-for-parallel-work)
10. [Setup Instructions](#10-setup-instructions-for-the-readme)
11. [Hard Rules for Implementation](#11-hard-rules-for-implementation)
12. [Demo Script](#12-demo-script-for-the-45-minute-video)
13. [Report Outline](#13-report-outline-48-pages)
14. [What Claude Code Should Do First](#14-what-claude-code-should-do-first)

---

## 1. Project Overview

A locally-hosted **Multi-Agent System (MAS)** that automates end-to-end event planning. The user provides a single natural-language request such as:

> *"Plan a 50-person tech meetup in Colombo with a budget of LKR 200,000 on May 15th, 2026."*

The system autonomously produces a complete, ready-to-send event package: ranked venue recommendations, an itemized budget, a chronological run-of-show, an attendee-facing invitation email, and a vendor-facing logistics brief — all written to local files. Every agent action and tool call is captured in a structured trace log.

The system runs **entirely offline** on local hardware via Ollama. No cloud APIs, no API keys, no recurring cost.

### 1.1 What it is NOT

- Not a chatbot. There is no back-and-forth conversation loop in the core flow.
- Not a wrapper around a single LLM call. It is a pipeline of four specialised agents.
- Not dependent on any paid API (OpenAI, Anthropic Claude API, etc. are explicitly prohibited by the assignment).

### 1.2 What it IS

- A **directed graph of four agents** orchestrated by LangGraph.
- A system where the **LLM does reasoning and narration**, but **deterministic Python tools do anything that must be correct** (arithmetic, validation, file I/O, DB queries, API calls).
- A **typed, observable, testable** application with property-based tests and an LLM-as-Judge evaluation harness.

---

## 2. Workflow

```
User Request (natural language)
        │
        ▼
┌─────────────────────────┐
│ 1. Coordinator Agent    │  Parses request → validated EventRequirements
└─────────────────────────┘
        │ state.requirements
        ▼
┌─────────────────────────┐
│ 2. Venue Agent          │  Searches DB + checks weather → venue_options
└─────────────────────────┘
        │ state.venue_options, state.chosen_venue
        ▼
┌─────────────────────────┐
│ 3. Budget Agent         │  Computes budget + builds schedule
└─────────────────────────┘
        │ state.budget, state.schedule
        ▼
┌─────────────────────────┐
│ 4. Communications Agent │  Drafts emails + writes plan to disk
└─────────────────────────┘
        │ state.communications, state.output_files
        ▼
Output: ./output/<event_slug>_<timestamp>/
        ├── event_plan.md
        ├── invitation_email.md
        └── vendor_brief.md

+ ./logs/run_<timestamp>.jsonl  (full execution trace)
```

---

## 3. Technology Stack

| Layer            | Choice                                  | Notes                                         |
| ---------------- | --------------------------------------- | --------------------------------------------- |
| Language         | Python 3.11+                            | Required for modern type hints                |
| LLM Engine       | Ollama (`llama3.1:8b` primary, `phi3:mini` fallback) | Local only                          |
| Orchestrator     | LangGraph                               | Explicit graph + typed state                  |
| LLM Client       | `ollama` Python package                 | Use `format="json"` for structured outputs    |
| Validation       | Pydantic v2                             | Schemas for tool I/O and state shape          |
| Storage          | SQLite (`sqlite3` stdlib)               | Local venue database                          |
| External API     | Open-Meteo (`https://api.open-meteo.com`) | Free, no key, weather forecasts             |
| HTTP             | `httpx`                                 | For Open-Meteo calls                          |
| Testing          | `pytest` + `hypothesis`                 | Property-based tests                          |
| Logging          | stdlib `logging` + custom JSONL tracer  | Required for observability rubric             |
| Package Manager  | `uv` (preferred) or `pip` + venv        | Pin versions in `pyproject.toml`              |

### 3.1 System Requirements

- **Minimum:** 16 GB RAM, modern CPU, ~20 GB free disk.
- **Comfortable:** 16 GB RAM + a discrete GPU with 6+ GB VRAM, OR an Apple Silicon Mac (M1/M2/M3 with 16 GB unified memory).
- **8 GB RAM machines:** workable only with `phi3:mini`. Will struggle during the demo recording.
- **Designate one teammate's strong machine as the demo recording machine** to keep the 4–5 minute video crisp.

---

## 4. Global State Contract (THE Most Important Section)

Every agent reads from and writes to a single shared `EventState` object. This is a `TypedDict` so LangGraph can manage merge semantics natively.

```python
# state/event_state.py
from typing import TypedDict, Optional
from datetime import datetime
from pydantic import BaseModel

# --- Pydantic models referenced by EventState ---

class EventRequirements(BaseModel):
    event_type: str                    # "tech_meetup", "wedding", "workshop", "conference"
    attendee_count: int
    location: str                      # city/area, e.g. "Colombo"
    budget_lkr: int
    event_date: datetime               # required, future date
    duration_hours: int
    special_requirements: list[str]    # ["projector", "outdoor", "vegetarian"]

class Venue(BaseModel):
    id: int
    name: str
    capacity_min: int
    capacity_max: int
    price_per_day_lkr: int
    amenities: list[str]
    location: str
    description: str
    fit_score: float                   # 0.0 - 1.0, set by venue_lookup
    source: str                        # "venue_db" — proves no hallucination

class WeatherInfo(BaseModel):
    date: str
    temperature_c: float
    precipitation_probability: int     # 0-100
    conditions: str
    is_outdoor_friendly: bool

class VenueRecommendation(BaseModel):
    venue: Venue
    rank: int                          # 1, 2, 3
    pros: list[str]
    cons: list[str]
    weather_advisory: str

class BudgetLineItem(BaseModel):
    category: str                      # "venue", "food_and_beverage", "av_equipment", "decor", "contingency"
    amount_lkr: int
    percentage: float
    notes: str

class BudgetBreakdown(BaseModel):
    total_budget_lkr: int
    line_items: list[BudgetLineItem]
    is_balanced: bool                  # True iff sum(line_items) == total_budget_lkr

class ScheduleEntry(BaseModel):
    start_time: str                    # "HH:MM"
    end_time: str                      # "HH:MM"
    activity: str
    notes: Optional[str] = None

class Communications(BaseModel):
    invitation_email: str              # markdown
    vendor_brief: str                  # markdown
    final_plan: str                    # markdown — the full consolidated document

# --- The shared state ---

class EventState(TypedDict, total=False):
    # Input
    user_request: str
    trace_id: str

    # Agent 1 (Coordinator) writes:
    requirements: EventRequirements
    clarification_needed: Optional[list[str]]   # if not None, the agent could not proceed

    # Agent 2 (Venue) writes:
    venue_options: list[VenueRecommendation]
    chosen_venue: Venue                          # always venue_options[0]
    weather: WeatherInfo

    # Agent 3 (Budget) writes:
    budget: BudgetBreakdown
    schedule: list[ScheduleEntry]

    # Agent 4 (Communications) writes:
    communications: Communications
    output_files: list[str]                      # absolute paths
```

**Rules of the contract:**

1. Each agent **only writes the keys assigned to it**. It may read any prior key.
2. If a key required by a downstream agent is missing, the downstream agent must **fail loudly** with a clear error, not invent values.
3. The `trace_id` is set once at graph start and propagated through every log line.

---

## 5. Directory Structure

```
ai-event-planner/
├── README.md                              # Setup + run instructions
├── pyproject.toml                         # Pinned deps, project metadata
├── .gitignore                             # Excludes /logs, /output, *.db, .venv
├── .env.example                           # OLLAMA_HOST, OLLAMA_MODEL
│
├── docs/
│   ├── architecture.md                    # Mermaid diagrams, state schema docs
│   ├── REPORT.md                          # The 4-8 page technical report
│   └── images/                            # Diagram exports for the report
│
├── data/
│   ├── venues.sql                         # Schema + seed data for SQLite
│   ├── seed_db.py                         # One-shot script: builds venues.db
│   └── venues.db                          # GIT-IGNORED — generated locally
│
├── src/
│   └── event_planner/
│       ├── __init__.py
│       │
│       ├── state/
│       │   ├── __init__.py
│       │   └── event_state.py             # MEMBER 1 OWNS — shared state contract
│       │
│       ├── agents/
│       │   ├── __init__.py
│       │   ├── coordinator.py             # MEMBER 1 OWNS — Coordinator Agent
│       │   ├── venue.py                   # MEMBER 2 OWNS — Venue & Logistics Agent
│       │   ├── budget.py                  # MEMBER 3 OWNS — Budget & Scheduling Agent
│       │   └── communications.py          # MEMBER 4 OWNS — Communications Agent
│       │
│       ├── prompts/
│       │   ├── __init__.py
│       │   ├── coordinator_prompt.py      # MEMBER 1 — system prompt + few-shots
│       │   ├── venue_prompt.py            # MEMBER 2
│       │   ├── budget_prompt.py           # MEMBER 3
│       │   └── communications_prompt.py   # MEMBER 4
│       │
│       ├── tools/
│       │   ├── __init__.py
│       │   ├── requirements_validator.py  # MEMBER 1 — Pydantic + logical checks
│       │   ├── venue_lookup.py            # MEMBER 2 — SQLite venue search
│       │   ├── weather_check.py           # MEMBER 2 — Open-Meteo API
│       │   ├── budget_calculator.py       # MEMBER 3 — deterministic budget
│       │   ├── schedule_builder.py        # MEMBER 3 — run-of-show generator
│       │   └── report_writer.py           # MEMBER 4 — file output
│       │
│       ├── observability/
│       │   ├── __init__.py
│       │   └── tracer.py                  # MEMBER 4 OWNS — JSONL tracer singleton
│       │
│       ├── llm/
│       │   ├── __init__.py
│       │   └── client.py                  # GROUP — Ollama wrapper, JSON-mode helper
│       │
│       └── graph.py                       # GROUP — LangGraph wiring (all 4 nodes)
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py                        # GROUP — shared fixtures
│   ├── test_coordinator.py                # MEMBER 1
│   ├── test_venue.py                      # MEMBER 2
│   ├── test_budget.py                     # MEMBER 3
│   ├── test_communications.py             # MEMBER 4
│   └── test_end_to_end.py                 # GROUP — full pipeline smoke test
│
├── evals/
│   ├── __init__.py
│   ├── llm_judge.py                       # GROUP — shared LLM-as-Judge harness
│   ├── eval_coordinator.py                # MEMBER 1 — 15 ambiguous prompts
│   ├── eval_venue.py                      # MEMBER 2 — venue grounding checks
│   ├── eval_budget.py                     # MEMBER 3 — schedule plausibility
│   └── eval_communications.py             # MEMBER 4 — email professionalism + PII leak
│
├── run_demo.py                            # GROUP — single-command end-to-end runner
│
├── logs/                                  # GIT-IGNORED — JSONL traces per run
└── output/                                # GIT-IGNORED — generated event plans
```

---

## 6. File-by-File Responsibilities

### 6.1 `src/event_planner/state/event_state.py` — Member 1

Defines `EventState` (TypedDict) and all Pydantic models listed in section 4. This file is the contract; changes here require team review.

### 6.2 `src/event_planner/llm/client.py` — Group

Thin wrapper around the `ollama` Python client.

```python
def get_llm_response(
    system_prompt: str,
    user_prompt: str,
    *,
    model: str = "llama3.1:8b",
    json_mode: bool = True,
    temperature: float = 0.2,
) -> dict | str:
    """
    Calls Ollama. If json_mode=True, parses and returns dict.
    Raises LLMError on connection failure or invalid JSON when json_mode=True.
    """
```

Used by all four agents. Centralises retry, timeout, and JSON parsing.

### 6.3 Agents — One file per member

Each agent file follows the same pattern:

```python
def <agent_name>_node(state: EventState) -> EventState:
    """
    Reads required keys from state, calls LLM with system prompt, calls tools,
    writes assigned keys back into state, returns updated state.
    """
```

The agent function is what LangGraph calls as a node. Tools are imported from `event_planner.tools.*`. The system prompt is imported from `event_planner.prompts.*`.

### 6.4 Tools — Strict contracts

Every tool follows this template:

```python
def <tool_name>(<typed_args>) -> <typed_return>:
    """
    One-line summary.

    Args:
        ...

    Returns:
        ...

    Raises:
        <specific exceptions>
    """
```

Required for every tool: full type hints, comprehensive docstring, custom exception classes for each failure mode, no `print()` calls (use the tracer instead).

### 6.5 `src/event_planner/observability/tracer.py` — Member 4

Singleton tracer. API:

```python
class Tracer:
    def start_run(self, trace_id: str) -> None: ...
    def log(
        self,
        agent: str,
        event_type: str,        # "agent_start", "tool_call", "agent_end", "error"
        inputs: dict | None = None,
        outputs: dict | None = None,
        latency_ms: int | None = None,
        error: str | None = None,
    ) -> None: ...
    def end_run(self) -> dict: ...   # returns summary
```

Writes one JSON object per line to `./logs/run_<trace_id>.jsonl`. Every agent and every tool call goes through this.

### 6.6 `src/event_planner/graph.py` — Group

Builds the LangGraph `StateGraph(EventState)`:

```python
def build_graph():
    graph = StateGraph(EventState)
    graph.add_node("coordinator", coordinator_node)
    graph.add_node("venue", venue_node)
    graph.add_node("budget", budget_node)
    graph.add_node("communications", communications_node)
    graph.set_entry_point("coordinator")
    graph.add_edge("coordinator", "venue")
    graph.add_edge("venue", "budget")
    graph.add_edge("budget", "communications")
    graph.add_edge("communications", END)
    return graph.compile()
```

Optionally add a conditional edge: if `state.clarification_needed` is set after the coordinator, route to END instead of venue.

### 6.7 `run_demo.py` — Group

Single CLI entry point used in the demo video:

```bash
python run_demo.py "Plan a 50-person tech meetup in Colombo with LKR 200,000 on May 15, 2026"
```

Initialises tracer, builds graph, runs it, prints summary, points the user at output files.

### 6.8 `data/seed_db.py` — Member 2

One-shot script that creates `venues.db` from `venues.sql`. Run once on setup. README documents this.

`venues.sql` contains the schema and 25–30 INSERT statements for realistic Colombo venues.

### 6.9 Tests — One per member, plus group

`tests/conftest.py` provides shared fixtures:

```python
@pytest.fixture
def sample_state() -> EventState: ...

@pytest.fixture
def mock_llm(monkeypatch) -> Callable: ...

@pytest.fixture
def temp_output_dir(tmp_path) -> Path: ...
```

Each `test_<agent>.py` contains:

- Property-based tests using Hypothesis (Member's own tool)
- Unit tests for the agent's node function with mocked LLM
- Integration tests for tool error handling

### 6.10 Evals — One per member

LLM-as-Judge tests live separately from `pytest` because they are slow and non-deterministic. `evals/llm_judge.py` exposes:

```python
def judge(
    rubric: str,
    candidate_output: str,
    *,
    judge_model: str = "llama3.1:8b",
) -> JudgeResult:  # {pass: bool, score: int, reasoning: str}
```

Each `eval_<agent>.py` runs ~15 scripted scenarios and reports pass rate.

---

## 7. Per-Member Implementation Guides

This section is the detailed brief for each teammate. Each member should read **their own subsection in full** plus sections 4 (state contract), 9 (build order), and 11 (hard rules). When working with Claude Code on a feature branch, paste your member subsection into the prompt as context.

---

### 7.1 Member 1 — Coordinator / Requirements Agent

**Role summary:** The system's **front door**. Owns the agent that turns a vague human request into structured, validated data, and owns the **global state schema** that all four agents share.

**Files owned:**
- `src/event_planner/state/event_state.py`
- `src/event_planner/agents/coordinator.py`
- `src/event_planner/prompts/coordinator_prompt.py`
- `src/event_planner/tools/requirements_validator.py`
- `tests/test_coordinator.py`
- `evals/eval_coordinator.py`

**Libraries to use:** LangGraph, Pydantic v2, `ollama` (with `format="json"`), Hypothesis. A second Ollama call (same model, different system prompt) acts as the **judge** in the LLM-as-Judge evaluation.

**Step-by-step:**

1. **Define the global state schema** (`state/event_state.py`) — implement section 4 verbatim. This is the contract every other agent depends on; ship it on day 1 and freeze it.
2. **Design the agent system prompt** — persona is a meticulous event intake specialist. Constraints: outputs strict JSON matching `EventRequirements`; if any mandatory field is missing or implausible, returns a `clarification_needed` flag with specific questions instead of inventing values; never assumes defaults for budget, date, or attendee count. Include 2–3 few-shot examples in the prompt: one happy path, one ambiguous request that triggers clarification, one obviously invalid request that triggers refusal.
3. **Build `requirements_validator.py`** — exposes `validate_requirements(raw_extraction: dict) -> ValidationResult`. Uses Pydantic for type validation, then runs *logical* checks beyond types: budget-per-head sanity floor (e.g., a wedding for 200 people at LKR 50k total is logically impossible), date must be in the future, attendee count must be a positive integer, location must be a non-empty string. Returns `ValidationResult(ok: bool, data: EventRequirements | None, errors: list[ValidationError])`. Strict type hints, comprehensive docstrings, custom exception classes (`MissingFieldError`, `LogicalInconsistencyError`).
4. **Implement the coordinator agent node** — calls the LLM in JSON mode with the system prompt, passes the raw extraction to the validator tool, writes either `state.requirements` or `state.clarification_needed`.
5. **Wire the agent into the LangGraph graph** as the entry node (coordinate with the group on `graph.py`).
6. **Write the evaluation script:**
   - **Property-based** with Hypothesis: generate random valid `EventRequirements` dicts → assert validator round-trips them. Generate invalid ones → assert validator always rejects them, never silently passes.
   - **LLM-as-Judge:** 15 scripted prompts ranging from clear to deliberately ambiguous. Judge model scores each on (a) correct field extraction, (b) appropriate flagging of missing info, (c) absence of hallucinated values.

**Challenges to expect (good for the report):**
- SLMs love to invent dates when not given one. The prompt needs explicit "do not infer" instructions plus few-shot examples of the refusal pattern.
- JSON mode reliability with llama3.1 — use Ollama's `format="json"` parameter and validate the parsed output against Pydantic before trusting it.
- Pydantic `datetime` parsing — clearly document the accepted date string formats in the prompt.

**Final deliverable:** Working entry-point agent, the canonical state schema for the entire team, a robust validator tool, and a comprehensive test suite covering both.

---

### 7.2 Member 2 — Venue & Logistics Agent

**Role summary:** The **most tool-heavy agent**. Owns interaction with both a local database and a real public API — directly maximising the Tool Development & Integration mark.

**Files owned:**
- `src/event_planner/agents/venue.py`
- `src/event_planner/prompts/venue_prompt.py`
- `src/event_planner/tools/venue_lookup.py`
- `src/event_planner/tools/weather_check.py`
- `data/venues.sql`
- `data/seed_db.py`
- `tests/test_venue.py`
- `evals/eval_venue.py`

**Libraries to use:** LangGraph, `sqlite3` (stdlib) for the venue database, `httpx` for the Open-Meteo API, Pydantic for `Venue` and `WeatherInfo` models, Hypothesis for property-based tests.

**External API:** Open-Meteo (`https://api.open-meteo.com/v1/forecast`) — free, no key required, perfectly aligns with the "free public APIs" requirement.

**Step-by-step:**

1. **Seed the venue database** (`data/venues.sql`) — schema:
   ```sql
   CREATE TABLE venues (
     id INTEGER PRIMARY KEY,
     name TEXT NOT NULL,
     capacity_min INTEGER NOT NULL,
     capacity_max INTEGER NOT NULL,
     price_per_day_lkr INTEGER NOT NULL,
     amenities_json TEXT NOT NULL,        -- JSON array of strings
     location TEXT NOT NULL,
     description TEXT NOT NULL,
     latitude REAL NOT NULL,
     longitude REAL NOT NULL
   );
   ```
   Seed with 25–30 realistic Colombo venues — mix hotel ballrooms, co-working spaces, garden venues, beachside locations. Include realistic LKR pricing and capacity ranges. `seed_db.py` is a one-shot script that runs the SQL file against a fresh `venues.db`.
2. **Design the agent system prompt** — persona is a pragmatic logistics planner. Constraints: every recommended venue must include a `source` field referencing the tool result (no hallucinated venues); if no venues match, says so explicitly rather than relaxing constraints silently; output is a ranked list of 2–3 venues with score, pros, cons, and a weather advisory. Include a few-shot example showing the agent refusing to invent a venue.
3. **Build `venue_lookup.py`** — `search_venues(capacity: int, max_price_lkr: int, required_amenities: list[str], location: str) -> list[Venue]`. Connects to SQLite, filters by capacity range and budget, ranks by fit (amenity match + price headroom). Robust error handling: DB connection error, empty result set, malformed amenity JSON. Returns Pydantic `Venue` models with `source="venue_db"`.
4. **Build `weather_check.py`** — `get_weather_forecast(latitude: float, longitude: float, date: str) -> WeatherInfo`. Calls Open-Meteo, parses response into `WeatherInfo`, derives `is_outdoor_friendly` (true if precip probability < 30% and temp 20–32°C). Handle network errors with timeouts, dates beyond the ~16-day forecast window (graceful degradation: return `WeatherInfo` with `conditions="forecast_unavailable"`), invalid coordinates.
5. **Implement the venue agent node** — reads `state.requirements`, calls `venue_lookup` first, then `weather_check` for the chosen date and the top venue's coordinates, then synthesises the ranked recommendations via the LLM. Writes `state.venue_options`, `state.chosen_venue` (= `venue_options[0].venue`), `state.weather`.
6. **Write the evaluation script:**
   - **Property-based:** for 100 random valid requirement sets, assert every returned venue satisfies capacity AND budget constraints. This is the strongest Hypothesis test in the project.
   - **LLM-as-Judge:** assert the agent's final ranked output (a) only references venues that actually appear in the tool result, (b) the rationale matches the venue attributes, (c) no fabricated venue names appear.

**Challenges to expect:**
- SLMs occasionally invent venue names that "sound right." The constraint that every venue must cite a tool source is your defense — make this very explicit in the prompt with a refusal example.
- Open-Meteo only forecasts ~16 days ahead; design the graceful degradation path and document it.
- SQLite amenity matching: store amenities as a JSON array string and filter in Python rather than wrestling with SQL JSON operators.

**Final deliverable:** Seeded venue database, two robust real-world tools (one local, one network), the most demonstrable "agent uses tools to solve real problems" component in the system.

---

### 7.3 Member 3 — Budget & Scheduling Agent

**Role summary:** The **most rigorously testable agent**. Owns the deterministic numerical core of the system. Your report section gets to make a strong engineering point about why arithmetic should never be left to an LLM.

**Files owned:**
- `src/event_planner/agents/budget.py`
- `src/event_planner/prompts/budget_prompt.py`
- `src/event_planner/tools/budget_calculator.py`
- `src/event_planner/tools/schedule_builder.py`
- `tests/test_budget.py`
- `evals/eval_budget.py`

**Libraries to use:** LangGraph, Pydantic for `BudgetBreakdown`, `BudgetLineItem`, `ScheduleEntry`, Hypothesis (this is the agent where property-based tests shine brightest), stdlib `datetime` for schedule logic.

**Step-by-step:**

1. **Design the agent system prompt** — persona is a disciplined financial planner. Constraints: budget line items must sum to ≤ total budget (non-negotiable); schedule entries must be chronologically ordered and non-overlapping; all monetary values in LKR with explicit thousands formatting; flags if venue cost exceeds 60% of total budget. The LLM **only narrates** around tool outputs; it does not produce numbers itself.
2. **Build `budget_calculator.py`** — `compute_budget(total_budget_lkr: int, venue_cost: int, attendees: int, event_type: str) -> BudgetBreakdown`. Returns a structured breakdown: venue (fixed from input), F&B (per-head × attendees, capped at 40% of total), AV/equipment, decor, contingency (always ≥ 10% of total). Validates: line items sum **exactly** to total; no category exceeds its policy cap. Handles rounding remainders explicitly so `sum(line_items.amount_lkr) == total_budget_lkr` exactly. **This is the design decision worth highlighting in the report:** the LLM is bad at arithmetic, so a deterministic tool does the math and the LLM only narrates around it. This is realistic, professional engineering.
3. **Build `schedule_builder.py`** — `build_schedule(start_time: str, duration_hours: int, event_type: str) -> list[ScheduleEntry]`. Generates the run-of-show as 30-minute time blocks given the start time, duration, and event type. Pure-Python, deterministic. Different event types map to different default block patterns (e.g., a tech meetup has registration → talks → networking; a wedding has ceremony → reception → dancing).
4. **Implement the budget agent node** — reads `state.chosen_venue.price_per_day_lkr` and `state.requirements`, calls `budget_calculator` with the venue cost as a fixed input, calls `schedule_builder`, then has the LLM narrate (write a short rationale paragraph) but **not** modify any numbers. Writes `state.budget` and `state.schedule`.
5. **Write the evaluation script:**
   - **Property-based (strongest in the project):** for any random valid input, assert (a) line items sum exactly to total, (b) no category exceeds its policy cap, (c) percentages sum to 100% (within rounding tolerance), (d) contingency is always ≥ 10%.
   - **LLM-as-Judge:** assert the schedule is chronologically valid and event-appropriate (e.g., a wedding doesn't start with "Q&A panel").

**Challenges to expect:**
- The temptation to let the LLM "do" the budget — resist it. Tool does math, LLM explains.
- Rounding errors when splitting a budget proportionally — handle the rounding remainder explicitly (assign the remainder to one category, e.g., contingency, so totals match exactly).
- SLM hallucinating budget figures despite the prompt — the prompt must include an explicit rule "you must not output any numerical figure that is not from the budget_calculator tool result" with a refusal example.

**Final deliverable:** Deterministic budget engine, clean schedule builder, and the strongest property-based test suite in the project.

---

### 7.4 Member 4 — Communications Agent + Observability Owner

**Role summary:** Owns the **final user-visible output** plus the **cross-cutting logging layer** the entire team uses. Two distinct contributions — the second covers an entire rubric criterion (State Management & Observability, 10%) on top of your individual agent and tool marks.

**Files owned:**
- `src/event_planner/agents/communications.py`
- `src/event_planner/prompts/communications_prompt.py`
- `src/event_planner/tools/report_writer.py`
- `src/event_planner/observability/tracer.py`
- `tests/test_communications.py`
- `evals/eval_communications.py`

**Libraries to use:** LangGraph, stdlib `logging` + a custom JSONL tracer, `pathlib` for safe file operations, Pydantic for output models, Hypothesis for the file-output property tests.

**Step-by-step:**

1. **Design the agent system prompt** — persona is a professional event communications writer. Constraints: drafts are professional in tone, no emojis, no marketing-speak; **must not leak budget figures into attendee-facing communications** (only into vendor-facing ones); produces three distinct artifacts (invitation email, vendor brief, full consolidated event plan).
2. **Build `report_writer.py`** — `write_event_plan(state: EventState, output_dir: str) -> list[Path]`. Takes the full final state and writes three files to `./output/<event_slug>_<timestamp>/`:
   - `event_plan.md` — full consolidated plan (everything)
   - `invitation_email.md` — attendee-facing draft (no budget figures, no vendor details)
   - `vendor_brief.md` — vendor-facing brief (includes budget and logistics)
   Sanitises filenames (no spaces, no special chars), creates the directory if missing, handles permission errors, returns the list of written paths. Strict type hints, comprehensive docstrings, custom exception classes.
3. **Build the observability layer (`observability/tracer.py`)** — singleton tracer used by every agent and every tool. Records JSON-lines events: `{timestamp, run_id, agent, event_type, tool_called, inputs, outputs, latency_ms, error}` to `./logs/run_<timestamp>.jsonl`. Provides `start_run()`, `log()`, `end_run() -> summary` (number of agent calls, total tool invocations, total time, error count). The summary is printed at the end of `run_demo.py` and shown in the demo video.
4. **Wire the tracer into the LangGraph graph** — coordinate with the other three members so they import the tracer from a common module and call `tracer.log()` at the start and end of every agent node and around every tool call.
5. **Implement the communications agent node** — reads the full state, has the LLM draft each communication separately, validates no sensitive fields leaked into the wrong audience, calls `report_writer` to persist the files. Writes `state.communications` and `state.output_files`.
6. **Write the evaluation script:**
   - **Property-based:** output directory and all three files exist after every successful run; filenames have no forbidden characters; **vendor brief contains budget figures, invitation email does NOT** (this doubles as a security/info-leak test — call this out explicitly in the report).
   - **LLM-as-Judge:** assert the email is professional, on-topic, complete (date, venue, RSVP), and contains no leaked internal data.

**Challenges to expect:**
- Tracer thread-safety if you go async — start synchronous, document the limitation.
- SLMs leaking internal info into customer-facing emails is a real risk — the PII-leak property test is a genuine catch worth highlighting in the report.
- File path edge cases on Windows (drive letters, backslashes) — use `pathlib` exclusively, never string concatenation.

**Final deliverable:** Final user-facing output, robust file-writing tool, and the team-wide observability infrastructure that lights up the entire trace log.

---

## 8. Group-Owned Deliverables

These belong to the team collectively and don't fall under any one member:

- **`pyproject.toml`** — pinned versions of all dependencies.
- **`run_demo.py`** — single-command end-to-end runner used in the demo video.
- **Unified pytest harness** — shared `tests/conftest.py` with fixtures for the Ollama client, mock state, sample requirements, and temp output directories. Each member's `test_<their_agent>.py` lives alongside.
- **`tests/test_end_to_end.py`** — full pipeline smoke test that runs the whole graph against a known-good prompt.
- **`evals/llm_judge.py`** — shared LLM-as-Judge harness consumed by all four `eval_*.py` scripts.
- **`README.md`** — setup steps including Ollama install, model pulls, DB seed, and the run command.
- **`docs/architecture.md`** — Mermaid workflow diagram and state schema documentation for the report.
- **`src/event_planner/graph.py`** — LangGraph wiring that connects all four agents.
- **`src/event_planner/llm/client.py`** — shared Ollama client wrapper.
- **Demo video (4–5 min)** — each member records the segment covering their own agent.
- **Technical report (4–8 pages)** — each member writes their own section on their agent, tool, and challenges; group sections (problem domain, architecture, evaluation methodology) are co-authored.

---

## 9. Per-Member Build Order (for parallel work)

To avoid blocking each other:

**Day 1 (everyone):**
- Member 1 ships `state/event_state.py` and the `llm/client.py` skeleton.
- Members 2, 3, 4 review and approve the state contract. Once approved, the contract is frozen.

**Day 2–4 (parallel):**
- Member 1: Coordinator agent + validator tool + tests.
- Member 2: Seeds venue DB, builds both tools, builds agent, tests.
- Member 3: Budget calculator + schedule builder + agent + tests.
- Member 4: Tracer + report writer + agent skeleton (waits on others for full integration testing).

**Day 5:**
- Group: Wire `graph.py`. End-to-end smoke test. Member 4 finalises agent against real upstream output. Fix any contract violations surfaced by integration.

**Day 6:**
- Group: Polish, record demo, write report, push final repo.

---

## 10. Setup Instructions (for the README)

```bash
# 1. Install Ollama from https://ollama.com
ollama pull llama3.1:8b
ollama pull phi3:mini    # fallback for low-RAM machines

# 2. Clone and install
git clone <repo>
cd ai-event-planner
python -m venv .venv && source .venv/bin/activate
pip install -e .

# 3. Seed the venue database (one-time)
python data/seed_db.py

# 4. Run the demo
python run_demo.py "Plan a 50-person tech meetup in Colombo with LKR 200,000 on May 15, 2026"

# 5. Run tests
pytest tests/

# 6. Run evals (slower, hits the LLM)
python -m evals.eval_coordinator
python -m evals.eval_venue
python -m evals.eval_budget
python -m evals.eval_communications
```

---

## 11. Hard Rules for Implementation

These are non-negotiable engineering constraints. Claude Code must follow them.

1. **The LLM never does arithmetic.** All math goes through `budget_calculator.py` or `schedule_builder.py`. The LLM only narrates around tool outputs.
2. **No agent invents data.** Venues must come from `venue_lookup`. Weather must come from `weather_check`. Budget must come from `budget_calculator`. Every agent prompt enforces this with explicit constraints and at least one few-shot refusal example.
3. **Strict typing everywhere.** Every function signature has type hints. Every Pydantic model has explicit field types. `mypy --strict` should pass on the `tools/` directory at minimum.
4. **No `print()` in agent or tool code.** Use the tracer for events and `logging` for diagnostics.
5. **Tools raise specific exceptions.** Never return `None` to indicate failure. Each failure mode gets its own exception class.
6. **Filenames are sanitised.** `report_writer` strips spaces and special characters before writing.
7. **Budget always balances.** `budget_calculator` handles rounding remainders explicitly so `sum(line_items.amount_lkr) == total_budget_lkr` exactly.
8. **No PII in attendee comms.** The invitation email must not contain budget figures or vendor details. The vendor brief is the only place those appear. There is a property test for this.
9. **Every run produces a trace.** No exceptions. The tracer is initialised in `run_demo.py` before the graph runs.
10. **Ollama JSON mode is used wherever the LLM produces structured output.** Coordinator and Venue agents must use `format="json"`.

---

## 12. Demo Script (for the 4–5 minute video)

Suggested structure:

1. **0:00–0:30** — Show the user request being typed into `run_demo.py`. Brief intro of the system.
2. **0:30–1:00** — Show the Coordinator parsing the request. Display the validated `EventRequirements` JSON in the trace log. **(Member 1 narrates)**
3. **1:00–2:00** — Show the Venue Agent calling `venue_lookup` (DB hit) and `weather_check` (live Open-Meteo call). Display the ranked recommendations. **(Member 2 narrates)**
4. **2:00–3:00** — Show the Budget Agent's deterministic line items balancing exactly. Show the schedule. **(Member 3 narrates)**
5. **3:00–4:00** — Open the generated `event_plan.md`, `invitation_email.md`, `vendor_brief.md`. Show the JSONL trace summary printed at the end. **(Member 4 narrates)**
6. **4:00–4:30** — Quickly run `pytest` to show the test suite passing. End.

Each member records the segment showing their own agent so the contribution is visible.

---

## 13. Report Outline (4–8 pages)

1. **Problem domain** (0.5 pg) — Why event planning is a good MAS use case.
2. **System architecture** (1 pg) — Mermaid workflow diagram + state schema.
3. **Agent design** (1.5 pg) — Each member writes their own subsection: persona, system prompt, constraints, reasoning logic.
4. **Custom tools** (1.5 pg) — Each member writes their own subsection: API, example usage, error handling.
5. **State management** (0.5 pg) — TypedDict design, contract rules, why it preserves context.
6. **Observability** (0.5 pg) — Tracer architecture, sample trace excerpt, post-run summary.
7. **Evaluation methodology** (1 pg) — Property-based tests + LLM-as-Judge approach. Pass rates per agent.
8. **Individual contributions** (0.5 pg) — Per member: agent built, tool built, challenges faced.
9. **GitHub link** (1 line).

---

## 14. What Claude Code Should Do First

When a user says "scaffold this project," Claude Code should:

1. Create the directory tree exactly as in section 5.
2. Generate `pyproject.toml` with pinned versions of: `langgraph`, `ollama`, `pydantic>=2`, `httpx`, `pytest`, `hypothesis`, `python-dotenv`.
3. Implement `state/event_state.py` exactly as defined in section 4.
4. Implement `llm/client.py` with the signature in section 6.2.
5. Implement `observability/tracer.py` with the API in section 6.5.
6. Stub out all four agent files with the function signature in section 6.3 and a `# TODO: implement` body.
7. Stub out all six tool files with proper signatures and docstrings, raising `NotImplementedError`.
8. Implement `data/seed_db.py` and `data/venues.sql` with 25–30 realistic Colombo venues.
9. Write `tests/conftest.py` with the fixtures in section 6.9.
10. Implement `run_demo.py` with arg parsing, tracer setup, graph invocation, and summary printout.
11. Write a `README.md` based on section 10.

After scaffolding is complete, each member opens their assigned subsection of section 7 and implements their agent + tool + tests. The contracts in section 4 ensure they can work in parallel without stepping on each other.

---

**End of bootstrap document.**