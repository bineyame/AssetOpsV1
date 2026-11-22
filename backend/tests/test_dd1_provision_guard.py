"""DD1.2 (D-DD.35): `provision_gateway` compares the served tenant, not the constant `demo`. No database."""
from __future__ import annotations

import pytest

from assetops_backend.evidence import provision_gateway as pg


class _Store:
    def __init__(self):
        self.calls = []

    def __getattr__(self, name):
        def call(*a, **k):
            self.calls.append(name)
        return call


def _run(tenant, store=None):
    store = store or _Store()
    code = pg.main(["enable-gateway", "--tenant", tenant, "--site", "S-1", "--gateway", "edge-s-1"], store=store)
    return code, store


def test_unset_and_demo_runs(monkeypatch) -> None:
    monkeypatch.delenv("ASSETOPS_TENANT_SLUG", raising=False)
    code, store = _run("demo")
    assert code == 0 and store.calls


def test_unset_and_other_tenant_refused(monkeypatch, capsys) -> None:
    monkeypatch.delenv("ASSETOPS_TENANT_SLUG", raising=False)
    code, store = _run("lakeside-power")
    assert code == 2 and not store.calls
    assert 'is not the tenant this environment serves (ASSETOPS_TENANT_SLUG; unset means "demo").' in capsys.readouterr().err


def test_set_and_same_tenant_runs(monkeypatch) -> None:
    monkeypatch.setenv("ASSETOPS_TENANT_SLUG", "lakeside-power")
    code, store = _run("lakeside-power")
    assert code == 0 and store.calls


def test_set_and_demo_flag_refused(monkeypatch) -> None:
    monkeypatch.setenv("ASSETOPS_TENANT_SLUG", "lakeside-power")
    code, store = _run("demo")
    assert code == 2 and not store.calls


def test_invalid_served_slug_exits_2_and_builds_no_store(monkeypatch, capsys) -> None:
    monkeypatch.setenv("ASSETOPS_TENANT_SLUG", "Not A Slug")
    monkeypatch.setattr(pg, "build_gateway_access", lambda url: pytest.fail("a store was built"))
    code = pg.main(["enable-gateway", "--tenant", "demo", "--site", "S-1", "--gateway", "g"])
    assert code == 2 and "ASSETOPS_TENANT_SLUG" in capsys.readouterr().err
