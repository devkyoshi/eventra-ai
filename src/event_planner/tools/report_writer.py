"""Report writer tool — Member 4.

Writes the three event output documents to ./output/<slug>_<timestamp>/.
Uses pathlib exclusively — no string concatenation for paths.
"""

# TODO: Member 4 — implement this tool
# Reference: PROJECT-BOOTSTRAP.md § 7.4 step 2

from __future__ import annotations

from pathlib import Path


class ReportWriterError(Exception):
    """File system error while writing output documents."""


class SanitisationError(Exception):
    """Event slug contains characters that cannot be safely used in a path."""


def write_event_plan(
    state: dict,
    output_dir: str = "output",
) -> list[Path]:
    """Write the three event output files to a timestamped output directory.

    Creates ./output/<event_slug>_<timestamp>/ and writes:
      - event_plan.md       — full consolidated plan (all details)
      - invitation_email.md — attendee-facing (NO budget figures, NO vendor info)
      - vendor_brief.md     — vendor-facing (includes budget and logistics)

    The event_slug is derived from state["requirements"].event_type and
    state["requirements"].location, with spaces replaced by underscores and
    special characters stripped.

    Args:
        state: The final EventState dict (must contain "communications" and
            "requirements" keys).
        output_dir: Root directory for output. Defaults to "./output".

    Returns:
        List of Path objects for the three files written (absolute paths).

    Raises:
        ReportWriterError: On permission errors or other I/O failures.
        SanitisationError: If the derived slug is empty after sanitisation.
        NotImplementedError: Until Member 4 implements this tool.
    """
    raise NotImplementedError(
        "write_event_plan is not yet implemented. "
        "Member 4: see PROJECT-BOOTSTRAP.md § 7.4 step 2."
    )
