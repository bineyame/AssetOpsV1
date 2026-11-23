"""DD4.4 (spec `specs/DD-demo-data/spec.md` §5.6, §5.4; D-DD.20, D-DD.99, D-DD.123, D-DD.124): the measured books.

Written by `world_history.py exports --telemetry DIR` from each tenant's `<slug>/telemetry/measured.json`, after the
readings, so each metered quantity has one figure (D-DD.20):

- cold electricity bill (`cold-electricity-bill-illustrative`): one USAGE row per room-month, the room meter's kWh at
  `COLD_GRID_PRICE` under `COLD_GRID_TARIFF`, account `<CODE>-UTIL`;
- EV utility invoice (`ev-utility-invoice-illustrative`): one USAGE row per price class of the Site's schedule
  (`body.band`), plus DEMAND where the schedule has a `demand_rate`; prices and classes from the Site's TARIFF_SCHEDULE
  records (`world/tariffs.py`, the records the product admits), never from literals;
- departure log (`ev-departures-illustrative`): one row per bus-night in the span, `block_met` derived;
- `<slug>.meter-billed.json` (`assetops.world-meter-billed/1`): each measured leaf with the manifest's value beside the
  metered one, information only, never admitted;
- cold and EV statements (`assetops.world-statements/1`): cold revenue = Σ the invoicing file's CHARGE rows, energy
  cost = Σ bill rows; EV energy cost = Σ invoice rows and no revenue (a captive depot: missing is never zero).

Bills and invoices cover whole months only (a month with `partial_to` is not billed). Every value is read from the
written text, so a book equals `measured.json` exactly. Pure: documents in, files out.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import ROUND_HALF_EVEN, Decimal

from .canonical import file_bytes
from .exports import ExportFile
from .profile_csv import PROFILES_DIR, load_profile, render_profile
from .records import STRUCTURE_KEY
from .statements import SCHEMA as STATEMENTS_SCHEMA, source_ref
from .tariffs import tariff_schedules

MEASURED_SCHEMA = "assetops.world-measured/1"
METER_BILLED_SCHEMA = "assetops.world-meter-billed/1"
#: D-DD.124: one illustrative grid tariff for the cold rooms, declared once (parity test against `M`
#: `harvest-cold.prices.electricity_usd_per_kwh`; the run refuses a view whose price differs).
COLD_GRID_TARIFF = "T-GRID-COLD"
COLD_GRID_PRICE = Decimal("0.20")
#: D-DD.99: the fixed key set of a month, by vertical (`partial_to` is the frame's, on the span's last month).
MONTH_KEYS = {"MINI_GRID": frozenset({"demand_kwh", "served_kwh", "unserved_kwh", "generator_kwh"}),
              "COLD_CHAIN": frozenset({"room_kwh"}),
              "EV_DEPOT_CAPTIVE": frozenset({"bands", "demand_kw", "import_kwh", "windows"})}  # windows: D-DD.158
#: D-DD.158: the EV month's `windows` key set, fixed.
EV_WINDOW_KEYS = frozenset({"2200_2400", "0000_0500"})
DEPARTURE_KEYS = frozenset({"site_code", "vehicle_ref", "block_ref", "service_day", "departure_at", "required_kwh",
                            "kwh_at_departure"})
PROFILES = {"bill": "cold-electricity-bill-illustrative", "invoice": "ev-utility-invoice-illustrative",
            "departures": "ev-departures-illustrative"}
CENT = Decimal("0.01")


class MeasuredRefused(ValueError):
    """A refusal; the message's first word is its code (`TEL_FOUNDATION`, `EMU_MEASURED`)."""


@dataclass(frozen=True)
class MeasuredResult:
    files: tuple[ExportFile, ...]
    #: (file name, bytes): `<slug>.meter-billed.json` and `<slug>.statements.json`, cold and EV tenants.
    extras: tuple[tuple[str, bytes], ...]


def _money(value: Decimal) -> Decimal:
    return value.quantize(CENT, rounding=ROUND_HALF_EVEN)


def _next_month(month: str) -> str:
    year, number = int(month[:4]), int(month[5:])
    return f"{year + number // 12}-{number % 12 + 1:02d}"


def _structure(tenant: dict) -> str:
    return STRUCTURE_KEY.get(tenant.get("vertical"), "")


