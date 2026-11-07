"""CH-5a2b L0 (build sheet CH-5a §B13 R2/R3, §B14; CH-6 §S.2): the PC-1 `Claim`, the one `count_basis`, the count
texts, `provenance_suffix`, the one thread classifier and the public GradeCounts-from-DayFacts function. Pure."""
from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest

from assetops_backend.chain.read import DayFacts
from assetops_backend.chain.reader import GradeCounts, grade_counts_of
from assetops_backend.chain.threads import classify
from assetops_backend.chain.vocabulary import Claim, count_basis, count_claim, provenance_suffix, sum_days


def days(complete=0, partial=0, low=0, no_data=0, pending=0, expected=None):
    exp = complete + partial + low + no_data + pending if expected is None else expected
    return {"complete": complete, "partial": partial, "low": low, "no_data": no_data, "pending": pending,
            "expected": exp}


@pytest.mark.parametrize("d, basis", [
    (None, "NOT_KNOWN"), (days(expected=0), "NOT_KNOWN"), (days(pending=2, no_data=1), "NOT_KNOWN"),
    (days(complete=7), "COMPLETE"), (days(complete=6, partial=1), "CHECKED_DAYS"),
    (days(complete=1, no_data=6), "CHECKED_DAYS"), (days(low=3), "CHECKED_DAYS")])
def test_count_basis_is_the_one_rule(d, basis) -> None:
    assert count_basis(d) == basis


def test_count_basis_takes_grade_counts() -> None:
    g = GradeCounts(requested=7, expected=7, complete=7, partial=0, low=0, no_data=0, not_expected=0, pending=0,
                    enough_data_days=7)
    assert count_basis(g) == "COMPLETE"
    assert sum_days([g, days(complete=6, partial=1)]) == days(complete=13, partial=1)
    assert sum_days([g, None]) is None


@pytest.mark.parametrize("key, value, d, text", [
    ("count.open_threads", 1, days(complete=7), "1 open finding"),
    ("count.open_threads", 3, days(complete=7), "3 open findings"),
    ("count.open_threads", 2, days(complete=5, partial=2), "2 open on the days checked"),
    ("count.open_threads", 0, days(complete=5, partial=2), "None open on the days checked"),
    ("count.verified_results", 1, days(complete=7), "1 fix confirmed"),
    ("count.verified_results", 2, days(complete=7), "2 fixes confirmed"),
    ("count.verified_results", 1, days(complete=1, low=1), "1 confirmed, from the days checked"),
    ("count.verified_results", 0, days(complete=1, low=1), "None confirmed on the days checked"),
    ("count.opportunities", 1, days(complete=7), "1 opportunity"),
    ("count.opportunities", 0, days(complete=7), "0 opportunities"),
    ("count.opportunities", 1, days(complete=6, no_data=1), "1 found on the days checked"),
    ("count.opportunities", 0, days(complete=6, no_data=1), "None found on the days checked"),
    ("count.opportunities", 1, None, "Not known yet"),
    ("count.opportunities", None, days(complete=7), "Not known yet")])
def test_count_claim_texts(key, value, d, text) -> None:
    c = count_claim(key, value, d)
    assert c.text == text
    assert c.basis == ("NOT_KNOWN" if value is None or d is None else count_basis(d))


def test_claim_wire_shape() -> None:
    assert count_claim("count.opportunities", 2, days(complete=7)).to_json() == {
        "key": "count.opportunities", "value": 2, "basis": "COMPLETE", "days": days(complete=7),
        "text": "2 opportunities"}
    assert Claim("money.x", Decimal("1.50"), "COMPLETE", None, "t").to_json()["value"] == "1.50"


def test_provenance_suffix() -> None:
    assert provenance_suffix("REGISTERED_SIMULATION") == provenance_suffix("AUTHORED_DEMONSTRATION") == " on example data"
    assert provenance_suffix("MEASURED_FIELD") == provenance_suffix(None) == provenance_suffix("MIXED") == ""


def test_classify_thread_states() -> None:
    states = ["OPEN", "RECURRED", "REOPENED", "ACTION_IN_HAND", "CHANGE_APPLIED", "RESOLVED_MONITORING", "CLOSED",
              "WITHDRAWN", None]
    assert classify(states) == {"open": 3, "in_hand": 2, "verified": 2}


def test_grade_counts_of_day_facts() -> None:
    d1, d2, d3 = date(2026, 10, 30), date(2026, 10, 31), date(2026, 11, 1)
    facts = DayFacts(days=(d1, d2, d3), grades={d1: {"m": {"s": "COMPLETE"}}, d2: {"m": {"s": "PARTIAL"}}},
                     settled=True, readiness="FULL", gaps=())
    g = grade_counts_of(facts, ["m"])
    assert (g.requested, g.expected, g.complete, g.partial, g.no_data) == (3, 3, 1, 1, 1)


