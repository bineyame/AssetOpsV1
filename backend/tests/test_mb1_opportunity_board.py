"""MB-1a (FUEL-1 MB-1-R §2.5, L0): the mill (an opportunity-origin domain Action) in the claim and the Assure row.

1. `site_chain.opportunity_actions` truth table; 2. `claims.estate_count_claims` with a fake request (R3 as amended);
3. `mini.compose` with fake ports (the Assure row, MD-FUEL-MB1-1); 4. the board's `_verified_results` expression.
Expected texts are built from the backend constants, never typed."""
from __future__ import annotations

from dataclasses import replace
from datetime import date, datetime, timedelta, timezone
from types import SimpleNamespace

import pytest

from assetops_backend.chain import claims as CL
from assetops_backend.chain import site_chain
from assetops_backend.chain.vocabulary import provenance_suffix
from assetops_backend.outcomes.display_code import display_code
from assetops_backend.site_outcomes import mini

import test_out_b2_mini as B2

UTC = timezone.utc
LO, HI = datetime(2026, 10, 1, tzinfo=UTC), datetime(2026, 10, 8, tzinfo=UTC)
MILL, MILL_T, OPP = "a-mill", "t-mill", "o-mill"
VERDICT_AT = datetime(2026, 10, 5, 23, tzinfo=UTC)


def _occ(tid, fid, oid, start, end=None):
    return {"thread_id": tid, "mechanism": "PRODUCTIVE_USE_HEADROOM", "subject_ref": "site", "occurrence_no": 1,
            "finding_id": fid, "opportunity_id": oid, "opportunity_no": 7, "episode_start": start,
            "episode_end": end}


def _ev(tid, seq, state, day, recorded):
    return {"thread_id": tid, "seq": seq, "state": state, "cause_kind": "X", "cause_id": "c", "effective_day": day,
            "recorded_at": recorded, "cause_known_at": None}


def _act(aid=MILL, tid=MILL_T, kind="DOMAIN_INTENT", opp=OPP, finding=None, accepted=datetime(2026, 10, 2, tzinfo=UTC),
         outcome="VERIFIED", recorded=VERDICT_AT, code="ACT-000002", new_keys=True):
    row = {"action_id": aid, "action_code": code, "kind": kind, "thread_id": tid, "origin_finding_id": finding,
           "origin_opportunity_id": opp, "accepted_at": accepted}
    if new_keys:
        row.update(outcome=outcome, outcome_recorded_at=recorded)
    return row


def _rows(*actions, occurrences=None, events=()):
    occs = occurrences if occurrences is not None else (_occ(MILL_T, None, OPP, datetime(2026, 10, 1, 6, tzinfo=UTC)),)
    return {"occurrences": tuple(occs), "events": tuple(events), "actions": tuple(actions)}


def _opp(rows, cutoff=None, lo=LO, hi=HI):
    return site_chain.opportunity_actions(rows, site="KOBO-001", tz="Etc/UTC", cutoff=cutoff, lo=lo, hi=hi)


# ---- 1. opportunity_actions truth table ---------------------------------------------------------------------------

def test_the_mill_row_is_listed_with_its_outcome_and_a_domain_verdict_ref() -> None:
    (item,) = _opp(_rows(_act()))
    assert item["action_id"] == MILL and item["thread_id"] == MILL_T and item["origin_opportunity_id"] == OPP
    assert item["outcome"] == "VERIFIED" and item["outcome_recorded_at"] == VERDICT_AT
    assert item["ref"]["kind"] == "DOMAIN_VERDICT" and item["ref"]["id"] == MILL


@pytest.mark.parametrize("row, why", [
    (_act(kind="MINI_TRIAL", opp=None, finding="f1"), "a MINI_TRIAL is ignored"),
    (_act(opp=None, finding="f1"), "a domain intent with origin_finding_id is ignored"),
    (_act(accepted=HI), "accepted_at == hi is excluded"),
    (_act(tid=None), "no thread"),
])
def test_rows_that_are_not_a_shown_mill_are_excluded(row, why) -> None:
    assert _opp(_rows(row)) == [], why


