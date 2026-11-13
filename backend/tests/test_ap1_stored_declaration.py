"""AP-1 (D-SR.75, D-SR.77): `/api/sites/{id}/analytics` for a stored Site. No DB: a fake store feeds
`stored_site_declaration`; the PostgreSQL path is `test_ap1_stored_declaration_postgres.py`.

Unit: the fail-closed role map, configured capability never read as observed, Load per bound feeder, the
dispatch-3.2 coverage adapter, SR-12b's four range edges through the stored view. Route: stored 200 in the T028
shape, legacy unchanged, closed gate 409, cold/EV `analytics: []`, store down 503. Consistency: the panel's missing
roles equal the claim-limit section's gaps for the same stored revision.
"""

from __future__ import annotations

import dataclasses
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from assetops_backend.analytics import dispatch_v3
from assetops_backend.analytics.assessment_inputs import CONTROL_BATTERY_RESERVE, CONTROL_MINIMUM_RUNTIME
from assetops_backend.analytics.claim_limit_read import GAP_CODES, GEN, _reasons, role_coverage
from assetops_backend.analytics.declaration import DISPATCH, EvidenceRequirement, in_window
from assetops_backend.analytics.ports import AssessmentStoreUnavailable
from assetops_backend.analytics.stored_declaration import (
    COVERAGE_ROLES,
    ROLE_OF_REQUIREMENT,
    UnsupportedModel,
    stored_requirements,
    stored_site_declaration,
    v3_assessment_view,
)
from assetops_backend.analytics_api import build_analytics_router
from assetops_backend.sites.ports import SiteAwaitingMigration

T0 = datetime(2026, 10, 8, 8, 0, tzinfo=timezone.utc)
STEP = timedelta(minutes=5)
LOAD, PV, DIS, SOC = dispatch_v3.LOAD, dispatch_v3.PV_AVAILABLE, dispatch_v3.DISCHARGE, dispatch_v3.SOC


def _z(t: datetime) -> str:
    return t.strftime("%Y-%m-%dT%H:%M:%SZ")


def seg(i: int, *, observed: bool = True, missing: tuple[str, ...] = (), cls: str = "CANDIDATE_AVOIDABLE") -> dict:
    return {"start": _z(T0 + i * STEP), "end": _z(T0 + (i + 1) * STEP), "minutes": "5", "observed": observed,
            "classification": cls if observed else "INDETERMINATE", "reasons": ["PV available alone"],
            "missing": sorted(missing), "evidence_ids": []}


def revision(*segments: dict, model: str = dispatch_v3.MODEL_VERSION, first_on=None, last_on=None) -> dict:
    return {"id": uuid4(), "model_version": model, "claim_level": "CANDIDATE_AVOIDABLE",
            "window_start": T0.replace(hour=0), "window_end": T0.replace(hour=0) + timedelta(days=1),
            "result": {"segments": list(segments), "limitations": [],
                       "interval": {"first_on": first_on or (segments[0]["start"] if segments else None),
                                    "last_on": last_on or (segments[-1]["end"] if segments else None)}}}


def miss(role: str, problem: str = "MISSING") -> str:
    return dispatch_v3._missing(role, problem)


COVERED_REV = revision(seg(0), seg(1), seg(2))
PCS_GAP_REV = revision(seg(0), seg(1, missing=(miss(DIS),), cls="INDETERMINATE"), seg(2))
UNOBSERVED_REV = revision(seg(0), seg(1, observed=False, missing=("generator state not observed",)), seg(2))
UNKNOWN_TEXT_REV = revision(seg(0, missing=(f"{dispatch_v3.LABELS[PV]}: some new problem wording",)), seg(1))
POOR_CONFLICT_REV = revision(seg(0, missing=(miss(SOC, "NOT_GOOD"),)), seg(1, missing=(miss(PV, "CONFLICTING"),)))

