"""DD2b (spec `specs/DD-demo-data/spec.md` §3, §5.2, §5.3; D-DD.61): the cold rate card and the EV time-of-use
schedules, written as canonical TARIFF_SCHEDULE records from the manifest's prices in the view.

DS1b writes no TARIFF_SCHEDULE, so this module is their one writer. A tariff comes from the party that sets it: the
cold operator's invoicing system issues the rate card (`storage_rate_card`, source system `cold-storage-invoicing`),
the utility issues the EV schedule (`utility_invoice`, source system `ev-utility-invoice`, the system of the EV
invoice profile). The batches are staged canonical JSON (D-DD.60), not a native file.

- Cold: per Site, `T-STORAGE` from 2026-07-01, one band `STORAGE` 00:00-24:00 at `storage_usd_per_crate_day`.
- EV: Embakasi `C-114`, to the day before 1 November, with every non-peak hour at the off-peak price, then from 2026-11-01 with the
  `NIGHT` 00:00-05:00 tier; Ruiru `C-117` (the October Embakasi bands, its own prices); Kasarani `FLAT-EV-KASARANI`.
  Every price is read from the Site's `tariff.prices`; a Site with a `demand_per_kw_month` carries a `demand_rate`.
- WORKAROUND (D-DD.61): a canonical band is one interval with a unique name, so the all-other-hours off-peak price is
  two bands, `OFFPEAK-AM` and `OFFPEAK-PM`. An invoice line reads `OFFPEAK`; the link is the name before the hyphen.

Standard library and the world modules only.
"""

from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

from .books import batch_object
from .records import STRUCTURE_KEY

COLD_SOURCE = ("storage_rate_card", "cold-storage-invoicing")
EV_SOURCE = ("utility_invoice", "ev-utility-invoice")
FROM = "2026-07-01"  # the first history month
NIGHT_FROM = "2026-11-01"  # the new Embakasi contract term
LAST_OLD_DAY = (date.fromisoformat(NIGHT_FROM) - timedelta(days=1)).isoformat()


def _money(value: object) -> str:
    return f"{Decimal(str(value)):.2f}"


def _band(name: str, start: str, end: str, rate: object, unit: str) -> dict:
    return {"band": name, "from": start, "to": end, "rate": _money(rate), "unit": unit}


def _record(code: str, effective_from: str, effective_to: str | None, contract: str, currency: str, bands: list,
            demand: object | None = None) -> dict:
    body = {"contract_ref": contract, "currency": currency, "bands": bands}
    if demand is not None:
        body["demand_rate"] = _money(demand)
    clocks = {"effective_from": effective_from}
    if effective_to is not None:
        clocks["effective_to"] = effective_to
    return {"format_version": 1, "kind": "TARIFF_SCHEDULE", "source_record_id": f"gen:{code}:tariff:{effective_from}",
            "source_version": "1", "site_code": code, "clocks": clocks, "body": body}


def _cold(tenant: dict, currency: str) -> list[dict]:
    rate = tenant["prices"]["storage_usd_per_crate_day"]
    return [_record(site["code"], FROM, None, "T-STORAGE", currency,
                    [_band("STORAGE", "00:00", "24:00", rate, "per_crate_day")]) for site in tenant["sites"]]


def _ev_site(site: dict, currency: str) -> list[dict]:
    code, tariff = site["code"], site["tariff"]
    prices = tariff["prices"]
    if tariff.get("type") == "FLAT":
        return [_record(code, FROM, None, f"FLAT-EV-{site['site'].upper()}", currency,
                        [_band("FLAT", "00:00", "24:00", tariff["usd_per_kwh"], "per_kWh")])]
    contract = tariff["contract"].split()[0]
    demand = prices["demand_per_kw_month"]
    peak, off = prices["peak"], prices["offpeak"]

    def day(night: object | None) -> list[dict]:
        bands = [_band("OFFPEAK-AM", "00:00", "18:00", off, "per_kWh")] if night is None else [
            _band("NIGHT", "00:00", "05:00", night, "per_kWh"), _band("OFFPEAK-AM", "05:00", "18:00", off, "per_kWh")]
        return bands + [_band("PEAK", "18:00", "22:00", peak, "per_kWh"),
                        _band("OFFPEAK-PM", "22:00", "24:00", off, "per_kWh")]

    if prices["night_from_1_nov"] == off:  # no night tier (Ruiru's older contract)
        return [_record(code, FROM, None, contract, currency, day(None), demand)]
    return [_record(code, FROM, LAST_OLD_DAY, contract, currency, day(None), demand),
            _record(code, NIGHT_FROM, None, contract, currency, day(prices["night_from_1_nov"]), demand)]


def tariff_schedules(view: dict) -> dict[str, dict]:
    """{tenant: the canonical batch object of its TARIFF_SCHEDULE records}, cold and EV tenants only."""
    out = {}
    for tenant in view.get("tenants", []):
        key = STRUCTURE_KEY.get(tenant.get("vertical"))
        if key == "COLD_CHAIN":
            source, rows = COLD_SOURCE, _cold(tenant, view["currency"])
        elif key == "EV_DEPOT_CAPTIVE":
            source = EV_SOURCE
            rows = [r for site in tenant["sites"] for r in _ev_site(site, view["currency"])]
        else:
            continue
        out[tenant["tenant"]] = batch_object(view, tenant["tenant"], source[0], source[1],
                                             sorted(rows, key=lambda r: (r["site_code"], r["clocks"]["effective_from"])))
    return out
