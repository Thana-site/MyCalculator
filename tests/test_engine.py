import sys
from pathlib import Path

import numpy as np
import pytest
import sympy as sp

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from engine.parser import parse_expression, parse_equation, parse_matrix  # noqa: E402
from engine.calculator import evaluate, to_numeric, evaluate_text  # noqa: E402
from engine.solver import solve_equation  # noqa: E402
from engine import matrix as mx  # noqa: E402
from engine.graph import generate_numeric_data  # noqa: E402
from engine.integration import integrate_signed, integrate_geometric  # noqa: E402
from engine.errors import (  # noqa: E402
    NoVariableError,
    VariableRequiredError,
    DimensionMismatchError,
    SingularMatrixError,
    GraphError,
    IntegrationError,
)

x, y = sp.symbols("x y")


# ---------------------------------------------------------------------------
# Calculator
# ---------------------------------------------------------------------------

class TestCalculator:
    def test_evaluate_keeps_exact_rational(self):
        assert evaluate_text("1/3") == sp.Rational(1, 3)

    def test_evaluate_simplifies(self):
        result = evaluate(parse_expression("2+2*3"))
        assert result == 8

    def test_to_numeric(self):
        result = to_numeric(sp.Rational(1, 3))
        assert abs(float(result) - 0.333333) < 1e-5


# ---------------------------------------------------------------------------
# Solver
# ---------------------------------------------------------------------------

class TestSolver:
    def test_single_variable_auto_selected(self):
        eq = parse_equation("x^2 - 4 = 0")
        result = solve_equation(eq)
        assert result["variable"] == x
        assert set(result["exact"]) == {-2, 2}

    def test_numeric_solutions_present(self):
        eq = parse_equation("x^2 + 3x - 5 = 0")
        result = solve_equation(eq)
        assert len(result["numeric"]) == 2
        for n in result["numeric"]:
            assert n is not None

    def test_multi_variable_requires_choice(self):
        eq = parse_equation("x + y = 5")
        with pytest.raises(VariableRequiredError):
            solve_equation(eq)

    def test_multi_variable_with_explicit_choice(self):
        eq = parse_equation("x + y = 5")
        result = solve_equation(eq, variable=x)
        assert result["variable"] == x
        assert result["exact"] == [5 - y]

    def test_variable_not_in_equation(self):
        eq = parse_equation("x^2 - 4 = 0")
        with pytest.raises(VariableRequiredError):
            solve_equation(eq, variable=sp.Symbol("z"))

    def test_no_variable(self):
        eq = parse_equation("2 + 2 = 4")
        with pytest.raises(NoVariableError):
            solve_equation(eq)


# ---------------------------------------------------------------------------
# Matrix
# ---------------------------------------------------------------------------

