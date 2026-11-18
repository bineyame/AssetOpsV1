# W6-01 A1Q sweep: W5-01 and W5-03 guard and composition ownership

*Produced by Claude Architect under the 2026-10-22 Codex-reset exception; Codex to review retrospectively.*

**Scope.** This sweep checks the W5-01 and W5-03 unit cards for the gap class that stopped W6-01 A1: a unit that adds a PostgreSQL reader or writer, adapter, router or route without listing the guard files and composition files it must edit.

**Sources.** Cards: `.agent/W5-01-build-spec.md` and `.agent/W5-03-build-spec.md`, byte-identical to `main` at `25814281`. Guards: `tools/checks/*` and `tools/writer_guard_probes.py` on that same base.

**This file edits nothing.** Another Architect is amending W5-01 in a separate worktree, so W5 files are not edited here. Each finding below gives literal amendment text for the W5 Architect to apply to its card, closure table and decision.

**Result: 11 findings.**

| Severity | Count | Meaning |
| --- | --- | --- |
| Blocking | 4 (W5S-1, W5S-3, W5S-5, W5S-7) | `check-all` would fail, or the builder must choose a file outside its list |
| Implementer-decision | 5 (W5S-2, W5S-4, W5S-6, W5S-8, W5S-11) | Wiring or ownership is named but not literal |
| Guard-literal notes | 2 (W5S-9, W5S-10) | Constraints the cards do not state |

Page units C2, C3, C5, E2, E3, E4 and E6 already list `App.tsx`, `operatorSiteRoutes.ts`, the frames they mount and, where a tab changes, `navigation-truthfulness.ps1` and `navigation-rail-fixtures.ps1`. They need nothing beyond W5S-10.

## Guard facts used

- `analytics` is a `$domains` entry (`tools/checks/configuration-persistence.ps1:116-127`).
- **Rule 2** (`:254-305`) bans the following inside `backend/assetops_backend/analytics/` outside `adapters/`:
  - any `sqlalchemy`, `psycopg`, `alembic`, `yaml`, `pathlib` or `sqlite3` import;
  - any text matching `open\(` in any letter case. The pattern has no word boundary, so identifiers such as `is_open(` also fail.
- **Rule 8** (`:829-836`) admits a driver import only in `$pgWriters` and `$pgReaders`. Any SQL write outside `$pgWriters` fails as "A second product database writer".
- **Every writer is a policy set.** Each `$pgWriters` entry also needs the following, or rule 8 reports the policy unproven:
  - `$pgWritesSeen` and `$pgDriverSeen` entries (`:879-884`);
  - an owned-table list with an insert-only check and per-table anti-vacuity (mini-decision precedent `:818-823`, `:938-941`, `:1080-1095`, `:1315-1320`);
  - probe names registered at `:1486-1491` and present in `tools/writer_guard_probes.py`.
- `tools/checks/analytic-declaration.ps1` requires that any module defining a module-level `ANALYTIC_ID` be declared in `analytics/declaration.py`. It also bans `import_module(` in `analytics/`.
- The HTTP scan (`configuration-persistence.ps1:1533-1550`) refuses these tokens in `main.py` and every `*_api.py`:
  - `register_publication`, `register_authored`, `register_run`;
  - `authored_record`, `simulation_records`;
  - `publish_source`, `evidence_publication`, `batch_publication_link`, `run_attestation`;
  - `evidence.publication`, `runs.source_publication`.
- Caller-connection reads already exist:
  - `ColdReadService.accepted_on(c, t, s, ids, after=None, limit=None)` (`analytics/adapters/postgres_assessment_store.py:2468`) returns `id`, `record_kind`, `source_time`, `role`, `normalized_value_text`, `outcome` and more.
  - `EvReadService.accepted_on(c, snap)` (`:3001`) returns `role`, `value`, `source_time`, `connector_id`, `asset_id` and `quality`.
  - `EvReadService.foundation_on(c, snap)` is at `:2979`.

## Findings

### W5S-1 (W5-01 C1, blocking): door-event read placement

C1's derivation table says "add the read in `analytics/cold_depth.py`". A SQL read there fails rule 2 and rule 8, but the C1 file list has neither an adapter nor a guard edit.

Replace the sentence "C1 reads event kind and source time for the exact selected accepted `door_event` evidence IDs from the Site-scoped evidence ledger on the same REPEATABLE READ connection (add the read in `analytics/cold_depth.py`)" with:

