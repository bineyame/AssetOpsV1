# DS4 reviewer guide

Architect (Claude), 2026-11-21, rev 1. Discovery review (W5): a new mechanism that decides what a "clean, good"
database is, and one edit in the bulk load's seam. Read `spec.md`, `rulings.md`, then the diff. Done means every
question of spec §7 answers yes with evidence and every plant below fails its named test. Run nothing heavy yourself
unless a finding needs it; cite the builder's runs at the same commit (`.ai/ROLE_CONFIG.md`).

## What to check, and how

1. **The telemetry ruling is kept.** The definition says `telemetry.source` `none`; no code path reads the walkthrough
   build's output, a harness fixture or another database into a world; `read_definition` refuses any other source
   (D-DS4.1). Nothing adds a binding set to an onboarded Site.
2. **Only the product writes.** `tools/world.py` runs product commands as subprocesses and the admin statements of
   spec §3.5, nothing else (T11 scans literals; you read every `execute` call). No adapter import, no `*_api` import.
3. **Names and databases.** Every name is built by one function and checked by `permitted_database` before the first
   statement (T4); no `FORCE`; the tool never connects to a frozen template (T12 asserts `datallowconn` false; read
   where connections are opened). The packet lists every database created, kept and dropped; the kept ones are only
   the three `assetops_world_audit_*` rungs.
4. **Keys.** The parts match spec §3.2 in content and order; the clean-tree check covers every keyed path and runs
   before any key or database call (T2, T3); reuse needs both the manifest and the database; a partial is dropped
   and rebuilt (T5).
5. **Environment.** Every product step's environment is built from spec §3.5's list (T5 proves a parent `PGDATABASE`
   and real-data switch do not leak). The parity run (C5) uses the tool's environment without `DATABASE_URL`.
6. **The check is independent (W2).** C4 reads `derived-values.json` and the snapshot payload directly; the expected
   values are never computed by product code; a `None` never equals anything; zero equal values fails. T1b reads the
   manifest YAML and the derived values itself, not through the tool. C2 compares the clone with the manifest's
   census recorded at build, not with itself.
7. **The gap rule.** Step 3a sits after step 3 and before admission; days are Site-local; a refusal writes and records
   nothing; the DS3 regression (parity with the v4 batch, the pooled tests) passes unchanged (D-DS4.9).
8. **Keys of identities.** L1's key directory is 0700 under the given root; clones share it; dropping an L1 erases
   each tenant's key first and refuses while a child exists (T6, T13) (D-DS4.10).
9. **The bench says what it measured.** The report has every spec §4 row; `NOT_BUILT` rows for the option change and
   the contract-term edit; the projection labelled as one with its basis; no test asserts a time. The packet gives
   each number's meaning (spec §4) and the machine state at the start.

## Planted violations (each must fail the named test; the builder shows each failing once, in a scratch copy)

| # | Plant | Fails |
|---|---|---|
| P1 | L1's key parts omit `code` | T2 |
| P2 | `clone` uses the most recent L2 whatever its key | T6 (`WORLD_TEMPLATE_STALE`) |
| P3 | `drop` issues `DROP DATABASE ... WITH (FORCE)` | T5/T6 (no `FORCE`), T14 |
| P4 | Dropping an L1 skips `pseudonym_key erase` | T6, T13 |
| P5 | Product steps inherit the parent environment | T5 (`PGDATABASE` reaches a step) |
| P6 | The name check is skipped for clone labels | T4 (`walk1` accepted) |
| P7 | `local_days` uses UTC dates | T8, T15 |
| P8 | Step 3a runs after `bulk_admit` | T15 (ledger counts change) |
| P9 | C2 compares the check clone's census with itself | T9 |
| P10 | C4 compares the actual side only | T9 (plan-side mismatch passes) |
| P11 | C4 counts a `None` product value as equal to expected `0.0` | T9 |
| P12 | The rung is not frozen before its manifest is written | T5 (statement order), T12 (`datallowconn`) |
| P13 | A failed step still writes the rung's manifest | T5 |
| P14 | `build` reuses a database whose manifest is missing | T5 (partial rebuilt) |
| P15 | The clean-tree check is removed | T3 |
| P16 | `read_definition` accepts `telemetry.source` `"simulator"` | T1 |
| P17 | The check clone is not dropped when a check raises | T9 |

## Verdict

ACCEPT when spec §7 is all yes and P1 to P17 each failed once; findings by severity (High: a protected seam, a
permitted-name or connection rule, the check's independence, the telemetry ruling; Medium: a missing test or plant;
Low: wording). The coordinator records the verdict.
