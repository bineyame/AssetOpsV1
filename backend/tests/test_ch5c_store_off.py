"""CH-5c2 (L0, no database): the stored route responses are ON by default (CH5c-R7, turned on by CH-5c2).

With `ASSETOPS_RESPONSE_STORE` unset the store is built; an explicit opt-out composes outside it and a pre-build
reports `SKIPPED_STORE_OFF`; `compose` builds a compose-only store (the W6 probe). The `demo_combined` serve
environment passes the owner's choice through. M3: the tree has exactly one alembic head. (The test suite itself
runs with the store off, `conftest.py`, unless a test opts in.)
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools"))

from assetops_backend.chain import prebuild  # noqa: E402
from assetops_backend.chain.adapters import file_code_version  # noqa: E402
from assetops_backend.chain.composition import build_response_store  # noqa: E402
from assetops_backend.chain.response_store import ResponseStore, enabled, mode  # noqa: E402


class Untouchable:
    """An engine that fails on any use: proves the default-off path never reads or writes the store."""

    def __getattr__(self, name):
        raise AssertionError(f"store touched: {name}")


def test_default_is_on(monkeypatch) -> None:
    monkeypatch.delenv("ASSETOPS_RESPONSE_STORE", raising=False)
    assert enabled() is True and mode() == "on"
    store = build_response_store("postgresql://x", engine=Untouchable())
    assert isinstance(store, ResponseStore) and not store.compose_only


@pytest.mark.parametrize("value", ["off", "0", "false", "NO"])
def test_an_explicit_opt_out_is_off(monkeypatch, value) -> None:
    monkeypatch.setenv("ASSETOPS_RESPONSE_STORE", value)
    assert enabled() is False
    assert build_response_store("postgresql://x", engine=Untouchable()) is None


@pytest.mark.parametrize("value", ["on", "1", "TRUE", "yes", "", "maybe"])
def test_anything_but_an_opt_out_builds_the_store(monkeypatch, value) -> None:
    monkeypatch.setenv("ASSETOPS_RESPONSE_STORE", value)
    assert enabled() is True
    assert isinstance(build_response_store(None, engine=Untouchable()), ResponseStore)


def test_compose_mode_builds_a_compose_only_store(monkeypatch) -> None:
    monkeypatch.setenv("ASSETOPS_RESPONSE_STORE", "compose")
    store = build_response_store(None, engine=Untouchable())
    assert store.compose_only


def test_default_off_body_equals_a_store_less_compose(monkeypatch) -> None:
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    from assetops_backend.estate_api import build_estate_router

    monkeypatch.setenv("ASSETOPS_RESPONSE_STORE", "off")
    calls: list[int] = []

    class Composer:
        def findings(self, tenant, parsed, admit):
            calls.append(1)
            return {"rows": [], "total_count": None, "lens": parsed.lens, "limit": parsed.limit,
                    "known_at": "2026-11-01T00:00:00+00:00", "selection_token": "t"}

    def get(responses):
        app = FastAPI()
        app.include_router(build_estate_router(Composer(), lambda: "tenant", access=lambda r, c: None,
                                               responses=responses))
        q = "/api/estate/findings?from=2026-10-25T00:00:00Z&to=2026-11-01T00:00:00Z"
        return TestClient(app).get(q).content

    defaulted = build_response_store("postgresql://x", engine=Untouchable())  # off: None, never touches the engine
    assert get(defaulted) == get(None)
    assert len(calls) == 2  # each request composed


@pytest.mark.parametrize("value", ["off", "compose"])
def test_a_prebuild_with_the_store_off_stores_nothing(monkeypatch, value) -> None:
    monkeypatch.setenv("ASSETOPS_RESPONSE_STORE", value)

    class Never:
        def get(self, path):
            raise AssertionError(path)

    result = prebuild.run("postgresql://x", Never())
    assert result["code"] == "SKIPPED_STORE_OFF" and result["requests"] == 0 and len(result["code_version"]) == 16


def test_the_demo_combined_serve_env_passes_the_store_choice_through(tmp_path, monkeypatch) -> None:
    import demo_combined as tool

    monkeypatch.delenv("ASSETOPS_RESPONSE_STORE", raising=False)
    demo = tool.Demo("assetops_demo3_storeoff_test", "var/demo3_storeoff")
    demo.work, demo.tree = tmp_path, tmp_path / "tree"
    (tmp_path / "keys.json").write_text("{}", encoding="utf-8")
    env = demo.serve_env()
    assert env.get("ASSETOPS_RESPONSE_STORE") is None
    monkeypatch.setenv("ASSETOPS_RESPONSE_STORE", "off")
    assert demo.serve_env()["ASSETOPS_RESPONSE_STORE"] == "off"  # the demo passes the owner's choice through, no more


def test_exactly_one_alembic_head() -> None:
    head = file_code_version.alembic_head()
    assert head and "," not in head, f"alembic heads: {head!r}"
