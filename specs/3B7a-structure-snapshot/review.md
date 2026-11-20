# 3B7a units 1-3 review, round 1 (discovery, W5)

Reviewer: Claude (fresh; not the author), 2026-11-20. Branch `task/3B7a-snapshot` at `260db0daf`, worktree
`/opt/assetecon/AssetOpsV1-3b7a`, read only. Against spec rev 3, rulings D-3B7A.1-15, reviewer guide rev 2, packet
including "Fix round 1" and guard block (A)-(E).

## Summary (verdict: ACCEPT WITH FINDINGS FIXED ON THE BRANCH)

- Served read is honest on every path I traced: every `SERVED` computes RECORDS (stamps + held kinds), MONTH_CLOSED
  and RULES; FORMAT/STRUCTURE_VERSION never decode; nothing recomputed on read (only `stale`, `kinds.of`, `compose`).
- Build reads at one instant (every read passes `known_at=as_of`); k, n and `out` per D-3B7A.15; `untracked` right;
  migration 0066 chain/downgrade right; code digest moved per D-3B7A.13; `UNKNOWN_SNAPSHOT` per Q3.
- Guard block (A)-(E): additive (40 added, 0 removed), `$snapshotWriter` untouched, each part shown failing,
  (E) now also by a code plant (adapter INSERT deleted).
- F1 Medium (spec gap, Architect): the code digest skips `assetops_contracts`, which the build's values import
  (`parse_record`, `LEAF_FACTORS`, units). A contracts change leaves an old snapshot served as current (plant shown).
- F2 Medium (missing test): building `held_kinds` at "now" instead of `as_of` passes all 23 tests.
- F3 Low: `verify` reports any ValueError/LookupError raised during the rebuild as `UNKNOWN_SNAPSHOT`.
- F4 Low: composition leaks three engines if `rules_digest()` raises.
- Checks: no-database 29 passed; Postgres 7 passed (`--db`); 3 code plants + 3 guard plants; arch check shows only
  the 4 expected pre-block failures; workflow check passed. Merge to main conflicts only in 3 index/state docs.

## Findings

### F1 - Medium - acceptance gap in the ruling, not a build defect
`backend/assetops_backend/structure_snapshot/adapters/code_digest.py:17,25,55` (`ROOT_PACKAGE = "assetops_backend"`).
- What: the closure keeps only `assetops_backend` modules. The build's values import `assetops_contracts` code:
  `commercial/months.py:25` (`LEAF_FACTORS`, `parse_record`, `loads_canonical`: how stored records become month
  amounts and leaf units), `structure/targets/lines.py:24` (`parse_record`), `structure/check.py:26`
  (`LEAF_FACTORS`, `STRUCTURE_KEYS`, `leaves_of`), units in `rows_mini_grid`, `registry`, `evaluate`, `expressions`.
- Shown: scratch copy, build with the running digest, append one line to
  `contracts/assetops_contracts/canonical/factors.py`, read in a new process: `built==running True`, Site reasons
  `()`, portfolio reasons `()`. The month stamps hash stored rows, so they do not catch it either.
- Why: D-3B7A.11's class is "a value changed by code"; a parser or factor-table change in contracts changes served
  figures with no reason given (decisions-register item 19). The ruling text says "every `assetops_backend` module",
  so the builder followed it; the gap is the ruling's.
- Fix: Architect amends D-3B7A.11 to cover `assetops_contracts` (one more root package and its directory, passed to
  the adapter by the composition); test 11(b) asserts `assetops_contracts.canonical.factors` is in the closure and
  11(c) shows a contracts byte change moves the digest. Small; fits this branch.

### F2 - Medium - missing test (one instant, held kinds)
`backend/assetops_backend/structure_snapshot/build.py:99`; test `test_4c_one_build_one_instant` (`tests/...:354`).
- What: plant `held_kinds=tuple(self._kinds.of(tenant_id, site.site_id))` (no `known_at`): 23 passed. Test 4(c)
  checks the one instant for stamps and values only.
- Why: if it regresses, a first record of a new kind ingested after `as_of` is frozen as "held" while the values
  lack it; the serve then sees no difference and an incomplete figure reads as current (the D-3B7A.12 class).
- Fix: in 4(c) (or a 4(d) variant), ingest the Mto charge before a build whose clock is `AS_OF`; assert the Mto
  row's `held_kinds` lacks `CHARGE` and the read is immediately `RECORDS` with `changed_kinds == ("MTO-001:CHARGE",)`.

### F3 - Low - honesty of the command's refusal
`backend/assetops_backend/build_structure_snapshot.py:93`.
- What: `except (LookupError, ValueError)` wraps the whole `verify`, rebuild included. `StructureError` is a
  `ValueError` and `KeyError` a `LookupError`, so a failure while rebuilding prints "No portfolio snapshot of this
  organisation has that id." (exit 2) for an id that exists.
- Why: Q3 says "refused before any rebuild"; a real rebuild fault would be misreported to the analyst.
- Fix: resolve the row first (`store.get` + the portfolio check) inside the narrow `try`, then call the rebuild
  outside it; or have `verify` raise a dedicated `UnknownSnapshot`. Add a test with a rebuild that raises.

