"""Run the analytics over accepted evidence and keep their revision history (T028).

AC13: assessing the same accepted evidence under the same model version
changes nothing (no new revision, no duplicate active Finding). A changed
evidence basis or model version appends a revision to the matched lineage; the
prior revision is retained and stays readable. Matching is by assessed window
overlap, so late evidence that moves an interval's bounds revises it rather
than raising a second Finding.

Assessment runs after every completed ingestion batch (the listener the
composition root registers) and, idempotently, before a read, so evidence
accepted before this analytic existed is assessed too.
"""

from __future__ import annotations

import hashlib
import threading
from dataclasses import replace
from datetime import datetime, timezone
from fractions import Fraction
from typing import Any, Callable

from assetops_backend.analytics import dispatch, plain
from assetops_backend.analytics.declaration import DISPATCH
from assetops_backend.analytics.models import (
    AssessmentHistory,
    AssessmentLineage,
    AssessmentRevision,
)
from assetops_backend.analytics.ports import AssessmentStore
from assetops_backend.evidence.ports import EvidenceStore
from assetops_backend.sites.models import SiteRecord

Clock = Callable[[], str]
_FMT = "%Y-%m-%dT%H:%M:%SZ"


def _t(text: str) -> int:
    return int(datetime.strptime(text, _FMT).replace(tzinfo=timezone.utc).timestamp())


def fuel_basis(site: SiteRecord) -> dispatch.FuelBasis:
    """The Foundation's generator specific fuel consumption, if configured."""
    for component in site.foundation.components:
        if component.component_type != "GENERATOR":
            continue
        for prop in component.properties or ():
            if prop.property_key == "specific-fuel-consumption" and prop.unit == "L/kWh":
                return dispatch.FuelBasis(
                    Fraction(str(prop.value)),
                    f"Foundation v{site.foundation.version} {component.component_id} "
                    f"specific-fuel-consumption {prop.value} L/kWh ({prop.source})",
                )
    return dispatch.FuelBasis(None, "No generator specific fuel consumption in the Foundation.")


def _window(assessment: dict[str, Any]) -> tuple[int, int]:
    window = assessment["assessed_window"]
    return _t(window["start"]), _t(window["end"])


def _overlaps(a: tuple[int, int], b: tuple[int, int]) -> bool:
    return a[0] <= b[1] and b[0] <= a[1]


def _new_id(site_id: str, assessment: dict[str, Any], taken: set[str]) -> str:
    seed = f"{site_id}|{dispatch.ANALYTIC_ID}|{assessment['interval']['first_running_observed']}"
    base = "dispatch-" + hashlib.sha256(seed.encode("utf-8")).hexdigest()[:12]
    candidate, n = base, 1
    while candidate in taken:
        n += 1
        candidate = f"{base}-{n}"
    return candidate


def revision_summary(revision: AssessmentRevision) -> dict[str, Any]:
    a = revision.assessment
    return {
        "revision": revision.revision,
        "assessed_at": revision.assessed_at,
        "model_version": revision.model_version,
        "evidence_basis_digest": revision.basis_digest,
        "evidence_records": len(a["evidence_basis"]["message_ids"]),
        "assessed_window": a["assessed_window"],
        "claim_level": a["claim_level"],
        "label": a["label"],
        "summary": a["summary"],
    }


def lineage_summary(lineage: AssessmentLineage) -> dict[str, Any]:
    latest = lineage.latest.assessment
    return {
        "assessment_id": lineage.assessment_id,
        "finding_id": lineage.assessment_id if latest["raises_finding"] else None,
        "analytic_id": lineage.analytic_id,
        "finding_type": lineage.finding_type,
        "active": lineage.active,
        "retired_at": lineage.retired_at,
        "revision": lineage.latest.revision,
        "revisions": len(lineage.revisions),
        "claim_level": latest["claim_level"],
        "label": latest["label"],
        "summary": latest["summary"],
        "interval": latest["interval"],
        "assessed_window": latest["assessed_window"],
        "confidence": latest["confidence"]["level"],
        "model_version": lineage.latest.model_version,
        # Read-time plain reading of the latest revision; not persisted, so it
        # adds no revision (D-2026-10-04-plain-language-analysis-views).
        "reading": plain.reading(latest),
    }