> C1 reads event kind and source time for the exact selected accepted `door_event` evidence IDs by calling the existing caller-connection `ColdReadService.accepted_on(c, t, s, ids)` (`analytics/adapters/postgres_assessment_store.py:2468`) on the same REPEATABLE READ connection. The kind is the returned `record_kind` (`DOOR_OPEN` or `DOOR_CLOSE`) and the time is `source_time`. `analytics/cold_depth.py` holds:
>
> - no SQL text;
> - no `sqlalchemy`, `psycopg`, `alembic`, `yaml`, `pathlib` or `sqlite3` import;
> - no text matching `open\(` in any case;
> - no `import_module(`;
> - no module-level `ANALYTIC_ID`.
>
> These are rule 2 and rule 8 of `tools/checks/configuration-persistence.ps1` and rule 1 of `tools/checks/analytic-declaration.ps1`. C1 makes no `$pgReaders` edit.

### W5S-2 (W5-01 C1, implementer-decision): composition

C1 lists `main.py` but not the wiring. Append to the C1 file paragraph:

> Lane A wiring in `main.py`:
>
> - add `from assetops_backend.analytics.cold_depth import ColdDepthReadService` and `from assetops_backend.cold_depth_api import build_cold_depth_router`;
> - directly after the `app.include_router(build_cold_site_router(...))` call, add:
>   `# W5-01a C1 (Lane A): selected cold Cooling and Health depth on the W2-03 read service; typed 503 without a database.`
>   `app.include_router(build_cold_depth_router(registry, None if cold_reads is None else ColdDepthReadService(cold_reads)))`.
>
> No edit to `analytics/composition.py`: `main.py` already holds `cold_reads`.

### W5S-3 (W5-01 C4, blocking): new writer without guard edits

`cold_scenarios/store.py` INSERTs `cold_scenario` and `cold_scenario_revision`. C4's list has neither `tools/checks/configuration-persistence.ps1` nor `tools/writer_guard_probes.py`, so rule 8 fails with "Database driver imported outside" and "A second product database writer".

Add both files to C4 (Lane A) and append this paragraph:

