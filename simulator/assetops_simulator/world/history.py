"""The history rule engine (spec §4.6, §6).

Each history leaf is generated from October's value on the same side by a declared
rule; no leaf, node or total figure is typed in. Arithmetic is exact (`Fraction`),
each leaf is rounded once (half to even) to an integer unit, money to integer cents.
Totals and nodes are not generated here: the evaluator computes them.

Every refusal is `ValueError("<CODE> <scope_key> <leaf>")`. A refusal found before
any scope (the months, the money leaves, an override for an unknown Site, a
malformed family) uses `history` or the override's key in the scope position.
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from fractions import Fraction

from . import GENERATOR
from .allocate import allocate
from .leaves import MONEY_LEAVES, is_money
from .months import dates_of, day_class, days_in, next_month, parse_month, period_end
from .scope import PHYSICAL_READS, RUN_WRITTEN, SIDES, merged_rules, physical_read, scope_digest, scope_input, scope_key, seed, unit_interval
from .view import ManifestView, view_digest

SCHEMA = "assetops.history/1"

#: rule word -> token count, the word included
ARITY = {
    "per_day": 1, "fixed": 1, "plan_value": 1, "zero": 1, "fleet_kwh": 1, "fleet_nights": 1,
    "scale": 2, "ratio": 2, "rest": 3, "sum": 3, "occupancy": 4,
    "trend": 5, "level": 5, "cold_kwh": 5, "share": 5,
}
#: rules whose second token is a family
FAMILY_RULES = frozenset({"scale", "trend", "level", "cold_kwh"})
#: rules ending in a Jul/Aug/Sep list; those in ANCHORABLE also take `anchor`
LIST_RULES = frozenset({"trend", "level", "occupancy", "cold_kwh", "share"})
ANCHORABLE = frozenset({"occupancy", "cold_kwh", "share"})
ANCHOR = "anchor"

#: D-DD.176: per vertical, the history keys (either side) computed from a `scope.RUN_WRITTEN` value, so they move with
#: October's run-written leaves through the rule the spec declares (`scale`/`trend`/`level` read `october(side, leaf)`;
#: `cold_kwh` reads October's kwh; EV's metered leaves are October × weight). Listed from the code and proved by
#: `test_scope_run_written.py`: changing a run-written October key moves only these paths. Generate 1 to 2 may move
#: only these values and `meta.view_digest`; generates 2 and 3 are byte-identical.
RUN_DERIVED: dict[str, tuple[str, ...]] = {
    "MINI_GRID": ("necessary_l", "candidate_l"),
    "COLD_CHAIN": ("kwh",),
    "EV_DEPOT": ("peak_kwh", "offpeak_kwh", "kwh_2200_2400", "kwh_0000_0500", "max_kw"),
}

#: D-DD.176: per vertical, the history `actual`/`plan` keys a writer reads: `telemetry.books_for` (delivered kWh and
#: unexplained litres) and `telemetry_cold.cold_books_for` (its ledger, built by `exports_cold`: crate days,
#: outstanding, revenue, received). EV's writer reads no history block. Proved by `test_scope_run_written.py`.
WRITER_READS: dict[str, tuple[str, ...]] = {
    "MINI_GRID": ("delivered_kwh", "unexplained_l"),
    "COLD_CHAIN": ("crate_days", "outstanding", "revenue", "received"),
    "EV_DEPOT": (),
}


def _run_derived_is_never_read_back() -> None:
    """A derived key that a writer or a physical rule reads would be D-DD.164's loop again: refused at import."""
    physical = {k for keys in PHYSICAL_READS.values() for k in keys} | set(PHYSICAL_READS)
    for vertical, derived in RUN_DERIVED.items():
        if vertical not in RUN_WRITTEN:
            raise ValueError(f"RUN_DERIVED_VERTICAL {vertical}")
        for key in derived:
            if key in physical or key in WRITER_READS.get(vertical, ()):
                raise ValueError(f"RUN_DERIVED_READ_BACK {vertical} {key}")


_run_derived_is_never_read_back()


def _refuse(code: str, key: str, leaf: str) -> ValueError:
    return ValueError(f"{code} {key} {leaf}")