class AssessmentService:
    def __init__(
        self,
        evidence: EvidenceStore,
        assessments: AssessmentStore,
        sites: Callable[[str], SiteRecord],
        clock: Clock,
    ) -> None:
        self._evidence = evidence
        self._assessments = assessments
        self._sites = sites
        self._clock = clock
        self._lock = threading.Lock()

    @property
    def store(self) -> AssessmentStore:
        return self._assessments

    def assess_site(self, site_id: str) -> AssessmentHistory:
        """Assess a Site's accepted evidence; append revisions only where it changed."""
        site = self._sites(site_id)
        with self._lock:
            history = self._assessments.load_history(site_id)
            if site.site_type not in DISPATCH.site_types:
                return history
            records = self._evidence.load_site(site_id).records
            intervals = dispatch.assess(records, fuel_basis(site))
            updated, changed = self._reconcile(history, intervals)
            if changed:
                self._assessments.save_history(updated)
            return updated

    def _reconcile(
        self, history: AssessmentHistory, intervals: list[dict[str, Any]]
    ) -> tuple[AssessmentHistory, bool]:
        now = self._clock()
        lineages = list(history.lineages)
        taken = {l.assessment_id for l in lineages}
        matched: set[int] = set()
        changed = False
        for interval in sorted(intervals, key=_window):
            span = _window(interval)
            index = next(
                (
                    i for i, l in enumerate(lineages)
                    if l.active and l.analytic_id == dispatch.ANALYTIC_ID and i not in matched
                    and _overlaps(span, _window(l.latest.assessment))
                ),
                None,
            )
            digest = interval["evidence_basis"]["digest"]
            if index is None:
                assessment_id = _new_id(history.site_id, interval, taken)
                taken.add(assessment_id)
                lineages.append(AssessmentLineage(
                    assessment_id=assessment_id,
                    site_id=history.site_id,
                    analytic_id=dispatch.ANALYTIC_ID,
                    finding_type=dispatch.FINDING_TYPE,
                    active=True,
                    retired_at=None,
                    revisions=(AssessmentRevision(1, now, dispatch.MODEL_VERSION, digest, interval),),
                ))
                matched.add(len(lineages) - 1)
                changed = True
                continue
            matched.add(index)
            lineage = lineages[index]
            # Unchanged only when the digest, model and payload all match: the
            # digest covers every record and basis read (R1), and the payload
            # check keeps any changed conclusion from being silently dropped.
            if (lineage.latest.basis_digest, lineage.latest.model_version) == (
                digest, dispatch.MODEL_VERSION
            ) and lineage.latest.assessment == interval:
                continue
            revision = AssessmentRevision(
                lineage.latest.revision + 1, now, dispatch.MODEL_VERSION, digest, interval
            )
            lineages[index] = replace(lineage, revisions=lineage.revisions + (revision,))
            changed = True
        for i, lineage in enumerate(lineages):
            if lineage.active and lineage.analytic_id == dispatch.ANALYTIC_ID and i not in matched:
                lineages[i] = replace(lineage, active=False, retired_at=now)
                changed = True
        return AssessmentHistory(history.site_id, tuple(lineages)), changed

    # --- reads ------------------------------------------------------------------
    def _active(self, site_id: str) -> list[AssessmentLineage]:
        history = self.assess_site(site_id)
        return sorted(
            (l for l in history.lineages if l.active),
            key=lambda l: l.latest.assessment["interval"]["first_running_observed"],
        )

    def dispatch(self, site_id: str) -> dict[str, Any]:
        active = self._active(site_id)
        return {
            "site_id": site_id,
            "analytic_id": dispatch.ANALYTIC_ID,
            "model_version": dispatch.MODEL_VERSION,
            "assessments": [
                {**lineage_summary(l), "assessment": l.latest.assessment} for l in active
            ],
        }

    def findings(self, site_id: str) -> dict[str, Any]:
        active = self._active(site_id)
        return {
            "site_id": site_id,
            "findings": [
                lineage_summary(l) for l in active if l.latest.assessment["raises_finding"]
            ],
        }

    def lineage(self, site_id: str, assessment_id: str) -> AssessmentLineage | None:
        history = self.assess_site(site_id)
        return next((l for l in history.lineages if l.assessment_id == assessment_id), None)

    def assessment(self, site_id: str, assessment_id: str) -> dict[str, Any] | None:
        lineage = self.lineage(site_id, assessment_id)
        if lineage is None:
            return None
        return {
            **lineage_summary(lineage),
            "assessment": lineage.latest.assessment,
            "revision_history": [revision_summary(r) for r in reversed(lineage.revisions)],
        }

    def revisions(self, site_id: str, assessment_id: str) -> dict[str, Any] | None:
        lineage = self.lineage(site_id, assessment_id)
        if lineage is None:
            return None
        return {
            "site_id": site_id,
            "assessment_id": assessment_id,
            "active": lineage.active,
            "retired_at": lineage.retired_at,
            "statement": (
                "Every revision is retained. A revision is added only when the accepted "
                "evidence basis or the model version changes; the newest is first."
            ),
            "revisions": [
                {**revision_summary(r), "assessment": r.assessment}
                for r in reversed(lineage.revisions)
            ],
        }

    def card_assessments(
        self, site: SiteRecord, window_start: str | None, window_end: str | None
    ) -> dict[str, Any]:
        """The Overview's Dispatch card slot and Finding links for a window.

        Read from the persisted assessment, never recomputed for the card (AC12).
        """
        if site.site_type not in DISPATCH.site_types or window_start is None or window_end is None:
            return {"cards": {}, "findings": []}
        span = (_t(window_start), _t(window_end))
        active = [l for l in self._active(site.site_id) if _overlaps(span, _window(l.latest.assessment))]
        findings = [lineage_summary(l) for l in active if l.latest.assessment["raises_finding"]]
        levels = [l.latest.assessment["claim_level"] for l in active]
        base = {
            "capability_id": DISPATCH.analytic_id,
            "capability_display_name": DISPATCH.display_name,
            "model_version": dispatch.MODEL_VERSION,
        }
        if not active:
            card = {**base, "status": "NO_GENERATOR_RUNTIME", **plain.card(None, None, 0),
                    "assessment_ids": []}
        else:
            for level in (dispatch.CANDIDATE, dispatch.INDETERMINATE, dispatch.NECESSARY):
                if level in levels:
                    lead = next(l for l in active if l.latest.assessment["claim_level"] == level)
                    break
            others = len(active) - 1
            card = {**base, "status": level,
                    **plain.card(level, lead.latest.assessment, others),
                    "assessment_ids": [l.assessment_id for l in active],
                    "lead_assessment_id": lead.assessment_id}
        return {"cards": {"Dispatch": card}, "findings": findings}
