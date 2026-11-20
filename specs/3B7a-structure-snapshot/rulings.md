# 3B7a rulings

Architect (Claude), 2026-11-20. Each ruling gives its reason. Index lines: `.ai/decisions/index-rulings-11.md`.
Handshake answers go below, under "Handshake answers (round 1)".

## D-3B7A.1 A snapshot freezes one Site-month; the portfolio row names its Site rows; nothing is ever changed

- **Ruling.** One row per Site-month build holds that Site's inputs, evaluated actual values and target side; one
  portfolio row per build holds the operator-level budget lines and the IDs of the Site rows it composes. Rows are
  append-only (memory store and the 0005 `ledger_append_only()` trigger); the latest by "as of" is served.
- **Why.** OD-23: "a calculated daily snapshot that the UI would use". `3B7b` recalculates only the Sites and periods
  a trigger marks, so the Site row is the unit of recalculation; a portfolio row naming its Site rows lets a later
  partial rebuild compose a new portfolio without recomputing untouched Sites. Append-only keeps every served figure
  reproducible (design §2.8: "every snapshot can be rebuilt from its records").

## D-3B7A.2 One build, one instant: every read at `known_at = as_of`; the stamps are 3A4's under that instant

- **Ruling.** The build takes `as_of` from its clock once and passes it as `known_at` to every read. Each Site row
  carries the `site_month` stamp of its budget-line read (`BudgetLines.stamp`), and the portfolio row the
  `portfolio_month` stamp, both under `known_at`.
- **Why.** A record arriving during a build would otherwise be in one read and not another. 3A4's stamp covers every
  money kind placed in the Site-month (charges, receipts, expenses, budget lines), so one stamp per Site covers both
  sides; under `known_at` it describes exactly what was read, and `CommercialMonths.stale` compares it with the
  current digest, so any later record, correction or move between months marks it (3A4 review L1).

## D-3B7A.3 Out of date has four named reasons; the read serves stale values with them, never as current

- **Ruling.** `RECORDS` (a stamp is stale), `MONTH_CLOSED` (built before the month ended, read after), and
  `STRUCTURE_VERSION` or `FORMAT` (the stored form no longer matches the code). The first two serve the frozen values
  with `current` False; the last two serve no values (`REBUILD_NEEDED`). The served read calls only the store and
  `CommercialMonths.stale`: no evaluation and no month read.
- **Why.** Decisions-register item 19: "a screen must never show an older figure as current". Showing the frozen
  figure with its "as of" and the reason is honest and keeps pages fast (OD-23); a figure in another structure version
  cannot be decoded faithfully. A month read on serve would be the recompute-on-read the snapshot removes.

## D-3B7A.4 Compositions and the bridge are derived on serve from the frozen Site values

- **Ruling.** The snapshot stores each Site's values and the operator-level lines; the portfolio totals (`compose`)
  and `5b`'s gap are computed on serve from them. Owner question Q1 carries this with its default.
- **Why.** Both are arithmetic over the frozen values (no record is read), so the speed OD-23 asks for is kept; a
  stored total could disagree with its stored parts, which the never-sum and weakest-part rules forbid.

## D-3B7A.5 Inputs no stamp covers are listed, not hidden

- **Ruling.** `Freshness.untracked` lists the valued actual leaves whose sources are not commercial records (readings,
  declared prices), excluding option-only neutrals and the calendar. Their changes are detected by `3B7b` (triggers 1
  and 4). Owner question Q2.
- **Why.** A month stamp says nothing about a price setting or a reading; claiming "current" for those figures would
  overstate. The deep-dive's money is records, so on Lakeside the list is empty wherever invoices give the price.

## D-3B7A.6 Rebuilt on command after an accepted import; verification rebuilds at the "as of"

- **Ruling.** `build_structure_snapshot build` is run by the analyst after each accepted import (runbook). `verify`
  rebuilds every payload at the stored `as_of` without writing and names each differing part. The daily run and
  *Recalculate now* are `3B7b`.
- **Why.** Plan §0.3: "the analyst rebuilds the snapshot after each accepted import (`3B7a`); automatic triggers
  follow". Design §2.8: "a check compares it with a fresh evaluation"; at the same `known_at` the commercial reads are
  reproducible, so a difference is a real fault (or an untracked input that changed).

## D-3B7A.7 `StructureRead.site_inputs` is the shared seam with `5b`

- **Ruling.** `structure/read.py` gains `SiteInputs`, `evaluate_inputs` and `StructureRead.site_inputs`; `site` becomes
  `evaluate_inputs(site_inputs(...))` with unchanged results. Whichever of `3B7a` unit 1 and `5b` unit 2 merges first
  writes it exactly as 3B7a spec §2.1; the other merges `main`.
- **Why.** The snapshot freezes inputs so it can be verified and so `5b` can carry a missing actual at its target and
  re-evaluate from frozen values; `5b` needs the same inputs on the fresh path. One definition, one place.

## D-3B7A.8 The payload is canonical JSON with exact decimals and a digest

- **Ruling.** Sorted keys, compact separators, UTF-8; every `Decimal` as `str(d)`; times in UTC ISO form; no JSON
  number but `int`s; `payload_sha256` checked on every decode, a mismatch raising (never served).
- **Why.** Exact money (no float, exponent kept) and byte-for-byte verification need one canonical form; the digest
  turns silent corruption into a failure.

## D-3B7A.9 Migration 0066 and its writer

- **Ruling.** One table, `structure_snapshot`, written only by `structure_snapshot/adapters/
  postgres_structure_snapshot_store.py` with one plain INSERT shape, registered in rule 8 as 3A1's writer is; partial
  unique indexes per scope and instant; no column defaults; downgrade refused while rows exist.
- **Why.** The persistence guard's pattern (3A1, 3A2) keeps one writer per table and refuses UPDATE by code review and
  trigger alike.

## Handshake answers (round 1)

(none yet)
