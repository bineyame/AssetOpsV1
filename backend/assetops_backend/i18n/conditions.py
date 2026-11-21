"""SC-1 (spec section 3.4, section 3.7.1; D-SC1.5, D-SC1.20, D-SC1.23): the one condition evaluator.

A condition is data: a dict with one operator key, dispatched by `OPERATORS` (never by comparing a string). `holds`
is the render-time evaluation over the message's facts (an omitted optional fact is `Absent("OMITTED")`);
`kleene` is the load-time three-valued evaluation over the same operator table, with one slot fixed to one value and
every other atom unknown (`None`), which `PICK_REACH` uses. The load check has proved every condition well formed.
"""
from __future__ import annotations

import operator
from decimal import Decimal
from typing import TypedDict

from assetops_backend.i18n import schema
from assetops_backend.i18n.facts import FIGURES, Absent, Fact, Flag, Money, Quantity, State

_COMPARE = dict(zip(schema.COMPARATORS, (operator.lt, operator.le, operator.eq, operator.ge, operator.gt)))
_SIGN = dict(zip((-1, 0, 1), schema.SIGNS))


class _Operand(TypedDict):
    """Section 3.4's operand keys, read as identifiers: the mechanism holds no string outside `schema.py`
    (D-SC1.17; `mid-build-questions.md` Q2)."""

    abs: object
    const: object


ABS, CONST = _Operand.__annotations__


class ConditionTypeError(TypeError):
    """Two operands that cannot be compared (render reports it as `CONDITION_TYPE`)."""


def sign_of(value) -> str:
    return _SIGN[(value > 0) - (value < 0)]


def split_path(path: str) -> tuple[str, str | None]:
    base, _, suffix = path.partition(".")
    return base, suffix or None


def operand_slot(operand) -> str | None:
    """The slot an operand reads (None for a const)."""
    if isinstance(operand, str):
        return split_path(operand)[0]
    if isinstance(operand, dict) and len(operand) == 1 and ABS in operand:
        return operand_slot(operand[ABS])
    return None


def const_value(raw):
    return raw if isinstance(raw, int) else Decimal(raw)


# --- render time -----------------------------------------------------------------------------------------------


class _Absent:
    """An operand read from an `Absent` fact: every comparison over it is false."""


def _value(operand, facts):
    """(value, kind) of an operand; kind is `int`, a figure's (class, currency, unit), or None for a const."""
    if isinstance(operand, str):
        base, suffix = split_path(operand)
        fact = facts[base]
        if isinstance(fact, Absent):
            return _Absent, None
        if suffix is not None:
            return getattr(fact, suffix), int
        if isinstance(fact, FIGURES):
            return fact.exact, (type(fact), getattr(fact, _CURRENCY, None), getattr(fact, _UNIT, None))
        return fact.exact, int
    if ABS in operand:
        value, kind = _value(operand[ABS], facts)
        return (value if value is _Absent else abs(value)), kind
    return const_value(operand[CONST]), None


#: Field names read through the fact classes' own slots (no string constant: D-SC1.17).
_CURRENCY = Money.__slots__[1]
_UNIT = Quantity.__slots__[1]


def _cmp(args, facts) -> bool:
    left, comparator, right = args
    (lv, lk), (rv, rk) = _value(left, facts), _value(right, facts)
    if lv is _Absent or rv is _Absent:
        return False
    if lk is not None and rk is not None and lk != rk:
        raise ConditionTypeError(args)
    if lk is None and rk is None:
        raise ConditionTypeError(args)
    return _COMPARE[comparator](lv, rv)


def _present(slot, facts) -> bool:
    return not isinstance(facts[slot], Absent)


def _is(args, facts) -> bool:
    slot, value = args
    fact = facts[slot]
    return isinstance(fact, (State, Flag)) and fact.value == value and type(fact.value) is type(value)


def _sign(args, facts) -> bool:
    slot, word = args
    fact = facts[slot]
    return isinstance(fact, FIGURES) and sign_of(fact.exact) == word


def _reason(args, facts) -> bool:
    slot, code = args
    fact = facts[slot]
    return isinstance(fact, Absent) and fact.reason == code


_HOLDS = {
    "present": _present,
    "absent": lambda slot, facts: not _present(slot, facts),
    "reason": _reason,
    "is": _is,
    "sign": _sign,
    "cmp": _cmp,
    "all": lambda conds, facts: all(holds(c, facts) for c in conds),
    "any": lambda conds, facts: any(holds(c, facts) for c in conds),
    "not": lambda cond, facts: not holds(cond, facts),
}


def holds(cond: dict, facts: dict[str, Fact]) -> bool:
    """Whether `cond` holds over `facts` (every slot the statement tree declares that takes a fact is present, an
    omitted optional one as `Absent("OMITTED")`). Raises `ConditionTypeError` for incomparable operands."""
    (op, args), = cond.items()
    return _HOLDS[op](args, facts)


# --- load time: three-valued (Kleene) evaluation for PICK_REACH -------------------------------------------------


def _k_and(values) -> bool | None:
    values = list(values)
    if False in values:
        return False
    return None if None in values else True


def _k_or(values) -> bool | None:
    values = list(values)
    if True in values:
        return True
    return None if None in values else False


def _k_not(value) -> bool | None:
    return None if value is None else not value


def _k_present(slot, x, v):
    return None if slot != x else v is not None


def _k_reason(args, x, v):
    return None if args[0] != x or v is None else False


def _k_is(args, x, v):
    return None if args[0] != x else (v is not None and v == args[1])


def _k_cmp(args, x, v):
    left, comparator, right = args
    for a, b, flip in ((left, right, False), (right, left, True)):
        if operand_slot(a) == x and isinstance(b, dict) and CONST in b and const_value(b[CONST]) == 0:
            if v is None:
                return False
            s = schema.SIGNS.index(v) - 1
            s = abs(s) if not isinstance(a, str) else s
            return _COMPARE[comparator](0, s) if flip else _COMPARE[comparator](s, 0)
    return None


_KLEENE = {
    "present": _k_present,
    "absent": lambda slot, x, v: _k_not(_k_present(slot, x, v)),
    "reason": _k_reason,
    "is": _k_is,
    "sign": _k_is,
    "cmp": _k_cmp,
    "all": lambda conds, x, v: _k_and(kleene(c, x, v) for c in conds),
    "any": lambda conds, x, v: _k_or(kleene(c, x, v) for c in conds),
    "not": lambda cond, x, v: _k_not(kleene(cond, x, v)),
}


def kleene(cond: dict | None, x: str, v: str | None) -> bool | None:
    """`cond` with slot `x` fixed to value `v` (a sign word or a state value; None for absent) and every atom not
    about `x` unknown (None). A missing condition (no `when`) is true."""
    if cond is None:
        return True
    (op, args), = cond.items()
    return _KLEENE[op](args, x, v)
