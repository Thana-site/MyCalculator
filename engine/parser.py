"""
Central Math Parser — the single contract every other engine module
(calculator, solver, matrix, graph, integration) parses user input through.

Locked responsibilities (per spec):
    Parser DOES:      normalize, validate, parse, raise custom errors
    Parser DOES NOT:  calculate, solve, integrate, do matrix ops, plot

Public API:
    parse_expression(text) -> sp.Expr
    parse_equation(text)   -> sp.Eq            (evaluate=False, exactly one '=')
    parse_matrix(text)     -> sp.Matrix        (cells parsed via parse_expression)
    detect_type(text)      -> "expression" | "equation" | "matrix"   (UI-only helper)
    get_symbols(obj)       -> list[sp.Symbol]  (deterministic, sorted by name)
"""

from __future__ import annotations

import re
from typing import Literal

import sympy as sp
from sympy.parsing.sympy_parser import (
    parse_expr,
    standard_transformations,
    implicit_multiplication_application,
)

from .errors import InvalidEquationError, InvalidExpressionError, InvalidMatrixError

# ---------------------------------------------------------------------------
# Controlled namespace — the ONLY names/functions parsing is allowed to see.
# auto_symbol (part of standard_transformations) turns any other bare name
# into a plain sp.Symbol, so unknown "function calls" fail naturally instead
# of reaching an arbitrary SymPy/Python object.
# ---------------------------------------------------------------------------

_ALLOWED_FUNCTIONS = {
    "sin": sp.sin,
    "cos": sp.cos,
    "tan": sp.tan,
    "sqrt": sp.sqrt,
    "log": sp.log,
    "ln": sp.log,      # canonical output is sp.log either way
    "exp": sp.exp,
    "abs": sp.Abs,      # stays symbolic (sp.Abs), never Python abs()
}

_ALLOWED_CONSTANTS = {
    "pi": sp.pi,
    "e": sp.E,
    "E": sp.E,
}

_GLOBAL_DICT = {
    **_ALLOWED_FUNCTIONS,
    **_ALLOWED_CONSTANTS,
    # Required by standard_transformations (auto_number/auto_symbol rewrite
    # literals and bare names into calls to these). These are SymPy's own
    # constructors, not arbitrary code — safe to expose.
    "Integer": sp.Integer,
    "Float": sp.Float,
    "Rational": sp.Rational,
    "Symbol": sp.Symbol,
}

# Function *classes* an AST is allowed to contain, for post-parse validation.
_ALLOWED_FUNC_CLASSES = {sp.sin, sp.cos, sp.tan, sp.log, sp.exp, sp.Abs}

_TRANSFORMATIONS = standard_transformations + (implicit_multiplication_application,)

# Matches "<func> <term>" with no parentheses, e.g. "sin x", "sin 2x".
# Term is kept as-is (e.g. "2x") — implicit multiplication is normalized
# later by the SymPy transformation, not by this regex.
_BARE_FUNC_CALL_RE = re.compile(
    r"\b(" + "|".join(_ALLOWED_FUNCTIONS.keys()) + r")\s+([A-Za-z0-9_.]+)"
)

# Any identifier directly followed by '(' is a function call attempt.
# implicit_multiplication_application's symbol-splitting would otherwise
# silently reinterpret e.g. "foo(x)" as f*o*o*x instead of erroring, so this
# is checked explicitly before parsing rather than relying on AST validation
# alone.
_FUNC_CALL_ATTEMPT_RE = re.compile(r"([A-Za-z_][A-Za-z0-9_]*)\s*\(")


# ---------------------------------------------------------------------------
# Normalization
# ---------------------------------------------------------------------------

def _wrap_bare_function_calls(text: str) -> str:
    """'sin x' -> 'sin(x)', 'sin 2x' -> 'sin(2x)' (NOT '2*sin(x)')."""
    previous = None
    while previous != text:
        previous = text
        text = _BARE_FUNC_CALL_RE.sub(lambda m: f"{m.group(1)}({m.group(2)})", text)
    return text


def normalize_expression(text: str) -> str:
    """Single, centralized place where surface syntax is rewritten into
    something SymPy's parser can read. All ^ -> ** and bare-function-call
    rewriting happens here ONLY — never scattered as ad hoc .replace() calls
    elsewhere in the codebase.
    """
    text = text.strip()
    text = text.replace("^", "**")
    text = _wrap_bare_function_calls(text)
    return text


# ---------------------------------------------------------------------------
# AST validation
# ---------------------------------------------------------------------------

def _validate_no_unknown_function_calls(text: str, *, error_cls) -> None:
    for name in _FUNC_CALL_ATTEMPT_RE.findall(text):
        if name not in _ALLOWED_FUNCTIONS:
            raise error_cls(f"Unknown function: '{name}'.")


def _validate_ast(expr: sp.Expr, *, error_cls=InvalidExpressionError) -> None:
    """Walk the parsed expression tree and reject anything outside the
    allowed function whitelist. Catches cases where controlled parsing
    still produced an unexpected structure.
    """
    for func in expr.atoms(sp.Function):
        if func.func not in _ALLOWED_FUNC_CLASSES:
            raise error_cls(f"Unknown function: '{func.func}'.")


