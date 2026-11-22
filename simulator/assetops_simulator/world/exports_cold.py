"""DD2.3 (spec `specs/DD-demo-data/spec.md` §5.2; D-DD.49, D-DD.50, D-DD.51): the cold-chain decided books.

Per Site-month (July to September from `history.json`, October from `period`), in the source profiles' own formats:

- the storage ledger (`cold-storage-ledger-illustrative`): batches of 40 crates (the remainder batch of a month
  carries the rest), each staying 7 days, admitted at 08:00 and checked out at 16:00 local. A crate-day is a crate in
  the room on a date from its admission date up to the day before it leaves (`crate_days_in`), so a batch admitted
  late in a month carries crate-days into the next. Admissions are spread over the month's days, and the month's
  occupied crate-days equal the leaf exactly: the standard batches fill what earlier batches have not, and the
  remainder batch carries the rest (`r // 7` crates for 7 days, plus one crate leaving after `r % 7` days). The
  manifest's named batches (B-1029, B-1031, B-1034; `NAMED_BATCHES`, with a parity test) keep their crates and times.
  A movement after `as_of` is not written (the crates are still in the room). Rows dated in June are opening stock
  (D-DD.63): batches admitted in June that are still in on 1 July, with every OUT after their IN. June has no
  invoice, receipt or leaf, and a check that reads the ledger by month judges July to October only. The room never
  holds more than `capacity_crates_per_room` (`EMU_CAPACITY`).
- invoicing (`cold-storage-invoicing-illustrative`, D-DD.59): one export of the operator's one invoicing system, a
  `Type` column naming each row. `Invoice`: one per customer per month, on the customer's crate-days of the month,
  tariff `T-STORAGE` (the rate card is `tariffs.py`'s, D-DD.61); their sum is the node `revenue` of
  `structures.COLD_CHAIN` (D-DD.50). `Receipt`: the node `received = revenue - outstanding`, all COLLECTED (the cold
  structure has no in-transit leaf), customers paid in order; the rest is outstanding. `Credit note`: DS1b's
  ADJUSTMENT (Thika's October liability), a row of this file.
- expenses (`expenses-illustrative-1`, unchanged): DS1b's EXPENSE rows only (OM, STAFF). No ENERGY or PENALTY row.
- budget (`cold-budget-illustrative`, D-DD.49): DS1b's own-leaf lines plus the node line `kwh`.

For October the evaluated node must equal the node `period` records (`EMU_NODE`). A missing required leaf writes no
row for its node and is listed `NOT_IN_HISTORY`. Every plan field with no line stays in `unwritten` with DS1b's reason.

Standard library, `assetops_contracts` and the world modules only.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from fractions import Fraction
from pathlib import Path

from assetops_contracts.native import LAYOUTS, render_layout

from .books import (AS_UNPAID_CHARGES, NOT_IN_HISTORY, SOURCE_VERSION, BooksResult, SiteMonth, budget_rows, checked,
                    ds1b_by_tenant, expense_rows, remaining_unwritten, site_months, staged_batch, zone_currency)
from .exports import ExportFile
from .months import days_in, parse_month, period_end
from .nodes import NODES, emu_node, evaluate
from .profile_csv import PROFILES_DIR, load_profile, render_profile, row_digest
from .records import RecordsResult, money_text

KEY = "COLD_CHAIN"
BATCH_CRATES = 40
STAY_DAYS = 7  # Assumed (spec §5.2)
IN_AT = time(8, 0)
OUT_AT = time(16, 0)
CUSTOMERS = 6
COMMODITIES = ("Tomatoes", "Cabbage", "Kale", "Mangoes", "French beans", "Avocado")
METHODS = ("MOBILE_MONEY", "MOBILE_MONEY", "BANK")
TARIFF_CODE = "T-STORAGE"
PAID_AT = time(10, 0)
BUDGET_LINES = ("crate_days", "kwh", "staff", "maint", "liability")
PROFILES = {"ledger": "cold-storage-ledger-illustrative", "invoicing": "cold-storage-invoicing-illustrative",
            "budget": "cold-budget-illustrative"}
#: The invoicing export's row order within a Site-month (D-DD.59): invoices, receipts, then credit notes.
TYPE_ORDER = {"CHARGE": 0, "RECEIPT": 1, "ADJUSTMENT": 2}

#: D-DD.50, D-DD.62: the `structures.COLD_CHAIN` nodes the books carry are `nodes.NODES["COLD_CHAIN"]` (money in cents).
#: The `factor_map.COLD_CHAIN` text of each leaf the nodes read (parity test).
LEAF_TEXT = {"crate_days": "record.crate_days", "rate": "prices.storage_usd_per_crate_day",
             "contract_crate_days": "0", "contract_rate": "0", "outstanding": "record.outstanding | 0"}
#: The `period` field that records each node (its October check, `EMU_NODE`).
PERIOD_FIELD = {"revenue": "revenue", "received": "collected"}

#: D-DD.51: the manifest's named batches (`tenants.harvest-cold.sites.*.incident.batches`), with a parity test. Only
#: B-1029's check-out is a manifest time; the other times are the 7-day stay around the 6 Oct incident (Assumed).
NAMED_BATCHES = (
    ("COLD-THIKA", "B-1029", "Cabbage", 60, "2026-09-28T08:00", "2026-10-05T16:00"),
    ("COLD-THIKA", "B-1031", "French beans, export grade", 120, "2026-10-01T08:00", "2026-10-08T16:00"),
    ("COLD-THIKA", "B-1034", "Avocado", 80, "2026-10-01T08:00", "2026-10-08T16:00"),
)


@dataclass
class Batch:
    code: str
    ref: str
    customer: str
    commodity: str
    admitted: datetime
    outs: list = field(default_factory=list)  # [(at, crates)], in time order

    @property
    def crates(self) -> int:
        return sum(n for _, n in self.outs)


def crate_days_in(batch: Batch, month: str) -> int:
    """The batch's crate-days dated in `month`: each crate counts the dates from admission up to its leaving day."""
    first, last = date(*parse_month(month), 1), period_end(month)
    total = 0
    for out_at, crates in batch.outs:
        start, stop = max(batch.admitted.date(), first), min(out_at.date() - timedelta(days=1), last)
        if stop >= start:
            total += crates * ((stop - start).days + 1)
    return total


