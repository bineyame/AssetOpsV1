"""W3-02 0c on real Postgres: the pinned cold/EV Site facades return exactly the W2 Site read's capability rows and
money for the same exact window, on the caller's connection with no `_ctx`/`open_on`/`_selected`/`within`; and
`select_consequence_on` carries the selected W1 head's immutable window, quantity and overlap group. 0c r1: cold
money runs the W2-04 producer (real `PRODUCT_EXPOSURE` heads), and a pinned read at K is unchanged by a later
replay/recompute (cold) or tariff correction (EV) while a later cutoff selects the later head.
"""

from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from test_w205b_ev_replay_postgres import URL

pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

if URL:
    from sqlalchemy import text
    from test_s1_bindings_postgres import engine, store  # noqa: F401
    from test_w202_cold_replay_postgres import chain as cold_chain  # noqa: F401
    from test_w203_cold_replay_postgres import opened, run
    from test_w204_cold_consequence import drain
    from test_w205b_ev_replay_postgres import chain  # noqa: F401
    from test_w206_ev_store_postgres import run_worker
    from test_w207_ev_money_postgres import (
        EV_KEY,
        GOLDEN_FROM,
        GOLDEN_TO,
        SYSTEM_PUBLISHER,
        PostgresAssumptionStore,
        Publication,
        ev_money_rows,
        golden_tariff,
        money_head,
    )
    from test_w207_ev_money_postgres import money as run_ev_money
    from test_w301_w1_money_snapshot_helpers_postgres import rig  # noqa: F401

    from assetops_backend.analytics.adapters.postgres_assessment_store import ColdReadService, EvReadService
    from assetops_backend.analytics.cold_reads import ColdPinnedLineageUnavailable
    from assetops_backend.analytics.cold_site_reads import ColdSiteReadService
    from assetops_backend.ev_site_reads import STALE_AS_OF_COPY, EvSiteReads
    from assetops_backend.evidence.composition import build_link_rows_reader
    from assetops_backend.financials.adapters.postgres_consequence_store import EvMoneyReads
    from assetops_backend.financials.composition import build_cold_consequence_store

COLD_CODE, EV_CODE = "COLD-READ", "EV-LAB-001"
COLD_DAY = datetime(2026, 10, 6, tzinfo=timezone.utc)  # the W2-03 late-reading fixture day


@contextmanager
def snapshot(built_engine):
    with built_engine.connect().execution_options(isolation_level="REPEATABLE READ") as c:
        with c.begin():
            yield c
            assert c.in_transaction(), "a facade ended the caller's transaction"


def clocks(built) -> tuple:
    with built.engine.connect() as c:
        return (c.execute(text("SELECT max(decided_at) FROM ingestion_disposition WHERE site_id = :s"),
                          {"s": built.site_id}).scalar_one(),
                c.execute(text("SELECT clock_timestamp()")).scalar_one())


def day_of(at):
    return at.replace(hour=0, minute=0, second=0, microsecond=0)


def forbid(monkeypatch, obj, *names) -> None:
    for name in names:
        monkeypatch.setattr(obj, name, lambda *a, **k: pytest.fail(f"a pinned facade called {name}"))


def cold_pinned_read(built, wm, k) -> dict:
    """One pinned cold estate read at (`wm`, K): the pinned window, its selected Finding revisions and `money_on`."""
    reads = ColdReadService(engine=built.engine, link_rows=build_link_rows_reader())
    consequences = build_cold_consequence_store(built.engine.url.render_as_string(hide_password=False))
    site = ColdSiteReadService(reads, consequences)
    try:
        with snapshot(built.engine) as c:
            (pinned,) = reads.estate_snapshots_on(c, built.tenant_id, built.site_id, COLD_CODE, COLD_DAY,
                                                  COLD_DAY + timedelta(days=1), wm, k)
            findings = sorted(str(i["revision_id"]) for i in reads.current_findings_on(c, pinned))
            money = site.money_on(c, pinned, [{"finding_revision_id": f} for f in findings])
    finally:
        consequences.dispose()
    return {"seqs": pinned["selection_seqs"], "findings": findings, "money": money,
            "heads": [(r["id"], r["kind"], r["exact_basis"], r["counted"]) for r in money["consequences"]]}


