"""0K4b (spec `specs/0K4b-fuel-curve-taper/spec.md` section 2.6, D-0K4.19): what a model profile needs from the
Foundation, one sentence per need. 0K4a adds two statements to this file. Pure literal data (D-SC1.3)."""
STATEMENTS = {
    "model_profile.need": {
        "slots": {"need": {"type": "state", "values": ["GENERATOR_NO_LOAD_FUEL_RATE", "GENERATOR_MINIMUM_LOAD",
                                                       "BATTERY_CHARGE_TAPER_START"]}},
        "variants": [
            {"id": "no_load_fuel_rate", "when": {"is": ["need", "GENERATOR_NO_LOAD_FUEL_RATE"]},
             "text": "Litres an hour the generator burns while starting or running at no output."},
            {"id": "minimum_load", "when": {"is": ["need", "GENERATOR_MINIMUM_LOAD"]},
             "text": "Site policy: the least share of its rating a running generator is held at."},
            {"id": "taper_start", "when": {"is": ["need", "BATTERY_CHARGE_TAPER_START"]},
             "text": "The state of charge above which the battery accepts less than its charge limit."},
        ],
        "exhaustive": "need",
        "rephrase": "never",
    },
}
