"""W2-04 commit 2: cold consequence revisions over the six registered W2-02 replays, through S2 and W2-03.

`.agent/W2-04-build-spec.md` "Fixtures, named tests and guards" (`test_w204_cold_consequence.py`), "Money schema
`0023` and rules" and Q4-Q6. Each case runs the W2-02 chain (gateway, Batch V2, ordinary S2 acceptance) and the
W2-03 cold worker in a fresh private `*_test` database; the 0023 triggers enqueue the cold work and the W2-04
worker derives from it. No accepted, assessment, Finding or consequence row is inserted by hand. Needs
`ASSETOPS_TEST_DATABASE_URL`; skipped (never passed) without it.
"""

from __future__ import annotations

import os
from datetime import datetime, timezone
from decimal import Decimal

import pytest

from assetops_backend.evidence.source_provenance import LinkRow
from assetops_backend.financials import cold_consequence as cc

URL = os.environ.get("ASSETOPS_TEST_DATABASE_URL")
needs_db = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

if URL:
    from sqlalchemy import text
    from test_w203_cold_replay_postgres import (  # noqa: F401 - `chain` is the W2-02 replay fixture
        CASES,
        chain,
        opened,
        rows,
        run,
    )

    from assetops_backend.financials.composition import build_cold_consequence_worker


def db_now(built):
    with built.engine.connect() as c:
        return c.execute(text("SELECT clock_timestamp()")).scalar_one()


def drain(built) -> list:
    """Run the W2-04 cold worker over every pending item, inside an observed DB time interval (Q6)."""
    before = db_now(built)
    worker = build_cold_consequence_worker(URL)
    outcomes = worker.run_pending(built.tenant_id, built.site_id)
    worker._store.dispose()
    after = db_now(built)
    assert outcomes and all(o.succeeded and o.error_code is None for o in outcomes), outcomes
    built.interval = (before, after)
    return outcomes


def consequences(built) -> list:
    return rows(built, "SELECT * FROM cold_consequence_revision WHERE site_id = :s ORDER BY created_at, id")


def links(built, revision_id) -> list:
    return rows(built, "SELECT evidence_id, use, reason, created_at FROM cold_consequence_evidence "
                       "WHERE site_id = :s AND consequence_revision_id = :r ORDER BY evidence_id, use", r=revision_id)


def chamber_room(built):
    [room] = rows(built, "SELECT s.id FROM asset s WHERE s.site_id = :s AND s.asset_code = 'room-1'")
    return room["id"]


def expected_basis_sha(built, rev) -> str:
    """Rebuild the canonical basis document from the stored rows (exact IDs, uses, cutoff) and hash it."""
    [fr] = rows(built, "SELECT id, basis_sha256 FROM finding_revision WHERE id = :r", r=rev["finding_revision_id"])
    [er] = rows(built, "SELECT basis_sha256 FROM cold_episode_revision WHERE id = :r", r=rev["episode_revision_id"])
    [ar] = rows(built, "SELECT a.basis_sha256, run.knowledge_cutoff FROM assessment_revision a JOIN analytic_run run "
                       "ON run.id = a.analytic_run_id WHERE a.id = :r", r=rev["assessment_revision_id"])
    evidence = [[str(x["evidence_id"]), x["use"], x["reason"]] for x in links(built, rev["id"])]
    evidence.sort(key=lambda e: (e[0], cc.USES.index(e[1])))
    return cc.basis_sha256({
        "model_id": "cold-exposure/1", "kind": "PRODUCT_EXPOSURE",
        "finding_revision_id": str(fr["id"]), "finding_basis_sha256": fr["basis_sha256"],
        "episode_revision_id": str(rev["episode_revision_id"]), "episode_basis_sha256": er["basis_sha256"],
        "assessment_revision_id": str(rev["assessment_revision_id"]), "assessment_basis_sha256": ar["basis_sha256"],
        "window": [cc.selected_instant(rev["window_start"]), cc.selected_instant(rev["window_end"])],
        "known_at": cc.selected_instant(ar["knowledge_cutoff"]), "evidence": evidence,
        "quantity": {"unit": "degC_min", "low": cc.decimal_text(rev["quantity_low"]),
                     "high": cc.decimal_text(rev["quantity_high"])},
        "source_classification": rev["source_classification"], "source_gate_sha256": rev["source_gate_sha256"],
        "assumption_revision_ids": [],
        "missing_assumptions": ["cold_exposure_rule", "cold_stock_quantity", "cold_stock_unit_value"]})


