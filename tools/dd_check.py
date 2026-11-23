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
from datetime import datetime, timedelta
from decimal import ROUND_HALF_EVEN, Decimal
from fractions import Fraction
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
    "C-DD8": "DD3.3", "C-DD9": "DD6.1", "C-DD10": "DD6.1",
    "C-DD14": "DD5.2", "C-DD15": "DD6.1", "C-DD17": "DD3.3", "C-DD18": "DD6.1",
    "C-DD19": "DD3.3",
}
#: D-DD.121: C-DD6 is live by vertical (so in LIVE, not STUBS); its clauses not yet producible, each with the unit that makes it live.
PENDING = {"C-DD6": ("KISIWA-001 GEN-KS-01 2026-10-30T18:40 DD3b", "MTO-001 INV-MT-02 2026-10-28T11:02 DD3b"),
           "C-DD7": ("mini-grid load served + unserved = delivered_kwh: unserved energy is no readings channel (DD3a writes "
                     "it to measured.json only); the readings-side clause lands with DD3b/DD5",
                     "EV kwh_2200_2400, kwh_0000_0500 (D-DD.158): each `measured.json` window is judged exactly "
                     "against site-meter/import when the world's measured.json is given; the loaded world's fetch is "
                     "DD5b's (D-DD.160)"),
           "C-DD20": ("KISIWA-001 unserved evening energy after 2026-10-30T18:40, none from 2026-08-17T11:00 to then DD3b",
                      "MTO-001 generator litres per day after 2026-10-28T11:02 above the 28 days before DD3b")}
ORDER = tuple(f"C-DD{i}" for i in range(1, 22))


class InputError(Exception):
    """A checker input is missing or does not match its pin; no check is judged."""


@dataclass
class Result:
    check: str
    passed: bool
    detail: list[str] = field(default_factory=list)
    pending: list[str] = field(default_factory=list)
    #: printed beside the result, never judged (C-DD7's manifest figures, C-DD20's series)
    info: list[str] = field(default_factory=list)


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


#: C-DD6's live clauses (D-DD.121), the checker's own reading of `M`: each failure on its own unit's channels at its
#: local instant (`at` is a prefix: Ruiru's is the day `M` names, D-DD.123), and the two batches present that night at
#: Thika with their limits. GEN-CR-01 is the generator controller's channel; CH-K2 faults both its connectors.
FAILURES_LIVE = ({"site": "COLD-THIKA", "unit": "GEN-CR-01", "source_ids": ("generator-controller",), "outcome": "FAILED",
                  "at": "2026-10-06T19:11"},
                 {"site": "EV-KAS", "unit": "CH-K2", "outcome": "FAULTED", "at": "2026-11-01T23:40",
                  "source_ids": ("ch-k2-c1-connector-controller", "ch-k2-c2-connector-controller")},
                 {"site": "EV-RUI", "unit": "CH-R7 c2", "outcome": "FAULTED", "at": "2026-10-06",
                  "source_ids": ("ch-r7-c2-connector-controller",)})
EXCURSIONS = ({"site": "COLD-THIKA", "batch": "B-1031", "day": "2026-10-06", "limit_c": Decimal(5), "above_minutes": 15},
              {"site": "COLD-THIKA", "batch": "B-1034", "day": "2026-10-06", "limit_c": Decimal(12)})
CHAMBER = "chamber-probe"


