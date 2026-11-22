"""IA-P P3a (`spec-period.md` P.4 to P.6; D-IAP.16, D-IAP.17, D-IAP.25, D-IAP.28): E2's words, the Overview on the
date range.

Pure literal data (D-SC1.3). A month name is rendered by `portfolio_period.month` (alone when every month a sentence
names is in one year, with its year otherwise) and reaches the other statements as a name, joined by the list form.
"""
STATEMENTS = {
    "portfolio_period.month": {
        "slots": {"month": {"type": "month", "form": "month"},
                  "years": {"type": "state", "values": ["ONE", "SEVERAL"]}},
        "variants": [
            {"id": "one_year", "when": {"is": ["years", "ONE"]}, "text": "{month}"},
            {"id": "years", "options": {"month": {"form": "month_year"}}, "text": "{month}"},
        ],
        "rephrase": "never",
    },
    "portfolio_period.span": {
        "slots": {"first": {"type": "name"},
                  "last": {"type": "name", "absent": ["ONE"]},
                  "count": {"type": "state", "values": ["ONE", "TWO", "MORE"]}},
        "variants": [
            {"id": "one", "when": {"is": ["count", "ONE"]}, "text": "{first}"},
            {"id": "two", "when": {"is": ["count", "TWO"]}, "requires": {"present": "last"},
             "text": "{first} and {last}"},
            {"id": "more", "requires": {"present": "last"}, "text": "{first} to {last}"},
        ],
        "rephrase": "never",
    },
    "portfolio_period.headline": {
        "evidence": "served",
        "slots": {
            "gap": {"type": "money", "abs": True, "optional": True},
            "big": {"type": "money", "abs": True, "optional": True},
            "subject": {"type": "word", "vocabulary": "headline_subject", "form": "in_sentence", "optional": True},
            "period": {"type": "name"},
            "sites": {"type": "k_of_n"},
            "fewer": {"type": "state", "values": ["YES", "NO"]},
            "direction": {"type": "pick", "on": {"sign": "gap"}, "domain": ["negative", "positive"],
                          "words": {"negative": "below", "positive": "above"}},
            "compared": {"type": "part", "key": "portfolio_period.compared"},
        },
        "variants": [
            {"id": "not_available", "when": {"absent": "gap"},
             "text": "Contribution across {period} is not available yet."},
            {"id": "on_target", "when": {"sign": ["gap", "zero"]},
             "text": "Contribution is on target across {period}.{compared}"},
            {"id": "gap_only", "when": {"absent": "big"},
             "text": "Contribution is {gap} {direction} target across {period}.{compared}"},
            {"id": "more_than_gap", "when": {"cmp": [{"abs": "big"}, ">", {"abs": "gap"}]},
             "requires": {"any": [{"all": [{"sign": ["gap", "negative"]}, {"sign": ["big", "negative"]}]},
                                  {"all": [{"sign": ["gap", "positive"]}, {"sign": ["big", "positive"]}]}]},
             "text": "Contribution is {gap} {direction} target across {period}; {subject} {big}, more than the whole "
                     "gap.{compared}"},
            {"id": "share_of_gap",
             "requires": {"any": [{"all": [{"sign": ["gap", "negative"]}, {"sign": ["big", "negative"]}]},
                                  {"all": [{"sign": ["gap", "positive"]}, {"sign": ["big", "positive"]}]}]},
             "text": "Contribution is {gap} {direction} target across {period}; {subject} {big} of it.{compared}"},
        ],
        "rephrase": "never",
    },
    # D-IAP.25: appended when any served month compares fewer Sites than it asks; `sites` is the latest month's.
    "portfolio_period.compared": {
        "evidence": "served",
        "slots": {"sites": {"type": "k_of_n"}, "fewer": {"type": "state", "values": ["YES", "NO"]}},
        "variants": [{"id": "some", "when": {"is": ["fewer", "YES"]}, "text": " Compared for {sites}."},
                     {"id": "all", "text": ""}],
    },
    "portfolio_period.missing": {
        "slots": {"months": {"type": "items", "of": {"type": "name"}, "order": "given"},
                  "number": {"type": "state", "values": ["ONE", "SEVERAL"]}},
        "variants": [
            {"id": "one", "when": {"is": ["number", "ONE"]},
             "text": "No figures are served for {months}, so it is not in these figures."},
            {"id": "several", "text": "No figures are served for {months}, so they are not in these figures."},
        ],
        "rephrase": "never",
    },
    "portfolio_period.partial": {
        "slots": {"months": {"type": "items", "of": {"type": "name"}, "order": "given"},
                  "number": {"type": "state", "values": ["ONE", "SEVERAL"]}},
        "variants": [
            {"id": "one", "when": {"is": ["number", "ONE"]},
             "text": "{months} is only partly in this range, so it is not counted: the figures are kept by whole "
                     "month."},
            {"id": "several",
             "text": "{months} are only partly in this range, so they are not counted: the figures are kept by whole "
                     "month."},
        ],
        "rephrase": "never",
    },
    "portfolio_period.open": {
        "slots": {"months": {"type": "items", "of": {"type": "name"}, "order": "given"},
                  "number": {"type": "state", "values": ["ONE", "SEVERAL"]}},
        "variants": [
            {"id": "one", "when": {"is": ["number", "ONE"]}, "text": "{months} has not closed yet, so it has no figures."},
            {"id": "several", "text": "{months} have not closed yet, so they have no figures."},
        ],
        "rephrase": "never",
    },
    "portfolio_period.none": {
        "variants": [{"id": "none", "text": "This range holds no whole month with figures. Contribution against target "
                                            "is kept by whole calendar month."}],
        "rephrase": "never",
    },
    "portfolio_period.suggest": {
        "slots": {"month": {"type": "month"}},
        "variants": [{"id": "suggest", "text": "Show {month}"}],
        "rephrase": "never",
    },
    "portfolio_period.currencies": {
        "variants": [{"id": "currencies", "text": "The months are in different currencies, so they are not added."}],
        "rephrase": "never",
    },
    "portfolio_period.fresh": {
        "slots": {"months": {"type": "items", "of": {"type": "name"}, "order": "given"}},
        "variants": [{"id": "fresh",
                      "text": "Some months' figures are out of date: {months}. Open a month for what changed."}],
        "rephrase": "never",
    },
    # D-IAP.34: a Site out in some served months but not all; `line` is 5c's own `out` sentence.
    "portfolio_period.out_only": {
        "slots": {"line": {"type": "name"}, "months": {"type": "items", "of": {"type": "name"}, "order": "given"}},
        "variants": [{"id": "only", "text": "{line} Only in {months}."}],
        "rephrase": "never",
    },
    "portfolio_period.grow_line": {
        "slots": {"count": {"type": "count"}},
        "variants": [{"id": "grow", "text": "Revenue against target, over {count}"}],
        "rephrase": "never",
    },
    "portfolio_period.assure_line": {
        "slots": {"months": {"type": "k_of_n"}},
        "variants": [{"id": "assure", "text": "{months} reconciled"}],
        "rephrase": "never",
    },
    # P.5's assure drawer line, "{month_words}: {standing_m.text}" (the standing's text is 3A7's own statement).
    "portfolio_period.assure_entry": {
        "slots": {"month": {"type": "month"}, "standing": {"type": "name"}},
        "variants": [{"id": "entry", "text": "{month}: {standing}"}],
        "rephrase": "never",
    },
    "portfolio_period.text": {
        "slots": {"piece": {"type": "state", "values": ["MONTHS_TITLE", "MONTH", "DRIVER"]}},
        "variants": [
            {"id": "months_title", "when": {"is": ["piece", "MONTHS_TITLE"]}, "text": "Month by month"},
            {"id": "month", "when": {"is": ["piece", "MONTH"]}, "text": "Month"},
            {"id": "driver", "text": "Largest driver against target"},
        ],
        "rephrase": "never",
    },
    "portfolio_period.refused": {
        "slots": {"code": {"type": "state", "values": ["BAD_RANGE", "RANGE_TOO_LONG"]},
                  "days": {"type": "example", "text": "two"},
                  "order": {"type": "example", "text": "the first not after the last"},
                  "cap": {"type": "count", "optional": True}},
        "variants": [
            {"id": "bad_range", "when": {"is": ["code", "BAD_RANGE"]},
             "text": "Write the range as {days} days, YYYY-MM-DD, {order}."},
            {"id": "too_long", "text": "The month figures cover at most {cap}. Narrow the date range."},
        ],
        "rephrase": "never",
    },
}
