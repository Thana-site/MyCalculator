import streamlit as st
import plotly.graph_objects as go

from engine.parser import parse_expression
from engine.graph import generate_numeric_data
from engine.integration import integrate_signed, integrate_geometric
from engine.errors import MathToolError


def render() -> None:
    st.subheader("Area Under Curve")
    st.caption("Single-variable functions only, e.g. x, x^2 - 1")

    text = st.text_input("f(x) =", key="area_input", placeholder="e.g. x")

    col1, col2 = st.columns(2)
    a = col1.number_input("a (lower bound)", value=-1.0, key="area_a")
    b = col2.number_input("b (upper bound)", value=1.0, key="area_b")

    area_type = st.radio(
        "Area type",
        ["Definite Integral (Signed)", "Geometric Area"],
        key="area_type",
        help="Signed: ∫f(x)dx, can be negative. Geometric: ∫|f(x)|dx, always ≥ 0.",
    )

    if not text.strip():
        return
    if b <= a:
        st.error("b must be greater than a.")
        return

    try:
        expr = parse_expression(text)
        if area_type.startswith("Definite"):
            result = integrate_signed(expr, a, b)
        else:
            result = integrate_geometric(expr, a, b)
        x_vals, y_vals = generate_numeric_data(expr, a, b)
    except MathToolError as e:
        st.error(str(e))
        return

    st.markdown(f"**Result:** {result}")

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=x_vals, y=y_vals, mode="lines", name="f(x)"))
    fig.add_trace(
        go.Scatter(
            x=x_vals, y=y_vals, fill="tozeroy", mode="none",
            name="area", fillcolor="rgba(99, 110, 250, 0.3)",
        )
    )
    fig.update_layout(
        xaxis_title="x",
        yaxis_title="f(x)",
        margin=dict(l=10, r=10, t=10, b=10),
    )
    st.plotly_chart(fig, width="stretch")
