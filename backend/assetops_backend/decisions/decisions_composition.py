"""6a: re-exports the decisions composition for the commands, `6c` and `6f`. Imports no adapter."""
from assetops_backend.decisions.composition import DecisionsService, build_decisions

__all__ = ["DecisionsService", "build_decisions"]
