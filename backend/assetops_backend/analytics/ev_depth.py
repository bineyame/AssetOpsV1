"""W5-03a E1b: the selected EV Availability, Energy and Health depth reads (`ev-depth-1`).

Each read runs on one read-only REPEATABLE READ connection (`EvReadService.within`) and one W2-06 snapshot
(`open_on`, or `EvSiteReads.context_on` when the W2-07 money selector is needed), so selected energy and Health rows
are never re-read at another cutoff. Pure composition over the injected readers: no SQL text here.
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any
from urllib.parse import quote

from assetops_backend.analytics.ev import plain
from assetops_backend.analytics.ev_availability import availability_on, selected_foundation
from assetops_backend.evidence.public_provenance import dual_blocks

SCHEMA_VERSION = "ev-depth-1"
SITE_IMPORT = "ev_site_import"
BATTERY = {"condition_state": "UNKNOWN", "limitation": "Battery configuration is not established by this Foundation."}
CONNECTOR_FAULT = ("NEEDS_INVESTIGATION", "Session interruption observed",
                   "Fault-stopped session observed; cause not diagnosed",
                   "Retrieve diagnostic log and witness a complete session")
CONNECTOR_UNKNOWN = ("UNKNOWN", "Condition unknown", "No charger condition assessment",
                     "Record diagnostic and covered operation")
SITE_METER = ("UNKNOWN", "Sampled import only", None, "Record continuous import and request/limit evidence")
METER_UNKNOWN = ("UNKNOWN", "Meter role not established", "No selected Site-import binding for this meter",
                 "Confirm meter topology and source binding")
ENERGY_KEYS = ("metered_complete_kwh", "partial_kwh", "unknown_seconds", "energy_limitation", "import_sample_count",
               "import_samples", "observed_peak_import_kw", "peak_sample_at", "configured_import_limit_kw",
               "peak_below_limit", "power_constraint_state", "consequence")


class EvDepthReadService:
    """The three depth reads over W2-06's `EvReadService` and W2-07's `EvSiteReads` (its money selector)."""

    def __init__(self, reads: Any, site_reads: Any) -> None:
        self._reads, self._site = reads, site_reads

    def dispose(self) -> None:
        self._reads.dispose()

    # --- the three reads ---------------------------------------------------------------------------------------

    def availability(self, t, s, code: str, lo, hi, known_at) -> dict[str, Any]:
        def work(c):
            snap, body = self._reads.open_on(c, t, s, code, lo, hi, known_at)
            return _wrap(snap, body, code, "availability", availability_on(self._reads, c, snap))
        return self._reads.within(work)

    def energy(self, t, s, code: str, lo, hi, known_at) -> dict[str, Any]:
        def work(c):
            ctx = self._site.context_on(c, t, s, code, lo, hi, known_at)
            snap, body = ctx["snap"], ctx["body"]
            energy, site_power = self._site.energy_on(ctx)
            accepted = ctx.get("accepted")
            if accepted is None:
                accepted = self._reads.accepted_on(c, snap)
            samples = import_samples(accepted, snap)
            # One selected peak (ruling 2): the card, chart, peak time and below-limit answer all come from `samples`.
            # The W2 overview keeps its broader `_site_import` peak for compatibility; it is not a depth source.
            peak, limit = observed_peak(samples), site_power["configured_limit_kw"]
            return _wrap(snap, body, code, "energy", {
                "metered_complete_kwh": energy["complete_kwh"],
                "partial_kwh": energy["partial_kwh"],
                "unknown_seconds": energy["unknown_seconds"],
                "energy_limitation": energy["limitation"],
                "import_sample_count": len(samples),
                "import_samples": samples,
                "observed_peak_import_kw": peak,
                "peak_sample_at": peak_sample_at(samples),
                "configured_import_limit_kw": limit,
                "peak_below_limit": peak_below_limit(peak, limit),
                "power_constraint_state": "UNKNOWN",
                "consequence": self._site.consequence_on(ctx),
            })
        return self._reads.within(work)

    def health(self, t, s, code: str, lo, hi, known_at) -> dict[str, Any]:
        def work(c):
            snap, body = self._reads.open_on(c, t, s, code, lo, hi, known_at)
            revision = self._reads.foundation_revision_on(c, snap)
            if snap["selected"] is not None:
                revision = selected_foundation(revision, snap, snap["lo"], snap["hi"])
            sessions = self._reads.sessions_on(c, snap) if snap["selected"] is not None else []
            imports = sorted({r["evidence_id"] for r in _imports(self._reads.accepted_on(c, snap), snap)})
            return _wrap(snap, body, code, "health", health(revision, self._reads.assets_on(c, snap), sessions,
                                                            imports))
        return self._reads.within(work)


# --- pure projections --------------------------------------------------------------------------------------------


def _selected_ids(snap: dict[str, Any]) -> set[str]:
    sel = snap["selected"]
    return set() if sel is None else {str(x).lower() for x in sel["evidence_ids"]}


def _overlaps(r: dict[str, Any], snap: dict[str, Any]) -> bool:
    lo, hi, a, b = snap["lo"], snap["hi"], r.get("interval_start"), r.get("interval_end")
    return lo is not None and a is not None and b is not None and min(b, hi) > max(a, lo)


def _imports(accepted: list[dict[str, Any]], snap: dict[str, Any]) -> list[dict[str, Any]]:
    """Selected accepted non-EXCLUDED `ev_site_import` rows whose interval overlaps the window (W2-07's
    `_site_import` predicate, restricted to the selected cited set)."""
    ids = _selected_ids(snap)
    return [r for r in accepted if r.get("role") == SITE_IMPORT and r.get("use") != "EXCLUDED"
            and str(r.get("evidence_id")).lower() in ids and _overlaps(r, snap)]


def import_samples(accepted: list[dict[str, Any]], snap: dict[str, Any]) -> list[dict[str, Any]]:
    """`{source_time, import_kw, evidence_id}` for each selected GOOD `INTERVAL_MEAN` import row in kW (finite,
    non-negative, stored value verbatim), at its interval-end `source_time`, sorted `(source_time, evidence_id)`;
    only identical evidence IDs are deduplicated."""
    out, seen = [], set()
    for r in _imports(accepted, snap):
        eid = str(r["evidence_id"]).lower()
        if (eid in seen or r.get("quality") != "GOOD" or r.get("measurement") != "INTERVAL_MEAN"
                or r.get("unit") != "kW" or r.get("source_time") is None):
            continue
        try:
            value = Decimal(str(r.get("value")))
        except (InvalidOperation, ValueError):
            continue
        if not value.is_finite() or value < 0:
            continue
        seen.add(eid)
        out.append({"source_time": plain(r["source_time"]), "import_kw": str(r["value"]), "evidence_id": eid})
    return sorted(out, key=lambda x: (x["source_time"], x["evidence_id"]))


def _peak_sample(samples: list[dict[str, Any]]) -> dict[str, Any] | None:
    best = None
    for x in samples:  # already in (source_time, evidence_id) order, so a strict `>` keeps the earliest tie
        if best is None or Decimal(x["import_kw"]) > Decimal(best["import_kw"]):
            best = x
    return best


def observed_peak(samples: list[dict[str, Any]]) -> str | None:
    """The selected samples' maximum `import_kw` (stored value verbatim); null when there are none."""
    best = _peak_sample(samples)
    return None if best is None else best["import_kw"]


