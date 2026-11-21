# SC-1f review packet (round 1)

Task: SC-1f, `spec.md` rev 1 and `rulings.md` D-SC1F.1-6. Branch `task/SC-1f-declared-word`, based on main `fa13f254f`.
Two commits: `8a48b8e51` (the word, 0.5) and `baf072f50` (the guard, 0.5). Non-screen. `USER_REVIEW_REQUIRED: true` for
the word only; the owner sees it at the 5c walkthrough, and it does not block the merge (D-SC1F.6).

## Outcome

- A declared setting, such as the 1% tolerance, reads "Declared" for every origin.
- The management accounts read "Recorded".
- An evidence word names only the figures its sentence states.
- The statement guard treats `_LOG`, `LOGGER`, `self._log` and any name bound to `getLogger` as loggers.
- The P55 plants add their entry to the real allow file instead of replacing it.

## Files

- Commit 1:
  - `i18n/statements/en/vocabulary.py`: `DECLARED` moves to `by_evidence_first`.
  - `i18n/render.py`: a two-pass fill. A `_LATE` table drives it (see Known Deviations, KD2). `_Rendering.stated` is new, and `_fill_evidence` counts only stated slots.
  - `structure/reconciliation.py`: `ACCOUNTS` and `SETTING`.
  - Tests: `statement_cases/{reconciliation,worked}.py`, `test_sc1_statements.py` and three 3A7 test files.
- Commit 2:
  - `tools/checks/statement_catalogue.py`: `LOG_STEMS`, `_getlogger`, `_bound_loggers`, `_logger(receiver, bound)` at both call sites, the merged `allow()`, and plants N14-N17, P58a and P58b.
  - Baseline and allow JSON files.

## Sentences whose wording changes (for 5c, which renders them)

All the changes are in `reconciliation.*`. No other statement's English changes.

| Statement / variant | Old | New |
|---|---|---|
| `reconciliation.heading` `matched`, `not_matched`: records of emulated origin (the 3A7 fixtures) | `Revenue (Recorded and Emulated): ...` | `Revenue (Recorded, Emulated and Declared): ...` |
| the same, financial origin (C1-C4, R3 boundary cases) | `Revenue (Recorded): ...` | `Revenue (Recorded and Declared): ...` |
| the same, no origin named (`test_r3_an_unnamed_origin_reads_estimated`) | `(Recorded and Estimated)` | `(Recorded, Estimated and Declared)` (KD3) |
| `reconciliation.heading` `zero_stated`, `not_received` | `Fuel cost (Recorded): the accounts say $0.00 and no fuel invoices are recorded.` | unchanged, also when a tolerance is passed (C10) |
| `reconciliation.statement` `matched` / `not_matched` | `... matches the management accounts within 1% (Recorded).` | `... within 1% (Declared).` |
| `reconciliation.standing` `reconciled`, `this_month_not_matched`, `none_matched` | `Reconciled: ... within 1% (Recorded).` / `Not yet reconciled: ... within 1% (Recorded) yet.` | `(Declared)` in place of `(Recorded)` |
| `reconciliation.money_word` | the figure's word, for example `Recorded` | unchanged: a `RECORDED` figure (KD1) |

Every changed expected string is in the commit-1 diff (`git show 8a48b8e51 -- backend/tests`). These are 58 added
lines that contain "Declared". Each follows rule R1 or R3, apart from KD3.

## Acceptance (spec §6)

- **V1, C11, C12:** `DECLARED` reads "Declared" for all 6 origins and for `None`. Pass.
- **Accounts "Recorded", tolerance "Declared" in every 3A7 sentence that prints them:** R1 and R3 strings. Pass.
- **No evidence word for an unprinted figure:** C10 gives C7's sentence. Pass.
- **Logger rule:** N14-N17 pass, while P58a and P58b are still caught (`HAND_BUILT_NEW`). Pass.
- **P55 on the real allow file:** P55a-c behave under the merged helper. The allow file holds exactly the two `profiles.py` lines. Pass.

## Checks run (revision `baf072f50` unless stated)

- Tests first (red): the new tests on main `fa13f254f`, before any code change: 41 failed, 413 passed.
- `run-host-tests.ps1 -- test_sc1_statements.py test_3a7_reconciliation_words.py test_3a7_reconcile_command.py test_3a7_reconciliation.py`: **512 passed**, 3.7 s.
- `heavy-slot.sh --db -- run-host-tests.ps1 -- test_3a7_reconciliation_postgres.py` on `assetops_test`: **3 passed**, 7.65 s.
- `python3 tools/checks/statement_catalogue.py`: `OK statement catalogue: load, coverage, legacy, scan (2 adopted), keys, imports`, with `ALLOWED entries: 2`:
  - `ALLOWED backend/assetops_backend/commercial/profiles.py:124 CODE h:_swap_day_month:052fded502f9 | return fmt.replace("DD", "\0").replace("MM", "DD").replace("\0", "MM")`
  - the same line for `h:_swap_day_month:d40e38ccee22`
- `--self-test`:
  - Red: plants in place, logger code old. `FAIL N14/N15/N16: expected pass; got HAND_BUILT_NEW`; `75 of 78 plants behave`. N17 already passed, because `_log` was in `LOG_NAMES`. P59d proves N17 instead.
  - Green: `OK statement catalogue self-test: 78 of 78 plants behave`.
- Baseline diff: `--prune` removed exactly `commercial_upload_api.py` `g:build_commercial_upload_router.run:395904969735` and `estate/index.py` `g:opportunity_read:693eaf7b776b`. The two `profiles.py` fingerprints were removed by hand. Nothing else changed (10 deletions).
- P59 plants and check-all: see the round-1 section that follows.

## Known deviations

- **KD1 (render rule, D-SC1F.3).** Read literally, the ruling raises `ABSENT_PRINTED` on `reconciliation.money_word`.
  - That statement prints only `{word}`, the evidence word of a figure that the page prints beside it (D-SC1.16). Read literally, the ruling counts no slot there, and 5 money_word tests failed.
  - Built rule: a variant that states no figure at all keeps wording all its present `of` figures. Any variant that states a figure counts only those figures.
  - The Architect should confirm this, or rule another way, for example a `requires` on the variant.
- **KD2 (guard shape).** The obvious `slots[field]["type"] == "evidence"` comparisons trip `MECH_BRANCH` in `render.py`. The second pass is therefore chosen by a `_LATE = {"evidence": True}` table, like `_FILL`. Behaviour is unchanged.
- **KD3.** The heading for unnamed-origin records changes from `(Recorded and Estimated)` to `(Recorded, Estimated and Declared)`. This is R1's rule, applied to an origin that R1's two literals do not list.
- **Broader rule 3.** `_getlogger` also accepts a bare `getLogger(...)` receiver, which the ruling's rule 2 already names.
- **Not changed.** `test_3a7_reconciliation_words.py` defines `test_mixed_origin_lines_read_the_weakest_origin` twice; this was already the case on main.

## Residual risk and review focus

- KD1 is the one semantic call the ruling did not make.
- The two-pass fill and the nested parts: a part's own late pass sets `r.stated`, and the parent resets it after all its first-pass fills.
- `_bound_loggers` collects attribute names too, so `self.audit = logging.getLogger()` makes any `.audit` receiver in the module a logger.
