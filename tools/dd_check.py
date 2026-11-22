"""DD checker (spec `specs/DD-demo-data/spec.md` §8.1; D-DD.14, D-DD.31): the independent check of the demo world.

    python tools/dd_check.py --database-url URL [--only C-DD1,C-DD13] [--json]

Each check is a question that can FAIL with its detail. The checker shares no module, list or expected figure with
the simulator or the generators: it reads the clone by SQL, the product's reads through an in-process ASGI client on
the app factory (no port is opened), the manifest's blocks by its own YAML read, and `history.json` by its own JSON
read after asserting its sha256 equals the history golden's `file_sha256`.

Exit 0 when every selected check passes, 1 when any fails, 2 on a usage or input error (a pin mismatch is one).
A check whose unit has not landed is a stub that FAILs, naming the unit that makes it live.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from dataclasses import dataclass, field
from decimal import ROUND_HALF_EVEN, Decimal
from pathlib import Path
from typing import Callable

import yaml

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "Docs/demo-sprint/product-direction-layer4/demo-site-scenario-manifest.yaml"
HISTORY = ROOT / "Docs/demo-sprint/product-direction-layer4/history.json"
HISTORY_GOLDEN = ROOT / "simulator/tests/world/golden/history_v1.json"

#: The checker's own reading of the manifest's verticals as product Site types (spec §1 cast table).
SITE_TYPE = {"MINI_GRID": "MINIGRID", "COLD_CHAIN": "COLDCHAIN", "EV_DEPOT": "EV_CHARGING"}

#: Stubs: each check's question and the unit that makes it live (spec §8.1 "Live from").
STUBS = {
    "C-DD5": "DD4.4", "C-DD6": "DD4.4", "C-DD7": "DD4.4",
    "C-DD8": "DD3.3", "C-DD9": "DD6.1", "C-DD10": "DD6.1", "C-DD11": "DD3.1", "C-DD12": "DD3.1",
    "C-DD14": "DD5.2", "C-DD15": "DD6.1", "C-DD16": "DD3.2", "C-DD17": "DD3.3", "C-DD18": "DD6.1",
    "C-DD19": "DD3.3", "C-DD20": "DD4.4",
}
ORDER = tuple(f"C-DD{i}" for i in range(1, 21))


class InputError(Exception):
    """A checker input is missing or does not match its pin; no check is judged."""


@dataclass
class Result:
    check: str
    passed: bool
    detail: list[str] = field(default_factory=list)
    pending: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class Inputs:
    manifest: dict
    history: dict
    database_url: str


def read_inputs(database_url: str, manifest: Path = MANIFEST, history: Path = HISTORY,
                golden: Path = HISTORY_GOLDEN) -> Inputs:
    pinned = json.loads(golden.read_text(encoding="utf-8"))["file_sha256"]
    raw = history.read_bytes()
    actual = hashlib.sha256(raw).hexdigest()
    if actual != pinned:
        raise InputError(f"history.json sha256 {actual} is not the golden's {pinned}")
    with manifest.open(encoding="utf-8") as handle:
        doc = yaml.safe_load(handle)
    return Inputs(manifest=doc, history=json.loads(raw), database_url=database_url)


# --- manifest reads (the checker's own) -------------------------------------------------------------------------------

def expected_cast(manifest: dict) -> tuple[dict[str, set[tuple[str, str]]], dict[str, dict[str, str]]]:
    """Per tenant slug: {(site code, product type)}; and per tenant: Site display name -> code."""
    sites: dict[str, set[tuple[str, str]]] = {}
    names: dict[str, dict[str, str]] = {}
    for tenant in manifest["tenants"]:
        slug, kind = tenant["tenant"], SITE_TYPE.get(tenant["vertical"], f"?{tenant['vertical']}")
        sites[slug] = {(s["code"], kind) for s in tenant["sites"]}
        names[slug] = {s["site"]: s["code"] for s in tenant["sites"]}
    return sites, names


def expected_triples(manifest: dict, names: dict[str, dict[str, str]]) -> dict[str, set[tuple[str, str, str]]]:
    """Per tenant slug: demo_workflow's (person, role, Site code or "") triples."""
    out: dict[str, set[tuple[str, str, str]]] = {}
    for tenant in manifest["demo_workflow"]["tenants"]:
        slug = tenant["tenant"]
        out[slug] = {(p["name"], p["role"], names[slug][p["site"]] if "site" in p else "") for p in tenant["people"]}
    return out


