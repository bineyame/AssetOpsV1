"""SC-1 (spec section 3.12): every closed list the statement mechanism uses, written from the spec exactly.

Adding to any of these sets is a spec change; `test_sc1_statements.py` T12 asserts each equals the spec's list. The
guard's mechanism scope (spec section 3.8.4 (1)) allows a string constant in `i18n/*.py` only when it is a member of
`TOKENS` or `SYMBOLS`, an upper snake code, or a decimal literal.
"""
from __future__ import annotations

#: Section 3.3's slot types.
TYPES = ("money", "price", "quantity", "percent", "count", "k_of_n", "month", "day", "instant", "word", "name",
         "items", "evidence", "pick", "part", "example", "state", "flag")

#: Section 3.3's options per type. A display option maps to its allowed values, default first (`int` stands for any
#: non-negative integer). A structural option maps to `()`: its shape is proved by the load check. `evidence` lists
#: its three forms (section 3.3.1): `"inline"`, `{"with": <evidence slot>}`, `{"derived_from": [<figure slots>]}`.
_EVIDENCE_FORMS = ("inline", "with", "derived_from")
OPTIONS = {
    "money": {"round": ("half_even", "down", "up"), "abs": (False, True), "signed": (False, True), "evidence": _EVIDENCE_FORMS},
    "price": {"abs": (False, True), "evidence": _EVIDENCE_FORMS},
    "quantity": {"places": ("normal", int), "abs": (False, True), "signed": (False, True), "evidence": _EVIDENCE_FORMS},
    "percent": {"places": (0, 1, 2, "normal"), "round": ("half_even", "down", "up"), "evidence": _EVIDENCE_FORMS},
    "count": {"bare": (False, True)},
    "k_of_n": {},
    "month": {"form": ("month_year", "month")},
    "day": {},
    "instant": {},
    "word": {"vocabulary": (), "form": ("label", "in_sentence"), "article": (False, True)},
    "name": {},
    "items": {"of": (), "order": ("given", "vocabulary")},
    "evidence": {"of": (), "money": (False, True)},
    "pick": {"on": (), "words": (), "domain": ()},
    "part": {"key": ()},
    "example": {"text": ()},
    "state": {"values": ()},
    "flag": {},
}

#: The data shapes' field names: statements, variants, slots, vocabularies, the forms and the `evidence` tables.
FIELDS = ("slots", "variants", "exhaustive", "evidence", "rephrase", "part_only", "id", "when", "requires", "options",
          "text", "type", "absent", "optional", "forms", "order", "entries",
          "label", "in_sentence", "article", "one", "other", "symbol",
          "by_evidence_first", "by_origin", "no_origin", "observed_by_evidence", "money_suffix")

#: Section 3.4's operators and comparators.
OPERATORS = ("present", "absent", "reason", "is", "sign", "cmp", "all", "any", "not")
COMPARATORS = ("<", "<=", "==", ">=", ">")
SIGNS = ("negative", "zero", "positive")
MODES = ("inline", "served")
REPHRASE = ("never", "allowed")

#: Copied from `structure.evaluate` (no import: `i18n` imports nothing outside `i18n`); T12 proves parity.
EVIDENCE_ORDER = ("RECORDED", "MEASURED", "DECLARED", "DERIVED", "ESTIMATED", "MODELLED", "NOT_AVAILABLE")
ORIGIN_ORDER = ("observed-financial", "field-integrated", "bench-tested", "source-emulated", "demo-simulated",
                "unknown")
ORIGINS = ORIGIN_ORDER
#: A figure's evidence: `EVIDENCE_ORDER` without `NOT_AVAILABLE` (a figure with no value is `Absent`).
EVIDENCES = EVIDENCE_ORDER[:-1]

#: The vocabularies the formats read, and the `format` vocabulary's keys (the only words the formats print).
FORMAT_VOCABULARIES = ("format", "unit", "noun", "month", "evidence")
FORMAT_WORDS = ("less_than", "more_than", "and", "of", "per", "utc")

#: D-SC1.21, D-SC1.32: number words per locale as `(roots, suffixes)` pairs. A number word is a root joined to a
#: suffix of its own pair, and nothing else; the load refuses one (case-folded) as a token of any template or
#: vocabulary literal split on non-letters, so compounds ("twenty-five", "two-thirds") fail by their parts.
NUMBER_WORDS = {"en": (
    (("zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten", "eleven", "twelve",
      "hundred", "thousand", "million", "billion", "trillion"), ("", "s", "th", "ths", "fold")),
    (("thir", "four", "fif", "six", "seven", "eigh", "nine"), ("teen", "teens", "teenth", "teenths")),
    (("twen", "thir", "for", "fif", "six", "seven", "eigh", "nine"), ("ty", "ties", "tieth", "tieths", "tyfold")),
    (("first", "second", "third", "fifth", "eighth", "ninth", "twelfth"), ("", "s")),
    (("once", "twice", "thrice", "single", "both", "pair", "couple", "dozen", "half", "quarter", "percent",
      "cent"), ("", "s")),
    (("doubl", "tripl", "quadrupl", "halv"), ("e", "es", "ed", "ing")),
    (("zero", "nought"), ("", "s", "es")),
)}


def number_words(locale: str) -> frozenset:
    """Every number word of `locale`: each root joined to each suffix of its pair (D-SC1.32)."""
    return frozenset(root + suffix for roots, suffixes in NUMBER_WORDS[locale] for root in roots for suffix in suffixes)

#: Section 3.8.4: exception types whose text is never served (their `raise` arguments are exempt from the scan).
UNSERVED = ("ValueError", "TypeError", "KeyError", "LookupError", "RuntimeError", "AssertionError",
            "NotImplementedError", "StatementError", "CatalogueError", "WireError", "SeriesRefused")

#: The punctuation the formats and the template filler may write.
SYMBOLS = ("", " ", ", ", "$", "−", "+", "%", ",", ".", "(", ")", " (", "{", "}", ":", "-", "T")

#: Names the loader and formats use that belong to no set above.
SYSTEM = ("STATEMENTS", "VOCABULARY", "statements", "vocabulary", "utf-8", "en", "USD", "OMITTED", "ABSENT")


def _tokens() -> frozenset:
    out: set = set()
    for group in (TYPES, FIELDS, OPERATORS, COMPARATORS, SIGNS, MODES, REPHRASE, EVIDENCES, EVIDENCE_ORDER, ORIGINS,
                  FORMAT_VOCABULARIES, FORMAT_WORDS, UNSERVED, SYSTEM):
        out.update(group)
    for kind, opts in OPTIONS.items():
        out.add(kind)
        for name, allowed in opts.items():
            out.add(name)
            out.update(v for v in allowed if isinstance(v, str))
    return frozenset(out)


#: The union of every set above except `SYMBOLS` and `NUMBER_WORDS` (D-SC1.32: a suffix such as `s` must never be a
#: legal mechanism constant).
TOKENS = _tokens()
