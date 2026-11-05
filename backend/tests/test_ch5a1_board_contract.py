"""CH-5a1 L1 (build sheet Part A §A9 item 2): the board composed by `SiteOutcomeBoardService` over a fixture
`ChainReader` equals the stored golden board JSON, and a fixture ledger shows 0 calls of the three deleted reads
(the mini overview, the Finding index and the estate evidence readiness).

The ChainReader is the real one (`chain/read.py`), over an in-memory `ChainReadPort`, so `ChainRequest.day` runs
with the real measure registry (`chain/measures.py` `measures_for`): the phase-2b bug (`m.measure` for `m.key`)
passed L0 because L0's measures were fakes. Every other producer is a small fake service.

Goldens (`backend/tests/fixtures/ch5a1_board_contract/`), taken from this fixture reader on the B side (the A-side
capture is the phase-3 L3 A/B; coordinator ruling for phase 2c). The E-change each carries (§A6):

- `kobo_2026-10-31.json` - E1 (readiness `readiness_of` over the board day's snapshots: one PARTIAL row ->
  LIMITED), E3 (the gap line names 10-15 and 10-16 by day grade, NO_DATA and PENDING), E4 (window
  [30 Oct 21:00Z, 31 Oct 21:00Z), the Addis local day), E2 (rows read from settled snapshots, no overview).
- `kobo_2026-11-01.json` - E1 (1 Nov, a PENDING row: the board day is unsettled, readiness UNKNOWN, measured
  outcomes UNKNOWN), E3, E4 ([31 Oct 21:00Z, 1 Nov 21:00Z)).
- `cold_2026-10-31.json` - E1 (Cold readiness over the one Addis local day the window covers: LIMITED), E4.
- `ev_2026-10-27.json` - E1 (EV LOW day grades -> NONE, the "Low" chip; CH5a1-R Q11), E4 unchanged (Etc/UTC).
E5 (known_at on occurrences) does not move a golden: every head is visible at the cutoff.

Regenerate with `ASSETOPS_REGEN_CH5A1_GOLDENS=1` only for an intended, reviewed change.
"""
from __future__ import annotations

import copy
import json
import os
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from uuid import UUID

import pytest

import test_out_b2_mini as B2
import test_out_b3_cold_ev as B3
from assetops_backend import read_scope
from assetops_backend.chain.measures import measures_for
from assetops_backend.chain.read import SITE_TYPE_OF_DOMAIN, ChainReader, FindingHead
from assetops_backend.site_outcomes.read import BoardServices, SiteOutcomeBoardService, SiteRef

UTC = timezone.utc
GOLDEN = Path(__file__).parent / "fixtures" / "ch5a1_board_contract"
REGEN = os.environ.get("ASSETOPS_REGEN_CH5A1_GOLDENS") == "1"
ADDIS = "Africa/Addis_Ababa"
TENANT = UUID("00000000-0000-4000-8000-000000000001")
KOBO = SiteRef(TENANT, UUID("00000000-0000-4000-8000-0000000000a1"), "KOBO-001", "Kobo", "MINIGRID", ADDIS)
COLD = SiteRef(TENANT, UUID("00000000-0000-4000-8000-0000000000c1"), "COLD-LAB-001", "GreenHarvest", "COLDCHAIN",
               ADDIS)
EV = SiteRef(TENANT, UUID("00000000-0000-4000-8000-0000000000e1"), "EV-LAB-001", "Depot", "EV_CHARGING", "Etc/UTC")
KNOWN = datetime(2026, 11, 3, 12, tzinfo=UTC)
#: The deleted reads (§A5): none of these may be called or appear in the read-scope ledger.
DELETED = ("mini_overview", "finding_index", "evidence_readiness", "readiness", "site_readiness",
           "site_readiness_many")


def at(d: int, h: int = 0, m: int = 0, month: int = 10) -> datetime:
    return datetime(2026, month, d, h, m, tzinfo=UTC)


@dataclass(frozen=True)
class Row:  # the `SnapshotReader.latest` row fields `chain/read.py` reads
    local_day: date
    measure: str
    subject_ref: str
    grade: str


def _rows(site_type: str, days: list[date], grade_of) -> list[Row]:
    out = []
    for d in days:
        for spec in measures_for(site_type):
            subject = "SITE" if spec.subject_kind == "SITE" else "asset-1"
            out.append(Row(d, spec.key, subject, grade_of(d, spec.key)))
    return out