ALL_BOUND = [
    {"role": dispatch_v3.GEN_STATE, "asset_id": None, "device_id": "generator-controller", "signal_id": "status",
     "last_source_time": T0},
    {"role": dispatch_v3.GEN_POWER, "asset_id": None, "device_id": "generator-controller", "signal_id": "ac-power",
     "last_source_time": T0},
    {"role": LOAD, "asset_id": uuid4(), "device_id": "clinic-meter", "signal_id": "active-power", "last_source_time": T0},
    {"role": LOAD, "asset_id": uuid4(), "device_id": "mill-meter", "signal_id": "active-power", "last_source_time": T0},
    {"role": PV, "asset_id": None, "device_id": "pv-inverter-controller", "signal_id": "available-power",
     "last_source_time": T0},
    {"role": SOC, "asset_id": None, "device_id": "battery-pcs-controller", "signal_id": "state-of-charge",
     "last_source_time": T0},
    {"role": DIS, "asset_id": None, "device_id": "battery-pcs-controller", "signal_id": "discharge-capability",
     "last_source_time": T0},
]


class FakeStore:
    def __init__(self, site_type="MINIGRID", presence=ALL_BOUND, controls=frozenset({CONTROL_BATTERY_RESERVE}),
                 revisions=(), down=False):
        self.site_type, self.presence, self.controls, self.revisions, self.down = (
            site_type, list(presence), set(controls), list(revisions), down)
        self.reads: list[str] = []
        self.windows: list[Any] = []

    def read_snapshot(self, work):
        if self.down:
            raise AssessmentStoreUnavailable("The assessment store failed: test")
        return work(object())

    def site_type_on(self, c, t, s):
        return self.site_type

    def role_presence(self, c, t, s, roles):
        self.reads.append("presence")
        return [p for p in self.presence if p["role"] in roles]

    def foundation_controls_on(self, c, t, s):
        self.reads.append("controls")
        return self.controls

    def selected_intervals_on(self, c, t, s, analytic_id, domain, bracket, window=None):
        self.reads.append("intervals")
        self.windows.append(window)
        return [{**r, "scope": "INTERVAL"} for r in self.revisions]


def declare(store, window=None, gate=None):
    return stored_site_declaration(store, uuid4(), uuid4(), "KOBO-001", window, gate=gate)


# --- unit: the role map ------------------------------------------------------------------------------------------

def test_every_dispatch_requirement_maps_or_fails_closed():
    labels = {r.role for r in (*DISPATCH.required_evidence, *DISPATCH.optional_evidence)}
    assert labels <= set(ROLE_OF_REQUIREMENT), labels - set(ROLE_OF_REQUIREMENT)
    mystery = dataclasses.replace(DISPATCH, required_evidence=(
        *DISPATCH.required_evidence, EvidenceRequirement("x-device", "x-signal", "MEASUREMENT", "Mystery input")))
    everything = [{**p, "role": r} for p in ALL_BOUND[:1] for r in {*dispatch_v3.LABELS, "Mystery input"}]
    required, _ = stored_requirements(mystery, [*ALL_BOUND, *everything], set(ROLE_OF_REQUIREMENT.values()))
    (row,) = [r for r in required if r["role"] == "Mystery input"]
    assert row["available"] is False and (row["device_id"], row["signal_id"]) == (None, None)  # D-SR.78 Q2


def test_configured_capability_is_never_an_observed_reading():
    # Every control configured, no reading bound: only the policy rows are available.
    required, optional = stored_requirements(DISPATCH, [], {CONTROL_BATTERY_RESERVE, CONTROL_MINIMUM_RUNTIME})
    assert {r["role"] for r in required if r["available"]} == {"Reserve policy"}
    assert {r["role"] for r in optional if r["available"]} == {"Minimum runtime policy"}
    # A bound role with no GOOD accepted reading is not available either.
    silent = [{**p, "last_source_time": None} if p["role"] == DIS else p for p in ALL_BOUND]
    required, _ = stored_requirements(DISPATCH, silent, set())
    assert {r["role"]: r["available"] for r in required}["Battery capability"] is False
    assert {r["role"]: r["available"] for r in required}["Reserve policy"] is False


