"""AssetOps deterministic simulator root.

Simulator-side module root of the modular monolith. Owns simulated world state,
private truth, run execution, the observation transform and, in a later slice,
gateway staging.

T021 adds the first causal kernel: `kernel/` walks the execution contract's
boundary cycle over one frozen Draft, and `packs/fuel.py` is the minimal fuel
world it executes - one tank, one generator, and the law that fuel consumed is
specific consumption times energy delivered. T022 makes that kernel steppable and
adds `observation/`, which turns the samples it takes into what a configured
device published, or into the fact that nothing was published and why. The two are
separate components, and the two records they consume are what keeps them so: a
kernel is handed no reporting parameter and the transform is handed no world
quantity.

It imports `assetops_contracts` and nothing else. The simulator must never import
or write into the product backend root (`assetops_backend`), and the only
intended crossing is released canonical Source Envelopes consumed through product
ingestion. Composition happens in the neutral `host/` leaf, which nothing imports.
"""

__all__: list[str] = []