def _kobo_grade(d: date, measure: str) -> str:
    if d == date(2026, 10, 15):
        return "NO_DATA"
    if d == date(2026, 10, 16) and measure == "productive_kwh":
        return "PENDING"
    if d == date(2026, 10, 31) and measure == "daylight_headroom_kw":
        return "PARTIAL"
    if d == date(2026, 11, 1) and measure == "avoidable_gen_min":
        return "PENDING"
    return "COMPLETE"


KOBO_DAYS = [date(2026, 10, 1) + timedelta(days=i) for i in range(32)]  # 1 Oct .. 1 Nov
SNAPSHOTS = {
    KOBO.site_id: _rows("MINIGRID", KOBO_DAYS, _kobo_grade),
    COLD.site_id: _rows("COLDCHAIN", [date(2026, 10, 30), date(2026, 10, 31)],
                        lambda d, m: "PARTIAL" if m == "backup_start_chain" else "COMPLETE"),
    EV.site_id: _rows("EV_CHARGING", [date(2026, 10, 27)], lambda d, m: "LOW"),
}
F1 = FindingHead("f1", "f1r", 2, "SUPPORTED", "BASIS_REFRESHED", at(31, 6), at(31, 7),
                 "GENERATOR_SUPPORT_CANDIDATE", None, "th-1", 2)
F2 = FindingHead("f2", "f2r", 1, "UNCONFIRMED", None, at(1, 5, month=11), at(1, 6, month=11),
                 "GENERATOR_SUPPORT_CANDIDATE", None, "th-2", 1)
HEADS = {KOBO.site_id: (F1, F2)}


class Port:
    """The in-memory `ChainReadPort`; `calls` is the fixture ledger of every port call."""

    def __init__(self) -> None:
        self.calls: list[tuple[str, tuple]] = []

    def snapshots(self, tenant_id, site_id, lo, hi, measures, known_at):
        self.calls.append(("snapshots", (site_id, lo, hi, tuple(measures))))
        return [r for r in SNAPSHOTS.get(site_id, []) if lo <= r.local_day <= hi and r.measure in measures]

    def finding_heads(self, tenant_id, site_id, domain, analytic_id, lo, hi, known_at):
        self.calls.append(("finding_heads", (site_id, domain, analytic_id, lo, hi)))
        return [h for h in HEADS.get(site_id, ()) if h.episode_start < hi and (h.episode_end or h.episode_start) > lo]

    def findings_settled(self, tenant_id, site_id, known_at):
        self.calls.append(("findings_settled", (site_id,)))
        return True

    def has_change(self, tenant_id, action_ids):
        self.calls.append(("has_change", tuple(action_ids)))
        return {str(a).lower(): str(a) == "a1" for a in action_ids}

    # CH-5a2b R1: the chip's placement facts and the labels' Action rows (the estate `site_work_rows` facts the
    # board read before: f1r Example data; a1 accepted on 30 Oct, no plan, no outcome).
    def placement_facts(self, tenant_id, site_id, revision_ids, known_at):
        self.calls.append(("placement_facts", (site_id, tuple(revision_ids))))
        facts = {"f1r": {"source_state": "REGISTERED_SIMULATION", "recurs_after_finding_id": None,
                         "recurs_after_title": None}}
        return {r: facts[r] for r in revision_ids if r in facts} if site_id == KOBO.site_id else {}

    def action_rows(self, tenant_id, site_id, known_at):
        self.calls.append(("action_rows", (site_id,)))
        if site_id != KOBO.site_id:
            return {"actions": (), "events": (), "plans": (), "outcomes": ()}
        return {"actions": ({"id": "a1"},),
                "events": ({"id": "e1", "action_id": "a1", "kind": "ACCEPTED", "recorded_at": at(30),
                            "failure_code": None},),
                "plans": (), "outcomes": ()}


class Never:
    """A deleted read's service: any method call is recorded (and must stay at 0)."""

    def __init__(self, name: str, seen: list[str]) -> None:
        self._name, self._seen = name, seen

    def __getattr__(self, attr: str) -> Any:
        def call(*a: Any, **k: Any) -> Any:
            self._seen.append(f"{self._name}.{attr}")
            raise AssertionError(f"{self._name}.{attr} is not a board read (CH-5a1 §A5)")
        return call


def _shift(value: Any, old: str, new: str) -> Any:
    return json.loads(json.dumps(value).replace(old, new))


def _money(t, s, fid, rid, is_latest, source_open):
    return {"body": {"money_eligibility": {"state": "ELIGIBLE"}, "currentness": {"current_amount_shown": True},
                     "consequence": {"display": {"amount_low": "3.31", "amount_high": "3.97", "currency": "USD"}}},
            "source": {"state": "REGISTERED_SIMULATION"}}


