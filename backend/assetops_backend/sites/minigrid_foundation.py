"""W4-02 mini-grid depth Foundation rules (`D-2026-10-20-w4-02-buildspec` closure 1 Q9, closure 4 N2).

`validate_minigrid_properties` runs after the shared strict parser on every import and every later revision, at the
same point as the cold and EV rules: each of the three typed depth properties sits on its one carrier component type,
and `backup-recovery-target` is strictly positive. The shared parser already refuses a negative unsigned value, so
`pv-available-uncertainty` and `renewable-retained-margin` are nonnegative. No default is ever supplied.
"""

from __future__ import annotations

from typing import Callable, NoReturn

from assetops_backend.sites.models import (
    MINIGRID_PROPERTY_CARRIERS,
    MINIGRID_STRICTLY_POSITIVE_PROPERTIES,
    SiteFoundation,
)


def validate_minigrid_properties(foundation: SiteFoundation, *, source: str,
                                 invalid: Callable[[str], NoReturn]) -> None:
    """Refuse a mini-grid depth property on the wrong carrier or with a nonpositive recovery target."""
    for component in foundation.components:
        for prop in component.properties or ():
            carrier = MINIGRID_PROPERTY_CARRIERS.get(prop.property_key)
            if carrier is None:
                continue
            if component.component_type != carrier:
                invalid(f"{prop.property_key} belongs on a {carrier} component, not on {component.component_id} "
                        f"({component.component_type}), in {source}.")
            if prop.property_key in MINIGRID_STRICTLY_POSITIVE_PROPERTIES and not float(prop.value) > 0:
                invalid(f"{prop.property_key} on {component.component_id} must be greater than zero in {source}.")


__all__ = ["validate_minigrid_properties"]
