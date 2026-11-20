"""3B1: the structure registry (spec `specs/3B1-structure-registry/spec.md`).

`registry` holds the records and `REGISTRIES`; `rows_mini_grid` the mini-grid rows;
`expressions` the expression language (`Expr`, a contract for 3B3); `check` the
start-up check. `registry` is imported first because the rows import its records.
"""

from assetops_backend.structure import registry  # noqa: F401  (load order: records before rows)
