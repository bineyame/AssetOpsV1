"""0K4b (spec `specs/0K4b-fuel-curve-taper/spec.md` section 2.6, D-0K4.19): what a model profile needs from the
Foundation, one sentence per need. 0K4a (spec section 2.7) adds `model_profile.description` and
`model_profile.state`: what `mini-grid` v8 changes from the previous version, and its restated fuel-tank state. Pure
literal data (D-SC1.3)."""
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
    "model_profile.description": {
        "slots": {"profile": {"type": "state", "values": ["MINI_GRID_V8"]}},
        "variants": [
            {"id": "cycle_charging", "when": {"is": ["profile", "MINI_GRID_V8"]},
             "text": "As the previous mini-grid version, except that the generator runs as a cycle charger: while it "
                     "runs it carries the load and charges the battery, the battery helps only above what solar and "
                     "the generator give, the generator is held at its minimum load by charging and then by "
                     "curtailing solar, fuel follows its declared curve, and charging tapers near full."},
        ],
        "exhaustive": "profile",
        "rephrase": "never",
    },
    "model_profile.state": {
        "slots": {"state": {"type": "state", "values": ["FUEL_TANK_VOLUME_CURVE"]}},
        "variants": [
            {"id": "fuel_tank_volume_curve", "when": {"is": ["state", "FUEL_TANK_VOLUME_CURVE"]},
             "text": "The fuel in the tank, initialized by the scenario, moved by the generator's fuel curve while it "
                     "starts or runs and by any frozen declared cause, such as a recorded operational action."},
        ],
        "exhaustive": "state",
        "rephrase": "never",
    },
}
