"""0K4b (spec section 2.6, D-0K4.19): the cases of `model_profile.need`, one per variant; 0K4a (spec section 2.7)
adds one case for each variant of `model_profile.description` and `model_profile.state`. The English is the spec's
sentence, written by hand (W2), never computed."""
from __future__ import annotations

from assetops_backend.i18n import State

from statement_cases import Case

CASES = [
    Case("model_profile.need", "no_load_fuel_rate", {"need": State("GENERATOR_NO_LOAD_FUEL_RATE")},
         "Litres an hour the generator burns while starting or running at no output."),
    Case("model_profile.need", "minimum_load", {"need": State("GENERATOR_MINIMUM_LOAD")},
         "Site policy: the least share of its rating a running generator is held at."),
    Case("model_profile.need", "taper_start", {"need": State("BATTERY_CHARGE_TAPER_START")},
         "The state of charge above which the battery accepts less than its charge limit."),
    Case("model_profile.description", "cycle_charging", {"profile": State("MINI_GRID_V8")},
         "As the previous mini-grid version, except that the generator runs as a cycle charger: while it runs it "
         "carries the load and charges the battery, the battery helps only above what solar and the generator give, "
         "the generator is held at its minimum load by charging and then by curtailing solar, fuel follows its "
         "declared curve, and charging tapers near full."),
    Case("model_profile.state", "fuel_tank_volume_curve", {"state": State("FUEL_TANK_VOLUME_CURVE")},
         "The fuel in the tank, initialized by the scenario, moved by the generator's fuel curve while it starts or "
         "runs and by any frozen declared cause, such as a recorded operational action."),
]
