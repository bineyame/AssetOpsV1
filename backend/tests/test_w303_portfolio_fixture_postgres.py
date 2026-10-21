"""W3-03 seam run 0b: the single persisted one-day three-domain Portfolio fixture and its exact public root reads.

Spec: `.agent/W3-03-build-spec.md` closure 4 B3/B4 (closure 2 Q9 as amended there, closure 3). One private `*_test`
database and the one `demo` tenant compose, without the golden `S4_CASES["F03"]` KOBO import:

* the W3-01 golden `mixed_replay` mechanics - cold `excursion` (drained) and EV `complete` with their second database reset
  suppressed (test-scoped, as `mixed_replay` does);
* the W3-02 `two_ev_sites` second Site `EV-LAB-002` (`install_second_ev_site`) and its golden tariff and W2-07 money
  worker sequence for both EV Sites;
* the W3-01 `power_estate` P01-bound `PowerSite`/`Rig` producer for the one and only `KOBO-001` (S4-05
  `publishing_submit(P01)`, SYSTEM diesel price v1-v3, the consequence worker drained).

After every ingestion, publication and worker decision one read clock is frozen and the estate snapshots pinned to it.
`/findings`, `/actions`, `/evidence` and `/financials` are then read through their public routers over the 10-06
request window with no `known_at`. Portfolio code does not exist yet (run 1a); its card/combined-value assertions
belong to runs 1a/1b, which build on `build_portfolio_fixture` here. Needs ASSETOPS_TEST_DATABASE_URL.

The cold producer is `excursion` plus the W2-04 consequence drain (r0b P-0b-1): `normal` selects no cold Finding or
product-exposure line on 2026-10-06. Callers (runs 1a/1b) import `build_portfolio_fixture` and get the replay
fixtures, which this module imports below; the builder patches `pg_harness.fresh_database`, the snapshot classes and
`CaseRunner.submit` for the rest of the test.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any
from urllib.parse import urlencode
from uuid import UUID

import pytest

from test_w301_estate_index_postgres import URL

pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

DAY = datetime(2026, 10, 6, tzinfo=timezone.utc)
WINDOW_TO = DAY + timedelta(days=1)
IMPORTED_AT = DAY - timedelta(days=1)
VARIANT_B_CUTOFF = datetime(2026, 9, 30, tzinfo=timezone.utc)
CODES = ("COLD-LAB-001", "EV-LAB-001", "EV-LAB-002", "KOBO-001")

if URL:
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from sqlalchemy import create_engine, text

    import pg_harness
    from test_s4_consequence_store_postgres import POWER_DAY, PowerSite
    from test_s4_finding_store_postgres import CaseRunner
    from test_s405_publication_postgres import P01
    from test_s405_resolver_postgres import publishing_submit
    from test_w203_cold_replay_postgres import opened, run
    from test_w205b_ev_replay_postgres import Chain as EvChain
    from test_w206_ev_store_postgres import run_worker
    from test_w207_ev_money_postgres import golden_tariff, money
    from test_w301_estate_golden_postgres import cold_chain, ev_chain  # noqa: F401 - the replay factories
    from test_w301_estate_index_postgres import Estate, consequence_row, db_now, imported_before, iso
    from test_w301_w1_money_snapshot_helpers_postgres import Rig
    from test_w302_evidence_scope_snapshot_postgres import evidence_read
    from test_w302_money_comparability_postgres import (
        SECOND_EV, SECOND_SCENARIO_ID, _line_matches, _stored, install_second_ev_site, second_scenario_repository)

    from assetops_backend.analytics.adapters.postgres_assessment_store import PostgresAssessmentStore
    from assetops_backend.estate.adapters import postgres_estate_read
    from assetops_backend.estate.adapters import postgres_evidence_money_read as pemr
    from assetops_backend.estate.evidence_money import EstateEvidenceService, group_key_for_partition
    from assetops_backend.estate_evidence_money_api import build_estate_evidence_money_router
    from assetops_backend.sites.adapters.postgres_foundation_store import PostgresFoundationStore


# --- the composed fixture -----------------------------------------------------------------------------------------

@dataclass
class PortfolioFixture:
    """The clean four-Site fixture: its engine, tenant, Site IDs by code, producers and the frozen read clock."""

    engine: Any
    tenant_id: Any
    site_ids: dict[str, str]
    cold: Any
    evs: tuple[Any, Any]
    tariffs: dict[str, Any]
    power: Any
    rig: Any
    power_revision: dict
    frozen: datetime
    window: dict[str, str] = field(default_factory=lambda: {"from": iso(DAY), "to": iso(WINDOW_TO)})

    def estate(self) -> "Estate":
        return Estate(self.engine, self.tenant_id)

    def money(self) -> "EvidenceMoney":
        return EvidenceMoney(self.engine, self.tenant_id)


class EvidenceMoney:
    """The W3-02 Evidence/Financials router over the one-transaction estate snapshot of `evidence_read`."""

    def __init__(self, engine, tenant_id) -> None:
        self.read = evidence_read(engine)
        app = FastAPI()
        app.include_router(build_estate_evidence_money_router(EstateEvidenceService(self.read), lambda: tenant_id,
                                                              access=lambda request, code: None))
        self.client = TestClient(app)

    def ok(self, root: str, **params) -> dict:
        response = self.client.get(f"/api/estate/{root}?" + urlencode(params))
        assert response.status_code == 200, response.text
        return response.json()


def pin_snapshots(monkeypatch, present, targets=None) -> None:
    """TEST-SCOPED: the estate and Evidence/Financials snapshots' `read_at` and the assessment store's
    live-or-historical test are the frozen `present()` (W3-01 `pin_read_at` plus the W3-02 `EvidenceMoneySnapshot`
    pin). Every query, cutoff, selection and rule stays real; only "now" is the fixture's."""
    for module, name in targets or ((postgres_estate_read, "EstateSnapshot"), (pemr, "EvidenceMoneySnapshot")):
        real = getattr(module, name)
        real = getattr(real, "_real", real)  # idempotent: a re-pin replaces, never nests, the earlier clock

        class Pinned(real):  # type: ignore[valid-type, misc]
            def __init__(self, owner, c, read_at) -> None:
                super().__init__(owner, c, present())

        Pinned._real = real  # type: ignore[attr-defined]
        monkeypatch.setattr(module, name, Pinned)
    monkeypatch.setattr(PostgresAssessmentStore, "_transaction_time", staticmethod(lambda c: present()))


