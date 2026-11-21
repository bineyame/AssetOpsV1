# 3A1 rulings

Architect (Claude), 2026-11-20. Each ruling has its reason. The index lines are in
`.ai/decisions/index-rulings-8.md`. Handshake answers go below, under "Handshake answers (round 1)".

## D-3A1.1 The store takes canonical batches only

- **Ruling.** The one write path is `CommercialRecords.ingest(bytes)`, which reads `2a`'s canonical format. Native
  files are parsed to canonical by `3A2` and `3A3`.
- **Why.** Every source then passes the same refusals, and the store has one input contract (D-2A.2).

## D-3A1.2 A record's identity is (tenant, source system, source record ID)

- **Ruling.** Within that identity, the record's kind and Site never change.
- **Why.** This is the design's key (`integration-source-to-canonical-design.md` §6.1). It is also what makes a
  repeated file a no-op. A record that changes kind or Site is a different record in disguise, so it is refused rather
  than revised.

## D-3A1.3 Revisions are keyed by the source's own version

- **Ruling.** A new `source_version` appends a revision. The same version with the same digest adds nothing. The same
  version with a different digest is a conflict and is refused.
- **Why.** The source decides what a correction is (P3A rule 1). Accepting a silent change under an old version would
  overwrite history.

## D-3A1.4 Refusals are results, and are stored

- **Ruling.** A refused intake is one REFUSED intake row. A refused record is a rejection row. Neither is ever a
  record.
- **Why.** `3A2` must show the person what was refused and why, and the store keeps that account (P3A rule 4). The
  model follows the reading-upload precedent.

## D-3A1.5 No time column in the revision table's uniqueness (pushback on strategy §7)

- **Ruling.** `UNIQUE (record_id, source_version)` stands.
- **Why.** It is the idempotency the rules rely on. Adding `recorded_at` to it would let the same version enter twice.
  Partitioning is post-pilot (strategy Appendix E). When it comes, this uniqueness moves to a small identity table.
  That move is a conversion, not a redesign.

## D-3A1.6 No chain change-log registration yet

- **Ruling.** The four tables do not join `chain_input_change`.
- **Why.** No stored route reads them. Registering them would invalidate every cached route on each commercial write,
  for no reader. The first slice whose stored read uses them registers them, as 0058 did for fuel. Structure
  dirtiness is `3B7b`'s.

## D-3A1.7 Estimates and coverage are DS3's

- **Ruling.** The store holds only records a source sent. DS3 carries the generated world's
  `ESTIMATED_NOT_RECEIVED` and coverage reasons as declarations beside the store, never as zero records.
- **Why.** An estimate is not a record (D-DS1B.7). The DS1b review names this as residual risk.

## Handshake answers (round 1)

Answered once, 2026-11-20, and folded into `spec.md` rev 2 and `reviewer-guide.md` rev 2. "Adopted" means the
proposed answer is the ruling. The estimate stays at 3 units.

**The Highs**
- **R1: adopted.** The envelope columns are nullable unless the intake is STORED. A refused intake fills only what
  parsed and passes its CHECK. `batch_sha256` is the SHA-256 of the bytes as received. The bytes are never stored.
- **R6: adopted.** `intake()` returns an `IntakeSummary`: the intake row, its rejections in order, and the revision
  IDs it wrote. Only `ingest` returns per-record outcomes. UNCHANGED records are counted, not listed. If `3A2` needs
  a stored row-by-row account, `3A2` adds it.
- **R7: adopted.** "Latest" is picked per record over all of its revisions; the filters apply after that. A test in
  both stores proves that a correction which moves the month is counted once (D-3A1.8).

**The rest**
- **R2: adopted.** No filter; a test asserts the invariant.
- **R3: adopted.** Unbounded `numeric`; the exactness test runs over every fixture record; a grep test finds no
  `float(`.
- **R4: adopted.** READ COMMITTED; the proof checks the advisory waiters in `pg_locks`; the negative run is
  recorded.
- **R5: adopted.**
- **R8: adopted.**
- **R9: adopted.** A running state within the batch.
- **R10: adopted as the default.** Arrival order, documented. A stale or out-of-order version is a named residual for
  `3A3`'s contract test, which may require versions to rise monotonically per source.
- **R11: adopted.** Composite foreign keys for `supersedes_revision_id` and for `kind`. `site_id` agreement is a
  Postgres test.
- **R12: adopted** (D-3A1.9).
- **R13: adopted** (D-3A1.10).
- **R14: adopted** (D-3A1.12).
- **R15: adopted.**
- **R16: done.** `mid-build-questions.md` is reset to the template.
- **R17: adopted, as a hand-off to `3A2`.** Its copy says how many records were stored and how many refused, never
  "stored" alone.
- **P1: adopted.**
- **P2: adopted.**
- **P3: adopted.**
- **P4: adopted.**
- **P5: adopted.**
- **P6: adopted.**
- **P7: adopted.** `None` means no filter. A portfolio-only read is `3A4`'s.

**Open after round 1:** none.

## D-3A1.8 "Latest" before any filter

- **Ruling.** As R7.
- **Why.** A late correction must move money to its new month, never count it in both (P3A rule 2).

## D-3A1.9 Provenance is declared here and capped by the path in 3A2

- **Ruling.** The store keeps the batch's declared provenance. The same version under another provenance is refused
  with `INTAKE_PROVENANCE_CHANGED`. `3A2` caps what a path may declare: a person's upload of an emulator file can never
  be `observed-financial`.
- **Why.** The evidence word comes from the record (P3A rule 7). A label that silently keeps its first value, or that
  any file can raise, is not honest.

## D-3A1.10 Personal data

- **Ruling.**
  - The store holds only refs as the adapter sent them. The adapter (`3A2`, `3A3`) must pseudonymise them.
  - No raw bytes are stored.
  - No ref or record value is logged or put into an error.
  - Amended by D-3A6.29: the `commercial/` package holds no logging at all (R13); a cause code and byte count for an
    envelope breach is logged by the upload API, outside the package.
  - Erasure is a pilot residual, done by destroying the pseudonym key upstream.
- **Why.** The tables are append-only by design (D-3A1.4), so what enters them must already be safe to keep.

## D-3A1.11 Records in one batch are decided in input order

- **Ruling.** As R9.
- **Why.** A valid batch may carry two versions of one record. Deciding both against the pre-batch state would lose
  the whole intake on a unique key.

## D-3A1.12 Migration numbering for parallel slices

- **Ruling.** The first of the parallel migration slices to merge takes the next number on the current head. Each
  later one is renumbered on top of it at merge preparation. Tests read the head and `down_revision` from the
  migration modules, never a literal name.
- **Why.** Two lanes add migrations at once (`3A1`, `3C1a`). A pinned name breaks the second merge.

## Ratification of the three unstated choices (review r1, L2)

Ratified in `specs/3A2-commercial-file-intake/rulings.md`: `ExistingRecord.provenances` (D-3A2.1), `StoreRefused`
widened to every non-connection `DBAPIError` (D-3A2.2), `revision_no = None` for UNCHANGED (D-3A2.3).
