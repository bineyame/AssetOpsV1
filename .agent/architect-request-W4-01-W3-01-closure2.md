# Architect request: close the remaining spec items for W4-01 and W3-01 (closure 2)

You are the AssetOps Architect. Read:
- `.agent/W4-01-W3-01-closure-check.md`, which lists 13 open items: 5 in W4-01 and 8 in W3-01. D2, D3 and D6 are among them.
- The two build specs and the `D-2026-10-20-*` decisions.
- The merged code each item cites.

For every open item, check it against the code, then answer it with a concrete artifact. The examples that come up repeatedly:
- the exact snapshot keys that actually exist in `0016_action_store.py` and its Python writer. If `action_title` or `success_criterion` do not exist, say where the values come from, or give the honest-missing copy;
- the exact `detail` keys that the resolver in `evidence/source_provenance.py` emits;
- the `selected_revision_ids` definition for an Action row and for a W4 case revision;
- the commit (slice and commit number) that owns the shared `public_provenance.py` patch.

Append to each spec as "Review closure 2 (2026-10-20)", and amend decisions where needed. End each spec with this line: "No item in the closure check remains open."

Write only those files. Do not commit.
