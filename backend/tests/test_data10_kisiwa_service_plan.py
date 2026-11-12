"""DATA-10 (D-17N.4, K14): Kisiwa's generator service plan on the story calendar. No database: the story resolution and
the `WorkService.post_plan` call are pinned with a fake service; the Postgres proof is the VPS scratch prepare named in
`.agent/DATA-17N-packet.md`."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from uuid import uuid4

import pytest

import demo_combined as dc
import demo_combined_kisiwa as kis

DB_NOW = datetime(2026, 11, 8, 10, 0, tzinfo=timezone.utc)


def _kisiwa() -> dict:
    return dc.resolve_story(DB_NOW, kisiwa=True)["kisiwa"]


def test_the_plan_is_one_250_hour_service_due_within_the_story_month() -> None:
    k = _kisiwa()
    p = k["service_plan"]
    assert (p["title"], p["trigger_kind"], p["due_hours"], p["asset_code"]) == (
        "Generator 250-hour service", "CALENDAR", None, "generator")
    written, due = kis.at(p["at"]), kis.at(p["due_at"])
    assert kis.at(k["install_at"]) < written < due  # after the Site exists, due after it is written
    S = kis.at(k["run1_start"]) + timedelta(days=9) - timedelta(hours=12)  # run 1 opens S-9d 12:00
    assert S - timedelta(days=30) <= written and due <= S + timedelta(days=30), (p, S)


def test_the_body_is_the_story_plan_shape_on_the_generator() -> None:
    k, asset = _kisiwa(), str(uuid4())
    body = kis.service_plan_body(k, asset)
    p = k["service_plan"]
    assert body["asset_id"] == asset and body["idempotency_key"] == "kisiwa-gen-250h"
    assert (body["title"], body["trigger_kind"], body["next_due_at"], body["next_due_hours"], body["occurred_at"]) == (
        p["title"], "CALENDAR", p["due_at"], None, p["at"])


class _Conn:
    def __init__(self, asset: str) -> None:
        self.asset, self.params = asset, None

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def execute(self, _sql, params):
        self.params = params
        return SimpleNamespace(scalar_one=lambda: self.asset)


def test_the_plan_is_posted_once_at_its_story_instant() -> None:
    k, asset, conn = _kisiwa(), str(uuid4()), None
    conn = _Conn(asset)
    calls: list[tuple] = []
    store = SimpleNamespace(test_db_clock_override=None)

    def post_plan(tenant, site, body, principal):
        calls.append((tenant, site, body, store.test_db_clock_override()))
        return 201, {"canonical_plan_id": "p-1", "public_code": "PM-021"}

    service = SimpleNamespace(_store=store, post_plan=post_plan)
    out = kis.write_service_plan(service, SimpleNamespace(connect=lambda: conn), "t", "s", k)
    assert conn.params == {"s": "s", "a": "generator"}
    [(tenant, site, body, recorded)] = calls
    assert (tenant, site, body["asset_id"], recorded) == ("t", "s", asset, kis.at(k["service_plan"]["at"]))
    assert out == {"id": "p-1", "code": "PM-021", "title": "Generator 250-hour service", "asset_id": asset,
                   "due_at": k["service_plan"]["due_at"]}


def test_a_refused_plan_stops_the_build() -> None:
    k = _kisiwa()
    service = SimpleNamespace(_store=SimpleNamespace(), post_plan=lambda *a: (409, {"detail": "x"}))
    with pytest.raises(SystemExit, match="PLAN_REFUSED"):
        kis.write_service_plan(service, SimpleNamespace(connect=lambda: _Conn("a")), "t", "s", k)


def test_build_writes_the_plan() -> None:
    from pathlib import Path

    source = (Path(kis.__file__)).read_text(encoding="utf-8")
    assert 'out["service_plan"] = write_service_plan(work_service, engine, tenant_id, site_id, kisiwa)' in source
