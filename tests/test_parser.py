import sys
from pathlib import Path

import pytest
import sympy as sp

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from engine.parser import (  # noqa: E402
    parse_expression,
    parse_equation,
    parse_matrix,
    matrix_from_grid,
    detect_type,
    get_symbols,
)
from engine.errors import (  # noqa: E402
    InvalidExpressionError,
    InvalidEquationError,
    InvalidMatrixError,
)

x, y = sp.symbols("x y")


# ---------------------------------------------------------------------------
# Expression — golden cases
# ---------------------------------------------------------------------------

class TestExpressionGolden:
    def test_implicit_multiplication_number_symbol(self):
        assert sp.simplify(parse_expression("2x") - 2 * x) == 0

    def test_implicit_multiplication_with_parens(self):
        assert sp.simplify(parse_expression("2(x+1)") - 2 * (x + 1)) == 0

    def test_power_operator(self):
        assert sp.simplify(parse_expression("x^2") - x**2) == 0

    def test_full_polynomial(self):
        assert sp.simplify(parse_expression("2x^2 + 3x - 5") - (2 * x**2 + 3 * x - 5)) == 0

    def test_bare_function_call(self):
        assert sp.simplify(parse_expression("sin x") - sp.sin(x)) == 0

    def test_bare_function_call_with_coefficient(self):
        # 'sin 2x' means sin(2*x), NOT 2*sin(x)
        assert sp.simplify(parse_expression("sin 2x") - sp.sin(2 * x)) == 0

    def test_parenthesized_function_call(self):
        assert sp.simplify(parse_expression("sin(x+1)") - sp.sin(x + 1)) == 0

    def test_sqrt(self):
        assert parse_expression("sqrt(4)") == 2

    def test_ln_maps_to_log(self):
        assert parse_expression("ln(x)") == sp.log(x)

    def test_log_and_ln_are_same_canonical_function(self):
        assert parse_expression("log(x)").func == parse_expression("ln(x)").func

    def test_constant_e_lowercase(self):
        assert parse_expression("e") == sp.E

    def test_constant_e_uppercase(self):
        assert parse_expression("E") == sp.E

    def test_pi(self):
        assert parse_expression("pi") == sp.pi

    def test_abs_stays_symbolic(self):
        result = parse_expression("abs(x)")
        assert result.func == sp.Abs

    def test_rational_stays_exact(self):
        # canonical representation should not collapse to a float
        assert parse_expression("1/3") == sp.Rational(1, 3)

    def test_asin_golden(self):
        assert parse_expression("asin(1)") == sp.pi / 2

    def test_acos_golden(self):
        assert parse_expression("acos(1)") == 0

    def test_atan_golden(self):
        assert parse_expression("atan(1)") == sp.pi / 4

    def test_factorial(self):
        assert parse_expression("factorial(5)") == 120

    def test_infinity_constant(self):
        assert parse_expression("oo") == sp.oo


# ---------------------------------------------------------------------------
# Expression — invalid cases
# ---------------------------------------------------------------------------

class TestExpressionInvalid:
    @pytest.mark.parametrize("text", ["", "   "])
    def test_empty(self, text):
        with pytest.raises(InvalidExpressionError):
            parse_expression(text)

    @pytest.mark.parametrize(
        "text", ["2**", "sin(", "x^^2", "**", "2+", "(1+", "2/**3"]
    )
    def test_malformed(self, text):
        with pytest.raises(InvalidExpressionError):
            parse_expression(text)

    def test_unknown_function_rejected(self):
        with pytest.raises(InvalidExpressionError):
            parse_expression("foo(x)")

    @pytest.mark.parametrize(
        "text", ["csc(x)", "sec(x)", "cot(x)", "acsc(x)", "asec(x)", "acot(x)"]
    )
    def test_reserved_trig_functions_not_yet_whitelisted(self, text):
        # csc/sec/cot (and inverses) are cosmetic-only placeholders in the UI
        # for this phase; the parser must still reject them like any unknown
        # function rather than silently accepting them.
        with pytest.raises(InvalidExpressionError):
            parse_expression(text)

    def test_arbitrary_python_not_reachable(self):
        # controlled namespace: no access to __import__, open, etc.
        with pytest.raises(InvalidExpressionError):
            parse_expression("__import__('os')")


