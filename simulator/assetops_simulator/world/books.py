"""DD2.3/DD2.4 (spec `specs/DD-demo-data/spec.md` §5.2, §5.3; D-DD.49, D-DD.54): what the cold and EV book writers
share, and the one call that writes every tenant's decided books.

- `site_months`: a tenant's Site-months, the history months from `history.json` (money in integer cents) and the
  accounting period from the view's `period` (money in dollars), in (month, Site code) order.
- `ds1b_by_tenant`: DS1b's canonical records of one tenant, as plain dicts.
- `budget_rows` / `expense_rows`: D-DD.49's budget lines (DS1b's own-leaf lines plus the node lines of `NODE_LINES`)
  and DS1b's EXPENSE rows.
- `build_books`: the mini-grid files (`exports.build_exports`), then the cold and EV files, with one unwritten list.
  Every DS1b record of a cold or EV tenant lands in exactly one place: an exported file (a credit note is a row of
  the cold invoicing file, D-DD.59), staged canonical JSON or `unwritten.json`. Staged JSON (D-DD.60) is the cold
  rate cards and EV tariff schedules (`tariffs.py`, D-DD.61) and a DS1b record of a kind in `STAGED_KINDS` that no
  exported file of its source type can carry; `tools/world.py` places it under `<slug>/staged/`.
- `check_source_systems`: the store invariant at export (D-DD.60): one source system per source type per Site, so a
  clash stops `EMU_SOURCE_SWITCH <tenant> <source_type> <site>` at generation, not at the load.

Standard library, `assetops_contracts` and the world modules only.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date, datetime, time
from decimal import Decimal
from fractions import Fraction
from zoneinfo import ZoneInfo

from assetops_contracts.canonical import CanonicalRefused, parse_batch, parse_record, to_canonical_json
from assetops_contracts.native import LAYOUTS

from .exports import NOT_ON_PATH_VERTICAL, ExportFile
from .profile_csv import load_profile
from .records import PROVENANCE, SOURCE_SYSTEM, STRUCTURE_KEY, RecordsResult, money_text
from .view import ManifestView

#: D-DD.54: DS1b's JSON kinds that are staged as canonical JSON, never written into a native file.
STAGED_KINDS = frozenset({"ADJUSTMENT", "METER_ASSIGNMENT", "TARIFF_SCHEDULE"})
#: D-DD.49 (b): plan fields that name a node of the Site's structure and become budget lines with their recorded
#: value. A parity test asserts each name is a node of `M` `structures[key]`.
NODE_LINES = {
    "COLD_CHAIN": {"kwh": "whole"},
    "EV_DEPOT_CAPTIVE": {"energy_cost": "money", "departures_required": "whole"},
}
VERSION_REF = "budget-2026-v1"
SOURCE_VERSION = "1"

NOT_IN_HISTORY = "NOT_IN_HISTORY"
NOT_IN_LAYOUT = "NOT_IN_LAYOUT"
AS_UNPAID_CHARGES = "AS_UNPAID_CHARGES"


@dataclass(frozen=True)
class BooksResult:
    files: tuple[ExportFile, ...]
    unwritten: tuple[tuple[str, ...], ...]
    #: (file name, bytes): staged canonical JSON `<tenant>.<source_type>.json` (D-DD.60), by name.
    staged: tuple[tuple[str, bytes], ...] = ()
    #: (file name, bytes): `<tenant>.statements.json` (DD spec §5.4), by name.
    statements: tuple[tuple[str, bytes], ...] = ()


@dataclass(frozen=True)
class SiteMonth:
    tenant: str
    code: str
    name: str
    month: str
    actual: dict
    plan: dict
    coverage: dict
    october: bool  # True for the view's accounting period (money in dollars)
    site: dict

    def where(self) -> str:
        return f"{self.tenant}/{self.code} {self.month}"

    def cents(self, side: str, field: str) -> int | None:
        """A money field as integer cents, or None when absent. History money is cents, the period's dollars."""
        value = (self.actual if side == "actual" else self.plan).get(field)
        if value is None:
            return None
        number = Fraction(Decimal(str(value))) * (1 if not self.october else 100)
        if number.denominator != 1:
            raise ValueError(f"EMU_PRICE {self.where()} {field}")
        return int(number)

    def whole(self, side: str, field: str) -> int | None:
        value = (self.actual if side == "actual" else self.plan).get(field)
        if value is None:
            return None
        number = Fraction(Decimal(str(value)))
        if number.denominator != 1:
            raise ValueError(f"EMU_QUANTITY {self.where()} {field}")
        return int(number)


