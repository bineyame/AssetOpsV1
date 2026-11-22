"""IA-P P3a and P4a (`spec-period.md` P.8): the cases of `portfolio_sites.*`, one or more per variant. The English is
P.8's statements and test literals, written by hand (W2), never computed."""
from __future__ import annotations

from decimal import Decimal as D

from assetops_backend.i18n import Count, Evidence, KOfN, Money, Name, State

from statement_cases import Case


def usd(value: str) -> Money:
    return Money(D(value), "USD", Evidence("DERIVED", "source-emulated"))


OCTOBER = Name("October", "portfolio_period.span")

CASES = [
    Case("portfolio_sites.headline", "some", {"sites": KOfN(3, 3, "site"), "period": OCTOBER, "below": State("SOME")},
         "3 of 3 Sites are below target in October"),
    Case("portfolio_sites.headline", "none", {"sites": KOfN(0, 3, "site"), "period": OCTOBER, "below": State("NONE")},
         "Every Site is on or above target in October"),
    Case("portfolio_sites.months", "months", {"months": KOfN(1, 2, "month")}, "Compared in 1 of 2 months"),
    Case("portfolio_sites.contribution", "contribution", {"actual": usd("883.00"), "target": usd("1445.00")},
         "$883.00 against a target of $1,445.00", ["Emulated"]),
    Case("portfolio_sites.driver", "driver",
         {"factor": Name("Fuel cost", "deep_dive.label"), "effect": Name("−$600.00", "deep_dive.money")},
         "Fuel cost −$600.00"),
    Case("portfolio_sites.no_driver", "no_driver", {}, "No driver widens the gap"),
    Case("portfolio_sites.no_figures", "coldchain", {"domain": State("COLDCHAIN")},
         "No monthly figures for cold-chain Sites yet"),
    Case("portfolio_sites.no_figures", "ev_charging", {"domain": State("EV_CHARGING")},
         "No monthly figures for EV charging Sites yet"),
    Case("portfolio_sites.without_target", "one", {"count": Count(1, "site"), "number": State("ONE")},
         "1 Site without a target is not in this figure"),
    Case("portfolio_sites.without_target", "several", {"count": Count(2, "site"), "number": State("SEVERAL")},
         "2 Sites without a target are not in this figure"),
    Case("portfolio_sites.group", "minigrid", {"domain": State("MINIGRID")}, "Mini-grid"),
    Case("portfolio_sites.group", "coldchain", {"domain": State("COLDCHAIN")}, "Cold-chain"),
    Case("portfolio_sites.group", "ev_charging", {"domain": State("EV_CHARGING")}, "EV charging"),
    Case("portfolio_sites.text", "group", {"piece": State("GROUP")}, "Group"),
    Case("portfolio_sites.text", "waiting", {"piece": State("WAITING")}, "Waiting for a choice"),
]