# --- clone reads (SQL) ------------------------------------------------------------------------------------------------

def stored_cast(database_url: str) -> tuple[dict[str, set[tuple[str, str]]], dict[str, set[tuple[str, str, str]]]]:
    from sqlalchemy import create_engine, text

    engine = create_engine(database_url)
    try:
        with engine.connect() as c:
            tenants = {r.slug: set() for r in c.execute(text("SELECT slug FROM tenant"))}
            for r in c.execute(text("SELECT t.slug, s.site_code, s.site_type FROM site s "
                                    "JOIN tenant t ON t.id = s.tenant_id")):
                tenants.setdefault(r.slug, set()).add((r.site_code, r.site_type))
            triples: dict[str, set[tuple[str, str, str]]] = {slug: set() for slug in tenants}
            rows = c.execute(text(
                "SELECT t.slug, a.display_name, g.role, coalesce(s.site_code, '') AS site_code "
                "FROM role_grant g JOIN tenant t ON t.id = g.tenant_id "
                "JOIN operator_account a ON a.id = g.person_id LEFT JOIN site s ON s.id = g.site_id "
                "WHERE g.action = 'GRANTED' AND NOT EXISTS "
                "(SELECT 1 FROM role_grant r WHERE r.grant_id = g.id AND r.action = 'REMOVED')"))
            for r in rows:
                triples.setdefault(r.slug, set()).add((r.display_name, r.role, r.site_code))
    finally:
        engine.dispose()
    return tenants, triples


# --- the checks ---------------------------------------------------------------------------------------------------------

def judge_cast(manifest: dict, stored_sites: dict[str, set[tuple[str, str]]],
               stored_triples: dict[str, set[tuple[str, str, str]]]) -> Result:
    """C-DD1: exactly the three tenants, nine Sites (codes, product types) and demo_workflow's triples."""
    sites, names = expected_cast(manifest)
    triples = expected_triples(manifest, names)
    detail: list[str] = []
    if set(stored_sites) != set(sites):
        detail.append(f"tenants {sorted(stored_sites)} != expected {sorted(sites)}")
    for slug in sorted(sites):
        got = stored_sites.get(slug, set())
        if got != sites[slug]:
            detail.append(f"{slug} Sites: missing {sorted(sites[slug] - got)}, extra {sorted(got - sites[slug])}")
        have = stored_triples.get(slug, set())
        if have != triples[slug]:
            detail.append(f"{slug} people: missing {sorted(triples[slug] - have)}, extra {sorted(have - triples[slug])}")
    return Result("C-DD1", not detail, detail)


def check_cast(inputs: Inputs) -> Result:
    stored_sites, stored_triples = stored_cast(inputs.database_url)
    return judge_cast(inputs.manifest, stored_sites, stored_triples)


def _client_for(database_url: str, slug: str):
    """The product app served as `slug`, in process (no port)."""
    from starlette.testclient import TestClient

    os.environ["DATABASE_URL"] = database_url
    os.environ["ASSETOPS_TENANT_SLUG"] = slug
    from assetops_backend.main import create_app

    return TestClient(create_app())


