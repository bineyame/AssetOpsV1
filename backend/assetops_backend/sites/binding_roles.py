"""The code-owned MINIGRID signal role vocabulary (S1-02).

PROPOSED, pending the Architect's answers in `.agent/S1-02-questions.md`
(Q1 role names and requirement, Q3 battery reserve, Q4 units and conversions).
Every vocabulary choice lives here, so an answer changes this table and the
Kobo conversion fixture, not the binding mechanism.

A role names what a bound channel means for analysis. The canonical unit is
fixed per role. A role is either a channel role (bound to one registered
device signal) or a configuration role (covered by a Foundation control, not
by a channel).
"""

from __future__ import annotations

from dataclasses import dataclass

ROLE_SET_MINIGRID = "minigrid-roles-1"

#: The canonical generator states an ENUM conversion may map to.
GENERATOR_STATES: tuple[str, ...] = ("STOPPED", "STARTING", "RUNNING", "FAILED")

#: One binding per Site, or one per asset of the role's asset type.
ONE = "ONE"
PER_ASSET = "PER_ASSET"


@dataclass(frozen=True)
class Role:
    role: str
    label: str
    asset_type: str
    canonical_unit: str
    value_kind: str  # NUMBER | STATE
    cardinality: str  # ONE | PER_ASSET
    required: bool
    #: "CHANNEL" roles are bound to a device signal; "FOUNDATION_CONTROL"
    #: roles are covered by a configured Foundation control (Q3 proposal).
    covered_by: str = "CHANNEL"


MINIGRID_ROLES: tuple[Role, ...] = (
    Role("generator_state", "Generator state", "GENERATOR", "state", "STATE", ONE, True),
    Role("generator_power", "Generator power", "GENERATOR", "kW", "NUMBER", ONE, True),
    Role("feeder_demand", "Feeder demand", "LOAD", "kW", "NUMBER", PER_ASSET, True),
    Role("battery_soc", "Battery state of charge", "BATTERY", "%", "NUMBER", ONE, True),
    Role(
        "battery_reserve", "Battery reserve", "BATTERY", "%", "NUMBER", ONE, True,
        covered_by="FOUNDATION_CONTROL",
    ),
    Role("pv_power", "Solar inverter power", "INVERTER", "kW", "NUMBER", ONE, False),
    Role("pv_irradiance", "Solar irradiance", "PV_ARRAY", "W/m2", "NUMBER", ONE, False),
    Role("battery_power", "Battery converter power", "POWER_CONVERSION_SYSTEM", "kW", "NUMBER", ONE, False),
    Role("fuel_level", "Fuel level", "FUEL_TANK", "L", "NUMBER", ONE, False),
)

ROLES_BY_SET: dict[str, tuple[Role, ...]] = {ROLE_SET_MINIGRID: MINIGRID_ROLES}
ROLE_SET_BY_SITE_TYPE: dict[str, str] = {"MINIGRID": ROLE_SET_MINIGRID}

CONVERSION_KINDS = ("IDENTITY", "LINEAR", "ENUM")


def roles_for(role_set: str) -> dict[str, Role]:
    return {role.role: role for role in ROLES_BY_SET.get(role_set, ())}


def conversion_problem(role: Role, source_unit: str, conversion: object) -> str | None:
    """Why this conversion cannot turn `source_unit` into the role's unit, or None."""
    if not isinstance(conversion, dict) or set(conversion) != {"kind", "parameters"}:
        return "conversion must be an object with exactly 'kind' and 'parameters'"
    kind, parameters = conversion["kind"], conversion["parameters"]
    if kind not in CONVERSION_KINDS:
        return f"conversion kind {kind!r} is not one of {', '.join(CONVERSION_KINDS)}"
    if not isinstance(parameters, dict):
        return "conversion parameters must be an object"
    if kind == "IDENTITY":
        if parameters:
            return "an IDENTITY conversion takes no parameters"
        if source_unit != role.canonical_unit:
            return (
                f"an IDENTITY conversion needs the source unit to be {role.canonical_unit!r}, "
                f"not {source_unit!r}"
            )
        if role.value_kind != "NUMBER":
            return f"{role.label} is a state; use an ENUM conversion"
        return None
    if kind == "LINEAR":
        if role.value_kind != "NUMBER":
            return f"{role.label} is a state; a LINEAR conversion applies only to numbers"
        if set(parameters) != {"scale", "offset"}:
            return "a LINEAR conversion takes exactly 'scale' and 'offset'"
        for key in ("scale", "offset"):
            value = parameters[key]
            try:
                if not isinstance(value, str) or not _is_decimal(value):
                    raise ValueError
            except ValueError:
                return f"LINEAR {key} must be a decimal string, e.g. \"0.001\""
        return None
    # ENUM
    if role.value_kind != "STATE":
        return f"{role.label} is a number; an ENUM conversion applies only to states"
    if set(parameters) != {"map"} or not isinstance(parameters["map"], dict) or not parameters["map"]:
        return "an ENUM conversion takes exactly a non-empty 'map'"
    for label, state in parameters["map"].items():
        if not isinstance(label, str) or state not in GENERATOR_STATES:
            return f"ENUM map entry {label!r} must map to one of {', '.join(GENERATOR_STATES)}"
    if source_unit != role.canonical_unit:
        return f"a state is reported in {role.canonical_unit!r}, not {source_unit!r}"
    return None


def _is_decimal(text: str) -> bool:
    body = text[1:] if text[:1] in "+-" else text
    whole, _, fraction = body.partition(".")
    return bool(whole or fraction) and (whole + fraction).isdigit()
