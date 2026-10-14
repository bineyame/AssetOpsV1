"""`fuel-cost-1`: the reviewed conditional fuel quantity and consequence basis (S4-02b phase 1).

`D-2026-10-13-s4-bounded-financial-basis` and its S4-02b addendum; Architect rulings Q1 and C4 in
`.agent/architect-S4-02-answers.md`; packet `tasks/S4-02b-fuel-consequence.md` items 1-3.

This module does no I/O. The PostgreSQL consequence store reads the exact persisted inputs (one
FindingRevision, its primary and every supporting INTERVAL AssessmentRevision with their analytic-run input
sets, the accepted generator-power interval means of that generator, and the as-accepted Foundation/binding
revisions those readings name) and hands them here as plain public values. Lab private truth, legacy
`dispatch-2` fuel outputs, inferred constant load, interpolation and Necessary/Indeterminate time never
enter.

Quantity rule (Architect C4, fail-closed containment):
- `T_i` is the exact `[start, end)` of each Finding candidate span that is a stored `CANDIDATE` segment with
  `observed: true` in a cited INTERVAL assessment. Interval `upper_minutes`, `off_before`, `off_after` are
  never read. `C` is their union; adjacent spans form one contiguous component.
- The selected readings are the accepted, GOOD, interval-mean generator-power readings intersecting `C`. Each
  must belong to a cited analytic run's input set, lie wholly inside one contiguous component of `C`, not
  overlap another selected reading, carry one positive time-valid SFC (L/kWh) from its as-accepted Foundation
  revision and a binding revision valid for its whole interval. Their union must equal `C`.
- Any failure anywhere makes the whole quantity `QUANTITY_UNAVAILABLE` with no numeric high.
- `quantity_low = 0 L`; `quantity_high = 1.10 * sum_j(P_j kW * (b_j - a_j) h * SFC_j L/kWh)`, each reading once.

Exact arithmetic runs in `Fraction`. Hours are seconds/3600, so the exact upper is generally not a finite
decimal; it is converted to `Decimal` once at `QUANTITY_DIGITS` significant digits rounding toward +infinity
(outward for an upper bound) and the exact fraction's numerator/denominator are stored beside it. Amounts are
exact Decimal products of that stored upper and the price; display rounding happens at read time.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from decimal import ROUND_CEILING, Decimal, InvalidOperation, localcontext
from fractions import Fraction
from typing import Any, Iterable, Sequence

MODEL_ID = "fuel-cost-1"
CONSEQUENCE_TYPE = "POTENTIAL_FUEL_COST"
BASIS_KIND = "MODELLED_CONDITIONAL"
QUANTITY_UNIT = "L"
PRICE_KEY = "diesel_price_per_litre"
PRICE_UNIT = "currency/L"
POWER_ROLE = "generator_power"
POWER_UNIT = "kW"
SFC_PROPERTY = "specific-fuel-consumption"
SFC_UNIT = "L/kWh"
QUANTITY_DIGITS = 50

# The stored dispatch-3.1 segment classifications (`analytics/dispatch.py`).
CANDIDATE, NECESSARY, INDETERMINATE = "CANDIDATE_AVOIDABLE", "NECESSARY", "INDETERMINATE"

# The immutable, reviewed model parameter version (Architect Q1). Changing any field changes its digest and
# needs a new version and review; it is never edited in place to reprice a pinned consequence.
PARAMETER_VERSION: dict[str, Any] = {
    "model_id": MODEL_ID,
    "parameter_version": "fuel-cost-1/sfc-upper-multiplier/v1",
    "parameter": "sfc_upper_multiplier",
    "value": "1.10",
    "value_type": "Decimal, dimensionless",
    "inequality": "actual L/kWh <= sfc_upper_multiplier * selected time-valid Foundation specific-fuel-consumption",
    "limitation": ("An expressly conditional modelling allowance reviewed for fuel-cost-1. It is not a calibrated "
                   "or measured bound, not a physical maximum and not the legacy dispatch-2 SFC_UNCERTAINTY."),
    "scope": ("Every Site and generator asset quantified by fuel-cost-1, for any period; a calibrated or "
              "Site-specific value needs a new version and review."),
    "formula": ("quantity_low = 0 L; quantity_high = sfc_upper_multiplier * sum_j(P_j,mean kW * (b_j - a_j) h * "
                "SFC_j L/kWh) over distinct accepted GOOD generator-power interval means wholly contained in "
                "observed Candidate time and covering it without gaps"),
    "sfc_selection_rule": ("SFC_j is the single positive specific-fuel-consumption (L/kWh) of the generator "
                           "component in the reading's as-accepted Foundation revision, which must be one of the "
                           "cited analytic runs' Foundation revisions and valid over the whole reading interval; "
                           "the reading's binding revision must also be valid over the whole interval"),
    "source": ".agent/architect-S4-02-answers.md (Q1, C4); addendum to D-2026-10-13-s4-bounded-financial-basis",
    "author": "Codex Architect",
    "reviewer": ("Codex Architect ruling 2026-10-13 (.agent/architect-S4-02-answers.md Q1, C4); independent fresh "
                 "Claude review of the model and wording, ACCEPT, .agent/S4-02b-phase-1-review.md (2026-10-14)"),
    "review_date": "2026-10-14",
}
MULTIPLIER = Decimal(PARAMETER_VERSION["value"])


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=_default, ensure_ascii=True)


def sha256_canonical(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def _default(value: Any) -> str:
    if isinstance(value, datetime):
        return iso(value)
    if isinstance(value, Decimal):
        return format(value, "f")
    return str(value)


def iso(instant: datetime | None) -> str | None:
    if instant is None:
        return None
    return instant.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


PARAMETER_SHA256 = sha256_canonical(PARAMETER_VERSION)
FORMULA_VERSION = f"{MODEL_ID}+{PARAMETER_VERSION['parameter_version']}"


# ---- public inputs ---------------------------------------------------------------------------------------

@dataclass(frozen=True)
class Segment:
    start: datetime
    end: datetime
    observed: bool
    classification: str


@dataclass(frozen=True)
class AssessmentInput:
    assessment_revision_id: str
    analytic_run_id: str
    scope: str  # INTERVAL or WINDOW
    is_primary: bool
    generator_asset_id: str | None
    segments: tuple[Segment, ...]
    run_evidence_ids: frozenset[str]
    run_foundation_revision_ids: frozenset[str]


@dataclass(frozen=True)
class CandidateSpan:
    start: datetime
    end: datetime
    assessment_revision_id: str


@dataclass(frozen=True)
class PowerReading:
    evidence_id: str
    asset_id: str
    interval_start: datetime | None
    interval_end: datetime | None
    value_text: str | None
    unit: str
    quality: str
    envelope_sha256: str
    foundation_revision_id: str | None
    binding_revision_id: str | None


@dataclass(frozen=True)
class FoundationRevision:
    revision_id: str
    valid_from: datetime
    valid_to: datetime | None
    sfc: tuple[tuple[str | None, str | None], ...]  # (value_text, unit) per SFC property on the generator


@dataclass(frozen=True)
class BindingRevision:
    revision_id: str
    valid_from: datetime
    valid_to: datetime | None


@dataclass(frozen=True)
class FindingInput:
    tenant_id: str
    site_id: str
    finding_id: str
    finding_revision_id: str
    generator_asset_id: str
    window_start: datetime
    window_end: datetime
    lifecycle: str
    candidate_spans: tuple[CandidateSpan, ...]
    assessments: tuple[AssessmentInput, ...]
    readings: tuple[PowerReading, ...]
    foundations: tuple[FoundationRevision, ...]
    bindings: tuple[BindingRevision, ...]


# ---- quantity ---------------------------------------------------------------------------------------------

@dataclass(frozen=True)
class CountedInterval:
    evidence_id: str
    interval_start: datetime
    interval_end: datetime
    mean_kw: Decimal
    duration_seconds: int
    sfc_l_per_kwh: Decimal
    foundation_revision_id: str
    binding_revision_id: str
    envelope_sha256: str
    covered_spans: tuple[tuple[datetime, datetime], ...]
    containment: str = "CONTAINED"

    @property
    def litres(self) -> Fraction:
        """The interval's exact modelled litres before the multiplier: P * hours * SFC."""
        return Fraction(self.mean_kw) * Fraction(self.duration_seconds, 3600) * Fraction(self.sfc_l_per_kwh)


