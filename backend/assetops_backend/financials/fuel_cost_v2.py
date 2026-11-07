"""`fuel-cost-2`: `fuel-cost-1` plus running at 0 kW counted at a declared no-load fuel rate (FUEL-1 A1).

`.agent/build-sheet-FUEL-1.md` §4.1 (Option A, idle fuel) and the owner's answers in
`.agent/owner-fuel-scope-2026-11-07.md` ("Generic 3.3 L/h, labelled"). `fuel_cost.py` (fuel-cost-1) is never edited
in place: this is a new reviewed model with its own immutable parameter version.

Selection (`quantify`): fuel-cost-2 applies to a FindingRevision iff `fuel_cost.quantify` succeeds and at least one
counted reading's as-accepted Foundation revision declares `generator-no-load-fuel-rate` on the generator. Otherwise
the fuel-cost-1 result is returned unchanged, so every Site that declares no rate stays fuel-cost-1, byte-equal.

Inside fuel-cost-2 the fuel-cost-1 checks have already run in their order; then, over the counted readings:
- an idle reading (accepted GOOD mean exactly 0 kW, wholly inside observed Candidate time, which fuel-cost-1 already
  proved) whose Foundation revision declares no rate -> `NO_LOAD_RATE_MISSING`;
- more than one distinct declared rate (or basis) across the counted readings -> `NO_LOAD_RATE_CONFLICT`;
- the rate is not a positive L/h number -> `NO_LOAD_RATE_INVALID`;
- a declaring revision has no recognised basis property -> `NO_LOAD_RATE_BASIS_MISSING`.

`quantity_low = 0 L; quantity_high = 1.10 * [sum_loaded P_j h_j SFC_j + sum_idle h_j r_j]`. Loaded intervals compute
exactly as fuel-cost-1. This module does no I/O.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, localcontext
from fractions import Fraction
from typing import Any

from assetops_backend.financials import fuel_cost as fc

MODEL_ID = "fuel-cost-2"
NO_LOAD_PROPERTY = "generator-no-load-fuel-rate"
NO_LOAD_UNIT = "L/h"
NO_LOAD_BASIS_PROPERTY = "generator-no-load-fuel-rate-basis"
NO_LOAD_BASES = ("GENERIC_DEFAULT", "MANUFACTURER_DATASHEET", "SITE_TEST")

# The immutable, reviewed parameter version of fuel-cost-2 (FUEL-1 §4.1). Never edited in place.
PARAMETER_VERSION: dict[str, Any] = {
    "model_id": MODEL_ID,
    "parameter_version": "fuel-cost-2/sfc-upper-multiplier-and-no-load/v1",
    "parameter": "sfc_upper_multiplier",
    "value": "1.10",
    "value_type": "Decimal, dimensionless",
    "applies_to": "both terms: the loaded SFC term and the declared no-load term",
    "inequality": ("actual L/kWh <= sfc_upper_multiplier * selected time-valid Foundation specific-fuel-consumption; "
                   "actual L/h at 0 kW <= sfc_upper_multiplier * selected time-valid declared no-load fuel rate"),
    "limitation": ("An expressly conditional modelling allowance reviewed for fuel-cost-2. It is not a calibrated or "
                   "measured bound and not a physical maximum. A no-load rate whose declared basis is "
                   "GENERIC_DEFAULT is a generic figure, not this generator's own."),
    "scope": ("Every Site and generator asset whose counted readings' Foundation revisions declare a generator "
              "no-load fuel rate, for any period; a calibrated or Site-specific multiplier needs a new version and "
              "review."),
    "formula": ("quantity_low = 0 L; quantity_high = sfc_upper_multiplier * [sum_loaded(P_j,mean kW * (b_j - a_j) h "
                "* SFC_j L/kWh) + sum_idle((b_j - a_j) h * r_j L/h)] over distinct accepted GOOD generator-power "
                "interval means wholly contained in observed Candidate time and covering it without gaps; an idle "
                "interval is one whose accepted GOOD mean is exactly 0 kW, Candidate time being generator-running "
                "time by the dispatch classification"),
    "sfc_selection_rule": fc.PARAMETER_VERSION["sfc_selection_rule"],
    "no_load_selection_rule": ("r_j is the single positive generator-no-load-fuel-rate (L/h) of the generator "
                               "component in the reading's as-accepted Foundation revision, valid over the whole "
                               "reading interval, with its declared generator-no-load-fuel-rate-basis"),
    "source": ".agent/build-sheet-FUEL-1.md §4.1; .agent/owner-fuel-scope-2026-11-07.md",
    "author": "Claude Architect (FUEL-1)",
    "reviewer": ".agent/review-A1.md (FUEL-1 A1 review)",
    "review_date": "2026-11-07",
}
MULTIPLIER = Decimal(PARAMETER_VERSION["value"])
PARAMETER_SHA256 = fc.sha256_canonical(PARAMETER_VERSION)
FORMULA_VERSION = f"{MODEL_ID}+{PARAMETER_VERSION['parameter_version']}"

#: The reviewed parameter digest of each fuel model, so a read can say whether a stored row's parameters are the
#: reviewed ones of the model that row names.
REVIEWED_PARAMETER_SHA256 = {fc.MODEL_ID: fc.PARAMETER_SHA256, MODEL_ID: PARAMETER_SHA256}

LIMITATIONS = (
    fc.LIMITATIONS[0],
    fc.LIMITATIONS[1],
    "The upper assumes actual L/kWh does not exceed 1.10 times the selected Foundation specific fuel consumption, "
    "and the declared no-load fuel rate for running at 0 kW (fuel-cost-2 reviewed modelling allowance).",
    fc.LIMITATIONS[3],
    "Running at 0 kW inside Candidate time is counted at the declared no-load fuel rate; a generic rate is not this "
    "generator's own figure.",
)


# ---- public inputs and quantity ---------------------------------------------------------------------------

@dataclass(frozen=True)
class FoundationRevision(fc.FoundationRevision):
    """A fuel-cost-1 Foundation revision plus the generator's declared no-load rate(s) and basis value(s)."""
    no_load: tuple[tuple[str | None, str | None], ...] = ()  # (value_text, unit) per no-load property
    no_load_basis: tuple[str | None, ...] = ()  # value per basis property