def test_cold_facades_match_the_w2_site_window(cold_chain, monkeypatch) -> None:  # noqa: F811
    built = opened("late-reading", cold_chain)
    run(built)
    drain(built)  # 0c r1 M1: the W2-04 producer stores a real PRODUCT_EXPOSURE head before the snapshot
    wm, k = clocks(built)
    url = built.engine.url.render_as_string(hide_password=False)
    reads = ColdReadService(engine=built.engine, link_rows=build_link_rows_reader())
    consequences = build_cold_consequence_store(url)
    site = ColdSiteReadService(reads, consequences)
    t, s = built.tenant_id, built.site_id
    try:
        with snapshot(built.engine) as c:
            (pinned,) = reads.estate_snapshots_on(c, t, s, COLD_CODE, COLD_DAY, COLD_DAY + timedelta(days=1), wm, k)
            w2 = reads.selection_on(c, t, s, COLD_CODE, pinned["lo"], pinned["hi"], wm)
            findings = reads.current_findings_on(c, w2)
            expected_caps = site._capabilities(c, w2)
            expected_money = site._money(c, w2, findings)
            expected_heads = expected_money["heads"]
            forbid(monkeypatch, site, "_selected", "overview", "evidence", "financials")
            forbid(monkeypatch, reads, "within", "_read", "selection_on", "envelope_on")
            caps = site.capabilities_on(c, pinned)
            money = site.money_on(c, pinned, [{"finding_revision_id": i["revision_id"]} for i in findings])
            with pytest.raises(ColdPinnedLineageUnavailable, match="cannot be proved"):
                site.capabilities_on(c, w2)  # the W2 (unpinned) snapshot of the same window
    finally:
        consequences.dispose()
    assert caps["capabilities"] == expected_caps and len(expected_caps) == 6
    assert caps["assessment_revision_ids"] == {a: str(x.revision_id) for a, x in pinned["selected"].items()}
    assert caps["selection_seqs"] == pinned["selection_seqs"]
    assert caps["evidence_ids"] == sorted({str(e) for x in pinned["selected"].values() for e in x.evidence_ids})
    assert len(expected_heads) >= 1 and any(h["kind"] == "PRODUCT_EXPOSURE" for h in expected_heads)
    counted = {str(h["id"]) for h in expected_money["counted"]}
    assert [(r["id"], r["kind"], r["exact_basis"], r["counted"]) for r in money["consequences"]] == [
        (str(h["id"]), h["kind"], site._exact_basis(h), str(h["id"]) in counted)
        for h in sorted(expected_heads, key=lambda h: (str(h["finding_revision_id"]), h["kind"]))]
    assert any(r["counted"] for r in money["consequences"])
    assert money["withheld"] == expected_money["withheld"]
    assert money["hold"] == (expected_money["hold"] if expected_money["withheld"] else None)
    assert money["selection_seqs"] == caps["selection_seqs"] and money["known_at"] == caps["known_at"]


