"""W4-02 unit 4 step 3: pure projection of one assessed Site-local hour into an immutable revision `result`.

`D-2026-10-20-w4-02-buildspec`. Base "Wire, order and refusals" (domain card/row keys and sort orders), closure 1
Q8 (closed wire: numbers or null, bounds `{low,high}|null`, sorted `evidence_ids`, row `coverage`) and Q15
(`result.basis`), closure 2 (renewable `used_kw` is a bound at the card level; source freshness is an
evidence-basis value), closure 4 S8 (`site_timezone` in the basis) and q3 ruling 8 (`cards.outage_count` is null
unless complete supply coverage is established, which instant supply reports never give in W4-02).

No clock, no database, no envelope status precedence: currentness, provenance and the read-time comparison belong
to the read. Renewable persists one noon hour per revision; its cards and envelope status are composed by the read
over the selected days (closure 1 Q4), so the per-hour result carries the day row and that hour's values only.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any, Iterable, Sequence
from uuid import UUID

from assetops_backend.financials import fuel_cost
from assetops_backend.mini_depth import rules
from assetops_backend.mini_depth.inputs import CRITICAL_ROLES, HourInputs
from assetops_backend.mini_depth.rules import (
    Bound, Coverage, Limitation, Series, Window,
)
from assetops_backend.mini_depth.store import DOMAINS, MODEL_VERSIONS, MiniRevision


def _num(value: Decimal | int | None) -> float | int | None:
    if value is None:
        return None
    if isinstance(value, int):
        return value
    return int(value) if value == value.to_integral_value() else float(value)


def _bound(b: Bound | None) -> dict[str, Any] | None:
    return None if b is None else {"low": _num(b.low), "high": _num(b.high)}


def _ids(values: Iterable[UUID]) -> list[str]:
    return sorted({str(v) for v in values})


def _coverage(c: Coverage) -> dict[str, Any]:
    return {"required_seconds": c.required_seconds, "observed_seconds": c.observed_seconds,
            "source_count": c.source_count,
            "gaps": [{"from": fuel_cost.iso(g.start), "to": fuel_cost.iso(g.end)} for g in c.gaps]}


def _limitations(items: Sequence[Limitation]) -> list[dict[str, Any]]:
    return [{"code": l.code, "evidence_ids": _ids(l.evidence_ids)} for l in items]


def _role_series(domain: str, inputs: HourInputs) -> dict[str, list[Series]]:
    """The interval-mean roles each domain's rule requires, on the assets it judges (Q15 `role_coverage`)."""
    w, rows = inputs.window, inputs.readings
    crit = inputs.critical_asset_id

    def pinned(role: str, asset: UUID | None) -> Series:
        return rules.series(rows if asset is not None else (), role, asset, w)

    if domain == "renewable":
        return {
            rules.PV_AVAILABLE: [rules.series(rows, rules.PV_AVAILABLE, None, w, any_asset=True)],
            rules.PV_POWER: [rules.series(rows, rules.PV_POWER, None, w, any_asset=True)],
            rules.FEEDER_DEMAND: [rules.series(rows, rules.FEEDER_DEMAND, a, w)
                                  for a in sorted(set(inputs.renewable.feeder_asset_ids), key=str)],
            rules.CHARGE_REQUEST: [rules.series(rows, rules.CHARGE_REQUEST, None, w, any_asset=True)],
            **{role: [pinned(role, crit)] for role in CRITICAL_ROLES},
        }
    if domain == "service":
        out: dict[str, list[Series]] = {rules.FEEDER_DEMAND: [], rules.FEEDER_REQUESTED: [],
                                        rules.CRITICAL_REQUESTED: []}
        for load in inputs.loads:
            out[rules.FEEDER_DEMAND].append(rules.series(rows, rules.FEEDER_DEMAND, load.asset_id, w))
            if load.feeder_request_bound:
                out[rules.FEEDER_REQUESTED].append(rules.series(rows, rules.FEEDER_REQUESTED, load.asset_id, w))
            elif load.critical:
                out[rules.CRITICAL_REQUESTED].append(rules.series(rows, rules.CRITICAL_REQUESTED, load.asset_id, w))
        # Feeder demand is always required (an absent load set is a zero-coverage entry, q6 ruling 5); the request
        # roles are required only for the loads they are bound to.
        return {k: v for k, v in out.items() if v or k == rules.FEEDER_DEMAND}
    if domain == "fuel":
        fr = inputs.fuel_readings()
        return {rules.GENERATOR_POWER: [rules.series(fr, rules.GENERATOR_POWER, None, w, any_asset=True)],
                "fuel_level": [rules.series(fr, "fuel_level", None, w, any_asset=True)]}
    br = inputs.backup_readings()
    return {rules.GENERATOR_POWER: [rules.series(br, rules.GENERATOR_POWER, None, w, any_asset=True)],
            **{role: [pinned(role, crit)] for role in CRITICAL_ROLES}}