def _number(text, key: str, field: str) -> Fraction:
    """A view number (int, or decimal text) as an exact rational.

    Anything else (not a decimal, not finite, text over 32 characters, or an
    adjusted exponent outside [-12, 12]) is `HISTORY_NUMBER`, before any Fraction.
    """
    if isinstance(text, bool) or not isinstance(text, (int, str)):
        raise _refuse("HISTORY_NUMBER", key, field)
    try:
        decimal = Decimal(str(text))
    except InvalidOperation:
        raise _refuse("HISTORY_NUMBER", key, field) from None
    if not decimal.is_finite() or len(str(text)) > 32 or not -12 <= decimal.adjusted() <= 12:
        raise _refuse("HISTORY_NUMBER", key, field)
    return Fraction(decimal)


def _round_half_even(value: Fraction) -> int:
    whole, rest = divmod(value.numerator, value.denominator)
    remainder = Fraction(rest, value.denominator)
    if remainder > Fraction(1, 2) or (remainder == Fraction(1, 2) and whole % 2 == 1):
        whole += 1
    return whole


# ---- validation of the history block ------------------------------------------------


REQUIRED_FIELDS = (
    "version", "months", "anchor_period", "shape_source", "money_leaves", "label",
    "missing_cause", "seasons", "day_classes", "families", "rules",
)


def _validate_fields(history: dict) -> None:
    for name in REQUIRED_FIELDS:
        if name not in history:
            raise _refuse("HISTORY_FIELD", "history", name)


def _validate_months(history: dict) -> list[str]:
    months = history["months"]
    # the three-value lists are read by position over exactly three months (review L3)
    if not isinstance(months, dict) or len(months) != 3:
        raise _refuse("HISTORY_MONTHS", "history", "months")
    ordered = sorted(months)
    for i, month in enumerate(ordered):
        try:
            parse_month(month)
            calendar_days = days_in(month)
        except ValueError:
            raise _refuse("HISTORY_MONTHS", "history", month) from None
        if months[month] != calendar_days:
            raise _refuse("HISTORY_MONTHS", "history", month)
        if i and next_month(ordered[i - 1]) != month:
            raise _refuse("HISTORY_MONTHS", "history", month)
    anchor = history.get("anchor_period")
    if anchor in months or anchor != next_month(ordered[-1]):
        raise _refuse("HISTORY_MONTHS", "history", "anchor_period")
    seasons = history["seasons"]
    if not isinstance(seasons, dict):
        raise _refuse("HISTORY_MONTHS", "history", "seasons")
    for month in ordered + [anchor]:
        if month not in seasons:
            raise _refuse("HISTORY_MONTHS", "history", "seasons")
    classes = history["day_classes"]
    if not isinstance(classes, dict) or not all(isinstance(d, list) for d in classes.values()):
        raise _refuse("HISTORY_MONTHS", "history", "day_classes")
    weekdays = sorted(day for days in classes.values() for day in days if isinstance(day, int))
    if weekdays != [1, 2, 3, 4, 5, 6, 7]:
        raise _refuse("HISTORY_MONTHS", "history", "day_classes")
    return ordered


def _validate_families(history: dict) -> None:
    families = history["families"]
    if not isinstance(families, dict):
        raise _refuse("HISTORY_FAMILY_UNKNOWN", "history", "families")
    for name, family in sorted(families.items()):
        try:
            weights = [*family["season"].values(), *family["day"].values(), family["jitter"]]
        except (KeyError, TypeError, AttributeError):
            raise _refuse("HISTORY_FAMILY_UNKNOWN", "history", name) from None
        for weight in weights:
            _number(weight, "history", name)


def _validate_overrides(view: dict) -> None:
    known = {f"{t['tenant']}/{s['site']}" for t in view.get("tenants", []) for s in t.get("sites", [])}
    for key in sorted(view["history"].get("sites", {})):
        if key not in known:
            raise _refuse("HISTORY_RULE_UNKNOWN", key, "sites")


def _validate_money(history: dict) -> None:
    leaves = history["money_leaves"]
    if not isinstance(leaves, list) or set(leaves) != MONEY_LEAVES:
        raise _refuse("HISTORY_MONEY_LEAVES", "history", "money_leaves")


# ---- one scope -------------------------------------------------------------------------