def test_each_bound_feeder_is_one_load_row_with_its_binding_ids():
    required, optional = stored_requirements(DISPATCH, ALL_BOUND, {CONTROL_BATTERY_RESERVE})
    loads = [r for r in required if r["role"] == "Load"]
    assert [(r["device_id"], r["signal_id"]) for r in loads] == [("clinic-meter", "active-power"),
                                                                  ("mill-meter", "active-power")]
    assert all(r["available"] and r["last_source_time"] == _z(T0) and r["usable_records"] is None for r in loads)
    # Stop threshold and operator overrides have no stored record kind: not observed.
    assert {r["role"]: r["available"] for r in optional} == {
        "Minimum runtime policy": False, "Stop threshold policy (context)": False, "Operator override": False}
    # An unbound role keeps the declaration's rows, not available.
    required, _ = stored_requirements(DISPATCH, [p for p in ALL_BOUND if p["role"] != LOAD], set())
    assert [r["available"] for r in required if r["role"] == "Load"] == [False, False, False]


def test_unbound_role_gives_null_ids_and_policy_rows_no_reference():
    # D-SR.78 Q2: on the stored path ids come only from a stored binding.
    required, optional = stored_requirements(DISPATCH, [p for p in ALL_BOUND if p["role"] != LOAD], {CONTROL_BATTERY_RESERVE})
    loads = [r for r in required if r["role"] == "Load"]
    assert loads and all(r["device_id"] is None and r["signal_id"] is None and r["unbound"] is True for r in loads)
    policy = [r for r in [*required, *optional] if r["role"].endswith("policy")]
    assert policy and all(r["device_id"] is None and r["signal_id"] is None and r["unbound"] is False for r in policy)
    bound = [r for r in required if r["role"] == "Battery capability"]
    assert bound and all(r["device_id"] is not None and r["unbound"] is False for r in bound)


# --- unit: the dispatch-3.2 coverage adapter ---------------------------------------------------------------------

def _inputs(view: dict) -> dict[str, tuple[int, int]]:
    return {row["input"]: (row["usable_segments"], row["evaluated_segments"]) for row in view["coverage"]["inputs"]}


def test_a_covered_revision_has_no_gap():
    view = v3_assessment_view(COVERED_REV)
    assert _inputs(view) == {r: (3, 3) for r in COVERAGE_ROLES}
    assert view["coverage"]["unobserved_generator_state"] == []
    assert view["assessed_window"] == {"start": _z(T0), "end": _z(T0 + 3 * STEP)}


def test_a_missing_pcs_span_is_one_unusable_segment_named_by_its_label():
    view = v3_assessment_view(PCS_GAP_REV)
    assert _inputs(view)[DIS] == (2, 3) and _inputs(view)[PV] == (3, 3)
    assert view["segments"][1]["missing"][0].startswith(dispatch_v3.LABELS[DIS])


def test_an_unobserved_generator_span_is_not_evaluated_and_counted_in_minutes():
    view = v3_assessment_view(UNOBSERVED_REV)
    assert _inputs(view) == {r: (2, 2) for r in COVERAGE_ROLES}
    assert view["coverage"]["unobserved_generator_state"] == [
        {"start": _z(T0 + STEP), "end": _z(T0 + 2 * STEP), "minutes": "5"}]


def test_unknown_problem_text_stays_not_covered():
    assert _inputs(v3_assessment_view(UNKNOWN_TEXT_REV))[PV] == (1, 2)


def test_another_model_is_refused():
    with pytest.raises(UnsupportedModel):
        v3_assessment_view(revision(seg(0), model="dispatch-3.1"))


def test_the_four_sr12b_range_edges_through_the_stored_view():
    view = v3_assessment_view(COVERED_REV)  # [08:00, 08:15)
    start, end = T0, T0 + 3 * STEP
    assert not in_window(view, end, end + timedelta(days=1))  # 1: ends exactly at `from`: before
    assert not in_window(view, start - timedelta(days=1), start)  # 2: starts at `to`: after
    instant = v3_assessment_view(revision(seg(0)))
    instant["assessed_window"]["end"] = instant["assessed_window"]["start"]
    assert in_window(instant, start, start + STEP)  # 3: a zero-length assessment at `from` is inside
    bare = v3_assessment_view(revision(first_on=_z(T0 - STEP), last_on=_z(T0)))  # no segments: observed bounds
    assert "assessed_window" not in bare and in_window(bare, T0, T0 + STEP)  # 4: last observed = from: inside


