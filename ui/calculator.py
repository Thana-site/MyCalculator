import streamlit as st
import sympy as sp

from engine.parser import parse_expression
from engine.calculator import evaluate, to_numeric
from engine.errors import MathToolError
from ui import theme

# Only functions the engine parser actually supports get wired in here —
# no dead keys that would just raise "Unknown function."
_SCI_ROWS = [
    [("x²", "^2"), ("log", "log("), ("ln", "ln("), ("abs", "abs(")],
    [("sin", "sin("), ("cos", "cos("), ("tan", "tan("), ("x^y", "^")],
    [("(", "("), (")", ")"), ("π", "pi"), ("e", "e")],
]
_NUM_ROWS = [
    [("7", "7"), ("8", "8"), ("9", "9"), ("DEL", None), ("AC", None)],
    [("4", "4"), ("5", "5"), ("6", "6"), ("×", "*"), ("÷", "/")],
    [("1", "1"), ("2", "2"), ("3", "3"), ("+", "+"), ("−", "-")],
    [("0", "0"), (".", "."), ("×10ˣ", "*10^"), ("Ans", None), ("=", None)],
]


def _append(token: str) -> None:
    st.session_state.calc_expression = st.session_state.get("calc_expression", "") + token


def _clear() -> None:
    st.session_state.calc_expression = ""
    st.session_state.calc_prev_line = ""
    st.session_state.calc_error = None
    st.session_state.calc_last_result = None


def _backspace() -> None:
    st.session_state.calc_expression = st.session_state.get("calc_expression", "")[:-1]


def _use_ans() -> None:
    last = st.session_state.get("calc_last_result")
    if last is not None:
        _append(f"({last})")


def _equals() -> None:
    text = st.session_state.get("calc_expression", "")
    if not text.strip():
        return
    try:
        expr = parse_expression(text)
        result = evaluate(expr)
    except MathToolError as e:
        st.session_state.calc_error = str(e)
        return
    st.session_state.calc_error = None
    st.session_state.calc_prev_line = f"{text} ="
    st.session_state.calc_expression = str(result)
    st.session_state.calc_last_result = result


def _keyed_button(col, label: str, key: str, on_click) -> None:
    with col.container(key=f"key-{key}"):
        st.button(label, key=f"btn_{key}", on_click=on_click, width="stretch")


def render() -> None:
    theme.page_header(
        "Calculator",
        "Calculator",
        "Examples: 2+2*3, sqrt(4), sin(pi/2), 2x^2 + 3x - 5",
    )

    for key, default in [
        ("calc_expression", ""),
        ("calc_prev_line", ""),
        ("calc_error", None),
        ("calc_last_result", None),
    ]:
        st.session_state.setdefault(key, default)

    with theme.card("calc-card"):
        theme.lcd_display(
            theme.esc(st.session_state.calc_prev_line),
            theme.esc(st.session_state.calc_expression),
        )

        st.text_input(
            "Expression", key="calc_expression",
            placeholder="or type directly, e.g. 2x^2 + 3x - 5",
            label_visibility="collapsed",
        )

        st.html('<div style="height:10px"></div>')

        for row in _SCI_ROWS:
            cols = st.columns(4)
            for col, (label, token) in zip(cols, row):
                _keyed_button(col, label, f"sci-{label}", lambda t=token: _append(t))

        st.html('<div style="height:6px"></div>')

        for row in _NUM_ROWS:
            cols = st.columns(5)
            for col, (label, token) in zip(cols, row):
                if label == "DEL":
                    _keyed_button(col, label, "del", _backspace)
                elif label == "AC":
                    _keyed_button(col, label, "ac", _clear)
                elif label == "Ans":
                    _keyed_button(col, label, "ans", _use_ans)
                elif label == "=":
                    _keyed_button(col, label, "eq", _equals)
                else:
                    _keyed_button(col, label, f"num-{label}", lambda t=token: _append(t))

    if st.session_state.calc_error:
        theme.note(f"<strong>Error</strong> — {theme.esc(st.session_state.calc_error)}", err=True)
        return

    result = st.session_state.calc_last_result
    if result is None:
        return

    with theme.card("calc-result-card"):
        col1, col2 = st.columns(2)
        with col1:
            st.markdown('<p class="card-label">Exact</p>', unsafe_allow_html=True)
            st.write(result)
        with col2:
            st.markdown('<p class="card-label">Numeric</p>', unsafe_allow_html=True)
            st.write(to_numeric(result))
