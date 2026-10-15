"""Pure precedence tests of the shared LR-01 money eligibility gate (`financials/money_eligibility.evaluate`).

Packet outcome table and plan re-review N3: pending S3/S4 work or staleness wins; once settled a material
unresolved generator-series refusal withholds; ELIGIBLE passes this gate only.
"""

from __future__ import annotations

from datetime import date, datetime, timezone

from assetops_backend.analytics.dispatch_v3 import MODEL_VERSION
from assetops_backend.analytics.finding_episode import MATCHER_VERSION
from assetops_backend.financials.money_eligibility import (
    ELIGIBLE,
    PENDING_REASSESSMENT,
    WITHHELD_GENERATOR_SERIES,
    days_over,
    evaluate,
)

D = date(2026, 10, 24)
LATEST = {"id": "rev-3", "revision_no": 3, "episode_start": datetime(2026, 10, 24, 6, 5, tzinfo=timezone.utc),
          "episode_end": datetime(2026, 10, 24, 8, tzinfo=timezone.utc), "matcher_version": MATCHER_VERSION,
          "claim": {"end_reason": "OPEN_BOUND", "series_limits": []},
          "assessments": [{"assessment_revision_id": "win-24", "scope": "WINDOW"}]}


def day(d=D, *, status="CURRENT", wa="win-24", model=MODEL_VERSION, limits=(), jobs=(), matched=True, sel=True):
    read = {"status": status, "jobs": [{"id": j} for j in jobs], "window_assessment": {"id": wa} if wa else None,
            "selection": {"run_id": f"run-{d}", "model_version": model, "cohort": {"limits": list(limits)}}
            if sel else None}
    return {"day": d, "read": read, "match": {"matched": matched}}


def limit(asset="G1", start="2026-10-24T07:05:00Z", end="2026-10-24T08:00:00Z", role="generator_power"):
    return {"kind": "SEQUENCE_ORDER_INVERTED", "role": role, "asset_id": asset, "start": start, "end": end,
            "evidence_ids": ["ev-late"], "clock": "NO_ATTESTATION", "attestation_refs": []}


def state(days, latest=LATEST):
    return evaluate("f-1", latest, "G1", days)


def test_settled_with_no_refusal_is_eligible_and_names_its_lineage() -> None:
    out = state([day()])
    assert out["state"] == ELIGIBLE and out["pending_reasons"] == [] and out["series_limits"] == []
    assert out["windows"][0]["window_assessment_revision_id"] == "win-24"
    assert out["latest_finding_revision_id"] == "rev-3"


def test_n3_a_missing_selected_window_for_an_episode_day_is_pending() -> None:
    out = state([day(status="UNASSESSED", sel=False, wa=None)])
    assert out["state"] == PENDING_REASSESSMENT
    assert out["pending_reasons"][0].startswith("NO_SELECTED_WINDOW")


def test_an_unassessed_bracket_only_day_without_evidence_does_not_block() -> None:
    latest = {**LATEST, "episode_start": datetime(2026, 10, 24, 2, tzinfo=timezone.utc)}
    out = state([day(date(2026, 10, 23), status="UNASSESSED", sel=False, wa=None), day()], latest)
    assert out["state"] == ELIGIBLE


def test_pending_wins_over_withheld() -> None:
    for d in (day(status="STALE", limits=[limit()]), day(jobs=["j1"], limits=[limit()]),
              day(matched=False, limits=[limit()]), day(model="dispatch-3.1", limits=[limit()]),
              day(wa="win-24-new", limits=[limit()])):
        assert state([d])["state"] == PENDING_REASSESSMENT, d
    assert state([day()], {**LATEST, "matcher_version": "finding-episode-2"})["state"] == PENDING_REASSESSMENT


def test_settled_material_refusal_withholds_and_others_do_not() -> None:
    assert state([day(limits=[limit()])])["state"] == WITHHELD_GENERATOR_SERIES
    assert state([day()], {**LATEST, "claim": {"end_reason": "SERIES_LIMIT", "series_limits": [limit()]}})[
        "state"] == WITHHELD_GENERATOR_SERIES
    assert state([day(limits=[limit(asset="G2")])])["state"] == ELIGIBLE
    assert state([day(limits=[limit(role="pv_available_power")])])["state"] == ELIGIBLE
    far = limit(start="2026-10-24T20:00:00Z", end="2026-10-24T21:00:00Z")  # beyond the 6 h bracket
    assert state([day(limits=[far])])["state"] == ELIGIBLE


def test_days_cover_the_bracket() -> None:
    assert days_over(datetime(2026, 10, 23, 23, tzinfo=timezone.utc),
                     datetime(2026, 10, 25, 1, tzinfo=timezone.utc)) == [date(2026, 10, 23), D, date(2026, 10, 25)]
