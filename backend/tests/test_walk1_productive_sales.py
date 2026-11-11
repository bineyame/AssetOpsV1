"""WALK1-3 §4.3-§4.5: measured productive use (pure) and the Kobo Grow row's estimated productive-use sales.

Every case of the §4.4 table, the priced subline, the MG-1 reading and the vocabulary of the new strings. The fake
ports are OUT-B2's (`test_out_b2_mini.Fake`); the three productive-use ports are replaced per case.
"""
from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timedelta, timezone
from decimal import ROUND_HALF_UP, Decimal
from typing import Any
from uuid import UUID

import pytest

from assetops_backend.chain.outcomes import NodeInputs, OutcomeEvaluator
from assetops_backend.chain.ports import SnapshotRow
from assetops_backend.chain.vocabulary import days_line
from assetops_backend.outcomes.objectives import judge_month
from assetops_backend.site_outcomes import mini, objective_facts
from assetops_backend.site_outcomes.board import assemble
from assetops_backend.site_outcomes.mini import compose
from assetops_backend.site_outcomes.productive_use import productive_energy
from link_parity import checked
from test_out_b2_mini import C, DAY, DEPTH, ZONE, Fake, contributor

GROW = mini.GROW
LO = datetime(DAY.year, DAY.month, DAY.day, tzinfo=timezone.utc)
HI = LO + timedelta(days=1)
MILL = {"asset_code": "load-mill", "asset_id": "a-mill", "name": "Grain mill"}
REV = "0b8a1f1e-0000-4000-8000-000000000001"   # the declared price's assumption revision
PRICE = {"selection": {"state": "PRICED", "revision_id": REV, "price": {"value": "0.2500", "currency": "USD"}}}
NO_PRICE = {"selection": {"state": "NO_PRICE", "price": None}}
ASSUMPTIONS = f"/sites/{C}/financials/assumptions"


def reading(start: datetime, minutes: int = 5, kw: Any = "12", quality: str = "GOOD") -> dict[str, Any]:
    return {"start": start, "end": start + timedelta(minutes=minutes), "value_kw": kw, "quality": quality}


def story_day(kw: Any = "12") -> list[dict[str, Any]]:
    """The gateway's measured hours on story days: 03:00-11:00 UTC in five-minute intervals."""
    return [reading(LO + timedelta(hours=3, minutes=5 * n), kw=kw) for n in range(96)]


# --------------------------------------------------------------- pure measured energy

def test_exact_sum_over_good_intervals() -> None:
    got = productive_energy(story_day("12.6"), LO, HI)
    assert got == {"kwh": Decimal("100.8"), "measured_seconds": 8 * 3600, "evidence_count": 96, "conflict_assets": []}


def test_clipping_to_the_window() -> None:
    got = productive_energy([reading(LO - timedelta(minutes=3), kw="6")], LO, HI)  # 2 of 5 minutes inside
    assert got == {"kwh": Decimal("0.2"), "measured_seconds": 120, "evidence_count": 1, "conflict_assets": []}
    assert productive_energy([reading(HI, kw="6")], LO, HI)["kwh"] is None  # touching the end is outside


def test_non_good_readings_are_gaps_never_zero() -> None:
    rows = [reading(LO, quality="UNAVAILABLE"), reading(LO + timedelta(minutes=5), kw=None),
            reading(LO + timedelta(minutes=10), kw="NaN")]
    assert productive_energy(rows, LO, HI) == {"kwh": None, "measured_seconds": 0, "evidence_count": 0, "conflict_assets": []}
    assert productive_energy([], LO, HI)["kwh"] is None


def test_gaps_and_overlaps_in_measured_seconds() -> None:
    rows = [{**reading(LO, kw="1"), "asset_id": "a1"}, {**reading(LO + timedelta(minutes=20), kw="1"), "asset_id": "a1"},
            {**reading(LO, kw="2"), "asset_id": "a2"}]  # two users over the same five minutes
    got = productive_energy(rows, LO, HI)
    assert got["measured_seconds"] == 600 and got["evidence_count"] == 3
    assert got["kwh"] == Decimal(4) * Decimal(300) / Decimal(3600) and got["conflict_assets"] == []


