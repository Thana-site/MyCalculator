import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import engine.history as history  # noqa: E402


@pytest.fixture(autouse=True)
def isolated_db(tmp_path, monkeypatch):
    """Every test gets its own throwaway SQLite file — never touches the
    real data/history.db, and tests never see each other's entries."""
    monkeypatch.setattr(history, "_DB_PATH", tmp_path / "test_history.db")
    yield


class TestHistory:
    def test_log_and_get_round_trip(self):
        history.log_entry("Calculator", "2+2", "4")
        entries = history.get_history()
        assert len(entries) == 1
        assert entries[0].mode == "Calculator"
        assert entries[0].input_text == "2+2"
        assert entries[0].result_text == "4"
        assert entries[0].created_at  # non-empty ISO timestamp

    def test_most_recent_first(self):
        history.log_entry("Calculator", "1+1", "2")
        history.log_entry("Calculator", "2+2", "4")
        history.log_entry("Calculator", "3+3", "6")
        entries = history.get_history()
        assert [e.input_text for e in entries] == ["3+3", "2+2", "1+1"]

    def test_limit(self):
        for i in range(5):
            history.log_entry("Calculator", str(i), str(i))
        entries = history.get_history(limit=2)
        assert len(entries) == 2
        assert entries[0].input_text == "4"
        assert entries[1].input_text == "3"

    def test_filter_by_mode(self):
        history.log_entry("Calculator", "2+2", "4")
        history.log_entry("Matrix", "[[1,2],[3,4]]", "det=-2")
        history.log_entry("Calculator", "3*3", "9")

        calc_only = history.get_history(mode="Calculator")
        assert len(calc_only) == 2
        assert all(e.mode == "Calculator" for e in calc_only)

        matrix_only = history.get_history(mode="Matrix")
        assert len(matrix_only) == 1
        assert matrix_only[0].input_text == "[[1,2],[3,4]]"

    def test_get_history_empty(self):
        assert history.get_history() == []

    def test_clear_all(self):
        history.log_entry("Calculator", "2+2", "4")
        history.log_entry("Matrix", "[[1,2],[3,4]]", "det=-2")
        deleted = history.clear_history()
        assert deleted == 2
        assert history.get_history() == []

    def test_clear_by_mode_only_removes_that_mode(self):
        history.log_entry("Calculator", "2+2", "4")
        history.log_entry("Matrix", "[[1,2],[3,4]]", "det=-2")
        deleted = history.clear_history(mode="Calculator")
        assert deleted == 1
        remaining = history.get_history()
        assert len(remaining) == 1
        assert remaining[0].mode == "Matrix"

    def test_db_file_created_on_first_use(self):
        assert not history._DB_PATH.exists()
        history.log_entry("Calculator", "2+2", "4")
        assert history._DB_PATH.exists()

    def test_persists_across_separate_connections(self):
        # Simulates separate Streamlit reruns / app restarts, since each
        # call opens and closes its own sqlite3 connection.
        history.log_entry("Calculator", "2+2", "4")
        entries_first_read = history.get_history()
        entries_second_read = history.get_history()
        assert entries_first_read == entries_second_read
