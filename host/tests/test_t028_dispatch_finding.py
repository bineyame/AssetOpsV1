"""T028 phase 1: the dispatch Finding through normal ingestion, real kernel and gateway.

Each world is executed to the end, staged, committed and released through
`IngestionService.ingest`; the assessment runs on the completed batch and is
read back over the analytics routes. Nothing here hands the analytic a world,
a stage or a scenario: it reads the accepted records only (AC9, AC14).

Proof rows: prolonged-runtime interval with adequate capability (candidate),
healthy reference (no false candidate), PCS capability missing for part of the
interval (segmented claim and named gap), override absent (limitation
explicit), delayed evidence (source-time placement), rerun (no new revision).
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from assetops_backend.analytics.adapters.json_assessment_store import JsonAssessmentStore
from assetops_backend.config import FeatureFlags
from assetops_backend.evidence.adapters.json_evidence_store import JsonEvidenceStore
from assetops_backend.main import create_app
from assetops_backend.runs.adapters.json_commit_store import JsonCommitStore
from fixtures import FakeRuns, FakeSites
from kobo import KOBO_SITE_ID, kobo_draft, kobo_site
from lab_execution import HostLabExecution, YamlExecutionArtifacts
from source_stages import JsonSourceStages

PROLONGED = dict(start_time="2026-09-22T03:00:00Z", end_time="2026-09-22T11:00:00Z")
EVENING = dict(start_time="2026-09-22T09:00:00Z", end_time="2026-09-22T17:00:00Z")
ENABLED = FeatureFlags(simulator_lab_enabled=True)
DISABLED = FeatureFlags(simulator_lab_enabled=False)
SITE = f"/api/sites/{KOBO_SITE_ID}"


class World:
    """One executed Kobo Draft, committed and released into its own stores."""

    def __init__(self, root: Path, scenario: str, window: dict[str, str]) -> None:
        self.root = root
        self.run = kobo_draft(
            scenario, model_profile="mini-grid", model_profile_version=3,
            timestep_minutes=5, publication_profile_version=5, **window,
        )
        self.runs = FakeRuns()
        self.runs.create_run(self.run)
        execution = self.execution()
        execution.start(self.run)
        execution.run_to_end(self.run)
        response = self.client().post(f"/api/simulator-lab/runs/{self.run.run_id}/commit")
        assert response.status_code == 200, response.text

    def execution(self) -> HostLabExecution:
        return HostLabExecution(
            artifacts=YamlExecutionArtifacts(self.root / "executions"),
            stages=JsonSourceStages(self.root / "stages"),
        )

    def client(self, flags: FeatureFlags = ENABLED) -> TestClient:
        return TestClient(create_app(
            flags,
            site_repository=FakeSites((kobo_site(),)),
            run_repository=self.runs,
            execution=self.execution() if flags.simulator_lab_enabled else None,
            evidence_store=JsonEvidenceStore(self.root / "evidence"),
            commit_store=JsonCommitStore(self.root / "commits"),
            assessment_store=JsonAssessmentStore(self.root / "assessments"),
            clock=lambda: "2026-09-29T12:00:00Z",
        ))


@pytest.fixture(scope="module")
def prolonged(tmp_path_factory):
    return World(tmp_path_factory.mktemp("t028-prolonged"), "kobo-mini-grid-prolonged", PROLONGED)


@pytest.fixture(scope="module")
def healthy(tmp_path_factory):
    return World(tmp_path_factory.mktemp("t028-healthy"), "kobo-mini-grid-evening", EVENING)


@pytest.fixture(scope="module")
def degraded(tmp_path_factory):
    return World(tmp_path_factory.mktemp("t028-degraded"), "kobo-mini-grid-degraded-evidence", PROLONGED)


def read(world: World, path: str, flags: FeatureFlags = DISABLED) -> dict:
    response = world.client(flags).get(f"{SITE}{path}")
    assert response.status_code == 200, response.text
    return response.json()


def only(world: World) -> dict:
    assessments = read(world, "/dispatch")["assessments"]
    assert len(assessments) == 1, [a["summary"] for a in assessments]
    return assessments[0]


def segments(assessment: dict, level: str) -> list[dict]:
    return [s for s in assessment["assessment"]["segments"] if s["classification"] == level]


def dispatch_card(world: World) -> dict:
    cards = read(world, "/overview")["cards"]
    assert [c["domain_id"] for c in cards] == ["Service", "Dispatch", "Battery", "Fuel", "Renewable"]
    for card in cards:
        if card["domain_id"] != "Dispatch":
            assert card["assessment"]["status"] == "NO_ASSESSMENT", card["domain_id"]
    return next(c for c in cards if c["domain_id"] == "Dispatch")["assessment"]


# --- prolonged runtime: a candidate with reasons (AC4, AC9, AC10) ------------


def test_prolonged_runtime_is_a_bounded_candidate_with_its_constraints(prolonged) -> None:
    a = only(prolonged)
    body = a["assessment"]
    assert body["claim_level"] == "CANDIDATE_AVOIDABLE" and body["raises_finding"] is True
    candidate = body["portions_hours"]["CANDIDATE_AVOIDABLE"]
    assert float(candidate["low"]) >= 3 and float(candidate["high"]) >= float(candidate["low"])
    # The start is Necessary for named reasons, not folded into the candidate (AC4/AC5).
    assert {"MINIMUM_RUNTIME", "BATTERY_AT_RESERVE"} <= set(body["binding_constraints"])
    assert all(s["binding_constraint"] for s in segments(a, "NECESSARY"))
    assert body["fuel"]["status"] == "BOUNDED" and body["fuel"]["basis"] == "modelled"
    assert float(body["fuel"]["low_litres"]) < float(body["fuel"]["high_litres"])
    assert body["confidence"]["level"] in {"HIGH", "MEDIUM", "LOW"} and body["confidence"]["basis"]


def test_candidate_evidence_links_are_accepted_records_and_never_observed_pv(prolonged) -> None:
    a = only(prolonged)
    accepted = {
        r["message_id"]: (r["device_id"], r["signal_id"])
        for r in read(prolonged, "/evidence/records?limit=1000")["records"]
    }
    for segment in segments(a, "CANDIDATE_AVOIDABLE"):
        signals = {(e["device_id"], e["signal_id"]) for e in segment["evidence"]}
        assert ("pv-inverter-controller", "available-power") in signals
        assert ("battery-pcs-controller", "discharge-capability") in signals
        # AC3: observed PV output never stands in for available PV capability.
        assert ("pv-inverter-controller", "ac-power") not in signals
        for link in segment["evidence"]:
            assert accepted[link["message_id"]] == (link["device_id"], link["signal_id"])


def test_override_absence_is_a_stated_limitation_not_proof(prolonged) -> None:
    body = only(prolonged)["assessment"]
    absent = next(x for x in body["alternatives"] if x["id"] == "UNOBSERVED_OVERRIDE")
    assert absent["status"] == "NOT_EXCLUDED" and "not proof" in absent["statement"]
    assert absent["statement"] in body["claim_limits"]
    assert {x["id"] for x in body["alternatives"]} >= {
        "POLICY_CONSTRAINT", "PCS_CAPABILITY_UNAVAILABLE", "UNMEASURED_PV_VARIATION"
    }


def test_overview_dispatch_card_links_the_finding_not_a_recomputation(prolonged) -> None:
    a = only(prolonged)
    card = dispatch_card(prolonged)
    assert card["status"] == "CANDIDATE_AVOIDABLE" and card["capability_id"] == "dispatch"
    assert card["lead_assessment_id"] == a["assessment_id"]
    assert card["reason"].startswith(a["summary"])
    findings = read(prolonged, "/findings")["findings"]
    assert [f["finding_id"] for f in findings] == [a["assessment_id"]]
    assert read(prolonged, "/overview")["findings"] == findings


def test_the_global_findings_index_lists_the_same_finding_with_its_site(prolonged, healthy) -> None:
    """T028 phase 2 AC21: the Findings rail root's index is the per-Site read
    repeated with the Site named, never a second assessment."""
    a = only(prolonged)
    response = prolonged.client(DISABLED).get("/api/findings")
    assert response.status_code == 200, response.text
    rows = response.json()["findings"]
    assert [r["finding_id"] for r in rows] == [a["assessment_id"]]
    site_rows = read(prolonged, "/findings")["findings"]
    assert {k: v for k, v in rows[0].items() if k not in {"site_id", "site_display_name", "site_type"}} == site_rows[0]
    assert rows[0]["site_id"] == SITE.rsplit("/", 1)[-1]
    # A Necessary-only Site contributes no row (owner ruling 2026-10-03).
    assert healthy.client(DISABLED).get("/api/findings").json()["findings"] == []


def test_rerun_on_the_same_evidence_adds_no_revision(prolonged) -> None:
    a = only(prolonged)
    app_client = prolonged.client()
    again = app_client.post(f"/api/simulator-lab/runs/{prolonged.run.run_id}/commit")
    assert again.status_code == 200
    app_client.app.state.assessments.assess_site(KOBO_SITE_ID)
    history = read(prolonged, f"/assessments/{a['assessment_id']}/revisions")
    assert [r["revision"] for r in history["revisions"]] == [1]
    assert len(read(prolonged, "/findings")["findings"]) == 1


def test_removing_private_artifacts_leaves_the_same_assessment(prolonged, tmp_path) -> None:
    """AC14: rebuild from accepted evidence alone, Lab gated off, no executions."""
    before = only(prolonged)["assessment"]
    shutil.copytree(prolonged.root / "evidence", tmp_path / "evidence")
    client = TestClient(create_app(
        DISABLED,
        site_repository=FakeSites((kobo_site(),)),
        evidence_store=JsonEvidenceStore(tmp_path / "evidence"),
        assessment_store=JsonAssessmentStore(tmp_path / "assessments"),
        clock=lambda: "2030-01-01T00:00:00Z",
    ))
    after = client.get(f"{SITE}/dispatch").json()["assessments"]
    assert [x["assessment"] for x in after] == [before]


# --- healthy reference: no false candidate (AC9) --------------------------------


def test_healthy_reference_raises_no_finding(healthy) -> None:
    assessments = read(healthy, "/dispatch")["assessments"]
    assert assessments, "the healthy world runs its generator; the test must see it"
    assert {a["claim_level"] for a in assessments} == {"NECESSARY"}
    for a in assessments:
        assert all(s["binding_constraint"] for s in a["assessment"]["segments"])
    assert read(healthy, "/findings")["findings"] == []
    card = dispatch_card(healthy)
    assert card["status"] == "NECESSARY"
    assert read(healthy, "/overview")["findings"] == []


# --- degraded evidence: segmented claim, named gap, delayed record (AC5-AC7) ---


def test_missing_pcs_capability_segments_the_claim_and_names_the_gap(degraded) -> None:
    a = only(degraded)
    body = a["assessment"]
    assert body["claim_level"] == "CANDIDATE_AVOIDABLE"
    indeterminate = segments(a, "INDETERMINATE")
    assert indeterminate and float(body["portions_hours"]["INDETERMINATE"]["low"]) > 0
    assert all(
        any("Battery discharge capability" in m for m in s["missing"]) for s in indeterminate
    )
    # The weak portion is listed beside the candidate, not hidden in it (AC5).
    assert any("Indeterminate" in limit for limit in body["claim_limits"])
    row = next(r for r in body["coverage"]["inputs"] if r["input"] == "discharge_capability")
    assert row["usable_segments"] < row["evaluated_segments"] and row["gaps"]
    pcs = next(x for x in body["alternatives"] if x["id"] == "PCS_CAPABILITY_UNAVAILABLE")
    assert pcs["status"] == "NOT_EXCLUDED" and pcs["gaps"]
    assert body["confidence"]["level"] != "HIGH"


def test_delayed_soc_record_is_placed_at_its_source_time(degraded) -> None:
    body = only(degraded)["assessment"]
    at_seven = next(s for s in body["segments"] if s["end"] == "2026-09-22T07:00:00Z")
    soc = [e for e in at_seven["evidence"] if e["signal_id"] == "state-of-charge"
           and e["source_time"] == "2026-09-22T07:00:00Z"]
    assert soc, "the held 07:00 SOC sample describes 07:00"
    record = read(degraded, f"/evidence/records/{soc[0]['message_id']}")
    assert record["published_at"] > record["source_time"]


def test_a_stop_the_published_policy_cannot_explain_is_said_so(degraded) -> None:
    """The operator's override record is suppressed: the stop at about 60 % is
    below the published 90 % threshold, and the alternative says so instead of
    quoting 90 % as the effective policy (carried stop-60 question)."""
    body = only(degraded)["assessment"]
    policy = next(x for x in body["alternatives"] if x["id"] == "POLICY_CONSTRAINT")
    assert "90 %" in policy["statement"] and "does not explain this stop" in policy["statement"]



# --- changed accepted evidence through a second Commit (AC13, owner UI path) -----


def test_a_second_commit_that_fills_a_gap_revises_and_keeps_the_prior(tmp_path) -> None:
    """The phase 1 UI check's revision path. Commit the degraded-evidence recipe,
    then the prolonged recipe over the same window onto the same Site. Records at
    an already-accepted (device, signal, time) are held as conflicts by
    ingestion; the ones the degraded run never published are accepted, so the
    interval's evidence changes and its assessment gains revision 2. Revision 1
    stays listed, unchanged, read through a fresh application (reload)."""
    world = World(tmp_path, "kobo-mini-grid-degraded-evidence", PROLONGED)
    (first,) = read(world, "/dispatch")["assessments"]
    before = read(world, f"/assessments/{first['assessment_id']}/revisions")["revisions"]
    assert [r["revision"] for r in before] == [1]

    later = kobo_draft(
        "kobo-mini-grid-prolonged", model_profile="mini-grid", model_profile_version=3,
        timestep_minutes=5, publication_profile_version=5, **PROLONGED,
    )
    world.runs.create_run(later)
    execution = world.execution()
    execution.start(later)
    execution.run_to_end(later)
    response = world.client().post(f"/api/simulator-lab/runs/{later.run_id}/commit")
    assert response.status_code == 200, response.text

    revisions = read(world, f"/assessments/{first['assessment_id']}/revisions")["revisions"]
    assert sorted(r["revision"] for r in revisions) == [1, 2], revisions
    prior = next(r for r in revisions if r["revision"] == 1)
    current = next(r for r in revisions if r["revision"] == 2)
    assert prior == before[0], "the prior revision is retained, not overwritten"
    assert prior["evidence_basis_digest"] != current["evidence_basis_digest"]
    assert current["evidence_records"] > prior["evidence_records"]
    assert len(read(world, "/findings")["findings"]) == 1, "a revision, not a second Finding"


# --- AC20: Site > Evidence capability row, scored through normal ingestion ----------


def capability_row(world: World) -> dict:
    (analytic,) = read(world, "/analytics")["analytics"]
    assert analytic["analytic_id"] == "dispatch"
    return analytic["readiness"]


def test_degraded_evidence_scores_limited_and_names_battery_capability(degraded) -> None:
    r = capability_row(degraded)
    assert r["level"] == "LIMITED", r
    gaps = [m for m in r["missing_evidence"] if m["kind"] == "COVERAGE_GAP"]
    battery = next(m for m in gaps if m["role"] == "Battery discharge capability")
    assert battery["limits_claim"] is True
    assert battery["assessment_ids"] == [only(degraded)["assessment_id"]]
    assert r["claim_ceiling"]["claim_level"] == "CANDIDATE_AVOIDABLE"


def test_prolonged_and_healthy_readiness_is_scored_from_their_own_coverage(prolonged, healthy) -> None:
    for world in (prolonged, healthy):
        r = capability_row(world)
        assert r["level"] == "FULL" and r["assessed_intervals"] >= 1
        assert not any(m["limits_claim"] for m in r["missing_evidence"])
        # A gap is listed only where an assessment's coverage names one (rule 3).
        assessments = {a["assessment_id"]: a["assessment"] for a in read(world, "/dispatch")["assessments"]}
        for gap in (m for m in r["missing_evidence"] if m["kind"] == "COVERAGE_GAP"):
            for assessment_id in gap["assessment_ids"]:
                rows = assessments[assessment_id]["coverage"]["inputs"]
                assert any(row["label"] == gap["role"] and row["gaps"] for row in rows)
