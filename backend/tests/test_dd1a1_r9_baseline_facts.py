"""DD1a1-R9: a baseline day re-selected onto a run with equal facts is `reselected`, not moved.

Unit level: `VerificationService._day_states` with fake ports (no database)."""
from __future__ import annotations

import copy
from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import UUID, uuid4

from assetops_backend.actions.verification import VerificationPorts, VerificationService

T, S = uuid4(), uuid4()
PINNED, CURRENT = uuid4(), uuid4()
LO = datetime(2026, 11, 4, 12, 0, tzinfo=timezone.utc)
HI = datetime(2026, 11, 4, 13, 0, tzinfo=timezone.utc)


def _interval(key: str, first_on: str, off_after: str, candidate: str = "40") -> dict:
    return {"scope": "INTERVAL", "id": uuid4(), "analytic_run_id": uuid4(), "assessment_key": key,
            "claim_level": "CANDIDATE", "evidence_ids": [str(uuid4())], "basis_sha256": uuid4().hex,
            "result": {"generator_asset_id": "gen-1", "claim_level": "CANDIDATE",
                       "interval": {"first_on": first_on, "last_on": off_after, "off_after": off_after},
                       "portions_minutes": {"candidate": candidate},
                       "segments": [{"start": first_on, "end": off_after, "classification": "CANDIDATE"}],
                       "limitations": []}}


def _revisions() -> list[dict]:
    return [{"scope": "WINDOW", "id": uuid4(), "assessment_key": "dispatch-3:window:2026-11-04",
             "claim_level": "WINDOW_COMPLETE", "result": {"cohort": {"reading_count": 100}}},
            _interval("k-in", "2026-11-04T12:10:00Z", "2026-11-04T12:50:00Z"),
            _interval("k-out", "2026-11-04T20:00:00Z", "2026-11-04T21:00:00Z")]


def _service(pinned: list[dict], current: list[dict], *, with_port: bool = True) -> VerificationService:
    runs = {PINNED: pinned, CURRENT: current}

    def day_status(t, s, day):
        return {"day": day.isoformat(), "s3_status": "CURRENT", "s3_reasons": [], "run_id": str(CURRENT),
                "s4_matched": True, "s4_match_deferred": False}

    ports = VerificationPorts(day_status=day_status,
                              run_assessments=(lambda t, s, r: copy.deepcopy(runs.get(UUID(str(r)))))
                              if with_port else None)
    actions = SimpleNamespace(store=None, clock=lambda: HI, verification_ports=ports)
    return VerificationService(actions)


def _state(service: VerificationService, window=(LO, HI)) -> dict:
    [state] = service._day_states(T, S, [{"day": "2026-11-04", "run_id": str(PINNED)}], require_s4=True,
                                  facts_window=window)
    return state


def test_equal_facts_with_a_different_run_id_is_reselected_not_moved() -> None:
    base = _revisions()
    current = copy.deepcopy(base)
    for r in current:  # new run identities, revision ids, evidence and the window summary change; facts do not
        r["id"], r["analytic_run_id"], r["basis_sha256"] = uuid4(), uuid4(), uuid4().hex
        r["evidence_ids"] = [str(uuid4())]
    current[0]["result"]["cohort"]["reading_count"] = 136
    state = _state(_service(base, current))
    assert state["moved"] == [] and state["current"] is True
    assert state["reselected"] == [{"pinned_run_id": str(PINNED), "current_run_id": str(CURRENT),
                                    "facts": "equal", "assessments": 1}]


def test_one_changed_baseline_value_is_moved() -> None:
    base = _revisions()
    current = copy.deepcopy(base)
    current[1]["result"]["portions_minutes"]["candidate"] = "41"
    state = _state(_service(base, current))
    assert state["moved"] == [f"selection moved from run {PINNED} to {CURRENT}"] and "reselected" not in state


def test_one_changed_baseline_interval_is_moved() -> None:
    base = _revisions()
    current = copy.deepcopy(base)
    current[1]["result"]["segments"][0]["end"] = "2026-11-04T12:55:00Z"
    assert _state(_service(base, current))["moved"]


def test_an_assessment_outside_the_baseline_window_does_not_count() -> None:
    base = _revisions()
    current = copy.deepcopy(base)
    current[2]["result"]["portions_minutes"]["candidate"] = "60"
    current[2]["claim_level"] = "NECESSARY"
    current.append(_interval("k-late", "2026-11-05T03:00:00Z", "2026-11-05T04:00:00Z"))
    state = _state(_service(base, current))
    assert state["moved"] == [] and state["reselected"][0]["assessments"] == 1


def test_a_new_interval_inside_the_window_is_moved() -> None:
    base = _revisions()
    current = copy.deepcopy(base) + [_interval("k-new", "2026-11-04T12:55:00Z", "2026-11-04T13:30:00Z")]
    assert _state(_service(base, current))["moved"]


def test_without_the_port_or_window_a_new_run_fails_closed_as_moved() -> None:
    base = _revisions()
    assert _state(_service(base, copy.deepcopy(base), with_port=False))["moved"]
    assert _state(_service(base, copy.deepcopy(base)), window=None)["moved"]
    assert _state(_service(None, copy.deepcopy(base)))["moved"]  # the pinned run cannot be read
