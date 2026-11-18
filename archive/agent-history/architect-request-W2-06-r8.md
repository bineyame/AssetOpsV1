# Architect request: W2-06 review findings (r8)

You are the AssetOps Architect. Read:
- `.ai/ROLE_CONFIG.md`: the sections "Mockup drives the design; implementers never decide" and "Token Efficiency";
- `.agent/W2-06-build-spec.md`, with all rulings through r7;
- `.agent/W2-technical-design-ev.md`;
- `.agent/W2-06-review.md`, the independent first review: ACCEPT WITH FIXES.

The code is on branch `task/W2-06-ev-assessment` at `5f90c3a6`. Inspect it with `git show`.

For each of H1, M1, M2 and M3, rule the exact fix as a concrete artifact:
- a literal predicate or SQL;
- the window-selection or re-head rule, written as pseudocode;
- the per-record source-class rule, with a table showing how each combination maps to a status, reason and copy;
- a completeness-chip derivation table, from exact uses to chips;
- which evidence the Finding `Record {short id}` line names, with the exact copy.

For each fix, also name the regression test that proves it, and say whether any of the six W2-05b manifests or the R12 vectors file must change. If a fix changes the vectors, give the literal expected values.

**H1 constraint:** no selected window may read CURRENT while a wider or replacing selection supersedes its basis.

Also confirm the Low items: `limit` with non-ASCII digits must return 422 `EV_PARAMETER_INVALID`, or name the correct code; and add a packet note on the SQL-seeded trigger tests.

Append everything to `.agent/W2-06-build-spec.md` as "Review rulings (r8)", amending `D-2026-10-18-w2-06-07-buildspec`. Write nothing else. Do not commit.