def test_an_action_accepted_after_the_cutoff_is_excluded() -> None:
    assert _opp(_rows(_act()), cutoff=datetime(2026, 10, 1, 23, tzinfo=UTC)) == []


def test_no_opportunity_occurrence_meeting_the_window_is_excluded() -> None:
    before = (_occ(MILL_T, None, OPP, datetime(2026, 9, 1, tzinfo=UTC), datetime(2026, 9, 2, tzinfo=UTC)),)
    assert _opp(_rows(_act(), occurrences=before)) == []
    finding_only = (_occ(MILL_T, "f9", None, datetime(2026, 10, 3, tzinfo=UTC)),)
    assert _opp(_rows(_act(), occurrences=finding_only)) == []


def test_an_outcome_recorded_after_the_cutoff_is_not_judged_and_cutoff_none_sees_it() -> None:
    (early,) = _opp(_rows(_act()), cutoff=VERDICT_AT - timedelta(seconds=1))
    assert early["outcome"] is None and early["outcome_recorded_at"] is None
    (at,) = _opp(_rows(_act()), cutoff=VERDICT_AT)
    assert at["outcome"] == "VERIFIED"
    (now,) = _opp(_rows(_act()), cutoff=None)
    assert now["outcome"] == "VERIFIED"


def test_a_row_without_the_new_keys_reads_not_judged() -> None:
    (item,) = _opp(_rows(_act(new_keys=False)))
    assert item["outcome"] is None


def test_items_are_in_code_order() -> None:
    rows = _rows(_act(aid="b", code="ACT-000009"), _act(aid="a", code="ACT-000003"))
    assert [i["action_id"] for i in _opp(rows)] == ["a", "b"]


# ---- 2. claims (R3 as amended) ------------------------------------------------------------------------------------

FIND_T = "t-fix"
FIND_ROWS = ((_occ(FIND_T, "f2", None, datetime(2026, 10, 2, tzinfo=UTC)),),
             (_ev(FIND_T, 1, "OPEN", date(2026, 10, 2), datetime(2026, 10, 2, 8, tzinfo=UTC)),
              _ev(FIND_T, 2, "RESOLVED_MONITORING", date(2026, 10, 4), datetime(2026, 10, 4, 8, tzinfo=UTC))))
MILL_EVENTS = (_ev(MILL_T, 1, "OPEN", date(2026, 10, 1), datetime(2026, 10, 1, 8, tzinfo=UTC)),
               _ev(MILL_T, 2, "RESOLVED_MONITORING", date(2026, 10, 3), VERDICT_AT))


class _Req:
    def __init__(self, rows, k=None, fail=False):
        self.rows, self.k, self.fail = rows, k, fail

    def day(self, site_id, site_type, days):
        return SimpleNamespace(days=tuple(days), grades={})

    def threads(self, site_id):
        if self.fail:
            raise LookupError("down")
        return self.rows

    def evidence_cutoff(self, site_id):
        return None


SITE = SimpleNamespace(site_id="s1", site_code="KOBO-001", domain="mini_grid", timezone="Etc/UTC", tenant_id="t")


def _claims(monkeypatch, *actions, mill_events=MILL_EVENTS, mill_occ=None, fail=False):
    monkeypatch.setattr(CL, "claim_days", lambda req, site, lo, hi: None)
    occs = (*FIND_ROWS[0], *(mill_occ or (_occ(MILL_T, None, OPP, datetime(2026, 10, 1, 6, tzinfo=UTC)),)))
    rows = {"occurrences": occs, "events": (*FIND_ROWS[1], *mill_events), "actions": tuple(actions)}
    return CL.estate_count_claims(_Req(rows, fail=fail), [SITE], LO, HI, [], (LookupError,))


def test_a_verified_finding_thread_plus_a_verified_mill_is_two(monkeypatch) -> None:
    out = _claims(monkeypatch, _act())
    assert out.claims[CL.VERIFIED_RESULTS].value == 2
    assert out.threads["KOBO-001"]["verified"] == 1 and out.threads["KOBO-001"]["verified_actions"] == 1


def test_an_ineffective_mill_is_not_counted(monkeypatch) -> None:
    out = _claims(monkeypatch, _act(outcome="INEFFECTIVE"))
    assert out.claims[CL.VERIFIED_RESULTS].value == 1 and out.threads["KOBO-001"]["verified_actions"] == 0


