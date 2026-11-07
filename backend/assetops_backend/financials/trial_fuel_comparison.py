"""OUT-E E2: the modelled cost change after a verified generator trial (pure, exact `Fraction` arithmetic).

`.agent/build-sheet-OUT-E.md` E2, with the CC-D2 "Interfaces", "Reason conditions", "Compute" and "Output split" of
the commercial design spec. Per window: fuel = SFC x generator kWh (upper x `fuel_cost.MULTIPLIER`), cost = fuel x
diesel price, cost per kWh of feeder demand = cost / feeder kWh. The change is baseline - later, nominal and upper;
`MODELLED_IMPROVEMENT` iff the nominal change is > 0. The intervention cost is stated beside the change and never
subtracted from it (it is a total; the change is per kWh). No annualising, no realised-savings claim.

FUEL-1 A2 (`.agent/build-sheet-FUEL-1.md` §4.2): `trial-fuel-comparison/2` applies iff one positive declared
generator no-load fuel rate r (L/h) is in force over each of the two windows. Its window fuel adds the idle term,
SFC x generator kWh + r x idle seconds / 3600 (upper x the same multiplier), and a MODELLED_IMPROVEMENT result gains
the stored, priced total of the trial hour (`priced_total`, stored only when the amount is above 0). Without a rate in force over both windows the result is
`trial-fuel-comparison/1`, byte-equal to before.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from fractions import Fraction
from typing import Any, Mapping, Sequence

from assetops_backend.actions.verification_rules import fmt
from assetops_backend.financials.fuel_cost import MULTIPLIER, PriceSelection
from assetops_backend.mini_depth.rules import SfcValue

FORMULA = "trial-fuel-comparison/1"
FORMULA_V2 = "trial-fuel-comparison/2"
CLAIM_LEVEL = "POST_INTERVENTION_MODELLED"
BENEFICIARY = "MINI_OPERATOR"
LABEL = "Modelled change after the trial · not realised savings"
#: FUEL-1 A2: the basis of the stored, priced total of a `/2` MODELLED_IMPROVEMENT (`outcomes/credit.py` credits it)
PRICED_TOTAL_BASIS = "TRIAL_HOUR_MODELLED_FUEL"
REASSESSMENT_STATES = ("MODELLED_IMPROVEMENT", "MODELLED_NO_IMPROVEMENT", "UNAVAILABLE")
#: precedence order: the first that applies is the reason. 0037's `REASONS` (the table CHECK) plus A2's two, placed
#: after SFC_DIFFERS (0053 widens the CHECK; a CHECK is a set). The two A2 reasons apply to `/2` only.
REASSESSMENT_REASONS = ("OUTCOME_INCONCLUSIVE", "WINDOW_INCOMPLETE", "NOT_COMPARABLE", "SOURCE_NOT_COHERENT",
                        "EVIDENCE_REPLAY_MISMATCH", "GENERATOR_KWH_UNKNOWN", "ZERO_DEMAND", "SFC_MISSING",
                        "SFC_DIFFERS", "IDLE_SECONDS_UNKNOWN", "NO_LOAD_RATE_DIFFERS", "PRICE_MISSING",
                        "PRICE_BASIS_DIFFERS")
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
    #: FUEL-1 A2: the window's generator RUNNING seconds at exactly 0 kWh (`window_evidence`), None when unknown
    idle_seconds: int | None = None


@dataclass(frozen=True)
class NoLoadValue:
    """FUEL-1 A2: one Foundation revision's declared generator `generator-no-load-fuel-rate` in L/h over its in-force
    `[valid_from, valid_to)` (`valid_to=None` is open); the `SfcValue` shape."""

    foundation_revision_id: Any
    value_l_per_h: Decimal
    valid_from: datetime
    valid_to: datetime | None
    #: FUEL-1 A3-R G4(b): the same revision's `generator-no-load-fuel-rate-basis` (one of the three states), else None.
    #: Stored in the result's `no_load` block only; never a digest input.
    basis: str | None = None


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


def no_load_for(window: WindowFacts, rates: Sequence[NoLoadValue]) -> NoLoadValue | None:
    """FUEL-1 A2: the one positive declared no-load fuel rate in force over the whole window (`sfc_for` semantics),
    or None."""
    found = [r for r in rates if r.valid_from <= window.start and (r.valid_to is None or window.end <= r.valid_to)]
    if len(found) != 1 or not found[0].value_l_per_h > 0:
        return None
    return found[0]


def _exact(value: Any) -> Fraction | None:
    return None if value is None else Fraction(str(value))


def _pair(nominal: Fraction | None, upper: Fraction | None) -> dict[str, str | None] | None:
    return None if nominal is None else {"nominal": fmt(nominal), "upper": fmt(upper)}


def _reason(baseline: WindowFacts, later: WindowFacts, outcome: OutcomeFacts, sfc: tuple, prices: tuple,
            no_load: tuple | None = None) -> str | None:
    """`no_load` is the two windows' rates under `/2`, None under `/1` (the A2 reasons never apply to `/1`)."""
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
    if no_load is not None:
        if any(w.idle_seconds is None for w in windows):
            return "IDLE_SECONDS_UNKNOWN"
        if no_load[0].value_l_per_h != no_load[1].value_l_per_h:
            return "NO_LOAD_RATE_DIFFERS"
    if any(p.state != "PRICED" for p in prices):
        return "PRICE_MISSING"
    if prices[0].revision_id != prices[1].revision_id:
        return "PRICE_BASIS_DIFFERS"
    return None


