import streamlit as st
import sympy as sp

from engine.parser import parse_expression
from engine.calculator import evaluate, to_numeric
from engine.errors import MathToolError
from ui import theme

# ---------------------------------------------------------------------------
# Keypad definitions
#
# Every key that is NOT marked cosmetic=True inserts a token the engine
# parser can actually evaluate (see engine/parser.py's whitelist). SHIFT
# gives some keys a secondary token; cosmetic keys are grayed-out
# placeholders for functions reserved for a future phase (they never insert
# anything, so they can never produce a stray "Unknown function" error).
# ---------------------------------------------------------------------------

_ALGEBRA_ROWS = [
    [
        {"key": "alg-x2", "label": "x²", "tok": "^2", "shift": ("√", "sqrt(")},
        {"key": "alg-xy", "label": "x^y", "tok": "^", "shift": ("ʸ√x", "^(1/")},
        {"key": "alg-log", "label": "log", "tok": "log(", "shift": ("ln", "ln(")},
        {"key": "alg-abs", "label": "abs", "tok": "abs(", "shift": ("eˣ", "exp(")},
    ],
    [
        {"key": "alg-fact", "label": "n!", "tok": "factorial("},
        {"key": "alg-inf", "label": "∞", "tok": "oo"},
        {"key": "alg-ncr", "label": "nCr", "cosmetic": True},
        {"key": "alg-npr", "label": "nPr", "cosmetic": True},
    ],
    [
        {"key": "alg-paren-open", "label": "(", "tok": "("},
        {"key": "alg-paren-close", "label": ")", "tok": ")"},
        {"key": "alg-pi", "label": "π", "tok": "pi"},
        {"key": "alg-e", "label": "e", "tok": "e"},
    ],
]

_TRIG_ROWS = [
    [
        {"key": "trig-sin", "label": "sin", "tok": "sin(", "shift": ("sin⁻¹", "asin(")},
        {"key": "trig-cos", "label": "cos", "tok": "cos(", "shift": ("cos⁻¹", "acos(")},
        {"key": "trig-tan", "label": "tan", "tok": "tan(", "shift": ("tan⁻¹", "atan(")},
        {"key": "trig-x2", "label": "x²", "tok": "^2", "shift": ("√", "sqrt(")},
    ],
    [
        {"key": "trig-csc", "label": "csc", "cosmetic": True},
        {"key": "trig-sec", "label": "sec", "cosmetic": True},
        {"key": "trig-cot", "label": "cot", "cosmetic": True},
        {"key": "trig-deg", "label": "°→rad", "tok": "*pi/180"},
    ],
    [
        {"key": "trig-paren-open", "label": "(", "tok": "("},
        {"key": "trig-paren-close", "label": ")", "tok": ")"},
        {"key": "trig-pi", "label": "π", "tok": "pi"},
        {"key": "trig-e", "label": "e", "tok": "e"},
    ],
]

_CALCULUS_ROWS = [
    [
        {"key": "calc-ddx", "label": "d/dx", "cosmetic": True},
        {"key": "calc-int", "label": "∫", "cosmetic": True},
        {"key": "calc-oint", "label": "∮", "cosmetic": True},
        {"key": "calc-sum", "label": "Σ", "cosmetic": True},
    ],
    [
        {"key": "calc-prod", "label": "Π", "cosmetic": True},
        {"key": "calc-lim", "label": "lim", "cosmetic": True},
        {"key": "calc-cnk", "label": "C(n,k)", "cosmetic": True},
        {"key": "calc-pnk", "label": "P(n,k)", "cosmetic": True},
    ],
    [
        {"key": "calc-fact", "label": "n!", "tok": "factorial("},
        {"key": "calc-inf", "label": "∞", "tok": "oo"},
        {"key": "calc-log", "label": "log", "tok": "log(", "shift": ("ln", "ln(")},
        {"key": "calc-paren-open", "label": "(", "tok": "("},
    ],
]

