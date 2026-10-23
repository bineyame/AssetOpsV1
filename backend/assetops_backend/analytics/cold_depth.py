"""W5-01 C1: the selected cold Cooling and Health depth reads (`.agent/W5-01-build-spec.md` "Shared selected
read and guards", "C1", its derivation table and the "C1 Health read" tables).

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
from assetops_backend.analytics.cold_site_reads import cooling_response_state

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
    """Matched accepted `door_event` OPEN/CLOSE pairs (Q3/L1): sort the accepted door rows by `(source_time, id)`;
    a `DOOR_OPEN` while no OPEN is held becomes the held OPEN (a further OPEN while one is held is ignored); a
    `DOOR_CLOSE` with elapsed seconds `> 0` from the held OPEN closes the pair and clears the hold; a `DOOR_CLOSE`
    with elapsed `<= 0` is skipped and does not clear the hold; a CLOSE with no held OPEN is ignored. Returns all
    paired OPEN and CLOSE IDs, sorted, and the integer sum of their elapsed seconds, or `([], None)` when no pair
    matches (a lone OPEN or CLOSE is not a duration)."""
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


def _query(snap: dict[str, Any]) -> str:
    pairs = [(k, _plain(snap[v])) for k, v in (("from", "lo"), ("to", "hi"), ("known_at", "known"))
             if snap[v] is not None]
    return "?" + urlencode(pairs) if pairs else ""


def _link(snap: dict[str, Any], suffix: str) -> str:
    return f"/api/sites/{quote(snap['code'], safe='')}/cold/{suffix}" + _query(snap)


# --- /cold/health (C1 Health read, Q7) -------------------------------------------------------------------------

NOT_CONFIGURED = "NOT_CONFIGURED"
HEALTH_ROW_KEYS = ("kind", "label", "asset_id", "assets", "observation", "condition_state", "limitation",
                   "next_evidence", "evidence_ids", "link")
START_CHAIN_STEPS = ("START_REQUEST", "START_RESULT", "GENERATOR")


def _lower(value: Any) -> str | None:
    return str(value).lower() if value else None


def _asset_id(assets: list[dict[str, Any]], *candidates: Any) -> str | None:
    """The first candidate policy asset that is one of `assets`; else the only asset; else null."""
    held = {a["asset_id"] for a in assets}
    for candidate in candidates:
        if _lower(candidate) in held:
            return _lower(candidate)
    return assets[0]["asset_id"] if len(assets) == 1 else None


def _health_row(kind: str, label: str, next_evidence: str, assets: list[dict[str, Any]], asset_id: str | None,
                state: str, observation: str, limitation: str, evidence_ids: list[str],
                link: str | None) -> dict[str, Any]:
    configured = state != NOT_CONFIGURED
    return {"kind": kind, "label": label, "asset_id": asset_id if configured else None, "assets": assets,
            "observation": observation, "condition_state": state, "limitation": limitation,
            "next_evidence": next_evidence, "evidence_ids": evidence_ids, "link": link if configured else None}


def health_rows(snap: dict[str, Any], accepted: list[dict[str, Any]], foundation: dict[str, Any] | None,
                links: dict[str, str]) -> list[dict[str, Any]]:
    """The three Health rows of the C1 Health literal table, in order. `accepted` are the selected cited records
    present in the ledger; every row `evidence_ids` is a subset of them. An unresolved Foundation (None) never
    yields `NOT_CONFIGURED`."""
    ledger = {str(r["id"]).lower(): r for r in accepted}
    exc, st = snap["selected"].get(EXC), snap["selected"].get(START)
    chains = (st.result.get("chains") or []) if st else []
    start_policy = (st.result.get("policy") or {}) if st else {}
    exc_policy = (exc.result.get("policy") or {}) if exc else {}

    def present(values) -> list[str]:
        return _ids(v for v in values if str(v).lower() in ledger)

    def assets_of(component_type: str) -> list[dict[str, Any]]:
        return [{"asset_id": x["asset_id"], "asset_code": x["asset_code"], "display_name": x["display_name"]}
                for x in (foundation or {}).get("components") or () if x["component_type"] == component_type]

    def absent(assets: list[dict[str, Any]]) -> bool:
        return foundation is not None and not assets

    def step_ids(names: tuple[str, ...], result: str | None = None, observed: bool = True) -> list[str]:
        return present(e for ch in chains if result is None or ch["result"] == result for x in ch["steps"]
                       if x["step"] in names and (not observed or x["state"] == "OBSERVED")
                       for e in x.get("evidence_ids") or ())

    # Backup generator.
    gens = assets_of("GENERATOR")
    gen_asset = _asset_id(gens, start_policy.get("generator_asset_id"))
    failed = step_ids(START_CHAIN_STEPS, "OBSERVED_FAILURE")
    succeeded = step_ids(START_CHAIN_STEPS, "OBSERVED_SUCCESS")
    if absent(gens):
        gen = (NOT_CONFIGURED, "Not configured", "No backup generator is declared in the selected Foundation", [])
    elif any(ch["result"] == "CONTRADICTORY" for ch in chains) or any(
            x["state"] == "CONTRADICTORY" for ch in chains for x in ch["steps"]):
        gen = ("UNKNOWN", "Start results conflict", "Selected start results conflict; no condition is assessed",
               step_ids(("START_RESULT",), observed=False))
    elif failed:
        gen = ("NEEDS_INVESTIGATION", "Automatic start failed", "Failed automatic start observed; part not diagnosed",
               failed)
    elif succeeded:
        gen = ("UNKNOWN", "Automatic start succeeded", "A successful start does not establish generator condition",
               succeeded)
    else:
        gen = ("UNKNOWN", "No accepted start result", "No accepted automatic-start result in this window", [])

    # Cooling plant.
    comps = assets_of("COMPRESSOR")
    if absent(comps):
        plant = (NOT_CONFIGURED, "Not configured", "No cooling plant is declared in the selected Foundation", [])
    else:
        plant = ("UNKNOWN", "Condition unknown", "Comparable recovery and condition evidence absent",
                 step_ids(("COMPRESSOR",)))

    # Temperature sensing.
    probes = assets_of("TEMPERATURE_PROBE")
    support = [x["evidence_id"] for x in (exc.result.get("links") or []) if x["use"] == "SUPPORT"] if exc else []
    probe_ids = [i for i in present(support + step_ids(("PROBE",))) if ledger[i]["role"] == cold.PROBE_ROLE]
    n = len({str(ledger[i]["source_id"]) for i in probe_ids})
    if absent(probes):
        sensing = (NOT_CONFIGURED, "Not configured", "No temperature probe is declared in the selected Foundation", [])
    elif n == 1:
        sensing = ("LIMITED", "Single-point observation", "One accepted probe does not establish room-wide coverage",
                   probe_ids)
    elif n == 0:
        sensing = ("UNKNOWN", "No accepted probe", "No accepted probe observation in this window", [])
    else:
        sensing = ("UNKNOWN", "Multiple probe observations",
                   "Multiple selected probes do not establish room-wide condition", probe_ids)
    probe_asset = _asset_id(probes, exc_policy.get("probe_asset_id"), start_policy.get("probe_asset_id"),
                         (foundation or {}).get("chamber_probe_asset_id"))

    return [
        _health_row("BACKUP_GENERATOR", "Backup generator", "Witness an automatic-start test", gens, gen_asset,
                    *gen, links["backup"]),
        _health_row("COOLING_PLANT", "Cooling plant", "Record matched loading, door and ambient context", comps,
                    _asset_id(comps), *plant, _link(snap, "cooling")),
        _health_row("TEMPERATURE_SENSING", "Temperature sensing", "Add calibrated spatial coverage", probes,
                    probe_asset, *sensing, links["evidence"]),
    ]


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
    def _links(snap: dict[str, Any]) -> dict[str, str]:
        return {key: _link(snap, suffix) for key, suffix in LINK_SUFFIX.items()}

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

    def basis_on(self, c, t: UUID, s: UUID, code: str, lo, hi, known_at) -> dict[str, Any]:
        """W5-01b C4: the selected window, selection and server-resolved authored basis on the caller's `c` (the
        C4 write or read snapshot), composed only from `_selected`, `_head` and `foundation_on`. Read-only."""
        snap = self._selected(c, t, s, code, lo, hi, known_at)
        head = self._head(c, snap)
        foundation = self._reads.foundation_on(c, snap)
        window, selection = head["window"], head["selection"]
        return {"window": window, "selection": selection, "authored_basis": {
            "from": window["from"], "to": window["to"], "cutoff": window["known_at"],
            "assessment_revision_ids": selection["assessment_revision_ids"],
            "accepted_evidence_ids": selection["accepted_evidence_ids"],
            "foundation_revision_id": foundation["revision_id"] if foundation else None,
            "source_provenance": selection["source_provenance"]}}

    @staticmethod
    def _selected_ids(snap: dict[str, Any]) -> list[str]:
        return _ids(e for sel in snap["selected"].values() for e in sel.evidence_ids)

    # --- /cold/cooling ---------------------------------------------------------------------------------------

    def cooling(self, t: UUID, s: UUID, code: str, lo, hi, known_at) -> dict[str, Any]:
        def work(c):
            snap = self._selected(c, t, s, code, lo, hi, known_at)
            head = self._head(c, snap)
            accepted = self._reads.accepted_on(c, t, s, self._selected_ids(snap)) if snap["selected"] else []
            return {**head, "cooling": self._cooling(snap, accepted), "links": self._links(snap)}
        return self._reads.within(work)

    # --- /cold/health ----------------------------------------------------------------------------------------

    def health(self, t: UUID, s: UUID, code: str, lo, hi, known_at) -> dict[str, Any]:
        def work(c):
            snap = self._selected(c, t, s, code, lo, hi, known_at)
            head = self._head(c, snap)
            accepted = self._reads.accepted_on(c, t, s, self._selected_ids(snap)) if snap["selected"] else []
            foundation = self._reads.foundation_on(c, snap)
            links = self._links(snap)
            return {**head, "health": {"foundation_revision_id": foundation["revision_id"] if foundation else None,
                                       "rows": health_rows(snap, accepted, foundation, links)},
                    "links": links}
        return self._reads.within(work)

    @staticmethod
    def _recovery_state(snap: dict[str, Any]) -> str:
        return RECOVERY_FROM_W2[cooling_response_state(snap["selected"].get(START))]

    @staticmethod
    def _policy_high(snap: dict[str, Any]) -> Any:
        """Q2: the selected excursion's stored `result["policy"]["policy_high"]` exactly as stored, else null."""
        exc = snap["selected"].get(EXC)
        return (exc.result.get("policy") or {}).get("policy_high") if exc else None

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

    def _cooling(self, snap: dict[str, Any], accepted: list[dict[str, Any]]) -> dict[str, Any]:
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
            "recovery_state": self._recovery_state(snap),
            "policy_high_deg_c": self._policy_high(snap),
            "selected_points": self._points(snap, accepted_ids),
            "observed_restart_at": None,
            "observed_return_to_policy_at": None,
            "duration_lower_seconds": None,
            "duration_upper_seconds": None,
            "comparison_state": COMPARISON_CONTEXT_MISSING,
            "context": [rows[name] for name in CONTEXT_ROWS],
        }

