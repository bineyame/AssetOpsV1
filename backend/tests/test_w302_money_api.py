"""W3-02 commit 3: the estate Financials root over a fake one-transaction snapshot (no database).

Router refusals with `groups/exclusions/diagnostics:null`, the literal empty-scope vector, exact selected heads per
domain (W1 priced, cold product exposure and recorded repair unpriced, EV gross tariff), the closure 2 ordered
eligibility table, the transient EV `STALE_BASIS` guard (no invented head), historical/pending lines, overlap by
group/IDs/citations, Decimal sums, and page-invariant groups/exclusions with the 5-part cursor. The persisted proof
is `test_w302_money_comparability_postgres.py`.
"""

from __future__ import annotations

import json
from datetime import timedelta
from decimal import Decimal
from urllib.parse import urlencode

import pytest

from assetops_backend.estate import financials
from assetops_backend.estate.financials import compare, decide
from assetops_backend.estate.scope import decode_cursor
from test_w302_evidence_api import (
    A, CO, CUT, D0, EVS, MG, SITES, T, WINDOW, FakeSnapshot, FakeStore, client, pin)

SUPPORTED = {"classification": "REGISTERED_SIMULATION", "state": "REGISTERED_SIMULATION", "source_ids": [], "evidence_ids": [],
             "basis_sha256": "sha256:" + "0" * 64, "reasons": []}
NULLS = {"rows": None, "total_count": None, "groups": None, "exclusions": None, "diagnostics": None}


def w1_head(frid, cid, *, state="PRICED", currentness="CURRENT", low="0.00", high="3.97", power=(A[45],)):
    return {"consequence_revision_id": cid, "consequence_state": state, "currentness": {"state": currentness},
            "window_start": "2026-10-13T06:00:00Z", "window_end": "2026-10-13T09:00:00Z",
            "quantity_low": "0", "quantity_high": "4.1", "quantity_unit": "L", "overlap_group": f"g-{cid}",
            "amount_low": low, "amount_high": high, "currency": "USD",
            "price": {"state": "PUBLISHED", "value": "0.97", "currency": "USD"},
            "cited": {"power_evidence_ids": list(power), "price_revision_id": A[44], "assumption_revision_ids": []}}


def cold_row(cid, kind, frid, *, state="UNPRICED"):
    return {"id": cid, "kind": kind, "state": state, "quantity_bounds": {"low": "12", "high": "30"},
            "quantity_unit": "degC_min", "amount_bounds": {"low": None, "high": None}, "currency": None,
            "reason": None, "overlap_group": f"c-{cid}", "limitation": "Product exposure is not priced.",
            "finding_revision_id": frid, "window_start": "2026-10-13T00:00:00Z", "window_end": "2026-10-14T00:00:00Z",
            "counted": kind == "PRODUCT_EXPOSURE",
            "exact_basis": {"evidence_ids": [A[10]], "assumption_revision_ids": [A[41]]}}


def ev_head(rid, *, state="ESTIMATED", amount="8.33250000", currency="KES", sessions=(A[40],), evidence=(A[30],),
            group="ev-g"):
    return {"revision_id": rid, "revision_no": 1, "state": state, "reason": "ELIGIBLE_COMPLETE_INTERVALS"
            if state == "ESTIMATED" else state, "quantity_kwh": "30.000", "tariff_revision_id": A[43],
            "tariff_value": "0.27775", "currency": currency, "amount": amount, "overlap_group": group,
            "recorded_at": "2026-10-13T10:00:00Z", "tariff_recorded_at": None, "source_gate": None,
            "session_revision_ids": list(sessions), "evidence_ids": list(evidence), "limitation": None}