def assert_common(built) -> None:
    """Every revision is unpriced, server-timed inside the worker interval, scoped to the chamber room, and cites
    only this Site's accepted evidence; every work item has exactly one SUCCEEDED attempt with its exact IDs."""
    lo, hi = built.interval
    room = chamber_room(built)
    generators = {r["id"] for r in rows(built, "SELECT id FROM asset WHERE site_id = :s AND asset_code = 'generator-1'")}
    for rev in consequences(built):
        assert (rev["amount_low"], rev["amount_high"], rev["currency"]) == (None, None, None)
        assert lo <= rev["created_at"] <= hi
        assert rev["room_asset_id"] == room and rev["room_asset_id"] not in generators
        assert rev["overlap_group"] == cc.overlap_group(built.tenant_id, built.site_id, rev["window_start"],
                                                        rev["window_end"], room)
        assert (rev["kind"], rev["model_id"], rev["assumption_revision_ids"]) == (
            "PRODUCT_EXPOSURE", "cold-exposure/1", [])
        assert rev["consequence_basis_sha256"] == expected_basis_sha(built, rev)
        cited = links(built, rev["id"])
        assert cited and all(lo <= x["created_at"] <= hi for x in cited)
        accepted = {r["id"] for r in rows(built, "SELECT id FROM accepted_evidence WHERE site_id = :s")}
        assert {x["evidence_id"] for x in cited} <= accepted  # exact accepted IDs, no private world keys
        finding_cited = {r["evidence_id"] for r in rows(
            built, "SELECT evidence_id FROM finding_revision_evidence WHERE finding_revision_id = :r",
            r=rev["finding_revision_id"])}
        episode_cited = {(r["evidence_id"], r["use"]) for r in rows(
            built, "SELECT evidence_id, use FROM cold_episode_evidence WHERE episode_revision_id = :r",
            r=rev["episode_revision_id"])}
        assert {(x["evidence_id"], x["use"]) for x in cited} == episode_cited | {(e, "SUPPORT") for e in finding_cited}
    attempts = rows(built, "SELECT w.id, a.outcome, a.consequence_revision_ids, a.finished_at FROM "
                           "cold_consequence_work w JOIN cold_consequence_work_attempt a ON a.work_id = w.id "
                           "WHERE w.site_id = :s ORDER BY w.id, a.attempt_no")
    work = rows(built, "SELECT id FROM cold_consequence_work WHERE site_id = :s")
    assert sorted(str(a["id"]) for a in attempts) == sorted(str(w["id"]) for w in work)
    assert all(a["outcome"] == "SUCCEEDED" and lo <= a["finished_at"] <= hi for a in attempts)
    ids = {str(r["id"]) for r in consequences(built)}
    assert {i for a in attempts for i in a["consequence_revision_ids"]} == ids


def exposure_findings(built) -> list:
    return rows(built, "SELECT r.id, r.finding_id, r.claim, r.lifecycle FROM finding_revision r JOIN finding f "
                       "ON f.id = r.finding_id WHERE r.site_id = :s AND f.mechanism = 'COLD_EXCURSION' "
                       "ORDER BY r.revision_no")


