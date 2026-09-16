import streamlit as st
import sympy as sp

from engine.parser import parse_equation, get_symbols
from engine.solver import solve_equation
from engine.errors import MathToolError


def render() -> None:
    st.subheader("Equation Solver")
    st.caption("Examples: x^2 + 3x - 5 = 0, x + y = 5")

    text = st.text_input(
        "Equation", key="solver_input", placeholder="e.g. x^2 + 3x - 5 = 0"
    )

    if not text.strip():
        return

    try:
        eq = parse_equation(text)
    except MathToolError as e:
        st.error(str(e))
        return

    symbols = get_symbols(eq)
    variable = None
    if len(symbols) > 1:
        names = [s.name for s in symbols]
        chosen = st.selectbox("Solve for:", names, key="solver_variable")
        variable = sp.Symbol(chosen)

    try:
        result = solve_equation(eq, variable)
    except MathToolError as e:
        st.error(str(e))
        return

    st.write(f"Solving for **{result['variable']}**")

    st.markdown("**Exact**")
    if result["exact"]:
        for sol in result["exact"]:
            st.latex(sp.latex(sol))
    else:
        st.write("No solution found.")

    st.markdown("**Numeric**")
    for i, sol in enumerate(result["numeric"], start=1):
        st.write(f"x_{i} = {sol}" if sol is not None else f"x_{i} = (not numeric)")
