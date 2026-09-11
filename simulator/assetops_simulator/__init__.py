"""AssetOps deterministic simulator root.

Simulator-side module root of the modular monolith. Owns simulated world state,
private truth, run execution, and gateway staging as later slices add them.

T001 scope: the root exists so dependency direction can be guarded. There is no
simulated world, no run execution, and no published output. The simulator must
never import or write into the product backend root (`assetops_backend`); the
only intended crossing is released canonical Source Envelopes consumed through
product ingestion.
"""

__all__: list[str] = []