def test_cold_pinned_read_at_k_survives_a_later_replay(cold_chain) -> None:  # noqa: F811
    """0c r1 H1/L1/L2 (the Q7-1 shape): K0 before the producer ran holds K0's pending work even after a SUCCEEDED
    attempt; K after the first drain selects the first head; a late reading, replay and second drain leave the read
    at K identical, and a later cutoff selects the new Finding and consequence."""
    built = opened("late-reading", cold_chain)
    run(built)
    wm0, k0 = clocks(built)
    before = cold_pinned_read(built, wm0, k0)
    assert before["money"]["withheld"] is True and before["heads"] == [] and before["findings"]
    drain(built)
    wm, k = clocks(built)
    first = cold_pinned_read(built, wm, k)
    again0 = cold_pinned_read(built, wm0, k0)  # a SUCCEEDED attempt after K0 does not clear K0's pending work
    assert again0["money"]["withheld"] is True and again0["money"]["hold"] == before["money"]["hold"]
    assert again0["heads"] == []  # the head recorded after K0 is absent at K0
    assert first["money"]["withheld"] is False and first["money"]["hold"] is None
    assert [h[1] for h in first["heads"]] == ["PRODUCT_EXPOSURE"] and first["heads"][0][3] is True
    built.advance_late()
    run(built)
    drain(built)
    repeat = cold_pinned_read(built, wm, k)
    assert repeat["seqs"] == first["seqs"] and repeat["findings"] == first["findings"]
    assert repeat["heads"] == first["heads"]  # IDs, kind, exact basis and counted unchanged at K
    wm2, k2 = clocks(built)
    later = cold_pinned_read(built, wm2, k2)
    assert later["findings"] != first["findings"]
    assert [h[0] for h in later["heads"]] and {h[0] for h in later["heads"]}.isdisjoint({h[0] for h in first["heads"]})
    assert all(h[2]["finding_revision_id"] in later["findings"] for h in later["heads"])


def test_ev_facades_match_the_w2_site_window(chain, monkeypatch) -> None:  # noqa: F811
    built = chain("complete")
    built.start_release_upload()
    run_worker(built)
    golden_tariff(built)
    assert all(o.succeeded for o in run_ev_money(built))  # one stored, priced EV head
    head = money_head(ev_money_rows(built))
    wm, k = clocks(built)
    link_rows = build_link_rows_reader()
    reads = EvReadService(engine=built.engine, link_rows=link_rows)
    site = EvSiteReads(reads, EvMoneyReads(link_rows))
    t, s = built.tenant_id, built.site_id
    with snapshot(built.engine) as c:
        day = c.execute(text("SELECT min(window_start) FROM analytic_run_selection WHERE site_id = :s"),
                        {"s": s}).scalar_one()
        pinned = reads.estate_snapshots_on(c, t, s, EV_CODE, day_of(day), day_of(day) + timedelta(days=1), wm, k)
        expected = []
        for p in pinned:
            ctx = site._ctx(c, t, s, EV_CODE, p["lo"], p["hi"], wm)
            expected.append((site._capabilities(ctx), site._consequence(ctx), ctx["money"]["guard"]))
        forbid(monkeypatch, site, "_ctx", "overview", "evidence", "financials")
        forbid(monkeypatch, reads, "open_on", "within", "_read")
        got = [(site.capabilities_on(c, p), site.money_on(c, p)) for p in pinned]
    assert pinned and len(got) == len(expected)
    assert str(head["id"]) in {m["consequence"]["revision_id"] for _, m in got if m["consequence"]}
    for p, (caps, money), (want_caps, want_consequence, want_guard) in zip(pinned, got, expected):
        assert caps["capabilities"] == want_caps and want_caps
        assert money["consequence"] == want_consequence and money["guard"] == want_guard
        assert caps["assessment_revision_id"] == str(p["selected"]["revision_id"]).lower()
        assert caps["selection_seqs"] == p["selection_seqs"] and caps["evidence_ids"] == p["selected"]["evidence_ids"]
        assert money["state"] == p["state"]