def _window(w: WindowFacts, sfc: SfcValue | None, price: PriceSelection,
            no_load: NoLoadValue | None = None, v2: bool = False) -> dict[str, Any]:
    """One window's fuel, cost and cost per demand kWh. Under `/2` (A2) the fuel adds r x idle seconds / 3600 and is
    unknown when the idle seconds are; under `/1` the keys and values are exactly as before."""
    fuel = cost = per = None
    if w.generator_kwh is not None and sfc is not None and (
            not v2 or (w.idle_seconds is not None and no_load is not None)):
        nominal = _exact(sfc.value_l_per_kwh) * w.generator_kwh
        if v2:
            nominal += _exact(no_load.value_l_per_h) * Fraction(w.idle_seconds, 3600)
        fuel = (nominal, nominal * _exact(MULTIPLIER))
        if price.state == "PRICED" and price.value is not None:
            cost = tuple(x * _exact(price.value) for x in fuel)
            if w.feeder_demand_kwh:
                per = tuple(x / w.feeder_demand_kwh for x in cost)
    out: dict[str, Any] = {"generator_kwh": fmt(w.generator_kwh), "feeder_demand_kwh": fmt(w.feeder_demand_kwh)}
    if v2:
        out["idle_seconds"] = w.idle_seconds
    out.update({"fuel_l": _pair(*fuel) if fuel else None, "cost": _pair(*cost) if cost else None,
                "cost_per_demand_kwh": _pair(*per) if per else None, "_per": per, "_fuel": fuel, "_cost": cost})
    return out


def _iso(instant: datetime) -> str:
    """ISO 8601 UTC with `+00:00` (the verification wire form)."""
    return instant.astimezone(timezone.utc).isoformat()