_TABS = [("Algebra", _ALGEBRA_ROWS), ("Trigonometry", _TRIG_ROWS), ("Calculus", _CALCULUS_ROWS)]

_MEM_ROW = [("MC", "mc"), ("MR", "mr"), ("M+", "m+"), ("M−", "m-"), ("MS", "ms")]
_NUM_ROWS = [
    [("7", "7"), ("8", "8"), ("9", "9"), ("DEL", None), ("AC", None)],
    [("4", "4"), ("5", "5"), ("6", "6"), ("×", "*"), ("÷", "/")],
    [("1", "1"), ("2", "2"), ("3", "3"), ("+", "+"), ("−", "-")],
    [("0", "0"), (".", "."), ("×10ˣ", "*10^"), ("Ans", None), ("=", None)],
]

_HISTORY_LIMIT = 50
_CHIP_LIMIT = 5


def _append(token: str) -> None:
    st.session_state.calc_expression = st.session_state.get("calc_expression", "") + token


def _press_digit(token: str) -> None:
    # Any keypress — not just function keys — cancels an armed SHIFT,
    # matching a physical calculator (SHIFT + digit isn't a real
    # combination, so it shouldn't stay armed for the next press).
    _append(token)
    st.session_state.shift_active = False


def _clear() -> None:
    st.session_state.calc_expression = ""
    st.session_state.calc_prev_line = ""
    st.session_state.calc_error = None
    st.session_state.calc_last_result = None
    st.session_state.shift_active = False


def _backspace() -> None:
    st.session_state.calc_expression = st.session_state.get("calc_expression", "")[:-1]
    st.session_state.shift_active = False


def _use_ans() -> None:
    last = st.session_state.get("calc_last_result")
    if last is not None:
        _append(f"({last})")
    st.session_state.shift_active = False


def _equals() -> None:
    text = st.session_state.get("calc_expression", "")
    st.session_state.shift_active = False
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
    st.session_state.calc_history.insert(0, {"expr": text, "result": result})
    del st.session_state.calc_history[_HISTORY_LIMIT:]


def _reload_from_history(expr: str) -> None:
    st.session_state.calc_expression = expr
    st.session_state.calc_prev_line = ""
    st.session_state.calc_error = None
    st.session_state.calc_last_result = None
    st.session_state.shift_active = False


def _current_value():
    """The value memory keys act on: the last computed result, or whatever
    is currently typed if it parses cleanly."""
    if st.session_state.get("calc_last_result") is not None:
        return st.session_state.calc_last_result
    text = st.session_state.get("calc_expression", "")
    if not text.strip():
        return None
    try:
        return evaluate(parse_expression(text))
    except MathToolError:
        return None


def _mem_clear() -> None:
    st.session_state.calc_memory = None
    st.session_state.shift_active = False


def _mem_recall() -> None:
    mem = st.session_state.get("calc_memory")
    if mem is not None:
        _append(f"({mem})")
    st.session_state.shift_active = False


def _mem_add() -> None:
    val = _current_value()
    if val is not None:
        st.session_state.calc_memory = (st.session_state.get("calc_memory") or 0) + val
    st.session_state.shift_active = False


def _mem_subtract() -> None:
    val = _current_value()
    if val is not None:
        st.session_state.calc_memory = (st.session_state.get("calc_memory") or 0) - val
    st.session_state.shift_active = False


def _mem_store() -> None:
    val = _current_value()
    if val is not None:
        st.session_state.calc_memory = val
    st.session_state.shift_active = False


def _clear_history() -> None:
    st.session_state.calc_history = []


_MEM_ACTIONS = {
    "mc": _mem_clear, "mr": _mem_recall, "m+": _mem_add, "m-": _mem_subtract, "ms": _mem_store,
}


def _toggle_shift() -> None:
    st.session_state.shift_active = not st.session_state.get("shift_active", False)