def check_tenant_isolation(inputs: Inputs, client_for: Callable[[str, str], object] = _client_for) -> Result:
    """C-DD13: no tenant reads another's Sites through the product's reads; TENANT-1's refusal is DD5.2's."""
    sites, _ = expected_cast(inputs.manifest)
    detail: list[str] = []
    saved = {k: os.environ.get(k) for k in ("DATABASE_URL", "ASSETOPS_TENANT_SLUG")}
    try:
        for slug in sorted(sites):
            own = {code for code, _ in sites[slug]}
            others = sorted(code for other, rows in sites.items() if other != slug for code, _ in rows)
            client = client_for(inputs.database_url, slug)
            listed = client.get("/api/sites")
            if listed.status_code != 200:
                detail.append(f"{slug}: GET /api/sites returned {listed.status_code}")
            else:
                body = listed.json()
                items = body.get("sites", body) if isinstance(body, dict) else body
                codes = {item.get("site_id") for item in items}
                if codes != own:
                    detail.append(f"{slug}: /api/sites lists {sorted(codes)}, not its own {sorted(own)}")
            for code in others:
                status = client.get(f"/api/sites/{code}").status_code
                if status != 404:
                    detail.append(f"{slug}: GET /api/sites/{code} (another tenant's) returned {status}, not 404")
    finally:
        for key, value in saved.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
    return Result("C-DD13", not detail, detail, pending=["TENANT-1 refused and counted: planted by DD5.2"])


# --- the checker's own evaluator of the manifest's formulas (D-DD.55) -------------------------------------------------
# `structures` node expressions and `factor_map` leaf expressions are text: names, numbers, `+ - *`, parentheses, and
# `a | b` (a, or b where a is not recorded). This shares no code or table with the simulator's node table (D-DD.48).

_TOKEN = re.compile(r"\s*(?:(?P<num>[0-9]+(?:\.[0-9]+)?)|(?P<ref>[A-Za-z_][A-Za-z_0-9.]*(?:\[[a-z]+\])?)|(?P<op>[-+*|()]))")


class FormulaError(Exception):
    """A formula uses something the checker's small evaluator does not read."""


class _Absent(Exception):
    """A `record.` field is not recorded: the enclosing `|` alternative is skipped."""


def _tokens(text: str) -> list[tuple[str, str]]:
    out, pos = [], 0
    while pos < len(text.rstrip()):
        m = _TOKEN.match(text, pos)
        if m is None:
            raise FormulaError(f"cannot read {text!r} at {pos}")
        pos = m.end()
        kind = m.lastgroup
        out.append((kind, m.group(kind)))
    return out


class Formulas:
    """Evaluates one vertical's `structures` and `factor_map` on a history record (money in dollars) and prices."""

    def __init__(self, structure: dict, factor_map: dict, record: dict, prices: dict, site: str) -> None:
        self.structure, self.factor_map, self.record, self.prices, self.site = structure, factor_map, record, prices, site
        self.cache: dict[str, Decimal] = {}

    def node(self, name: str) -> Decimal | None:
        """The named node or leaf, or None where the record does not reach it."""
        if name in self.cache:
            return self.cache[name]
        text = self.structure.get(name, self.factor_map.get(name))
        if text is None:
            raise FormulaError(f"unknown name {name}")
        try:
            value = self._alternatives(_tokens(text))
        except _Absent:
            return None
        self.cache[name] = value
        return value

    def _alternatives(self, tokens: list[tuple[str, str]]) -> Decimal:
        parts, depth, current = [], 0, []
        for token in tokens:
            if token == ("op", "(") or token == ("op", ")"):
                depth += 1 if token[1] == "(" else -1
            if token == ("op", "|") and depth == 0:
                parts.append(current)
                current = []
            else:
                current.append(token)
        parts.append(current)
        for part in parts:
            try:
                return self._sum(part)
            except _Absent:
                continue
        raise _Absent()

    def _sum(self, tokens: list[tuple[str, str]]) -> Decimal:
        value = None
        sign = 1
        for chunk, op in self._split(tokens, ("+", "-")):
            term = self._product(chunk)
            value = sign * term if value is None else value + sign * term
            sign = 1 if op == "+" else -1
        if value is None:
            raise FormulaError("empty formula")
        return value

    @staticmethod
    def _split(tokens: list[tuple[str, str]], ops: tuple[str, ...]):
        """Chunks between top-level operators of `ops`, each with the operator that FOLLOWS it (None at the end)."""
        chunk, depth = [], 0
        for token in tokens:
            if token == ("op", "("):
                depth += 1
            elif token == ("op", ")"):
                depth -= 1
            if token[0] == "op" and token[1] in ops and depth == 0 and chunk:
                yield chunk, token[1]
                chunk = []
            else:
                chunk.append(token)
        yield chunk, None

    def _product(self, tokens: list[tuple[str, str]]) -> Decimal:
        value = Decimal(1)
        for chunk, _ in self._split(tokens, ("*",)):
            value *= self._atom(chunk)
        return value

    def _atom(self, tokens: list[tuple[str, str]]) -> Decimal:
        if tokens and tokens[0] == ("op", "(") and tokens[-1] == ("op", ")"):
            return self._alternatives(tokens[1:-1])
        if len(tokens) != 1:
            raise FormulaError(f"cannot read {tokens}")
        kind, text = tokens[0]
        if kind == "num":
            return Decimal(text)
        if kind != "ref":
            raise FormulaError(f"cannot read {text}")
        if text.startswith("record."):
            if text[7:] not in self.record:
                raise _Absent()
            return Decimal(str(self.record[text[7:]]))
        if text.startswith("prices."):
            entry = self.prices.get(text[7:].split("[")[0])
            if isinstance(entry, dict):
                entry = entry.get(self.site)
            if entry is None:
                raise FormulaError(f"no price {text}")
            return Decimal(str(entry))
        value = self.node(text)
        if value is None:
            raise _Absent()
        return value


