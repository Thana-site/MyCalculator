import pandas as pd
import streamlit as st
import sympy as sp

from engine.parser import matrix_from_grid
from engine import matrix as mx
from engine.errors import MathToolError
from engine.history import log_entry
from ui import theme

_MAX_SIZE = 6


def _grid_input(key_prefix: str, default_rows: int = 2, default_cols: int = 2) -> list[list[str]]:
    """Rows x cols number pickers + an editable text grid (st.data_editor).
    Cells are text (not numeric) so symbolic entries like 'x' or 'sin(theta)'
    are valid input, same as the old bracket-text syntax. Supports pasting
    directly from Excel/clipboard, which st.data_editor handles natively.
    """
    col1, col2 = st.columns(2)
    rows = col1.number_input(
        "Rows", min_value=1, max_value=_MAX_SIZE, value=default_rows,
        key=f"{key_prefix}_rows",
    )
    cols = col2.number_input(
        "Columns", min_value=1, max_value=_MAX_SIZE, value=default_cols,
        key=f"{key_prefix}_cols",
    )

    state_key = f"{key_prefix}_df"
    if state_key not in st.session_state or st.session_state[state_key].shape != (rows, cols):
        # Preserve overlapping cells when the user resizes the grid instead
        # of wiping everything back to defaults.
        old = st.session_state.get(state_key)
        data = [["0"] * cols for _ in range(rows)]
        if old is not None:
            for r in range(min(rows, old.shape[0])):
                for c in range(min(cols, old.shape[1])):
                    data[r][c] = str(old.iat[r, c])
        st.session_state[state_key] = pd.DataFrame(data)

    edited = st.data_editor(
        st.session_state[state_key],
        key=f"{key_prefix}_editor",
        hide_index=True,
        num_rows="fixed",
        column_config={
            str(c): st.column_config.TextColumn(str(c), width="small")
            for c in st.session_state[state_key].columns
        },
    )
    st.session_state[state_key] = edited
    return edited.astype(str).values.tolist()


def render() -> None:
    theme.page_header(
        "Matrix",
        "Matrix",
        "Enter values in the grid — click a cell to edit, or paste directly from Excel/Sheets. "
        "Symbolic entries are OK too, e.g. E, x, sin(theta).",
    )

    tab_single, tab_two, tab_solve = st.tabs(
        ["Single-matrix", "Two-matrix", "Solve Ax = b"]
    )

    with tab_single:
        with theme.card("matrix-single-card"):
            st.markdown('<p class="card-label">Matrix A</p>', unsafe_allow_html=True)
            cells = _grid_input("matrix_single")
            op = st.selectbox(
                "Operation", ["Determinant", "Inverse", "Transpose", "Rank", "Eigenvalues"],
                key="matrix_op_single",
            )
            try:
                A = matrix_from_grid(cells)
                if op == "Determinant":
                    result = mx.determinant(A)
                    st.latex(sp.latex(result))
                elif op == "Inverse":
                    result = mx.inverse(A)
                    st.latex(sp.latex(result))
                elif op == "Transpose":
                    result = mx.transpose(A)
                    st.latex(sp.latex(result))
                elif op == "Rank":
                    result = mx.rank(A)
                    st.write(result)
                elif op == "Eigenvalues":
                    result = mx.eigen(A)
                    st.write(result)
                try:
                    log_entry("Matrix", f"{op}({sp.sstr(A)})", str(result))
                except Exception:  # noqa: BLE001 — history is best-effort
                    pass
            except MathToolError as e:
                theme.note(f"<strong>Error</strong> — {theme.esc(e)}", err=True)

    with tab_two:
        with theme.card("matrix-two-card"):
            col1, col2 = st.columns(2)
            with col1:
                st.markdown('<p class="card-label">Matrix A</p>', unsafe_allow_html=True)
                cells_a = _grid_input("matrix_a_two")
            with col2:
                st.markdown('<p class="card-label">Matrix B</p>', unsafe_allow_html=True)
                cells_b = _grid_input("matrix_b_two")
            op2 = st.selectbox("Operation", ["Add", "Subtract", "Multiply"], key="matrix_op_two")
            try:
                A = matrix_from_grid(cells_a)
                B = matrix_from_grid(cells_b)
                if op2 == "Add":
                    result = mx.add(A, B)
                elif op2 == "Subtract":
                    result = mx.subtract(A, B)
                else:
                    result = mx.multiply(A, B)
                st.latex(sp.latex(result))
                try:
                    log_entry("Matrix", f"{op2}({sp.sstr(A)}, {sp.sstr(B)})", str(result))
                except Exception:  # noqa: BLE001 — history is best-effort
                    pass
            except MathToolError as e:
                theme.note(f"<strong>Error</strong> — {theme.esc(e)}", err=True)

    with tab_solve:
        with theme.card("matrix-solve-card"):
            col1, col2 = st.columns(2)
            with col1:
                st.markdown('<p class="card-label">Matrix A</p>', unsafe_allow_html=True)
                cells_A = _grid_input("matrix_a_solve", default_rows=2, default_cols=2)
            with col2:
                st.markdown('<p class="card-label">Vector b</p>', unsafe_allow_html=True)
                cells_b = _grid_input("matrix_b_solve", default_rows=2, default_cols=1)
            try:
                A = matrix_from_grid(cells_A)
                b = matrix_from_grid(cells_b)
                result = mx.solve_linear_system(A, b)
                st.latex(sp.latex(result))
                try:
                    log_entry("Matrix", f"Solve({sp.sstr(A)}, {sp.sstr(b)})", str(result))
                except Exception:  # noqa: BLE001 — history is best-effort
                    pass
            except MathToolError as e:
                theme.note(f"<strong>Error</strong> — {theme.esc(e)}", err=True)
