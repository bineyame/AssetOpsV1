"""Domain packs: the model rules that are specific to a kind of installation.

Shared time, state and boundary mechanisms never branch on pack, site kind or
concrete component type (`.ai/ARCHITECTURE.md` Domain Reuse Boundary). Mini-grid
rules live here, behind the pack boundary, and the kernel consumes them through
`ModelSpec` without knowing which pack produced one.

One pack today: `fuel`, the minimal fuel world.
"""

__all__: list[str] = []
