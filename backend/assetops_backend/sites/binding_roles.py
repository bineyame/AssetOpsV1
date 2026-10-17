"""The code-owned MINIGRID signal role vocabulary (S1-02).

Decided by `D-2026-10-08-s1-bindings-roles-and-snapshot` (Architect answers
Q1, Q3 and Q4 in `.agent/architect-S1-02-answers-2026-10-08.md`). Every
vocabulary choice lives here; the binding mechanism does not name a role.

A role names what a bound channel means for analysis. The canonical unit is
fixed per role. A role is either a channel role (bound to one registered
device signal) or a configuration role (covered by a Foundation control, not
by a channel).
"""

from __future__ import annotations

from dataclasses import dataclass

#: S1-02's vocabulary. Kept readable for every binding set recorded under it.
ROLE_SET_MINIGRID_1 = "minigrid-roles-1"
#: S3-01 (`D-2026-10-11-s3-dispatch-interval-assessment`, Architect batch 5
#: "S3-01 Planner questions"): roles-1 plus the two optional capability
#: channels a dispatch Candidate needs. Observed `pv_power` and
#: `battery_power` are not these capabilities.
ROLE_SET_MINIGRID_2 = "minigrid-roles-2"
#: S6-02a (`D-2026-10-16-s6-verification`, `D-2026-10-16-s602-questions`):
#: roles-2 plus the requested and delivered critical-load power a reserve
#: trial's service guardrail needs. A Site opts in by publishing with this
#: role set explicitly; new publications still default to roles-2.
ROLE_SET_MINIGRID_3 = "minigrid-roles-3"
#: The set a new MINIGRID binding publication is recorded under.
ROLE_SET_MINIGRID = ROLE_SET_MINIGRID_2
#: W2-01 (`.agent/W2-technical-design-cold.md` section 3, `D-2026-10-17-w2-01-answers`
#: and its W2-02 channel closure): the immutable COLDCHAIN vocabulary.
ROLE_SET_COLD_1 = "cold-roles-1"

#: The canonical generator states an ENUM conversion may map to.
GENERATOR_STATES: tuple[str, ...] = ("STOPPED", "STARTING", "RUNNING", "FAILED")
#: W2-01 role-specific ENUM member sets (`D-2026-10-17-w2-01-answers` B).
COMPRESSOR_STATES: tuple[str, ...] = ("OFF", "STARTING", "RUNNING", "FAILED")
GRID_STATES: tuple[str, ...] = ("AVAILABLE", "LOST")
BUS_STATES: tuple[str, ...] = ("POWERED", "UNPOWERED")

#: The nonquantitative declared unit of an event channel (`SIGNAL_UNITS`).
EVENT_UNIT = "event"

#: One binding per Site, or one per asset of the role's asset type.
ONE = "ONE"
PER_ASSET = "PER_ASSET"


@dataclass(frozen=True)
class Role:
    role: str
    label: str
    asset_type: str
    canonical_unit: str
    value_kind: str  # NUMBER | STATE | EVENT
    cardinality: str  # ONE | PER_ASSET
    required: bool
    #: "CHANNEL" roles are bound to a device signal; "FOUNDATION_CONTROL"
    #: roles are covered by a configured Foundation control (decision Q3).
    covered_by: str = "CHANNEL"
    #: S6-02a: a ONE role describing the Site's critical load - the first
    #: member of the Foundation's `critical-load-priority` control. The
    #: control identifies the one asset, so several LOAD components are not
    #: an ambiguity; a binding naming any other load is refused.
    critical_load: bool = False
    #: W2-01: a STATE role's own ENUM member set. Empty means the generator
    #: states every MINIGRID state role has always mapped to.
    states: tuple[str, ...] = ()
    #: W2-01: an EVENT role's exact v4 record kinds; the outcomes allowed for
    #: each are the closed v4 kind-to-outcome table's.
    event_kinds: tuple[str, ...] = ()

    @property
    def enum_states(self) -> tuple[str, ...]:
        return self.states or GENERATOR_STATES


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

MINIGRID_ROLES_2: tuple[Role, ...] = MINIGRID_ROLES + (
    Role("pv_available_power", "Solar available power", "INVERTER", "kW", "NUMBER", ONE, False),
    Role(
        "pcs_discharge_capability", "Battery converter discharge capability",
        "POWER_CONVERSION_SYSTEM", "kW", "NUMBER", ONE, False,
    ),
)

MINIGRID_ROLES_3: tuple[Role, ...] = MINIGRID_ROLES_2 + (
    Role(
        "critical_load_requested_power", "Critical load requested power", "LOAD", "kW", "NUMBER", ONE, False,
        critical_load=True,
    ),
    Role(
        "critical_load_delivered_power", "Critical load delivered power", "LOAD", "kW", "NUMBER", ONE, False,
        critical_load=True,
    ),
)

