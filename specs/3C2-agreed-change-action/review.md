# 3C2 review

Commit 1's review is `review-c1.md`. This file holds the later rounds.

## Commit 2 (text through SC-1 statements): fresh review, 2026-11-21

**Verdict: ACCEPT.** No High or Medium findings. Two Low notes; neither blocks the merge.

Summary (at most 15 lines):

- Scope: `7aed5c3ab..2f6433de4`. That is the merge of main `6de329dc4`, the text commit `ac6a5d4ec`, the packet and
  state commit `a2d7c807a`, and the index split `2f6433de4`.
- All 14 refusal sentences and both state words match spec §2.5 and §4 exactly. Each one renders through
  `render(message(...))`, and the tests assert them from hand literals.
- `actions/agreed.py` is in `ADOPTED`, and the adopted scan finds nothing in it.
- `record_action.py` builds no English apart from argparse `help`, `description` and `epilog`. Those are static
  chrome under SC-1 §3.8.4 (g), and the epilog is chrome by D-3C2.14.
- The three declared deviations are sound: the key form, the T8 pin, and `state_code` kept beside `state_words`.
- Q1 holds. The 30 general categories are still 30 distinct codes when upper-cased, and the refused set is unchanged
  over all 0x110000 code points.
- Migration 0070 has one head, `0070_agreed_action`, with `down_revision` `0068_structure_finding`. No `0069_agreed`
  reference is left in code.
- The index split loses and duplicates no line, its headers say "of 3", and `INDEX.md` lists `index-3.md`.
- Full check-all: all 43 guards passed.

### Findings

- **L1 (bookkeeping; not an acceptance gap).** `.ai/state/INDEX.md:18`: the `work.md` row says `8` sections and
  `22 KB`. The file now has 10 sections and is 26 KB. The row was already stale on main (9 sections), and no guard
  reads the column. Fix: set it to `10 | 26 KB` in any later docs commit.
- **L2 (merge-time instruction; not a defect on this branch).** `task/3A7-month-reconciled` makes three edits that
  overlap with this branch:
  - it adds the same noun, `character`, to `i18n/statements/en/vocabulary.py`;
  - it sets `ADOPTED` in `tools/checks/statement_catalogue.py:41` (to `structure/reconciliation.py`);
  - it extends T8's set in `backend/tests/test_sc1_statements.py:317-323`.

  When 3C2 merges after 3A7, resolve each edit as follows:
  - Keep one `character` entry and one `"character"` in `noun.order`. A duplicate in `order` fails the load with
    `VOCABULARY_SCHEMA`; I checked this, so a bad resolution cannot pass silently.
  - Make `ADOPTED` the union of both paths.
  - Make T8's statement and vocabulary sets the union of both branches' additions.

### Item by item

1. **Sentences (spec §2.5).** I compared each variant in `i18n/statements/en/agreed_action.py` with §2.5 character
   by character, and all 14 match.
   - `BAD_TITLE` reads "Write a title of {least} to {most}.", where `least` is a bare count and `most` is a count of
     `character`. It renders "Write a title of 1 to 200 characters.". Digits must come in through slots (D-SC1.21),
     and D-3C2.14 allows that.
   - `BAD_DUE`'s date is an `example` slot.
   - `agreed.py:133-142`: `state_words` and `refusal_sentence` render the two statements.
   - `record_action.py:45` writes `<CODE> <sentence>\n`. The f-string holds only a space and a newline, so the
     ratchet does not flag it.
   - The JSON `state` field is the rendered word (`record_action.py:58`).
   - The baseline, allow and legacy JSON files are unchanged.
2. **Deviations.**
   - (a) Key form. One `agreed_action.refused` statement with a `state` slot, marked `exhaustive`, gives the same
     coverage. The three-segment plant fails `KEY_FORM`. 3A7 uses the same shape (`reconciliation.refused`).
   - (b) T8. SC-1 spec §6 T8 only requires that the shipped catalogue loads. The exact-set pin is the test's own
     choice, and an adopter extending it is the expected path (see L2 for the merge).
   - (c) `state_code` kept. It is additive. The 5c contract field `state_words: str` is present, and Postgres test 8
     now asserts both fields.