@pytest.mark.parametrize("case", ["complete", "missing-meter"])
def test_ev_capabilities_on_exposes_unknown_meter_of_the_selected_sessions(chain, monkeypatch, case) -> None:  # noqa: F811
    """W3-02 c1-q2: `unknown_meter` is whether an exact selected session has positive unknown meter seconds, from
    the same pinned context on the caller's connection (no `_ctx` or second snapshot)."""
    built = chain(case)
    built.start_release_upload()
    run_worker(built)
    wm, k = clocks(built)
    link_rows = build_link_rows_reader()
    reads = EvReadService(engine=built.engine, link_rows=link_rows)
    site = EvSiteReads(reads, EvMoneyReads(link_rows))
    t, s = built.tenant_id, built.site_id
    with snapshot(built.engine) as c:
        day = c.execute(text("SELECT min(window_start) FROM analytic_run_selection WHERE site_id = :s"),
                        {"s": s}).scalar_one()
        pinned = reads.estate_snapshots_on(c, t, s, EV_CODE, day_of(day), day_of(day) + timedelta(days=1), wm, k)
        expected = []
        for p in pinned:
            ctx = site._pinned_ctx(c, p)
            expected.append((site._capabilities(ctx),
                             [session.get("unknown_meter_seconds") for session in site._sessions(ctx)]))
        forbid(monkeypatch, site, "_ctx", "overview", "evidence", "financials")
        forbid(monkeypatch, reads, "open_on", "within", "_read")
        got = [site.capabilities_on(c, p) for p in pinned]
    assert pinned and len(got) == len(expected)
    for caps, (want_caps, seconds) in zip(got, expected):
        assert caps["capabilities"] == want_caps
        assert caps["unknown_meter"] is any((x or 0) > 0 for x in seconds)
    assert any(caps["unknown_meter"] for caps in got) is (case == "missing-meter")


def ev_pinned_read(built, wm, k) -> dict:
    """One pinned EV estate read at (`wm`, K) of the selected session window, with the basis derived at K."""
    link_rows = build_link_rows_reader()
    reads = EvReadService(engine=built.engine, link_rows=link_rows)
    site = EvSiteReads(reads, EvMoneyReads(link_rows))
    t, s = built.tenant_id, built.site_id
    with snapshot(built.engine) as c:
        day = c.execute(text("SELECT min(window_start) FROM analytic_run_selection WHERE site_id = :s "
                             "AND analytic_id = 'ev-session/1'"), {"s": s}).scalar_one()
        pinned = reads.estate_snapshots_on(c, t, s, EV_CODE, day_of(day), day_of(day) + timedelta(days=1), wm, k)
        reads_at_k = [(site.money_on(c, p), site._pinned_ctx(c, p)["money"]["derived"]) for p in pinned]
    (money, derived), = [(m, d) for m, d in reads_at_k if m["consequence"] is not None] or reads_at_k[:1]
    cons = money["consequence"]
    return {"money": money, "basis": None if derived is None else derived.basis_sha256,
            "ids": (cons["revision_id"], cons["tariff_revision_id"], cons["evidence_ids"],
                    cons["session_revision_ids"]),
            "history": [h["revision_id"] for h in money["history"]]}


