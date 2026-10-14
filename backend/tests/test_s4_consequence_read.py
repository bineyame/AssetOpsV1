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
    def __init__(self, outs, claimed=True):
        self.outs, self.claimed, self.calls = outs, claimed, []

    def run(self, tenant_id, site_id, limit):
        from datetime import datetime, timezone

        from assetops_backend.financials.recompute import RunReport

        self.calls.append(limit)
        return RunReport(tenant_id, site_id, self.claimed, datetime(2026, 10, 14, tzinfo=timezone.utc),
                         list(self.outs) if self.claimed else [], deferred=1, backlog=2)


def out(cause, succeeded, *, appended=(), no_op_reason=None, error_code=None):
    return SimpleNamespace(work_id=uuid4(), cause=cause, succeeded=succeeded, attempt_no=1,
                           appended=list(appended), replayed=[], no_op_reason=no_op_reason, error_code=error_code,
                           error_detail=None if error_code is None else "down")


def test_cli_reports_each_work_item_a_scoped_summary_and_fails_when_any_failed(capsys) -> None:
    ok = out("ASSUMPTION_PUBLISHED", True, appended=[uuid4()])
    noop = out("EVIDENCE_ACCEPTED", True, no_op_reason="FINDING_REVISION_SUPERSEDED")
    bad = out("FINDING_REVISION_APPENDED", False, error_code="STORE_UNAVAILABLE")
    prices = Prices(("KOBO-001", uuid4(), uuid4()))
    w = Worker([ok, noop])
    assert main(["run", "--tenant", "demo", "--site", "KOBO-001", "--limit", "7"], worker=w, prices=prices) == 0
    assert w.calls == [7]
    assert main(["run", "--tenant", "demo", "--site", "KOBO-001"], worker=Worker([ok, bad]), prices=prices) == 1
    lines = [json.loads(x) for x in capsys.readouterr().out.splitlines()]
    summary = lines[2]
    assert {k: summary[k] for k in ("site_code", "tenant", "claimed", "skipped", "limit", "selected", "appended",
                                    "replayed", "no_op", "failed", "deferred", "backlog")} == {
        "site_code": "KOBO-001", "tenant": "demo", "claimed": True, "skipped": False, "limit": 7, "selected": 2,
        "appended": 1, "replayed": 0, "no_op": 1, "failed": 0, "deferred": 1, "backlog": 2}
    assert lines[1]["no_op_reason"] == "FINDING_REVISION_SUPERSEDED"
    assert lines[4]["error_code"] == "STORE_UNAVAILABLE" and lines[5]["failed"] == 1 and lines[5]["limit"] == 100
    assert main(["run", "--tenant", "demo", "--site", "NOPE"], worker=Worker([]), prices=Prices(None)) == 2


def test_cli_reports_a_claimed_site_as_skipped_and_refuses_other_tenants(capsys) -> None:
    prices = Prices(("KOBO-001", uuid4(), uuid4()))
    assert main(["run", "--tenant", "demo", "--site", "KOBO-001"], worker=Worker([], claimed=False),
                prices=prices) == 0
    (summary,) = [json.loads(x) for x in capsys.readouterr().out.splitlines()]
    assert (summary["claimed"], summary["skipped"], summary["selected"]) == (False, True, 0)
    # Item 4: explicit tenant and Site; another tenant is refused, never iterated as all-Site coverage.
    assert main(["run", "--tenant", "acme", "--site", "KOBO-001"], worker=Worker([]), prices=prices) == 2
    assert "does not cover other tenants" in capsys.readouterr().err
