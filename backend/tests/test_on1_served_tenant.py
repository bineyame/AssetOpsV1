"""ON1 (spec §3.4, §6 "Settings, demo and runbook, no database"; D-ON1.5, D-ON1.11, D-ON1.12, D-ON1.13): the served
tenant, the demo pin and the runbook.

No database: the autouse no-connect fixture makes every connection attempt raise, and every URL naming a database uses
host `rc4.invalid` port 1.
"""
from __future__ import annotations

import psycopg
import pytest
import sqlalchemy.engine
from sqlalchemy import create_engine

from assetops_backend.config import ConfigurationError, served_tenant_slug
from assetops_backend.database_target import PG_TARGET_ENV
from foundation_fakes import InMemoryFoundationStore

SETTINGS = ("DATABASE_URL", "ASSETOPS_REAL_OPERATOR_DATA", "ASSETOPS_TENANT_SLUG", "ASSETOPS_PSEUDONYM_KEY_DIR")


def _no_connect(*_a, **_k):
    raise AssertionError("connection attempted")


@pytest.fixture(autouse=True)
def no_connect(monkeypatch):
    monkeypatch.setattr(psycopg, "connect", _no_connect)
    monkeypatch.setattr(psycopg.Connection, "connect", classmethod(_no_connect))
    monkeypatch.setattr(sqlalchemy.engine.Engine, "connect", _no_connect)
    for variable in PG_TARGET_ENV + SETTINGS:
        monkeypatch.delenv(variable, raising=False)


def test_no_connect_fixture_holds() -> None:
    with pytest.raises(AssertionError, match="^connection attempted$"):
        create_engine("postgresql+psycopg://u:p@rc4.invalid:1/x").connect()


# --- 1: the setting --------------------------------------------------------------------------------------------------

def test_1_served_tenant_slug(monkeypatch) -> None:
    assert served_tenant_slug() == "demo"
    monkeypatch.setenv("ASSETOPS_TENANT_SLUG", "lakeside-power")
    assert served_tenant_slug() == "lakeside-power"
    for bad in ("", "Lakeside", "a b"):
        monkeypatch.setenv("ASSETOPS_TENANT_SLUG", bad)
        with pytest.raises(ConfigurationError, match="^ASSETOPS_TENANT_SLUG must be a tenant slug.$"):
            served_tenant_slug()


# --- 2: the app ------------------------------------------------------------------------------------------------------

def test_2_an_operator_database_never_serves_the_demo_tenant(monkeypatch) -> None:
    from assetops_backend.main import create_app

    monkeypatch.setenv("ASSETOPS_REAL_OPERATOR_DATA", "on")
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://u:p@rc4.invalid:1/assetops_op_pilot1")
    with pytest.raises(ConfigurationError, match="^An operator database serves its operator's tenant"):
        create_app()


def test_2_the_app_serves_the_named_tenant(monkeypatch) -> None:
    from assetops_backend.main import create_app

    monkeypatch.setenv("ASSETOPS_TENANT_SLUG", "lakeside-power")
    app = create_app(foundation_store=InMemoryFoundationStore())
    assert app.state.site_registry.served_tenant_slug == "lakeside-power"
    assert app.state.site_registry.service.tenant_slug == "lakeside-power"