@needs_db
@pytest.mark.parametrize("case", CASES if URL else [])
def test_six_replays_consequence_states(chain, case) -> None:  # noqa: F811
    built = opened(case, chain)
    run(built)
    causes = {w["cause"] for w in rows(built, "SELECT cause FROM cold_consequence_work WHERE site_id = :s")}
    assert causes >= {"EPISODE_REVISION_APPENDED"}, causes  # every replay has at least its start-response episode
    drain(built)
    assert_common(built)
    revs = consequences(built)
    if case in ("normal", "missing-probe"):
        # No warranted excursion Finding: no exposure row, and no zero row stands for unknown.
        assert exposure_findings(built) == [] and revs == []
        return
    if case == "contradictory":
        # The contradiction is in the start chain: no observed failure, so no start Finding and no repair row; the
        # sound room excursion keeps its single unpriced exposure (no priced amount anywhere).
        assert not rows(built, "SELECT 1 FROM finding f WHERE f.site_id = :s AND f.mechanism = 'COLD_START_FAILURE'")
    # excursion, backup-failed, late-reading (first cutoff), contradictory: one open excursion, counted once per
    # overlap group.
    [f] = exposure_findings(built)
    [rev] = revs
    [episode] = rows(built, "SELECT degree_minutes_low, degree_minutes_high FROM cold_episode_revision WHERE id = :r",
                     r=f["claim"]["episode_revision_id"])
    assert str(rev["finding_revision_id"]) == str(f["id"])
    assert str(rev["episode_revision_id"]) == f["claim"]["episode_revision_id"]
    assert (rev["state"], rev["reason"], rev["quantity_unit"]) == ("UNPRICED", cc.REASON_UNPRICED, "degC_min")
    # Copied exactly from the W2-03 episode revision's degree-minute bounds, never integrated or inferred.
    assert (rev["quantity_low"], rev["quantity_high"]) == (episode["degree_minutes_low"],
                                                          episode["degree_minutes_high"])
    assert rev["quantity_low"] > 0
    # Q4: a null upper bound carries the named open-upper limit; a proved upper bound carries none.
    assert rev["limitation"] == (None if rev["quantity_high"] is not None else "OPEN_EPISODE_UPPER_UNKNOWN")
    assert (rev["revision_no"], rev["prior_revision_id"]) == (1, None)
    assert rev["source_classification"] == "REGISTERED_SIMULATION"
    assert len({r["overlap_group"] for r in revs}) == 1
    if case == "backup-failed":
        # The start-failure Finding shares the room/window but carries no counted exposure row (W2-04 emits none).
        failure = rows(built, "SELECT r.id FROM finding_revision r JOIN finding f ON f.id = r.finding_id "
                              "WHERE r.site_id = :s AND f.mechanism = 'COLD_START_FAILURE'")
        assert failure and not rows(built, "SELECT 1 FROM cold_consequence_revision WHERE finding_revision_id = "
                                           "ANY(:ids)", ids=[x["id"] for x in failure])
        assert {(x["use"], x["reason"]) for x in links(built, rev["id"]) if x["reason"] == "DOOR_EVENT"} == {
            ("CONTEXT", "DOOR_EVENT")}


@needs_db
def test_late_reading_appends_a_new_basis_and_keeps_history(chain) -> None:  # noqa: F811
    built = opened("late-reading", chain)
    run(built)
    drain(built)
    [first] = consequences(built)
    built.advance_late()
    run(built)
    drain(built)
    assert_common_late = consequences(built)
    old, new = assert_common_late
    assert old == first  # immutable: the 20:05 revision is retained unchanged
    assert (new["revision_no"], new["prior_revision_id"]) == (2, first["id"])
    assert new["finding_revision_id"] != old["finding_revision_id"]
    assert new["assessment_revision_id"] != old["assessment_revision_id"]
    assert new["consequence_basis_sha256"] != old["consequence_basis_sha256"]
    assert new["overlap_group"] == old["overlap_group"]
    assert new["state"] == "UNPRICED" and new["amount_low"] is None
    assert new["consequence_basis_sha256"] == expected_basis_sha(built, new)
    assert Decimal(new["quantity_low"]) >= 0


# --- pure derivation (no database) ---------------------------------------------------------------------------

T, S = "00000000-0000-4000-8000-0000000000a1", "00000000-0000-4000-8000-0000000000b2"
E1, E2 = "00000000-0000-4000-8000-0000000000e1", "00000000-0000-4000-8000-0000000000e2"
WS, WE = datetime(2026, 10, 6, 19, 0, tzinfo=timezone.utc), datetime(2026, 10, 6, 20, 5, tzinfo=timezone.utc)
ROOM = "00000000-0000-4000-8000-00000000000f"


