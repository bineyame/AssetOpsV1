"""SC-1 (spec section 3.5): the English vocabulary, transcribed by hand. Pure literal data (D-SC1.3, D-SC1.8).

Forms are declared per entry, never derived by a letter rule: `in_sentence` is 5c section 2.2's `lower(label)` applied
once by hand, `article` is chosen by the in-sentence word's sound. `record` is 5c section 2.3 with `SITE_SETUP` as 5c's
SC-1 amendment rewords it (D-SC1.21: no number word); `BUDGET_LINES` is the statement `common.budget_lines`.
"""
VOCABULARY = {
    "factor": {
        "forms": ["label", "in_sentence", "article"],
        "order": ["contribution", "revenue", "billed_kwh", "metered_kwh", "delivered_kwh", "technical_loss_kwh", "unexplained_loss_kwh", "adjustments_kwh", "unmapped_kwh", "tariff", "productive_kwh", "productive_tariff", "cost_to_serve", "fuel_cost", "diesel_l", "necessary_l", "candidate_l", "unexplained_l", "extra_l", "diesel_price", "om", "staff", "collection_cost", "battery_wear", "battery_throughput_kwh", "wear_rate", "collected", "in_transit", "outstanding"],
        "entries": {
            "contribution": {"label": "Contribution", "in_sentence": "contribution", "article": "a"},
            "revenue": {"label": "Revenue", "in_sentence": "revenue", "article": "a"},
            "billed_kwh": {"label": "Energy billed", "in_sentence": "energy billed", "article": "an"},
            "metered_kwh": {"label": "Energy metered", "in_sentence": "energy metered", "article": "an"},
            "delivered_kwh": {"label": "Energy delivered", "in_sentence": "energy delivered", "article": "an"},
            "technical_loss_kwh": {"label": "Technical losses", "in_sentence": "technical losses", "article": "a"},
            "unexplained_loss_kwh": {"label": "Unexplained losses", "in_sentence": "unexplained losses", "article": "an"},
            "adjustments_kwh": {"label": "Billing adjustments", "in_sentence": "billing adjustments", "article": "a"},
            "unmapped_kwh": {"label": "Energy on unmapped meters", "in_sentence": "energy on unmapped meters", "article": "an"},
            "tariff": {"label": "Tariff", "in_sentence": "tariff", "article": "a"},
            "productive_kwh": {"label": "Productive-use energy", "in_sentence": "productive-use energy", "article": "a"},
            "productive_tariff": {"label": "Productive-use price", "in_sentence": "productive-use price", "article": "a"},
            "cost_to_serve": {"label": "Cost to serve", "in_sentence": "cost to serve", "article": "a"},
            "fuel_cost": {"label": "Fuel cost", "in_sentence": "fuel cost", "article": "a"},
            "diesel_l": {"label": "Diesel used", "in_sentence": "diesel used", "article": "a"},
            "necessary_l": {"label": "Diesel not shown to be avoidable", "in_sentence": "diesel not shown to be avoidable", "article": "a"},
            "candidate_l": {"label": "Diesel run while solar and battery could carry the load", "in_sentence": "diesel run while solar and battery could carry the load", "article": "a"},
            "unexplained_l": {"label": "Unexplained fuel", "in_sentence": "unexplained fuel", "article": "an"},
            "extra_l": {"label": "Extra diesel from a change", "in_sentence": "extra diesel from a change", "article": "an"},
            "diesel_price": {"label": "Diesel price", "in_sentence": "diesel price", "article": "a"},
            "om": {"label": "O&M", "in_sentence": "O&M", "article": "an"},
            "staff": {"label": "Staff", "in_sentence": "staff", "article": "a"},
            "collection_cost": {"label": "Collection cost", "in_sentence": "collection cost", "article": "a"},
            "battery_wear": {"label": "Battery wear", "in_sentence": "battery wear", "article": "a"},
            "battery_throughput_kwh": {"label": "Battery throughput", "in_sentence": "battery throughput", "article": "a"},
            "wear_rate": {"label": "Battery wear rate", "in_sentence": "battery wear rate", "article": "a"},
            "collected": {"label": "Cash collected", "in_sentence": "cash collected", "article": "a"},
            "in_transit": {"label": "Paid, in transit", "in_sentence": "paid, in transit", "article": "a"},
            "outstanding": {"label": "Outstanding", "in_sentence": "outstanding", "article": "an"},
        },
    },
    "heading": {
        "forms": ["label", "in_sentence"],
        "order": ["GROW_REVENUE", "OPTIMIZE_COST", "PROTECT_ASSET", "ASSURE_PERFORMANCE", "REVENUE", "FUEL_COST"],
        "entries": {
            "GROW_REVENUE": {"label": "Grow revenue", "in_sentence": "grow revenue"},
            "OPTIMIZE_COST": {"label": "Optimize cost and efficiency", "in_sentence": "optimize cost and efficiency"},
            "PROTECT_ASSET": {"label": "Protect asset and capital", "in_sentence": "protect asset and capital"},
            "ASSURE_PERFORMANCE": {"label": "Assure performance and returns", "in_sentence": "assure performance and returns"},
            "REVENUE": {"label": "Revenue", "in_sentence": "revenue"},
            "FUEL_COST": {"label": "Fuel cost", "in_sentence": "fuel cost"},
        },
    },
    "headline_subject": {
        "forms": ["in_sentence"],
        "order": ["OPTIMIZE_COST", "GROW_REVENUE"],
        "entries": {
            "OPTIMIZE_COST": {"in_sentence": "cost and efficiency explain"},
            "GROW_REVENUE": {"in_sentence": "Grow revenue explains"},
        },
    },
    "record": {
        "forms": ["in_sentence"],
        "order": ["BILLING", "BILLING_ADJUSTMENTS", "FEEDER_METER", "METER_REGISTER", "TARIFF_SHEET", "PRODUCTIVE_LINES", "PRODUCTIVE_TARIFF", "SETTLEMENTS", "RECEIPTS", "EMS", "FUEL_CURVE", "TANK_DIPS", "FUEL_DELIVERIES", "FUEL_INVOICES", "OM_INVOICES", "PAYROLL", "SITE_SETUP", "ANALYSING", "MONTH_CLOSE"],
        "entries": {
            "BILLING": {"in_sentence": "the billing export"},
            "BILLING_ADJUSTMENTS": {"in_sentence": "billing adjustments (credit notes)"},
            "FEEDER_METER": {"in_sentence": "a feeder meter export"},
            "METER_REGISTER": {"in_sentence": "a meter register with change dates"},
            "TARIFF_SHEET": {"in_sentence": "the tariff sheet"},
            "PRODUCTIVE_LINES": {"in_sentence": "productive-use lines in the billing export"},
            "PRODUCTIVE_TARIFF": {"in_sentence": "the productive-use tariff"},
            "SETTLEMENTS": {"in_sentence": "the mobile-money settlement statement"},
            "RECEIPTS": {"in_sentence": "customer receipts"},
            "EMS": {"in_sentence": "the EMS interval export (generator running and output, solar available power, battery charge)"},
            "FUEL_CURVE": {"in_sentence": "the generator's fuel curve (litres per kWh; litres per hour idle)"},
            "TANK_DIPS": {"in_sentence": "tank dips at the start and end of the month"},
            "FUEL_DELIVERIES": {"in_sentence": "fuel delivery notes"},
            "FUEL_INVOICES": {"in_sentence": "fuel invoices with litres"},
            "OM_INVOICES": {"in_sentence": "the service contractor's invoices"},
            "PAYROLL": {"in_sentence": "payroll lines"},
            "SITE_SETUP": {"in_sentence": "a generator and a fuel tank declared in the Site's setup (litres are worked out for each)"},
            "ANALYSING": {"in_sentence": "the running record's analysis, still in progress"},
            "MONTH_CLOSE": {"in_sentence": "the month to close"},
        },
    },
    "record_noun": {
        "forms": ["in_sentence"],
        "order": ["REVENUE", "FUEL_COST"],
        "entries": {
            "REVENUE": {"in_sentence": "billing records"},
            "FUEL_COST": {"in_sentence": "fuel invoices"},
        },
    },
    "unit": {
        "forms": ["symbol"],
        "order": ["L", "kWh"],
        "entries": {
            "L": {"symbol": "L"},
            "kWh": {"symbol": "kWh"},
        },
    },
    "noun": {
        "forms": ["one", "other"],
        "order": ["site", "budget_disagreement", "reading", "character", "day"],
        "entries": {
            "site": {"one": "Site", "other": "Sites"},
            "budget_disagreement": {"one": "budget disagreement", "other": "budget disagreements"},
            "reading": {"one": "reading", "other": "readings"},
            # 3C2 (D-3C2.14): the agreed change's title length, in its refusal sentence.
            "character": {"one": "character", "other": "characters"},
            # 1a (D-1A.8): the window's days, in the Optimize card's scope line.
            "day": {"one": "day", "other": "days"},
        },
    },
    "month": {
        "forms": ["label"],
        "order": ["january", "february", "march", "april", "may", "june", "july", "august", "september", "october", "november", "december"],
        "entries": {
            "january": {"label": "January"},
            "february": {"label": "February"},
            "march": {"label": "March"},
            "april": {"label": "April"},
            "may": {"label": "May"},
            "june": {"label": "June"},
            "july": {"label": "July"},
            "august": {"label": "August"},
            "september": {"label": "September"},
            "october": {"label": "October"},
            "november": {"label": "November"},
            "december": {"label": "December"},
        },
    },
    "format": {
        "forms": ["in_sentence"],
        "order": ["less_than", "more_than", "and", "of", "per", "utc"],
        "entries": {
            "less_than": {"in_sentence": "less than"},
            "more_than": {"in_sentence": "more than"},
            "and": {"in_sentence": "and"},
            "of": {"in_sentence": "of"},
            "per": {"in_sentence": "per"},
            "utc": {"in_sentence": "UTC"},
        },
    },
    "evidence": {
        "by_evidence_first": {"ESTIMATED": "Estimated", "MODELLED": "Modelled", "DECLARED": "Declared"},
        "by_origin": {"source-emulated": "Emulated", "demo-simulated": "Simulated", "unknown": "Estimated"},
        "no_origin": "Estimated",
        "observed_by_evidence": {"RECORDED": "Recorded", "MEASURED": "Measured", "DERIVED": "Calculated"},
        "money_suffix": "not yet reconciled",
    },
    # 3C2 (D-3C2.14): an agreed change's state on the deep-dive screen and the command's success line.
    "action_state": {
        "forms": ["label"],
        "order": ["OPEN", "OVERDUE"],
        "entries": {
            "OPEN": {"label": "Open"},
            "OVERDUE": {"label": "Overdue"},
        },
    },
}
