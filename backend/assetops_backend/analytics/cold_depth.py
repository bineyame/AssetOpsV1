"""W5-01 C1: the selected cold Cooling depth read (`.agent/W5-01-build-spec.md` "Shared selected read and guards",
"C1" and its derivation table).

Pure composition over `ColdReadService` (no SQL driver here): one REPEATABLE READ connection from
`ColdReadService.within`, the W2-03 selected snapshot (`selection_on`), its envelope `source_provenance`
(`envelope_on`, revision-ID selection) and the exact selected accepted records from the Site-scoped evidence ledger
(`accepted_on`). Read-only. The W2 selected start chain stores only first steps, so no ordered compressor-to-policy
recovery is proved here: restart, return-to-policy and both duration bounds stay null and the comparison is
`CONTEXT_MISSING` for every W2 replay (W2-F closure S2, `cold_site_reads.COOLING_TEXT`).
"""

from __future__ import annotations

from typing import Any
from urllib.parse import quote, urlencode
from uuid import UUID

from assetops_backend.analytics import cold
from assetops_backend.analytics.cold_reads import ColdCursorRefused
from assetops_backend.analytics.cold_site_reads import ColdSiteReadService

SCHEMA_VERSION = "cold-depth-1"
EXC, START = cold.EXCURSION_ANALYTIC, cold.START_RESPONSE_ANALYTIC
RECOVERY_STATES = ("LIMITED", "CONTRADICTORY", "UNKNOWN")
COMPARISON_CONTEXT_MISSING = "CONTEXT_MISSING"
OBSERVED, UNKNOWN = "Observed", "Unknown"
CONTEXT_ROWS = ("Ambient temperature", "Power availability", "Door-open duration", "Loading / batch", "Defrost")
#: W2 COOLING_RESPONSE capability state -> recovery_state (derivation table).
RECOVERY_FROM_W2 = {"LIMITED": "LIMITED", "CONTRADICTORY": "CONTRADICTORY", "UNAVAILABLE": "UNKNOWN"}
#: The two start-chain first steps a Cooling point may come from, and the role whose record observes each.
POINT_STEPS = {"COMPRESSOR": cold.COMPRESSOR_ROLE, "PROBE": cold.PROBE_ROLE}
LINK_SUFFIX = {"temperature": "temperature", "backup": "backup-chain", "evidence": "evidence", "health": "health"}


def _plain(value: Any) -> Any:
    return cold.plain(value)


def _ids(values) -> list[str]:
    return sorted({str(UUID(str(v))).lower() for v in values})


def door_pairs(rows: list[dict[str, Any]]) -> tuple[list[str], int | None]:
    """Matched accepted `door_event` OPEN/CLOSE pairs in `(source_time, id)` order: each OPEN is paired with the
    next CLOSE strictly later than it. Returns the pairs' evidence IDs and their summed positive elapsed seconds,
    or `([], None)` when no pair matches (a lone OPEN or CLOSE is not a duration)."""
    ordered = sorted(rows, key=lambda r: (r["source_time"], str(r["id"])))
    ids: list[str] = []
    total = 0
    opened: dict[str, Any] | None = None
    for row in ordered:
        if row["record_kind"] == "DOOR_OPEN":
            opened = opened or row
        elif row["record_kind"] == "DOOR_CLOSE" and opened is not None:
            elapsed = int((row["source_time"] - opened["source_time"]).total_seconds())
            if elapsed > 0:
                ids += [str(opened["id"]), str(row["id"])]
                total += elapsed
            opened = None
    return (_ids(ids), total) if ids else ([], None)


