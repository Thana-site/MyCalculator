"""
UI smoke tests for the Graph Plotter page: multi-function add/remove/toggle
and pan/zoom config, via streamlit.testing.v1.AppTest.
"""

import json
import sys
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import engine.history as history  # noqa: E402

_APP_PATH = str(Path(__file__).resolve().parents[1] / "app.py")


@pytest.fixture(autouse=True)
def isolated_db(tmp_path, monkeypatch):
    monkeypatch.setattr(history, "_DB_PATH", tmp_path / "test_ui_history.db")
    yield


def _chart_spec(at):
    el = at.get("plotly_chart")[0]
    return json.loads(el.proto.spec), json.loads(el.proto.config)


@pytest.fixture
def at():
    test = AppTest.from_file(_APP_PATH, default_timeout=15)
    test.run()
    test.sidebar.radio[0].set_value("Graph Plotter").run()
    return test


def test_page_loads_with_one_default_function_row(at):
    assert not at.exception
    assert [ti.key for ti in at.text_input] == ["graph_expr_1"]


def test_single_function_plots_one_trace(at):
    at.text_input(key="graph_expr_1").set_value("sin(x)").run()
    assert not at.exception
    spec, _ = _chart_spec(at)
    assert len(spec["data"]) == 1
    assert spec["data"][0]["name"] == "f1(x) = sin(x)"


def test_pan_and_zoom_are_enabled(at):
    at.text_input(key="graph_expr_1").set_value("sin(x)").run()
    spec, config = _chart_spec(at)
    assert spec["layout"]["dragmode"] == "pan"
    assert config["scrollZoom"] is True


class TestMultipleFunctions:
    def test_add_function_creates_a_new_input(self, at):
        at.button(key="graph_add").click().run()
        assert [ti.key for ti in at.text_input] == ["graph_expr_1", "graph_expr_2"]

    def test_both_functions_plot_as_separate_colored_traces(self, at):
        at.text_input(key="graph_expr_1").set_value("sin(x)").run()
        at.button(key="graph_add").click().run()
        at.text_input(key="graph_expr_2").set_value("x^2/4").run()

        spec, _ = _chart_spec(at)
        assert not at.exception
        assert len(spec["data"]) == 2
        names = {t["name"] for t in spec["data"]}
        assert names == {"f1(x) = sin(x)", "f2(x) = x^2/4"}
        colors = {t["line"]["color"] for t in spec["data"]}
        assert len(colors) == 2  # distinct colors

    def test_toggling_visibility_removes_its_trace(self, at):
        at.text_input(key="graph_expr_1").set_value("sin(x)").run()
        at.button(key="graph_add").click().run()
        at.text_input(key="graph_expr_2").set_value("cos(x)").run()

        at.button(key="graph_toggle_2").click().run()
        spec, _ = _chart_spec(at)
        assert [t["name"] for t in spec["data"]] == ["f1(x) = sin(x)"]

        at.button(key="graph_toggle_2").click().run()  # toggle back on
        spec, _ = _chart_spec(at)
        assert len(spec["data"]) == 2

    def test_removing_a_function_drops_its_input_and_trace(self, at):
        at.text_input(key="graph_expr_1").set_value("sin(x)").run()
        at.button(key="graph_add").click().run()
        at.text_input(key="graph_expr_2").set_value("cos(x)").run()

        at.button(key="graph_remove_1").click().run()
        assert not at.exception
        assert [ti.key for ti in at.text_input] == ["graph_expr_2"]
        spec, _ = _chart_spec(at)
        # Trace numbering is positional ("f1", "f2", ...), so the remaining
        # row renumbers to f1 even though its underlying id is still 2.
        assert [t["name"] for t in spec["data"]] == ["f1(x) = cos(x)"]

    def test_last_remaining_function_cannot_be_removed(self, at):
        assert at.button(key="graph_remove_1").disabled is True

    def test_default_single_function_behavior_still_works_unchanged(self, at):
        # Additive rework: the plain single-function path (no "+ Add
        # function" ever clicked) must behave exactly as before.
        at.text_input(key="graph_expr_1").set_value("1/x").run()
        assert not at.exception
        spec, _ = _chart_spec(at)
        assert len(spec["data"]) == 1


class TestErrorHandling:
    def test_invalid_expression_shows_note_without_exception(self, at):
        at.text_input(key="graph_expr_1").set_value("sin(").run()
        assert not at.exception

    def test_multivariable_expression_shows_note_without_exception(self, at):
        at.text_input(key="graph_expr_1").set_value("x+y").run()
        assert not at.exception

    def test_one_bad_function_does_not_block_the_others(self, at):
        at.text_input(key="graph_expr_1").set_value("sin(").run()
        at.button(key="graph_add").click().run()
        at.text_input(key="graph_expr_2").set_value("cos(x)").run()
        assert not at.exception
        spec, _ = _chart_spec(at)
        assert [t["name"] for t in spec["data"]] == ["f2(x) = cos(x)"]

    def test_x_max_not_greater_than_x_min_is_rejected(self, at):
        at.text_input(key="graph_expr_1").set_value("x").run()
        at.number_input(key="graph_xmax").set_value(-20.0).run()
        assert not at.exception
