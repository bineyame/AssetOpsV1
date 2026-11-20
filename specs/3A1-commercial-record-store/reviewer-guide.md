# 3A1 reviewer guide

For the fresh Reviewer: first at the handshake (read `spec.md`, `rulings.md`, P3A and this guide, and put your
questions in `handshake.md`), then at the review. The review depth is discovery (W5).

## First checks

1. **Scope.** The diff holds only spec §7.6's list, plus the finish bookkeeping.
2. **Migration.** It is spec §2's SQL, written as a raw string, with four append-only triggers and the 0061-style
   downgrade.
3. **Module path.** The packet's `__file__` output shows the worktree, not `main`.

## Done means

Spec §7's six questions are answered yes, with real output: the focused file, the pooled Postgres set run through
`tools/heavy-slot.sh --db`, check-all, `select-tests`, and the two planted guard failures.

## Probes

- **P1 Idempotent.** Ingest 2a's fixture twice: the second run is all `UNCHANGED`, and the row counts do not change.
- **P2 Revision.** Change one record's amount and bump its `source_version`. The result is revision 2, which
  supersedes revision 1, and `latest_revisions` returns revision 2.
- **P3 Conflict.** Same `source_version`, different amount: `INTAKE_VERSION_CONFLICT`, and nothing is written for it.
- **P4 Isolation.** A batch whose `tenant_code` is another tenant's is REFUSED. A Site code from another tenant is
  `INTAKE_SITE_UNKNOWN`.
- **P5 Lock.** Read the lock-proof test: it must hold the lock itself and see both threads alive before releasing.
- **P6 No leak.** Force a CHECK failure through the adapter. The error text holds no record value
  (`hide_parameters`).
- **P7 Exactness.** Amounts round-trip as `Decimal`, and `canonical` equals `to_canonical_json` byte for byte.

## Class sweeps (W6)

- If a refusal code is wrong, check all of spec §3's codes.
- If a table lacks its trigger, check all four.

## Risks

- `3A2` adds acceptance by a person (OD-15). Check that nothing here pretends a record was accepted by someone.
- DS3's estimate declarations must not be written into this store as zero records (D-3A1.7).
