"""OUT-B addendum 7: the board's estate reads use the covering UTC days; the estate methods keep the estate's own
window rule (no bypass, never widened); more than 31 covering days is INVALID_WINDOW, Assure UNKNOWN, board PARTIAL.
No database: the estate services are real classes whose snapshot read is replaced by a marker."""
from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

import pytest

from assetops_backend.estate.portfolio import EstatePortfolioService
from assetops_backend.estate.scope import EstateRefusal
from assetops_backend.site_outcomes.read import BoardServices, SiteOutcomeBoardService, SiteRef, covering_days

UTC = timezone.utc
T = uuid4()
COLD = SiteRef(T, uuid4(), "COLD-LAB-001", "GreenHarvest", "COLDCHAIN", None)
EV = SiteRef(T, uuid4(), "EV-LAB-001", "Lab", "EV_CHARGING", None)


def at(*a: int) -> datetime:
    return datetime(*a, tzinfo=UTC)


class Estate(EstatePortfolioService):
    """The real validation, then a marker instead of the snapshot read."""

    def __init__(self) -> None:  # no database
        pass

    def _read(self, work):
        return "READ"


def test_covering_days_floor_and_ceil_and_midnight_unchanged() -> None:
    assert covering_days(at(2026, 10, 29, 16), at(2026, 10, 29, 17, 5)) == (at(2026, 10, 29), at(2026, 10, 30))
    assert covering_days(at(2026, 10, 6), at(2026, 10, 7)) == (at(2026, 10, 6), at(2026, 10, 7))
    assert covering_days(at(2026, 10, 6, 8), at(2026, 10, 7)) == (at(2026, 10, 6), at(2026, 10, 7))


@pytest.mark.parametrize("lo,hi", [(at(2026, 10, 6, 8), at(2026, 10, 7)), (at(2026, 10, 6), at(2026, 10, 7, 9)),
                                   (at(2026, 10, 1), at(2026, 11, 2)), (at(2026, 10, 7), at(2026, 10, 6))])
def test_estate_methods_refuse_misaligned_or_overlong_windows_with_the_estate_code(lo, hi) -> None:
    est = Estate()
    with pytest.raises(EstateRefusal) as e1:
        est.site_readiness(T, "EV-LAB-001", lo, hi)
    with pytest.raises(EstateRefusal) as e2:
        est.site_work_rows(T, "KOBO-001", lo, hi, lo, hi)
    assert e1.value.args == e2.value.args == ("INVALID_WINDOW",)


def test_estate_methods_accept_whole_days_and_do_not_widen() -> None:
    assert Estate().site_readiness(T, "EV-LAB-001", at(2026, 10, 6), at(2026, 10, 7)) == "READ"


@pytest.mark.parametrize("site,ports", [(COLD, "cold_ports"), (EV, "ev_ports")])
def test_cold_and_ev_board_widens_readiness_to_covering_days(site, ports) -> None:
    seen = []

    class Rec(Estate):
        def site_readiness(self, *a):
            seen.append(a)
            return "FULL"

    p = getattr(SiteOutcomeBoardService(BoardServices(estate=Rec())), ports)(site)
    assert p.readiness(at(2026, 10, 29, 16), at(2026, 10, 29, 17, 5)) == "FULL"
    assert seen[0][2:4] == (at(2026, 10, 29), at(2026, 10, 30))


@pytest.mark.parametrize("site", [COLD, EV])
def test_over_31_covering_days_is_invalid_window_assure_unknown_board_partial(site) -> None:
    svc = SiteOutcomeBoardService(BoardServices(estate=Estate()))
    lo, hi = at(2026, 10, 1, 5), at(2026, 11, 1, 5)  # 31 days unaligned: the covering days are 32
    ports = svc.cold_ports(site) if site is COLD else svc.ev_ports(site)
    with pytest.raises(EstateRefusal) as e:
        ports.readiness(lo, hi)
    assert e.value.args == ("INVALID_WINDOW",)
    comp, window = svc.compose(site, lo=lo, hi=hi)
    assert "evidence_readiness" in comp.failed and comp.read_state == "PARTIAL"
    assert window["from"] == lo and window["to"] == hi  # the board window is not widened
    assert comp.facts.readiness is None
    body = svc.board(site, lo=lo, hi=hi)
    assert body["window"]["from"] == "2026-10-01T05:00:00Z"
    assm = [r for r in body["rows"] if r["category"].upper().startswith("ASSURE")] or body["rows"][3:4]
    assert assm[0]["state"] == "UNKNOWN"