@dataclass(frozen=True)
class CountedInterval(fc.CountedInterval):
    idle: bool = False
    no_load_l_per_h: Decimal | None = None
    no_load_basis: str | None = None

    @property
    def litres(self) -> Fraction:
        """Idle: hours * r. Loaded: fuel-cost-1's P * hours * SFC."""
        if self.idle:
            return Fraction(self.duration_seconds, 3600) * Fraction(self.no_load_l_per_h)
        return super().litres


@dataclass(frozen=True)
class Quantity(fc.Quantity):
    """A fuel-cost-2 quantity. The rate, basis and idle seconds are set only when the quantity is AVAILABLE."""
    no_load_l_per_h: Decimal | None = None
    no_load_basis: str | None = None
    idle_seconds: int | None = None
    model_id: str = MODEL_ID


def _unavailable(reason: str, detail: str, q1: fc.Quantity) -> Quantity:
    return Quantity("QUANTITY_UNAVAILABLE", reason, detail, None, None, None, (), q1.spans, q1.examined_evidence_ids)


def _declared(fr: fc.FoundationRevision | None) -> tuple[tuple[str | None, str | None], ...]:
    return tuple(getattr(fr, "no_load", ()) or ())


def selects_v2(f: fc.FindingInput, q1: fc.Quantity) -> bool:
    """fuel-cost-2 applies iff fuel-cost-1 counted readings and one of their Foundation revisions declares a rate."""
    if q1.state != "AVAILABLE":
        return False
    foundations = {x.revision_id: x for x in f.foundations}
    return any(_declared(foundations.get(c.foundation_revision_id)) for c in q1.intervals)


def quantify_v2(f: fc.FindingInput, q1: fc.Quantity) -> Quantity:
    """The fuel-cost-2 quantity over fuel-cost-1's AVAILABLE counted readings (`selects_v2(f, q1)` is true)."""
    foundations = {x.revision_id: x for x in f.foundations}
    rows = []
    for c in q1.intervals:
        fr = foundations[c.foundation_revision_id]
        rows.append((c, fr, c.mean_kw == 0))
    for c, fr, idle in rows:
        if idle and not _declared(fr):
            return _unavailable("NO_LOAD_RATE_MISSING",
                                f"Reading {c.evidence_id} runs at 0 kW but Foundation revision {fr.revision_id} "
                                "declares no generator no-load fuel rate.", q1)
    declaring = [(c, fr) for c, fr, _ in rows if _declared(fr)]
    rates = {(fc._decimal(v), u) for _, fr in declaring for v, u in _declared(fr)}
    bases = {b for _, fr in declaring for b in (getattr(fr, "no_load_basis", ()) or ())}
    if len(rates) != 1 or len(bases) > 1:
        return _unavailable("NO_LOAD_RATE_CONFLICT",
                            "The counted readings' Foundation revisions declare more than one generator no-load "
                            "fuel rate or basis.", q1)
    ((rate, unit),) = rates
    if unit != NO_LOAD_UNIT or rate is None or rate <= 0:
        return _unavailable("NO_LOAD_RATE_INVALID", "The declared generator no-load fuel rate is not a positive L/h "
                                                    "number.", q1)
    for c, fr in declaring:
        if not set(getattr(fr, "no_load_basis", ()) or ()) & set(NO_LOAD_BASES):
            return _unavailable("NO_LOAD_RATE_BASIS_MISSING",
                                f"Foundation revision {fr.revision_id} declares a no-load fuel rate without a "
                                "recognised basis.", q1)
    (basis,) = bases
    counted = tuple(CountedInterval(
        c.evidence_id, c.interval_start, c.interval_end, c.mean_kw, c.duration_seconds, c.sfc_l_per_kwh,
        c.foundation_revision_id, c.binding_revision_id, c.envelope_sha256, c.covered_spans, c.containment,
        idle, rate if _declared(fr) else None, basis if _declared(fr) else None) for c, fr, idle in rows)
    exact = Fraction(MULTIPLIER) * sum((c.litres for c in counted), Fraction(0))
    idle_seconds = sum(c.duration_seconds for c in counted if c.idle)
    return Quantity("AVAILABLE", None, None, Decimal(0), fc.to_decimal_ceiling(exact), exact, counted, q1.spans,
                    q1.examined_evidence_ids, rate, basis, idle_seconds)


