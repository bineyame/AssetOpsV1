"""DD3.2 commit 1b (D-DD.19, D-DD.70) and DD3.3: the pure run on one mini-grid Site, July to October.

    python tools/dd3_pure_run.py --books DIR [--site KOBO-001|KISIWA-001|MTO-001] [--no-load 0.62|3.3]
                                 [--start 2026-07-01 --end 2026-10-31]
    python tools/dd3_pure_run.py --restate-notes [--check] --site CODE [--start --end]
    python tools/dd3_pure_run.py --leaves --site CODE [--start --end]

`--restate-notes` (D-DD.92): pure run, first crossing below 25 % of the tank, place the reorder notes, rerun, until no
new crossing in the span; writes the Site's entry of `config/world/fuel-notes.json` (`--check`: exit 1 when the file
differs from what the rule gives). `--leaves` (D-DD.131) runs the span on the file's notes and prints `M`'s October
fuel leaves, the fuel balance, the bridge's fuel lines and whether the bridge closes against the restated variance.

Kisiwa and Mto run on v9 from their committed `/2` kit (D-DD.70, D-DD.128); `--no-load` is Kobo's only.
No database. Applies the data-sheet slot to the committed `/2` file in memory (at 3.3 L/h the slot's no-load item is
restated as GENERIC_DEFAULT), builds the Site's inputs, drives the writer as it runs for the world (a delivery that
overfills is recorded, not refused, so the table can show it), and prints per month: delivered (notes), accepted,
refused, burned (tank), modelled (the readings at the curve), drawn, tank minimum and maximum, the balance
(opening + accepted deliveries - closing - modelled), unserved energy and a stand-in candidate. `DIR` is the
directory `world_history.py exports` wrote. Exit 0 printed, 3 refused.
"""
from __future__ import annotations

import argparse
import copy
import json
import sys
from datetime import datetime, timedelta
from decimal import ROUND_HALF_EVEN, Decimal
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for part in ("simulator", "contracts", "tools"):
    sys.path.insert(0, str(ROOT / part))

import datasheet_template  # noqa: E402
import world_history  # noqa: E402
from assetops_simulator.world import telemetry  # noqa: E402
from assetops_simulator.world.exports import DATED_NOTES, DELIVERY_L, NOTE_HOUR  # noqa: E402
from assetops_simulator.world.history import generate_history  # noqa: E402

ONBOARDING = ROOT / "backend/tests/fixtures/on1/lakeside-power.onboarding.json"
BINDINGS = ROOT / "backend/conversions/world"
SLOT = ROOT / "config/datasheets/kobo-equipment.json"
MANIFEST = ROOT / "Docs/demo-sprint/product-direction-layer4/demo-site-scenario-manifest.yaml"
NOTES_FILE = ROOT / "config/world/fuel-notes.json"
NOTES_SCHEMA = "assetops.world-fuel-notes/1"
REORDER_SHARE = Fraction(1, 4)  # D-DD.92: notes when the level first falls below 25 % of the tank
MAX_NOTES = 2


# --- D-DD.92: the reorder rule ---------------------------------------------------------------------------------------

def note_instant(crossed: datetime) -> datetime:
    """The next 10:00 local after the crossing: the same day only when the crossing is before 10:00."""
    same = crossed.replace(hour=NOTE_HOUR, minute=0, second=0, microsecond=0)
    return same if crossed < same else same + timedelta(days=1)


