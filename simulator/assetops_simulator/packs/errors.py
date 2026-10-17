"""Errors shared by every domain pack.

`PhysicallyUnacceptable` lived in `fuel.py` until a second standalone pack
(`cold`) needed it; `fuel.py` re-exports it so existing imports are unchanged.
"""

from __future__ import annotations


class PhysicallyUnacceptable(ValueError):
    """The resolver was handed a value the world cannot have.

    Raised by a handler rather than by the kernel, because which values a state
    admits is a property of the state the model declares. The kernel turns it
    into `PHYSICAL_RESOLUTION_FAILURE` at the phase the resolver runs in.
    """


__all__ = ["PhysicallyUnacceptable"]
