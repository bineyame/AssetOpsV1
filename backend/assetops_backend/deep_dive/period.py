"""IA-P P3a (`spec-period.md` P.1 to P.5; D-IAP.16, D-IAP.17, D-IAP.25): the Overview on the date range, pure.

Contribution against target is kept per whole calendar month, so a range counts the whole, closed months inside it and
names every month it cannot count; nothing is cut by day. `resolve` finds those months, `header` states them (E2 and
E1 share it), and `period_view` is E2's body: one month's figures are 5c's own `_View`, and a period's are exact sums of
those, never re-formatted (one figure). Every word is an SC-1 statement.
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from decimal import Context, Decimal, localcontext
from typing import Any

from assetops_backend.i18n import Absent, Count, Items, KOfN, Name, State, Word, message, render
from assetops_backend.i18n import served as served_words

from assetops_backend.deep_dive import tables as T
from assetops_backend.deep_dive import view as V
from assetops_backend.deep_dive import words as W

SCHEMA = T.PERIOD_SCHEMA
MAX_MONTHS = 24
BAD_RANGE, RANGE_TOO_LONG = "BAD_RANGE", "RANGE_TOO_LONG"
PARTIAL, OPEN = "PARTIAL", "OPEN"
SERVED = "SERVED"


class RangeRefused(ValueError):
    """`ValueError("BAD_RANGE")` or `ValueError("RANGE_TOO_LONG")` (P.2), with its code for the route."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


@dataclass(frozen=True)
class Period:
    first: date
    last: date
    months: tuple[str, ...]                 # whole months, "YYYY-MM", ascending
    edges: tuple[tuple[str, str], ...]      # (month, "PARTIAL" | "OPEN"), ascending


@dataclass(frozen=True)
class MonthServed:
    month: str
    served: Any                             # 3B7a's `Served`, as `month()` reads it
    standing: Any                           # 3A7's standing; read only when SERVED (5c section 4.1)


# --- P.2: the resolver ---------------------------------------------------------------------------------------------

def _next(month: str) -> str:
    year, mon = (int(p) for p in month.split("-"))
    return T.month_code(year, mon + 1)


def _first(month: str) -> date:
    year, mon = (int(p) for p in month.split("-"))
    return date(year, mon, 1)


def month_days(month: str) -> tuple[date, date]:
    """The first and last day of a `YYYY-MM` month."""
    return _first(month), _first(_next(month)) - timedelta(days=1)


def closed(month: str, now: datetime) -> bool:
    """P.1: the first instant (UTC) of the next month is at or before `now`."""
    after = _first(_next(month))
    return datetime(after.year, after.month, 1, tzinfo=timezone.utc) <= now


def resolve(first: date, last: date, now: datetime) -> Period:
    if first > last:
        raise RangeRefused(BAD_RANGE)
    months: list[str] = []
    edges: list[tuple[str, str]] = []
    month, end = T.month_code(first.year, first.month), T.month_code(last.year, last.month)
    while month <= end:
        a, b = month_days(month)
        inside = a >= first and b <= last
        if inside and closed(month, now):
            months.append(month)
        else:
            edges.append((month, OPEN if inside else PARTIAL))
        month = _next(month)
    if len(months) > MAX_MONTHS:
        raise RangeRefused(RANGE_TOO_LONG)
    return Period(first, last, tuple(months), tuple(edges))


# --- words ---------------------------------------------------------------------------------------------------------

def _names(months: Sequence[str]) -> list[Name]:
    """D-IAP.28: month names alone when every month named is in one year, else with the year."""
    years = State(T.NUMBER[len({m[:4] for m in months}) == 1])
    return [Name(render(message("portfolio_period.month", month=W.month_of(m), years=years)),
                 "portfolio_period.month") for m in months]


def span(months: Sequence[str]) -> str:
    names = _names(months)
    count = T.SPAN_COUNT[min(len(names), 3) - 1]
    return render(message("portfolio_period.span", first=names[0],
                          last=names[-1] if len(names) > 1 else Absent(T.SPAN_COUNT[0]), count=State(count)))


def _note(key: str, months: Sequence[str]) -> str:
    return render(message(key, months=Items(tuple(_names(months))),
                          number=State(T.NUMBER[len(months) == 1])))


def _bounds(month: str) -> dict:
    a, b = month_days(month)
    return {"from": a.isoformat(), "to": b.isoformat()}


def _days(month: str) -> dict:
    return {"month_words": W.render_month(month), **_bounds(month)}