class _Scope:
    def __init__(self, view: dict, tenant: dict, site: dict, month: str, jitter: bool) -> None:
        self.history = view["history"]
        self.tenant = tenant
        self.site = site
        self.month = month
        self.key = scope_key(tenant["tenant"], site["site"], month)
        self.days = days_in(month)
        self.anchor = self.history["anchor_period"]
        self.anchor_days = days_in(self.anchor)
        self.months = sorted(self.history["months"])
        self.jitter = jitter
        rules = merged_rules(self.history, tenant["vertical"], tenant["tenant"], site["site"])
        if rules is None:
            raise _refuse("HISTORY_RULE_UNKNOWN", self.key, tenant["vertical"])
        self.rules = rules
        self.physical_keys = physical_read(site, rules)   # D-DD.102: only what the rules read
        self.digest = scope_digest(scope_input(view, tenant, site, month, rules))
        self._factors: dict = {}

    # October values, in engine units (money in cents)
    def october(self, side: str, leaf: str, code: str = "HISTORY_RULE_REF") -> Fraction:
        values = self.site["period"].get(side, {})
        if leaf not in values:
            raise _refuse(code, self.key, leaf)
        value = _number(values[leaf], self.key, leaf)
        return value * 100 if is_money(leaf) else value

    def tenant_number(self, path: tuple[str, ...], leaf: str, code: str) -> Fraction:
        node = self.tenant
        for part in path:
            if not isinstance(node, dict) or part not in node:
                raise _refuse(code, self.key, leaf)
            node = node[part]
        return _number(node, self.key, leaf)

    def physical(self, name: str, leaf: str) -> Fraction:
        physical = self.physical_keys
        if name not in physical:
            raise _refuse("HISTORY_RULE_REF", self.key, leaf)
        return _number(physical[name], self.key, leaf)

    # seasonality (§6.2)
    def _family(self, name: str, leaf: str) -> dict:
        family = self.history.get("families", {}).get(name)
        if family is None:
            raise _refuse("HISTORY_FAMILY_UNKNOWN", self.key, leaf)
        return family

    def _weight(self, name: str, month: str, leaf: str) -> Fraction:
        family = self._family(name, leaf)
        season = self.history.get("seasons", {}).get(month)
        if season is None:
            raise _refuse("HISTORY_MONTHS", self.key, leaf)
        if season not in family["season"]:
            raise _refuse("HISTORY_FAMILY_UNKNOWN", self.key, leaf)
        season_weight = _number(family["season"][season], self.key, leaf)
        total = Fraction(0)
        for day in dates_of(month):
            cls = day_class(day, self.history.get("day_classes", {}))
            if cls is None:
                raise _refuse("HISTORY_MONTHS", self.key, leaf)
            if cls not in family["day"]:
                raise _refuse("HISTORY_FAMILY_UNKNOWN", self.key, leaf)
            total += season_weight * _number(family["day"][cls], self.key, leaf)
        return total

    def _jitter(self, name: str, leaf: str) -> Fraction:
        if not self.jitter:
            return Fraction(1)
        amplitude = _number(self._family(name, leaf)["jitter"], self.key, leaf)
        return 1 + amplitude * unit_interval(seed(self.digest, self.key, name))

    def _ratio(self, name: str, leaf: str) -> tuple[Fraction, Fraction]:
        if name not in self._factors:
            here = self._weight(name, self.month, leaf)
            there = self._weight(name, self.anchor, leaf)
            if there == 0:
                raise _refuse("HISTORY_ANCHOR_ZERO", self.key, leaf)
            self._factors[name] = (here, there)
        return self._factors[name]

    def volume(self, name: str, leaf: str) -> Fraction:
        """R(f): the month's weight over the anchor's, times the seeded factor."""
        here, there = self._ratio(name, leaf)
        return here / there * self._jitter(name, leaf)

    def shape(self, name: str, leaf: str) -> Fraction:
        """S(f): the same per day, free of the month's length."""
        here, there = self._ratio(name, leaf)
        return (here / self.days) / (there / self.anchor_days) * self._jitter(name, leaf)

    def listed(self, tokens: list[str], leaf: str) -> str:
        """This month's entry of a Jul/Aug/Sep list."""
        values = tokens[-3:]
        if self.month in self.months:
            return values[self.months.index(self.month)]
        if len(set(values)) == 1:  # a month outside the set reads a list only when it cannot differ
            return values[0]
        raise _refuse("HISTORY_MONTHS", self.key, leaf)


