"""0K4e (`specs/0K4e-candidate-energy/spec.md` §2.5, D-0K4.19 item 3, D-0K4.24): the words for a dispatch-3.3
energy-cover entry. Pure literal data (D-SC1.3). `dispatch.energy_cover` is the segment reason `plain._segment`
serves; `dispatch.energy_cover_cause` is the fragment `finding_read.portion_cause` adds to an undecided portion."""
STATEMENTS = {
    "dispatch.energy_cover": {
        "slots": {
            "state": {"type": "state", "values": ["COVERED", "SHORT", "GAP", "NOT_REACHED", "NOT_CONFIGURED"]},
            "held": {"type": "quantity", "places": "normal", "optional": True, "evidence": {"with": "basis"}},
            "need": {"type": "quantity", "places": "normal", "optional": True, "evidence": {"with": "basis"}},
            "headroom": {"type": "percent", "places": "normal", "optional": True, "evidence": {"with": "basis"}},
            "basis": {"type": "evidence", "of": ["held", "need", "headroom"]},
            "input": {"type": "word", "vocabulary": "dispatch_input", "form": "in_sentence", "optional": True},
            "problem": {"type": "word", "vocabulary": "reading_problem", "form": "in_sentence", "optional": True},
            "at": {"type": "instant", "optional": True},
            "controls": {"type": "items", "of": {"type": "word", "vocabulary": "dispatch_input", "form": "in_sentence"},
                         "order": "vocabulary", "optional": True},
        },
        "variants": [
            {"id": "covered", "when": {"is": ["state", "COVERED"]},
             "requires": {"all": [{"present": "held"}, {"present": "need"}, {"present": "headroom"}]},
             "text": "The available solar power and battery output were more than the site demand, with battery "
                     "charge above its minimum reserve, and the battery's {held} above that reserve covers the {need} "
                     "needed until solar power covers site demand with {headroom} headroom ({basis}); no reason the "
                     "generator was needed was recorded."},
            {"id": "short", "when": {"is": ["state", "SHORT"]},
             "requires": {"all": [{"present": "held"}, {"present": "need"}, {"present": "headroom"}]},
             "text": "Battery support was not counted: the battery's {held} above its minimum reserve does not cover "
                     "the {need} needed until solar power covers site demand with {headroom} headroom ({basis})."},
            {"id": "gap", "when": {"is": ["state", "GAP"]},
             "requires": {"all": [{"present": "input"}, {"present": "problem"}, {"present": "at"}]},
             "text": "Battery support was not counted: {input} has {problem} at {at}, before solar power covers site "
                     "demand."},
            {"id": "not_reached", "when": {"is": ["state", "NOT_REACHED"]}, "requires": {"present": "at"},
             "text": "Battery support was not counted: solar power does not cover site demand before the assessed "
                     "records end at {at}."},
            {"id": "not_configured", "when": {"is": ["state", "NOT_CONFIGURED"]}, "requires": {"present": "controls"},
             "text": "Battery support was not counted: the Site's Foundation does not give {controls}."},
        ],
        "exhaustive": "state",
        "rephrase": "never",
    },
    "dispatch.energy_cover_cause": {
        "slots": {"state": {"type": "state", "values": ["SHORT", "NOT_REACHED"]}},
        "variants": [
            {"id": "short", "when": {"is": ["state", "SHORT"]},
             "text": "the battery's stored energy above its minimum reserve would not have lasted until solar power "
                     "covered site demand"},
            {"id": "not_reached", "when": {"is": ["state", "NOT_REACHED"]},
             "text": "solar power did not cover site demand before the assessed records end"},
        ],
        "exhaustive": "state",
        "rephrase": "never",
    },
}
