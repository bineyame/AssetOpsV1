# 3B7a units 1-3 packet: the frozen monthly structure snapshot

Implementer (Claude, fresh), 2026-11-20. Branch `task/3B7a-snapshot` off `main` `264d7d6a7` (unit 0 merged). Commits
`54aea2c90` (unit 1), `9b94e2d07` (unit 2 + no-database tests), `1f7e3b743` (unit 3), then this packet's commit.
`USER_REVIEW_REQUIRED: false` (no screen); the guard edit needs the owner's approval (Q6/R2). Mid-build count: **3**
(`mid-build-questions.md`: Q1, Q2 stop one part each; Q3 default applied).

## Files

New: `backend/assetops_backend/structure_snapshot/` (`model`, `codec`, `untracked`, `rules_digest`, `kinds`, `store`,
`build`, `read`, `composition`, `adapters/postgres_structure_snapshot_store`), `assetops_backend/build_structure_snapshot.py`,
`migrations/versions/0066_structure_snapshot.py`, `tests/test_3b7a_structure_snapshot.py` (23),
`tests/test_3b7a_structure_snapshot_postgres.py` (7). No diff in `structure/read.py`; no existing file edited except
spec status, `specs/INDEX.md`, `.ai/state/` and the mid-build file.

## §7 questions

1. Served = fresh at "as of", field by field: test 3 (`inputs`, `actual`, `targets` object-equal per Site; `actual()` ==
   `StructureRead.portfolio`, `targets()` == `TargetRead.portfolio`; §5 literals). Yes.
2. Late invoice: 4(a) `RECORDS`, Kisiwa's stamp named, old values served; 4(b) rebuild gives om 700.00, contribution
   -250.00, current, 8 rows, first rows unchanged; 4(c) one instant; 4(d) `changed_kinds ("MTO-001:CHARGE",)`. Yes.
3. Month closed: 5(a), 5(b) `("RECORDS", "MONTH_CLOSED")`. Yes. 4. Other version/format: test 6 `REBUILD_NEEDED`. Yes.
5. No recompute: test 7 (`OnlyStale`), test 10 imports. Yes. 6. Append-only, same instant refused whole: tests 4(b), 8,
   Postgres 2 (trigger text `structure_snapshot rows are append-only`). Yes.
7. `untracked` (Mto `diesel_price`), `RULES` (11a), kinds (4d). Yes. 8. Verify at "as of", names parts: test 9. Yes.
9. Seam merged alone first; scope as listed. Yes (guard block pending, below).

## Checks (revision `1f7e3b743`; evidence `/opt/assetecon/evidence/3B7a/build-u1-3/`)

- Tests first: `tests-first.txt` (collection error before the package existed).
- No-database focused + regression (3B7a both files, 3B3 evaluate + window price, 4b1, 4b, 5a, 3A4): `252 passed in
  10.87s` (`nodb-regression.txt`).
- Postgres via `/opt/assetecon/AssetOpsV1/tools/heavy-slot.sh --db -- pwsh tools/run-host-tests.ps1`: 3B7a, 3A4, 4b,
  5a, 3B3 read, 3A2: `1 failed, 66 passed` in 35 s; the failure is Q2 (3A2 asserts 0065 is head). 3A1 (downgrade
  through 0066): `12 passed` (`pg-regression.txt`, `pg-3a1.txt`).