def quantify(f: fc.FindingInput) -> fc.Quantity:
    """The selected fuel model's quantity: fuel-cost-2 when `selects_v2`, else fuel-cost-1's result unchanged."""
    q1 = fc.quantify(f)
    return quantify_v2(f, q1) if selects_v2(f, q1) else q1


def is_v2(q: fc.Quantity) -> bool:
    return isinstance(q, Quantity)


def technical_input_sha256(f: fc.FindingInput, q: Quantity) -> str:
    """fuel-cost-1's technical digest content plus the model id, r, the basis and the idle flags."""
    return fc.sha256_canonical({
        "model": MODEL_ID, "parameter_sha256": PARAMETER_SHA256,
        "finding_revision_id": f.finding_revision_id, "generator_asset_id": f.generator_asset_id,
        "window": [fc.iso(f.window_start), fc.iso(f.window_end)],
        "assessments": sorted([a.assessment_revision_id, a.analytic_run_id, a.scope, a.is_primary]
                              for a in f.assessments),
        "candidate_spans": [[fc.iso(s), fc.iso(e)] for s, e in q.spans],
        "examined_evidence_ids": list(q.examined_evidence_ids),
        "intervals": [[c.evidence_id, c.envelope_sha256, fc.iso(c.interval_start), fc.iso(c.interval_end),
                       c.mean_kw, c.sfc_l_per_kwh, c.foundation_revision_id, c.binding_revision_id, c.idle,
                       c.no_load_l_per_h, c.no_load_basis] for c in q.intervals],
        "no_load": [q.no_load_l_per_h, q.no_load_basis, q.idle_seconds],
        "quantity": [q.state, q.reason],
    })


@dataclass(frozen=True)
class Consequence(fc.Consequence):
    """A fuel-cost-2 consequence; its quantity is a fuel-cost-2 `Quantity`."""


def consequence(f: fc.FindingInput, q: fc.Quantity, price: fc.PriceSelection) -> fc.Consequence:
    """The consequence of the selected model: fuel-cost-1's `consequence` for a fuel-cost-1 quantity, unchanged."""
    if not is_v2(q):
        return fc.consequence(f, q, price)
    if q.state != "AVAILABLE":
        price = fc.NOT_EVALUATED
        state, low, high, currency = "QUANTITY_UNAVAILABLE", None, None, None
    elif price.state != "PRICED":
        state, low, high, currency = "UNPRICED", None, None, None
    else:
        with localcontext() as ctx:  # exact product, as fuel-cost-1
            ctx.prec = 4 * fc.QUANTITY_DIGITS + 100
            amount = q.high * price.value
        state, low, high, currency = "PRICED", Decimal(0), amount, price.currency
    tech = technical_input_sha256(f, q)
    basis = fc.sha256_canonical({
        "consequence_type": fc.CONSEQUENCE_TYPE, "basis_kind": fc.BASIS_KIND, "formula_version": FORMULA_VERSION,
        "parameter_sha256": PARAMETER_SHA256, "finding_revision_id": f.finding_revision_id,
        "technical_input_sha256": tech, "state": state,
        "quantity": [q.state, q.reason, q.low, q.high],
        "no_load": [q.no_load_l_per_h, q.no_load_basis, q.idle_seconds],
        "price": [price.state, price.reason, price.revision_id, price.value, price.currency,
                  [list(x) for x in price.considered]],
        "amount": [low, high, currency],
    })
    return Consequence(f, q, price, state, low, high, currency, tech, basis, LIMITATIONS)


def model_columns(c_: fc.Consequence) -> dict[str, Any]:
    """The stored model columns of a consequence of either model (`financial_consequence_revision`, 0011 + 0053)."""
    q = c_.quantity
    if not is_v2(q):
        return {"model_id": fc.MODEL_ID, "formula_version": fc.FORMULA_VERSION,
                "parameter_version": fc.PARAMETER_VERSION["parameter_version"],
                "parameter_sha256": fc.PARAMETER_SHA256, "sfc_upper_multiplier": fc.MULTIPLIER,
                "no_load_fuel_rate_l_per_h": None, "no_load_fuel_rate_basis": None, "idle_seconds": None}
    return {"model_id": MODEL_ID, "formula_version": FORMULA_VERSION,
            "parameter_version": PARAMETER_VERSION["parameter_version"], "parameter_sha256": PARAMETER_SHA256,
            "sfc_upper_multiplier": MULTIPLIER, "no_load_fuel_rate_l_per_h": q.no_load_l_per_h,
            "no_load_fuel_rate_basis": q.no_load_basis, "idle_seconds": q.idle_seconds}