# ---------------------------------------------------------------------------
# Expression — invariants
# ---------------------------------------------------------------------------

class TestExpressionInvariants:
    @pytest.mark.parametrize(
        "a,b",
        [
            ("2x", "2*x"),
            ("x^2", "x**2"),
            ("sin x", "sin(x)"),
        ],
    )
    def test_equivalent_surface_syntax_parses_equal(self, a, b):
        assert sp.simplify(parse_expression(a) - parse_expression(b)) == 0

    def test_normalize_is_idempotent_on_result(self):
        # parsing an already-canonical string should reproduce the same expr
        e1 = parse_expression("2*x**2 + 3*x - 5")
        e2 = parse_expression("2x^2 + 3x - 5")
        assert sp.simplify(e1 - e2) == 0


class TestInverseTrigInvariants:
    @pytest.mark.parametrize(
        "value",
        [sp.Rational(1, 2), sp.Rational(-1, 2), sp.sqrt(2) / 2, 0, 1, -1],
    )
    def test_asin_sin_round_trip(self, value):
        expr = sp.sin(parse_expression(f"asin({value})"))
        assert sp.simplify(expr - value) == 0

    @pytest.mark.parametrize(
        "value",
        [sp.Rational(1, 2), sp.Rational(-1, 2), sp.sqrt(2) / 2, 0, 1, -1],
    )
    def test_acos_cos_round_trip(self, value):
        expr = sp.cos(parse_expression(f"acos({value})"))
        assert sp.simplify(expr - value) == 0

    @pytest.mark.parametrize("value", [0, 1, -1, sp.Rational(1, 2)])
    def test_atan_tan_round_trip(self, value):
        expr = sp.tan(parse_expression(f"atan({value})"))
        assert sp.simplify(expr - value) == 0

    def test_factorial_matches_sympy_directly(self):
        for n in range(6):
            assert parse_expression(f"factorial({n})") == sp.factorial(n)


# ---------------------------------------------------------------------------
# Equation
# ---------------------------------------------------------------------------

class TestEquation:
    def test_basic_equation_returns_eq(self):
        eq = parse_equation("x^2 + 3x - 5 = 0")
        assert isinstance(eq, sp.Eq)
        assert sp.simplify(eq.lhs - (x**2 + 3 * x - 5)) == 0
        assert eq.rhs == 0

    def test_equation_does_not_auto_evaluate(self):
        # Eq(2+2, 4) would collapse to `True` under default SymPy evaluation;
        # evaluate=False must prevent that.
        eq = parse_equation("2 + 2 = 4")
        assert isinstance(eq, sp.Eq)
        assert eq is not sp.S.true

    @pytest.mark.parametrize("text", ["", "   ", "x =", "= x", "=", "x = y = 2"])
    def test_invalid_equations(self, text):
        with pytest.raises(InvalidEquationError):
            parse_equation(text)

    def test_invalid_lhs_wraps_as_equation_error(self):
        with pytest.raises(InvalidEquationError):
            parse_equation("sin( = 0")

    def test_invalid_rhs_wraps_as_equation_error(self):
        with pytest.raises(InvalidEquationError):
            parse_equation("x = 2**")


# ---------------------------------------------------------------------------
# Matrix
# ---------------------------------------------------------------------------

