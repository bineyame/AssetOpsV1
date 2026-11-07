"""DIESEL-1 K1 (ruling DIESEL-1-R3c §9c.1) L2: F0r's measured result reproduces on the registered Kisiwa Site.

Needs `ASSETOPS_TEST_DATABASE_URL` naming a `*_test` database (K1: `assetops_k1_test`); skipped without it.

KISIWA-001 is registered on Postgres by `tools/demo_combined_kisiwa.py` `register_in` on F0r's clock (import 09:00Z,
conversion 09:30Z; everything recorded by 10:00Z), then `tools/probe_kisiwa_fuel.py` `build()` runs unedited with
its `Registered` replaced by `KisiwaRegistered` (setup clock 11:00Z, product mini-grid v7). The result must equal the
committed `.agent/DIESEL-F0/probe-result.json` except for the keys the ruling removes: the model lines, the
registered-path record and the example report text; the fuel-level binding is compared on role, units and
conversion only.
"""

from __future__ import annotations

import copy
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
for extra in (ROOT / "backend" / "tests", ROOT / "tools", ROOT / "host", Path(__file__).resolve().parent):
    if str(extra) not in sys.path:
        sys.path.insert(0, str(extra))

URL = os.environ.get("ASSETOPS_TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(
    not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)"
)

REFERENCE = ROOT / ".agent" / "DIESEL-F0" / "probe-result.json"
IMPORT_AT = datetime(2026, 9, 29, 9, 0, tzinfo=timezone.utc)
INSTALL_AT = datetime(2026, 9, 29, 9, 30, tzinfo=timezone.utc)
SETUP_AT = "2026-09-29T11:00:00Z"
BINDING_KEPT = ("role", "source_unit", "canonical_unit", "conversion")


@pytest.fixture(scope="module")
def store():
    import pg_harness
    from sqlalchemy.engine import make_url

    import demo_combined_kisiwa as kis
    from assetops_backend.sites.adapters.postgres_foundation_store import PostgresFoundationStore

    url = make_url(URL)
    assert url.database and url.database.endswith("_test"), "Refusing a database not named *_test"
    pg_harness.fresh_database()
    owned = PostgresFoundationStore(URL)
    kis.register_in(owned, IMPORT_AT, INSTALL_AT)
    yield owned
    pg_harness.dispose(owned)


def _strip(result: dict) -> tuple[dict, dict]:
    """The comparable result and the removed values."""
    doc = copy.deepcopy(result)
    removed = {
        "assumptions.model": doc["assumptions"].pop("model"),
        "assumptions.probe_local_v7": doc["assumptions"].pop("probe_local_v7"),
        "assumptions.registered_path": doc["assumptions"].pop("registered_path"),
        "gates.F6.example_fuel_level_report_text": doc["gates"]["F6"].pop("example_fuel_level_report_text"),
    }
    binding = doc["gates"]["F6"]["snapshot_fuel_level_binding"]
    removed["gates.F6.snapshot_fuel_level_binding"] = binding
    doc["gates"]["F6"]["snapshot_fuel_level_binding"] = (
        None if binding is None else {k: binding[k] for k in BINDING_KEPT})
    return doc, removed


def _differences(a, b, path="") -> list[str]:
    if isinstance(a, dict) and isinstance(b, dict):
        out = []
        for key in sorted(set(a) | set(b)):
            if key not in a or key not in b:
                out.append(f"{path}.{key}: only in {'result' if key in a else 'reference'}")
            else:
                out += _differences(a[key], b[key], f"{path}.{key}")
        return out
    if isinstance(a, list) and isinstance(b, list) and len(a) == len(b):
        return [d for i, (x, y) in enumerate(zip(a, b)) for d in _differences(x, y, f"{path}[{i}]")]
    return [] if a == b else [f"{path}: result {json.dumps(a, default=str)[:300]} reference "
                              f"{json.dumps(b, default=str)[:300]}"]


def test_f0r_reproduces_on_the_registered_site(store, monkeypatch) -> None:
    import probe_kisiwa_fuel as probe
    from kisiwa import KisiwaRegistered

    monkeypatch.setattr(probe, "Registered", lambda: KisiwaRegistered(store, SETUP_AT))
    # The committed file is the JSON text of `build()`; compare in that form.
    result = json.loads(json.dumps(probe.build(), ensure_ascii=False))
    ref = json.loads(REFERENCE.read_text(encoding="utf-8"))
    got, got_removed = _strip(result)
    want, want_removed = _strip(ref)
    for key in got_removed:
        print(f"K1 parity removed {key}\n  registered: {json.dumps(got_removed[key], default=str)}\n"
              f"  F0r:        {json.dumps(want_removed[key], default=str)}")
    differences = _differences(got, want)
    assert not differences, "\n".join(differences[:40])