#: `cold-roles-1`, canonical per the design's role table and the W2-02 channel
#: closure: one `backup_start_event` channel carries both start kinds, and
#: `grid_power_event` is separate from `grid_state`. The two room policy roles
#: are Foundation controls (typed `cold-policy-low/high` properties), never
#: channel bindings. Immutable: a change is a new named version.
COLD_ROLES_1: tuple[Role, ...] = (
    Role("chamber_temperature", "Chamber temperature", "TEMPERATURE_PROBE", "degC", "NUMBER", PER_ASSET, True),
    Role(
        "cold_policy_low", "Temperature policy low", "COLD_ROOM", "degC", "NUMBER", PER_ASSET, True,
        covered_by="FOUNDATION_CONTROL",
    ),
    Role(
        "cold_policy_high", "Temperature policy high", "COLD_ROOM", "degC", "NUMBER", PER_ASSET, True,
        covered_by="FOUNDATION_CONTROL",
    ),
    Role(
        "compressor_state", "Compressor state", "COMPRESSOR", "state", "STATE", PER_ASSET, True,
        states=COMPRESSOR_STATES,
    ),
    Role("compressor_power", "Compressor power", "COMPRESSOR", "kW", "NUMBER", PER_ASSET, False),
    Role("grid_state", "Grid state", "METER", "state", "STATE", ONE, True, states=GRID_STATES),
    Role(
        "backup_start_event", "Generator start request and result", "GENERATOR", EVENT_UNIT, "EVENT", ONE, True,
        event_kinds=("START_REQUEST", "START_RESULT"),
    ),
    Role(
        "generator_state", "Generator state", "GENERATOR", "state", "STATE", ONE, True,
        states=GENERATOR_STATES,
    ),
    Role("backup_bus_state", "Backup bus state", "AC_BUS", "state", "STATE", ONE, True, states=BUS_STATES),
    Role(
        "grid_power_event", "Grid power loss and restoration", "METER", EVENT_UNIT, "EVENT", ONE, True,
        event_kinds=("POWER_LOSS", "POWER_RESTORED"),
    ),
    Role(
        "transfer_result", "Transfer result", "TRANSFER_SWITCH", EVENT_UNIT, "EVENT", ONE, False,
        event_kinds=("TRANSFER_RESULT",),
    ),
    Role(
        "door_event", "Door open and close", "COLD_ROOM", EVENT_UNIT, "EVENT", PER_ASSET, False,
        event_kinds=("DOOR_OPEN", "DOOR_CLOSE"),
    ),
    Role("ambient_temperature", "Ambient temperature", "TEMPERATURE_PROBE", "degC", "NUMBER", PER_ASSET, False),
    Role(
        "manual_temperature", "Manual temperature log", "COLD_ROOM", "degC", "EVENT", PER_ASSET, False,
        event_kinds=("MANUAL_LOG",),
    ),
)

#: The Foundation property each cold policy role is selected from.
COLD_POLICY_PROPERTIES: dict[str, str] = {
    "cold_policy_low": "cold-policy-low",
    "cold_policy_high": "cold-policy-high",
}
#: W2-01 publishes this fixed `cold-roles-1` channel contract, never a stored
#: or observed cadence (`D-2026-10-17-w2-01-answers` D-I): periodic channels
#: sample every 300 s; EVENT channels are transition-driven (no cadence).
COLD_PERIODIC_CADENCE_SECONDS = 300

ROLES_BY_SET: dict[str, tuple[Role, ...]] = {
    ROLE_SET_MINIGRID_1: MINIGRID_ROLES,
    ROLE_SET_MINIGRID_2: MINIGRID_ROLES_2,
    ROLE_SET_MINIGRID_3: MINIGRID_ROLES_3,
    ROLE_SET_COLD_1: COLD_ROLES_1,
}
#: The role set a new publication for a Site type is recorded under.
ROLE_SET_BY_SITE_TYPE: dict[str, str] = {"MINIGRID": ROLE_SET_MINIGRID, "COLDCHAIN": ROLE_SET_COLD_1}
#: Every role set a Site type still serves: a binding set recorded under an
#: older version stays interpretable (and selectable as a historical basis)
#: under the role definitions it was published with, never today's.
SERVED_ROLE_SETS_BY_SITE_TYPE: dict[str, frozenset[str]] = {
    "MINIGRID": frozenset({ROLE_SET_MINIGRID_1, ROLE_SET_MINIGRID_2, ROLE_SET_MINIGRID_3}),
    "COLDCHAIN": frozenset({ROLE_SET_COLD_1}),
}

#: S6-02a verification inputs (Architect S6-02a Q2). Interval-power roles
#: need five-minute interval-valued readings covering each UTC slot; point
#: roles need an accepted sample at each five-minute boundary.
VERIFICATION_ROLE_SETS: frozenset[str] = frozenset({ROLE_SET_MINIGRID_3})
VERIFICATION_POWER_ROLES: tuple[str, ...] = (
    "generator_power", "feeder_demand", "pv_available_power", "pcs_discharge_capability",
    "critical_load_requested_power", "critical_load_delivered_power",
)
VERIFICATION_POINT_ROLES: tuple[str, ...] = ("generator_state", "battery_soc")
#: Names the wording below; any wording change is a new version.
VERIFICATION_READINESS_VERSION = "verification-readiness-1"

