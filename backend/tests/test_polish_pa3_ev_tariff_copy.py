"""POLISH PA-3 (Addendum 11, R655): the EV next-evidence tariff gap reads in plain words on the Depot board."""
from __future__ import annotations

from assetops_backend.ev_site_reads import NEXT_EVIDENCE, NO_MONEY


def test_tariff_gap_wording_is_plain() -> None:
    title, detail, area = NEXT_EVIDENCE["TARIFF_GAP"]
    assert (title, detail, area) == ("Publish a charging tariff", "Needed before charging income can be estimated.",
                                     "financials")
    assert not any("scenario" in text.lower() or "gross" in text.lower() for text in (title, detail))


def test_no_money_limitation_is_plain() -> None:
    """PA-3 review residual (R655): the EV money limitation without a tariff estimate."""
    assert NO_MONEY == "No charging income estimate yet."
