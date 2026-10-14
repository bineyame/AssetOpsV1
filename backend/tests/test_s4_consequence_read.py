"""S4-02b phase 2a: display rounding of a stored consequence and the recompute CLI (no database)."""

from __future__ import annotations

import json
from decimal import Decimal
from types import SimpleNamespace
from uuid import uuid4

from assetops_backend.financials.consequence_read import MINOR_UNITS, display
from assetops_backend.recompute_consequences import main


def row(high: str, currency: str, low: str = "0") -> dict:
    return {"state": "PRICED", "currency": currency, "amount_low": Decimal(low), "amount_high": Decimal(high)}


def test_high_rounds_up_and_low_down_to_the_currency_minor_unit() -> None:
    d = display(row("3.4375", "USD"))
    assert (d["amount_low"], d["amount_high"], d["minor_unit"]) == ("0.00", "3.44", 2)
    assert display(row("3.4301", "USD"))["amount_high"] == "3.44"  # up, not to nearest
    assert display(row("3.44", "USD"))["amount_high"] == "3.44"  # exact stays exact
    assert display(row("5", "USD", low="0.019"))["amount_low"] == "0.01"  # down


def test_non_two_decimal_currencies() -> None:
    assert MINOR_UNITS["JPY"] == 0 and display(row("412.01", "JPY"))["amount_high"] == "413"
    assert MINOR_UNITS["KWD"] == 3 and display(row("1.23401", "KWD"))["amount_high"] == "1.235"


def test_unknown_minor_unit_shows_no_rounded_amount_and_unpriced_has_no_display() -> None:
    d = display(row("3.4375", "XYZ"))
    assert (d["state"], d["amount_low"], d["amount_high"]) == ("MINOR_UNIT_UNKNOWN", None, None)
    assert display({"state": "UNPRICED", "currency": None, "amount_low": None, "amount_high": None}) is None


class Prices:
    def __init__(self, scope):
        self.scope = scope

    def site_scope(self, tenant, code):
        return self.scope


class Worker:
    def __init__(self, outs):
        self.outs = outs

    def run_pending(self, tenant_id, site_id, limit):
        return self.outs


def test_cli_reports_each_work_item_and_fails_when_any_failed(capsys) -> None:
    ok = SimpleNamespace(work_id=uuid4(), cause="ASSUMPTION_PUBLISHED", succeeded=True, attempt_no=1,
                         appended=[uuid4()], replayed=[], error_code=None, error_detail=None)
    bad = SimpleNamespace(work_id=uuid4(), cause="FINDING_REVISION_APPENDED", succeeded=False, attempt_no=2,
                          appended=[], replayed=[], error_code="STORE_UNAVAILABLE", error_detail="down")
    prices = Prices(("KOBO-001", uuid4(), uuid4()))
    assert main(["run", "--site", "KOBO-001"], worker=Worker([ok]), prices=prices) == 0
    assert main(["run", "--site", "KOBO-001"], worker=Worker([ok, bad]), prices=prices) == 1
    lines = [json.loads(x) for x in capsys.readouterr().out.splitlines()]
    assert [x["succeeded"] for x in lines] == [True, True, False] and lines[-1]["error_code"] == "STORE_UNAVAILABLE"
    assert main(["run", "--site", "NOPE"], worker=Worker([]), prices=Prices(None)) == 2
