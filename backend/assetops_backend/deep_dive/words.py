"""5c (spec section 2 as SC-1 statements, D-SC1.14): the functions that build the deep-dive's facts and render its
statements. Which heading the headline names (D-5C.15), the records a gap needs (section 2.3) and each figure's
evidence word (section 2.4, through 3A7's `money_word`) are decided here; every word is a statement's.
"""
from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from decimal import ROUND_HALF_EVEN, Context, Decimal
from typing import Any, Protocol

from assetops_backend.i18n import (Absent, Count, Day, Evidence, Flag, Instant, Items, KOfN, Money, Month, Name, Percent,
                                   Price, Quantity, State, Word, message, render)
from assetops_backend.i18n import served as served_words
from assetops_backend.structure.evaluate import weakest, weakest_origin
from assetops_backend.structure.reconciliation import money_word

from assetops_backend.deep_dive import tables as T

CENT = Decimal("0.01")
EXACT = Context(prec=34, rounding=ROUND_HALF_EVEN)  # the caller's context never reaches a figure


class Standing(Protocol):
    """3A7's `MoneyStanding` satisfies it (spec section 3, D-3A7.16)."""
    reconciled: bool
    reason: str
    text: str
    details: tuple[str, ...]


def text(piece: str) -> str:
    """One of the screen's fixed words (`deep_dive.text`)."""
    return render(message("deep_dive.text", piece=State(piece)))


def figure_text(msg) -> str:
    """A `served` statement's text; its evidence is the payload's `word` beside it."""
    return served_words(msg)["text"]


def month_of(code: str) -> Month:
    year, month = code.split("-")
    return Month(int(year), int(month))


def render_month(code: str) -> str:
    """`month_words`: "October 2026"."""
    return render(message("deep_dive.month_words", month=month_of(code)))


#: Section 2.4 (D-5C.3, D14) on this screen: a declared figure reads by its weakest origin, as a recorded one does
#: ("Emulated", "Simulated", "Estimated", else "Recorded"). The shared vocabulary reads `DECLARED` "Declared" for
#: every origin (D-SC1F.1, written for a declared setting); this screen's figures never take that word.
SCREEN_EVIDENCE = {"DECLARED": "RECORDED"}


def evidence(ev: str, origins: Sequence[str]) -> Evidence:
    """A figure's evidence in section 2.4's order (`SCREEN_EVIDENCE`), for every word and served figure here."""
    return Evidence(SCREEN_EVIDENCE.get(ev, ev), weakest_origin(origins))


def money(value: Decimal, currency: str | None, ev: Evidence | None = None) -> Money:
    return Money(cents(value), currency, ev or Evidence("DERIVED"))


def amount(value: Decimal | None, currency: str | None, form: str = "PLAIN", ev: Evidence | None = None) -> str:
    """A money value or cell: `deep_dive.money` (PF4's bare "Not available yet" when there is none)."""
    if value is None or currency is None:
        return figure_text(message("deep_dive.money", value=Absent("NOT_AVAILABLE"), form=State(form)))
    return figure_text(message("deep_dive.money", value=money(value, currency, ev), form=State(form)))


def cents(value: Decimal) -> Decimal:
    """Round for display without a negative zero (D-DD.185)."""
    rounded = value.quantize(CENT, rounding=ROUND_HALF_EVEN, context=EXACT)
    return EXACT.plus(rounded)


def plain(value: Decimal) -> str:
    """A bare display amount for a bar, with the underlying value kept exact (D-DD.163)."""
    return str(cents(value))


def not_compared() -> str:
    return figure_text(message("deep_dive.money", value=Absent("NOT_COMPARED"), form=State("PLAIN")))


def word(ev: str, origins: Sequence[str], standing: Standing, currency: str) -> str:
    """Section 2.4 for a money figure in `currency`: "Not available yet", else the evidence word (section 2.4's order,
    `evidence`) with 3A7's money suffix. A figure with no value or no currency has no word: the view's `figure_word`
    never calls this for one (D-5C.26)."""
    if ev == "NOT_AVAILABLE":
        return text("NOT_AVAILABLE")
    return money_word(Money(Decimal(0), currency, evidence(ev, origins)), standing)