class TestMatrixOps:
    def test_add(self):
        A = parse_matrix("[[1,2],[3,4]]")
        B = parse_matrix("[[5,6],[7,8]]")
        assert mx.add(A, B) == sp.Matrix([[6, 8], [10, 12]])

    def test_add_dimension_mismatch(self):
        A = parse_matrix("[[1,2],[3,4]]")
        B = parse_matrix("[1,2,3]")
        with pytest.raises(DimensionMismatchError):
            mx.add(A, B)

    def test_subtract(self):
        A = parse_matrix("[[5,6],[7,8]]")
        B = parse_matrix("[[1,2],[3,4]]")
        assert mx.subtract(A, B) == sp.Matrix([[4, 4], [4, 4]])

    def test_subtract_dimension_mismatch(self):
        A = parse_matrix("[[1,2],[3,4]]")
        B = parse_matrix("[1;2;3]")
        with pytest.raises(DimensionMismatchError):
            mx.subtract(A, B)

    def test_eigen(self):
        A = parse_matrix("[[2,0],[0,3]]")
        assert mx.eigen(A) == {2: 1, 3: 1}

    def test_eigen_non_square(self):
        A = parse_matrix("[1,2,3]")
        with pytest.raises(DimensionMismatchError):
            mx.eigen(A)

    def test_solve_linear_system_dimension_mismatch(self):
        A = parse_matrix("[[1,2],[3,4]]")   # 2x2
        b = parse_matrix("[1;2;3]")          # 3x1
        with pytest.raises(DimensionMismatchError):
            mx.solve_linear_system(A, b)

    def test_multiply(self):
        A = parse_matrix("[[1,2],[3,4]]")  # 2x2
        B = parse_matrix("[[1],[1]]")       # 2x1
        assert mx.multiply(A, B) == sp.Matrix([[3], [7]])

    def test_multiply_dimension_mismatch(self):
        A = parse_matrix("[[1,2],[3,4]]")   # 2x2
        B = parse_matrix("[[1,2],[3,4],[5,6]]")  # 3x2
        with pytest.raises(DimensionMismatchError):
            mx.multiply(A, B)

    def test_transpose(self):
        A = parse_matrix("[1,2,3]")
        assert mx.transpose(A) == sp.Matrix([[1], [2], [3]])

    def test_determinant(self):
        A = parse_matrix("[[1,2],[3,4]]")
        assert mx.determinant(A) == -2

    def test_determinant_non_square(self):
        A = parse_matrix("[1,2,3]")
        with pytest.raises(DimensionMismatchError):
            mx.determinant(A)

    def test_inverse_non_square(self):
        A = parse_matrix("[1,2,3]")
        with pytest.raises(DimensionMismatchError):
            mx.inverse(A)

    def test_inverse(self):
        A = parse_matrix("[[1,2],[3,4]]")
        inv = mx.inverse(A)
        assert mx.multiply(A, inv) == sp.eye(2)

    def test_inverse_singular(self):
        A = parse_matrix("[[1,2],[2,4]]")
        with pytest.raises(SingularMatrixError):
            mx.inverse(A)

    def test_rank(self):
        A = parse_matrix("[[1,2],[2,4]]")
        assert mx.rank(A) == 1

    def test_symbolic_matrix_ops(self):
        A = parse_matrix("[[E,2],[3,x]]")
        det = mx.determinant(A)
        assert sp.simplify(det - (sp.E * x - 6)) == 0

    def test_solve_linear_system(self):
        A = parse_matrix("[[1,1],[1,-1]]")
        b = parse_matrix("[3;1]")
        result = mx.solve_linear_system(A, b)
        assert result == sp.Matrix([[2], [1]])

    def test_solve_linear_system_singular(self):
        A = parse_matrix("[[1,2],[2,4]]")
        b = parse_matrix("[1;1]")
        with pytest.raises(SingularMatrixError):
            mx.solve_linear_system(A, b)

    def test_unimplemented_backend(self):
        A = parse_matrix("[[1,0],[0,1]]")
        b = parse_matrix("[1;1]")
        with pytest.raises(NotImplementedError):
            mx.solve_linear_system(A, b, backend="numpy")


# ---------------------------------------------------------------------------
# Graph
# ---------------------------------------------------------------------------

class TestGraph:
    def test_basic_curve(self):
        expr = parse_expression("x^2")
        xs, ys = generate_numeric_data(expr, -2, 2, num_points=5)
        assert len(xs) == 5
        assert np.isclose(ys[0], 4.0)  # x=-2 -> 4
        assert np.isclose(ys[-1], 4.0)  # x=2 -> 4

    def test_constant_expression_broadcasts(self):
        expr = parse_expression("5")
        xs, ys = generate_numeric_data(expr, -1, 1, num_points=4)
        assert np.allclose(ys, 5.0)

    def test_asymptote_masked_not_finite(self):
        expr = parse_expression("1/x")
        xs, ys = generate_numeric_data(expr, -1, 1, num_points=401)
        # the value nearest x=0 should be masked (nan), not a huge spike used for plotting
        idx_near_zero = np.argmin(np.abs(xs))
        assert np.isnan(ys[idx_near_zero]) or abs(xs[idx_near_zero]) > 1e-6

    def test_multivariable_rejected(self):
        expr = parse_expression("x + y")
        with pytest.raises(GraphError):
            generate_numeric_data(expr, -1, 1)

    def test_sin_curve(self):
        expr = parse_expression("sin(x)")
        xs, ys = generate_numeric_data(expr, 0, np.pi, num_points=3)
        assert np.isclose(ys[0], 0.0, atol=1e-9)
        assert np.isclose(ys[1], 1.0, atol=1e-9)   # sin(pi/2) = 1
        assert np.isclose(ys[-1], 0.0, atol=1e-9)

    def test_sqrt_domain_produces_nan_outside_domain(self):
        # sqrt(x) is undefined (complex) for x<0 -> those points must not be
        # plotted as real, finite values.
        expr = parse_expression("sqrt(x)")
        xs, ys = generate_numeric_data(expr, -4, 4, num_points=401)
        negative_mask = xs < 0
        assert not np.any(np.isfinite(ys[negative_mask]))
        positive_mask = xs > 0
        assert np.any(np.isfinite(ys[positive_mask]))