def peak_sample_at(samples: list[dict[str, Any]]) -> str | None:
    """The maximum sample's `source_time`; ties go to the earliest `(source_time, evidence_id)`."""
    best = _peak_sample(samples)
    return None if best is None else best["source_time"]


def peak_below_limit(peak: str | None, limit: str | None) -> str:
    if peak is None or limit is None:
        return "UNKNOWN"
    return "YES" if Decimal(peak) < Decimal(limit) else "NO"


def _site_meters(content: dict[str, Any]) -> set[str]:
    """METER components whose topology node is fed directly from a BUS node: the declared Site import meter. A
    connector-level meter is never a Site meter."""
    topology = content.get("topology") or {}
    nodes = {n.get("node_id"): n for n in topology.get("nodes") or ()}
    out = set()
    for edge in topology.get("connections") or ():
        source, target = nodes.get(edge.get("from_node")) or {}, nodes.get(edge.get("to_node")) or {}
        if source.get("node_role") == "BUS" and target.get("node_role") == "METERING":
            out.add(target.get("component_id"))
    return out


def health(revision: dict[str, Any] | None, assets: dict[str, str], sessions: list[dict[str, Any]],
           import_ids: list[str]) -> dict[str, Any]:
    """The `health` wire object: connector rows, then meter rows, from the Foundation revision's components with a
    scoped asset; no physical diagnosis, no HEALTHY state and an always-Unknown stationary battery."""
    if revision is None:
        return {"foundation_revision_id": None, "rows": [], "battery": dict(BATTERY)}
    components = [x for x in revision["content"].get("components") or () if assets.get(x.get("component_id"))]
    meters = _site_meters(revision["content"])

    def row(kind: str, x: dict[str, Any], words: tuple, session_id, ids: list[str]) -> dict[str, Any]:
        code = x["component_id"]
        state, observation, limitation, next_evidence = words
        return {"kind": kind, "label": x.get("display_name") or code, "asset_id": assets[code], "asset_code": code,
                "condition_state": state, "observation": observation, "limitation": limitation,
                "next_evidence": next_evidence, "session_id": session_id, "evidence_ids": ids}

    rows = []
    for x in sorted((x for x in components if x.get("component_type") == "EV_CONNECTOR"),
                    key=lambda x: x["component_id"]):
        faulted = sorted((y for y in sessions if y.get("connector_asset_id") == assets[x["component_id"]]
                          and y.get("fault_evidence_id") is not None),
                         key=lambda y: (plain(y["start_at"]) if y.get("start_at") is not None else "", str(y["session_id"])))
        if faulted:
            rows.append(row("CONNECTOR", x, CONNECTOR_FAULT, faulted[0]["session_id"],
                            sorted({y["fault_evidence_id"] for y in faulted})))
        else:
            rows.append(row("CONNECTOR", x, CONNECTOR_UNKNOWN, None, []))
    for x in sorted((x for x in components if x.get("component_type") == "METER"), key=lambda x: x["component_id"]):
        if x["component_id"] in meters:
            rows.append(row("SITE_METER", x, SITE_METER, None, list(import_ids)))
        else:
            rows.append(row("UNKNOWN", x, METER_UNKNOWN, None, []))
    return {"foundation_revision_id": revision["id"], "rows": rows, "battery": dict(BATTERY)}


