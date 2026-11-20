# 3A1 rulings

Architect (Claude), 2026-11-20. Each ruling has its reason. The index lines are in
`.ai/decisions/index-rulings-7.md`. Handshake answers go below, under "Handshake answers (round 1)".

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
