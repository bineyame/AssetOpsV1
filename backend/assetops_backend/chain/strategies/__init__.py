"""CH-6a1 (build sheet CH-6 R4): the six registered contribution strategies; `REGISTRY.resolve("<key>@<version>")`."""
from __future__ import annotations

from assetops_backend.chain.strategies.avoided_cost import AvoidedCost
from assetops_backend.chain.strategies.base import Registry
from assetops_backend.chain.strategies.direction_only import DirectionOnly
from assetops_backend.chain.strategies.finding_presence import FindingPresence
from assetops_backend.chain.strategies.graded_verdict import GradedVerdict
from assetops_backend.chain.strategies.priced_energy import PricedEnergy
from assetops_backend.chain.strategies.recorded_amount import RecordedAmount

REGISTRY = Registry((FindingPresence(), DirectionOnly(), GradedVerdict(), PricedEnergy(), AvoidedCost(),
                     RecordedAmount()))