def _parse(scope: _Scope, leaf: str, rule) -> list[str]:
    if not isinstance(rule, str) or not rule.split():
        raise _refuse("HISTORY_RULE_UNKNOWN", scope.key, leaf)
    tokens = rule.split()
    word = tokens[0]
    if word not in ARITY:
        raise _refuse("HISTORY_RULE_UNKNOWN", scope.key, leaf)
    if len(tokens) != ARITY[word]:
        raise _refuse("HISTORY_RULE_ARITY", scope.key, leaf)
    if word in FAMILY_RULES and tokens[1] not in scope.history.get("families", {}):
        raise _refuse("HISTORY_FAMILY_UNKNOWN", scope.key, leaf)
    if word in LIST_RULES:
        for token in tokens[-3:]:
            if token == ANCHOR and word in ANCHORABLE:
                continue
            _number(token, scope.key, leaf)
    return tokens


def _references(tokens: list[str]) -> list[str]:
    word = tokens[0]
    if word in {"ratio", "share"}:
        return [tokens[1]]
    if word in {"rest", "sum"}:
        return [tokens[1], tokens[2]]
    if word == "cold_kwh":
        return ["crate_days"]
    return []


def _order(scope: _Scope, deps: dict[str, set[str]]) -> list[str]:
    order: list[str] = []
    done: set[str] = set()
    remaining = set(deps)
    while remaining:
        ready = sorted(leaf for leaf in remaining if deps[leaf] <= done)
        if not ready:
            raise _refuse("HISTORY_RULE_CYCLE", scope.key, min(remaining))
        order.append(ready[0])
        done.add(ready[0])
        remaining.discard(ready[0])
    return order


def _value(scope: _Scope, side: str, leaf: str, tokens: list[str], made: dict[str, int]) -> Fraction:
    word = tokens[0]
    key = scope.key
    if word == "per_day":
        return scope.october(side, leaf) * scope.days / scope.anchor_days
    if word == "fixed":
        return scope.october(side, leaf)
    if word == "plan_value":
        return scope.october("plan", leaf, "HISTORY_NO_PLAN_VALUE")
    if word == "zero":
        return Fraction(0)
    if word == "scale":
        return scope.october(side, leaf) * scope.volume(tokens[1], leaf)
    if word == "trend":
        return scope.october(side, leaf) * _number(scope.listed(tokens, leaf), key, leaf) * scope.volume(tokens[1], leaf)
    if word == "level":
        return scope.october(side, leaf) * _number(scope.listed(tokens, leaf), key, leaf) * scope.shape(tokens[1], leaf)
    if word == "occupancy":
        capacity = scope.tenant_number(("capacity_crates_per_room",), leaf, "HISTORY_RULE_REF")
        if capacity == 0:
            raise _refuse("HISTORY_ANCHOR_ZERO", key, leaf)
        entry = scope.listed(tokens, leaf)
        if entry == ANCHOR:
            occupancy = scope.october(side, "crate_days") / (capacity * scope.anchor_days)
        else:
            occupancy = _number(entry, key, leaf)
        if occupancy > 1:
            raise _refuse("HISTORY_BOUND", key, leaf)
        return occupancy * capacity * scope.days
    if word == "cold_kwh":
        base = scope.tenant_number(("energy_model", "base_kwh"), leaf, "HISTORY_RULE_REF")
        slope = scope.tenant_number(("energy_model", "k_kwh_per_crate_day"), leaf, "HISTORY_RULE_REF")
        model = base + slope * made["crate_days"]
        entry = scope.listed(tokens, leaf)
        if entry != ANCHOR:
            return model * _number(entry, key, leaf)
        october_model = base + slope * scope.october(side, "crate_days")
        if october_model == 0:
            raise _refuse("HISTORY_ANCHOR_ZERO", key, leaf)
        excess = scope.october(side, "kwh") / october_model
        return model * excess * scope.shape(tokens[1], leaf)
    if word == "ratio":
        denominator = scope.october(side, tokens[1])
        if denominator == 0:
            raise _refuse("HISTORY_ANCHOR_ZERO", key, leaf)
        return scope.october(side, leaf) * made[tokens[1]] / denominator
    if word == "share":
        entry = scope.listed(tokens, leaf)
        if entry == ANCHOR:
            denominator = scope.october(side, tokens[1])
            if denominator == 0:
                raise _refuse("HISTORY_ANCHOR_ZERO", key, leaf)
            fraction = scope.october(side, leaf) / denominator
        else:
            fraction = _number(entry, key, leaf)
        if fraction < 0 or fraction > 1:
            raise _refuse("HISTORY_BOUND", key, leaf)
        return Fraction(allocate(made[tokens[1]], [fraction, 1 - fraction])[0])
    if word == "rest":
        return Fraction(made[tokens[1]] - made[tokens[2]])
    if word == "sum":
        return Fraction(made[tokens[1]] + made[tokens[2]])
    if word == "fleet_kwh":
        return scope.physical("buses", leaf) * scope.physical("kwh_per_bus_night", leaf) * scope.days
    if word == "fleet_nights":
        return scope.physical("buses", leaf) * scope.days
    raise _refuse("HISTORY_RULE_UNKNOWN", key, leaf)  # unreachable: _parse admits only ARITY's words


