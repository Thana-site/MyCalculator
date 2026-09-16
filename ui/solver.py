import streamlit as st
import sympy as sp

from engine.parser import parse_equation, get_symbols
from engine.solver import solve_equation
from engine.errors import MathToolError
from ui import theme


def render() -> None:
    theme.page_header(
        "Equation solver",
        "Equation Solver",
        "Examples: x^2 + 3x - 5 = 0, x + y = 5",
    )

    with theme.card("solver-card"):
        text = st.text_input(
            "Equation", key="solver_input", placeholder="e.g. x^2 + 3x - 5 = 0"
        )

        if not text.strip():
            return

        try:
            eq = parse_equation(text)
        except MathToolError as e:
            theme.note(f"<strong>Error</strong> — {theme.esc(e)}", err=True)
            return

        symbols = get_symbols(eq)
        variable = None
        if len(symbols) > 1:
            names = [s.name for s in symbols]
            st.markdown('<p class="card-label">Solve for</p>', unsafe_allow_html=True)
            chosen = st.selectbox(
                "Solve for:", names, key="solver_variable", label_visibility="collapsed",
            )
            variable = sp.Symbol(chosen)

        try:
            result = solve_equation(eq, variable)
        except MathToolError as e:
            theme.note(f"<strong>Error</strong> — {theme.esc(e)}", err=True)
            return

    with theme.card("solver-result-card"):
        st.markdown(
            f'<p class="card-label">Solving for {result["variable"]}</p>',
            unsafe_allow_html=True,
        )

        st.markdown('<p class="card-label">Exact</p>', unsafe_allow_html=True)
        if result["exact"]:
            for sol in result["exact"]:
                st.latex(sp.latex(sol))
        else:
            st.write("No solution found.")

        st.markdown('<p class="card-label">Numeric</p>', unsafe_allow_html=True)
        for i, sol in enumerate(result["numeric"], start=1):
            st.write(f"x_{i} = {sol}" if sol is not None else f"x_{i} = (not numeric)")
