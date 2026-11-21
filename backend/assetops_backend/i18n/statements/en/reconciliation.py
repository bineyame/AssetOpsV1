"""3A7 (spec `specs/3A7-month-reconciled/spec.md` section 2.7; rulings "Amendment (SC-1)"; SC-1 spec sections 5.1 and
5.4): one closed month reconciled, as statements. The heading, gap, share and scope statements are SC-1 section 5.1
and 5.4 exactly. Pure literal data (D-SC1.3)."""
STATEMENTS = {
    "reconciliation.heading": {
        "slots": {
            "state": {"type": "state", "values": ["MATCHED", "NOT_MATCHED", "ZERO_STATED", "NOT_RECEIVED",
                                                  "CURRENCY_MISMATCH", "MONTH_OPEN"]},
            "heading": {"type": "word", "vocabulary": "heading", "form": "label"},
            "records": {"type": "word", "vocabulary": "record_noun", "form": "in_sentence", "optional": True},
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
    "reconciliation.scope": {
        "slots": {"scope": {"type": "state", "values": ["SITE", "ORGANISATION"]},
                  "site": {"type": "name", "absent": ["ORGANISATION"]}},
        "variants": [{"id": "site", "when": {"is": ["scope", "SITE"]}, "text": "{site}"},
                     {"id": "organisation", "when": {"is": ["scope", "ORGANISATION"]},
                      "requires": {"reason": ["site", "ORGANISATION"]}, "text": "the organisation"}],
        "exhaustive": "scope",
    },
    # Spec section 2.7's `reconciliation.statement.*`: one statement's live check.
    "reconciliation.statement": {
        "slots": {
            "state": {"type": "state", "values": ["MATCHED", "NOT_MATCHED", "NOT_COMPARABLE"]},
            "month": {"type": "month"},
            "scope_words": {"type": "part", "key": "reconciliation.scope"},
            "tolerance": {"type": "percent", "places": "normal", "evidence": "inline"},
        },
        "variants": [
            {"id": "matched", "when": {"is": ["state", "MATCHED"]},
             "text": "{month} ({scope_words}) matches the management accounts within {tolerance}."},
            {"id": "not_matched", "when": {"is": ["state", "NOT_MATCHED"]},
             "text": "{month} ({scope_words}) does not match the management accounts within {tolerance}."},
            {"id": "not_comparable", "when": {"is": ["state", "NOT_COMPARABLE"]},
             "text": "{month} ({scope_words}) cannot be compared with the management accounts yet."},
        ],
        "exhaustive": "state",
    },
    # Spec section 2.7's `reconciliation.standing.*`: whether money of a Site-month reads reconciled (section 2.3).
    "reconciliation.standing": {
        "slots": {
            "reason": {"type": "state", "values": ["RECONCILED", "THIS_MONTH_NOT_MATCHED", "THIS_MONTH_NOT_COMPARABLE",
                                                   "NO_STATEMENT", "NONE_MATCHED"]},
            "month": {"type": "month", "optional": True},
            "scope_words": {"type": "part", "key": "reconciliation.scope"},
            "tolerance": {"type": "percent", "places": "normal", "evidence": "inline"},
        },
        "variants": [
            {"id": "reconciled", "when": {"is": ["reason", "RECONCILED"]}, "requires": {"present": "month"},
             "text": "Reconciled: {month} ({scope_words}) matches the management accounts within {tolerance}."},
            {"id": "this_month_not_matched", "when": {"is": ["reason", "THIS_MONTH_NOT_MATCHED"]},
             "requires": {"present": "month"},
             "text": "Not yet reconciled: {month} ({scope_words}) does not match the management accounts within "
                     "{tolerance}."},
            {"id": "this_month_not_comparable", "when": {"is": ["reason", "THIS_MONTH_NOT_COMPARABLE"]},
             "requires": {"present": "month"},
             "text": "Not yet reconciled: {month} ({scope_words}) cannot be compared with the management accounts "
                     "yet."},
            {"id": "no_statement", "when": {"is": ["reason", "NO_STATEMENT"]},
             "text": "Not yet reconciled: no closed month has been compared with the management accounts."},
            {"id": "none_matched", "when": {"is": ["reason", "NONE_MATCHED"]},
             "text": "Not yet reconciled: no month's recorded revenue and fuel cost match the management accounts "
                     "within {tolerance} yet."},
        ],
        "exhaustive": "reason",
    },
    # Spec section 2.3's `money_word` (D-SC1.16): the figure's own evidence word, with the money suffix while money of
    # its Site-month is not yet reconciled. The figure is not printed; its evidence is.
    "reconciliation.money_word": {
        "slots": {"figure": {"type": "money", "evidence": {"with": "word"}},
                  "word": {"type": "evidence", "of": ["figure"], "money": True}},
        "variants": [{"id": "word", "text": "{word}"}],
    },
    # Spec section 2.5's refusals of a statement (`reconciliation.refused.<code lower>`), one variant per code.
    "reconciliation.refused": {
        "slots": {
            "code": {"type": "state", "values": ["RECON_ROLE", "RECON_PERIOD", "RECON_SITE_UNKNOWN", "RECON_SITE_TYPE",
                                                 "RECON_CURRENCY", "RECON_AMOUNT", "RECON_SOURCE_REF",
                                                 "RECON_MONTH_OPEN"]},
            "site": {"type": "name", "optional": True},
            "heading": {"type": "word", "vocabulary": "heading", "form": "in_sentence", "optional": True},
            "month": {"type": "month", "optional": True},
            "limit": {"type": "count", "optional": True},
            "period_example": {"type": "example", "text": "2026-10"},
            "currency_example": {"type": "example", "text": "USD"},
            "amount_example": {"type": "example", "text": "1200.00"},
        },
        "variants": [
            {"id": "role", "when": {"is": ["code", "RECON_ROLE"]},
             "text": "Only the finance lead records the management accounts."},
            {"id": "period", "when": {"is": ["code", "RECON_PERIOD"]},
             "text": "Write the month as YYYY-MM, like {period_example}."},
            {"id": "site_unknown", "when": {"all": [{"is": ["code", "RECON_SITE_UNKNOWN"]}, {"present": "site"}]},
             "text": "This Site is not this organisation's: {site}."},
            {"id": "no_mini_grid", "when": {"is": ["code", "RECON_SITE_UNKNOWN"]},
             "text": "This organisation has no mini-grid Site to compare with the management accounts."},
            {"id": "site_type", "when": {"is": ["code", "RECON_SITE_TYPE"]}, "requires": {"present": "site"},
             "text": "Only mini-grid Sites are compared with the management accounts for now: {site}."},
            {"id": "currency", "when": {"is": ["code", "RECON_CURRENCY"]},
             "text": "Write the currency as its code in capital letters, like {currency_example}."},
            {"id": "amount", "when": {"is": ["code", "RECON_AMOUNT"]}, "requires": {"present": "heading"},
             "text": "Write the {heading} as digits with a decimal point and no separators, like {amount_example}."},
            {"id": "source_ref", "when": {"is": ["code", "RECON_SOURCE_REF"]}, "requires": {"present": "limit"},
             "text": "Say where the figures come from, in at most {limit}."},
            {"id": "month_open", "requires": {"all": [{"is": ["code", "RECON_MONTH_OPEN"]}, {"present": "month"}]},
             "text": "{month} is not closed yet: record a closed month."},
        ],
    },
}