def weakest_of(rows: Iterable[Any]) -> tuple[str, tuple[str, ...]]:
    """The weakest evidence and the union of origins of `rows` (a heading's steps)."""
    rows = list(rows)
    origins: list[str] = []
    for r in rows:
        origins.extend(o for o in r.origins if o not in origins)
    return weakest([r.evidence for r in rows]), tuple(origins)


def factor_label(factor_id: str) -> str:
    return render(message("deep_dive.label", factor=Word("factor", factor_id)))


def heading_label(category: str) -> str:
    return render(message("deep_dive.heading", heading=Word("heading", category)))


def sites(k: int, n: int) -> str:
    return render(message("deep_dive.sites", sites=KOfN(k, n, "site")))


def names_of(codes: Sequence[str], names: Mapping[str, str]) -> Items:
    return Items(tuple(Name(names.get(c, c), "site.name") for c in codes))


# --- the headline (D-5C.15) -----------------------------------------------------------------------------------------

def named(gap: Decimal | None, grow: Decimal | None, optimize: Decimal | None) -> tuple[str | None, Decimal | None]:
    """Of Grow and Optimize, those whose sum has the gap's sign (zero and a missing sum have none); the larger in
    magnitude, ties to Optimize; (None, None) when none."""
    if gap is None or cents(gap) == 0:
        return None, None
    same = [(h, v) for h, v in ((T.OPTIMIZE, optimize), (T.GROW, grow))
            if v is not None and cents(v) != 0 and (v < 0) == (gap < 0)]
    if not same:
        return None, None
    best = same[0]
    for h, v in same[1:]:
        if abs(v) > abs(best[1]):
            best = (h, v)
    return best


def headline_facts(gap: Money | None, big: Money | None, subject: str | None, month: str, k: int, n: int,
                   currencies_differ: bool = False) -> dict:
    facts: dict[str, Any] = {"month": month_of(month), "sites": KOfN(k, n, "site")}
    if currencies_differ:
        facts["cause"] = State("CURRENCIES")
    if gap is not None:
        facts["gap"] = gap
    if big is not None:
        facts["big"] = big
        facts["subject"] = Word("headline_subject", subject)
    return facts


def headline(gap: Money | None, big: Money | None, subject: str | None, month: str, k: int, n: int,
             currencies_differ: bool = False) -> dict:
    return served_words(message("deep_dive.headline",
                                **headline_facts(gap, big, subject, month, k, n, currencies_differ)))


def bridge_title(gap: Money, big: Money | None, subject: str | None) -> str:
    facts: dict[str, Any] = {"gap": gap}
    if big is not None:
        facts["big"] = big
        facts["subject"] = Word("headline_subject", subject)
    return figure_text(message("deep_dive.bridge_title", **facts))


# --- the records a gap needs (section 2.3) --------------------------------------------------------------------------

def record_keys(leaf: str, note: str | None) -> tuple[str, ...]:
    """A leaf's record keys as `NOTE_KEYS` says: a note adds its keys; ANALYSING and MONTH_CLOSE replace them."""
    added = T.NOTE_KEYS.get(note or "", ())
    if any(k in T.REPLACING for k in added):
        return added
    return (*T.RECORD_KEYS.get(leaf, ()), *added)


def record_chain(keys: Sequence[str]) -> Name:
    """The records as a comma list, built from the right (`deep_dive.record_chain`); a Name of its finished text."""
    out: Name | None = None
    for key in reversed(keys):
        facts: dict[str, Any] = {"head": Word("record", key)}
        if out is not None:
            facts["rest"] = out
        out = Name(render(message("deep_dive.record_chain", **facts)), "deep_dive.record_chain")
    return out


def needs_facts(keys: Iterable[str], target_leaves: Sequence[str]) -> dict:
    """`deep_dive.needs`'s facts: the distinct records in `RECORDS` order (the last apart), then the budget lines of
    `target_leaves`."""
    held = set(keys)
    records = [k for k in T.RECORDS if k in held]
    facts: dict[str, Any] = {}
    factors = list(dict.fromkeys(target_leaves))
    if factors:
        facts["factors"] = Items(tuple(Word("factor", f) for f in factors))
    if records:
        facts["last"] = Word("record", records[-1])
        if len(records) > 1:
            facts["records"] = record_chain(records[:-1])
    return facts


def actual_keys(leaves: Sequence[str], notes: Mapping[str, str | None]) -> list[str]:
    out: list[str] = []
    for leaf in leaves:
        out.extend(record_keys(leaf, notes.get(leaf)))
    return out


