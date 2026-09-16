"""
Integration engine — Phase 6.

Locked spec distinction:
    integrate_signed(f, a, b)     -> plain definite integral, CAN be negative
    integrate_geometric(f, a, b)  -> true (unsigned) area, split at zero
                                      crossings, each segment's magnitude summed

Example: f(x) = x, [-1, 1]
    signed:     0
    geometric:  1
"""

from __future__ import annotations

import numpy as np
import sympy as sp
from scipy import integrate as _scipy_integrate

from .parser import get_symbols
from .errors import IntegrationError


def _resolve_variable(expr: sp.Expr, variable: sp.Symbol | None) -> sp.Symbol:
    if variable is not None:
        return variable
    symbols = get_symbols(expr)
    if len(symbols) == 0:
        return sp.Symbol("x")
    if len(symbols) == 1:
        return symbols[0]
    names = [s.name for s in symbols]
    raise IntegrationError(
        f"Integration requires a single-variable expression; found {names}."
    )


def integrate_signed(
    expr: sp.Expr, a: float, b: float, variable: sp.Symbol | None = None
) -> sp.Expr:
    variable = _resolve_variable(expr, variable)

    try:
        result = sp.integrate(expr, (variable, a, b))
        if not result.has(sp.Integral):
            return result
    except Exception:  # noqa: BLE001
        pass

    # Fallback: numeric quadrature when SymPy can't find a closed form.
    f = sp.lambdify(variable, expr, "numpy")
    with np.errstate(all="ignore"):
        val, _ = _scipy_integrate.quad(f, float(a), float(b))
    if not np.isfinite(val):
        raise IntegrationError(
            f"Could not compute a finite integral over [{a}, {b}]; "
            "the expression may be undefined (e.g. complex-valued) over part of this range."
        )
    return sp.Float(val)


def _find_zero_crossings(
    expr: sp.Expr, variable: sp.Symbol, a: float, b: float
) -> list[float]:
    try:
        roots = sp.solveset(sp.Eq(expr, 0), variable, domain=sp.Interval(a, b))
        if roots.is_FiniteSet:
            return sorted(
                float(r) for r in roots if r.is_real and a < float(r) < b
            )
    except Exception:  # noqa: BLE001
        pass
    return []


def integrate_geometric(
    expr: sp.Expr, a: float, b: float, variable: sp.Symbol | None = None
) -> sp.Expr:
    variable = _resolve_variable(expr, variable)
    a, b = float(a), float(b)

    crossings = _find_zero_crossings(expr, variable, a, b)
    points = sorted(set([a, b] + crossings))

    try:
        total = sp.Integer(0)
        for lo, hi in zip(points, points[1:]):
            mid = (lo + hi) / 2
            sign_probe = sp.N(expr.subs(variable, mid))
            if not sign_probe.is_real:
                raise IntegrationError("Non-real value encountered; cannot determine sign.")
            segment = sp.integrate(expr, (variable, lo, hi))
            if segment.has(sp.Integral):
                raise IntegrationError("no closed form")  # trigger fallback below
            total += -segment if sign_probe < 0 else segment
        return sp.simplify(total)
    except Exception:  # noqa: BLE001
        # Fallback: numeric quadrature of |f(x)| over the whole interval.
        f = sp.lambdify(variable, sp.Abs(expr), "numpy")
        with np.errstate(all="ignore"):
            val, _ = _scipy_integrate.quad(f, a, b)
        if not np.isfinite(val):
            raise IntegrationError(
                f"Could not compute a finite area over [{a}, {b}]; "
                "the expression may be undefined (e.g. complex-valued) over part of this range."
            )
        return sp.Float(val)
