"""SC-1 (spec section 3.11; D-SC1.19): the lossless JSON form of a message holding facts.

`to_wire(msg)` and `from_wire(obj)` are exact inverses. `from_wire` is strict: an unknown fact name, a missing or
extra field, or a value of the wrong JSON type raises `WireError("WIRE_FORM", path)`; then the fact's own
constructor runs. A legacy `str`/`int`/`float` param stays itself. Field names are the fact classes' own fields and
the `Message`'s keys, read as identifiers (no string constant outside `schema.py`: D-SC1.17).
"""
from __future__ import annotations

import datetime
from decimal import Decimal, InvalidOperation
from typing import TypedDict

from assetops_backend.i18n.facts import (Absent, Count, Day, Evidence, Fact, Flag, Instant, Items, KOfN, Money,
                                         Month, Name, Percent, Price, Quantity, State, Word)
from assetops_backend.i18n.messages import Message

_KEY, _PARAMS = Message.__annotations__


class _Envelope(TypedDict):
    """The wire's own key for a fact's type name (section 3.11), read as an identifier."""

    fact: str


_FACT, = _Envelope.__annotations__


class WireError(ValueError):
    def __init__(self, code: str, path=None):
        super().__init__(code, path)
        self.code, self.path = code, path


def _fail(path):
    raise WireError("WIRE_FORM", path)


# One codec per field kind: (encode, decode). `decode` refuses a value of the wrong JSON type.


def _dec_decimal(value, path):
    if not isinstance(value, str):
        _fail(path)
    try:
        return Decimal(value)
    except InvalidOperation:
        _fail(path)


def _dec_str(value, path):
    return value if isinstance(value, str) else _fail(path)


def _dec_int(value, path):
    return value if isinstance(value, int) and not isinstance(value, bool) else _fail(path)


def _dec_bool(value, path):
    return value if isinstance(value, bool) else _fail(path)


def _nullable(decode):
    return lambda value, path: None if value is None else decode(value, path)


def _dec_day(value, path):
    try:
        return datetime.date.fromisoformat(_dec_str(value, path))
    except ValueError:
        _fail(path)


def _dec_instant(value, path):
    try:
        return datetime.datetime.fromisoformat(_dec_str(value, path))
    except ValueError:
        _fail(path)


def _same(value):
    return value


_DECIMAL = (str, _dec_decimal)
_STR = (_same, _dec_str)
_INT = (_same, _dec_int)
_BOOL = (_same, _dec_bool)
_EVIDENCE = (lambda e: _fields(e, _EVIDENCE_FIELDS), lambda v, p: _object(Evidence, _EVIDENCE_FIELDS, v, p))
_EVIDENCE_FIELDS = (_STR, (_same, _nullable(_dec_str)), (_same, _nullable(_dec_bool)))
_ITEMS = (lambda items: [_encode(i) for i in items],
          lambda v, p: tuple(_decode(i, (*p, n)) for n, i in enumerate(v)) if isinstance(v, list) else _fail(p))

#: Each fact class: its wire type name (section 3.3's) and one codec per field, in field order.
_CODECS = {
    Money: ("money", (_DECIMAL, _STR, _EVIDENCE)),
    Price: ("price", (_DECIMAL, _STR, _STR, _EVIDENCE)),
    Quantity: ("quantity", (_DECIMAL, _STR, _EVIDENCE)),
    Percent: ("percent", (_DECIMAL, _EVIDENCE)),
    Count: ("count", (_INT, _STR)),
    KOfN: ("k_of_n", (_INT, _INT, _STR)),
    Month: ("month", (_INT, _INT)),
    Day: ("day", ((datetime.date.isoformat, _dec_day),)),
    Instant: ("instant", ((datetime.datetime.isoformat, _dec_instant),)),
    Word: ("word", (_STR, _STR)),
    Name: ("name", (_STR, _STR)),
    State: ("state", (_STR,)),
    Flag: ("flag", (_BOOL,)),
    Items: ("items", (_ITEMS,)),
    Absent: ("absent", (_STR,)),
}
_BY_NAME = {name: (cls, codecs) for cls, (name, codecs) in _CODECS.items()}


def _fields(fact: Fact, codecs) -> dict:
    return {f: enc(getattr(fact, f)) for f, (enc, _) in zip(type(fact).__slots__, codecs)}


def _encode(fact: Fact) -> dict:
    name, codecs = _CODECS[type(fact)]
    return {_FACT: name, **_fields(fact, codecs)}


def _object(cls, codecs, value, path):
    if not isinstance(value, dict) or set(value) != set(cls.__slots__):
        _fail(path)
    return cls(*(dec(value[f], (*path, f)) for f, (_, dec) in zip(cls.__slots__, codecs)))


def _decode(value, path):
    if not isinstance(value, dict) or value.get(_FACT) not in _BY_NAME:
        _fail(path)
    cls, codecs = _BY_NAME[value[_FACT]]
    rest = {k: v for k, v in value.items() if k != _FACT}
    return _object(cls, codecs, rest, path)


def to_wire(msg: Message) -> dict:
    """The message as JSON-ready data; a fact becomes an object with its type name and fields."""
    params = msg[_PARAMS]
    return {_KEY: msg[_KEY], _PARAMS: {n: _encode(p) if isinstance(p, Fact) else p for n, p in params.items()}}


def from_wire(obj) -> Message:
    """The exact inverse of `to_wire`, strict (`WireError`), then each fact's own constructor."""
    if not isinstance(obj, dict) or set(obj) != {_KEY, _PARAMS} or not isinstance(obj[_KEY], str) \
            or not isinstance(obj[_PARAMS], dict):
        _fail(())
    params = {}
    for name, value in obj[_PARAMS].items():
        if isinstance(value, bool) or not isinstance(value, (str, int, float, dict)):
            _fail((name,))
        params[name] = _decode(value, (name,)) if isinstance(value, dict) else value
    return {_KEY: obj[_KEY], _PARAMS: params}
