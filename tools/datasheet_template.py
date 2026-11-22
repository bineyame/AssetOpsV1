"""DD3.2 (spec `specs/DD-demo-data/spec.md` §6; D-DD.17, D-DD.30): Kobo's data sheets onto Lakeside's `/2` file.

    python tools/datasheet_template.py --slot config/datasheets/kobo-equipment.json \
        --onboarding backend/tests/fixtures/on1/lakeside-power.onboarding.json --site KOBO-001 (--check | --write)

Pure and exact (`Fraction`). It maps the slot's generator and battery values onto the Site's GENERATOR and BATTERY
components with their `-basis` properties, prints the sheet's L/h beside the line's per stated point and the diff,
and refuses on any failure (exit 3, stderr `<CODE> <detail>`). `--check` exits 1 when the file differs from the
mapping; `--write` rewrites it. Nothing else in the file moves: the PCS, reserve, start and stop SOC, delays and tank
stay as Lakeside's `/1` values.
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from decimal import ROUND_HALF_EVEN, Decimal, localcontext
from fractions import Fraction
from pathlib import Path

REPOSITORY = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY / "simulator"))

from assetops_simulator.packs import generator_curve  # noqa: E402  v8's own curve refusals

SCHEMA = "assetops.equipment-datasheets/1"
DECLARED, FIT, GENERIC = "MANUFACTURER_DATASHEET", "DATASHEET_FIT", "GENERIC_DEFAULT"
UNITS = {"generator-rated-power": "kW", "specific-fuel-consumption": "L/kWh", "generator-no-load-fuel-rate": "L/h",
         "generator-minimum-load": "%", "battery-energy-capacity": "kWh", "battery-charge-taper-start": "%"}


class DatasheetRefused(ValueError):
    def __init__(self, code: str, detail: str) -> None:
        super().__init__(f"{code} {detail}")
        self.code = code


@dataclass(frozen=True)
class Mapping:
    generator: dict[str, tuple[str, str]]  # property -> (value text, basis)
    battery: dict[str, tuple[str, str]]
    generator_rating: str
    battery_rating: str
    residuals: list[tuple[str, str, str]]  # (load pct, sheet L/h, line L/h)


def half_even(value: Fraction, quantum: str) -> str:
    q = Decimal(quantum)
    with localcontext() as ctx:
        ctx.prec = 50
        exact = Decimal(value.numerator) / Decimal(value.denominator)
        return str(exact.quantize(q, rounding=ROUND_HALF_EVEN))


def fit_intercept(points: list[tuple[Fraction, Fraction]]) -> Fraction:
    """The zero-load intercept of the least-squares line through (load kW, L/h)."""
    n = len(points)
    if n < 2 or len({x for x, _ in points}) < 2:
        raise DatasheetRefused("DATASHEET_CURVE_INVALID", f"{n} stated point(s); a line needs two loads")
    mx = sum((x for x, _ in points), Fraction(0)) / n
    my = sum((y for _, y in points), Fraction(0)) / n
    sxx = sum(((x - mx) ** 2 for x, _ in points), Fraction(0))
    sxy = sum(((x - mx) * (y - my) for x, y in points), Fraction(0))
    return my - sxy / sxx * mx


def _assumed(slot: dict, item: str) -> dict | None:
    return next((a for a in slot.get("assumed", []) if a.get("item") == item), None)


def _stated_or_assumed(slot: dict, stated, item: str) -> tuple[str, str]:
    if stated is not None:
        return str(stated), DECLARED
    entry = _assumed(slot, item)
    if entry is None or "value" not in entry or entry.get("basis_code") not in (GENERIC, FIT):
        raise DatasheetRefused("DATASHEET_UNSTATED", f"{item} is neither stated nor assumed with a basis code")
    return str(entry["value"]), entry["basis_code"]


def map_slot(slot: dict) -> Mapping:
    if slot.get("schema") != SCHEMA:
        raise DatasheetRefused("DATASHEET_SCHEMA", str(slot.get("schema")))
    gen, bat = slot["generator"], slot["battery"]
    prime = Fraction(gen["prime_kw"])
    points = sorted(((Fraction(int(pct), 100) * prime, Fraction(v), pct)
                     for pct, v in gen["fuel_l_per_h"].items() if v is not None), key=lambda p: -p[0])
    if "100" not in gen["fuel_l_per_h"] or gen["fuel_l_per_h"]["100"] is None:
        raise DatasheetRefused("DATASHEET_CURVE_INVALID", "no full-load fuel rate")
    sfc_text = half_even(Fraction(gen["fuel_l_per_h"]["100"]) / prime, "0.0001")
    if gen.get("no_load_l_per_h") is not None:
        no_load_text, no_load_basis = str(gen["no_load_l_per_h"]), DECLARED
    else:
        intercept = fit_intercept([(x, y) for x, y, _ in points])
        if intercept <= 0:
            raise DatasheetRefused("DATASHEET_CURVE_INVALID", f"the fitted line meets zero load at {float(intercept):.3f} L/h")
        no_load_text, no_load_basis = _stated_or_assumed(slot, None, "generator.no_load_l_per_h")
        fitted = half_even(intercept, "0.01")
        if no_load_basis == FIT and Decimal(no_load_text) != Decimal(fitted):
            raise DatasheetRefused("DATASHEET_FIT_MISMATCH", f"slot says {no_load_text}, the fit gives {fitted}")
    sfc, no_load = Fraction(sfc_text), Fraction(no_load_text)
    try:
        generator_curve.fuel_curve(sfc, no_load / 60, prime)
    except generator_curve.CurveRefused as refused:
        raise DatasheetRefused(refused.code, refused.detail) from refused
    min_load = _stated_or_assumed(slot, gen.get("minimum_load_pct"), "generator.minimum_load_pct")
    taper = _stated_or_assumed(slot, bat.get("charge_taper_start_soc_pct"), "battery.charge_taper_start_soc_pct")
    capacity_text = half_even(bat["modules"] * Fraction(bat["module_usable_kwh"]), "0.1")
    slope = sfc - no_load / prime
    residuals = [(pct, half_even(y, "0.01"), half_even(no_load + slope * x, "0.01")) for x, y, pct in points]
    prime_text = str(gen["prime_kw"])
    return Mapping(
        generator={"generator-rated-power": (prime_text, DECLARED), "specific-fuel-consumption": (sfc_text, DECLARED),
                   "generator-no-load-fuel-rate": (no_load_text, no_load_basis),
                   "generator-minimum-load": min_load},
        battery={"battery-energy-capacity": (capacity_text, DECLARED), "battery-charge-taper-start": taper},
        generator_rating=prime_text, battery_rating=capacity_text, residuals=residuals)


def _number(text: str) -> int | float:
    value = Decimal(text)
    return int(value) if value == value.to_integral_value() else float(text)


def _set(component: dict, values: dict[str, tuple[str, str]], rating: str) -> None:
    component["rating"]["value"] = _number(rating)
    props = component.setdefault("properties", [])
    for key, (text, basis) in values.items():
        for name, value, unit in ((key, _number(text), UNITS[key]), (f"{key}-basis", basis, "state")):
            entry = next((p for p in props if p["property_key"] == name), None)
            if entry is None:
                entry = {"property_key": name}
                props.append(entry)
            entry.update({"value": value, "unit": unit, "source": "SITE", "source_version": 1})


def apply(document: dict, site_code: str, mapping: Mapping) -> dict:
    site = next((s for s in document["sites"] if s["code"] == site_code), None)
    if site is None:
        raise DatasheetRefused("DATASHEET_SITE", f"{site_code} is not in the file")
    for kind, values, rating in (("GENERATOR", mapping.generator, mapping.generator_rating),
                                 ("BATTERY", mapping.battery, mapping.battery_rating)):
        found = [c for c in site["components"] if c["type"] == kind]
        if len(found) != 1:
            raise DatasheetRefused("DATASHEET_SITE", f"{site_code} has {len(found)} {kind} components; the tool maps one")
        _set(found[0], values, rating)
    return document


def _dump(document: dict) -> str:
    return json.dumps(document, indent=2, ensure_ascii=False) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--slot", required=True, type=Path)
    parser.add_argument("--onboarding", required=True, type=Path)
    parser.add_argument("--site", required=True)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--write", action="store_true")
    args = parser.parse_args(argv)
    try:
        mapping = map_slot(json.loads(args.slot.read_text(encoding="utf-8")))
        before_text = args.onboarding.read_text(encoding="utf-8")
        before = json.loads(before_text)
        after = apply(json.loads(before_text), args.site, mapping)
    except DatasheetRefused as refused:
        print(str(refused), file=sys.stderr)
        return 3
    for pct, sheet, line in mapping.residuals:
        print(f"{pct} % load: sheet / line L/h {sheet} / {line}")
    import difflib
    diff = list(difflib.unified_diff(_dump(before).splitlines(), _dump(after).splitlines(), "before", "after", lineterm=""))
    print("\n".join(diff) if diff else "no change")
    if args.write and after != before:
        args.onboarding.write_text(_dump(after), encoding="utf-8")
    return 1 if args.check and after != before else 0


if __name__ == "__main__":
    raise SystemExit(main())