def site_months(view: dict, history: dict, tenant: dict) -> list[SiteMonth]:
    out = []
    blocks = history["tenants"].get(tenant["tenant"], {})
    for site in tenant.get("sites", []):
        for month in sorted(history["meta"]["months"]):
            block = blocks.get(site["site"], {}).get(month, {})
            out.append(SiteMonth(tenant["tenant"], site["code"], site["site"], month, block.get("actual", {}),
                                 block.get("plan", {}), block.get("coverage", {}), False, site))
        period = site.get("period", {})
        out.append(SiteMonth(tenant["tenant"], site["code"], site["site"], view["accounting_period"],
                             period.get("actual", {}), period.get("plan", {}), period.get("coverage", {}), True, site))
    return sorted(out, key=lambda m: (m.month, m.code))


def months_of(view: dict, history: dict) -> list[str]:
    return sorted(history["meta"]["months"]) + [view["accounting_period"]]


def ds1b_by_tenant(records: RecordsResult, tenant: str) -> list[dict]:
    out = []
    for batch in records.batches:
        if batch.batch.tenant_code == tenant:
            out += json.loads(to_canonical_json(batch))["records"]
    return out


def batch_object(view: dict, tenant: str, source_type: str, source_system: str, records: list[dict]) -> dict:
    """A canonical batch object for `records`, produced at 06:00 local on `as_of` like DS1b's."""
    zone = ZoneInfo(view["timezone_default"])
    produced_at = datetime.combine(date.fromisoformat(view["as_of"]), time(6, 0), tzinfo=zone).isoformat()
    return {"format_version": 1, "tenant_code": tenant, "source_type": source_type, "source_system": source_system,
            "provenance": PROVENANCE, "produced_at": produced_at, "records": records}


def staged_file(batch: dict) -> tuple[str, bytes]:
    """(`<tenant>.<source_type>.json`, canonical bytes) of a batch object; `EMU_FORMAT` when the contract refuses it."""
    try:
        parsed = parse_batch(batch)
    except CanonicalRefused as refused:
        raise ValueError(f"EMU_FORMAT staged {refused.code} {refused.path}") from None
    return f"{batch['tenant_code']}.{batch['source_type']}.json", to_canonical_json(parsed)


def staged_batch(view: dict, tenant: str, source_type: str, records: list[dict]) -> tuple[str, bytes]:
    """DS1b's own records as a staged file: the generator's source system, as DS1b writes them."""
    return staged_file(batch_object(view, tenant, source_type, SOURCE_SYSTEM, records))


def check_source_systems(files: list[ExportFile] | tuple[ExportFile, ...],
                         staged: list[tuple[str, bytes]] | tuple[tuple[str, bytes], ...]) -> None:
    """D-DD.60, mirroring D-3A6.5 and the loader's `_mixed`: a tenant's exported files each hold their own source type
    (a), and a staged batch never names a Site that an exported file of its source type names under another source
    system (b). Otherwise `EMU_SOURCE_SWITCH <tenant> <source_type> <site>`."""
    seen: list[tuple[str, str, str, set[str]]] = []  # (tenant, source_type, source_system, Sites)
    for f in files:
        layout = LAYOUTS.get(f.layout_id) or load_profile(f.layout_id)[1]
        sites = {r["site_code"] for r in f.records}
        for tenant, source_type, _, other in seen:
            if tenant == f.tenant and source_type == layout.source_type:
                raise ValueError(f"EMU_SOURCE_SWITCH {f.tenant} {source_type} {min(sites | other, default='*')}")
        seen.append((f.tenant, layout.source_type, layout.source_system, sites))
    for name, data in staged:
        batch = json.loads(data)
        sites = {r["site_code"] for r in batch["records"]}
        for tenant, source_type, system, exported in seen:
            clash = sites & exported
            if tenant == batch["tenant_code"] and source_type == batch["source_type"] \
                    and system != batch["source_system"] and clash:
                raise ValueError(f"EMU_SOURCE_SWITCH {tenant} {source_type} {min(clash)}")


def checked(where: str, record: dict) -> dict:
    try:
        parse_record(record)
    except CanonicalRefused as refused:
        raise ValueError(f"EMU_FORMAT {where} {refused.code} {refused.path}") from None
    return record