> **C4 rule-8 writer policy (literal).**
>
> 1. **Writer and tables.** In `tools/checks/configuration-persistence.ps1`, after line 823 (`foreach ($table in $decisionTables) { $decisionInsertsSeen[$table] = 0 }`), insert:
>
>    ```powershell
>    # W5-01b C4 (migration 0032): the authored cold scenario store is the sole runtime writer of the two 0032 tables,
>    # INSERT-only (no UPDATE, DELETE, upsert, TRUNCATE, MERGE, COPY or DDL), and it writes no other table. Each table
>    # keeps at least one owner INSERT in the store (anti-vacuity below).
>    $coldScenarioWriter = "$backendRoot/cold_scenarios/store.py"
>    $coldScenarioTables = @('cold_scenario', 'cold_scenario_revision')
>    $coldScenarioInsertsSeen = @{}
>    foreach ($table in $coldScenarioTables) { $coldScenarioInsertsSeen[$table] = 0 }
>    ```
>
> 2. **Writer tallies.** Append `$coldScenarioWriter` as the last element of `$pgWriters`. Append `; $coldScenarioWriter = 0` inside the `$pgWritesSeen` literal and `; $coldScenarioWriter = $false` inside the `$pgDriverSeen` literal.
>
> 3. **Forbidden-line check.** After the mini-decision forbidden-line block (`:938-941`), insert:
>
>    ```powershell
>                if ($module.Path -eq $coldScenarioWriter -and $line -match $actionForbidden) {
>                    $failures.Add("The cold scenario store never updates, deletes, truncates, upserts or runs DDL; " +
>                        "$($module.Path):${lineNumber}: $($line.Trim()).") | Out-Null
>                }
>    ```
>
> 4. **Statement check.** After the mini-decision statement block (`:1080-1095`), insert:
>
>    ```powershell
>                    if ($module.Path -eq $coldScenarioWriter -and -not (
>                            $line -match '(?i)\bINSERT\s+INTO\s+([a-z_]+)\s*\(' -and $coldScenarioTables -contains $Matches[1].ToLowerInvariant())) {
>                        $failures.Add(("The cold scenario store only inserts into $($coldScenarioTables -join ', ') " +
>                            "(append-only); $($module.Path):${lineNumber}: $($line.Trim()).")) | Out-Null
>                    }
>                    if ($null -ne $target -and $coldScenarioTables -contains $target) {
>                        if ($module.Path -ne $coldScenarioWriter) {
>                            $failures.Add(("Only $coldScenarioWriter writes cold scenario table '$target'; " +
>                                "$($module.Path):${lineNumber}: $($line.Trim()).")) | Out-Null
>                        } elseif ($line -notmatch '(?i)^INSERT\s+INTO\b' -or $line -match '(?i)\bON\s+CONFLICT\b') {
>                            $failures.Add(("Cold scenario table '$target' is insert-only: no UPDATE, DELETE, TRUNCATE, " +
>                                "MERGE, COPY or upsert from any module; $($module.Path):${lineNumber}: $($line.Trim()).")) | Out-Null
>                        } else {
>                            $coldScenarioInsertsSeen[$target]++
>                        }
>                    }
>    ```
>
> 5. **Anti-vacuity.** After the mini-decision anti-vacuity loop (`:1315-1320`), insert:
>
>    ```powershell
>        foreach ($table in $coldScenarioTables) {
>            if ($extractorRan -and $coldScenarioInsertsSeen[$table] -lt 1) {
>                $failures.Add(("Rule 8 found no INSERT INTO $table in $coldScenarioWriter, so the cold scenario insert-only " +
>                    "check is vacuous. Update the check, do not delete it.")) | Out-Null
>            }
>        }
>    ```
>
> 6. **Probe names.** After the mini-decision probe names (`:1486-1491`), insert:
>
>    ```powershell
>        # W5-01b C4: the cold scenario writer policy fails closed the same way.
>        foreach ($table in $coldScenarioTables) {
>            $workProbeNames += @("controls cold-scenario $table insert", "cold-scenario $table foreign insert",
>                "cold-scenario $table update", "cold-scenario $table delete", "cold-scenario $table upsert",
>                "cold-scenario $table owner insert unseen")
>        }
>        $workProbeNames += @('cold-scenario truncate')
>    ```
>
> 7. **Probe corpus.** In `tools/writer_guard_probes.py`:
>
>    - after `DECISION = f"{B}/mini_decisions/store.py"`, add `COLD_SCENARIO = f"{B}/cold_scenarios/store.py"`;
>    - add one docstring `Sets:` bullet: ``- `cold-scenario <table> ...`: W5-01b C4 (migration 0032) two cold scenario tables, the same family as `decision`, owned by `cold_scenarios/store.py`; `cold-scenario truncate`; `controls cold-scenario <table> insert` must pass.``;
>    - after the `decision truncate` entry, add the block below.
>
>    The guard searches for each literal `("<name>"`, so every name is written out, never formatted.
>
>    ```python
>    # W5-01b C4 (migration 0032): the cold scenario store alone INSERTs both cold scenario tables, which no module
>    # updates, deletes, upserts, truncates, merges or copies; each table keeps at least one owner INSERT.
>
>    def _cold_scenario_only(table: str) -> str:
>        return f"Cold scenario table '{table}' is insert-only"
>
>
>    def _cold_scenario_unseen(table: str) -> tuple:
>        return (COLD_SCENARIO, ("replace", f'"INSERT INTO {table} (', f'"SELECT * FROM {table} WHERE ('),
>                f"Rule 8 found no INSERT INTO {table} in ")
>
>
>    NEGATIVE += [
>        ("cold-scenario cold_scenario foreign insert", FINDING, _work_foreign("cold_scenario"), "writes cold scenario table 'cold_scenario'"),
>        ("cold-scenario cold_scenario update", COLD_SCENARIO, split("cold_scenario", "site_id = :s WHERE tenant_id = :i"), _cold_scenario_only("cold_scenario")),
>        ("cold-scenario cold_scenario delete", COLD_SCENARIO, _work_delete("cold_scenario"), _cold_scenario_only("cold_scenario")),
>        ("cold-scenario cold_scenario upsert", COLD_SCENARIO, _work_upsert("cold_scenario"), _cold_scenario_only("cold_scenario")),
>        ("cold-scenario cold_scenario owner insert unseen", *_cold_scenario_unseen("cold_scenario")),
>        ("cold-scenario cold_scenario_revision foreign insert", FINDING, _work_foreign("cold_scenario_revision"), "writes cold scenario table 'cold_scenario_revision'"),
>        ("cold-scenario cold_scenario_revision update", COLD_SCENARIO, split("cold_scenario_revision", "site_id = :s WHERE tenant_id = :i"), _cold_scenario_only("cold_scenario_revision")),
>        ("cold-scenario cold_scenario_revision delete", COLD_SCENARIO, _work_delete("cold_scenario_revision"), _cold_scenario_only("cold_scenario_revision")),
>        ("cold-scenario cold_scenario_revision upsert", COLD_SCENARIO, _work_upsert("cold_scenario_revision"), _cold_scenario_only("cold_scenario_revision")),
>        ("cold-scenario cold_scenario_revision owner insert unseen", *_cold_scenario_unseen("cold_scenario_revision")),
>        ("cold-scenario truncate", COLD_SCENARIO, '_OPS02 = "TRUNCATE cold_scenario"\n',
>         "The cold scenario store never updates, deletes, truncates, upserts or runs DDL"),
>    ]
>    WRITER_CONTROLS += [
>        ("controls cold-scenario cold_scenario insert", COLD_SCENARIO, _work_control("cold_scenario")),
>        ("controls cold-scenario cold_scenario_revision insert", COLD_SCENARIO, _work_control("cold_scenario_revision")),
>    ]
>    ```
>
> 8. **Store style.** Every store INSERT is one string literal beginning `"INSERT INTO <table> (`, so the owner-insert-unseen probe can find it. The store has no `ON CONFLICT` anywhere: the `$actionForbidden` line check refuses it, so idempotent replay is a SELECT followed by a caught unique violation, as in `mini_decisions/store.py`.
>
> 9. **Checks.** C4 runs `tools/check-all.ps1` and `python tools/writer_guard_probes.py --seam` on the names starting `cold-scenario` and `controls cold-scenario`, on a clean committed tree.