def judge_failures_at_instant(readings: dict[str, list[dict]], sites: tuple[str, ...] | None = None) -> Result:
    """C-DD6 on readings rows (`{site code: rows}`, the writer's row shape), over the clauses of `sites` (all by
    default): each live failure is its outcome's event on its own channels at its local instant, and on no other
    channel then; B-1031 is above 5 degC for more than 15 minutes by
    the 5-minute readings' lower bound ((n - 1) x 5 for n consecutive readings above); B-1034 stays below 12 degC."""
    detail = []
    for clause in FAILURES_LIVE:
        if sites is not None and clause["site"] not in sites:
            continue
        rows = readings.get(clause["site"], [])
        failed = {r["source_id"] for r in rows if r.get("unit") == "event"
                  and r["event"].get("outcome") == clause["outcome"] and r["start"].startswith(clause["at"])}
        if failed != set(clause["source_ids"]):
            detail.append(f"{clause['site']} {clause['unit']}: {clause['outcome']} at {clause['at']} on "
                          f"{sorted(failed) or 'nothing'}")
    for clause in EXCURSIONS:
        if sites is not None and clause["site"] not in sites:
            continue
        chamber = [(r["start"], Decimal(r["value"])) for r in readings.get(clause["site"], [])
                   if r["source_id"] == CHAMBER and r["start"].startswith(clause["day"])]
        if not chamber:
            detail.append(f"{clause['site']} {clause['batch']}: no chamber readings on {clause['day']}")
            continue
        if "above_minutes" in clause:
            run = longest = 0
            for _at, value in chamber:
                run = run + 1 if value > clause["limit_c"] else 0
                longest = max(longest, run)
            bound = max(longest - 1, 0) * 5
            if bound <= clause["above_minutes"]:
                detail.append(f"{clause['site']} {clause['batch']}: above {clause['limit_c']} degC at least {bound} "
                              f"minutes, not more than {clause['above_minutes']}")
        else:
            peak = max(value for _at, value in chamber)
            if peak >= clause["limit_c"]:
                detail.append(f"{clause['site']} {clause['batch']}: peak {peak} degC is not below {clause['limit_c']}")
    pending = [f"{p} pending" for p in PENDING["C-DD6"]]
    return Result("C-DD6", not detail, detail, pending)


def stored_readings(database_url: str) -> dict[str, list[dict]]:
    """C-DD6's fetch from the clone. The world's readings reach the store only through DD5's loader (DD5.1); until it
    lands the store holds none, so the check fails on the clone naming the missing rows (D-DD.121)."""
    return {}


def check_failures(inputs: "Inputs") -> Result:
    return judge_failures_at_instant(stored_readings(inputs.database_url))


# --- C-DD5, C-DD7, C-DD20 (DD4.4; D-DD.55, D-DD.99, D-DD.124): judges on rows -----------------------------------------

#: C-DD5's cadence table, the checker's own (D-DD.31, D-DD.124): states and events on change, with no grid; every other
#: unit is a mean inside one 5-minute slot aligned to :00 (an EV row may be a piece of its slot, cut at a session edge)
#: or a sample at the slot's start instant (the cold probes).
CADENCE = {"state": "ON_CHANGE", "event": "ON_CHANGE"}
MEAN_SLOT = timedelta(minutes=5)
SIMULATED = "SIMULATED"
#: D-DD.103: the span ends at 06:00 local on `M` `as_of`; it starts on `M` history's first month (+03:00, no DST).
SPAN_END_LOCAL = "06:00:00+03:00"


def span_of(manifest: dict) -> tuple[datetime, datetime]:
    first = min(manifest["history"]["months"])
    return (datetime.fromisoformat(f"{first}-01T00:00:00+03:00"),
            datetime.fromisoformat(f"{manifest['as_of']}T{SPAN_END_LOCAL}"))


