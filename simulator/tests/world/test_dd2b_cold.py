"""DD2.3 (spec `specs/DD-demo-data/spec.md` §5.2; D-DD.49, D-DD.50, D-DD.51): the cold-chain decided books."""

from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime, timedelta
from decimal import Decimal

import pytest

from assetops_contracts.native import LAYOUTS, read_layout
from assetops_simulator.world import exports_cold
from assetops_simulator.world.nodes import NODES
from assetops_simulator.world.books import NODE_LINES
from assetops_simulator.world.profile_csv import load_profile

from .books_support import COLD, EV, build, built, files_by_name, m_site, m_tenant, manifest, tenant_view
from .conftest import load_fixture, site_of

SITES = ("COLD-KIRI", "COLD-MWEA", "COLD-THIKA")
MONTHS = ("2026-07", "2026-08", "2026-09", "2026-10")


def rows(name: str) -> list[dict]:
    return list(files_by_name(built()[3])[f"{COLD}.{name}.csv"].records)


def invoicing(kind: str) -> list[dict]:
    """One kind of the one invoicing export (D-DD.59)."""
    return [r for r in rows("profile.cold-storage-invoicing") if r["kind"] == kind]


def money(records) -> Decimal:
    return sum((Decimal(r["amount"]["value"]) for r in records), Decimal(0))


def leaf(month: str, code: str, field: str):
    view, history = built()[0], built()[1]
    site = next(s for s in tenant_view(view, COLD)["sites"] if s["code"] == code)
    if month == view["accounting_period"]:
        return site["period"]["actual"].get(field)
    return history["tenants"][COLD][site["site"]][month]["actual"].get(field)


def batches_from(ledger: list[dict]) -> dict:
    """Each batch's admission lots and check-outs, read back from the ledger rows alone (independent of the module).
    D-DD.85: a batch has one or more IN lots."""
    out: dict = defaultdict(lambda: {"ins": [], "crates": 0, "outs": []})
    for r in ledger:
        b = out[(r["site_code"], r["body"]["batch_ref"])]
        at = datetime.fromisoformat(r["clocks"]["occurred_at"])
        if r["body"]["direction"] == "IN":
            b["ins"].append((at, int(r["quantity"]["value"])))
            b["crates"] += int(r["quantity"]["value"])
        else:
            b["outs"].append((at, int(r["quantity"]["value"])))
    return out


