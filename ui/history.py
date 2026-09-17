import streamlit as st

from engine.history import get_history, clear_history
from ui import theme

_MODES = [
    "All", "Calculator", "Equation Solver", "Graph Plotter",
    "Area Under Curve", "Matrix",
]


def render() -> None:
    theme.page_header(
        "History",
        "History",
        "Persistent log of past calculations across every mode "
        "(stored locally in data/history.db, survives app restarts).",
    )

    with theme.card("history-card"):
        col1, col2 = st.columns([3, 1])
        mode_filter = col1.selectbox("Filter by mode", _MODES, key="history_filter")
        if col2.button("Clear", key="history_clear", width="stretch"):
            deleted = clear_history(None if mode_filter == "All" else mode_filter)
            st.success(f"Cleared {deleted} entr{'y' if deleted == 1 else 'ies'}.")

        entries = get_history(limit=100, mode=None if mode_filter == "All" else mode_filter)

        if not entries:
            theme.empty_note("No history yet — results from other pages will appear here.")
            return

        for entry in entries:
            theme.history_entry(
                f"{theme.esc(entry.mode)} · {theme.esc(entry.created_at.replace('T', ' '))}"
                f"<br>{theme.esc(entry.input_text)}",
                theme.esc(entry.result_text),
            )