def history_record(block_actual: dict, money_leaves: set[str]) -> dict:
    """A history month's `actual` record in dollars (history.json money is integer cents, `meta.money_unit`)."""
    return {k: (Decimal(v) / 100 if k in money_leaves else v) for k, v in block_actual.items()}


# --- the stored books (SQL) and the judges of C-DD2 to C-DD4 --------------------------------------------------------------

BOOK_QUERY = (
    "SELECT t.slug AS tenant, s.site_code AS site, r.kind, "
    "coalesce(r.recognition_period, to_char(r.effective_from, 'YYYY-MM'), to_char(r.occurred_at, 'YYYY-MM')) AS month, "
    "r.provenance, r.amount, r.quantity, r.status, r.canonical "
    "FROM commercial_record_revision r JOIN tenant t ON t.id = r.tenant_id LEFT JOIN site s ON s.id = r.site_id "
    "WHERE NOT EXISTS (SELECT 1 FROM commercial_record_revision n WHERE n.supersedes_revision_id = r.id)")
#: The decided kinds each product type holds in every Site-month (spec §3; the measured kinds are DD4.4's).
DECIDED_KINDS = {"MINI_GRID": ("CHARGE", "RECEIPT", "EXPENSE", "BUDGET_LINE"),
                 "COLD_CHAIN": ("STORAGE_MOVEMENT", "CHARGE", "RECEIPT", "EXPENSE", "BUDGET_LINE"),
                 "EV_DEPOT": ("FLEET_ROSTER", "EXPENSE", "BUDGET_LINE")}
EMULATED = "source-emulated"


def stored_books(database_url: str) -> list[dict]:
    """The latest revision of every commercial record, one dict each (amounts and quantities exact)."""
    from sqlalchemy import create_engine, text

    engine = create_engine(database_url)
    try:
        with engine.connect() as c:
            return [{"tenant": r.tenant, "site": r.site, "kind": r.kind, "month": r.month, "provenance": r.provenance,
                     "amount": None if r.amount is None else Decimal(r.amount),
                     "quantity": None if r.quantity is None else Decimal(r.quantity), "status": r.status,
                     "body": json.loads(r.canonical).get("body", {})} for r in c.execute(text(BOOK_QUERY))]
    finally:
        engine.dispose()