def presence_peak(batches: list[Batch]) -> int:
    """The most crates in the room at once (movements in time order; a check-out before an admission at one instant)."""
    events = []
    for b in batches:
        events.append((b.admitted, 1, b.crates))
        events += [(at, 0, -n) for at, n in b.outs]
    level = peak = 0
    for _, _, n in sorted(events, key=lambda e: (e[0], e[1])):
        level += n
        peak = max(peak, level)
    return peak


def _named(code: str, zone) -> list[Batch]:
    out = []
    for site, ref, commodity, crates, admitted, leaves in NAMED_BATCHES:
        if site == code:
            at_in = datetime.fromisoformat(admitted).replace(tzinfo=zone)
            at_out = datetime.fromisoformat(leaves).replace(tzinfo=zone)
            out.append(Batch(code, ref, f"{code}-K-01", commodity, at_in, [(at_out, crates)]))
    return out


def presence_by_date(batches: list[Batch]) -> dict[date, int]:
    """Crates in the room at some time of each date, its leaving day included (a check-out is at 16:00, after the
    day's admissions at 08:00)."""
    out: dict[date, int] = {}
    for b in batches:
        for out_at, crates in b.outs:
            day = b.admitted.date()
            while day <= out_at.date():
                out[day] = out.get(day, 0) + crates
                day += timedelta(days=1)
    return out


