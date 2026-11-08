"""DIESEL-1-R3p (K8) L0: the unexplained-fuel Finding in the estate Finding rows (build sheet §9p.2, §9p.3, §9p.12).

No database. `select_finding_scope` runs for real over a monkeypatched `site_coverage` and a fake snapshot carrying
`fuel_findings`/`finding_provenance`; the Portfolio runs through `test_w303_portfolio_api.World` (its money scope is a
fake, so the persisted money proof is `test_k8_estate_fuel_postgres.py`)."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace as NS
from uuid import UUID

import pytest

from assetops_backend.chain import claims as CL
from assetops_backend.chain.threads import VERIFIED_CLASS
from assetops_backend.estate import index, portfolio
from assetops_backend.estate.coverage import CURRENT, HISTORICAL, PARTIAL, PENDING, STALE, UNKNOWN
from assetops_backend.estate.money_invariants import double_count_violations
from assetops_backend.estate.placement import place
from assetops_backend.fuel_balance.adapters.postgres_fuel_balance_store import PostgresFuelBalanceStore
from assetops_backend.fuel_balance.model import FINDINGS_REFUSED
from assetops_backend.site_outcomes import mini as site_mini
from test_w303_portfolio_api import (  # noqa: F401 - `_cursor_key` is the autouse Portfolio cursor-key fixture
    READ_AT, SITES, T, WINDOW, _cursor_key, client, cov, get, world)

MG_SITE, CO_SITE = SITES
FUEL_ID = UUID("50000000-0000-4000-8000-000000000001")
FUEL_REV = UUID("50000000-0000-4000-8000-000000000002")
CONS_ID = UUID("50000000-0000-4000-8000-000000000003")
EVIDENCE = ["60000000-0000-4000-8000-000000000002", "60000000-0000-4000-8000-000000000001"]
NIGHT_START = datetime(2026, 10, 15, 15, tzinfo=timezone.utc)  # 6 pm local (UTC+3)
NIGHT_END = NIGHT_START + timedelta(hours=18)
REQ = NS(from_=datetime(2026, 10, 13, tzinfo=timezone.utc), to=datetime(2026, 10, 20, tzinfo=timezone.utc))
PRICED = {"id": CONS_ID, "state": "PRICED", "amount_low": "41.25", "amount_high": "57.75", "currency": "USD"}


def fuel_finding(consequence=PRICED, start=NIGHT_START, end=NIGHT_END, lifecycle="SUPPORTED"):
    return NS(finding_id=FUEL_ID, revision_id=FUEL_REV, revision_no=1, lifecycle=lifecycle,
              night_date=start.date(), window=NS(window_start=start, window_end=end), consequence=consequence,
              created_at=start)


class FuelSnap:
    """The two snapshot reads the join uses; `findings` is what `fuel_findings` returns for the mini Site."""

    def __init__(self, findings=()):
        self.findings, self.calls = list(findings), []

    def fuel_findings(self, t, s, from_, to, k):
        self.calls.append((t, s, from_, to, k))
        return [{"finding": f, "evidence_ids": sorted(EVIDENCE)} for f in self.findings] if s == MG_SITE["site_id"] else []

    def finding_provenance(self, t, s, frid, evidence_ids):
        return {"classification": "SITE_RECORD", "state": "KNOWN", "evidence_ids": list(evidence_ids), "frid": frid}


class NoFuelSnap:
    """A snapshot without the fuel read (every pre-K8 test fake)."""


def run_scope(monkeypatch, snap, state=CURRENT, sites=(MG_SITE,)):
    monkeypatch.setattr(index, "site_coverage", lambda *a, **kw: cov(state))
    return index.select_finding_scope(snap, T, REQ, {"sites": list(sites), "k": READ_AT})


def fuel_rows(rows):
    return [r for r in rows if r["_mechanism"] == index.FUEL_MECHANISM]


# --- 1. the row ---------------------------------------------------------------------------------------------------

def test_one_fuel_row_with_every_field(monkeypatch) -> None:
    _, rows = run_scope(monkeypatch, FuelSnap([fuel_finding()]))
    (row,) = fuel_rows(rows)
    fid = str(FUEL_ID)
    assert row["lens_flags"] == ["RISK"]
    assert row["categories"]["state"] == "MAPPED"
    assert [(m["category"], m["role"], [o["key"] for o in m["outcomes"]]) for m in row["categories"]["items"]] == [
        ("PROTECT_ASSET", "MOVES", ["MG-8"])]
    assert row["links"]["finding"] == f"/sites/{MG_SITE['site_code']}/fuel-findings/{fid}".replace(" ", "%20")
    assert row["link_refs"]["finding"]["kind"] == "FUEL_FINDING" and row["link_refs"]["finding"]["id"] == fid
    assert row["consequence"] == {"state": "PRICED", "amount": "41.25", "amount_low": "41.25", "amount_high": "57.75",
                                  "currency": "USD", "source_revision_id": str(CONS_ID),
                                  "basis": "UNEXPLAINED_FUEL_AT_DECLARED_PRICE"}
    assert row["title"] == "Unexplained fuel overnight" and row["lifecycle"] == "SUPPORTED"
    assert row["finding_id"] == fid and row["finding_revision_id"] == str(FUEL_REV)
    assert row["source_provenance"]["evidence_ids"] == sorted(EVIDENCE)
    assert row["episode_start"] == "2026-10-15T15:00:00Z" and row["status"] == CURRENT
    assert row["_episode_end"] == NIGHT_END and row["_revision_no"] == 1


def test_fuel_row_keys_follow_the_mini_row_order(monkeypatch) -> None:
    """§9p.2 item 4: every key a mini row has, in the same order (the Findings and Portfolio wires keep their shape)."""
    mini_raw = {"finding_id": "m1", "finding_revision_id": "m2", "title": "t", "lifecycle": "SUPPORTED",
                "consequence": {"state": "UNPRICED"}, "source_provenance": {}, "episode_start": NIGHT_START,
                "mechanism": "GENERATOR_SUPPORT_CANDIDATE"}
    monkeypatch.setattr(index, "site_coverage", lambda *a, **kw: {**cov(CURRENT), "rows": [mini_raw]})
    _, rows = index.select_finding_scope(FuelSnap([fuel_finding()]), T, REQ, {"sites": [MG_SITE], "k": READ_AT})
    mini_row, fuel_row = rows
    assert list(fuel_row) == list(mini_row)


# --- 2./3. money untouched, counts ----------------------------------------------------------------------------------

MONEY_KEYS = ("selected_lines", "money", "value_cards", "footer")


def portfolio_body(world, monkeypatch, findings, **params):
    real = world.select_finding_scope

    def with_fuel(snap, t, req, scope, cutoffs=None):
        per, rows = real(snap, t, req, scope, cutoffs)
        for site, _, c in per:
            if site["site_type"] == "MINIGRID":
                rows = rows + index._fuel_rows(FuelSnap(findings), t, site, c, req, scope["k"])
        return per, rows

    monkeypatch.setattr(portfolio, "select_finding_scope", with_fuel)
    return get(client(world), {**WINDOW, **params}).json()


def test_money_untouched_and_counts(world, monkeypatch) -> None:
    without = portfolio_body(world, monkeypatch, [])
    with_ = portfolio_body(world, monkeypatch, [fuel_finding()])
    for key in MONEY_KEYS:
        assert with_[key] == without[key], key
    for key in ("combined_value", "combined_value_state"):
        assert with_["summary"][key] == without["summary"][key], key
    assert double_count_violations(with_) == [] and double_count_violations(without) == []
    assert str(FUEL_ID) not in repr({k: with_[k] for k in MONEY_KEYS})
    before, after = without["summary"], with_["summary"]
    assert after["finding_count"] == before["finding_count"] + 1
    protect_b, protect_a = before["category_counts"]["PROTECT_ASSET"], after["category_counts"]["PROTECT_ASSET"]
    assert protect_a["open_findings"] == protect_b["open_findings"] + 1
    assert protect_a["sites_with_primary_finding"] == 1  # the mini Site (the fake rows carry no mechanism)
    risks = portfolio_body(world, monkeypatch, [fuel_finding()], lens="risks")
    cost = portfolio_body(world, monkeypatch, [fuel_finding()], lens="cost")
    assert str(FUEL_ID) in [r["finding_id"] for r in risks["rows"]]
    assert str(FUEL_ID) not in [r["finding_id"] for r in cost["rows"]]


# --- 4. consequence cases -------------------------------------------------------------------------------------------

@pytest.mark.parametrize(("q", "state", "expected"), [
    (None, CURRENT, {"state": "UNPRICED", "source_revision_id": None, "amount_low": None}),
    ({"id": CONS_ID, "state": "UNPRICED"}, CURRENT, {"state": "UNPRICED", "source_revision_id": str(CONS_ID),
                                                     "amount_low": None}),
    (PRICED, PARTIAL, {"state": "UNKNOWN", "source_revision_id": str(CONS_ID), "amount_low": None}),
    (PRICED, HISTORICAL, {"state": "UNKNOWN", "source_revision_id": str(CONS_ID), "amount_low": None}),
])
def test_consequence_cases(monkeypatch, q, state, expected) -> None:
    _, rows = run_scope(monkeypatch, FuelSnap([fuel_finding(consequence=q)]), state=state)
    (row,) = fuel_rows(rows)
    c = row["consequence"]
    assert {k: c[k] for k in expected} == expected
    assert c["amount"] is None and c["amount_high"] is None and c["currency"] is None
    assert c["basis"] == site_mini.FUEL_BASIS == index.FUEL_CONSEQUENCE_BASIS


# --- 5. gates -------------------------------------------------------------------------------------------------------

@pytest.mark.parametrize("state", [UNKNOWN, PENDING, STALE])
def test_no_fuel_row_unless_coverage_is_current_historical_or_partial(monkeypatch, state) -> None:
    snap = FuelSnap([fuel_finding()])
    _, rows = run_scope(monkeypatch, snap, state=state)
    assert fuel_rows(rows) == [] and snap.calls == []


def test_cold_site_never_reads_fuel(monkeypatch) -> None:
    snap = FuelSnap([fuel_finding()])
    monkeypatch.setattr(index, "_WindowRecorder", lambda s: s)
    run_scope(monkeypatch, snap, sites=(CO_SITE,))
    assert snap.calls == []


def test_snapshot_without_the_read_gives_no_row(monkeypatch) -> None:
    _, rows = run_scope(monkeypatch, NoFuelSnap())
    assert rows == []


def test_empty_fuel_read_is_byte_equal_to_no_read(world, monkeypatch) -> None:
    """Kobo byte-equality: `fuel_findings` -> [] gives the same rows and Portfolio body as a snapshot without it."""
    assert run_scope(monkeypatch, FuelSnap([])) == run_scope(monkeypatch, NoFuelSnap())

    def portfolio_with(snap):
        real = world.select_finding_scope

        def scope(s, t, req, sc, cutoffs=None):
            per, rows = real(s, t, req, sc, cutoffs)
            for site, _, c in per:
                if site["site_type"] == "MINIGRID":
                    rows = rows + index._fuel_rows(snap, t, site, c, req, sc["k"])
            return per, rows

        monkeypatch.setattr(portfolio, "select_finding_scope", scope)
        return get(client(world), WINDOW).json()

    assert portfolio_with(FuelSnap([])) == portfolio_with(NoFuelSnap())


# --- 6. the Action column -------------------------------------------------------------------------------------------

def _portfolio_row(monkeypatch, thread_state, consequence=PRICED, mechanism=None):
    _, rows = run_scope(monkeypatch, FuelSnap([fuel_finding(consequence=consequence)]))
    (row,) = fuel_rows(rows)
    if mechanism is not None:
        row = {**row, "_mechanism": mechanism}
    row["_thread"] = None if thread_state is None else {"state": thread_state}
    return portfolio.portfolio_row(row, [], cov(CURRENT), None)


def test_action_column_reads_the_fuel_thread(monkeypatch) -> None:
    verified = _portfolio_row(monkeypatch, "RESOLVED_MONITORING")
    assert verified["workflow_label"] == "Verified"
    assert (verified["placement"]["group"], verified["placement"]["reasons"][0]["code"]) == (
        "MONITOR", "VERIFIED_WATCH_RETURN")
    assert verified["action_id"] is None and verified["action_title"] is None
    opened = _portfolio_row(monkeypatch, "OPEN")
    assert opened["workflow_label"] == "No action agreed yet"
    assert (opened["placement"]["group"], opened["placement"]["reasons"][0]["code"]) == (
        "COMPARE_VALUE", "PRICED_SINGLE")
    unpriced = _portfolio_row(monkeypatch, "OPEN", consequence=None)
    assert (unpriced["placement"]["group"], unpriced["placement"]["reasons"][0]["code"]) == (
        "UNPRICED_RISK", "UNPRICED_OTHER")


def test_cold_row_with_a_verified_thread_keeps_its_action_words(monkeypatch) -> None:
    """The override is mechanism-gated: any other mechanism reads its (absent) Action."""
    cold = _portfolio_row(monkeypatch, "RESOLVED_MONITORING", mechanism="COLD_EXCURSION")
    assert cold["workflow_label"] == "No action agreed yet"


def test_place_without_label_is_unchanged(monkeypatch) -> None:
    _, rows = run_scope(monkeypatch, FuelSnap([fuel_finding()]))
    (row,) = fuel_rows(rows)
    assert place(row, None, cov(CURRENT), None) == place(row, None, cov(CURRENT), None, label=None)
    assert place(row, None, cov(CURRENT), None).wire()["reasons"][0]["code"] == "PRICED_SINGLE"


# --- 7. Assure (§9p.3) ----------------------------------------------------------------------------------------------

def _fuel_threads(start, end):
    occ = {"thread_id": "t-fuel", "mechanism": "UNEXPLAINED_FUEL", "subject_ref": "tank", "occurrence_no": 1,
           "finding_id": str(FUEL_ID), "opportunity_id": None, "opportunity_no": None, "episode_start": start,
           "episode_end": end}
    ev = lambda seq, state, day: {"thread_id": "t-fuel", "seq": seq, "state": state, "cause_kind": "X",  # noqa: E731
                                  "cause_id": "c", "effective_day": day, "recorded_at": datetime.combine(
                                      day, datetime.min.time(), tzinfo=timezone.utc), "cause_known_at": None}
    return {"occurrences": (occ,), "events": (ev(1, "OPEN", start.date()),
                                              ev(2, "RESOLVED_MONITORING", (start + timedelta(days=2)).date())),
            "actions": ()}


class _Req:
    def __init__(self, rows):
        self.rows, self.k = rows, None

    def day(self, site_id, site_type, days):
        return NS(days=tuple(days), grades={})

    def threads(self, site_id):
        return self.rows

    def evidence_cutoff(self, site_id):
        return None


KISIWA = NS(site_id="s4", site_code="KISIWA-001", domain="mini_grid", timezone="Africa/Dar_es_Salaam", tenant_id="t")


def test_assure_counts_the_verified_fuel_thread_only_inside_the_window(monkeypatch) -> None:
    monkeypatch.setattr(CL, "claim_days", lambda req, site, lo, hi: None)
    inside = CL.estate_count_claims(_Req(_fuel_threads(NIGHT_START, NIGHT_END)), [KISIWA], REQ.from_, REQ.to, [])
    assert inside.threads["KISIWA-001"]["verified"] == 1
    assert inside.claims["count.verified_results"].value == 1
    assert not inside.disrupted.get("KISIWA-001")
    outside = CL.estate_count_claims(_Req(_fuel_threads(NIGHT_START - timedelta(days=30),
                                                        NIGHT_END - timedelta(days=30))),
                                     [KISIWA], REQ.from_, REQ.to, [])
    assert outside.threads["KISIWA-001"]["verified"] == 0
    assert outside.claims["count.verified_results"].value == 0
    assert "RESOLVED_MONITORING" in VERIFIED_CLASS


# --- 8. store parity ------------------------------------------------------------------------------------------------

def _store(found):
    store = PostgresFuelBalanceStore.__new__(PostgresFuelBalanceStore)
    conn = object()
    store._read = lambda work: work(conn)
    store._fuel_findings = lambda c, t, s, fid, k: (assert_conn(c, conn), list(found))[1]
    return store, conn


def assert_conn(c, conn):
    assert c is conn


def test_store_on_connection_equals_the_owned_read_and_filters_the_window() -> None:
    later = fuel_finding(start=NIGHT_START + timedelta(days=1), end=NIGHT_END + timedelta(days=1))
    before = fuel_finding(start=NIGHT_START - timedelta(days=10), end=NIGHT_END - timedelta(days=10))
    store, conn = _store([later, fuel_finding(), before])
    lo, hi = REQ.from_, REQ.to
    owned = store.fuel_findings(T, MG_SITE["site_id"], lo, hi, READ_AT)
    on = store.fuel_findings_on(conn, T, MG_SITE["site_id"], lo, hi, READ_AT)
    assert owned == on and isinstance(on, tuple)
    assert [f.window.window_start for f in on] == [NIGHT_START, NIGHT_START + timedelta(days=1)]  # `before` dropped
    # A window outside [from, to) gives no row.
    assert store.fuel_findings_on(conn, T, MG_SITE["site_id"], NIGHT_END + timedelta(days=5),
                                  NIGHT_END + timedelta(days=6), READ_AT) == ()


@pytest.mark.parametrize(("lo", "hi", "k"), [
    (REQ.to, REQ.from_, None),
    (REQ.from_.replace(tzinfo=None), REQ.to, None),
    (REQ.from_, REQ.to, READ_AT.replace(tzinfo=None)),
])
def test_store_refusals_match(lo, hi, k) -> None:
    store, conn = _store([])
    for call in (lambda: store.fuel_findings(T, MG_SITE["site_id"], lo, hi, k),
                 lambda: store.fuel_findings_on(conn, T, MG_SITE["site_id"], lo, hi, k)):
        with pytest.raises(ValueError, match=FINDINGS_REFUSED.replace("(", r"\(")):
            call()
