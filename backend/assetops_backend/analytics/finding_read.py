"""Exact Finding root/revision read (S4-01 phase 2, `I-finding-read`).

`D-2026-10-12-finding-episode-and-revisions`, `D-2026-10-12-s4-finding-phase-1-clarifications`,
`D-2026-10-12-s4-finding-phase-1-fix-clarifications` (Q10-Q15) and
`D-2026-10-09-pre-s3-claim-routes-and-actor`:

- A Finding is read under its tenant and Site; an unknown or foreign root or revision is None (404).
- Omitted `revision_id` selects the latest recorded revision; an exact ID pins that immutable revision.
  The S3 worker `knowledge_cutoff` is not a commit-ordered fence, so no arbitrary `knowledge_at` replay is
  offered: only exact stored revisions and IDs.
- Every revision is returned (stable `revision_no` order, paged), with its prior/new window and interval
  AssessmentRevision IDs, control/binding revisions, basis digest and `support_changed`; consecutive
  `BASIS_REFRESHED` entries are grouped only as a presentation hint.
- Currentness compares the window AssessmentRevisions the revision itself cites (the exact basis window set,
  for supported and unsupported paths alike) with the S3 read's current selection of those windows.
- A pinned non-latest revision is `SUPERSEDED_BY_LATER_REVISION`; the Finding's current state (`state`) is
  always its latest revision's (phase-2 review B2).
- No Finding is never a healthy verdict: `window_state` says `NO_FINDING` only for a CURRENT window whose
  window assessment is not Indeterminate, with no Candidate segment and no Finding over it; an Indeterminate
  (e.g. ambiguous-cohort) window is `NOT_DETERMINABLE` (review B1). Claim level and limitations are returned.
- With the Performance source closed (Q19) the router refuses default reads; a pinned revision is served with
  `source_open=False`: audit material only, no S3 currentness read, never a current claim.

S4-03 phase 1 adds `evidence` (the selected revision's complete cited set, paged, with per-record lineage and
named broken links) and `history` (every stored revision, paged, with distinct time kinds).
"""

from __future__ import annotations

import re
from datetime import datetime, timedelta
from typing import Any, Protocol
from uuid import UUID

from assetops_backend.analytics.assessment_inputs import sha256_json
from assetops_backend.analytics.dispatch import CANDIDATE
from assetops_backend.analytics.dispatch_read import CURRENT, FAILED, PENDING, STALE, UNASSESSED, DispatchReadService
from assetops_backend.analytics.dispatch_v3 import _NOT_EVIDENCE_GAPS

REPLAY = ("Exact stored revisions only. The S3 knowledge cutoff is a worker selection timestamp, not a "
          "commit-ordered acceptance fence, so no arbitrary knowledge_at replay is offered.")
BASIS_REFRESHED_LABEL = "assessment basis updated; supported candidate amount unchanged"
PROVENANCE_STATEMENT = ("Central evidence carries no fixture or gateway-sealed marker: gateway, source, sequence "
                        "epoch and batch are the recorded provenance. A case label, when present, comes only from "
                        "the environment's demo manifest matched by exact accepted evidence IDs.")
UNAVAILABLE = {
    "money": "UNAVAILABLE: no fuel, saving or monetary claim (S4-02)",
    "recommendation": "UNAVAILABLE: no recommendation or Action (S6)",
    "evidence_tab": "UNAVAILABLE: the full Evidence child view is S4-03; the cited IDs are listed here",
    "history_tab": "UNAVAILABLE: the full chronological History child view is S4-03; every revision is listed here",
    "site_list": "UNAVAILABLE: the Site Findings list is S4-04",
    "control_route": "UNAVAILABLE: no product route edits the generator minimum runtime; fixture controls were "
                     "published by the labelled fixture producer",
}
_PROJECTION = {UNASSESSED: "NOT_ASSESSED", PENDING: "PENDING", STALE: "STALE", FAILED: "FAILED"}
_ORDER = ("FAILED", "PENDING", "STALE", "NOT_ASSESSED")
PAGE_LIMIT = 500

# ---- S4-03 phase 1 (`I-finding-evidence-read`, `I-finding-history-read`) ----
MEMBERSHIP = ("Membership is the selected revision's cited accepted evidence (finding_revision_evidence): the "
              "records its supported candidate segments cite. The input set of the analytic runs it cites is the "
              "full analytic input and is counted separately; it is not this bundle.")
LINEAGE_STATEMENT = ("Every cited ID is checked through its accepted row, batch, acceptance disposition, stored "
                     "envelope digest, accepted-as Foundation/binding revisions, citing assessment and run input "
                     "set. A link that does not resolve is named and its positive lineage claim is withheld; a "
                     "cited ID is never dropped or counted as zero evidence.")
