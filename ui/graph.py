import streamlit as st
import plotly.graph_objects as go

from engine.parser import parse_expression
from engine.graph import generate_numeric_data
from engine.errors import MathToolError
from ui import theme


def render() -> None:
    theme.page_header(
        "Graph plotter",
        "Graph Plotter",
        "Single-variable functions only, e.g. sin(x) + x^2, 1/x",
    )

    with theme.card("graph-card"):
        text = st.text_input("f(x) =", key="graph_input", placeholder="e.g. sin(x) + x^2")

        col1, col2 = st.columns(2)
        x_min = col1.number_input("x min", value=-10.0, key="graph_xmin")
        x_max = col2.number_input("x max", value=10.0, key="graph_xmax")

        if not text.strip():
            return
        if x_max <= x_min:
            theme.note("<strong>Error</strong> — x max must be greater than x min.", err=True)
            return

        try:
            expr = parse_expression(text)
            x_vals, y_vals = generate_numeric_data(expr, x_min, x_max)
        except MathToolError as e:
            theme.note(f"<strong>Error</strong> — {theme.esc(e)}", err=True)
            return

        fig = go.Figure(go.Scatter(
            x=x_vals, y=y_vals, mode="lines", name=text,
            line=dict(color="#5DCBFF", width=2),
        ))
        fig.update_layout(
            xaxis_title="x",
            yaxis_title="f(x)",
            margin=dict(l=10, r=10, t=10, b=10),
            paper_bgcolor="#1B1B1B",
            plot_bgcolor="#1B1B1B",
            font=dict(color="#A3A3A3", family="IBM Plex Mono, monospace"),
            xaxis=dict(gridcolor="#2A2A2A", zerolinecolor="#333333"),
            yaxis=dict(gridcolor="#2A2A2A", zerolinecolor="#333333"),
        )
        st.plotly_chart(fig, width="stretch")
