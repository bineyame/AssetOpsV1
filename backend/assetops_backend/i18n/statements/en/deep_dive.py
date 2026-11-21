"""5c (spec section 2.5, as SC-1 statements by D-SC1.14/.26/.28): every sentence of the deep-dive month. Pure literal
data (D-SC1.3). `deep_dive.headline`, `deep_dive.compared`, `deep_dive.share` and `deep_dive.status_disagreement` are
SC-1 spec sections 5.2 and 5.4 exactly. A statement that prints a figure is `served`: the payload carries the
figure's evidence word beside it (the `word` fields, 3A7's `money_word`), or, for the headline, the served list.
"""
STATEMENTS = {
    # SC-1 spec section 5.2, exactly.
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
            {"id": "more_than_gap", "when": {"cmp": [{"abs": "big"}, ">", {"abs": "gap"}]},
             "requires": {"any": [{"all": [{"sign": ["gap", "negative"]}, {"sign": ["big", "negative"]}]},
                                  {"all": [{"sign": ["gap", "positive"]}, {"sign": ["big", "positive"]}]}]},
             "text": "Contribution is {gap} {direction} target in {month}; {subject} {big}, more than the whole gap."
                     "{compared}"},
            {"id": "share_of_gap",
             "requires": {"any": [{"all": [{"sign": ["gap", "negative"]}, {"sign": ["big", "negative"]}]},
                                  {"all": [{"sign": ["gap", "positive"]}, {"sign": ["big", "positive"]}]}]},
             "text": "Contribution is {gap} {direction} target in {month}; {subject} {big} of it.{compared}"},
        ],
    },
    "deep_dive.compared": {
        "evidence": "served",
        "slots": {"sites": {"type": "k_of_n"}},
        "variants": [{"id": "some", "when": {"cmp": ["sites.k", "<", "sites.n"]}, "text": " Compared for {sites}."},
                     {"id": "all", "text": ""}],
    },
    # SC-1 spec section 5.4, exactly.
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
    # Section 2.5 `bridge_title`: the headline's choice, opening with the subject's label form.
    "deep_dive.bridge_title": {
        "evidence": "served",
        "slots": {
            "gap": {"type": "money", "abs": True},
            "big": {"type": "money", "abs": True, "optional": True},
            "subject": {"type": "word", "vocabulary": "headline_subject", "form": "label", "optional": True},
        },
        "variants": [
            {"id": "gap_only", "when": {"absent": "big"},
             "text": "The {gap} gap, by heading. Open a step for what is behind it."},
            {"id": "more_than_gap", "when": {"cmp": [{"abs": "big"}, ">", {"abs": "gap"}]},
             "requires": {"any": [{"all": [{"sign": ["gap", "negative"]}, {"sign": ["big", "negative"]}]},
                                  {"all": [{"sign": ["gap", "positive"]}, {"sign": ["big", "positive"]}]}]},
             "text": "{subject} {big}, more than the whole {gap} gap. Open a step for what is behind it."},
            {"id": "share_of_gap",
             "requires": {"any": [{"all": [{"sign": ["gap", "negative"]}, {"sign": ["big", "negative"]}]},
                                  {"all": [{"sign": ["gap", "positive"]}, {"sign": ["big", "positive"]}]}]},
             "text": "{subject} {big} of the {gap} gap. Open a step for what is behind it."},
        ],
    },
    # A money figure as a value or a cell (PF4: "Not available yet" without a period is this statement's).
    "deep_dive.money": {
        "evidence": "served",
        "slots": {"value": {"type": "money", "absent": ["NOT_AVAILABLE", "NOT_COMPARED"]},
                  "form": {"type": "state", "values": ["PLAIN", "SIGNED", "AT_BUDGET"]}},
        "variants": [
            {"id": "not_available", "when": {"reason": ["value", "NOT_AVAILABLE"]}, "text": "Not available yet"},
            {"id": "not_compared", "when": {"reason": ["value", "NOT_COMPARED"]}, "text": "Not compared"},
            {"id": "plain", "when": {"is": ["form", "PLAIN"]}, "text": "{value}"},
            {"id": "signed", "when": {"is": ["form", "SIGNED"]}, "options": {"value": {"signed": True}},
             "text": "{value}"},
            # D-5C.23: a carried Site's step value names its source.
            {"id": "at_budget", "requires": {"is": ["form", "AT_BUDGET"]}, "options": {"value": {"signed": True}},
             "text": "{value} (at budget)"},
        ],
    },
    # The fixed words of the screen, one variant per piece.
    "deep_dive.text": {
        "slots": {"piece": {"type": "state", "values": [
            "NOT_AVAILABLE", "CONTRIBUTION", "GAP", "GAP_TO_TARGET", "TARGET", "SITE", "PLAN_SPEND", "PLAN_SPEND_LINE",
            "PLAN_VALUE_LINE", "CASH_TITLE", "BILLED", "COLLECTED", "IN_TRANSIT", "OUTSTANDING", "DECISIONS_TITLE",
            "DECISIONS", "ACTIONS_TITLE", "ACTIONS_OFF", "ACTIONS_NONE", "NOT_BUILT", "OPTIMIZE_LINE",
            "PROTECT_LINE", "RECONCILED", "NOT_RECONCILED", "ASSURE_TITLE"]}},
        "variants": [
            {"id": "not_available", "when": {"is": ["piece", "NOT_AVAILABLE"]}, "text": "Not available yet"},
            {"id": "contribution", "when": {"is": ["piece", "CONTRIBUTION"]}, "text": "Contribution"},
            {"id": "gap", "when": {"is": ["piece", "GAP"]}, "text": "Gap"},
            {"id": "gap_to_target", "when": {"is": ["piece", "GAP_TO_TARGET"]}, "text": "Gap to target"},
            {"id": "target", "when": {"is": ["piece", "TARGET"]}, "text": "Target"},
            {"id": "site", "when": {"is": ["piece", "SITE"]}, "text": "Site"},
            {"id": "plan_spend", "when": {"is": ["piece", "PLAN_SPEND"]}, "text": "Plan spend"},
            {"id": "plan_spend_line", "when": {"is": ["piece", "PLAN_SPEND_LINE"]}, "text": "No plan has been made yet"},
            # D-SC1.21: "once" is a number word; "when" is the only wording change (PF5).
            {"id": "plan_value_line", "when": {"is": ["piece", "PLAN_VALUE_LINE"]},
             "text": "Each change is valued against doing nothing when decisions are recorded"},
            {"id": "cash_title", "when": {"is": ["piece", "CASH_TITLE"]},
             "text": "Cash collected, outside the contribution gap"},
            {"id": "billed", "when": {"is": ["piece", "BILLED"]}, "text": "Billed"},
            {"id": "collected", "when": {"is": ["piece", "COLLECTED"]}, "text": "Collected"},
            {"id": "in_transit", "when": {"is": ["piece", "IN_TRANSIT"]}, "text": "In transit"},
            {"id": "outstanding", "when": {"is": ["piece", "OUTSTANDING"]}, "text": "Outstanding"},
            {"id": "decisions_title", "when": {"is": ["piece", "DECISIONS_TITLE"]}, "text": "Decisions"},
            {"id": "decisions", "when": {"is": ["piece", "DECISIONS"]},
             "text": "Not available yet: no decision has been valued against doing nothing."},
            {"id": "actions_title", "when": {"is": ["piece", "ACTIONS_TITLE"]}, "text": "Actions in hand"},
            {"id": "actions_off", "when": {"is": ["piece", "ACTIONS_OFF"]},
             "text": "Not available yet: an agreed change is recorded as an Action with its owner and due date."},
            {"id": "actions_none", "when": {"is": ["piece", "ACTIONS_NONE"]}, "text": "No change has been agreed yet."},
            {"id": "not_built", "when": {"is": ["piece", "NOT_BUILT"]},
             "text": "Not built yet: the value of each change against doing nothing, and the limits, warranties and "
                     "rights under Protect."},
            {"id": "optimize_line", "when": {"is": ["piece", "OPTIMIZE_LINE"]},
             "text": "Fuel, O&M and staff against target; cash collected is shown apart"},
            {"id": "protect_line", "when": {"is": ["piece", "PROTECT_LINE"]},
             "text": "Limits, warranties and rights are not set up yet"},
            {"id": "reconciled", "when": {"is": ["piece", "RECONCILED"]}, "text": "Reconciled"},
            {"id": "not_reconciled", "when": {"is": ["piece", "NOT_RECONCILED"]}, "text": "Not yet reconciled"},
            {"id": "assure_title", "when": {"is": ["piece", "ASSURE_TITLE"]},
             "text": "Reconciliation with the management accounts"},
        ],
        "exhaustive": "piece",
    },
    "deep_dive.label": {
        "slots": {"factor": {"type": "word", "vocabulary": "factor", "form": "label"}},
        "variants": [{"id": "factor", "text": "{factor}"}],
    },
    "deep_dive.heading": {
        "slots": {"heading": {"type": "word", "vocabulary": "heading", "form": "label"}},
        "variants": [{"id": "heading", "text": "{heading}"}],
    },
    "deep_dive.plan_value_label": {
        "slots": {"horizon": {"type": "count"}},
        "variants": [{"id": "label", "text": "Plan value, {horizon}"}],
    },
    "deep_dive.totals_label": {
        "slots": {"month": {"type": "month", "form": "month"}},
        "variants": [{"id": "label", "text": "Contribution, {month}"}],
    },
    "deep_dive.sites": {
        "slots": {"sites": {"type": "k_of_n"}},
        "variants": [{"id": "sites", "text": "{sites}"}],
    },
    "deep_dive.as_of": {
        "slots": {"at": {"type": "instant"}},
        "variants": [{"id": "as_of", "text": "Figures as of {at}."}],
    },
    "deep_dive.standing_short": {
        "slots": {"reconciled": {"type": "flag"}},
        "variants": [{"id": "reconciled", "when": {"is": ["reconciled", True]},
                      "text": "Reconciled with the management accounts."},
                     {"id": "not_reconciled", "text": "Not yet reconciled with the management accounts."}],
    },
    # D-5C.14: the as-of sentence, the standing in a few words, then the budget disagreements by Site.
    "deep_dive.status_line": {
        "slots": {"as_of_words": {"type": "part", "key": "deep_dive.as_of"},
                  "standing_words": {"type": "part", "key": "deep_dive.standing_short"},
                  "disagreement_words": {"type": "part", "key": "deep_dive.status_disagreement"}},
        "variants": [{"id": "agreed", "when": {"absent": "sites"}, "text": "{as_of_words} {standing_words}"},
                     {"id": "disagreements", "text": "{as_of_words} {standing_words} {disagreement_words}"}],
    },
    "deep_dive.tile_target": {
        "evidence": "served",
        "slots": {"target": {"type": "money"},
                  "share": {"type": "percent", "places": 0, "optional": True, "absent": ["TARGET_NOT_POSITIVE"]}},
        "variants": [{"id": "share", "when": {"present": "share"}, "text": "Target {target} · {share} of target"},
                     {"id": "target", "text": "Target {target}"}],
    },
    "deep_dive.cost_received": {
        "evidence": "served",
        "slots": {"share": {"type": "percent", "places": 1}},
        "variants": [{"id": "share", "text": "{share} of cost from figures received"}],
    },
    "deep_dive.tile_split": {
        "evidence": "served",
        "slots": {"grow": {"type": "money", "signed": True}, "optimize": {"type": "money", "signed": True}},
        "variants": [{"id": "split", "text": "Grow {grow} · Optimize {optimize}"}],
    },
    "deep_dive.tile_rest": {
        "evidence": "served",
        "slots": {"rest": {"type": "money", "abs": True}, "gap": {"type": "money"}},
        "variants": [
            {"id": "all_split", "when": {"sign": ["rest", "zero"]}, "text": "All of it split to its drivers"},
            {"id": "widens", "when": {"any": [{"all": [{"sign": ["gap", "negative"]}, {"sign": ["rest", "negative"]}]},
                                              {"all": [{"sign": ["gap", "positive"]}, {"sign": ["rest", "positive"]}]}]},
             "text": "{rest} of it not split to its drivers yet"},
            {"id": "offsets", "requires": {"not": {"sign": ["gap", "zero"]}},
             "text": "{rest} not split to its drivers yet, offsetting the gap"},
        ],
    },
    "deep_dive.disagreement": {
        "evidence": "served",
        "slots": {"site": {"type": "name"},
                  "factor": {"type": "word", "vocabulary": "factor", "form": "in_sentence", "article": True},
                  "stated": {"type": "money"},
                  "computed": {"type": "money", "absent": ["NOT_ADDED"]}},
        "variants": [
            {"id": "open", "when": {"reason": ["computed", "NOT_ADDED"]},
             "text": "{site}'s budget states {factor} of {stated}; its budget lines do not add up to a figure yet, so "
                     "they cannot be compared."},
            {"id": "added", "text": "{site}'s budget states {factor} of {stated}; its budget lines add to {computed}. "
                                    "The target used is {computed}."},
        ],
    },
    "deep_dive.drawer_values": {
        "evidence": "served",
        "slots": {"actual": {"type": "money"}, "target": {"type": "money"},
                  "difference": {"type": "money", "signed": True}},
        "variants": [{"id": "values",
                      "text": "Actual {actual} · Target {target} · Difference {difference}"}],
    },
    "deep_dive.drawer_effect": {
        "evidence": "served",
        "slots": {"effect": {"type": "money", "signed": True}},
        "variants": [{"id": "effect", "text": "Effect on contribution {effect}"}],
    },
    # Section 3.2 a driver's "Actual {a} · Target {t}" by unit.
    "deep_dive.driver_detail": {
        "evidence": "served",
        "slots": {"actual_money": {"type": "money", "optional": True},
                  "target_money": {"type": "money", "optional": True},
                  "actual_quantity": {"type": "quantity", "optional": True},
                  "target_quantity": {"type": "quantity", "optional": True},
                  "actual_price": {"type": "price", "optional": True},
                  "target_price": {"type": "price", "optional": True}},
        "variants": [
            {"id": "quantity", "when": {"all": [{"present": "actual_quantity"}, {"present": "target_quantity"}]},
             "text": "Actual {actual_quantity} · Target {target_quantity}"},
            {"id": "price", "when": {"all": [{"present": "actual_price"}, {"present": "target_price"}]},
             "text": "Actual {actual_price} · Target {target_price}"},
            {"id": "money", "requires": {"all": [{"present": "actual_money"}, {"present": "target_money"}]},
             "text": "Actual {actual_money} · Target {target_money}"},
        ],
    },
    "deep_dive.carried": {
        "slots": {"site": {"type": "name"}, "leaf": {"type": "state", "values": ["OM", "STAFF"]}},
        "variants": [
            {"id": "om", "when": {"is": ["leaf", "OM"]},
             "text": "{site}: no service contractor invoice received; taken at its budget line for the month "
                     "(estimate)."},
            {"id": "staff", "when": {"is": ["leaf", "STAFF"]},
             "text": "{site}: no payroll line received; taken at its budget line for the month (estimate)."},
        ],
        "exhaustive": "leaf",
    },
    "deep_dive.portfolio_line": {
        "evidence": "served",
        "slots": {"value": {"type": "money"},
                  "factor": {"type": "word", "vocabulary": "factor", "form": "in_sentence"}},
        "variants": [{"id": "line", "text": "The organisation's budget also states {value} for {factor} that no Site "
                                            "carries; it is listed, not added."}],
    },
    # Section 2.3 `needs`: the records in `RECORDS` order (all but the last as a comma chain, then the last), then the
    # budget-lines phrase, as one list: "a, b, c and budget lines for x".
    "deep_dive.record_chain": {
        "slots": {"head": {"type": "word", "vocabulary": "record", "form": "in_sentence"},
                  "rest": {"type": "name", "optional": True}},
        "variants": [{"id": "one", "when": {"absent": "rest"}, "text": "{head}"},
                     {"id": "more", "text": "{head}, {rest}"}],
    },
    "deep_dive.needs": {
        "evidence": "served",
        "part_only": True,
        "slots": {"records": {"type": "name", "optional": True},
                  "last": {"type": "word", "vocabulary": "record", "form": "in_sentence", "optional": True},
                  "factors": {"type": "items", "of": {"type": "word", "vocabulary": "factor", "form": "in_sentence"},
                              "order": "vocabulary", "optional": True}},
        "variants": [
            {"id": "last_only", "when": {"all": [{"absent": "factors"}, {"absent": "records"}]},
             "requires": {"present": "last"}, "text": "{last}"},
            {"id": "records_last", "when": {"absent": "factors"}, "requires": {"present": "last"},
             "text": "{records} and {last}"},
            {"id": "budget_one", "when": {"all": [{"absent": "last"}, {"cmp": ["factors.count", "==", {"const": 1}]}]},
             "text": "a budget line for {factors}"},
            {"id": "budget", "when": {"absent": "last"}, "text": "budget lines for {factors}"},
            {"id": "last_one", "when": {"all": [{"absent": "records"}, {"cmp": ["factors.count", "==", {"const": 1}]}]},
             "text": "{last} and a budget line for {factors}"},
            {"id": "last", "when": {"absent": "records"}, "text": "{last} and budget lines for {factors}"},
            {"id": "both_one", "when": {"cmp": ["factors.count", "==", {"const": 1}]},
             "text": "{records}, {last} and a budget line for {factors}"},
            {"id": "both", "text": "{records}, {last} and budget lines for {factors}"},
        ],
    },
    # Section 2.5 stops (D-5C.9): why, then the records that would fill it.
    "deep_dive.stop": {
        "evidence": "served",
        "slots": {"reason": {"type": "state", "values": ["GAP_NOT_AVAILABLE", "DETAIL_NOT_AVAILABLE", "NO_RULE"]},
                  "needs": {"type": "part", "key": "deep_dive.needs"}},
        "variants": [
            {"id": "gap", "when": {"is": ["reason", "GAP_NOT_AVAILABLE"]}, "text": "Not compared until {needs}."},
            {"id": "detail", "when": {"is": ["reason", "DETAIL_NOT_AVAILABLE"]},
             "text": "Not split further until {needs}."},
            {"id": "no_rule", "when": {"is": ["reason", "NO_RULE"]},
             "text": "Not split further: no rule splits it exactly yet."},
        ],
        "exhaustive": "reason",
    },
    "deep_dive.stop_residual": {
        "evidence": "served",
        "slots": {"parent": {"type": "word", "vocabulary": "factor", "form": "in_sentence"},
                  "effect": {"type": "money", "signed": True},
                  "needs": {"type": "part", "key": "deep_dive.needs"}},
        "variants": [{"id": "residual", "text": "The rest of {parent}: {effect}. Not split further until {needs}."}],
    },
    "deep_dive.stop_differ": {
        "evidence": "served",
        "slots": {"side": {"type": "state", "values": ["ACTUAL", "TARGET"]},
                  "stated": {"type": "money"}, "computed": {"type": "money"},
                  "apart": {"type": "money", "abs": True}},
        "variants": [
            {"id": "actual", "when": {"is": ["side", "ACTUAL"]},
             "text": "Not split further: the records state {stated} and its parts add to {computed}, {apart} apart."},
            {"id": "target", "when": {"is": ["side", "TARGET"]},
             "text": "The target's budget line states {stated} and its parts add to {computed}, {apart} apart."},
        ],
        "exhaustive": "side",
    },
    "deep_dive.stop_currency": {
        "slots": {"currencies": {"type": "items", "of": {"type": "name"}, "order": "given"}},
        "variants": [{"id": "currency",
                      "text": "Not compared: the actual and the target are in different currencies ({currencies})."}],
    },
    # Section 2.5 `out`: a Site left out of a figure, named with why.
    "deep_dive.out": {
        "evidence": "served",
        "slots": {"site": {"type": "name"},
                  "reason": {"type": "state", "values": ["NOT_MINI_GRID", "NOT_SPLIT", "NEEDS"]},
                  "needs": {"type": "part", "key": "deep_dive.needs"},
                  "target": {"type": "money", "optional": True}},
        "variants": [
            {"id": "not_mini_grid", "when": {"is": ["reason", "NOT_MINI_GRID"]},
             "text": "{site}: not a mini-grid Site, not included."},
            {"id": "not_split", "when": {"is": ["reason", "NOT_SPLIT"]}, "text": "{site}: not split this far."},
            {"id": "needs_target", "when": {"present": "target"},
             "text": "{site}: not compared until {needs}; its own target is {target}."},
            {"id": "needs", "requires": {"is": ["reason", "NEEDS"]}, "text": "{site}: not compared until {needs}."},
        ],
    },
    "deep_dive.cash": {
        "evidence": "served",
        "slots": {"month": {"type": "month", "form": "month"},
                  "collected": {"type": "money", "absent": ["NOT_AVAILABLE"]},
                  "expected": {"type": "money", "optional": True},
                  "outstanding": {"type": "money", "optional": True},
                  "in_transit": {"type": "money", "optional": True}},
        "variants": [
            {"id": "not_available", "when": {"absent": "collected"},
             "text": "Cash collected in {month} is not available yet."},
            {"id": "cash", "requires": {"all": [{"present": "expected"}, {"present": "outstanding"},
                                                {"present": "in_transit"}]},
             "text": "In {month}, {collected} was collected against {expected} expected; {outstanding} is still "
                     "outstanding and {in_transit} is paid but in transit."},
        ],
    },
    "deep_dive.fresh_records": {
        "part_only": True,
        "slots": {"sites": {"type": "items", "of": {"type": "name"}, "order": "given", "optional": True}},
        "variants": [{"id": "named", "when": {"present": "sites"},
                      "text": "records have arrived since they were prepared for {sites}"},
                     {"id": "unnamed", "text": "records have arrived since they were prepared"}],
    },
    "deep_dive.fresh": {
        "slots": {"records": {"type": "flag"}, "closed": {"type": "flag"}, "rules": {"type": "flag"},
                  "records_words": {"type": "part", "key": "deep_dive.fresh_records"},
                  "at": {"type": "instant"}},
        "variants": [
            {"id": "all", "when": {"all": [{"is": ["records", True]}, {"is": ["closed", True]}, {"is": ["rules", True]}]},
             "text": "These figures are out of date: {records_words}; the month has closed since they were prepared; "
                     "the way they are worked out has changed. They are shown as they were on {at}."},
            {"id": "records_closed", "when": {"all": [{"is": ["records", True]}, {"is": ["closed", True]}]},
             "text": "These figures are out of date: {records_words}; the month has closed since they were prepared. "
                     "They are shown as they were on {at}."},
            {"id": "records_rules", "when": {"all": [{"is": ["records", True]}, {"is": ["rules", True]}]},
             "text": "These figures are out of date: {records_words}; the way they are worked out has changed. They "
                     "are shown as they were on {at}."},
            {"id": "closed_rules", "when": {"all": [{"is": ["closed", True]}, {"is": ["rules", True]}]},
             "text": "These figures are out of date: the month has closed since they were prepared; the way they are "
                     "worked out has changed. They are shown as they were on {at}."},
            {"id": "records", "when": {"is": ["records", True]},
             "text": "These figures are out of date: {records_words}. They are shown as they were on {at}."},
            {"id": "closed", "when": {"is": ["closed", True]},
             "text": "These figures are out of date: the month has closed since they were prepared. They are shown "
                     "as they were on {at}."},
            {"id": "rules", "requires": {"is": ["rules", True]},
             "text": "These figures are out of date: the way they are worked out has changed. They are shown as they "
                     "were on {at}."},
        ],
    },
    "deep_dive.untracked_entry": {
        "slots": {"factor": {"type": "word", "vocabulary": "factor", "form": "label"},
                  "sites": {"type": "items", "of": {"type": "name"}, "order": "given"}},
        "variants": [{"id": "entry", "text": "{factor} ({sites})"}],
    },
    "deep_dive.untracked": {
        "slots": {"entries": {"type": "items", "of": {"type": "name"}, "order": "given"}},
        "variants": [{"id": "untracked", "text": "Not checked for later changes: {entries}."}],
    },
    "deep_dive.month_words": {
        "slots": {"month": {"type": "month"}},
        "variants": [{"id": "month", "text": "{month}"}],
    },
    "deep_dive.no_snapshot": {
        "slots": {"month": {"type": "month"}},
        "variants": [{"id": "no_snapshot", "text": "The figures for {month} have not been prepared yet."}],
    },
    "deep_dive.rebuild": {
        "slots": {"month": {"type": "month"}},
        "variants": [{"id": "rebuild", "text": "The figures for {month} must be prepared again before they can be "
                                               "shown."}],
    },
    # Section 2.5 `errors` (unit 2, spec section 4.2): the route's refusals; PF5's example slot for the month.
    "deep_dive.refused": {
        "slots": {"code": {"type": "state", "values": ["BAD_MONTH", "DEEP_DIVE_UNAVAILABLE"]},
                  "month_example": {"type": "example", "text": "2026-10"}},
        "variants": [{"id": "bad_month", "when": {"is": ["code", "BAD_MONTH"]},
                      "text": "Write the month as YYYY-MM, like {month_example}."},
                     {"id": "unavailable", "text": "The month's figures cannot be read right now."}],
    },
    "deep_dive.action_owner": {
        "slots": {"owner": {"type": "name"}, "due": {"type": "day"}},
        "variants": [{"id": "owner", "text": "Owner {owner} · due {due}"}],
    },
    "deep_dive.action_agreed": {
        "slots": {"by": {"type": "name"}, "on": {"type": "day"}},
        "variants": [{"id": "agreed", "text": "Agreed by {by} on {on}"}],
    },
    "deep_dive.grow_line": {
        "slots": {"sites": {"type": "k_of_n"}},
        "variants": [{"id": "line", "text": "Revenue against target, {sites}"}],
    },
    "deep_dive.assure_line": {
        "evidence": "served",
        "slots": {"disagreements": {"type": "count"},
                  "cost": {"type": "percent", "places": 1, "optional": True}},
        "variants": [
            {"id": "none_cost", "when": {"all": [{"cmp": ["disagreements", "==", {"const": 0}]}, {"present": "cost"}]},
             "text": "No budget disagreement · {cost} of cost from figures received"},
            {"id": "none", "when": {"cmp": ["disagreements", "==", {"const": 0}]}, "text": "No budget disagreement"},
            {"id": "some_cost", "when": {"present": "cost"},
             "text": "{disagreements} · {cost} of cost from figures received"},
            {"id": "some", "text": "{disagreements}"},
        ],
    },
    "deep_dive.fills": {
        "slots": {"factors": {"type": "items", "of": {"type": "word", "vocabulary": "factor", "form": "label"},
                              "order": "vocabulary"},
                  "carried": {"type": "flag"}},
        "variants": [{"id": "carried", "when": {"is": ["carried", True]},
                      "text": "{factors} (taken at its budget line meanwhile)"},
                     {"id": "fills", "text": "{factors}"}],
    },
    "deep_dive.needs_row": {
        "evidence": "served",
        "slots": {"needs": {"type": "part", "key": "deep_dive.needs"}},
        "variants": [{"id": "needs", "text": "{needs}"}],
    },
    "deep_dive.names": {
        "slots": {"sites": {"type": "items", "of": {"type": "name"}, "order": "given"}},
        "variants": [{"id": "names", "text": "{sites}"}],
    },
    # Finished sentences one after another (a drawer cell): folded from the right, so any number joins.
    "deep_dive.sentences": {
        "slots": {"head": {"type": "name"}, "rest": {"type": "name", "optional": True}},
        "variants": [{"id": "one", "when": {"absent": "rest"}, "text": "{head}"},
                     {"id": "more", "text": "{head} {rest}"}],
    },
}