### W5S-4 (W5-01 C4, implementer-decision): composition

Append to C4:

> Lane A wiring in `main.py`:
>
> - add `from assetops_backend.cold_scenarios.service import ColdScenarioService`, `from assetops_backend.cold_scenarios.store import PostgresColdScenarioStore` and `from assetops_backend.cold_scenarios_api import build_cold_scenarios_router`;
> - after the C1 mount, add:
>
>   ```python
>       # W5-01b C4: authored cold scenarios. Writes need the two explicit decision injections; reads use the cold gate.
>       cold_scenario_store = PostgresColdScenarioStore.from_url(database_url()) if cold_reads is not None else None
>       if cold_scenario_store is not None:
>           app.router.on_shutdown.append(cold_scenario_store.dispose)
>       app.include_router(build_cold_scenarios_router(
>           registry, None if cold_scenario_store is None else ColdScenarioService(cold_scenario_store, cold_reads),
>           command_access=mini_decision_command_access, principal=mini_decision_principal))
>   ```
>
> `cold_scenarios` is a top-level package like `mini_decisions`, not a `$domains` entry and not an adapter layer, so `main.py` may import its store directly.

### W5S-5 (W5-03 E1a, blocking): availability read placement

E1a puts `analytics/ev_availability.py` above the adapter layer and gives no read path for accepted `ev_connector_state` rows. The cards also call the calculation version `ev-availability/1`. If that becomes a module-level `ANALYTIC_ID`, the analytic-declaration guard fails.

Append to the E1a file list:

> Accepted `ev_connector_state` rows come only from the existing caller-connection `EvReadService.accepted_on(c, snap)` (`analytics/adapters/postgres_assessment_store.py:3001`; fields `role`, `value`, `source_time`, `connector_id`, `asset_id`, `quality`). The Foundation comes from `EvReadService.foundation_on(c, snap)` (`:2979`). Both run on the selected snapshot connection.
>
> `analytics/ev_availability.py` holds:
>
> - no SQL text;
> - no `sqlalchemy`, `psycopg`, `alembic`, `yaml`, `pathlib` or `sqlite3` import;
> - no text matching `open\(` in any case;
> - no `import_module(`;
> - no module-level `ANALYTIC_ID`.
>
> The version constant is `CALCULATION_VERSION = "ev-availability/1"`. No `$pgReaders` edit. If a needed row is not exposed by an existing caller-connection method, stop for an Architect amendment.

### W5S-6 (W5-03 E1b, implementer-decision): composition belongs in `financials/composition.py`

