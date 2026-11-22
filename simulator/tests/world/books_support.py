"""DD2b test support (spec `specs/DD-demo-data/spec.md` §5.2, §5.3): the built books of the fixture view, the
manifest `M` read as YAML (the modules never read it), and the profile samples (D-DD.24).

Samples of a file the emulator writes are a slice of that file (`SAMPLES`), so a sample cannot drift from the
emulator. Samples of a file whose rows come later (DD4.4) or that has under three rows are rendered from the
hand-written records of `HAND_SAMPLES`. `--update-golden` rewrites both (`test_dd2b_books.py`).
"""

from __future__ import annotations

import copy
import json
from functools import lru_cache
from pathlib import Path

import yaml

from assetops_simulator.world.books import build_books
from assetops_simulator.world.exports import file_name
from assetops_simulator.world.history import generate_history
from assetops_simulator.world.profile_csv import PROFILES_DIR, load_profile, render_profile, row_digest
from assetops_simulator.world.records import build_records
from assetops_simulator.world.view import ManifestView

from .conftest import REPOSITORY_ROOT, load_fixture

MANIFEST = REPOSITORY_ROOT / "Docs" / "demo-sprint" / "product-direction-layer4" / "demo-site-scenario-manifest.yaml"
COLD, EV = "harvest-cold", "metro-bus"


@lru_cache(maxsize=1)
def manifest() -> dict:
    return yaml.safe_load(MANIFEST.read_text(encoding="utf-8"))


def m_tenant(name: str) -> dict:
    return next(t for t in manifest()["tenants"] if t["tenant"] == name)


def m_site(tenant: str, code: str) -> dict:
    return next(s for s in m_tenant(tenant)["sites"] if s["code"] == code)


def build(view: dict | None = None, edit_history=None):
    """The books of a view (the fixture by default); `edit_history(history)` may plant a change in the history."""
    view = ManifestView.from_document(load_fixture() if view is None else view)
    history = generate_history(view)
    if edit_history is not None:
        edit_history(history)
    return view, history, build_records(view, history), build_books(view, history)


_CACHE: dict = {}


def built():
    """The fixture's books, built once per session (callers must not change them)."""
    if "b" not in _CACHE:
        _CACHE["b"] = build()
    return _CACHE["b"]


def files_by_name(books) -> dict:
    return {file_name(f): f for f in books.files}


def tenant_view(view: dict, name: str) -> dict:
    return next(t for t in view["tenants"] if t["tenant"] == name)


# --- samples (D-DD.24) -----------------------------------------------------------------------------------------------

def _first(n: int):
    return lambda rows: rows[:n]


def _month_sites(month: str, *codes: str):
    return lambda rows: [r for r in rows if r["clocks"]["recognition_period"] == month and r["site_code"] in codes]


def _ins_and_outs(n: int):
    def pick(rows):
        ins = [r for r in rows if r["body"]["direction"] == "IN"][:n]
        outs = [r for r in rows if r["body"]["direction"] == "OUT"][:n]
        return [r for r in rows if r in ins or r in outs]
    return pick


def _invoicing_slice(rows):
    """Three invoices, three receipts and the credit note: every Type of the export (D-DD.59)."""
    out = []
    for kind, n in (("CHARGE", 3), ("RECEIPT", 3), ("ADJUSTMENT", 1)):
        out += [r for r in rows if r["kind"] == kind][:n]
    return out


def _receipt(code, i, at, amount, method, status):
    return {"format_version": 1, "kind": "RECEIPT", "source_record_id": f"gen:{code}:2026-10:receipt-x{i}",
            "source_version": "", "site_code": code, "subject": {"kind": "CUSTOMER", "ref": f"{code}-K-0{i}"},
            "clocks": {"occurred_at": at, "recognition_period": "2026-10"},
            "amount": {"value": amount, "currency": "USD"}, "status": status,
            "body": {"payer_ref": f"{code}-K-0{i}", "method": method}}