BROKEN_WORDS = {
    "ACCEPTED_EVIDENCE": "the cited ID has no accepted evidence row in this Site",
    "BATCH": "the accepted row's ingestion batch does not resolve",
    "ACCEPTANCE_DISPOSITION": "no ACCEPTED disposition for this record resolves at its batch ordinal",
    "ENVELOPE": "the stored envelope text is missing",
    "ENVELOPE_DIGEST": "the stored envelope text does not hash to the recorded envelope digest",
    "FOUNDATION_REVISION": "the accepted-as Foundation revision does not resolve",
    "BINDING_SET_REVISION": "the accepted-as binding set revision does not resolve",
    "BINDING_REVISION": "the accepted-as binding revision does not resolve",
    "ASSESSMENT_CITATION": "no assessment revision cited by this Finding revision lists this record",
    "RUN_INPUT": "this record is not in the input set of any analytic run this Finding revision cites",
    "ANALYTIC_RUN": "a cited assessment's analytic run does not resolve",
    "CITED_SET_DIGEST": "the cited set does not hash to the revision's recorded cited_evidence_sha256",
}
TIME_KINDS = {
    "source_time": "when the device reported the reading (cited records' first/last source time)",
    "received_at": "when central ingestion received the latest cited record",
    "accepted_at": "when central acceptance decided the latest cited record",
    "analytic_completed_at": "when the latest analytic run this revision cites completed",
    "recorded_at": "when this Finding revision was recorded",
}
HISTORY_STATEMENT = ("Every stored revision of this Finding in revision_no order. Revisions are immutable: late "
                     "evidence appends a revision and never rewrites an earlier one. The selected stored revision "
                     "and its basis IDs are the historical anchor.")


def _choose(revisions: list[dict[str, Any]], revision_id: UUID | None) -> dict[str, Any] | None:
    if revision_id is None:
        return revisions[-1]
    return next((r for r in revisions if r["id"] == revision_id), None)


def _relations(detail: dict[str, Any], opened: dict[str, Any]) -> dict[str, Any]:
    root, relations = detail["finding"], detail["relations"]
    merged_into = relations["merged_into"][0]["canonical_finding_id"] if relations["merged_into"] else None
    return {
        "canonical_finding_id": merged_into or root["id"],
        "merged_into": relations["merged_into"], "merged_from": relations["merged_from"],
        "split_from_finding_id": root["split_from_finding_id"], "split_parts": relations["split_parts"],
        "recurs_after_finding_id": root["recurs_after_finding_id"], "recurred_by": relations["recurred_by"],
        "recurrence": opened.get("recurrence") or {
            "status": "NOT_RECORDED", "reason": "opened before the matcher recorded recurrence evidence"},
    }


def _root(detail: dict[str, Any]) -> dict[str, Any]:
    root = detail["finding"]
    return {k: root[k] for k in (
        "id", "finding_key", "domain", "mechanism", "analytic_id", "generator_asset_id", "anchor_start",
        "anchor_assessment_revision_id", "cohort_sha256", "matcher_version", "opened_at",
        "recurs_after_finding_id", "split_from_finding_id")}


def _record_breaks(r: dict[str, Any]) -> list[str]:
    if r["evidence_id"] is None:
        return ["ACCEPTED_EVIDENCE"]
    out = []
    if r["batch_found"] is None:
        out.append("BATCH")
    if r["disposition"] != "ACCEPTED" or str(r["disposition_evidence_id"]) != str(r["evidence_id"]):
        out.append("ACCEPTANCE_DISPOSITION")
    if not r["envelope_present"]:
        out.append("ENVELOPE")
    elif not r["envelope_digest_ok"]:
        out.append("ENVELOPE_DIGEST")
    for key, link in (("foundation_found", "FOUNDATION_REVISION"), ("binding_set_found", "BINDING_SET_REVISION"),
                      ("binding_found", "BINDING_REVISION")):
        if r[key] is None:
            out.append(link)
    if not r["cited_by_assessment_revision_ids"]:
        out.append("ASSESSMENT_CITATION")
    if not r["input_of_run_ids"]:
        out.append("RUN_INPUT")
    return out