def compare(baseline: WindowFacts, later: WindowFacts, outcome: OutcomeFacts, sfc_in_force: Sequence[SfcValue],
            prices: tuple[PriceSelection, PriceSelection], intervention_cost: InterventionCost,
            no_load_in_force: Sequence[NoLoadValue] = ()) -> dict[str, Any]:
    """The stored cost-check result for one final verification outcome (everything but the read-layer fields).

    A2: `/2` iff a declared no-load rate is in force over both windows (`no_load_for` gives one for each);
    otherwise `/1`, byte-equal to before."""
    sfc = (sfc_for(baseline, sfc_in_force), sfc_for(later, sfc_in_force))
    rates = (no_load_for(baseline, no_load_in_force), no_load_for(later, no_load_in_force))
    v2 = rates[0] is not None and rates[1] is not None
    reason = _reason(baseline, later, outcome, sfc, prices, rates if v2 else None)
    windows = {name: _window(w, s, p, r if v2 else None, v2)
               for name, w, s, p, r in zip(WINDOWS, (baseline, later), sfc, prices, rates)}
    change = priced_total = None
    if reason is None:
        b, l = windows["baseline"]["_per"], windows["later"]["_per"]
        nominal, upper = b[0] - l[0], b[1] - l[1]
        change = {"nominal": fmt(nominal), "upper": fmt(upper)}
        state = "MODELLED_IMPROVEMENT" if nominal > 0 else "MODELLED_NO_IMPROVEMENT"
        bw, lw = windows["baseline"], windows["later"]
        amount = bw["_cost"][0] - lw["_cost"][0] if v2 else None
        if v2 and state == "MODELLED_IMPROVEMENT" and amount > 0:
            priced_total = {"amount": fmt(amount), "currency": prices[0].currency,
                            "basis": PRICED_TOTAL_BASIS, "window": [_iso(later.start), _iso(later.end)],
                            "fuel_change_l": fmt(bw["_fuel"][0] - lw["_fuel"][0])}
    else:
        state = "UNAVAILABLE"
    for w in windows.values():
        del w["_per"], w["_fuel"], w["_cost"]
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
    formula = FORMULA_V2 if v2 else FORMULA
    basis = {
        "formula": formula, "outcome_id": outcome.outcome_id, "evidence_ids": evidence,
        "generator_kwh": {n: windows[n]["generator_kwh"] for n in WINDOWS},
        "feeder_demand_kwh": {n: windows[n]["feeder_demand_kwh"] for n in WINDOWS},
        "sfc_l_per_kwh": {n: None if s is None else fmt(_exact(s.value_l_per_kwh)) for n, s in zip(WINDOWS, sfc)},
        "price_revision_ids": {n: p.revision_id if p.state == "PRICED" else None for n, p in zip(WINDOWS, prices)},
        "intervention_cost": cost, "state": state, "reason": reason,
    }
    if v2:  # A2: the idle inputs enter the digest of a `/2` result only, so a `/1` digest is unchanged
        basis["idle_seconds"] = {n: w.idle_seconds for n, w in zip(WINDOWS, (baseline, later))}
        basis["no_load_l_per_h"] = {n: fmt(_exact(r.value_l_per_h)) for n, r in zip(WINDOWS, rates)}
    result = {
        "formula": formula, "claim_level": CLAIM_LEVEL, "beneficiary": BENEFICIARY, "state": state, "reason": reason,
        "outcome_id": outcome.outcome_id, "plan_id": outcome.plan_id,
        "origin_finding_revision_id": outcome.origin_finding_revision_id, "windows": windows,
        "change_per_demand_kwh": change, "intervention_cost": cost,
        "price": None if shared is None else {"revision_id": shared.revision_id, "value": fmt(_exact(shared.value)),
                                              "currency": shared.currency},
        "sfc": None if shared_sfc is None else {"value_l_per_kwh": fmt(_exact(shared_sfc.value_l_per_kwh))},
        "evidence_ids": evidence, "basis_sha256": sha256(basis), "label": LABEL,
    }
    if v2:
        same = rates[0].value_l_per_h == rates[1].value_l_per_h
        # FUEL-1 A3-R G4(b): the stored label of the rate (outside `basis`, so `basis_sha256` is unchanged)
        result["no_load"] = {"value_l_per_h": fmt(_exact(rates[0].value_l_per_h)),
                             "basis": rates[0].basis if rates[0].basis == rates[1].basis else None} if same else None
        if priced_total is not None:
            result["priced_total"] = priced_total
    return result


def sha256(value: Any) -> str:
    """SHA-256 of sort-keyed compact JSON."""
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
