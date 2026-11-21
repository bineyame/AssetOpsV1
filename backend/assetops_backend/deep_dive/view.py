"""5c (spec section 3): the deep-dive month, one pure function from the served snapshot to the payload.

Every figure is a row of `portfolio_bridge`'s `rows` or a Site bridge's `roots` (D-5B.12, D-5C.13); the snapshot's
`actual()` and `targets()` are never read. Every word is an SC-1 statement (`deep_dive/words.py`); every money
figure's word carries the organisation's standing, read by the caller at `served.as_of` (D-3A7.9, D-5C.4).
"""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date, datetime, timezone
from collections.abc import Sequence
from decimal import ROUND_HALF_EVEN, Context, Decimal, localcontext
from typing import Any

from assetops_backend.outcomes.catalogue import CATEGORIES
from assetops_backend.structure.attribution.bridge import BridgeRow, lowest
from assetops_backend.structure.attribution.portfolio import portfolio_bridge
from assetops_backend.structure.attribution.site import site_bridge
from assetops_backend.structure.read import SITE_TYPE_TO_STRUCTURE
from assetops_backend.structure.registry import REGISTRIES

from assetops_backend.deep_dive import tables as T
from assetops_backend.deep_dive import words as W
from assetops_backend.deep_dive.words import Standing


@dataclass(frozen=True)
class AgreedAction:
    """The read 3C2 provides (spec section 4.3)."""
    action_id: str
    title: str
    site_code: str | None
    factor_id: str | None
    owner_name: str
    created_by_name: str
    created_at: datetime
    due_on: date
    state_words: str


@dataclass(frozen=True)
class AgreedActions:
    connected: bool
    actions: tuple[AgreedAction, ...]     # newest first, as the port gives them (D-5C.17)


def _nav(month: str, now: datetime) -> dict:
    year, mon = (int(p) for p in month.split("-"))
    after = T.month_code(year, mon + 1)
    y2, m2 = (int(p) for p in T.month_code(year, mon + 2).split("-"))
    end = datetime(y2, m2, 1, tzinfo=timezone.utc)  # the next month's end
    return {"previous": T.month_code(year, mon - 1), "next": after if end <= now else None}


def bridge_bars(effects: Sequence[Decimal | None], gap: Decimal | None) -> tuple[list[dict | None], dict | None]:
    """Spec section 3.2 "Bars" (D-5C.27): each step's bar on the gap's scale and the scale's two marks, as percentages
    of the step track (plain strings, two places, half even). `effects` in JSON order; None for a step with no
    figure in R's currency. No gap (None or 0): no bar and no scale."""
    if gap is None or gap == 0:
        return [None] * len(effects), None
    with localcontext(Context(prec=34, rounding=ROUND_HALF_EVEN)):
        spans: list[tuple[Decimal, Decimal, Decimal] | None] = []
        p = Decimal(0)
        for e in effects:
            if e is None or e == 0:
                spans.append(None)
                continue
            a, b = p, p + e / gap * 100
            p = b
            spans.append((a, b, e))
        ends = [x for span in spans if span is not None for x in span[:2]]
        lo, hi = min([Decimal(0), *ends]), max([Decimal(100), *ends])

        def at(x: Decimal) -> Decimal:
            return (x - lo) / (hi - lo) * 100

        def text(x: Decimal) -> str:
            return str(x.quantize(Decimal(T.BAR_PLACES)))
        bars: list[dict | None] = []
        for span in spans:
            if span is None:
                bars.append(None)
                continue
            a, b, e = span
            left = at(min(a, b))
            width = max(Decimal(T.BAR_MIN_WIDTH), min(abs(at(b) - at(a)), 100 - left))
            bars.append({"left": text(left), "width": text(width),
                         "tone": T.TONE_LOWERS if e < 0 else T.TONE_RAISES})
        return bars, {"target_at": text(at(Decimal(0))), "actual_at": text(at(Decimal(100)))}


def _walk(row: BridgeRow):
    yield row
    for child in row.rows:
        yield from _walk(child)


def _find(root: BridgeRow, factor_id: str) -> BridgeRow | None:
    for r in _walk(root):
        if r.factor_id == factor_id and r.kind != "RESIDUAL":
            return r
    return None