def read_measured(document: dict, tenant: dict) -> dict:
    """D-DD.99's read: the schema, the tenant, each month's fixed key set; `departures` for an EV tenant only."""
    slug, structure = tenant["tenant"], _structure(tenant)
    if document.get("schema") != MEASURED_SCHEMA or document.get("tenant") != slug:
        raise MeasuredRefused(f"TEL_FOUNDATION {slug} measured.json schema or tenant")
    allowed = {"schema", "tenant", "sites"} | ({"departures"} if structure == "EV_DEPOT_CAPTIVE" else set())
    if not set(document) <= allowed:
        raise MeasuredRefused(f"TEL_FOUNDATION {slug} keys {sorted(set(document) - allowed)}")
    keys = MONTH_KEYS[structure]
    for code, months in document["sites"].items():
        for month, block in months.items():
            if set(block) - {"partial_to"} != keys:
                raise MeasuredRefused(f"TEL_FOUNDATION {code} {month} keys {sorted(block)}")
            if "windows" in keys and set(block["windows"]) != EV_WINDOW_KEYS:
                raise MeasuredRefused(f"TEL_FOUNDATION {code} {month} windows {sorted(block['windows'])}")
    for d in document.get("departures", []):
        if set(d) != DEPARTURE_KEYS:
            raise MeasuredRefused(f"TEL_FOUNDATION departure keys {sorted(d)}")
    return document


def _whole(months: dict) -> list[tuple[str, dict]]:
    return [(m, b) for m, b in sorted(months.items()) if "partial_to" not in b]


def _charge(code: str, record_id: str, month: str, quantity: str, unit: str, amount: Decimal, currency: str,
            body: dict) -> dict:
    return {"format_version": 1, "kind": "CHARGE", "source_record_id": record_id, "source_version": "1",
            "site_code": code, "subject": {"kind": "SITE", "ref": code},
            "clocks": {"effective_from": f"{month}-01", "effective_to": f"{_next_month(month)}-01",
                       "recognition_period": month},
            "quantity": {"value": quantity, "unit": unit}, "amount": {"value": f"{amount:.2f}", "currency": currency},
            "body": body}


def cold_bill_rows(tenant: dict, document: dict, currency: str) -> list[dict]:
    price = Decimal(str(tenant["prices"]["electricity_usd_per_kwh"]))
    if price != COLD_GRID_PRICE:
        raise MeasuredRefused(f"EMU_MEASURED {tenant['tenant']} electricity price {price} is not {COLD_GRID_TARIFF}'s "
                              f"{COLD_GRID_PRICE}")
    rows = []
    for code, months in sorted(document["sites"].items()):
        for month, block in _whole(months):
            kwh = block["room_kwh"]
            rows.append(_charge(code, f"gen:{code}:{month}:electricity", month, kwh, "kWh",
                                _money(Decimal(kwh) * COLD_GRID_PRICE), currency,
                                {"account_ref": f"{code}-UTIL", "line_type": "USAGE", "tariff_code": COLD_GRID_TARIFF}))
    return rows


def _schedule(records: list[dict], code: str, month: str) -> dict:
    """The TARIFF_SCHEDULE in force for the whole month (a month split across two schedules is refused)."""
    first, last = date.fromisoformat(f"{month}-01"), date.fromisoformat(f"{_next_month(month)}-01")
    found = [r for r in records if r["site_code"] == code and r["clocks"]["effective_from"] <= first.isoformat()
             and last.isoformat() <= _after(r)]
    if len(found) != 1:
        raise MeasuredRefused(f"EMU_MEASURED {code} {month} has {len(found)} schedules in force for the whole month")
    return found[0]


def _after(record: dict) -> str:
    """The day after a schedule's last day (`effective_to` is inclusive in `world/tariffs.py`)."""
    to = record["clocks"].get("effective_to")
    if to is None:
        return "9999-12-31"
    return date.fromordinal(date.fromisoformat(to).toordinal() + 1).isoformat()


