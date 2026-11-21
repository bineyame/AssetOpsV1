"""The forward replay port, owned by the product and implemented in the composition leaf (0K1).

Valuing a generator setting needs the kernel (design `domain-and-decision-models.md` §4.2), and the product may not
reach it (`tools/checks/dependency-direction.ps1`). This is the seam: one method that takes the product's own frozen
`SimulationRun` and a neutral `ForwardReplayRequest`, and returns a neutral `ForwardReplayProjection`. Both live in
`assetops_contracts.forward_replay`; nothing simulator-shaped crosses in either direction.

It is a separate port, not a thirteenth method on `LabExecutionPort` (D-0K1.1): that port is `runtime_checkable`,
so a new method would make every existing implementation and fake fail `isinstance`, and a replay is not a Lab
control (it advances no Draft and writes no artifact).

Nothing in the product composes it in 0K1. Like the Lab port, it is received by injection (`execution_ports.py`,
"Why the product cannot build an implementation of it"); `0K2` and `6c` are its first callers.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from assetops_backend.runs.models import SimulationRun
from assetops_contracts.forward_replay import ForwardReplayProjection, ForwardReplayRequest


@runtime_checkable
class ForwardReplayPort(Protocol):
    def forward_replay(self, run: SimulationRun, request: ForwardReplayRequest) -> ForwardReplayProjection:
        """Replay a frozen mini-grid run's world under a request; raises ForwardReplayRefused when nothing ran."""
        ...


__all__ = ["ForwardReplayPort"]
