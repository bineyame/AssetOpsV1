"""SC-1 (spec section 3.1; D-SC1.2, D-SC1.18, D-SC1.19): typed facts, the only params a structured statement takes.

A fact is one typed value taken from the computed structure. Its constructor refuses a value that cannot be true
(`TypeError` for a wrong class, `ValueError` for a wrong value), so an impossible fact cannot be built. Facts are
immutable `__slots__` classes with value equality, not dataclasses: no generic encoder can walk them, and they leave
`i18n` only rendered or through `i18n.wire`.

A fact's fields are its constructor's parameter names (the metaclass reads them), so the field names are code
identifiers, never strings: the mechanism scope holds no string outside `schema.py` (D-SC1.17).
"""
from __future__ import annotations

import datetime
import string
import unicodedata
from decimal import Decimal

from assetops_backend.i18n import schema

_UPPER = frozenset(string.ascii_uppercase)


class _FactMeta(type):
    def __new__(mcls, name, bases, namespace):
        init = namespace.get("__init__")
        code = getattr(init, "__code__", None)
        namespace["__slots__"] = () if code is None else code.co_varnames[1:code.co_argcount]
        return super().__new__(mcls, name, bases, namespace)


class Fact(metaclass=_FactMeta):
    """Immutable, value-equal, hashable; the fields are `type(self).__slots__`, in constructor order."""

    #: The integer paths a condition may read (`x.k`, `x.count`); none by default.
    _paths: tuple = ()

    def _set(self, *values) -> None:
        for field, value in zip(type(self).__slots__, values):
            object.__setattr__(self, field, value)

    def _values(self) -> tuple:
        return tuple(getattr(self, f) for f in type(self).__slots__)

    def __setattr__(self, name, value):
        raise AttributeError(name)

    def __delattr__(self, name):
        raise AttributeError(name)

    def __eq__(self, other):
        return type(other) is type(self) and other._values() == self._values()

    def __hash__(self):
        return hash((type(self), self._values()))

    def __repr__(self):
        return f"{type(self).__name__}({', '.join(repr(v) for v in self._values())})"


def _str(value, *, empty: bool = False) -> str:
    if not isinstance(value, str):
        raise TypeError(value)
    if not value and not empty:
        raise ValueError(value)
    return value


def _int(value) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(value)
    return value


def _decimal(value) -> Decimal:
    if not isinstance(value, Decimal):
        raise TypeError(value)
    if not value.is_finite():
        raise ValueError(value)
    return value


def is_upper_snake(value: str) -> bool:
    return (isinstance(value, str) and value.isascii() and value.isidentifier() and value[:1] in _UPPER
            and value == value.upper())


def is_lower_snake(value: str) -> bool:
    return (isinstance(value, str) and value.isascii() and value.isidentifier() and value[:1].isalpha()
            and value == value.lower() and not any(c.isdigit() for c in value))


def _code(value) -> str:
    if not is_upper_snake(_str(value)):
        raise ValueError(value)
    return value


class Evidence(Fact):
    """A figure's evidence class, its weakest origin (the caller computes it) and 3A7's standing (None: none applies).
    Never a message param: it is a field of a figure."""

    def __init__(self, evidence, origin=None, reconciled=None):
        if _str(evidence) not in schema.EVIDENCES:
            raise ValueError(evidence)
        if origin is not None and _str(origin) not in schema.ORIGINS:
            raise ValueError(origin)
        if reconciled is not None and not isinstance(reconciled, bool):
            raise TypeError(reconciled)
        self._set(evidence, origin, reconciled)


def _evidence(value, *, standing: bool) -> Evidence:
    if not isinstance(value, Evidence):
        raise TypeError(value)
    if not standing and value.reconciled is not None:
        raise ValueError(value)
    return value


def _currency(value) -> str:
    if not (len(_str(value)) == 3 and value.isascii() and value.isalpha() and value.isupper()):
        raise ValueError(value)
    return value


