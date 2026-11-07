"""PV-1 (FUEL-1 PV-1-R): the Portfolio Assure card's verified-value lines, one per verified result with money, each
with its own basis, never added together. L0: fake ports, no DB.

The board's Assure row carries `nodes.verified_values` (mill: the verdict page's own `value`; trial: the credited
stored priced total); `portfolio_cards` lists them per Site and states the clause; `card_notes` keeps the gap clause."""
from __future__ import annotations

import json
from dataclasses import replace
from datetime import date
from decimal import Decimal
from fractions import Fraction
from uuid import UUID

import pytest
from fastapi.encoders import jsonable_encoder

from assetops_backend.actions import verification_families as vf
from assetops_backend.chain import vocabulary as v
from assetops_backend.estate.portfolio import card_notes
from assetops_backend.outcomes.credit import MONEY_NOT_CREDITED
from assetops_backend.outcomes.display_code import display_code
from assetops_backend.site_outcomes import mini
from assetops_backend.site_outcomes.read import portfolio_cards

import test_mb1_opportunity_board as MB
import test_out_b2_mini as B2
from test_ch9b3_mill_verdict import _details, _price

MILL_DETAILS = _details("42.00", "110.00")
MILL_VALUE = jsonable_encoder(vf.mill_value(MILL_DETAILS, "VERIFIED", _price("0.25")))


def _cost_check(amount="4.125", litres="3.3", state="MODELLED_IMPROVEMENT", with_total=True):
    cc = {"state": state, "reason": None, "nominal": "0.275", "upper": "0.3", "currency": "USD",
          "recorded_at": "2026-10-20T00:00:00+00:00"}
    if with_total:
        cc["priced_total"] = {"amount": amount, "currency": "USD", "basis": "TRIAL_HOUR_MODELLED_FUEL",
                              "window": ["2026-10-19T10:00:00+00:00", "2026-10-19T11:00:00+00:00"],
                              "fuel_change_l": litres}
    return cc


class Port:
    """A counting `verdict_value` fake."""

    def __init__(self, value=MILL_VALUE, raises=False):
        self.value, self.raises, self.calls = value, raises, []

    def __call__(self, action_id):
        self.calls.append(action_id)
        if self.raises:
            raise RuntimeError("verdict refused")
        return self.value


def _ports(fake, *, mill=None, port=None, k=None):
    ports = fake.ports() if mill is None else MB._mill_ports(fake, mill, k=k)
    return replace(ports, verdict_value=port or Port())


def _trial(cost_check=None, state="VERIFIED"):
    return B2.Fake(verification={"state": state, "source_class": None, "cost_check": cost_check})


def _values(rows):
    return (rows[mini.ASSURE]["nodes"] or {}).get("verified_values")


# ---- the board's Assure row ---------------------------------------------------------------------------------------

def test_no_mill_and_no_credited_trial_give_no_key_and_never_call_the_port() -> None:
    port = Port()
    _, rows = MB._compose(_ports(_trial(None), port=port))
    assert _values(rows) is None and "verified_values" not in (rows[mini.ASSURE]["nodes"] or {})
    assert port.calls == []


def test_mill_only_is_one_entry_equal_to_the_verdict_page_value() -> None:
    port = Port()
    comp, rows = MB._compose(_ports(_trial(None, state="PENDING"), mill=MB._mill(), port=port))
    assert port.calls == [MB.MILL]
    want = vf.mill_value(MILL_DETAILS, "VERIFIED", _price("0.25"))
    assert _values(rows) == [{
        "key": MB.MILL, "action_code": "ACT-000002", "basis": want["basis"], "amount": want["per_day"],
        "currency": "USD",
        "text": mini.VALUE_LINE_MILL.format(code=display_code("ACT-000002"), d=want["per_day"], cur="USD")}]
    # S-c parity: the entry's amount is MV-1's `mill_value` over the same details and price
    assert _values(rows)[0]["amount"] == want["per_day"] == "17.00"
    assert comp.read_state == "AVAILABLE"


def test_mill_plus_trial_are_two_entries_in_code_order_never_summed() -> None:
    _, rows = MB._compose(_ports(_trial(_cost_check()), mill=MB._mill()))
    entries = _values(rows)
    assert [e["action_code"] for e in entries] == ["ACT-000002", "ACT-048"]
    trial = entries[1]
    assert trial == {"key": "a48", "action_code": "ACT-048", "basis": "TRIAL_HOUR_MODELLED_FUEL", "amount": "4.12",
                     "currency": "USD", "text": mini.VALUE_LINE_TRIAL_FUEL.format(
                         code=display_code("ACT-048"), l="3.3", amount="4.12", cur="USD")}
    total = f"{Decimal(entries[0]['amount']) + Decimal(entries[1]['amount']):.2f}"
    assert total not in json.dumps(rows, default=str)


