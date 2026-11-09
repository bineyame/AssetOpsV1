"""E4 D-E4.1 (C2), no database: the pre-built route list is read from the file named by `ASSETOPS_PREBUILT_ROUTES`
when that variable is set, from `config/chain/prebuilt-routes-v1.json` otherwise, and the variable never moves
`code_version` (it chooses what is warmed and never changes a body)."""
from __future__ import annotations

import json

from assetops_backend.chain import watermark
from assetops_backend.chain.adapters import file_chain_config, file_code_version
from assetops_backend.chain.composition import code_version, prebuilt_requests
from assetops_backend.chain.prebuilt import SCHEMA, PrebuiltRequest

NAME = "ASSETOPS_PREBUILT_ROUTES"
REQUESTS = [{"id": "board.day:kobo:2026-11-08", "path": "/api/sites/KOBO-001/outcome-board", "query": "date=2026-11-08"},
            {"id": "summary.week", "path": "/api/estate/outcome-summary",
             "query": "from=2026-11-01T00%3A00%3A00Z&to=2026-11-08T00%3A00%3A00Z"}]


def _write(tmp_path, requests=REQUESTS):
    path = tmp_path / "prebuilt-routes.json"
    path.write_text(json.dumps({"schema": SCHEMA, "requests": requests}), encoding="utf-8")
    return path


def test_the_named_file_is_read_when_the_variable_is_set(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv(NAME, str(_write(tmp_path)))
    assert prebuilt_requests() == tuple(PrebuiltRequest(r["id"], r["path"], r["query"]) for r in REQUESTS)


def test_a_rewritten_file_is_read_again(tmp_path, monkeypatch) -> None:
    """The demo tool rewrites the file before every prebuild; the reader is not cached on it."""
    monkeypatch.setenv(NAME, str(_write(tmp_path)))
    assert len(prebuilt_requests()) == 2
    _write(tmp_path, REQUESTS[:1])
    assert [r.id for r in prebuilt_requests()] == [REQUESTS[0]["id"]]


def test_the_config_default_is_read_without_the_variable(monkeypatch) -> None:
    monkeypatch.delenv(NAME, raising=False)
    default = json.loads((file_chain_config.REPO_ROOT / "config" / "chain" / "prebuilt-routes-v1.json")
                         .read_text(encoding="utf-8"))
    assert [r.id for r in prebuilt_requests()] == [r["id"] for r in default["requests"]]
    monkeypatch.setenv(NAME, "")  # an empty value is unset
    assert [r.id for r in prebuilt_requests()] == [r["id"] for r in default["requests"]]


def test_code_version_is_equal_with_and_without_the_variable(tmp_path, monkeypatch) -> None:
    monkeypatch.delenv(NAME, raising=False)
    file_code_version.code_version.cache_clear()
    try:
        without = code_version()
        monkeypatch.setenv(NAME, str(_write(tmp_path)))
        file_code_version.code_version.cache_clear()
        assert code_version() == without
        # control: a composer setting does move it, so the comparison can fail
        monkeypatch.setenv(watermark.COMPOSER_ENV[0], "00" * 32)
        file_code_version.code_version.cache_clear()
        assert code_version() != without
    finally:
        file_code_version.code_version.cache_clear()


def test_the_variable_is_not_a_composer_or_serve_setting() -> None:
    assert file_chain_config.PREBUILT_ROUTES_ENV == NAME
    assert NAME not in watermark.COMPOSER_ENV
    assert NAME not in watermark.SERVE_KEYS
