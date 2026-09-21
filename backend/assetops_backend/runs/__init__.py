"""The SimulationRun domain: Draft run setup and the inputs a run freezes.

A third domain package beside `sites/` and `scenarios/`, built to the same
shape and holding the same line. A `SimulationRun` is neither a Site nor a
scenario: it has its own identity space, its own port, its own error
vocabulary, and its own store.

Nothing here executes anything. T019 freezes the inputs a later causal kernel
will consume and decides whether the selected model profile can consume them;
the kernel, the clock, the step and the trace belong to later slices.
"""