def ev_invoice_rows(document: dict, schedules: list[dict], currency: str) -> list[dict]:
    rows = []
    for code, months in sorted(document["sites"].items()):
        for month, block in _whole(months):
            schedule = _schedule(schedules, code, month)
            body = schedule["body"]
            prices: dict[str, Decimal] = {}
            for band in body["bands"]:  # D-DD.61: the class is the band name before `-`
                prices.setdefault(band["band"].split("-")[0], Decimal(band["rate"]))
            if set(prices) != set(block["bands"]):
                raise MeasuredRefused(f"EMU_MEASURED {code} {month} bands {sorted(block['bands'])} against the "
                                      f"schedule's {sorted(prices)}")
            tariff = body["contract_ref"]
            for name, price in prices.items():
                kwh = block["bands"][name]
                rows.append(_charge(code, f"gen:{code}:{month}:invoice:{name}", month, kwh, "kWh",
                                    _money(Decimal(kwh) * price), currency,
                                    {"account_ref": f"{code}-UTIL", "band": name, "line_type": "USAGE",
                                     "tariff_code": tariff}))
            if "demand_rate" in body:
                kw = block["demand_kw"]
                rows.append(_charge(code, f"gen:{code}:{month}:invoice:DEMAND", month, kw, "kW",
                                    _money(Decimal(kw) * Decimal(body["demand_rate"])), currency,
                                    {"account_ref": f"{code}-UTIL", "band": "DEMAND", "line_type": "DEMAND",
                                     "tariff_code": tariff}))
    return rows


def departure_rows(document: dict) -> list[dict]:
    rows = []
    for d in document.get("departures", []):
        code, bus = d["site_code"], d["vehicle_ref"]
        rows.append({"format_version": 1, "kind": "DEPARTURE",
                     "source_record_id": f"gen:{code}:{d['service_day']}:departure:{bus.removeprefix(code + '-')}",
                     "source_version": "1", "site_code": code, "subject": {"kind": "VEHICLE", "ref": bus},
                     "clocks": {"occurred_at": d["departure_at"]},
                     "body": {"vehicle_ref": bus, "service_day": d["service_day"],
                              "block_met": Decimal(d["kwh_at_departure"]) >= Decimal(d["required_kwh"]),
                              "kwh_at_departure": d["kwh_at_departure"], "block_ref": d["block_ref"]}})
    return rows


# --- meter_billed (D-DD.20, D-DD.124): information only ----------------------------------------------------------

def _cold_metered(block: dict, bill: dict | None) -> dict[str, str | None]:
    return {"kwh": block["room_kwh"], "energy": None if bill is None else bill["amount"]["value"]}


def _ev_metered(block: dict, invoice: dict[str, dict]) -> dict[str, str | None]:
    def amount(band: str) -> str | None:
        return invoice[band]["amount"]["value"] if band in invoice else None

    usage = [r for r in invoice.values() if r["body"]["line_type"] == "USAGE"]
    return {"kwh": block["import_kwh"], "peak_kwh": block["bands"].get("PEAK"),
            "offpeak_kwh": block["bands"].get("OFFPEAK"), "max_kw": block["demand_kw"],
            "kwh_2200_2400": block["windows"]["2200_2400"], "kwh_0000_0500": block["windows"]["0000_0500"],  # D-DD.158
            "peak_cost": amount("PEAK"), "offpeak_cost": amount("OFFPEAK"), "demand_cost": amount("DEMAND"),
            "energy_cost": f"{sum((Decimal(r['amount']['value']) for r in usage), Decimal(0)):.2f}" if usage else None}


def meter_billed(view: dict, history: dict, tenant: dict, document: dict, book_rows: list[dict]) -> dict:
    slug, structure = tenant["tenant"], _structure(tenant)
    names = {s["code"]: s["site"] for s in tenant["sites"]}
    periods = {s["code"]: s["period"]["actual"] for s in tenant["sites"]}
    rows = []
    for code, months in sorted(document["sites"].items()):
        for month, block in sorted(months.items()):
            if month == view["accounting_period"]:
                manifest, where = periods[code], f"tenants.{slug}.sites.{code}.period.actual"
            else:
                manifest = history["tenants"][slug].get(names[code], {}).get(month, {}).get("actual")
                where = f"history.tenants.{slug}.{names[code]}.{month}.actual"
            if manifest is None:
                continue  # a month with no books (November): nothing to set beside the meter
            mine = [r for r in book_rows if r["site_code"] == code and r["clocks"]["recognition_period"] == month]
            if structure == "COLD_CHAIN":
                metered = _cold_metered(block, mine[0] if mine else None)
            else:
                metered = _ev_metered(block, {r["body"]["band"]: r for r in mine})
            for leaf, value in metered.items():
                if leaf in manifest:
                    rows.append({"site_code": code, "month": month, "leaf": leaf, "metered": value,
                                 "manifest": str(manifest[leaf]), "manifest_path": f"{where}.{leaf}"})
    return {"schema": METER_BILLED_SCHEMA, "tenant": slug, "rows": rows}


