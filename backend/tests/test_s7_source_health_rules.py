"""S7-01b follow-up to the S7-01a source-health read (`D-2026-10-16-s701-clock`).

Pure rule checks, no database: the two separate 5000 ms rules, never a signed or untrusted reported age, and
the typed reason beside `NO_REGISTERED_SOURCE`.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import uuid4

from assetops_backend.evidence import source_health as sh

READ = datetime(2026, 10, 16, 9, 10, tzinfo=timezone.utc)


def test_the_two_rules_are_separate_named_constants_with_the_ruled_values() -> None:
    assert sh.CLOCK_OFFSET_LIMIT_MS == 5_000
    assert sh.OBSERVED_AFTER_RECEIPT_ALLOWANCE_MS == 5_000
    assert not hasattr(sh, "CLOCK_TRUST_TOLERANCE_MS")


def test_clock_offset_limit_is_inclusive() -> None:
    assert sh.clock_trust(5_000)[0] == "WITHIN_TOLERANCE"
    assert sh.clock_trust(-5_000)[0] == "WITHIN_TOLERANCE"
    assert sh.clock_trust(5_001) == ("UNTRUSTED", "OFFSET_BEYOND_TOLERANCE")
    assert sh.clock_trust(None) == ("UNKNOWN", "OFFSET_NOT_MEASURED")


def test_observed_after_receipt_allowance_is_inclusive_and_independent_of_offset() -> None:
    received = READ - timedelta(seconds=10)
    at_limit = received + timedelta(milliseconds=sh.OBSERVED_AFTER_RECEIPT_ALLOWANCE_MS)
    assert sh.fact_age(at_limit, received, "WITHIN_TOLERANCE", 60, READ)[0] == "CURRENT"
    beyond = at_limit + timedelta(milliseconds=1)
    assert sh.fact_age(beyond, received, "WITHIN_TOLERANCE", 60, READ) == ("UNKNOWN", "OBSERVED_AFTER_RECEIPT")
    assert sh.fact_age(beyond, received, "UNKNOWN", 60, READ) == ("UNKNOWN", "OBSERVED_AFTER_RECEIPT")


def test_reported_age_is_never_negative_and_never_from_an_untrusted_clock() -> None:
    assert sh.reported_age(READ - timedelta(seconds=30), "WITHIN_TOLERANCE", READ) == 30
    assert sh.reported_age(READ, "WITHIN_TOLERANCE", READ) == 0
    assert sh.reported_age(READ + timedelta(seconds=2), "WITHIN_TOLERANCE", READ) is None
    assert sh.reported_age(READ - timedelta(seconds=30), "UNTRUSTED", READ) is None
    assert sh.reported_age(None, "WITHIN_TOLERANCE", READ) is None


def _snapshot(*disabled: bool) -> sh.SourceHealthSnapshot:
    tenant, site = uuid4(), uuid4()
    gateways = tuple(sh.RegisteredGateway(tenant, site, uuid4(), f"edge-{i}", "SIMULATED", READ - timedelta(days=1),
                                          flag, 60) for i, flag in enumerate(disabled))
    return sh.SourceHealthSnapshot(tenant, site, "repeatable read", gateways, (), ())


def test_summary_reason_names_why_there_is_no_source() -> None:
    empty = sh.source_health_document(_snapshot(), "S", READ, "test")["summary"]
    assert (empty["status"], empty["reason"]) == ("NO_REGISTERED_SOURCE", "NO_REGISTERED_GATEWAY")
    disabled = sh.source_health_document(_snapshot(True, True), "S", READ, "test")
    assert (disabled["summary"]["status"], disabled["summary"]["reason"]) == ("NO_REGISTERED_SOURCE",
                                                                              "NO_ENABLED_GATEWAY")
    assert disabled["summary"]["disabled_gateway_count"] == 2
    assert {g["registration"] for g in disabled["gateways"]} == {"DISABLED"}
    enabled = sh.source_health_document(_snapshot(False, True), "S", READ, "test")["summary"]
    assert (enabled["status"], enabled["reason"]) == ("NOT_ALL_CURRENT", None)
    assert enabled["enabled_gateway_count"] == 1 and enabled["contact_counts"]["UNKNOWN"] == 1


def test_receipt_lag_is_never_negative_and_keeps_legitimate_lag() -> None:
    """W1-UX-06: a report observed after it was received publishes no lag (null), never a negative number."""
    received = READ - timedelta(seconds=10)
    assert sh.receipt_lag(received, received - timedelta(seconds=21_600)) == 21_600
    assert sh.receipt_lag(received, received - timedelta(seconds=2)) == 2
    assert sh.receipt_lag(received, received) == 0
    assert sh.receipt_lag(received, received + timedelta(seconds=90)) is None
    # Within the observed-after-receipt allowance the observation is still after receipt: no negative lag either.
    assert sh.receipt_lag(received, received + timedelta(milliseconds=1)) is None
