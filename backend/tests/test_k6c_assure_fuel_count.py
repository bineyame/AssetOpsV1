"""DIESEL-K6c (DIESEL-1-R3u U2/U3, L0): the Assure verified count includes the fuel verdicts `_assure` lists, and the
estate summary's `verified_result_count` is the chain claim's value (one computation).

1. `mini.compose` with fakes: one VERIFIED fuel verdict reads "1 verified result" and passes COH-17 A1;
2. a PENDING / INEFFECTIVE / INCONCLUSIVE fuel verdict is not counted;
3. a VERIFIED trial, mill and fuel verdict give "3 verified results";
4. no double count: a FUEL_BALANCE Action reaches the board only through `fuel_verdict_actions`;
5. the summary reports the claim's value (the S shape: board sum 2, claim 1), None without a chain reader.
Expected texts are built from the backend constants, never typed."""
from __future__ import annotations

import sys
from dataclasses import replace
from datetime import date, datetime, timezone
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))  # `checks.chain_coherence`

from assetops_backend.chain import site_chain
from assetops_backend.chain.claims import CLAIM_KEYS, VERIFIED_RESULTS, EstateCounts
from assetops_backend.chain.vocabulary import Claim
from assetops_backend.site_outcomes import mini
from assetops_backend.site_outcomes import read as R
from assetops_backend.site_outcomes.read import BoardServices, SiteOutcomeBoardService

import test_mb1_opportunity_board as MB
import test_out_b2_mini as B2
import test_out_b4_read as B4

FUEL_A, FUEL_T, FUEL_F = "a-fuel", "t-fuel", "f-fuel"
FUEL_CODE = "ACT-000004"


def _fuel_occ(start):
    return {"thread_id": FUEL_T, "mechanism": "UNEXPLAINED_FUEL", "subject_ref": "site", "occurrence_no": 1,
            "finding_id": FUEL_F, "opportunity_id": None, "opportunity_no": None, "episode_start": start,
            "episode_end": None}


def _fuel_act(outcome="VERIFIED", accepted=None, recorded=None):
    return {"action_id": FUEL_A, "action_code": FUEL_CODE, "kind": "DOMAIN_INTENT", "thread_id": FUEL_T,
            "origin_finding_id": FUEL_F, "origin_opportunity_id": None, "action_domain": "FUEL_BALANCE",
            "accepted_at": accepted or B2.T(12), "outcome": outcome, "outcome_recorded_at": recorded or B2.T(15),
            "source_class": "REGISTERED_SIMULATION"}


def _ports(fake, *actions, mill=False):
    occs = [_fuel_occ(B2.T(10))] + ([MB._occ(MB.MILL_T, None, MB.OPP, B2.T(10))] if mill else [])

    def chain_threads():
        return mini.ChainThreads(MB._rows(*actions, occurrences=tuple(occs)), None, None)
    return replace(fake.ports(), chain_threads=chain_threads)


def _headline(n: int) -> str:
    return f"{n} {mini.plural(n, 'verified result', 'verified results')}" if n else mini.NO_VERIFIED


def _board_count(comp) -> int:
    """`read.py` board `_verified_results`, the same expression (R3u: plus the fuel term)."""
    return (sum(1 for a in comp.facts.actions if a.verification_state == "VERIFIED")
            + sum(1 for o in comp.facts.opportunity_actions if o.outcome == "VERIFIED")
            + sum(1 for f in comp.facts.fuel_verdicts if f.outcome == "VERIFIED"))


def _a1(assure: dict) -> list:
    from checks.chain_coherence import _coh17_a1
    return _coh17_a1("S", "KISIWA-001", assure, [], {"compared": 0})


# ---- 1. one VERIFIED fuel verdict ---------------------------------------------------------------------------------

def test_1_one_verified_fuel_verdict_reads_one_verified_result_and_passes_a1() -> None:
    comp, rows = MB._compose(_ports(B2.Fake(), _fuel_act()))   # the trial ACT-048 is PENDING; no mill
    assure = rows[mini.ASSURE]
    assert [f.outcome for f in comp.facts.fuel_verdicts] == ["VERIFIED"] and comp.facts.opportunity_actions == ()
    assert assure["headline"] == _headline(1) == "1 verified result"
    entries = [c for c in assure["contributors"] if c["key"] == "verified_results"
               and (c["link_ref"] or {}).get("kind") == "FUEL_VERDICT"]
    assert len(entries) == 1 and " not yet verified" not in entries[0]["text"]
    assert _a1(assure) == []
    assert _board_count(comp) == 1


# ---- 2. a fuel verdict that is not VERIFIED is not counted ----------------------------------------------------------