def _wrap(snap: dict[str, Any], body: dict[str, Any], code: str, key: str, payload: dict[str, Any]) -> dict[str, Any]:
    """The shared `ev-depth-1` envelope, keys in order: schema_version, site_id, window, selection, payload, links."""
    sel = snap["selected"]
    provenance = body.get("selected_source_provenance")
    if provenance is None:
        provenance = dual_blocks(None, None)["source_provenance"]
    window = body["window"]
    query = ""
    if snap["lo"] is not None:
        query = f"?from={window['from']}&to={window['to']}"
        if window["known_at"] is not None:  # no resolved watermark: omit the parameter (W2 precedent)
            query += f"&known_at={window['known_at']}"
    base = f"/api/sites/{quote(code, safe='')}/ev"
    return {
        "schema_version": SCHEMA_VERSION,
        "site_id": body["site_id"],
        "window": {"from": window["from"], "to": window["to"], "known_at": window["known_at"],
                   "committed_watermark": plain(snap["watermark"])},
        "selection": {
            "state": snap["state"],
            "assessment_revision_id": None if sel is None else plain(sel["revision_id"]),
            "session_revision_ids": [] if sel is None else sorted(
                str(x).lower() for x in sel["result"].get("session_revision_ids") or ()),
            "accepted_evidence_ids": [] if sel is None else sorted(str(x).lower() for x in sel["evidence_ids"]),
            "source_provenance": provenance,
        },
        key: payload,
        "links": {"sessions": f"{base}/sessions{query}", "evidence_analysis": f"{base}/evidence/analysis{query}",
                  "financials": f"{base}/financials{query}"},
    }
