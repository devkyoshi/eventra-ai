"""Thin wrapper around the Ollama Python client.

All agents import `get_llm_response` from here — never call ollama directly.
This centralises retry logic, JSON parsing, and model configuration.
"""

from __future__ import annotations

import json
import os
from typing import Union

import ollama


class LLMError(Exception):
    """Raised when the LLM call fails or returns unparseable JSON."""


def get_llm_response(
    system_prompt: str,
    user_prompt: str,
    *,
    model: str | None = None,
    json_mode: bool = True,
    temperature: float = 0.2,
) -> Union[dict, str]:
    """Call Ollama and return the model response.

    Args:
        system_prompt: The agent persona / constraint prompt.
        user_prompt: The per-call user message.
        model: Ollama model tag. Defaults to OLLAMA_MODEL env var or llama3.1:8b.
        json_mode: When True, instructs Ollama to emit valid JSON and parses the
            result into a dict. When False, returns the raw string content.
        temperature: Sampling temperature (0.0 – 1.0).

    Returns:
        Parsed dict when json_mode=True, raw string otherwise.

    Raises:
        LLMError: On Ollama connection failure, timeout, or invalid JSON when
            json_mode=True.
    """
    resolved_model = model or os.getenv("OLLAMA_MODEL", "llama3.1:8b")
    host = os.getenv("OLLAMA_HOST", "http://localhost:11434")

    client = ollama.Client(host=host)

    options: dict = {"temperature": temperature}
    kwargs: dict = {
        "model": resolved_model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "options": options,
    }
    if json_mode:
        kwargs["format"] = "json"

    try:
        response = client.chat(**kwargs)
    except Exception as exc:
        raise LLMError(f"Ollama connection failed ({resolved_model}): {exc}") from exc

    content: str = response["message"]["content"]

    if not json_mode:
        return content

    try:
        return json.loads(content)
    except json.JSONDecodeError as exc:
        raise LLMError(
            f"Model returned invalid JSON. Model: {resolved_model}. "
            f"Raw response (first 300 chars): {content[:300]!r}"
        ) from exc