# --- the stored declaration --------------------------------------------------------------------------------------

def test_a_stored_minigrid_scores_the_selected_revisions_with_the_same_shape():
    store = FakeStore(revisions=[COVERED_REV, PCS_GAP_REV])
    body = declare(store)
    assert set(body) == {"site_id", "site_type", "statement", "analytics", "readiness_window"}
    (row,) = body["analytics"]
    assert row["analytic_id"] == "dispatch" and row["readiness"]["assessed_intervals"] == 2
    r = row["readiness"]
    assert r["level"] == "LIMITED"
    (gap,) = r["missing_evidence"]
    assert gap["kind"] == "COVERAGE_GAP" and gap["role"] == dispatch_v3.LABELS[DIS] and gap["limits_claim"]
    assert r["gaps"][0].startswith("Available battery output: no usable record for 1 of 3 assessed parts in 1 assessed period")
    assert all(p["plain_role"] for p in row["required_evidence"])


def test_full_when_every_input_is_evidenced_and_covered():
    r = declare(FakeStore(revisions=[COVERED_REV]))["analytics"][0]["readiness"]
    assert r["level"] == "FULL" and r["missing_evidence"] == []


def test_a_range_is_passed_to_the_store_and_applied_per_assessment():
    store = FakeStore(revisions=[COVERED_REV, PCS_GAP_REV])
    window = (T0 + timedelta(days=1), T0 + timedelta(days=2))
    body = declare(store, window)
    assert store.windows == [window]
    assert body["readiness_window"] == {"from": _z(window[0]), "to": _z(window[1])}
    assert body["analytics"][0]["readiness"]["assessed_intervals"] == 0


@pytest.mark.parametrize("site_type", ["COLDCHAIN", "EV_CHARGING"])
def test_cold_and_ev_answer_an_empty_list_without_the_gate_or_any_reading(site_type):
    def closed():
        raise AssertionError("the Dispatch gate is not asked for a Site with no declaration")

    store = FakeStore(site_type=site_type)
    body = declare(store, gate=closed)
    assert body["analytics"] == [] and body["site_type"] == site_type and store.reads == []


# --- consistency with the claim-limit section --------------------------------------------------------------------

_LABEL_ROLE = {dispatch_v3.LABELS[r]: r for r in COVERAGE_ROLES}


@pytest.mark.parametrize("rev", [COVERED_REV, PCS_GAP_REV, UNOBSERVED_REV, UNKNOWN_TEXT_REV, POOR_CONFLICT_REV],
                         ids=["covered", "pcs-gap", "unobserved", "unknown-text", "poor-conflict"])
def test_panel_missing_roles_equal_the_claim_limit_gaps_for_the_same_revision(rev):
    # The claim-limit section (`claim_limit_on` -> `reduce_day`) names a gap per role-tagged reason.
    coverage = role_coverage(rev["result"]["segments"], {}, str(rev["id"]))
    reasons = [r for r in _reasons(rev["result"], coverage, []) if r["code"] in GAP_CODES and r.get("role")]
    claim_roles = {r["role"] for r in reasons if r["code"] != "GENERATOR_UNOBSERVED"}
    claim_unobserved = any(r["code"] == "GENERATOR_UNOBSERVED" and r["role"] == GEN for r in reasons)
    body = declare(FakeStore(revisions=[rev]))
    gaps = [g for g in body["analytics"][0]["readiness"]["missing_evidence"] if g["kind"] == "COVERAGE_GAP"]
    panel_roles = {_LABEL_ROLE[g["role"]] for g in gaps if g["role"] != "Generator state"}
    assert panel_roles == claim_roles
    assert any(g["role"] == "Generator state" for g in gaps) == claim_unobserved


# --- route -------------------------------------------------------------------------------------------------------

class LegacySites:
    def get_site(self, site_id):
        raise SiteAwaitingMigration(f"Site {site_id} moved")