def _press_function_key(keydef: dict) -> None:
    if st.session_state.get("shift_active") and "shift" in keydef:
        tok = keydef["shift"][1]
    else:
        tok = keydef["tok"]
    _append(tok)
    st.session_state.shift_active = False


def _keyed_button(col, label: str, key: str, on_click) -> None:
    with col.container(key=f"key-{key}"):
        st.button(label, key=f"btn_{key}", on_click=on_click, width="stretch")


def _render_function_grid(rows: list) -> None:
    for row in rows:
        cols = st.columns(4)
        for col, keydef in zip(cols, row):
            with col.container(key=f"key-{keydef['key']}"):
                if keydef.get("cosmetic"):
                    st.button(
                        keydef["label"], key=f"btn_{keydef['key']}", disabled=True,
                        help="Reserved for a future phase", width="stretch",
                    )
                else:
                    hint = f"SHIFT → {keydef['shift'][0]}" if "shift" in keydef else None
                    st.button(
                        keydef["label"], key=f"btn_{keydef['key']}",
                        on_click=_press_function_key, args=(keydef,),
                        help=hint, width="stretch",
                    )


def _render_history_chips() -> None:
    seen = set()
    chips = []
    for entry in st.session_state.calc_history:
        if entry["expr"] not in seen:
            seen.add(entry["expr"])
            chips.append(entry["expr"])
        if len(chips) >= _CHIP_LIMIT:
            break
    if not chips:
        return
    st.html('<div style="height:6px"></div>')
    cols = st.columns(len(chips))
    for i, (col, expr) in enumerate(zip(cols, chips)):
        with col.container(key=f"chip-{i}"):
            st.button(
                expr, key=f"btn_chip_{i}",
                on_click=_reload_from_history, args=(expr,),
                help="Reload into the expression field", width="stretch",
            )


def _render_keypad() -> None:
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

        mem_cols = st.columns(5)
        for col, (label, action) in zip(mem_cols, _MEM_ROW):
            _keyed_button(col, label, f"mem-{action}", _MEM_ACTIONS[action])

        st.html('<div style="height:6px"></div>')

        shift_col = st.columns(1)[0]
        with shift_col.container(key="key-shift-toggle"):
            st.button(
                "SHIFT" + (" ●" if st.session_state.shift_active else ""),
                key="btn_shift",
                type="primary" if st.session_state.shift_active else "secondary",
                on_click=_toggle_shift,
                help="Arms the next function key's secondary (orange) function",
                width="stretch",
            )

        st.html('<div style="height:6px"></div>')

        tab_labels = [name for name, _ in _TABS]
        tabs = st.tabs(tab_labels)
        for tab, (_, rows) in zip(tabs, _TABS):
            with tab:
                _render_function_grid(rows)

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
                    _keyed_button(col, label, f"num-{label}", lambda t=token: _press_digit(t))

        _render_history_chips()

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


def _render_side_panel() -> None:
    with theme.card("calc-side-card"):
        tab_hist, tab_mem = st.tabs(["History", "Memory"])

        with tab_hist:
            history = st.session_state.calc_history
            if not history:
                theme.empty_note("There's no history yet.")
            else:
                st.button("Clear history", key="btn_clear_history", on_click=_clear_history)
                for entry in history:
                    theme.history_entry(
                        f"{theme.esc(entry['expr'])} =", theme.esc(entry["result"])
                    )

        with tab_mem:
            mem = st.session_state.calc_memory
            if mem is None:
                theme.empty_note("No value stored yet. Use MS to save the current result.")
            else:
                theme.memory_value(theme.esc(mem))


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
        ("calc_history", []),
        ("calc_memory", None),
        ("shift_active", False),
    ]:
        st.session_state.setdefault(key, default)

    col_main, col_side = st.columns([2, 1], gap="medium")
    with col_main:
        _render_keypad()
    with col_side:
        _render_side_panel()