def note_count(free: Fraction) -> int:
    """As many 400 L notes as fit in the free space, at most two."""
    return min(MAX_NOTES, int(free // DELIVERY_L))


def first_crossing(levels, threshold: Fraction, after: datetime | None) -> datetime | None:
    """The first step boundary after `after` whose level is below `threshold` while the one before is not."""
    previous = None
    for instant, level in levels:
        if previous is not None and (after is None or instant > after) and previous >= threshold > level:
            return instant
        previous = level
    return None


def restate(simulate, capacity: Fraction, dated: list[dict]) -> list[dict]:
    """Iterate the rule: `simulate(notes)` yields (instant, level) at every step boundary of the span, the run taking
    `notes`. A pass stops at the 10:00 after its first new crossing, places the notes on the free space there and
    reruns; the pass that finds no new crossing (or whose 10:00 falls past the span) ends it."""
    threshold = capacity * REORDER_SHARE
    notes = sorted(dated, key=lambda n: n["at"])
    after = None
    while True:
        crossed = placed = previous = None
        for instant, level in simulate(notes):
            if crossed is None and previous is not None and (after is None or instant > after) \
                    and previous >= threshold > level:
                crossed = instant
            previous = level
            if crossed is not None and instant >= note_instant(crossed):
                placed = level
                break
        if placed is None:
            return notes
        note = {"at": note_instant(crossed).isoformat(), "litres": str(DELIVERY_L), "basis": "REORDER"}
        notes = sorted(notes + [dict(note) for _ in range(note_count(capacity - placed))], key=lambda n: n["at"])
        after = crossed


def kobo_site(no_load: str) -> dict:
    slot = json.loads(SLOT.read_text(encoding="utf-8"))
    if no_load != "0.62":
        for item in slot["assumed"]:
            if item["item"] == "generator.no_load_l_per_h":
                item.update(value=no_load, basis_code="GENERIC_DEFAULT", basis="the 7 Nov generic rule: 3.3 L/h for the 40 kW set")
    document = datasheet_template.apply(json.loads(ONBOARDING.read_text(encoding="utf-8")), "KOBO-001",
                                        datasheet_template.map_slot(slot))
    codes = {"KOBO-001": json.loads((BINDINGS / "KOBO-001-bindings.json").read_text(encoding="utf-8"))}
    return next(s for s in telemetry.site_inputs(document, codes)["sites"] if s["code"] == "KOBO-001")


def mini_site(code: str) -> dict:
    """Kisiwa's or Mto's inputs from the committed `/2` file as the writer reads it (no slot is applied)."""
    codes = {code: json.loads((BINDINGS / f"{code}-bindings.json").read_text(encoding="utf-8"))}
    document = json.loads(ONBOARDING.read_text(encoding="utf-8"))
    return next(s for s in telemetry.site_inputs(document, codes)["sites"] if s["code"] == code)


def run_table(no_load: str, books_dir: Path, first: str, last: str, code: str = "KOBO-001") -> int:
    view = world_history.load_view(MANIFEST)
    expenses = {p.name.removesuffix(".expenses.csv"): p.read_text(encoding="utf-8") for p in books_dir.glob("*.expenses.csv")}
    books = telemetry.books_for(view, generate_history(view), expenses)[code]
    run = telemetry.SiteRun(kobo_site(no_load) if code == "KOBO-001" else mini_site(code), books, first, last)
    run.strict = False
    stopped = None
    try:
        for _ in run.days:
            run.next_day_readings()
    except telemetry.TelemetryRefused as error:
        stopped = str(error)
    kit = f"no-load {no_load} L/h" if code == "KOBO-001" else "the /2 kit"
    print(f"{kit}; {code} {first}..{last}; pack v{run.frozen.model_profile_version}; "
          f"tank capacity {run.frozen.bounds[0].value} L")
    head = ("month", "notes_l", "accepted_l", "refused_l", "drawn_l", "burned_tank_l", "modelled_l", "tank_min", "tank_max",
            "open_l", "close_l", "balance_l", "unserved_kwh", "gen_h", "standin_cand_l")
    print(" ".join(f"{h:>13}" for h in head))
    start = run._start
    refused: dict[str, Fraction] = {}
    for item in run._execution.bounded_transitions:
        day = (start + __import__("datetime").timedelta(minutes=item.at_offset_minutes)).astimezone(run.zone)
        refused[day.strftime("%Y-%m")] = refused.get(day.strftime("%Y-%m"), Fraction(0)) + item.refused
    for month, row in sorted(run.ledger.items()):
        notes = sum(Fraction(n["litres"]) for n in books["fuel_notes"] if n["at"].startswith(month))
        drawn = Fraction(books["months"][month]["unexplained_l"]) if month in books["months"] else Fraction(0)
        accepted = notes - refused.get(month, Fraction(0))
        burned = row["tank_open"] + accepted - drawn - row.get("tank_close", row["tank_open"])
        balance = row["tank_open"] + accepted - row.get("tank_close", row["tank_open"]) - row["modelled_l"]
        cells = (month, notes, accepted, refused.get(month, 0), drawn, burned, row["modelled_l"], row["tank_min"], row["tank_max"],
                 row["tank_open"], row.get("tank_close", 0), balance, sum(row["unserved_kwh"].values(), Fraction(0)),
                 Fraction(row["generator_minutes"], 60), row["standin_candidate_l"])
        print(" ".join(f"{(month if i == 0 else f'{float(c):.2f}'):>13}" for i, c in enumerate(cells)))
    print(f"bound hit: {'YES' if refused else 'no'}; stopped: {stopped or 'no'}")
    return 3 if stopped else 0


# --- D-DD.92: the notes run and the notes file ------------------------------------------------------------------------

def site_inputs(code: str) -> dict:
    return kobo_site("0.62") if code == "KOBO-001" else mini_site(code)


def plain_books(code: str) -> dict:
    """The Site's books without any expenses file's notes: the notes come from the rule."""
    view = world_history.load_view(MANIFEST)
    slugs = {t["tenant"]: "" for t in view["tenants"] if t.get("vertical") == "MINI_GRID"}
    return telemetry.books_for(view, generate_history(view), slugs)[code]


def dated_notes(code: str, zone) -> list[dict]:
    """A disorder test's dated note keeps its date (D-DD.53): `exports.DATED_NOTES`, at 10:00 local."""
    view = world_history.load_view(MANIFEST)
    names = {(t["tenant"], s["site"]): s["code"] for t in view["tenants"] for s in t.get("sites", [])}
    out = []
    for test, tenant, site, day, litres in DATED_NOTES:
        if names.get((tenant, site)) == code:
            instant = datetime.fromisoformat(day).replace(hour=NOTE_HOUR, tzinfo=zone)
            out.append({"at": instant.isoformat(), "litres": str(litres), "basis": f"STORY:{test}"})
    return out


def _with_notes(books: dict, notes: list[dict]) -> dict:
    return dict(books, fuel_notes=[{"at": n["at"], "litres": int(n["litres"])} for n in sorted(notes, key=lambda n: n["at"])])


def simulation(site: dict, books: dict, first: str, last: str):
    """`simulate(notes)`: the strict writer's run on `notes`, yielding (local instant, tank litres) at every step
    boundary, a day at a time (an overfill is refused, so a placed note never overfills unnoticed)."""
    def simulate(notes):
        run = telemetry.SiteRun(site, _with_notes(books, notes), first, last)
        seen = 0
        for steps in run.day_steps:
            run.advance(steps)
            boundaries = run._execution.boundaries
            for k in range(seen, run.steps_advanced + 1):
                yield ((run._start + timedelta(minutes=k * telemetry.STEP_MINUTES)).astimezone(run.zone),
                       boundaries[k].stock(run._tank))
            seen = run.steps_advanced + 1
    return simulate


def _litres_text(value: Fraction) -> str:
    return str(value.numerator) if value.denominator == 1 else str(Decimal(value.numerator) / Decimal(value.denominator))


def notes_entry(code: str, first: str, last: str) -> dict:
    site, books = site_inputs(code), plain_books(code)
    probe = telemetry.SiteRun(site, _with_notes(books, []), first, first)
    capacity = probe.frozen.bounds[0].value
    notes = restate(simulation(site, books, first, last), capacity, dated_notes(code, probe.zone))
    return {"site_code": code, "rule": "D-DD.92", "tank_l": _litres_text(capacity), "notes": notes}


def read_notes_file() -> dict:
    if NOTES_FILE.exists():
        return json.loads(NOTES_FILE.read_text(encoding="utf-8"))
    return {"schema": NOTES_SCHEMA, "sites": []}


def restate_notes(code: str, first: str, last: str, check: bool) -> int:
    entry = notes_entry(code, first, last)
    document = read_notes_file()
    held = next((s for s in document["sites"] if s["site_code"] == code), None)
    for note in entry["notes"]:
        print(f"{code} note {note['at']} {note['litres']} L {note['basis']}")
    print(f"{code}: {len(entry['notes'])} notes, {sum(int(n['litres']) for n in entry['notes'])} L, "
          f"tank {entry['tank_l']} L, {first}..{last}")
    if check:
        same = held == entry
        print(f"fuel-notes {code}: {'matches the rule' if same else 'DIFFERS from the rule'}")
        return 0 if same else 1
    document["sites"] = sorted([s for s in document["sites"] if s["site_code"] != code] + [entry],
                               key=lambda s: s["site_code"])
    NOTES_FILE.parent.mkdir(parents=True, exist_ok=True)
    NOTES_FILE.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {NOTES_FILE.relative_to(ROOT)}")
    return 0


# --- D-DD.131: the leaves from the notes run ---------------------------------------------------------------------------

def _whole(value) -> int:
    value = Fraction(value)
    return int((Decimal(value.numerator) / Decimal(value.denominator)).quantize(Decimal(1), rounding=ROUND_HALF_EVEN))


def _money(value) -> Decimal:
    return Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_EVEN)


def october_leaves(ledger: dict, notes: list[dict], price: Decimal, plan: dict, actual: dict,
                   month: str = "2026-10") -> dict:
    """D-DD.131 on one month's ledger row: `diesel_l` = burned + declared draw (whole, half-even); the split from the
    pure run (candidate = the writer's stand-in, necessary = the rest of `diesel_l` after candidate and unexplained);
    cost, contribution and variance by `M`'s identities; the fuel balance from the tank; the bridge's fuel lines by
    their stated formulas (plan necessary = the plan's `necessary_l`, else its `diesel_l`)."""
    unexplained = int(actual["unexplained_l"])
    diesel = _whole(ledger["modelled_l"] + unexplained)
    candidate = _whole(ledger["standin_candidate_l"])
    necessary = diesel - candidate - unexplained
    cost = _money(Decimal(diesel) * price)
    contribution = _money(Decimal(str(actual["revenue"])) - cost - Decimal(str(actual["om"])) - Decimal(str(actual["staff"])))
    opening, closing = _whole(ledger["tank_open"]), _whole(ledger["tank_close"])
    deliveries = sum(int(n["litres"]) for n in notes if n["at"][:7] == month)
    consumed = opening + deliveries - closing
    implied = _whole(ledger["modelled_l"])
    plan_necessary = int(plan.get("necessary_l", plan["diesel_l"]))
    return {"diesel_l": diesel, "necessary_l": necessary, "candidate_l": candidate, "unexplained_l": unexplained,
            "diesel_cost": cost, "contribution": contribution,
            "variance": _money(contribution - Decimal(str(plan["contribution"]))),
            "fuel_balance": {"opening_dip_l": opening, "deliveries_l": deliveries, "closing_dip_l": closing,
                             "consumed_l": consumed, "model_implied_l": implied, "residual_l": consumed - implied},
            "bridge": {"CANDIDATE_RUNNING": _money(-candidate * price),
                       "NECESSARY": _money(-(necessary - plan_necessary) * price),
                       "UNEXPLAINED_RESIDUAL": _money(-unexplained * price)}}


NECESSARY_DRIVERS = ("EVENING_LOAD_GROWTH", "SOLAR_SHORTFALL_NECESSARY_GEN", "EVENING_NECESSARY_GEN")


def restated_bridge(lines: list[dict], leaves: dict) -> list[tuple[str, Decimal, Decimal]]:
    """`M`'s bridge lines with each fuel line on its stated formula: (driver, old, new)."""
    out = []
    for line in lines:
        driver, old = line["driver"], _money(line["amount"])
        key = "NECESSARY" if driver in NECESSARY_DRIVERS else driver
        out.append((driver, old, leaves["bridge"].get(key, old)))
    return out


def print_leaves(code: str, first: str, last: str) -> int:
    import yaml

    document = read_notes_file()
    entry = next((s for s in document["sites"] if s["site_code"] == code), None)
    if entry is None:
        print(f"{code} is not in {NOTES_FILE.relative_to(ROOT)}: run --restate-notes first")
        return 2
    manifest = yaml.safe_load(MANIFEST.read_text(encoding="utf-8"))
    tenant = next(t for t in manifest["tenants"] if any(s.get("code") == code for s in t.get("sites", [])))
    site = next(s for s in tenant["sites"] if s.get("code") == code)
    price = Decimal(str(tenant["prices"]["diesel_usd_per_l"][site["site"]]))
    run = telemetry.SiteRun(site_inputs(code), _with_notes(plain_books(code), entry["notes"]), first, last)
    peak = Fraction(0)
    gen_sources = {(p["source_id"], p["signal_id"]): p["address"] for p in run.pairs if p["role"] == "generator_power"}
    candidate_days = 0
    for day in run.days:
        month = day.strftime("%Y-%m")
        before = run.ledger.get(month, {}).get("standin_candidate_l", Fraction(0))
        rows = run.next_day_readings()
        if month == "2026-10" and run.ledger[month]["standin_candidate_l"] > before:
            candidate_days += 1
        for row in rows:
            if (row["source_id"], row["signal_id"]) in gen_sources and "2026-10-30T18:40" <= row["start"][:16] \
                    and 18 <= int(row["start"][11:13]) < 23:
                peak = max(peak, Fraction(row["value"]))
    period = site["period"]
    leaves = october_leaves(run.ledger["2026-10"], entry["notes"], price, period["plan"], period["actual"])
    actual, balance = period["actual"], period.get("fuel_balance", {})
    print(f"{code} October leaves from the notes run ({first}..{last}; {len(entry['notes'])} notes; price {price})")
    for leaf in ("diesel_l", "necessary_l", "candidate_l", "unexplained_l", "diesel_cost", "contribution"):
        print(f"  period.actual.{leaf}: {actual.get(leaf)} -> {leaves[leaf]}")
    print(f"  period.variance: {period.get('variance')} -> {leaves['variance']}")
    for key, value in leaves["fuel_balance"].items():
        print(f"  fuel_balance.{key}: {balance.get(key)} -> {value}")
    bridge = restated_bridge(period.get("bridge", []), leaves)
    for driver, old, new in bridge:
        print(f"  bridge {driver}: {old} -> {new}")
    total = sum((new for _, _, new in bridge), Decimal(0))
    closes = total == leaves["variance"]
    gap = "" if closes else f" (gap {leaves['variance'] - total})"
    print(f"  bridge total {total} against variance {leaves['variance']}: {'closes' if closes else 'DOES NOT CLOSE'}{gap}")
    print(f"  findings_expected GENERATOR_SUPPORT_CANDIDATE days: {candidate_days} of 31, exposure [0, "
          f"{leaves['candidate_l']}] L, [0, {_money(leaves['candidate_l'] * price)}]")
    print(f"  stand-in candidate {float(run.ledger['2026-10']['standin_candidate_l']):.2f} L; "
          f"peak evening generator power after 30 Oct 18:40: {float(peak):.2f} kW")
    return 0 if closes else 4


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--books", type=Path)
    parser.add_argument("--restate-notes", action="store_true")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--leaves", action="store_true")
    parser.add_argument("--site", default="KOBO-001", choices=("KOBO-001", "KISIWA-001", "MTO-001"))
    parser.add_argument("--no-load", default="0.62", choices=("0.62", "3.3"))
    parser.add_argument("--start", default="2026-07-01")
    parser.add_argument("--end", default="2026-10-31")
    args = parser.parse_args(argv)
    if args.site != "KOBO-001" and args.no_load != "0.62":
        parser.error("--no-load is Kobo's only")
    if args.restate_notes:
        return restate_notes(args.site, args.start, args.end, args.check)
    if args.leaves:
        return print_leaves(args.site, args.start, args.end)
    if args.books is None:
        parser.error("--books is required for the table")
    return run_table(args.no_load, args.books, args.start, args.end, args.site)


if __name__ == "__main__":
    raise SystemExit(main())
