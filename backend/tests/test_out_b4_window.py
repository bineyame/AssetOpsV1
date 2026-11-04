"""OUT-B addendum 7: the board's estate reads use the covering UTC days; the estate methods keep the estate's own
window rule (no bypass, never widened); more than 31 covering days is INVALID_WINDOW, Assure UNKNOWN, board PARTIAL.
No database: the estate services are real classes whose snapshot read is replaced by a marker."""
from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

import pytest

from assetops_backend.chain.read import SITE_TYPE_OF_DOMAIN
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


class Reader:
    """CH-5a1: a fixture ChainReader whose `day` records the Site-local days it is asked for."""

    def __init__(self, seen: list, readiness: str = "FULL") -> None:
        self.seen, self.readiness = seen, readiness

    def request(self, tenant, k):
        outer = self

        class Request:
            def day(self, sid, site_type, days, readiness_days=None):
                from assetops_backend.chain.read import DayFacts
                outer.seen.append((sid, site_type, tuple(days)))
                return DayFacts(tuple(days), {}, True, outer.readiness, ())

        return Request()


@pytest.mark.parametrize("site,ports", [(COLD, "cold_ports"), (EV, "ev_ports")])
def test_cold_and_ev_readiness_reads_every_local_day_the_window_intersects(site, ports) -> None:
    """CH5a1-R Q8 (E1): `readiness_of` over the Site-local days `[lo, hi)` intersects; the estate readiness (and its
    `covering_days` widening) is not read."""
    seen: list = []

    class Rec(Estate):
        def site_readiness(self, *a):  # pragma: no cover - CH-5a1: never a board read
            raise AssertionError("estate readiness is not a board read")

    p = getattr(SiteOutcomeBoardService(BoardServices(estate=Rec(), chain_reader=Reader(seen))), ports)(site)
    assert p.readiness(at(2026, 10, 29, 16), at(2026, 10, 29, 17, 5)) == "FULL"
    assert seen == [(site.site_id, SITE_TYPE_OF_DOMAIN[site.domain], (at(2026, 10, 29).date(),))]  # measure registry type
    seen.clear()
    p.readiness(at(2026, 10, 6), at(2026, 10, 7))  # midnight end: one day, never the next
    assert seen[0][2] == (at(2026, 10, 6).date(),)


@pytest.mark.parametrize("site", [COLD, EV])
def test_unaligned_31_day_window_pools_its_32_local_days_and_is_not_widened(site) -> None:
    """Formerly the estate refused 32 covering days (INVALID_WINDOW, Assure UNKNOWN). CH5a1-R Q8: readiness is R5 over
    the local days the window intersects, so it reads them all; the board window itself is still not widened."""
    seen: list = []
    svc = SiteOutcomeBoardService(BoardServices(estate=Estate(), chain_reader=Reader(seen)))
    lo, hi = at(2026, 10, 1, 5), at(2026, 11, 1, 5)  # 31 days unaligned: the covering days are 32
    comp, window = svc.compose(site, lo=lo, hi=hi)
    assert "readiness_of" not in comp.failed and "evidence_readiness" not in comp.failed
    assert len(seen[-1][2]) == 32 and comp.facts.readiness == "FULL"
    assert window["from"] == lo and window["to"] == hi  # the board window is not widened
    body = svc.board(site, lo=lo, hi=hi)
    assert body["window"]["from"] == "2026-10-01T05:00:00Z"
