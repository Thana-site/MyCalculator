import streamlit as st
import sympy as sp

from engine.parser import parse_expression
from engine.calculator import evaluate, to_numeric
from engine.errors import MathToolError
from ui import theme

# Each function key: main action always available; shift/alpha are optional
# alternates (only functions the engine parser actually supports get wired
# in — no dead keys that would just raise "Unknown function").
_FUNCTION_KEYS = [
    [
        {"label": "x²", "tok": "^2", "shift": ("√", "sqrt("), "alpha": ("X", "X")},
        {"label": "log", "tok": "log(", "shift": ("10ˣ", "10^"), "alpha": ("Y", "Y")},
        {"label": "ln", "tok": "ln(", "shift": ("eˣ", "exp("), "alpha": ("A", "A")},
        {"label": "abs", "tok": "abs(", "alpha": ("B", "B")},
    ],
    [
        {"label": "sin", "tok": "sin("},
        {"label": "cos", "tok": "cos("},
        {"label": "tan", "tok": "tan("},
        {"label": "x^y", "tok": "^"},
    ],
    [
        {"label": "(", "tok": "(", "alpha": ("M", "M")},
        {"label": ")", "tok": ")"},
        {"label": "π", "tok": "pi"},
        {"label": "e", "tok": "e"},
    ],
]

_NUMPAD_ROWS = [
    ["7", "8", "9", "DEL", "AC"],
    ["4", "5", "6", "×", "÷"],
    ["1", "2", "3", "+", "−"],
    ["0", ".", "×10^x", "Ans", "="],
]

_NUMPAD_TOKENS = {
    "×": "*", "÷": "/", "−": "-", "×10^x": "*10^",
}


def _key_press(main_tok: str, shift: tuple | None = None, alpha: tuple | None = None) -> None:
    if st.session_state.get("calc_shift") and shift:
        tok = shift[1]
    elif st.session_state.get("calc_alpha") and alpha:
        tok = alpha[1]
    else:
        tok = main_tok
    st.session_state.calc_expression = st.session_state.get("calc_expression", "") + tok
    st.session_state.calc_shift = False
    st.session_state.calc_alpha = False


def _toggle_shift() -> None:
    st.session_state.calc_shift = not st.session_state.get("calc_shift", False)
    st.session_state.calc_alpha = False


def _toggle_alpha() -> None:
    st.session_state.calc_alpha = not st.session_state.get("calc_alpha", False)
    st.session_state.calc_shift = False


def _clear() -> None:
    st.session_state.calc_expression = ""
    st.session_state.calc_shift = False
    st.session_state.calc_alpha = False


def _backspace() -> None:
    st.session_state.calc_expression = st.session_state.get("calc_expression", "")[:-1]


def _press_ans() -> None:
    last = st.session_state.get("calc_last_answer")
    tok = f"({last})" if last is not None else ""
    st.session_state.calc_expression = st.session_state.get("calc_expression", "") + tok
    st.session_state.calc_shift = False
    st.session_state.calc_alpha = False


def _noop() -> None:
    pass


def _keyed_button(col, label: str, key: str, on_click, help_text: str | None = None) -> None:
    with col.container(key=f"key-{key}"):
        st.button(label, key=f"btn_{key}", on_click=on_click, width="stretch", help=help_text)


def render() -> None:
    theme.page_header(
        "Calculator",
        "Calculator",
        "Examples: 2+2*3, sqrt(4), sin(pi/2), 2x^2 + 3x - 5",
    )

    if "calc_expression" not in st.session_state:
        st.session_state.calc_expression = ""
    st.session_state.setdefault("calc_shift", False)
    st.session_state.setdefault("calc_alpha", False)

    text = st.session_state.calc_expression
    result = None
    error = None
    if text.strip():
        try:
            expr = parse_expression(text)
            result = evaluate(expr)
            st.session_state.calc_last_answer = result
        except MathToolError as e:
            error = str(e)

    with theme.card("calc-card"):
        theme.lcd_display(
            f"{theme.esc(text)} =" if text.strip() else "",
            theme.esc(result) if result is not None else ("ERROR" if error else ""),
            shift=st.session_state.calc_shift,
            alpha=st.session_state.calc_alpha,
        )

        st.text_input(
            "Expression", key="calc_expression",
            placeholder="or type directly, e.g. 2x^2 + 3x - 5",
            label_visibility="collapsed",
        )

        st.html('<div style="height:12px"></div>')

        # SHIFT / ALPHA toggles
        c1, c2 = st.columns(2)
        _keyed_button(c1, "SHIFT", "shift", _toggle_shift)
        _keyed_button(c2, "ALPHA", "alpha", _toggle_alpha)

        st.html('<div style="height:6px"></div>')

        # Scientific function keys, with SHIFT/ALPHA alternates shown as a tooltip.
        for row in _FUNCTION_KEYS:
            cols = st.columns(len(row))
            for col, keydef in zip(cols, row):
                hints = []
                if "shift" in keydef:
                    hints.append(f"SHIFT → {keydef['shift'][0]}")
                if "alpha" in keydef:
                    hints.append(f"ALPHA → {keydef['alpha'][0]}")
                help_text = "  |  ".join(hints) or None
                key_id = f"fn-{keydef['label']}"
                _keyed_button(
                    col, keydef["label"], key_id,
                    lambda k=keydef: _key_press(k["tok"], k.get("shift"), k.get("alpha")),
                    help_text,
                )

        st.html('<div style="height:6px"></div>')

        # Numeric block, Casio-style: 7 8 9 DEL AC / 4 5 6 x / ...
        for row in _NUMPAD_ROWS:
            cols = st.columns(len(row))
            for col, token in zip(cols, row):
                key_id = f"num-{token}"
                if token == "DEL":
                    _keyed_button(col, "DEL", "del", _backspace)
                elif token == "AC":
                    _keyed_button(col, "AC", "ac", _clear)
                elif token == "Ans":
                    _keyed_button(col, "Ans", "ans", _press_ans)
                elif token == "=":
                    _keyed_button(col, "=", "eq", _noop)
                else:
                    tok = _NUMPAD_TOKENS.get(token, token)
                    _keyed_button(
                        col, token, key_id, lambda t=tok: _key_press(t),
                    )

    if error:
        theme.note(f"<strong>Error</strong> — {theme.esc(error)}", err=True)
        return
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
