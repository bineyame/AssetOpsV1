"""SC-1 spec sections 5.1, 5.2 and 5.4: the worked statements 3A7 and 5c adopt, copied into a test catalogue, with
their hand-computed cases (W2). 3A7 and 5c write these statements in their own modules (D-SC1.26); until then the
guard's coverage skips keys absent from the shipped catalogue, and T9 renders these cases through `catalogue()`.
"""
from __future__ import annotations

from decimal import Decimal as D

from assetops_backend.i18n import (Absent, Count, Evidence, Items, KOfN, Money, Month, Name, Percent, State, Word)

from statement_cases import Case

SAME_SIGN = {"any": [{"all": [{"sign": ["gap", "negative"]}, {"sign": ["big", "negative"]}]},
                     {"all": [{"sign": ["gap", "positive"]}, {"sign": ["big", "positive"]}]}]}

#: Spec section 5.1, exactly, except `records` names its form (Q3).
RECONCILIATION = {
    "reconciliation.heading": {
        "slots": {
            "state": {"type": "state", "values": ["MATCHED", "NOT_MATCHED", "ZERO_STATED", "NOT_RECEIVED",
                                                  "CURRENCY_MISMATCH", "MONTH_OPEN"]},
            "heading": {"type": "word", "vocabulary": "heading", "form": "label"},
            "records": {"type": "word", "vocabulary": "record_noun", "form": "in_sentence", "optional": True},
            # ^ `form` added: section 3.5 gives `record_noun` only `in_sentence` (mid-build-questions.md Q3).
            "accounts": {"type": "money", "optional": True, "evidence": {"with": "basis"}},
            "recorded": {"type": "money", "optional": True, "evidence": {"with": "basis"}},
            "allowed": {"type": "money", "optional": True, "evidence": {"derived_from": ["accounts", "tolerance"]}},
            "tolerance": {"type": "percent", "places": "normal", "optional": True, "evidence": {"with": "basis"}},
            "basis": {"type": "evidence", "of": ["accounts", "recorded", "tolerance"]},
            "month": {"type": "month", "optional": True},
            "record_currencies": {"type": "items", "of": {"type": "name"}, "optional": True},
            "currency": {"type": "name", "optional": True},
            "gap_words": {"type": "part", "key": "reconciliation.gap"},
            "share_words": {"type": "part", "key": "reconciliation.share"},
        },
        "variants": [
            {"id": "matched", "when": {"is": ["state", "MATCHED"]},
             "options": {"difference": {"round": "down"}, "allowed": {"round": "up"}},
             "text": "{heading} ({basis}): the accounts say {accounts} and the records say {recorded}, {gap_words}, "
                     "within the {allowed} allowed ({tolerance})."},
            {"id": "not_matched", "when": {"is": ["state", "NOT_MATCHED"]},
             "options": {"difference": {"round": "up"}, "allowed": {"round": "down"}, "share": {"round": "up"}},
             "text": "{heading} ({basis}): the accounts say {accounts} and the records say {recorded}, "
                     "{gap_words}{share_words}, beyond the {allowed} allowed ({tolerance})."},
            {"id": "zero_stated", "when": {"is": ["state", "ZERO_STATED"]},
             "text": "{heading} ({basis}): the accounts say {accounts} and no {records} are recorded."},
            {"id": "not_received", "when": {"is": ["state", "NOT_RECEIVED"]},
             "text": "{heading} ({basis}): the accounts say {accounts}, but no {records} are recorded for {month}."},
            {"id": "currency_mismatch", "when": {"is": ["state", "CURRENCY_MISMATCH"]},
             "text": "{heading}: the accounts are in {currency}, but the records are in {record_currencies}."},
            {"id": "month_open", "when": {"is": ["state", "MONTH_OPEN"]}, "text": "{heading}: {month} is not closed yet."},
        ],
        "exhaustive": "state",
        "rephrase": "never",
    },
    "reconciliation.gap": {
        "part_only": True,
        "slots": {"difference": {"type": "money", "abs": True, "optional": True,
                                 "evidence": {"derived_from": ["accounts", "recorded"]}},
                  "direction": {"type": "pick", "on": {"sign": "difference"}, "domain": ["negative", "positive"],
                                "words": {"negative": "less", "positive": "more"}}},
        "variants": [{"id": "same", "when": {"sign": ["difference", "zero"]}, "text": "the same"},
                     {"id": "differs", "requires": {"present": "difference"}, "text": "{difference} {direction}"}],
    },
    "reconciliation.share": {
        "part_only": True,
        "slots": {"share": {"type": "percent", "places": 2, "optional": True, "absent": ["ACCOUNTS_ZERO"],
                            "evidence": {"derived_from": ["difference", "accounts"]}}},
        "variants": [{"id": "shown", "when": {"present": "share"}, "text": " ({share})"},
                     {"id": "omitted", "text": ""}],
    },
}

