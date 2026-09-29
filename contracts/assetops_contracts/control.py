"""What a controller saw, asked for, and what the world accepted (T024).

Execution contract 9's `COUPLING_RULES` in record form. Four records per step,
and the point of having four is that none of them can stand in for another:

- `ControllerView` is what the controller was permitted to look at, at T. It is
  built by the kernel from world state and forcings, never from a published
  reading, and it is immutable - a controller handed one has nothing it could
  write to.
- `ControlIntent` is what the controller asked for over [T, T+dt).
- `AcceptedFlowSet` is what the resolver accepted: named energy flows, per-load
  service, the requests it clipped and why, the stock changes, and the balance
  identities the kernel verifies exactly.
- `ControlStep` is the three together, recorded on the private trajectory at
  the boundary the step begins at.

Every quantity is an exact `Fraction`. Energies are kWh over the step; a mean
power is that energy over the step's length in hours. A flow is never negative:
direction is carried by which flow it is, not by a sign.

These records are private truth. Only the gated Lab renders them; nothing on a
product path may consume one.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction

#: T025a. The unit a typed discrete value carries: a member of a discrete
#: state's declared allowed values (`RUNNING`), or a request naming one
#: (`RUN`). Such a value is text and never a number standing in for it; every
#: other unit carries an exact `Fraction`. Checked on construction, so an enum
#: cannot cross as a number or a number as an enum.
DISCRETE_UNIT = "state"


def check_typed_value(
    value: object, unit: str, what: str, *, optional: bool = False
) -> None:
    """Refuse a discrete value carried as a number, or a number as text.

    Public since T025b, because a published reading is typed by the same rule
    as the controller's view: the observation path carries a generator status
    as the member it is, never a decimal code for it.
    """
    if value is None and optional:
        return
    if (unit == DISCRETE_UNIT) != isinstance(value, str):
        raise ValueError(
            f"{what} {value!r} in unit {unit!r}: a discrete value is text in "
            f"unit {DISCRETE_UNIT!r} and every other value is a number."
        )


_typed = check_typed_value


@dataclass(frozen=True)
class ViewEntry:
    """One local input the controller read at T.

    `value` is a `Fraction`, or since T025a a typed discrete value in
    `DISCRETE_UNIT` (the generator's physical state at T).
    """

    name: str
    address: str
    value: Fraction | str | None
    unit: str

    def __post_init__(self) -> None:
        _typed(self.value, self.unit, f"view entry {self.name}", optional=True)

    def as_fields(self) -> tuple[object, ...]:
        return (self.name, self.address, self.value, self.unit)


@dataclass(frozen=True)
class ControllerView:
    """Everything the controller was permitted to see at one instant."""

    at_offset_minutes: int
    #: The end of the span [T, T+dt) the controller is asked to decide for.
    for_until_offset: int
    entries: tuple[ViewEntry, ...]

    def value(self, name: str, address: str | None = None) -> Fraction | None:
        for entry in self.entries:
            if entry.name == name and (address is None or entry.address == address):
                return entry.value
        return None

    def as_fields(self) -> tuple[object, ...]:
        return (
            self.at_offset_minutes,
            self.for_until_offset,
            tuple(entry.as_fields() for entry in self.entries),
        )


@dataclass(frozen=True)
class ControlRequest:
    """One request the controller made for the coming span.

    `requested` is signed where the quantity is: a battery power request is
    positive to discharge and negative to charge, which is how the PCS's own
    telemetry is signed.
    """

    address: str
    quantity: str
    requested: Fraction | str
    unit: str
    reason: str

    def __post_init__(self) -> None:
        _typed(self.requested, self.unit, f"request {self.quantity}")

    def as_fields(self) -> tuple[object, ...]:
        return (self.address, self.quantity, self.requested, self.unit, self.reason)


@dataclass(frozen=True)
class ControlIntent:
    """What the controller asked for over [from, to). A request, never a flow."""

    from_offset: int
    to_offset: int
    requests: tuple[ControlRequest, ...]

    def request(self, address: str, quantity: str) -> ControlRequest | None:
        for item in self.requests:
            if item.address == address and item.quantity == quantity:
                return item
        return None

    def as_fields(self) -> tuple[object, ...]:
        return (
            self.from_offset,
            self.to_offset,
            tuple(item.as_fields() for item in self.requests),
        )


@dataclass(frozen=True)
class AcceptedFlow:
    """One named physical flow over the step, as energy and as mean power."""

    flow_id: str
    from_address: str
    to_address: str
    energy: Fraction
    mean_power: Fraction

    def __post_init__(self) -> None:
        if self.energy < 0:
            raise ValueError(
                f"Flow {self.flow_id} carries {self.energy} kWh. A flow's "
                "direction is which flow it is; its energy is never negative."
            )

    def as_fields(self) -> tuple[object, ...]:
        return (
            self.flow_id,
            self.from_address,
            self.to_address,
            self.energy,
            self.mean_power,
        )


@dataclass(frozen=True)
class AcceptedControl:
    """What the resolver accepted of one request, and what limited it.

    `requested` repeats the intent's number so the pair can be read on one row;
    the intent record is still the authority for what was asked. `accepted` is
    the mean accepted power over the step. `limited_by` names every constraint
    that bound, in words a reader can check - "pcs-discharge-limit 22 kW".
    """

    address: str
    quantity: str
    requested: Fraction | str
    accepted: Fraction | str
    unit: str
    limited_by: tuple[str, ...]

    def __post_init__(self) -> None:
        _typed(self.requested, self.unit, f"control {self.quantity} request")
        _typed(self.accepted, self.unit, f"control {self.quantity} acceptance")

    def as_fields(self) -> tuple[object, ...]:
        return (
            self.address,
            self.quantity,
            self.requested,
            self.accepted,
            self.unit,
            self.limited_by,
        )


@dataclass(frozen=True)
class LoadService:
    """One addressed load over the step: what it asked for and what it got."""

    address: str
    priority_rank: int
    demand_energy: Fraction
    served_energy: Fraction
    unserved_energy: Fraction
    demand_power: Fraction
    served_power: Fraction
    unserved_power: Fraction

    def as_fields(self) -> tuple[object, ...]:
        return (
            self.address,
            self.priority_rank,
            self.demand_energy,
            self.served_energy,
            self.unserved_energy,
        )


@dataclass(frozen=True)
class EffectiveControl:
    """The value of one control in effect over one segment, and where from.

    `origin` is `BASELINE` for the frozen Foundation answer and `OVERRIDE` for a
    scenario forcing replacing it inside its window; `provenance` names which.
    """

    address: str
    from_offset: int
    to_offset: int
    value: Fraction
    unit: str
    origin: str
    provenance: str

    def as_fields(self) -> tuple[object, ...]:
        return (
            self.address,
            self.from_offset,
            self.to_offset,
            self.value,
            self.unit,
            self.origin,
            self.provenance,
        )


@dataclass(frozen=True)
class BalanceIdentity:
    """One balance the kernel checks exactly: sources equal sinks.

    Named by flow id. The kernel sums the flows' energies itself, so a resolver
    cannot pass a balance by reporting the sums rather than the flows.
    """

    identity_id: str
    sources: tuple[str, ...]
    sinks: tuple[str, ...]

    def as_fields(self) -> tuple[object, ...]:
        return (self.identity_id, self.sources, self.sinks)


@dataclass(frozen=True)
class StockAccount:
    """How a stock's change is accounted for in energy.

    `delta` is the change in the stock's own unit (state of charge in %);
    `energy_per_unit` converts it to kWh. The kernel checks that
    `delta * energy_per_unit` equals the energy of `inflows` less `outflows`.
    """

    address: str
    delta: Fraction
    energy_per_unit: Fraction
    inflows: tuple[str, ...]
    outflows: tuple[str, ...]

    def as_fields(self) -> tuple[object, ...]:
        return (
            self.address,
            self.delta,
            self.energy_per_unit,
            self.inflows,
            self.outflows,
        )


@dataclass(frozen=True)
class AcceptedFlowSet:
    """What the resolver accepted over [from, to)."""

    from_offset: int
    to_offset: int
    segments: tuple[tuple[int, int], ...]
    flows: tuple[AcceptedFlow, ...]
    controls: tuple[AcceptedControl, ...]
    loads: tuple[LoadService, ...]
    effective_controls: tuple[EffectiveControl, ...]
    balances: tuple[BalanceIdentity, ...]
    stock_accounts: tuple[StockAccount, ...]
    #: Energy per address over the step, which the next boundary's interval
    #: readings describe. Signed where the quantity is signed (the PCS).
    interval_energies: tuple[tuple[str, Fraction], ...]
    notes: tuple[str, ...] = ()

    def flow(self, flow_id: str) -> AcceptedFlow | None:
        for item in self.flows:
            if item.flow_id == flow_id:
                return item
        return None

    def energy(self, flow_id: str) -> Fraction:
        item = self.flow(flow_id)
        if item is None:
            raise KeyError(flow_id)
        return item.energy

    def load(self, address: str) -> LoadService | None:
        for item in self.loads:
            if item.address == address:
                return item
        return None

    def control(self, address: str, quantity: str) -> AcceptedControl | None:
        for item in self.controls:
            if item.address == address and item.quantity == quantity:
                return item
        return None

    def as_fields(self) -> tuple[object, ...]:
        return (
            self.from_offset,
            self.to_offset,
            self.segments,
            tuple(item.as_fields() for item in self.flows),
            tuple(item.as_fields() for item in self.controls),
            tuple(item.as_fields() for item in self.loads),
            tuple(item.as_fields() for item in self.effective_controls),
            tuple(item.as_fields() for item in self.balances),
            tuple(item.as_fields() for item in self.stock_accounts),
            self.interval_energies,
        )


@dataclass(frozen=True)
class ControlStep:
    """One step's view, intent and acceptance, kept as three records."""

    view: ControllerView
    intent: ControlIntent
    accepted: AcceptedFlowSet

    def as_fields(self) -> tuple[object, ...]:
        return (
            self.view.as_fields(),
            self.intent.as_fields(),
            self.accepted.as_fields(),
        )