def test_repin_moves_the_snapshot_clock(monkeypatch) -> None:
    """A second `pin_snapshots` replaces the first clock: a snapshot reads at the latest pinned clock."""
    import types

    class Snap:
        def __init__(self, owner, c, read_at) -> None:
            self.read_at = read_at

    ns = types.SimpleNamespace(Snap=Snap)
    first, second = datetime(2026, 10, 30, tzinfo=timezone.utc), datetime(2026, 11, 2, tzinfo=timezone.utc)
    pin_snapshots(monkeypatch, lambda: first, targets=((ns, "Snap"),))
    pin_snapshots(monkeypatch, lambda: second, targets=((ns, "Snap"),))
    assert ns.Snap(None, None, DAY).read_at == second != first


def _stamped_tables(engine, key: str) -> list[tuple[str, str]]:
    """Each public table with column `key` and its stored time (`recorded_at`, else `created_at`, else the accepted
    evidence `received_at`)."""
    with engine.connect() as c:
        cols: dict[str, dict[str, str]] = {}
        for table, column, kind in c.execute(text(
                "SELECT table_name, column_name, data_type FROM information_schema.columns "
                "WHERE table_schema = 'public' AND column_name IN (:k, 'recorded_at', 'created_at', 'received_at')"), {"k": key}):
            cols.setdefault(table, {})[column] = kind
    out = []
    for table, have in sorted(cols.items()):
        stamp = next((x for x in ("recorded_at", "created_at", "received_at") if x in have), None)
        if key in have and stamp is not None and have[key] == "uuid":
            out.append((table, stamp))
    return out


def latest_recorded(engine, site_ids) -> datetime:
    """The latest stored time of any Site-scoped row of these Sites (selection, assessment, Finding, consequence,
    evidence, tariff): the cold/EV recorded times the frozen clock must follow."""
    latest = None
    with engine.connect() as c:
        for table, stamp in _stamped_tables(engine, "site_id"):
            at = c.execute(text(f"SELECT max({stamp}) FROM {table} WHERE site_id = ANY(CAST(:s AS uuid[]))"),
                           {"s": [str(s) for s in site_ids]}).scalar_one()
            if at is not None and (latest is None or at > latest):
                latest = at
    assert latest is not None
    return latest