def test_ev_pinned_read_at_k_survives_a_later_tariff_correction(chain) -> None:  # noqa: F811
    """0c r1 H1 (EV) / L2: K0 before any tariff is `STALE_BASIS` (null revision, as-of copy) even after a tariff and
    head are stored; K after the first head keeps its tariff, basis, consequence, cited IDs and history after a
    later correction and its head; a later cutoff selects the new matching head."""
    built = chain("complete")
    built.start_release_upload()
    run_worker(built)
    wm0, k0 = clocks(built)
    tariff = golden_tariff(built)
    assert all(o.succeeded for o in run_ev_money(built))
    first_head = money_head(ev_money_rows(built))
    wm, k = clocks(built)
    first = ev_pinned_read(built, wm, k)
    assert first["ids"][0] == str(first_head["id"]) and first["ids"][1] == str(tariff)
    assert first["basis"] == first_head["basis_sha256"].strip() and first["money"]["guard"] is None
    prices = PostgresAssumptionStore(URL)
    try:
        second = prices.publish(built.tenant_id, built.site_id, Publication(
            assumption_key=EV_KEY, currency="KES", value=Decimal("0.30000"), basis="AUTHORED_ESTIMATE",
            source_reference="W3-02 0c r1 later tariff", valid_from=GOLDEN_FROM, valid_to=GOLDEN_TO,
            change_kind="CORRECTION", correction_reason="W3-02 0c r1 second price", expected_prior_revision_id=tariff,
            idempotency_key="w302-0c-r1-tariff-2", channel="SYSTEM_FIXTURE", provenance={}),
            SYSTEM_PUBLISHER).revision_id
    finally:
        prices.dispose()
    assert all(o.succeeded for o in run_ev_money(built))
    newest = money_head(ev_money_rows(built))
    assert newest["id"] != first_head["id"] and newest["tariff_revision_id"] == second
    repeat = ev_pinned_read(built, wm, k)
    assert (repeat["ids"], repeat["basis"], repeat["history"]) == (first["ids"], first["basis"], first["history"])
    wm2, k2 = clocks(built)
    later = ev_pinned_read(built, wm2, k2)
    assert later["ids"][:2] == (str(newest["id"]), str(second)) and later["basis"] == newest["basis_sha256"].strip()
    assert str(first_head["id"]) in later["history"]
    stale = ev_pinned_read(built, wm0, k0)  # no tariff recorded at K0: no stored head for the as-of basis
    assert stale["money"]["guard"] == "STALE_BASIS" and stale["ids"][0] is None
    assert stale["money"]["consequence"]["limitation"] == STALE_AS_OF_COPY and stale["history"] == []
    assert stale["money"]["consequence"]["amount"] is None


HEAD_FIELDS = ("window_start", "window_end", "quantity_low", "quantity_high", "quantity_unit", "overlap_group")
W301_KEYS = {"finding_revision_id", "known_at", "finding_id", "consequence_revision_id", "revision_no", "recorded_at",
             "consequence_state", "amount_low", "amount_high", "currency", "basis", "price", "cited", "currentness"}


def stored_head(engine, revision_id) -> dict:  # noqa: F811
    with engine.connect() as c:
        return dict(c.execute(text(
            "SELECT window_start, window_end, quantity_low, quantity_high, quantity_unit, overlap_group "
            "FROM financial_consequence_revision WHERE id = :r"), {"r": revision_id}).one()._mapping)


def test_select_consequence_on_carries_immutable_head_fields(rig) -> None:  # noqa: F811
    from test_s4_consequence_store_postgres import POWER_DAY

    rig.run()  # revision 1: UNPRICED
    rev = rig.site.on(POWER_DAY)
    created_at = rig.now()
    rig.site.publish("v1")
    rig.run()  # revision 2: PRICED
    live, at1 = rig.on(rev["id"], rig.now()), rig.on(rev["id"], created_at)
    assert W301_KEYS <= set(live) and set(live) - W301_KEYS == set(HEAD_FIELDS)
    for got in (live, at1):
        row = stored_head(rig.engine, got["consequence_revision_id"])
        assert tuple(datetime.fromisoformat(got[f].replace("Z", "+00:00")) for f in ("window_start", "window_end"))             == (row["window_start"], row["window_end"])
        assert (got["quantity_low"], got["quantity_high"]) == (format(row["quantity_low"], "f"),
                                                               format(row["quantity_high"], "f"))
        assert (got["quantity_unit"], got["overlap_group"]) == (row["quantity_unit"], row["overlap_group"])
        assert got["quantity_low"] is not None and got["overlap_group"]
    assert at1["consequence_revision_id"] != live["consequence_revision_id"]  # each head's own fields
    assert at1["currentness"]["state"] == "CURRENT" and at1["amount_high"] is None
    with rig.engine.connect() as c:
        made = c.execute(text("SELECT created_at FROM finding_revision WHERE id = :r"), {"r": rev["id"]}).scalar_one()
    pending = rig.on(rev["id"], made)  # created, no consequence recorded: every head field null
    assert pending["currentness"]["state"] == "PENDING" and all(pending[f] is None for f in HEAD_FIELDS)
