"""DIESEL-K4a L0 (`.agent/build-sheet-DIESEL-1.md` §9j.8 A1-A7, §9k.5 A9): the unexplained-fuel Finding's wording,
money, lifecycle and the no-sum guard, with no database. Every "must fail" names the mutation it kills."""

from __future__ import annotations

import ast
import inspect
import json
import re
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from fractions import Fraction
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

import pytest

from assetops_backend.actions.verification_rules import fmt, parse_exact
from assetops_backend.financials.adapters.postgres_consequence_store import PostgresConsequenceStore
from assetops_backend.financials.fuel_cost import PriceSelection
from assetops_backend.financials.recompute import NO_OP_ASSET, evidence_no_op
from assetops_backend.fuel_balance import finding_text as ft
from assetops_backend.fuel_balance import findings_service as fs
from assetops_backend.fuel_balance.model import FuelBalanceWindow, FuelFinding

REPO = Path(__file__).resolve().parents[2]
PROBE = json.loads((REPO / ".agent" / "DIESEL-F0" / "probe-result.json").read_text(encoding="utf-8"))
TZ = "Africa/Dar_es_Salaam"
NIGHT4 = date(2026, 10, 4)
BAND = PROBE["nights"][3]["readings"]
LOW, HIGH = Fraction(BAND["residual_low"]["exact"]), Fraction(BAND["residual_high"]["exact"])
GAP = ((datetime(2026, 10, 4, 21, 45, tzinfo=timezone.utc), datetime(2026, 10, 4, 23, 30, tzinfo=timezone.utc)),)
PRICE = PriceSelection("PRICED", None, str(uuid4()), Decimal("1.25"), "USD", str(uuid4()))
FORBIDDEN = ("theft", "stolen", "stole", "siphon", "pilfer")
MINI_PERFORMANCE = REPO / "frontend" / "src" / "sites" / "MiniPerformance.tsx"
NEW_NOTICE = ("Unexplained fuel is fuel that left the tank and that the generator's modelled use and the recorded "
              "deliveries don't account for, within a stated margin. It does not say why the fuel left, and it is "
              "never added to the generator's possible extra fuel.")
NEW_RESIDUAL = "Needs every term with a supported range; never says why fuel left"

EXPECTED_CLAIM = ("About 95.7–144.3 L left the tank on the night of 4 Oct (6 pm to noon) that the generator's "
                  "modelled use and the recorded deliveries don't explain.")
EXPECTED_GAP = "The tank sensor sent no readings from 00:45 to 02:30."
EXPECTED_MONEY = ("Worth about 119.57–180.43 USD at your declared 1.25 USD per litre "
                  "(a modelled range that includes the stated margin)")