E1b composes the W2-07 money and energy selection, which needs `EvMoneyReads` from `financials/adapters/postgres_consequence_store.py`. Rule 1 lets only `financials/composition.py` import that adapter, and the W2-07 precedent is `financials/composition.py:106-114` `build_ev_site_read_service`. E1b lists only `main.py`.

Add `backend/assetops_backend/financials/composition.py` to E1b (Lane A) and append:

> E1b appends to `financials/composition.py`:
>
> ```python
> def build_ev_depth_read_service(database_url: str):
>     """W5-03a E1b: EV Availability, Energy and Health depth over W2-06's `EvReadService` and the SELECT-only EV money
>     reads, both on the one read connection (W2-07's shared selector)."""
>     from assetops_backend.analytics.composition import build_ev_read_service
>     from assetops_backend.analytics.ev_depth import EvDepthReadService
>     from assetops_backend.ev_site_reads import EvSiteReads
>     from assetops_backend.evidence.composition import build_link_rows_reader
>     from assetops_backend.financials.adapters.postgres_consequence_store import EvMoneyReads
>
>     reads = build_ev_read_service(database_url)
>     return EvDepthReadService(reads, EvSiteReads(reads, EvMoneyReads(build_link_rows_reader())))
> ```
>
> `EvDepthReadService` exposes `dispose()` delegating to `reads.dispose()`. In `main.py`, directly after the `build_ev_site_router` include, add:
>
> ```python
>     # W5-03a E1b (Lane A): selected EV Availability, Energy and Health depth; typed 503 without a database.
>     ev_depth_reads = build_ev_depth_read_service(database_url()) if database_url() else None
>     if ev_depth_reads is not None:
>         app.router.on_shutdown.append(ev_depth_reads.dispose)
>     app.include_router(build_ev_depth_router(registry, ev_depth_reads))
> ```
>
> `analytics/ev_depth.py` obeys the same rule-2, rule-8 and analytic-declaration limits as W5S-5.

### W5S-7 (W5-03 E5, blocking): new writer without guard edits

This is the same gap as W5S-3, for `ev_scenarios/store.py`, `ev_scenario` and `ev_scenario_revision`. Add `tools/checks/configuration-persistence.ps1` and `tools/writer_guard_probes.py` to E5 (Lane A). Append the W5S-3 paragraph with these substitutions:

| W5S-3 text | E5 text |
| --- | --- |
| `W5-01b C4 (migration 0032)` | `W5-03b E5 (migration 0034)` |
| `$coldScenarioWriter` | `$evScenarioWriter` |
| `$coldScenarioTables` | `$evScenarioTables` |
| `$coldScenarioInsertsSeen` | `$evScenarioInsertsSeen` |
| `cold_scenarios/store.py` | `ev_scenarios/store.py` |
| `'cold_scenario', 'cold_scenario_revision'` | `'ev_scenario', 'ev_scenario_revision'` |
| message words `cold scenario` / `Cold scenario` | `EV scenario` / `EV scenario` |
| probe prefix `cold-scenario` | `ev-scenario` |
| `COLD_SCENARIO` | `EV_SCENARIO` |
| `_cold_scenario_only` / `_cold_scenario_unseen` | `_ev_scenario_only` / `_ev_scenario_unseen` |
| truncate probe `"TRUNCATE cold_scenario"` | `"TRUNCATE ev_scenario"` |

Insert every E5 block directly after the corresponding C4 block. If W5-01b has not merged when E5 runs, insert after the mini-decision block instead.

### W5S-8 (W5-03 E5, implementer-decision): composition

Append to E5:

> Lane A wiring in `main.py`: add the imports `EvScenarioService`, `PostgresEvScenarioStore` and `build_ev_scenarios_router`, and after the E1b mount add:
>
> ```python
>     # W5-03b E5: authored EV scenarios. Writes need the two explicit decision injections; reads use the EV gate.
>     ev_scenario_store = PostgresEvScenarioStore.from_url(database_url()) if ev_reads is not None else None
>     if ev_scenario_store is not None:
>         app.router.on_shutdown.append(ev_scenario_store.dispose)
>     app.include_router(build_ev_scenarios_router(
>         registry, None if ev_scenario_store is None else EvScenarioService(ev_scenario_store, ev_reads),
>         command_access=mini_decision_command_access, principal=mini_decision_principal))
> ```
>
> The store resolves the `ev_consequence_revision` and tariff IDs with its own SELECTs inside its write snapshot. It is a registered writer and may hold that SQL. It imports no `financials` adapter.

