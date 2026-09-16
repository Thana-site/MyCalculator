import streamlit as st
import sympy as sp

from engine.parser import parse_matrix
from engine import matrix as mx
from engine.errors import MathToolError


def render() -> None:
    st.subheader("Matrix")
    st.caption(
        "Formats: [[1,2],[3,4]]  ·  1,2;3,4  ·  [1,2,3] (row)  ·  [1;2;3] (column)  ·  symbolic entries OK, e.g. [[E,2],[3,x]]"
    )

    tab_single, tab_two, tab_solve = st.tabs(
        ["Single-matrix", "Two-matrix", "Solve Ax = b"]
    )

    with tab_single:
        text = st.text_input("Matrix A", key="matrix_a_single", placeholder="[[1,2],[3,4]]")
        op = st.selectbox(
            "Operation", ["Determinant", "Inverse", "Transpose", "Rank", "Eigenvalues"],
            key="matrix_op_single",
        )
        if text.strip():
            try:
                A = parse_matrix(text)
                if op == "Determinant":
                    st.latex(sp.latex(mx.determinant(A)))
                elif op == "Inverse":
                    st.latex(sp.latex(mx.inverse(A)))
                elif op == "Transpose":
                    st.latex(sp.latex(mx.transpose(A)))
                elif op == "Rank":
                    st.write(mx.rank(A))
                elif op == "Eigenvalues":
                    st.write(mx.eigen(A))
            except MathToolError as e:
                st.error(str(e))

    with tab_two:
        col1, col2 = st.columns(2)
        text_a = col1.text_input("Matrix A", key="matrix_a_two", placeholder="[[1,2],[3,4]]")
        text_b = col2.text_input("Matrix B", key="matrix_b_two", placeholder="[[5,6],[7,8]]")
        op2 = st.selectbox("Operation", ["Add", "Subtract", "Multiply"], key="matrix_op_two")
        if text_a.strip() and text_b.strip():
            try:
                A = parse_matrix(text_a)
                B = parse_matrix(text_b)
                if op2 == "Add":
                    result = mx.add(A, B)
                elif op2 == "Subtract":
                    result = mx.subtract(A, B)
                else:
                    result = mx.multiply(A, B)
                st.latex(sp.latex(result))
            except MathToolError as e:
                st.error(str(e))

    with tab_solve:
        col1, col2 = st.columns(2)
        text_A = col1.text_input("Matrix A", key="matrix_a_solve", placeholder="[[1,1],[1,-1]]")
        text_b = col2.text_input("Vector b", key="matrix_b_solve", placeholder="[3;1]")
        if text_A.strip() and text_b.strip():
            try:
                A = parse_matrix(text_A)
                b = parse_matrix(text_b)
                result = mx.solve_linear_system(A, b)
                st.latex(sp.latex(result))
            except MathToolError as e:
                st.error(str(e))