_LAB_INTERVAL = (
    "Run the Lab with the five-minute publication profile (registered-kobo-publication v4), "
    "which publishes this channel as an interval mean for every five-minute slot."
)
_LAB_POINT = (
    "Run the Lab with the five-minute publication profile (registered-kobo-publication v4), "
    "which publishes a sample at every five-minute boundary."
)
_SITE_INTERVAL = (
    "Publish five-minute interval-valued power in kW: an interval mean whose interval covers "
    "each UTC five-minute slot, or non-overlapping sub-intervals that exactly partition it. "
    "Point readings alone do not count."
)
#: role -> (Lab message, real-Site message).
VERIFICATION_MESSAGES: dict[str, tuple[str, str]] = {
    "generator_power": (_LAB_INTERVAL, "Bind the generator output meter. " + _SITE_INTERVAL),
    "feeder_demand": (_LAB_INTERVAL, "Bind a feeder meter for every load asset. " + _SITE_INTERVAL),
    "pv_available_power": (
        _LAB_INTERVAL, "Bind the inverter's available (uncurtailed) power. " + _SITE_INTERVAL,
    ),
    "pcs_discharge_capability": (
        _LAB_INTERVAL, "Bind the battery converter's discharge capability. " + _SITE_INTERVAL,
    ),
    "critical_load_requested_power": (
        _LAB_INTERVAL, "Bind the power the critical load requested. " + _SITE_INTERVAL,
    ),
    "critical_load_delivered_power": (
        _LAB_INTERVAL, "Bind the power delivered to the critical load. " + _SITE_INTERVAL,
    ),
    "generator_state": (
        _LAB_POINT, "Bind the generator state and publish a sample at every UTC five-minute boundary.",
    ),
    "battery_soc": (
        _LAB_POINT,
        "Bind battery state of charge (%) and publish a sample at every UTC five-minute boundary, "
        "including the window end.",
    ),
}


def serves(site_type: str, role_set: str) -> bool:
    """Whether a Site of `site_type` can read bindings recorded under `role_set`."""
    return role_set in SERVED_ROLE_SETS_BY_SITE_TYPE.get(site_type, frozenset())

#: S1 publishes numeric IDENTITY and generator-state ENUM only (decision Q4).
#: LINEAR is deferred until supported unit pairs, coefficients and
#: normalization rules are decided; a LINEAR conversion is refused.
CONVERSION_KINDS = ("IDENTITY", "ENUM")
DEFERRED_CONVERSION_KINDS = ("LINEAR",)


def roles_for(role_set: str) -> dict[str, Role]:
    return {role.role: role for role in ROLES_BY_SET.get(role_set, ())}


def conversion_problem(role: Role, source_unit: str, conversion: object) -> str | None:
    """Why this conversion cannot turn `source_unit` into the role's unit, or None."""
    if not isinstance(conversion, dict) or set(conversion) != {"kind", "parameters"}:
        return "conversion must be an object with exactly 'kind' and 'parameters'"
    kind, parameters = conversion["kind"], conversion["parameters"]
    if kind in DEFERRED_CONVERSION_KINDS:
        return f"a {kind} conversion is not published in this release; only IDENTITY and ENUM are"
    if kind not in CONVERSION_KINDS:
        return f"conversion kind {kind!r} is not one of {', '.join(CONVERSION_KINDS)}"
    if not isinstance(parameters, dict):
        return "conversion parameters must be an object"
    if kind == "IDENTITY":
        if parameters:
            return "an IDENTITY conversion takes no parameters"
        if role.value_kind == "STATE":
            return f"{role.label} is a state; use an ENUM conversion"
        # W2-01: the `event` unit is valid only on an EVENT role, whose
        # IDENTITY passes its declared unit through and converts nothing.
        if source_unit == EVENT_UNIT and role.value_kind != "EVENT":
            return f"{role.label} is not an event channel; the 'event' unit applies only to events"
        if source_unit != role.canonical_unit:
            return (
                f"an IDENTITY conversion needs the source unit to be {role.canonical_unit!r}, "
                f"not {source_unit!r}"
            )
        return None
    # ENUM
    if role.value_kind != "STATE":
        noun = "a number" if role.value_kind == "NUMBER" else "an event"
        return f"{role.label} is {noun}; an ENUM conversion applies only to states"
    if set(parameters) != {"map"} or not isinstance(parameters["map"], dict) or not parameters["map"]:
        return "an ENUM conversion takes exactly a non-empty 'map'"
    members = role.enum_states
    for label, state in parameters["map"].items():
        if not isinstance(label, str) or state not in members:
            return f"ENUM map entry {label!r} must map to one of {', '.join(members)}"
    if source_unit != role.canonical_unit:
        return f"a state is reported in {role.canonical_unit!r}, not {source_unit!r}"
    return None

