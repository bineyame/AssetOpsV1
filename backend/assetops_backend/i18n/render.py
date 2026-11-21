"""UQ-6a (D-I18N.1) and SC-1 (spec section 3.6; D-SC1.1, D-SC1.11, D-SC1.18): render a `Message` for a locale at
read. One internal function, two return shapes: `render` (the text) and `served` (the text with the evidence words
of every figure it states). Neither takes a catalogue (D-SC1.22). A structured statement that cannot be rendered
truthfully raises `StatementError`; there is no fallback text. A legacy entry renders exactly as before.
"""
from __future__ import annotations

from typing import TypedDict

from assetops_backend.i18n import catalogue as _catalogue
from assetops_backend.i18n import conditions, formats, schema
from assetops_backend.i18n.catalogue import StatementError
from assetops_backend.i18n.facts import BY_TYPE, FIGURES, Absent, Evidence, Fact
from assetops_backend.i18n.locale import DEFAULT_LOCALE, current_locale
from assetops_backend.i18n.messages import Message

#: The public surface (D-SC1.36): a name outside this list is private to `i18n` (`I18N_BYPASS`).
__all__ = ["Served", "render", "served"]

_KEY, _PARAMS = Message.__annotations__
_RANK = {e: i for i, e in enumerate(schema.EVIDENCE_ORDER)}
_ORIGIN_RANK = {o: i for i, o in enumerate(schema.ORIGIN_ORDER)}
_NO_ORIGIN_RANK = len(_ORIGIN_RANK)  # None: an origin that cannot be named is the weakest
_DERIVED_RANK = _RANK["DERIVED"]
_OMITTED = Absent("OMITTED")
_INLINE, _WITH, _DERIVED = schema.OPTIONS["money"]["evidence"]


class Served(TypedDict):
    text: str
    evidence: list[str]


def render(msg: Message, locale: str | None = None) -> str:
    """The message for `locale` (the request's locale when None). A legacy key: its template for the locale, else
    the English template, filled with its params verbatim. A structured key: spec section 3.6. An unknown key raises
    `KeyError`."""
    return _render(msg, locale, False)[0]


def served(msg: Message, locale: str | None = None) -> Served:
    """A `served` statement's text with the evidence words of every figure it states (D-SC1.18)."""
    text, words = _render(msg, locale, True)
    return {"text": text, "evidence": words}


class _Rendering:
    """One render's state: the facts (an omitted optional one as `Absent("OMITTED")`), the root's slot tree, the
    locale's statements and vocabulary, the figures printed (text order) and read by a chosen condition or pick, and
    an optional trace of the chosen (key, variant) chain (the guard's coverage)."""

    def __init__(self, cat, locale: str, tree: dict, facts: dict, trace: list | None):
        self.statements, self.vocab = cat.statements[locale], cat.vocabulary[locale]
        self.tree, self.facts, self.trace = tree, facts, trace
        self.printed: list[str] = []
        self.read: list[str] = []
        self.stated: set[str] = set()  # the figures the variant being filled printed or read (D-SC1F.3)


def _render(msg: Message, locale: str | None, want_served: bool, trace: list | None = None):
    cat = _catalogue.current()
    loc = current_locale() if locale is None else locale
    key, params = msg[_KEY], msg[_PARAMS]
    if key not in cat.statements[DEFAULT_LOCALE]:
        return _legacy(cat, loc, key, params, want_served), []
    if any(not isinstance(p, Fact) or isinstance(p, Evidence) for p in params.values()):
        raise StatementError("FACT_TYPE", key)
    loc = loc if loc in cat.statements else DEFAULT_LOCALE
    st = cat.statements[loc][key]
    if st.get("part_only"):
        raise StatementError("PART_ONLY", key)
    served_mode = st.get("evidence", _INLINE) != _INLINE
    if served_mode and not want_served:
        raise StatementError("EVIDENCE_UNSERVED", key)
    if want_served and not served_mode:
        raise StatementError("EVIDENCE_MODE", key)
    tree = cat.trees[loc][key]
    r = _Rendering(cat, loc, tree, _facts(key, tree, params, cat.vocabulary[loc]), trace)
    text = _statement(r, key, {})
    return text, (_served_words(r) if served_mode else [])


def _legacy(cat, loc: str, key: str, params, want_served: bool) -> str:
    if any(isinstance(p, Fact) for p in params.values()):
        raise StatementError("FACT_TYPE", key)
    if want_served:
        raise StatementError("EVIDENCE_MODE", key)
    template = cat.legacy.get(loc, {}).get(key)
    if template is None:
        template = cat.legacy[DEFAULT_LOCALE][key]
    return template.format_map(dict(params))