def _slots(start: datetime, a: datetime, b: datetime) -> range:
    return range((a - start) // MEAN_SLOT, -((start - b) // MEAN_SLOT))


def judge_cadence(readings: dict[str, list[dict]], source_modes: dict[str, str], sites: tuple[str, ...],
                  start: datetime, end: datetime, outages: dict[str, list[tuple[datetime, datetime]]]) -> Result:
    """C-DD5: each Site has readings, its source mode is SIMULATED (`source_modes` is a store field, a separate input),
    every row lies in the span and keeps the cadence table, and every 5-minute slot of the span holds a mean unless a
    declared outage covers it."""
    detail = []
    every = set(range((end - start) // MEAN_SLOT))
    for code in sites:
        rows = readings.get(code, [])
        if not rows:
            detail.append(f"{code}: no readings")
            continue
        if source_modes.get(code) != SIMULATED:
            detail.append(f"{code}: source_mode {source_modes.get(code)} is not {SIMULATED}")
        covered, off, outside = set(), [], []
        for r in rows:
            a, b = datetime.fromisoformat(r["start"]), datetime.fromisoformat(r["end"])
            if a < start or b > end or b < a:
                outside.append(r["start"])
            elif CADENCE.get(r["unit"]) != "ON_CHANGE":
                i = (a - start) // MEAN_SLOT
                if a < b <= start + MEAN_SLOT * (i + 1) or (a == b and a == start + MEAN_SLOT * i):
                    covered.add(i)
                else:
                    off.append(f"{r['source_id']}/{r['signal_id']} {r['start']}..{r['end']}")
        declared = {i for a, b in outages.get(code, ()) for i in _slots(start, a, b)}
        missing = sorted(every - covered - declared)
        if outside:
            detail.append(f"{code}: {len(outside)} rows outside the span, first {outside[0]}")
        if off:
            detail.append(f"{code}: {len(off)} rows off the cadence (a mean inside one 5-minute slot, or a sample at its "
                          f"start), first {off[0]}")
        if missing:
            days = sorted({(start + MEAN_SLOT * i).date().isoformat() for i in missing})
            detail.append(f"{code}: gap of {len(missing)} 5-minute slots on {len(days)} days, first "
                          f"{(start + MEAN_SLOT * missing[0]).isoformat()}")
    return Result("C-DD5", not detail, detail[:40])


def stored_source_modes(database_url: str) -> dict[str, str]:
    """C-DD5's `source_mode` per Site from the clone: empty until DD5's loader stores the world's readings."""
    return {}


def check_cadence(inputs: "Inputs") -> Result:
    sites = tuple(s["code"] for t in inputs.manifest["tenants"] for s in t["sites"])
    return judge_cadence(stored_readings(inputs.database_url), stored_source_modes(inputs.database_url), sites,
                         *span_of(inputs.manifest), {})


#: C-DD7's meters, the checker's own (Site code prefix -> the meter channel the books bill).
METERS = {"COLD-": ("compressor-meter", "power"), "EV-": ("site-meter", "import")}


def _meter_of(code: str) -> tuple[str, str] | None:
    return next((m for prefix, m in METERS.items() if code.startswith(prefix)), None)


def _milli(value: Fraction) -> Decimal:
    return Decimal(round(value * 1000)) / 1000  # half-even (Fraction rounding), once


def _hhmm(text: str) -> int:
    hours, minutes = text.split(":")
    return int(hours) * 60 + int(minutes)


def _metered(rows: list[dict], channel: tuple[str, str], schedules: list[dict]) -> tuple[dict, dict, list[str]]:
    """Energy by (month, price class) and the largest 30-minute mean by month (:00 and :30 windows), exact."""
    bands: dict[tuple[str, str], Fraction] = {}
    windows: dict[tuple[str, str], Fraction] = {}
    problems: list[str] = []
    for r in rows:
        if (r["source_id"], r["signal_id"]) != channel:
            continue
        a, b = datetime.fromisoformat(r["start"]), datetime.fromisoformat(r["end"])
        kwh = Fraction(Decimal(r["value"])) * Fraction(int((b - a).total_seconds()), 3600)
        month, day, minute = r["start"][:7], r["start"][:10], a.hour * 60 + a.minute
        name = "ALL"
        if schedules:
            found = [s for s in schedules if s["clocks"]["effective_from"] <= day <= s["clocks"].get("effective_to", "9999")]
            hit = [x["band"].split("-")[0] for x in (found[0]["body"]["bands"] if len(found) == 1 else [])
                   if _hhmm(x["from"]) <= minute < _hhmm(x["to"])]
            if len(hit) != 1:
                problems.append(f"{r['start']} is in {len(found)} schedules / {len(hit)} bands")
                continue
            name = hit[0]
        bands[(month, name)] = bands.get((month, name), Fraction(0)) + kwh
        window = f"{r['start'][:14]}{'00' if a.minute < 30 else '30'}"
        windows[(month, window)] = windows.get((month, window), Fraction(0)) + kwh
    demand: dict[str, Fraction] = {}
    for (month, _w), kwh in windows.items():
        demand[month] = max(demand.get(month, Fraction(0)), kwh * 2)
    return bands, demand, problems


def _manifest_kwh(manifest: dict) -> dict[tuple[str, str], object]:
    out = {}
    for tenant in manifest.get("tenants", []):
        for site in tenant["sites"]:
            kwh = site.get("period", {}).get("actual", {}).get("kwh")
            if tenant.get("vertical") == "COLD_CHAIN" and kwh is not None:
                out[(site["code"], manifest["accounting_period"])] = kwh
    return out


#: D-DD.158: C-DD7's EV hour windows, the checker's own (`measured.json` window -> local minutes [from, to) of a day).
EV_WINDOWS = {"2200_2400": (22 * 60, 24 * 60), "0000_0500": (0, 5 * 60)}


def _windows_metered(rows: list[dict], channel: tuple[str, str]) -> dict[tuple[str, str], Fraction]:
    """Site-meter energy by (local month, window), exact: a row's minutes inside the window, at its mean kW."""
    out: dict[tuple[str, str], Fraction] = {}
    for r in rows:
        if (r["source_id"], r["signal_id"]) != channel:
            continue
        a, b = datetime.fromisoformat(r["start"]), datetime.fromisoformat(r["end"])
        start = a.hour * 60 + a.minute
        end = start + int((b - a).total_seconds()) // 60
        kw = Fraction(Decimal(r["value"]))
        for name, (lo, hi) in EV_WINDOWS.items():
            minutes = max(0, min(end, hi) - max(start, lo))
            out[(r["start"][:7], name)] = out.get((r["start"][:7], name), Fraction(0)) + kw * Fraction(minutes, 60)
    return out


def judge_meter_books(manifest: dict, readings: dict[str, list[dict]], rows: list[dict], sites: tuple[str, ...],
                      measured: dict[str, dict] | None = None) -> Result:
    """C-DD7, exact: the cold bill's kWh equals the room meter's; each EV invoice band's kWh equals the Site meter's
    energy in that price class of the schedule in force, DEMAND the largest 30-minute mean; each departure's
    `block_met` is delivered >= the roster's required, delivered never above it (so undelivered = required - delivered
    is the rest), and each roster bus-night has one departure. Metered kWh is printed beside `M`'s, as information.
    `measured` (Site code -> `measured.json` months): each EV month's `windows` equals the Site meter's energy over the
    same local minutes, exactly (D-DD.158); without it that clause stays pending."""
    detail, info = [], []
    for code in sites if measured is not None else ():
        channel = _meter_of(code)
        if not code.startswith("EV-") or channel is None or code not in measured:
            continue
        metered = _windows_metered(readings.get(code, []), channel)
        for month, block in sorted(measured[code].items()):
            for name, value in sorted(block.get("windows", {}).items()):
                if _milli(metered.get((month, name), Fraction(0))) != Decimal(value):
                    detail.append(f"{code} {month} window {name}: measured {value} kWh, meter "
                                  f"{_milli(metered.get((month, name), Fraction(0)))}")
    known = _manifest_kwh(manifest)
    for code in sites:
        mine = [r for r in rows if r.get("site_code") == code]
        charges = [r for r in mine if r["kind"] == "CHARGE" and r.get("quantity", {}).get("unit") in ("kWh", "kW")]
        channel = _meter_of(code)
        if charges and channel is not None:
            schedules = [r for r in mine if r["kind"] == "TARIFF_SCHEDULE"] if code.startswith("EV-") else []
            meter_rows = readings.get(code, [])
            if not any((r["source_id"], r["signal_id"]) == channel for r in meter_rows):
                detail.append(f"{code}: books without readings of {channel[0]}/{channel[1]}")
                continue
            bands, demand, problems = _metered(meter_rows, channel, schedules)
            detail += [f"{code} {p}" for p in problems[:5]]
            for r in charges:
                month, qty = r["clocks"]["recognition_period"], Decimal(r["quantity"]["value"])
                band = r["body"].get("band")
                if r["quantity"]["unit"] == "kW":
                    metered, label = demand.get(month, Fraction(0)), f"{code} {month} {band}"
                elif band is None:
                    metered = sum((v for (m, _n), v in bands.items() if m == month), Fraction(0))
                    label = f"{code} {month} bill"
                    if (code, month) in known:
                        info.append(f"info: {label} {r['quantity']['value']} kWh; M {known[(code, month)]} kWh")
                else:
                    metered, label = bands.get((month, band), Fraction(0)), f"{code} {month} {band}"
                if _milli(metered) != qty:
                    detail.append(f"{label}: book {r['quantity']['value']} {r['quantity']['unit']}, meter {_milli(metered)}")
            invoiced = {(r["clocks"]["recognition_period"], r["body"].get("band")) for r in charges if r["body"].get("band")}
            for month, name in sorted(bands) if invoiced else ():
                if any(m == month for m, _b in invoiced) and (month, name) not in invoiced:
                    detail.append(f"{code} {month} {name}: metered {_milli(bands[(month, name)])} kWh, not invoiced")
        roster = {(r["body"]["vehicle_ref"], r["clocks"]["effective_from"]): Decimal(r["body"]["required_kwh"])
                  for r in mine if r["kind"] == "FLEET_ROSTER"}
        departed = set()
        for r in (r for r in mine if r["kind"] == "DEPARTURE"):
            key = (r["body"]["vehicle_ref"], r["body"]["service_day"])
            departed.add(key)
            if key not in roster:
                detail.append(f"{code} {key[0]} {key[1]}: departure without a roster night")
                continue
            delivered, required = Decimal(r["body"]["kwh_at_departure"]), roster[key]
            if delivered > required:
                detail.append(f"{code} {key[0]} {key[1]}: delivered {delivered} kWh above required {required}")
            if r["body"]["block_met"] != (delivered >= required):
                detail.append(f"{code} {key[0]} {key[1]}: block_met {r['body']['block_met']} with {delivered} of {required}")
        detail += [f"{code} {k[0]} {k[1]}: no departure for the roster night" for k in sorted(set(roster) - departed)]
    pending = [p for p in PENDING["C-DD7"] if measured is None or not p.startswith("EV kwh_2200_2400")]
    return Result("C-DD7", not detail, detail[:40], pending, info)


def check_meter_books(inputs: "Inputs") -> Result:
    sites = tuple(s["code"] for t in inputs.manifest["tenants"] for s in t["sites"])
    return judge_meter_books(inputs.manifest, stored_readings(inputs.database_url), stored_books(inputs.database_url),
                             sites)


#: C-DD20's directions (spec §8.1), the checker's own: kWh per crate-day rises each whole month at Mwea (as its
#: occupancy falls) and Kirinyaga; Embakasi's metered peak share rises each month.
STORY_MONTHS = ("2026-07", "2026-08", "2026-09", "2026-10")
PER_CRATE_DAY = ("COLD-MWEA", "COLD-KIRI")
OCCUPANCY_FALLS = ("COLD-MWEA",)
PEAK_SHARE = ("EV-EMB",)


def crate_days_of(inputs: "Inputs") -> dict[str, dict[str, int]]:
    """Occupied crate-days per cold Site and month: `history.json` (July-September) and `M`'s October actual."""
    out: dict[str, dict[str, int]] = {}
    for _t, vertical, _name, code, month, record, *_rest in _site_months(inputs, None):
        if vertical == "COLD_CHAIN" and "crate_days" in record:
            out.setdefault(code, {})[month] = int(record["crate_days"])
    return out


def _rising(values: list[Fraction]) -> bool:
    return all(b > a for a, b in zip(values, values[1:]))


def judge_story_directions(rows: list[dict], crate_days: dict[str, dict[str, int]]) -> Result:
    """C-DD20 on the measured books: a failure stops for the Architect; nothing is tuned."""
    detail, info = [], []

    def usage(code: str, month: str, band=None) -> list[Fraction]:
        return [Fraction(Decimal(r["quantity"]["value"])) for r in rows
                if r.get("site_code") == code and r["kind"] == "CHARGE" and r["clocks"]["recognition_period"] == month
                and r.get("quantity", {}).get("unit") == "kWh" and (band is None or r["body"].get("band") == band)]

    for code in PER_CRATE_DAY:
        crates = crate_days.get(code, {})
        missing = [m for m in STORY_MONTHS if len(usage(code, m)) != 1 or not crates.get(m)]
        if missing:
            detail.append(f"{code}: no bill or crate-days for {missing}")
            continue
        per = [usage(code, m)[0] / crates[m] for m in STORY_MONTHS]
        info.append(f"info: {code} kWh per crate-day " + ", ".join(f"{m} {float(v):.4f}" for m, v in zip(STORY_MONTHS, per)))
        if not _rising(per):
            detail.append(f"{code}: kWh per crate-day does not rise each month")
        if code in OCCUPANCY_FALLS and not _rising([Fraction(-crates[m]) for m in STORY_MONTHS]):
            detail.append(f"{code}: occupancy (crate-days) does not fall each month")
    for code in PEAK_SHARE:
        shares = []
        for m in STORY_MONTHS:
            total, peak = sum(usage(code, m), Fraction(0)), sum(usage(code, m, "PEAK"), Fraction(0))
            shares.append(peak / total if total else None)
        if None in shares:
            detail.append(f"{code}: no invoice for {[m for m, s in zip(STORY_MONTHS, shares) if s is None]}")
            continue
        info.append(f"info: {code} peak share " + ", ".join(f"{m} {float(v):.4f}" for m, v in zip(STORY_MONTHS, shares)))
        if not _rising(shares):
            detail.append(f"{code} peak share does not rise each month")
    return Result("C-DD20", not detail, detail, list(PENDING["C-DD20"]), info)


def check_story(inputs: "Inputs") -> Result:
    return judge_story_directions(stored_books(inputs.database_url), crate_days_of(inputs))


GENERATOR_MODULES = ("simulator/assetops_simulator/world", "tools/world_history.py")
#: Names the writer's own refusal may carry; every other mention of the answer block in a generator module fails C-DD12.
ANSWER_BLOCK_ALLOWED = ("refuse_oracle", "TEL_ORACLE_READ", "ORACLE_KEY")


def check_no_oracle_read(inputs: Inputs) -> Result:
    """C-DD12: no generator module imports, names or indexes the answer block (static scan of the sources; the writer's
    own `TEL_ORACLE_READ` refusal is the runtime half). Docstrings and comments are not code."""
    import ast

    detail = []
    paths = sorted(p for part in GENERATOR_MODULES for p in
                   ((ROOT / part).rglob("*.py") if (ROOT / part).is_dir() else [ROOT / part]))
    for path in paths:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        docstrings = {id(n.body[0].value) for n in ast.walk(tree)
                      if isinstance(n, (ast.Module, ast.FunctionDef, ast.ClassDef)) and n.body
                      and isinstance(n.body[0], ast.Expr) and isinstance(n.body[0].value, ast.Constant)}
        for node in ast.walk(tree):
            if isinstance(node, ast.Name):
                text = node.id
            elif isinstance(node, ast.Attribute):
                text = node.attr
            elif isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                text = node.name
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                text = " ".join([getattr(node, "module", None) or "", *[a.name for a in node.names]])
            elif isinstance(node, ast.Constant) and isinstance(node.value, str) and id(node) not in docstrings:
                text = node.value
            else:
                continue
            if "oracle" in text.lower() and not any(a in text for a in ANSWER_BLOCK_ALLOWED):
                detail.append(f"{path.relative_to(ROOT)}:{getattr(node, 'lineno', 0)} {text[:60]}")
    return Result("C-DD12", not detail, [f"{len(paths)} modules scanned"] + detail[:20] if detail else
                  [f"{len(paths)} modules scanned, none names the answer block"])


def _run_world(args: list[str]) -> None:
    import subprocess

    done = subprocess.run([sys.executable, str(ROOT / "tools/world_history.py"), *args], capture_output=True, text=True)
    if done.returncode != 0:
        raise RuntimeError(f"world_history.py {args[0]} exited {done.returncode}: {done.stderr.strip()[:300]}")


def check_two_processes_agree(inputs: Inputs, first: str = "2026-07-01", last: str = "2026-07-02") -> Result:
    """C-DD11: two generator runs in separate processes give identical bytes for books, readings and measured books.
    A two-day window of Kobo and Mwea (the writer is deterministic by construction; this is the proof it is)."""
    import tempfile

    onboarding = ROOT / "backend/tests/fixtures/on1"
    manifest = str(MANIFEST)
    digests = []
    with tempfile.TemporaryDirectory(prefix="ddcheck-") as scratch:
        for run in ("a", "b"):
            base = Path(scratch) / run
            _run_world(["exports", "--manifest", manifest, "--out", str(base / "books")])
            _run_world(["site-inputs", "--onboarding", str(onboarding), "--bindings",
                        str(ROOT / "backend/conversions/world"), "--out", str(base / "sites.json")])
            _run_world(["telemetry", "--manifest", manifest, "--sites", str(base / "sites.json"), "--books",
                        str(base / "books"), "--out", str(base / "telemetry"), "--start", first, "--end", last,
                        "--site", "KOBO-001", "--site", "COLD-MWEA"])  # Mwea from DD4a (D-DD.122)
            digests.append({str(p.relative_to(base)): hashlib.sha256(p.read_bytes()).hexdigest()
                            for p in sorted(base.rglob("*")) if p.is_file()})
    differing = sorted(k for k in set(digests[0]) | set(digests[1]) if digests[0].get(k) != digests[1].get(k))
    kinds = {"books": any(k.startswith("books/") for k in digests[0]),
             "readings": any(k.endswith(".readings.json") for k in digests[0]),
             "measured": any(k.endswith("measured.json") for k in digests[0])}
    detail = [f"{len(digests[0])} files compared; books/readings/measured present: {kinds}"]
    return Result("C-DD11", not differing and all(kinds.values()), detail + [f"differs: {k}" for k in differing[:10]])


def check_property_table_parity(inputs: Inputs) -> Result:
    """C-DD21: the writer's property-to-address table (`telemetry.NEEDS`) equals the backend's, which the product freezes.
    Compared on Kobo's v8 draft built through the host adapter: every initial value's address, state key, unit and
    dimension, and the writer's table row for it; and the pack's foundation needs by name."""
    for part in ("host", "host/tests", "backend", "contracts", "simulator"):
        sys.path.insert(0, str(ROOT / part))
    from assetops_simulator.world import telemetry
    from execution_adapter import frozen_world_inputs
    from kobo_season import base_run, season_site_v2
    from assetops_backend.runs.profiles import MINI_GRID_V8_MODEL

    frozen = frozen_world_inputs(base_run(1, version=8, site_edit=season_site_v2))
    backend = {r.state_key: (r.address.split("@")[0], r.canonical_unit, r.dimension, r.parameter_id.removeprefix("model-need:"))
               for r in frozen.initial_values if r.answered_by == "SITE_FOUNDATION"}
    table = {n.state_key: (n.state_key, n.unit, n.dimension, n.property_key) for n in telemetry.NEEDS}
    detail = [f"{k}: backend {backend.get(k)} != writer {table.get(k)}" for k in sorted(set(backend) | set(table))
              if backend.get(k) != table.get(k)]
    needs = set(MINI_GRID_V8_MODEL.foundation_needs)
    missing = sorted(needs - {n.state_key for n in telemetry.NEEDS} - {"pv-rated-power"} - set(backend) - {"fuel-tank-capacity"})
    detail += [f"foundation need {m} has no writer row" for m in missing]
    return Result("C-DD21", not detail, detail[:20] or [f"{len(table)} rows equal the backend's frozen initial values"])


DATASHEET_SLOT = ROOT / "config/datasheets/kobo-equipment.json"
DATASHEET_FILE = ROOT / "backend/tests/fixtures/on1/lakeside-power.onboarding.json"
DATASHEET_SITE = "KOBO-001"


def _half_even(value, quantum: str) -> str:
    from fractions import Fraction

    value = Fraction(value)
    return str((Decimal(value.numerator) / Decimal(value.denominator)).quantize(Decimal(quantum), rounding=ROUND_HALF_EVEN))


def datasheet_expectation(slot: dict) -> dict[str, dict[str, tuple[str, str]]]:
    """C-DD16: the checker's own reading of spec §6's mapping table (exact arithmetic; shares nothing with the tool).
    Per component type: property key -> (value text, basis code). Raises ValueError when the slot cannot be mapped."""
    from fractions import Fraction

    gen, bat = slot["generator"], slot["battery"]
    assumed = {a["item"]: a for a in slot.get("assumed", [])}

    def stated_or_assumed(stated, item: str) -> tuple[str, str]:
        if stated is not None:
            return str(stated), "MANUFACTURER_DATASHEET"
        entry = assumed.get(item) or {}
        if "value" not in entry or not entry.get("basis_code"):
            raise ValueError(f"{item}: neither stated nor assumed with a basis code")
        return str(entry["value"]), entry["basis_code"]

    prime = Fraction(gen["prime_kw"])
    pts = [(Fraction(int(pct), 100) * prime, Fraction(v)) for pct, v in gen["fuel_l_per_h"].items() if v is not None]
    sfc = _half_even(Fraction(gen["fuel_l_per_h"]["100"]) / prime, "0.0001")
    if gen.get("no_load_l_per_h") is not None:
        no_load = (str(gen["no_load_l_per_h"]), "MANUFACTURER_DATASHEET")
    else:
        no_load = stated_or_assumed(None, "generator.no_load_l_per_h")
        if no_load[1] == "DATASHEET_FIT":
            n = len(pts)
            mx, my = sum(x for x, _ in pts) / n, sum(y for _, y in pts) / n
            slope = sum((x - mx) * (y - my) for x, y in pts) / sum((x - mx) ** 2 for x, _ in pts)
            fitted = _half_even(my - slope * mx, "0.01")
            if Decimal(no_load[0]) != Decimal(fitted):
                raise ValueError(f"the slot's DATASHEET_FIT no-load {no_load[0]} is not the fit's {fitted}")
    capacity = _half_even(bat["modules"] * Fraction(bat["module_usable_kwh"]), "0.1")
    return {"GENERATOR": {"generator-rated-power": (str(gen["prime_kw"]), "MANUFACTURER_DATASHEET"),
                          "specific-fuel-consumption": (sfc, "MANUFACTURER_DATASHEET"),
                          "generator-no-load-fuel-rate": no_load,
                          "generator-minimum-load": stated_or_assumed(gen.get("minimum_load_pct"), "generator.minimum_load_pct")},
            "BATTERY": {"battery-energy-capacity": (capacity, "MANUFACTURER_DATASHEET"),
                        "battery-charge-taper-start": stated_or_assumed(bat.get("charge_taper_start_soc_pct"),
                                                                        "battery.charge_taper_start_soc_pct")}}


def judge_datasheet(slot: dict, document: dict, site_code: str = DATASHEET_SITE) -> Result:
    """C-DD16: the world's Kobo Site (its `/2` foundation, which the writer runs on) carries each mapped value and its
    `-basis` sibling, each with source SITE, version 1, and the generator's and battery's ratings equal the mapped ones."""
    try:
        want = datasheet_expectation(slot)
    except (ValueError, KeyError, ZeroDivisionError) as error:
        return Result("C-DD16", False, [f"slot cannot be mapped (fit or slot): {error}"])
    site = next((s for s in document.get("sites", []) if s.get("code") == site_code), None)
    if site is None:
        return Result("C-DD16", False, [f"{site_code} is not in the /2 file"])
    detail, compared = [], 0
    rating_of = {"GENERATOR": "generator-rated-power", "BATTERY": "battery-energy-capacity"}
    for kind, values in want.items():
        found = [c for c in site.get("components", []) if c.get("type") == kind]
        if len(found) != 1:
            detail.append(f"{site_code} has {len(found)} {kind} components, not one")
            continue
        props = {p.get("property_key"): p for p in found[0].get("properties", [])}
        rating = (found[0].get("rating") or {}).get("value")
        if rating is None or Decimal(str(rating)) != Decimal(values[rating_of[kind]][0]):
            detail.append(f"{kind} rating {rating} != {values[rating_of[kind]][0]}")
        for key, (text, basis) in values.items():
            for name, expected in ((key, text), (f"{key}-basis", basis)):
                compared += 1
                p = props.get(name)
                if p is None:
                    detail.append(f"{kind} {name}: missing (want {expected})")
                    continue
                got = p.get("value")
                same = (got == expected) if name.endswith("-basis") else (
                    not isinstance(got, (str, bool)) and got is not None and Decimal(str(got)) == Decimal(expected))
                if not same:
                    detail.append(f"{kind} {name}: {got!r} != {expected}")
                if (p.get("source"), p.get("source_version")) != ("SITE", 1):
                    detail.append(f"{kind} {name}: source {p.get('source')} v{p.get('source_version')} != SITE v1")
    return Result("C-DD16", not detail, detail[:20] or [f"{compared} properties and 2 ratings equal the slot's mapping"])


def check_datasheet(inputs: Inputs) -> Result:
    """C-DD16 on the committed slot and Lakeside's `/2` file."""
    return judge_datasheet(json.loads(DATASHEET_SLOT.read_text(encoding="utf-8")),
                           json.loads(DATASHEET_FILE.read_text(encoding="utf-8")))


LIVE: dict[str, Callable[[Inputs], Result]] = {
    "C-DD11": check_two_processes_agree, "C-DD12": check_no_oracle_read, "C-DD21": check_property_table_parity,
    "C-DD16": check_datasheet,
    "C-DD1": check_cast, "C-DD2": _judged(judge_kinds), "C-DD3": _judged(judge_identities),
    "C-DD4": _judged(judge_leaves_and_nodes), "C-DD13": check_tenant_isolation, "C-DD6": check_failures,
    "C-DD5": check_cadence, "C-DD7": check_meter_books, "C-DD20": check_story}


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
            for line in r.info:
                print(f"  {line}")
    return 0 if all(r.passed for r in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
