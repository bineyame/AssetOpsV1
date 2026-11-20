"""Canonical record v1: the fourteen kinds, their batch, parsing and canonical bytes.

2a spec §6. Every record is one JSON object with a closed key set; every
refusal is a `CanonicalRefused` with a code from the closed list of §6.7 and a
dotted path (§6.8). The kinds' table (§6.4) is held as data in `KIND_SPECS`:
one generic parser reads it, so no kind has a branch of its own that could
drift from the table.

Values: decimals are JSON strings in plain notation (at most 32 characters,
adjusted exponent within [-12, 12]) and are written back as `format(d, "f")`,
which equals the accepted text (R2). Instants carry their own UTC offset and are
written as `isoformat()` of the parsed value; they are compared as moments and
never converted between zones (R12). Every pattern is ASCII and applied with
`re.fullmatch` (R5).

This is version 1 and a protected seam (D-2A.2): a change to what a valid
record is becomes version 2 beside this module, never an edit of it.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from types import MappingProxyType

from assetops_contracts.canonical.factors import FACTOR_ID_PATTERN, LEAF_FACTORS
from assetops_contracts.canonical.sources_v1 import SOURCE_TYPES
from assetops_contracts.canonical.units import BAND_UNITS, QUANTITY_UNITS

FORMAT_VERSION = 1
MAX_RECORDS = 10_000

PROVENANCES = frozenset({
    "demo-simulated", "source-emulated", "bench-tested", "field-integrated", "observed-financial",
})
SUBJECTS = ("CUSTOMER", "METER", "BATCH", "VEHICLE", "ASSET", "SITE")
CLOCK_KEYS = ("occurred_at", "effective_from", "effective_to", "recognition_period", "settled_at")
RECORD_KEYS = frozenset({
    "format_version", "kind", "source_record_id", "source_version", "site_code", "subject", "clocks",
    "amount", "quantity", "status", "body",
})
BATCH_KEYS = frozenset({
    "format_version", "tenant_code", "source_type", "source_system", "provenance", "produced_at", "records",
})

_A = re.ASCII
_DECIMAL = re.compile(r"-?(0|[1-9][0-9]*)(\.[0-9]+)?", _A)
_INSTANT = re.compile(
    r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(\.[0-9]{1,6})?(Z|[+-][0-9]{2}:[0-9]{2})", _A)
_DATE = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", _A)
_PERIOD = re.compile(r"[0-9]{4}-(0[1-9]|1[0-2])", _A)
_TIME = re.compile(r"([01][0-9]|2[0-3]):[0-5][0-9]", _A)
_CURRENCY = re.compile(r"[A-Z]{3}", _A)
_TENANT = re.compile(r"[a-z0-9][a-z0-9-]{0,62}", _A)
_SITE = re.compile(r"[A-Z0-9][A-Z0-9-]{0,63}", _A)
_SHA256 = re.compile(r"[0-9a-f]{64}", _A)
_SURROGATE = re.compile("[\ud800-\udfff]")
_REF_BANNED = re.compile("[\x00-\x1f\x7f-\x9f]")


class CanonicalRefused(Exception):
    """A refusal: `code` from spec §6.7 and a dotted `path` (§6.8)."""

    def __init__(self, code: str, path: str) -> None:
        super().__init__(code, path)
        self.code = code
        self.path = path

    def __str__(self) -> str:
        return f"{self.code} {self.path}"


def _fail(code: str, path: str):
    raise CanonicalRefused(code, path)


# --- The kinds' table as data (§6.4) ------------------------------------------------------


@dataclass(frozen=True)
class _When:
    """A presence ("R", "O" or "F") that depends on another value of the record.

    `source` is `body` (a body field's value), `status` (the record's status) or
    `present` (whether the body field `key` is present: `True` or `False`).
    """

    source: str
    key: str
    by_value: Mapping
    default: str


@dataclass(frozen=True)
class _Field:
    name: str
    type: str
    presence: object = "R"
    max_len: int = 200
    values: tuple = ()
    sign: str = "nonneg"
    upper: Decimal | None = None
    min_items: int = 0
    lo: int = 0
    hi: int = 0
    after: tuple | None = None  # (source "body"/"clocks", key, strict)


@dataclass(frozen=True)
class _Part:
    """`amount` or `quantity` of one kind."""

    presence: object = "F"
    sign: str = "nonneg"
    units: tuple = ()
    whole: bool = False
    units_by: _When | None = None


@dataclass(frozen=True)
class KindSpec:
    """One row of spec §6.4. `kind` and `store_family` are public; the rest is private."""

    kind: str
    store_family: str
    _clocks_required: tuple
    _clocks_optional: tuple
    _site: str
    _subject: tuple  # (presence, allowed subject kinds)
    _amount: _Part
    _quantity: _Part
    _status: tuple  # (presence, allowed values)
    _body: tuple
    _rules: tuple = ()


def _ref(name, presence="R", max_len=200):
    return _Field(name, "ref", presence, max_len=max_len)


def _enum(name, *values, presence="R"):
    return _Field(name, "enum", presence, values=values)


def _dec(name, presence="R", sign="nonneg", upper=None):
    return _Field(name, "decimal", presence, sign=sign, upper=upper)


_CR = "COMMERCIAL_RECORD"
_OR = "OPERATIONAL_RECORD"
_NO_PART = _Part()

_SPECS = (
    KindSpec(
        "CHARGE", _CR, ("effective_from", "effective_to", "recognition_period"), (), "R",
        ("O", ("CUSTOMER", "METER", "SITE")),
        _Part("R"),
        _Part(_When("body", "line_type",
                    {"USAGE": "R", "DEMAND": "R", "STORAGE": "R", "FIXED": "F"}, ""),
              units_by=_When("body", "line_type",
                             {"USAGE": ("kWh",), "DEMAND": ("kW",), "STORAGE": ("crate_day",)}, ())),
        ("F", ()),
        (_ref("account_ref"), _enum("line_type", "USAGE", "FIXED", "DEMAND", "STORAGE"), _ref("tariff_code"),
         _ref("band", "O", 40), _enum("tariff_class", "STANDARD", "PRODUCTIVE", presence="O")),
    ),
    KindSpec(
        "RECEIPT", _CR, ("occurred_at", "recognition_period"), (), "R",
        ("O", ("CUSTOMER",)),
        _Part("R", "positive"),
        _NO_PART,
        ("R", ("PAID_IN_TRANSIT", "COLLECTED")),
        (_ref("payer_ref"), _enum("method", "CASH", "MOBILE_MONEY", "BANK", "CARD", "OTHER"),
         _Field("applied_to", "refset", "O")),
    ),
    KindSpec(
        "SETTLEMENT", _CR, ("settled_at",), ("recognition_period",), "R",
        ("F", ()),
        _Part("R", "positive"),
        _NO_PART,
        ("F", ()),
        (_ref("provider"), _ref("batch_ref"), _Field("receipts", "refset", min_items=1)),
    ),
    KindSpec(
        "ADJUSTMENT", _CR, ("effective_from", "recognition_period"), (), "R",
        ("O", ("CUSTOMER", "METER", "SITE")),
        _Part("O", "any"),
        _Part("O", "any", ("kWh", "crate_day")),
        ("F", ()),
        (_ref("reason_code", max_len=40), _ref("authorised_by_ref"), _Field("applies_to", "refset", "O"),
         _ref("document_ref", "O")),
        ("amount_or_quantity",),
    ),
    KindSpec(
        "EXPENSE", _CR, ("occurred_at", "recognition_period"), (), "R",
        ("O", ("ASSET", "SITE")),
        _Part("R"),
        _Part(_When("body", "category", {"FUEL": "R"}, "F"), units=("L",)),
        ("R", ("QUOTE", "INVOICED", "PAID")),
        (_ref("counterparty_ref"),
         _enum("category", "FUEL", "OM", "STAFF", "REPAIR", "ENERGY", "PENALTY", "COLLECTION", "HANDLING"),
         _ref("document_ref")),
    ),
    KindSpec(
        "BUDGET_LINE", _CR, ("recognition_period",), (), "O",
        ("F", ()),
        _NO_PART,
        _NO_PART,
        ("F", ()),
        (_Field("factor_id", "factor_id"), _dec("value", sign="any"), _ref("version_ref"),
         _Field("currency", "currency", "O"), _ref("line_ref", "O")),
        ("budget_currency",),
    ),
    KindSpec(
        "STORAGE_MOVEMENT", _CR, ("occurred_at",), (), "R",
        ("R", ("BATCH",)),
        _NO_PART,
        _Part("R", "positive", ("crate",), whole=True),
        ("F", ()),
        (_ref("batch_ref"), _enum("direction", "IN", "OUT"), _ref("commodity"), _ref("customer_ref"),
         _dec("rate", "O"), _Field("currency", "currency", _When("present", "rate", {True: "R", False: "F"}, "F"))),
    ),
    KindSpec(
        "CUSTOMER_METER_READ", _CR, ("effective_from", "effective_to"), (), "R",
        ("R", ("METER",)),
        _NO_PART,
        _Part(_When("body", "read_type", {"INTERVAL": "R", "REGISTER": "F"}, ""), units=("kWh",)),
        ("F", ()),
        (_ref("meter_ref"), _enum("read_type", "INTERVAL", "REGISTER"),
         _dec("register_start", _When("body", "read_type", {"REGISTER": "R", "INTERVAL": "F"}, "O")),
         _Field("register_end", "decimal", _When("body", "read_type", {"REGISTER": "R", "INTERVAL": "F"}, "O"),
                after=("body", "register_start", False))),
    ),
    KindSpec(
        "METER_ASSIGNMENT", _CR, ("effective_from",), ("effective_to",), "R",
        ("R", ("METER",)),
        _NO_PART,
        _NO_PART,
        ("F", ()),
        (_ref("meter_ref"), _ref("customer_ref"), _ref("correction_reason", "O")),
    ),
    KindSpec(
        "FLEET_ROSTER", _CR, ("effective_from",), (), "R",
        ("R", ("VEHICLE",)),
        _NO_PART,
        _NO_PART,
        ("F", ()),
        (_ref("vehicle_ref"), _Field("return_at", "instant"),
         _Field("departure_at", "instant", after=("body", "return_at", True)),
         _dec("required_kwh", sign="positive"), _ref("tag_ref", "O"), _ref("block_ref", "O")),
    ),
    KindSpec(
        "DEPARTURE", _CR, ("occurred_at",), (), "R",
        ("R", ("VEHICLE",)),
        _NO_PART,
        _NO_PART,
        ("F", ()),
        (_ref("vehicle_ref"), _Field("service_day", "date"), _Field("block_met", "bool"),
         _dec("soc_pct", "O", upper=Decimal(100)), _dec("kwh_at_departure", "O"), _ref("block_ref", "O")),
    ),
    KindSpec(
        "TARIFF_SCHEDULE", _CR, ("effective_from",), ("effective_to",), "R",
        ("F", ()),
        _NO_PART,
        _NO_PART,
        ("F", ()),
        (_ref("contract_ref"), _Field("currency", "currency"), _Field("bands", "bands"), _dec("demand_rate", "O")),
        ("bands_overlap",),
    ),
    KindSpec(
        "SERVICE_TICKET", _OR, ("occurred_at",), (), "R",
        ("R", ("ASSET",)),
        _NO_PART,
        _NO_PART,
        ("R", ("OPEN", "ACKNOWLEDGED", "RESTORED", "CLOSED")),
        (_ref("asset_ref"), _ref("counterparty_ref"),
         _Field("acknowledged_at", "instant", "O", after=("clocks", "occurred_at", False)),
         _Field("restored_at", "instant", _When("status", "", {"RESTORED": "R"}, "O"),
                after=("clocks", "occurred_at", False))),
    ),
    KindSpec(
        "CONTRACT_DOCUMENT", _CR, ("effective_from",), ("effective_to",), "O",
        ("O", ("ASSET", "SITE")),
        _NO_PART,
        _NO_PART,
        ("R", ("SUBMITTED", "ACCEPTED", "REJECTED")),
        (_Field("document_sha256", "sha256"), _ref("counterparty_ref"),
         _enum("contract_type", "WARRANTY", "EPC", "OM_SLA", "INSURANCE", "STORAGE", "SERVICE", "SUPPLY"),
         _Field("pages", "int", lo=1, hi=10_000), _Field("parties", "refset", "O")),
    ),
)

KIND_SPECS: Mapping[str, KindSpec] = MappingProxyType({spec.kind: spec for spec in _SPECS})
KINDS = frozenset(KIND_SPECS)

_BAND_KEYS = frozenset({"band", "from", "to", "rate", "unit"})


# --- Parsed objects (§6.5) ----------------------------------------------------------------


@dataclass(frozen=True)
class CanonicalRecordV1:
    kind: str
    source_record_id: str
    source_version: str
    site_code: str | None
    subject: tuple[str, str] | None
    clocks: Mapping[str, str]
    amount: tuple[Decimal, str] | None
    quantity: tuple[Decimal, str] | None
    status: str | None
    body: Mapping[str, object]


@dataclass(frozen=True)
class CanonicalBatchV1:
    tenant_code: str
    source_type: str
    source_system: str
    provenance: str
    produced_at: str


@dataclass(frozen=True)
class BatchResult:
    batch: CanonicalBatchV1
    outcomes: tuple  # tuple[CanonicalRecordV1 | CanonicalRefused, ...], in input order


# --- Bytes in (§6.6, R7) ------------------------------------------------------------------


def _pairs(pairs):
    out = {}
    for key, value in pairs:
        if key in out:
            _fail("CANONICAL_DUPLICATE", f"json.{key}")
        out[key] = value
    return out


def _constant(name):
    _fail("CANONICAL_NUMBER", "json")


def loads_canonical(data: bytes) -> object:
    """The one public entry for raw bytes: UTF-8 JSON, no repeated key, no NaN or Infinity."""
    if not isinstance(data, (bytes, bytearray)):
        _fail("CANONICAL_TYPE", "json")
    try:
        text = bytes(data).decode("utf-8")
    except UnicodeDecodeError:
        _fail("CANONICAL_TYPE", "json")
    try:
        return json.loads(text, object_pairs_hook=_pairs, parse_constant=_constant)
    except CanonicalRefused:
        raise
    except (ValueError, RecursionError):
        _fail("CANONICAL_TYPE", "json")


# --- Value checks (§6.3) ------------------------------------------------------------------


def _string(value, path: str) -> str:
    if not isinstance(value, str):
        _fail("CANONICAL_TYPE", path)
    if _SURROGATE.search(value):
        _fail("CANONICAL_REF", path)
    return value


def _check_ref(value, path: str, max_len: int = 200) -> str:
    value = _string(value, path)
    if not 1 <= len(value) <= max_len or _REF_BANNED.search(value) or value != value.strip():
        _fail("CANONICAL_REF", path)
    return value


def _check_pattern(value, path: str, pattern: re.Pattern, code: str) -> str:
    value = _string(value, path)
    if pattern.fullmatch(value) is None:
        _fail(code, path)
    return value


def _check_enum(value, path: str, values) -> str:
    value = _string(value, path)
    if value not in values:
        _fail("CANONICAL_ENUM", path)
    return value


def _check_decimal(value, path: str, sign: str = "nonneg", whole: bool = False,
                   upper: Decimal | None = None) -> Decimal:
    if value is None:
        _fail("CANONICAL_TYPE", path)
    if not isinstance(value, str):
        _fail("CANONICAL_NUMBER", path)
    if _SURROGATE.search(value):
        _fail("CANONICAL_REF", path)
    if len(value) > 32 or _DECIMAL.fullmatch(value) is None:
        _fail("CANONICAL_NUMBER", path)
    try:
        number = Decimal(value)
    except InvalidOperation:
        _fail("CANONICAL_NUMBER", path)
    if value.startswith("-") and number == 0:
        _fail("CANONICAL_NUMBER", path)
    if not -12 <= number.adjusted() <= 12 or format(number, "f") != value:
        _fail("CANONICAL_NUMBER", path)
    if whole and number != number.to_integral_value():
        _fail("CANONICAL_NUMBER", path)
    if (sign == "nonneg" and number < 0) or (sign == "positive" and number <= 0):
        _fail("CANONICAL_SIGN", path)
    if upper is not None and number > upper:
        _fail("CANONICAL_RANGE", path)
    return number


def _check_instant(value, path: str) -> tuple[str, datetime]:
    value = _check_pattern(value, path, _INSTANT, "CANONICAL_CLOCK")
    try:
        moment = datetime.fromisoformat(value)
    except ValueError:
        _fail("CANONICAL_CLOCK", path)
    if moment.tzinfo is None:
        _fail("CANONICAL_CLOCK", path)
    return moment.isoformat(), moment


def _check_date(value, path: str) -> tuple[str, date]:
    value = _check_pattern(value, path, _DATE, "CANONICAL_CLOCK")
    try:
        return value, date.fromisoformat(value)
    except ValueError:
        _fail("CANONICAL_CLOCK", path)


def _check_time(value, path: str, allow_24: bool) -> int:
    value = _string(value, path)
    if allow_24 and value == "24:00":
        return 24 * 60
    if _TIME.fullmatch(value) is None:
        _fail("CANONICAL_CLOCK", path)
    return int(value[:2]) * 60 + int(value[3:])


def _check_object(value, path: str) -> dict:
    if not isinstance(value, dict):
        _fail("CANONICAL_TYPE", path)
    return value


def _check_keys(obj: dict, allowed, path: str) -> None:
    unknown = sorted(str(key) for key in obj if key not in allowed)
    if unknown:
        _fail("CANONICAL_FORBIDDEN", f"{path}.{unknown[0]}")


def _check_refset(value, path: str, min_items: int) -> tuple[str, ...]:
    if not isinstance(value, list):
        _fail("CANONICAL_TYPE", path)
    if len(value) < min_items:
        _fail("CANONICAL_RANGE", path)
    seen: set[str] = set()
    for index, item in enumerate(value):
        item = _check_ref(item, f"{path}[{index}]")
        if item in seen:
            _fail("CANONICAL_DUPLICATE", f"{path}[{index}]")
        seen.add(item)
    return tuple(sorted(seen))


# --- Record parsing (§6.6) ----------------------------------------------------------------


def _resolve(presence, record: dict, body: dict, status) -> str:
    """The presence ("R", "O", "F" or "" when undecidable) of a field."""
    if not isinstance(presence, _When):
        return presence
    if presence.source == "present":
        return presence.by_value.get(presence.key in body, presence.default)
    controlling = status if presence.source == "status" else body.get(presence.key)
    if not isinstance(controlling, str):
        return presence.default
    return presence.by_value.get(controlling, presence.default)


def _present(container: dict, key: str, presence: str, path: str) -> bool:
    if key not in container:
        if presence == "R":
            _fail("CANONICAL_FIELD", f"{path}.{key}")
        return False
    if presence == "F":
        _fail("CANONICAL_FORBIDDEN", f"{path}.{key}")
    if container[key] is None:
        _fail("CANONICAL_TYPE", f"{path}.{key}")
    return True


def _parse_clocks(spec: KindSpec, record: dict) -> tuple[dict[str, str], dict[str, object]]:
    _present(record, "clocks", "R", "record")
    clocks = _check_object(record["clocks"], "record.clocks")
    allowed = set(spec._clocks_required) | set(spec._clocks_optional)
    _check_keys(clocks, allowed, "record.clocks")
    texts: dict[str, str] = {}
    values: dict[str, object] = {}
    for key in CLOCK_KEYS:
        if key not in allowed:
            continue
        presence = "R" if key in spec._clocks_required else "O"
        path = f"record.clocks.{key}"
        if not _present(clocks, key, presence, "record.clocks"):
            continue
        if key in ("occurred_at", "settled_at"):
            texts[key], values[key] = _check_instant(clocks[key], path)
        elif key == "recognition_period":
            texts[key] = values[key] = _check_pattern(clocks[key], path, _PERIOD, "CANONICAL_CLOCK")
        else:
            texts[key], values[key] = _check_date(clocks[key], path)
    if "effective_to" in values and "effective_from" in values:
        if values["effective_to"] <= values["effective_from"]:
            _fail("CANONICAL_RANGE", "record.clocks.effective_to")
    return texts, values


def _parse_part(name: str, part: _Part, record: dict, body: dict) -> tuple[Decimal, str] | None:
    presence = _resolve(part.presence, record, body, None)
    path = f"record.{name}"
    if not _present(record, name, presence or "O", "record"):
        return None
    obj = _check_object(record[name], path)
    second = "currency" if name == "amount" else "unit"
    _check_keys(obj, {"value", second}, path)
    _present(obj, "value", "R", path)
    number = _check_decimal(obj["value"], f"{path}.value", part.sign, part.whole)
    _present(obj, second, "R", path)
    if name == "amount":
        currency = _check_pattern(obj["currency"], f"{path}.currency", _CURRENCY, "CANONICAL_CURRENCY")
        return number, currency
    unit = _string(obj["unit"], f"{path}.unit")
    if unit not in QUANTITY_UNITS:
        _fail("CANONICAL_UNIT", f"{path}.unit")
    allowed = part.units
    if part.units_by is not None:
        allowed = _resolve(part.units_by, record, body, None)
    if presence == "":
        # The controlling body value is absent or invalid: the body step refuses it.
        allowed = tuple(QUANTITY_UNITS)
    if unit not in allowed:
        _fail("CANONICAL_UNIT", f"{path}.unit")
    return number, unit


def _parse_bands(value, path: str, context: dict) -> tuple:
    if not isinstance(value, list):
        _fail("CANONICAL_TYPE", path)
    if not 1 <= len(value) <= 24:
        _fail("CANONICAL_RANGE", path)
    names: set[str] = set()
    parsed = []
    for index, raw in enumerate(value):
        here = f"{path}[{index}]"
        band = _check_object(raw, here)
        _check_keys(band, _BAND_KEYS, here)
        _present(band, "band", "R", here)
        name = _check_ref(band["band"], f"{here}.band", 40)
        if name in names:
            _fail("CANONICAL_DUPLICATE", f"{here}.band")
        names.add(name)
        _present(band, "from", "R", here)
        start = _check_time(band["from"], f"{here}.from", allow_24=False)
        _present(band, "to", "R", here)
        end = _check_time(band["to"], f"{here}.to", allow_24=True)
        if end <= start:
            _fail("CANONICAL_RANGE", f"{here}.to")
        _present(band, "rate", "R", here)
        rate = _check_decimal(band["rate"], f"{here}.rate")
        _present(band, "unit", "R", here)
        unit = _string(band["unit"], f"{here}.unit")
        if unit not in BAND_UNITS:
            _fail("CANONICAL_UNIT", f"{here}.unit")
        parsed.append((start, end, index, MappingProxyType(
            {"band": name, "from": band["from"], "to": band["to"], "rate": rate, "unit": unit})))
    parsed.sort(key=lambda item: item[0])
    context["bands"] = parsed
    return tuple(item[3] for item in parsed)


def _parse_field(field: _Field, value, path: str, context: dict):
    kind = field.type
    if kind == "ref":
        return _check_ref(value, path, field.max_len)
    if kind == "enum":
        return _check_enum(value, path, field.values)
    if kind == "refset":
        return _check_refset(value, path, field.min_items)
    if kind == "decimal":
        number = _check_decimal(value, path, field.sign, upper=field.upper)
        return number, number
    if kind == "instant":
        return _check_instant(value, path)
    if kind == "date":
        return _check_date(value, path)[0]
    if kind == "bool":
        if type(value) is not bool:
            _fail("CANONICAL_TYPE", path)
        return value
    if kind == "int":
        if type(value) is not int:
            _fail("CANONICAL_TYPE", path)
        if not field.lo <= value <= field.hi:
            _fail("CANONICAL_RANGE", path)
        return value
    if kind == "sha256":
        return _check_pattern(value, path, _SHA256, "CANONICAL_REF")
    if kind == "currency":
        return _check_pattern(value, path, _CURRENCY, "CANONICAL_CURRENCY")
    if kind == "factor_id":
        return _check_pattern(value, path, FACTOR_ID_PATTERN, "CANONICAL_FACTOR")
    if kind == "bands":
        return _parse_bands(value, path, context)
    raise AssertionError(kind)  # the table names only the types above


def _parse_body(spec: KindSpec, record: dict, status, clock_values: dict, context: dict) -> dict:
    _present(record, "body", "R", "record")
    body = _check_object(record["body"], "record.body")
    _check_keys(body, {field.name for field in spec._body}, "record.body")
    out: dict[str, object] = {}
    compare: dict[str, object] = {}
    for field in spec._body:
        path = f"record.body.{field.name}"
        presence = _resolve(field.presence, record, body, status) or "O"
        if not _present(body, field.name, presence, "record.body"):
            continue
        parsed = _parse_field(field, body[field.name], path, context)
        if field.type in ("decimal", "instant"):
            out[field.name], compare[field.name] = parsed
        else:
            out[field.name] = parsed
        if field.after is not None:
            source, key, strict = field.after
            other = (compare if source == "body" else clock_values).get(key)
            mine = compare[field.name]
            if other is not None and (mine < other or (strict and mine == other)):
                _fail("CANONICAL_RANGE", path)
    return out


def _cross_field(spec: KindSpec, amount, quantity, body: dict, context: dict) -> None:
    for rule in spec._rules:
        if rule == "amount_or_quantity" and amount is None and quantity is None:
            _fail("CANONICAL_FIELD", "record.amount")
        elif rule == "budget_currency":
            factor = LEAF_FACTORS.get(body["factor_id"])
            if factor is not None:
                needs = any(d == "MONEY" for d, _ in factor.unit.exponents)
                if needs != ("currency" in body):
                    _fail("CANONICAL_FACTOR", "record.body.currency")
        elif rule == "bands_overlap":
            bands = context["bands"]
            for previous, current in zip(bands, bands[1:]):
                if current[0] < previous[1]:
                    _fail("CANONICAL_RANGE", f"record.body.bands[{current[2]}].from")


def parse_record(obj: object) -> CanonicalRecordV1:
    """Validate one decoded record; raise the first `CanonicalRefused` in §6.6's order."""
    record = _check_object(obj, "record")
    version = record.get("format_version")
    if type(version) is not int or version != FORMAT_VERSION:
        _fail("CANONICAL_VERSION", "record.format_version")
    _present(record, "kind", "R", "record")
    kind = _string(record["kind"], "record.kind")
    if kind not in KIND_SPECS:
        _fail("CANONICAL_KIND", "record.kind")
    spec = KIND_SPECS[kind]
    _check_keys(record, RECORD_KEYS, "record")

    _present(record, "source_record_id", "R", "record")
    source_record_id = _check_ref(record["source_record_id"], "record.source_record_id")
    _present(record, "source_version", "R", "record")
    source_version = _check_ref(record["source_version"], "record.source_version", 64)

    site_code = None
    if _present(record, "site_code", spec._site, "record"):
        site_code = _check_pattern(record["site_code"], "record.site_code", _SITE, "CANONICAL_REF")

    subject = None
    if _present(record, "subject", spec._subject[0], "record"):
        raw = _check_object(record["subject"], "record.subject")
        _check_keys(raw, {"kind", "ref"}, "record.subject")
        _present(raw, "kind", "R", "record.subject")
        subject_kind = _check_enum(raw["kind"], "record.subject.kind", spec._subject[1])
        _present(raw, "ref", "R", "record.subject")
        subject = (subject_kind, _check_ref(raw["ref"], "record.subject.ref"))

    clocks, clock_values = _parse_clocks(spec, record)
    raw_body = record.get("body") if isinstance(record.get("body"), dict) else {}
    amount = _parse_part("amount", spec._amount, record, raw_body)
    quantity = _parse_part("quantity", spec._quantity, record, raw_body)

    status = None
    if _present(record, "status", spec._status[0], "record"):
        status = _check_enum(record["status"], "record.status", spec._status[1])

    context: dict = {}
    body = _parse_body(spec, record, status, clock_values, context)
    _cross_field(spec, amount, quantity, body, context)

    return CanonicalRecordV1(
        kind=kind,
        source_record_id=source_record_id,
        source_version=source_version,
        site_code=site_code,
        subject=subject,
        clocks=MappingProxyType(clocks),
        amount=amount,
        quantity=quantity,
        status=status,
        body=MappingProxyType(body),
    )