class TestMatrix:
    def test_nested_form(self):
        m = parse_matrix("[[1,2],[3,4]]")
        assert m == sp.Matrix([[1, 2], [3, 4]])

    def test_matlab_style_no_brackets(self):
        m = parse_matrix("1,2;3,4")
        assert m == sp.Matrix([[1, 2], [3, 4]])

    def test_row_vector(self):
        m = parse_matrix("[1,2,3]")
        assert m == sp.Matrix([[1, 2, 3]])
        assert m.shape == (1, 3)

    def test_column_vector(self):
        m = parse_matrix("[1;2;3]")
        assert m == sp.Matrix([[1], [2], [3]])
        assert m.shape == (3, 1)

    def test_symbolic_entries(self):
        m = parse_matrix("[[E,2],[3,x]]")
        assert m[0, 0] == sp.E
        assert m[1, 1] == x

    def test_symbolic_trig_entries(self):
        m = parse_matrix("[[sin(theta),0],[0,cos(theta)]]")
        theta = sp.Symbol("theta")
        assert m[0, 0] == sp.sin(theta)
        assert m[1, 1] == sp.cos(theta)

    @pytest.mark.parametrize("text", ["", "[]", "[[]]"])
    def test_empty_matrix_invalid(self, text):
        with pytest.raises(InvalidMatrixError):
            parse_matrix(text)

    def test_ragged_rows_invalid(self):
        with pytest.raises(InvalidMatrixError):
            parse_matrix("[[1,2],[3]]")

    def test_empty_entry_invalid(self):
        with pytest.raises(InvalidMatrixError):
            parse_matrix("[[1,],[3,4]]")

    def test_invalid_cell_expression_invalid(self):
        with pytest.raises(InvalidMatrixError):
            parse_matrix("[[1,foo(x)],[3,4]]")


class TestMatrixFromGrid:
    def test_basic_grid(self):
        m = matrix_from_grid([["1", "2"], ["3", "4"]])
        assert m == sp.Matrix([[1, 2], [3, 4]])

    def test_symbolic_entries(self):
        m = matrix_from_grid([["E", "2"], ["3", "x"]])
        assert m[0, 0] == sp.E
        assert m[1, 1] == x

    def test_parity_with_parse_matrix(self):
        # The two input paths (bracket-text vs grid) must agree exactly,
        # since matrix_from_grid() funnels through the same validation core.
        from_text = parse_matrix("[[1,2],[3,4]]")
        from_grid = matrix_from_grid([["1", "2"], ["3", "4"]])
        assert from_text == from_grid

    def test_empty_entry_invalid(self):
        with pytest.raises(InvalidMatrixError):
            matrix_from_grid([["1", ""], ["3", "4"]])

    def test_whitespace_only_entry_invalid(self):
        with pytest.raises(InvalidMatrixError):
            matrix_from_grid([["1", "   "], ["3", "4"]])

    def test_invalid_cell_expression_invalid(self):
        with pytest.raises(InvalidMatrixError):
            matrix_from_grid([["1", "foo(x)"], ["3", "4"]])

    def test_empty_grid_invalid(self):
        with pytest.raises(InvalidMatrixError):
            matrix_from_grid([])

    def test_row_vector_from_grid(self):
        m = matrix_from_grid([["1", "2", "3"]])
        assert m.shape == (1, 3)

    def test_column_vector_from_grid(self):
        m = matrix_from_grid([["1"], ["2"], ["3"]])
        assert m.shape == (3, 1)


# ---------------------------------------------------------------------------
# detect_type
# ---------------------------------------------------------------------------

class TestDetectType:
    @pytest.mark.parametrize(
        "text,expected",
        [
            ("2x^2 + 3x - 5", "expression"),
            ("x^2 + 3x - 5 = 0", "equation"),
            ("[[1,2],[3,4]]", "matrix"),
            ("1,2;3,4", "matrix"),
        ],
    )
    def test_detect(self, text, expected):
        assert detect_type(text) == expected


# ---------------------------------------------------------------------------
# get_symbols
# ---------------------------------------------------------------------------

class TestGetSymbols:
    def test_deterministic_alphabetical_order(self):
        expr = parse_expression("3*y + 2*x")
        assert get_symbols(expr) == [x, y]

    def test_single_variable(self):
        eq = parse_equation("x^2 + 3x - 5 = 0")
        assert get_symbols(eq) == [x]

    def test_multi_variable_equation(self):
        eq = parse_equation("x + y = 5")
        assert get_symbols(eq) == [x, y]

    def test_matrix_symbols(self):
        m = parse_matrix("[[E,2],[3,x]]")
        assert get_symbols(m) == [x]
