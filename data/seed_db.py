"""One-shot script to create and seed the venues SQLite database.

Usage:
    python data/seed_db.py

Creates data/venues.db from data/venues.sql. Safe to re-run — drops and
recreates the venues table each time so the seed is idempotent.
"""

import sqlite3
import sys
from pathlib import Path


def seed(db_path: Path, sql_path: Path) -> int:
    """Create venues.db from venues.sql and return the row count inserted."""
    sql = sql_path.read_text(encoding="utf-8")

    conn = sqlite3.connect(db_path)
    try:
        conn.executescript("DROP TABLE IF EXISTS venues;")
        conn.executescript(sql)
        conn.commit()
        (count,) = conn.execute("SELECT COUNT(*) FROM venues").fetchone()
    finally:
        conn.close()

    return count


def main() -> None:
    repo_root = Path(__file__).parent.parent
    db_path = repo_root / "data" / "venues.db"
    sql_path = repo_root / "data" / "venues.sql"

    if not sql_path.exists():
        print(f"ERROR: venues.sql not found at {sql_path}", file=sys.stderr)
        sys.exit(1)

    count = seed(db_path, sql_path)
    print(f"venues.db created at {db_path} — {count} venues loaded.")


if __name__ == "__main__":
    main()
