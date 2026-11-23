"""IA-P P4a (`spec-period.md` P.8; D-IAP.9, D-IAP.20, D-IAP.26): E1, the Sites rows for the same months as the
Overview, pure.

E2's resolver and header state the months; each compared Site's figures are its own 5b root rows in 5c's month views,
summed exactly over the served months in which it is compared. The compared Sites' effects sum exactly to the
portfolio's (the sum check), and `total` is the Overview's tile 2 for the same range, string for string. A Site of a
type with no monthly snapshot says so by its type (MD-IAP-12). Every word is an SC-1 statement.
"""
from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any

from assetops_backend.i18n import Count, KOfN, Name, State, message, render

from assetops_backend.deep_dive import period as P
from assetops_backend.deep_dive import tables as T
from assetops_backend.deep_dive import view as V
from assetops_backend.deep_dive import words as W

SCHEMA = T.SITES_SCHEMA
SUM_CHECK = "SITES_SUM"


@dataclass(frozen=True)
class SiteRef:
    code: str
    name: str
    domain: str                             # the registry's Site type: MINIGRID, COLDCHAIN, EV_CHARGING


def _text(piece: str) -> str:
    return render(message("portfolio_sites.text", piece=State(piece)))


def _group(domain: str) -> str:
    return render(message("portfolio_sites.group", domain=State(domain)))


def _not_compared(ref: SiteRef) -> dict:
    missing = W.text("NOT_AVAILABLE")
    contribution = (missing if ref.domain == T.MINIGRID_DOMAIN
                    else render(message("portfolio_sites.no_figures", domain=State(ref.domain))))
    return {"site_code": ref.code, "site": ref.name, "group": _group(ref.domain), "contribution": contribution,
            "gap": missing, "gap_word": None, "driver": missing, "driver_heading": None, "below": False,
            "months_text": None}


class _Site:
    """One Site's figures over the served months in which it is compared (P.8 "The months")."""

    def __init__(self, z: P.Sums, code: str) -> None:
        self.z = z
        self.months = [v for v in z.vs if code in v.sb and code not in dict(v.R.out)]
        self.roots = [v.sb[code].roots[T.ROOT] for v in self.months]
        actual_cur = P.one_currency(v.own_cur(code, r) for v, r in zip(self.months, self.roots))
        target_cur = P.one_currency(v.own_cur(code, r, T.TARGET_SIDE) for v, r in zip(self.months, self.roots))
        # One figure: a Site's money is shown in the months' own currency, the one its row adds to; a Site in
        # another, or months with none (World X), read "Not available yet" (I7: degrade, never a mixed sum).
        actual_cur = actual_cur if actual_cur == z.cur else None
        target_cur = target_cur if target_cur == z.cur else None
        self.cur = actual_cur
        self.actual = P.exact_sum([r.actual for r in self.roots]) if actual_cur is not None else None
        self.target = P.exact_sum([r.target for r in self.roots]) if target_cur is not None else None
        self.target_cur = target_cur
        self.effect = P.exact_sum([r.effect for r in self.roots]) if actual_cur is not None else None
        steps = []
        for step in T.STEPS[T.MINI_GRID]:
            own = [(v, V._find(r, step)) for v, r in zip(self.months, self.roots)]
            cur = P.one_currency(v.own_cur(code, row) if row is not None else None for v, row in own)
            effects = [row.effect if row is not None else None for _, row in own]
            steps.append((step, P.exact_sum(effects) if cur is not None else None, cur))
        self.steps = steps

    def row(self, ref: SiteRef) -> dict:
        z = self.z
        words, heading = P.driver(self.steps, z.latest.home)
        served = len(z.vs)
        return {"site_code": ref.code, "site": ref.name, "group": _group(ref.domain),
                "contribution": P.contribution(self.actual, self.target, self.cur, self.target_cur),
                "gap": W.amount(self.effect, self.cur, "SIGNED"),
                "gap_word": z.word(self.effect, self.cur, self.roots),
                "driver": words, "driver_heading": heading,
                "below": self.effect is not None and W.cents(self.effect) < 0,
                "months_text": (render(message("portfolio_sites.months", months=KOfN(len(self.months), served,
                                                                                     T.MONTH_NOUN)))
                                if len(self.months) < served else None)}


def _check_sum(z: P.Sums, compared: Sequence[_Site]) -> None:
    """P.8 and I7: when the portfolio's effect and every compared effect are present, they agree exactly."""
    total = P.exact_sum([R.effect for R in z.Rs])
    effects = [s.effect for s in compared]
    if total is None or any(e is None for e in effects):
        return
    if P.exact_sum(effects) != total:
        raise AssertionError(SUM_CHECK)


def sites_view(*, period: P.Period, read: Sequence[P.MonthServed], suggest: str | None, sites: Sequence[SiteRef],
               now: datetime) -> dict:
    """E1's JSON (P.8), keys in order."""
    out: dict[str, Any] = {"schema": SCHEMA, **P.header(period, read, suggest, now=now)}
    columns = [W.text("SITE"), _text(T.GROUP_PIECE), W.text("CONTRIBUTION"), W.text("GAP_TO_TARGET"),
               P.text(T.DRIVER_PIECE), _text(T.WAITING_PIECE)]
    if out["mode"] == T.MODE_NONE:
        out.update(as_of_text=None, headline=None, columns=columns, rows=[_not_compared(s) for s in sites],
                   total=None, without_target={"count": 0, "text": None})
        return out
    z = P.Sums(read, {s.code: s.name for s in sites})
    figures = {s.code: _Site(z, s.code) for s in sites}
    compared = [s for s in sites if figures[s.code].months]
    rest = [s for s in sites if not figures[s.code].months]
    _check_sum(z, [figures[s.code] for s in compared])
    if all(figures[s.code].effect is None for s in compared):
        head = render(message("portfolio_sites.no_comparisons",
                              period=Name(out["period_words"], "portfolio_period.span")))
        out.update(as_of_text=W.as_of(max(r.served.as_of for r in z.M)),
                   headline={"text": head, "evidence": []}, columns=columns,
                   rows=[_not_compared(s) for s in sites],
                   total={"gap": W.text("NOT_AVAILABLE"), "word": None},
                   without_target={"count": 0, "text": None})
        return out
    asked = list(z.latest.snap.asked)
    rank = {c: i for i, c in enumerate(asked)}

    def order(s: SiteRef) -> tuple:
        e = figures[s.code].effect
        return (e is None, e if e is not None else Decimal(0), rank.get(s.code, len(asked)))

    compared.sort(key=order)
    rows = [figures[s.code].row(s) for s in compared] + [_not_compared(s) for s in rest]
    gap, word = z.gap()
    below = sum(1 for r in rows if r["below"])
    head = render(message("portfolio_sites.headline", sites=KOfN(below, len(compared), T.SITE_NOUN),
                          period=Name(out["period_words"], "portfolio_period.span"),
                          below=State(T.BELOW[below > 0])))
    count = len(rest)
    out.update(as_of_text=W.as_of(max(r.served.as_of for r in z.M)),
               headline={"text": head, "evidence": [w for w in (word,) if w is not None]},
               columns=columns, rows=rows, total={"gap": gap, "word": word},
               without_target={"count": count, "text": (render(message(
                   "portfolio_sites.without_target", count=Count(count, T.SITE_NOUN),
                   number=State(T.NUMBER[count == 1]))) if count else None)})
    return out