def test_one_assets_overlapping_readings_are_conflicting_with_no_partial_sum() -> None:
    """Review M1: a re-delivered batch over the same interval must not double-count."""
    rows = [{**reading(LO, kw="5"), "asset_id": "a1"}, {**reading(LO + timedelta(minutes=2), kw="5"), "asset_id": "a1"},
            {**reading(LO, kw="2"), "asset_id": "a2"}]
    got = productive_energy(rows, LO, HI, {"a1": "Grain mill", "a2": "Pump"})
    assert got["kwh"] is None and got["conflict_assets"] == ["Grain mill"]
    touching = [{**reading(LO, kw="5"), "asset_id": "a1"}, {**reading(LO + timedelta(minutes=5), kw="5"), "asset_id": "a1"}]
    assert productive_energy(touching, LO, HI)["kwh"] is not None


def test_zero_use_is_a_measured_zero() -> None:
    assert productive_energy(story_day("0"), LO, HI) == {"kwh": Decimal(0), "measured_seconds": 28800,
                                                         "evidence_count": 96, "conflict_assets": []}


# --------------------------------------------------------------- composer (§4.4 table)

MG1 = [{"outcome_key": "MG-1", "measure_key": "productive_use_kwh", "target": "300", "currency": None,
        "source": "DECLARED", "id": "o1", "source_note": "Declared for the demonstration"}]


def snapshot(readings: Any, price: Any = PRICE, grade: str = "COMPLETE") -> tuple[SnapshotRow, ...]:
    """CH6a3-R2 H1: the board day's stored `productive_kwh` row as the producer writes it from the same readings
    (`chain/measure_impls.py` ProductiveEnergy: kWh to the watt-hour, money on the unrounded energy at the selected
    price, with its revision). No row when the readings give no energy (no readings, a conflicting day)."""
    e = productive_energy(readings, LO, HI)
    if e["kwh"] is None or e["conflict_assets"]:
        return ()
    sel = (price or {}).get("selection") or {}
    rate = (sel.get("price") or {}).get("value")
    money = None if sel.get("state") != "PRICED" or rate is None else {
        "amount": f"{(e['kwh'] * Decimal(rate)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP):f}",
        "currency": "USD", "assumption_revision_id": sel["revision_id"]}
    value = {"kwh": f"{e['kwh'].quantize(Decimal('0.001'), rounding=ROUND_HALF_UP):f}",
             "measured_seconds": e["measured_seconds"]}
    return (SnapshotRow(UUID(int=1), UUID(int=2), DAY, "ASSET", "asset:a-mill", "productive_kwh", "MEASURED", 1, True,
                        28800, e["measured_seconds"], "100", grade, value, money, "p", "c", 1, "fp"),)


def mg1_month(rows: tuple[SnapshotRow, ...]):
    """The MG-1 month reading and verdict recomputed from the stored rows (`judge_month`, the evaluator's R5)."""
    o = objective_facts.from_rows(MG1, mini.num)[0]
    reading, _, _ = OutcomeEvaluator()._month_reading(
        NodeInputs(C, "mini_grid", ZONE, (DAY, DAY), rows, (o,)), "productive_kwh")
    return reading, judge_month(o, reading)


def assert_mg1(comp: Any, rows: tuple[SnapshotRow, ...], **kw: Any):
    """CH6a3-R2 H1: MG-1 lives in `nodes["MG-1"]["kpi"]` (R5). Without an objective it reads "No target set yet";
    with the declared one its verdict equals `judge_month` over the stored rows. Returns the recomputed reading."""
    assert comp.facts.nodes["MG-1"]["kpi"]["text"] == "No target set yet"
    declared, _ = run(objectives=MG1, **kw)
    reading, verdict = mg1_month(rows)
    assert declared.facts.nodes["MG-1"]["kpi"]["value"] == verdict
    return reading