def _site_months(inputs: "Inputs", tenants: set[str] | None):
    """(tenant slug, vertical, Site name, code, month, record dict in dollars, coverage, is_october, prices)."""
    manifest, history = inputs.manifest, inputs.history
    money = set(history["meta"]["money_leaves"])
    for tenant in manifest["tenants"]:
        if tenants is not None and tenant["tenant"] not in tenants:
            continue
        for site in tenant["sites"]:
            for month in history["meta"]["months"]:
                block = history["tenants"][tenant["tenant"]][site["site"]][month]
                yield (tenant["tenant"], tenant["vertical"], site["site"], site["code"], month,
                       history_record(block["actual"], money), block.get("coverage", {}), False,
                       tenant.get("prices", {}))
            period = site["period"]
            yield (tenant["tenant"], tenant["vertical"], site["site"], site["code"], manifest["accounting_period"],
                   period["actual"], period.get("coverage", {}), True, tenant.get("prices", {}))


def _by(rows: list[dict], tenant: str, code: str, month: str, kind: str) -> list[dict]:
    return [r for r in rows if (r["tenant"], r["site"], r["month"], r["kind"]) == (tenant, code, month, kind)]


def _sum(rows: list[dict], key: str = "amount") -> Decimal:
    return sum((r[key] for r in rows), Decimal(0))


def judge_kinds(inputs: "Inputs", rows: list[dict], tenants: set[str] | None = None) -> Result:
    """C-DD2: every Site-month July to October holds each decided kind of its Site type, all labelled Emulated."""
    detail: list[str] = []
    for tenant, vertical, _, code, month, _, _, _, _ in _site_months(inputs, tenants):
        for kind in DECIDED_KINDS.get(vertical, ()):
            if not _by(rows, tenant, code, month, kind):
                detail.append(f"{tenant}/{code} {month}: no {kind} record")
    for r in rows:
        if (tenants is None or r["tenant"] in tenants) and r["provenance"] != EMULATED:
            detail.append(f"{r['tenant']}/{r['site']} {r['month']} {r['kind']}: source word {r['provenance']}, not Emulated")
    return Result("C-DD2", not detail, detail[:40] + ([f"... {len(detail) - 40} more"] if len(detail) > 40 else []))


#: D-DD.58: an EV invoice line's price class and the key of its price in `M` `tenants.<t>.sites.<s>.tariff.prices`.
_EV_PRICE = {"PEAK": "peak", "OFFPEAK": "offpeak", "NIGHT": "night_from_1_nov", "FLAT": "usd_per_kwh",
             "DEMAND": "demand_per_kw_month"}


def _site_prices(inputs: "Inputs", tenant: str, code: str) -> dict:
    for t in inputs.manifest["tenants"]:
        if t["tenant"] == tenant:
            return next((s.get("tariff", {}).get("prices", {}) for s in t["sites"] if s["code"] == code), {})
    return {}


