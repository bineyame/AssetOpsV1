"""3B7a unit 1 (spec §2.3; D-3B7A.8): the payload, canonical JSON with exact decimals and a digest.

Canonical form: sorted keys, compact separators, UTF-8 (`ensure_ascii=False`). Every `Decimal` is written as
`str(d)` and read back with `Decimal(s)` (the exponent kept: "1.3", "1.30", "1E+2"); times are UTC ISO strings; UUIDs
strings; tuples lists; mappings objects. No JSON number but `int`s. Snapshot IDs are never in a payload, so a rebuild
at the same instant gives the same bytes. Decoding checks the digest first and rebuilds the frozen dataclasses in
registry order (never the JSON object order), with tuples and `MappingProxyType` mappings.
"""
from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from datetime import datetime, timezone
from decimal import Decimal
from types import MappingProxyType
from typing import Any
from uuid import UUID

from assetops_backend.chain.ports import SiteRef
from assetops_backend.commercial.months import MonthStamp
from assetops_backend.structure.evaluate import Coverage, FactorValue, LeafValue, Missing, SiteStructure
from assetops_backend.structure.read import SiteInputs
from assetops_backend.structure.registry import REGISTRIES, Registry
from assetops_backend.structure.targets.lines import BudgetLines, TargetLine, UnusedLine
from assetops_backend.structure.targets.read import SiteTargets, TargetCheck
from assetops_backend.structure_snapshot.model import SNAPSHOT_FORMAT, PortfolioMonthSnapshot, SiteMonthSnapshot, \
    SnapshotRow

SITE_MONTH, PORTFOLIO_MONTH = "SITE_MONTH", "PORTFOLIO_MONTH"
DIGEST_MISMATCH = "snapshot payload does not match its digest"