@pytest.mark.parametrize("value", [None, jsonable_encoder(vf.mill_value(
    MILL_DETAILS, "VERIFIED", _price(state="NOT_DECLARED", reason="NO_REVISION")))])
def test_an_unpriced_or_absent_mill_value_gives_no_entry(value) -> None:
    assert value is None or value["state"] == "UNPRICED"
    _, rows = MB._compose(_ports(_trial(None), mill=MB._mill(), port=Port(value)))
    assert _values(rows) is None


def test_a_failed_verdict_value_read_is_partial_and_gives_no_entry() -> None:
    comp, rows = MB._compose(_ports(_trial(_cost_check()), mill=MB._mill(), port=Port(raises=True)))
    assert comp.read_state == "PARTIAL" and "verdict_value" in comp.failed
    assert [e["action_code"] for e in _values(rows)] == ["ACT-048"]


@pytest.mark.parametrize("mill", [MB._mill(outcome="INEFFECTIVE"), MB._mill(outcome="INCONCLUSIVE")])
def test_the_port_is_not_called_without_a_verified_mill(mill) -> None:
    port = Port()
    _, rows = MB._compose(_ports(_trial(None), mill=mill, port=port))
    assert port.calls == [] and _values(rows) is None


def test_a_mill_verdict_after_the_cutoff_is_not_read() -> None:
    port = Port()
    _, rows = MB._compose(_ports(_trial(None), mill=MB._mill(), port=port, k=B2.T(14)))
    assert port.calls == [] and _values(rows) is None


@pytest.mark.parametrize(("cc", "state"), [
    (_cost_check(with_total=False), "VERIFIED"),                      # a `/1` result: no priced total
    (_cost_check(amount="-1.5"), "VERIFIED"),                          # negative
    (_cost_check(amount="0"), "VERIFIED"),                             # zero
    (_cost_check(state="NO_MODELLED_IMPROVEMENT"), "VERIFIED"),        # not an improvement
    (_cost_check(), "INEFFECTIVE"),                                    # not VERIFIED
])
def test_an_uncredited_trial_gives_no_entry(cc, state) -> None:
    _, rows = MB._compose(_ports(_trial(cc, state=state)))
    assert _values(rows) is None


@pytest.mark.parametrize(("amount", "litres", "want_amount", "want_litres"), [
    ("1/3", "0.25", "0.33", "0.2"), ("0.125", "3.3", "0.12", "3.3"), ("0.135", "0.35", "0.14", "0.4")])
def test_rounding_is_half_even(amount, litres, want_amount, want_litres) -> None:
    _, rows = MB._compose(_ports(_trial(_cost_check(amount=amount, litres=litres))))
    (entry,) = _values(rows)
    assert entry["amount"] == want_amount
    assert entry["text"] == mini.VALUE_LINE_TRIAL_FUEL.format(code=display_code("ACT-048"), l=want_litres,
                                                              amount=want_amount, cur="USD")
    assert want_amount == f"{Decimal(round(Fraction(amount) * 100)) / 100:.2f}"


def test_grow_optimize_and_protect_rows_are_byte_equal_with_and_without_entries() -> None:
    fake = _trial(_cost_check())
    _, without = MB._compose(_ports(fake, mill=MB._mill(), port=Port(None)))
    _, with_values = MB._compose(_ports(_trial(_cost_check()), mill=MB._mill()))
    for cat in (mini.GROW, mini.COST, mini.PROTECT):
        assert with_values[cat] == without[cat], cat
    assert len(_values(with_values)) == 2
    a, b = dict(with_values[mini.ASSURE]), dict(without[mini.ASSURE])
    a["nodes"] = {k: x for k, x in a["nodes"].items() if k != "verified_values"}
    b["nodes"] = {k: x for k, x in b["nodes"].items() if k != "verified_values"}
    assert a == b   # the board shows no new line: only `nodes.verified_values` differs


