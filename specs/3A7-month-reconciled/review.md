# 3A7 review, commit 2 (discovery, W5)

Commit 1's review is `review-c1.md` (ACCEPT at `bc24b8e25`). This file reviews everything after `bc24b8e25` up to head
`50f39f69d`: the main merge `214cae7fc`, the mid-build answers merge `9eab92105`, and commit 2 (`7db25a8b9`,
`2ecf0ddeb`, `d192a3816`, `50f39f69d`). Reviewer: a fresh Claude reviewer who did not author the work. Date: 2026-11-21.

## Summary

- **Verdict: ACCEPT WITH FIXES.** All three findings are Low: two test gaps that my plants exposed, and one duplicate
  function. Fix them on the branch. The coordinator can verify the fixes; no re-review is needed.
- Every served sentence goes through the composer. `structure/reconciliation.py` is in `ADOPTED` and builds no English.
  The guard passes with nothing added to the baseline or the allow file. `reconciliation.heading`, `.gap`, `.share`
  and `.scope` equal SC-1 §5.1 and §5.4 exactly: a test compares them with `worked.py`, and I read them against the
  spec.
- Honesty holds. `money_word` reads "Recorded" only while the standing is reconciled. A missing figure is `None` or
  omitted, never 0. The records' evidence word carries the weakest origin of the used lines.
- **D1 is correct and honest, and nothing served is lost.** `details` carries each failing heading's full sentence
  and goes into the JSON. The Architect's ruling has to carry the change to D-3A7.13, to §6.1's standing shape and to
  5c's reader (see "Builder's questions").
- Migration: there is one head, `0069_commercial_reconciliation`, on `0068_structure_finding`. Q1 to Q3 pass on
  Postgres. Check-all passes all 43 guards. The two `test_3a3_single_writer` failures are identical to `main`'s.
- The 3C2 merge conflicts in 6 files, and its 0070 must be re-pointed. The resolution is listed under "Merge with 3C2".

## Checks run (my output; logs in `/opt/assetecon/evidence/3A7/review-c2/`)

- `bash tools/heavy-slot.sh --wait-seconds 3000 -- pwsh -NoProfile -File tools/check-all.ps1` at `50f39f69d`:
  **All 43 guards passed (blocking; 0 advisory, 0 warned)**, 352.8 s wall. This includes "Statement catalogue (SC-1):
  load, coverage, legacy, scan (1 adopted), keys, imports" and its self-test, "72 of 72 plants behave"
  (`check-all.log`).
- Focused tests, no database, through `heavy-slot.sh`: the three 3A7 files, `test_sc1_statements.py`,
  `tools/checks/test_statement_catalogue.py`, 3A3 single writer, 3A4 months, 4b money leaves, 4b1, 3A1 service and
  3C1a person work. Result: **2 failed, 941 passed** (`focused.log`). Both failures are in `test_3a3_single_writer.py`
  (`test_s1_one_writer_of_commercial_records`, `test_s1_allowlists_are_exact`). I listed the S1 violations on this
  branch and on `main` (`78481d02d`) with the same scanner. Both lists are the same 12 entries, all `S1-DYN
  tools/checks/statement_catalogue.py:{715,877,881-884}`. **3A7 adds nothing to them.**
- Postgres, `heavy-slot.sh --db -- pwsh tools/run-host-tests.ps1 -- backend/tests/test_3a7_reconciliation_postgres.py`
  on the default `assetops_test`: **3 passed** (Q1 chain, triggers, CHECKs and refused downgrade; Q2; Q3) (`pg.log`).
  The implementer's 16-test run, which also covers 3B4's downgrade through 0069, was at `d192a3816`. `d192a3816` to
  `50f39f69d` changes only `packet.md`, so that run stands for this head.
- Migration heads, read from `down_revision` across `versions/`: one head, `0069_commercial_reconciliation`, with
  `down_revision = "0068_structure_finding"`.
- Import direction: no module in `commercial/` imports `structure` (grep). `structure/reconciliation.py` imports
  `commercial.model` (the forms and citation helpers) and `structure.money` (the three helpers). D-3A4.8 holds.

### Plants (in a scratch copy of HEAD; the worktree was never edited; `plants.log`)