def text(piece: str) -> str:
    return render(message("portfolio_period.text", piece=State(piece)))


def refused_text(code: str) -> str:
    """E2's and E1's own 422 text (`deep_dive_api.py`)."""
    facts: dict[str, Any] = {"code": State(code)}
    if code == RANGE_TOO_LONG:
        facts["cap"] = Count(MAX_MONTHS, "month")
    return render(message("portfolio_period.refused", **facts))


# --- P.4: the header (E2 and E1) -----------------------------------------------------------------------------------

def mode_of(read: Sequence[MonthServed]) -> str:
    n = sum(1 for r in read if r.served.state == SERVED)
    return T.PERIOD_MODES[min(n, 2)]


def header(period: Period, read: Sequence[MonthServed], suggest: str | None, *, now: datetime) -> dict:
    served = [r.month for r in read if r.served.state == SERVED]
    mode = mode_of(read)
    notes = []
    missing = [r.month for r in read if r.served.state != SERVED]
    for key, months in (("portfolio_period.missing", missing),
                        ("portfolio_period.partial", [m for m, k in period.edges if k == PARTIAL]),
                        ("portfolio_period.open", [m for m, k in period.edges if k == OPEN])):
        if months:
            notes.append(_note(key, months))
    if mode == T.MODE_NONE:
        notes.append(render(message("portfolio_period.none")))
    shown = None
    if served:
        a, b = month_days(served[0])[0], month_days(served[-1])[1]
        if (a, b) != (period.first, period.last):
            shown = {"from": a.isoformat(), "to": b.isoformat()}
    nav = None
    if mode == T.MODE_MONTH:
        codes = V._nav(served[0], now)
        nav = {k: (_days(codes[k]) if codes[k] is not None else None) for k in T.NAV_KEYS}
    hint = None
    if mode == T.MODE_NONE and suggest is not None:
        hint = {"text": render(message("portfolio_period.suggest", month=W.month_of(suggest))), **_bounds(suggest)}
    return {"from": period.first.isoformat(), "to": period.last.isoformat(), "mode": mode,
            "months": [{"month": r.month, **_days(r.month), "state": r.served.state} for r in read],
            "served": served, "period_words": span(served) if served else None, "notes": notes, "shown": shown,
            "nav": nav, "suggest": hint}


# --- P.5: sums and the shared driver rule --------------------------------------------------------------------------

def exact_sum(values: Sequence[Decimal | None]) -> Decimal | None:
    """P.5: exact over every term; None when any term is None."""
    if any(v is None for v in values):
        return None
    with localcontext(Context(prec=34)):
        total = Decimal(0)
        for v in values:
            total += v
        return total


def one_currency(currencies) -> str | None:
    held = set(currencies)
    return next(iter(held)) if len(held) == 1 and None not in held else None


def driver(effects: Sequence[tuple[str, Decimal | None, str | None]], home) -> tuple[str, str | None]:
    """P.8's rule: among `(step, effect, currency)` in STEPS order, the most negative effect below 0 (ties to the
    earlier step) names the driver and its heading; with none, `portfolio_sites.no_driver` and no heading."""
    best = None
    for step, effect, cur in effects:
        if effect is not None and effect < 0 and (best is None or effect < best[1]):
            best = (step, effect, cur)
    if best is None:
        return render(message("portfolio_sites.no_driver")), None
    step, effect, cur = best
    words = render(message("portfolio_sites.driver", factor=Name(W.factor_label(step), "deep_dive.label"),
                           effect=Name(W.amount(effect, cur, "SIGNED"), "deep_dive.money")))
    return words, W.heading_label(home(step))


def contribution(actual: Decimal | None, target: Decimal | None, actual_cur: str | None,
                 target_cur: str | None) -> str:
    if actual is None or target is None or actual_cur is None or target_cur is None:
        return W.text("NOT_AVAILABLE")
    return W.figure_text(message("portfolio_sites.contribution", actual=W.money(actual, actual_cur),
                                 target=W.money(target, target_cur)))


def _step_effects(v) -> list[tuple[str, Decimal | None, str | None]]:
    return [(s, v.rows[s].effect, v.rows[s].currency) for s in v.steps if s in v.rows]


# --- P.5: the period body ------------------------------------------------------------------------------------------