def stop_text(reason: str, keys: Iterable[str], target_leaves: Sequence[str]) -> str:
    return figure_text(message("deep_dive.stop", reason=State(reason), **needs_facts(keys, target_leaves)))


def residual_text(parent: str, effect: Money, keys: Iterable[str], target_leaves: Sequence[str]) -> str:
    return figure_text(message("deep_dive.stop_residual", parent=Word("factor", parent), effect=effect,
                               **needs_facts(keys, target_leaves)))


def differ_text(side: str, stated: Money, computed: Money) -> str:
    apart = money(stated.value - computed.value, stated.currency, stated.evidence)
    return figure_text(message("deep_dive.stop_differ", side=State(side), stated=stated, computed=computed,
                               apart=apart))


def currency_text(currencies: Sequence[str]) -> str:
    return render(message("deep_dive.stop_currency",
                          currencies=Items(tuple(Name(c, "row.currency") for c in currencies))))


def needs_row(keys: Iterable[str], target_leaves: Sequence[str]) -> str:
    return figure_text(message("deep_dive.needs_row", **needs_facts(keys, target_leaves)))


def out_text(site: str, reason: str, keys: Iterable[str] = (), target_leaves: Sequence[str] = (),
             target: Money | None = None, currencies: Sequence[str] = ()) -> str:
    facts: dict[str, Any] = {"site": Name(site, "site.name"), "reason": State(reason)}
    if currencies:
        facts["currency"] = Items(tuple(Name(c, "row.currency") for c in currencies))
    if reason == "NEEDS":
        facts.update(needs_facts(keys, target_leaves))
    if target is not None:
        facts["target"] = target
    return figure_text(message("deep_dive.out", **facts))


# --- other sentences ------------------------------------------------------------------------------------------------

def drawer_values(actual: Money, target: Money, difference: Money) -> str:
    return figure_text(message("deep_dive.drawer_values", actual=actual, target=target, difference=difference))


def drawer_effect(effect: Money) -> str:
    return figure_text(message("deep_dive.drawer_effect", effect=effect))


def share(value: Decimal, ev: Evidence) -> str:
    return figure_text(message("deep_dive.share", share=Percent(value, Evidence(ev.evidence, ev.origin))))


def carried(site: str, leaf: str) -> str:
    return render(message("deep_dive.carried", site=Name(site, "site.name"), leaf=State(T.CARRIED_STATE[leaf])))


def portfolio_line(value: Money, factor_id: str) -> str:
    return figure_text(message("deep_dive.portfolio_line", value=value, factor=Word("factor", factor_id)))


def disagreement(site: str, factor_id: str, stated: Money, computed: Money | None) -> str:
    return figure_text(message("deep_dive.disagreement", site=Name(site, "site.name"),
                               factor=Word("factor", factor_id), stated=stated,
                               computed=computed if computed is not None else Absent("NOT_ADDED")))


def status_line(at, reconciled: bool, disagreeing: Sequence[str], names: Mapping[str, str]) -> str:
    facts: dict[str, Any] = {"at": Instant(at), "reconciled": Flag(reconciled)}
    if disagreeing:
        facts["sites"] = names_of(disagreeing, names)
        facts["total"] = Count(len(disagreeing), "site")
    else:
        facts["sites"], facts["total"] = Absent("NONE"), Absent("NONE")
    return render(message("deep_dive.status_line", **facts))


def as_of(at) -> str:
    return render(message("deep_dive.as_of", at=Instant(at)))


def tile_target(target: Money, ratio: Decimal | None) -> str:
    facts: dict[str, Any] = {"target": target}
    facts["share"] = Percent(ratio, Evidence("DERIVED")) if ratio is not None else Absent("TARGET_NOT_POSITIVE")
    return figure_text(message("deep_dive.tile_target", **facts))


def cost_at_budget(ratio: Decimal) -> str:
    return figure_text(message("deep_dive.cost_at_budget", share=Percent(ratio, Evidence("DERIVED"))))


def tile_split(grow: Money, optimize: Money) -> str:
    return figure_text(message("deep_dive.tile_split", grow=grow, optimize=optimize))


def tile_rest(rest: Money, gap: Money) -> str:
    return figure_text(message("deep_dive.tile_rest", rest=rest, gap=gap))