| # | Plant | Result |
|---|---|---|
| P1 | `money_word` ignores the standing (always reconciled) | caught: `test_r6_money_word` |
| P2 | share divided by the recorded figure, not the accounts | caught: R1 words |
| P3 | `details` keeps the MATCHED headings too | caught: R2 words (T2) |
| P4 | standing sentence shows the default tolerance, not the tenant's | caught: R2 words T3 |
| P5 | slug citation boundary drops `-` on the **leading** side | **survived** (L2) |
| P6 | the records' evidence takes the strongest origin, not the weakest | **survived** (L1) |
| P7 | a Site statement's sentence names "the organisation" | caught: R1 words |

The builder's own plants (V19, V12, V15, origin forced to financial, L2 trailing side, an f-string in the service)
are in the packet. I did not rerun them: P3 covers V19's class, and P2 and R3 cover the share.

## Findings

**L1 (Low; test gap, honesty rule).** `structure/reconciliation.py:163` gives the records, the difference and the
share the *weakest* origin of the used lines. That is what makes a mixed month read "(Recorded and Emulated)" rather
than "(Recorded)". No test has a heading whose used lines have more than one origin, so P6 (strongest origin) passes
every test. It matters because the evidence word is the product's honesty marker (D-SC1.16). To fix, add a pure case
to `test_3a7_reconciliation_words.py`: `words("500.00", "500.00", origins=("observed-financial", "source-emulated"))`
starts with `"Revenue (Recorded and Emulated): "`.

**L2 (Low; test gap on review-c1 L2).** `commercial/model.py:345` `cites_slug` excludes `[a-z0-9-]` on both sides. M5
tests only the trailing side (`lakeside-power-north`). P5 (no `-` in the lookbehind, so `north-lakeside-power` cites
`lakeside-power`) passes every test. To fix, add a case to M5 or to the service tests: an owner file holding only
`north-lakeside-power 2%` gives `OWNER_REF_INVALID` for `lakeside-power`.

**L3 (Low; tidy).** `_compare` is defined twice in `structure/reconciliation.py`, at lines 135 and 235, with identical
bodies. The second shadows the first. Delete one.

No acceptance gap. No hand-built text, no baseline or allow-file entry, no `LEGACY_NEW`.

## Builder's questions

**D1 (the Architect is ruling separately).** I judge the as-built form correct and honest:

- SC-1 cannot join two rendered heading sentences. A part shares its parent's facts, so two headings cannot both be
  parts, and `Items` holds facts, not messages. Joining them in code would be a `HAND_BUILT` hit in an adopted module.
- Each failing heading is still served in full, in heading order, as its own composed sentence. It is in
  `MoneyStanding.details` and in the `show` JSON (`"details"`). R2 asserts T2's `(T2_FUEL,)` and T6's `(T6_FUEL,)`.
  `none_matched` and `no_statement` carry `()`, so review-c1 residual 3 is closed: `none_matched` never reads the
  covering zero-stated check.
- Nothing served is lost in the service or the command. The loss is possible only at the reader. D-3A7.13's reason is
  that "the label 5c shows is `standing.text`", and Done question 3 asks for "saying exactly what did not match".
  Unless 5c shows `details` beside `text`, that part of the screen goes missing.
- The ruling should therefore amend D-3A7.13 and spec §2.3 "Text", add `details` to §6.1's "stable" standing shape,
  and name `details` in 5c's spec as part of the label.

**D4 ("within 1% (Recorded)").** This is consistent with SC-1. §5.1's worked cases already give the tolerance as
`DECLARED`/`observed-financial` under the heading's `basis`. `reconciliation.scope` is an inline §5.4 shape, so its
parents cannot be `served`. Honesty: the default 1% (RC8) is not a figure from the operator's records, so "(Recorded)"
after it is a stretch. Read in place, though, the word qualifies the comparison basis and claims nothing false about
the money. I record this as an owner wording item for the walkthrough, not a finding.

**The regex move.** This is a sound move, not a way around the guard.

- The five forms are record forms that mirror 0069's CHECKs, so `commercial/model.py`, beside `StatementRow` and
  `ToleranceRow`, is their natural home.
- There they stay in ratchet scope and add no fingerprint, because they are not prose.
- The citation helpers (`percent_token`, `cites_figure`, `cites_slug`) are service rules rather than record forms.
  Their placement is a preference, not a finding.
- `structure/money.py`'s `used_lines`, `line_sources` and `line_origins` are thin public wrappers over 4b's own
  `_ROWS[f].plus`, `_sources` and `_origins`. 4b's filters are reused, not restated.
