"""OWN-G3a (R2-G3a 6): `ASSETOPS_OPERATIONAL_ENTRY` is read by `host/lab_app.py`; `on` switches the entry route
on, unset or empty leaves it off, any other value refuses startup. Imported with the variable unset, so the
module-level `app` builds with the route off."""

from __future__ import annotations

import dataclasses
import os

import pytest

os.environ.pop("ASSETOPS_OPERATIONAL_ENTRY", None)

import lab_app  # noqa: E402
from assetops_backend.config import ConfigurationError  # noqa: E402


def test_on_injects_the_entry_service(monkeypatch) -> None:
    monkeypatch.setenv(lab_app.OPERATIONAL_ENTRY_ENV, "on")
    principal = lab_app.operational_entry_from_environment()
    assert principal is not None and principal(None, "KISIWA-001") == "service:operator-entry"


@pytest.mark.parametrize("value", [None, ""])
def test_unset_or_empty_leaves_the_route_off(monkeypatch, value) -> None:
    if value is None:
        monkeypatch.delenv(lab_app.OPERATIONAL_ENTRY_ENV, raising=False)
    else:
        monkeypatch.setenv(lab_app.OPERATIONAL_ENTRY_ENV, value)
    assert lab_app.operational_entry_from_environment() is None


@pytest.mark.parametrize("value", ["yes", "ON", "on "])
def test_any_other_value_refuses_startup(monkeypatch, value) -> None:
    monkeypatch.setenv(lab_app.OPERATIONAL_ENTRY_ENV, value)
    with pytest.raises(ConfigurationError, match="ASSETOPS_OPERATIONAL_ENTRY must be 'on' or unset"):
        lab_app.operational_entry_from_environment()
    with pytest.raises(ConfigurationError):
        lab_app.build_app()  # refused before anything is composed


def test_build_app_passes_the_principal_and_an_explicit_override_wins(monkeypatch) -> None:
    seen: list[object] = []
    monkeypatch.setattr(lab_app, "create_app", lambda flags, execution=None, **o: seen.append(o) or object())
    flags = dataclasses.replace(lab_app.load_feature_flags(), simulator_lab_enabled=False)
    monkeypatch.setenv(lab_app.OPERATIONAL_ENTRY_ENV, "on")
    lab_app.build_app(flags)
    assert seen[-1]["operational_entry_principal"] is lab_app.operational_entry_principal
    mine = lambda r, c: "service:test"  # noqa: E731
    lab_app.build_app(flags, operational_entry_principal=mine)
    assert seen[-1]["operational_entry_principal"] is mine
    monkeypatch.delenv(lab_app.OPERATIONAL_ENTRY_ENV)
    lab_app.build_app(flags)
    assert "operational_entry_principal" not in seen[-1]