def app_client(store=None, *, gate_open=True, scoped=("KOBO-001",)):
    ids = {code: (code, uuid4(), uuid4()) for code in scoped}
    asked: list[str] = []

    def gate(code, t, s):
        asked.append(code)
        return gate_open, "test: no Performance comparison report"

    def stored(t, s, code, window, *, gate):
        return stored_site_declaration(store, t, s, code, window, gate=gate)

    app = FastAPI()
    app.include_router(build_analytics_router(None, None, LegacySites(), scope=ids.get, gate=gate,
                                              stored=None if store is None else stored))
    return TestClient(app), asked


def test_route_stored_minigrid_is_200_in_the_t028_shape():
    client, asked = app_client(FakeStore(revisions=[PCS_GAP_REV]))
    response = client.get("/api/sites/KOBO-001/analytics?from=2026-10-08T00%3A00%3A00Z&to=2026-10-09T00%3A00%3A00Z")
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["site_id"] == "KOBO-001" and asked == ["KOBO-001"]
    (row,) = body["analytics"]
    assert set(row) == {"analytic_id", "display_name", "site_types", "finding_type", "model_version", "claim_levels",
                        "required_evidence", "optional_evidence", "thresholds", "readiness"}
    assert row["readiness"]["assessed_intervals"] == 1 and body["readiness_window"]["from"] == "2026-10-08T00:00:00Z"


def test_route_legacy_code_keeps_the_file_path():
    client, asked = app_client(FakeStore())
    response = client.get("/api/sites/LEGACY-1/analytics")
    assert response.status_code == 409 and response.json()["detail"]["code"] == "AWAITING_EVIDENCE_MIGRATION"
    assert asked == []


def test_route_closed_gate_is_the_existing_409():
    client, _ = app_client(FakeStore(revisions=[COVERED_REV]), gate_open=False)
    response = client.get("/api/sites/KOBO-001/analytics")
    assert response.status_code == 409
    assert response.json()["detail"] == {"code": "AWAITING_EVIDENCE_MIGRATION",
                                         "message": "test: no Performance comparison report"}


def test_route_cold_site_is_an_empty_list_even_with_the_gate_closed():
    client, asked = app_client(FakeStore(site_type="COLDCHAIN"), gate_open=False)
    response = client.get("/api/sites/KOBO-001/analytics")
    assert response.status_code == 200 and response.json()["analytics"] == [] and asked == []


@pytest.mark.parametrize("store", [FakeStore(down=True), None], ids=["store-down", "no-database"])
def test_route_store_down_is_503(store):
    client, _ = app_client(store)
    response = client.get("/api/sites/KOBO-001/analytics")
    assert response.status_code == 503 and response.json()["detail"]["code"] == "ASSESSMENT_UNAVAILABLE"


def test_route_unsupported_model_is_422():
    client, _ = app_client(FakeStore(revisions=[revision(seg(0), model="dispatch-3.1")]))
    response = client.get("/api/sites/KOBO-001/analytics")
    assert response.status_code == 422 and response.json()["detail"]["code"] == "UNSUPPORTED_RULE_VERSION"


def test_route_bad_window_is_still_422_on_the_stored_branch():
    client, _ = app_client(FakeStore())
    assert client.get("/api/sites/KOBO-001/analytics?from=2026-10-08").json()["detail"]["code"] == "INVALID_WINDOW"


class _KeyErrorStore(FakeStore):
    def role_presence(self, c, t, s, roles):
        raise KeyError("role")


def test_route_missing_stored_site_is_404_but_a_key_error_is_never_site_not_found():
    """AP-1 L1 (D-SR.79): only `StoredSiteNotFound` maps to 404; a programming KeyError stays a 500."""
    client, _ = app_client(FakeStore(site_type=None))
    response = client.get("/api/sites/KOBO-001/analytics")
    assert response.status_code == 404 and response.json()["detail"]["code"] == "SITE_NOT_FOUND"
    failing = TestClient(app_client(_KeyErrorStore())[0].app, raise_server_exceptions=False)
    assert failing.get("/api/sites/KOBO-001/analytics").status_code == 500