# --- step 2: facts against slots ------------------------------------------------------------------------------------


def _facts(key: str, tree: dict, params, vocab: dict) -> dict:
    takes = {n: s for n, s in tree.items() if s["type"] in BY_TYPE}
    for name in params:
        if name not in takes:
            raise StatementError("FACT_UNKNOWN", key, None, name)
    facts = {}
    for name, spec in takes.items():
        if name not in params:
            if not spec.get("optional"):
                raise StatementError("FACT_MISSING", key, None, name)
            facts[name] = _OMITTED
            continue
        _check_fact(key, name, spec, params[name], vocab)
        facts[name] = params[name]
    for name, spec in takes.items():
        ev = spec.get("evidence")
        if isinstance(ev, dict) and _DERIVED in ev and not isinstance(facts[name], Absent):
            _check_derived(key, name, facts[name], [facts[i] for i in ev[_DERIVED]])
    return facts


def _check_fact(key: str, name: str, spec: dict, fact, vocab: dict) -> None:
    if isinstance(fact, Absent):
        allowed = list(spec.get("absent", [])) + [_OMITTED.reason] * bool(spec.get("optional"))
        if not allowed:
            raise StatementError("FACT_TYPE", key, None, name)
        if fact.reason not in allowed:
            raise StatementError("ABSENT_REASON", key, None, name)
        return
    if type(fact) is not BY_TYPE[spec["type"]]:
        raise StatementError("FACT_TYPE", key, None, name)
    _VOCABULARY_CHECKS.get(spec["type"], _no_check)(key, name, spec, fact, vocab)


def _no_check(key, name, spec, fact, vocab) -> None:
    return None


def _known(key, name, vocab: dict, vocabulary: str, entry: str) -> None:
    if entry not in vocab[vocabulary]["entries"]:
        raise StatementError("VOCABULARY_UNKNOWN", key, None, name)


def _check_word(key, name, spec, fact, vocab) -> None:
    if fact.vocabulary != spec["vocabulary"]:
        raise StatementError("FACT_TYPE", key, None, name)
    _known(key, name, vocab, fact.vocabulary, fact.key)


def _check_state(key, name, spec, fact, vocab) -> None:
    if fact.value not in spec["values"]:
        raise StatementError("FACT_TYPE", key, None, name)


def _check_items(key, name, spec, fact, vocab) -> None:
    for item in fact.items:
        _check_fact(key, name, spec["of"], item, vocab)


def _check_unit(key, name, spec, fact, vocab) -> None:
    _known(key, name, vocab, "unit", fact.unit)


def _check_noun(key, name, spec, fact, vocab) -> None:
    _known(key, name, vocab, "noun", fact.noun)


_VOCABULARY_CHECKS = {"word": _check_word, "state": _check_state, "items": _check_items, "price": _check_unit,
                      "quantity": _check_unit, "count": _check_noun, "k_of_n": _check_noun}


def _origin_rank(origin) -> int:
    return _NO_ORIGIN_RANK if origin is None else _ORIGIN_RANK[origin]


def _check_derived(key: str, name: str, fact, inputs: list) -> None:
    """Spec section 3.3.1: a derived figure is no stronger than `DERIVED` and than its weakest present input, and
    its origin is the weakest of its present inputs' origins."""
    present = [i.evidence for i in inputs if not isinstance(i, Absent)]
    floor = max([_DERIVED_RANK, *(_RANK[e.evidence] for e in present)])
    if _RANK[fact.evidence.evidence] < floor:
        raise StatementError("EVIDENCE_DERIVED", key, None, name)
    if present and _origin_rank(fact.evidence.origin) != max(_origin_rank(e.origin) for e in present):
        raise StatementError("EVIDENCE_DERIVED", key, None, name)


# --- steps 3 to 6: choose, require, fill, parts ---------------------------------------------------------------------


def _holds(r: _Rendering, key: str, vid, cond) -> bool:
    try:
        return conditions.holds(cond, r.facts)
    except conditions.ConditionTypeError:
        raise StatementError("CONDITION_TYPE", key, vid) from None


