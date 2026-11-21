"""0K4b (spec section 2.6, D-0K4.19): the cases of `model_profile.need`, one per variant. The English is the spec's
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
]
