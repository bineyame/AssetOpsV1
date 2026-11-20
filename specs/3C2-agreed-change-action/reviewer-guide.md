# 3C2 reviewer guide

Architect (Claude), 2026-11-20, rev 1. Discovery review (W5): a new table and a person rule. Read `spec.md`,
`rulings.md`, 5c `spec.md` §4.3, then the diff. Done means every question in spec §6 answers yes with evidence and
every plant below fails its named test.

## What to check, and how

1. **Hand values (W2).** Tests 1 and 2 write spec §4's literals; an expected JSON line built by calling the command
   is High.
2. **The rules in order.** Read `record` against spec §2.3 step by step; the first failing step refuses; the owner
   scope reads held grants (`OnboardPerson.roles`), not a role name alone.
3. **Append-only.** The migration's trigger and checks match §2.1 byte for byte; test 6 proves each; the downgrade
   refuses with rows.
4. **One writer.** The persistence guard's new block; its two failing runs are in the packet.
5. **Seams.** `git diff main...HEAD --stat` lists only spec §0's files; nothing under `actions/` other than the three
   new modules changes; `actions/agreed.py` imports no S6-01a module (test 5).
6. **Names, not emails.** The command's stdout holds no `@` (tests 1 and 7).
7. **Unit 2.** One class and one line in `deep_dive/`; 5c test 9(d) passes; 5c's other tests unchanged.

## Planted violations (each must fail the named test; the builder shows each failing once, in a scratch copy)

| # | Plant | Fails |
|---|---|---|
| P1 | the finance lead admitted as creator (`action.agree` gains FINANCE) | tests 2 (`--as joseph`) and 4 |
| P2 | the owner checked for membership only (no scope) | test 2 (`--owner halima` with KOBO-001) |
| P3 | a Site manager accepted as owner with no Site | test 2 (R1 without `--site`, owner Peter) |
| P4 | a re-run inserts a second row | tests 1 and 7 |
| P5 | the read oldest first | tests 3 and 8 |
| P6 | "Overdue" on the due day itself | test 3 (`state_words(2026-12-15, 2026-12-15)`) |
| P7 | the trigger left out of the migration | test 6 (UPDATE succeeds) |
| P8 | the adapter's read also selects S6-01a `action` rows | test 5 (SQL table grep) |
| P9 | emails printed instead of names | tests 1 and 7 (`@` in stdout) |
| P10 | an UPDATE statement in the adapter | the persistence guard |

## Not findings

No HTTP route and no screen control (3C3). No owner or due date on the S6-01a Actions (`3C2b`). "Overdue" by the UTC
date (queue Q4).
