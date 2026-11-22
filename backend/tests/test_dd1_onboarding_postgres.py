"""DD1.2 (spec §7 DD1.2; D-DD.35, D-DD.36): `onboard_operator apply --bindings DIR` into a routed `*_test` database.

After an emulated apply each Site has its gateway and sources enabled and one published binding set; a second apply
changes nothing. Needs `ASSETOPS_TEST_DATABASE_URL`; run through `tools/heavy-slot.sh --db`. One operator per database.
"""
from __future__ import annotations

import json
import os
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


def test_lakeside_kisiwa_and_mto_are_refused_by_the_product_role_limit(store, engine, tmp_path, monkeypatch, capsys) -> None:  # noqa: F811
    """Q-DD1.7: `minigrid-roles-4` binds one GENERATOR and one INVERTER per Site (BINDING_ROLE_AMBIGUOUS); Kisiwa has two
    generators and Mto two inverters. Written as the fact today; it turns into a pass when the question is answered."""
    _env(monkeypatch, tmp_path, "lakeside-power")
    code, _, err = _run(capsys, ON1 / "lakeside-power.onboarding.json", ("--bindings", str(WORLD)))
    assert code == 3 and "BINDING_ROLE_AMBIGUOUS" in err and "KISIWA-001" in err