def judge_identities(inputs: "Inputs", rows: list[dict], tenants: set[str] | None = None) -> Result:
    """C-DD3: the manifest `checks` identities on the stored records, by sums. Mini: revenue = billed x tariff and
    collected + in transit + outstanding = revenue. Cold: revenue = crate-days x 0.20. EV (D-DD.58): each stored invoice
    line = quantity x its band price in `M`, half-even to the cent; pending while no EV CHARGE row is stored. A missing
    figure is a FAIL line, never an exception."""
    detail: list[str] = []
    ev_pending = False
    for tenant, vertical, name, code, month, record, _, _, prices in _site_months(inputs, tenants):
        where = f"{tenant}/{code} {month}"
        charges = _by(rows, tenant, code, month, "CHARGE")
        receipts = _by(rows, tenant, code, month, "RECEIPT")
        if vertical == "MINI_GRID":
            revenue, billed = _sum(charges), _sum(charges, "quantity")
            tariff = Decimal(str(prices["tariff_usd_per_kwh"][name]))
            if revenue != billed * tariff:
                detail.append(f"{where}: revenue {revenue} != billed {billed} x tariff {tariff}")
            paid = _sum([r for r in receipts if r["status"] == "COLLECTED"])
            transit = _sum([r for r in receipts if r["status"] == "PAID_IN_TRANSIT"])
            outstanding = Decimal(str(record.get("outstanding", 0)))
            if paid + transit + outstanding != revenue:
                detail.append(f"{where}: collected {paid} + in transit {transit} + outstanding {outstanding} "
                              f"!= revenue {revenue}")
        elif vertical == "COLD_CHAIN":
            invoices = [r for r in charges if r["body"].get("line_type") == "STORAGE"]
            if "crate_days" not in record:
                detail.append(f"{where}: crate_days not recorded")
                continue
            expected = Decimal(str(record["crate_days"])) * Decimal(str(prices["storage_usd_per_crate_day"]))
            if _sum(invoices) != expected:
                detail.append(f"{where}: storage invoices {_sum(invoices)} != crate-days {record['crate_days']} x rate")
        elif vertical == "EV_DEPOT":
            lines = [r for r in charges if r["body"].get("line_type") in ("USAGE", "DEMAND")]
            if not any(r["kind"] == "CHARGE" for r in rows if r["tenant"] == tenant):
                ev_pending = True
                continue
            site_prices = _site_prices(inputs, tenant, code)
            for r in lines:
                price_key = _EV_PRICE.get(str(r["body"].get("band", "")) if r["body"].get("line_type") == "USAGE" else "DEMAND")
                price = site_prices.get(price_key) if price_key else None
                if price is None:
                    detail.append(f"{where}: {price_key or r['body'].get('band')} not recorded")
                    continue
                expected = (r["quantity"] * Decimal(str(price))).quantize(Decimal("0.01"), rounding=ROUND_HALF_EVEN)
                if r["amount"] != expected:
                    detail.append(f"{where} {r['body'].get('band') or 'DEMAND'}: amount {r['amount']} != "
                                  f"quantity {r['quantity']} x {price_key} {price}")
    return Result("C-DD3", not detail, detail[:40],
                  pending=["EV utility invoices are DD4.4's"] if ev_pending else [])


#: The checker's own list of the decided node figures of a history month, per vertical (D-DD.55): the stored figure's
#: reading from the rows, and the node of `structures` it must equal.
def _stored_nodes(vertical: str, rows: list[dict], tenant: str, code: str, month: str) -> dict[str, Decimal]:
    charges = _by(rows, tenant, code, month, "CHARGE")
    receipts = _by(rows, tenant, code, month, "RECEIPT")
    if vertical == "MINI_GRID":
        fuel = [r for r in _by(rows, tenant, code, month, "EXPENSE") if r["body"].get("category") == "FUEL"]
        return {"billed_kwh": _sum(charges, "quantity"), "revenue": _sum(charges),
                "collected": _sum([r for r in receipts if r["status"] == "COLLECTED"]),
                "diesel_l": _sum(fuel, "quantity"), "fuel_cost": _sum(fuel)}
    if vertical == "COLD_CHAIN":
        return {"revenue": _sum([r for r in charges if r["body"].get("line_type") == "STORAGE"]),
                "received": _sum(receipts)}
    return {}


#: Stored decided leaves: (expense category, the record fields that hold it, by vertical).
_EXPENSE_LEAVES = {"MINI_GRID": (("OM", "om"), ("STAFF", "staff")), "COLD_CHAIN": (("OM", "maint"), ("STAFF", "staff")),
                   "EV_DEPOT": (("OM", "maintenance"),)}
_RECORDED_NODE = {"MINI_GRID": {"billed_kwh": "billed_kwh", "revenue": "revenue", "collected": "collected",
                                "diesel_l": "diesel_l", "fuel_cost": "diesel_cost"},
                  "COLD_CHAIN": {"revenue": "revenue", "received": "collected"}}
_STRUCTURE = {"MINI_GRID": "MINI_GRID", "COLD_CHAIN": "COLD_CHAIN", "EV_DEPOT": "EV_DEPOT_CAPTIVE"}