#: Hand-written rows added to a slice so the sample shows every value of the profile's maps (3A6 admission step 4b):
#: the emulator writes no cash receipt and nothing in transit (the cold structure has no in-transit leaf, D-DD.50).
SAMPLE_EXTRAS = {
    "cold-storage-invoicing-illustrative": [
        _receipt("COLD-THIKA", 7, "2026-10-30T15:20:00+03:00", "42.00", "CASH", "COLLECTED"),
        _receipt("COLD-THIKA", 8, "2026-10-31T18:45:00+03:00", "36.00", "MOBILE_MONEY", "PAID_IN_TRANSIT"),
    ],
}

#: profile id -> (emulated file, row selection)
SAMPLES = {
    "cold-storage-ledger-illustrative": (f"{COLD}.profile.cold-storage-ledger.csv", _ins_and_outs(3)),
    "cold-storage-invoicing-illustrative": (f"{COLD}.profile.cold-storage-invoicing.csv", _invoicing_slice),
    "cold-budget-illustrative": (f"{COLD}.profile.cold-budget.csv", _month_sites("2026-07", "COLD-THIKA")),
    "ev-budget-illustrative": (f"{EV}.profile.ev-budget.csv", _month_sites("2026-07", "EV-EMB", "EV-RUI")),
    "ev-fleet-roster-illustrative": (f"{EV}.profile.ev-fleet-roster.csv", _first(6)),
}


def _ticket(code, asset, opened, state, ack=None, restored=None):
    body = {"asset_ref": asset, "counterparty_ref": "oem-contractor"}
    if ack:
        body["acknowledged_at"] = ack
    if restored:
        body["restored_at"] = restored
    return {"format_version": 1, "kind": "SERVICE_TICKET", "source_record_id": f"gen:{code}:ticket:{asset}",
            "source_version": "", "site_code": code, "subject": {"kind": "ASSET", "ref": asset},
            "clocks": {"occurred_at": opened}, "status": state, "body": body}


def _invoice_line(code, band, line_type, qty, unit, amount, tariff, month="2026-10", first="2026-10-01",
                  after="2026-11-01"):
    return {"format_version": 1, "kind": "CHARGE", "source_record_id": f"gen:{code}:{month}:invoice:{band}",
            "source_version": "1", "site_code": code, "subject": {"kind": "SITE", "ref": code},
            "clocks": {"effective_from": first, "effective_to": after, "recognition_period": month},
            "quantity": {"value": qty, "unit": unit}, "amount": {"value": amount, "currency": "USD"},
            "body": {"account_ref": f"{code}-UTIL", "band": band, "line_type": line_type, "tariff_code": tariff}}


def _departure(code, bus, day, at, met, kwh):
    return {"format_version": 1, "kind": "DEPARTURE", "source_record_id": f"gen:{code}:{day}:departure:{bus[-2:]}",
            "source_version": "1", "site_code": code, "subject": {"kind": "VEHICLE", "ref": bus},
            "clocks": {"occurred_at": at},
            "body": {"vehicle_ref": bus, "service_day": day, "block_met": met, "kwh_at_departure": kwh,
                     "block_ref": f"{code}-BLK-{bus[-2:]}"}}


