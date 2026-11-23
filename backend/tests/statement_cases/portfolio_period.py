"""IA-P P3a (`spec-period.md` P.6): the cases of `portfolio_period.*`, one or more per variant. The English is P.6's
table and P.7's literals, written by hand (W2), never computed."""
from __future__ import annotations

from decimal import Decimal as D

from assetops_backend.i18n import Absent, Count, Evidence, Items, KOfN, Money, Month, Name, State, Word

from statement_cases import Case

EV = ["Emulated"]
SEP, OCT, NOV = Month(2026, 9), Month(2026, 10), Month(2026, 11)


def usd(value: str) -> Money:
    return Money(D(value), "USD", Evidence("DERIVED", "source-emulated"))


def n(text: str) -> Name:
    return Name(text, "portfolio_period.month")


def months(*names: str) -> Items:
    return Items(tuple(n(x) for x in names))


PERIOD = Name("September and October", "portfolio_period.span")
HEAD = {"period": PERIOD, "sites": KOfN(3, 3, "site"), "fewer": State("NO")}
OPT = Word("headline_subject", "OPTIMIZE_COST")

CASES = [
    Case("portfolio_period.month", "one_year", {"month": SEP, "years": State("ONE")}, "September"),
    Case("portfolio_period.month", "years", {"month": SEP, "years": State("SEVERAL")}, "September 2026"),
    Case("portfolio_period.span", "one", {"first": n("October"), "last": Absent("ONE"), "count": State("ONE")},
         "October"),
    Case("portfolio_period.span", "two", {"first": n("September"), "last": n("October"), "count": State("TWO")},
         "September and October"),
    Case("portfolio_period.span", "more",
         {"first": n("November 2025"), "last": n("February 2026"), "count": State("MORE")},
         "November 2025 to February 2026"),
    Case("portfolio_period.headline", "not_available", HEAD,
         "Contribution across September and October is not available yet.", []),
    Case("portfolio_period.headline", "on_target", {**HEAD, "gap": usd("0.00")},
         "Contribution is on target across September and October.", EV),
    Case("portfolio_period.headline", "gap_only", {**HEAD, "gap": usd("-1704.00")},
         "Contribution is $1,704.00 below target across September and October.", EV),
    Case("portfolio_period.headline", "more_than_gap",
         {**HEAD, "gap": usd("-1704.00"), "big": usd("-2000.00"), "subject": OPT},
         "Contribution is $1,704.00 below target across September and October; cost and efficiency explain "
         "$2,000.00, more than the whole gap.", EV),
    Case("portfolio_period.headline", "share_of_gap",
         {**HEAD, "gap": usd("-1704.00"), "big": usd("-1510.00"), "subject": OPT, "sites": KOfN(3, 4, "site"),
          "fewer": State("YES")},
         "Contribution is $1,704.00 below target across September and October; cost and efficiency explain "
         "$1,510.00 of it. Compared for 3 of 4 Sites.", EV),
    Case("portfolio_period.compared", "some", {"sites": KOfN(3, 4, "site"), "fewer": State("YES")},
         " Compared for 3 of 4 Sites.", []),
    Case("portfolio_period.compared", "all", {"sites": KOfN(3, 3, "site"), "fewer": State("NO")}, "", []),
    Case("portfolio_period.missing", "one", {"months": months("September"), "number": State("ONE")},
         "No figures are served for September, so it is not in these figures."),
    Case("portfolio_period.missing", "several", {"months": months("August", "September"), "number": State("SEVERAL")},
         "No figures are served for August and September, so they are not in these figures."),
    Case("portfolio_period.partial", "one", {"months": months("November"), "number": State("ONE")},
         "November is only partly in this range, so it is not counted: the figures are kept by whole month."),
    Case("portfolio_period.partial", "several", {"months": months("October", "November"), "number": State("SEVERAL")},
         "October and November are only partly in this range, so they are not counted: the figures are kept by "
         "whole month."),
    Case("portfolio_period.open", "one", {"months": months("November"), "number": State("ONE")},
         "November has not closed yet, so it has no figures."),
    Case("portfolio_period.open", "several",
         {"months": months("December 2026", "January 2027"), "number": State("SEVERAL")},
         "December 2026 and January 2027 have not closed yet, so they have no figures."),
    Case("portfolio_period.none", "none", {},
         "This range holds no whole month with figures. Contribution against target is kept by whole calendar month."),
    Case("portfolio_period.suggest", "suggest", {"month": OCT}, "Show October 2026"),
    Case("portfolio_period.currencies", "currencies", {},
         "The months are in different currencies, so they are not added."),
    Case("portfolio_period.fresh", "fresh", {"months": months("September")},
         "Some months' figures are out of date: September. Open a month for what changed."),
    Case("portfolio_period.out_only", "only",
         {"line": Name("Thika: not a mini-grid Site, not included.", "portfolio_period.out_line"),
          "months": months("September")},
         "Thika: not a mini-grid Site, not included. Only in September."),
    Case("portfolio_period.grow_line", "grow", {"count": Count(2, "month")}, "Revenue against target, over 2 months"),
    Case("portfolio_period.assure_line", "assure", {"months": KOfN(0, 2, "month")}, "0 of 2 months reconciled"),
    Case("portfolio_period.assure_entry", "entry",
         {"month": OCT, "standing": Name("Reconciled: revenue and fuel bought for October 2026 (the organisation) match the management accounts "
                                         "within 1%.", "reconciliation.standing")},
         "October 2026: Reconciled: revenue and fuel bought for October 2026 (the organisation) match the management accounts within 1%."),
    Case("portfolio_period.text", "months_title", {"piece": State("MONTHS_TITLE")}, "Month by month"),
    Case("portfolio_period.text", "month", {"piece": State("MONTH")}, "Month"),
    Case("portfolio_period.text", "driver", {"piece": State("DRIVER")}, "Largest driver against target"),
    Case("portfolio_period.refused", "bad_range", {"code": State("BAD_RANGE")},
         "Write the range as two days, YYYY-MM-DD, the first not after the last."),
    Case("portfolio_period.refused", "too_long", {"code": State("RANGE_TOO_LONG"), "cap": Count(24, "month")},
         "The month figures cover at most 24 months. Narrow the date range."),
]
