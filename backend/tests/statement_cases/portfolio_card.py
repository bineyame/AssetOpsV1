"""1a (spec section 3.2, D-1A.9): the cases of `portfolio_card.cost_scope`, one per variant. The English is D-1A.9's
table rendered from S1 to S5's facts, written by hand (W2), never computed."""
from __future__ import annotations

from datetime import date

from assetops_backend.i18n import Absent, Count, Day, Name, State

from statement_cases import Case

KEY = "portfolio_card.cost_scope"
OCT30 = Day(date(2026, 10, 30))


def _one(site: str, span: str, day, days) -> dict:
    return {"sites": State("ONE"), "site": Name(site, "site.name"), "span": State(span), "day": day, "days": days}


def _each(span: str, day, days) -> dict:
    return {"sites": State("SEVERAL"), "site": Absent("SEVERAL"), "span": State(span), "day": day, "days": days}


CASES = [
    Case(KEY, "one_day", _one("Kobo", "ONE_DAY", OCT30, Absent("ONE_DAY")),
         "Cost of Kobo's lead issue on 30 October 2026"),
    Case(KEY, "one_range", _one("Kobo", "RANGE", OCT30, Count(30, "day")),
         "Cost of Kobo's lead issue on 30 October 2026, the last of the 30 days shown, not their total"),
    Case(KEY, "one_latest", _one("GreenHarvest", "RANGE", Absent("LATEST_IN_RANGE"), Count(7, "day")),
         "Cost of GreenHarvest's latest issue in the 7 days shown, not their total"),
    Case(KEY, "each_one_day", _each("ONE_DAY", OCT30, Absent("ONE_DAY")),
         "Cost at each Site of its lead issue on 30 October 2026"),
    Case(KEY, "each_range", _each("RANGE", OCT30, Count(30, "day")),
         "Cost at each Site of its lead issue on 30 October 2026, the last of the 30 days shown, not their total"),
    # S5 (days differ), S5b (two PERIOD Sites), S5c (a DAY and a PERIOD Site): one text, D-1A.10.
    Case(KEY, "each_differ", _each("RANGE", Absent("DAYS_DIFFER"), Absent("DAYS_DIFFER")),
         "Cost at each Site of its lead issue in the days it shows, not their total"),
]