def _side(scope: _Scope, side: str) -> dict[str, int]:
    rules = scope.rules[side]
    parsed = {leaf: _parse(scope, leaf, rules[leaf]) for leaf in sorted(rules)}
    october = scope.site["period"].get(side, {})
    generated = [leaf for leaf in sorted(parsed) if leaf in october]  # other leaves are skipped
    deps: dict[str, set[str]] = {}
    for leaf in generated:
        refs = _references(parsed[leaf])
        for ref in refs:
            if ref not in october or ref not in parsed:
                raise _refuse("HISTORY_RULE_REF", scope.key, leaf)
        deps[leaf] = set(refs)
    made: dict[str, int] = {}
    for leaf in _order(scope, deps):
        value = _value(scope, side, leaf, parsed[leaf], made)
        if value < 0:
            raise _refuse("HISTORY_BOUND", scope.key, leaf)
        made[leaf] = _round_half_even(value)
    return made


def _find(view: dict, tenant: str, site: str, month: str) -> tuple[dict, dict]:
    for tenant_doc in view.get("tenants", []):
        if tenant_doc["tenant"] != tenant:
            continue
        for site_doc in tenant_doc.get("sites", []):
            if site_doc["site"] == site:
                return tenant_doc, site_doc
    raise _refuse("HISTORY_RULE_UNKNOWN", scope_key(tenant, site, month), "site")


def _validate(view: dict) -> list[str]:
    """The checks made before any scope; returns the sorted month set."""
    history = view.get("history")
    if not isinstance(history, dict):
        raise _refuse("HISTORY_FIELD", "history", "history")
    _validate_fields(history)
    months = _validate_months(history)
    _validate_families(history)
    _validate_money(history)
    _validate_overrides(view)
    return months


def _scope_block(view: dict, tenant: str, site: str, month: str, jitter: bool) -> dict:
    tenant_doc, site_doc = _find(view, tenant, site, month)
    scope = _Scope(view, tenant_doc, site_doc, month, jitter)
    block = {
        "scope_digest": scope.digest,
        "period_days": scope.days,
        "period_end": period_end(month).isoformat(),
    }
    for side in SIDES:
        block[side] = _side(scope, side)
    block["coverage"] = {line: "RECORDED" for line in site_doc["period"].get("coverage", {})}
    return block


def generate_scope(view: dict, tenant: str, site: str, month: str, *, jitter: bool = True) -> dict:
    """One Site's month. It runs the same validation as `generate_history`, except that
    it does not check that the month is in the history's set."""
    view = ManifestView.from_document(view)
    _validate(view)
    return _scope_block(view, tenant, site, month, jitter)


def generate_history(view: dict) -> dict:
    """The history file (§7.1) for every tenant and Site, in view order, and every month."""
    view = ManifestView.from_document(view)
    months = _validate(view)
    history = view["history"]
    tenants: dict = {}
    for tenant_doc in view.get("tenants", []):
        sites = tenants.setdefault(tenant_doc["tenant"], {})
        for site_doc in tenant_doc.get("sites", []):
            sites[site_doc["site"]] = {
                month: _scope_block(view, tenant_doc["tenant"], site_doc["site"], month, True) for month in months
            }
    meta = {
        "schema": SCHEMA,
        "generator": GENERATOR,
        "shape_source": history["shape_source"],
        "view_digest": view_digest(view),
        "anchor_period": history["anchor_period"],
        "months": months,
        "money_unit": "cents",
        "money_leaves": sorted(history["money_leaves"]),
        "label": history["label"],
        "missing_cause": history["missing_cause"],
    }
    return {"meta": meta, "tenants": tenants}