@dataclass(frozen=True)
class Quantity:
    state: str  # AVAILABLE or QUANTITY_UNAVAILABLE
    reason: str | None
    detail: str | None
    low: Decimal | None
    high: Decimal | None
    high_exact: Fraction | None
    intervals: tuple[CountedInterval, ...]
    spans: tuple[tuple[datetime, datetime], ...]
    examined_evidence_ids: tuple[str, ...]


def _unavailable(reason: str, detail: str, spans=(), examined=()) -> Quantity:
    return Quantity("QUANTITY_UNAVAILABLE", reason, detail, None, None, None, (), tuple(spans),
                    tuple(sorted(examined)))


def _overlaps(a0: datetime, a1: datetime | None, b0: datetime, b1: datetime | None) -> bool:
    return (a1 is None or b0 < a1) and (b1 is None or a0 < b1)


def _contains(lo: datetime, hi: datetime | None, a: datetime, b: datetime) -> bool:
    return lo <= a and (hi is None or b <= hi)


def merge(spans: Iterable[tuple[datetime, datetime]]) -> list[tuple[datetime, datetime]]:
    """Union of half-open spans; touching spans join into one contiguous component."""
    out: list[list[datetime]] = []
    for s, e in sorted(spans):
        if out and s <= out[-1][1]:
            out[-1][1] = max(out[-1][1], e)
        else:
            out.append([s, e])
    return [(s, e) for s, e in out]