def test_the_board_service_binds_verdict_value_to_the_verification_domain_summary() -> None:
    """PV-1-R §1: `read.py` `mini_ports` reads `s.verification.domain_summary(t, sid, UUID(id))["value"]`."""
    import test_ch5a1_board_contract as BC
    from assetops_backend import read_scope
    from assetops_backend.site_outcomes.read import SiteOutcomeBoardService

    class Port_(BC.Port):
        def site_threads(self, tenant_id, site_id, known_at):
            occ = (MB._occ(MB.MILL_T, None, MB.OPP, BC.at(20)),)
            return MB._rows(MB._act(aid=str(UUID(int=7)), accepted=BC.at(21), recorded=BC.at(22)), occurrences=occ)

    seen = []

    class Verification:
        def domain_summary(self, tenant_id, site_id, action_id):
            seen.append((tenant_id, site_id, action_id))
            return {"value": vf.mill_value(MILL_DETAILS, "VERIFIED", _price("0.25")), "state": "VERIFIED"}

    svc = replace(BC.services(Port_(), []), verification=Verification())
    with read_scope.scope("test:pv1"):
        body = SiteOutcomeBoardService(svc).board(BC.KOBO, known_at=BC.KNOWN, day=date(2026, 10, 31))
    assert seen == [(BC.KOBO.tenant_id, BC.KOBO.site_id, UUID(int=7))]
    assure = next(r for r in body["rows"] if r["category"] == mini.ASSURE)
    assert [e["amount"] for e in assure["nodes"]["verified_values"]] == ["17.00"]


# ---- the Portfolio card -------------------------------------------------------------------------------------------

def _site(code, name, entries=None, grow_nodes=None):
    assure_nodes = {"kpi": None, "earnings": None, "potential": None}
    if entries is not None:
        assure_nodes["verified_values"] = entries
    return {"site_code": code, "site_name": name, "earnings": None,
            "rows": [{"category": "GROW_REVENUE", "state": "OPPORTUNITY", "state_label": "Opportunity",
                      "short_value": None, "nodes": grow_nodes},
                     {"category": "ASSURE_PERFORMANCE", "state": "ON_TRACK", "state_label": "On track",
                      "short_value": None, "nodes": assure_nodes}]}


def _entry(key, code, amount, text):
    return {"key": key, "action_code": code, "basis": "B", "amount": amount, "currency": "USD", "text": text}


MILL_E = _entry("m", "ACT-000002", "17.00", "ACT-2: mill")
TRIAL_E = _entry("t", "ACT-048", "4.12", "ACT-48: trial")
OTHER_E = _entry("x", "ACT-003", "1.50", "ACT-3: other")


def _cards(sites):
    return portfolio_cards(sites, None, v.estate_income([]), [], None, 0)


def test_card_lists_site_order_then_code_order_and_states_the_clause() -> None:
    sites = [_site("K", "Kobo", [MILL_E, TRIAL_E]), _site("C", "GreenHarvest"), _site("D", "Depot", [OTHER_E])]
    assure = _cards(sites)["ASSURE_PERFORMANCE"]
    assert assure["value_lines"] == ["Kobo · ACT-2: mill", "Kobo · ACT-48: trial", "Depot · ACT-3: other"]
    assert assure["value_lines"][0] == v.card_text("assure.value_line", site="Kobo", text=MILL_E["text"])
    assert assure["value_note"] == v.card_text("assure.values_separate")
    # never summed: no Decimal sum of any two same-currency amounts appears anywhere on the card
    amounts = [e["amount"] for e in (MILL_E, TRIAL_E, OTHER_E)]
    blob = json.dumps(assure)
    for i, a in enumerate(amounts):
        for b in amounts[i + 1:]:
            assert f"{Decimal(a) + Decimal(b):.2f}" not in blob
    assert f"{sum(Decimal(a) for a in amounts):.2f}" not in blob


def test_no_line_reads_the_not_credited_clause() -> None:
    assure = _cards([_site("K", "Kobo"), _site("D", "Depot", [])])["ASSURE_PERFORMANCE"]
    assert assure["value_lines"] == [] and assure["value_note"] == MONEY_NOT_CREDITED
    assert _cards([])["ASSURE_PERFORMANCE"]["value_note"] == MONEY_NOT_CREDITED


def test_grow_optimize_and_protect_cards_are_byte_equal_with_lines() -> None:
    with_lines = _cards([_site("K", "Kobo", [MILL_E, TRIAL_E])])
    without = _cards([_site("K", "Kobo")])
    for key in ("GROW_REVENUE", "OPTIMIZE_COST", "PROTECT_ASSET"):
        assert with_lines[key] == without[key], key
    a, b = dict(with_lines["ASSURE_PERFORMANCE"]), dict(without["ASSURE_PERFORMANCE"])
    for d in (a, b):
        d.pop("value_lines"), d.pop("value_note")
    assert a == b


def test_card_notes_gives_the_gap_clause_alone() -> None:
    notes = card_notes({"count_basis": "COMPLETE", "evidence_gap_site_count": 0}, 3)
    assert notes == {"PROTECT_ASSET": None, "ASSURE_PERFORMANCE": v.evidence_gap_text(0, 3, False)}
    assert MONEY_NOT_CREDITED not in notes["ASSURE_PERFORMANCE"]