def _statement(r: _Rendering, key: str, inherited: dict) -> str:
    st = r.statements[key]
    chosen = next((v for v in st["variants"] if v.get("when") is None or _holds(r, key, v["id"], v["when"])), None)
    if chosen is None:
        # A defence a loaded catalogue cannot reach: the load proved a last variant without `when` or an exhaustive
        # set over a state slot that is always given (NO_FALLBACK, NOT_EXHAUSTIVE); no plant can trigger it.
        raise StatementError("NO_VARIANT", key)
    vid = chosen["id"]
    if chosen.get("requires") is not None and not _holds(r, key, vid, chosen["requires"]):
        raise StatementError("REQUIRES_FAILED", key, vid)
    if r.trace is not None:
        r.trace.append((key, vid))
    start = (len(r.printed), len(r.read))
    for c in (chosen.get("when"), chosen.get("requires")):
        r.read.extend(_catalogue.condition_slots(c))
    merged = dict(inherited)
    for slot, opts in chosen.get("options", {}).items():
        merged[slot] = {**merged.get(slot, {}), **opts}
    slots = st.get("slots", {})
    # Two passes (D-SC1F.3): every field but the `evidence` ones first, recording what this variant (and the parts
    # chosen under it) printed and read; then the `evidence` fields, which count only those figures. Text order kept.
    pieces = list(_catalogue.fields(chosen["text"]))
    filled: dict[int, str] = {}
    for late in (False, True):
        if late:
            r.stated = {*r.printed[start[0]:], *r.read[start[1]:]}
        for i, (_, field) in enumerate(pieces):
            if field is not None and _LATE.get(slots[field]["type"], False) is late:
                spec = slots[field]
                filled[i] = _FILL.get(spec["type"], _fill_fact)(r, key, vid, field, spec, merged)
    return "".join(literal + filled.get(i, "") for i, (literal, _) in enumerate(pieces))


def _fill_fact(r: _Rendering, key, vid, name: str, spec: dict, merged: dict) -> str:
    fact = r.facts[name]
    if isinstance(fact, Absent):
        raise StatementError("ABSENT_PRINTED", key, vid, name)
    text = formats.FORMATS[spec["type"]](fact, formats.options(spec, merged.get(name)), r.vocab)
    if isinstance(fact, FIGURES):
        r.printed.append(name)
        if isinstance(spec.get("evidence"), str):  # the `inline` form: the word after the figure
            text = text + " (" + formats.evidence_word(fact.evidence, r.vocab) + ")"
    return text


def _fill_evidence(r: _Rendering, key, vid, name: str, spec: dict, merged: dict) -> str:
    """The `with` basis: the words of its `of` slots that are present and that this variant states, by printing them
    (in its text or a part under it) or reading them in its `when`/`requires` (D-SC1F.3, `_served_words`' rule). A
    statement that words a figure printed elsewhere (3A7's `money_word`) reads it with `requires: present`
    (D-SC1F.7)."""
    stated = r.stated
    opts = formats.options(spec, merged.get(name))
    words: list[str] = []
    for slot in spec["of"]:
        fact = r.facts[slot]
        if not isinstance(fact, Absent) and slot in stated:
            w = formats.figure_word(fact, opts, r.vocab)
            if w not in words:
                words.append(w)
    if not words:
        raise StatementError("ABSENT_PRINTED", key, vid, name)
    return formats.join(r.vocab, words)


def _pick_value(fact):
    if isinstance(fact, Absent):
        return None
    if isinstance(fact, FIGURES):
        return conditions.sign_of(fact.exact)
    return fact.value


def _fill_pick(r: _Rendering, key, vid, name: str, spec: dict, merged: dict) -> str:
    slot, domain = _catalogue.pick_domain(spec, r.tree)
    r.read.append(slot)
    value = _pick_value(r.facts[slot])
    if value not in domain:
        # A defence a loaded catalogue cannot reach: PICK_REACH proved at load that no path reaches this pick with a
        # value outside its domain; no plant can trigger it.
        raise StatementError("PICK_DOMAIN", key, vid, name)
    return spec["words"][value]


def _fill_part(r: _Rendering, key, vid, name: str, spec: dict, merged: dict) -> str:
    return _statement(r, spec["key"], merged)


def _fill_example(r: _Rendering, key, vid, name: str, spec: dict, merged: dict) -> str:
    return spec["text"]


_FILL = {"evidence": _fill_evidence, "pick": _fill_pick, "part": _fill_part, "example": _fill_example}
#: D-SC1F.3: the slot types filled in a variant's second pass, after what it printed and read is known.
_LATE = {"evidence": True}


def _served_words(r: _Rendering) -> list[str]:
    """Printed figures in text order, then figures only read by a chosen condition or pick in slot declaration
    order; present ones only; their distinct words."""
    order = [*r.printed, *(n for n in r.tree if n in r.read and n not in r.printed)]
    words: list[str] = []
    for name in order:
        fact = r.facts.get(name)
        if isinstance(fact, FIGURES):
            w = formats.evidence_word(fact.evidence, r.vocab)
            if w not in words:
                words.append(w)
    return words
