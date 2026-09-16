"""
Graph engine — Phase 5.

Pipeline (locked spec): SymPy expression -> lambdify -> NumPy arrays.
Plotly (or any other renderer) is a UI-layer concern; this module never
imports a plotting library.

Known limitation (documented, not solved in this phase): only basic
np.isfinite masking is done to avoid a line being drawn straight through
an asymptote (e.g. 1/x). Sophisticated discontinuity detection is future
work.
"""

from __future__ import annotations

import numpy as np
import sympy as sp

from .parser import get_symbols
from .errors import GraphError


def generate_numeric_data(
    expr: sp.Expr,
    x_min: float,
    x_max: float,
    num_points: int = 400,
) -> tuple[np.ndarray, np.ndarray]:
    symbols = get_symbols(expr)

    if len(symbols) == 0:
        x_sym = sp.Symbol("x")
    elif len(symbols) == 1:
        x_sym = symbols[0]
    else:
        names = [s.name for s in symbols]
        raise GraphError(
            f"Graphing requires a single-variable expression; found {names}."
        )

    f = sp.lambdify(x_sym, expr, "numpy")
    x_vals = np.linspace(x_min, x_max, num_points)

    try:
        with np.errstate(all="ignore"):
            y_vals = np.asarray(f(x_vals), dtype=float)
        if y_vals.shape == ():
            # constant expression (didn't broadcast) -> fill manually
            y_vals = np.full_like(x_vals, float(y_vals))
    except Exception as exc:  # noqa: BLE001
        raise GraphError(f"Could not evaluate expression over the given range: {exc}") from exc

    # Mask non-finite points (asymptotes, domain errors) instead of letting
    # a renderer draw a line straight through them.
    with np.errstate(all="ignore"):
        y_vals = np.where(np.isfinite(y_vals), y_vals, np.nan)

    return x_vals, y_vals