def _record(r: dict[str, Any], breaks: list[str]) -> dict[str, Any]:
    """One cited record with every recorded lineage column. An unresolved accepted row returns only its cited ID;
    a broken sub-link keeps the stored ID it names but its `resolved` flag is false (no fabricated value)."""
    eid = str(r["cited_evidence_id"])
    status = "BROKEN" if breaks else "RESOLVED"
    if "ACCEPTED_EVIDENCE" in breaks:
        return {"evidence_id": eid, "resolved": False, "lineage_status": status, "broken_links": breaks,
                "withheld": BROKEN_WORDS["ACCEPTED_EVIDENCE"] + "; no role, value, source or envelope is shown"}
    return {
        "evidence_id": eid, "resolved": True, "lineage_status": status, "broken_links": breaks,
        "role": r["role"], "value": r["value"], "unit": r["unit"], "quality": r["quality"],
        "unavailable_reason": r["unavailable_reason"],
        "source_time": r["source_time"], "interval": {"start": r["interval_start"], "end": r["interval_end"]},
        "published_at": r["published_at"], "received_at": r["received_at"],
        "accepted_at": None if "ACCEPTANCE_DISPOSITION" in breaks else r["accepted_at"],
        "disposition": r["disposition"],
        "source": {"gateway_id": r["gateway_id"], "source_id": r["source_id"], "sequence_epoch": r["sequence_epoch"],
                   "sequence": r["sequence"], "device_id": r["device_id"], "signal_id": r["signal_id"],
                   "asset_id": r["asset_id"], "source_mode": r["source_mode"]},
        "batch": {"batch_id": r["batch_id"], "external_batch_id": r["external_batch_id"],
                  "resolved": "BATCH" not in breaks},
        "message_id": r["message_id"],
        "envelope": {"sha256": r["envelope_sha256"],
                     "digest_verified": not ({"ENVELOPE", "ENVELOPE_DIGEST"} & set(breaks))},
        "accepted_as": {
            "foundation_revision_id": r["foundation_revision_id"], "foundation_version": r["foundation_version"],
            "foundation_resolved": "FOUNDATION_REVISION" not in breaks,
            "binding_set_revision_id": r["binding_set_revision_id"],
            "binding_set_version": r["binding_set_version"],
            "binding_set_resolved": "BINDING_SET_REVISION" not in breaks,
            "binding_revision_id": r["binding_revision_id"], "binding_resolved": "BINDING_REVISION" not in breaks,
            "conversion_kind": r["conversion_kind"], "configuration_outdated": r["configuration_outdated"]},
        "used_by": {"assessment_revision_ids": r["cited_by_assessment_revision_ids"],
                    "run_ids": r["input_of_run_ids"]},
    }


# Why a portion could not be decided, in plain words, per dispatch-3.1 modelling prefix (`_NOT_EVIDENCE_GAPS`).
# Every other `missing` entry on an Indeterminate portion is a record gap: the same rule the window assessment
# uses for its own `EVIDENCE_GAP` limitation. A revision's `limitations` (OPEN_BOUND, ANCHOR_OUTSIDE_SUPPORT)
# never decide this: they do not carry segment-level record gaps.
_MODELLING_WORDS = {
    "transition inside the segment": "conditions changed part-way through a stretch of the period, and that "
                                     "stretch only counts when both of its ends could have done without the "
                                     "generator",
    "possibly within the configured minimum runtime": "the generator may still have been inside its {runtime}"
                                                      "minimum operating time after starting",
    "battery inside the 10-point": "battery charge was within 10 points of its minimum reserve, so the battery "
                                   "was not counted on",
    "capability margin inside": "solar power and the battery together only just covered site demand, inside the "
                                "10 % safety margin",
}
assert set(_MODELLING_WORDS) == set(_NOT_EVIDENCE_GAPS), "plain words must cover every dispatch-3.1 modelling cause"
_RUNTIME = re.compile(r"minimum runtime \((\d+(?:\.\d+)?) min")
RECORD_GAP, MODELLING, UNSTATED = "RECORD_GAP", "MODELLING", "UNSTATED"
RECORD_GAP_SENTENCE = "Some records it needs are missing or conflict over part of the period."


def portion_cause(missing: list[str]) -> tuple[str, list[str]]:
    """(kind, plain fragments) for one Indeterminate portion's `missing` list."""
    if any(not m.startswith(_NOT_EVIDENCE_GAPS) for m in missing):
        return RECORD_GAP, []
    words: list[str] = []
    for m in missing:
        prefix = next(p for p in _NOT_EVIDENCE_GAPS if m.startswith(p))
        runtime = _RUNTIME.search(m)
        words.append(_MODELLING_WORDS[prefix].format(
            runtime=f"{runtime.group(1)}-minute " if runtime else ""))
    return (MODELLING, list(dict.fromkeys(words))) if words else (UNSTATED, [])


def indeterminate_cause(portions: list[dict[str, Any]]) -> dict[str, str] | None:
    """One plain cause for a revision's undecided portions; a record gap anywhere wins. None without portions."""
    if not portions:
        return None
    if any(p["kind"] == RECORD_GAP for p in portions):
        return {"kind": RECORD_GAP, "sentence": RECORD_GAP_SENTENCE}
    words = list(dict.fromkeys(w for p in portions for w in p["plain"]))
    # A transition portion is undecided because its other end is; name that end's cause when one is known.
    transition = _MODELLING_WORDS["transition inside the segment"]
    if len(words) > 1:
        words = [w for w in words if w != transition]
    if words:
        return {"kind": MODELLING, "sentence": "No records are missing. It could not decide because "
                + "; and ".join(words) + "."}
    return {"kind": UNSTATED, "sentence": "The assessment this version cites does not say why it could not "
            "decide; its own words are in Analysis."}