def _role_coverage(w: Window, parts: dict[str, list[Series]]) -> dict[str, dict[str, Any]]:
    """q6 ruling 5: a required role with no series (no bound asset) is a zero-coverage entry, never omitted."""
    return {role: _coverage(rules._combined(w, s, rules._sources(s)) if s else rules._coverage(w, (), set()))
            for role, s in sorted(parts.items())}


def _freshness(role_coverage: dict[str, dict[str, Any]], parts: dict[str, list[Series]],
               limitations: Sequence[Limitation]) -> str:
    """Closure 2: CURRENT iff every required role has complete accepted GOOD nonconflicting coverage at the cutoff
    (the selected rows already passed the source gate in the Q13 query); STALE is only a read-time comparison."""
    complete = bool(role_coverage) and all(c["observed_seconds"] == c["required_seconds"] and not c["gaps"]
                                           for c in role_coverage.values())
    clean = all(s.state == rules.COMPLETE and not s.unusable for ss in parts.values() for s in ss)
    blocked = any(l.code in ("CONFLICT", "REQUIRED_INPUT_UNUSABLE", "COVERAGE_GAP") for l in limitations)
    return "CURRENT" if complete and clean and not blocked else "UNKNOWN"


def assess(domain: str, inputs: HourInputs) -> Any:
    """Run the one pure domain rule on the hour's adapted inputs (pinned rows only for fuel and backup)."""
    w = inputs.window
    if domain == "renewable":
        return rules.assess_renewable_hour(inputs.local_day, w, inputs.readings, inputs.renewable)
    if domain == "service":
        return rules.assess_service_hour(w, inputs.readings, inputs.loads)
    if domain == "fuel":
        return rules.assess_fuel_hour(w, inputs.fuel_readings(), inputs.fuel)
    if domain == "backup":
        return rules.assess_backup_hour(w, inputs.observations, inputs.backup_readings(),
                                        inputs.recovery_target_min, critical_asset_id=inputs.critical_asset_id)
    raise ValueError(f"Unknown mini-depth domain {domain!r}")


def _renewable(h: rules.RenewableHour) -> dict[str, Any]:
    return {
        "hour": {"capability_kw": _bound(h.capability_kw), "used_kw": _num(h.used_kw),
                 "headroom_kw": _bound(h.headroom_kw), "decision": h.decision},
        "rows": [{"day": h.day.isoformat(), "from": fuel_cost.iso(h.window.start), "to": fuel_cost.iso(h.window.end),
                  "opportunity_kwh": _bound(h.opportunity_kwh), "constraints": list(h.constraints),
                  "decision": h.decision, "coverage": _coverage(h.coverage), "evidence_ids": _ids(h.evidence_ids)}],
        "limitations": [], "coverage": _coverage(h.coverage),
    }


def _service(h: rules.ServiceHour) -> dict[str, Any]:
    rows = sorted(h.rows, key=lambda r: (r.role != "CRITICAL", r.asset_code, str(r.asset_id)))
    return {
        "status": h.status,
        "cards": {"delivered_load_kw": _num(h.delivered_load_kw), "interruptions_seen": h.interruptions_seen,
                  "critical_delivered_kw": _num(h.critical_delivered_kw), "unserved_kwh": _num(h.unserved_kwh)},
        "rows": [{"asset_id": str(r.asset_id), "asset_code": r.asset_code, "load_label": r.load_label,
                  "role": r.role, "delivered_kw": _num(r.delivered_kw),
                  "requested_evidence_state": r.requested_evidence_state, "assessment": r.assessment,
                  "coverage": _coverage(r.coverage), "evidence_ids": _ids(r.evidence_ids)} for r in rows],
        "limitations": _limitations(h.limitations), "coverage": _coverage(h.coverage),
    }


def _fuel(h: rules.FuelHour) -> dict[str, Any]:
    order = {t: i for i, t in enumerate(rules.FUEL_TERMS)}
    return {
        "status": h.status,
        "cards": {"opening_l": _bound(h.opening_l), "deliveries_l": _bound(h.deliveries_l),
                  "expected_use_l": _bound(h.expected_use_l), "closing_l": _bound(h.closing_l),
                  "residual_l": _bound(h.residual_l)},
        "rows": [{"term": r.term, "basis": r.basis, "treatment": r.treatment, "value": _bound(r.value),
                  "coverage": _coverage(r.coverage), "evidence_ids": _ids(r.evidence_ids)} for r in sorted(h.rows, key=lambda r: order[r.term])],
        "limitations": _limitations(h.limitations), "coverage": _coverage(h.coverage),
    }


