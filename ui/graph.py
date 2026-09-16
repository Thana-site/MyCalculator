import streamlit as st
import plotly.graph_objects as go

from engine.parser import parse_expression
from engine.graph import generate_numeric_data
from engine.errors import MathToolError


def render() -> None:
    st.subheader("Graph Plotter")
    st.caption("Single-variable functions only, e.g. sin(x) + x^2, 1/x")

    text = st.text_input("f(x) =", key="graph_input", placeholder="e.g. sin(x) + x^2")

    col1, col2 = st.columns(2)
    x_min = col1.number_input("x min", value=-10.0, key="graph_xmin")
    x_max = col2.number_input("x max", value=10.0, key="graph_xmax")

    if not text.strip():
        return
    if x_max <= x_min:
        st.error("x max must be greater than x min.")
        return

    try:
        expr = parse_expression(text)
        x_vals, y_vals = generate_numeric_data(expr, x_min, x_max)
    except MathToolError as e:
        st.error(str(e))
        return

    fig = go.Figure(go.Scatter(x=x_vals, y=y_vals, mode="lines", name=text))
    fig.update_layout(
        xaxis_title="x",
        yaxis_title="f(x)",
        margin=dict(l=10, r=10, t=10, b=10),
    )
    st.plotly_chart(fig, width="stretch")
