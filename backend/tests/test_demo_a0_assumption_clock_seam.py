"""DEMO-A0: the assumption store's test-only recorded clock seam (mirrors `test_decision_clock_override`).

Source check: no product module passes the keyword. Postgres (needs ASSETOPS_TEST_DATABASE_URL): with the override
at X the publication is recorded at X, invisible at X - 1 s and selected at X; without it the server clock rules.
"""

from __future__ import annotations

import ast
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

URL = os.environ.get("ASSETOPS_TEST_DATABASE_URL")
KW = "test_recorded_clock_override"
PKG = Path(__file__).resolve().parents[1] / "assetops_backend"
STORE_FILE = PKG / "financials" / "adapters" / "postgres_assumption_store.py"


def test_no_product_module_passes_the_recorded_clock_override():
    offenders = []
    for path in PKG.rglob("*.py"):
        if path == STORE_FILE:
            continue
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, ast.Call) and any(k.arg == KW for k in node.keywords):
                offenders.append(f"{path.relative_to(PKG)}:{node.lineno}")
            if isinstance(node, ast.Attribute) and node.attr == KW:
                offenders.append(f"{path.relative_to(PKG)}:{node.lineno}")
    assert offenders == []
    for name in ("financials/composition.py", "main.py"):
        assert KW not in (PKG / name).read_text(encoding="utf-8")


def test_seam_check_is_non_vacuous():
    tree = ast.parse("PostgresAssumptionStore(url, test_recorded_clock_override=f)")
    assert any(isinstance(n, ast.Call) and any(k.arg == KW for k in n.keywords) for n in ast.walk(tree))


pg = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

if URL:
    from test_s4_assumptions_postgres import KEY, UTC, pub, site  # noqa: F401
    from test_s1_bindings_postgres import engine, store  # noqa: F401

    from assetops_backend.financials.adapters.postgres_assumption_store import PostgresAssumptionStore
    from assetops_backend.financials.assumptions import SYSTEM_PUBLISHER


@pg
def test_override_sets_recorded_instant_and_snapshot_visibility(site):  # noqa: F811
    tenant, site_id = site
    x = datetime(2026, 9, 1, 8, 0, tzinfo=UTC)
    s = PostgresAssumptionStore(URL, test_recorded_clock_override=lambda: x)
    try:
        s.publish(tenant, site_id, pub(None, "a0-1"), SYSTEM_PUBLISHER)
        before = s.snapshot(tenant, site_id, KEY, x - timedelta(seconds=1), 0, 10)
        at = s.snapshot(tenant, site_id, KEY, x, 0, 10)
    finally:
        s.dispose()
    assert before["timeline"] == [] and before["revisions"] == []
    assert len(at["timeline"]) == 1 and at["timeline"][0]["recorded_from"] == x
    assert at["revisions"][0]["recorded_at"] == x


@pg
def test_without_override_uses_the_server_clock(site):  # noqa: F811
    tenant, site_id = site
    s = PostgresAssumptionStore(URL)
    assert s.test_recorded_clock_override is None
    lo = datetime.now(timezone.utc) - timedelta(seconds=30)
    try:
        out = s.publish(tenant, site_id, pub(None, "a0-2"), SYSTEM_PUBLISHER)
    finally:
        s.dispose()
    assert lo < out.recorded_at < datetime.now(timezone.utc) + timedelta(seconds=30)


@pg
def test_override_keeps_recorded_time_not_later(site):  # noqa: F811
    from assetops_backend.financials.assumptions import PublicationRefused
    tenant, site_id = site
    x = datetime(2026, 9, 1, 8, 0, tzinfo=UTC)
    s = PostgresAssumptionStore(URL, test_recorded_clock_override=lambda: x)
    try:
        first = s.publish(tenant, site_id, pub(None, "a0-3"), SYSTEM_PUBLISHER)
        with pytest.raises(PublicationRefused) as e:
            s.publish(tenant, site_id, pub(first.revision_id, "a0-4", kind="CORRECTION", reason="r"),
                      SYSTEM_PUBLISHER)
    finally:
        s.dispose()
    assert e.value.code == "RECORDED_TIME_NOT_LATER"
