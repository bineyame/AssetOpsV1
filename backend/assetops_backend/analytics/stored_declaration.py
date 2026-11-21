"""AP-1 (D-SR.75, D-SR.77): the `/api/sites/{id}/analytics` readiness read for a stored (PostgreSQL) Site.

The same declarations (`declaration.DECLARATIONS`), the same scoring (`score_readiness`, `plain.readiness`), the
same range rule (`in_window`, SR-12b) and the same JSON shape (`declaration_payload`) as the file-backed read. Only
the two ingredients are stored reads, both in one REPEATABLE READ snapshot:

- whether each declared input has a usable accepted record: one latest-GOOD-reading probe per bound role
  (`role_presence`), or a configured Foundation control for a policy row. A row with no mapping, or a kind the
  stored model does not record (stop threshold, operator override), fails closed: not available.
- the coverage of the selected dispatch-3.2/3.3 interval revisions (`selected_intervals_on`), adapted by
  `v3_assessment_view` from `claim_limit_read.segment_roles`, so the panel and the claim-limit section read the same
  per-role status of the same stored segments. Configured capability is never counted as observed (S3-02a rule).
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Callable, Protocol
from uuid import UUID

from assetops_backend.analytics import dispatch_v3
from assetops_backend.analytics.assessment_inputs import BRACKET, CONTROL_BATTERY_RESERVE, CONTROL_MINIMUM_RUNTIME
from assetops_backend.analytics.assessment_worker import DOMAIN
from assetops_backend.analytics.claim_limit_read import COVERED, GEN, SUPPORTED_MODELS, segment_roles
from assetops_backend.analytics.declaration import AnalyticDeclaration, applicable, declaration_payload

READING, CONTROL, NOT_STORED = "READING", "CONTROL", "NOT_STORED"

#: Each Dispatch declaration row (by its role label) -> what stored record evidences it. A reading role is checked
#: per bound asset (each Load row is `feeder_demand` on one bound feeder). A label missing here fails closed.
ROLE_OF_REQUIREMENT: dict[str, tuple[str, str | None]] = {
    "Generator state": (READING, dispatch_v3.GEN_STATE),
    "Generator state and output": (READING, dispatch_v3.GEN_POWER),
    "Load": (READING, dispatch_v3.LOAD),
    "PV capability": (READING, dispatch_v3.PV_AVAILABLE),
    "Battery state": (READING, dispatch_v3.SOC),
    "Battery capability": (READING, dispatch_v3.DISCHARGE),
    "Reserve policy": (CONTROL, CONTROL_BATTERY_RESERVE),
    "Minimum runtime policy": (CONTROL, CONTROL_MINIMUM_RUNTIME),
    # The stored model holds no stop-threshold or operator-command record (dispatch_read: UNAVAILABLE).
    "Stop threshold policy (context)": (NOT_STORED, None),
    "Operator override": (NOT_STORED, None),
}

#: The coverage inputs of a stored dispatch-3.2/3.3 revision: the claim-limit rule's required roles besides generator
#: state, labelled as the stored segments' `missing` texts name them.
COVERAGE_ROLES = (dispatch_v3.LOAD, dispatch_v3.PV_AVAILABLE, dispatch_v3.DISCHARGE, dispatch_v3.SOC)


class UnsupportedModel(Exception):
    """A selected revision of a model whose stored segment vocabulary is not mapped (never guessed)."""

    def __init__(self, message: str, *, revision: Any = None, model: Any = None) -> None:
        super().__init__(message)
        self.revision, self.model = revision, model


class StoredSiteNotFound(Exception):
    """The Site code resolved to a stored Site, but no stored Site row answers it (AP-1 L1: never a LookupError,
    so a missing key in a stored row stays a 500 and is not reported as "Site not found")."""


class StoredDeclarationStore(Protocol):
    def read_snapshot(self, work: Any) -> Any: ...
    def site_type_on(self, c: Any, tenant_id: UUID, site_id: UUID) -> str | None: ...
    def role_presence(self, c: Any, tenant_id: UUID, site_id: UUID, roles: tuple[str, ...]) -> list[dict[str, Any]]: ...
    def foundation_controls_on(self, c: Any, tenant_id: UUID, site_id: UUID) -> set[str]: ...
    def selected_intervals_on(self, c: Any, tenant_id: UUID, site_id: UUID, analytic_id: str, domain: str,
                              bracket: Any, window: tuple[datetime, datetime] | None = None) -> list[dict[str, Any]]: ...


def _iso(value: datetime | str | None) -> str | None:
    if value is None or isinstance(value, str):
        return value
    return value.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _t(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _row(req: Any, *, available: bool, device_id: str | None = None, signal_id: str | None = None,
         last: datetime | None = None, unbound: bool = False) -> dict[str, Any]:
    # D-SR.78 Q2: ids come only from a stored binding; never the file-era declaration's reference.
    return {
        "device_id": device_id,
        "signal_id": signal_id,
        "unbound": unbound,
        "family": req.family,
        "role": req.role,
        "available": available,
        # AP-1: presence is a latest-record probe, not a count (D-SR.75 A3); the stored read states no count.
        "usable_records": None,
        "last_source_time": _iso(last),
    }


def stored_requirements(declaration: AnalyticDeclaration, presence: list[dict[str, Any]],
                        controls: set[str]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """The (required, optional) availability rows of one declaration from the stored presence and controls.

    A reading role gives one row per bound asset, ids from that binding (the declaration's several Load rows become
    the Site's bound feeders); an unbound role keeps the declaration's rows, not available, with null ids and `unbound` true (D-SR.78 Q2). A control row is available
    only when a Foundation revision configures it. NOT_STORED and unmapped rows are not available (fail closed)."""
    by_role: dict[str, list[dict[str, Any]]] = {}
    for p in presence:
        by_role.setdefault(p["role"], []).append(p)

    def rows(reqs: tuple[Any, ...]) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        done: set[str] = set()
        for req in reqs:
            kind, key = ROLE_OF_REQUIREMENT.get(req.role, (NOT_STORED, None))
            if kind == READING and by_role.get(key):
                if req.role not in done:
                    out += [_row(req, available=b["last_source_time"] is not None, device_id=b["device_id"],
                                 signal_id=b["signal_id"], last=b["last_source_time"]) for b in by_role[key]]
                    done.add(req.role)
                continue
            out.append(_row(req, available=kind == CONTROL and key in controls, unbound=kind == READING))
        return out

    return rows(declaration.required_evidence), rows(declaration.optional_evidence)


def _unobserved(segments: list[dict[str, Any]]) -> list[dict[str, str]]:
    spans: list[list[str]] = []
    for seg in segments:
        if seg.get("observed"):
            continue
        if spans and spans[-1][1] == seg["start"]:
            spans[-1][1] = seg["end"]
        else:
            spans.append([seg["start"], seg["end"]])
    return [{"start": a, "end": b, "minutes": str(int((_t(b) - _t(a)).total_seconds() // 60))} for a, b in spans]


def v3_assessment_view(revision: dict[str, Any]) -> dict[str, Any]:
    """One stored dispatch-3.2/3.3 INTERVAL revision as the dict `score_readiness` reads: per-input usable vs evaluated
    (observed) segments from `segment_roles` (unknown problem text is not covered), the generator-state unobserved
    spans, each segment's `missing` labels, and an `assessed_window` (first segment start to last segment end) so
    `in_window` applies unchanged. Any other model is refused."""
    if revision.get("model_version") not in SUPPORTED_MODELS:
        raise UnsupportedModel(
            f"Readiness maps {', '.join(SUPPORTED_MODELS)} results only; revision {revision.get('id')} is "
            f"{revision.get('model_version')}.", revision=revision.get("id"), model=revision.get("model_version"))
    result = revision.get("result") or {}
    segments = list(result.get("segments", []))
    observed = [s for s in segments if s.get("observed")]
    statuses = [segment_roles(s, {}) for s in observed]
    inputs = [{
        "input": role,
        "label": dispatch_v3.LABELS[role],
        "usable_segments": sum(1 for st in statuses if st[role][0] == COVERED),
        "evaluated_segments": len(observed),
    } for role in COVERAGE_ROLES]
    interval = result.get("interval") or {}
    view: dict[str, Any] = {
        "model_version": revision["model_version"],
        "claim_level": revision.get("claim_level"),
        "interval": {"first_running_observed": interval.get("first_on"),
                     "last_running_observed": interval.get("last_on")},
        "coverage": {"inputs": inputs, "unobserved_generator_state": _unobserved(segments)},
        "segments": [{"start": s["start"], "end": s["end"], "missing": list(s.get("missing", []))}
                     for s in segments],
    }
    if segments:
        view["assessed_window"] = {"start": segments[0]["start"], "end": segments[-1]["end"]}
    return view


def stored_site_declaration(store: StoredDeclarationStore, tenant_id: UUID, site_id: UUID, site_code: str,
                            window: tuple[datetime, datetime] | None = None, *,
                            gate: Callable[[], None] | None = None) -> dict[str, Any]:
    """`site_declaration`'s output for a stored Site, read in one REPEATABLE READ snapshot. A Site type with no
    declaration (cold chain, EV) answers `analytics: []` without reading readings or assessments. `gate` (the
    Performance cutover gate; it raises when closed) is asked only when a declaration applies."""

    def work(c: Any) -> dict[str, Any]:
        site_type = store.site_type_on(c, tenant_id, site_id)
        if site_type is None:
            raise StoredSiteNotFound(f"Site {site_code} is not in the stored Site table.")
        declarations = applicable(site_type)
        if not declarations:
            return declaration_payload(site_code, site_type, lambda d: ([], []), {}, window)
        if gate is not None:
            gate()
        roles = tuple(sorted({key for d in declarations for r in (*d.required_evidence, *d.optional_evidence)
                              for kind, key in [ROLE_OF_REQUIREMENT.get(r.role, (NOT_STORED, None))]
                              if kind == READING}))
        presence = store.role_presence(c, tenant_id, site_id, roles)
        controls = store.foundation_controls_on(c, tenant_id, site_id)
        assessments: dict[str, list[tuple[str, dict[str, Any]]]] = {}
        for d in declarations:
            revisions = store.selected_intervals_on(c, tenant_id, site_id, d.analytic_id, DOMAIN, BRACKET, window)
            assessments[d.analytic_id] = [(str(r["id"]), v3_assessment_view(r))
                                          for r in sorted(revisions, key=lambda r: (r["window_start"], str(r["id"])))]
        return declaration_payload(site_code, site_type,
                                   lambda d: stored_requirements(d, presence, controls), assessments, window)

    return store.read_snapshot(work)


__all__ = ["COVERAGE_ROLES", "GEN", "ROLE_OF_REQUIREMENT", "UnsupportedModel", "stored_requirements",
           "stored_site_declaration", "v3_assessment_view"]
