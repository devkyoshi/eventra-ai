# AI Event Planning & Management System

A locally-hosted **Multi-Agent System (MAS)** that automates end-to-end event planning using [LangGraph](https://github.com/langchain-ai/langgraph) and [Ollama](https://ollama.com) (no cloud APIs, no API keys, no recurring cost).

Given a single natural-language request like:

> *"Plan a 50-person tech meetup in Colombo with a budget of LKR 200,000 on May 15th, 2026."*

The system autonomously produces ranked venue recommendations, an itemised budget, a run-of-show schedule, an attendee invitation email, and a vendor logistics brief — all written to local files.

---

## Architecture

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
│ 2. Venue Agent          │  SQLite DB + Open-Meteo weather → venue_options
└─────────────────────────┘
        │ state.venue_options, state.chosen_venue
        ▼
┌─────────────────────────┐
│ 3. Budget Agent         │  Deterministic budget calculator + schedule builder
└─────────────────────────┘
        │ state.budget, state.schedule
        ▼
┌─────────────────────────┐
│ 4. Communications Agent │  Drafts emails + writes plan to disk
└─────────────────────────┘
        │
        ▼
./output/<event_slug>_<timestamp>/
    ├── event_plan.md
    ├── invitation_email.md
    └── vendor_brief.md

./logs/run_<timestamp>.jsonl   ← full execution trace
```

See [docs/architecture.md](docs/architecture.md) for the full Mermaid diagram and state schema.

---

## System Requirements

| RAM | GPU | Notes |
|-----|-----|-------|
| 16 GB+ | Discrete 6 GB VRAM _or_ Apple Silicon M1/M2/M3 | Recommended — use `llama3.1:8b` |
| 8 GB | Any | Use `phi3:mini` fallback; will be slower |

Minimum free disk: ~20 GB (Ollama models).

---

## Prerequisites

- **Python 3.11+**
- **[Ollama](https://ollama.com)** installed and running

---

## Setup

### 1. Install Ollama and pull models

```bash
# Install from https://ollama.com, then:
ollama pull llama3.1:8b          # primary (~4.7 GB)
ollama pull phi3:mini             # fallback for low-RAM machines (~2.3 GB)
```

### 2. Clone the repository

```bash
git clone <repo-url>
cd ai-event-planner
```

### 3. Create a virtual environment and install dependencies

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

> **uv users:** `uv venv && uv pip install -e ".[dev]"`

### 4. Configure environment (optional)

```bash
cp .env.example .env
# Edit .env if Ollama runs on a non-default port, or to switch to phi3:mini
```

### 5. Seed the venue database (one-time)

```bash
python data/seed_db.py
# Creates data/venues.db with 25-30 realistic Colombo venues
```

---

## Running the Demo

```bash
python run_demo.py "Plan a 50-person tech meetup in Colombo with LKR 200,000 on May 15, 2026"
```

Output files are written to `./output/<slug>_<timestamp>/`. A full trace log is written to `./logs/`.

### Using a different model

```bash
OLLAMA_MODEL=phi3:mini python run_demo.py "..."
```

---

## Running Tests

```bash
pytest tests/                    # unit + integration tests
```

### Running Evaluations (LLM-as-Judge — slow)

```bash
python -m evals.eval_coordinator
python -m evals.eval_venue
python -m evals.eval_budget
python -m evals.eval_communications
```

---

## Project Structure

```
ai-event-planner/
├── src/event_planner/
│   ├── state/          # Shared EventState contract (Member 1)
│   ├── agents/         # One agent per member
│   ├── prompts/        # System prompts per agent
│   ├── tools/          # Deterministic tool functions
│   ├── observability/  # JSONL tracer (Member 4)
│   ├── llm/            # Ollama client wrapper
│   └── graph.py        # LangGraph wiring
├── data/               # venues.sql schema + seed_db.py
├── tests/              # pytest suite
├── evals/              # LLM-as-Judge evaluation scripts
├── docs/               # Architecture diagrams and report
├── run_demo.py         # Single-command demo runner
└── logs/ output/       # Runtime-generated (git-ignored)
```

---

## Member Responsibilities

| Member | Agent | Key Files |
|--------|-------|-----------|
| 1 (you) | Coordinator / Requirements | `agents/coordinator.py`, `tools/requirements_validator.py`, `state/event_state.py` |
| 2 | Venue & Logistics | `agents/venue.py`, `tools/venue_lookup.py`, `tools/weather_check.py`, `data/` |
| 3 | Budget & Scheduling | `agents/budget.py`, `tools/budget_calculator.py`, `tools/schedule_builder.py` |
| 4 | Communications + Observability | `agents/communications.py`, `tools/report_writer.py`, `observability/tracer.py` |

---

## Hard Rules (non-negotiable)

1. The LLM **never does arithmetic** — all math goes through `budget_calculator.py`.
2. No agent invents data — venues from DB, weather from Open-Meteo, budget from calculator.
3. Full type hints everywhere; `mypy --strict` passes on `tools/`.
4. No `print()` in agent/tool code — use the tracer.
5. Tools raise specific exceptions, never return `None` for failure.
6. Budget line items sum **exactly** to total.
7. No budget figures in attendee-facing emails.
8. Every run produces a JSONL trace.