def _backup(h: rules.BackupHour) -> dict[str, Any]:
    step_order = {c: i for i, c in enumerate(rules.BACKUP_STEPS)}

    def recovery(r: rules.Recovery | None) -> dict[str, Any] | None:
        return None if r is None else {"seconds": _num(r.seconds), "target_seconds": _num(r.target_seconds)}

    chains = sorted(h.chains, key=lambda c: (c.outage_start, c.chain_id))
    return {
        "status": h.status,
        # q3 ruling 8: instant supply reports cover zero seconds, so no outage count is ever proved here. q6 ruling 6:
        # the start count is null until one witnessed request/result pair exists.
        "cards": {"outage_count": None, "start_success_count": h.start_success_count,
                  "last_witnessed_test_at": None, "critical_recovery": recovery(h.critical_recovery)},
        "rows": [{"chain_id": c.chain_id, "outage_start": fuel_cost.iso(c.outage_start),
                  "steps": [{"code": s.code, "state": s.state, "at": None if s.at is None else fuel_cost.iso(s.at),
                             "evidence_ids": _ids(s.evidence_ids)}
                            for s in sorted(c.steps, key=lambda s: step_order[s.code])],
                  "service_outcome": c.service_outcome, "result": c.result,
                  "critical_recovery": recovery(c.critical_recovery), "coverage": _coverage(c.coverage),
                  "evidence_ids": _ids(c.evidence_ids)}
                 for c in chains],
        "limitations": _limitations(h.limitations), "coverage": _coverage(h.coverage),
    }


def result(domain: str, inputs: HourInputs, hour: Any) -> dict[str, Any]:
    """The immutable revision `result`: domain body plus the Q15 `basis`."""
    body = {"renewable": _renewable, "service": _service, "fuel": _fuel, "backup": _backup}[domain](hour)
    parts = _role_series(domain, inputs)
    role_coverage = _role_coverage(inputs.window, parts)
    if domain == "backup":
        # q3 ruling 8 / q6 ruling 3: the instant state/event roles are required too and cover zero seconds (no
        # continuity rule); they count the distinct sources of usable in-hour observations of that exact role. The
        # prior supply witness and unusable rows stay cited (accepted IDs) but do not count.
        w = inputs.window
        for role in (rules.SITE_SUPPLY, rules.START_EVENT, rules.BACKUP_BUS):
            role_coverage[role] = _coverage(rules._instant_coverage(w, (
                o.source_id for o in inputs.observations
                if o.role == role and w.start <= o.source_time < w.end and not rules._bad_observation(o))))
        role_coverage = dict(sorted(role_coverage.items()))
    watermark = inputs.committed_watermark
    basis: dict[str, Any] = {
        "committed_watermark": None if watermark is None else fuel_cost.iso(watermark),
        "source_freshness": _freshness(role_coverage, parts, getattr(hour, "limitations", ())),
        "role_coverage": role_coverage,
        "foundation_revision_ids": _ids([inputs.foundation_revision_id]),
        "binding_set_revision_ids": _ids([inputs.binding_set_revision_id]),
        "accepted_evidence_ids": _ids(inputs.evidence_ids),
        "model_version": MODEL_VERSIONS[domain],
        "site_timezone": inputs.site_timezone,
    }
    if domain == "fuel":
        sfc = _ids(hour.sfc_property_revision_ids)
        basis["generator_power_evidence_ids"] = _ids(hour.generator_power_evidence_ids)
        # q6 ruling 4: the scalar is the sole SFC revision used (null for none or several); the array keeps them all.
        basis["specific_fuel_consumption_property_revision_id"] = sfc[0] if len(sfc) == 1 else None
        basis["specific_fuel_consumption_property_revision_ids"] = sfc
    return {"schema_version": "mini-depth-1", "domain": domain, **body, "basis": basis}


def project(domain: str, inputs: HourInputs) -> MiniRevision:
    """Assess and project one hour for one domain into the revision the store appends."""
    if domain not in DOMAINS:
        raise ValueError(f"Unknown mini-depth domain {domain!r}")
    hour = assess(domain, inputs)
    return MiniRevision(
        tenant_id=inputs.tenant_id, site_id=inputs.site_id, domain=domain, model_version=MODEL_VERSIONS[domain],
        window_start=inputs.window.start, window_end=inputs.window.end, knowledge_cutoff=inputs.knowledge_cutoff,
        input_sha256=inputs.input_sha256, foundation_revision_ids=(inputs.foundation_revision_id,),
        binding_set_revision_ids=(inputs.binding_set_revision_id,), result=result(domain, inputs, hour),
        evidence_ids=inputs.evidence_ids,
    )


__all__ = ["assess", "project", "result"]