class Money(Fact):
    def __init__(self, value, currency, evidence):
        self._set(_decimal(value), _currency(currency), _evidence(evidence, standing=True))

    @property
    def exact(self) -> Decimal:
        return self.value


class Price(Fact):
    def __init__(self, value, currency, unit, evidence):
        self._set(_decimal(value), _currency(currency), _str(unit), _evidence(evidence, standing=False))

    @property
    def exact(self) -> Decimal:
        return self.value


class Quantity(Fact):
    def __init__(self, value, unit, evidence):
        self._set(_decimal(value), _str(unit), _evidence(evidence, standing=False))

    @property
    def exact(self) -> Decimal:
        return self.value


class Percent(Fact):
    """A fraction: `Decimal("0.0101")` is 1.01%."""

    def __init__(self, value, evidence):
        self._set(_decimal(value), _evidence(evidence, standing=False))

    @property
    def exact(self) -> Decimal:
        return self.value


class Count(Fact):
    def __init__(self, n, noun):
        if _int(n) < 0:
            raise ValueError(n)
        self._set(n, _str(noun))

    @property
    def exact(self) -> int:
        return self.n


class KOfN(Fact):
    def __init__(self, k, n, noun):
        if not 0 <= _int(k) <= _int(n) or n < 1:
            raise ValueError((k, n))
        self._set(k, n, _str(noun))


KOfN._paths = KOfN.__slots__[:2]


class Month(Fact):
    def __init__(self, year, month):
        if not datetime.MINYEAR <= _int(year) <= datetime.MAXYEAR or not 1 <= _int(month) <= 12:
            raise ValueError((year, month))
        self._set(year, month)


class Day(Fact):
    def __init__(self, day):
        if isinstance(day, datetime.datetime) or not isinstance(day, datetime.date):
            raise TypeError(day)
        self._set(day)


class Instant(Fact):
    def __init__(self, at):
        if not isinstance(at, datetime.datetime):
            raise TypeError(at)
        if at.utcoffset() is None:
            raise ValueError(at)
        self._set(at)


class Word(Fact):
    """A vocabulary entry; whether the vocabulary and key exist is checked at render (the vocabulary is per locale)."""

    def __init__(self, vocabulary, key):
        self._set(_str(vocabulary), _str(key))


class Name(Fact):
    """Text copied verbatim from a record, with the record field it came from (`site.code`, `action.title`)."""

    def __init__(self, text, source):
        text = _str(text)
        if any(unicodedata.category(c).upper() == "CC" for c in text):
            raise ValueError(text)
        self._set(text, _str(source))


class State(Fact):
    """A computed state (upper snake case); never printed, read by conditions and picks."""

    def __init__(self, value):
        self._set(_code(value))


class Flag(Fact):
    def __init__(self, value):
        if not isinstance(value, bool):
            raise TypeError(value)
        self._set(value)


class Absent(Fact):
    """An explicit absence with its reason (upper snake case). A missing figure is `Absent`, never None or zero."""

    def __init__(self, reason):
        self._set(_code(reason))


class Items(Fact):
    """One fact class throughout, at least one item, no repeats, no `Absent` (no items is `Absent`)."""

    def __init__(self, items):
        if not isinstance(items, tuple):
            raise TypeError(items)
        if not items:
            raise ValueError(items)
        first = type(items[0])
        if any(type(i) is not first for i in items) or first in (Absent, Evidence) or not issubclass(first, Fact):
            raise TypeError(items)
        if len(set(items)) != len(items):
            raise ValueError(items)
        self._set(items)

    @property
    def count(self) -> int:
        return len(self.items)


Items._paths = (Items.count.fget.__name__,)

#: Figures: the facts that carry evidence.
FIGURES = (Money, Price, Quantity, Percent)
#: The fact class each fact-taking slot type takes (`items`'s items follow its `of`).
BY_TYPE = {"money": Money, "price": Price, "quantity": Quantity, "percent": Percent, "count": Count, "k_of_n": KOfN,
           "month": Month, "day": Day, "instant": Instant, "word": Word, "name": Name, "items": Items, "state": State,
           "flag": Flag}