def bound(evidence_id: str, run: str = "run-1") -> LinkRow:
    commitment = (T, S, "gw", "src", "batch-x", "h" * 64)
    return LinkRow(requested_id=evidence_id, in_scope=True, in_tenant_elsewhere=False, batch_id="b1",
                   evidence_gateway_source=("gw", "src"), batch=commitment, link_publication_id="p1",
                   link=commitment, publication=commitment, source_class="REGISTERED_SIMULATION",
                   run_id=run, run_identity_sha256="r" * 64)


def basis(**over) -> "cc.ColdBasis":
    doc = dict(
        tenant_id=T, site_id=S, finding_revision_id="f-rev", finding_id="f", finding_lifecycle="SUPPORTED",
        finding_basis_sha256="a" * 64, finding_assessment_revision_id="a-rev",
        claim={"kind": "EXCURSION", "episode_id": "ep", "episode_revision_id": "ep-rev"},
        episode_revision_id="ep-rev", episode_id="ep", episode_kind="EXCURSION",
        episode_assessment_revision_id="a-rev", episode_basis_sha256="b" * 64, claim_level="BOUNDED",
        degree_minutes_low=Decimal("19.0"), degree_minutes_high=Decimal("23"), coverage=Decimal("1.0000"),
        assessment_revision_id="a-rev", assessment_basis_sha256="c" * 64, window_start=WS, window_end=WE,
        known_at=WE, room_asset_id=ROOM,
        evidence=(cc.EvidenceUse(E1, "SUPPORT"), cc.EvidenceUse(E2, "CONTEXT", "DOOR_EVENT")),
        link_rows=(bound(E1), bound(E2)))
    doc.update(over)
    return cc.ColdBasis(**doc)


WORK = {"cause": "FINDING_REVISION_APPENDED", "finding_revision_id": "f-rev", "episode_revision_id": None,
        "window_start": WS, "window_end": WE, "room_asset_id": ROOM}


def test_sound_bounds_are_copied_unpriced() -> None:
    out = cc.derive(basis())
    assert (out.state, out.reason, out.limitation) == ("UNPRICED", cc.REASON_UNPRICED, None)
    assert (out.quantity_low, out.quantity_high, out.quantity_unit) == ("19", "23", "degC_min")
    assert out.source_classification == "REGISTERED_SIMULATION" and out.assumption_revision_ids == ()
    assert out.overlap_group == "cold:" + cc.sha256_canonical([T, S, "2026-10-06T19:00:00Z", "2026-10-06T20:05:00Z",
                                                               ROOM])


def test_open_upper_keeps_lower_bound_with_named_limit() -> None:  # Q4
    out = cc.derive(basis(degree_minutes_high=None))
    assert (out.state, out.quantity_low, out.quantity_high, out.limitation) == (
        "UNPRICED", "19", None, cc.LIMIT_OPEN_UPPER)


@pytest.mark.parametrize("over, limit", [
    ({"claim_level": "CONTRADICTORY"}, "CONTRADICTORY_EVIDENCE"),
    ({"claim_level": "POSSIBLE"}, "CLAIM_LEVEL_POSSIBLE"),
    ({"coverage": Decimal("0.5385")}, "COVERAGE_INCOMPLETE"),
    ({"degree_minutes_low": None, "degree_minutes_high": None}, "EXPOSURE_LOWER_BOUND_UNKNOWN"),
])
def test_unproved_technical_claims_are_withheld_with_null_quantity(over, limit) -> None:
    out = cc.derive(basis(**over))
    assert (out.state, out.reason, out.quantity_low, out.quantity_high) == (
        "WITHHELD", cc.REASON_TECHNICAL_WITHHELD, None, None)
    assert limit in out.limitation.split("; ")