### F4 - Low - disposal on a builder failure
`backend/assetops_backend/structure_snapshot/composition.py:67`.
- What: `rules_digest()` (file reads, can raise `OSError`/`SyntaxError`) runs after the three services are built,
  outside any `try`; a failure leaks all three engines. Reviewer-guide probe "Disposal".
- Fix: compute `rules` first, or wrap the post-build wiring and call `dispose()` on failure.

## Notes (no change asked)
- Plant "portfolio RULES checks only its own row" survived, but it is equivalent: a portfolio row and its Site rows
  always come from one build with one digest. Not a finding.
- Postgres test 1 reuses the no-database checks with synthetic Thika (n = 4); the command path (test 3) asks the
  three real Sites. D-3B7A.15 says "the Postgres world asks three"; the n = 3 snapshot's `asked` is not asserted.
- Test 3 checks the actual side's `out` codes as a set and not Thika's reason; equality with the fresh
  `StructureRead.portfolio` covers both.
- The packet's fix-round runs (252, 79) and guard evidence name no revision; the files postdate the code change and
  match `260db0daf` by content, but the packet should say so.
- The builder showed (E) by breaking the guard's pattern, not the adapter as D-3B7A.13 asked; my code plant closes it.

## Guard block (A)-(E), the text the owner approves
- Additive: `block.diff` (identical in `build-u1-3/` and `fix-r1/`): 40 added lines, 0 removed. `guard-original.ps1`
  equals the branch's `tools/checks/configuration-persistence.ps1` byte for byte; the branch diff has no `tools/` change.
- `$snapshotWriter`: no line naming it is added or changed (only a comment mentions it).
- (A) domain entry, (B) names and pattern, (C) one `$pgWriters +=` line, (D) the two checks in the commercial pattern,
  (E) anti-vacuity. Pattern is anchored, so `ON CONFLICT`, `RETURNING` and `SELECT` sources fail.
- My runs (scratch git copy of `260db0daf`, block applied with `patch`):
  - clean: `failures: 0`;
  - R-E, adapter `_INSERT` deleted: 1 failure, "Rule 8 found no INSERT INTO structure_snapshot ... vacuous";
  - R-G4, `ON CONFLICT DO NOTHING` added to the adapter INSERT: 2 failures (the plain-INSERT rule and (E));
  - R-G5, `DELETE FROM structure_snapshot` in `build.py`: 1 failure, "A second product database writer".
- Builder's G1, G2 (2), G2b, G3 (3 existing) and (E) outputs in `fix-r1/guard-plants.txt` read as claimed.

## Checks run (revision `260db0daf`)
- Module paths: `assetops_backend` and `assetops_contracts` resolved to the worktree (PYTHONPATH backend, contracts,
  simulator); scratch runs resolved to the scratch copy.
- `heavy-slot.sh -- pytest tests/test_3b7a_structure_snapshot.py tests/test_3b7a_site_inputs_seam.py`: 29 passed.
- `heavy-slot.sh --db -- pwsh tools/run-host-tests.ps1 -- backend/tests/test_3b7a_structure_snapshot_postgres.py`:
  7 passed in 26.89 s.
- Code plants, in scratch `rev3b7a-r1-1795198035`:
  - P1, `structure/sources.py` `ASSUMPTION_WORDS["diesel_price"]` changed between a build and a read in a new
    process: digest moved, Site and portfolio reasons `("RULES",)`;
  - P2 is F1;
  - P3 is F2;
  - P4 is equivalent (Notes).
  - Each was restored; `diff -rq` against the worktree is clean.
- `check-architecture.ps1`: only the 4 expected persistence failures without the block (adapter import outside a
  domain, sqlalchemy x2, second writer), as the packet says. `check-agent-workflow.ps1`: passed.
- Builder's runs cited, not rerun: no-database 252 passed, Postgres 79 passed (3A1, 3A2, 3A4, 4b, 5a, 3B3 read),
  plants V1-V16 and R6 (`build-u1-3/plants.txt`), guard G1, G2, G2b, (E).
- `git merge-tree main HEAD`: conflicts in `.ai/state/data.md`, `.ai/state/index-2.md` and `specs/INDEX.md`
  (append lines; merge preparation). The 0066 to 0067 to 0068 chain matches 3A6's and 3A7's specs on `main`.

## Not verified
- Full suite and `select-tests`: left to the coordinator (migration means full mode).
- check-all with the block in the repo file: waits for owner approval.

## Residual risk the packet does not name
- F1 beyond contracts: any value input that is not Python (none found in `structure/` or `commercial/` today) would
  also fall outside the digest. A grep of the closure found file reads only in adapters outside the build path.
- A Site added to a tenant after a build is not in the frozen `asked`, and the portfolio stamp (portfolio-level
  records only) does not change. The portfolio is served as current with the old n until rebuilt. Name it for 3B7b.
- The `.ai/state/data.md` entry still says "spec rev 2, rulings D-3B7A.1-12" and lists Q1-Q3 as open; refresh it
  at merge.
