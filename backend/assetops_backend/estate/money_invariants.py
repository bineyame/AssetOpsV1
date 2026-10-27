"""CC-R1: the no-double-count invariant over parsed estate Portfolio and Financials HTTP bodies (pure).

Commercial build spec 2026-10-27, CC-R1 "Approach and interfaces". Called by tests and by the s602b `estate`
producer case; never by the API at runtime. The member set is always `portfolio["selected_lines"]` (the full,
unpaged set), never the paged `financials["rows"]`.
"""

from __future__ import annotations

from typing import Any, Mapping

from assetops_backend.estate.financials import BENEFICIARY_OF_CATEGORY

#: Fields every member of a summed group must agree on (currency is read separately, see `_currency`).
AGREE = ("category", "window_start", "window_end", "period_kind", "assumption_fingerprint", "beneficiary")
DISJOINT = ("technical_interval_ids", "basis_evidence_ids")


def _get(body: Mapping[str, Any] | None, *path: str) -> Any:
    value: Any = body
    for key in path:
        if not isinstance(value, Mapping):
            return None
        value = value.get(key)
    return value


def _currency(line: Mapping[str, Any]) -> Any:
    return (line.get("amount") or (line.get("disclosure") or {}).get("pinned_amount") or {}).get("currency")


def _field(line: Mapping[str, Any], name: str) -> Any:
    if name == "beneficiary":
        return line.get("beneficiary", BENEFICIARY_OF_CATEGORY.get(line.get("category")))
    return line.get(name)


def double_count_violations(portfolio: Mapping[str, Any],
                            financials: Mapping[str, Any] | None = None) -> list[str]:
    """One text per violation; `[]` when no figure can count the same money twice."""
    out: list[str] = []
    totals = [("portfolio.money.estate_total", _get(portfolio, "money", "estate_total")),
              ("portfolio.summary.combined_value", _get(portfolio, "summary", "combined_value"))]
    if financials is not None:
        totals.append(("financials.summary.estate_total", _get(financials, "summary", "estate_total")))
    out += [f"TOTAL_NOT_NULL: {name}" for name, value in totals if value is not None]

    members = {line["line_key"]: line for line in portfolio.get("selected_lines") or []}
    sources = [("portfolio", _get(portfolio, "money", "groups") or [])]
    if financials is not None:
        sources.append(("financials", financials.get("groups") or []))
    for where, groups in sources:
        for group in groups:
            if group.get("amount") is None:
                continue
            gkey = group.get("group_key")
            found = []
            for key in group.get("line_keys") or []:
                if key in members:
                    found.append(members[key])
                else:
                    out.append(f"MEMBER_NOT_FOUND: {where} group {gkey} line {key}")
            for name in AGREE:
                if len({repr(_field(m, name)) for m in found}) > 1:
                    out.append(f"MEMBERS_DISAGREE: {where} group {gkey} on {name}")
            if len({repr(_currency(m)) for m in found}) > 1:
                out.append(f"MEMBERS_DISAGREE: {where} group {gkey} on currency")
            for i, a in enumerate(found):
                for b in found[i + 1:]:
                    for name in DISJOINT:
                        if set(a.get(name) or []) & set(b.get(name) or []):
                            out.append(f"MEMBERS_INTERSECT: {where} group {gkey} lines {a['line_key']} and "
                                       f"{b['line_key']} share {name}")
    return out
