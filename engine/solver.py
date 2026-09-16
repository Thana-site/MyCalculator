"""
Equation Solver engine — Phase 3.

Locked contract:
    solve_equation(eq: sp.Eq, variable: sp.Symbol | None = None) -> dict

    - Single-variable equation: variable may be omitted (auto-selected).
    - Multi-variable equation: variable MUST be supplied by the caller
      (the UI is responsible for presenting a "Solve for: [x v]" choice) —
      the solver never silently guesses.
"""

from __future__ import annotations

from typing import TypedDict

import sympy as sp

from .parser import get_symbols
from .errors import NoVariableError, VariableRequiredError


class SolveResult(TypedDict):
    variable: sp.Symbol
    exact: list[sp.Expr]
    numeric: list[sp.Float | None]


def solve_equation(eq: sp.Eq, variable: sp.Symbol | None = None) -> SolveResult:
    symbols = get_symbols(eq)

    if not symbols:
        raise NoVariableError("Equation has no variable to solve for.")

    if variable is None:
        if len(symbols) == 1:
            variable = symbols[0]
        else:
            names = ", ".join(s.name for s in symbols)
            raise VariableRequiredError(
                f"Equation has multiple variables ({names}); specify which one to solve for."
            )
    elif variable not in symbols:
        raise VariableRequiredError(
            f"'{variable}' does not appear in the equation."
        )

    exact_solutions = sp.solve(sp.Eq(eq.lhs, eq.rhs), variable)

    numeric_solutions: list[sp.Float | None] = []
    for sol in exact_solutions:
        try:
            numeric_solutions.append(sp.N(sol, 6))
        except (TypeError, ValueError):
            numeric_solutions.append(None)

    return {
        "variable": variable,
        "exact": exact_solutions,
        "numeric": numeric_solutions,
    }
