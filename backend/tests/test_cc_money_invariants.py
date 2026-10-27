"""CC-R1: `estate.money_invariants.double_count_violations` over crafted Portfolio/Financials bodies (pure).

Commercial build spec 2026-10-27, CC-R1 gates: `[]` on clean bodies (the persisted `test_w303_portfolio_*` bodies
are checked in `test_w303_portfolio_scope_snapshot_postgres.Portfolio.ok` and the fixture test), one violation per
crafted defect.
"""

from __future__ import annotations

import copy

import pytest

from assetops_backend.estate.money_invariants import double_count_violations


def _line(key, tech, cited, **extra):
    amount = {"low": "1.10", "high": "2.20", "currency": "KES"}
    return {"line_key": key, "category": "GROSS_TARIFF_SCENARIO", "beneficiary": "CHARGING_SERVICE",
            "window_start": "2026-10-13T08:00:00Z", "window_end": "2026-10-13T09:05:00Z",
            "period_kind": "SCENARIO_WINDOW", "assumption_fingerprint": "sha256:" + "a" * 64,
            "technical_interval_ids": tech, "basis_evidence_ids": cited, "amount": amount,
            "disclosure": {"pinned_amount": amount}, **extra}


def _group(keys):
    return {"group_key": "sha256:g", "state": "COMPARABLE", "line_keys": list(keys),
            "amount": {"low": "2.20", "high": "4.40", "currency": "KES"}}


def clean():
    lines = [_line("ev_charging:a", ["t1"], ["c1"]), _line("ev_charging:b", ["t2"], ["c2"]),
             # an unpriced line: in the member set, in no amount-bearing group
             _line("cold_chain:c", [], [], category="POTENTIAL_PRODUCT_EXPOSURE", beneficiary="GOODS_OWNER",
                   amount=None, disclosure={"pinned_amount": None})]
    unpriced = {"group_key": "sha256:u", "state": "INELIGIBLE", "line_keys": ["cold_chain:c"], "amount": None}
    portfolio = {"summary": {"combined_value": None}, "selected_lines": lines,
                 "money": {"groups": [_group(["ev_charging:a", "ev_charging:b"]), unpriced], "estate_total": None}}
    financials = {"summary": {"estate_total": None}, "groups": copy.deepcopy(portfolio["money"]["groups"]),
                  "rows": []}  # paged rows are never the member set
    return portfolio, financials


def test_clean_bodies_have_no_violation() -> None:
    portfolio, financials = clean()
    assert double_count_violations(portfolio) == []
    assert double_count_violations(portfolio, financials) == []
    # A line without the key falls back to its category's beneficiary.
    del portfolio["selected_lines"][1]["beneficiary"]
    assert double_count_violations(portfolio, financials) == []


def _set(path, value):
    def apply(portfolio, financials):
        body = financials if path[0] == "financials" else portfolio
        target = body
        for key in path[1:-1]:
            target = target[key]
        target[path[-1]] = value
    return apply


def _member(index, **change):
    def apply(portfolio, financials):
        portfolio["selected_lines"][index].update(change)
    return apply


def _currency(portfolio, financials):
    line = portfolio["selected_lines"][1]
    line["amount"] = {**line["amount"], "currency": "USD"}


DEFECTS = {
    "portfolio estate total": (_set(("portfolio", "money", "estate_total"), {"low": "1"}), "TOTAL_NOT_NULL"),
    "combined value": (_set(("portfolio", "summary", "combined_value"), "4.40"), "TOTAL_NOT_NULL"),
    "financials estate total": (_set(("financials", "summary", "estate_total"), "4.40"), "TOTAL_NOT_NULL"),
    "missing member": (lambda p, f: f["groups"][0]["line_keys"].append("ev_charging:z"), "MEMBER_NOT_FOUND"),
    "category": (_member(1, category="CANDIDATE_OPERATING_COST_EXPOSURE", beneficiary="CHARGING_SERVICE"),
                 "MEMBERS_DISAGREE"),
    "currency": (_currency, "MEMBERS_DISAGREE"),
    "window start": (_member(1, window_start="2026-10-13T07:00:00Z"), "MEMBERS_DISAGREE"),
    "window end": (_member(1, window_end="2026-10-13T10:00:00Z"), "MEMBERS_DISAGREE"),
    "period": (_member(1, period_kind="OBSERVED_WINDOW"), "MEMBERS_DISAGREE"),
    "fingerprint": (_member(1, assumption_fingerprint="sha256:" + "b" * 64), "MEMBERS_DISAGREE"),
    "beneficiary": (_member(1, beneficiary="FLEET_OPERATOR"), "MEMBERS_DISAGREE"),
    "technical": (_member(1, technical_interval_ids=["t1"]), "MEMBERS_INTERSECT"),
    "cited": (_member(1, basis_evidence_ids=["c1"]), "MEMBERS_INTERSECT"),
}


@pytest.mark.parametrize("name", sorted(DEFECTS))
def test_one_violation_per_crafted_defect(name) -> None:
    portfolio, financials = clean()
    # Member defects are seen by both bodies' groups; check them over the Portfolio groups alone.
    member_defect = name not in ("financials estate total", "missing member")
    apply, code = DEFECTS[name]
    apply(portfolio, financials)
    found = double_count_violations(portfolio, None if member_defect else financials)
    assert len(found) == 1 and found[0].startswith(code + ":"), (name, found)


def test_paged_rows_are_never_the_member_set() -> None:
    portfolio, financials = clean()
    financials["rows"] = list(portfolio["selected_lines"])
    portfolio["selected_lines"] = portfolio["selected_lines"][:1]
    found = double_count_violations(portfolio, financials)
    assert found and all(v.startswith("MEMBER_NOT_FOUND:") for v in found)


def test_unpriced_groups_are_not_checked() -> None:
    portfolio, financials = clean()
    portfolio["money"]["groups"][1]["line_keys"].append("nowhere")
    assert double_count_violations(portfolio, None) == []


def test_fake_world_portfolio_body_is_clean(monkeypatch) -> None:
    import test_w303_portfolio_api as api
    from assetops_backend.estate.scope import PORTFOLIO_CURSOR_KEY_ENV
    monkeypatch.setenv(PORTFOLIO_CURSOR_KEY_ENV, api.KEY_HEX)
    body = api.get(api.client(api.World(monkeypatch)), {**api.WINDOW, "limit": 4}).json()
    assert "selected_lines" in body and double_count_violations(body) == []