def _month_row(r: MonthServed, v) -> dict:
    row = {"month": r.month, **_days(r.month), "state": r.served.state}
    if v is None:
        sentence = W.no_snapshot(r.month) if r.served.state == "NO_SNAPSHOT" else W.rebuild(r.month)
        row.update(contribution=sentence, gap=None, gap_word=None, driver=None, driver_heading=None, sites=None)
        return row
    R = v.R
    gap = v.tiles()[1]
    words, heading = driver(_step_effects(v), v.home)
    row.update(contribution=contribution(R.actual, R.target, R.currency, R.currency), gap=gap["value"],
               gap_word=gap["word"], driver=words, driver_heading=heading, sites=W.sites(R.k, v.n))
    return row


class Sums:
    """P.5's sums over the served months' 5c views, shared by E2's body and E1's total (one figure)."""

    def __init__(self, read: Sequence[MonthServed], names: Mapping[str, str]) -> None:
        self.views = {r.month: V._View(r.served, r.standing, names, r.month) for r in read
                      if r.served.state == SERVED}
        self.M = [r for r in read if r.month in self.views]
        self.vs = [self.views[r.month] for r in self.M]
        self.latest = self.vs[-1]
        self.Rs = [v.R for v in self.vs]
        self.cur = one_currency(R.currency for R in self.Rs)
        self.differ = len({R.currency for R in self.Rs if R.currency is not None}) > 1
        unreconciled = [r.standing for r in self.M if not r.standing.reconciled]
        self.S = unreconciled[-1] if unreconciled else self.M[-1].standing
        cur = self.cur
        self.A = exact_sum([R.actual for R in self.Rs]) if cur is not None else None
        self.Tg = exact_sum([R.target for R in self.Rs]) if cur is not None else None
        self.E = exact_sum([R.effect for R in self.Rs]) if cur is not None else None
        self.groups = {}
        for category in (T.GROW, T.OPTIMIZE):
            gcur = one_currency(v.group_cur(category) for v in self.vs)
            self.groups[category] = (exact_sum([v.group_sums()[category] for v in self.vs])
                                     if gcur is not None else None, gcur)

    def word(self, value, currency, rows) -> str | None:
        if value is None or currency is None:
            return None
        return W.word(*W.weakest_of(rows), self.S, currency)

    def heading_rows(self, category: str) -> list:
        return [v.rows[s] for v in self.vs for s in v.steps
                if s in v.rows and v.home(s) == category and v.rows[s].effect is not None]

    def gap(self) -> tuple[str, str | None]:
        """The Overview's tile 2 `value` and `word` for these months: 5c's own in mode `month`, ΣE in `period`."""
        if len(self.vs) == 1:
            tile = self.latest.tiles()[1]
            return tile["value"], tile["word"]
        return W.amount(self.E, self.cur, "SIGNED"), self.word(self.E, self.cur, self.Rs)


