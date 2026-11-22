"""DD1 fix round (D-DD.45): readiness for cold and EV Sites equals main's, byte for byte.

Goldens in `fixtures/dd1_readiness_parity/` were captured from main `05be2b968` (see its README). The same helper
writes them when `DD1_PARITY_CAPTURE_DIR` is set; it uses no DD1 code, so it runs on main unchanged.
"""

from __future__ import annotations

import json
import os
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

URL = os.environ.get("ASSETOPS_TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

if URL:
    from test_s1_bindings_postgres import Clock, engine, store  # noqa: F401

    from assetops_backend import onboard_operator as command
    from assetops_backend.database_target import PG_TARGET_ENV
    from assetops_backend.sites.binding_conversion import convert
    from assetops_backend.sites.binding_service import BindingService, readiness
    from assetops_backend.sites.cold_lab import install_cold_lab
    from assetops_backend.sites.ev_lab import install_ev_lab
    from assetops_backend.sites.foundation_service import FoundationService, utc_now

BACKEND = Path(__file__).resolve().parent.parent
GOLDEN = BACKEND / "tests" / "fixtures" / "dd1_readiness_parity"
HARVEST = BACKEND / "tests" / "fixtures" / "on1" / "harvest-cold.onboarding.json"
WORLD = BACKEND / "conversions" / "world"
NOW = datetime(2026, 10, 17, 12, 0, tzinfo=timezone.utc)
UUID = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}")


def _normal(document) -> str:
    text = json.dumps(document, sort_keys=True, indent=1, default=str)
    seen: dict[str, str] = {}
    return UUID.sub(lambda m: seen.setdefault(m.group(0), f"uuid-{len(seen) + 1}"), text) + "\n"


def _readiness(store, tenant_slug, code) -> str:
    tenant = store.resolve_tenant(tenant_slug)
    site = store.find_site(tenant.id, code)
    seen = FoundationService(store, "demo", Clock(datetime.now(timezone.utc))).read(site, tenant, None, None)
    return _normal(readiness(seen.site, seen.revision, seen.registrations, seen.binding_set))


def _cold_lab(store) -> str:
    install_cold_lab(store, tenant_slug="demo", clock=Clock(NOW - timedelta(hours=3)))
    return _readiness(store, "demo", "COLD-LAB-001")


def _ev(store) -> str:
    install_ev_lab(store, tenant_slug="demo", clock=Clock(NOW - timedelta(hours=3)))
    return _readiness(store, "demo", "EV-LAB-001")


def _kiri(store, monkeypatch, tmp_path) -> str:
    keys = tmp_path / "keys"
    keys.mkdir(mode=0o700, exist_ok=True)
    os.chmod(keys, 0o700)
    for variable in PG_TARGET_ENV:
        monkeypatch.delenv(variable, raising=False)
    monkeypatch.delenv("ASSETOPS_REAL_OPERATOR_DATA", raising=False)
    monkeypatch.setenv("DATABASE_URL", URL)
    monkeypatch.setenv("ASSETOPS_TENANT_SLUG", "harvest-cold")
    monkeypatch.setenv("ASSETOPS_PSEUDONYM_KEY_DIR", str(keys))
    from io import StringIO
    import contextlib
    with contextlib.redirect_stdout(StringIO()) as out:
        command.main(["digest", "--file", str(HARVEST)])
    digest = out.getvalue().strip()
    assert command.main(["apply", "--file", str(HARVEST), "--confirmed-digest", digest]) == 0
    tenant = store.resolve_tenant("harvest-cold")
    site = store.find_site(tenant.id, "COLD-KIRI")
    fixture = json.loads((WORLD / "COLD-KIRI-bindings.json").read_text(encoding="utf-8"))
    convert(store, BindingService(store, utc_now), tenant, site, fixture)
    return _readiness(store, "harvest-cold", "COLD-KIRI")


def _check(name: str, actual: str) -> None:
    capture = os.environ.get("DD1_PARITY_CAPTURE_DIR")
    if capture:
        Path(capture, f"{name}.json").write_text(actual, encoding="utf-8")
        return
    assert actual == (GOLDEN / f"{name}.json").read_text(encoding="utf-8")


def test_cold_lab_readiness_equals_main(store) -> None:
    _check("cold-lab-001", _cold_lab(store))


def test_cold_kiri_readiness_equals_main(store, monkeypatch, tmp_path) -> None:
    _check("cold-kiri", _kiri(store, monkeypatch, tmp_path))


def test_ev_readiness_equals_main(store) -> None:
    _check("ev-lab-001", _ev(store))


def test_cold_goldens_name_no_unbound_channel_role() -> None:
    """Main's cold readiness is INCOMPLETE for policy controls, never for a probe channel (the H1 statement)."""
    for name in ("cold-lab-001", "cold-kiri"):
        document = json.loads((GOLDEN / f"{name}.json").read_text(encoding="utf-8"))
        assert document["missing_roles"] == ["Temperature policy low", "Temperature policy high"], name


def test_every_component_implies_per_asset_and_is_exactly_the_seven() -> None:
    from assetops_backend.sites.binding_roles import PER_ASSET, ROLES_BY_SET

    flagged = {name: {r.role for r in roles if r.every_component} for name, roles in ROLES_BY_SET.items()}
    for roles in ROLES_BY_SET.values():
        assert all(r.cardinality == PER_ASSET for r in roles if r.every_component)
    units = {"generator_state", "generator_power", "mini_backup_start_event", "pv_power", "pv_available_power"}
    feeders = {"feeder_demand", "feeder_requested_power"}
    for name, got in flagged.items():
        expected = {r.role for r in ROLES_BY_SET[name] if r.role in feeders}
        assert got == expected | (units if name == "minigrid-roles-5" else set()), name
    assert set().union(*flagged.values()) == feeders | units


@pytest.mark.skipif(bool(os.environ.get("DD1_PARITY_CAPTURE_DIR")), reason="capture mode")
def test_plant_every_component_on_chamber_temperature_fails_the_cold_parity(store, monkeypatch) -> None:
    from dataclasses import replace

    from assetops_backend.sites import binding_roles as roles

    planted = tuple(replace(r, every_component=True) if r.role == "chamber_temperature" else r
                    for r in roles.COLD_ROLES_1)
    monkeypatch.setitem(roles.ROLES_BY_SET, roles.ROLE_SET_COLD_1, planted)
    assert _cold_lab(store) != (GOLDEN / "cold-lab-001.json").read_text(encoding="utf-8")