@pytest.mark.parametrize("outcome", [None, "INEFFECTIVE", "INCONCLUSIVE"])
def test_2_a_fuel_verdict_not_verified_is_not_counted(outcome) -> None:
    comp, rows = MB._compose(_ports(B2.Fake(), _fuel_act(outcome=outcome)))
    assert [f.outcome for f in comp.facts.fuel_verdicts] == [outcome]
    assert rows[mini.ASSURE]["headline"] == mini.NO_VERIFIED and _board_count(comp) == 0
    assert _a1(rows[mini.ASSURE]) == []


# ---- 3. trial + mill + fuel ---------------------------------------------------------------------------------------

def test_3_a_verified_trial_mill_and_fuel_verdict_give_three() -> None:
    fake = B2.Fake(verification={"state": "VERIFIED", "source_class": None})
    comp, rows = MB._compose(_ports(fake, MB._mill(), _fuel_act(), mill=True))
    assert rows[mini.ASSURE]["headline"] == _headline(3) == "3 verified results"
    assert _a1(rows[mini.ASSURE]) == [] and _board_count(comp) == 3


# ---- 4. no double count -------------------------------------------------------------------------------------------

def test_4_a_fuel_action_reaches_the_board_only_through_fuel_verdict_actions() -> None:
    """R3u U2: a FUEL_BALANCE domain Action is never an opportunity Action (it has no opportunity origin), so the
    fuel term counts it once; a VERIFIED fuel verdict and nothing else reads 1, never 2."""
    rows = MB._rows(_fuel_act(), occurrences=(_fuel_occ(B2.T(10)),))
    assert site_chain.opportunity_actions(rows, site=B2.C, tz=B2.ZONE, cutoff=None, lo=B2.T(1), hi=B2.T(25)) == []
    (only,) = site_chain.fuel_verdict_actions(rows, site=B2.C, cutoff=None, lo=B2.T(1), hi=B2.T(25))
    assert only["action_id"] == FUEL_A and only["ref"]["kind"] == "FUEL_VERDICT"
    comp, out = MB._compose(_ports(B2.Fake(), _fuel_act()))
    assert all(a.action_id != FUEL_A for a in comp.facts.actions)   # the Action index lists the trial only
    assert [o.action_id for o in comp.facts.opportunity_actions] == []
    assert out[mini.ASSURE]["headline"] == _headline(1)


# ---- 5. the summary reports the claim's value -----------------------------------------------------------------------

def _counts(verified: int) -> EstateCounts:
    claims = {k: Claim(k, verified if k == VERIFIED_RESULTS else 0, "COMPLETE", None, "") for k in CLAIM_KEYS}
    return EstateCounts(claims=claims, days={}, threads={})


def test_5_the_summary_verified_count_is_the_claim_not_the_board_sum(monkeypatch) -> None:
    """The S shape: each board's work window lists 2 VERIFIED Actions (board sum 2); the claim counts 1."""
    real_board = SiteOutcomeBoardService.board

    def board(self, site, **kw):
        body = real_board(self, site, **kw)
        if site is B4.KOBO:
            body["_verified_results"] = 2
        return body

    monkeypatch.setattr(SiteOutcomeBoardService, "board", board)
    monkeypatch.setattr(SiteOutcomeBoardService, "estate_counts", lambda self, *a, **kw: _counts(1))
    monkeypatch.setattr(R, "portfolio_cards", lambda *a, **kw: [])
    lo, hi = datetime(2026, 10, 1, tzinfo=timezone.utc), datetime(2026, 10, 8, tzinfo=timezone.utc)
    svc = SiteOutcomeBoardService(BoardServices())
    assert svc.board(B4.KOBO, day=date(2026, 10, 6))["_verified_results"] == 2
    out = svc.summary([B4.KOBO, B4.COLD, B4.ODD], lo, hi)
    assert out["verified_result_count"] == 1
    assert out["verified_sites_unread"] == 1   # ODD's board fails; unchanged


def test_5_without_a_chain_reader_the_summary_verified_count_is_none(monkeypatch) -> None:
    real_board = SiteOutcomeBoardService.board

    def board(self, site, **kw):
        body = real_board(self, site, **kw)
        body["_verified_results"] = 2
        return body

    monkeypatch.setattr(SiteOutcomeBoardService, "board", board)
    lo, hi = datetime(2026, 10, 1, tzinfo=timezone.utc), datetime(2026, 10, 8, tzinfo=timezone.utc)
    svc = SiteOutcomeBoardService(BoardServices())
    assert svc.s.chain_reader is None and svc.estate_counts([B4.KOBO], lo, hi, None) is None
    out = svc.summary([B4.KOBO, B4.COLD], lo, hi)
    assert out["verified_result_count"] is None and out["verified_sites_unread"] == 0
