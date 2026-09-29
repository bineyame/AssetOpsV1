"""The simulated gateway: generated readings becoming canonical source envelopes.

v4 section 11.2. A separate component from the observation transform, exactly as
the transform is separate from the kernel: the transform decides what a device
reported, and the gateway decides what of that is PUBLISHED toward AssetOps and
in what canonical form. Sensor behaviour changes reports; gateway behaviour
changes publication; neither changes the world.

Two modules: `mappings`, the shipped allowlist, and `publish`, the conversion.
"""

__all__: list[str] = []
