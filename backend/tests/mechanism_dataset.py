"""MD-0: the mechanism test dataset (build sheet `.agent/build-sheet-MD-0.md`, rulings §1 MD0-R and §14 MD0-PF).

Phase 1 (this file so far): the fixture loader with its schema rules (§2.1), the `MECHANISM_DB_ONLY` database
guard (R2, D-AW-1), the Dn date map and the `late_fill` declared-gap refusal (§4). Seeding (`seed_database`),
`late_fill`'s write path and `build_work` follow in later phases (`.agent/MD-0-phase-1-handoff.md`).

Inputs only: the fixture never carries an expected output (R3). Every write goes through an existing writer at its
story time (R1, R4); no snapshot, thread or study row is ever inserted directly and no row is UPDATEd.
"""

from __future__ import annotations

import json
import re
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

FIXTURE = Path(__file__).resolve().parents[1] / "conversions" / "mechanism-v1.json"
FIXTURE_ID, FIXTURE_VERSION = "assetops.mechanism-dataset", "1"
DAY_SETS = ("full", "states")

#: R2 / D-AW-1: the only databases MD-0 may seed or fill. The pg_harness worker pattern is
#: `<stem>_pt<run>_<tag>_test` (`pg_harness.database_name`).
MECHANISM_DB_RE = re.compile(r"^assetops_mechanism(_close)?_test$")
WORKER_DB_RE = re.compile(r"^[a-z0-9_]+_pt[0-9a-z]+_(main|tpl|gw[0-9]+)_test$")
ALWAYS_REFUSED_RE = re.compile(r"^assetops_(polish|demo)")
PROTECTED = ("assetops_polish_full_test", "assetops_demo3_full_test")  # B/chain/backfill.py:29

OUTPUT_KEYS = {"grade", "state", "status", "eligible_days", "minutes"}
OUTCOME_ID_RE = re.compile(r"\b(MG|CC|EV)-\d")


class MechanismRefused(ValueError):
    """A refused MD-0 request; `str(error)` is the code (`MECHANISM_DB_ONLY`, `DAY_HAS_EVIDENCE`, ...)."""


def mechanism_db_allowed(name: str) -> bool:
    """Pure: may MD-0 write into the database called `name`? Polish, demo and protected DBs are always refused."""
    if name in PROTECTED or ALWAYS_REFUSED_RE.match(name):
        return False
    return bool(MECHANISM_DB_RE.match(name) or WORKER_DB_RE.match(name))


def require_mechanism_db(engine) -> str:
    """Reads `current_database()` and raises `MechanismRefused("MECHANISM_DB_ONLY")` unless it is allowed."""
    from sqlalchemy import text

    with engine.connect() as c:
        name = c.execute(text("SELECT current_database()")).scalar_one()
    if not mechanism_db_allowed(name):
        raise MechanismRefused("MECHANISM_DB_ONLY")
    return name


# --- the fixture ---------------------------------------------------------------------------------------------


def day(spec: dict, n: int) -> date:
    """Dn = day_zero + n (D1 Mon 19 Oct 2026 ... D14 Sun 1 Nov 2026)."""
    return date.fromisoformat(spec["story"]["day_zero"]) + timedelta(days=n)


def local_instant(spec: dict, site: str, n: int, hhmm: str) -> datetime:
    """Site-local Dn at HH:MM ("24:00" is the next midnight), as a UTC instant."""
    tz = ZoneInfo(spec["sites"][site]["time_zone"])
    h, m = (int(x) for x in hhmm.split(":"))
    base = datetime.combine(day(spec, n), datetime.min.time(), tzinfo=tz)
    return (base + timedelta(hours=h, minutes=m)).astimezone(timezone.utc)


def _walk(node: Any, path: str = ""):
    if isinstance(node, dict):
        for k, v in node.items():
            yield path, k, v
            yield from _walk(v, f"{path}.{k}")
    elif isinstance(node, list):
        for i, v in enumerate(node):
            yield from _walk(v, f"{path}[{i}]")