#: Spec section 5.2, exactly.
DEEP_DIVE = {
    "deep_dive.headline": {
        "evidence": "served",
        "slots": {
            "gap": {"type": "money", "abs": True, "optional": True},
            "big": {"type": "money", "abs": True, "optional": True},
            "subject": {"type": "word", "vocabulary": "headline_subject", "form": "in_sentence", "optional": True},
            "month": {"type": "month", "form": "month"},
            "sites": {"type": "k_of_n"},
            "direction": {"type": "pick", "on": {"sign": "gap"}, "domain": ["negative", "positive"],
                          "words": {"negative": "below", "positive": "above"}},
            "compared": {"type": "part", "key": "deep_dive.compared"},
        },
        "variants": [
            {"id": "not_available", "when": {"absent": "gap"}, "text": "Contribution for {month} is not available yet."},
            {"id": "on_target", "when": {"sign": ["gap", "zero"]}, "text": "Contribution is on target in {month}.{compared}"},
            {"id": "gap_only", "when": {"absent": "big"},
             "text": "Contribution is {gap} {direction} target in {month}.{compared}"},
            {"id": "more_than_gap", "when": {"cmp": [{"abs": "big"}, ">", {"abs": "gap"}]}, "requires": SAME_SIGN,
             "text": "Contribution is {gap} {direction} target in {month}; {subject} {big}, more than the whole gap."
                     "{compared}"},
            {"id": "share_of_gap", "requires": SAME_SIGN,
             "text": "Contribution is {gap} {direction} target in {month}; {subject} {big} of it.{compared}"},
        ],
    },
    "deep_dive.compared": {
        "evidence": "served",
        "slots": {"sites": {"type": "k_of_n"}},
        "variants": [{"id": "some", "when": {"cmp": ["sites.k", "<", "sites.n"]}, "text": " Compared for {sites}."},
                     {"id": "all", "text": ""}],
    },
}

#: Spec section 5.4, exactly.
FURTHER = {
    "deep_dive.share": {
        "evidence": "served",
        "slots": {"share": {"type": "percent", "places": 0}},
        "variants": [{"id": "widens", "when": {"sign": ["share", "positive"]}, "text": "{share} of what widens the gap"},
                     {"id": "offsets", "when": {"sign": ["share", "negative"]}, "text": "Offsets it"},
                     {"id": "no_effect", "requires": {"sign": ["share", "zero"]}, "text": "No effect"}],
    },
    "deep_dive.status_disagreement": {
        "slots": {"sites": {"type": "items", "of": {"type": "name"}, "order": "given", "absent": ["NONE"]},
                  "total": {"type": "count", "absent": ["NONE"]}},
        "variants": [
            {"id": "none", "when": {"absent": "sites"}, "requires": {"absent": "total"}, "text": ""},
            {"id": "one", "when": {"cmp": ["sites.count", "==", {"const": 1}]},
             "text": "{sites}'s budget disagrees with its own lines."},
            {"id": "few", "when": {"all": [{"cmp": ["sites.count", ">=", {"const": 2}]},
                                           {"cmp": ["sites.count", "<=", {"const": 3}]}]},
             "text": "The budgets of {sites} disagree with their own lines."},
            {"id": "many", "requires": {"cmp": ["total", "==", "sites.count"]},
             "text": "The budgets of {total} disagree with their own lines."},
        ],
    },
    "reconciliation.scope": {
        "slots": {"scope": {"type": "state", "values": ["SITE", "ORGANISATION"]},
                  "site": {"type": "name", "absent": ["ORGANISATION"]}},
        "variants": [{"id": "site", "when": {"is": ["scope", "SITE"]}, "text": "{site}"},
                     {"id": "organisation", "when": {"is": ["scope", "ORGANISATION"]},
                      "requires": {"reason": ["site", "ORGANISATION"]}, "text": "the organisation"}],
        "exhaustive": "scope",
    },
}