def window(low: Fraction | None = LOW, high: Fraction | None = HIGH, *, state: str = "UNEXPLAINED",
           spans=GAP, revision: int = 1, wid: UUID | None = None, night: date = NIGHT4) -> FuelBalanceWindow:
    start = datetime(night.year, night.month, night.day, 15, tzinfo=timezone.utc)
    gap = sum(int((b - a).total_seconds() // 60) for a, b in spans)
    return FuelBalanceWindow(
        id=wid or uuid4(), tenant_id=uuid4(), site_id=uuid4(), tank_asset_id=uuid4(), generator_asset_id=uuid4(),
        night_date=night, window_start=start, window_end=start + timedelta(hours=18), revision=revision,
        parameter_version="fuel-balance-1/v1", recorded_at=start + timedelta(hours=21), state=state, reason=None,
        residual_low=low, residual_high=high, gap_minutes=gap, gap_spans=tuple(spans),
        limitations=("REPORTING_GAP",) if gap else (), terms={"accuracy_l": "10"}, evidence_ids=(), record_ids=(),
        input_sha256="a" * 64)


class FakeConnection:
    def __init__(self) -> None:
        self.params: list[dict[str, Any]] = []

    def execute(self, statement: Any, params: dict[str, Any] | None = None) -> None:
        self.params.append(dict(params or {}))


def stored(w: FuelBalanceWindow, price: PriceSelection = PRICE) -> dict[str, Any]:
    """The row `fuel_residual_append` writes (the real method, on a recording connection)."""
    c = FakeConnection()
    PostgresConsequenceStore.fuel_residual_append(c, w.tenant_id, w.site_id, uuid4(), uuid4(), w, price,
                                                  w.recorded_at)
    p = c.params[-1]
    return {"state": p["state"], "price_reason": p["reason"], "currency": p["cur"], "price_value": p["pv"],
            "amount_low": p["al"], "amount_high": p["ah"], "litres_low": p["ll"], "litres_high": p["lh"]}


def finding(w: FuelBalanceWindow, consequence: Any, lifecycle: str = "SUPPORTED") -> FuelFinding:
    return FuelFinding(uuid4(), uuid4(), 1, lifecycle, w.night_date, w, consequence, w.recorded_at)


# --- A1 text, night 4 ---------------------------------------------------------------------------------------------


def test_a1_night4_lines_exactly() -> None:
    w = window()
    lines = ft.finding_lines(finding(w, stored(w)), TZ)
    assert lines["claim"] == EXPECTED_CLAIM
    assert lines["gap"] == EXPECTED_GAP
    assert lines["money"] == EXPECTED_MONEY
    assert lines["title"] == ft.TITLE and lines["not_why"] == ft.NOT_WHY and lines["no_longer"] is None
    assert lines["margin"] == ("The range allows for the tank sensor's declared accuracy of 10 L at each reading, "
                               "10 % either way on the generator's modelled use, and 1 % on each recorded delivery.")


def test_a1_litres_round_half_even_and_money_is_exact() -> None:
    # must fail if litres round half-up at a .x5 case
    assert ft.claim_line(Fraction("1.25"), Fraction("2.35"), NIGHT4).startswith("About 1.2–2.4 L ")
    # must fail if money2 is replaced by round(x, 2) on a float (2.675 is 2.67499... as a float)
    assert ft.money(Fraction(2675, 1000)) == "2.68" and f"{round(2.675, 2):.2f}" == "2.67"
    assert ft.money(Fraction(1, 3)) == "0.33" and ft.money("119.625") == "119.62"


# --- A2 gap --------------------------------------------------------------------------------------------------------


def test_a2_gap_absent_and_two_spans_in_site_time() -> None:
    w = window(spans=())
    assert ft.finding_lines(finding(w, stored(w)), TZ)["gap"] is None
    two = GAP + ((datetime(2026, 10, 5, 0, 0, tzinfo=timezone.utc), datetime(2026, 10, 5, 1, 10, tzinfo=timezone.utc)),)
    line = ft.finding_lines(finding(window(spans=two), None), TZ)["gap"]
    assert line == "The tank sensor sent no readings from 00:45 to 02:30, and from 03:00 to 04:10."
    assert "21:45" not in line  # must fail if the spans are rendered in UTC


# --- A3 unpriced ---------------------------------------------------------------------------------------------------


@pytest.mark.parametrize("reason, literal", [
    ("NO_PRICE", ft.UNPRICED_NO_PRICE), ("PRICE_CONFLICT", ft.UNPRICED_PRICE_CHANGES),
    ("PRICE_SPANS_WINDOW", ft.UNPRICED_PRICE_CHANGES), ("PRICE_REVISION_MISSING", ft.UNPRICED_OTHER),
    ("PRICE_UNIT_MISMATCH", ft.UNPRICED_OTHER), ("PRICE_INVALID", ft.UNPRICED_OTHER)])
def test_a3_each_unpriced_reason_has_its_literal(reason: str, literal: str) -> None:
    w = window()
    row = stored(w, PriceSelection("UNPRICED", reason))
    assert row["state"] == "UNPRICED" and row["amount_low"] is None and row["price_value"] is None
    money = ft.finding_lines(finding(w, row), TZ)["money"]
    assert money == literal and not re.search(r"\d", money)


# --- A4 wording guard ----------------------------------------------------------------------------------------------


def _without_line_comments(source: str) -> str:
    """The product text of a TSX file: `//` line comments removed (the MD-FUEL-K-2 deviation comments quote the v69
    words they replace, by ruling DIESEL-1-R3j §9j.7)."""
    return "\n".join(line for line in source.splitlines() if not line.lstrip().startswith("//"))


def test_a4_no_k4a_or_fuel_page_string_says_theft() -> None:
    source = MINI_PERFORMANCE.read_text(encoding="utf-8")
    assert NEW_NOTICE in source and NEW_RESIDUAL in source
    for text in (*ft.LITERALS, NEW_NOTICE, NEW_RESIDUAL, _without_line_comments(source)):
        lowered = text.lower()
        assert not [w for w in FORBIDDEN if w in lowered], text[:80]
    # non-vacuous: the comment really quotes the replaced words, and the scan would see an old string
    assert "theft" in source.lower()
    assert "theft" in _without_line_comments(source + '\n  "It cannot establish theft"').lower()


# --- A5 amounts exact ----------------------------------------------------------------------------------------------


def test_a5_amounts_are_exact_litres_times_price() -> None:
    row = stored(window())
    assert parse_exact(row["amount_low"]) == LOW * Fraction(5, 4)
    assert parse_exact(row["amount_high"]) == HIGH * Fraction(5, 4)
    assert row["amount_low"] == fmt(parse_exact(row["amount_low"]))
    assert (row["litres_low"], row["litres_high"]) == (fmt(LOW), fmt(HIGH))
    # must fail if amounts come from the 0.1-L display litres (95.7 x 1.25 = 119.625 -> "119.62")
    assert ft.money(row["amount_low"]) == "119.57" and ft.money(row["amount_high"]) == "180.43"


# --- A6 never summed (static) --------------------------------------------------------------------------------------

FUEL_BALANCE = REPO / "backend" / "assetops_backend" / "fuel_balance"
FORBIDDEN_IMPORTS = ("fuel_cost_v2", "financial_consequence")


def _amount_name(node: ast.AST) -> bool:
    name = node.id if isinstance(node, ast.Name) else node.attr if isinstance(node, ast.Attribute) else (
        node.value if isinstance(node, ast.Constant) and isinstance(node.value, str) else None)
    if isinstance(node, ast.Subscript):
        return _amount_name(node.slice)
    if isinstance(node, ast.Call) and node.args:
        return _amount_name(node.args[0])
    return isinstance(name, str) and name.startswith("amount_")


def summed(tree: ast.AST) -> list[str]:
    hits = []
    for node in ast.walk(tree):
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add) and _amount_name(node.left) \
                and _amount_name(node.right):
            hits.append(ast.unparse(node))
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "sum" and any(
                _amount_name(x) or (isinstance(x, ast.Name) and x.id.startswith("amount"))
                for arg in node.args for x in ast.walk(arg)):
            hits.append(ast.unparse(node))
    return hits


def imports(tree: ast.AST) -> list[str]:
    out = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            out += [node.module or ""] + [a.name for a in node.names]
        elif isinstance(node, ast.Import):
            out += [a.name for a in node.names]
    return out


def _new_trees() -> list[tuple[str, ast.AST]]:
    trees = [(p.name, ast.parse(p.read_text(encoding="utf-8"))) for p in sorted(FUEL_BALANCE.rglob("*.py"))]
    source = inspect.getsource(PostgresConsequenceStore.fuel_residual_append)
    trees.append(("fuel_residual_append", ast.parse(inspect.cleandoc("\n" + source))))
    return trees


def test_a6_no_fuel_module_imports_dispatch_money_or_sums_amounts() -> None:
    trees = _new_trees()
    assert len(trees) >= 8
    for name, tree in trees:
        names = imports(tree)
        assert not [i for i in names if any(f in i for f in FORBIDDEN_IMPORTS)], name
        assert summed(tree) == [], name


def test_a6_guard_is_not_vacuous() -> None:
    assert summed(ast.parse("x = row['amount_low'] + other.amount_high")) != []
    assert summed(ast.parse("x = sum(amounts)")) != []
    assert summed(ast.parse("x = sum(r['amount_high'] for r in rows)")) != []
    assert summed(ast.parse("x = low * value + sum(deliveries, start)")) == []
    assert imports(ast.parse("from assetops_backend.financials import fuel_cost_v2")) != []


# --- A7 lifecycle table ----------------------------------------------------------------------------------------------


def test_a7_lifecycle_table_all_five_rows() -> None:
    w = str(uuid4())
    assert fs.fuel_transition(False, None, w, "UNEXPLAINED") == ("OPENED", "SUPPORTED")
    for other in ("BELOW_MATERIALITY", "WITHIN_MARGIN", "EXCESS", "NOT_ASSESSED"):
        assert fs.fuel_transition(False, None, w, other) is None
    assert fs.fuel_transition(True, w, w, "UNEXPLAINED") is None
    assert fs.fuel_transition(True, w, w, "WITHIN_MARGIN") is None
    assert fs.fuel_transition(True, str(uuid4()), w, "UNEXPLAINED") == ("SUPPORT_CHANGED", "SUPPORTED")
    assert fs.fuel_transition(True, str(uuid4()), w, "WITHIN_MARGIN") == ("NO_LONGER_SUPPORTED",
                                                                           "NO_LONGER_SUPPORTED")


class _Tx:
    def __enter__(self) -> "_Tx":
        return self

    def __exit__(self, *exc: Any) -> None:
        return None


@dataclass
class FakeStores:
    """In-memory fuel, assessment, Finding and consequence stores (the Finding store applies `fuel_transition`)."""

    current: FuelBalanceWindow | None = None

    def __post_init__(self) -> None:
        self.findings_rows: dict[str, list[tuple[str, str, str]]] = {}   # key -> [(transition, lifecycle, window id)]
        self.ids: dict[str, UUID] = {}
        self.persisted: list[str] = []
        self.consequences: list[str] = []
        self.writes = 0

    # fuel store
    def night_window_on(self, c, t, s, night):
        return datetime(2026, 10, 6, tzinfo=timezone.utc), self.current

    # assessment store
    def transaction(self):
        return _Tx()

    def fuel_balance_persist(self, c, w, now):
        self.persisted.append(str(w.id))
        return {"revision_id": uuid4(), "run_id": uuid4(), "basis": w.input_sha256}

    # Finding store
    def fuel_held(self, c, t, s, w):
        key = f"{w.tank_asset_id}:{w.night_date}"
        rows = self.findings_rows.get(key)
        return None if not rows else (self.ids[key], rows[-1][2])

    def fuel_apply(self, c, t, s, w, persisted, writer, now):
        held = self.fuel_held(c, t, s, w)
        decided = fs.fuel_transition(held is not None, None if held is None else held[1], str(w.id), w.state)
        if decided is None:
            return []
        key = f"{w.tank_asset_id}:{w.night_date}"
        self.ids.setdefault(key, uuid4())
        self.findings_rows.setdefault(key, []).append((decided[0], decided[1], str(w.id)))
        self.writes += 1
        rid = uuid4()
        if decided[1] == "SUPPORTED":
            writer(c, self.ids[key], rid, w, now)
        return [rid]

    # consequence store
    def fuel_residual_append(self, c, t, s, fid, rid, w, price, now):
        self.consequences.append(price.state)


def test_a7_service_statuses_and_the_idempotent_rerun_writes_nothing() -> None:
    fake = FakeStores()
    svc = fs.FuelFindingService(fs.FuelFindingStores(fake, fake, fake, fake, lambda *a: PRICE))
    t, s = uuid4(), uuid4()
    assert svc.raise_night(t, s, NIGHT4).status == fs.NO_WINDOW
    base = window(state="WITHIN_MARGIN")
    fake.current = base
    assert svc.raise_night(t, s, NIGHT4).status == fs.NO_FINDING and fake.persisted == []
    w1 = FuelBalanceWindow(**{**base.__dict__, "id": uuid4(), "revision": 2, "state": "UNEXPLAINED"})
    fake.current = w1
    opened = svc.raise_night(t, s, NIGHT4)
    assert opened.status == fs.OPENED and opened.revision_id is not None and fake.consequences == ["PRICED"]
    writes = (fake.writes, len(fake.persisted), len(fake.consequences))
    again = svc.raise_night(t, s, NIGHT4)
    assert again.status == fs.UNCHANGED and again.finding_id == opened.finding_id and again.revision_id is None
    assert (fake.writes, len(fake.persisted), len(fake.consequences)) == writes   # nothing written
    fake.current = FuelBalanceWindow(**{**base.__dict__, "id": uuid4(), "revision": 3, "state": "UNEXPLAINED"})
    assert svc.raise_night(t, s, NIGHT4).status == fs.REVISED and len(fake.consequences) == 2
    fake.current = FuelBalanceWindow(**{**base.__dict__, "id": uuid4(), "revision": 4, "state": "WITHIN_MARGIN"})
    withdrawn = svc.raise_night(t, s, NIGHT4)
    assert withdrawn.status == fs.WITHDRAWN and len(fake.consequences) == 2   # no consequence when withdrawn
    rows = next(iter(fake.findings_rows.values()))
    assert [r[:2] for r in rows] == [("OPENED", "SUPPORTED"), ("SUPPORT_CHANGED", "SUPPORTED"),
                                     ("NO_LONGER_SUPPORTED", "NO_LONGER_SUPPORTED")]


def test_a7_no_longer_supported_lines() -> None:
    lines = ft.finding_lines(finding(window(), None, "NO_LONGER_SUPPORTED"), TZ)
    assert {k: v for k, v in lines.items() if v is not None} == {
        "title": ft.TITLE, "no_longer": ft.NO_LONGER, "not_why": ft.NOT_WHY}


# --- A9 the evidence path no-ops on a fuel-shaped target (§9k.5) ---------------------------------------------------


def test_a9_evidence_no_op_on_a_fuel_target_is_no_op_asset() -> None:
    gen = str(uuid4())
    start = datetime(2026, 10, 4, 15, tzinfo=timezone.utc)
    target = {"evidence": {"role": "generator_power", "asset_id": gen, "interval_start": start,
                           "interval_end": start + timedelta(minutes=5), "accepted": True},
              "revision": {"revision_no": 1, "latest_revision_no": 1, "episode_start": start,
                           "episode_end": start + timedelta(hours=18), "claim": {}, "generator_asset_id": None}}
    assert evidence_no_op(target) == NO_OP_ASSET
    # non-vacuous: the same reading on a dispatch revision of that generator is not an asset no-op
    target["revision"]["generator_asset_id"] = gen
    assert evidence_no_op(target) != NO_OP_ASSET