def _fill(code: str, month: str, need: int, zone, seq: list[int], existing: list[Batch]) -> list[Batch]:
    """Batches admitted in `month` whose crate-days dated in the month are exactly `need`.

    Standard batches (40 crates, 7 days) go one at a time on the day whose stay sees the fewest crates (ties: the
    earlier day), while their crate-days dated in the month still fit. What is left (under one batch) is the
    remainder batch, inside the month: `rest // 7` crates for 7 days, plus one crate leaving after `rest % 7` days."""
    year, number = parse_month(month)
    days = days_in(month)
    presence = presence_by_date(existing)

    def at(day: int, t: time) -> datetime:
        return datetime.combine(date(year, number, day), t, tzinfo=zone)

    def weight(day: int) -> int:
        return min(STAY_DAYS, days - day + 1)

    def crowd(day: int, stay: int) -> int:
        first = date(year, number, day)
        return max(presence.get(first + timedelta(days=k), 0) for k in range(stay + 1))

    def batch(day: int) -> Batch:
        seq[0] += 1
        n = seq[0]
        return Batch(code, f"{code}-B{n:04d}", f"{code}-K-{(n - 1) % CUSTOMERS + 1:02d}",
                     COMMODITIES[(n - 1) % len(COMMODITIES)], at(day, IN_AT))

    def add(b: Batch, after_days: int, crates: int) -> None:
        b.outs.append((b.admitted.replace(hour=OUT_AT.hour) + timedelta(days=after_days), crates))
        for k in range(after_days + 1):
            day = b.admitted.date() + timedelta(days=k)
            presence[day] = presence.get(day, 0) + crates

    out: list[Batch] = []
    left = need
    while True:
        fits = [d for d in range(1, days + 1) if BATCH_CRATES * weight(d) <= left]
        if not fits:
            break
        day = min(fits, key=lambda d: (crowd(d, STAY_DAYS), d))
        b = batch(day)
        add(b, STAY_DAYS, BATCH_CRATES)
        out.append(b)
        left -= BATCH_CRATES * weight(day)
    if left:
        crates, short = divmod(left, STAY_DAYS)
        day = min(range(1, days - STAY_DAYS + 2), key=lambda d: (crowd(d, STAY_DAYS), d))
        b = batch(day)
        if short:  # the remainder batch carries the month's last crate-days: one crate leaves early
            add(b, short, 1)
        if crates:
            add(b, STAY_DAYS, crates)
        out.append(b)
    return out


def _opening(m: SiteMonth, crate_days: int, zone, seq: list[int]) -> list[Batch]:
    """The batches admitted in the month before the first, filled at the first month's daily rate, that are still
    in the room on its first day (otherwise the first week would start from an empty room)."""
    year, number = parse_month(m.month)
    before = f"{year - 1:04d}-12" if number == 1 else f"{year:04d}-{number - 1:02d}"
    need = (crate_days * days_in(before)) // days_in(m.month)
    return [b for b in _fill(m.code, before, need, zone, seq, []) if crate_days_in(b, m.month) > 0]


def _evaluate(m: SiteMonth, rate_cents: int) -> dict | None:
    """The nodes of the month in cents, or None when the required leaf `crate_days` is absent."""
    crate_days = m.whole("actual", "crate_days")
    if crate_days is None:
        return None
    outstanding = m.cents("actual", "outstanding")
    values = {"crate_days": crate_days, "rate": rate_cents, "contract_crate_days": 0, "contract_rate": 0,
              "outstanding": 0 if outstanding is None else outstanding}
    values |= evaluate(KEY, values)
    for node, _, _ in NODES[KEY]:
        if values[node] < 0:
            raise ValueError(f"EMU_COLLECTIONS {m.tenant}/{m.code} {m.month} {node}")
    if m.october:
        emu_node(m.tenant, m.code, m.month, values, {n: m.cents("actual", f) for n, f in PERIOD_FIELD.items()})
    return values


def _rate_cents(tenant: dict) -> int:
    value = tenant.get("prices", {}).get("storage_usd_per_crate_day")
    if value is None:
        raise ValueError(f"EMU_PRICE {tenant['tenant']} storage_usd_per_crate_day")
    cents = Fraction(Decimal(str(value))) * 100
    if cents.denominator != 1:
        raise ValueError(f"EMU_PRICE {tenant['tenant']} storage_usd_per_crate_day")
    return int(cents)


def _movement_records(batches: list[Batch], as_of_end: datetime) -> list[dict]:
    out = []
    for b in batches:
        rows = [("in", "IN", b.admitted, b.crates)]
        rows += [(f"out-{k}", "OUT", at, n) for k, (at, n) in enumerate(b.outs, start=1)]
        for suffix, direction, at, crates in rows:
            if at > as_of_end:
                continue
            out.append(checked(b.code, {
                "format_version": 1, "kind": "STORAGE_MOVEMENT", "source_record_id": f"gen:{b.code}:{b.ref}:{suffix}",
                "source_version": SOURCE_VERSION, "site_code": b.code, "subject": {"kind": "BATCH", "ref": b.ref},
                "clocks": {"occurred_at": at.isoformat()}, "quantity": {"value": str(crates), "unit": "crate"},
                "body": {"batch_ref": b.ref, "customer_ref": b.customer, "commodity": b.commodity,
                         "direction": direction}}))
    return sorted(out, key=lambda r: (r["clocks"]["occurred_at"][:7], r["site_code"], r["clocks"]["occurred_at"],
                                      r["source_record_id"]))


