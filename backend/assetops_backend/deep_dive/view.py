"""5c (spec section 3): the deep-dive month, one pure function from the served snapshot to the payload.

Every figure is a row of `portfolio_bridge`'s `rows` or a Site bridge's `roots` (D-5B.12, D-5C.13); the snapshot's
`actual()` and `targets()` are never read. Every word is an SC-1 statement (`deep_dive/words.py`); every money
figure's word carries the organisation's standing, read by the caller at `served.as_of` (D-3A7.9, D-5C.4).
"""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date, datetime, timezone
from decimal import Decimal
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
        self.cur = self.R.currency or "USD"
        self.steps = T.STEPS[T.MINI_GRID]

    # --- small pieces ---------------------------------------------------------------------------------------------

    def name(self, code: str) -> str:
        return self.names.get(code, code)

    def money(self, value: Decimal, row=None):
        ev = W.evidence(row.evidence, row.origins) if row is not None and row.evidence != "NOT_AVAILABLE" else None
        return W.money(value, self.cur, ev)

    def word(self, row) -> str:
        return W.word(row.evidence, row.origins, self.standing, self.cur)

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
        if r.kind == "RESIDUAL":
            return W.residual_text(r.parent, self.money(r.effect or Decimal(0), r), keys, r.unobserved_target)
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
                    parts.append(W.differ_text(side, W.money(v.value, self.cur), W.money(v.computed, self.cur)))
            return T.spaced(parts)
        if reason in T.NO_RULE:
            return W.stop_text("NO_RULE", (), ())
        return None

    # --- section 3.1 ----------------------------------------------------------------------------------------------

    def group_sums(self) -> dict[str, Decimal]:
        sums = {c: Decimal(0) for c in CATEGORIES}
        for step in self.steps:
            row = self.rows.get(step)
            if row is not None and row.effect is not None:
                sums[self.home(step)] += row.effect
        return sums

    def big(self, category: str | None):
        if category is None:
            return None
        steps = [self.rows[s] for s in self.steps if s in self.rows and self.home(s) == category]
        ev, origins = W.weakest_of(steps)
        return W.money(self.group_sums()[category], self.cur, W.evidence(ev, origins))

    def headline(self) -> tuple[dict, str | None]:
        sums = self.group_sums()
        R = self.R
        subject, _ = W.named(R.effect, sums[T.GROW], sums[T.OPTIMIZE])
        gap = self.money(R.effect, R) if R.effect is not None else None
        big = self.big(subject)
        head = W.headline(gap, big, subject, self.month, R.k, self.n)
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
        ratio = self.cost_ratio()
        lines = []
        if R.target is not None:
            share = R.actual / R.target if R.actual is not None and R.target > 0 else None
            lines.append(W.tile_target(W.money(R.target, self.cur), share))
        lines.append(W.sites(R.k, self.n))
        if ratio is not None:
            lines.append(W.cost_received(ratio))
        contribution = {"key": T.TILE_KEYS[0], "label": W.text("CONTRIBUTION"), "value": W.amount(R.actual, self.cur),
                        "word": self.word(R), "lines": lines,
                        "bar": ({"actual": str(R.actual), "target": str(R.target)}
                                if R.actual is not None and R.target is not None else None)}
        gap_lines = [W.tile_split(W.money(sums[T.GROW], self.cur), W.money(sums[T.OPTIMIZE], self.cur))]
        if R.effect is not None:
            gap_lines.append(W.tile_rest(W.money(self.rest(), self.cur), W.money(R.effect, self.cur)))
        gap = {"key": T.TILE_KEYS[1], "label": W.text("GAP_TO_TARGET"), "value": W.amount(R.effect, self.cur, "SIGNED"),
               "word": self.word(R), "lines": gap_lines, "bar": None}
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
        gap = self.R.effect or Decimal(0)
        widening = [self.rows[s].effect for s in self.steps if s in self.rows and self.rows[s].effect is not None
                    and self.rows[s].effect != 0 and (self.rows[s].effect < 0) == (gap < 0)]
        total = sum((abs(e) for e in widening), Decimal(0))
        out = {}
        for s in self.steps:
            row = self.rows.get(s)
            if row is None or row.effect is None:
                continue
            e = row.effect
            if e == 0 or gap == 0 or total == 0:
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
        actual = [r[len(T.ACTUAL_PREFIX):] for r in reasons if r.startswith(T.ACTUAL_PREFIX)]
        target = [r[len(T.TARGET_PREFIX):] for r in reasons if r.startswith(T.TARGET_PREFIX)]
        if code not in self.sb or not (actual or target):
            return W.out_text(self.name(code), "NOT_MINI_GRID")
        own = self.sb[code].roots[T.ROOT].target
        keys = W.actual_keys(actual, self.notes(code))
        return W.out_text(self.name(code), "NEEDS", keys, target,
                          W.money(own, self.cur) if own is not None else None)

    def descendants(self, step: str) -> set[str]:
        out: set[str] = set()
        todo = [step]
        while todo:
            f = todo.pop()
            for child in self.reg.row(f).children:
                if child not in out:
                    out.add(child)
                    todo.append(child)
        return out

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
        return W.detail(kind, row.actual, row.target, self.cur, symbol)

    def drawer(self, step: str, row) -> dict:
        lines = []
        if row.actual is not None and row.target is not None and row.gap is not None:
            lines.append(W.drawer_values(W.money(row.actual, self.cur), W.money(row.target, self.cur),
                                         W.money(row.gap, self.cur)))
        lines.append(W.drawer_effect(W.money(row.effect or Decimal(0), self.cur)))
        lines.append(W.sites(row.k, self.n))
        site_rows = []
        for code in self.included(row):
            own = _find(self.sb[code].roots[T.ROOT], step)
            stops = self.stops(code, own) if own is not None else []
            site_rows.append({"site": self.name(code),
                              "value": W.amount(own.effect if own is not None else None, self.cur, "SIGNED"),
                              "text": T.spaced(stops) if stops else None})
        carried = [W.carried(self.name(c), step) for c in row.carried if step in T.CARRIED_STATE]
        out = [self.out_line(c, reasons) for c, reasons in row.out]
        lines_org = [W.portfolio_line(W.money(line.value, line.currency or self.cur), line.factor_id)
                     for line in self._portfolio_lines() if line.factor_id == step]
        below = self.descendants(step)
        drivers = []
        for key, r in self.rows.items():
            parent = key[len(T.RESIDUAL_PREFIX):] if key.startswith(T.RESIDUAL_PREFIX) else None
            if key in below or (parent is not None and (parent == step or parent in below)):
                drivers.append({"label": W.factor_label(key) if parent is None else W.factor_label(parent),
                                "value": W.amount(r.effect, self.cur, "SIGNED"), "sites": W.sites(r.k, self.n),
                                "detail": self.driver_detail(key, r), "word": self.word(r)})
        return {"title": W.factor_label(step), "lines": lines, "sites": site_rows, "carried": carried, "out": out,
                "lines_org": lines_org, "drivers": drivers}

    def _portfolio_lines(self):
        return self.pb.portfolio_lines.lines if self.pb.portfolio_lines is not None else ()

    def bridge(self, title: str | None) -> dict:
        R = self.R
        shares = self.shares()
        groups = []
        for category in CATEGORIES:
            steps = [s for s in self.steps if self.home(s) == category]
            if not steps:
                continue
            total = Decimal(0)
            items = []
            for s in steps:
                row = self.rows.get(s)
                effect = row.effect if row is not None else None
                total += effect or Decimal(0)
                items.append({"key": s, "label": W.factor_label(s), "value": W.amount(effect, self.cur, "SIGNED"),
                              "share": shares.get(s), "word": self.word(row) if row is not None else
                              W.text("NOT_AVAILABLE"), "sites": W.sites(row.k, self.n) if row is not None else None,
                              "drawer": self.drawer(s, row) if row is not None else None})
            groups.append({"key": category, "label": W.heading_label(category),
                           "value": W.amount(total, self.cur, "SIGNED"), "steps": items})
        totals = {"actual_label": W.totals_label(self.month), "actual": W.amount(R.actual, self.cur),
                  "target_label": W.text("TARGET"), "target": W.amount(R.target, self.cur)}
        return {"title": title, "totals": totals, "groups": groups, "by_site": self.by_site()}

    def by_site(self) -> dict:
        columns = [W.text("SITE"), W.text("CONTRIBUTION"), W.text("TARGET"), W.text("GAP"),
                   *(W.factor_label(s) for s in self.steps)]
        out = dict(self.R.out)
        rows = []
        for code in self.snap.asked:
            if code not in self.sb:
                continue
            root = self.sb[code].roots[T.ROOT]
            cells = [self.name(code), W.amount(root.actual, self.cur), W.amount(root.target, self.cur)]
            if code in out:
                cells.extend(W.not_compared() for _ in range(1 + len(self.steps)))
            else:
                cells.append(W.amount(root.gap, self.cur, "SIGNED"))
                for s in self.steps:
                    own = _find(root, s)
                    form = "ESTIMATE" if own is not None and own.carried else "SIGNED"
                    cells.append(W.amount(own.effect if own is not None else None, self.cur, form))
            rows.append(cells)
        total = [W.sites(self.R.k, self.n), W.amount(self.R.actual, self.cur), W.amount(self.R.target, self.cur),
                 W.amount(self.R.effect, self.cur, "SIGNED"),
                 *(W.amount(self.rows[s].effect if s in self.rows else None, self.cur, "SIGNED") for s in self.steps)]
        return {"columns": columns, "rows": rows, "total": total}

    # --- section 3.3 ----------------------------------------------------------------------------------------------

    def cash(self) -> dict:
        rows = self.pb.rows[T.CASH]
        root = rows[T.CASH]
        transit, owed, revenue = rows.get(T.IN_TRANSIT), rows.get(T.OUTSTANDING), self.rows.get(T.REVENUE)

        def m(row):
            return W.money(row.actual, self.cur) if row is not None and row.actual is not None else None
        sentence = W.cash(self.month, m(root), W.money(root.target, self.cur) if root.target is not None else None,
                          m(owed), m(transit))
        table_rows = []
        for code in self.snap.asked:
            if code not in self.sb:
                continue
            cash_root = self.sb[code].roots[T.CASH]
            rev = _find(self.sb[code].roots[T.ROOT], T.REVENUE)
            t = _find(cash_root, T.IN_TRANSIT)
            o = _find(cash_root, T.OUTSTANDING)
            table_rows.append([self.name(code), W.amount(rev.actual if rev is not None else None, self.cur),
                               W.amount(cash_root.actual, self.cur),
                               W.amount(t.actual if t is not None else None, self.cur),
                               W.amount(o.actual if o is not None else None, self.cur)])
        total = [W.sites(root.k, self.n), W.amount(revenue.actual if revenue is not None else None, self.cur),
                 W.amount(root.actual, self.cur), W.amount(transit.actual if transit is not None else None, self.cur),
                 W.amount(owed.actual if owed is not None else None, self.cur)]
        columns = [W.text("SITE"), W.text("BILLED"), W.text("COLLECTED"), W.text("IN_TRANSIT"), W.text("OUTSTANDING")]
        return {"title": W.text("CASH_TITLE"), "text": sentence, "word": self.word(root),
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
            ev, origins = W.weakest_of(steps)
            card["value"] = W.amount(sums[category], v.cur, "SIGNED")
            card["word"] = W.word(ev, origins, standing, v.cur)
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