# ---------------------------------------------------------------------------
# Public API — expression
# ---------------------------------------------------------------------------

def parse_expression(text: str) -> sp.Expr:
    if text is None or not text.strip():
        raise InvalidExpressionError("Expression cannot be empty.")

    normalized = normalize_expression(text)
    _validate_no_unknown_function_calls(normalized, error_cls=InvalidExpressionError)

    try:
        expr = parse_expr(
            normalized,
            transformations=_TRANSFORMATIONS,
            global_dict=dict(_GLOBAL_DICT),
            local_dict={},
            evaluate=True,
        )
    except Exception as exc:  # noqa: BLE001 — deliberately broad, re-raised as our own type
        raise InvalidExpressionError("Invalid expression.") from exc

    if not isinstance(expr, sp.Basic):
        raise InvalidExpressionError("Invalid expression.")

    _validate_ast(expr)
    return expr


# ---------------------------------------------------------------------------
# Public API — equation
# ---------------------------------------------------------------------------

def parse_equation(text: str) -> sp.Eq:
    if text is None or not text.strip():
        raise InvalidEquationError("Equation cannot be empty.")

    text = text.strip()

    if text.count("=") != 1:
        raise InvalidEquationError("An equation must contain exactly one '='.")

    lhs_str, rhs_str = text.split("=")
    lhs_str, rhs_str = lhs_str.strip(), rhs_str.strip()

    if not lhs_str:
        raise InvalidEquationError("Equation is missing a left-hand side.")
    if not rhs_str:
        raise InvalidEquationError("Equation is missing a right-hand side.")

    try:
        lhs = parse_expression(lhs_str)
        rhs = parse_expression(rhs_str)
    except InvalidExpressionError as exc:
        raise InvalidEquationError(f"Invalid equation: {exc}") from exc

    # evaluate=False: preserve the equation as-written (e.g. Eq(2+2, 4)
    # must NOT collapse to `True`) — the parser's job is representation,
    # not simplification.
    return sp.Eq(lhs, rhs, evaluate=False)


# ---------------------------------------------------------------------------
# Public API — matrix
# ---------------------------------------------------------------------------

def _split_nested_rows(inner: str) -> list[str]:
    """'[1,2],[3,4]' -> ['1,2', '3,4'], tracking bracket depth."""
    rows: list[str] = []
    depth = 0
    current: list[str] = []
    for ch in inner:
        if ch == "[":
            depth += 1
            if depth == 1:
                current = []
                continue
        elif ch == "]":
            depth -= 1
            if depth == 0:
                rows.append("".join(current))
                continue
        if depth >= 1:
            current.append(ch)
    return rows


def _extract_matrix_rows(text: str) -> list[list[str]]:
    text = text.strip()

    if text.startswith("[") and text.endswith("]"):
        inner = text[1:-1].strip()
        if not inner:
            return []

        if inner.startswith("["):
            # Nested form: [[1,2],[3,4]]
            row_texts = _split_nested_rows(inner)
            return [
                [c.strip() for c in row.split(",") if c.strip() != ""]
                for row in row_texts
            ]

        if ";" in inner:
            # [1;2;3] -> column vector, one entry per row
            return [[c.strip()] for c in inner.split(";")]

        # [1,2,3] -> row vector
        return [[c.strip() for c in inner.split(",")]]

    # No outer brackets: MATLAB-style "1,2;3,4" — ';' = row sep, ',' = col sep
    return [[c.strip() for c in row.split(",")] for row in text.split(";")]


def parse_matrix(text: str) -> sp.Matrix:
    if text is None or not text.strip():
        raise InvalidMatrixError("Matrix cannot be empty.")

    rows_str = _extract_matrix_rows(text)

    if not rows_str or len(rows_str[0]) == 0:
        raise InvalidMatrixError("Matrix cannot be empty.")

    ncols = len(rows_str[0])
    for row in rows_str:
        if len(row) != ncols:
            raise InvalidMatrixError(
                "All rows must have the same number of columns."
            )
        if any(cell == "" for cell in row):
            raise InvalidMatrixError("Matrix contains an empty entry.")

    try:
        parsed_rows = [[parse_expression(cell) for cell in row] for row in rows_str]
    except InvalidExpressionError as exc:
        raise InvalidMatrixError(f"Invalid matrix entry: {exc}") from exc

    return sp.Matrix(parsed_rows)


# ---------------------------------------------------------------------------
# Public API — type detection (UI layer only; engines call the specific
# parse_* function directly and never rely on guessing).
# ---------------------------------------------------------------------------

def detect_type(text: str) -> Literal["expression", "equation", "matrix"]:
    stripped = (text or "").strip()
    if "=" in stripped:
        return "equation"
    if "[" in stripped or ";" in stripped:
        return "matrix"
    return "expression"


# ---------------------------------------------------------------------------
# Public API — symbols
# ---------------------------------------------------------------------------

def get_symbols(obj: sp.Basic) -> list[sp.Symbol]:
    """Deterministic (alphabetical) list of free symbols in an expression,
    equation, or matrix. Downstream code (e.g. Solver's variable dropdown)
    must never depend on SymPy's unordered `.free_symbols`.
    """
    return sorted(obj.free_symbols, key=lambda s: s.name)