def validate(spec: dict) -> None:
    """The §2.1 L0 schema rules; raises `ValueError` naming the first broken rule."""
    if spec.get("schema") != {"id": FIXTURE_ID, "version": int(FIXTURE_VERSION)}:
        raise ValueError("schema: not assetops.mechanism-dataset v1")
    text_ = json.dumps(spec)
    if OUTCOME_ID_RE.search(text_):
        raise ValueError("outcome id in the fixture (OL-1)")
    for path, key, _ in _walk(spec):
        if key in OUTPUT_KEYS:
            raise ValueError(f"output key {key!r} at {path}")
    for where, value in _value_nodes(spec):
        if "source" not in value:
            raise ValueError(f"no source at {where}")
    if set(spec["day_sets"]) != set(DAY_SETS):
        raise ValueError("day_sets must be full and states")
    gaps = {(g["site"], g["day"]) for g in spec["gaps"]}
    fixed = _event_and_action_days(spec)
    if gaps & fixed:
        raise ValueError(f"a gap falls on an event, action or study day: {sorted(gaps & fixed)}")
    for name, sets in spec["day_sets"].items():
        if name == "source":
            continue
        for site, days in sets.items():
            if site == "source":
                continue
            if any((site, d) in gaps and spec_gap(spec, site, d)["kind"] == "nothing_delivered" for d in days):
                raise ValueError(f"day set {name} delivers a nothing_delivered gap on {site}")
    ev = spec["sites"]["ev"]["sessions"]
    for name in DAY_SETS:
        for n in spec["day_sets"][name]["ev"]:
            if day(spec, n).weekday() != 1:
                raise ValueError(f"EV D{n} is not a Tuesday")
    start = int(ev["first_local"].split(":")[0])
    if not (8 <= start and start + ev["per_day"] * ev["length_minutes"] / 60 <= 16):
        raise ValueError("EV sessions fall outside TUE 08:00-16:00")


def _value_nodes(spec: dict):
    """Every dict that declares an input value, so needs a `source` (§2.1)."""
    yield "delivery", spec["delivery"]
    for name in DAY_SETS:
        yield f"day_sets.{name}", spec["day_sets"][name]
    for g in spec["gaps"]:
        yield f"gaps.{g['id']}", g
    yield "late_fill", spec["late_fill"]
    for site, s in spec["sites"].items():
        for key in ("configuration", "reading_rules", "noon", "sessions"):
            if key in s:
                yield f"{site}.{key}", s[key]
        nd = s.get("normal_day")
        if nd is not None:
            for i, b in enumerate(nd.get("blocks") or [nd]):
                yield f"{site}.normal_day[{i}]", b
        for key in ("controls", "events", "actions", "studies", "publications"):
            for i, x in enumerate(s.get(key, [])):
                yield f"{site}.{key}[{i}]", x


def _event_and_action_days(spec: dict) -> set[tuple[str, int]]:
    out: set[tuple[str, int]] = set()
    for site, s in spec["sites"].items():
        for e in s.get("events", []):
            out.add((site, e["day"]))
        for a in s.get("actions", []):
            for step in a.values():
                if isinstance(step, dict) and "day" in step:
                    out.add((site, step["day"]))
        for st in s.get("studies", []):
            out |= {(site, d) for d in range(st["from_day"], st["to_day"] + 1)}
    return out


def spec_gap(spec: dict, site: str, n: int) -> dict | None:
    return next((g for g in spec["gaps"] if g["site"] == site and g["day"] == n), None)


def load(path: Path = FIXTURE) -> dict:
    spec = json.loads(path.read_text(encoding="utf-8"))
    validate(spec)
    return spec


def fill_target(spec: dict, site_code: str, n: int, kind: str = "normal") -> dict:
    """§4: the declared fillable gap for (site_code, Dn), or `MechanismRefused` with the FILL-1 code."""
    site = next((k for k, s in spec["sites"].items() if s["site_code"] == site_code), None)
    gap = spec_gap(spec, site, n) if site else None
    if gap is None:  # an undeclared day is already one of the dataset's declared days
        raise MechanismRefused("DUPLICATE_DAY")
    if not gap.get("fill"):  # GAP-C3 / GAP-E2 hold delivered evidence (stores are append-only)
        raise MechanismRefused("DAY_HAS_EVIDENCE")
    if kind not in gap.get("fill_kinds", ()):
        raise MechanismRefused("PREPARE_ONLY_KIND")
    return gap
