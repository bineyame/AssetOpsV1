"""DD3.2 commit 1b (D-DD.19, D-DD.70): the pure run on Kobo, July to October, at one no-load rate.

    python tools/dd3_pure_run.py --books DIR [--no-load 0.62|3.3] [--start 2026-07-01 --end 2026-10-31]

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
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for part in ("simulator", "contracts", "tools"):
    sys.path.insert(0, str(ROOT / part))

import datasheet_template  # noqa: E402
import world_history  # noqa: E402
from assetops_simulator.world import telemetry  # noqa: E402
from assetops_simulator.world.history import generate_history  # noqa: E402

ONBOARDING = ROOT / "backend/tests/fixtures/on1/lakeside-power.onboarding.json"
BINDINGS = ROOT / "backend/conversions/world"
SLOT = ROOT / "config/datasheets/kobo-equipment.json"
MANIFEST = ROOT / "Docs/demo-sprint/product-direction-layer4/demo-site-scenario-manifest.yaml"


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


def run_table(no_load: str, books_dir: Path, first: str, last: str) -> int:
    view = world_history.load_view(MANIFEST)
    expenses = {p.name.removesuffix(".expenses.csv"): p.read_text(encoding="utf-8") for p in books_dir.glob("*.expenses.csv")}
    books = telemetry.books_for(view, generate_history(view), expenses)["KOBO-001"]
    run = telemetry.SiteRun(kobo_site(no_load), books, first, last)
    run.strict = False
    stopped = None
    try:
        for _ in run.days:
            run.next_day_readings()
    except telemetry.TelemetryRefused as error:
        stopped = str(error)
    print(f"no-load {no_load} L/h; Kobo {first}..{last}; tank capacity {run.frozen.bounds[0].value} L")
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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--books", required=True, type=Path)
    parser.add_argument("--no-load", default="0.62", choices=("0.62", "3.3"))
    parser.add_argument("--start", default="2026-07-01")
    parser.add_argument("--end", default="2026-10-31")
    args = parser.parse_args(argv)
    return run_table(args.no_load, args.books, args.start, args.end)


if __name__ == "__main__":
    raise SystemExit(main())