class _View:
    def __init__(self, served, standing: Standing, names: Mapping[str, str], month: str) -> None:
        snap = served.snapshot
        self.snap, self.standing, self.month = snap, standing, month
        self.key = SITE_TYPE_TO_STRUCTURE["MINIGRID"]
        self.reg = REGISTRIES[self.key]
        self.sb = {c: site_bridge(s.inputs, s.targets) for c, s in snap.sites.items()}
        self.pb = portfolio_bridge(self.sb, snap.asked, snap.sites_excluded, snap.portfolio_lines, snap.month,
                                   self.key, self.reg.version)
        self.n = len(snap.asked)
        self.names = {c: names.get(c, c) for c in snap.asked}
        self.rows = self.pb.rows[T.ROOT]
        self.R = self.rows[T.ROOT]
        self.steps = T.STEPS[T.MINI_GRID]

    # --- small pieces ---------------------------------------------------------------------------------------------

    def name(self, code: str) -> str:
        return self.names.get(code, code)

    def money(self, value: Decimal, row=None, cur: str | None = None):
        """`value` in `cur`, else in its row's own currency (review H3: every figure in the currency of what it sums)."""
        ev = W.evidence(row.evidence, row.origins) if row is not None and row.evidence != "NOT_AVAILABLE" else None
        return W.money(value, cur if cur is not None else row.currency, ev)

    def own_cur(self, code: str, row=None, side: str = "ACTUAL") -> str | None:
        """The currency a Site's own figure prints in: the row's (its root's, D-5B), else, when the Site's actual and
        target differ in currency (5b case (h)), that side's own currency for the row's factor. Never the
        portfolio's (review H3); None prints "Not available yet"."""
        sb = self.sb[code]
        row = row if row is not None else sb.roots[T.ROOT]
        if row.currency is not None:
            return row.currency
        values = sb.actual.values if side == "ACTUAL" else sb.targets.structure.values
        held = values.get(row.factor_id if row.factor_id is not None else row.parent)
        return held.currency if held is not None else None

    def figure_word(self, value: Decimal | None, currency: str | None, ev: str, origins) -> str | None:
        """D-5C.26: a figure slot's word (section 2.4 through `money_word`); None exactly when the figure is absent
        (its value or its currency is None). Every slot's word and the headline's evidence come from here."""
        if value is None or currency is None:
            return None
        return W.word(ev, origins, self.standing, currency)

    def heading_word(self, category: str) -> str | None:
        """A heading's sum's word (its card, the headline when named): the steps' weakest evidence."""
        total, cur = self.group_totals()[category]
        return self.figure_word(total, cur, *self.heading_evidence(category))

    def home(self, factor_id: str) -> str | None:
        home = self.reg.row(factor_id).home
        return home.category if home is not None else None

    def notes(self, code: str) -> dict[str, str | None]:
        values = self.sb[code].actual.values
        return {f: (v.missing.note if v.missing is not None else None) for f, v in values.items()}

    def stops(self, code: str, row: BridgeRow) -> list[str]:
        """The stop sentence of `row` or of its lowest descendants that stop, each once, in tree order."""
        out: list[str] = []
        for r in (row,) if row.split == "NOT_SPLIT" else lowest(row):
            sentence = self.stop(code, r)
            if sentence is not None and sentence not in out:
                out.append(sentence)
        return out

    def stop(self, code: str, r: BridgeRow) -> str | None:
        keys = W.actual_keys(r.unobserved_actual, self.notes(code))
        if r.kind == "RESIDUAL":  # no figure, no line (review H1)
            return (W.residual_text(r.parent, self.money(r.effect, r, self.own_cur(code, r)), keys, r.unobserved_target)
                    if r.effect is not None else None)
        if r.split != "NOT_SPLIT":
            return None
        reason = r.reason or ""
        if reason in ("GAP_NOT_AVAILABLE", "DETAIL_NOT_AVAILABLE"):
            return W.stop_text(reason, keys, r.unobserved_target)
        if reason.startswith(T.CURRENCY_PREFIX):
            return W.currency_text(reason[len(T.CURRENCY_PREFIX):].split(T.CURRENCY_SEP))
        if reason == "RECORD_AND_FACTORS_DIFFER":
            sb = self.sb[code]
            parts = []
            for side, values in (("ACTUAL", sb.actual.values), ("TARGET", sb.targets.structure.values)):
                v = values.get(r.factor_id)
                if v is not None and v.stated and v.computed is not None and v.computed != v.value:
                    c = self.own_cur(code, r, side)
                    parts.append(W.differ_text(side, W.money(v.value, c), W.money(v.computed, c)))
            return W.sentences(parts)
        if reason in T.NO_RULE:
            return W.stop_text("NO_RULE", (), ())
        return None

    # --- section 3.1 ----------------------------------------------------------------------------------------------

    def group_totals(self) -> dict[str, tuple[Decimal | None, str | None]]:
        """Each heading's sum of its steps' effects with its currency; (None, None) when no step has one (never 0 for
        missing, review H1) or when its steps' effects are in more than one currency (review H3)."""
        held: dict[str, list] = {c: [] for c in CATEGORIES}
        for step in self.steps:
            row = self.rows.get(step)
            if row is not None and row.effect is not None:
                held[self.home(step)].append(row)
        out: dict[str, tuple[Decimal | None, str | None]] = {}
        for category, rows in held.items():
            currencies = {r.currency for r in rows}
            if not rows or len(currencies) != 1 or None in currencies:
                out[category] = (None, None)
                continue
            total = Decimal(0)
            for r in rows:
                total += r.effect
            out[category] = (total, rows[0].currency)
        return out

    def group_sums(self) -> dict[str, Decimal | None]:
        return {c: total for c, (total, _) in self.group_totals().items()}

    def group_cur(self, category: str) -> str | None:
        return self.group_totals()[category][1]

    def heading_evidence(self, category: str) -> tuple[str, tuple[str, ...]]:
        """The weakest evidence of the heading's steps its sum adds (those with an effect): the evidence its sum, its
        card and the headline carry. A step with no figure adds nothing to the sum, so it does not set its word
        (D-5C.26: a figure that is present never reads "Not available yet")."""
        return W.weakest_of(self.rows[s] for s in self.steps if s in self.rows and self.home(s) == category
                            and self.rows[s].effect is not None)

    def big(self, category: str | None):
        if category is None:
            return None
        ev, origins = self.heading_evidence(category)
        total, cur = self.group_totals()[category]
        return W.money(total, cur, W.evidence(ev, origins))

    def headline(self) -> tuple[dict, str | None]:
        sums = self.group_sums()
        R = self.R
        subject, _ = W.named(R.effect, sums[T.GROW], sums[T.OPTIMIZE])
        gap = self.money(R.effect, R) if R.effect is not None else None
        big = self.big(subject)
        differ = gap is None and (R.note or "").startswith(T.CURRENCY_PREFIX)  # review L7: say why
        head = W.headline(gap, big, subject, self.month, R.k, self.n, differ)
        # D-5C.20: each figure the headline states carries the payload's own word for it (through `money_word`, with
        # the standing): the gap R's, the named heading its steps' weakest. `served`'s unmarked words are replaced.
        words = []
        if gap is not None:
            words.append(self.figure_word(R.effect, R.currency, R.evidence, R.origins))
            if big is not None:
                words.append(self.heading_word(subject))
        head["evidence"] = list(dict.fromkeys(w for w in words if w is not None))
        title = W.bridge_title(gap, big, subject) if gap is not None else None
        return head, title

    def cost_ratio(self) -> Decimal | None:
        C = self.rows.get(T.COST)
        if C is None or C.actual is None or C.actual == 0:
            return None
        carried = Decimal(0)
        for code, sb in self.sb.items():
            if code in dict(C.out):
                continue
            for leaf in sb.carried:
                value = sb.actual.values[leaf].value
                carried += value if value is not None else Decimal(0)
        return (C.actual - carried) / C.actual

    def rest(self) -> Decimal:
        total = Decimal(0)
        out = dict(self.R.out)
        for code, sb in self.sb.items():
            if code in out:
                continue
            for r in lowest(sb.roots[T.ROOT]):
                if (r.split == "NOT_SPLIT" or r.kind == "RESIDUAL") and r.effect is not None:
                    total += r.effect
        return total

    def tiles(self) -> list[dict]:
        R, sums = self.R, self.group_sums()
        cur, ratio = R.currency, self.cost_ratio()
        lines = []
        if R.target is not None:
            share = R.actual / R.target if R.actual is not None and R.target > 0 else None
            lines.append(W.tile_target(W.money(R.target, cur), share))
        lines.append(W.sites(R.k, self.n))
        if ratio is not None:
            lines.append(W.cost_received(ratio))
        contribution = {"key": T.TILE_KEYS[0], "label": W.text("CONTRIBUTION"), "value": W.amount(R.actual, cur),
                        "word": self.figure_word(R.actual, cur, R.evidence, R.origins), "lines": lines,
                        "bar": ({"actual": str(R.actual), "target": str(R.target)}
                                if R.actual is not None and R.target is not None else None)}
        gap_lines = []
        if R.effect is not None and sums[T.GROW] is not None and sums[T.OPTIMIZE] is not None:
            gap_lines.append(W.tile_split(W.money(sums[T.GROW], self.group_cur(T.GROW)),
                                          W.money(sums[T.OPTIMIZE], self.group_cur(T.OPTIMIZE))))
        if R.effect is not None and R.effect != 0:  # KD2 ruling: a gap of 0 has no rest line (nothing to offset)
            gap_lines.append(W.tile_rest(W.money(self.rest(), cur), W.money(R.effect, cur)))
        gap = {"key": T.TILE_KEYS[1], "label": W.text("GAP_TO_TARGET"), "value": W.amount(R.effect, cur, "SIGNED"),
               "word": self.figure_word(R.effect, cur, R.evidence, R.origins), "lines": gap_lines, "bar": None}
        spend = {"key": T.TILE_KEYS[2], "label": W.text("PLAN_SPEND"), "value": W.text("NOT_AVAILABLE"), "word": None,
                 "lines": [W.text("PLAN_SPEND_LINE")], "bar": None}
        value = {"key": T.TILE_KEYS[3], "label": W.plan_value_label(), "value": W.text("NOT_AVAILABLE"),
                 "word": None, "lines": [W.text("PLAN_VALUE_LINE")], "bar": None}
        return [contribution, gap, spend, value]

    def disagreeing(self) -> list[str]:
        return list(dict.fromkeys(code for code, _ in self.pb.disagreements))

    def notices(self) -> list[str]:
        out = []
        for code, check in self.pb.disagreements:
            computed = W.money(check.computed, check.currency) if check.computed is not None else None
            out.append(W.disagreement(self.name(code), check.factor_id, W.money(check.stated, check.currency),
                                      computed))
        return out

    # --- section 3.2 ----------------------------------------------------------------------------------------------

    def shares(self) -> dict[str, str]:
        """Section 3.2: each step's share of what widens the gap; none when R has no gap (None or 0, D-5C.28)."""
        gap = self.R.effect
        if gap is None or gap == 0:
            return {}
        widening = [self.rows[s].effect for s in self.steps if s in self.rows and self.rows[s].effect is not None
                    and self.rows[s].effect != 0 and (self.rows[s].effect < 0) == (gap < 0)]
        total = sum((abs(e) for e in widening), Decimal(0))
        out = {}
        for s in self.steps:
            row = self.rows.get(s)
            if row is None or row.effect is None:
                continue
            e = row.effect
            if e == 0 or total == 0:
                value = Decimal(0) if e == 0 else Decimal(-1)
            elif (e < 0) == (gap < 0):
                value = abs(e) / total
            else:
                value = Decimal(-1)
            out[s] = W.share(value, W.evidence(row.evidence, row.origins) if row.evidence != "NOT_AVAILABLE"
                             else W.evidence("DERIVED", ()))
        return out

    def included(self, row) -> list[str]:
        out = dict(row.out)
        return [c for c in self.snap.asked if c in self.sb and c not in out]

    def out_line(self, code: str, reasons: tuple[str, ...]) -> str:
        if reasons == (T.OUT_NOT_SPLIT,):
            return W.out_text(self.name(code), "NOT_SPLIT")
        if code in self.sb and (self.sb[code].roots[T.ROOT].reason or "").startswith(T.CURRENCY_PREFIX):
            return self.out_currency(code)
        actual = [r[len(T.ACTUAL_PREFIX):] for r in reasons if r.startswith(T.ACTUAL_PREFIX)]
        target = [r[len(T.TARGET_PREFIX):] for r in reasons if r.startswith(T.TARGET_PREFIX)]
        if code not in self.sb or not (actual or target):
            return W.out_text(self.name(code), "NOT_MINI_GRID")
        own = self.sb[code].roots[T.ROOT].target
        keys = W.actual_keys(actual, self.notes(code))
        return W.out_text(self.name(code), "NEEDS", keys, target,
                          W.money(own, self.own_cur(code, side="TARGET")) if own is not None else None)

    def out_currency(self, code: str) -> str:
        """Review M3: a mini-grid Site out because its own actual and target are in different currencies; both
        sides' currencies are named (the held pair from the reason)."""
        reason = self.sb[code].roots[T.ROOT].reason
        held = reason[len(T.CURRENCY_PREFIX):].split(T.CURRENCY_SEP)
        return W.out_text(self.name(code), "CURRENCY_MISMATCH", currencies=held)

    def descendants(self, step: str) -> dict[str, str]:
        """Each registry descendant of `step` with its registry parent (the first reached, breadth first)."""
        out: dict[str, str] = {}
        todo = [step]
        while todo:
            f = todo.pop(0)
            for child in self.reg.row(f).children:
                if child not in out and child != step:
                    out[child] = f
                    todo.append(child)
        return out

    def drivers(self, step: str) -> list[dict]:
        """Spec section 3.2, D-5C.21: the step's direct parts, each with its own parts in `children`. A driver's parent
        is its nearest registry ancestor that is the step or has a driver row; `residual:<x>` is the last child of
        `x`; within a level, `pb.rows` order."""
        below = self.descendants(step)
        keys = []
        for key in self.rows:
            x = key[len(T.RESIDUAL_PREFIX):] if key.startswith(T.RESIDUAL_PREFIX) else None
            if key in below or (x is not None and (x == step or x in below)):
                keys.append(key)
        held = set(keys)

        def parent(key: str) -> str:
            up = key[len(T.RESIDUAL_PREFIX):] if key.startswith(T.RESIDUAL_PREFIX) else below[key]
            while up != step and up not in held:
                up = below[up]
            return up
        kids: dict[str, list[str]] = {}
        for key in keys:  # `pb.rows` order; then each residual last among its parent's children
            kids.setdefault(parent(key), []).append(key)
        for level in kids.values():
            level.sort(key=lambda k: k.startswith(T.RESIDUAL_PREFIX))

        def node(key: str) -> dict:
            r = self.rows[key]
            x = key[len(T.RESIDUAL_PREFIX):] if key.startswith(T.RESIDUAL_PREFIX) else None
            return {"key": key, "label": W.factor_label(key if x is None else x),
                    "value": W.amount(r.effect, r.currency, "SIGNED"), "sites": W.sites(r.k, self.n),
                    "detail": self.driver_detail(key, r),
                    "word": self.figure_word(r.effect, r.currency, r.evidence, r.origins),
                    "children": [node(k) for k in kids.get(key, [])]}
        return [node(k) for k in kids.get(step, [])]

    def driver_detail(self, key: str, row) -> str | None:
        if row.actual is None or row.target is None or key.startswith(T.RESIDUAL_PREFIX):
            return None
        unit = self.reg.row(key).unit
        others = [name for name, power in unit.exponents if name != "MONEY"]
        symbol = others[0] if others else None
        if unit.is_money:
            kind = "MONEY"
        elif ("MONEY", 1) in unit.exponents:
            kind = "PRICE"
        else:
            kind = "QUANTITY"
        return W.detail(kind, row.actual, row.target, row.currency, symbol)

    def drawer(self, step: str, row) -> dict:
        lines = []
        if row.actual is not None and row.target is not None and row.gap is not None:
            lines.append(W.drawer_values(W.money(row.actual, row.currency), W.money(row.target, row.currency),
                                         W.money(row.gap, row.currency)))
        if row.effect is not None:
            lines.append(W.drawer_effect(W.money(row.effect, row.currency)))
        lines.append(W.sites(row.k, self.n))
        site_rows = []
        for code in self.included(row):
            own = _find(self.sb[code].roots[T.ROOT], step)
            stops = self.stops(code, own) if own is not None else []
            site_rows.append({"site": self.name(code),
                              "value": W.amount(own.effect if own is not None else None, self.own_cur(code, own),
                                                T.CELL_FORM[own is not None and own.carried]),
                              "text": W.sentences(stops) if stops else None})
        carried = [W.carried(self.name(c), step) for c in row.carried if step in T.CARRIED_STATE]
        out = [self.out_line(c, reasons) for c, reasons in row.out]
        lines_org = [W.portfolio_line(W.money(line.value, line.currency), line.factor_id)
                     for line in self._portfolio_lines() if line.factor_id == step and line.currency is not None]
        drivers = self.drivers(step)
        return {"title": W.factor_label(step), "lines": lines, "sites": site_rows, "carried": carried, "out": out,
                "lines_org": lines_org, "drivers": drivers}

    def _portfolio_lines(self):
        return self.pb.portfolio_lines.lines if self.pb.portfolio_lines is not None else ()

    def bridge(self, title: str | None) -> dict:
        R = self.R
        shares = self.shares()
        homes = [(c, [s for s in self.steps if self.home(s) == c]) for c in CATEGORIES]
        homes = [(c, steps) for c, steps in homes if steps]
        order = [s for _, steps in homes for s in steps]  # JSON order (D-5C.27)

        def bar_effect(s: str) -> Decimal | None:  # a step's bar needs its figure in R's currency
            row = self.rows.get(s)
            return row.effect if row is not None and row.currency == R.currency else None
        bars, scale = bridge_bars([bar_effect(s) for s in order], R.effect)
        bar = dict(zip(order, bars))
        groups = []
        for category, steps in homes:
            items = []
            for s in steps:
                row = self.rows.get(s)
                effect, cur = (row.effect, row.currency) if row is not None else (None, None)
                items.append({"key": s, "label": W.factor_label(s), "value": W.amount(effect, cur, "SIGNED"),
                              "share": shares.get(s),
                              "word": self.figure_word(effect, cur, row.evidence, row.origins) if row is not None
                              else None,
                              "sites": W.sites(row.k, self.n) if row is not None else None, "bar": bar[s],
                              "drawer": self.drawer(s, row) if row is not None else None})
            total, cur = self.group_totals()[category]
            groups.append({"key": category, "label": W.heading_label(category),
                           "value": W.amount(total, cur, "SIGNED"), "steps": items})
        totals = {"actual_label": W.totals_label(self.month), "actual": W.amount(R.actual, R.currency),
                  "target_label": W.text("TARGET"), "target": W.amount(R.target, R.currency)}
        return {"title": title, "totals": totals, "scale": scale, "groups": groups, "by_site": self.by_site()}

    def by_site(self) -> dict:
        columns = [W.text("SITE"), W.text("CONTRIBUTION"), W.text("TARGET"), W.text("GAP"),
                   *(W.factor_label(s) for s in self.steps)]
        out = dict(self.R.out)
        rows = []
        for code in self.snap.asked:
            if code not in self.sb:
                continue
            root = self.sb[code].roots[T.ROOT]
            c = self.own_cur(code, root)
            cells = [self.name(code), W.amount(root.actual, c),
                     W.amount(root.target, self.own_cur(code, root, "TARGET"))]
            if code in out:
                cells.extend(W.not_compared() for _ in range(1 + len(self.steps)))
            else:
                cells.append(W.amount(root.gap, c, "SIGNED"))
                for s in self.steps:
                    own = _find(root, s)
                    carried = own is not None and own.carried
                    cells.append(W.amount(own.effect if own is not None else None, self.own_cur(code, own),
                                          T.CELL_FORM[carried]))
            rows.append(cells)
        R = self.R
        total = [W.sites(R.k, self.n), W.amount(R.actual, R.currency), W.amount(R.target, R.currency),
                 W.amount(R.effect, R.currency, "SIGNED"),
                 *(W.amount(self.rows[s].effect, self.rows[s].currency, "SIGNED") if s in self.rows
                   else W.amount(None, None, "SIGNED") for s in self.steps)]
        return {"columns": columns, "rows": rows, "total": total}

    # --- section 3.3 ----------------------------------------------------------------------------------------------

    def cash(self) -> dict:
        rows = self.pb.rows[T.CASH]
        root = rows[T.CASH]
        transit, owed, revenue = rows.get(T.IN_TRANSIT), rows.get(T.OUTSTANDING), self.rows.get(T.REVENUE)

        def m(row, value=None):  # each cash figure in its own row's currency (review H3)
            value = row.actual if row is not None and value is None else value
            return W.money(value, row.currency) if value is not None and row.currency is not None else None

        def a(row):
            return W.amount(row.actual, row.currency) if row is not None else W.amount(None, None)
        sentence = W.cash(self.month, m(root), m(root, root.target), m(owed), m(transit))
        table_rows = []
        for code in self.snap.asked:
            if code not in self.sb:
                continue
            cash_root = self.sb[code].roots[T.CASH]
            rev = _find(self.sb[code].roots[T.ROOT], T.REVENUE)
            t = _find(cash_root, T.IN_TRANSIT)
            o = _find(cash_root, T.OUTSTANDING)
            table_rows.append([self.name(code),
                               W.amount(rev.actual if rev is not None else None, self.own_cur(code, rev)),
                               W.amount(cash_root.actual, self.own_cur(code, cash_root)),
                               W.amount(t.actual if t is not None else None, self.own_cur(code, t)),
                               W.amount(o.actual if o is not None else None, self.own_cur(code, o))])
        total = [W.sites(root.k, self.n), a(revenue), a(root), a(transit), a(owed)]
        columns = [W.text("SITE"), W.text("BILLED"), W.text("COLLECTED"), W.text("IN_TRANSIT"), W.text("OUTSTANDING")]
        return {"title": W.text("CASH_TITLE"), "text": sentence,
                "word": self.figure_word(root.actual, root.currency, root.evidence, root.origins),
                "sites": W.sites(root.k, self.n), "table": {"columns": columns, "rows": table_rows, "total": total}}

    # --- section 3.4 ----------------------------------------------------------------------------------------------

    def not_available(self) -> dict:
        actual: dict[str, dict[str, list]] = {}
        budget: dict[str, list] = {"leaves": [], "sites": []}
        carried_keys: set[str] = set()

        def add(key: str, leaf: str, code: str, is_carried: bool = False) -> None:
            entry = actual.setdefault(key, {"leaves": [], "sites": []})
            if leaf not in entry["leaves"]:
                entry["leaves"].append(leaf)
            if code not in entry["sites"]:
                entry["sites"].append(code)
            if is_carried:
                carried_keys.add(key)
        for code in self.snap.asked:
            if code not in self.sb:
                continue
            notes = self.notes(code)
            for root in self.sb[code].roots.values():
                for r in _walk(root):
                    for leaf in r.unobserved_actual:
                        for key in W.record_keys(leaf, notes.get(leaf)):
                            add(key, leaf, code)
                    for leaf in r.unobserved_target:
                        if leaf not in budget["leaves"]:
                            budget["leaves"].append(leaf)
                        if code not in budget["sites"]:
                            budget["sites"].append(code)
            for leaf in self.sb[code].carried:
                for key in W.record_keys(leaf, notes.get(leaf)):
                    add(key, leaf, code, True)
        rows = []
        for key in T.RECORDS:
            if key in actual:
                entry = actual[key]
                rows.append({"needs": W.needs_row((key,), ()), "fills": W.fills(entry["leaves"], key in carried_keys),
                             "sites": W.site_names(entry["sites"], self.names)})
        if budget["leaves"]:
            rows.append({"needs": W.needs_row((), budget["leaves"]), "fills": W.fills(budget["leaves"], False),
                         "sites": W.site_names(budget["sites"], self.names)})
        return {"rows": rows, "not_built": W.text("NOT_BUILT")}

    # --- freshness ------------------------------------------------------------------------------------------------

    def fresh(self, freshness, as_of: datetime) -> dict:
        by_id = {s.site.site_id: c for c, s in self.snap.sites.items()}
        record_sites = {c.split(T.UNTRACKED_SEP)[0] for c in freshness.changed_kinds}
        record_sites |= {by_id[s.site_id] for s in freshness.stale_stamps if s.site_id in by_id}
        ordered = [c for c in self.snap.asked if c in record_sites]
        text = None if freshness.current else W.fresh(freshness.reasons, ordered, self.names, as_of)
        untracked = None
        if freshness.untracked:
            per: dict[str, list[str]] = {}
            for entry in freshness.untracked:
                code, leaf = entry.split(T.UNTRACKED_SEP, 1)
                per.setdefault(leaf, [])
                if code not in per[leaf]:
                    per[leaf].append(code)
            order = [r.factor_id for r in self.reg.rows]
            entries = [(f, [c for c in self.snap.asked if c in per[f]]) for f in order if f in per]
            untracked = W.untracked(entries, self.names)
        return {"current": freshness.current, "text": text, "untracked_text": untracked}


