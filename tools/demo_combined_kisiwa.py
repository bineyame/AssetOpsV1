"""DIESEL-1 K1 (ruling DIESEL-1-R3c §9c.1): the Kisiwa (KISIWA-001) Site, registered the way the combined demo
prepare will register it. K7 adds the story part to this file; K1 writes only the registration.

    python tools/demo_combined_kisiwa.py register <database-url> <work> <import-at ISO> <install-at ISO>

Steps, in order (modelled on `tools/demo_combined_kobo.py` `build` and `configure_at`):
1. import the Site from `backend/tests/fixtures/s1/kisiwa-001.yaml` (the shipped `kisiwa-diesel-hybrid-60kw`
   template rendered for KISIWA-001) at `import_at`;
2. convert its bindings with `backend/conversions/kisiwa-001-bindings.json` (12 rows, minigrid-roles-2) at
   `install_at`;
3. as known at install + 30 min: the three supply uses and the generator's generic no-load fuel rate at
   install + 25 min, then the labelled roles-4 demo configuration (the fuel level sensor's generic accuracy and the
   three roles-4 bindings) at install + 27 min.
`register` (Postgres only) also enables the Site's gateway and source as Kobo's build does and publishes diesel price
v1 at install + 1 h. Kisiwa has no productive load, so no productive-use price is published.

The no-load rate and the sensor accuracy are Site-declared data; their "generic" label travels in their basis
property, never in product copy. Nothing here adds Kisiwa to `tools/demo_combined.py`.
"""

from __future__ import annotations

import copy
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

from demo_combined import at, iso

ROOT = Path(__file__).resolve().parents[1]
CONVERSIONS = ROOT / "backend" / "conversions"

SITE_CODE = "KISIWA-001"
SITE_SOURCE = ROOT / "backend" / "tests" / "fixtures" / "s1" / "kisiwa-001.yaml"
IMPORT_PATH = "var/sites/kisiwa-001.yaml"
BINDINGS = json.loads((CONVERSIONS / "kisiwa-001-bindings.json").read_text(encoding="utf-8"))
ROLES4 = json.loads((CONVERSIONS / "kisiwa-001-minigrid-roles-demo-config.json").read_text(encoding="utf-8"))
FIXTURE_PRICES = CONVERSIONS / "demo-diesel-price-publications.json"

CONFIG_OFFSETS = {"uses": timedelta(minutes=25), "roles4": timedelta(minutes=27), "known": timedelta(minutes=30),
                  "price": timedelta(hours=1)}
#: DIESEL-1 §2.2: what each Kisiwa feeder supplies (load-clinic is the cold store, load-mill the water pump).
SUPPLY_USES = {"load-clinic": "ESSENTIAL_SERVICE", "load-res": "HOUSEHOLD", "load-mill": "HOUSEHOLD"}
SUPPLY_USE_NOTE = "Demonstration supply use declared at commissioning"
NO_LOAD = [
    {"property_key": "generator-no-load-fuel-rate", "value": 4.9, "unit": "L/h", "source": "SITE",
     "source_version": 1},
    {"property_key": "generator-no-load-fuel-rate-basis", "value": "GENERIC_DEFAULT", "unit": "state",
     "source": "SITE", "source_version": 1},
]
NO_LOAD_NOTE = ("Generic no-load fuel rate for a 60 kW diesel set (common design-software default, about 0.08 L/h "
                "per kW of rating); not this generator's datasheet. Owner decision 2026-11-07 (generic, labelled).")
#: The model pin: Kisiwa runs only on mini-grid v7 (K1a). Kobo stays on v6 (`d-verification-window-v3.json`).
RUN_PROFILE = {"model_profile": {"profile_id": "mini-grid", "profile_version": 7},
               "publication_profile": {"profile_id": "registered-kobo-publication", "profile_version": 5},
               "timestep_minutes": 5, "seed": 20260929}


class Clock:
    def __init__(self, now: datetime) -> None:
        self.now = now

    def __call__(self) -> datetime:
        return self.now


def import_source():
    """The import record and the sha256 of the fixture file's bytes."""
    from assetops_backend.sites.adapters.import_files import read_import_source
    from assetops_backend.sites.foundation_service import ImportSource

    read = read_import_source(str(SITE_SOURCE))
    return ImportSource(path=IMPORT_PATH, sha256=read.sha256, record=read.record)


def declare_supply_uses(foundation, imported, effective_from: datetime) -> None:
    for code, use in SUPPLY_USES.items():
        foundation.publish_component_properties(
            imported.tenant, imported.site, asset_code=code, effective_from=effective_from, note=SUPPLY_USE_NOTE,
            properties=[{"property_key": "supply-use", "value": use, "unit": "state", "source": "SITE",
                         "source_version": 1}])


