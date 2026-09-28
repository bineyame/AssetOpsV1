"""The reporting path: private truth becoming, or failing to become, a reading.

A separate component from the kernel, which is what the task asked for and what
v4 sections 6 and 11.1 require. The kernel evolves a world and samples it; this
turns a sample into what a configured device published, or into the fact that
nothing was published and why.

Separate is structural rather than a file layout. The transform is handed the
boundaries a kernel produced and a `FrozenReportingInputs` that has no field a
stock, a bound or a cause could arrive in, so it cannot move the world - and the
kernel is handed a `FrozenWorldInputs` that has no field a cadence, a bias or a
dropout could arrive in, so it cannot see the reporting path. The two records are
what make "the same world, a changed report series" a fact about the code rather
than a claim about a caller.

One module: `transform`.
"""

__all__: list[str] = []
