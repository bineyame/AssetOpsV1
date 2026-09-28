"""The shared causal kernel: time, state, events and the boundary cycle.

`Execution` is one run in progress: a handle over the world, advanced a boundary
at a time, with the boundaries so far readable mid-flight. `start` opens one
without advancing it, and `execute` is that handle advanced to the end and
returning a private trajectory, which is what every caller that does not step
wants.
`model` holds what a model can do, as a table of executable handlers whose
grouping IS the advertised supported set rather than a second declaration of it.

Nothing here reads a document, a Site or a store. What it consumes is
`assetops_contracts.world_inputs.FrozenWorldInputs`, built by the neutral host
adapter from a frozen run and the versioned definition it names.
"""

__all__: list[str] = []