# --- statements (§5.4, D-DD.124) --------------------------------------------------------------------------------

def _by_month(rows: list[dict]) -> dict[str, Decimal]:
    out: dict[str, Decimal] = {}
    for r in rows:
        month = r["clocks"]["recognition_period"]
        out[month] = out.get(month, Decimal(0)) + Decimal(r["amount"]["value"])
    return out


def statements(tenant: dict, currency: str, cost_rows: list[dict], revenue_rows: list[dict] | None) -> dict:
    """One statement per billed month. `revenue_rows` None: the EV depot, whose statement omits `revenue`."""
    if revenue_rows is None and _structure(tenant) != "EV_DEPOT_CAPTIVE":
        raise MeasuredRefused(f"EMU_MEASURED {tenant['tenant']} a statement without revenue is EV_DEPOT only")
    cost = _by_month(cost_rows)
    revenue = None if revenue_rows is None else _by_month(revenue_rows)
    out = []
    for month in sorted(cost):
        entry = {"period": month, "currency": currency, "energy_cost": f"{cost[month]:.2f}",
                 "source_ref": source_ref(month)}
        if revenue is not None:
            if month not in revenue:
                raise MeasuredRefused(f"EMU_MEASURED STATEMENT_INCOMPLETE {tenant['tenant']} {month}")
            entry["revenue"] = f"{revenue[month]:.2f}"
        out.append(entry)
    return {"schema": STATEMENTS_SCHEMA, "tenant": tenant["tenant"], "statements": out}


# --- the run -----------------------------------------------------------------------------------------------------

def build_measured_exports(view: dict, history: dict, books_files: tuple[ExportFile, ...], measured: dict[str, dict],
                           profiles_dir=PROFILES_DIR) -> MeasuredResult:
    """`measured`: tenant slug -> its `measured.json` document, for every cold and EV tenant to write; `books_files`
    the decided books (the cold invoicing file's CHARGE rows are the statement's revenue)."""
    currency = view["currency"]
    layouts = {key: load_profile(pid, profiles_dir)[1] for key, pid in PROFILES.items()}
    schedules = tariff_schedules(view)
    files, extras = [], []
    for tenant in view["tenants"]:
        slug, structure = tenant["tenant"], _structure(tenant)
        if structure not in ("COLD_CHAIN", "EV_DEPOT_CAPTIVE") or slug not in measured:
            continue
        document = read_measured(measured[slug], tenant)
        missing = {s["code"] for s in tenant["sites"]} - set(document["sites"])
        if missing:
            raise MeasuredRefused(f"EMU_MEASURED {slug} measured.json lacks {sorted(missing)}")
        if structure == "COLD_CHAIN":
            bill = cold_bill_rows(tenant, document, currency)
            files.append(ExportFile(slug, "profile.cold-electricity-bill", PROFILES["bill"], tuple(bill),
                                    render_profile(layouts["bill"], bill)))
            invoicing = next(f for f in books_files if f.tenant == slug and f.key == "profile.cold-storage-invoicing")
            revenue = [r for r in invoicing.records if r["kind"] == "CHARGE"]
            book_rows, statement = bill, statements(tenant, currency, bill, revenue)
        else:
            invoice = ev_invoice_rows(document, schedules[slug]["records"], currency)
            departures = departure_rows(document)
            files.append(ExportFile(slug, "profile.ev-utility-invoice", PROFILES["invoice"], tuple(invoice),
                                    render_profile(layouts["invoice"], invoice)))
            files.append(ExportFile(slug, "profile.ev-departures", PROFILES["departures"], tuple(departures),
                                    render_profile(layouts["departures"], departures)))
            book_rows, statement = invoice, statements(tenant, currency, invoice, None)
        extras.append((f"{slug}.meter-billed.json", file_bytes(meter_billed(view, history, tenant, document, book_rows))))
        extras.append((f"{slug}.statements.json", file_bytes(statement)))
    return MeasuredResult(tuple(files), tuple(extras))


__all__ = ["COLD_GRID_PRICE", "COLD_GRID_TARIFF", "MeasuredRefused", "MeasuredResult", "build_measured_exports",
           "cold_bill_rows", "departure_rows", "ev_invoice_rows", "meter_billed", "read_measured", "statements"]