def recorded_times(engine, ids) -> dict[str, datetime]:
    """The stored time of each public ID, from whichever table holds that `id` (exactly one per ID)."""
    wanted = sorted({str(i).lower() for i in ids})
    found: dict[str, datetime] = {}
    with engine.connect() as c:
        for table, stamp in _stamped_tables(engine, "id"):
            for rid, at in c.execute(text(f"SELECT CAST(id AS text), {stamp} FROM {table} "
                                          "WHERE id = ANY(CAST(:ids AS uuid[]))"), {"ids": wanted}):
                assert rid not in found, f"{rid} is held by two tables"
                found[rid] = at
    return found


def build_portfolio_fixture(request, monkeypatch, capsys, cold_case: str = "excursion",
                            cold_drain: bool = True) -> PortfolioFixture:
    """Closure 4 B3: the one-day three-domain composition in one private DB and the `demo` tenant. P-0b-1 (resolved): the cold
    producer is `excursion` plus the W2-04 consequence drain before the frozen public reads; `normal` selects no
    cold Finding or product-exposure line on 2026-10-06."""
    fresh = pg_harness.fresh_database()  # the only database reset
    monkeypatch.setattr(pg_harness, "fresh_database", lambda: fresh)
    # Cold `excursion` (drained) and EV `complete`, settled as in `mixed_replay` (their Chain.open() resets suppressed).
    cold = opened(cold_case, request.getfixturevalue("cold_chain"))
    run(cold)
    if cold_drain:
        from test_w204_cold_consequence import drain
        drain(cold)
    first = request.getfixturevalue("ev_chain")("complete")
    first.start_release_upload()
    run_worker(first)
    # EV-LAB-002 as in `two_ev_sites`: the reviewed second-Site install, scenario and seed, its own UUID tag.
    from test_w205b_ev_replay_postgres import hold_uuids
    hold_uuids(monkeypatch, 0x3022)
    tmp = request.getfixturevalue("tmp_path")
    second = EvChain("complete", tmp / "ev-lab-002", site_code=SECOND_EV, seed=20518)
    request.addfinalizer(second.close)
    second.open(fresh=False, install=install_second_ev_site,
                scenarios=second_scenario_repository(tmp / "scenarios"), scenario_id=SECOND_SCENARIO_ID)
    second.start_release_upload()
    run_worker(second)
    assert cold.tenant_id == first.tenant_id == second.tenant_id
    with first.engine.connect() as c:
        for built in (cold, first, second):
            start = c.execute(text("SELECT min(window_start) FROM analytic_run_selection WHERE site_id = :s"),
                              {"s": built.site_id}).scalar_one()
            assert start.date() == DAY.date(), (built.site_code, start)
    tariffs = {}
    for built in (first, second):
        tariffs[built.site_code] = golden_tariff(built, currency="KES")
        outcomes = money(built)
        assert outcomes and all(o.succeeded for o in outcomes), [(o.error_code, o.error_detail) for o in outcomes]
    # KOBO-001: the `power_estate` P01-bound PowerSite and consequence worker on the same DB, with a directly
    # owned store (the `store` fixture would empty the tables). Its POWER_DAY is the request day.
    assert POWER_DAY == DAY
    store = PostgresFoundationStore(URL)
    eng = create_engine(URL)
    request.addfinalizer(lambda: pg_harness.dispose(store, eng))
    monkeypatch.setattr(CaseRunner, "submit", publishing_submit(lambda device, texts: P01))
    power = PowerSite(store, eng, capsys)
    request.addfinalizer(lambda: pg_harness.dispose(power.runner.findings, power.prices, power.store))
    assert power.tenant == cold.tenant_id
    pin_snapshots(monkeypatch, lambda: power.runner.now + timedelta(minutes=1))  # as `power_estate` pins
    rig = Rig(power, eng)
    capsys.readouterr()  # drop the replay chains' output: the publisher's stdout is parsed line by line
    power.publish("v1", "v2", "v3")
    rig.run()
    power_revision = power.on(POWER_DAY)
    site_ids = {"COLD-LAB-001": str(cold.site_id), "EV-LAB-001": str(first.site_id),
                SECOND_EV: str(second.site_id), "KOBO-001": str(power.site)}
    for site_id in site_ids.values():
        imported_before(eng, power.tenant, site_id, IMPORTED_AT)
    # One read clock after all decisions (B3): never a fictitious wall clock.
    windowed = [cold.site_id, first.site_id, second.site_id]
    frozen = max(power.runner.now + timedelta(minutes=1), db_now(eng),
                 latest_recorded(eng, windowed) + timedelta(microseconds=1))
    pin_snapshots(monkeypatch, lambda: frozen)
    return PortfolioFixture(engine=eng, tenant_id=power.tenant, site_ids=site_ids, cold=cold, evs=(first, second),
                            tariffs=tariffs, power=power, rig=rig, power_revision=power_revision, frozen=frozen)


