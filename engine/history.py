"""
History engine — persistent, cross-session log of past calculations.

Design notes:
    - SQLite (stdlib) chosen over a flat file/JSON so entries are queryable
      (filter by mode, ordered, limited) without loading the whole log into
      memory, and over adding a new third-party dependency for something
      this small.
    - Deliberately separate from calculator/solver/matrix/graph/integration:
      history is a cross-cutting concern (every mode writes to it), not a
      math operation itself, so it does not go through parser.py.
    - log_entry() is best-effort by design: a failure to write history must
      never prevent the user from seeing a calculation result they already
      got. Callers should wrap it in try/except and ignore failures (or log
      them) rather than surface them as a MathToolError.
"""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

_DB_PATH = Path(__file__).resolve().parent.parent / "data" / "history.db"

_SCHEMA = """
CREATE TABLE IF NOT EXISTS history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    mode TEXT NOT NULL,
    input_text TEXT NOT NULL,
    result_text TEXT NOT NULL,
    created_at TEXT NOT NULL
);
"""


@dataclass(frozen=True)
class HistoryEntry:
    id: int
    mode: str
    input_text: str
    result_text: str
    created_at: str  # ISO 8601, UTC


@contextmanager
def _connect():
    _DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(_DB_PATH)
    try:
        conn.execute(_SCHEMA)
        yield conn
        conn.commit()
    finally:
        conn.close()


def log_entry(mode: str, input_text: str, result_text: str) -> None:
    """Append one computation to history."""
    timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
    with _connect() as conn:
        conn.execute(
            "INSERT INTO history (mode, input_text, result_text, created_at) "
            "VALUES (?, ?, ?, ?)",
            (mode, input_text, result_text, timestamp),
        )


def get_history(limit: int = 50, mode: str | None = None) -> list[HistoryEntry]:
    """Most-recent-first list of history entries, optionally filtered by mode."""
    with _connect() as conn:
        if mode:
            cursor = conn.execute(
                "SELECT id, mode, input_text, result_text, created_at FROM history "
                "WHERE mode = ? ORDER BY id DESC LIMIT ?",
                (mode, limit),
            )
        else:
            cursor = conn.execute(
                "SELECT id, mode, input_text, result_text, created_at FROM history "
                "ORDER BY id DESC LIMIT ?",
                (limit,),
            )
        rows = cursor.fetchall()
    return [HistoryEntry(*row) for row in rows]


def clear_history(mode: str | None = None) -> int:
    """Delete history entries (all, or just one mode). Returns rows deleted."""
    with _connect() as conn:
        if mode:
            cursor = conn.execute("DELETE FROM history WHERE mode = ?", (mode,))
        else:
            cursor = conn.execute("DELETE FROM history")
        return cursor.rowcount
