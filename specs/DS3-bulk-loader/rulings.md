# DS3 rulings

Architect (Claude), 2026-11-21, on the owner's delegation (`owner/owner-away-architect-decides-2026-11-21.md`).
D-DS3.1 to D-DS3.8 are applied by `spec.md` rev 1. D-DS3.1, D-DS3.2 and D-DS3.8 change what the owner-accepted
strategy text says, so each is logged for the owner in `specs/OWNER-AWAY/decisions-2026-11-21.md` (rows 9 to 11).

## D-DS3.1 Set-based `INSERT ... SELECT FROM unnest` inside the ledger's one writer, not `COPY` into staging

- **Ruling.** The bulk path is a method of `PostgresEvidenceLedger`, writing each table with one literal set-based
  statement per batch and only the existing `DO NOTHING` arbiters. No `COPY`, no staging table, no second writer.
- **Why.** `tools/checks/configuration-persistence.ps1` holds three rules the strategy's wording would break: "No
  product writer runs MERGE or COPY" (`:1260-1263`), only the ledger writer writes ledger tables (`:1723`), and the
  ledger runs no DDL (`:1747`, so no staging table). Changing them is a guard change the owner approves (OWNER-AWAY
  row 5), and the delegation does not widen authorisations. Putting the loader under `tools/`, outside the guard's
  scan, would be working around a safety check (`.ai/RULES.md` §7). The property the strategy wanted, "constraints,
  append-only triggers and change triggers still fire, once per statement instead of once per row", holds for a
  set-based `INSERT ... SELECT` exactly as for `INSERT ... SELECT FROM staging`; `unnest` of array parameters is
  already used in this adapter (`:1200`). Unit 3 measures it; if DS4 finds it misses the build target, the COPY writer
  block goes to the owner then, with numbers.
- **Reverse.** The owner approves a COPY writer block; only `_BULK_EVIDENCE_SQL` changes.

## D-DS3.2 Commercial records keep one path: `3A2`'s intake, through the existing loader

- **Ruling.** The world command calls `load_emulated_exports.main` per tenant for the DS1b canonical files. DS3 adds no
  commercial write and no commercial parity half.
- **Why.** D-3A3.1 (merged): "No emulator, seed, bootstrap or bulk loader calls `CommercialRecords.ingest` ... This
  binds `DS3` too". A second commercial path would store raw references where the intake stores pseudonyms and turn
  one record sent both ways into `INTAKE_VERSION_CONFLICT`. Volumes are small (D-3A1 Q2; the strategy measured 8,100
  rows), so the intake costs seconds. With one path, a parity test on it would compare a path with itself.

## D-DS3.3 Parity is row equality on the four input tables; recompute jobs by coverage

- **Ruling.** Rows are equal column by column, generated IDs and receipt and decision instants apart. Recompute jobs
  are compared by what the pipeline needs: every accepted reading inside a PENDING job window, the bulk path with no
  more jobs than the real path.
- **Why.** The real path coalesces jobs per 64-ordinal chunk (`decide_chunk`, `_coalesce_job`), so it may hold several
  touching windows where the bulk path, deciding a batch at once, holds one. Both feed the same day windows to the
  assessment; demanding equal job rows would force the bulk path to imitate chunking, which is not a property of the
  evidence.

## D-DS3.4 A batch already published for a registered run is refused in bulk

- **Ruling.** `BULK_PUBLISHED_BATCH` when an `evidence_publication` row exists for the slot.
- **Why.** The link between a registered run's publication and its batch is made only "in the admission transaction
  that inserts the batch; never afterwards" (`open_batch`); the bulk path does not write provenance (the guard keeps
  `batch_publication_link` to `open_batch`'s literal INSERT). Registered runs go through the real path.

## D-DS3.5 The bulk path admits clean batches only

- **Ruling.** Any `Rejected` ordinal, any message, event or session collision refuses the whole batch
  (`BULK_REJECTED_ORDINAL`, `BULK_MESSAGE_COLLISION`) in one transaction.
- **Why.** Duplicates, conflicts and rejections are typed by the real path's ordered reread (`_collision`), which a
  set-based statement cannot reproduce without copying it. The generated world is clean by construction; the disorder
  tests (DUP-1 to CLOCK-1) are planted through the real path, where they are tested.

## D-DS3.6 Label and database refusals

- **Ruling.** Only `source_mode` SIMULATED batches; only databases named `*_test` or `<prefix>_audit*` and never an
  operator database (`database_target`, `is_operator_name`), checked before any connection.
- **Why.** Strategy §4 and §8: the bulk loader "refuses any reading that is not SIMULATED"; `.ai/RULES.md` §7 names the
  permitted databases. The command is a trusted tool with no gateway credential (residual risk `R-TRUST`), so the two
  refusals are what keep it off live and operator data.

## D-DS3.7 No user-facing text

- **Ruling.** The command's stderr lines are developer diagnostics (code, batch, detail); nothing is served.
  D-SC1.28 does not engage.

## D-DS3.8 Lines not received are not estimated by DS3

- **Ruling.** DS3 loads what DS1b wrote. A line DS1b lists `ESTIMATED_NOT_RECEIVED` (Kisiwa O&M, Thika maintenance,
  Kasarani maintenance) has no record and no estimate: the structure read shows it as missing, "Not available yet"
  with the record that would fill it. D-3A1.7's "declarations beside the store" are queued as their own unit (a
  declared estimate with its declarer), not built here.
- **Why.** An estimate is not a record (D-DS1B.7); no store for declared estimates exists on `main`, and building one is
  a new schema outside DS3's three units. The owner's rule "a cost line not sent reads 'Not available yet', or
  *Estimated* where the operator states an estimate, never 0" (build plan §0.4) holds: no estimate has been stated
  through any path, so "Not available yet" is the honest reading.
- **Reverse.** Queue the declared-estimate unit ahead of WK; DS3 needs no change.
