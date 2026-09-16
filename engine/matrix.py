"""
Matrix engine — Phase 4.

Default path: SymPy (symbolic) — exact, supports symbolic entries.
Numerical path (NumPy/SciPy): interface reserved via `backend=` params
below, NOT implemented in this phase. Do not optimize for sparse
matrices yet — just don't close off the door (per locked spec).

Responsibility split:
    parser.py    -> "is this valid matrix syntax?"
    matrix.py    -> "is this operation valid for these matrices' shapes?"
"""

from __future__ import annotations

import sympy as sp

from .errors import DimensionMismatchError, SingularMatrixError


def add(A: sp.Matrix, B: sp.Matrix) -> sp.Matrix:
    if A.shape != B.shape:
        raise DimensionMismatchError(
            f"Matrix addition requires equal dimensions; got {A.shape} and {B.shape}."
        )
    return A + B


def subtract(A: sp.Matrix, B: sp.Matrix) -> sp.Matrix:
    if A.shape != B.shape:
        raise DimensionMismatchError(
            f"Matrix subtraction requires equal dimensions; got {A.shape} and {B.shape}."
        )
    return A - B


def multiply(A: sp.Matrix, B: sp.Matrix) -> sp.Matrix:
    if A.cols != B.rows:
        raise DimensionMismatchError(
            f"Matrix multiplication requires A.columns == B.rows; "
            f"got A{A.shape} and B{B.shape}."
        )
    return A * B


def transpose(A: sp.Matrix) -> sp.Matrix:
    return A.T


def determinant(A: sp.Matrix) -> sp.Expr:
    if A.rows != A.cols:
        raise DimensionMismatchError("Determinant requires a square matrix.")
    return A.det()


def inverse(A: sp.Matrix) -> sp.Matrix:
    if A.rows != A.cols:
        raise DimensionMismatchError("Inverse requires a square matrix.")
    if A.det() == 0:
        raise SingularMatrixError("Matrix is singular; inverse does not exist.")
    return A.inv()


def rank(A: sp.Matrix) -> int:
    return A.rank()


def eigen(A: sp.Matrix) -> dict[sp.Expr, int]:
    """Eigenvalues mapped to their algebraic multiplicity."""
    if A.rows != A.cols:
        raise DimensionMismatchError("Eigenvalues require a square matrix.")
    return A.eigenvals()


def solve_linear_system(
    A: sp.Matrix, b: sp.Matrix, backend: str = "sympy"
) -> sp.Matrix:
    """Solve A x = b.

    `backend` is part of the locked interface for a future NumPy/SciPy
    path (large/sparse systems, e.g. stiffness matrices); only "sympy"
    is implemented in this phase.
    """
    if backend != "sympy":
        raise NotImplementedError(
            f"Backend '{backend}' is reserved for a future phase; "
            "only 'sympy' is implemented now."
        )
    if A.rows != b.rows:
        raise DimensionMismatchError(
            f"A and b must have the same number of rows; got A{A.shape} and b{b.shape}."
        )
    try:
        return A.solve(b)
    except Exception as exc:  # noqa: BLE001
        raise SingularMatrixError(
            "System has no unique solution (matrix is singular or system is inconsistent)."
        ) from exc