class FindingReadStore(Protocol):
    def finding_detail(self, tenant_id: UUID, site_id: UUID, finding_id: UUID) -> dict[str, Any] | None: ...

    def revision_lineage(self, tenant_id: UUID, site_id: UUID, finding_revision_id: UUID,
                         off_bounds: list[tuple[str, str]]) -> dict[str, Any]: ...

    def findings_over(self, tenant_id: UUID, site_id: UUID, lo: datetime, hi: datetime) -> list[dict[str, Any]]: ...

    def match_state(self, tenant_id: UUID, site_id: UUID, analytic_id: str, window_start: datetime
                    ) -> dict[str, Any]: ...

    def revision_evidence(self, tenant_id: UUID, site_id: UUID, finding_revision_id: UUID) -> dict[str, Any]: ...

    def revision_times(self, tenant_id: UUID, site_id: UUID, finding_id: UUID) -> dict[str, dict[str, Any]]: ...


def _ids(rows: list[dict[str, Any]], scope: str) -> list[str]:
    return sorted(str(x["assessment_revision_id"]) for x in rows if x["scope"] == scope)


def _union(rows: list[dict[str, Any]], key: str) -> list[str]:
    return sorted({str(v) for x in rows for v in (x.get(key) or [])})


def _summary(rev: dict[str, Any], prior: dict[str, Any] | None) -> dict[str, Any]:
    cites = rev["assessments"]
    return {
        "id": rev["id"], "revision_no": rev["revision_no"], "recorded_at": rev["created_at"],
        "transition": rev["transition"], "lifecycle": rev["lifecycle"], "claim_level": rev["claim_level"],
        "support_changed": rev["transition"] != "BASIS_REFRESHED",
        "model_version": rev["model_version"], "matcher_version": rev["matcher_version"],
        "episode": {"start": rev["episode_start"], "end": rev["episode_end"]},
        "candidate_minutes": str(rev["candidate_minutes"]),
        "basis_sha256": rev["basis_sha256"], "support_sha256": rev["support_sha256"],
        "primary_assessment_revision_id": rev["assessment_revision_id"],
        "window_assessment_revision_ids": _ids(cites, "WINDOW"),
        "interval_assessment_revision_ids": _ids(cites, "INTERVAL"),
        "prior_window_assessment_revision_ids": None if prior is None else _ids(prior["assessments"], "WINDOW"),
        "prior_interval_assessment_revision_ids": None if prior is None else _ids(prior["assessments"], "INTERVAL"),
        "foundation_revision_ids": _union(cites, "foundation_revision_ids"),
        "binding_set_revision_ids": _union(cites, "binding_set_revision_ids"),
        "cited_evidence_count": rev["cited_evidence_count"],
    }


