# Eventra-AI

Eventra-AI is a local event-planning system with:

- a Python backend in [D:\assignment\eventra-ai\backend](D:\assignment\eventra-ai\backend)
- a React frontend in [D:\assignment\eventra-ai\frontend](D:\assignment\eventra-ai\frontend)

The backend is built around a LangGraph pipeline:

`Coordinator -> Venue -> Budget -> Communications`

Right now, the coordinator is implemented. The FastAPI server uses the real coordinator plus mock venue, budget, and communications data so the frontend can still show the full experience.

## Project Structure

```text
eventra-ai/
|- backend/   # Python backend, LangGraph flow, FastAPI server
`- frontend/  # React + Vite UI
```

## Backend Prerequisites

Before running the backend, make sure you have:

- Python 3.11 or newer
- [Ollama](https://ollama.com) installed
- the `llama3.1:8b` model pulled locally

## Backend Setup

From the repo root:

```powershell
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev]"
Copy-Item .env.example .env
python data\seed_db.py
```

If Ollama is not ready yet:

```powershell
ollama pull llama3.1:8b
```

The default backend config lives in [D:\assignment\eventra-ai\backend\.env](D:\assignment\eventra-ai\backend\.env).

## Recommended Startup Order

For this project, the smoothest order is:

1. Open the Ollama app first
2. Confirm the model can run in a terminal
3. Start the backend
4. Start the frontend

### Step 1: Open Ollama

Launch the Ollama desktop app and leave it running in the background.

### Step 2: Confirm Ollama can run the model

Open a new PowerShell terminal and run:

```powershell
ollama run llama3.1:8b
```

If the model starts and gives you an interactive prompt, Ollama is working.

If it fails, the backend will fail too, so fix Ollama first before starting FastAPI.

You can exit the interactive Ollama prompt with `Ctrl + C`.

### Step 3: Start the backend

In another terminal:

```powershell
cd D:\assignment\eventra-ai\backend
.venv\Scripts\activate
python -m uvicorn api:app --reload
```

### Step 4: Start the frontend

In another terminal:

```powershell
cd D:\assignment\eventra-ai\frontend
npm install
npm run dev
```

Then open the frontend URL shown by Vite, usually [http://127.0.0.1:5173](http://127.0.0.1:5173).

## How To Run The Backend

There are two useful ways to run it.

### 1. Run the LangGraph demo

Use this if you want to exercise the backend directly from the terminal:

```powershell
cd backend
.venv\Scripts\activate
python run_demo.py "Plan a 50-person tech meetup in Colombo on 2026-07-15 with a budget of LKR 250,000"
```

What this does:

- creates a trace in `backend\logs\`
- runs the graph from the command line
- prints the parsed result or clarification questions

Note: some downstream agents are still stubs, so `run_demo.py` can stop with `NotImplementedError` until the full pipeline is finished.

### 2. Run the FastAPI server

Use this if you want the frontend to talk to the backend:

```powershell
cd backend
.venv\Scripts\activate
python -m uvicorn api:app --reload
```

The API will start at:

- [http://127.0.0.1:8000](http://127.0.0.1:8000)
- health check: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)

Important:

- `POST /api/plan` uses the real coordinator agent
- venue, budget, schedule, and communications are currently mocked in `backend/api.py` so the frontend can render a complete response

## Run The Frontend With The Backend

Open two terminals.

Terminal 1:

```powershell
cd backend
.venv\Scripts\activate
python -m uvicorn api:app --reload
```

Terminal 2:

```powershell
cd frontend
npm install
npm run dev
```

Then open the Vite URL, usually:

- [http://127.0.0.1:5173](http://127.0.0.1:5173)

The Vite config already proxies `/api` requests to `http://localhost:8000`.

## Backend Tests

From `backend/`:

```powershell
.venv\Scripts\activate
pytest tests
```

Run one file:

```powershell
pytest tests\test_coordinator.py
```

## Backend Evaluation Commands

From `backend/`:

```powershell
python -m evals.eval_coordinator
python -m evals.eval_venue
python -m evals.eval_budget
python -m evals.eval_communications
```

## Useful Backend Files

- [D:\assignment\eventra-ai\backend\api.py](D:\assignment\eventra-ai\backend\api.py) - FastAPI server used by the frontend
- [D:\assignment\eventra-ai\backend\run_demo.py](D:\assignment\eventra-ai\backend\run_demo.py) - CLI demo runner
- [D:\assignment\eventra-ai\backend\PROJECT-BOOTSTRAP.md](D:\assignment\eventra-ai\backend\PROJECT-BOOTSTRAP.md) - implementation guide
- [D:\assignment\eventra-ai\backend\src\event_planner\graph.py](D:\assignment\eventra-ai\backend\src\event_planner\graph.py) - LangGraph wiring

## Troubleshooting

If the backend does not start:

1. Confirm Ollama is running locally.
2. Confirm `ollama run llama3.1:8b` works before starting the backend.
3. Confirm `ollama pull llama3.1:8b` completed successfully.
4. Confirm you are inside `backend/` before running `python -m uvicorn` or `python run_demo.py`.
5. Confirm the virtual environment is activated.
6. If `llama3.1:8b` crashes in Ollama, switch to `phi3:mini` in [D:\assignment\eventra-ai\backend\.env](D:\assignment\eventra-ai\backend\.env).
7. If the frontend cannot fetch data, check that the backend is running on port `8000`.
