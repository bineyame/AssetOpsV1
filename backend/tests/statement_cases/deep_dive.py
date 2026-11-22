"""5c (spec sections 2.5 and 3.5, D-SC1.28): a hand-written case per variant of every statement in
`i18n/statements/en/deep_dive.py` that `worked.py` does not already cover (the headline, its compared part, share and
status_disagreement are `worked.py`'s H1-H6, SH1-SH5, SD1-SD4). `deep_dive.needs` and `deep_dive.fresh_records` are
parts, covered through the statements that carry them. Every English literal is written by hand (W2).
"""
from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal as D

from assetops_backend.i18n import (Absent, Count, Day, Evidence, Flag, Instant, Items, KOfN, Money, Month, Name,
                                   Percent, Price, Quantity, State, Word)

from statement_cases import Case

EMU = "source-emulated"
EV = ["Emulated"]
AT = Instant(datetime(2026, 11, 19, 11, 0, tzinfo=timezone.utc))
OCT = Month(2026, 10)


def usd(value: str) -> Money:
    return Money(D(value), "USD", Evidence("DERIVED", EMU))


def pct(value: str) -> Percent:
    return Percent(D(value), Evidence("DERIVED", EMU))


def text(piece: str) -> dict:
    return {"piece": State(piece)}


def chain(text: str) -> Name:
    """The comma list of all but the last record (`deep_dive.record_chain`), as its finished text."""
    return Name(text, "deep_dive.record_chain")


def last(key: str) -> Word:
    return Word("record", key)


def factors(*ids: str) -> Items:
    return Items(tuple(Word("factor", f) for f in ids))


def names(*texts: str) -> Items:
    return Items(tuple(Name(t, "site.name") for t in texts))


def stop(reason: str, **needs) -> dict:
    return {"reason": State(reason), **needs}


TEXTS = [
    ("not_available", "NOT_AVAILABLE", "Not available yet"), ("contribution", "CONTRIBUTION", "Contribution"),
    ("gap", "GAP", "Gap"), ("gap_to_target", "GAP_TO_TARGET", "Gap to target"), ("target", "TARGET", "Target"),
    ("site", "SITE", "Site"), ("plan_spend", "PLAN_SPEND", "Plan spend"),
    ("plan_spend_line", "PLAN_SPEND_LINE", "No plan has been made yet"),
    ("plan_value_line", "PLAN_VALUE_LINE", "Each change is valued against doing nothing when decisions are recorded"),
    ("cash_title", "CASH_TITLE", "Cash collected, outside the contribution gap"),
    ("billed", "BILLED", "Billed"), ("collected", "COLLECTED", "Collected"), ("in_transit", "IN_TRANSIT", "In transit"),
    ("outstanding", "OUTSTANDING", "Outstanding"), ("decisions_title", "DECISIONS_TITLE", "Decisions"),
    ("decisions", "DECISIONS", "Not available yet: no decision has been valued against doing nothing."),
    ("actions_title", "ACTIONS_TITLE", "Actions in hand"),
    ("actions_off", "ACTIONS_OFF",
     "Not available yet: an agreed change is recorded as an Action with its owner and due date."),
    ("actions_none", "ACTIONS_NONE", "No change has been agreed yet."),
    ("not_built", "NOT_BUILT", "Not built yet: the value of each change against doing nothing, and the limits, "
                               "warranties and rights under Protect."),
    ("optimize_line", "OPTIMIZE_LINE", "Fuel, O&M and staff against target; cash collected is shown apart"),
    ("protect_line", "PROTECT_LINE", "Limits, warranties and rights are not set up yet"),
    ("reconciled", "RECONCILED", "Reconciled"), ("not_reconciled", "NOT_RECONCILED", "Not yet reconciled"),
    ("assure_title", "ASSURE_TITLE", "Reconciliation with the management accounts"),
]

