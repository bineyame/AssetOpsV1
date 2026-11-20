# 3B7a reviewer guide (rev 2, handshake round 1 answered)

For the fresh Reviewer: first at the handshake (read `spec.md`, `rulings.md` and this guide; put questions in
`handshake.md`), then at the review. Depth: discovery (W5): a new table and writer, and a read the deep-dive screen
serves money from.

## First checks

0. **Unit 0 (the seam), its own verification review before merge.** The diff of `task/3B7a-seam` against `main` is
   exactly `structure/read.py` and `backend/tests/test_3b7a_site_inputs_seam.py` (D-3B7A.10); 3B3, 4b, 5a tests green
   unchanged; the seam test's read count is one `site_month` per call.
1. **Scope.** New: `structure_snapshot/` (model, codec, rules digest, kinds, store, build, read, composition,
   adapter), the command module, migration 0066, the guard block, the test files, the packet. The slice branch has
   no diff in `structure/read.py` beyond what unit 0 merged. Nothing else.
2. **W2.** Expected values are 4b's and 5a's literals (spec §5) and fresh reads at the same `known_at`, never the
   snapshot's own output compared with itself.
3. **Migration.** Head and `down_revision` read from the modules; renumbered at merge preparation if needed.

## Done means

Spec §7's nine questions answered yes with real output: the no-database file, the Postgres file and the regression
set through `tools/heavy-slot.sh --db`; check-all with the three guard plants shown failing; every planted violation
below failing its named test; the owner's approval of the additive guard edit recorded before unit 3 merges.

## Planted violations (plant, run, revert; each must fail a named test)

| # | Plant | Must fail |
|---|---|---|
| V0 | The seam branch also edits another file, or 5b's branch edits `structure/read.py` | first check 0; 5b guide check 1 (`git diff` non-empty) |
| V1 | `SnapshotRead` always reports current (skip `months.stale`) | test 4(a) |
| V2 | The builder reads without `known_at` (or takes the stamp from a current read) | test 4(c) |
| V3 | The served read evaluates or calls `site_month` | test 7 |
| V4 | Ignore `closed_at_build` | test 5 |
| V5 | Decode and serve a row of another structure version or format | test 6 |
| V6 | Skip the digest check on decode | test 2 |
| V7 | Encode a `Decimal` through `float` or `format(d, "f")` | test 2 (`1E+2`, `1.30`) |
| V8 | Replace the Site's row on rebuild (update or delete the old one) | test 4(b); Postgres test 2 |
| V9 | `put` writes Site rows before refusing the portfolio row on `SnapshotExists` | test 8 (`[KOBO]` then `[KISIWA]` at one instant: row count) |
| V10 | Store the composed portfolio total and serve it instead of composing | test 3 (`actual()` equals `StructureRead.portfolio`) after a planted wrong stored total; and grep: no composed value in the payload |
| V11 | `verify` compares against a current read (no `known_at`) | test 9 (after `LATE` it must still match) |
| V12 | Drop `untracked`, or count a commercial or calendar leaf in it | test 3 (Kobo, Kisiwa `()`), §5 Mto `("diesel_price",)` |
| V13 | The guard misses a second writer, or redefines `$snapshotWriter` | the three guard plants (packet output) |
| V14 | Skip the held-kinds comparison on serve | test 4(d) |
| V15 | The read ignores `rules_digest` | test 11(a) |
| V16 | The closure walker reads module-level imports only; or the digest hashes names, not bytes | test 11(b) (`commercial.composition`); test 11(c) |

## Probes

- **Freshness order.** `reasons` is always a subsequence of `REASONS` (five, `RULES` third) in that order;
  `REBUILD_NEEDED` never carries a snapshot.
- **One instant.** Grep the builder: every read call passes `known_at` (or the positional equivalent) equal to `as_of`.
- **No ids in payloads.** Two builds at different instants over unchanged records give equal site payloads except
  `known_at`.
- **Disposal.** Each builder failure in the composition disposes what was built (3B3's L1 pattern).

## Class sweeps (W6)

- *Mid-build round 1 (D-3B7A.13 to D-3B7A.15):* no `pathlib` or file read in `structure_snapshot/` outside
  `adapters/`; the guard block in the repo file equals `packet.md` (A) to (E) and (E) is shown failing; the only test
  file outside the slice in the diff is `test_3a2_commercial_upload_postgres.py`, line 280 only; no test asserts its
  own migration "is head"; every k-of-n assertion checks k, n and the `out` codes.

- *A stored figure served as current while out of date:* every path that returns `SERVED` computes `RECORDS` (stamps
  and kinds), `MONTH_CLOSED` and `RULES`.
- *A figure recomputed on read:* every function reachable from `SnapshotRead` (grep its imports).
- *Inexact money:* every `Decimal` crossing the codec.

## Risks

- The seam written twice: only unit 0 writes it (D-3B7A.10); `5b` unit 2 starts after it is on `main`.
- The digest over-reports (any change in the closure, e.g. a commercial adapter refactor): intended (D-3B7A.11); a
  rebuild clears it.
- A Postgres reader list in rule 8 the spec did not name: the builder follows 3A1's block; check it.