def _decimal(text: str | None) -> Decimal | None:
    if text is None:
        return None
    try:
        value = Decimal(str(text))
    except (InvalidOperation, ValueError):
        return None
    return value if value.is_finite() else None


def to_decimal_ceiling(value: Fraction) -> Decimal:
    with localcontext() as ctx:
        ctx.prec = QUANTITY_DIGITS
        ctx.rounding = ROUND_CEILING
        result = Decimal(value.numerator) / Decimal(value.denominator)
    return result


def _crossing_reason(f: FindingInput, a: datetime, b: datetime, components) -> str:
    """Name what the part of `[a,b)` outside Candidate time falls into (most specific first)."""
    outside = [(a, b)]
    for cs, ce in components:
        nxt = []
        for s, e in outside:
            if s < cs:
                nxt.append((s, min(e, cs)))
            if e > ce:
                nxt.append((max(s, ce), e))
        outside = [(s, e) for s, e in nxt if s < e]
    segs = [s for x in f.assessments if x.scope == "INTERVAL" for s in x.segments]
    hit = {(s.classification, s.observed) for s in segs for o0, o1 in outside if _overlaps(s.start, s.end, o0, o1)}
    if any(not observed for _, observed in hit):
        return "INTERVAL_CROSSES_UNOBSERVED"
    if any(c == NECESSARY for c, _ in hit):
        return "INTERVAL_CROSSES_NECESSARY"
    if any(c == INDETERMINATE for c, _ in hit):
        return "INTERVAL_CROSSES_INDETERMINATE"
    return "INTERVAL_OUTSIDE_FINDING"


