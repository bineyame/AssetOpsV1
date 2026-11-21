"""SC-1 (spec section 3.3; D-SC1.10, D-SC1.24, D-SC1.25): one format per slot type, product-wide.

Formats only display: they quantize, take the magnitude, add a sign. They never add, divide or compare figures (a
share, a difference, an allowed amount is a fact the caller computed). Every word they print comes from the locale's
vocabulary (`format`, `unit`, `noun`, `month`, `evidence`); they dispatch by table (`FORMATS`, `ROUNDINGS`), never
by comparing a string. Private to `i18n`: the only renderer is `i18n.render` (D-SC1.22).
"""
from __future__ import annotations

import datetime
from decimal import ROUND_DOWN, ROUND_HALF_EVEN, ROUND_UP, Context, Decimal, DivisionByZero, InvalidOperation, Overflow

from assetops_backend.i18n import schema
from assetops_backend.i18n.facts import Money

DISPLAY = Context(prec=34, rounding=ROUND_HALF_EVEN, traps=[InvalidOperation, DivisionByZero, Overflow])
ROUNDINGS = dict(zip(schema.OPTIONS["money"]["round"], (ROUND_HALF_EVEN, ROUND_DOWN, ROUND_UP)))
MINUS, PLUS, SPACE = "−", "+", " "
#: USD reads `$1,200.00`; every other currency `KES 1,200.00` (5c section 2.1).
_PREFIX = {"USD": "$"}
_NOUN_FORM = {True: "one", False: "other"}
_PRICE_PLACES = (2, 4)
_BY_VOCABULARY = schema.OPTIONS["items"]["order"][1]


def options(spec: dict, overrides: dict | None = None) -> dict:
    """The slot's options: each display option from `overrides` (a variant's), else the slot's, else its default."""
    out = {}
    for name, allowed in schema.OPTIONS[spec["type"]].items():
        default = allowed[0] if allowed else None
        out[name] = (overrides or {}).get(name, spec.get(name, default))
    return out


def word(vocab: dict, vocabulary: str, key: str, form: str) -> str:
    return vocab[vocabulary]["entries"][key][form]


def _fmt(vocab: dict, key: str) -> str:
    return word(vocab, "format", key, "in_sentence")


def _number(value: Decimal, places, rounding, *, magnitude: bool, signed: bool, prefix: str, suffix: str,
            commas: bool, vocab: dict) -> str:
    """A figure's digits with its sign, prefix and suffix. `places` an int quantizes (and a non-zero value that
    displays as zero reads `less than` the smallest unit: D-SC1.24); `normal` prints the normalised value."""
    if isinstance(places, int):
        unit = Decimal(1).scaleb(-places, context=DISPLAY)
        q = value.quantize(unit, rounding=rounding, context=DISPLAY)
        if q.is_zero() and not value.is_zero():
            body = prefix + f"{unit:f}" + suffix
            if value < 0 and not magnitude:
                return _fmt(vocab, "more_than") + SPACE + MINUS + body
            return _fmt(vocab, "less_than") + SPACE + body
    else:
        q = value.normalize(DISPLAY)
    digits = f"{abs(q):,f}" if commas else f"{abs(q):f}"
    sign = ""
    if q < 0 and not magnitude:
        sign = MINUS
    elif q > 0 and signed:
        sign = PLUS
    return sign + prefix + digits + suffix


def _prefix(currency: str) -> str:
    return _PREFIX.get(currency, currency + SPACE)


def money(fact, opts: dict, vocab: dict) -> str:
    return _number(fact.value, 2, ROUNDINGS[opts["round"]], magnitude=opts["abs"], signed=opts["signed"],
                   prefix=_prefix(fact.currency), suffix="", commas=True, vocab=vocab)


def _unit_suffix(vocab: dict, unit: str) -> str:
    return SPACE + word(vocab, "unit", unit, "symbol")


def price(fact, opts: dict, vocab: dict) -> str:
    places = _PRICE_PLACES[-fact.value.normalize(DISPLAY).as_tuple().exponent > 2]
    suffix = SPACE + _fmt(vocab, "per") + _unit_suffix(vocab, fact.unit)
    return _number(fact.value, places, ROUND_HALF_EVEN, magnitude=opts["abs"], signed=False,
                   prefix=_prefix(fact.currency), suffix=suffix, commas=True, vocab=vocab)