# ---- §B14 Q7/Q8: the one count computation (`chain/claims.py`) -------------------------------------------------

from datetime import date as _date, datetime as _dt, timezone as _tz  # noqa: E402
from types import SimpleNamespace as _NS  # noqa: E402

from assetops_backend.chain import claims as CL  # noqa: E402


def _o(tid, fid, oid, start, end):
    return {"thread_id": tid, "mechanism": "GENERATOR_SUPPORT_CANDIDATE", "subject_ref": "a", "occurrence_no": 1,
            "finding_id": fid, "opportunity_id": oid, "opportunity_no": None, "episode_start": start,
            "episode_end": end}


def _e(tid, seq, state, day, recorded):
    return {"thread_id": tid, "seq": seq, "state": state, "cause_kind": "X", "cause_id": "c", "effective_day": day,
            "recorded_at": recorded, "cause_known_at": None}


_LO, _HI = _dt(2026, 10, 1, tzinfo=_tz.utc), _dt(2026, 10, 8, tzinfo=_tz.utc)
_ROWS = {"occurrences": (
    _o("t-open", "f1", None, _dt(2026, 10, 3, tzinfo=_tz.utc), _dt(2026, 10, 3, 6, tzinfo=_tz.utc)),
    _o("t-verified", "f2", None, _dt(2026, 10, 2, tzinfo=_tz.utc), None),
    _o("t-before", "f3", None, _dt(2026, 9, 1, tzinfo=_tz.utc), _dt(2026, 9, 2, tzinfo=_tz.utc)),  # event-only
    _o("t-opp", None, "o1", _dt(2026, 10, 3, tzinfo=_tz.utc), None)),  # opportunity-only
    "events": (_e("t-open", 1, "OPEN", _date(2026, 10, 3), _dt(2026, 10, 3, 8, tzinfo=_tz.utc)),
               _e("t-verified", 1, "OPEN", _date(2026, 10, 2), _dt(2026, 10, 2, 8, tzinfo=_tz.utc)),
               _e("t-verified", 2, "RESOLVED_MONITORING", _date(2026, 10, 5), _dt(2026, 10, 5, 8, tzinfo=_tz.utc)),
               _e("t-before", 1, "OPEN", _date(2026, 10, 4), _dt(2026, 10, 4, 8, tzinfo=_tz.utc)),
               _e("t-opp", 1, "OPEN", _date(2026, 10, 3), _dt(2026, 10, 3, 8, tzinfo=_tz.utc))),
    "actions": ()}
_DAYS = {d: {"m": {"s": "COMPLETE"}} for d in (_date(2026, 10, i) for i in range(1, 8))}


class _Req:
    def __init__(self, k=None, ev=None, fail=False):
        self.k, self.ev, self.fail, self.ev_calls = k, ev, fail, 0

    def day(self, site_id, site_type, days):
        return _NS(days=tuple(days), grades={})

    def threads(self, site_id):
        if self.fail:
            raise LookupError("down")
        return _ROWS

    def evidence_cutoff(self, site_id):
        self.ev_calls += 1
        return self.ev


_MINI = _NS(site_id="s1", site_code="KOBO-001", domain="mini_grid", timezone="Etc/UTC", tenant_id="t")
_COLD = _NS(site_id="s2", site_code="COLD-001", domain="cold_chain", timezone="Etc/UTC", tenant_id="t")


def test_claims_count_only_finding_threads_meeting_the_window(monkeypatch) -> None:
    monkeypatch.setattr(CL, "claim_days", lambda req, site, lo, hi: None)
    out = CL.estate_count_claims(_Req(), [_MINI], _LO, _HI, [1, 2])
    # no event- or opportunity-only thread; MB-1-R §2.2: no opportunity-origin Action, `verified_actions` 0
    assert out.threads["KOBO-001"] == {"open": 1, "in_hand": 0, "verified": 1, "verified_actions": 0}
    assert out.claims["count.open_threads"].value == 1 and out.claims["count.verified_results"].value == 1
    assert out.claims["count.opportunities"].value == 2
    assert {c.basis for c in out.claims.values()} == {"NOT_KNOWN"}  # days None: the grade read failed