WORKED = {**RECONCILIATION, **DEEP_DIVE, **FURTHER}


def catalogue(*modules: dict):
    """The test catalogue: the shipped English vocabulary and `modules` (default: every worked statement)."""
    from assetops_backend.i18n import catalogue as cat
    from assetops_backend.i18n.statements.en.vocabulary import VOCABULARY

    return cat._build({"en": list(modules or (WORKED,))}, {"en": VOCABULARY})


# --- hand facts ----------------------------------------------------------------------------------------------------

FIN = "observed-financial"
EMU = "source-emulated"


def usd(value: str, evidence: str, origin: str = FIN, currency: str = "USD") -> Money:
    return Money(D(value), currency, Evidence(evidence, origin))


def heading(state: str, name: str, **facts) -> dict:
    return {"state": State(state), "heading": Word("heading", name), **facts}


C3 = heading("MATCHED", "REVENUE", accounts=usd("1200.00", "DECLARED"), recorded=usd("1200.00", "RECORDED"),
             difference=usd("0", "DERIVED"), allowed=usd("12.00", "DERIVED"),
             tolerance=Percent(D("0.005"), Evidence("DECLARED", FIN)))


def h(gap: str | None, big: str | None, k: int, n: int, subject: str | None = None) -> dict:
    facts = {"month": Month(2026, 10), "sites": KOfN(k, n, "site")}
    if gap is not None:
        facts["gap"] = usd(gap, "DERIVED", EMU)
    if big is not None:
        facts["big"] = usd(big, "DERIVED", EMU)
    if subject is not None:
        facts["subject"] = Word("headline_subject", subject)
    return facts


def share(value: str) -> dict:
    return {"share": Percent(D(value), Evidence("DERIVED", EMU))}


def names(*texts: str) -> Items:
    return Items(tuple(Name(t, "site.name") for t in texts))


