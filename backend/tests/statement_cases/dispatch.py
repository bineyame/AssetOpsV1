"""0K4e (`specs/0K4e-candidate-energy/spec.md` §2.5, §3): the cases of the `dispatch.*` statements, one per variant,
from E1-E7's figures (hand literals, W2)."""
from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

from assetops_backend.i18n import Evidence, Instant, Items, Percent, Quantity, State, Word

from statement_cases import Case

HELD_95 = Quantity(Decimal("95"), "kWh", Evidence("DERIVED"))
HELD_133 = Quantity(Decimal("133"), "kWh", Evidence("DERIVED"))
NEED_120 = Quantity(Decimal("120"), "kWh", Evidence("DERIVED"))
HEADROOM = Percent(Decimal("0.1"), Evidence("DECLARED"))

CASES = [
    Case("dispatch.energy_cover", "covered",  # E2
         {"state": State("COVERED"), "held": HELD_133, "need": NEED_120, "headroom": HEADROOM},
         "The available solar power and battery output were more than the site demand, with battery charge above its "
         "minimum reserve, and the battery's 133 kWh above that reserve covers the 120 kWh needed until solar power "
         "covers site demand with 10% headroom (Estimated and Declared); no reason the generator was needed was "
         "recorded."),
    Case("dispatch.energy_cover", "short",  # E1
         {"state": State("SHORT"), "held": HELD_95, "need": NEED_120, "headroom": HEADROOM},
         "Battery support was not counted: the battery's 95 kWh above its minimum reserve does not cover the 120 kWh "
         "needed until solar power covers site demand with 10% headroom (Estimated and Declared)."),
    Case("dispatch.energy_cover", "gap",  # E4
         {"state": State("GAP"), "held": HELD_133, "input": Word("dispatch_input", "pv_available_power"),
          "problem": Word("reading_problem", "MISSING"), "at": Instant(datetime(2026, 10, 2, 23, tzinfo=timezone.utc))},
         "Battery support was not counted: solar available power has no accepted reading at 2 October 2026, 23:00 UTC, "
         "before solar power covers site demand."),
    Case("dispatch.energy_cover", "not_reached",  # E6
         {"state": State("NOT_REACHED"), "held": HELD_133,
          "at": Instant(datetime(2026, 10, 3, 6, tzinfo=timezone.utc))},
         "Battery support was not counted: solar power does not cover site demand before the assessed records end at "
         "3 October 2026, 06:00 UTC."),
    Case("dispatch.energy_cover", "not_configured",  # E7, both controls absent
         {"state": State("NOT_CONFIGURED"), "controls": Items((Word("dispatch_input", "pcs_conversion_efficiency"),
                                                               Word("dispatch_input", "battery_energy_capacity")))},
         "Battery support was not counted: the Site's Foundation does not give the battery energy capacity and the PCS "
         "conversion efficiency."),
    Case("dispatch.energy_cover_cause", "short", {"state": State("SHORT")},
         "the battery's stored energy above its minimum reserve would not have lasted until solar power covered site "
         "demand"),
    Case("dispatch.energy_cover_cause", "not_reached", {"state": State("NOT_REACHED")},
         "solar power did not cover site demand before the assessed records end"),
]