def quantify(f: FindingInput) -> Quantity:
    """The fail-closed `fuel-cost-1` quantity for one exact FindingRevision."""
    if f.lifecycle != "SUPPORTED":
        return _unavailable("FINDING_NOT_SUPPORTED", f"The finding revision is {f.lifecycle}, not SUPPORTED.")
    cited = {a.assessment_revision_id: a for a in f.assessments}
    intervals = [a for a in f.assessments if a.scope == "INTERVAL"]
    if sum(1 for a in intervals if a.is_primary) != 1:
        return _unavailable("ASSESSMENT_LINEAGE_INVALID", "Exactly one primary INTERVAL assessment is required.")
    if any(a.generator_asset_id != f.generator_asset_id for a in intervals):
        return _unavailable("ASSESSMENT_LINEAGE_INVALID",
                            "A cited interval assessment names a different generator than the finding.")
    if not f.candidate_spans:
        return _unavailable("NO_CANDIDATE_TIME", "The finding revision has no Candidate span.")
    for span in f.candidate_spans:
        a = cited.get(span.assessment_revision_id)
        if a is None or a.scope != "INTERVAL":
            return _unavailable("CANDIDATE_SPAN_UNVERIFIED",
                                f"Candidate span {iso(span.start)} cites an assessment the revision does not link.")
        if not any(s.start == span.start and s.end == span.end and s.classification == CANDIDATE and s.observed
                   for s in a.segments):
            return _unavailable("CANDIDATE_SPAN_UNVERIFIED",
                                f"Candidate span {iso(span.start)}-{iso(span.end)} is not a stored observed "
                                "CANDIDATE segment of its assessment.")
        if not (f.window_start <= span.start <= span.end <= f.window_end):
            return _unavailable("CANDIDATE_SPAN_UNVERIFIED", "A Candidate span lies outside the finding window.")
    raw_spans = [(s.start, s.end) for s in f.candidate_spans if s.start < s.end]  # zero-width spans hold no time
    if not raw_spans:
        return _unavailable("NO_CANDIDATE_TIME", "The finding revision has no positive-duration Candidate span.")
    components = merge(raw_spans)
    spans = tuple(sorted(set(raw_spans)))

    run_inputs = frozenset().union(*(a.run_evidence_ids for a in intervals))
    run_foundations = frozenset().union(*(a.run_foundation_revision_ids for a in intervals))
    candidates = [r for r in f.readings
                  if r.asset_id == f.generator_asset_id and r.interval_start is not None
                  and r.interval_end is not None
                  and any(_overlaps(r.interval_start, r.interval_end, s, e) for s, e in components)]
    examined = [r.evidence_id for r in candidates]
    selected = []
    for r in candidates:
        if r.quality != "GOOD":
            continue  # not an accepted good mean; coverage decides whether its time is missing
        value = _decimal(r.value_text)
        if value is None or r.unit != POWER_UNIT:
            return _unavailable("POWER_INVALID", f"Generator-power reading {r.evidence_id} has no usable kW mean.",
                                spans, examined)
        if value < 0:
            return _unavailable("POWER_NEGATIVE", f"Generator-power reading {r.evidence_id} is negative.",
                                spans, examined)
        if r.evidence_id not in run_inputs:
            return _unavailable("POWER_NOT_IN_ASSESSMENT_INPUTS",
                                f"Reading {r.evidence_id} is not in a cited analytic run's accepted input set.",
                                spans, examined)
        selected.append((r, value))
    if not selected:
        return _unavailable("POWER_MISSING", "No accepted good generator-power interval mean covers Candidate time.",
                            spans, examined)
    ordered = sorted(selected, key=lambda x: (x[0].interval_start, x[0].interval_end, x[0].evidence_id))
    for (r1, _), (r2, _) in zip(ordered, ordered[1:]):
        if r2.interval_start < r1.interval_end:
            return _unavailable("POWER_OVERLAP_CONFLICT",
                                f"Readings {r1.evidence_id} and {r2.evidence_id} overlap in time; neither is chosen.",
                                spans, examined)
    for r, _ in ordered:
        if not any(_contains(s, e, r.interval_start, r.interval_end) for s, e in components):
            return _unavailable(_crossing_reason(f, r.interval_start, r.interval_end, components),
                                f"Reading {r.evidence_id} [{iso(r.interval_start)}, {iso(r.interval_end)}) is not "
                                "wholly inside observed Candidate time.", spans, examined)
    if merge((r.interval_start, r.interval_end) for r, _ in ordered) != components:
        return _unavailable("POWER_COVERAGE_GAP", "Accepted good power means do not cover every Candidate span.",
                            spans, examined)

    foundations = {x.revision_id: x for x in f.foundations}
    bindings = {x.revision_id: x for x in f.bindings}
    counted = []
    for r, mean in ordered:
        a, b = r.interval_start, r.interval_end
        fr = foundations.get(r.foundation_revision_id or "")
        if fr is None or r.foundation_revision_id not in run_foundations:
            return _unavailable("SFC_REVISION_UNVERIFIED",
                                f"Reading {r.evidence_id}'s Foundation revision is not a cited run's revision.",
                                spans, examined)
        if not _contains(fr.valid_from, fr.valid_to, a, b):
            return _unavailable("SFC_CHANGES_WITHIN_INTERVAL",
                                f"Foundation revision {fr.revision_id} is not valid over reading {r.evidence_id}.",
                                spans, examined)
        if not fr.sfc:
            return _unavailable("SFC_MISSING", f"Foundation revision {fr.revision_id} has no generator SFC.",
                                spans, examined)
        values = {(_decimal(v), u) for v, u in fr.sfc}
        if len(values) != 1:
            return _unavailable("SFC_CONFLICT", f"Foundation revision {fr.revision_id} has conflicting SFC values.",
                                spans, examined)
        ((sfc, unit),) = values
        if unit != SFC_UNIT or sfc is None:
            return _unavailable("SFC_INVALID", f"Foundation revision {fr.revision_id} SFC is not a L/kWh number.",
                                spans, examined)
        if sfc <= 0:
            return _unavailable("SFC_NONPOSITIVE", f"Foundation revision {fr.revision_id} SFC is not positive.",
                                spans, examined)
        br = bindings.get(r.binding_revision_id or "")
        if br is None:
            return _unavailable("BINDING_MISSING", f"Reading {r.evidence_id} names no known binding revision.",
                                spans, examined)
        if not _contains(br.valid_from, br.valid_to, a, b):
            return _unavailable("BINDING_CHANGES_WITHIN_INTERVAL",
                                f"Binding revision {br.revision_id} is not valid over reading {r.evidence_id}.",
                                spans, examined)
        if (b - a) % timedelta(seconds=1):  # review L3: never shorten an upper bound's duration
            return _unavailable("INTERVAL_NOT_WHOLE_SECONDS",
                                f"Reading {r.evidence_id} does not span a whole number of seconds.", spans, examined)
        covered = tuple(s for s in spans if _overlaps(s[0], s[1], a, b))
        counted.append(CountedInterval(r.evidence_id, a, b, mean, (b - a) // timedelta(seconds=1), sfc,
                                       fr.revision_id, br.revision_id, r.envelope_sha256, covered))
    exact = Fraction(MULTIPLIER) * sum((c.litres for c in counted), Fraction(0))
    return Quantity("AVAILABLE", None, None, Decimal(0), to_decimal_ceiling(exact), exact, tuple(counted), spans,
                    tuple(sorted(examined)))