def revision_groups(summaries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Presentation hint only (Q14): consecutive provenance-only revisions as one entry with its count and
    exact IDs; every other revision stands alone. Storage and the `revisions` list are never squashed."""
    groups: list[dict[str, Any]] = []
    for s in summaries:
        last = groups[-1] if groups else None
        if s["transition"] == "BASIS_REFRESHED" and last is not None and last["kind"] == "BASIS_REFRESHED":
            last["revision_ids"].append(s["id"])
            last["count"] += 1
            last["last_revision_no"] = s["revision_no"]
            continue
        groups.append({"kind": "BASIS_REFRESHED" if s["transition"] == "BASIS_REFRESHED" else "REVISION",
                       "label": BASIS_REFRESHED_LABEL if s["transition"] == "BASIS_REFRESHED" else s["transition"],
                       "count": 1, "revision_ids": [s["id"]], "first_revision_no": s["revision_no"],
                       "last_revision_no": s["revision_no"], "support_changed": s["support_changed"]})
    return groups


def _off_bounds(claim: dict[str, Any]) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    rec = claim.get("recurrence") or {}
    for key in ("off_after_prior", "off_before_new"):
        if rec.get(key):
            out.append((rec[key]["assessment_revision_id"], rec[key]["at"]))
    for gap in claim.get("continuity") or ():
        for stop in gap.get("stops") or ():
            out.append((stop["ended_assessment_revision_id"], stop["off_after"]))
            out.append((stop["next_assessment_revision_id"], stop["off_before"]))
    return list(dict.fromkeys(out))


class FindingReadService:
    def __init__(self, store: FindingReadStore, dispatch: DispatchReadService) -> None:
        self.store, self.dispatch = store, dispatch

    def _indeterminate_reasons(self, tenant_id: UUID, site_id: UUID, rev: dict[str, Any]) -> list[dict[str, Any]]:
        """Read-time only: why the selected revision's cited interval assessments could not decide a portion."""
        out: list[dict[str, Any]] = []
        for cite in (x for x in rev["assessments"] if x["scope"] == "INTERVAL"):
            read = self.dispatch.revision(tenant_id, site_id, UUID(str(cite["assessment_revision_id"])))
            segments = ((read or {}).get("result") or {}).get("segments") or []
            for seg in segments:
                if seg.get("classification") == "INDETERMINATE":
                    missing = list(seg.get("missing") or [])
                    kind, plain = portion_cause(missing)
                    out.append({"assessment_revision_id": str(cite["assessment_revision_id"]),
                                "start": seg.get("start"), "end": seg.get("end"), "kind": kind, "plain": plain,
                                "reasons": list(seg.get("reasons") or []), "missing": missing})
        return out

    def _currentness(self, tenant_id: UUID, site_id: UUID, rev: dict[str, Any]) -> dict[str, Any]:
        """The revision's own cited window set against the S3 read's current selection of those windows."""
        windows = []
        for cite in (x for x in rev["assessments"] if x["scope"] == "WINDOW"):
            read = self.dispatch.window(tenant_id, site_id, cite["window_start"].date())
            current = read.get("window_assessment")
            windows.append({"day": cite["window_start"].date().isoformat(),
                            "cited_window_assessment_revision_id": cite["assessment_revision_id"],
                            "status": read["status"], "status_reasons": read["status_reasons"],
                            "currently_selected_window_assessment_revision_id": None if current is None
                            else current["id"],
                            "cited_is_current_selection": current is not None
                            and str(current["id"]) == str(cite["assessment_revision_id"])})
        bad = [_PROJECTION[w["status"]] for w in windows if w["status"] != CURRENT]
        if bad:
            state = next(s for s in _ORDER if s in bad)
        elif not windows:
            state = "NOT_ASSESSED"
        elif all(w["cited_is_current_selection"] for w in windows):
            state = "CURRENT"
        else:
            state = "FINDING_MATCH_PENDING"
        return {"state": state, "windows": windows,
                "basis": "the window AssessmentRevisions this revision cites (its exact basis window set)"}

    def finding(self, tenant_id: UUID, site_id: UUID, finding_id: UUID, revision_id: UUID | None = None, *,
                after_revision_no: int = 0, limit: int = PAGE_LIMIT, source_open: bool = True
                ) -> dict[str, Any] | None:
        detail = self.store.finding_detail(tenant_id, site_id, finding_id)
        if detail is None:
            return None
        revisions = detail["revisions"]
        if not revisions:
            return None
        latest = revisions[-1]
        selected = _choose(revisions, revision_id)
        if selected is None:
            return None
        index = revisions.index(selected)
        prior = revisions[index - 1] if index else None
        summaries = [_summary(r, revisions[i - 1] if i else None) for i, r in enumerate(revisions)]
        limit = max(1, min(limit, PAGE_LIMIT))
        page = [s for s in summaries if s["revision_no"] > after_revision_no][:limit]
        claim = selected["claim"] or {}
        opened = revisions[0]["claim"] or {}
        # The recurrence relation is immutable and recorded at opening; the stops are the selected revision's.
        bounds = _off_bounds({"recurrence": opened.get("recurrence"), "continuity": claim.get("continuity")})
        lineage = self.store.revision_lineage(tenant_id, site_id, selected["id"], bounds)
        evidence_ids = {str(e["evidence_id"]) for e in lineage["evidence"]}
        relations = detail["relations"]
        merged_into = relations["merged_into"][0]["canonical_finding_id"] if relations["merged_into"] else None
        if source_open:
            latest_current = self._currentness(tenant_id, site_id, latest)
            selected_current = latest_current if selected is latest else {
                **self._currentness(tenant_id, site_id, selected), "state": "SUPERSEDED_BY_LATER_REVISION",
                "latest_revision_id": latest["id"],
                "note": "a later recorded revision supersedes this one; the Finding's current state is under "
                        "`state`, from its latest revision"}
        else:
            latest_current = selected_current = {
                "state": "SOURCE_CLOSED", "windows": [],
                "basis": "the Performance source is closed: no current S3 selection is read or claimed"}
        portions = self._indeterminate_reasons(tenant_id, site_id, selected) if source_open else []
        groups: dict[tuple, int] = {}
        for e in lineage["evidence"]:
            key = (str(e["gateway_id"]), str(e["source_id"]), e["sequence_epoch"], e["source_mode"])
            groups[key] = groups.get(key, 0) + 1
        return {
            "finding": _root(detail),
            "selection": {"revision_id": selected["id"], "revision_no": selected["revision_no"],
                          "selected_by": "LATEST_RECORDED" if revision_id is None else "EXACT_REVISION_ID",
                          "latest_revision_id": latest["id"], "is_latest": selected is latest, "replay": REPLAY},
            "revision": {
                **_summary(selected, prior),
                "title": selected["title"], "mechanism": selected["mechanism"],
                "analytic_id": selected["analytic_id"], "analytic_run_id": selected["analytic_run_id"],
                "window_assessment_revision_id": selected["window_assessment_revision_id"],
                "minutes": {"candidate": str(selected["candidate_minutes"]),
                            "necessary": str(selected["necessary_minutes"]),
                            "indeterminate": str(selected["indeterminate_minutes"])},
                "claim": claim, "limitations": selected["limitations"],
                "cited_evidence_sha256": selected["cited_evidence_sha256"],
                "input_evidence_sha256": selected["input_evidence_sha256"],
                "assessments": selected["assessments"],
                "runs": lineage["runs"],
                "cited_evidence": lineage["evidence"],
                "off_reports": lineage["off_reports"],
                "previous_revision_id": None if prior is None else prior["id"],
                "currentness": selected_current,
                "indeterminate_reasons": portions,
                "indeterminate_cause": indeterminate_cause(portions),
            },
            "state": {
                "lifecycle": latest["lifecycle"], "latest_transition": latest["transition"],
                # A superseded Finding is history: the canonical Finding carries the current claim (Q12).
                "projection": "MERGED_INTO_CANONICAL" if latest["lifecycle"] == "MERGED" else latest_current["state"],
                "claim_is_current": latest_current["state"] == "CURRENT" and latest["lifecycle"] == "SUPPORTED",
                "claim_is_current_refers_to": "LATEST_REVISION", "latest_revision_id": latest["id"],
                "merged_into_finding_id": merged_into,
                "note": ("A recorded Finding's lifecycle is shown as recorded; it is a current claim only when its "
                         "basis windows are CURRENT and still the selected assessments."),
            },
            "relations": _relations(detail, opened),
            "revisions": page,
            "revision_page": {"after_revision_no": after_revision_no, "limit": limit, "total": len(summaries),
                              "next_after_revision_no": page[-1]["revision_no"]
                              if page and page[-1]["revision_no"] < summaries[-1]["revision_no"] else None},
            "revision_groups": revision_groups(summaries),
            "provenance": {
                "statement": PROVENANCE_STATEMENT,
                "cited_evidence_by_source": [
                    {"gateway_id": g, "source_id": s, "sequence_epoch": e, "source_mode": m, "count": n}
                    for (g, s, e, m), n in sorted(groups.items())],
                "case_annotations": self.dispatch._annotate(evidence_ids),
            },
            "watermarks": {"finding_recorded_at": selected["created_at"],
                           "analytic_built_at": max((r["completed_at"] for r in lineage["runs"]
                                                     if r["completed_at"]), default=None)},
            "unavailable": UNAVAILABLE,
        }

    def evidence(self, tenant_id: UUID, site_id: UUID, finding_id: UUID, revision_id: UUID | None = None, *,
                 offset: int = 0, limit: int = 200, source_open: bool = True) -> dict[str, Any] | None:
        """`I-finding-evidence-read`: the exact selected revision's complete cited set, paged, with full
        recorded lineage per record, set-level completeness checks and the distinct analytic input counts."""
        detail = self.store.finding_detail(tenant_id, site_id, finding_id)
        if detail is None or not detail["revisions"]:
            return None
        revisions = detail["revisions"]
        selected, latest = _choose(revisions, revision_id), revisions[-1]
        if selected is None:
            return None
        index = revisions.index(selected)
        prior = revisions[index - 1] if index else None
        data = self.store.revision_evidence(tenant_id, site_id, selected["id"])
        runs = {str(r["id"]): r for r in self.store.revision_lineage(tenant_id, site_id, selected["id"], [])["runs"]}
        rows = data["rows"]
        breaks = {str(r["cited_evidence_id"]): _record_breaks(r) for r in rows}
        set_breaks: list[dict[str, Any]] = []
        unresolved = [i for i, b in breaks.items() if "ACCEPTED_EVIDENCE" in b]
        # The recorded cited digest is over [[id, envelope_sha256]] in ID order (the writer's own construction).
        if unresolved:
            digest = {"status": "NOT_VERIFIED", "reason": "cited IDs do not resolve to accepted rows",
                      "recorded": selected["cited_evidence_sha256"]}
        else:
            recomputed = sha256_json(sorted([str(r["cited_evidence_id"]), r["envelope_sha256"]] for r in rows))
            ok = recomputed == selected["cited_evidence_sha256"]
            digest = {"status": "VERIFIED" if ok else "MISMATCH", "recorded": selected["cited_evidence_sha256"],
                      "recomputed": recomputed}
            if not ok:
                set_breaks.append({"link": "CITED_SET_DIGEST", "detail": BROKEN_WORDS["CITED_SET_DIGEST"]})
        assessments = []
        for a in selected["assessments"]:
            run = runs.get(str(a["analytic_run_id"]))
            if run is None:
                set_breaks.append({"link": "ANALYTIC_RUN", "assessment_revision_id": str(a["assessment_revision_id"]),
                                   "analytic_run_id": str(a["analytic_run_id"]),
                                   "detail": BROKEN_WORDS["ANALYTIC_RUN"]})
            assessments.append({
                "assessment_revision_id": str(a["assessment_revision_id"]), "scope": a["scope"],
                "is_primary": a["is_primary"], "assessment_key": a["assessment_key"],
                "assessment_revision_no": a["revision_no"], "claim_level": a["claim_level"],
                "window": {"start": a["window_start"], "end": a["window_end"]}, "model_version": a["model_version"],
                "analytic_run_id": str(a["analytic_run_id"]), "run_resolved": run is not None,
                "cohort": None if run is None else {"status": run["cohort_status"], "sha256": run["cohort_sha256"]},
                "basis": None if run is None else {
                    "foundation_revision_ids": run["foundation_revision_ids"],
                    "binding_set_revision_ids": run["binding_set_revision_ids"],
                    "configuration_sha256": run["configuration_sha256"],
                    "control_basis": "recorded only inside the run's configuration digest (minimum runtime and "
                                     "other controls); no separate control revision ID exists"},
                "cited_records": sum(1 for r in rows if str(a["assessment_revision_id"])
                                     in r["cited_by_assessment_revision_ids"])})
        broken_records = [{"evidence_id": i, "links": b} for i, b in breaks.items() if b]
        total = len(rows)
        limit = max(1, min(limit, PAGE_LIMIT))
        page = rows[offset:offset + limit]
        counts = {"cited_total": total, "cited_resolved": total - len(unresolved),
                  "cited_unresolved": len(unresolved), "cited_with_broken_lineage": len(broken_records),
                  "input_distinct_total": data["distinct_input_evidence_count"],
                  "input_by_run": [{"analytic_run_id": k, "input_evidence_count": v["input_evidence_count"],
                                    "input_sha256": v["input_sha256"]} for k, v in sorted(runs.items())],
                  "statement": MEMBERSHIP}
        by_source: dict[tuple, int] = {}
        for r in rows:
            if r["evidence_id"] is not None:
                key = (str(r["gateway_id"]), str(r["source_id"]), r["sequence_epoch"], r["source_mode"])
                by_source[key] = by_source.get(key, 0) + 1
        return {
            "finding": _root(detail),
            "selection": {"revision_id": selected["id"], "revision_no": selected["revision_no"],
                          "selected_by": "LATEST_RECORDED" if revision_id is None else "EXACT_REVISION_ID",
                          "latest_revision_id": latest["id"], "is_latest": selected is latest, "replay": REPLAY},
            "revision": {**_summary(selected, prior), "claim_level": selected["claim_level"],
                         "minutes": {"candidate": str(selected["candidate_minutes"]),
                                     "necessary": str(selected["necessary_minutes"]),
                                     "indeterminate": str(selected["indeterminate_minutes"])},
                         "analytic_run_id": selected["analytic_run_id"],
                         "window_assessment_revision_id": selected["window_assessment_revision_id"],
                         "cited_evidence_sha256": selected["cited_evidence_sha256"],
                         "input_evidence_sha256": selected["input_evidence_sha256"],
                         "limitations": selected["limitations"]},
            "counts": counts,
            "lineage": {"status": "BROKEN" if (broken_records or set_breaks) else "COMPLETE",
                        "scope": "every cited ID of the selected revision, not only this page",
                        "cited_set_digest": digest, "set_breaks": set_breaks, "broken_records": broken_records,
                        "statement": LINEAGE_STATEMENT, "words": BROKEN_WORDS},
            "assessments": assessments,
            "records": [_record(r, breaks[str(r["cited_evidence_id"])]) for r in page],
            "page": {"offset": offset, "limit": limit, "total": total, "returned": len(page),
                     "next_offset": offset + len(page) if offset + len(page) < total else None,
                     "order": "source_time, then evidence_id (the cited set is immutable, so offsets are stable)"},
            "provenance": {
                "statement": PROVENANCE_STATEMENT,
                "cited_evidence_by_source": [
                    {"gateway_id": g, "source_id": s, "sequence_epoch": e, "source_mode": m, "count": n}
                    for (g, s, e, m), n in sorted(by_source.items())],
                "case_annotations": self.dispatch._annotate(
                    {str(r["evidence_id"]) for r in page if r["evidence_id"] is not None})},
            "currentness": None if source_open else {
                "state": "SOURCE_CLOSED",
                "basis": "the Performance source is closed: no current S3 selection is read or claimed"},
            "unavailable": UNAVAILABLE,
        }

    def history(self, tenant_id: UUID, site_id: UUID, finding_id: UUID, revision_id: UUID | None = None, *,
                after_revision_no: int = 0, limit: int = 200) -> dict[str, Any] | None:
        """`I-finding-history-read`: every stored revision in revision_no order, paged exhaustively, with the
        History row facts and the distinct time kinds. No knowledge_at replay."""
        detail = self.store.finding_detail(tenant_id, site_id, finding_id)
        if detail is None or not detail["revisions"]:
            return None
        revisions = detail["revisions"]
        selected, latest = _choose(revisions, revision_id), revisions[-1]
        if selected is None:
            return None
        times = self.store.revision_times(tenant_id, site_id, finding_id)
        rows = []
        for i, r in enumerate(revisions):
            t = times.get(str(r["id"])) or {}
            cited, resolved = int(t.get("cited") or 0), int(t.get("cited_resolved") or 0)
            rows.append({
                **_summary(r, revisions[i - 1] if i else None), "claim_level": r["claim_level"],
                "minutes": {"candidate": str(r["candidate_minutes"]), "necessary": str(r["necessary_minutes"]),
                            "indeterminate": str(r["indeterminate_minutes"])},
                "previous_revision_id": revisions[i - 1]["id"] if i else None,
                "is_selected": r is selected, "is_latest": r is latest,
                "cited_evidence": {"count": cited, "resolved": resolved,
                                   "lineage": "COMPLETE" if cited == resolved else "BROKEN"},
                "times": {"recorded_at": r["created_at"],
                          "analytic_completed_at": t.get("analytic_completed_latest"),
                          "source_time": {"first": t.get("source_first"), "last": t.get("source_last")},
                          "received_at": t.get("received_latest"), "accepted_at": t.get("accepted_latest")}})
        limit = max(1, min(limit, PAGE_LIMIT))
        page = [s for s in rows if s["revision_no"] > after_revision_no][:limit]
        return {
            "finding": _root(detail),
            "selection": {"revision_id": selected["id"], "revision_no": selected["revision_no"],
                          "selected_by": "LATEST_RECORDED" if revision_id is None else "EXACT_REVISION_ID",
                          "selected_note": "latest at read time; a later append changes it" if revision_id is None
                          else "pinned: stays this exact revision after any later append",
                          "latest_revision_id": latest["id"], "latest_revision_no": latest["revision_no"],
                          "is_latest": selected is latest, "replay": REPLAY},
            "revisions": page,
            "page": {"after_revision_no": after_revision_no, "limit": limit, "total": len(rows),
                     "returned": len(page),
                     "next_after_revision_no": page[-1]["revision_no"]
                     if page and page[-1]["revision_no"] < rows[-1]["revision_no"] else None},
            "earlier_versions": "NONE" if len(rows) == 1 else "PRESENT",
            "revision_groups": revision_groups([{k: s[k] for k in ("id", "revision_no", "transition",
                                                                    "support_changed")} for s in rows]),
            "state": {"lifecycle": latest["lifecycle"], "latest_transition": latest["transition"],
                      "note": "recorded lifecycle of the latest revision; currentness is read on the Finding root"},
            "relations": _relations(detail, revisions[0]["claim"] or {}),
            "time_kinds": TIME_KINDS,
            "statement": HISTORY_STATEMENT,
            "unavailable": {k: UNAVAILABLE[k] for k in ("recommendation",)},
        }

    def window_state(self, tenant_id: UUID, site_id: UUID, day) -> dict[str, Any]:
        """Assessed `NO_FINDING` versus not assessed / pending / stale / failed / match pending for one UTC day."""
        read = self.dispatch.window(tenant_id, site_id, day)
        lo = read["window"]["start"]
        findings = self.store.findings_over(tenant_id, site_id, lo, lo + timedelta(days=1))
        current = read.get("window_assessment")
        current_id = None if current is None else str(current["id"])
        for f in findings:
            f["cites_current_window_selection"] = current_id in {str(x) for x in f["window_assessment_revision_ids"]}
        claim_level = None if current is None else current["claim_level"]
        match = self.store.match_state(tenant_id, site_id, read["analytic_id"], lo)
        candidate = any(s.get("classification") == CANDIDATE for i in read.get("intervals") or ()
                        for s in (i.get("result") or {}).get("segments") or ())
        if read["status"] != CURRENT:
            state, note = _PROJECTION[read["status"]], "no current assessed basis; this is not a no-Finding verdict"
        elif claim_level == "INDETERMINATE" and not findings:
            state, note = "NOT_DETERMINABLE", ("the current selected assessment cannot determine this window "
                                               "(Indeterminate); this is not a no-Finding verdict")
        elif not candidate and not findings and not match["matched"]:
            state, note = "FINDING_MATCH_PENDING", ("no completed Finding match at the current selection yet; this "
                                                    "is not a no-Finding verdict")
        elif not candidate and not findings:
            state, note = "NO_FINDING", ("the current selected assessment has no Candidate segment and no Finding, "
                                         "and a completed Finding match covers that selection")
        elif (candidate and not any(f["cites_current_window_selection"] for f in findings)) or any(
                not f["cites_current_window_selection"] for f in findings if f["lifecycle"] != "MERGED"):
            state, note = "FINDING_MATCH_PENDING", ("the current selected assessment is newer than the recorded "
                                                    "Finding revisions over this window")
        else:
            state, note = "FINDINGS_RECORDED", "Findings over this window are listed with their latest revision"
        return {"day": lo.date().isoformat(), "state": state, "note": note, "assessment_status": read["status"],
                "assessment_status_reasons": read["status_reasons"],
                "selected_window_assessment_revision_id": current_id,
                "selected_run_id": (read.get("selection") or {}).get("run_id"),
                "window_claim_level": claim_level, "window_limitations": list(read.get("limitations") or []),
                "watermarks": read.get("watermarks"), "finding_match": match,
                "has_candidate_segment": candidate, "findings": findings, "unavailable": UNAVAILABLE}