3. **Q1.** `agreed.py:40` and `agreed.py:150`. My own scan found 30 categories, still 30 distinct when upper-cased,
   and the same refused set over every code point. The exhaustive test is at
   `test_3c2_agreed_actions.py:506-511`. `.upper()` is not one of the adopted-scope forbidden calls.
4. **Migration 0070.** `ScriptDirectory.get_heads()` returns `['0070_agreed_action']` and `down_revision` is
   `0068_structure_finding`. The renamed references are `HAND_PAIR`, test 5's path, the downgrade message,
   `pg_harness`, `test_pg_harness` and the persistence-guard comments. The only `0069_agreed` mentions left are
   history in `handoff.md`, `handshake.md`, `packet.md` and `spec.md`.

   3A7 has `0069_commercial_reconciliation` with `down_revision` `0068_structure_finding`. When it merges, change:
   - `0070_agreed_action.py:15` (docstring `Revises:`) and `:21` (`down_revision`) to
     `0069_commercial_reconciliation`;
   - `test_3c2_agreed_actions_postgres.py:40`, `HAND_PAIR`, to
     `("0070_agreed_action", "0069_commercial_reconciliation")`;
   - the file's numbering note at lines 9-11.

   Then confirm there is one head, and rerun `test_3c2_agreed_actions_postgres.py`, `test_3a7_reconciliation_postgres.py`
   and `test_3b4_observer_postgres.py`, because their downgrades now pass through both migrations. The L2 merge
   points apply at the same time.
5. **Index split.** The numbered lines of `index-2.md` at `a2d7c807a` are identical to the new `index-2.md` and
   `index-3.md` together. The headers read "part N of 3", and `INDEX.md:24` lists all three files.
   `check-decision-index.py` returns OK (1207 IDs). `index-3.md` is 3,142 bytes.
6. **Plants.** The builder's plants are asserted in tests that I ran and that pass. I also ran a scratch spot-check
   of my own:
   - Adopted-scan hits on `agreed.py` for a `%` format, `.title()`, a `== "Open"` comparison, a `"{} refused".format`
     and a bare `"Overdue"` constant.
   - Load failures for an extra state value (`NOT_EXHAUSTIVE`) and a digit in `bad_due` (`LITERAL_DIGIT`).
   - A render error for an unknown code (`FACT_TYPE`).
7. **Merge `6de329dc4`.** `permissions.py` keeps `action.agree` beside 3B4's `structure.tolerance.*`. The filter in
   `test_3c1a` excludes the `commercial.`, `action.` and `structure.` prefixes, and `COMMAND_ROLES == SPEC_ROLES` is
   still asserted in full. Nothing is weakened.

### Checks run (reviewer, head `2f6433de4`)

- `bash tools/heavy-slot.sh --wait-seconds 3000 -- pwsh -NoProfile -File tools/check-all.ps1`: **All 43 guards
  passed (blocking; 0 advisory, 0 warned)**, exit 0. This includes:
  - `Statement catalogue (SC-1)`: "OK statement catalogue: load, coverage, legacy, scan (1 adopted), keys, imports";
  - its self-test: "72 of 72 plants behave";
  - `configuration-persistence.ps1`: passed, with the owner-approved writer block (`42de02e06`, an ancestor);
  - the decision, state, spec and owner index guard: OK;
  - agent workflow: passed;
  - the estate guard self-tests: 17 passed.
- Unit tests through `heavy-slot.sh` and `run-host-tests.ps1`: `test_3c2_agreed_actions.py` and
  `test_sc1_statements.py`, **489 passed**.
- Postgres tests through `heavy-slot.sh --db` on `assetops_test` (`test_3c2_agreed_actions_postgres.py` and
  `test_pg_harness.py`): **28 passed** (7 warnings), exit 0.
- `alembic` `ScriptDirectory`: one head, `0070_agreed_action`.

### Not verified, and residual risk

- Not rerun: `test_3b4_observer_postgres.py` (downgrades through 0070) and the full suites. I accept the builder's same-revision runs (41 passed under `--db`; 636 unit tests at `ac6a5d4ec`), because the later commits change only docs.
- The 3A7-merge step (item 4 and L2) is still ahead; until then 0070's parent is provisional.
- `R-AUTH` is unchanged and stated in the packet.
