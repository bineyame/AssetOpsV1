"""A per-process memo of the scenario catalogue for the W2 replay-chain fixtures (OPS-01 post-W2 follow-up).

Why. Every cold/EV replay chain hands the host a scenario repository, and each `get_scenario` call re-parses all
shipped YAML documents with the production parser (about 3 s per catalogue read on the Windows host, two or
three reads per chain, about a hundred chains per full run). The documents are tracked, read-only files that no
test rewrites during a run, and every definition type is a frozen dataclass, so serving the first successful read
again returns the same values. The production repository is still built and read for real, once per process;
failures are never cached. Production code is unchanged.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Any


class CachedScenarioRepository:
    """`list_scenarios`/`get_scenario` of `inner`, each successful answer kept for the rest of the process."""

    def __init__(self, inner: Any) -> None:
        self._inner = inner
        self._listed: tuple | None = None
        self._by_id: dict[str, Any] = {}

    def list_scenarios(self) -> tuple:
        if self._listed is None:
            self._listed = tuple(self._inner.list_scenarios())
        return self._listed

    def get_scenario(self, scenario_id: str) -> Any:
        if scenario_id not in self._by_id:
            self._by_id[scenario_id] = self._inner.get_scenario(scenario_id)
        return self._by_id[scenario_id]


@lru_cache(maxsize=1)
def cached_scenario_repository() -> CachedScenarioRepository:
    """The product composition (`build_scenario_repository()`), read once per test process."""
    from assetops_backend.scenarios.composition import build_scenario_repository

    return CachedScenarioRepository(build_scenario_repository())
