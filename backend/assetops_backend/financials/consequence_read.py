"""The exact Finding consequence read (S4-02b phase 2a).

Packet `tasks/S4-02b-fuel-consequence.md` "Migration, recompute and reads" and item 3. For one exact
FindingRevision of one Finding it returns the stored consequence chain (current head or an exact pinned
revision, a complete keyset-paged history), the lineage of each revision, and a currentness verdict:

- `CURRENT`: the head's consequence basis equals what the exact persisted inputs and today's price timeline
  derive now (review M1: the basis carries the selected price revision or the window-clipped price boundaries,
  never raw assignment IDs, so an unrelated later publication is not stale).
- `STALE`: a head exists but its basis differs (named reasons: price selection, technical input). The head is
  never presented as current; the work that will recompute it is listed. Stale with no such work also carries
  the typed code `NO_WORK_RECORDED` (S4-02c), never a claim that a recalculation is queued.
- `PENDING`: no consequence exists yet for this FindingRevision (work pending, or none recorded: review L4
  reads "no consequence and no work" as pending, never as absent or zero).
- `HISTORICAL`: the FindingRevision is not the Finding's latest; its consequences are audit material.

LR-01 (`D-2026-10-15-lr01-source-time-cohort`): every read also carries the shared `money_eligibility`
(`financials/money_eligibility.py`), and `presented_as_current` / `current_amount_shown` additionally require it to
be `ELIGIBLE`. A basis-CURRENT PRICED head under `PENDING_REASSESSMENT` or `WITHHELD_GENERATOR_SERIES` stays
recorded history, never a current amount. The gate fails closed: a service built without it, or a gate read that
fails, is `PENDING_REASSESSMENT`.

Amounts stay unrounded in `amount`; `display` rounds the low bound down and the high bound up to the
currency's ISO 4217 minor unit. An unknown minor unit gives no display amount (`MINOR_UNIT_UNKNOWN`), never a
guessed rounding. Nothing is summed across revisions, Findings, currencies or windows.
"""

from __future__ import annotations

import json
from decimal import ROUND_CEILING, ROUND_FLOOR, Decimal
from typing import Any
from uuid import UUID

from assetops_backend.evidence.provenance_read import consequence_provenance, finding_provenance, source_gate
from assetops_backend.financials import fuel_cost as fc
from assetops_backend.financials import money_eligibility as me
from assetops_backend.financials.recompute import ConsequenceStore, PriceStore, derive

PAGE_LIMIT = 200
NO_WORK_RECORDED = "NO_WORK_RECORDED"

# ISO 4217 minor units for the currencies a Site price may plausibly use. Anything else: no display rounding.
MINOR_UNITS: dict[str, int] = {
    "USD": 2, "EUR": 2, "GBP": 2, "CHF": 2, "CAD": 2, "AUD": 2, "NZD": 2, "ZAR": 2, "INR": 2, "CNY": 2,
    "ETB": 2, "KES": 2, "TZS": 2, "UGX": 0, "RWF": 0, "NGN": 2, "GHS": 2, "XOF": 0, "XAF": 0, "MAD": 2,
    "EGP": 2, "JPY": 0, "KRW": 0, "VND": 0, "CLP": 0, "ISK": 0, "BHD": 3, "KWD": 3, "OMR": 3, "JOD": 3,
    "TND": 3, "LYD": 3, "IQD": 3,
}

READ_LIMITATIONS = (
    "The quantity uses each power reading's as-accepted Foundation specific fuel consumption; a later "
    "Foundation correction does not requote an existing consequence.",
    "Currentness compares the stored basis with what today's exact inputs and price timeline give; the price "
    "applied is the one valid for the Finding's whole window, never today's price for old operation.",
)


def outward(value: Decimal | None, currency: str | None, rounding: str) -> str | None:
    if value is None or currency not in MINOR_UNITS:
        return None
    return format(value.quantize(Decimal(1).scaleb(-MINOR_UNITS[currency]), rounding=rounding), "f")


def display(row: dict[str, Any]) -> dict[str, Any] | None:
    """Outward display rounding of a PRICED row: low down, high up, to the currency's minor unit."""
    if row["state"] != "PRICED":
        return None
    currency = row["currency"]
    if currency not in MINOR_UNITS:
        return {"state": "MINOR_UNIT_UNKNOWN", "currency": currency, "amount_low": None, "amount_high": None,
                "note": "No ISO 4217 minor unit is known for this currency, so no rounded amount is shown."}
    return {"state": "ROUNDED_OUTWARD", "currency": currency, "minor_unit": MINOR_UNITS[currency],
            "amount_low": outward(row["amount_low"], currency, ROUND_FLOOR),
            "amount_high": outward(row["amount_high"], currency, ROUND_CEILING),
            "rule": "low rounded down and high rounded up to the currency minor unit; unrounded values in amount"}


