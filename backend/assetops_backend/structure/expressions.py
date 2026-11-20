"""3B1: the structure expression language (spec §3; D-3B1.2, D-3B1.8; R2, R3, R8, R16).

`Expr` is the contract `3B3` evaluates: five frozen node types with fixed arities.
`parse` reads an expression text into `Expr`; `unit_of` composes its unit under the
literal rule. There is no evaluation here, and no binary fraction anywhere: a numeric literal
is a `Decimal` built from its own source text.
"""

from __future__ import annotations

import ast
import re
from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal
from typing import Union

from assetops_contracts.canonical.units import ONE, Unit

OPERATORS = ("+", "-", "*", "/")
FUNCTIONS = ("min", "max", "ceil", "floor")
_UNARY_FUNCTIONS = ("ceil", "floor")  # exactly 1 argument; min and max take at least 2
_NUMBER = re.compile(r"[0-9]+(\.[0-9]+)?", re.ASCII)
_BINARY = {ast.Add: "+", ast.Sub: "-", ast.Mult: "*", ast.Div: "/"}


class ExpressionError(ValueError):
    """An expression text outside the language. Not a `StructureError`; `check` maps it (R8)."""

    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


class UnitError(ValueError):
    """The operands of `+`, `-`, `min` or `max` have unequal units."""


@dataclass(frozen=True)
class Num:
    value: Decimal


@dataclass(frozen=True)
class Ref:
    name: str


@dataclass(frozen=True)
class Bin:
    op: str
    left: "Expr"
    right: "Expr"


@dataclass(frozen=True)
class Neg:
    operand: "Expr"


@dataclass(frozen=True)
class Call:
    func: str
    args: tuple["Expr", ...]


Expr = Union[Num, Ref, Bin, Neg, Call]


def parse(text: str) -> Expr:
    """The `Expr` of `text`; any form outside spec §3 raises `ExpressionError`."""
    if not isinstance(text, str):
        raise ExpressionError("expression is not text")
    try:
        tree = ast.parse(text, mode="eval")
    except SyntaxError as error:
        raise ExpressionError(f"syntax: {error.msg}") from error
    return _node(tree.body, text)


def _node(node: ast.AST, text: str) -> Expr:
    if isinstance(node, ast.BinOp):
        op = _BINARY.get(type(node.op))
        if op is None:
            raise ExpressionError(f"operator {type(node.op).__name__}")
        return Bin(op, _node(node.left, text), _node(node.right, text))
    if isinstance(node, ast.UnaryOp):
        if not isinstance(node.op, ast.USub):
            raise ExpressionError(f"unary {type(node.op).__name__}")
        return Neg(_node(node.operand, text))
    if isinstance(node, ast.Name):
        return Ref(node.id)
    if isinstance(node, ast.Constant):
        # Only the source text decides: strings, bytes, booleans, None, complex numbers,
        # exponents, hex and underscores all fail the pattern (R2).
        segment = ast.get_source_segment(text, node)
        if segment is None or _NUMBER.fullmatch(segment) is None:
            raise ExpressionError(f"numeric literal {segment!r}")
        return Num(Decimal(segment))
    if isinstance(node, ast.Call):
        if not isinstance(node.func, ast.Name) or node.func.id not in FUNCTIONS:
            raise ExpressionError("unknown function")
        if node.keywords:
            raise ExpressionError("keyword arguments")
        func = node.func.id
        args = tuple(_node(arg, text) for arg in node.args)
        if func in _UNARY_FUNCTIONS and len(args) != 1:
            raise ExpressionError(f"{func} takes 1 argument")
        if func not in _UNARY_FUNCTIONS and len(args) < 2:
            raise ExpressionError(f"{func} takes at least 2 arguments")
        return Call(func, args)
    raise ExpressionError(f"form {type(node).__name__}")


def names(expr: Expr) -> tuple[str, ...]:
    """The distinct factor names in `expr`, in first-seen order; function names excluded (R3)."""
    seen: dict[str, None] = {}

    def walk(e: Expr) -> None:
        if isinstance(e, Ref):
            seen.setdefault(e.name, None)
        elif isinstance(e, Bin):
            walk(e.left)
            walk(e.right)
        elif isinstance(e, Neg):
            walk(e.operand)
        elif isinstance(e, Call):
            for arg in e.args:
                walk(arg)

    walk(expr)
    return tuple(seen)


def unit_of(expr: Expr, units: Mapping[str, Unit]) -> Unit:
    """The composed unit of `expr` from the given units of its names (the literal rule, D-3B1.2, R16).

    A literal-only subtree is unit-free: in `+`, `-`, `min` and `max` it takes the unit of
    the other operands, and it is `ONE` in `*`, `/` or at the top.
    """
    unit = _unit(expr, units)
    return ONE if unit is None else unit


def _same(operands: list[Unit | None], where: str) -> Unit | None:
    found = [u for u in operands if u is not None]
    if any(u != found[0] for u in found[1:]):
        raise UnitError(f"{where}: {', '.join(str(u) for u in found)}")
    return found[0] if found else None


def _unit(expr: Expr, units: Mapping[str, Unit]) -> Unit | None:
    if isinstance(expr, Num):
        return None
    if isinstance(expr, Ref):
        return units[expr.name]
    if isinstance(expr, Neg):
        return _unit(expr.operand, units)
    if isinstance(expr, Bin):
        left, right = _unit(expr.left, units), _unit(expr.right, units)
        if expr.op in ("+", "-"):
            return _same([left, right], expr.op)
        if left is None and right is None:
            return None
        left = ONE if left is None else left
        right = ONE if right is None else right
        return left * right if expr.op == "*" else left / right
    if isinstance(expr, Call):
        operands = [_unit(arg, units) for arg in expr.args]
        if expr.func in _UNARY_FUNCTIONS:
            return operands[0]
        return _same(operands, expr.func)
    raise UnitError(f"not an expression: {expr!r}")
