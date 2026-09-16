import streamlit as st
import sympy as sp

from engine.parser import parse_expression
from engine.calculator import evaluate, to_numeric
from engine.errors import MathToolError
from ui import theme

_KEYPAD_ROWS = [
    ["7", "8", "9", "/"],
    ["4", "5", "6", "*"],
    ["1", "2", "3", "-"],
    ["0", ".", "(", ")"],
    ["+", "^", "C", "⌫"],
]


def _append(token: str) -> None:
    st.session_state.calc_expression = st.session_state.get("calc_expression", "") + token


def _clear() -> None:
    st.session_state.calc_expression = ""


def _backspace() -> None:
    st.session_state.calc_expression = st.session_state.get("calc_expression", "")[:-1]


def render() -> None:
    theme.page_header(
        "Calculator",
        "Calculator",
        "Examples: 2+2*3, sqrt(4), sin(pi/2), 2x^2 + 3x - 5",
    )

    if "calc_expression" not in st.session_state:
        st.session_state.calc_expression = ""

    with theme.card("calc-card"):
        # Typing and the keypad below both read/write the same session_state key,
        # so either input method keeps the other in sync.
        st.text_input(
            "Expression", key="calc_expression",
            placeholder="e.g. 2x^2 + 3x - 5", label_visibility="collapsed",
        )

        st.markdown('<div style="height:10px"></div>', unsafe_allow_html=True)

        for row in _KEYPAD_ROWS:
            cols = st.columns(len(row))
            for col, token in zip(cols, row):
                if token == "C":
                    col.button(token, key="key_C", on_click=_clear, width="stretch")
                elif token == "⌫":
                    col.button(token, key="key_bksp", on_click=_backspace, width="stretch")
                else:
                    col.button(
                        token, key=f"key_{token}", on_click=_append, args=(token,),
                        width="stretch",
                    )

    text = st.session_state.calc_expression
    if not text.strip():
        return

    try:
        expr = parse_expression(text)
        result = evaluate(expr)
    except MathToolError as e:
        theme.note(f"<strong>Error</strong> — {theme.esc(e)}", err=True)
        return

    with theme.card("calc-result-card"):
        theme.result_display(f"{theme.esc(text)} =", theme.esc(result))

        col1, col2 = st.columns(2)
        with col1:
            st.markdown('<p class="card-label">Exact</p>', unsafe_allow_html=True)
            st.write(result)
        with col2:
            st.markdown('<p class="card-label">Numeric</p>', unsafe_allow_html=True)
            st.write(to_numeric(result))
