"""The shared causal kernel: time, state, events and the boundary cycle.

`execute` walks one frozen Draft's interval and returns a private trajectory.
`model` holds what a model can do, as a table of executable handlers whose
grouping IS the advertised supported set rather than a second declaration of it.

Nothing here reads a document, a Site or a store. What it consumes is
`assetops_contracts.world_inputs.FrozenWorldInputs`, built by the neutral host
adapter from a frozen run and the versioned definition it names.
"""

__all__: list[str] = []