CASES = [
    Case("reconciliation.heading", "not_matched",  # C1
         heading("NOT_MATCHED", "REVENUE", accounts=usd("501.50", "DECLARED"), recorded=usd("506.52", "RECORDED"),
                 difference=usd("5.02", "DERIVED"), allowed=usd("5.015", "DERIVED"),
                 share=Percent(D("0.0100099700897308"), Evidence("DERIVED", FIN)),
                 tolerance=Percent(D("0.01"), Evidence("DECLARED", FIN))),
         "Revenue (Recorded): the accounts say $501.50 and the records say $506.52, $5.02 more (1.01%), beyond the "
         "$5.01 allowed (1%)."),
    Case("reconciliation.heading", "matched",  # C2
         heading("MATCHED", "FUEL_COST", accounts=usd("505.00", "DECLARED"), recorded=usd("504.996", "RECORDED"),
                 difference=usd("-0.004", "DERIVED"), allowed=usd("5.05", "DERIVED"),
                 tolerance=Percent(D("0.01"), Evidence("DECLARED", FIN))),
         "Fuel cost (Recorded): the accounts say $505.00 and the records say $505.00, less than $0.01 less, within "
         "the $5.05 allowed (1%)."),
    Case("reconciliation.heading", "matched", C3,  # C3
         "Revenue (Recorded): the accounts say $1,200.00 and the records say $1,200.00, the same, within the $12.00 "
         "allowed (0.5%)."),
    Case("reconciliation.heading", "not_matched",  # C4
         heading("NOT_MATCHED", "REVENUE", accounts=usd("0.00", "DECLARED", currency="KES"),
                 recorded=usd("10.00", "RECORDED", currency="KES"), difference=usd("10.00", "DERIVED", currency="KES"),
                 allowed=usd("0.00", "DERIVED", currency="KES"), share=Absent("ACCOUNTS_ZERO"),
                 tolerance=Percent(D("0.01"), Evidence("DECLARED", FIN))),
         "Revenue (Recorded): the accounts say KES 0.00 and the records say KES 10.00, KES 10.00 more, beyond the "
         "KES 0.00 allowed (1%)."),
    Case("reconciliation.heading", "currency_mismatch",  # C5
         heading("CURRENCY_MISMATCH", "FUEL_COST", currency=Name("KES", "statement.currency"),
                 record_currencies=Items((Name("USD", "record.currency"), Name("EUR", "record.currency")))),
         "Fuel cost: the accounts are in KES, but the records are in USD and EUR."),
    Case("reconciliation.heading", "month_open", heading("MONTH_OPEN", "REVENUE", month=Month(2026, 11)),  # C6
         "Revenue: November 2026 is not closed yet."),
    Case("reconciliation.heading", "zero_stated",  # C7
         heading("ZERO_STATED", "FUEL_COST", accounts=usd("0.00", "DECLARED"), records=Word("record_noun", "FUEL_COST")),
         "Fuel cost (Recorded): the accounts say $0.00 and no fuel invoices are recorded."),
    Case("reconciliation.heading", "not_received",  # C8
         heading("NOT_RECEIVED", "REVENUE", accounts=usd("900.00", "DECLARED"), records=Word("record_noun", "REVENUE"),
                 month=Month(2026, 10)),
         "Revenue (Recorded): the accounts say $900.00, but no billing records are recorded for October 2026."),
    Case("reconciliation.heading", "matched",  # C9
         {**C3, "recorded": usd("1200.00", "RECORDED", EMU), "difference": usd("0", "DERIVED", EMU)},
         "Revenue (Recorded and Emulated): the accounts say $1,200.00 and the records say $1,200.00, the same, within "
         "the $12.00 allowed (0.5%)."),
    Case("deep_dive.headline", "share_of_gap", h("-562.00", "-412.00", 3, 3, "OPTIMIZE_COST"),  # H1
         "Contribution is $562.00 below target in October; cost and efficiency explain $412.00 of it.", ["Emulated"]),
    Case("deep_dive.headline", "more_than_gap", h("-562.00", "-700.00", 2, 3, "OPTIMIZE_COST"),  # H2
         "Contribution is $562.00 below target in October; cost and efficiency explain $700.00, more than the whole "
         "gap. Compared for 2 of 3 Sites.", ["Emulated"]),
    Case("deep_dive.headline", "gap_only", h("150.00", None, 1, 1),  # H3
         "Contribution is $150.00 above target in October.", ["Emulated"]),
    Case("deep_dive.headline", "on_target", h("0.00", None, 1, 2),  # H4: the gap is stated by `on_target`'s `when`
         "Contribution is on target in October. Compared for 1 of 2 Sites.", ["Emulated"]),
    Case("deep_dive.headline", "not_available", h(None, None, 0, 3),  # H5
         "Contribution for October is not available yet.", []),
    Case("deep_dive.headline", "share_of_gap", h("80.00", "80.00", 3, 3, "GROW_REVENUE"),  # H6
         "Contribution is $80.00 above target in October; Grow revenue explains $80.00 of it.", ["Emulated"]),
    Case("deep_dive.share", "widens", share("0.3333"), "33% of what widens the gap", ["Emulated"]),  # SH1
    Case("deep_dive.share", "widens", share("0.125"), "12% of what widens the gap", ["Emulated"]),  # SH2 half even
    Case("deep_dive.share", "offsets", share("-0.2"), "Offsets it", ["Emulated"]),  # SH3
    Case("deep_dive.share", "no_effect", share("0"), "No effect", ["Emulated"]),  # SH4
    Case("deep_dive.share", "widens", share("0.004"), "less than 1% of what widens the gap", ["Emulated"]),  # SH5
    Case("deep_dive.status_disagreement", "one", {"sites": names("Kisiwa"), "total": Count(1, "site")},  # SD1
         "Kisiwa's budget disagrees with its own lines."),
    Case("deep_dive.status_disagreement", "few", {"sites": names("Kisiwa", "Mto"), "total": Count(2, "site")},  # SD2
         "The budgets of Kisiwa and Mto disagree with their own lines."),
    Case("deep_dive.status_disagreement", "many",  # SD3
         {"sites": names("Kisiwa", "Mto", "Kobo", "Thika"), "total": Count(4, "site")},
         "The budgets of 4 Sites disagree with their own lines."),
    Case("deep_dive.status_disagreement", "none", {"sites": Absent("NONE"), "total": Absent("NONE")}, ""),  # SD4
    Case("reconciliation.scope", "site", {"scope": State("SITE"), "site": Name("KOBO-001", "site.code")},  # SC1
         "KOBO-001"),
    Case("reconciliation.scope", "organisation",  # SC2
         {"scope": State("ORGANISATION"), "site": Absent("ORGANISATION")}, "the organisation"),
]