- The import direction holds (see Checks).

**Smaller deviations.**

- D2: `money_word(figure: Money, standing)` follows D-SC1.16. The word comes from the figure's evidence. Accepted.
- D3: `CONFIGURATION` alone, because printing the message would serve exception text. Accepted. The spec text should
  drop `<message>` when it is next touched.
- D5: the files beyond §3 are each required by the SC-1 amendment (`ADOPTED`, T8, `noun.character`, cases) or by the
  move above. Accepted.
- D6: `show` refuses with `RECON_PERIOD` and `RECON_SITE_UNKNOWN` codes at exit 2. Accepted.
- The refusal rewordings ("not this organisation's", "its code in capital letters", "digits with a decimal point")
  are D-SC1.21's number-word rule.
- The new `no_mini_grid` variant gives commit 1's Site-less `RECON_SITE_UNKNOWN` a true sentence. Accepted.

## L1 to L3 of review-c1

- L1: fixed. The docstring at `structure/reconciliation.py:349-352` says the command builds the reader and the
  composition passes it through. The handoff, the packet and `.ai/state/data.md` no longer say "awaits the
  Architect". The P4 residual is gone. `rulings.md`'s SC-1 amendment names `structure/reconciliation.py`.
- L2: fixed in code (`cites_slug`, trailing side tested). The leading side is untested (L2 above).
- L3: resolved. 3A7's line is `179` in the new `index-3.md`, `index-2.md` is back under its cap, and the `data.md`
  entry is merged.

## Merge with 3C2 (`task/3C2-agreed-change` `846124834`; `git merge-tree` against this head)

There are 6 textual conflicts and 1 migration re-point:

- `i18n/statements/en/vocabulary.py`: both sides add `noun.character` with identical forms and the same `order`
  entry. 3A7's copy is at line 111 (comment "3A7: a refusal's length limit"), 3C2's at line 112 (comment above it).
  Keep **one** entry. A duplicate dict key would silently shadow, and a duplicate `order` entry fails the
  vocabulary load (`VOCABULARY_SCHEMA`, `catalogue.py:180`). Its comment should name both users.
- `tools/checks/statement_catalogue.py` `ADOPTED`: take the union,
  `(f"{PKG}/structure/reconciliation.py", "backend/assetops_backend/actions/agreed.py")`, and take 3A7's comment
  (3C2's still names `commercial/reconciliation.py`).
- `backend/tests/test_sc1_statements.py` T8: the statements set is the union (both commons, the 8 `reconciliation.*`
  keys and the 2 `agreed_action.*` keys). The vocabulary set is 3C2's, with `action_state`; 3A7 adds no vocabulary.
- `accounts/permissions.py` and `test_3c1a_person_work.py`: keep both keys, `commercial.accounts_statement` and
  `action.agree`.
- `.ai/state/index-3.md`: both branches create it as an add/add conflict, and both claim line 179. Keep one file and
  renumber the second-merged entry to 180.
- `0070_agreed_action.py`: `down_revision` becomes `"0069_commercial_reconciliation"`, otherwise there are two heads.
  3C2's Postgres test that asserts its chain link, if any, changes with it.

## Not verified

- I did not rerun the full backend suite. I cite the implementer's same-revision Postgres run (`d192a3816`, docs-only
  since then) and my own focused set.
- I did not test 5c's use of `details`, because 5c is not built.
- I did not render the `show` JSON against a live `serve` database. That was out of scope by the brief.

## Residual risk the packet does not name

1. **The `--site` input is echoed in a refusal.** `refusal_words` wraps the typed site code in
   `Name(value, "site.code")`. A code holding a control character makes `Name` raise `ValueError` inside `_record`'s
   handler, so the command exits with a traceback instead of printing `REFUSED`. This is an operator-only command, so
   I noted it rather than raising a finding.
2. **Non-mini-grid Sites read the tenant gate.** `show --site FRZ-001` returns `RECONCILED` once a mini-grid statement
   opens the gate, though FRZ-001's money was never compared. This follows D-3A7.2's tenant gate and RC5 (5c shows
   mini-grids only). Any later screen that shows cold-chain or EV money with `money_word` would inherit it.
3. **The 3C2 merge.** Without the single `character` entry and the 0070 re-point, the vocabulary load or the
   migration head check breaks on `main`. Check-all after that merge should be read for both.