# --- Batch parsing ------------------------------------------------------------------------


def parse_batch(obj: object) -> BatchResult:
    """Validate a batch envelope and each record; a record's refusal is its own outcome.

    An envelope failure raises. Then, in order: each record is parsed; a record
    whose kind its source type does not emit is refused; among the records still
    valid, a second `(source_record_id, source_version)` is refused (R13).
    """
    batch = _check_object(obj, "batch")
    _check_keys(batch, BATCH_KEYS, "batch")
    version = batch.get("format_version")
    if type(version) is not int or version != FORMAT_VERSION:
        _fail("CANONICAL_VERSION", "batch.format_version")
    _present(batch, "tenant_code", "R", "batch")
    tenant_code = _check_pattern(batch["tenant_code"], "batch.tenant_code", _TENANT, "CANONICAL_REF")
    _present(batch, "source_type", "R", "batch")
    source_type = _string(batch["source_type"], "batch.source_type")
    if source_type not in SOURCE_TYPES:
        _fail("CANONICAL_SOURCE_TYPE", "batch.source_type")
    _present(batch, "source_system", "R", "batch")
    source_system = _check_ref(batch["source_system"], "batch.source_system")
    _present(batch, "provenance", "R", "batch")
    provenance = _string(batch["provenance"], "batch.provenance")
    if provenance not in PROVENANCES:
        _fail("CANONICAL_PROVENANCE", "batch.provenance")
    _present(batch, "produced_at", "R", "batch")
    produced_at = _check_instant(batch["produced_at"], "batch.produced_at")[0]
    _present(batch, "records", "R", "batch")
    records = batch["records"]
    if not isinstance(records, list):
        _fail("CANONICAL_TYPE", "batch.records")
    if len(records) > MAX_RECORDS:
        _fail("CANONICAL_RANGE", "batch.records")

    outcomes: list = []
    for raw in records:
        try:
            outcomes.append(parse_record(raw))
        except CanonicalRefused as refused:
            outcomes.append(refused)
    kinds = SOURCE_TYPES[source_type].kinds
    claimed: set[tuple[str, str]] = set()
    for index, outcome in enumerate(outcomes):
        if not isinstance(outcome, CanonicalRecordV1):
            continue
        if outcome.kind not in kinds:
            outcomes[index] = CanonicalRefused("CANONICAL_SOURCE_TYPE", "record.kind")
            continue
        key = (outcome.source_record_id, outcome.source_version)
        if key in claimed:
            outcomes[index] = CanonicalRefused("CANONICAL_DUPLICATE", "record.source_record_id")
            continue
        claimed.add(key)

    return BatchResult(
        batch=CanonicalBatchV1(tenant_code, source_type, source_system, provenance, produced_at),
        outcomes=tuple(outcomes),
    )