class ColdDepthReadService:
    def __init__(self, reads: Any) -> None:
        self._reads = reads

    # --- shared ----------------------------------------------------------------------------------------------

    def _selected(self, c, t: UUID, s: UUID, code: str, lo, hi, known_at) -> dict[str, Any]:
        snap = self._reads.selection_on(c, t, s, code, lo, hi, known_at)
        if known_at is not None and snap["watermark"] is not None and known_at > snap["watermark"]:
            raise ColdCursorRefused(422, "COLD_TIME_INVALID",
                                    "'known_at' is later than the latest committed evidence.")
        return snap

    @staticmethod
    def _query(snap: dict[str, Any]) -> str:
        pairs = [(k, _plain(snap[v])) for k, v in (("from", "lo"), ("to", "hi"), ("known_at", "known"))
                 if snap[v] is not None]
        return "?" + urlencode(pairs) if pairs else ""

    def _links(self, snap: dict[str, Any]) -> dict[str, str]:
        base = f"/api/sites/{quote(snap['code'], safe='')}/cold/"
        return {key: base + suffix + self._query(snap) for key, suffix in LINK_SUFFIX.items()}

    def _head(self, c, snap: dict[str, Any]) -> dict[str, Any]:
        """The shared `cold-depth-1` envelope: window with the committed watermark and the exact selection."""
        selected = snap["selected"]
        provenance = self._reads.envelope_on(c, snap, (EXC, START))["source_provenance"]
        return {
            "schema_version": SCHEMA_VERSION,
            "site_id": str(snap["s"]),
            "window": {"from": _plain(snap["lo"]), "to": _plain(snap["hi"]), "known_at": _plain(snap["known"]),
                       "committed_watermark": _plain(snap["watermark"])},
            "selection": {"state": snap["state"],
                          "assessment_revision_ids": sorted(str(selected[a].revision_id).lower()
                                                            for a in selected),
                          "accepted_evidence_ids": self._selected_ids(snap),
                          "source_provenance": provenance},
        }

    @staticmethod
    def _selected_ids(snap: dict[str, Any]) -> list[str]:
        return _ids(e for sel in snap["selected"].values() for e in sel.evidence_ids)

    # --- /cold/cooling ---------------------------------------------------------------------------------------

    def cooling(self, t: UUID, s: UUID, code: str, lo, hi, known_at) -> dict[str, Any]:
        def work(c):
            snap = self._selected(c, t, s, code, lo, hi, known_at)
            head = self._head(c, snap)
            accepted = self._reads.accepted_on(c, t, s, self._selected_ids(snap)) if snap["selected"] else []
            return {**head, "cooling": self._cooling(c, snap, accepted), "links": self._links(snap)}
        return self._reads.within(work)

    def _recovery_state(self, c, snap: dict[str, Any]) -> str:
        if START not in snap["selected"]:
            return "UNKNOWN"
        caps = {x["claim"]: x for x in ColdSiteReadService(self._reads, None)._capabilities(c, snap)}
        return RECOVERY_FROM_W2[caps["COOLING_RESPONSE"]["state"]]

    @staticmethod
    def _points(snap: dict[str, Any], accepted_ids: set[str]) -> list[dict[str, Any]]:
        st = snap["selected"].get(START)
        chains = (st.result.get("chains") or []) if st else []
        points = []
        for chain in chains:
            for step in chain["steps"]:
                ids = _ids(step.get("evidence_ids") or ())
                if (step["step"] in POINT_STEPS and step["state"] == "OBSERVED" and step.get("at") and ids
                        and set(ids) <= accepted_ids):
                    points.append({"role": POINT_STEPS[step["step"]], "source_time": step["at"],
                                   "evidence_ids": ids})
        return sorted(points, key=lambda p: (p["source_time"], p["role"], p["evidence_ids"]))

    def _cooling(self, c, snap: dict[str, Any], accepted: list[dict[str, Any]]) -> dict[str, Any]:
        accepted_ids = {str(r["id"]).lower() for r in accepted}
        grid = _ids(r["id"] for r in accepted if r["role"] == cold.GRID_EVENT_ROLE)
        door_ids, door_seconds = door_pairs([r for r in accepted if r["role"] == cold.DOOR_ROLE])
        rows = {name: {"label": name, "state": UNKNOWN, "evidence_ids": [], "duration_seconds": None}
                for name in CONTEXT_ROWS}
        if grid:
            rows["Power availability"].update(state=OBSERVED, evidence_ids=grid)
        if door_ids:
            rows["Door-open duration"].update(state=OBSERVED, evidence_ids=door_ids, duration_seconds=door_seconds)
        return {
            "recovery_state": self._recovery_state(c, snap),
            "selected_points": self._points(snap, accepted_ids),
            "observed_restart_at": None,
            "observed_return_to_policy_at": None,
            "duration_lower_seconds": None,
            "duration_upper_seconds": None,
            "comparison_state": COMPARISON_CONTEXT_MISSING,
            "context": [rows[name] for name in CONTEXT_ROWS],
        }