def node_line(m: SiteMonth, field: str, form: str, currency: str) -> dict | None:
    """D-DD.49 (b): the plan field's recorded value as a budget line, or None when the plan does not hold it."""
    if field not in m.plan:
        return None
    body = {"factor_id": field, "value": "", "version_ref": VERSION_REF, "line_ref": field}
    if form == "money":
        body["value"] = money_text(m.cents("plan", field))
        body["currency"] = currency
    else:
        body["value"] = str(m.whole("plan", field))
    return checked(m.where(), {
        "format_version": 1, "kind": "BUDGET_LINE", "source_record_id": f"gen:{m.code}:{m.month}:plan:{field}",
        "source_version": SOURCE_VERSION, "site_code": m.code, "clocks": {"recognition_period": m.month},
        "body": body})


def budget_rows(key: str, tenant: str, months: list[SiteMonth], ds1b: list[dict], lines: tuple[str, ...],
                currency: str, unwritten: list) -> tuple[list[dict], set[tuple[str, str, str]]]:
    """DS1b's BUDGET_LINE records whose factor is a profile line, then the node lines; ordered (month, Site, line).
    Returns the rows and the (code, month, field) plan fields written as node lines."""
    rows = []
    for r in ds1b:
        if r["kind"] != "BUDGET_LINE":
            continue
        if r["body"]["factor_id"] in lines:
            rows.append(r)
        else:
            unwritten.append((tenant, r["site_code"], r["clocks"]["recognition_period"], r["kind"],
                              r["source_record_id"], NOT_IN_LAYOUT))
    written = set()
    for m in months:
        for field, form in NODE_LINES[key].items():
            row = node_line(m, field, form, currency)
            if row is not None:
                rows.append(row)
                written.add((m.code, m.month, field))
    rows.sort(key=lambda r: (r["clocks"]["recognition_period"], r["site_code"], lines.index(r["body"]["factor_id"])))
    return rows, written


EXPENSE_ORDER = ("OM", "STAFF")


def expense_rows(ds1b: list[dict]) -> list[dict]:
    """DS1b's EXPENSE rows (D-DD.49 3: cold `maint` OM and `staff` STAFF, EV `maintenance` OM), (month, Site, category)."""
    rows = [r for r in ds1b if r["kind"] == "EXPENSE"]
    return sorted(rows, key=lambda r: (r["clocks"]["recognition_period"], r["site_code"],
                                       EXPENSE_ORDER.index(r["body"]["category"])))


def remaining_unwritten(records: RecordsResult, tenant: str, written: set[tuple[str, str, str, str]],
                        renamed: dict[tuple[str, str, str, str], str]) -> list[tuple[str, ...]]:
    """DS1b's unwritten rows of the tenant, less the fields this writer wrote; `renamed` gives a new reason."""
    out = []
    for row in records.unwritten:
        name, code, month, side, field, reason = row
        if name != tenant or (code, month, side, field) in written:
            continue
        out.append((name, code, month, side, field, renamed.get((code, month, side, field), reason)))
    return out


def zone_currency(view: dict) -> tuple[ZoneInfo, str]:
    return ZoneInfo(view["timezone_default"]), view["currency"]


def build_books(view: dict, history: dict) -> BooksResult:
    """Every tenant's decided books: mini-grid (3A3, D-DD.48), cold (DD2.3) and EV (DD2.4), one unwritten list."""
    from .exports import build_exports
    from .exports_cold import build_cold_exports
    from .exports_ev import build_ev_exports
    from .records import build_records
    from .tariffs import tariff_schedules

    view = ManifestView.from_document(view)
    records = build_records(view, history)
    mini = build_exports(view, history)
    files = list(mini.files)
    unwritten: list[tuple[str, ...]] = []
    staged: list[tuple[str, bytes]] = []
    covered = set()
    for tenant in view.get("tenants", []):
        key = STRUCTURE_KEY.get(tenant.get("vertical"))
        if key == "COLD_CHAIN":
            part = build_cold_exports(view, history, records, tenant)
        elif key == "EV_DEPOT_CAPTIVE":
            part = build_ev_exports(view, history, records, tenant)
        else:
            continue
        covered.add(tenant["tenant"])
        files += part.files
        unwritten += part.unwritten
        staged += part.staged
    unwritten += [row for row in mini.unwritten if not (row[0] in covered and row[5] == NOT_ON_PATH_VERTICAL)]
    # mini-grid's own staged JSON (DS1b's ADJUSTMENT and the like); a cold or EV tenant's is this module's (D-DD.54)
    staged += [(name, data) for name, data in mini.staged if name.split(".")[0] not in covered]
    for batch in tariff_schedules(view).values():  # D-DD.61: the rate cards and EV schedules
        staged.append(staged_file(batch))
    staged.sort()
    check_source_systems(files, staged)
    return BooksResult(tuple(files), tuple(sorted(unwritten)), tuple(staged), mini.statements)