def month_view(*, operator: str, month: str, served, standing: Standing, actions: AgreedActions,
               names: Mapping[str, str], now: datetime) -> dict:
    """Spec section 3.1: the payload, keys in order."""
    out: dict[str, Any] = {"schema": T.SCHEMA, "operator": operator, "month": month,
                           "month_words": W.render_month(month), "nav": _nav(month, now), "state": served.state}
    if served.state == "NO_SNAPSHOT":
        out["state_text"] = W.no_snapshot(month)
        return out
    if served.state == "REBUILD_NEEDED":
        out["state_text"] = W.rebuild(month)
        return out
    out["state_text"] = None
    v = _View(served, standing, names, month)
    as_of = served.as_of
    out["as_of"] = T.iso_z(as_of)
    out["as_of_text"] = W.as_of(as_of)
    fresh = v.fresh(served.freshness, as_of)
    out["fresh"] = fresh
    out["standing"] = {"reconciled": standing.reconciled, "reason": standing.reason, "text": standing.text,
                       "details": list(standing.details)}
    head, title = v.headline()
    out["headline"] = head
    out["status_line"] = W.status_line(as_of, standing.reconciled, v.disagreeing(), v.names)
    out["tiles"] = v.tiles()
    out["notices"] = v.notices()
    out["bridge"] = v.bridge(title)
    out["cash"] = v.cash()
    out["outcomes"] = _outcomes(v, standing, fresh)
    out["decisions"] = {"title": W.text("DECISIONS_TITLE"), "text": W.text("DECISIONS")}
    out["actions"] = _actions(actions)
    out["not_available"] = v.not_available()
    return out


