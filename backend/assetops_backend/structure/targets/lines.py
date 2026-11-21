"""5a unit 1 (spec `specs/5a-targets/spec.md` §2; D-5A.1 to D-5A.4, D-5A.14): budget lines as target lines.

A Site-month's (or the portfolio's) `BUDGET_LINE` lines from 3A4 are classified in a fixed order: two versions
govern nothing (rule 1); a line naming no registry factor is unused (rule 2); two lines, or 3A4's duplicate, for one
factor are never summed or picked (rule 3); a money line needs a currency and a quantity line must not have one
(rule 4); the rest are used (rule 5). Each used line names the intake that wrote its latest revision as its declarer.
The month's open or closed state is never read: budgets are declared ahead (handshake R5).
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from types import MappingProxyType
from typing import Mapping
from uuid import UUID

from assetops_backend.commercial.model import IntakeSummary, RevisionRow
from assetops_backend.commercial.months import DUPLICATE_DECLARATION, CommercialMonths, MonthAmounts, MonthLine, \
    MonthStamp
from assetops_backend.commercial.store import CommercialStore
from assetops_backend.structure.registry import REGISTRIES, Registry
from assetops_contracts.canonical import loads_canonical, parse_record

BUDGET_LINE = "BUDGET_LINE"
BUDGET_VERSIONS = "BUDGET_VERSIONS"
NOT_A_FACTOR = "NOT_A_FACTOR"
CURRENCY_MISSING = "CURRENCY_MISSING"
CURRENCY_ON_QUANTITY = "CURRENCY_ON_QUANTITY"
LEAF, NODE = "LEAF", "NODE"
_PERSON = re.compile(r"person:([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})")


@dataclass(frozen=True)
class TargetLine:
    factor_id: str
    value: Decimal
    currency: str | None
    unit: str | None
    version_ref: str
    line_ref: str | None
    provenance: str
    source_system: str
    revision_id: UUID
    intake_id: UUID
    declared_by: str            # the intake's entered_by
    person_id: UUID | None      # from "person:<uuid>", else None
    declared_at: datetime       # the intake's entered_at
    place: str                  # "LEAF" or "NODE"


@dataclass(frozen=True)
class UnusedLine:
    factor_id: str
    version_ref: str
    line_ref: str | None
    reason: str
    source_systems: tuple[str, ...]


@dataclass(frozen=True)
class BudgetLines:
    site_id: UUID | None
    period: str
    version_ref: str | None     # the governing version; None with no lines or a version problem
    problem: str | None         # "BUDGET_VERSIONS:<a>,<b>" or None
    lines: tuple[TargetLine, ...]          # sorted by factor_id
    blocked: Mapping[str, str]             # factor_id -> note; a factor with a line that cannot be used
    unused: tuple[UnusedLine, ...]         # sorted by (factor_id, version_ref, line_ref or "", reason)
    stamp: MonthStamp


def _dims(line: MonthLine) -> tuple[str, str, str | None]:
    dims = dict(line.dims)
    return dims["factor_id"], dims["version_ref"], dims["line_ref"]


def _unused(line: MonthLine, reason: str) -> UnusedLine:
    factor, version, line_ref = _dims(line)
    return UnusedLine(factor, version, line_ref, reason, line.source_systems)


def _classify(reg: Registry, candidates: list[MonthLine]):
    """Rules 1 to 5 of spec §2: (version_ref, problem, used candidates, blocked, unused)."""
    factors = {row.factor_id: row for row in reg.rows}
    blocked: dict[str, str] = {}
    unused: list[UnusedLine] = []
    versions = sorted({_dims(c)[1] for c in candidates})
    if len(versions) >= 2:  # rule 1: never pick a version (D-5A.1)
        for c in candidates:
            unused.append(_unused(c, BUDGET_VERSIONS))
            if _dims(c)[0] in factors:
                blocked[_dims(c)[0]] = BUDGET_VERSIONS
        return None, f"{BUDGET_VERSIONS}:" + ",".join(versions), [], blocked, unused
    by_factor: dict[str, list[MonthLine]] = {}
    for c in candidates:
        factor = _dims(c)[0]
        if factor not in factors:  # rule 2
            unused.append(_unused(c, NOT_A_FACTOR))
        else:
            by_factor.setdefault(factor, []).append(c)
    used: list[MonthLine] = []
    for factor, lines in by_factor.items():
        if len(lines) >= 2 or lines[0].value is None:  # rule 3: never summed or picked (D-5A.3)
            unused.extend(_unused(c, DUPLICATE_DECLARATION) for c in lines)
            blocked[factor] = DUPLICATE_DECLARATION
            continue
        line, money = lines[0], factors[factor].unit.has_money_dimension
        reason = CURRENCY_MISSING if money and line.currency is None else (
            CURRENCY_ON_QUANTITY if not money and line.currency is not None else None)
        if reason is not None:  # rule 4
            unused.append(_unused(line, reason))
            blocked[factor] = reason
            continue
        used.append(line)  # rule 5
    return (versions[0] if versions else None), None, used, blocked, unused


def _key(factor: str, version: str, line_ref: str | None, currency: str | None, provenance: str) -> tuple:
    return factor, version, line_ref, currency, provenance


class BudgetLineReader:
    def __init__(self, months: CommercialMonths, store: CommercialStore) -> None:
        self._months = months
        self._store = store

    def site(self, tenant_id: UUID, site_id: UUID, period: str, *, structure_key: str,
             known_at: datetime | None = None) -> BudgetLines:
        amounts = self._months.site_month(tenant_id, site_id, period, known_at=known_at)
        rows = self._store.latest_revisions(tenant_id, site_id=site_id, kind=BUDGET_LINE, recognition_period=period,
                                            known_at=known_at)
        return self._read(tenant_id, site_id, period, structure_key, amounts, rows)

    def portfolio(self, tenant_id: UUID, period: str, *, structure_key: str,
                  known_at: datetime | None = None) -> BudgetLines:
        amounts = self._months.portfolio_month(tenant_id, period, known_at=known_at)
        rows = self._store.latest_revisions(tenant_id, kind=BUDGET_LINE, recognition_period=period,
                                            known_at=known_at)
        return self._read(tenant_id, None, period, structure_key, amounts,
                          tuple(r for r in rows if r.site_id is None))

    def _read(self, tenant_id: UUID, site_id: UUID | None, period: str, structure_key: str, amounts: MonthAmounts,
              rows: tuple[RevisionRow, ...]) -> BudgetLines:
        reg = REGISTRIES[structure_key]
        candidates = [line for line in amounts.lines if line.kind == BUDGET_LINE]
        version_ref, problem, used, blocked, unused = _classify(reg, candidates)
        revisions: dict[tuple, list[RevisionRow]] = {}
        for row in rows:  # the declarer join (D-5A.2)
            record = parse_record(loads_canonical(row.canonical.encode("utf-8")))
            body = record.body
            key = _key(body["factor_id"], body["version_ref"], body.get("line_ref"), body.get("currency"),
                       row.provenance)
            revisions.setdefault(key, []).append(row)
        summaries: dict[UUID, IntakeSummary | None] = {}
        lines: list[TargetLine] = []
        for line in used:
            factor, version, line_ref = _dims(line)
            found = revisions.get(_key(factor, version, line_ref, line.currency, line.provenance), [])
            if len(found) != 1:
                raise RuntimeError("budget line without its revision")
            rev = found[0]
            if rev.intake_id not in summaries:
                summaries[rev.intake_id] = self._store.intake(tenant_id, rev.intake_id)
            summary = summaries[rev.intake_id]
            if summary is None:
                raise RuntimeError("budget line without its intake")
            entered_by = summary.intake.entered_by
            person = _PERSON.fullmatch(entered_by)
            lines.append(TargetLine(
                factor_id=factor, value=line.value, currency=line.currency, unit=line.unit, version_ref=version,
                line_ref=line_ref, provenance=line.provenance, source_system=rev.source_system, revision_id=rev.id,
                intake_id=rev.intake_id, declared_by=entered_by,
                person_id=UUID(person.group(1)) if person is not None else None,
                declared_at=summary.intake.entered_at, place=LEAF if reg.row(factor).is_leaf else NODE))
        return BudgetLines(
            site_id=site_id, period=period, version_ref=version_ref, problem=problem,
            lines=tuple(sorted(lines, key=lambda t: t.factor_id)),
            blocked=MappingProxyType(dict(sorted(blocked.items()))),
            unused=tuple(sorted(unused, key=lambda u: (u.factor_id, u.version_ref, u.line_ref or "", u.reason))),
            stamp=amounts.stamp)