def quantity(fact, opts: dict, vocab: dict) -> str:
    return _number(fact.value, opts["places"], ROUND_HALF_EVEN, magnitude=opts["abs"], signed=opts["signed"],
                   prefix="", suffix=_unit_suffix(vocab, fact.unit), commas=True, vocab=vocab)


def percent(fact, opts: dict, vocab: dict) -> str:
    return _number(DISPLAY.multiply(fact.value, Decimal(100)), opts["places"], ROUNDINGS[opts["round"]],
                   magnitude=False, signed=False, prefix="", suffix="%", commas=False, vocab=vocab)


def _noun(vocab: dict, noun: str, n: int) -> str:
    return word(vocab, "noun", noun, _NOUN_FORM[n == 1])


def count(fact, opts: dict, vocab: dict) -> str:
    number = f"{fact.n:,}"
    return number if opts["bare"] else number + SPACE + _noun(vocab, fact.noun, fact.n)


def k_of_n(fact, opts: dict, vocab: dict) -> str:
    return (f"{fact.k:,}" + SPACE + _fmt(vocab, "of") + SPACE + f"{fact.n:,}" + SPACE
            + _noun(vocab, fact.noun, fact.n))


def _month_name(vocab: dict, month: int) -> str:
    months = vocab["month"]
    return months["entries"][months["order"][month - 1]]["label"]


def month(fact, opts: dict, vocab: dict) -> str:
    forms = dict(zip(schema.OPTIONS["month"]["form"], (f"{_month_name(vocab, fact.month)} {fact.year}",
                                                       _month_name(vocab, fact.month))))
    return forms[opts["form"]]


def _day_words(vocab: dict, d: datetime.date) -> str:
    return f"{d.day} {_month_name(vocab, d.month)} {d.year}"


def day(fact, opts: dict, vocab: dict) -> str:
    return _day_words(vocab, fact.day)


def instant(fact, opts: dict, vocab: dict) -> str:
    at = fact.at.astimezone(datetime.timezone.utc)
    clock = str(at.hour).rjust(2, "0") + ":" + str(at.minute).rjust(2, "0")
    return _day_words(vocab, at.date()) + ", " + clock + SPACE + _fmt(vocab, "utc")


def word_slot(fact, opts: dict, vocab: dict) -> str:
    entry = vocab[fact.vocabulary]["entries"][fact.key]
    text = entry[opts["form"]]
    return (entry["article"] + SPACE + text) if opts["article"] else text


def name(fact, opts: dict, vocab: dict) -> str:
    return fact.text


def join(vocab: dict, parts: list[str]) -> str:
    """`A`, `A and B`, `A, B and C`."""
    if len(parts) == 1:
        return parts[0]
    return ", ".join(parts[:-1]) + SPACE + _fmt(vocab, "and") + SPACE + parts[-1]


def items(fact, opts: dict, vocab: dict) -> str:
    of = opts["of"]
    members = list(fact.items)
    if opts["order"] == _BY_VOCABULARY:
        members.sort(key=lambda w: vocab[w.vocabulary]["order"].index(w.key))
    inner = options(of)
    return join(vocab, [FORMATS[of["type"]](m, inner, vocab) for m in members])


def evidence_word(evidence, vocab: dict) -> str:
    """5c section 2.4 as data, applied by a fixed three-step algorithm: the evidence in `by_evidence_first`; else no
    origin reads `no_origin`, an origin in `by_origin` its word; else `observed_by_evidence[evidence]`."""
    table = vocab["evidence"]
    first = table["by_evidence_first"].get(evidence.evidence)
    if first is not None:
        return first
    if evidence.origin is None:
        return table["no_origin"]
    return table["by_origin"].get(evidence.origin) or table["observed_by_evidence"][evidence.evidence]


def figure_word(fact, opts: dict, vocab: dict) -> str:
    """A figure's evidence word; with the `evidence` slot's `money` option, a `Money` not yet reconciled adds the
    money suffix (3A7 `money_word`)."""
    text = evidence_word(fact.evidence, vocab)
    if opts.get("money") and isinstance(fact, Money) and fact.evidence.reconciled is False:
        return text + ", " + vocab["evidence"]["money_suffix"]
    return text


#: The one format per type that prints a fact (`evidence`, `pick`, `part` and `example` are filled by render).
FORMATS = {"money": money, "price": price, "quantity": quantity, "percent": percent, "count": count,
           "k_of_n": k_of_n, "month": month, "day": day, "instant": instant, "word": word_slot, "name": name,
           "items": items}
