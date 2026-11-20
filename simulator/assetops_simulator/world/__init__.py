"""The world generator core (DS1a, `specs/DS1-history-generator/spec.md` §4).

Generates month-grain history for the demo Sites from declared rules, never from
stated figures. Standard library and `assetops_contracts` only: no binary floating point, no randomness, no
clock and no environment reads. Every number is a `Fraction` until it is rounded
once into an integer leaf; every seed comes from a scope digest.

Modules: `view` (the allowlisted view of a manifest), `canonical` (bytes and
digests), `scope` (scope inputs, digests and seeds), `allocate` (exact
largest-remainder allocation), `leaves` (the money record fields), `months`
(calendar), `history` (the rule engine), `records` (DS1b: the canonical v1 money
records written from the view and the history).
"""

GENERATOR = "assetops_simulator.world/1"

__all__ = ["GENERATOR"]
