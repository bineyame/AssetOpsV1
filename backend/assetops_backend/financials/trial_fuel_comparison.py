"""OUT-E E2: the modelled cost change after a verified generator trial (pure, exact `Fraction` arithmetic).

`.agent/build-sheet-OUT-E.md` E2, with the CC-D2 "Interfaces", "Reason conditions", "Compute" and "Output split" of
the commercial design spec. Per window: fuel = SFC x generator kWh (upper x `fuel_cost.MULTIPLIER`), cost = fuel x
diesel price, cost per kWh of feeder demand = cost / feeder kWh. The change is baseline - later, nominal and upper;
`MODELLED_IMPROVEMENT` iff the nominal change is > 0. The intervention cost is stated beside the change and never
subtracted from it (it is a total; the change is per kWh). No annualising, no realised-savings claim.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime
from fractions import Fraction
from typing import Any, Mapping, Sequence

from assetops_backend.actions.verification_rules import fmt
from assetops_backend.financials.fuel_cost import MULTIPLIER, PriceSelection
from assetops_backend.mini_depth.rules import SfcValue

FORMULA = "trial-fuel-comparison/1"
CLAIM_LEVEL = "POST_INTERVENTION_MODELLED"
BENEFICIARY = "MINI_OPERATOR"
LABEL = "Modelled change after the trial · not realised savings"
REASSESSMENT_STATES = ("MODELLED_IMPROVEMENT", "MODELLED_NO_IMPROVEMENT", "UNAVAILABLE")
#: precedence order: the first that applies is the reason (equals 0037's `REASONS`, the table CHECK)
REASSESSMENT_REASONS = ("OUTCOME_INCONCLUSIVE", "WINDOW_INCOMPLETE", "NOT_COMPARABLE", "SOURCE_NOT_COHERENT",
                        "EVIDENCE_REPLAY_MISMATCH", "GENERATOR_KWH_UNKNOWN", "ZERO_DEMAND", "SFC_MISSING",
                        "SFC_DIFFERS", "PRICE_MISSING", "PRICE_BASIS_DIFFERS")
FINAL_COMPARABLE = ("VERIFIED", "INEFFECTIVE")
WINDOWS = ("baseline", "later")


@dataclass(frozen=True)
class WindowFacts:
    evidence_ids: tuple[str, ...]
    complete: bool
    generator_kwh: Fraction | None
    feeder_demand_kwh: Fraction | None
    start: datetime
    end: datetime


@dataclass(frozen=True)
class OutcomeFacts:
    outcome_id: str
    plan_id: str
    origin_finding_revision_id: str
    outcome: str  # VERIFIED | INEFFECTIVE | INCONCLUSIVE
    stored_evidence_ids: Mapping[str, tuple[str, ...]]  # outcome.basis.evidence_ids["baseline"|"later"]
    comparability_state: str  # rules.comparability(replayed windows)["state"]
    source_state: str  # rules.source_pair(replayed sources)["state"]


@dataclass(frozen=True)
class InterventionCost:
    amount: Fraction
    currency: str | None  # None = the price currency
    source: str


def sfc_for(window: WindowFacts, sfc: Sequence[SfcValue]) -> SfcValue | None:
    """The one positive SFC in force over the whole window (`mini_depth.rules._sfc_for` semantics), or None."""
    found = [s for s in sfc if s.valid_from <= window.start and (s.valid_to is None or window.end <= s.valid_to)]
    if len(found) != 1 or not found[0].value_l_per_kwh > 0:
        return None
    return found[0]


def _exact(value: Any) -> Fraction | None:
    return None if value is None else Fraction(str(value))


def _pair(nominal: Fraction | None, upper: Fraction | None) -> dict[str, str | None] | None:
    return None if nominal is None else {"nominal": fmt(nominal), "upper": fmt(upper)}


def _reason(baseline: WindowFacts, later: WindowFacts, outcome: OutcomeFacts, sfc: tuple, prices: tuple) -> str | None:
    windows = (baseline, later)
    if outcome.outcome not in FINAL_COMPARABLE:
        return "OUTCOME_INCONCLUSIVE"
    if not all(w.complete for w in windows):
        return "WINDOW_INCOMPLETE"
    if outcome.comparability_state != "PASS":
        return "NOT_COMPARABLE"
    if outcome.source_state != "PASS":
        return "SOURCE_NOT_COHERENT"
    if any(set(w.evidence_ids) != set(outcome.stored_evidence_ids.get(name) or ())
           for name, w in zip(WINDOWS, windows)):
        return "EVIDENCE_REPLAY_MISMATCH"
    if any(w.generator_kwh is None for w in windows):
        return "GENERATOR_KWH_UNKNOWN"
    if any(not w.feeder_demand_kwh for w in windows):  # 0 (or, unreachable once complete, unknown)
        return "ZERO_DEMAND"
    if any(s is None for s in sfc):
        return "SFC_MISSING"
    if sfc[0].value_l_per_kwh != sfc[1].value_l_per_kwh:
        return "SFC_DIFFERS"
    if any(p.state != "PRICED" for p in prices):
        return "PRICE_MISSING"
    if prices[0].revision_id != prices[1].revision_id:
        return "PRICE_BASIS_DIFFERS"
    return None


def _window(w: WindowFacts, sfc: SfcValue | None, price: PriceSelection) -> dict[str, Any]:
    fuel = cost = per = None
    if w.generator_kwh is not None and sfc is not None:
        nominal = _exact(sfc.value_l_per_kwh) * w.generator_kwh
        fuel = (nominal, nominal * _exact(MULTIPLIER))
        if price.state == "PRICED" and price.value is not None:
            cost = tuple(x * _exact(price.value) for x in fuel)
            if w.feeder_demand_kwh:
                per = tuple(x / w.feeder_demand_kwh for x in cost)
    return {"generator_kwh": fmt(w.generator_kwh), "feeder_demand_kwh": fmt(w.feeder_demand_kwh),
            "fuel_l": _pair(*fuel) if fuel else None, "cost": _pair(*cost) if cost else None,
            "cost_per_demand_kwh": _pair(*per) if per else None, "_per": per}


def compare(baseline: WindowFacts, later: WindowFacts, outcome: OutcomeFacts, sfc_in_force: Sequence[SfcValue],
            prices: tuple[PriceSelection, PriceSelection], intervention_cost: InterventionCost) -> dict[str, Any]:
    """The stored cost-check result for one final verification outcome (everything but the read-layer fields)."""
    sfc = (sfc_for(baseline, sfc_in_force), sfc_for(later, sfc_in_force))
    reason = _reason(baseline, later, outcome, sfc, prices)
    windows = {name: _window(w, s, p) for name, w, s, p in zip(WINDOWS, (baseline, later), sfc, prices)}
    change = None
    if reason is None:
        b, l = windows["baseline"]["_per"], windows["later"]["_per"]
        nominal, upper = b[0] - l[0], b[1] - l[1]
        change = {"nominal": fmt(nominal), "upper": fmt(upper)}
        state = "MODELLED_IMPROVEMENT" if nominal > 0 else "MODELLED_NO_IMPROVEMENT"
    else:
        state = "UNAVAILABLE"
    for w in windows.values():
        del w["_per"]
    shared = prices[0] if prices[0].state == "PRICED" and prices[1].state == "PRICED" and \
        prices[0].revision_id == prices[1].revision_id else None
    price_currency = shared.currency if shared else next((p.currency for p in prices if p.state == "PRICED"), None)
    currency = intervention_cost.currency or price_currency
    if intervention_cost.currency is not None and price_currency is not None and intervention_cost.currency != \
            price_currency:
        raise ValueError("the intervention cost currency must equal the price currency")
    cost = {"amount": fmt(intervention_cost.amount), "currency": currency, "source": intervention_cost.source}
    evidence = {name: sorted(w.evidence_ids) for name, w in zip(WINDOWS, (baseline, later))}
    shared_sfc = sfc[0] if sfc[0] is not None and sfc[1] is not None and \
        sfc[0].value_l_per_kwh == sfc[1].value_l_per_kwh else None
    basis = {
        "formula": FORMULA, "outcome_id": outcome.outcome_id, "evidence_ids": evidence,
        "generator_kwh": {n: windows[n]["generator_kwh"] for n in WINDOWS},
        "feeder_demand_kwh": {n: windows[n]["feeder_demand_kwh"] for n in WINDOWS},
        "sfc_l_per_kwh": {n: None if s is None else fmt(_exact(s.value_l_per_kwh)) for n, s in zip(WINDOWS, sfc)},
        "price_revision_ids": {n: p.revision_id if p.state == "PRICED" else None for n, p in zip(WINDOWS, prices)},
        "intervention_cost": cost, "state": state, "reason": reason,
    }
    return {
        "formula": FORMULA, "claim_level": CLAIM_LEVEL, "beneficiary": BENEFICIARY, "state": state, "reason": reason,
        "outcome_id": outcome.outcome_id, "plan_id": outcome.plan_id,
        "origin_finding_revision_id": outcome.origin_finding_revision_id, "windows": windows,
        "change_per_demand_kwh": change, "intervention_cost": cost,
        "price": None if shared is None else {"revision_id": shared.revision_id, "value": fmt(_exact(shared.value)),
                                              "currency": shared.currency},
        "sfc": None if shared_sfc is None else {"value_l_per_kwh": fmt(_exact(shared_sfc.value_l_per_kwh))},
        "evidence_ids": evidence, "basis_sha256": sha256(basis), "label": LABEL,
    }


def sha256(value: Any) -> str:
    """SHA-256 of sort-keyed compact JSON."""
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