def run(users: Any = (MILL,), readings: Any = None, price: Any = PRICE, refuse: tuple[str, ...] = (),
        fake: Fake | None = None, objectives: Any = None, snap: Any = None, grade: str = "COMPLETE"):
    fake = fake or Fake()
    readings = story_day() if readings is None else readings
    rows = (snapshot(readings, price, grade) if users else ()) if snap is None else tuple(snap)

    def port(name: str, value: Any):
        def call(*args: Any) -> Any:
            if name in refuse:
                raise RuntimeError(f"{name} refused")
            return value
        return call

    ports = replace(fake.ports(), productive_users=port("users", list(users)),
                    productive_readings=port("readings", readings),
                    productive_price=port("price", price))
    base_day = ports.chain_day

    def chain_day(days: Any, board_days: Any) -> Any:  # H1: the stored snapshot rows of the same day read
        facts = base_day(days, board_days)
        return facts if facts is None else replace(facts, rows=rows)

    ports = replace(ports, chain_day=chain_day)
    if objectives is not None:
        ports = replace(ports, objectives=lambda: objectives)
    comp = compose(ports, site_code=C, day=DAY, site_timezone=ZONE)
    return comp, {r["category"]: r for r in assemble(comp.facts)}[GROW]


def keys(row: dict) -> list[str]:
    return [c["key"] for c in row["contributors"]]


def test_no_productive_user_declared() -> None:
    comp, row = run(users=())
    assert row["headline"] == "18–24.3 kW of daytime solar unused" and row["headline_money"] is None
    assert row["subline"] == mini.GROW_SUBLINE
    assert keys(row) == ["productive_sales", "productive_use", "cash_collected", "site_earnings"]  # WALK1-3b §A2.3
    assert contributor(row, "productive_sales")["text"] == (
        "Not available yet · no productive users identified for this site")
    assert assert_mg1(comp, (), users=()).value is None  # no productive user: no stored row, nothing totalled
    assert comp.read_state == "AVAILABLE"


def test_users_without_readings() -> None:
    _, row = run(readings=[reading(LO, quality="UNAVAILABLE")])
    assert row["headline"] == "18–24.3 kW of daytime solar unused" and row["headline_money"] is None
    assert row["subline"] is None
    assert contributor(row, "productive_sales")["text"] == "Not available yet · no measured use by Grain mill on this day"
    assert contributor(row, "productive_price")["text"] == "Declared at 0.25 USD per kWh"


def test_measured_use_without_a_price() -> None:
    comp, row = run(price=NO_PRICE)
    assert row["headline"] == "18–24.3 kW of daytime solar unused" and row["headline_money"] is None
    assert row["subline"] is None
    sales = contributor(row, "productive_sales")
    # CH6a3-R2 H3 ONE-SOURCE: an unpriced day's stored row has no money, so the earnings claim is NOT_KNOWN and the
    # line states no live kWh beside it; the price line still says why.
    assert sales["text"] == "Not known yet · Complete readings on 1 of 1 day"
    assert sales["confidence"] is None
    assert checked(contributor(row, "productive_price")) == {
        "key": "productive_price", "label": "Price per kWh", "text": "Not available yet · no price per kWh declared",
        "confidence": None, "href": ASSUMPTIONS}
    # R5: MG-1 reads month to date from the stored rows (Nairobi local October through the 20th)
    reading = assert_mg1(comp, snapshot(story_day(), NO_PRICE), price=NO_PRICE)
    assert (reading.value, reading.checked_days, reading.elapsed_days) == (Decimal("96.000"), 1, 20)


def test_priced_zero_use() -> None:
    comp, row = run(readings=story_day("0"))
    assert row["headline"] == "18–24.3 kW of daytime solar unused"  # L3: spare solar leads
    assert row["headline_money"] is None
    assert contributor(row, "productive_sales")["text"] == "0 kWh used by Grain mill in 8 measured hours"
    assert contributor(row, "productive_sales")["confidence"] == {"label": "Declared", "tone": "neutral"}
    assert assert_mg1(comp, snapshot(story_day("0")), readings=story_day("0")).value == Decimal(0)


def test_priced_zero_use_without_spare_solar_leads_with_not_used() -> None:
    """L3: the zero-use headline is used only when there is no spare-solar headline."""
    none = dict(DEPTH, renewable={"headroom_kw": {"low": None, "high": None}, "eligible_days": None,
                                  "assessed_days": None})
    _, row = run(readings=story_day("0"), fake=Fake(cards=none))
    assert row["headline"] == "No productive-use sales on this day: Grain mill not used"


