"""
FastAPI backend for Math Tool.

Thin HTTP layer only: every endpoint parses its input through
engine.parser, calls exactly one engine function, and serializes the
result. No math happens here — see engine/ for that.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Literal

import sympy as sp
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from engine import matrix as mx
from engine.calculator import evaluate, to_numeric
from engine.errors import MathToolError
from engine.graph import generate_numeric_data
from engine.integration import integrate_geometric, integrate_signed
from engine.parser import get_symbols, parse_equation, parse_expression, parse_matrix
from engine.solver import solve_equation

app = FastAPI(title="Math Tool API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def _expr_payload(expr: sp.Expr) -> dict:
    return {
        "latex": sp.latex(expr),
        "plain": str(expr),
        "numeric": str(to_numeric(expr)),
    }


def _clean_floats(values) -> list[float | None]:
    """NaN isn't valid JSON — replace with None so the frontend can treat
    it as a gap in the plotted line (matches the engine's asymptote masking)."""
    out = []
    for v in values:
        f = float(v)
        out.append(None if math.isnan(f) or math.isinf(f) else f)
    return out


# ---------------------------------------------------------------------------
# Calculator
# ---------------------------------------------------------------------------

class ExpressionRequest(BaseModel):
    expression: str


@app.post("/api/calculate")
def calculate(req: ExpressionRequest) -> dict:
    try:
        expr = parse_expression(req.expression)
        result = evaluate(expr)
    except MathToolError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return _expr_payload(result)


# ---------------------------------------------------------------------------
# Equation Solver
# ---------------------------------------------------------------------------

class EquationRequest(BaseModel):
    equation: str
    variable: str | None = None


@app.post("/api/solve")
def solve(req: EquationRequest) -> dict:
    try:
        eq = parse_equation(req.equation)
    except MathToolError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    symbols = get_symbols(eq)
    if len(symbols) > 1 and req.variable is None:
        return {"needs_variable": True, "symbols": [s.name for s in symbols]}

    variable = sp.Symbol(req.variable) if req.variable else None
    try:
        result = solve_equation(eq, variable)
    except MathToolError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    return {
        "needs_variable": False,
        "symbols": [s.name for s in symbols],
        "variable": result["variable"].name,
        "exact": [{"latex": sp.latex(s), "plain": str(s)} for s in result["exact"]],
        "numeric": [None if s is None else str(s) for s in result["numeric"]],
    }


# ---------------------------------------------------------------------------
# Graph Plotter
# ---------------------------------------------------------------------------

class GraphRequest(BaseModel):
    expression: str
    x_min: float = -10.0
    x_max: float = 10.0


@app.post("/api/graph")
def graph(req: GraphRequest) -> dict:
    if req.x_max <= req.x_min:
        raise HTTPException(status_code=400, detail="x max must be greater than x min.")
    try:
        expr = parse_expression(req.expression)
        x_vals, y_vals = generate_numeric_data(expr, req.x_min, req.x_max)
    except MathToolError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return {"x": _clean_floats(x_vals), "y": _clean_floats(y_vals)}


# ---------------------------------------------------------------------------
# Area Under Curve
# ---------------------------------------------------------------------------

class AreaRequest(BaseModel):
    expression: str
    a: float = -1.0
    b: float = 1.0
    mode: Literal["signed", "geometric"] = "signed"


@app.post("/api/area")
def area(req: AreaRequest) -> dict:
    if req.b <= req.a:
        raise HTTPException(status_code=400, detail="b must be greater than a.")
    try:
        expr = parse_expression(req.expression)
        result = (
            integrate_signed(expr, req.a, req.b)
            if req.mode == "signed"
            else integrate_geometric(expr, req.a, req.b)
        )
        x_vals, y_vals = generate_numeric_data(expr, req.a, req.b)
    except MathToolError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return {
        **_expr_payload(result),
        "x": _clean_floats(x_vals),
        "y": _clean_floats(y_vals),
    }


# ---------------------------------------------------------------------------
# Matrix
# ---------------------------------------------------------------------------

class MatrixSingleRequest(BaseModel):
    matrix: str
    operation: Literal["determinant", "inverse", "transpose", "rank", "eigenvalues"]


@app.post("/api/matrix/single")
def matrix_single(req: MatrixSingleRequest) -> dict:
    try:
        A = parse_matrix(req.matrix)
        if req.operation == "determinant":
            return _expr_payload(mx.determinant(A))
        if req.operation == "inverse":
            return _expr_payload(mx.inverse(A))
        if req.operation == "transpose":
            return _expr_payload(mx.transpose(A))
        if req.operation == "rank":
            return {"plain": str(mx.rank(A))}
        eigenvalues = mx.eigen(A)
    except MathToolError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return {
        "eigenvalues": [
            {"latex": sp.latex(val), "plain": str(val), "multiplicity": mult}
            for val, mult in eigenvalues.items()
        ]
    }


class MatrixTwoRequest(BaseModel):
    matrix_a: str
    matrix_b: str
    operation: Literal["add", "subtract", "multiply"]


@app.post("/api/matrix/two")
def matrix_two(req: MatrixTwoRequest) -> dict:
    try:
        A = parse_matrix(req.matrix_a)
        B = parse_matrix(req.matrix_b)
        if req.operation == "add":
            result = mx.add(A, B)
        elif req.operation == "subtract":
            result = mx.subtract(A, B)
        else:
            result = mx.multiply(A, B)
    except MathToolError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return _expr_payload(result)


class MatrixSolveRequest(BaseModel):
    matrix_a: str
    vector_b: str


@app.post("/api/matrix/solve")
def matrix_solve(req: MatrixSolveRequest) -> dict:
    try:
        A = parse_matrix(req.matrix_a)
        b = parse_matrix(req.vector_b)
        result = mx.solve_linear_system(A, b)
    except MathToolError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return _expr_payload(result)


# ---------------------------------------------------------------------------
# Static frontend
# ---------------------------------------------------------------------------

_WEB_DIR = Path(__file__).resolve().parent.parent / "web"
app.mount("/", StaticFiles(directory=_WEB_DIR, html=True), name="web")