### W5S-9 (C1, C4, E1b, E5, guard-literal note): HTTP scan tokens

`cold_depth_api.py`, `cold_scenarios_api.py`, `ev_depth_api.py` and `ev_scenarios_api.py` are scanned as HTTP modules (`configuration-persistence.ps1:1533-1550`). Add one sentence to each of the four cards:

> `<module>_api.py` contains none of `register_publication`, `register_authored`, `register_run`, `authored_record`, `simulation_records`, `publish_source`, `evidence_publication`, `batch_publication_link`, `run_attestation`, `evidence.publication`, `runs.source_publication` (`authored_basis` is allowed).

### W5S-10 (C2, C3, C5, E2, E3, E4, E6, guard-literal note): table and chart primitives

Add one sentence to the shared measurement section of each spec:

> Every table renders through `DataTable` (`frontend/src/ui/DataTable.tsx`; `tools/checks/shell-overflow.ps1` rule 4 refuses a bare `<table`). Every `<svg` is drawn only in the existing diagram, chart, timeline or graphics modules that rule 5 names. No page module draws its own svg.

### W5S-11 (implementer-decision): serialization of shared guard files

Three units edit `tools/checks/configuration-persistence.ps1`:

- W6-01a A1 changes the `$pgReaders` list (`.agent/W6-01-build-spec.md` §3.1 G1);
- W5-01b C4 changes the writer lists, which W5-03b E5 also does;
- C4 and E5 also both edit `tools/writer_guard_probes.py`.

Add to both W5 gate sections:

> Lane A edits to `configuration-persistence.ps1` and `writer_guard_probes.py` are additive blocks anchored on the mini-decision lines. A unit that merges after another rebases and keeps both blocks. The W6-01a `$pgReaders` line and the W5 writer blocks do not overlap.

## Closure rows for the W5 Architect

Append to `.agent/W5-01-build-spec.md` "Readiness closure":

| Review item | Closing artifact location |
| --- | --- |
| A1Q-W5S-1 | C1 derivation table: door events through `ColdReadService.accepted_on`; `cold_depth.py` rule-2/8/declaration limits |
| A1Q-W5S-2 | C1 Lane A `main.py` mount of `build_cold_depth_router(registry, ColdDepthReadService(cold_reads))` |
| A1Q-W5S-3 | C4 rule-8 writer policy: `configuration-persistence.ps1` blocks and `writer_guard_probes.py` corpus |
| A1Q-W5S-4 | C4 Lane A `main.py` store and router wiring with the decision injections |
| A1Q-W5S-9/10/11 | C1/C4 HTTP scan tokens; C2/C3/C5 DataTable/svg; shared guard-file serialization |

Append to `.agent/W5-03-build-spec.md` "Readiness closure":

| Review item | Closing artifact location |
| --- | --- |
| A1Q-W5S-5 | E1a: `EvReadService.accepted_on`/`foundation_on` only; `CALCULATION_VERSION`; rule-2/8/declaration limits |
| A1Q-W5S-6 | E1b: `financials/composition.py` `build_ev_depth_read_service` and `main.py` mount |
| A1Q-W5S-7 | E5 rule-8 writer policy (C4 blocks with EV substitutions) |
| A1Q-W5S-8 | E5 Lane A `main.py` store and router wiring with the decision injections |
| A1Q-W5S-9/10/11 | E1b/E5 HTTP scan tokens; E2/E3/E4/E6 DataTable/svg; shared guard-file serialization |

## Proposed decision line for the W5 Architect

Append this after the last `D-2026-10-22-w5-01-w5-03-buildspec` amendment in `.ai/DECISIONS.md`, but only once the card text is applied:

> Amendment to `D-2026-10-22-w5-01-w5-03-buildspec` (2026-10-22, A1Q sweep): The W5-01 and W5-03 contracts now state the guard and composition ownership the W6-01 A1Q sweep found missing. C1, E1a and E1b read only through existing caller-connection read-service methods, with no SQL, driver import or `ANALYTIC_ID` above the analytics adapter layer. C4 and E5 register their scenario stores as rule-8 INSERT-only writers, with probe corpora. C1, C4, E1b and E5 have literal `main.py` wiring, and E1b has a `financials/composition.py` builder. New HTTP modules avoid the designation tokens, and pages use the shared table and chart primitives. No build or owner acceptance is claimed.
