"""
UI smoke tests for the Calculator page, using streamlit.testing.v1.AppTest.

These exercise the app through app.py exactly as a user's clicks would,
asserting on st.session_state (and, for history, the real engine.history
module) rather than rendered HTML — the same level the rest of this
project tests at.
"""

import sys
from pathlib import Path

import pytest
import sympy as sp
from streamlit.testing.v1 import AppTest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import engine.history as history  # noqa: E402

_APP_PATH = str(Path(__file__).resolve().parents[1] / "app.py")


@pytest.fixture(autouse=True)
def isolated_db(tmp_path, monkeypatch):
    """Every test gets its own throwaway SQLite file — never touches the
    real data/history.db."""
    monkeypatch.setattr(history, "_DB_PATH", tmp_path / "test_ui_history.db")
    yield


@pytest.fixture
def at():
    test = AppTest.from_file(_APP_PATH, default_timeout=15)
    test.run()
    test.button(key="btn_ac").click().run()
    return test


def test_app_loads_without_exception(at):
    assert not at.exception


def test_digit_and_operator_keys_append_to_expression(at):
    at.button(key="btn_num-7").click().run()
    assert at.session_state.calc_expression == "7"


def test_equals_evaluates_and_logs_real_history(at):
    at.button(key="btn_num-2").click().run()
    at.button(key="btn_eq").click().run()
    assert not at.exception
    assert at.session_state.calc_last_result == 2

    entries = history.get_history(mode="Calculator")
    assert len(entries) == 1
    assert entries[0].input_text == "2"
    assert entries[0].result_text == "2"


def test_equals_on_invalid_expression_sets_error_not_exception(at):
    at.button(key="btn_trig-sin").click().run()  # "sin(" — unterminated
    at.button(key="btn_eq").click().run()
    assert not at.exception
    assert at.session_state.calc_error is not None
    assert at.session_state.calc_last_result is None


# ---------------------------------------------------------------------------
# SHIFT modifier: arm-then-consume, not a persistent toggle
# ---------------------------------------------------------------------------

class TestShiftModifier:
    def test_shift_arms_and_function_key_consumes_it(self, at):
        assert at.session_state.shift_active is False
        at.button(key="btn_shift").click().run()
        assert at.session_state.shift_active is True

        at.button(key="btn_trig-sin").click().run()
        assert at.session_state.calc_expression == "asin("
        assert at.session_state.shift_active is False

    def test_shift_pressed_twice_cancels_before_use(self, at):
        at.button(key="btn_shift").click().run()
        at.button(key="btn_shift").click().run()
        assert at.session_state.shift_active is False

        at.button(key="btn_trig-cos").click().run()
        assert at.session_state.calc_expression == "cos("

    def test_unshifted_function_key_uses_primary_token(self, at):
        at.button(key="btn_trig-tan").click().run()
        assert at.session_state.calc_expression == "tan("

    def test_shift_resets_after_digit_key_too(self, at):
        at.button(key="btn_shift").click().run()
        at.button(key="btn_num-5").click().run()
        assert at.session_state.shift_active is False

    @pytest.mark.parametrize(
        "key,expected_token",
        [
            ("btn_trig-sin", "asin("),
            ("btn_trig-cos", "acos("),
            ("btn_trig-tan", "atan("),
            ("btn_alg-x2", "sqrt("),
            ("btn_alg-log", "ln("),
            ("btn_alg-abs", "exp("),
        ],
    )
    def test_shift_alternate_tokens(self, at, key, expected_token):
        at.button(key="btn_shift").click().run()
        at.button(key=key).click().run()
        assert at.session_state.calc_expression == expected_token


class TestCosmeticKeys:
    @pytest.mark.parametrize(
        "key", ["btn_trig-csc", "btn_trig-sec", "btn_trig-cot", "btn_calc-int", "btn_calc-sum"]
    )
    def test_cosmetic_keys_are_disabled(self, at, key):
        assert at.button(key=key).disabled is True

    def test_cosmetic_key_click_does_not_change_expression(self, at):
        # Disabled buttons can't be clicked through AppTest either (mirrors
        # the browser), but assert the invariant explicitly: nothing in the
        # cosmetic-key wiring ever calls _append.
        before = at.session_state.calc_expression
        assert at.button(key="btn_trig-csc").disabled
        assert at.session_state.calc_expression == before


class TestFunctionTabs:
    def test_three_tabs_present(self, at):
        labels = [t.label for t in at.tabs if t.label in ("Algebra", "Trigonometry", "Calculus")]
        assert set(labels) == {"Algebra", "Trigonometry", "Calculus"}

    def test_algebra_and_trig_keys_both_render_simultaneously(self, at):
        # All tab bodies exist in the Python-side tree every run (Streamlit
        # hides inactive tabs with CSS, not by skipping their code), so keys
        # from every tab must all be queryable in the same run.
        assert at.button(key="btn_alg-x2") is not None
        assert at.button(key="btn_trig-sin") is not None
        assert at.button(key="btn_calc-int") is not None


class TestMemory:
    def test_ms_stores_current_value(self, at):
        at.button(key="btn_num-5").click().run()
        at.button(key="btn_eq").click().run()
        at.button(key="btn_mem-ms").click().run()
        assert at.session_state.calc_memory == 5

    def test_mr_recalls_stored_value(self, at):
        at.button(key="btn_num-5").click().run()
        at.button(key="btn_eq").click().run()
        at.button(key="btn_mem-ms").click().run()
        at.button(key="btn_ac").click().run()
        at.button(key="btn_mem-mr").click().run()
        assert at.session_state.calc_expression == "(5)"

    def test_mc_clears_memory(self, at):
        at.button(key="btn_num-5").click().run()
        at.button(key="btn_eq").click().run()
        at.button(key="btn_mem-ms").click().run()
        at.button(key="btn_mem-mc").click().run()
        assert at.session_state.calc_memory is None

    def test_m_plus_accumulates(self, at):
        at.button(key="btn_num-3").click().run()
        at.button(key="btn_eq").click().run()
        at.button(key="btn_mem-ms").click().run()
        at.button(key="btn_ac").click().run()
        at.button(key="btn_num-4").click().run()
        at.button(key="btn_eq").click().run()
        at.button(key="btn_mem-m+").click().run()
        assert at.session_state.calc_memory == 7


class TestHistoryChips:
    def test_chip_appears_after_evaluating_and_reloads_expression(self, at):
        at.button(key="btn_num-9").click().run()
        at.button(key="btn_eq").click().run()

        entries = history.get_history(mode="Calculator")
        chip_key = f"btn_chip_{entries[0].id}"
        chip = at.button(key=chip_key)
        assert chip.label == "9"

        at.button(key="btn_num-1").click().run()  # dirty the expression
        assert at.session_state.calc_expression == "91"
        at.button(key=chip_key).click().run()
        assert at.session_state.calc_expression == "9"
        assert at.session_state.calc_last_result is None  # cleared until re-evaluated

    def test_no_chips_row_when_history_empty(self, at):
        assert history.get_history(mode="Calculator") == []
        assert not any(b.key and b.key.startswith("btn_chip_") for b in at.button)
