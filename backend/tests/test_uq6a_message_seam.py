"""UQ-6a (D-I18N.1, D-I18N.2): the server message seam.

Server words are `{key, params}` rendered for the request's locale at read; the locale is resolved from
`Accept-Language` (falling back to `en`), sent back as `Content-Language`, and is part of every stored-response key.
English only for now: no catalogue move (UQ-6b), no Babel formatting (UQ-4).
"""
from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from assetops_backend.analytics_api import build_analytics_router
from assetops_backend.chain import response_store as rs
from assetops_backend.chain.response_store import ResponseStore, StoredRoute, request_key
from assetops_backend.i18n import DEFAULT_LOCALE, LocaleMiddleware, current_locale, message, render, resolve
from assetops_backend.i18n.locale import using
from assetops_backend.i18n.messages import CATALOGUE
from assetops_backend.sites.ports import SiteNotFound

TENANT = UUID("00000000-0000-0000-0000-000000000001")
SITE = UUID("00000000-0000-0000-0000-0000000000aa")


# --- the contract and the render function -------------------------------------------------------------------

def test_a_message_is_a_key_and_typed_params() -> None:
    m = message("analytics.site_not_found", site_id="kobo-1")
    assert m == {"key": "analytics.site_not_found", "params": {"site_id": "kobo-1"}}


def test_render_fills_the_params_for_the_locale() -> None:
    assert render(message("analytics.site_not_found", site_id="kobo-1"), "en") == "No Site kobo-1 is configured."


def test_render_inserts_params_verbatim() -> None:
    """A param is never re-read as a template: braces in a value stay as they are."""
    assert render(message("analytics.site_not_found", site_id="{x}"), "en") == "No Site {x} is configured."


def test_render_of_an_unknown_locale_falls_back_to_english() -> None:
    assert render(message("analytics.site_not_found", site_id="a"), "xx") == "No Site a is configured."


def test_render_of_an_unknown_key_is_loud() -> None:
    with pytest.raises(KeyError):
        render(message("no.such.key"), "en")


def test_render_defaults_to_the_request_locale() -> None:
    with using("en"):
        assert render(message("analytics.site_not_found", site_id="b")) == "No Site b is configured."


# --- Accept-Language resolution ------------------------------------------------------------------------------

@pytest.mark.parametrize("header", [None, "", "en", "EN", "en-US", "en-GB,en;q=0.9", "en-US,en;q=0.9,fr;q=0.8",
                                    "sw", "fr-FR", "*", "xx;q=0.5", "fr;q=0, en;q=0.1", "garbage;;q=x"])
def test_accept_language_resolves_to_a_supported_locale_else_english(header) -> None:
    assert resolve(header) == "en" == DEFAULT_LOCALE


def test_resolution_is_by_quality_and_skips_unsupported(monkeypatch) -> None:
    from assetops_backend.i18n import locale as loc

    monkeypatch.setattr(loc, "SUPPORTED", ("en", "sw"))
    assert resolve("sw-TZ,en;q=0.5") == "sw"
    assert resolve("en;q=0.4,sw;q=0.9") == "sw"
    assert resolve("fr,sw;q=0.2") == "sw"
    assert resolve("sw;q=0,fr") == "en"


def _probe_app() -> FastAPI:
    app = FastAPI()
    app.add_middleware(LocaleMiddleware)

    @app.get("/probe")
    def probe() -> dict[str, str]:
        return {"locale": current_locale(), "stored": StoredRoute("/r", TENANT, {}).locale}

    @app.get("/probe-async")
    async def probe_async() -> dict[str, str]:
        return {"locale": current_locale()}

    return app


@pytest.mark.parametrize("headers", [{}, {"Accept-Language": "en"}, {"Accept-Language": "en-US,en;q=0.9"},
                                     {"Accept-Language": "sw"}])
def test_every_response_carries_content_language(headers) -> None:
    client = TestClient(_probe_app())
    for path in ("/probe", "/probe-async"):
        response = client.get(path, headers=headers)
        assert response.status_code == 200
        assert response.headers["content-language"] == "en"
        assert response.json()["locale"] == "en"


def test_a_stored_route_takes_the_request_locale(monkeypatch) -> None:
    from assetops_backend.i18n import locale as loc

    monkeypatch.setattr(loc, "SUPPORTED", ("en", "sw"))
    client = TestClient(_probe_app())
    swahili = client.get("/probe", headers={"Accept-Language": "sw"})
    assert swahili.json() == {"locale": "sw", "stored": "sw"}
    assert swahili.headers["content-language"] == "sw"
    assert client.get("/probe").json() == {"locale": "en", "stored": "en"}
    assert current_locale() == "en"  # nothing leaks out of a request


def test_outside_a_request_the_locale_is_english() -> None:
    """The pre-build and the tick compose outside any request: English (D-I18N.2: the pre-load list builds English)."""
    assert current_locale() == "en"
    assert StoredRoute("/r", TENANT, {}).locale == "en"


