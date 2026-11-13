"""PR-3 form half (rev 5 §5.3): the price page read's `entry` block and sign-in sentence, no database.

`entry.enabled` is true only with the site-admin entry service configured (the same injected switch the entry route
uses) and no `known_at`; `entry.keys` are the stored keys of the Site type, never a future key. The fixtures are
PR-2a's (`test_pr2a_price_page.py`).
"""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.testclient import TestClient

from assetops_backend.financials.assumption_read import AssumptionReadService
from assetops_backend.financials.price_page import ENTRY_SIGN_IN_TEXT, LIVE_VIEW_LINK, SIGN_IN_TEXT, compose
from assetops_backend.outcomes.price_action import STORED_KEYS
from assetops_backend.price_page_api import build_price_page_router
from test_pr2a_price_page import DIESEL, FACTS, PAGE, Down, Rows

NOW = datetime(2026, 11, 12, 22, 30, tzinfo=timezone.utc)  # 13 Nov in Nairobi (UTC+3)
ON = lambda request, site_code: object()  # noqa: E731 - the configured entry principal
OFF = lambda request, site_code: None  # noqa: E731


def client(principal=OFF) -> TestClient:
    app = FastAPI()
    app.include_router(build_price_page_router(
        AssumptionReadService(Rows({"diesel_price_per_litre": DIESEL})), FACTS.get, (Down,),
        entry_principal=principal, clock=lambda: NOW))
    return TestClient(app)


def test_entry_off_keeps_the_administrator_sentence_and_no_form():
    body = client(OFF).get(PAGE).json()
    assert body["sign_in_text"] == SIGN_IN_TEXT
    assert body["entry"]["enabled"] is False
    assert body["entry"]["live_view"] is None
    assert body["entry"]["unit_text"] == {} and body["entry"]["currencies"] == [] and body["entry"]["today"] is None


def test_entry_on_lists_only_stored_keys_with_site_local_today():
    body = client(ON).get(PAGE).json()
    entry = body["entry"]
    assert body["sign_in_text"] == ENTRY_SIGN_IN_TEXT
    assert entry["enabled"] is True
    assert entry["keys"] == ["diesel_price_per_litre", "productive_use_price_per_kwh"]
    assert set(entry["keys"]) <= set(STORED_KEYS)
    assert [r["key"] for r in body["prices"] if not r["stored"]]  # the Site has future keys, and none is enterable
    assert not {r["key"] for r in body["prices"] if not r["stored"]} & set(entry["keys"])
    assert entry["today"] == "2026-11-13"  # Site-local, not the UTC date
    assert entry["unit_text"] == {"diesel_price_per_litre": "per litre", "productive_use_price_per_kwh": "per kWh"}
    assert "USD" in entry["currencies"] and entry["currencies"] == sorted(entry["currencies"])
    assert entry["live_view"] is None


def test_entry_is_disabled_under_known_at_with_the_live_view_words():
    body = client(ON).get(PAGE, params={"known_at": "2026-10-01T00:00:00+00:00"}).json()
    entry = body["entry"]
    assert entry["enabled"] is False
    assert entry["live_view"] == {"text": "You are viewing prices as known at 1 Oct 2026, 03:00.",
                                  "link_label": LIVE_VIEW_LINK}
    assert body["sign_in_text"] == ENTRY_SIGN_IN_TEXT


def test_cold_site_has_no_enterable_key():
    entry = compose(site_code="GH-001", site_name="GH", site_type="COLDCHAIN", timezone="UTC", series={},
                    need=None, known_at=None, access_basis="x", entry_on=True, now=NOW)["entry"]
    assert entry["enabled"] is True and entry["keys"] == []