- Plants V1-V12, V14-V16 (two forms of V16) and R6: each fails its named test, tree clean after (`plants.txt`). V10
  is planted as a portfolio total composed from the wrong Sites (fails test 3's equality). V0: unit 0 review.
- Fast check-all: `Check failed: 1 of 40 blocking guards` - only `configuration-persistence.ps1` (`check-all-fast.txt`).
- `select-tests --base main`: full mode (548 files) because of the migration; full suite left to the coordinator.

## Guard (not applied; `tools/checks/configuration-persistence.ps1` untouched)

Without the block (repo file): 4 failures, all this package (adapter import outside every domain; driver imported
outside `$pgWriters` x2; "A second product database writer ... INSERT INTO structure_snapshot") (`guard-without-block.txt`).
With the block (a scratch copy built by `block.py`, run by `run.ps1`; diff `block.diff`, 40 added lines, 0 removed):
1 failure left, Q1 (`rules_digest.py:15: from pathlib import Path`, rule 2). Plants against it (`guard-plants.txt`):
G1 `UPDATE structure_snapshot` in the adapter -> "runs only one plain INSERT"; G2 `INSERT INTO structure_snapshot`
in the commercial adapter -> "Only ...postgres_structure_snapshot_store.py writes structure snapshot table"; G2b same
in `read.py` -> "A second product database writer"; G3 `UPDATE site_day_snapshot` in the chain writer -> its three
existing refusals. The block, in five places:

```powershell
# (A) $domains, after the "commercial" entry:
        @{
            # 3B7a (spec section 4.2; migration 0066; D-3B7A.9): the structure snapshot store. Rule 8 confines its
            # PostgreSQL writer ($structureSnapshotWriter). Only its composition imports the adapters.
            Name        = "structure_snapshot"
            Package     = "$backendRoot/structure_snapshot"
            Composition = "$backendRoot/structure_snapshot/composition.py"
            Writer      = $null
            UserRootVar = $null
            UserRootOwner = $null
        }
# (B) after `foreach ($shape in $commercialShapes.Keys) { $commercialShapesSeen[$shape] = 0 }`:
    $structureSnapshotWriter = "$backendRoot/structure_snapshot/adapters/postgres_structure_snapshot_store.py"
    $structureSnapshotTables = @('structure_snapshot')
    $structureSnapshotInsert = '(?i)^INSERT\s+INTO\s+structure_snapshot\s*\([^)]*\)\s*VALUES\s*\([^()]*\)\s*;?\s*$'
    $structureSnapshotInsertsSeen = 0
# (C) after line 1046 (`$pgWriters += $commercialWriter ...`):
    $pgWriters += $structureSnapshotWriter  # 3B7a: on its own line, as the account writer
# (D) statement loop, after the "Only $commercialWriter writes commercial table" check:
                if ($module.Path -eq $structureSnapshotWriter) {
                    if ($null -ne $target -and $structureSnapshotTables -contains $target -and
                            $line -match $structureSnapshotInsert) {
                        $structureSnapshotInsertsSeen++
                    } else {
                        $failures.Add(("The structure snapshot store runs only one plain INSERT INTO structure_snapshot " +
                            "(no UPDATE, DELETE, TRUNCATE, upsert, SELECT source or other table); " +
                            "$($module.Path):${lineNumber}: $($line.Trim()).")) | Out-Null
                    }
                }
                if ($null -ne $target -and $structureSnapshotTables -contains $target -and
                        $module.Path -ne $structureSnapshotWriter) {
                    $failures.Add(("Only $structureSnapshotWriter writes structure snapshot table '$target'; " +
                        "$($module.Path):${lineNumber}: $($line.Trim()).")) | Out-Null
                }
# (E) after the commercial anti-vacuity loop:
    if ($extractorRan -and $structureSnapshotInsertsSeen -lt 1) {
        $failures.Add(("Rule 8 found no INSERT INTO structure_snapshot statement in $structureSnapshotWriter, so the " +
            "structure snapshot writer check is vacuous. Update the check, do not delete it.")) | Out-Null
    }
```
(The scratch copy also carries one comment line per part; `block.diff` is exact.) `$snapshotWriter` and its checks are
not touched; `$pgWritesSeen`/`$pgDriverSeen` take the new key on first use (no literal edited). Not shown failing: the
anti-vacuity (E).

## Known deviations

- §5 "site_count 1 of 3 / 3 of 3": `site_count` counts n over every Site asked (four, Thika included, D-3B3.13); the
  tests assert k (1 and 3) and equality with the fresh reads, which carry n = 4.
- The command test (no database, injected service) lists Sites sorted by code (`tenant_sites`), not §5's order.
- `LATE` and the Mto charge use `produced_at` = their ingest instant (not fixed by §5).

## Residual risk and review focus

- The digest closure is 268 modules (all of `build_structure_read`'s reach): over-reports by design (D-3B7A.11).
- Q1 decides where `rules_digest` lives before the block can be applied; Q2 before `main`'s suite is green.
- Focus: `read.py` freshness paths (every `SERVED` path computes RECORDS, MONTH_CLOSED, RULES); codec decimal
  handling; `put` all-or-none in both stores.

Runbook line (coordinator adds to `Docs/engineering/operator-deep-dive-runbook.md` after ON1, R10):
`python -m assetops_backend.build_structure_snapshot build --tenant <slug> --month <YYYY-MM> --by person:<their account id>`
(the analyst, after each accepted import, and after a deploy).