# --- the locale in the response-store key -------------------------------------------------------------------

def test_the_store_key_differs_by_locale() -> None:
    en = request_key("/r", TENANT, [SITE], {"a": 1}, "en")
    assert en != request_key("/r", TENANT, [SITE], {"a": 1}, "sw")
    assert en == request_key("/r", TENANT, [SITE], {"a": 1})  # the default is English
    assert '"locale":"en"' in en


class _Rows:
    """An in-memory `chain_response` port: one quiet watermark, one Site."""

    def __init__(self) -> None:
        self.rows: dict[tuple[str, str], tuple[bytes, str]] = {}
        self.lookups: list[str] = []

    def read(self, work):
        return work(self)

    def watermark(self, tenant_id, sites):
        return "w1"

    def sites(self, tenant_id):
        return [(str(SITE), "kobo", "UTC")]

    def lookup(self, route, key, w, version, now):
        self.lookups.append(key)
        return self.rows.get((route, key))

    def insert(self, tenant_id, w, version, build_ms, until, rows, now):
        for route, key, tag, body in rows:
            self.rows[(route, key)] = (body, tag)
        return {route for route, *_ in rows}

    def dispose(self) -> None:
        pass


def _store_app(rows: _Rows, composed: list[int]) -> FastAPI:
    app = FastAPI()
    app.add_middleware(LocaleMiddleware)
    store = ResponseStore(rows, lambda: "v1")

    @app.get("/api/stored")
    def stored():
        def compose():
            composed.append(1)
            return {"/api/stored": {"n": len(composed)}}

        return store.serve(StoredRoute("/api/stored", TENANT, {"q": 1}), compose)

    return app


def test_a_request_with_no_or_english_accept_language_hits_the_prebuilt_row(monkeypatch) -> None:
    """The demo pre-build (`chain/prebuild.py`, an in-process client sending no `Accept-Language`) stores the row a
    browser's English request then hits: same key, no second compose."""
    monkeypatch.setattr(rs.read_scope, "clock", lambda: datetime(2026, 11, 11, 12, tzinfo=timezone.utc))
    rows, composed = _Rows(), []
    client = TestClient(_store_app(rows, composed))
    first = client.get("/api/stored")  # as the pre-build sends it
    assert first.headers[rs.HEADER] == "stored"
    for header in ("en", "en-US,en;q=0.9", "en-GB", "sw", "*"):
        again = client.get("/api/stored", headers={"Accept-Language": header})
        assert again.headers[rs.HEADER] == "hit", header
        assert again.content == first.content
        assert again.headers["content-language"] == "en"
    assert len(composed) == 1
    assert len(set(rows.lookups)) == 1
    assert '"locale":"en"' in rows.lookups[0]


def test_a_second_locale_is_stored_under_its_own_key(monkeypatch) -> None:
    from assetops_backend.i18n import locale as loc

    monkeypatch.setattr(loc, "SUPPORTED", ("en", "sw"))
    monkeypatch.setattr(rs.read_scope, "clock", lambda: datetime(2026, 11, 11, 12, tzinfo=timezone.utc))
    rows, composed = _Rows(), []
    client = TestClient(_store_app(rows, composed))
    assert client.get("/api/stored").headers[rs.HEADER] == "stored"
    assert client.get("/api/stored", headers={"Accept-Language": "sw"}).headers[rs.HEADER] == "stored"
    assert client.get("/api/stored", headers={"Accept-Language": "sw"}).headers[rs.HEADER] == "hit"
    assert len(composed) == 2 and len(rows.rows) == 2


def test_the_product_app_resolves_the_locale() -> None:
    from assetops_backend.main import app

    response = TestClient(app).get("/api/health", headers={"Accept-Language": "fr-FR,fr;q=0.9"})
    assert response.status_code == 200
    assert response.headers["content-language"] == "en"


# --- the reference user: the analytics Site-not-found body ---------------------------------------------------

class _NoSites:
    def get_site(self, site_id):
        raise SiteNotFound(site_id)


def test_the_converted_body_is_byte_equal_in_english_to_today() -> None:
    app = FastAPI()
    app.add_middleware(LocaleMiddleware)
    app.include_router(build_analytics_router(None, None, _NoSites()))
    client = TestClient(app)
    for headers in ({}, {"Accept-Language": "en-US,en;q=0.9"}, {"Accept-Language": "sw"}):
        response = client.get("/api/sites/kobo-1/analytics", headers=headers)
        assert response.status_code == 404
        # the bytes the f-string body served before UQ-6a
        assert response.content == b'{"detail":{"code":"SITE_NOT_FOUND","message":"No Site kobo-1 is configured."}}'
        assert response.headers["content-language"] == "en"
    assert CATALOGUE["en"]["analytics.site_not_found"] == "No Site {site_id} is configured."