def plan_value_label() -> str:
    return render(message("deep_dive.plan_value_label", horizon=Count(12, "month")))


def totals_label(month: str) -> str:
    return render(message("deep_dive.totals_label", month=month_of(month)))


def cash(month: str, collected: Money | None, parts: tuple[Money, Money, Money] | None) -> str:
    """`parts` is (billed, in_transit, outstanding), given together or not at all (D-5C.29)."""
    facts: dict[str, Any] = {"month": month_of(month),
                             "collected": collected if collected is not None else Absent("NOT_AVAILABLE")}
    if parts is not None:
        facts.update(billed=parts[0], in_transit=parts[1], outstanding=parts[2])
    return figure_text(message("deep_dive.cash", **facts))


def fresh(reasons: Sequence[str], record_sites: Sequence[str], names: Mapping[str, str], at) -> str:
    facts: dict[str, Any] = {"records": Flag("RECORDS" in reasons), "closed": Flag("MONTH_CLOSED" in reasons),
                             "rules": Flag(any(r != "RECORDS" and r != "MONTH_CLOSED" for r in reasons)),
                             "at": Instant(at)}
    if record_sites:
        facts["sites"] = names_of(record_sites, names)
    return render(message("deep_dive.fresh", **facts))


def untracked(entries: Sequence[tuple[str, Sequence[str]]], names: Mapping[str, str]) -> str:
    """`entries` (factor, Site codes) in registry order; each entry is its own statement, listed by name."""
    rendered = tuple(Name(render(message("deep_dive.untracked_entry", factor=Word("factor", f),
                                         sites=names_of(codes, names))), "deep_dive.untracked_entry")
                     for f, codes in entries)
    return render(message("deep_dive.untracked", entries=Items(rendered)))


def no_snapshot(month: str) -> str:
    return render(message("deep_dive.no_snapshot", month=month_of(month)))


def rebuild(month: str) -> str:
    return render(message("deep_dive.rebuild", month=month_of(month)))


def action_owner(owner: str, due) -> str:
    return render(message("deep_dive.action_owner", owner=Name(owner, "action.owner"), due=Day(due)))


def action_agreed(by: str, on) -> str:
    return render(message("deep_dive.action_agreed", by=Name(by, "action.created_by"), on=Day(on)))


def grow_line(k: int, n: int) -> str:
    return render(message("deep_dive.grow_line", sites=KOfN(k, n, "site")))


def assure_line(disagreements: int, cost: Decimal | None) -> str:
    facts: dict[str, Any] = {"disagreements": Count(disagreements, "budget_disagreement")}
    if cost is not None:
        facts["share"] = Percent(cost, Evidence("DERIVED"))
    return figure_text(message("deep_dive.assure_line", **facts))


def fills(factors: Sequence[str], is_carried: bool) -> str:
    return render(message("deep_dive.fills", factors=Items(tuple(Word("factor", f) for f in dict.fromkeys(factors))),
                          carried=Flag(is_carried)))


def site_names(codes: Sequence[str], names: Mapping[str, str]) -> str:
    return render(message("deep_dive.names", sites=names_of(codes, names)))


def detail(row_unit_kind: str, actual: Decimal, target: Decimal, currency: str | None, unit: str | None) -> str:
    """Section 3.2 a driver's "Actual {a} · Target {t}": quantity, price or money by the factor's unit."""
    ev = Evidence("DERIVED")
    if row_unit_kind == "QUANTITY":
        facts = {"actual_quantity": Quantity(actual, unit, ev), "target_quantity": Quantity(target, unit, ev)}
    elif row_unit_kind == "PRICE":
        facts = {"actual_price": Price(actual, currency, unit, ev), "target_price": Price(target, currency, unit, ev)}
    else:
        facts = {"actual_money": money(actual, currency, ev), "target_money": money(target, currency, ev)}
    return figure_text(message("deep_dive.driver_detail", **facts))


def sentences(parts: Sequence[str]) -> str:
    """Finished sentences, each already a rendered statement, one after another (section 3.2's drawer text)."""
    out = ""
    for index, part in enumerate(reversed(parts)):
        facts: dict[str, Any] = {"head": Name(part, "deep_dive.sentence")}
        if index:
            facts["rest"] = Name(out, "deep_dive.sentence")
        out = render(message("deep_dive.sentences", **facts))
    return out
