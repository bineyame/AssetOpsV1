"""OUT-D U3: the declared-objective store against Postgres (build sheet OUT-D §3 U3).

The demo file twice (6 rows, then 6 exact retries); a v2 for Kobo MG-2 supersedes v1; `current(known_at)` before the
v2 keeps returning v1 after it while `current(None)` returns v2; prior-mismatch, key-reuse and unknown-Site refusals;
the trigger refuses UPDATE. A fresh module database (pg_harness); requires ASSETOPS_TEST_DATABASE_URL naming `*_test`.
"""

from __future__ import annotations

import json
from dataclasses import replace
from decimal import Decimal
from pathlib import Path

import pytest

from test_s4_finding_store_postgres import URL

pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

if URL:
    from sqlalchemy import text
    from sqlalchemy.exc import DBAPIError

    from test_s1_bindings_postgres import engine, imported, store  # noqa: F401

    from assetops_backend import declare_objective
    from assetops_backend.objectives.composition import build_objective_store
    from assetops_backend.objectives.model import SYSTEM_DECLARER, Declaration, ObjectiveRefused

DEMO = Path(__file__).resolve().parents[1] / "conversions" / "demo-objectives.json"
SITES = ("KOBO-001", "COLD-LAB-001", "EV-LAB-001")


def run(objectives, capsys) -> list[dict]:
    code = declare_objective.main(["fixture", "--file", str(DEMO)], store=objectives)
    out = capsys.readouterr()
    assert code == 0, out.err
    return [json.loads(line) for line in out.out.splitlines()]


def refusal(fn) -> ObjectiveRefused:
    with pytest.raises(ObjectiveRefused) as caught:
        fn()
    return caught.value


def test_declare_idempotent_chain_reproducible_reads_and_refusals(store, engine, capsys) -> None:  # noqa: F811
    for code in SITES:
        imported(store, code)
    objectives = build_objective_store(URL)
    try:
        first = run(objectives, capsys)
        assert [(o["site_code"], o["outcome_key"], o["inserted"], o["revision_no"]) for o in first] == [
            ("KOBO-001", "MG-2", True, 1), ("KOBO-001", "MG-1", True, 1), ("KOBO-001", "MG-5", True, 1),
            ("COLD-LAB-001", "CC-6", True, 1), ("EV-LAB-001", "EV-1", True, 1), ("EV-LAB-001", "EV-2", True, 1)]
        again = run(objectives, capsys)
        assert [o["inserted"] for o in again] == [False] * 6
        assert [o["revision_id"] for o in again] == [o["revision_id"] for o in first]
        with engine.connect() as c:
            assert c.execute(text("SELECT count(*) FROM outcome_objective_revision")).scalar() == 6
            ev2 = c.execute(text("SELECT measure_kind, comparison, unit, currency, window_rule, target, actor_id, "
                                 "source_channel FROM outcome_objective_revision WHERE outcome_key = 'EV-2'")).one()
        assert tuple(ev2) == ("VALUE", "AT_MOST", "currency/km", "USD", "BOARD_WINDOW", Decimal("0.20"),
                              SYSTEM_DECLARER.actor_id, "SYSTEM_FIXTURE")

        tenant_id = objectives.tenant_id("demo")
        site_id = objectives.site_id(tenant_id, "KOBO-001")
        v1 = next(o for o in first if o["outcome_key"] == "MG-2")
        k1 = max(r["recorded_at"] for r in objectives.current(tenant_id, site_id, None))
        before = {r["outcome_key"]: r for r in objectives.current(tenant_id, site_id, k1)}
        assert sorted(before) == ["MG-1", "MG-2", "MG-5"] and str(before["MG-2"]["id"]) == v1["revision_id"]

        v2 = Declaration("KOBO-001", "MG-2", "avoidable_generator_minutes", Decimal("5"), None, "DECLARED",
                         "Declared for the demonstration; not a customer target", before["MG-2"]["id"],
                         "out-d-kobo-001-mg-2-v2")
        row, inserted = objectives.declare(tenant_id, v2, SYSTEM_DECLARER, "SYSTEM_CLI")
        assert inserted and row["revision_no"] == 2 and row["supersedes_revision_id"] == before["MG-2"]["id"]
        assert row["recorded_at"] > k1
        now = {r["outcome_key"]: r for r in objectives.current(tenant_id, site_id, None)}
        assert now["MG-2"]["id"] == row["id"] and now["MG-2"]["target"] == Decimal("5")
        still = {r["outcome_key"]: r for r in objectives.current(tenant_id, site_id, k1)}
        assert still["MG-2"]["id"] == before["MG-2"]["id"] and still["MG-2"]["target"] == Decimal("0")
        assert objectives.declare(tenant_id, v2, SYSTEM_DECLARER, "SYSTEM_CLI") == (row, False)

        stale = refusal(lambda: objectives.declare(
            tenant_id, replace(v2, idempotency_key="out-d-kobo-001-mg-2-v3"), SYSTEM_DECLARER, "SYSTEM_CLI"))
        assert (stale.status, stale.code) == (409, "OBJECTIVE_PRIOR_MISMATCH")
        none_vs_head = refusal(lambda: objectives.declare(
            tenant_id, replace(v2, expected_prior=None, idempotency_key="out-d-kobo-001-mg-2-v4"), SYSTEM_DECLARER,
            "SYSTEM_CLI"))
        assert none_vs_head.code == "OBJECTIVE_PRIOR_MISMATCH"
        reused = refusal(lambda: objectives.declare(tenant_id, replace(v2, target=Decimal("7")), SYSTEM_DECLARER,
                                                    "SYSTEM_CLI"))
        assert (reused.status, reused.code) == (409, "IDEMPOTENCY_KEY_REUSED")
        missing = refusal(lambda: objectives.declare(tenant_id, replace(v2, site_code="NOPE-001"), SYSTEM_DECLARER,
                                                     "SYSTEM_CLI"))
        assert (missing.status, missing.code) == (404, "SITE_NOT_FOUND")
        invalid = refusal(lambda: objectives.declare(tenant_id, replace(v2, target=Decimal("-1")), SYSTEM_DECLARER,
                                                     "SYSTEM_CLI"))
        assert (invalid.status, invalid.code) == (422, "OBJECTIVE_INVALID")
        with engine.connect() as c:
            assert c.execute(text("SELECT count(*) FROM outcome_objective_revision")).scalar() == 7

        with pytest.raises(DBAPIError, match="append only"):
            with engine.begin() as c:
                c.execute(text("UPDATE outcome_objective_revision SET target = 9 WHERE id = :id"), {"id": row["id"]})
    finally:
        objectives.dispose()