class MoneySnapshot(FakeSnapshot):
    def __init__(self, *args, w1=None, cold=None, ev=None, money="ELIGIBLE", classification="SUPPORTED",
                 cold_withheld=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.w1 = {A[21]: w1_head(A[21], A[31])} if w1 is None else w1
        self.cold = [cold_row(A[32], "PRODUCT_EXPOSURE", A[22]), cold_row(A[33], "RECORDED_REPAIR", A[22])] \
            if cold is None else cold
        self.ev = {"guard": None, "consequence": ev_head(A[34]), "history": []} if ev is None else ev
        self.money, self.classification, self.cold_withheld = money, classification, cold_withheld

    def consequence(self, t, s, frid, k):
        return self.w1.get(frid, {"consequence_revision_id": None})

    def consequence_provenance(self, t, s, cid, frid, cited):
        cls = SUPPORTED["state"] if self.classification == "SUPPORTED" else self.classification
        return {**SUPPORTED, "classification": cls, "state": cls, "evidence_ids": list(cited)}

    def eligibility(self, t, s, finding_id, k):
        return {"state": self.money}

    def cited_provenance(self, t, s, cited, selected):
        return {**SUPPORTED, "evidence_ids": list(cited)}

    def cold_money(self, t, s, p, k):
        rows = self.cold if p is self.cold_pins[0] else []
        return {"withheld": self.cold_withheld, "hold": None, "consequences": rows,
                "finding_ids": {A[22]: A[23]}}

    def ev_money(self, p):
        return {**self.ev, "window_start": "2026-10-13T08:00:00Z", "window_end": "2026-10-13T09:05:00Z",
                "session_revision_ids": list(self.sessions),  # c3-q2(6): the pinned selected session revisions
                "historical_label": "Historical as of 2026-10-13T00:00:00Z"}  # ignored (c1-q1)


@pytest.fixture(autouse=True)
def money_coverage(monkeypatch):
    states = {}

    def fake(snap, t, s, domain, from_, to, k):
        rows = [{"finding_id": A[24], "finding_revision_id": A[21], "source_provenance": {"evidence_ids": [A[20]]}},
                {"finding_id": A[25], "finding_revision_id": A[26], "source_provenance": {"evidence_ids": []}}]
        state = states.get(s, "HISTORICAL" if snap.basis_historical else "CURRENT")
        return {"selection_id": None, "watermark": CUT, "match_state": "COMPLETE", "job_state": "SETTLED",
                "source_freshness": "RECENT", "state": state, "rows": rows if domain == "mini_grid" else [],
                "selected_assessment_revision_ids": [A[1]]}
    monkeypatch.setattr(financials, "site_coverage", fake)
    return states


def fin(c, query):
    return c.get("/api/estate/financials?" + (query if isinstance(query, str) else urlencode(query)))


def body_of(snap, **query):
    response = fin(client(FakeStore(snap)), {**WINDOW, "limit": 100, **query})
    assert response.status_code == 200, response.text
    return response.json()


def test_w302_money_api_errors_and_cutoff() -> None:
    store = FakeStore(MoneySnapshot(sites=[]))
    response = fin(client(store, authenticate=lambda r: 401), "from=bad")
    assert response.status_code == 401 and response.headers["www-authenticate"] == "Bearer"
    assert response.json() == {"detail": {"code": "UNAUTHENTICATED", "message": "Sign in to read estate records.",
                                          **NULLS}} and store.calls == 0
    c = client(store)
    for query, code in [("to=2026-10-20T00:00:00Z", "INVALID_WINDOW"), (urlencode(WINDOW) + "&lens=x",
                        "INVALID_CURSOR"), (urlencode(WINDOW) + "&limit=101", "INVALID_LIMIT"),
                        (urlencode(WINDOW) + "&cursor=abc", "INVALID_CURSOR"),
                        (urlencode({**WINDOW, "known_at": "2026-10-21T00:00:00Z"}), "INVALID_KNOWN_AT")]:
        response = fin(c, query)
        assert response.status_code == 422 and response.json()["detail"] == {
            "code": code, "message": response.json()["detail"]["message"], **NULLS}, query
    no_db = fin(client(store, service=False), WINDOW)
    assert no_db.status_code == 503 and no_db.json()["detail"] == {
        "code": "ESTATE_STORE_UNAVAILABLE", "message": "Estate records could not be read.", **NULLS}
    assert fin(c, {**WINDOW, "known_at": "2026-10-20T12:00:00Z"}).json() == {
        "schema_version": "estate-financials-1",
        "scope": {"tenant_id": str(T), "authorized_site_count": 0, "covered_site_count": 0,
                  "access_basis": "sha256:df70eb2392c008ed241b3251f79f7ed2c9130159aa73c0c4d96cf7ec36fceea1"},
        "window": {"from": "2026-10-13T00:00:00Z", "to": "2026-10-20T00:00:00Z", "bounds": "[from, to)",
                   "known_at": "2026-10-20T12:00:00Z"},
        "status": "EMPTY_SCOPE", "coverage": {"state": "EMPTY", "sites": []},
        "summary": {"eligible_line_count": 0, "unpriced_line_count": 0, "withheld_line_count": 0,
                    "estate_total": None, "estate_total_state": "NO_ESTATE_TOTAL"},
        "order": "window_start desc nulls last, site_code_key asc, site_id asc, category asc, line_key asc",
        "total_count": 0, "rows": [], "groups": [], "exclusions": [], "diagnostics": [], "next_cursor": None,
        "selection_token": "sha256:5944cb919416dc307e7ce4b40c4cc4d047bcee9ec2d72b1a41815716b1d8765e"}
    # An explicit earlier estate cutoff: every line HISTORICAL with no current amount (c1-q1), `as_of` present.
    old = body_of(MoneySnapshot(historical=True), known_at="2026-10-20T06:00:00Z")
    assert old["status"] == "HISTORICAL" and old["summary"]["as_of"] == "2026-10-20T06:00:00Z"
    assert {r["eligibility"] for r in old["rows"]} == {"HISTORICAL"} and all(r["amount"] is None for r in old["rows"])
    assert all(g["amount"] is None and g["state"] != "COMPARABLE" for g in old["groups"])


def test_w302_money_exact_selected_heads_and_unpriced_cold() -> None:
    body = body_of(MoneySnapshot())
    rows = {r["line_key"]: r for r in body["rows"]}
    assert sorted(rows) == sorted([f"mini_grid:{A[31]}", f"cold_chain:{A[32]}", f"cold_chain:{A[33]}",
                                   f"ev_charging:{A[34]}"])  # the W1 Finding without a head gives no line
    w1, product, repair, ev = (rows[k] for k in (f"mini_grid:{A[31]}", f"cold_chain:{A[32]}", f"cold_chain:{A[33]}",
                                                 f"ev_charging:{A[34]}"))
    assert (w1["category"], w1["eligibility"], w1["amount"]) == (
        "CANDIDATE_OPERATING_COST_EXPOSURE", "ELIGIBLE", {"low": "0.00", "high": "3.97", "currency": "USD"})
    assert w1["technical_interval_ids"] == [A[45]] and w1["assumption_revision_ids"] == [A[44]]
    assert w1["links"] == {"site": "/sites/KOBO-001", "bridge": "/sites/KOBO-001/financials",
                           "evidence": "/sites/KOBO-001/evidence", "current_view_label": "Opens current Site view"}
    assert (product["category"], product["eligibility"], product["amount"]) == (
        "POTENTIAL_PRODUCT_EXPOSURE", "UNPRICED", None)
    assert (repair["category"], repair["eligibility"]) == ("RECORDED_REPAIR", "UNPRICED")
    assert product["finding_id"] == A[23] and product["quantity"] == {"low": "12", "high": "30", "unit": "degC_min"}
    assert product["links"]["bridge"].startswith("/sites/COLD%201/financials?from=")
    assert (ev["category"], ev["eligibility"], ev["period_kind"]) == ("GROSS_TARIFF_SCENARIO", "ELIGIBLE",
                                                                      "SCENARIO_WINDOW")
    assert ev["finding_id"] is None and ev["amount"] == {"low": "8.33250000", "high": "8.33250000", "currency": "KES"}
    assert ev["limit"] == "Gross scenario only; not cash collected."
    assert ev["links"]["bridge"].startswith("/sites/EV-1/ev/financials?from=")
    states = {g["category"]: g["state"] for g in body["groups"]}
    assert states == {"CANDIDATE_OPERATING_COST_EXPOSURE": "SINGLE_LINE", "POTENTIAL_PRODUCT_EXPOSURE": "INELIGIBLE",
                      "RECORDED_REPAIR": "INELIGIBLE", "GROSS_TARIFF_SCENARIO": "SINGLE_LINE"}
    assert body["summary"] == {"eligible_line_count": 2, "unpriced_line_count": 2, "withheld_line_count": 0,
                               "estate_total": None, "estate_total_state": "NO_ESTATE_TOTAL"}
    # STALE_BASIS: the transient guard is never a line, token revision or candidate; coverage is unknown.
    guard = {"revision_id": None, "state": "WITHHELD", "reason": "STALE_BASIS"}
    stale = body_of(MoneySnapshot(ev={"guard": "STALE_BASIS", "consequence": guard, "history": []}))
    assert not [r for r in stale["rows"] if r["domain"] == "ev_charging"]
    assert [g for g in stale["groups"] if g["category"] == "GROSS_TARIFF_SCENARIO"] == [{
        "group_key": None, "category": "GROSS_TARIFF_SCENARIO", "currency": None, "window_start": None,
        "window_end": None, "period_kind": None, "assumption_fingerprint": None, "state": "UNKNOWN_COVERAGE",
        "line_keys": [], "amount": None, "reason_codes": ["NO_LINES", "UNKNOWN_COVERAGE"]}]
    # With an older stored head, only that exact head shows, withheld.
    older = body_of(MoneySnapshot(ev={"guard": "STALE_BASIS", "consequence": guard, "history": [ev_head(A[35])]}))
    line = next(r for r in older["rows"] if r["domain"] == "ev_charging")
    assert (line["line_key"], line["eligibility"], line["amount"]) == (f"ev_charging:{A[35]}", "WITHHELD", None)


def test_w302_money_historical_pending_and_no_gap_rows(money_coverage) -> None:
    pending = body_of(MoneySnapshot(ev_pins=[pin(D0, "PENDING_RECOMPUTE")], cold_withheld=True,
                                    money="PENDING_REASSESSMENT"))
    by = {r["domain"]: r for r in pending["rows"]}
    assert by["mini_grid"]["eligibility"] == by["cold_chain"]["eligibility"] == by["ev_charging"]["eligibility"] \
        == "PENDING" and all(r["amount"] is None for r in pending["rows"])
    assert by["ev_charging"]["disclosure"]["pinned_amount"]["low"] == "8.33250000"  # pinned value in disclosure only
    assert next(g for g in pending["groups"] if g["category"] == "GROSS_TARIFF_SCENARIO")["state"] == \
        "UNKNOWN_COVERAGE"
    assert pending["summary"]["withheld_line_count"] == 4 and pending["summary"]["eligible_line_count"] == 0
    # A W2 HISTORICAL pin on a live basis is the valid as-of selection (c1 r1 M1): the line stays eligible.
    live = body_of(MoneySnapshot(ev_pins=[pin(D0, "HISTORICAL")]))
    assert next(r for r in live["rows"] if r["domain"] == "ev_charging")["eligibility"] == "ELIGIBLE"
    # Ordered table: source UNKNOWN/MIXED before WITHHELD; W1 non-eligible money gate is WITHHELD.
    for cls, reason in (("UNKNOWN", "UNKNOWN_SOURCE"), ("MIXED", "MIXED_SOURCE")):
        w1 = next(r for r in body_of(MoneySnapshot(classification=cls))["rows"] if r["domain"] == "mini_grid")
        assert (w1["eligibility"], w1["reason_codes"]) == ("WITHHELD", [reason])
    gated = next(r for r in body_of(MoneySnapshot(money="WITHHELD_GENERATOR_SERIES"))["rows"]
                 if r["domain"] == "mini_grid")
    assert (gated["eligibility"], gated["reason_codes"]) == ("WITHHELD", ["WITHHELD"])
    quantity = body_of(MoneySnapshot(w1={A[21]: w1_head(A[21], A[31], state="QUANTITY_UNAVAILABLE")}))
    assert next(r for r in quantity["rows"] if r["domain"] == "mini_grid")["reason_codes"] == ["BASIS_NOT_PROVEN"]
    # c3-q2(2) / M1: pending cold consequence work at K makes product coverage unknown on an otherwise covered Site.
    def product(**kw):
        body = body_of(MoneySnapshot(**kw))
        return ([g for g in body["groups"] if g["category"] == "POTENTIAL_PRODUCT_EXPOSURE"],
                [r for r in body["rows"] if r["category"] == "POTENTIAL_PRODUCT_EXPOSURE"])
    groups, _ = product(cold=[], cold_withheld=True)
    assert [(g["state"], g["reason_codes"]) for g in groups] == [("UNKNOWN_COVERAGE", ["NO_LINES", "UNKNOWN_COVERAGE"])]
    groups, lines = product(cold_withheld=True)
    assert [(g["state"], g["amount"]) for g in groups] == [("UNKNOWN_COVERAGE", None)] and lines
    assert all(g["state"] != "NO_LINES" and "NO_LINES" not in g["reason_codes"] for g in groups)
    groups, _ = product(cold=[], cold_withheld=False)  # covered-state results are retained
    assert [(g["state"], g["reason_codes"]) for g in groups] == [("NO_LINES", ["NO_LINES"])]
    groups, _ = product(cold_withheld=False)
    assert [g["state"] for g in groups] == ["INELIGIBLE"]
    # No gap rows: a mini-grid Site with no heads has no line; its category gets the NO_LINES sentinel.
    none = body_of(MoneySnapshot(w1={}))
    assert not [r for r in none["rows"] if r["domain"] == "mini_grid"]
    assert next(g for g in none["groups"] if g["category"] == "CANDIDATE_OPERATING_COST_EXPOSURE")["state"] == \
        "NO_LINES"


def _eligible(key, *, tech, cited, group=None, low="1.10", high="2.20", fp="sha256:" + "a" * 64):
    return {"line_key": key, "category": "GROSS_TARIFF_SCENARIO", "_currency": "KES",
            "window_start": "2026-10-13T08:00:00Z", "window_end": "2026-10-13T09:05:00Z",
            "period_kind": "SCENARIO_WINDOW", "assumption_fingerprint": fp, "technical_interval_ids": tech,
            "basis_evidence_ids": cited, "overlap_group": group, "eligibility": "ELIGIBLE", "reason_codes": [],
            "amount": {"low": low, "high": high, "currency": "KES"}}


def test_w302_money_overlap_by_group_ids_and_citations() -> None:
    cases = {"disjoint": ({}, "COMPARABLE", []), "group": ({"group": "same"}, "OVERLAPPING_BASIS",
                                                             ["OVERLAPPING_BASIS"]),
             "technical": ({"tech": [A[1]]}, "OVERLAPPING_BASIS", ["OVERLAPPING_BASIS"]),
             "cited": ({"cited": [A[3]]}, "OVERLAPPING_BASIS", ["OVERLAPPING_BASIS"]),
             "unproven": ({"tech": []}, "OVERLAPPING_BASIS", ["BASIS_NOT_PROVEN"])}
    for name, (change, state, reasons) in cases.items():
        a = _eligible("ev_charging:a", tech=[A[1]], cited=[A[3]], group="same" if "group" in change else None)
        b = _eligible("ev_charging:b", tech=change.get("tech", [A[2]]), cited=change.get("cited", [A[4]]),
                      group=change.get("group"))
        groups, exclusions, _ = compare([a, b], {"GROSS_TARIFF_SCENARIO": True})
        assert groups[0]["state"] == state, name
        if state == "COMPARABLE":
            assert groups[0]["amount"] == {"low": "2.20", "high": "4.40", "currency": "KES"} and exclusions == []
        else:
            assert groups[0]["amount"] is None and {a["eligibility"], b["eligibility"]} == {"CONFLICT"}, name
            assert set(reasons) <= set(groups[0]["reason_codes"]) and len(exclusions) == 2, name
            # c3-q2(3): missing proof is BASIS_NOT_PROVEN at the group, a proven collision OVERLAPPING_BASIS; each
            # involved line is CONFLICT with line reason OVERLAPPING_BASIS.
            other = "OVERLAPPING_BASIS" if reasons == ["BASIS_NOT_PROVEN"] else "BASIS_NOT_PROVEN"
            assert other not in groups[0]["reason_codes"], name
            assert all("OVERLAPPING_BASIS" in x["reason_codes"] for x in (a, b)), name
    # One line's own technical and cited arrays being equal is no collision (closure 4).
    same = _eligible("ev_charging:a", tech=[A[1]], cited=[A[1]])
    other = _eligible("ev_charging:b", tech=[A[2]], cited=[A[2]])
    assert compare([same, other], {"GROSS_TARIFF_SCENARIO": True})[0][0]["state"] == "COMPARABLE"
    # An ineligible member makes the partition INELIGIBLE even with two eligible lines; coverage wins over all.
    third = {**_eligible("ev_charging:c", tech=[A[5]], cited=[A[6]]), "eligibility": "WITHHELD",
             "reason_codes": ["WITHHELD"], "amount": None}
    a, b = _eligible("ev_charging:a", tech=[A[1]], cited=[A[3]]), _eligible("ev_charging:b", tech=[A[2]], cited=[A[4]])
    assert compare([a, b, third], {"GROSS_TARIFF_SCENARIO": True})[0][0]["state"] == "INELIGIBLE"
    # c3-q2(3): a withheld line sharing the eligible lines' basis is never marked CONFLICT.
    a, b = _eligible("ev_charging:a", tech=[A[1]], cited=[A[3]]), _eligible("ev_charging:b", tech=[A[1]], cited=[A[4]])
    held = {**_eligible("ev_charging:c", tech=[A[1]], cited=[A[3]]), "eligibility": "WITHHELD",
            "reason_codes": ["WITHHELD"], "amount": None}
    compare([a, b, held], {"GROSS_TARIFF_SCENARIO": True})
    assert (a["eligibility"], b["eligibility"], held["eligibility"]) == ("CONFLICT", "CONFLICT", "WITHHELD")
    assert held["reason_codes"] == ["WITHHELD"]
    a, b = _eligible("ev_charging:a", tech=[A[1]], cited=[A[3]]), _eligible("ev_charging:b", tech=[A[2]], cited=[A[4]])
    groups = compare([a, b], {"GROSS_TARIFF_SCENARIO": False})[0]
    assert groups[0]["state"] == "UNKNOWN_COVERAGE" and groups[0]["amount"] is None
    # Different currencies are two partitions plus a MIXED_CURRENCY diagnostic, never a merged total.
    a, b = _eligible("ev_charging:a", tech=[A[1]], cited=[A[3]]), _eligible("ev_charging:b", tech=[A[2]], cited=[A[4]])
    b.update(_currency="USD", amount={"low": "1", "high": "1", "currency": "USD"})
    groups, _, diagnostics = compare([a, b], {"GROSS_TARIFF_SCENARIO": True})
    assert [g["state"] for g in groups] == ["SINGLE_LINE", "SINGLE_LINE"]
    assert diagnostics == [{"category": "GROSS_TARIFF_SCENARIO", "code": "MIXED_CURRENCY",
                            "line_keys": ["ev_charging:a", "ev_charging:b"]}]


def test_w302_money_decimal_and_display_rounding() -> None:
    a = _eligible("ev_charging:a", tech=[A[1]], cited=[A[3]], low="0.1", high="0.30000001")
    b = _eligible("ev_charging:b", tech=[A[2]], cited=[A[4]], low="0.2", high="3.97")
    groups = compare([a, b], {"GROSS_TARIFF_SCENARIO": True})[0]
    assert groups[0]["amount"] == {"low": "0.3", "high": "4.27000001", "currency": "KES"}  # unrounded Decimal
    assert Decimal(groups[0]["amount"]["low"]) == Decimal("0.1") + Decimal("0.2")
    body = body_of(MoneySnapshot())
    text = json.dumps(body)
    w1 = next(r for r in body["rows"] if r["domain"] == "mini_grid")
    assert w1["amount"]["low"] == "0.00" and isinstance(w1["amount"]["high"], str) and "3.97" in text
    assert not any(isinstance(v, float) for r in body["rows"] for v in (r["amount"] or {}).values())
    # Normalized economic assumption values: 0.27775 and 0.277750 give one fingerprint, a different rate another.
    fp = financials.assumption_fingerprint
    assert fp("GROSS_TARIFF_SCENARIO", "KES", "kWh", "0.27775", "K") == fp("GROSS_TARIFF_SCENARIO", "KES", "kWh",
                                                                            "0.277750", "K")
    assert fp("GROSS_TARIFF_SCENARIO", "KES", "kWh", "0.3", "K") != fp("GROSS_TARIFF_SCENARIO", "KES", "kWh",
                                                                        "0.27775", "K")
    assert fp("GROSS_TARIFF_SCENARIO", None, "kWh", "0.3", "K") is None


def test_w302_money_page_invariant_exclusions() -> None:
    snap = MoneySnapshot()
    full = body_of(snap)
    c = client(FakeStore(snap))
    seen, cursor, pages = [], None, 0
    while True:
        query = {**WINDOW, "limit": 1, **({"cursor": cursor} if cursor else {})}
        page = fin(c, query).json()
        assert (page["groups"], page["exclusions"], page["diagnostics"], page["total_count"]) == (
            full["groups"], full["exclusions"], full["diagnostics"], full["total_count"])
        assert page["selection_token"] == full["selection_token"]
        seen += [r["line_key"] for r in page["rows"]]
        pages += 1
        cursor = page["next_cursor"]
        if cursor is None:
            break
        after = decode_cursor("financials", cursor)["after"]
        assert decode_cursor("financials", cursor)["kind"] == "financials" and len(after) == 5
    assert seen == [r["line_key"] for r in full["rows"]] and pages == full["total_count"] == 4
    starts = [r["window_start"] for r in full["rows"]]
    assert starts == sorted(starts, reverse=True)  # window_start desc
    # The token carries the selected consequence and assumption IDs; a changed head is the 409 fence.
    first = fin(c, {**WINDOW, "limit": 1}).json()
    changed = MoneySnapshot(cold=[cold_row(A[36], "PRODUCT_EXPOSURE", A[22])])
    response = fin(client(FakeStore(changed)), {**WINDOW, "limit": 1, "cursor": first["next_cursor"]})
    assert response.status_code == 409 and response.json()["detail"]["code"] == "ESTATE_BASIS_CHANGED"
    # Excluded lines each have one entry with that partition's group key, sorted by line key.
    keys = {g["group_key"] for g in full["groups"]}
    assert [e["line_key"] for e in full["exclusions"]] == sorted(e["line_key"] for e in full["exclusions"])
    assert all(e["group_key"] in keys and e["reason_codes"] for e in full["exclusions"])


def test_w302_money_decide_order() -> None:
    base = dict(historical=False, pending=False, provenance=SUPPORTED, withheld=False, unknown=False,
                unpriced=False, eligible=True)
    assert decide(**base) == ("ELIGIBLE", [])
    assert decide(**{**base, "historical": True, "pending": True}) == ("HISTORICAL", ["HISTORICAL"])
    assert decide(**{**base, "pending": True, "withheld": True}) == ("PENDING", ["PENDING"])
    assert decide(**{**base, "withheld": True, "unpriced": True}) == ("WITHHELD", ["WITHHELD"])
    assert decide(**{**base, "unknown": True, "unpriced": True}) == ("UNKNOWN", ["BASIS_NOT_PROVEN"])
    assert decide(**{**base, "unpriced": True}) == ("UNPRICED", ["UNPRICED"])
    assert decide(**{**base, "eligible": False}) == ("UNKNOWN", ["BASIS_NOT_PROVEN"])
    assert MG and CO and EVS and SITES and timedelta  # fixture Sites shared with the Evidence suite


def test_w302_money_w1_price_unit_limit_and_citation_union() -> None:
    """c3-q2(5): the W1 fingerprint uses the selected `price.state` and `price.value` with the economic unit
    `currency/L` (not the quantity unit `L`); the selected head's limitations join with `; `; citations are the
    selected Finding citations plus `cited.power_evidence_ids`, which are also the technical IDs."""
    head = {**w1_head(A[21], A[31], power=(A[45], A[46])), "limitations": ["First stored limit.", "Second one."]}
    body = body_of(MoneySnapshot(w1={A[21]: head}))
    w1 = next(r for r in body["rows"] if r["domain"] == "mini_grid")
    fp = financials.assumption_fingerprint
    assert w1["assumption_fingerprint"] == fp("CANDIDATE_OPERATING_COST_EXPOSURE", "USD", "currency/L", "0.97",
                                              "PUBLISHED")
    assert w1["assumption_fingerprint"] != fp("CANDIDATE_OPERATING_COST_EXPOSURE", "USD", "L", "0.97", "PUBLISHED")
    assert w1["limit"] == "First stored limit.; Second one."
    assert w1["basis_evidence_ids"] == sorted([A[20], A[45], A[46]])
    assert w1["technical_interval_ids"] == sorted([A[45], A[46]])
    bare = next(r for r in body_of(MoneySnapshot())["rows"] if r["domain"] == "mini_grid")
    assert bare["limit"] is None  # no stored limitations


def test_w302_money_ev_session_only_change_moves_token_and_fences() -> None:
    """c3-q2(6): the Financials token's `selected_assessment_revision_ids` carry every pinned selected EV window's
    session revision IDs, so a session-only change moves the token and fences a cursor, also with no stored head."""
    for ev in (None, {"guard": None, "consequence": None, "history": []}):
        label = "head" if ev is None else "no head"
        before = MoneySnapshot(ev=ev, sessions=(A[40],))
        after = MoneySnapshot(ev=ev, sessions=(A[41],))
        first = fin(client(FakeStore(before)), {**WINDOW, "limit": 1}).json()
        assert first["next_cursor"], label
        assert body_of(after)["selection_token"] != first["selection_token"], label
        assert body_of(MoneySnapshot(ev=ev, sessions=(A[40],)))["selection_token"] == first["selection_token"], label
        response = fin(client(FakeStore(after)), {**WINDOW, "limit": 1, "cursor": first["next_cursor"]})
        assert (response.status_code, response.json()["detail"]["code"]) == (409, "ESTATE_BASIS_CHANGED"), label


def test_w302_money_ev_guard_withholds_or_pends_the_older_head() -> None:
    """L1: only a pending recompute is pending; a stale or historical-current-claim guard withholds the older head."""
    for guard, state, reasons in (("HISTORICAL_CURRENT_CLAIM", "WITHHELD", ["WITHHELD"]),
                                  ("STALE_BASIS", "WITHHELD", ["WITHHELD"]),
                                  ("PENDING_RECOMPUTE", "PENDING", ["PENDING"])):
        transient = {"revision_id": None, "state": "WITHHELD", "reason": guard}
        body = body_of(MoneySnapshot(ev={"guard": guard, "consequence": transient, "history": [ev_head(A[35])]}))
        line = next(r for r in body["rows"] if r["domain"] == "ev_charging")
        assert (line["line_key"], line["eligibility"], line["reason_codes"], line["amount"]) == (
            f"ev_charging:{A[35]}", state, reasons, None), guard
        group = next(g for g in body["groups"] if g["category"] == "GROSS_TARIFF_SCENARIO")
        assert group["state"] == "UNKNOWN_COVERAGE" and group["amount"] is None, guard


def test_w302_money_ev_fingerprint_uses_the_economic_tariff_unit() -> None:
    """L2: the EV fingerprint is the stored tariff value, currency, kind and economic unit `currency/kWh`; the
    consequence quantity unit stays `kWh`."""
    ev = next(r for r in body_of(MoneySnapshot())["rows"] if r["domain"] == "ev_charging")
    fp = financials.assumption_fingerprint
    assert ev["assumption_fingerprint"] == fp("GROSS_TARIFF_SCENARIO", "KES", "currency/kWh", "0.27775",
                                              "GROSS_TARIFF_PER_KWH")
    assert ev["assumption_fingerprint"] != fp("GROSS_TARIFF_SCENARIO", "KES", "kWh", "0.27775", "GROSS_TARIFF_PER_KWH")
    assert ev["quantity"]["unit"] == "kWh"


def test_w302_money_partition_ineligible_reason_is_group_membership_only() -> None:
    """L4: an eligible line in an INELIGIBLE group carries only PARTITION_INELIGIBLE, not a mate's reason."""
    ok = _eligible("ev_charging:a", tech=["t1"], cited=["c1"])
    pending = {**_eligible("ev_charging:b", tech=["t2"], cited=["c2"]), "eligibility": "PENDING",
               "reason_codes": ["PENDING"], "amount": None}
    groups, exclusions, _ = compare([ok, pending], {"GROSS_TARIFF_SCENARIO": True})
    assert [g["state"] for g in groups] == ["INELIGIBLE"] and "PENDING" in groups[0]["reason_codes"]
    assert ok["eligibility"] == "ELIGIBLE"
    by = {e["line_key"]: e["reason_codes"] for e in exclusions}
    assert by == {"ev_charging:a": ["PARTITION_INELIGIBLE"], "ev_charging:b": ["PENDING"]}