def test_overlapping_readings_of_one_user_are_not_estimated() -> None:
    twice = story_day() + story_day()
    for r in twice:
        r["asset_id"] = "a-mill"
    comp, row = run(readings=twice)
    assert row["headline"] == "18–24.3 kW of daytime solar unused" and row["headline_money"] is None
    assert row["subline"] is None
    assert contributor(row, "productive_sales")["text"] == (
        "Not available yet · Grain mill has conflicting readings on this day, so use is not estimated")
    assert assert_mg1(comp, (), readings=twice).value is None  # a conflicting day stores no counted row
    two = {"asset_code": "load-pump", "asset_id": "a-pump", "name": "Pump"}
    both = [{**r, "asset_id": "a-pump"} for r in twice] + [{**r, "asset_id": "a-mill"} for r in twice]
    _, row2 = run(users=(MILL, two), readings=both)
    assert contributor(row2, "productive_sales")["text"] == (
        "Not available yet · Grain mill, Pump have conflicting readings on this day, so use is not estimated")


def test_priced_estimate_leads_the_grow_row() -> None:
    comp, row = run(readings=story_day("12.6225"))  # 100.98 kWh x 0.25 = 25.245 -> 25.25 (half up)
    assert row["headline"] == "estimated productive-use sales"
    assert row["headline_money"] == {"amount_low": "25.25", "amount_high": "25.25", "currency": "USD"}
    assert row["subline"] == ("101 kWh used by Grain mill in 8 measured hours, at the declared price of 0.25 USD "
                              "per kWh · not billed or collected")
    assert keys(row) == ["productive_sales", "productive_use", "productive_price", "cash_collected",
                         "site_earnings"]  # WALK1-3b §A2.3
    assert checked(contributor(row, "productive_sales")) == {
        "key": "productive_sales", "label": "Productive-use sales",
        "text": "101 kWh used by Grain mill in 8 measured hours",
        "confidence": {"label": "Declared", "tone": "neutral"}, "href": None}
    assert checked(contributor(row, "productive_price")) == {
        "key": "productive_price", "label": "Price per kWh", "text": "Declared at 0.25 USD per kWh",
        "confidence": {"label": "Declared", "tone": "neutral"}, "href": ASSUMPTIONS}
    # spare solar stays in its contributor and the Portfolio fallback value
    assert contributor(row, "productive_use")["text"] == ("Spare solar on 1 of 1 well-observed day"
                                                     " · 4 of the last 5 days without complete readings")
    assert comp.short_values == {GROW: "18–24.3 kW unused"}
    # WALK1-3b: MG-1 carries the month-to-date kWh (only this day has readings) and is complete only at month end
    mg1 = assert_mg1(comp, snapshot(story_day("12.6225")), readings=story_day("12.6225"))
    assert mg1.value == Decimal("100.98") and mg1.complete is False
    assert (mg1.checked_days, mg1.elapsed_days, mg1.month_days) == (1, 20, 31)


def test_low_day_states_nothing_but_not_known_with_its_days_line() -> None:
    """CH6a3-R2 H1/H3 (ONE-SOURCE): a LOW stored day is never totalled, so the earnings claim is NOT_KNOWN; the live
    read's 101 kWh and price must not appear beside it. Money None, subline None, the sales line "Not known yet"
    with the claim's own days line."""
    comp, row = run(readings=story_day("12.6225"), grade="LOW")
    earn = comp.facts.nodes["MG-1"]["earnings"]
    assert earn["value"] is None and earn["text"] == "Not known yet"
    assert row["headline_money"] is None and row["subline"] is None
    line = days_line(earn["days"], DAY)
    assert line == "Complete readings on 0 of 1 day · 1 with too few readings, not counted"
    assert contributor(row, "productive_sales")["text"] == f"Not known yet · {line}"
    assert "101" not in str(row["subline"]) and all("kWh used" not in c["text"] for c in row["contributors"])