@pytest.fixture()
def portfolio_fixture(request, monkeypatch, capsys):
    return build_portfolio_fixture(request, monkeypatch, capsys)


# --- the clean public-root proof ----------------------------------------------------------------------------------

def _by_site(rows: list[dict]) -> dict[str, list[dict]]:
    out: dict[str, list[dict]] = {}
    for row in rows:
        out.setdefault(row["site_id"], []).append(row)
    return out


def test_one_day_three_domain_fixture_public_roots(portfolio_fixture) -> None:
    """Closure 4 B3/B4 clean fixture, read through the public roots at the one frozen clock."""
    fx = portfolio_fixture
    estate, money_api = fx.estate(), fx.money()
    findings = estate.ok("findings", **fx.window, limit=100)
    actions = estate.ok("actions", **fx.window, limit=100)
    evidence = money_api.ok("evidence", **fx.window, limit=100)
    financials = money_api.ok("financials", **fx.window, limit=100)
    roots = {"findings": findings, "actions": actions, "evidence": evidence, "financials": financials}
    code_of = {v: k for k, v in fx.site_ids.items()}

    # One scope, one window and one cutoff across every root; the foreign tenant / empty Site are not in it.
    assert findings["window"]["known_at"] == iso(fx.frozen)  # every snapshot reads at `frozen`, not the first pin
    for name, body in roots.items():
        assert body["status"] == "CURRENT", name
        assert (body["window"]["from"], body["window"]["to"]) == (fx.window["from"], fx.window["to"]), name
        assert body["window"]["known_at"] == findings["window"]["known_at"], name
        assert sorted(code_of[s["site_id"]] for s in body["coverage"]["sites"]) == sorted(CODES), name
        assert body["scope"]["authorized_site_count"] == 4, name
    for name in ("findings", "evidence", "financials"):
        assert roots[name]["coverage"]["state"] == "COMPLETE", name
        assert {s["state"] for s in roots[name]["coverage"]["sites"]} == {"CURRENT"}, name

    # B4: the aligned 10-06 window selects no S6 Action (the reviewed accepted Actions are created 2026-11-01).
    assert actions["rows"] == [] and actions["total_count"] == 0
    with fx.engine.connect() as c:  # the empty root is not a window-exclusion proof: the DB holds no Action at all
        assert c.execute(text("SELECT count(*) FROM action")).scalar_one() == 0

    # Findings: the W1 head is the PowerSite power-day revision, PRICED from its exact stored consequence.
    rows = _by_site(findings["rows"])
    assert set(rows) <= set(fx.site_ids.values())
    (w1,) = rows[fx.site_ids["KOBO-001"]]
    assert w1["finding_revision_id"] == str(fx.power_revision["id"])
    stored = consequence_row(fx.engine, w1["consequence"]["source_revision_id"])
    assert stored[0] == w1["finding_revision_id"] and stored[1] == "PRICED"
    assert w1["consequence"]["state"] == "PRICED" and w1["lens_flags"] == ["COST"]
    assert (w1["consequence"]["amount_low"], w1["consequence"]["amount_high"],
            w1["consequence"]["currency"]) == stored[2:]
    for code in ("COLD-LAB-001", "EV-LAB-001", SECOND_EV):
        for row in rows.get(fx.site_ids[code], []):
            # A cold Finding is not priced from its product exposure; an EV Finding never inherits window money.
            assert row["consequence"]["state"] == "UNPRICED", (code, row["consequence"])
            assert row["consequence"]["amount_low"] is None and row["consequence"]["amount_high"] is None, code

    # Financials: the stored category lines, each Site in its own category; no estate total.
    lines = _by_site(financials["rows"])
    (w1_line,) = lines[fx.site_ids["KOBO-001"]]
    assert (w1_line["category"], w1_line["eligibility"]) == ("CANDIDATE_OPERATING_COST_EXPOSURE", "ELIGIBLE")
    assert w1_line["consequence_revision_id"] == w1["consequence"]["source_revision_id"]
    assert w1_line["finding_revision_id"] == w1["finding_revision_id"]
    assert w1_line["amount"]["low"] == stored[2] and w1_line["amount"]["high"] == stored[3]
    # P-0b-1: the selected cold POTENTIAL_PRODUCT_EXPOSURE line is UNPRICED, null amount, pins a selected cold Finding.
    cold_rows = lines.get(fx.site_ids["COLD-LAB-001"], [])
    (cold_line,) = cold_rows  # the ONLY cold line
    assert cold_line["category"] == "POTENTIAL_PRODUCT_EXPOSURE"
    assert len({r["category"] for r in financials["rows"]}) == 3
    assert cold_line["eligibility"] == "UNPRICED" and cold_line["amount"] is None, cold_line
    cold_revisions = {r["finding_revision_id"] for r in rows.get(fx.site_ids["COLD-LAB-001"], [])}
    assert cold_line["finding_revision_id"] in cold_revisions, (cold_line["finding_revision_id"], cold_revisions)
    with fx.engine.connect() as c:  # the cold line is the stored cold_consequence_revision row
        cold_stored = tuple(c.execute(text(
            "SELECT CAST(finding_revision_id AS text), kind, state, amount_low, amount_high FROM "
            "cold_consequence_revision WHERE CAST(id AS text) = :r"), {"r": cold_line["consequence_revision_id"]}).one())
    assert cold_stored == (cold_line["finding_revision_id"], "PRODUCT_EXPOSURE", "UNPRICED", None, None)
    cold_row = next(r for r in rows[fx.site_ids["COLD-LAB-001"]] if r["finding_revision_id"] == cold_line["finding_revision_id"])
    with fx.engine.connect() as c:  # the selected cold Finding revision is the stored head of its Finding
        head = c.execute(text("SELECT CAST(id AS text) FROM finding_revision WHERE CAST(finding_id AS text) = :f "
                              "ORDER BY revision_no DESC LIMIT 1"), {"f": str(cold_row["finding_id"])}).scalar_one()
    assert head == cold_line["finding_revision_id"]
    ev_stored = {b.site_code: _stored(b, fx.tariffs[b.site_code]) for b in fx.evs}
    for built in fx.evs:
        (line,) = lines[str(built.site_id)]
        _line_matches(line, built, ev_stored[built.site_code])
    a, b = lines[fx.site_ids["EV-LAB-001"]][0], lines[fx.site_ids[SECOND_EV]][0]
    for key in ("technical_interval_ids", "basis_evidence_ids"):
        assert a[key] and b[key] and not set(a[key]) & set(b[key]), key
    (group,) = [g for g in financials["groups"] if g["line_keys"] and g["category"] == "GROSS_TARIFF_SCENARIO"]
    assert group["state"] == "COMPARABLE" and group["line_keys"] == sorted([a["line_key"], b["line_key"]])
    assert group["group_key"] == group_key_for_partition(
        "GROSS_TARIFF_SCENARIO", "KES", a["window_start"], a["window_end"], a["period_kind"],
        a["assumption_fingerprint"])
    total = sum((Decimal(str(s["head"].amount)) for s in ev_stored.values()), Decimal(0))
    assert Decimal(group["amount"]["low"]) == total == Decimal(group["amount"]["high"])
    assert not [e for e in financials["exclusions"] if e["line_key"] in group["line_keys"]]
    assert financials["summary"]["estate_total"] is None
    assert financials["summary"]["estate_total_state"] == "NO_ESTATE_TOTAL"
    assert w1_line["category"] != a["category"]  # distinct categories, never combined

    # Evidence: every authorized Site has selected Evidence rows in the same window.
    assert {r["site_id"] for r in evidence["rows"]} == set(fx.site_ids.values())

    # B3: every selected head is at or before the frozen clock and strictly after the variant (b) cutoff.
    selected = {w1["finding_revision_id"], w1["consequence"]["source_revision_id"]}
    selected |= {r["finding_revision_id"] for r in findings["rows"]}
    selected |= {line["consequence_revision_id"] for line in financials["rows"]}
    selected |= {e for line in financials["rows"] for e in line["basis_evidence_ids"]}
    selected |= {x for row in evidence["rows"] for x in row["selected_revision_ids"]}
    times = recorded_times(fx.engine, selected)
    assert set(times) == {str(x).lower() for x in selected}
    for rid, at in times.items():
        assert VARIANT_B_CUTOFF < at <= fx.frozen, (rid, at)
    # Every one-day mini-grid dispatch selection is present at the frozen read.
    days = estate.read.read(lambda snap: snap.dispatch_days(UUID(str(fx.tenant_id)), UUID(fx.site_ids["KOBO-001"]),
                                                            DAY, WINDOW_TO, fx.frozen))
    assert [d["day"] for d in days] == [DAY.date()], days
