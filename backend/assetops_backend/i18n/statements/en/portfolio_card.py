"""1a (spec section 3.2; D-1A.9): the Portfolio Optimize card's day and scope.

Pure literal data (D-SC1.3). The card's figure is one lead issue's stored cost; this line says which issue and which
day, and that it is not the period's total. No amount is repeated in it (D-1A.2: one figure).
"""
STATEMENTS = {
    "portfolio_card.cost_scope": {
        "slots": {
            "sites": {"type": "state", "values": ["ONE", "SEVERAL"]},
            "site": {"type": "name", "absent": ["SEVERAL"]},
            "span": {"type": "state", "values": ["ONE_DAY", "RANGE"]},
            "day": {"type": "day", "absent": ["LATEST_IN_RANGE", "DAYS_DIFFER"]},
            "days": {"type": "count", "absent": ["ONE_DAY", "DAYS_DIFFER"]},
        },
        "variants": [
            {"id": "one_day", "when": {"all": [{"is": ["sites", "ONE"]}, {"is": ["span", "ONE_DAY"]}]},
             "requires": {"present": "day"},
             "text": "Cost of {site}'s lead issue on {day}"},
            {"id": "one_range", "when": {"all": [{"is": ["sites", "ONE"]}, {"present": "day"}]},
             "requires": {"present": "days"},
             "text": "Cost of {site}'s lead issue on {day}, the last of the {days} shown, not their total"},
            {"id": "one_latest", "when": {"is": ["sites", "ONE"]},
             "requires": {"all": [{"reason": ["day", "LATEST_IN_RANGE"]}, {"present": "days"}]},
             "text": "Cost of {site}'s latest issue in the {days} shown, not their total"},
            {"id": "each_one_day", "when": {"all": [{"is": ["span", "ONE_DAY"]}, {"present": "day"}]},
             "text": "Cost at each Site of its lead issue on {day}"},
            {"id": "each_range", "when": {"present": "day"}, "requires": {"present": "days"},
             "text": "Cost at each Site of its lead issue on {day}, the last of the {days} shown, not their total"},
            {"id": "each_differ", "requires": {"reason": ["day", "DAYS_DIFFER"]},
             "text": "Cost at each Site of its lead issue in the days it shows, not their total"},
        ],
        "rephrase": "never",
    },
}