def _november(site_batches: list[Batch], seq: list[int], as_of_end: datetime) -> list[Batch]:
    """D-DD.63 (DD4.2): 1-6 Oct's generated admissions (named batches excluded) repeated 31 days later with new refs,
    up to `as_of`. Assumed; no November invoice (the month is not closed)."""
    named = {ref for _site, ref, *_rest in NAMED_BATCHES}
    shift = timedelta(days=31)
    out: list[Batch] = []
    for b in sorted(site_batches, key=lambda b: (b.admitted, b.ref)):
        if b.ref in named or not (1 <= b.admitted.day <= 6 and (b.admitted.year, b.admitted.month) == (2026, 10)):
            continue
        if b.admitted + shift > as_of_end:
            continue
        seq[0] += 1
        out.append(Batch(b.code, f"{b.code}-B{seq[0]:04d}", b.customer, b.commodity, b.admitted + shift,
                         [(at + shift, n) for at, n in b.outs]))
    return out


def build_cold_exports(view: dict, history: dict, records: RecordsResult, tenant: dict, *,
                       profiles_dir: Path = PROFILES_DIR) -> BooksResult:
    zone, currency = zone_currency(view)
    name = tenant["tenant"]
    as_of_end = datetime.combine(date.fromisoformat(view["as_of"]), time(23, 59, 59), tzinfo=zone)
    capacity = tenant.get("capacity_crates_per_room")
    rate = _rate_cents(tenant)
    months = site_months(view, history, tenant)
    ds1b = ds1b_by_tenant(records, name)
    unwritten: list[tuple[str, ...]] = []
    written: set[tuple[str, str, str, str]] = set()
    renamed: dict[tuple[str, str, str, str], str] = {}
    batches: dict[str, list[Batch]] = {}
    seq: dict[str, list[int]] = {}
    invoicing: list[dict] = []  # D-DD.59: one export of one system: invoices, receipts, credit notes
    for m in months:  # (month, Site) order, so each Site's earlier months are filled first
        if m.coverage.get("revenue") == "ESTIMATED":
            continue  # GAP-1: an estimate is never written
        values = _evaluate(m, rate)
        if values is None:
            unwritten.append((name, m.code, m.month, "actual", "crate_days", NOT_IN_HISTORY))
            continue
        if m.code not in batches:  # the room's opening stock: the previous month's batches still in on day 1
            batches[m.code] = _named(m.code, zone) + _opening(m, values["crate_days"], zone, seq.setdefault(m.code, [0]))
        site_batches = batches[m.code]
        need = values["crate_days"] - sum(crate_days_in(b, m.month) for b in site_batches)
        if need < 0:
            raise ValueError(f"EMU_LEDGER {name}/{m.code} {m.month}")
        site_batches += _fill(m.code, m.month, need, zone, seq.setdefault(m.code, [0]), site_batches)
        if capacity is not None and presence_peak(site_batches) > int(capacity):
            raise ValueError(f"EMU_CAPACITY {name}/{m.code} {m.month}")
        by_customer: dict[str, int] = {}
        for b in site_batches:
            n = crate_days_in(b, m.month)
            if n:
                by_customer[b.customer] = by_customer.get(b.customer, 0) + n
        if sum(by_customer.values()) != values["crate_days"]:
            raise ValueError(f"EMU_LEDGER {name}/{m.code} {m.month}")
        first = date(*parse_month(m.month), 1)
        after = (period_end(m.month) + timedelta(days=1)).isoformat()
        charges = []
        for i, customer in enumerate(sorted(by_customer), start=1):
            cd = by_customer[customer]
            charges.append((customer, cd * rate))
            invoicing.append(checked(m.where(), {
                "format_version": 1, "kind": "CHARGE", "source_record_id": f"gen:{m.code}:{m.month}:invoice-{i:02d}",
                "source_version": SOURCE_VERSION, "site_code": m.code, "subject": {"kind": "CUSTOMER", "ref": customer},
                "clocks": {"effective_from": first.isoformat(), "effective_to": after, "recognition_period": m.month},
                "quantity": {"value": str(cd), "unit": "crate_day"},
                "amount": {"value": money_text(cd * rate), "currency": currency},
                "body": {"account_ref": customer, "line_type": "STORAGE", "tariff_code": TARIFF_CODE}}))
        if sum(c for _, c in charges) != values["revenue"]:
            raise ValueError(f"EMU_REVENUE {name}/{m.code} {m.month}")
        left = values["received"]
        paid_at = datetime.combine(period_end(m.month), PAID_AT, tzinfo=zone).isoformat()
        for i, (customer, owed) in enumerate(charges, start=1):
            pay = min(owed, left)
            if pay <= 0:
                break
            left -= pay
            record = {
                "format_version": 1, "kind": "RECEIPT", "source_record_id": f"gen:{m.code}:{m.month}:receipt-{i:02d}",
                "source_version": "", "site_code": m.code, "subject": {"kind": "CUSTOMER", "ref": customer},
                "clocks": {"occurred_at": paid_at, "recognition_period": m.month},
                "amount": {"value": money_text(pay), "currency": currency}, "status": "COLLECTED",
                "body": {"payer_ref": customer, "method": METHODS[(i - 1) % len(METHODS)]}}
            invoicing.append(record)
        if left != 0:
            raise ValueError(f"EMU_COLLECTIONS {name}/{m.code} {m.month}")
        for f in ("crate_days", "revenue", "collected"):
            written.add((m.code, m.month, "actual", f))
        renamed[(m.code, m.month, "actual", "outstanding")] = AS_UNPAID_CHARGES

    for code in sorted(batches):  # D-DD.63 "November" (DD4.2): the ledger runs to as_of for the rooms' readings
        batches[code] += _november(batches[code], seq[code], as_of_end)
        if capacity is not None and presence_peak(batches[code]) > int(capacity):
            raise ValueError(f"EMU_CAPACITY {name}/{code} 2026-11")
    files: list[ExportFile] = []
    ledger = _movement_records([b for code in sorted(batches) for b in batches[code]], as_of_end)
    invoicing_layout = load_profile(PROFILES["invoicing"], profiles_dir)[1]
    # D-DD.59: DS1b's ADJUSTMENT (a credit note) is a row of the invoicing file when the file exists; otherwise it
    # is staged canonical JSON (D-DD.60), under its own source type.
    adjustments = [r for r in ds1b if r["kind"] == "ADJUSTMENT"]
    staged: list[tuple[str, bytes]] = []
    if invoicing:
        invoicing += adjustments
        invoicing.sort(key=lambda r: (r["clocks"]["recognition_period"], r["site_code"], TYPE_ORDER[r["kind"]]))
        for r in invoicing:  # the State column versions each row by its digest (3A6)
            r["source_version"] = row_digest(invoicing_layout, r)
            checked(r["site_code"], r)
    elif adjustments:
        staged.append(staged_batch(view, name, "customer_invoicing", adjustments))
    budget, node_fields = budget_rows(KEY, name, months, ds1b, BUDGET_LINES, currency, unwritten)
    written |= {(code, month, "plan", f) for code, month, f in node_fields}
    for key, rows in (("ledger", ledger), ("invoicing", invoicing), ("budget", budget)):
        if rows:
            profile_id = PROFILES[key]
            layout = load_profile(profile_id, profiles_dir)[1]
            stem = profile_id.removesuffix("-illustrative")
            files.append(ExportFile(name, f"profile.{stem}", profile_id, tuple(rows), render_profile(layout, rows)))
    expenses = expense_rows(ds1b)
    if expenses:
        files.append(ExportFile(name, "expenses", "expenses-illustrative-1", tuple(expenses),
                                render_layout(LAYOUTS["expenses-illustrative-1"], expenses)))
    unwritten += remaining_unwritten(records, name, written, renamed)
    return BooksResult(tuple(files), tuple(unwritten), tuple(staged))