def _verification(t, s, code, aid):
    return {"state": "PENDING", "cost_check": None, "trial_hours": None}


class Opportunities:
    """CH9-R4 F2: the board's opportunity read (`opportunity_threads`), the Kobo study mirroring B2.DEPTH; the thread
    lookup returns no threads, so the goldens' thread fields are unchanged."""

    def opportunity_threads(self, tenant_id, site_ids, from_, to, k):
        r = B2.DEPTH["renewable"]
        return [{"site_code": KOBO.site_code, "study": {"headroom_kw": r["headroom_kw"], "eligible_days":
                 r["eligible_days"], "assessed_days": r["assessed_days"]}}] if str(KOBO.site_id) in map(str, site_ids) else []

    def lookup(self, tenant_id, finding_ids, action_ids, **kw):
        from assetops_backend.chain.lookup import thread_lookup
        return {**thread_lookup([]), "opportunities": []}


def services(port: Port, never: list[str]) -> BoardServices:
    open_gate = lambda c, t, s: (True, "open")  # noqa: E731

    class Depth:
        def read(self, **kw):
            return {"site": {"timezone": ADDIS}, "cards": B2.DEPTH[kw["domain"]]}

        def productive_users(self, **kw):
            return []

        def productive_readings(self, **kw):
            return []

    class Dispatch:
        def window(self, t, s, d):
            return B2.DISPATCH

    class Assumptions:
        def series(self, t, s, key, valid_at=None, recorded_at=None):
            return {"selection": {"state": "PRICED", "price": {"value": "1.45", "currency": "USD"}}}

    class Estate:
        def __getattr__(self, attr):  # site_readiness (E1), site_work_rows (CH-5a2b R1): deleted
            return Never("estate", never).__getattr__(attr)

    class ActionIndex:
        def read(self, t, s, c, req, access_basis=""):
            return {"rows": [{"action_id": "a1", "action_code": "ACT-001",
                              "origin": {"finding_id": "f1", "finding_revision_id": "f1r"},
                              "selected_event": {"id": "e1"}, "state": {"application": "PENDING"},
                              "links": {"selected_event": "/sites/KOBO-001/actions/a1?event_id=e1"}}],
                    "next_cursor": None}

    class ColdSite:
        def overview(self, t, s, c, lo, hi, known_at):
            return {**B3.COLD_OVERVIEW, "window": {"from": "2026-10-30T21:00:00Z", "to": "2026-10-31T21:00:00Z",
                                                   "known_at": "2026-11-01T00:00:00Z"}}

    class ColdReads:
        def findings(self, t, s, c, lo, hi, known_at, cursor, page):
            return {"items": _shift([B3.F118, B3.F119], "2026-10-20", "2026-10-31"), "next_cursor": None}

    class EvSite:
        def overview(self, t, s, c, lo, hi, known_at):
            return {**B3.EV_OVERVIEW, "window": {"from": "2026-10-27T08:00:00Z", "to": "2026-10-27T16:00:00Z",
                                                 "known_at": "2026-10-28T00:00:00Z"}}

    class EvReads:
        def findings(self, t, s, c, lo, hi, known_at, cursor, page):
            return {"items": _shift([B3.F130], "2026-10-20", "2026-10-27"), "next_cursor": None}

        def finding(self, t, s, c, fid, lo, hi, known_at):
            return None

    class EvDepth:
        def health(self, *a):
            return B3.HEALTH

        def availability(self, *a):
            return _shift(B3.AVAIL, "2026-10-20", "2026-10-27")

    class DomainActions:
        def index(self, t, s, c, req):
            rows = [B3.DA1] if c == COLD.site_code else [B3.EA1]
            return {"rows": copy.deepcopy(rows), "next_cursor": None}

    return BoardServices(
        overview=Never("mini_overview", never),
        overview_source=open_gate, mini_depth=Depth(), dispatch=Dispatch(), performance_gate=open_gate,
        finding_index_gate=open_gate, assumptions=Assumptions(), action_index=ActionIndex(),
        parse_action_index=lambda *a: a, estate=Estate(), cold_site=ColdSite(), cold_reads=ColdReads(),
        ev_site=EvSite(), ev_reads=EvReads(), ev_depth=EvDepth(), domain_actions=DomainActions(),
        parse_domain_index=lambda *a: a,
        chain_reader=ChainReader(port, verification=_verification, money=_money), threads=Opportunities())