def test_mixed_or_unknown_source_withholds_money() -> None:
    mixed = cc.derive(basis(link_rows=(bound(E1, "run-1"), bound(E2, "run-2"))))
    unknown = cc.derive(basis(link_rows=(bound(E1),)))  # E2 has no link row: not found
    assert (mixed.state, mixed.reason, mixed.source_classification) == ("WITHHELD", "SOURCE_GATE_WITHHELD", "MIXED")
    assert (unknown.state, unknown.source_classification) == ("WITHHELD", "UNKNOWN")
    assert mixed.limitation == "SOURCE_CLASS_MIXED" and mixed.quantity_low == "19"
    assert mixed.source_gate_sha256 != cc.derive(basis()).source_gate_sha256


@pytest.mark.parametrize("over", [{"finding_lifecycle": "UNCONFIRMED"}, {"finding_lifecycle": "NO_LONGER_SUPPORTED"},
                                  {"claim": {"kind": "START_RESPONSE", "episode_id": "ep",
                                             "episode_revision_id": "ep-rev"}, "episode_kind": "START_RESPONSE"}])
def test_only_a_warranted_excursion_gets_an_exposure(over) -> None:
    assert cc.derive(basis(**over)) is None


def test_basis_hash_tracks_cutoff_ids_and_evidence() -> None:
    base = cc.derive(basis()).consequence_basis_sha256
    assert cc.derive(basis()).consequence_basis_sha256 == base  # deterministic
    for over in ({"known_at": datetime(2026, 10, 6, 20, 10, tzinfo=timezone.utc)},
                 {"assessment_revision_id": "a2", "finding_assessment_revision_id": "a2",
                  "episode_assessment_revision_id": "a2"},
                 {"evidence": (cc.EvidenceUse(E1, "SUPPORT"), cc.EvidenceUse(E2, "EXCLUDED", "DOOR_EVENT"))}):
        assert cc.derive(basis(**over)).consequence_basis_sha256 != base


@pytest.mark.parametrize("over, work", [
    ({"episode_revision_id": None}, {}),
    ({"claim": {"kind": "EXCURSION", "episode_id": "other", "episode_revision_id": "ep-rev"}}, {}),
    ({"claim": {"kind": "START_RESPONSE", "episode_id": "ep", "episode_revision_id": "ep-rev"}}, {}),
    ({"episode_assessment_revision_id": "elsewhere"}, {}),
    ({"assessment_revision_id": None}, {}),
    ({}, {"window_end": datetime(2026, 10, 6, 20, 10, tzinfo=timezone.utc)}),
    ({}, {"room_asset_id": "00000000-0000-4000-8000-000000000999"}),
    ({}, {"finding_revision_id": "another"}),
    ({}, {"cause": "EPISODE_REVISION_APPENDED", "finding_revision_id": None, "episode_revision_id": "another"}),
])
def test_unpaired_basis_is_refused_as_mismatch(over, work) -> None:
    with pytest.raises(cc.ColdBasisMismatch) as refused:
        cc.check_basis(basis(**over), {**WORK, **work})
    assert refused.value.code == "COLD_BASIS_MISMATCH"
    cc.check_basis(basis(), WORK)  # the paired basis passes


def test_merged_evidence_is_one_row_per_id_and_use() -> None:
    merged = cc.merged_evidence([cc.EvidenceUse(E2, "CONTEXT", "DOOR_EVENT"), cc.EvidenceUse(E1, "SUPPORT")],
                                [E1, E2])
    assert merged == (cc.EvidenceUse(E1, "SUPPORT"), cc.EvidenceUse(E2, "SUPPORT"),
                      cc.EvidenceUse(E2, "CONTEXT", "DOOR_EVENT"))


def test_selected_instant_and_decimal_text() -> None:
    assert cc.selected_instant(WS) == "2026-10-06T19:00:00Z"
    assert cc.selected_instant(WS.replace(microsecond=1500)) == "2026-10-06T19:00:00.001500Z"
    assert [cc.decimal_text(Decimal(x)) for x in ("45.0000", "4.5E+1", "0.000", "18.50")] == ["45", "45", "0", "18.5"]