def canonical(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def digest(payload: str) -> str:
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


# --- encoding --------------------------------------------------------------------------------------------------------

def _dec(value: Decimal | None) -> str | None:
    if value is None:
        return None
    if not isinstance(value, Decimal):  # a float or int here would not come back as written
        raise TypeError(f"a snapshot value must be a Decimal, not {type(value).__name__}")
    return str(value)


def _time(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat()


def _uuid(value: UUID | None) -> str | None:
    return None if value is None else str(value)


def _coverage(c: Coverage | None) -> dict | None:
    if c is None:
        return None
    return {"covered": c.covered, "expected": c.expected, "grades": {g: int(n) for g, n in c.grades.items()}}


def _missing(m: Missing | None) -> dict | None:
    if m is None:
        return None
    return {"record_kind": m.record_kind, "source_family": m.source_family, "cause": m.cause,
            "carried_as": m.carried_as, "blocks": list(m.blocks), "record_words": m.record_words,
            "assumption": m.assumption, "note": m.note}


def _leaf(v: LeafValue) -> dict:
    return {"value": _dec(v.value), "evidence": v.evidence, "sources": list(v.sources),
            "coverage": _coverage(v.coverage), "missing": _missing(v.missing), "currency": v.currency,
            "origins": list(v.origins)}


def _factor(v: FactorValue) -> dict:
    return {"value": _dec(v.value), "evidence": v.evidence, "sources": list(v.sources),
            "coverage": _coverage(v.coverage), "missing": _missing(v.missing),
            "missing_leaves": list(v.missing_leaves), "assumed_leaves": list(v.assumed_leaves),
            "currency": v.currency, "origins": list(v.origins), "stated": bool(v.stated),
            "computed": _dec(v.computed), "detail_missing": list(v.detail_missing)}


def _stamp(s: MonthStamp) -> dict:
    return {"site_id": _uuid(s.site_id), "period": s.period, "digest": s.digest}


def _tline(t: TargetLine) -> dict:
    return {"factor_id": t.factor_id, "value": _dec(t.value), "currency": t.currency, "unit": t.unit,
            "version_ref": t.version_ref, "line_ref": t.line_ref, "provenance": t.provenance,
            "source_system": t.source_system, "revision_id": _uuid(t.revision_id), "intake_id": _uuid(t.intake_id),
            "declared_by": t.declared_by, "person_id": _uuid(t.person_id), "declared_at": _time(t.declared_at),
            "place": t.place}


def _uline(u: UnusedLine) -> dict:
    return {"factor_id": u.factor_id, "version_ref": u.version_ref, "line_ref": u.line_ref, "reason": u.reason,
            "source_systems": list(u.source_systems)}


def _lines(b: BudgetLines) -> dict:
    return {"site_id": _uuid(b.site_id), "period": b.period, "version_ref": b.version_ref, "problem": b.problem,
            "lines": [_tline(t) for t in b.lines], "blocked": {f: note for f, note in b.blocked.items()},
            "unused": [_uline(u) for u in b.unused], "stamp": _stamp(b.stamp)}


def _check(c: TargetCheck) -> dict:
    return {"factor_id": c.factor_id, "stated": _dec(c.stated), "computed": _dec(c.computed), "currency": c.currency,
            "agrees": bool(c.agrees)}


def stamps_json(stamps: Sequence[MonthStamp]) -> str:
    """The `stamps` column: a canonical JSON array of STAMP."""
    return canonical([_stamp(s) for s in stamps])


def encode_site(tenant_id: UUID, site: SiteRef, month: str, known_at: datetime, inputs: SiteInputs,
                actual: SiteStructure, targets: SiteTargets) -> str:
    return canonical({
        "format": SNAPSHOT_FORMAT, "kind": SITE_MONTH, "tenant_id": str(tenant_id), "site_id": str(site.site_id),
        "site_code": site.site_code, "site_type": site.site_type, "timezone": site.timezone, "month": month,
        "structure_key": inputs.structure_key, "structure_version": inputs.structure_version,
        "known_at": _time(known_at),
        "inputs": {"leaves": {f: _leaf(v) for f, v in inputs.leaves.items()},
                   "stated": {f: _leaf(v) for f, v in inputs.stated.items()}},
        "actual": {f: _factor(v) for f, v in actual.values.items()},
        "targets": {"values": {f: _factor(v) for f, v in targets.structure.values.items()},
                    "currency": targets.currency, "checks": [_check(c) for c in targets.checks],
                    "lines": _lines(targets.lines)},
    })


def encode_portfolio(tenant_id: UUID, month: str, structure_key: str, structure_version: int, known_at: datetime,
                     asked: Sequence[str], sites_excluded: Mapping[str, tuple[str, ...]],
                     portfolio_lines: BudgetLines) -> str:
    return canonical({
        "format": SNAPSHOT_FORMAT, "kind": PORTFOLIO_MONTH, "tenant_id": str(tenant_id), "month": month,
        "structure_key": structure_key, "structure_version": structure_version, "known_at": _time(known_at),
        "sites": list(asked), "sites_excluded": {code: list(r) for code, r in sites_excluded.items()},
        "portfolio_lines": _lines(portfolio_lines),
    })


# --- decoding --------------------------------------------------------------------------------------------------------

def _undec(value: str | None) -> Decimal | None:
    return None if value is None else Decimal(value)


def _unuuid(value: str | None) -> UUID | None:
    return None if value is None else UUID(value)


def _uncoverage(c: dict | None) -> Coverage | None:
    if c is None:
        return None
    return Coverage(c["covered"], c["expected"], MappingProxyType(dict(c["grades"])))


def _unmissing(m: dict | None) -> Missing | None:
    if m is None:
        return None
    return Missing(m["record_kind"], m["source_family"], m["cause"], m["carried_as"], tuple(m["blocks"]),
                   m["record_words"], m["assumption"], m["note"])


def _unleaf(v: dict) -> LeafValue:
    return LeafValue(_undec(v["value"]), v["evidence"], tuple(v["sources"]), _uncoverage(v["coverage"]),
                     _unmissing(v["missing"]), v["currency"], tuple(v["origins"]))


def _unfactor(reg: Registry, f: str, v: dict) -> FactorValue:
    return FactorValue(f, _undec(v["value"]), reg.row(f).unit, v["evidence"], tuple(v["sources"]),
                       _uncoverage(v["coverage"]), _unmissing(v["missing"]), tuple(v["missing_leaves"]),
                       tuple(v["assumed_leaves"]), v["currency"], tuple(v["origins"]), v["stated"],
                       _undec(v["computed"]), tuple(v["detail_missing"]))


def unstamp(s: dict) -> MonthStamp:
    return MonthStamp(_unuuid(s["site_id"]), s["period"], s["digest"])


def stamps_from_json(text: str) -> tuple[MonthStamp, ...]:
    return tuple(unstamp(s) for s in json.loads(text))


def _untline(t: dict) -> TargetLine:
    return TargetLine(
        factor_id=t["factor_id"], value=_undec(t["value"]), currency=t["currency"], unit=t["unit"],
        version_ref=t["version_ref"], line_ref=t["line_ref"], provenance=t["provenance"],
        source_system=t["source_system"], revision_id=UUID(t["revision_id"]), intake_id=UUID(t["intake_id"]),
        declared_by=t["declared_by"], person_id=_unuuid(t["person_id"]),
        declared_at=datetime.fromisoformat(t["declared_at"]), place=t["place"])


def _unuline(u: dict) -> UnusedLine:
    return UnusedLine(u["factor_id"], u["version_ref"], u["line_ref"], u["reason"], tuple(u["source_systems"]))


def _unlines(b: dict) -> BudgetLines:
    return BudgetLines(site_id=_unuuid(b["site_id"]), period=b["period"], version_ref=b["version_ref"],
                       problem=b["problem"], lines=tuple(_untline(t) for t in b["lines"]),
                       blocked=MappingProxyType(dict(b["blocked"])), unused=tuple(_unuline(u) for u in b["unused"]),
                       stamp=unstamp(b["stamp"]))


def _uncheck(c: dict) -> TargetCheck:
    return TargetCheck(c["factor_id"], _undec(c["stated"]), _undec(c["computed"]), c["currency"], c["agrees"])


def _ordered(reg: Registry, obj: Mapping[str, Any], build) -> MappingProxyType:
    """The stored entries in registry row order, never the JSON object order."""
    return MappingProxyType({row.factor_id: build(row.factor_id, obj[row.factor_id])
                             for row in reg.rows if row.factor_id in obj})


def payload_of(row: SnapshotRow) -> dict:
    """The row's payload as plain JSON objects, after its digest check (a mismatch is never served)."""
    if digest(row.payload) != row.payload_sha256:
        raise RuntimeError(DIGEST_MISMATCH)
    return json.loads(row.payload)


def site_ref(row: SnapshotRow) -> SiteRef:
    """The Site a Site row was built for, from its payload."""
    obj = payload_of(row)
    return SiteRef(UUID(obj["tenant_id"]), UUID(obj["site_id"]), obj["site_code"], obj["site_type"], obj["timezone"])


def decode_site(row: SnapshotRow, site: SiteRef) -> SiteMonthSnapshot:
    obj = payload_of(row)
    if obj["kind"] != SITE_MONTH:
        raise RuntimeError("not a Site-month snapshot")
    key, version, code, month = obj["structure_key"], obj["structure_version"], obj["site_code"], obj["month"]
    reg = REGISTRIES[key]
    inputs = SiteInputs(code, month, key, version,
                        _ordered(reg, obj["inputs"]["leaves"], lambda f, v: _unleaf(v)),
                        _ordered(reg, obj["inputs"]["stated"], lambda f, v: _unleaf(v)))
    actual = SiteStructure(code, month, key, version, _ordered(reg, obj["actual"], lambda f, v: _unfactor(reg, f, v)))
    t = obj["targets"]
    targets = SiteTargets(
        SiteStructure(code, month, key, version, _ordered(reg, t["values"], lambda f, v: _unfactor(reg, f, v))),
        _unlines(t["lines"]), tuple(_uncheck(c) for c in t["checks"]), t["currency"])
    return SiteMonthSnapshot(row.id, row.tenant_id, site, row.period, row.as_of, row.built_by, row.closed_at_build,
                             row.stamps, inputs, actual, targets)


def decode_portfolio(row: SnapshotRow, sites: Mapping[str, SiteMonthSnapshot]) -> PortfolioMonthSnapshot:
    obj = payload_of(row)
    if obj["kind"] != PORTFOLIO_MONTH:
        raise RuntimeError("not a portfolio-month snapshot")
    asked = tuple(obj["sites"])
    excluded = obj["sites_excluded"]
    return PortfolioMonthSnapshot(
        row.id, row.tenant_id, row.period, row.as_of, row.built_by, row.closed_at_build, row.stamps, asked,
        MappingProxyType({code: tuple(excluded[code]) for code in asked if code in excluded}),
        MappingProxyType({code: sites[code] for code in asked if code in sites}),
        _unlines(obj["portfolio_lines"]))


# --- verification parts (spec §3.2) ----------------------------------------------------------------------------------

def site_parts(payload: str) -> dict[str, str]:
    """Each part of a Site payload `verify` names, as its canonical JSON."""
    obj = json.loads(payload)
    parts = {}
    for f, v in obj["inputs"]["leaves"].items():
        parts[f"inputs.leaves.{f}"] = canonical(v)
    for f, v in obj["inputs"]["stated"].items():
        parts[f"inputs.stated.{f}"] = canonical(v)
    for f, v in obj["actual"].items():
        parts[f"actual.{f}"] = canonical(v)
    for f, v in obj["targets"]["values"].items():
        parts[f"targets.values.{f}"] = canonical(v)
    for name in ("lines", "checks", "currency"):
        parts[f"targets.{name}"] = canonical(obj["targets"][name])
    return parts


def portfolio_parts(payload: str) -> dict[str, str]:
    return {"portfolio_lines": canonical(json.loads(payload)["portfolio_lines"])}


__all__ = ["PORTFOLIO_MONTH", "SITE_MONTH", "canonical", "decode_portfolio", "decode_site", "digest",
           "encode_portfolio", "encode_site", "payload_of", "portfolio_parts", "site_parts", "site_ref",
           "stamps_from_json", "stamps_json"]
