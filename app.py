import streamlit as st

from ui import calculator, solver, graph, area, matrix, theme

st.set_page_config(page_title="Math Tool", page_icon="🧮", layout="centered")
theme.inject()
theme.sidebar_brand("Math Tool", "v0.1.0")

PAGES = {
    "Calculator": calculator,
    "Equation Solver": solver,
    "Graph Plotter": graph,
    "Area Under Curve": area,
    "Matrix": matrix,
}

choice = st.sidebar.radio("Mode", list(PAGES.keys()), label_visibility="collapsed")
PAGES[choice].render()