CASES = {
    "kobo_2026-10-31": (KOBO, {"day": date(2026, 10, 31)}),
    "kobo_2026-11-01": (KOBO, {"day": date(2026, 11, 1)}),
    "cold_2026-10-31": (COLD, {"lo": at(30, 21), "hi": at(31, 21)}),
    "ev_2026-10-27": (EV, {"lo": at(27, 8), "hi": at(27, 16)}),
}


def _board(name: str):
    port, never = Port(), []
    site, window = CASES[name]
    with read_scope.scope(f"test:{name}") as sc:
        body = SiteOutcomeBoardService(services(port, never)).board(site, known_at=KNOWN, **window)
    return json.loads(json.dumps(body, default=str)), port, never, sc


@pytest.mark.parametrize("name", sorted(CASES))
def test_board_equals_its_golden(name: str) -> None:
    body, _, _, _ = _board(name)
    path = GOLDEN / f"{name}.json"
    text = json.dumps(body, indent=1, sort_keys=True, ensure_ascii=False) + "\n"
    if REGEN or not path.exists():
        if not REGEN:
            pytest.fail(f"missing golden {path.name}; set ASSETOPS_REGEN_CH5A1_GOLDENS=1 to write it")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8", newline="\n")
    assert body == json.loads(path.read_text(encoding="utf-8"))
    for row in body["rows"]:  # CH-5a2 B4: the subline ends with the structured lines' texts, joined as before
        texts = [t["text"] for t in row["thread_lines"]]
        assert not texts or (row["subline"] or "").endswith(" · ".join(texts)), row["category"]


@pytest.mark.parametrize("name", sorted(CASES))
def test_fixture_ledger_has_no_deleted_read(name: str) -> None:
    body, port, never, sc = _board(name)
    assert never == [], never  # 0 calls of mini_overview, finding_index, estate site_readiness*
    names = sc.names()
    assert not [n for n in DELETED if n in names], names
    assert sc.max_per_key() == 1, sc.repeated()
    assert [c for c in port.calls if c[0] == "snapshots"], port.calls  # readiness reads the chain


@pytest.mark.parametrize("site,site_type", [(KOBO, "MINIGRID"), (COLD, "COLDCHAIN"), (EV, "EV_CHARGING")])
def test_chain_day_reads_the_real_measure_registry(site: SiteRef, site_type: str) -> None:
    """`ChainRequest.day` asks the port for the registry's measure keys (`MeasureSpec.key`) and grades the rows
    it gets back; with a wrong attribute every board fails `chain_day`/`readiness_of` (phase-2b fix 1)."""
    port = Port()
    request = ChainReader(port).request(TENANT, KNOWN)
    day = {KOBO.site_id: date(2026, 10, 31), COLD.site_id: date(2026, 10, 31), EV.site_id: date(2026, 10, 27)}[
        site.site_id]
    facts = request.day(site.site_id, site_type, (day,))
    (call,) = [c for c in port.calls if c[0] == "snapshots"]
    assert call[1][3] == tuple(m.key for m in measures_for(site_type)) and call[1][3]
    assert set(facts.grades[day]) == set(call[1][3])
    assert facts.readiness == {"MINIGRID": "LIMITED", "COLDCHAIN": "LIMITED", "EV_CHARGING": "NONE"}[site_type]


def test_every_board_domain_has_registry_measures() -> None:
    """Phase-2c fix: `SITE_TYPE_OF_DOMAIN` named EV "EV" while the registry keys it "EV_CHARGING", so every EV
    readiness read asked for no measures and read UNKNOWN."""
    assert all(measures_for(t) for t in SITE_TYPE_OF_DOMAIN.values()), SITE_TYPE_OF_DOMAIN


def test_goldens_carry_the_e_changes() -> None:
    """The golden facts named in the module docstring, read back from the composed boards."""
    k31, _, _, _ = _board("kobo_2026-10-31")
    k01, _, _, _ = _board("kobo_2026-11-01")
    assert (k31["window"]["from"], k31["window"]["to"]) == ("2026-10-30T21:00:00Z", "2026-10-31T21:00:00Z")  # E4
    assert (k01["window"]["from"], k01["window"]["to"]) == ("2026-10-31T21:00:00Z", "2026-11-01T21:00:00Z")
    text = json.dumps(k31)
    assert "2026-10-15" in text and "2026-10-16" in text  # E3: the gap days by day grade
    measured = {o["state"] for r in k01["rows"] for o in r["outcomes"]}
    assert "UNKNOWN" in measured  # E1/R4: 1 Nov's PENDING row unsettles the board day
