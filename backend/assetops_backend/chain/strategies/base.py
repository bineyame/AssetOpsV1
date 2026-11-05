"""CH-6a1 (build sheet CH-6 R4, §A1, §A2.3; CH6a1-R Q5): the contribution strategy registry.

A strategy turns facts that ChainReader has already read into an `Effect` for one `OutcomeContribution`. Pure: no
I/O, no clock, no store. **No strategy computes new money**: stored snapshot money (already measured x declared price,
`chain/measure_impls.py:152-160`) is summed, a stored consequence range is read, or headroom kW x 1 h x the declared
price is formed for a potential. `ContributionContext` may only grow additively (CH6a1-R Q5).
"""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any, Protocol

# Effect bases (§A2.3).
MEASURED, RECORDED, DECLARED, MODELLED, EXTERNAL = "MEASURED", "RECORDED", "DECLARED", "MODELLED", "EXTERNAL"
# Reasons carried when `Effect.money` is None (CH6a1-R Q5).
CURRENCY_MIXED = "CURRENCY_MIXED"
NO_RECORDS = "NO_RECORDS"
NOT_SUPPORTED = "NOT_SUPPORTED"
NOT_PRICED = "NOT_PRICED"
NOT_PRESENT = "NOT_PRESENT"
SUPPORTED = "SUPPORTED"


@dataclass(frozen=True)
class ContributionContext:
    """Facts already read for one record. Every field but `record` is optional; a strategy reads what it needs."""
    record: Any                                   # outcomes.outcome_map.OutcomeContribution
    day_rows: tuple[Any, ...] = ()                # chain.ports.SnapshotRow of the record's measure over the window
    signals: tuple[Any, ...] = ()                 # outcomes.status.Signal of the record's source (status inputs)
    money_head: Any = None                        # chain.read.MoneyHead | None (avoided_cost@1)
    price: Decimal | None = None                  # the declared price at the window's last day
    currency: str | None = None
    headroom_kw: tuple[Decimal, Decimal] | None = None   # (low, high) from the opportunity thread items (R13)
    evidence_status: str | None = None            # the opportunity's evidence status (SUPPORTED | LIMITED | ...)
    title: str | None = None                      # the source's own title (a warning, a Finding)


@dataclass(frozen=True)
class Effect:
    direction: str
    magnitude: tuple[Decimal | None, str | None] = (None, None)
    money: Mapping[str, Any] | None = None        # {"amount"} or {"low", "high"}, plus "currency"
    basis: str | None = None
    days: Mapping[str, int] = field(default_factory=dict)
    explanation_ids: tuple[str, ...] = ()
    reason: str | None = None                     # why `money` (or the effect) is empty
    title: str | None = None
    inputs: Mapping[str, Any] | None = None       # graded_verdict@1 judge inputs; finding_presence@1 signal facts


class ContributionStrategy(Protocol):
    key: str
    version: int

    def effect(self, ctx: ContributionContext) -> Effect: ...


class UnknownStrategy(LookupError):
    pass


class Registry:
    def __init__(self, strategies: tuple[ContributionStrategy, ...]) -> None:
        self._by: dict[str, ContributionStrategy] = {}
        for s in strategies:
            ref = f"{s.key}@{s.version}"
            if ref in self._by:
                raise ValueError(f"duplicate strategy {ref}")
            self._by[ref] = s

    def keys(self) -> tuple[str, ...]:
        return tuple(self._by)

    def resolve(self, ref: str) -> ContributionStrategy:
        try:
            return self._by[ref]
        except KeyError:
            raise UnknownStrategy(ref) from None