# --- Canonical bytes and digests (§6.6, R8) -----------------------------------------------


def _plain(value):
    if isinstance(value, Decimal):
        return format(value, "f")
    if isinstance(value, tuple):
        return [_plain(item) for item in value]
    if isinstance(value, Mapping):
        return {key: _plain(item) for key, item in value.items()}
    return value


def _record_object(record: CanonicalRecordV1) -> dict:
    out: dict[str, object] = {
        "format_version": FORMAT_VERSION,
        "kind": record.kind,
        "source_record_id": record.source_record_id,
        "source_version": record.source_version,
        "clocks": dict(record.clocks),
        "body": _plain(record.body),
    }
    if record.site_code is not None:
        out["site_code"] = record.site_code
    if record.subject is not None:
        out["subject"] = {"kind": record.subject[0], "ref": record.subject[1]}
    if record.amount is not None:
        out["amount"] = {"value": format(record.amount[0], "f"), "currency": record.amount[1]}
    if record.quantity is not None:
        out["quantity"] = {"value": format(record.quantity[0], "f"), "unit": record.quantity[1]}
    if record.status is not None:
        out["status"] = record.status
    return out


def to_canonical_json(x: CanonicalRecordV1 | BatchResult) -> bytes:
    """Canonical UTF-8 JSON: sorted keys, no spaces; a batch holds its valid records only."""
    if isinstance(x, CanonicalRecordV1):
        obj: object = _record_object(x)
    elif isinstance(x, BatchResult):
        obj = {
            "format_version": FORMAT_VERSION,
            "tenant_code": x.batch.tenant_code,
            "source_type": x.batch.source_type,
            "source_system": x.batch.source_system,
            "provenance": x.batch.provenance,
            "produced_at": x.batch.produced_at,
            "records": [_record_object(o) for o in x.outcomes if isinstance(o, CanonicalRecordV1)],
        }
    else:
        raise TypeError("to_canonical_json takes a CanonicalRecordV1 or a BatchResult")
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def record_digest(r: CanonicalRecordV1) -> str:
    """Lower-case hex SHA-256 of the record's canonical bytes."""
    return hashlib.sha256(to_canonical_json(r)).hexdigest()


def batch_digest(b: BatchResult) -> str:
    """Lower-case hex SHA-256 of the batch's canonical bytes: its valid records only."""
    return hashlib.sha256(to_canonical_json(b)).hexdigest()
