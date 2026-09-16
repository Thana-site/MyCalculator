import streamlit as st

from ui import calculator, solver, graph, area, matrix

st.set_page_config(page_title="Math Tool", page_icon="🧮", layout="centered")
st.title("🧮 Math Tool")

PAGES = {
    "Calculator": calculator,
    "Equation Solver": solver,
    "Graph Plotter": graph,
    "Area Under Curve": area,
    "Matrix": matrix,
}

choice = st.sidebar.radio("Mode", list(PAGES.keys()))
PAGES[choice].render()