def test_a_mill_on_a_thread_already_counted_is_counted_once(monkeypatch) -> None:
    on_fix = _act(tid=FIND_T)
    occ = (_occ(FIND_T, None, OPP, datetime(2026, 10, 2, tzinfo=UTC)),)
    out = _claims(monkeypatch, on_fix, mill_occ=occ, mill_events=())
    assert out.claims[CL.VERIFIED_RESULTS].value == 1 and out.threads["KOBO-001"]["verified_actions"] == 0


def test_recurred_after_verified_still_counts_the_mill(monkeypatch) -> None:
    recurred = (*MILL_EVENTS, _ev(MILL_T, 3, "RECURRED", date(2026, 10, 6), datetime(2026, 10, 6, 8, tzinfo=UTC)))
    out = _claims(monkeypatch, _act(), mill_events=recurred)
    assert out.claims[CL.VERIFIED_RESULTS].value == 2


def test_open_threads_are_unchanged_by_the_mill(monkeypatch) -> None:
    without = _claims(monkeypatch)
    with_mill = _claims(monkeypatch, _act())
    assert with_mill.claims[CL.OPEN_THREADS].value == without.claims[CL.OPEN_THREADS].value
    assert without.threads["KOBO-001"]["verified_actions"] == 0


def test_a_failed_thread_read_leaves_every_thread_claim_not_known(monkeypatch) -> None:
    out = _claims(monkeypatch, _act(), fail=True)
    assert out.threads["KOBO-001"] is None
    assert out.claims[CL.VERIFIED_RESULTS].value is None and out.claims[CL.OPEN_THREADS].value is None


# ---- 3. compose: the Assure row -----------------------------------------------------------------------------------

def _mill_ports(fake, *actions, k=None, raises=False):
    def chain_threads():
        fake.calls.append(("chain_threads", ()))
        if raises:
            raise RuntimeError("chain_threads refused")
        occ = (_occ(MILL_T, None, OPP, B2.T(10)),)
        return mini.ChainThreads(_rows(*actions, occurrences=occ), k, None)
    return replace(fake.ports(), chain_threads=chain_threads)


def _compose(ports):
    comp = mini.compose(ports, site_code=B2.C, day=B2.DAY, site_timezone=B2.ZONE)
    B2.checked(B2.assemble(comp.facts))  # href / link_ref parity (it strips `link_ref`, so the rows below are raw)
    return comp, {r["category"]: r for r in B2.assemble(comp.facts)}


def _mill(**kw):
    return _act(accepted=B2.T(12), recorded=B2.T(15), **kw)


def _verified_results(comp) -> int:
    """`site_outcomes/read.py` board `_verified_results` (MB-1-R Q5), the same expression."""
    return (sum(1 for a in comp.facts.actions if a.verification_state == "VERIFIED")
            + sum(1 for o in comp.facts.opportunity_actions if o.outcome == "VERIFIED"))


def test_s0_shape_lists_the_trial_and_the_mill_in_code_order() -> None:
    fake = B2.Fake(verification={"state": "VERIFIED", "source_class": None})
    comp, rows = _compose(_mill_ports(fake, _mill()))
    assure = rows[mini.ASSURE]
    assert assure["headline"] == f"{2} {mini.plural(2, 'verified result', 'verified results')}"
    entries = [c for c in assure["contributors"] if c["key"] == "verified_results"]
    want = sorted([("ACT-048", "ACTION"), ("ACT-000002", "DOMAIN_VERDICT")])
    assert [e["link_ref"]["kind"] for e in entries] == [k for _, k in want]
    mill = next(e for e in entries if e["link_ref"]["kind"] == "DOMAIN_VERDICT")
    assert mill["text"] == mini.VERIFICATION_TEXT["VERIFIED"].format(code=display_code("ACT-000002"),
                                                                     suffix=provenance_suffix(None))
    assert mill["link_ref"]["id"] == MILL and mill["confidence"] is None
    assert _verified_results(comp) == 2
    assert comp.read_state == "AVAILABLE"


