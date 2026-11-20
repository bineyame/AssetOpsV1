"""The world generator core (DS1a, `specs/DS1-history-generator/spec.md` §4).

Generates month-grain history for the demo Sites from declared rules, never from
stated figures. Standard library only: no binary floating point, no randomness, no
clock and no environment reads. Every number is a `Fraction` until it is rounded
once into an integer leaf; every seed comes from a scope digest.

Modules: `view` (the allowlisted view of a manifest), `canonical` (bytes and
digests), `scope` (scope inputs, digests and seeds), `allocate` (exact
largest-remainder allocation), `leaves` (the money leaves; the single mapping point
the canonical format replaces), `months` (calendar), `history` (the rule engine).
"""

GENERATOR = "assetops_simulator.world/1"

__all__ = ["GENERATOR"]
