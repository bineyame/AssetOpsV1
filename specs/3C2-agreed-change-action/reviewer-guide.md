# 3C2 reviewer guide

Architect (Claude), 2026-11-20, rev 2 (after handshake round 1). Discovery review (W5): a new table and a person rule. Read `spec.md`,
`rulings.md`, 5c `spec.md` §4.3, then the diff. Done means every question in spec §6 answers yes with evidence and
every plant below fails its named test.

## What to check, and how

1. **Hand values (W2).** Tests 1 and 2 write spec §4's literals; an expected JSON line built by calling the command
   is High.
2. **The rules in order.** Read `record` against spec §2.3 step by step; the first failing step refuses; the re-run
   read (step 7) precedes the due check; the owner scope is `owner_covers` over held grants (`OnboardPerson.roles`)
   with `OWNER_COVER` (D-3C2.6), not a role name alone; one clock read per call.
3. **Append-only.** The migration's two triggers and checks match §2.1 byte for byte; test 6 proves each (UPDATE,
   DELETE and TRUNCATE each asserted); the downgrade refuses with rows.
3a. **Gates.** The packet names gate A's head and number; the migration's `down_revision` is `main`'s head at merge
   (gate B; one `alembic heads`); no edit to `accounts/service.py` (3A6 supplies `tenant_by_slug`).
3b. **Once, twice over.** Tests 7(b) (index catch) and 7(c) (lock) each fail with their mechanism removed.
3c. **Trust stated.** The packet lists `R-AUTH`; nothing calls the command authenticated.
4. **One writer.** The persistence guard's new block; its two failing runs are in the packet.
5. **Seams.** `git diff main...HEAD --stat` lists only spec §0's files; nothing under `actions/` other than the three
   new modules and the appended agreed-action block in `actions/composition.py` (D-3C2.15; S6-01a's lines untouched) changes; `actions/agreed.py` imports no S6-01a module and `agreed_composition.py` imports no adapter (test 5); unit 2's two `deep_dive/` files import
   only `actions.agreed` and `actions.agreed_composition` (test 9(e)).
6. **Names, not emails; nothing valued.** The command's stdout and stderr hold no `@` (tests 1, 2 and 7); the line has
   exactly twelve keys (test 1); no value or money word in the migration or the adapter's SQL (test 5).
7. **Unit 2.** One class and one line in `deep_dive/`; 5c test 9(d) passes; 5c's other tests unchanged.

## Planted violations (each must fail the named test; the builder shows each failing once, in a scratch copy)

| # | Plant | Fails |
|---|---|---|
| P1 | the finance lead admitted as creator (`action.agree` gains FINANCE) | tests 2 (`--as joseph`) and 4 |
| P2 | the owner checked for membership only (no scope) | test 2 (`--owner halima` with KOBO-001) |
| P3 | a Site manager accepted as owner with no Site | test 2 (R1 without `--site`, owner Peter) |
| P4 | a re-run inserts a second row | tests 1 and 7(a) |
| P5 | the read oldest first | tests 3 and 8 |
| P6 | "Overdue" on the due day itself | test 3 (`state_words(2026-12-15, 2026-12-15)`) |
| P7 | the row trigger left out of the migration | test 6 (UPDATE and DELETE each succeed) |
| P8 | the adapter's read also selects S6-01a rows (`... FROM action`) | test 5 (table-name and `\baction\b` greps) |
| P9 | emails printed instead of names | tests 1 and 7(a) (`@` in stdout) |
| P10 | an UPDATE statement in the adapter | the persistence guard (exit and message in the packet) |
| P11 | a `value` key in the JSON line | test 1 (twelve keys exactly) |
| P12 | `created_role` taken from the owner | test 2 (accepted case, owner Joseph) and test 1 |
| P13 | the owner scope checked against the creator | test 2 (`--owner halima`) |
| P14 | steps 4 and 6 swapped | test 2 (`--site NOPE-001 --owner zara@…` gives SITE_NOT_FOUND) |
| P15 | `actions/agreed.py` imports `actions.service` | test 5 |
| P16 | `StoreAgreedActions` also given `build_action_service` | test 9(e) |
| P17 | rev 1's owner rule (any role but SITE_MANAGER covers all) | test 2 (`--owner wanjiru`, `--owner musa`) and test 4 |
| P18 | a SITE_MANAGER grant matched by role name, not Site | test 2 (`--site MTO-001`, owner Peter; `--owner david`) |
| P19 | the tie broken by `id ASC` or insertion order | tests 3 and 8 (E before D) |
| P20 | a `value numeric` column in the migration | test 5 (value-word grep) |
| P21 | the TRUNCATE trigger left out | test 6 (TRUNCATE succeeds) |
| P22 | `active` ignored for creator or owner | test 2 (`--as fatuma`, `--owner fatuma`) |
| P23 | the re-run read after the due check | test 2 / test 1 (R1 again at 2026-12-16 gives DUE_IN_PAST) |
| P24 | the adapter's `agreed_action_once` catch removed | test 7(b) |
| P25 | the advisory lock removed | test 7(c) |
| P26 | the factor checked against any registry (rev 1) | test 2 (`--site FRIDGE-001` gives FACTOR_SITE_TYPE) |
| P27 | a second clock read for `state` | test 2 (the two-value clock case reads "Open") |

## Not findings

No HTTP route and no screen control (3C3). No owner or due date on the S6-01a Actions (`3C2b`). "Overdue" by the UTC
date (queue Q4). No sign-in on the command (D-3C2.12; `R-AUTH` in the packet). No live S6-01a Action in 5c test 9(d)
(queue Q6; 9(e) covers the seam). A gate-B renumber is not a finding when logged.