def test_one_measured_hour_is_singular() -> None:
    _, row = run(readings=[reading(LO + timedelta(hours=3, minutes=5 * n)) for n in range(12)])
    assert contributor(row, "productive_sales")["text"] == "12 kWh used by Grain mill in 1 measured hour"


@pytest.mark.parametrize("port", ["users", "readings", "price"])
def test_a_failed_port_is_not_loaded_and_partial(port: str) -> None:
    comp, row = run(refuse=(port,))
    assert comp.read_state == "PARTIAL"
    texts = {c["key"]: c["text"] for c in row["contributors"]}
    if port == "price":
        assert texts["productive_price"] == mini.NOT_LOADED
        # H3 ONE-SOURCE: the stored row is priced, so the money and the sales line come from the earnings claim;
        # with no price read there is no single-revision price line, so no subline
        assert row["headline"] == "estimated productive-use sales"
        assert row["headline_money"] == {"amount_low": "24.00", "amount_high": "24.00", "currency": "USD"}
        assert texts["productive_sales"] == "96 kWh used by Grain mill in 8 measured hours"
        assert row["subline"] is None
    else:
        assert row["headline"] == "18–24.3 kW of daytime solar unused" and row["headline_money"] is None
        assert texts["productive_sales"] == mini.NOT_LOADED
        if port == "users":
            assert row["subline"] is None  # L4: no GROW_SUBLINE when the read failed


def test_row_state_with_the_estimate_is_unchanged() -> None:
    """Pre-flight E6: the estimate itself never sets the Grow row state; WALK1-3b judges the declared target."""
    _, priced = run(readings=story_day("12"))
    _, undeclared = run(users=())
    assert priced["state"] == undeclared["state"] == "OPPORTUNITY"  # no objective: the fixture's spare-solar signal
    # Kobo with the declared monthly MG-1 target (demo-objectives.json) and one checked day: WALK1-3b reads "Too early
    # to judge" (Unknown) under the default minimum of 3 checked days; with no productive user nothing is judged.
    kobo = dict(DEPTH, renewable={"headroom_kw": {"low": None, "high": None}, "eligible_days": None,
                                  "assessed_days": None})
    mg1 = MG1
    _, estimate = run(readings=story_day("21.0375"), fake=Fake(cards=kobo), objectives=mg1)
    _, none = run(users=(), fake=Fake(cards=kobo), objectives=mg1)
    assert estimate["headline_money"] == {"amount_low": "42.08", "amount_high": "42.08", "currency": "USD"}
    assert estimate["state"] == none["state"] == "UNKNOWN"
    reason = {r["key"]: r["reason"] for r in estimate["outcomes"]}["MG-1"]
    assert reason == "OBJECTIVE_TOO_EARLY"
    assert {r["key"]: r["reason"] for r in none["outcomes"]}["MG-1"] == "OBJECTIVE_NOT_JUDGED"


def test_new_strings_are_in_copy_and_plain() -> None:
    from test_out_b2_vocabulary import _patterns  # the OUT-B vocabulary scan (productVocabulary.json)

    patterns = _patterns()
    new = [mini.SALES_NO_USERS, mini.PRICE_NOT_DECLARED, mini.SALES_HEADLINE]
    assert all(x in mini.COPY for x in new)
    for row in (run()[1], run(users=())[1], run(price=NO_PRICE)[1], run(readings=story_day("0"))[1]):
        texts = [row["headline"] or "", row["subline"] or "", *(c["text"] for c in row["contributors"])]
        hits = [(t, name) for t in texts for name, pattern in patterns if pattern.search(t)]
        assert hits == [], hits
    ours = [mini.SALES_NO_USERS, mini.SALES_NO_READINGS, mini.SALES_USED, mini.SALES_NO_PRICE, mini.PRICE_DECLARED,
            mini.PRICE_NOT_DECLARED, mini.SALES_HEADLINE, mini.SALES_ZERO_HEADLINE, mini.SALES_SUBLINE, mini.MG1_SO_FAR,
            mini.MG1_PACE, mini.MG1_TOO_EARLY, mini.MG1_MISSED]
    for word in ("income", "revenue", "gross", "collected", "billed"):  # an estimate, never billed or collected
        assert [t for t in ours if word in t.lower()] == ([mini.SALES_SUBLINE] if word in ("collected", "billed")
                                                          else []), word
    assert mini.SALES_SUBLINE.endswith("· not billed or collected")


