"""Selected-window and interval read of the durable dispatch assessment (S3-01 phase 3).

`D-2026-10-11-s3-phase-2-selection-and-read` (Architect Q1, Q2, Q4, Q6-Q8):

- Projection status is derived, in one consistent snapshot, from the current
  accepted input basis, the last DEFAULT selection of the window (migration
  0008, commit order) and every overlapping PENDING/LEASED/FAILED job. CURRENT
  needs the selected run's input hash, configuration digest and model version to
  equal what the current accepted basis gives now, and no outstanding or failed
  job. Otherwise the prior selection stays inspectable, marked stale.
- Historical drill-down is pinned to the stored run, revision and exact
  evidence IDs/digests. `knowledge_cutoff` is the worker selection timestamp,
  not a replayable acceptance fence; no arbitrary `knowledge_at` replay exists.
- Each reading's as-accepted Foundation/binding revisions are shown beside the
  revisions the run selected; a difference is named as a later selection
  (backdated correction), never as the reading's acceptance basis.
- A demo-manifest fault-fixture label is a separate annotation matched by
  exact public IDs and attributed to the manifest, never central provenance.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from types import ModuleType
from typing import Any, Callable, Protocol
from uuid import UUID

from assetops_backend.analytics import dispatch_v3
from assetops_backend.analytics.assessment_inputs import EvidenceQuery, EvidenceQueryResult, Window
from assetops_backend.analytics.assessment_ports import WindowSnapshot
from assetops_backend.analytics.assessment_worker import DISPATCH_ROLES, DOMAIN, input_basis

UNASSESSED, PENDING, CURRENT, STALE, FAILED = "UNASSESSED", "PENDING", "CURRENT", "STALE_PROJECTION", "FAILED"
# The read's basis is "everything accepted and every configuration revision recorded so far".
OPEN_CUTOFF = datetime(9999, 1, 1, tzinfo=timezone.utc)
CUTOFF_LABEL = ("worker selection timestamp at lease time; not a commit-ordered acceptance fence, so it alone "
                "does not reproduce the run (the stored evidence IDs and digests do)")
UNAVAILABLE = {
    "alternatives": "UNAVAILABLE: no S2 V3 operator command record exists; an override is neither invented "
                    "nor ruled out",
    "policy_necessary": "UNAVAILABLE: a configured minimum runtime is not an authenticated runtime record",
    "fuel_and_money": "UNAVAILABLE: no fuel quantity, saving or monetary claim in S3 (S4 Finding work)",
    "finding": "UNAVAILABLE: interval assessments are not Findings (S4)",
}


class DispatchReadStore(Protocol):
    def window_snapshot(self, query: EvidenceQuery, analytic_id: str,
                        basis: Callable[[EvidenceQueryResult], tuple[str | None, str]]) -> WindowSnapshot: ...

    def run_detail(self, tenant_id: UUID, site_id: UUID, run_id: UUID) -> dict[str, Any] | None: ...

    def revision_detail(self, tenant_id: UUID, site_id: UUID, revision_id: UUID) -> dict[str, Any] | None: ...


class DemoAnnotations(Protocol):
    def annotate(self, evidence_ids: set[str]) -> list[dict[str, Any]]: ...


@dataclass(frozen=True)
class Projection:
    status: str
    reasons: tuple[str, ...]


def day_window(day: date) -> Window:
    start = datetime.combine(day, time(0), tzinfo=timezone.utc)
    return Window(start, start + timedelta(days=1))


def derive_status(snapshot: WindowSnapshot, model_version: str) -> Projection:
    """The five read states (task "Read states"). Latest `completed_at` is never consulted."""
    outstanding = [j for j in snapshot.jobs if j["status"] in ("PENDING", "LEASED")]
    failed = [j for j in snapshot.jobs if j["status"] == "FAILED"]
    reasons: list[str] = []
    if failed:
        reasons.append("RECOMPUTE_FAILED: " + "; ".join(f"job {j['id']}: {j['last_error'] or 'no reason'}"
                                                        for j in failed))
    if outstanding:
        reasons.append("RECOMPUTE_OUTSTANDING: " + ", ".join(f"job {j['id']} {j['status']}" for j in outstanding))
    run = snapshot.run
    if run is None:
        if failed:
            return Projection(FAILED, tuple(reasons))
        if outstanding:
            return Projection(PENDING, tuple(reasons))
        if snapshot.reading_count:
            reasons.append("NOT_ASSESSED: accepted evidence exists but no recompute job or run covers it")
        return Projection(UNASSESSED, tuple(reasons))
    if run["model_version"] != model_version:
        reasons.append(f"MODEL_VERSION_CHANGED: selected run used {run['model_version']}, current is {model_version}")
    if run["configuration_sha256"] != snapshot.current_configuration_sha256:
        reasons.append("CONFIGURATION_CHANGED: the Foundation/binding selection now differs from the run's "
                       "(for example a backdated publication)")
    if run["input_sha256"] != snapshot.current_input_sha256:
        reasons.append("INPUT_BASIS_CHANGED: the current accepted basis gives another input hash")
    if failed:
        return Projection(FAILED, tuple(reasons))
    if reasons:
        return Projection(STALE, tuple(reasons))
    return Projection(CURRENT, ())


def _scope(revisions: list[dict[str, Any]], scope: str) -> list[dict[str, Any]]:
    return [r for r in revisions if r.get("scope") == scope]


class DispatchReadService:
    def __init__(self, store: DispatchReadStore, *, model: ModuleType | Any = dispatch_v3,
                 annotations: DemoAnnotations | None = None) -> None:
        self.store, self.model, self.annotations = store, model, annotations

    def _annotate(self, evidence_ids: set[str]) -> list[dict[str, Any]]:
        return [] if self.annotations is None or not evidence_ids else self.annotations.annotate(evidence_ids)

    def window(self, tenant_id: UUID, site_id: UUID, day: date) -> dict[str, Any]:
        window = day_window(day)
        query = EvidenceQuery(tenant_id, site_id, DOMAIN, window, OPEN_CUTOFF, roles=DISPATCH_ROLES)

        def basis(result: EvidenceQueryResult) -> tuple[str | None, str]:
            inputs, config_sha = input_basis(result, self.model)
            return (None if inputs.cohort.status == "EMPTY" else inputs.input_sha256), config_sha

        snap = self.store.window_snapshot(query, self.model.ANALYTIC_ID, basis)
        projection = derive_status(snap, self.model.MODEL_VERSION)
        run = snap.run
        revisions = [] if run is None else run["revisions"]
        [window_rev] = _scope(revisions, "WINDOW") or [None]
        intervals = _scope(revisions, "INTERVAL")
        live_keys = {r["assessment_key"] for r in revisions}
        superseded = [k for k in snap.key_heads if k["assessment_key"] not in live_keys]
        evidence_ids = {str(e["evidence_id"]) for e in (run or {}).get("evidence", [])}
        return {
            "domain": DOMAIN, "analytic_id": self.model.ANALYTIC_ID, "model_version": self.model.MODEL_VERSION,
            "window": {"start": window.start, "end": window.end, "calendar": "UTC day (dispatch-3)"},
            "status": projection.status, "status_reasons": list(projection.reasons),
            "stale": projection.status in (STALE, FAILED) and run is not None,
            "current_basis": {"read_at": snap.read_at, "accepted_reading_count": snap.reading_count,
                              "input_sha256": snap.current_input_sha256,
                              "configuration_sha256": snap.current_configuration_sha256},
            "selection": None if run is None else {
                "run_id": run["id"], "selected_at": snap.head["selected_at"], "selected_by_job": snap.head["job_id"],
                "knowledge_cutoff": run["knowledge_cutoff"], "knowledge_cutoff_label": CUTOFF_LABEL,
                "model_version": run["model_version"], "input_sha256": run["input_sha256"],
                "configuration_sha256": run["configuration_sha256"], "cohort_status": run["cohort_status"],
                "cohort_sha256": run["cohort_sha256"], "cohort": run["cohort"],
                "foundation_revision_ids": run["foundation_revision_ids"],
                "binding_set_revision_ids": run["binding_set_revision_ids"], "built_at": run["completed_at"]},
            "coverage": None if run is None else run["role_coverage"],
            "watermarks": None if run is None else {**(run["watermarks"] or {}), "analytic_built_at": run["completed_at"]},
            "window_assessment": window_rev,
            "limitations": [] if window_rev is None else list((window_rev["result"] or {}).get("limitations", [])),
            "intervals": intervals,
            "superseded_keys": superseded,
            "jobs": snap.jobs,
            "unavailable": UNAVAILABLE,
            "evidence_count": len(evidence_ids),
            "demo_annotations": self._annotate(evidence_ids),
        }

    def run(self, tenant_id: UUID, site_id: UUID, run_id: UUID) -> dict[str, Any] | None:
        run = self.store.run_detail(tenant_id, site_id, run_id)
        if run is None:
            return None
        run["knowledge_cutoff_label"] = CUTOFF_LABEL
        run["demo_annotations"] = self._annotate({str(e["evidence_id"]) for e in run["evidence"]})
        return run

    def revision(self, tenant_id: UUID, site_id: UUID, revision_id: UUID) -> dict[str, Any] | None:
        revision = self.store.revision_detail(tenant_id, site_id, revision_id)
        if revision is None:
            return None
        run = revision["run"]
        selected_foundation = {str(x) for x in run["foundation_revision_ids"]}
        selected_sets = {str(x) for x in run["binding_set_revision_ids"]}
        for item in revision["evidence"]:
            later = []
            if str(item["foundation_revision_id"]) not in selected_foundation:
                later.append("foundation")
            if str(item["binding_set_revision_id"]) not in selected_sets:
                later.append("binding set")
            item["as_accepted"] = {k: item[k] for k in ("foundation_revision_id", "binding_set_revision_id",
                                                         "binding_revision_id")}
            item["selection_note"] = None if not later else (
                f"the run selected a later {' and '.join(later)} revision than this reading was accepted under "
                "(a backdated correction); the reading's acceptance basis is unchanged")
        revision["selected_configuration"] = {"foundation_revision_ids": sorted(selected_foundation),
                                              "binding_set_revision_ids": sorted(selected_sets)}
        revision["knowledge_cutoff_label"] = CUTOFF_LABEL
        revision["demo_annotations"] = self._annotate({str(e["evidence_id"]) for e in revision["evidence"]}
                                                      | {str(e["evidence_id"]) for e in run["evidence"]})
        revision["unavailable"] = UNAVAILABLE
        return revision