def _body(read: Sequence[MonthServed], names: Mapping[str, str], actions) -> dict:
    z = Sums(read, names)
    views, M, vs, latest, Rs, cur, differ, S = z.views, z.M, z.vs, z.latest, z.Rs, z.cur, z.differ, z.S
    A, Tg, E, groups = z.A, z.Tg, z.E, z.groups
    word, heading_rows = z.word, z.heading_rows

    as_of = max(r.served.as_of for r in M)
    every = {}
    for v in (latest, *vs[:-1]):
        for code in v.snap.asked:
            every.setdefault(code, v.name(code))
    disagreeing = {c for v in vs for c in v.disagreeing()}
    stale = [r.month for r in M if not r.served.freshness.current]

    # D-IAP.34: the Sites left out, named with why, and the count from the same set (`n - k == len(out)`). A code is out
    # in a month when it is in that month's `R.out`; its line is the latest such month's own sentence.
    out_lines = []
    for code in every:
        months_out = [r.month for r, v in zip(M, vs) if code in dict(v.R.out)]
        if not months_out:
            continue
        line = next(v.out_line(code, dict(v.R.out)[code]) for v in (latest, *vs[:-1]) if code in dict(v.R.out))
        if len(months_out) < len(M):
            line = render(message("portfolio_period.out_only", line=Name(line, "portfolio_period.out_line"),
                                  months=Items(tuple(_names(months_out)))))
        out_lines.append(line)

    # The headline: 5c's choice of heading over the sums (D-5C.15), "across {period}".
    period_words = span([r.month for r in M])
    n = len(every)
    k = n - len(out_lines)
    fewer = k < n
    subject, _ = W.named(E, groups[T.GROW][0], groups[T.OPTIMIZE][0])
    facts: dict[str, Any] = {"period": Name(period_words, "portfolio_period.span"), "sites": KOfN(k, n, "site"),
                             "fewer": State(T.FEWER[fewer])}
    if E is not None:
        facts["gap"] = W.money(E, cur, W.evidence(*W.weakest_of(Rs)))
        if subject is not None:
            total, gcur = groups[subject]
            facts["big"] = W.money(total, gcur, W.evidence(*W.weakest_of(heading_rows(subject))))
            facts["subject"] = Word("headline_subject", subject)
    head = served_words(message("portfolio_period.headline", **facts))
    head["evidence"] = [w for w in (word(E, cur, Rs),) if w is not None]

    lines = []
    if Tg is not None:
        share = A / Tg if A is not None and Tg > 0 else None
        lines.append(W.tile_target(W.money(Tg, cur), share))
    lines.append(W.sites(k, n))
    gap_lines = []
    (grow, grow_cur), (opt, opt_cur) = groups[T.GROW], groups[T.OPTIMIZE]
    if E is not None and grow is not None and opt is not None:
        gap_lines.append(W.tile_split(W.money(grow, grow_cur), W.money(opt, opt_cur)))
    tiles = [{"key": T.TILE_KEYS[0], "label": W.text("CONTRIBUTION"), "value": W.amount(A, cur),
              "word": word(A, cur, Rs), "lines": lines,
              "bar": {"actual": str(A), "target": str(Tg)} if A is not None and Tg is not None else None},
             {"key": T.TILE_KEYS[1], "label": W.text("GAP_TO_TARGET"), "value": z.gap()[0], "word": z.gap()[1],
              "lines": gap_lines, "bar": None},
             *latest.tiles()[2:]]

    rows = [_month_row(r, views.get(r.month)) for r in read]
    reconciled = sum(1 for r in M if r.standing.reconciled)
    cards = []
    for category in (T.GROW, T.OPTIMIZE, T.PROTECT, T.ASSURE):
        card: dict[str, Any] = {"key": T.OUTCOME_KEYS[category], "label": W.heading_label(category)}
        if category in (T.GROW, T.OPTIMIZE):
            total, gcur = groups[category]
            card["value"] = W.amount(total, gcur, "SIGNED")
            card["word"] = word(total, gcur, heading_rows(category))
            card["line"] = (render(message("portfolio_period.grow_line", count=Count(len(M), "month")))
                            if category == T.GROW else W.text("OPTIMIZE_LINE"))
            card["drawer"] = None
        elif category == T.PROTECT:
            card.update({"value": W.text("NOT_AVAILABLE"), "word": None, "line": W.text("PROTECT_LINE"),
                         "drawer": None})
        else:
            card.update({"value": W.text("RECONCILED") if S.reconciled else W.text("NOT_RECONCILED"), "word": None,
                         "line": render(message("portfolio_period.assure_line",
                                                months=KOfN(reconciled, len(M), "month"))),
                         "drawer": {"title": W.text("ASSURE_TITLE"), "lines": [
                             render(message("portfolio_period.assure_entry", month=W.month_of(r.month),
                                            standing=Name(r.standing.text, "reconciliation.standing")))
                             for r in M]}})
        cards.append(card)

    return {"as_of_text": W.as_of(as_of),
            "status_line": W.status_line(as_of, S.reconciled, [c for c in every if c in disagreeing], every),
            "fresh": (render(message("portfolio_period.fresh", months=Items(tuple(_names(stale)))))
                      if stale else None),
            "headline": head,
            "tiles": tiles,
            "notices": [render(message("portfolio_period.currencies"))] if differ else [],
            "out": out_lines,
            "months": {"title": text("MONTHS_TITLE"),
                       "columns": [text("MONTH"), W.text("CONTRIBUTION"), W.text("GAP_TO_TARGET"), text("DRIVER")],
                       "rows": rows},
            "outcomes": cards,
            "actions": V._actions(actions)}


def period_view(*, period: Period, read: Sequence[MonthServed], suggest: str | None, names: Mapping[str, str],
                actions, now: datetime) -> dict:
    """E2's JSON (P.4), keys in order; `body` only in mode `period` (P.5)."""
    out: dict[str, Any] = {"schema": SCHEMA, **header(period, read, suggest, now=now)}
    out["body"] = _body(read, names, actions) if out["mode"] == T.MODE_PERIOD else None
    return out