def test_a_mill_not_judged_as_known_reads_not_yet_verified_with_the_pending_chip() -> None:
    fake = B2.Fake()
    comp, rows = _compose(_mill_ports(fake, _mill(), k=B2.T(14)))  # the verdict (T(15)) is after the cutoff
    mill = next(c for c in rows[mini.ASSURE]["contributors"]
                if c["key"] == "verified_results" and (c["link_ref"] or {}).get("kind") == "DOMAIN_VERDICT")
    assert mill["text"] == mini.VERIFICATION_TEXT["PENDING"].format(code=display_code("ACT-000002"),
                                                                    suffix=provenance_suffix(None))
    assert mill["confidence"] == mini.PENDING_CHIP
    assert rows[mini.ASSURE]["headline"] == mini.NO_VERIFIED and _verified_results(comp) == 0


@pytest.mark.parametrize("outcome", ["INEFFECTIVE", "INCONCLUSIVE"])
def test_ineffective_and_inconclusive_use_their_existing_texts(outcome) -> None:
    _, rows = _compose(_mill_ports(B2.Fake(), _mill(outcome=outcome)))
    texts = [c["text"] for c in rows[mini.ASSURE]["contributors"] if c["key"] == "verified_results"]
    assert mini.VERIFICATION_TEXT[outcome].format(code=display_code("ACT-000002"), suffix="") in texts


def test_a_failed_chain_threads_read_is_partial_and_lists_no_mill() -> None:
    fake = B2.Fake(verification={"state": "VERIFIED", "source_class": None})
    comp, rows = _compose(_mill_ports(fake, _mill(), raises=True))
    assert comp.read_state == "PARTIAL" and "chain_threads" in comp.failed
    assert comp.facts.opportunity_actions == ()
    assert rows[mini.ASSURE]["headline"] == f"{1} {mini.plural(1, 'verified result', 'verified results')}"
    assert all((c["link_ref"] or {}).get("kind") != "DOMAIN_VERDICT" for c in rows[mini.ASSURE]["contributors"])


def test_the_default_port_leaves_the_body_byte_equal_to_a_board_without_it() -> None:
    fake = B2.Fake(verification={"state": "VERIFIED", "source_class": None})
    ports = fake.ports()
    assert ports.chain_threads() is None
    comp, rows = _compose(ports)
    _, again = _compose(replace(fake.ports(), chain_threads=lambda: None))
    assert rows == again and comp.facts.opportunity_actions == ()


def test_the_board_service_verified_results_is_the_assure_headline_number() -> None:
    """MB-1-R §2.5 item 4 through `SiteOutcomeBoardService.board` (`read.py` `_verified_results`, the real
    `mini_ports` binding of `chain_threads` over a `ChainReader` whose port carries the mill row)."""
    import test_ch5a1_board_contract as BC
    from assetops_backend import read_scope
    from assetops_backend.site_outcomes.read import SiteOutcomeBoardService

    class Port(BC.Port):
        def site_threads(self, tenant_id, site_id, known_at):
            occ = (_occ(MILL_T, None, OPP, BC.at(20)),)
            return _rows(_act(accepted=BC.at(21), recorded=BC.at(22)), occurrences=occ)

    with read_scope.scope("test:mb1"):
        body = SiteOutcomeBoardService(BC.services(Port(), [])).board(BC.KOBO, known_at=BC.KNOWN,
                                                                      day=date(2026, 10, 31))
    assure = next(r for r in body["rows"] if r["category"] == mini.ASSURE)
    shown = 0 if assure["headline"] == mini.NO_VERIFIED else int(assure["headline"].split()[0])
    assert body["_verified_results"] == shown >= 1
    assert any((c["link_ref"] or {}).get("kind") == "DOMAIN_VERDICT" for c in assure["contributors"])


def test_grow_optimize_and_protect_rows_are_byte_equal_with_the_mill() -> None:
    fake = B2.Fake(verification={"state": "VERIFIED", "source_class": None})
    _, without = _compose(fake.ports())
    _, with_mill = _compose(_mill_ports(fake, _mill()))
    for cat in (mini.GROW, mini.COST, mini.PROTECT):
        assert with_mill[cat] == without[cat], cat
