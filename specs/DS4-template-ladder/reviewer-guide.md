# DS4 reviewer guide

Architect (Claude), 2026-11-21, rev 2 (handshake round 1: D-DS4.16 to D-DS4.25). Discovery review (W5): a new mechanism that decides what a "clean, good"
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
   and real-data switch do not leak); every step on a rung or clone carries that L1's key directory (D-DS4.22). C5 and
   B5 go through `harness_run` only: their own `assetops_w<c5|b5>_pt<hex>_base_test`, created before and dropped
   after, `ASSETOPS_TEST_DATABASE_URL` naming it, never the parent's and never `assetops_test` (D-DS4.20, T9).
6. **The check is independent (W2) and total (D-DS4.16).** C4 reads `derived-values.json` and the snapshot payload
   directly; the expected values are never computed by product code; `C4_CONTRACT` equals spec §2.1 cell for cell
   (read the literal against the table yourself); every payload factor is judged (no `unchecked`), `E` by exact
   equality with `None` never equal, `B` blank with its record (no zero class: D-DS4.25); `C4_KNOWN_FINDINGS` holds only the three
   D-DS4.25 lines until 4a's fix merges, then nothing, and a known finding is still a FAIL. The spike's printout in the packet matches
   §2.1, or each difference has an Architect ruling. T1b and T9b read the manifest YAML and the derived values
   themselves, not through the tool. C2 compares the clone with the manifest's census recorded at build, not with
   itself. `check_passed` is reported only while `check_inputs` are unchanged (D-DS4.21).
7. **The cover rule (D-DS4.17).** Step 7a sits after step 7 and before step 8; spans are `COALESCE(interval_start,
   source_time)` to `COALESCE(interval_end, source_time)` as in `0044_chain_events.py`; days come from
   `chain.events.local_days` and `S3_BRACKET`, imported, not re-implemented, for both grains; the union is compared
   with the cover's days, not only checked for contiguity; an unreadable or naive time is `BULK_BATCH_TIME_UNREADABLE`,
   never a traceback; a refusal writes and records nothing; `site_timezone` has no cache and no `None` branch; the DS3
   regression (parity with the v4 batch, the pooled tests) passes unchanged.
8. **Keys of identities (D-DS4.10, D-DS4.19).** L1's key directory is 0700 under the given root, created with mode
   checked, an existing one accepted only at 0700 and owned by the user; clones share it; dropping an L1 erases each
   tenant's key first and refuses while a child exists (T6, T13); the tool never opens or names a file under it, and
   no stdout, manifest, report, packet or evidence line holds a key file name or content (T5); `--state` is checked
   the same way. Nothing creates `/opt/assetecon/keys` or `/opt/assetecon/worlds` but the coordinator, after the
   owner's say-so (row 40); unit 3's real runs are dated after it.
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
| P7 | `cover_gap`'s local grain uses UTC dates | T8 (a), T15 |
| P8 | Step 7a runs after step 8's write | T15 (ledger counts change) |
| P9 | C2 compares the check clone's census with itself | T9 |
| P10 | C4 compares the actual side only | T9 (plan-side mismatch passes) |
| P11 | C4 counts a `None` product value as equal to expected `0.0` | T9 |
| P12 | The rung is not frozen before its manifest is written | T5 (statement order), T12 (`datallowconn`) |
| P13 | A failed step still writes the rung's manifest | T5 |
| P14 | `build` reuses a database whose manifest is missing | T5 (partial rebuilt) |
| P15 | The clean-tree check is removed | T3 |
| P16 | `read_definition` accepts `telemetry.source` `"simulator"` | T1 |
| P17 | The check clone is not dropped when a check raises | T9 |
| P18 | One factor removed from `C4_CONTRACT` | T9 (`uncontracted`), T9b |
| P19 | C4 passes a `B` factor whatever its value | T9 |
| P20 | `adjustments_kwh` classed `E` or zero in `C4_CONTRACT` | T9b (counts and the B row) |
| P21 | C4 skips factors that are absent from the derived values or the payload (rev 1's `unchecked`) | T9 (`uncontracted`, `not_in_product`) |
| P22 | `harness_run` passes the parent's `ASSETOPS_TEST_DATABASE_URL` | T9 (the runner sees `assetops_test`) |
| P23 | `harness_run` does not drop its base | T9 (no `DROP DATABASE` of the base) |
| P24 | `clone` copies `check.passed` without comparing `check_inputs` | T6 (`check_stale: "derived_values"`) |
| P25 | `check_inputs` omits the check code | T6 (`check_stale: "code.tools/world.py"`) |
| P26 | A manifest or stdout line names a file under `key_dir` | T5 (marker or `.key` found) |
| P27 | An existing L1 key directory is accepted at any mode | T5 (0755 accepted) |
| P28 | `cover_gap` takes each envelope's start day only | T8 (d), (e); T16b |
| P29 | `cover_gap` checks the union for contiguity, not against the cover | T8 (f) |
| P30 | `cover_gap` checks the local grain only | T8 (g) |
| P31 | `envelope_span` lets `ValueError` or `TypeError` escape | T8 (unreadable cases) |
| P32 | Step 7a runs before step 6 | T16c (a real-path COMPLETED gap batch is refused instead of already loaded) |

## Verdict

ACCEPT when spec §7 is all yes and P1 to P32 each failed once; findings by severity (High: a protected seam, a
permitted-name or connection rule, the check's independence or totality, the telemetry ruling, a key file named or
read, `assetops_test` touched; Medium: a missing test or plant;
Low: wording). The coordinator records the verdict.
