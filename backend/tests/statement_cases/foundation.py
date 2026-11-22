"""0K4b (spec section 2.6, D-0K4.19): the cases of `foundation.property_name`, one per `foundation_property` entry.
The English is the spec's label, written by hand (W2), never computed."""
from __future__ import annotations

from assetops_backend.i18n import Word

from statement_cases import Case


def _name(key: str, english: str) -> Case:
    return Case("foundation.property_name", "label", {"property": Word("foundation_property", key)}, english)


CASES = [
    _name("generator_minimum_load", "Generator minimum load"),
    _name("generator_minimum_load_basis", "Generator minimum load basis"),
    _name("battery_charge_taper_start", "Battery charge taper start"),
    _name("battery_charge_taper_start_basis", "Battery charge taper start basis"),
    _name("pv_array_share", "PV array share"),
    _name("pv_array_share_basis", "PV array share basis"),
]
