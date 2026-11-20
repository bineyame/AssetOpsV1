# 3B7a reviewer guide (rev 1)

For the fresh Reviewer: first at the handshake (read `spec.md`, `rulings.md` and this guide; put questions in
`handshake.md`), then at the review. Depth: discovery (W5): a new table and writer, and a read the deep-dive screen
serves money from.

## First checks

1. **Scope.** New: `structure_snapshot/` (model, codec, store, build, read, composition, adapter), the command
   module, migration 0066, the guard block, the two test files, the packet. The one edit to existing code is spec
   §2.1 in `structure/read.py` (or it arrived from `5b` through `main`; D-3B7A.7). Nothing else.
2. **W2.** Expected values are 4b's and 5a's literals (spec §5) and fresh reads at the same `known_at`, never the
   snapshot's own output compared with itself.
3. **Migration.** Head and `down_revision` read from the modules; renumbered at merge preparation if needed.

## Done means

Spec §7's nine questions answered yes with real output: the no-database file, the Postgres file and the regression
set through `tools/heavy-slot.sh --db`; check-all with the two guard plants shown failing; every planted violation
below failing its named test.

## Planted violations (plant, run, revert; each must fail a named test)

| # | Plant | Must fail |
|---|---|---|
| V1 | `SnapshotRead` always reports current (skip `months.stale`) | test 4(a) |
| V2 | The builder reads without `known_at` (or takes the stamp from a current read) | test 4(c) |
| V3 | The served read evaluates or calls `site_month` | test 7 |
| V4 | Ignore `closed_at_build` | test 5 |
| V5 | Decode and serve a row of another structure version or format | test 6 |
| V6 | Skip the digest check on decode | test 2 |
| V7 | Encode a `Decimal` through `float` or `format(d, "f")` | test 2 (`1E+2`, `1.30`) |
| V8 | Replace the Site's row on rebuild (update or delete the old one) | test 4(b); Postgres test 2 |
| V9 | `put` writes Site rows before refusing the portfolio row on `SnapshotExists` | test 8 (row count) |
| V10 | Store the composed portfolio total and serve it instead of composing | test 3 (`actual()` equals `StructureRead.portfolio`) after a planted wrong stored total; and grep: no composed value in the payload |
| V11 | `verify` compares against a current read (no `known_at`) | test 9 (after `LATE` it must still match) |
| V12 | Drop `untracked`, or count a commercial or calendar leaf in it | test 3 (Kobo, Kisiwa `()`), §5 Mto `("diesel_price",)` |
| V13 | The guard misses a second writer | the two guard plants (packet output) |

## Probes

- **Freshness order.** `reasons` is always a subsequence of `REASONS` in that order; `REBUILD_NEEDED` never carries a
  snapshot.
- **One instant.** Grep the builder: every read call passes `known_at` (or the positional equivalent) equal to `as_of`.
- **No ids in payloads.** Two builds at different instants over unchanged records give equal site payloads except
  `known_at`.
- **Disposal.** Each builder failure in the composition disposes what was built (3B3's L1 pattern).

## Class sweeps (W6)

- *A stored figure served as current while out of date:* every path that returns `SERVED` computes all four reasons.
- *A figure recomputed on read:* every function reachable from `SnapshotRead` (grep its imports).
- *Inexact money:* every `Decimal` crossing the codec.

## Risks

- `5b` writes §2.1 first: check it is byte-identical to the spec and not written twice.
- A Postgres reader list in rule 8 the spec did not name: the builder follows 3A1's block; check it.