#: Hand-written sample records (rows come in DD4.4, or the file has under three rows). Ruiru's October bill lines are
#: the manifest's (6076 kWh x 0.24, 54684 kWh x 0.12, 380 kW x 12.00).
HAND_SAMPLES = {
    "ev-service-tickets-illustrative": [
        _ticket("EV-KAS", "CH-K2", "2026-11-01T23:40:00+03:00", "OPEN"),
        _ticket("EV-RUI", "CH-R7", "2026-10-06T00:00:00+03:00", "OPEN"),
        _ticket("EV-EMB", "CH-E3", "2026-09-12T02:15:00+03:00", "RESTORED", "2026-09-12T08:05:00+03:00",
                "2026-09-14T16:30:00+03:00"),
        _ticket("EV-EMB", "CH-E5", "2026-08-03T21:10:00+03:00", "ACKNOWLEDGED", "2026-08-04T09:00:00+03:00"),
        _ticket("EV-RUI", "CH-R2", "2026-07-19T04:30:00+03:00", "CLOSED", "2026-07-19T10:00:00+03:00",
                "2026-07-20T12:00:00+03:00"),
    ],
    "ev-utility-invoice-illustrative": [
        _invoice_line("EV-RUI", "PEAK", "USAGE", "6076", "kWh", "1458.24", "C-117"),
        _invoice_line("EV-RUI", "OFFPEAK", "USAGE", "54684", "kWh", "6562.08", "C-117"),
        _invoice_line("EV-RUI", "DEMAND", "DEMAND", "380", "kW", "4560.00", "C-117"),
        _invoice_line("EV-EMB", "NIGHT", "USAGE", "4200", "kWh", "378.00", "C-114", "2026-11", "2026-11-01",
                      "2026-12-01"),
    ],
    "ev-departures-illustrative": [
        _departure("EV-KAS", "EV-KAS-B01", "2026-11-01", "2026-11-02T05:00:00+03:00", True, "150.000"),
        _departure("EV-KAS", "EV-KAS-B07", "2026-11-02", "2026-11-03T05:00:00+03:00", False, "96.500"),
        _departure("EV-RUI", "EV-RUI-B03", "2026-10-06", "2026-10-07T05:00:00+03:00", True, "140.000"),
    ],
}


def sample_of(profile_id: str, books=None) -> tuple[bytes, list[dict]]:
    """The sample CSV and the expected records a profile ships with."""
    layout = load_profile(profile_id)[1]
    if profile_id in HAND_SAMPLES:
        records = copy.deepcopy(HAND_SAMPLES[profile_id])
        for r in records:
            if layout.version_digest:
                r["source_version"] = row_digest(layout, r)
        return render_profile(layout, records), records
    name, pick = SAMPLES[profile_id]
    f = files_by_name((books or built()[3]))[name]
    records = pick(list(f.records)) + copy.deepcopy(SAMPLE_EXTRAS.get(profile_id, []))
    for r in records:
        if layout.version_digest and not r["source_version"]:
            r["source_version"] = row_digest(layout, r)
    return render_profile(layout, records), records


def expected_bytes(records: list[dict]) -> bytes:
    return (json.dumps(records, indent=2, ensure_ascii=False) + "\n").encode("utf-8")


def shipped(profile_id: str) -> tuple[Path, Path]:
    return PROFILES_DIR / f"{profile_id}.sample.csv", PROFILES_DIR / f"{profile_id}.expected.json"


#: D-DD.65a: sha256 of every cold and EV exported file of the fixture view (the determinism pin; the EV golden of D-DD.59).
PINNED_COLD_EV: dict[str, str] = {
    "harvest-cold.expenses.csv":
        "63d607d981a0b4a05bd093f587918fc38c0bdb1e076d3642b6780cc61668a4e1",
    "harvest-cold.profile.cold-budget.csv":
        "9294a419590a6ee53a6a223031b1f543d08f0afacf02e41822a166225fac7609",
    "harvest-cold.profile.cold-storage-invoicing.csv":
        "3d6dd3e77b438d556d44ea39fc864836317188fa56f2b23ebcb87d686a7cfc4c",  # DD4a: receiving lots (D-DD.85)
    "harvest-cold.profile.cold-storage-ledger.csv":
        "474a7d3bdc013b93b9bcb4595cb7efb5958d30b2957b75355b06231dfd32eb33",  # DD4a: receiving lots (D-DD.85)
    "metro-bus.expenses.csv":
        "5b68506247721888acf47996428f1726c8f80a81bdef15dc8dfe11ee3400c822",
    "metro-bus.profile.ev-budget.csv":
        "3bfbfac1c3fd72c93b4291d9b3c2d690bc0d1e1d7c778413802cdc63af263748",
    "metro-bus.profile.ev-fleet-roster.csv":
        "3576f26c9e9b88caa948b1a1292f9d7bbac7c0ef6f48c3fa5f3fc51061bb681c",
    "metro-bus.profile.ev-service-tickets.csv":
        "3579df14f4c4442a38620b2a0ee5c7360ff5b18c4d061c5beb462f9c042b4a24",
}
