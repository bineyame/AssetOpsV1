# 3A2 reviewer guide

For the fresh Reviewer: first at the handshake (read `spec.md`, `rulings.md`, P3A and this guide; put questions in
`handshake.md`), then at the review. Depth: discovery (W5): a new schema, personal data, an acceptance seam and the
real-data boundary (RC4).

## First checks

1. **Scope.** The diff holds only spec §8 question 9's list.
2. **Migration.** Spec §2's SQL as a raw string, two append-only triggers, the 0063-style downgrade; head and
   `down_revision` read from the modules.
3. **Module paths.** The packet shows the worktree's `__file__`s.
4. **3A1 unchanged when unused.** `ingest` without the new keywords plans byte-identically; 3A1's tests pass
   untouched.

## Done means

Spec §8's nine questions answered yes with real output: the three no-database files, the Postgres file and the
regression set through `tools/heavy-slot.sh --db`, check-all, and each planted violation below failing.

## Planted violations (plant, run, revert; each must fail a named test)

| # | Plant | Must fail |
|---|---|---|
| V1 | Drop `body.payer_ref` from `PERSONAL_FIELDS` | service test 3 |
| V2 | Pseudonymise before `parse_record` (so a bad ref becomes a pseudonym) | service test 5 |
| V3 | Admit `observed-financial` with `real_data=False` | service test 10 |
| V4 | Add `ANALYST` to `commercial.upload_decision` | API test 2 and `SPEC_ROLES` |
| V5 | Remove the under-lock decision check in the adapter | Postgres test 3 (and in memory, service test 12) |
| V6 | Ingest at submission instead of at acceptance | service tests 1 and 2 |
| V7 | Remove the `site_scope` refusal | service tests 8 and 9 |
| V8 | Let a `DataError` through unscrubbed | Postgres test 4 |
| V9 | `INSERT INTO commercial_upload` from `uploads.py` | the guard |
| V10 | Start `create_app` with `ASSETOPS_REAL_OPERATOR_DATA=on` on `assetops_test` | the settings test |

## Probes

- **Atomic acceptance.** Read `write_intake`: the decision check is under the lock and before `decide`, and the
  decision insert is in the same transaction as the plan's rows.
- **No value leaks.** Grep `commercial/**` and `commercial_upload_api.py` for logging and f-strings over records,
  refs, `batch` or `canonical`. Run service test 3's grep yourself on a stored world.
- **Pseudonym goldens.** Recompute one golden with `hmac` by hand; the test must not call `pseudonym()` to make
  its expected value (W2).
- **Words.** Every code the service can emit has its words; render a refusal for row 3 and read it as an operator
  would.
- **RC4.** Read `commercial_upload_settings`: both directions of the "if and only if" are refused.

## Class sweeps (W6)

- A personal field missed in one kind: check the whole §3.4 table against 2a §6.4's ref fields.
- A refusal missing in one route: check the order table for both paths and all four routes.
- An error path carrying a value: check every `except` in `commercial/**` and the router.

## Risks

- `3A4` edits the same store, adapter and composition files in lane B; the merge must keep both sets of methods.
- The pseudonym key directory must exist before uploads are switched on for any tenant; the packet says who creates
  the demo tenants' keys (the coordinator, queue Q5).
