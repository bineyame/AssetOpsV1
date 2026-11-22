"""DD2.5 (D-DD.55): the checker's C-DD2 to C-DD4 judged on the simulator's emulated Lakeside books.

The checker (`tools/dd_check.py`) imports nothing from the simulator; this test feeds it the rows the exporter emits, as
the stored-record dicts the SQL read returns. Each plant must flip its check.
"""
from __future__ import annotations

import copy
import sys
from decimal import Decimal

import pytest

from .conftest import REPOSITORY_ROOT

sys.path.insert(0, str(REPOSITORY_ROOT / "tools"))
import dd_check  # noqa: E402

LAKESIDE = {"lakeside-power"}


@pytest.fixture(scope="module")
def inputs() -> dd_check.Inputs:
    return dd_check.read_inputs("postgresql+psycopg://u:p@dd.invalid:1/x_test")


@pytest.fixture(scope="module")
def mini_rows(inputs) -> list[dict]:
    """The emulator's Lakeside books, as the stored-record dicts the SQL read returns (latest revisions)."""
    from assetops_simulator.world.exports import build_exports
    from assetops_simulator.world.history import generate_history
    from assetops_simulator.world.view import ManifestView

    view = ManifestView.from_document(inputs.manifest)
    result = build_exports(view, generate_history(view))
    rows = []
    for f in result.files:
        for r in f.records:
            rows.append({"tenant": f.tenant, "site": r["site_code"], "kind": r["kind"],
                         "month": r["clocks"]["recognition_period"] if "recognition_period" in r["clocks"] else "",
                         "provenance": "source-emulated",
                         "amount": Decimal(r["amount"]["value"]) if "amount" in r else None,
                         "quantity": Decimal(r["quantity"]["value"]) if "quantity" in r else None,
                         "status": r.get("status"), "body": r.get("body", {})})
    return rows


# --- C-DD2 to C-DD4 ------------------------------------------------------------------------------------------------------

def test_the_mini_grid_books_pass_all_three(inputs, mini_rows) -> None:
    for judge in (dd_check.judge_kinds, dd_check.judge_identities, dd_check.judge_leaves_and_nodes):
        result = judge(inputs, mini_rows, LAKESIDE)
        assert result.passed, result.detail


def test_c_dd2_fails_on_a_missing_kind_and_a_wrong_source_word(inputs, mini_rows) -> None:
    short = [r for r in mini_rows if not (r["site"] == "KOBO-001" and r["month"] == "2026-08" and r["kind"] == "RECEIPT")]
    result = dd_check.judge_kinds(inputs, short, LAKESIDE)
    assert not result.passed and "lakeside-power/KOBO-001 2026-08: no RECEIPT record" in result.detail
    wrong = copy.deepcopy(mini_rows)
    wrong[0]["provenance"] = "field-integrated"
    assert not dd_check.judge_kinds(inputs, wrong, LAKESIDE).passed


def test_c_dd2_fails_without_the_other_tenants_books(inputs, mini_rows) -> None:
    result = dd_check.judge_kinds(inputs, mini_rows)  # all three tenants: cold and EV are DD2b's rows
    assert not result.passed and any(line.startswith("harvest-cold/") for line in result.detail)


def test_c_dd3_fails_when_billed_does_not_make_revenue(inputs, mini_rows) -> None:
    bent = copy.deepcopy(mini_rows)
    next(r for r in bent if r["site"] == "MTO-001" and r["month"] == "2026-09" and r["kind"] == "CHARGE")["amount"] += 1
    result = dd_check.judge_identities(inputs, bent, LAKESIDE)
    assert not result.passed and any("MTO-001 2026-09: revenue" in line for line in result.detail)


def test_c_dd3_fails_when_collections_do_not_close(inputs, mini_rows) -> None:
    bent = [r for r in mini_rows if not (r["site"] == "KOBO-001" and r["month"] == "2026-07" and r["kind"] == "RECEIPT"
                                         and r["body"].get("payer_ref", "").endswith("0001"))]
    result = dd_check.judge_identities(inputs, bent, LAKESIDE)
    assert not result.passed and any("KOBO-001 2026-07: collected" in line for line in result.detail)


def test_c_dd4_fails_when_a_history_node_is_not_the_manifests_evaluation(inputs, mini_rows) -> None:
    """The plant that matters: billed kWh is derived, so only an independent evaluation can see it move."""
    bent = copy.deepcopy(mini_rows)
    charges = [r for r in bent if r["site"] == "KOBO-001" and r["month"] == "2026-07" and r["kind"] == "CHARGE"]
    charges[0]["quantity"] += 1
    charges[0]["amount"] += Decimal("0.40")  # keeps C-DD3's identity: revenue = billed x tariff
    next(r for r in bent if r["site"] == "KOBO-001" and r["month"] == "2026-07" and r["kind"] == "RECEIPT")[
        "amount"] += Decimal("0.40")  # ... and collected + outstanding = revenue
    assert dd_check.judge_identities(inputs, bent, LAKESIDE).passed
    result = dd_check.judge_leaves_and_nodes(inputs, bent, LAKESIDE)
    assert not result.passed
    assert any("KOBO-001 2026-07: billed_kwh stored 8319 != evaluated 8318" in line for line in result.detail)


def test_c_dd4_fails_on_a_leaf_and_on_octobers_recorded_node(inputs, mini_rows) -> None:
    bent = copy.deepcopy(mini_rows)
    next(r for r in bent if r["site"] == "KOBO-001" and r["month"] == "2026-08" and r["kind"] == "EXPENSE"
         and r["body"].get("category") == "STAFF")["amount"] += Decimal("0.01")
    assert any("KOBO-001 2026-08: STAFF" in line
               for line in dd_check.judge_leaves_and_nodes(inputs, bent, LAKESIDE).detail)
    october = copy.deepcopy(mini_rows)
    next(r for r in october if r["site"] == "KOBO-001" and r["month"] == "2026-10" and r["kind"] == "EXPENSE"
         and r["body"].get("category") == "FUEL")["amount"] += Decimal("0.01")
    assert any("KOBO-001 2026-10: fuel_cost" in line
               for line in dd_check.judge_leaves_and_nodes(inputs, october, LAKESIDE).detail)




def test_the_mini_grid_detail_lines_are_unchanged_by_the_ev_and_missing_figure_rules(inputs, mini_rows) -> None:
    """D-DD.58 parity: the existing fixture rows give the same C-DD3 detail lines as before the fix round."""
    bent = copy.deepcopy(mini_rows)
    next(r for r in bent if r["site"] == "MTO-001" and r["month"] == "2026-09" and r["kind"] == "CHARGE")["amount"] += 1
    result = dd_check.judge_identities(inputs, bent, LAKESIDE)
    assert len(result.detail) == 2 and not result.pending
    assert result.detail[0].startswith("lakeside-power/MTO-001 2026-09: revenue ")
    assert result.detail[0].endswith(" x tariff " + str(Decimal(str(
        next(t for t in inputs.manifest["tenants"] if t["tenant"] == "lakeside-power")["prices"]["tariff_usd_per_kwh"]["Mto"]))))
    assert result.detail[1].startswith("lakeside-power/MTO-001 2026-09: collected ")