def _text(value: Decimal | None) -> str | None:
    return None if value is None else format(value, "f")


def _id(value: Any) -> str | None:
    return None if value is None else str(value)


def _iso(value: Any) -> str | None:
    return None if value is None else fc.iso(value)


def _considered(value: Any) -> list[list[str]]:
    return json.loads(value) if isinstance(value, str) else list(value or [])


def dto(row: dict[str, Any], links: dict[str, dict[Any, list[dict[str, Any]]]]) -> dict[str, Any]:
    cid = row["id"]
    intervals = links["intervals"].get(cid, [])
    return {
        "id": str(cid), "revision_no": row["revision_no"],
        "prior_consequence_revision_id": None if row["prior_consequence_revision_id"] is None
        else str(row["prior_consequence_revision_id"]),
        "finding_id": str(row["finding_id"]), "finding_revision_id": str(row["finding_revision_id"]),
        "consequence_type": row["consequence_type"], "basis_kind": row["basis_kind"], "state": row["state"],
        "window": {"start": _iso(row["window_start"]), "end": _iso(row["window_end"]), "bounds": "[start, end)"},
        "overlap_group": row["overlap_group"], "recorded_at": _iso(row["recorded_at"]), "actor_id": row["actor_id"],
        "model": {"model_id": row["model_id"], "formula_version": row["formula_version"],
                  "parameter_version": row["parameter_version"], "parameter_sha256": row["parameter_sha256"],
                  "sfc_upper_multiplier": _text(row["sfc_upper_multiplier"]),
                  "parameter_is_reviewed": row["parameter_sha256"] == fc.PARAMETER_SHA256},
        "quantity": {"state": row["quantity_state"], "reason": row["quantity_reason"],
                     "detail": row["quantity_detail"], "unit": row["quantity_unit"],
                     "low": _text(row["quantity_low"]), "high": _text(row["quantity_high"]),
                     "high_exact": row["quantity_high_exact"],
                     "high_display": None if row["quantity_high"] is None
                     else format(row["quantity_high"].quantize(Decimal("0.01"), rounding=ROUND_CEILING), "f")},
        "price": {"state": row["price_state"], "reason": row["price_reason"],
                  "revision_id": None if row["price_revision_id"] is None else str(row["price_revision_id"]),
                  "value": _text(row["price_value"]), "currency": row["price_currency"], "unit": fc.PRICE_UNIT,
                  "considered": _considered(row["price_considered"])},
        "amount": {"low": _text(row["amount_low"]), "high": _text(row["amount_high"]), "currency": row["currency"],
                   "unrounded": True},
        "display": display(row),
        "limitations": list(row["limitations"]) + list(READ_LIMITATIONS),
        "digests": {"technical_input_sha256": row["technical_input_sha256"],
                    "consequence_basis_sha256": row["consequence_basis_sha256"]},
        "lineage": {
            "assessments": [{"assessment_revision_id": str(a["assessment_revision_id"]),
                             "analytic_run_id": str(a["analytic_run_id"]), "is_primary": a["is_primary"]}
                            for a in links["assessments"].get(cid, [])],
            "assumptions": [{"assumption_revision_id": str(a["assumption_revision_id"]),
                             "assignment_id": str(a["assignment_id"]), "role": a["role"]}
                            for a in links["assumptions"].get(cid, [])],
            "power_intervals": [{"evidence_id": str(i["evidence_id"]), "interval_start": _iso(i["interval_start"]),
                                 "interval_end": _iso(i["interval_end"]), "mean_kw": _text(i["mean_kw"]),
                                 "duration_seconds": i["duration_seconds"], "sfc_l_per_kwh": _text(i["sfc_l_per_kwh"]),
                                 "foundation_revision_id": str(i["foundation_revision_id"]),
                                 "binding_revision_id": str(i["binding_revision_id"]),
                                 "envelope_sha256": i["envelope_sha256"], "covered_spans": i["covered_spans"],
                                 "containment": i["containment"]} for i in intervals],
            "evidence_ids": [str(i["evidence_id"]) for i in intervals]},
    }


def _selection(p: fc.PriceSelection) -> dict[str, Any]:
    return {"state": p.state, "reason": p.reason, "revision_id": p.revision_id, "value": _text(p.value),
            "currency": p.currency, "considered": [list(x) for x in p.considered]}


