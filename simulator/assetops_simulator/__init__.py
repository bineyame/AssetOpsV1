"""AssetOps deterministic simulator root.

Simulator-side module root of the modular monolith. Owns simulated world state,
private truth, run execution and, in later slices, the observation transform and
gateway staging.

T021 adds the first causal kernel: `kernel/` walks the execution contract's
boundary cycle over one frozen Draft and returns a private trajectory, and
`packs/fuel.py` is the minimal fuel world it executes - one tank, one generator,
and the law that fuel consumed is specific consumption times energy delivered.

It imports `assetops_contracts` and nothing else. The simulator must never import
or write into the product backend root (`assetops_backend`), and the only
intended crossing is released canonical Source Envelopes consumed through product
ingestion. Composition happens in the neutral `host/` leaf, which nothing imports.
"""

__all__: list[str] = []