def test_claims_threads_are_read_at_the_request_cutoff_for_every_domain(monkeypatch) -> None:
    """CH6b2-R2 (supersedes the CH-5a2 R7 cold/EV thread cutoff): lifecycle is read at `k`, never the evidence cutoff;
    evidence reads keep R7 (`site_cutoff`, test_ch6b2_portfolio_cards)."""
    monkeypatch.setattr(CL, "claim_days", lambda req, site, lo, hi: None)
    req = _Req(k=None, ev=_dt(2026, 10, 4, tzinfo=_tz.utc))  # the RESOLVED_MONITORING event is after the evidence cutoff
    out = CL.estate_count_claims(req, [_COLD], _LO, _HI, [])
    assert out.threads["COLD-001"] == {"open": 1, "in_hand": 0, "verified": 1,
                                       "verified_actions": 0} and req.ev_calls == 0
    mini = _Req(ev=_dt(2026, 10, 4, tzinfo=_tz.utc))
    CL.estate_count_claims(mini, [_MINI], _LO, _HI, [])
    assert mini.ev_calls == 0


def test_claims_failed_thread_read_or_opportunity_read_is_not_known(monkeypatch) -> None:
    full = {"complete": 7, "partial": 0, "low": 0, "no_data": 0, "pending": 0, "expected": 7}
    monkeypatch.setattr(CL, "claim_days", lambda req, site, lo, hi: full)
    out = CL.estate_count_claims(_Req(fail=True), [_MINI], _LO, _HI, None, (LookupError,))
    assert out.threads["KOBO-001"] is None
    assert [out.claims[k].basis for k in CL.CLAIM_KEYS] == ["NOT_KNOWN"] * len(CL.CLAIM_KEYS) == ["NOT_KNOWN"] * 4
    ok = CL.estate_count_claims(_Req(), [_MINI], _LO, _HI, [])
    assert ok.claims["count.open_threads"].text == "1 open finding"
    assert ok.claims["count.opportunities"].basis == "COMPLETE" and ok.claims["count.opportunities"].value == 0


def test_estate_claims_callable_resolves_codes_and_reads_one_request() -> None:
    seen = []

    class Reader:
        def request(self, tenant_id, known_at):
            seen.append((tenant_id, known_at))
            return _Req()

    class Opp:
        def opportunity_threads(self, *a):
            return [{"site_code": "KOBO-001"}]

    call = CL.EstateClaims(lambda: Reader(), lambda: Opp(), {"KOBO-001": _MINI}.get)
    out = call("t", ["KOBO-001", "GONE"], _LO, _HI, None)
    assert seen == [("t", None)] and set(out.threads) == {"KOBO-001"}
    assert out.claims["count.opportunities"].value == 1
    assert CL.EstateClaims(lambda: None, lambda: None, lambda c: None)("t", [], _LO, _HI, None) is None


# ---- R1 (§B14 Q5): `chain.read.reduce_action_rows` ----------------------------------------------------------

def test_action_rows_reduce_to_the_workflow_label_keys() -> None:
    from assetops_backend.chain.read import reduce_action_rows
    from assetops_backend.estate.portfolio import workflow_label
    t = lambda d, h=0: _dt(2026, 10, d, h, tzinfo=_tz.utc)  # noqa: E731
    ev = lambda i, a, kind, at, **kw: {"id": i, "action_id": a, "kind": kind, "recorded_at": at,  # noqa: E731
                                       "failure_code": None, **kw}
    raw = {"actions": ({"id": "A1"}, {"id": "a2"}, {"id": "a3"}),
           "events": (ev("e1", "a1", "ACCEPTED", t(1)), ev("e2", "a1", "APPLIED", t(2)),
                      ev("e3", "a1", "RESOLVED", t(5), verification_outcome_id="o1",
                         payload={"outcome": "VERIFIED"}),
                      ev("e4", "a2", "ACCEPTED", t(1)), ev("e5", "a2", "APPLIED", t(2))),
           "plans": ({"action_id": "a2", "later_start": t(3), "later_end": t(9)},),
           "outcomes": ({"id": "O1", "source_class": "REGISTERED_SIMULATION"},)}
    rows = {r["action_id"]: r for r in reduce_action_rows(raw, t(4))}
    assert set(rows) == {"A1", "a2"}  # a3 has no event by k: absent (the board marks it ACTION_ROW_MISSING)
    assert rows["A1"]["resolution_state"] == "RESOLVED" and rows["A1"]["verification_outcome"] == "VERIFIED"
    assert rows["A1"]["_raw"]["_source_class"] == "REGISTERED_SIMULATION"
    assert rows["a2"]["_raw"]["_verification_window"] is True and rows["a2"]["_raw"]["_source_class"] is None
    assert workflow_label(rows["A1"]) == "Verified" and workflow_label(rows["a2"]) != "Verified"
    assert reduce_action_rows(raw, t(10))[1]["_raw"]["_verification_window"] is False  # the window closed
