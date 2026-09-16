"""
Custom exception hierarchy for the Math Tool engine.

Design rule (locked spec):
    No raw SymPy/Python exception (ValueError, SympifyError, etc.)
    should ever reach the UI layer. Every failure surfaced to the
    user must be one of the exceptions below, with a clear,
    human-readable message.

UI usage pattern:
    try:
        result = engine.do_something(...)
    except MathToolError as e:
        st.error(str(e))
"""

from __future__ import annotations


class MathToolError(Exception):
    """Base class for every exception raised by the math tool engine."""


# ---------------------------------------------------------------------------
# Parsing errors
# ---------------------------------------------------------------------------

class ParseError(MathToolError):
    """Base class for all parsing failures (expression/equation/matrix)."""


class InvalidExpressionError(ParseError):
    """Raised when a string cannot be parsed as a valid expression.

    Examples:
        ""              -> "Expression cannot be empty."
        "2**"           -> "Invalid expression."
        "sin("          -> "Invalid expression."
    """


class InvalidEquationError(ParseError):
    """Raised when a string cannot be parsed as a valid equation.

    Examples:
        "x ="            -> missing right-hand side
        "= x"            -> missing left-hand side
        "x = y = 2"      -> more than one '='
    """


class InvalidMatrixError(ParseError):
    """Raised when a string cannot be parsed as a valid matrix.

    Examples:
        "[[1,2],[3]]"    -> "All rows must have the same number of columns."
        "[]"             -> empty matrix, no meaningful dimension
        "[[]]"           -> empty matrix, no meaningful dimension
    """


# ---------------------------------------------------------------------------
# Matrix engine errors (operation-level, not parsing-level)
# ---------------------------------------------------------------------------

class MatrixError(MathToolError):
    """Base class for matrix *operation* failures (post-parse)."""


class DimensionMismatchError(MatrixError):
    """Raised when a matrix operation receives incompatible dimensions.

    Example:
        multiply(A: 2x3, B: 4x2)
        -> "Matrix multiplication requires A.columns == B.rows."
    """


class SingularMatrixError(MatrixError):
    """Raised when an operation (e.g. inverse) requires a non-singular
    matrix but the matrix provided is singular (determinant == 0).
    """


# ---------------------------------------------------------------------------
# Solver errors
# ---------------------------------------------------------------------------

class SolverError(MathToolError):
    """Base class for equation-solving failures."""


class NoVariableError(SolverError):
    """Raised when an equation contains no free variable to solve for."""


class VariableRequiredError(SolverError):
    """Raised when an equation has multiple variables and none was chosen,
    or a chosen variable does not appear in the equation.
    """


# ---------------------------------------------------------------------------
# Graph errors
# ---------------------------------------------------------------------------

class GraphError(MathToolError):
    """Base class for graph-plotting failures (e.g. multivariable input,
    an expression that cannot be evaluated numerically)."""


# ---------------------------------------------------------------------------
# Integration errors
# ---------------------------------------------------------------------------

class IntegrationError(MathToolError):
    """Base class for area/integration failures."""
