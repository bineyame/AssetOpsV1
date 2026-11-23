"""DD3d-a (D-DD.154 as amended by D-DD.168): the operator's fuel records, `<slug>/fuel-records.json`.

Written by `world_history.py exports --telemetry DIR` for each mini-grid tenant, from the readings and the books:

- `TANK_DIP`: one per Site at 00:00 local on the first day of each book month and of the month after the last, valued
  at the tank level row the readings print at that instant (an ordinary month-end dip, Assumed);
- `FUEL_DELIVERY`: one per fuel EXPENSE row of the books, at its `occurred_at` with its litres.

Each record is recorded at its own instant, except a note a disorder test dates (`exports.DATED_NOTES`): its
`recorded_at` is that table's recorded date. `recorded_at` is the product's record time (`load_fuel_records`). Records
are in recorded order, then by id. Pure: documents in, bytes out.
"""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

from .canonical import file_bytes
from .exports import DATED_NOTES, NOTE_HOUR, ExportFile

SCHEMA = "assetops.world-fuel-records/1"
FILE_NAME = "fuel-records.json"
LEVEL_ROLE = "fuel_level"
LITRES = re.compile(r"[0-9]{1,6}(?:\.[0-9]{1,3})?")  # what the product's entry accepts (`operational_entry.VALUE`)


def mini_grid_tenants(view: dict, only: list[str] | None = None) -> list[dict]:
    return [t for t in view["tenants"] if t.get("vertical") == "MINI_GRID" and (not only or t["tenant"] in only)]


def dip_days(history: dict, accounting_period: str) -> list[str]:
    """The first day of each book month and of the month after the last."""
    months = sorted({*history["meta"]["months"], accounting_period})
    year, month = int(months[-1][:4]), int(months[-1][5:7])
    months.append(f"{year + month // 12}-{month % 12 + 1:02d}")
    return [f"{m}-01" for m in months]


def _refuse(code: str, instant: str) -> ValueError:
    return ValueError(f"EMU_FUEL_RECORDS {code} {instant}")


def _dips(code: str, days: list[str], document: dict | None, zone: ZoneInfo) -> list[dict]:
    out = []
    for day in days:
        local = f"{day}T00:00"
        at = datetime.fromisoformat(local).replace(tzinfo=zone).isoformat()
        document = document or {}
        channels = [(m["source_id"], m["signal_id"]) for m in document.get("manifest", {}).get("mappings", ())
                    if m["role"] == LEVEL_ROLE]
        rows = [r for r in document.get("days", {}).get(day, {}).get("readings", ())
                if r["start"] == at and [(r["source_id"], r["signal_id"])] == channels]
        if len(rows) != 1 or LITRES.fullmatch(rows[0]["value"]) is None:
            raise _refuse(code, local)
        out.append({"source_record_id": f"{code}:dip:{day}", "kind": "TANK_DIP", "taken_at_local": local,
                    "litres": rows[0]["value"], "ticket_reference": None, "recorded_at": at})
    return out


def _recorded_at(tenant: str, site: dict, at: datetime, litres: str, zone: ZoneInfo) -> str:
    for _, slug, name, day, note_l, recorded in DATED_NOTES:
        if (slug, name, day, str(note_l)) == (tenant, site["site"], at.strftime("%Y-%m-%d"), litres):
            return datetime.fromisoformat(f"{recorded}T{NOTE_HOUR:02d}:00").replace(tzinfo=zone).isoformat()
    return at.isoformat()


def _deliveries(tenant: str, site: dict, rows: list[dict], zone: ZoneInfo) -> list[dict]:
    code, out = site["code"], []
    ordinal: dict[str, int] = {}
    for row in rows:
        at = datetime.fromisoformat(row["clocks"]["occurred_at"]).astimezone(zone)
        local, litres = at.strftime("%Y-%m-%dT%H:%M"), row["quantity"]["value"]
        if LITRES.fullmatch(litres) is None:
            raise _refuse(code, local)
        day = at.strftime("%Y%m%d")
        ordinal[day] = ordinal.get(day, 0) + 1
        out.append({"source_record_id": row["source_record_id"], "kind": "FUEL_DELIVERY", "taken_at_local": local,
                    "litres": litres, "ticket_reference": f"FN-{code}-{day}-{ordinal[day]}",
                    "recorded_at": _recorded_at(tenant, site, at, litres, zone)})
    return out


def build_fuel_records(view: dict, history: dict, files: tuple[ExportFile, ...],
                       readings: dict[str, dict[str, Any]]) -> tuple[tuple[str, bytes], ...]:
    """(tenant slug, `fuel-records.json` bytes) for each mini-grid tenant of `readings`: slug -> Site code ->
    `{"manifest": the Site's readings manifest, "days": {day: the readings document}}`."""
    zone = ZoneInfo(view["timezone_default"])
    days = dip_days(history, view["accounting_period"])
    out = []
    for tenant in mini_grid_tenants(view):
        slug = tenant["tenant"]
        if slug not in readings:
            continue
        expenses = [r for f in files if (f.tenant, f.key) == (slug, "expenses") for r in f.records
                    if r["body"]["category"] == "FUEL"]
        sites = []
        for site in sorted(tenant["sites"], key=lambda s: s["code"]):
            rows = [r for r in expenses if r["site_code"] == site["code"]]
            records = _dips(site["code"], days, readings[slug].get(site["code"]), zone)
            records += _deliveries(slug, site, rows, zone)
            records.sort(key=lambda r: (datetime.fromisoformat(r["recorded_at"]), r["source_record_id"]))
            sites.append({"site_code": site["code"], "records": records})
        out.append((slug, file_bytes({"schema": SCHEMA, "tenant": slug, "sites": sites})))
    return tuple(out)
