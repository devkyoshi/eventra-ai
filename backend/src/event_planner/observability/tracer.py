"""JSONL execution tracer — singleton used by every agent and tool.

Usage:
    from event_planner.observability.tracer import get_tracer

    tracer = get_tracer()
    tracer.start_run("run-abc123")
    tracer.log(agent="coordinator", event_type="agent_start")
    tracer.log(agent="coordinator", event_type="tool_call",
               tool_called="validate_requirements",
               inputs={"raw": {...}}, outputs={"ok": True}, latency_ms=42)
    summary = tracer.end_run()
"""

from __future__ import annotations

import json
import logging
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class Tracer:
    """Thread-safe JSONL tracer that writes one event per line to a log file.

    Note: synchronous and single-file-per-run. If you move to async, wrap
    writes in an asyncio.Lock instead of threading.Lock.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._trace_id: str | None = None
        self._log_path: Path | None = None
        self._fh: object | None = None  # open file handle during a run
        self._start_time_ns: int = 0
        self._agent_calls: int = 0
        self._tool_calls: int = 0
        self._error_count: int = 0

    def start_run(self, trace_id: str) -> None:
        """Open the JSONL log file and reset counters for a new run.

        Args:
            trace_id: Unique run identifier (typically a UUID or timestamp slug).
        """
        with self._lock:
            self._trace_id = trace_id
            log_dir = Path("logs")
            log_dir.mkdir(exist_ok=True)
            self._log_path = log_dir / f"run_{trace_id}.jsonl"
            self._fh = self._log_path.open("w", encoding="utf-8")
            self._start_time_ns = time.monotonic_ns()
            self._agent_calls = 0
            self._tool_calls = 0
            self._error_count = 0

    def log(
        self,
        agent: str,
        event_type: str,
        *,
        tool_called: Optional[str] = None,
        inputs: Optional[dict] = None,
        outputs: Optional[dict] = None,
        latency_ms: Optional[int] = None,
        error: Optional[str] = None,
    ) -> None:
        """Write a single event to the JSONL log.

        Args:
            agent: Agent name ("coordinator", "venue", "budget", "communications").
            event_type: One of "agent_start", "tool_call", "agent_end", "error".
            tool_called: Tool function name (only for event_type="tool_call").
            inputs: Tool or agent inputs (serialisable dict).
            outputs: Tool or agent outputs (serialisable dict).
            latency_ms: Wall-clock milliseconds for the operation.
            error: Error message string (only for event_type="error").
        """
        if self._fh is None:
            logger.warning("Tracer.log called before start_run — dropping event.")
            return

        entry: dict = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "run_id": self._trace_id,
            "agent": agent,
            "event_type": event_type,
            "tool_called": tool_called,
            "inputs": inputs,
            "outputs": outputs,
            "latency_ms": latency_ms,
            "error": error,
        }

        with self._lock:
            if event_type == "agent_start":
                self._agent_calls += 1
            elif event_type == "tool_call":
                self._tool_calls += 1
            elif event_type == "error":
                self._error_count += 1

            try:
                line = json.dumps(entry, default=str) + "\n"
                self._fh.write(line)  # type: ignore[union-attr]
                self._fh.flush()  # type: ignore[union-attr]
            except Exception as exc:
                logger.error("Failed to write trace event: %s", exc)

    def end_run(self) -> dict:
        """Close the log file and return a run summary dict.

        Returns:
            {
                "trace_id": str,
                "log_path": str,
                "agent_calls": int,
                "tool_calls": int,
                "total_time_ms": int,
                "error_count": int,
            }
        """
        with self._lock:
            elapsed_ms = (time.monotonic_ns() - self._start_time_ns) // 1_000_000
            summary = {
                "trace_id": self._trace_id,
                "log_path": str(self._log_path),
                "agent_calls": self._agent_calls,
                "tool_calls": self._tool_calls,
                "total_time_ms": elapsed_ms,
                "error_count": self._error_count,
            }
            if self._fh is not None:
                try:
                    self._fh.close()  # type: ignore[union-attr]
                except Exception:
                    pass
                self._fh = None
            return summary


# Module-level singleton — import get_tracer() rather than _tracer directly.
_tracer = Tracer()


def get_tracer() -> Tracer:
    """Return the process-wide singleton Tracer instance."""
    return _tracer