class ConsequenceReadService:
    def __init__(self, store: Any, prices: PriceStore, *, eligibility: Any = None, provenance: Any = None) -> None:
        self._store = store
        self._prices = prices
        #: S4-05b: the exact-revision source provenance resolver; None reads every revision as UNKNOWN.
        self._provenance = provenance
        #: The shared money eligibility reader (`MoneyEligibility`); None fails closed.
        self._eligibility = eligibility

    def money_eligibility(self, tenant_id: UUID, site_id: UUID, finding_id: UUID) -> dict[str, Any]:
        if self._eligibility is None:
            return me.unavailable(str(finding_id), "ELIGIBILITY_GATE_NOT_WIRED")
        try:
            return self._eligibility.for_finding(tenant_id, site_id, finding_id)
        except Exception as exc:  # noqa: BLE001 - fail closed: no current money when the gate is unreadable
            return me.unavailable(str(finding_id), f"ELIGIBILITY_READ_FAILED: {type(exc).__name__}")

    def locate(self, tenant_id: UUID, site_id: UUID, finding_id: UUID, consequence_revision_id: UUID) -> UUID | None:
        return self._store.locate(tenant_id, site_id, finding_id, consequence_revision_id)

    def read(self, tenant_id: UUID, site_id: UUID, finding_id: UUID, finding_revision_id: UUID, *,
             finding_revision_is_latest: bool, source_open: bool, consequence_revision_id: UUID | None = None,
             after_revision_no: int = 0, limit: int = PAGE_LIMIT) -> dict[str, Any] | None:
        """None when a pinned consequence revision is not this FindingRevision's (never a fallback).

        `source_open` is the S3 source gate (review M1): while it is closed the Finding itself is audit-only, so
        its consequence is `AUDIT_ONLY` and never presented as current, whatever its basis."""
        chain = self._store.chain(tenant_id, site_id, finding_id, finding_revision_id,
                                  consequence_revision_id=consequence_revision_id,
                                  after_revision_no=after_revision_no, limit=limit)
        if consequence_revision_id is not None and chain["exact"] is None:
            return None
        head, links, pending = chain["head"], chain["links"], chain["pending"]
        work = [{"work_id": str(w["id"]), "cause": w["cause"], "attempts": w["attempts"],
                 "last_error_code": w["last_error_code"], "enqueued_at": _iso(w["enqueued_at"]),
                 "finding_revision_id": _id(w.get("finding_revision_id")),
                 "accepted_evidence_id": _id(w.get("accepted_evidence_id"))} for w in pending]
        reasons: list[str] = []
        now: fc.Consequence | None = None
        if not source_open:
            state = "AUDIT_ONLY"
            reasons.append("SOURCE_CLOSED")
            if not finding_revision_is_latest:
                reasons.append("FINDING_REVISION_SUPERSEDED")
        elif not finding_revision_is_latest:
            state = "HISTORICAL"
            reasons.append("FINDING_REVISION_SUPERSEDED")
        elif head is None:
            state = "PENDING"
            reasons.append("NOT_YET_COMPUTED" if work else "NOT_YET_COMPUTED_NO_WORK_RECORDED")
        else:
            now = derive(self._store, self._prices, tenant_id, site_id, finding_id, finding_revision_id)
            if now.basis_sha256 == head["consequence_basis_sha256"]:
                state = "CURRENT"
            else:
                state = "STALE"
                if now.technical_input_sha256 != head["technical_input_sha256"]:
                    reasons.append("TECHNICAL_INPUT_CHANGED")
                if (now.price.state, now.price.revision_id, [list(x) for x in now.price.considered]) != (
                        head["price_state"], None if head["price_revision_id"] is None
                        else str(head["price_revision_id"]), _considered(head["price_considered"])):
                    reasons.append("PRICE_SELECTION_CHANGED")
                if not reasons:
                    reasons.append("BASIS_CHANGED")
                if not work:
                    # S4-02c: stale with no unsucceeded work touching this read (e.g. a pre-0012 acceptance). A
                    # typed discrepancy only; the bridge keeps the reviewed STALE sentence (no new copy).
                    reasons.append(NO_WORK_RECORDED)
        money = self.money_eligibility(tenant_id, site_id, finding_id)
        eligible = money["state"] == me.ELIGIBLE
        selected_row = chain["exact"] if consequence_revision_id is not None else head
        selected = None if selected_row is None else dto(selected_row, links)
        is_head = selected_row is not None and head is not None and selected_row["id"] == head["id"]
        history = [dto(r, links) for r in chain["page"]]
        for row in [selected, *history]:
            if row is not None:  # S4-05b: each consequence revision keeps its own exact union provenance
                row["source_provenance"] = consequence_provenance(
                    self._provenance, tenant_id, site_id, finding_revision_id, row["id"])
        # S4-05b phase 2: the head's exact union source state is the third money gate (shared contract item 4).
        # MIXED/UNKNOWN withholds the current amount whatever CURRENT PRICED and LR eligibility say.
        if head is None:
            head_source = None
        elif selected is not None and is_head:
            head_source = selected["source_provenance"]
        else:
            head_source = consequence_provenance(self._provenance, tenant_id, site_id, finding_revision_id,
                                                 str(head["id"]))
        gate = source_gate(head_source)
        if selected is not None:
            selected["is_head"] = is_head
            selected["presented_as_current"] = (is_head and state == "CURRENT" and eligible
                                                 and gate["permits_current_money"])
            selected["historical"] = not selected["presented_as_current"]
        withheld = withheld_reasons(state, reasons, money["state"], gate, head)
        page = chain["page"]
        return {
            "consequence_selection": {
                "selected_by": "EXACT_CONSEQUENCE_REVISION_ID" if consequence_revision_id else "HEAD",
                "consequence_revision_id": None if selected is None else selected["id"],
                "head_consequence_revision_id": None if head is None else str(head["id"]),
                "finding_revision_id": str(finding_revision_id),
                "finding_revision_is_latest": finding_revision_is_latest, "source_open": source_open},
            "currentness": {
                "state": state, "reasons": reasons, "pending_work": work, "money_eligibility": money["state"],
                "current_amount_shown": selected is not None and selected["presented_as_current"],
                "source_gate": gate, "withheld_reasons": withheld,
                "derived_now": None if now is None or state == "CURRENT" else {
                    "quantity": {"state": now.quantity.state, "reason": now.quantity.reason},
                    "price": _selection(now.price),
                    "note": "What the exact inputs and today's price timeline give; not stored and not an amount "
                            "until the recompute appends it."}},
            "money_eligibility": {**money, "head_consequence_revision_id": None if head is None else str(head["id"]),
                                  "finding_revision_id": str(finding_revision_id)},
            "consequence": selected,
            "source_provenance": {
                "finding_revision": finding_provenance(self._provenance, tenant_id, site_id, finding_revision_id),
                "consequence_revision": None if selected is None else selected["source_provenance"]},
            "history": {"revisions": history, "total": chain["total"],
                        "page": {"after_revision_no": after_revision_no, "limit": limit,
                                 "next_after_revision_no": page[-1]["revision_no"] if chain["has_more"] else None}},
            "exclusions": ["No total across Findings, FindingRevisions, consequence revisions, currencies or "
                           "windows is computed.", "Necessary and Indeterminate time is never priced."],
        }


    def select_consequence_on(self, c: Any, tenant_id: UUID, site_id: UUID, finding_revision_id: UUID,
                              known_at: Any) -> dict[str, Any]:
        """W3-01 Run 6 `0a`: the consequence of one exact FindingRevision as recorded by `known_at`, on the caller's
        connection and transaction (no new snapshot, no write).

        Selects the latest fuel consequence revision of this exact tenant/Site/FindingRevision recorded by `:k`
        and applies `read`'s currentness on `c` at `:k`: the inputs are the FindingRevision and readings decided by
        `:k`, the price is the timeline known at `:k` (an old head is never repriced at today's price; a later
        consequence or price cannot change this read). States: `CURRENT`/`STALE` (basis comparison at `:k`),
        `HISTORICAL` (not the Finding's latest revision at `:k`), `PENDING` (no consequence recorded by `:k`) and
        `UNKNOWN` (the exact FindingRevision is not this Site's at `:k`, or the selected revision's price or
        lineage is missing) with no amount. The state is the basis currentness at `:k`; whether `:k` is the live
        cutoff, the money gate and the source gate are the caller's (Run 6 Blocker 2)."""
        k = known_at
        got = self._store.selected_on(c, tenant_id, site_id, finding_revision_id, k)
        rev, head, links = got["finding_revision"], got["head"], got["links"]
        out: dict[str, Any] = {
            "finding_revision_id": str(finding_revision_id), "known_at": _iso(k),
            "finding_id": None if rev is None else str(rev["finding_id"]),
            "consequence_revision_id": None if head is None else str(head["id"]),
            "revision_no": None if head is None else head["revision_no"],
            "recorded_at": None if head is None else _iso(head["recorded_at"]),
            "consequence_state": None if head is None else head["state"],
            "amount_low": None, "amount_high": None, "currency": None, "basis": None, "price": None,
            "cited": {"assessment_revision_ids": [], "assumption_revision_ids": [], "power_evidence_ids": [],
                      "price_revision_id": None}}
        reasons: list[str] = []
        if rev is None:
            out["currentness"] = {"state": "UNKNOWN", "reasons": ["FINDING_REVISION_NOT_AT_CUTOFF"]}
            return out
        if head is None:
            # W1 `read` precedence: a superseded FindingRevision is HISTORICAL even with no consequence recorded.
            superseded = str(rev["latest_id"]) != str(finding_revision_id)
            out["currentness"] = {"state": "HISTORICAL", "reasons": ["FINDING_REVISION_SUPERSEDED"]} if superseded                 else {"state": "PENDING", "reasons": ["NO_CONSEQUENCE_AT_CUTOFF"]}
            return out
        price_id = head["price_revision_id"]
        out["cited"] = {
            "assessment_revision_ids": [str(x["assessment_revision_id"]) for x in links.get("assessments", ())],
            "assumption_revision_ids": [str(x["assumption_revision_id"]) for x in links.get("assumptions", ())],
            "power_evidence_ids": [str(x["evidence_id"]) for x in links.get("intervals", ())],
            "price_revision_id": None if price_id is None else str(price_id)}
        out["basis"] = {"basis_kind": head["basis_kind"], "model_id": head["model_id"],
                        "formula_version": head["formula_version"], "parameter_sha256": head["parameter_sha256"],
                        "technical_input_sha256": head["technical_input_sha256"],
                        "consequence_basis_sha256": head["consequence_basis_sha256"]}
        out["price"] = {"state": head["price_state"], "reason": head["price_reason"],
                        "revision_id": out["cited"]["price_revision_id"], "value": _text(head["price_value"]),
                        "currency": head["price_currency"], "considered": _considered(head["price_considered"])}
        if not links.get("assessments"):
            reasons.append("CONSEQUENCE_LINEAGE_MISSING")
        if price_id is not None and not got["price_known"]:
            reasons.append("PRICE_NOT_AT_CUTOFF")
        f = None if reasons else self._store.load_input_on(c, tenant_id, site_id, rev["finding_id"],
                                                           finding_revision_id, known_at=k)
        if not reasons and f is None:
            reasons.append("FINDING_INPUT_MISSING")
        if reasons:
            out["currentness"] = {"state": "UNKNOWN", "reasons": reasons}
            return out
        if str(rev["latest_id"]) != str(finding_revision_id):
            state = "HISTORICAL"
            reasons.append("FINDING_REVISION_SUPERSEDED")
        else:
            q = fc.quantify(f)
            known = None if q.state != "AVAILABLE" else self._prices.snapshot_on(
                c, tenant_id, site_id, fc.PRICE_KEY, k, 0, 1)
            price = fc.NOT_EVALUATED if known is None else fc.select_window_price(
                known["timeline"], known["cited"], f.window_start, f.window_end)
            now = fc.consequence(f, q, price)
            if now.basis_sha256 == head["consequence_basis_sha256"]:
                state = "CURRENT"
            else:
                state = "STALE"
                if now.technical_input_sha256 != head["technical_input_sha256"]:
                    reasons.append("TECHNICAL_INPUT_CHANGED")
                if (now.price.state, now.price.revision_id, [list(x) for x in now.price.considered]) != (
                        head["price_state"], out["cited"]["price_revision_id"], _considered(head["price_considered"])):
                    reasons.append("PRICE_SELECTION_CHANGED")
                if not reasons:
                    reasons.append("BASIS_CHANGED")
        out["currentness"] = {"state": state, "reasons": reasons}
        out["amount_low"], out["amount_high"] = _text(head["amount_low"]), _text(head["amount_high"])
        out["currency"] = head["currency"]
        return out

def withheld_reasons(state: str, reasons: list[str], money_state: str, gate: dict[str, Any],
                     head: dict[str, Any] | None) -> list[str]:
    """Every failed typed gate on the current amount at once (S4-05 shared contract item 4): currentness and its
    reasons, the LR-01 money gate, the stored source gate and the head's own quantity/price state."""
    out: list[str] = []
    if state != "CURRENT":
        out += [state, *reasons]
    if money_state != me.ELIGIBLE:
        out.append(f"MONEY_{money_state}")
    if gate["reason"]:
        out.append(gate["reason"])
    if head is not None and head.get("state") not in (None, "PRICED"):
        out.append(str(head["state"]))
    return out