# ---------------------------------------------------------------------------
# Integration
# ---------------------------------------------------------------------------

class TestIntegration:
    def test_signed_integral_of_x_over_symmetric_range(self):
        expr = parse_expression("x")
        result = integrate_signed(expr, -1, 1)
        assert result == 0

    def test_geometric_area_of_x_over_symmetric_range(self):
        expr = parse_expression("x")
        result = integrate_geometric(expr, -1, 1)
        assert sp.simplify(result - 1) == 0

    def test_signed_vs_geometric_differ_with_sign_change(self):
        expr = parse_expression("x")
        signed = integrate_signed(expr, -2, 3)
        geometric = integrate_geometric(expr, -2, 3)
        # signed: (9-4)/2 = 2.5 ; geometric: 2 + 4.5 = 6.5
        assert sp.simplify(signed - sp.Rational(5, 2)) == 0
        assert sp.simplify(geometric - sp.Rational(13, 2)) == 0

    def test_no_sign_change_signed_equals_geometric(self):
        expr = parse_expression("x^2")
        signed = integrate_signed(expr, 1, 3)
        geometric = integrate_geometric(expr, 1, 3)
        assert sp.simplify(signed - geometric) == 0

    def test_constant_expression_integration(self):
        # no free symbols at all -> _resolve_variable's zero-symbols branch
        expr = parse_expression("5")
        assert abs(float(integrate_signed(expr, 0, 2)) - 10) < 1e-9
        assert abs(float(integrate_geometric(expr, 0, 2)) - 10) < 1e-9

    def test_domain_error_raises_clear_message_not_nan(self):
        # sqrt(x) is complex for x<0 -> must raise, never silently return NaN
        # (found during final audit: this previously returned NaN silently)
        expr = parse_expression("sqrt(x)")
        with pytest.raises(IntegrationError):
            integrate_geometric(expr, -1, 1)

    def test_signed_explicit_variable(self):
        expr = parse_expression("x + y")
        result = integrate_signed(expr, 0, 2, variable=x)
        assert sp.simplify(result - (2 * y + 2)) == 0

    def test_signed_multivariable_without_explicit_variable_raises(self):
        expr = parse_expression("x + y")
        with pytest.raises(IntegrationError):
            integrate_signed(expr, 0, 1)

    def test_geometric_multivariable_without_explicit_variable_raises(self):
        expr = parse_expression("x + y")
        with pytest.raises(IntegrationError):
            integrate_geometric(expr, 0, 1)

    def test_signed_numeric_fallback_for_no_closed_form(self):
        # exp(sin(x)) has no closed-form antiderivative at all (unlike
        # sin(x)/x, which SymPy resolves via the special function Si) ->
        # this genuinely exercises the scipy.integrate.quad fallback path.
        expr = parse_expression("exp(sin(x))")
        result = integrate_signed(expr, 0, 1)
        assert abs(float(result) - 1.6318696084180513) < 1e-6

    def test_geometric_numeric_fallback_for_no_closed_form(self):
        # x*exp(sin(x)) also has no closed form AND changes sign at x=0,
        # so this exercises both the zero-crossing split logic and the
        # per-segment "no closed form" -> whole-interval quad fallback.
        expr = parse_expression("x*exp(sin(x))")
        result = integrate_geometric(expr, -1, 1)
        assert abs(float(result) - 1.208235813332709) < 1e-6
