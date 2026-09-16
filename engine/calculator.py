"""
Calculator engine — Phase 2.

Design rule (locked spec): the canonical result of evaluation is a SymPy
object (e.g. Rational(1, 3)), never a pre-collapsed float. The UI decides
whether to display the exact or numeric form.
"""

from __future__ import annotations

import sympy as sp

from .parser import parse_expression


def evaluate(expr: sp.Expr) -> sp.Expr:
    """Simplify an already-parsed expression, keeping exact form."""
    return sp.simplify(expr)


def to_numeric(expr: sp.Expr, precision: int = 6) -> sp.Float:
    """Numeric approximation of an expression, to `precision` significant
    figures. Returned as a SymPy Float, not a Python float, so the UI can
    format it consistently.
    """
    return sp.N(expr, precision)


def evaluate_text(text: str) -> sp.Expr:
    """Convenience: parse + evaluate in one call."""
    return evaluate(parse_expression(text))