def counted(ledger: list[dict], code: str, month: str) -> int:
    """Crate-days dated in the month: a crate counts each date from its admission up to the day before it leaves.
    Crates not yet out by `as_of` are counted to the month's end."""
    year, number = map(int, month.split("-"))
    first = date(year, number, 1)
    last = (date(year + number // 12, number % 12 + 1, 1)) - timedelta(days=1)
    total = 0
    for (site, _), b in batches_from(ledger).items():
        if site != code:
            continue
        # a crate counts a date when its lot came in on or before it and it leaves after it (per lot, D-DD.85)
        def dates_from(day: date) -> int:
            return max(0, (last - max(day, first)).days + 1)
        total += sum(n * dates_from(at.date()) for at, n in b["ins"])
        total -= sum(n * dates_from(at.date()) for at, n in b["outs"])
    return total


def test_c1_files_and_profiles_round_trip() -> None:
    names = sorted(n for n in files_by_name(built()[3]) if n.startswith(f"{COLD}."))
    assert names == [f"{COLD}.expenses.csv", f"{COLD}.profile.cold-budget.csv",
                     f"{COLD}.profile.cold-storage-invoicing.csv", f"{COLD}.profile.cold-storage-ledger.csv"]
    for f in built()[3].files:
        if f.tenant != COLD:
            continue
        layout = LAYOUTS[f.layout_id] if f.layout_id in LAYOUTS else load_profile(f.layout_id)[1]
        read = read_layout(layout, f.data, tenant_code=COLD, produced_at="2026-11-06T06:00:00+03:00",
                           provenance="source-emulated")
        assert dict(read.refused) == {}, f.key
        assert read.obj["records"] == list(f.records), f.key


def test_c2_ledger_month_crate_days_equal_the_leaf() -> None:
    ledger = rows("profile.cold-storage-ledger")
    for code in SITES:
        for month in MONTHS:
            assert counted(ledger, code, month) == leaf(month, code, "crate_days"), (code, month)


def test_c3_ledger_batches_rooms_and_times() -> None:
    ledger = rows("profile.cold-storage-ledger")
    capacity = tenant_view(built()[0], COLD)["capacity_crates_per_room"]
    for code in SITES:
        events = []
        for (site, ref), b in batches_from(ledger).items():
            if site != code:
                continue
            assert all(at.timetz().isoformat() in ("08:00:00+03:00", "16:00:00+03:00") for at, _ in b["ins"]), ref
            assert all(at.timetz().isoformat() == "16:00:00+03:00" for at, _ in b["outs"]), ref
            assert b["crates"] <= 120 and sum(n for _, n in b["outs"]) <= b["crates"], ref
            if ref.startswith(f"{code}-B"):
                assert b["crates"] <= exports_cold.BATCH_CRATES, ref
                assert all(at.date() - b["ins"][0][0].date() <= timedelta(days=7) for at, _ in b["outs"]), ref
            events += [(at, 1, n) for at, n in b["ins"]]
            events += [(at, 0, -n) for at, n in b["outs"]]
        level = peak = 0
        for _, _, n in sorted(events, key=lambda e: (e[0], e[1])):
            level += n
            assert level >= 0, code
            peak = max(peak, level)
        assert 0 < peak <= capacity, (code, peak)
    assert max(r["clocks"]["occurred_at"] for r in ledger) <= "2026-11-06T23:59:59+03:00"


def test_c4_named_batches_keep_their_crates_and_times() -> None:
    found = batches_from(rows("profile.cold-storage-ledger"))
    for code, ref, commodity, crates, admitted, leaves in exports_cold.NAMED_BATCHES:
        b = found[(code, ref)]
        # D-DD.85: received in lots of at most 40, each at or before the named instant (exact lots: test_dd4_cold_receiving)
        assert (b["crates"], [at.isoformat()[:16] for at, _ in b["outs"]]) == (crates, [leaves])
        assert all(at.isoformat()[:16] <= admitted and n <= 40 for at, n in b["ins"])
    # D-DD.51 parity: the table equals the manifest's incident batches
    batches = {b["batch"]: b for b in m_site(COLD, "COLD-THIKA")["incident"]["batches"]}
    assert {ref for _, ref, *_ in exports_cold.NAMED_BATCHES} == set(batches)
    for _, ref, commodity, crates, _, leaves in exports_cold.NAMED_BATCHES:
        assert batches[ref]["crates"] == crates and batches[ref]["commodity"].lower() == commodity.lower()
    assert batches["B-1029"]["reason"] == "checked out 5 Oct 16:00"
    assert exports_cold.NAMED_BATCHES[0][5] == "2026-10-05T16:00"


def test_c5_invoices_are_the_revenue_node_and_receipts_received() -> None:
    invoices, receipts = invoicing("CHARGE"), invoicing("RECEIPT")
    for code in SITES:
        for month in MONTHS:
            inv = [r for r in invoices if (r["site_code"], r["clocks"]["recognition_period"]) == (code, month)]
            rec = [r for r in receipts if (r["site_code"], r["clocks"]["recognition_period"]) == (code, month)]
            crate_days = leaf(month, code, "crate_days")
            assert sum(int(r["quantity"]["value"]) for r in inv) == crate_days
            assert len({r["subject"]["ref"] for r in inv}) == len(inv)  # one invoice per customer per month
            revenue = Decimal(crate_days) * Decimal("0.20")
            assert money(inv) == revenue
            outstanding = Decimal(str(leaf(month, code, "outstanding")))
            if month != "2026-10":
                outstanding /= 100  # history money is cents
            assert money(rec) == revenue - outstanding
            assert {r["status"] for r in rec} == {"COLLECTED"}
    october = {c: (money([r for r in invoices if r["site_code"] == c and r["clocks"]["recognition_period"] == "2026-10"]),
                   money([r for r in receipts if r["site_code"] == c and r["clocks"]["recognition_period"] == "2026-10"]))
               for c in SITES}
    assert october == {"COLD-MWEA": (Decimal(868), Decimal(820)), "COLD-THIKA": (Decimal(1736), Decimal(1650)),
                       "COLD-KIRI": (Decimal(1984), Decimal(1900))}
    july = [r for r in receipts if r["site_code"] == "COLD-MWEA" and r["clocks"]["recognition_period"] == "2026-07"]
    assert money(july) == Decimal("1312.00")  # 6944 x 0.20 - 76.80


def test_c6_nodes_parity_with_the_manifest() -> None:
    structure, factors = manifest()["structures"]["COLD_CHAIN"], manifest()["factor_map"]["COLD_CHAIN"]
    for name, text in exports_cold.LEAF_TEXT.items():
        assert factors[name] == text, name
    assert set(exports_cold.PERIOD_FIELD) == {n for n, _, _ in NODES["COLD_CHAIN"]}
    for key, lines in NODE_LINES.items():  # D-DD.49: every node line names a node of its structure
        assert set(lines) <= set(manifest()["structures"][key]), key


def test_c7_planted_october_revenue_stops_the_emulator() -> None:
    view = load_fixture()
    site_of(view, COLD, "Room A · Mwea")["period"]["actual"]["revenue"] = "870.0"
    with pytest.raises(ValueError, match=r"^EMU_NODE harvest-cold/COLD-MWEA 2026-10 revenue$"):
        build(view)


def test_c8_planted_room_capacity_stops_the_emulator() -> None:
    view = load_fixture()
    next(t for t in view["tenants"] if t["tenant"] == COLD)["capacity_crates_per_room"] = 300
    with pytest.raises(ValueError, match=r"^EMU_CAPACITY harvest-cold/COLD-KIRI 2026-"):
        build(view)


def test_c9_missing_crate_days_is_listed_never_zero() -> None:
    def drop(history: dict) -> None:
        del history["tenants"][COLD]["Room A · Mwea"]["2026-08"]["actual"]["crate_days"]

    books = build(None, drop)[3]
    assert (COLD, "COLD-MWEA", "2026-08", "actual", "crate_days", "NOT_IN_HISTORY") in books.unwritten
    invoices = [r for r in files_by_name(books)[f"{COLD}.profile.cold-storage-invoicing.csv"].records
                if r["kind"] == "CHARGE"]
    assert not [r for r in invoices if r["site_code"] == "COLD-MWEA" and r["clocks"]["recognition_period"] == "2026-08"]
    assert [r for r in invoices if r["site_code"] == "COLD-MWEA" and r["clocks"]["recognition_period"] == "2026-09"]


def test_c10_no_energy_or_penalty_expense_row() -> None:
    """D-DD.49: energy is the bill's (DD4.4), penalties a node; the cold and EV ledgers carry DS1b's OM and STAFF."""
    books = built()[3]
    for tenant, allowed in ((COLD, {"OM", "STAFF"}), (EV, {"OM"})):
        f = files_by_name(books)[f"{tenant}.expenses.csv"]
        assert f.layout_id == "expenses-illustrative-1"
        categories = {r["body"]["category"] for r in f.records}
        assert categories == allowed and not categories & {"ENERGY", "PENALTY"}, tenant


def test_c11_budget_lines_and_unwritten_plan_fields() -> None:
    books = built()[3]
    budget = files_by_name(books)[f"{COLD}.profile.cold-budget.csv"].records
    for code in SITES:
        for month in MONTHS:
            lines = [r["body"]["factor_id"] for r in budget if (r["site_code"], r["clocks"]["recognition_period"]) == (code, month)]
            want = ["crate_days", "kwh", "staff", "maint"] + (["liability"] if code == "COLD-THIKA" else [])
            assert lines == want, (code, month)
    kwh = next(r for r in budget if r["source_record_id"] == "gen:COLD-MWEA:2026-07:plan:kwh")
    assert kwh["body"] == {"factor_id": "kwh", "value": "3410", "version_ref": "budget-2026-v1", "line_ref": "kwh"}
    money_line = next(r for r in budget if r["source_record_id"] == "gen:COLD-MWEA:2026-10:plan:staff")
    assert money_line["body"]["currency"] == "USD" and money_line["body"]["value"] == "300.00"
    plan = {(r[1], r[2], r[4]): r[5] for r in books.unwritten if r[0] == COLD and r[3] == "plan"}
    assert ("COLD-MWEA", "2026-07", "kwh") not in plan  # written as a node line
    for field in ("revenue", "energy", "contribution", "occupancy_pct"):  # labelled assumptions, never zero
        assert plan[("COLD-MWEA", "2026-10", field)] == "NOT_READ_BY_A_LEAF", field
