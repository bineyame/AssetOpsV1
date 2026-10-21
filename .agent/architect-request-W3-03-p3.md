# Architect request: W3-03 P-3-1, the registry rows (r3)

Read:
- `.agent/W3-03-build-spec.md`, r2's registry part;
- `.agent/W3-03-pending-rulings.md`, P-3-1, including the node layers the builder found;
- `frontend/docs/architecture/check_v69_dependency_registry.cjs`;
- `frontend/docs/architecture/v69-dependency-registry-pilot.json` and `v69-screen-ledger.json`, including how W3-01, W3-02 and W4-02 registered their panels.

Code: `9e1a955c` on `task/W3-03-portfolio-composition`.

r2's four Portfolio panel rows fail the checker in two ways:
- The `portfolio` screen-ledger row has no `registry_dependencies`. The checker requires `P-estate-area` plus the union of the rows' `requires`.
- Every panel's `requires` must include a "ui" node and a "projection" node. Panels 1, 2 and 4 lack a projection node, and panel 3 lacks a ui node.

Give the exact literal JSON for:
- every new or reused node, with its ID, layer and any fields;
- the four panel rows;
- the screen-ledger `registry_dependencies`.

The result must make the checker pass without changing the checker. Verify by reasoning against the checker's code.

Append the result as "Run-3 registry rulings (r3)" to `.agent/W3-03-build-spec.md`. Write nothing else. Do not commit.