def technical_input_sha256(f: FindingInput, q: Quantity) -> str:
    """Canonical digest of the exact technical inputs (not the price)."""
    return sha256_canonical({
        "model": MODEL_ID, "parameter_sha256": PARAMETER_SHA256,
        "finding_revision_id": f.finding_revision_id, "generator_asset_id": f.generator_asset_id,
        "window": [iso(f.window_start), iso(f.window_end)],
        "assessments": sorted([a.assessment_revision_id, a.analytic_run_id, a.scope, a.is_primary]
                              for a in f.assessments),
        "candidate_spans": [[iso(s), iso(e)] for s, e in q.spans],
        "examined_evidence_ids": list(q.examined_evidence_ids),
        "intervals": [[c.evidence_id, c.envelope_sha256, iso(c.interval_start), iso(c.interval_end), c.mean_kw,
                       c.sfc_l_per_kwh, c.foundation_revision_id, c.binding_revision_id] for c in q.intervals],
        "quantity": [q.state, q.reason],
    })


# ---- price selection over the whole consequence window ------------------------------------------------------

@dataclass(frozen=True)
class PriceSelection:
    state: str  # PRICED, UNPRICED, NOT_EVALUATED
    reason: str | None
    revision_id: str | None = None
    value: Decimal | None = None
    currency: str | None = None
    # Lineage only (the link table): assignment IDs are re-issued for unchanged remainders by every later
    # publication (`assumptions.plan_assignments`), so they never enter the consequence basis (review M1).
    assignment_id: str | None = None
    # The basis content of the selection: every assignment overlapping the window at the selection cutoff, as
    # sorted `(revision_id, max(valid_from, window_start), min(valid_to, window_end))`. Stable under remainder
    # re-IDing outside the window, yet two UNPRICED selections over different price boundaries still differ.
    considered: tuple[tuple[str, str, str], ...] = ()


NOT_EVALUATED = PriceSelection("NOT_EVALUATED", "QUANTITY_UNAVAILABLE")