def _outcomes(v: _View, standing: Standing, fresh: dict) -> list[dict]:
    sums = v.group_sums()
    cards = []
    for category in CATEGORIES:
        card: dict[str, Any] = {"key": T.OUTCOME_KEYS[category], "label": W.heading_label(category)}
        steps = [v.rows[s] for s in v.steps if s in v.rows and v.home(s) == category]
        if category in (T.GROW, T.OPTIMIZE):
            card["value"] = W.amount(sums[category], v.group_cur(category), "SIGNED")
            card["word"] = v.heading_word(category)  # D-5C.26 (revises L9): no figure, no word
            card["line"] = (W.grow_line(steps[0].k if steps else 0, v.n) if category == T.GROW
                            else W.text("OPTIMIZE_LINE"))
            card["drawer"] = None
        elif category == T.PROTECT:
            card.update({"value": W.text("NOT_AVAILABLE"), "word": None, "line": W.text("PROTECT_LINE"),
                         "drawer": None})
        else:
            lines = [standing.text, *standing.details]
            if fresh["untracked_text"] is not None:
                lines.append(fresh["untracked_text"])
            card.update({"value": W.text("RECONCILED") if standing.reconciled else W.text("NOT_RECONCILED"),
                         "word": None, "line": W.assure_line(len(v.disagreeing()), v.cost_ratio()),
                         "drawer": {"title": W.text("ASSURE_TITLE"), "lines": lines}})
        cards.append(card)
    return cards


def _actions(actions: AgreedActions) -> dict:
    out: dict[str, Any] = {"title": W.text("ACTIONS_TITLE"), "connected": actions.connected}
    if not actions.connected:
        out.update({"text": W.text("ACTIONS_OFF"), "rows": [], "more": 0})
        return out
    if not actions.actions:
        out.update({"text": W.text("ACTIONS_NONE"), "rows": [], "more": 0})
        return out
    shown = actions.actions[:3]
    out.update({"text": None, "rows": [{"title": a.title, "owner": W.action_owner(a.owner_name, a.due_on),
                                         "agreed": W.action_agreed(a.created_by_name, a.created_at.date()),
                                         "state": a.state_words} for a in shown],
                "more": len(actions.actions) - len(shown)})
    return out