# --------------------------------------------------------------- B4 binding (site_outcomes/read.py)

def test_b4_binds_the_productive_ports_to_the_reader_and_the_price_series() -> None:
    from uuid import uuid4

    from assetops_backend.site_outcomes.read import BoardServices, SiteOutcomeBoardService, SiteRef

    calls: list[tuple] = []

    class Depth:
        def productive_users(self, **kw):
            calls.append(("users", kw))
            return [MILL]

        def productive_readings(self, **kw):
            calls.append(("readings", kw))
            return []

    class Assumptions:
        def series(self, t, s, key, *, valid_at, recorded_at):
            calls.append(("price", (t, s, key, valid_at, recorded_at)))
            return {"selection": None}

    t, s = uuid4(), uuid4()
    known = datetime(2026, 10, 7, tzinfo=timezone.utc)
    ports = SiteOutcomeBoardService(BoardServices(mini_depth=Depth(), assumptions=Assumptions())).mini_ports(
        SiteRef(t, s, C, "Kobo", "MINIGRID", ZONE), known)
    assert ports.productive_users(LO) == [MILL]
    assert ports.productive_readings(["a-mill"], LO, HI) == []
    assert ports.productive_price(LO) == {"selection": None}
    assert calls == [("users", {"tenant_id": t, "site_id": s, "at": LO, "known_at": known}),
                     ("readings", {"tenant_id": t, "site_id": s, "asset_ids": ["a-mill"], "lo": LO, "hi": HI,
                                   "known_at": known}),
                     ("price", (t, s, "productive_use_price_per_kwh", LO, known))]


def month_rows(kwh_per_day: str, days: range) -> tuple[SnapshotRow, ...]:
    """Stored COMPLETE `productive_kwh` rows for the given October days (MG-1 reads the month to the board day)."""
    one = snapshot(story_day())[0]
    return tuple(replace(one, local_day=DAY.replace(day=d), value={"kwh": kwh_per_day, "measured_seconds": 28800})
                 for d in days)


def test_mg1_snapshot_verdict_sets_the_row_state_and_chip() -> None:
    """CH6a3-R2 M3: the board-level path from an MG-1 snapshot verdict to the Grow row state, its chip and the
    objectives wire. MET (3 x 120 kWh >= 300) -> ON_TRACK, "Met"; BEHIND_PACE (3 x 5 kWh, 15 x 31 < 300 x 3) ->
    WATCH, "Behind pace"; no objective -> OPPORTUNITY from the open headroom thread, with its potential node."""
    from assetops_backend.site_outcomes.board import objectives_wire

    def line(row: dict) -> dict:
        return next(c for c in row["contributors"] if c["key"] == "declared_objective_MG-1"
                    or c["label"].startswith("Declared objective"))

    comp, met = run(objectives=MG1, snap=month_rows("120", range(18, 21)))
    assert comp.facts.nodes["MG-1"]["kpi"]["value"] == "MET"
    assert met["state"] == "ON_TRACK" and line(met)["confidence"] == {"label": "Met", "tone": "green"}
    assert {o["key"]: o["reason"] for o in met["outcomes"]}["MG-1"] == "OBJECTIVE_MET"
    assert next(w for w in objectives_wire(comp.facts) if w["outcome_key"] == "MG-1")["verdict"] == "MET"
    comp, behind = run(objectives=MG1, snap=month_rows("5", range(18, 21)))
    assert comp.facts.nodes["MG-1"]["kpi"]["value"] == "BEHIND_PACE"
    assert behind["state"] == "WATCH" and line(behind)["confidence"] == {"label": "Behind pace", "tone": "amber"}
    comp, none = run(snap=month_rows("120", range(18, 21)))
    assert comp.facts.nodes["MG-1"]["kpi"]["text"] == "No target set yet"
    assert none["state"] == "OPPORTUNITY"
    assert none["nodes"]["potential"]["key"].startswith("potential.") and none["nodes"]["potential"]["value"]
