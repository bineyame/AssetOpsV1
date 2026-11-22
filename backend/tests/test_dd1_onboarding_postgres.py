"""DD1.2 (spec §7 DD1.2; D-DD.35, D-DD.36): `onboard_operator apply --bindings DIR` into a routed `*_test` database.

After an emulated apply each Site has its gateway and sources enabled and one published binding set; a second apply
changes nothing. Needs `ASSETOPS_TEST_DATABASE_URL`; run through `tools/heavy-slot.sh --db`. One operator per database.
"""
from __future__ import annotations

import json
import os
import shutil
from pathlib import Path

import pytest

URL = os.environ.get("ASSETOPS_TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

if URL:
    from sqlalchemy import text
    from test_s1_bindings_postgres import engine, store  # noqa: F401

    from assetops_backend import onboard_operator as command
    from assetops_backend.database_target import PG_TARGET_ENV

BACKEND = Path(__file__).resolve().parent.parent
ON1 = BACKEND / "tests" / "fixtures" / "on1"
WORLD = BACKEND / "conversions" / "world"
COUNTED = ("gateway_access_event", "signal_binding_set", "signal_binding_set_revision", "signal_binding_revision")


def _env(monkeypatch, tmp_path, slug):
    keys = tmp_path / "keys"
    keys.mkdir(mode=0o700, exist_ok=True)
    os.chmod(keys, 0o700)
    for variable in PG_TARGET_ENV:
        monkeypatch.delenv(variable, raising=False)
    monkeypatch.delenv("ASSETOPS_REAL_OPERATOR_DATA", raising=False)
    monkeypatch.setenv("DATABASE_URL", URL)
    monkeypatch.setenv("ASSETOPS_TENANT_SLUG", slug)
    monkeypatch.setenv("ASSETOPS_PSEUDONYM_KEY_DIR", str(keys))


def _apply(path, bindings=WORLD):
    digest = command.main(["digest", "--file", str(path)])  # prints; the value is read back below
    return digest


def _run(capsys, path, extra=()):
    command.main(["digest", "--file", str(path)])
    digest = capsys.readouterr().out.strip()
    code = command.main(["apply", "--file", str(path), "--confirmed-digest", digest, *extra])
    out, err = capsys.readouterr()
    return code, out, err


def _counts(engine):
    with engine.connect() as c:
        out = {}
        for table in COUNTED:
            try:
                out[table] = c.execute(text(f"SELECT count(*) FROM {table}")).scalar()
            except Exception:  # noqa: BLE001 - a table this schema names differently is not counted
                c.rollback()
        return out


@pytest.mark.parametrize("slug, sites", [("harvest-cold", 3), ("metro-bus", 3)])
def test_emulated_apply_enables_and_binds_each_site_and_a_second_changes_nothing(
        store, engine, tmp_path, monkeypatch, capsys, slug, sites) -> None:  # noqa: F811
    _env(monkeypatch, tmp_path, slug)
    path = ON1 / f"{slug}.onboarding.json"
    code, _, err = _run(capsys, path, ("--bindings", str(WORLD)))
    assert code == 0, err
    with engine.connect() as c:
        gateways = c.execute(text("SELECT g.gateway_external_id, g.disabled_at FROM gateway g")).all()
        disabled_sources = c.execute(text("SELECT count(*) FROM source WHERE disabled_at IS NOT NULL")).scalar()
        total_sources = c.execute(text("SELECT count(*) FROM source")).scalar()
        sets = c.execute(text("SELECT count(DISTINCT binding_set_id) FROM signal_binding_set_revision")).scalar()
    assert len(gateways) == sites and all(d is None for _, d in gateways)
    assert {g for g, _ in gateways} == {f"edge-{s['code'].lower()}" for s in json.loads(path.read_bytes())["sites"]}
    assert total_sources and disabled_sources == 0 and sets == sites
    before = _counts(engine)
    code, _, err = _run(capsys, path, ("--bindings", str(WORLD)))
    assert code == 0, err
    assert _counts(engine) == before


def test_a_site_without_its_conversion_refuses_before_any_write(store, engine, tmp_path, monkeypatch, capsys) -> None:  # noqa: F811
    _env(monkeypatch, tmp_path, "metro-bus")
    empty = tmp_path / "none"
    empty.mkdir()
    code, _, err = _run(capsys, ON1 / "metro-bus.onboarding.json", ("--bindings", str(empty)))
    assert code == 2 and err.startswith("ONBOARD_SITE_INVALID bindings/EV-EMB")
    with engine.connect() as c:
        assert c.execute(text("SELECT count(*) FROM tenant")).scalar() == 0


def _world_with(tmp_path, code, edit):
    """A copy of the world conversions with one Site's file edited by `edit(document)`."""
    out = tmp_path / "world"
    shutil.copytree(WORLD, out)
    path = out / f"{code}-bindings.json"
    document = json.loads(path.read_text(encoding="utf-8"))
    edit(document)
    path.write_text(json.dumps(document, indent=2), encoding="utf-8")
    return out


LAKESIDE = ON1 / "lakeside-power.onboarding.json"


def test_lakeside_publishes_under_roles_5_one_set_per_site_and_a_second_apply_is_a_no_op(
        store, engine, tmp_path, monkeypatch, capsys) -> None:  # noqa: F811
    """D-DD.41: Kisiwa (2 GENERATOR) and Mto (2 INVERTER) publish under minigrid-roles-5, each unit bound on its own."""
    _env(monkeypatch, tmp_path, "lakeside-power")
    code, _, err = _run(capsys, LAKESIDE, ("--bindings", str(WORLD)))
    assert code == 0, err
    with engine.connect() as c:
        sets = c.execute(text("SELECT count(DISTINCT binding_set_id) FROM signal_binding_set_revision")).scalar()
        roles = dict(c.execute(text(
            "SELECT s.site_code, r.role_set FROM signal_binding_set_revision r "
            "JOIN site s ON s.id = r.site_id")).all())
        per_unit = c.execute(text(
            "SELECT count(DISTINCT b.asset_id) FROM signal_binding_revision b WHERE b.role = 'generator_power'")).scalar()
    assert sets == 3 and roles["KISIWA-001"] == roles["MTO-001"] == "minigrid-roles-5"
    assert per_unit == 4  # gen-ks-01, gen-ks-02, Kobo's and Mto's one generator
    before = _counts(engine)
    code, _, err = _run(capsys, LAKESIDE, ("--bindings", str(WORLD)))
    assert code == 0, err
    assert _counts(engine) == before


def test_roles_4_on_the_same_foundation_still_refuses_two_generators(store, engine, tmp_path, monkeypatch, capsys) -> None:  # noqa: F811
    _env(monkeypatch, tmp_path, "lakeside-power")
    world = _world_with(tmp_path, "KISIWA-001", lambda d: d.update(role_set="minigrid-roles-4"))
    code, _, err = _run(capsys, LAKESIDE, ("--bindings", str(world)))
    assert code == 3 and "BINDING_ROLE_AMBIGUOUS" in err and "KISIWA-001" in err


def test_two_bindings_of_one_unit_role_on_one_unit_refuse_as_a_conflict(store, engine, tmp_path, monkeypatch, capsys) -> None:  # noqa: F811
    _env(monkeypatch, tmp_path, "lakeside-power")

    def twice(document):
        row = next(b for b in document["bindings"] if b["role"] == "generator_power" and b["asset_code"] == "gen-ks-01")
        document["declare_signals"] = [{"device_id": row["device_id"], "signal_id": "ac-power-2",
                                        "display_name": "Second power channel", "unit": "kW", "reason": "test"}]
        document["bindings"].append({**row, "legacy_mapping_id": None, "signal_id": "ac-power-2"})

    world = _world_with(tmp_path, "KISIWA-001", twice)
    code, _, err = _run(capsys, LAKESIDE, ("--bindings", str(world)))
    assert code == 3 and "BINDING_ROLE_CONFLICT" in err, err


def test_an_unbound_unit_is_named_in_readiness(store, engine, tmp_path, monkeypatch, capsys) -> None:  # noqa: F811
    from assetops_backend.sites.binding_service import readiness
    from datetime import datetime, timezone

    from test_s1_bindings_postgres import Clock

    from assetops_backend.sites.foundation_service import FoundationService

    _env(monkeypatch, tmp_path, "lakeside-power")
    world = _world_with(tmp_path, "KISIWA-001", lambda d: d.update(
        bindings=[b for b in d["bindings"] if b["asset_code"] != "gen-ks-02"]))
    code, _, err = _run(capsys, LAKESIDE, ("--bindings", str(world)))
    assert code == 0, err
    tenant = store.resolve_tenant("lakeside-power")
    site = store.find_site(tenant.id, "KISIWA-001")
    seen = FoundationService(store, "demo", Clock(datetime.now(timezone.utc))).read(site, tenant, None, None)
    missing = readiness(seen.site, seen.revision, seen.registrations, seen.binding_set)["missing_roles"]
    assert any(m.startswith("Generator power - ") and "Generator 02" in m for m in missing), missing
    assert not any("Generator 01" in m for m in missing)


def test_a_malformed_conversion_file_refuses_before_any_write(store, engine, tmp_path, monkeypatch, capsys) -> None:  # noqa: F811
    """D-DD.47: every input is parsed before the first write; a malformed file is the same refusal as a missing one."""
    _env(monkeypatch, tmp_path, "lakeside-power")
    world = tmp_path / "world"
    shutil.copytree(WORLD, world)
    (world / "KISIWA-001-bindings.json").write_text("{not json", encoding="utf-8")
    code, _, err = _run(capsys, LAKESIDE, ("--bindings", str(world)))
    assert code == 2 and err.startswith("ONBOARD_SITE_INVALID bindings/KISIWA-001"), err
    with engine.connect() as c:
        assert c.execute(text("SELECT count(*) FROM tenant")).scalar() == 0
        assert c.execute(text("SELECT count(*) FROM site")).scalar() == 0