CASES = [Case("deep_dive.text", variant, text(piece), english) for variant, piece, english in TEXTS] + [
    Case("deep_dive.label", "factor", {"factor": Word("factor", "unexplained_loss_kwh")}, "Unexplained losses"),
    Case("deep_dive.heading", "heading", {"heading": Word("heading", "ASSURE_PERFORMANCE")},
         "Assure performance and returns"),
    Case("deep_dive.plan_value_label", "label", {"horizon": Count(12, "month")}, "Plan value, 12 months"),
    Case("deep_dive.totals_label", "label", {"month": OCT}, "Contribution, October"),
    Case("deep_dive.sites", "sites", {"sites": KOfN(2, 3, "site")}, "2 of 3 Sites"),
    Case("deep_dive.as_of", "as_of", {"at": AT}, "Figures as of 19 November 2026, 11:00 UTC."),
    Case("deep_dive.standing_short", "reconciled", {"reconciled": Flag(True)},
         "Reconciled with the management accounts."),
    Case("deep_dive.standing_short", "not_reconciled", {"reconciled": Flag(False)},
         "Not yet reconciled with the management accounts."),
    Case("deep_dive.status_line", "agreed",
         {"at": AT, "reconciled": Flag(True), "sites": Absent("NONE"), "total": Absent("NONE")},
         "Figures as of 19 November 2026, 11:00 UTC. Reconciled with the management accounts."),
    Case("deep_dive.status_line", "disagreements",
         {"at": AT, "reconciled": Flag(False), "sites": names("Kisiwa"), "total": Count(1, "site")},
         "Figures as of 19 November 2026, 11:00 UTC. Not yet reconciled with the management accounts. "
         "Kisiwa's budget disagrees with its own lines."),
    Case("deep_dive.tile_target", "share", {"target": usd("2295.00"), "share": pct("0.6288")},
         "Target $2,295.00 · 63% of target", EV),
    Case("deep_dive.tile_target", "target", {"target": usd("0.00"), "share": Absent("TARGET_NOT_POSITIVE")},
         "Target $0.00", EV),
    Case("deep_dive.cost_received", "share", {"share": pct("0.9151")}, "91.5% of cost from figures received", EV),
    Case("deep_dive.tile_split", "split", {"grow": usd("-80.00"), "optimize": usd("-482.00")},
         "Grow −$80.00 · Optimize −$482.00", EV),
    Case("deep_dive.tile_rest", "all_split", {"rest": usd("0.00"), "gap": usd("-562.00")},
         "All of it split to its drivers", EV),
    Case("deep_dive.tile_rest", "widens", {"rest": usd("-100.00"), "gap": usd("-562.00")},
         "$100.00 of it not split to its drivers yet", EV),
    Case("deep_dive.tile_rest", "offsets", {"rest": usd("40.00"), "gap": usd("-562.00")},
         "$40.00 not split to its drivers yet, offsetting the gap", EV),
    Case("deep_dive.disagreement", "open",
         {"site": Name("Kisiwa", "site.name"), "factor": Word("factor", "om"), "stated": usd("300.00"),
          "computed": Absent("NOT_ADDED")},
         "Kisiwa's budget states an O&M of $300.00; its budget lines do not add up to a figure yet, so they cannot "
         "be compared.", EV),
    Case("deep_dive.disagreement", "added",
         {"site": Name("Kisiwa", "site.name"), "factor": Word("factor", "om"), "stated": usd("300.00"),
          "computed": usd("280.00")},
         "Kisiwa's budget states an O&M of $300.00; its budget lines add to $280.00. The target used is $280.00.", EV),
    Case("deep_dive.drawer_values", "values",
         {"actual": usd("1443.00"), "target": usd("2295.00"), "difference": usd("-852.00")},
         "Actual $1,443.00 · Target $2,295.00 · Difference −$852.00", EV),
    Case("deep_dive.drawer_effect", "effect", {"effect": usd("-852.00")}, "Effect on contribution −$852.00", EV),
    Case("deep_dive.driver_detail", "quantity",
         {"actual_quantity": Quantity(D("730"), "L", Evidence("DERIVED", EMU)),
          "target_quantity": Quantity(D("700"), "L", Evidence("DERIVED", EMU))},
         "Actual 730 L · Target 700 L", EV),
    Case("deep_dive.driver_detail", "price",
         {"actual_price": Price(D("1.40"), "USD", "L", Evidence("DERIVED", EMU)),
          "target_price": Price(D("1.30"), "USD", "L", Evidence("DERIVED", EMU))},
         "Actual $1.40 per L · Target $1.30 per L", EV),
    Case("deep_dive.driver_detail", "money", {"actual_money": usd("1020.00"), "target_money": usd("910.00")},
         "Actual $1,020.00 · Target $910.00", EV),
    Case("deep_dive.carried", "om", {"site": Name("Kisiwa", "site.name"), "leaf": State("OM")},
         "Kisiwa: no service contractor invoice received; taken at its budget line for the month (estimate)."),
    Case("deep_dive.carried", "staff", {"site": Name("Kisiwa", "site.name"), "leaf": State("STAFF")},
         "Kisiwa: no payroll line received; taken at its budget line for the month (estimate)."),
    Case("deep_dive.portfolio_line", "line", {"value": usd("120.00"), "factor": Word("factor", "staff")},
         "The organisation's budget also states $120.00 for staff that no Site carries; it is listed, not added.", EV),
    # deep_dive.needs variants, through the stops that carry it.
    Case("deep_dive.record_chain", "one", {"head": Word("record", "BILLING")},
         "the billing export with each line's kWh and tariff"),
    Case("deep_dive.record_chain", "more",
         {"head": Word("record", "BILLING"), "rest": Name("a feeder meter export", "deep_dive.record_chain")},
         "the billing export with each line's kWh and tariff, a feeder meter export"),
    Case("deep_dive.stop", "gap", stop("GAP_NOT_AVAILABLE", records=chain("the billing export"), last=last("FEEDER_METER")),
         "Not compared until the billing export and a feeder meter export.", []),
    Case("deep_dive.stop", "detail", stop("DETAIL_NOT_AVAILABLE", factors=factors("om")),
         "Not split further until a budget line for O&M.", []),
    Case("deep_dive.stop", "detail", stop("DETAIL_NOT_AVAILABLE", factors=factors("om", "staff")),
         "Not split further until budget lines for O&M and staff.", []),
    Case("deep_dive.stop", "detail",
         stop("DETAIL_NOT_AVAILABLE", last=Word("record", "OM_INVOICES"), factors=factors("staff")),
         "Not split further until the service contractor's invoices and a budget line for staff.", []),
    Case("deep_dive.stop", "detail",
         stop("DETAIL_NOT_AVAILABLE", last=Word("record", "OM_INVOICES"), factors=factors("om", "staff")),
         "Not split further until the service contractor's invoices and budget lines for O&M and staff.", []),
    Case("deep_dive.stop", "detail",
         stop("DETAIL_NOT_AVAILABLE", records=chain("the billing export"), last=last("PAYROLL"),
              factors=factors("staff")),
         "Not split further until the billing export, payroll lines and a budget line for staff.", []),
    Case("deep_dive.stop", "detail",
         stop("DETAIL_NOT_AVAILABLE", records=chain("the billing export, a feeder meter export"), last=last("PAYROLL"),
              factors=factors("om", "staff")),
         "Not split further until the billing export, a feeder meter export, payroll lines and budget lines for O&M "
         "and staff.", []),
    Case("deep_dive.stop", "no_rule", stop("NO_RULE"), "Not split further: no rule splits it exactly yet.", []),
    Case("deep_dive.stop_residual", "residual",
         {"parent": Word("factor", "cost_to_serve"), "effect": usd("-30.00"), "last": last("PAYROLL")},
         "The rest of cost to serve: −$30.00. Not split further until payroll lines.", EV),
    Case("deep_dive.stop_differ", "actual",
         {"side": State("ACTUAL"), "stated": usd("5100.00"), "computed": usd("4995.00"), "apart": usd("105.00")},
         "Not split further: the records state $5,100.00 and its parts add to $4,995.00, $105.00 apart.", EV),
    Case("deep_dive.stop_differ", "target",
         {"side": State("TARGET"), "stated": usd("5100.00"), "computed": usd("4995.00"), "apart": usd("105.00")},
         "The target's budget line states $5,100.00 and its parts add to $4,995.00, $105.00 apart.", EV),
    Case("deep_dive.stop_currency", "currency", {"currencies": Items((Name("KES", "row.currency"),
                                                                       Name("USD", "row.currency")))},
         "Not compared: the actual and the target are in different currencies (KES and USD)."),
    Case("deep_dive.out", "not_mini_grid",
         {"site": Name("Thika", "site.name"), "reason": State("NOT_MINI_GRID")},
         "Thika: not a mini-grid Site, not included.", []),
    Case("deep_dive.out", "currency_mismatch",
         {"site": Name("Mto", "site.name"), "reason": State("CURRENCY_MISMATCH"),
          "currency": Items((Name("KES", "row.currency"), Name("USD", "row.currency")))},
         "Mto: not compared: its actual and its target are in different currencies (KES and USD).", []),
    Case("deep_dive.out", "not_split", {"site": Name("Mto", "site.name"), "reason": State("NOT_SPLIT")},
         "Mto: not split this far.", []),
    Case("deep_dive.out", "needs_target",
         {"site": Name("Mto", "site.name"), "reason": State("NEEDS"), "last": last("BILLING"),
          "target": usd("2000.00")},
         "Mto: not compared until the billing export with each line's kWh and tariff; its own target is $2,000.00.", EV),
    Case("deep_dive.out", "needs",
         {"site": Name("Mto", "site.name"), "reason": State("NEEDS"), "last": last("BILLING")},
         "Mto: not compared until the billing export with each line's kWh and tariff.", []),
    Case("deep_dive.needs_row", "needs", {"records": chain("the billing export"), "last": last("METER_READS")},
         "the billing export and the customer meter reads for the month", []),
    Case("deep_dive.cash", "not_available", {"month": OCT, "collected": Absent("NOT_AVAILABLE")},
         "Cash collected in October is not available yet.", []),
    Case("deep_dive.cash", "cash",
         {"month": OCT, "collected": usd("9000.00"), "billed": usd("9700.00"), "in_transit": usd("200.00"),
          "outstanding": usd("500.00")},
         "Of $9,700.00 billed for October, $9,000.00 has been collected, $200.00 is paid but in transit and "
         "$500.00 is still outstanding.", EV),
    Case("deep_dive.cash", "collected_only", {"month": OCT, "collected": usd("9000.00")},
         "$9,000.00 has been collected on the bills for October; the amounts billed, in transit and still "
         "outstanding are not available for the same Sites yet.", EV),
    Case("deep_dive.fresh", "all",
         {"records": Flag(True), "closed": Flag(True), "rules": Flag(True), "at": AT, "sites": names("Kisiwa")},
         "These figures are out of date: records have arrived since they were prepared for Kisiwa; the month has "
         "closed since they were prepared; the way they are worked out has changed. They are shown as they were on "
         "19 November 2026, 11:00 UTC."),
    Case("deep_dive.fresh", "records_closed",
         {"records": Flag(True), "closed": Flag(True), "rules": Flag(False), "at": AT},
         "These figures are out of date: records have arrived since they were prepared; the month has closed since "
         "they were prepared. They are shown as they were on 19 November 2026, 11:00 UTC."),
    Case("deep_dive.fresh", "records_rules",
         {"records": Flag(True), "closed": Flag(False), "rules": Flag(True), "at": AT},
         "These figures are out of date: records have arrived since they were prepared; the way they are worked out "
         "has changed. They are shown as they were on 19 November 2026, 11:00 UTC."),
    Case("deep_dive.fresh", "closed_rules",
         {"records": Flag(False), "closed": Flag(True), "rules": Flag(True), "at": AT},
         "These figures are out of date: the month has closed since they were prepared; the way they are worked out "
         "has changed. They are shown as they were on 19 November 2026, 11:00 UTC."),
    Case("deep_dive.fresh", "records",
         {"records": Flag(True), "closed": Flag(False), "rules": Flag(False), "at": AT, "sites": names("Kisiwa", "Mto")},
         "These figures are out of date: records have arrived since they were prepared for Kisiwa and Mto. They are "
         "shown as they were on 19 November 2026, 11:00 UTC."),
    Case("deep_dive.fresh", "closed", {"records": Flag(False), "closed": Flag(True), "rules": Flag(False), "at": AT},
         "These figures are out of date: the month has closed since they were prepared. They are shown as they were "
         "on 19 November 2026, 11:00 UTC."),
    Case("deep_dive.fresh", "rules", {"records": Flag(False), "closed": Flag(False), "rules": Flag(True), "at": AT},
         "These figures are out of date: the way they are worked out has changed. They are shown as they were on "
         "19 November 2026, 11:00 UTC."),
    Case("deep_dive.untracked_entry", "entry", {"factor": Word("factor", "om"), "sites": names("Kisiwa", "Mto")},
         "O&M (Kisiwa and Mto)"),
    Case("deep_dive.untracked", "untracked",
         {"entries": Items((Name("O&M (Kisiwa)", "deep_dive.untracked_entry"),
                            Name("Staff (Mto)", "deep_dive.untracked_entry")))},
         "Not checked for later changes: O&M (Kisiwa) and Staff (Mto)."),
    Case("deep_dive.month_words", "month", {"month": OCT}, "October 2026"),
    Case("deep_dive.no_snapshot", "no_snapshot", {"month": OCT},
         "The figures for October 2026 have not been prepared yet."),
    Case("deep_dive.rebuild", "rebuild", {"month": OCT},
         "The figures for October 2026 must be prepared again before they can be shown."),
    Case("deep_dive.refused", "bad_month", {"code": State("BAD_MONTH")}, "Write the month as YYYY-MM, like 2026-10."),
    Case("deep_dive.refused", "unavailable", {"code": State("DEEP_DIVE_UNAVAILABLE")},
         "The month's figures cannot be read right now."),
    Case("deep_dive.action_owner", "owner", {"owner": Name("Amina", "action.owner"), "due": Day(date(2026, 12, 1))},
         "Owner Amina · due 1 December 2026"),
    Case("deep_dive.action_agreed", "agreed", {"by": Name("Amina", "action.created_by"), "on": Day(date(2026, 11, 20))},
         "Agreed by Amina on 20 November 2026"),
    Case("deep_dive.grow_line", "line", {"sites": KOfN(2, 3, "site")}, "Revenue against target, 2 of 3 Sites"),
    Case("deep_dive.assure_line", "none_cost", {"disagreements": Count(0, "budget_disagreement"), "cost": pct("0.9151")},
         "No budget disagreement · 91.5% of cost from figures received", EV),
    Case("deep_dive.assure_line", "none", {"disagreements": Count(0, "budget_disagreement")},
         "No budget disagreement", []),
    Case("deep_dive.assure_line", "some_cost", {"disagreements": Count(2, "budget_disagreement"), "cost": pct("0.9151")},
         "2 budget disagreements · 91.5% of cost from figures received", EV),
    Case("deep_dive.assure_line", "some", {"disagreements": Count(1, "budget_disagreement")},
         "1 budget disagreement", []),
    Case("deep_dive.fills", "carried", {"factors": factors("om", "staff"), "carried": Flag(True)},
         "O&M and Staff (taken at its budget line meanwhile)"),
    Case("deep_dive.fills", "fills", {"factors": factors("fuel_cost"), "carried": Flag(False)}, "Fuel cost"),
    Case("deep_dive.names", "names", {"sites": names("Kisiwa", "Mto", "Kobo")}, "Kisiwa, Mto and Kobo"),
    Case("deep_dive.sentences", "one", {"head": Name("One.", "deep_dive.sentence")}, "One."),
    Case("deep_dive.sentences", "more",
         {"head": Name("One.", "deep_dive.sentence"), "rest": Name("Two.", "deep_dive.sentence")}, "One. Two."),
    Case("deep_dive.headline", "currencies_differ", {"month": OCT, "sites": KOfN(0, 3, "site"), "cause": State("CURRENCIES")},
         "Contribution for October is not available yet: the Sites' figures are in different currencies.", []),
    # headline_subject label, money forms and the bridge title.
    Case("deep_dive.money", "not_available", {"value": Absent("NOT_AVAILABLE"), "form": State("PLAIN")},
         "Not available yet", []),
    Case("deep_dive.money", "not_compared", {"value": Absent("NOT_COMPARED"), "form": State("PLAIN")},
         "Not compared", []),
    Case("deep_dive.money", "plain", {"value": usd("38.00"), "form": State("PLAIN")}, "$38.00", EV),
    Case("deep_dive.money", "signed", {"value": usd("-852.00"), "form": State("SIGNED")}, "−$852.00", EV),
    Case("deep_dive.money", "at_budget", {"value": usd("0.00"), "form": State("AT_BUDGET")}, "$0.00 (at budget)", EV),
    Case("deep_dive.bridge_title", "gap_only", {"gap": usd("562.00")},
         "The $562.00 gap, by heading. Open a step for what is behind it.", EV),
    Case("deep_dive.bridge_title", "more_than_gap",
         {"gap": usd("-562.00"), "big": usd("-700.00"), "subject": Word("headline_subject", "OPTIMIZE_COST")},
         "Cost and efficiency explain $700.00, more than the whole $562.00 gap. Open a step for what is behind it.",
         EV),
    Case("deep_dive.bridge_title", "share_of_gap",
         {"gap": usd("-562.00"), "big": usd("-412.00"), "subject": Word("headline_subject", "OPTIMIZE_COST")},
         "Cost and efficiency explain $412.00 of the $562.00 gap. Open a step for what is behind it.", EV),
]