def declare_no_load_rate(foundation, imported, effective_from: datetime) -> None:
    foundation.publish_component_properties(
        imported.tenant, imported.site, asset_code="generator", effective_from=effective_from, note=NO_LOAD_NOTE,
        properties=copy.deepcopy(NO_LOAD))


def configure_roles4(store, foundation, bindings, imported, effective_from: datetime):
    from assetops_backend.sites.demo_configuration import apply_demo_configuration

    doc = copy.deepcopy(ROLES4)
    doc["component_properties"]["effective_from"] = iso(effective_from)
    doc["bindings"]["effective_from"] = iso(effective_from)
    assert doc["status"].startswith("SIMULATED DEMO CONFIGURATION"), doc["status"]
    applied = apply_demo_configuration(store, foundation, bindings, imported.tenant, imported.site, doc)
    assert applied.periods[-1]["role_set"] == "minigrid-roles-4", applied.periods
    return applied


def register_in(store, import_at: datetime, install_at: datetime) -> dict:
    """Import, convert and configure KISIWA-001 in `store` (Postgres or an in-memory Foundation store)."""
    from assetops_backend.sites.binding_conversion import convert
    from assetops_backend.sites.binding_service import BindingService
    from assetops_backend.sites.foundation_service import FoundationService, import_site

    imported = import_site(store, tenant_slug="demo", configured_tenant_slug="demo", source=import_source(),
                           legacy_documents=(), clock=Clock(import_at))
    convert(store, BindingService(store, Clock(install_at)), imported.tenant, imported.site, BINDINGS)
    clock = Clock(install_at + CONFIG_OFFSETS["known"])
    foundation, bindings = FoundationService(store, "demo", clock), BindingService(store, clock)
    declare_supply_uses(foundation, imported, install_at + CONFIG_OFFSETS["uses"])
    declare_no_load_rate(foundation, imported, install_at + CONFIG_OFFSETS["uses"])
    applied = configure_roles4(store, foundation, bindings, imported, install_at + CONFIG_OFFSETS["roles4"])
    return {"site_code": SITE_CODE, "tenant_id": str(imported.tenant.id), "site_id": str(imported.site.id),
            "import_at": iso(import_at), "install_at": iso(install_at),
            "supply_uses_effective_from": iso(install_at + CONFIG_OFFSETS["uses"]),
            "no_load_effective_from": iso(install_at + CONFIG_OFFSETS["uses"]),
            "roles4_effective_from": iso(install_at + CONFIG_OFFSETS["roles4"]),
            "recorded_at": iso(install_at + CONFIG_OFFSETS["known"]),
            "periods": [dict(p) for p in applied.periods]}


def publish_price(url: str, recorded_at: datetime) -> None:
    """Diesel price v1 only, recorded at `recorded_at` through the test-only recorded-time seam (Kobo's pattern)."""
    from assetops_backend.financials.adapters.postgres_assumption_store import PostgresAssumptionStore
    from assetops_backend.publish_assumption import main as publish
    import pg_harness

    store = PostgresAssumptionStore(url, test_recorded_clock_override=lambda: recorded_at)
    try:
        code = publish(["fixture", "--site", SITE_CODE, "--file", str(FIXTURE_PRICES), "--step", "v1"], store=store)
        if code != 0:
            raise SystemExit(f"diesel price v1 publication failed ({code})")
    finally:
        pg_harness.dispose(store)


def register(url: str, work: Path, import_at: datetime, install_at: datetime) -> dict:
    """`register_in` on Postgres, the Site's gateway and source enabled, diesel price v1; writes
    `<work>/kisiwa-register.json`."""
    import pg_harness
    from sqlalchemy import create_engine, text
    from assetops_backend.sites.adapters.postgres_foundation_store import PostgresFoundationStore

    store = PostgresFoundationStore(url)
    engine = create_engine(url)
    try:
        result = register_in(store, import_at, install_at)
        with engine.begin() as c:
            c.execute(text("UPDATE gateway SET disabled_at = NULL WHERE site_id = :s"), {"s": result["site_id"]})
            c.execute(text("UPDATE source SET disabled_at = NULL WHERE site_id = :s"), {"s": result["site_id"]})
    finally:
        engine.dispose()
        pg_harness.dispose(store)
    publish_price(url, install_at + CONFIG_OFFSETS["price"])
    result["price_recorded_at"] = iso(install_at + CONFIG_OFFSETS["price"])
    work.mkdir(parents=True, exist_ok=True)
    (work / "kisiwa-register.json").write_text(json.dumps(result, indent=2, sort_keys=True, default=str) + "\n",
                                               encoding="utf-8")
    return result


def main(argv: list[str]) -> int:
    if len(argv) != 5 or argv[0] != "register":
        print(__doc__, file=sys.stderr)
        return 2
    _, url, work, import_at, install_at = argv
    result = register(url, Path(work), at(import_at), at(install_at))
    print(json.dumps({"site_code": result["site_code"], "roles4_effective_from": result["roles4_effective_from"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