def select_window_price(assignments: Sequence[dict[str, Any]], revisions: dict[Any, dict[str, Any]],
                        window_start: datetime, window_end: datetime) -> PriceSelection:
    """One Site price valid for the entire `[window_start, window_end)`, from the assignments known at the
    selected recorded cutoff. Never partitions the window and never takes the current price for old time."""
    hits = [a for a in assignments if _overlaps(a["valid_from"], a["valid_to"], window_start, window_end)]
    seen = clipped(hits, window_start, window_end)
    if not hits:
        return PriceSelection("UNPRICED", "NO_PRICE")
    ordered = sorted(hits, key=lambda a: a["valid_from"])
    for x, y in zip(ordered, ordered[1:]):
        if x["valid_to"] is None or y["valid_from"] < x["valid_to"]:
            return PriceSelection("UNPRICED", "PRICE_CONFLICT", considered=seen)
    if len(hits) > 1 or not _contains(hits[0]["valid_from"], hits[0]["valid_to"], window_start, window_end):
        return PriceSelection("UNPRICED", "PRICE_SPANS_WINDOW", considered=seen)
    a = hits[0]
    rev = revisions.get(a["revision_id"])
    if rev is None:
        return PriceSelection("UNPRICED", "PRICE_REVISION_MISSING", considered=seen)
    if rev.get("assumption_key", PRICE_KEY) != PRICE_KEY or rev.get("unit") != PRICE_UNIT:
        return PriceSelection("UNPRICED", "PRICE_UNIT_MISMATCH", considered=seen)
    value = _decimal(None if rev.get("value") is None else str(rev["value"]))
    if value is None or value < 0 or not isinstance(rev.get("currency"), str) or len(rev["currency"]) != 3:
        return PriceSelection("UNPRICED", "PRICE_INVALID", considered=seen)
    return PriceSelection("PRICED", None, str(rev["id"]), value, rev["currency"], str(a.get("id")), seen)


def clipped(hits: Sequence[dict[str, Any]], window_start: datetime,
            window_end: datetime) -> tuple[tuple[str, str, str], ...]:
    """The window-clipped `(revision_id, from, to)` of each overlapping assignment, in time order (review M1)."""
    rows = [(str(a["revision_id"]), iso(max(a["valid_from"], window_start)),
             iso(window_end if a["valid_to"] is None else min(a["valid_to"], window_end))) for a in hits]
    return tuple(sorted(rows, key=lambda x: (x[1], x[2], x[0])))


# ---- consequence -----------------------------------------------------------------------------------------

LIMITATIONS = (
    "Modelled, assumption-conditioned potential fuel-cost exposure from zero to a stated upper amount.",
    "This is not measured fuel saved, not expenditure and not a physical maximum.",
    "The upper assumes actual L/kWh does not exceed 1.10 times the selected Foundation specific fuel "
    "consumption (fuel-cost-1 reviewed modelling allowance).",
    "Only observed Candidate time fully covered by accepted generator-power means is counted; Necessary and "
    "Indeterminate time is never priced.",
)


@dataclass(frozen=True)
class Consequence:
    finding: FindingInput
    quantity: Quantity
    price: PriceSelection
    state: str  # PRICED, UNPRICED, QUANTITY_UNAVAILABLE
    amount_low: Decimal | None
    amount_high: Decimal | None
    currency: str | None
    technical_input_sha256: str
    basis_sha256: str
    limitations: tuple[str, ...] = field(default=LIMITATIONS)


def consequence(f: FindingInput, q: Quantity, price: PriceSelection) -> Consequence:
    """Combine an exact quantity with the window price. A missing quantity ignores the price entirely."""
    if q.state != "AVAILABLE":
        price = NOT_EVALUATED
        state, low, high, currency = "QUANTITY_UNAVAILABLE", None, None, None
    elif price.state != "PRICED":
        state, low, high, currency = "UNPRICED", None, None, None
    else:
        with localcontext() as ctx:  # exact product: never rounded by the default 28-digit context
            ctx.prec = 4 * QUANTITY_DIGITS + 100
            amount = q.high * price.value
        state, low, high, currency = "PRICED", Decimal(0), amount, price.currency
    tech = technical_input_sha256(f, q)
    basis = sha256_canonical({
        "consequence_type": CONSEQUENCE_TYPE, "basis_kind": BASIS_KIND, "formula_version": FORMULA_VERSION,
        "parameter_sha256": PARAMETER_SHA256, "finding_revision_id": f.finding_revision_id,
        "technical_input_sha256": tech, "state": state,
        "quantity": [q.state, q.reason, q.low, q.high],
        "price": [price.state, price.reason, price.revision_id, price.value, price.currency,
                  [list(x) for x in price.considered]],
        "amount": [low, high, currency],
    })
    return Consequence(f, q, price, state, low, high, currency, tech, basis)