def judge_leaves_and_nodes(inputs: "Inputs", rows: list[dict], tenants: set[str] | None = None) -> Result:
    """C-DD4: each decided leaf equals October's `period.actual` and each history month's `history.json`, to the cent;
    each decided node figure of a history month equals this checker's own evaluation of `structures` and
    `factor_map` on `history.json`'s leaves, and October's equals what its period records (D-DD.55)."""
    detail: list[str] = []
    for tenant, vertical, name, code, month, record, cover, october, prices in _site_months(inputs, tenants):
        where = f"{tenant}/{code} {month}"
        expenses = _by(rows, tenant, code, month, "EXPENSE")
        for category, leaf in _EXPENSE_LEAVES.get(vertical, ()):
            if leaf not in record or cover.get(leaf) == "ESTIMATED" or cover.get({"maint": "om"}.get(leaf, leaf)) == "ESTIMATED":
                continue
            stored = _sum([r for r in expenses if r["body"].get("category") == category])
            if stored != Decimal(str(record[leaf])):
                detail.append(f"{where}: {category} {stored} != {leaf} {record[leaf]}")
        stored_nodes = _stored_nodes(vertical, rows, tenant, code, month)
        if october:
            expected = {n: Decimal(str(record[f])) for n, f in _RECORDED_NODE.get(vertical, {}).items() if f in record}
        else:
            formulas = Formulas(inputs.manifest["structures"][_STRUCTURE[vertical]],
                                inputs.manifest["factor_map"][_STRUCTURE[vertical]], record, prices, name)
            expected = {}
            for node in _RECORDED_NODE.get(vertical, {}):
                value = formulas.node(node)
                if value is not None:
                    expected[node] = value
        for node, value in expected.items():
            if cover.get("revenue") == "ESTIMATED" and node in ("billed_kwh", "revenue", "collected", "received"):
                continue
            if cover.get("diesel") == "ESTIMATED" and node in ("diesel_l", "fuel_cost"):
                continue
            if stored_nodes.get(node) != value:
                detail.append(f"{where}: {node} stored {stored_nodes.get(node)} != {'recorded' if october else 'evaluated'} {value}")
    return Result("C-DD4", not detail, detail[:40])


def _judged(judge: Callable[..., Result]) -> Callable[[Inputs], Result]:
    def run(inputs: Inputs) -> Result:
        return judge(inputs, stored_books(inputs.database_url))
    return run


def stub(check: str) -> Result:
    return Result(check, False, [f"not live: its unit {STUBS[check]} has not landed"])


LIVE: dict[str, Callable[[Inputs], Result]] = {
    "C-DD1": check_cast, "C-DD2": _judged(judge_kinds), "C-DD3": _judged(judge_identities),
    "C-DD4": _judged(judge_leaves_and_nodes), "C-DD13": check_tenant_isolation}


def run(inputs: Inputs, only: tuple[str, ...] = ORDER) -> list[Result]:
    results = []
    for check in only:
        if check in LIVE:
            try:
                results.append(LIVE[check](inputs))
            except Exception as error:  # noqa: BLE001 - an unreadable store is a FAIL with its detail
                results.append(Result(check, False, [f"could not be judged: {type(error).__name__}: {error}"]))
        else:
            results.append(stub(check))
    return results


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--database-url", default=os.environ.get("DATABASE_URL"))
    parser.add_argument("--only", default=",".join(ORDER))
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    only = tuple(c.strip() for c in args.only.split(",") if c.strip())
    unknown = sorted(set(only) - set(ORDER))
    if unknown or not args.database_url:
        print(f"DD_CHECK_USAGE unknown checks {unknown}" if unknown else "DD_CHECK_USAGE --database-url is required",
              file=sys.stderr)
        return 2
    try:
        inputs = read_inputs(args.database_url)
    except (InputError, OSError, KeyError, ValueError) as error:
        print(f"DD_CHECK_INPUT {error}", file=sys.stderr)
        return 2
    results = run(inputs, only)
    if args.json:
        print(json.dumps([r.__dict__ for r in results], indent=1))
    else:
        for r in results:
            print(f"{r.check} {'PASS' if r.passed else 'FAIL'}")
            for line in r.detail:
                print(f"  {line}")
            for line in r.pending:
                print(f"  pending: {line}")
    return 0 if all(r.passed for r in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
