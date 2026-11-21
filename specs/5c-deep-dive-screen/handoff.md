# 5c handoff (unit 1 done; units 2 and 3 next)

Builder (Claude), 2026-11-21, branch `task/5c-deep-dive-screen`, head 37e823259 (main fa13f254f merged at f3a995997).

## Unit 1: done
- `deep_dive/{tables,words,view}.py` and `i18n/statements/en/deep_dive.py`; `words.py` and `view.py` are in the
  guard's `ADOPTED` (`tools/checks/statement_catalogue.py:41`); `python tools/checks/statement_catalogue.py` is OK.
- Tests: `backend/tests/test_5c_deep_dive_view.py` (tests 1 to 7 plus every-variant case rendering; 136 passed),
  cases `backend/tests/statement_cases/deep_dive.py`, fixture `backend/tests/fixtures/5c/deep_dive_lakeside_2026-10.json`.
- Plants P1, P2, P4, P6, P9, P11, P13 to P17 each fail their test: `/opt/assetecon/evidence/5c/unit1/plants.txt`.
- Focused tests on the host: `bash tools/heavy-slot.sh --wait-seconds 3000 -- bash -c 'cd backend &&
  PYTHONPATH=$PWD:$PWD/../contracts:$PWD/../simulator /opt/assetecon/AssetOpsV1/.venv/bin/python -m pytest
  -p no:cacheprovider tests/<file> -q'`.

## Literals that differ from spec 3.5 (each from a rule; the packet lists them)
- PF2/D-4A.12: the revenue stop text and `not_available.rows` follow 4a's records (billing export, feeder meter,
  meter register, meter reads, loss band; no tariff-sheet or billing-adjustments row).
- PF5 "when" in tile4; PF8 `headline` is `{"text","evidence"}` (A: ["Estimated"]); D-3A7.16 `standing.details` and the
  assure drawer lines `[text, *details]`; A2 reads "so they cannot be compared"; PF12 SITE_SETUP words.
- KD1 (World H): the Diesel price driver has `detail` null (a price does not sum across Sites, so the portfolio row has
  no actual or target; section 3.2's rule gives null) and word "Modelled, not yet reconciled" (its effect is Modelled
  litres times the price difference). Spec 3.5 H's literal said "Actual $1.25 per L · Target $1.25 per L",
  "Emulated". The code follows the rule.
- KD2: the fixture was written from World A's run after every value was compared with section 3.5; test 3 asserts
  each section 3.5 literal by hand as well, so the fixture cannot drift without test 3 failing.
- L5 lead vector added (P14 survived L1 to L4).

## Next
- Unit 2 (spec section 4; tests 8, 9), then unit 3 (section 5; tests 10 to 15), then the packet.

## Unit 2: done (head after this commit; code at b7a3e3a9f)
- `deep_dive/read.py` (`DeepDiveRead.month` :43; organisation standing at `known_at=served.as_of` :52; `BadMonth`, a
  `ValueError("BAD_MONTH")`, :25), `deep_dive/actions.py` (`AgreedActionsPort`, `NotConnectedActions`),
  `deep_dive/composition.py` (`build_deep_dive_read` :32; the actions line :39), `deep_dive_api.py` (router :39;
  real-data person check :52; 422 :60; store fault 503 :62), `main.py:699` (after the commercial upload router;
  disposed on shutdown). Refusals `{"code","text"}`: statement `deep_dive.refused` (`i18n/statements/en/deep_dive.py:434`,
  PF5 `month_example` slot) and `person.person_required`. `ROUTE`, `NO_STORE`, `MONTH_PATTERN` in `deep_dive/tables.py`
  (PF9). `read.py` and `deep_dive_api.py` joined `ADOPTED` (`tools/checks/statement_catalogue.py:43`).
- 3C2's `actions/agreed.py` is on this branch, but mapping its views to `AgreedAction` is more than one line, so
  `NotConnectedActions()` stays (spec 4.3 leaves `StoreAgreedActions` and test 9(d) to 3C2's unit 2).
- Tests: `backend/tests/test_5c_deep_dive_api.py` (test 8, 17 cases; also the composition's dispose and `create_app`
  mounting the route) and `backend/tests/test_5c_deep_dive_postgres.py` (test 9 (a)-(c) plus the real composition).
  Failing first (tests only, at cf2d1db1a): both files error at collection. Plants P3 (test 9) and P10 (test 8) fail:
  `/opt/assetecon/evidence/5c/unit2/plants.txt`.
- How to run test 9: `bash tools/heavy-slot.sh --db --wait-seconds 3000 -- bash -c 'cd backend && export
  ASSETOPS_TEST_DATABASE_URL=postgresql+psycopg://assetops:assetops-local-dev@127.0.0.1:55432/assetops_test;
  PYTHONPATH=$PWD:$PWD/../contracts:$PWD/../simulator /opt/assetecon/AssetOpsV1/.venv/bin/python -m pytest
  -p no:cacheprovider tests/test_5c_deep_dive_postgres.py -q'` (the harness clones a run-owned `_test` database).
  `check-architecture.ps1` needs `ASSETOPS_GUARD_PYTHON=/opt/assetecon/AssetOpsV1/.venv/bin/python` in a worktree.
- Risks: MBQ1 (`mid-build-questions.md`): 3A7's real standing words end "within 1% (Recorded)."; spec 3.5 and the
  unit-1 fixture say "within 1%."; test 9 asserts 3A7's words, the Architect settles 3.5. With a `DATABASE_URL`,
  `create_app` now builds the snapshot composition (the rules digest reads files once per app).

## Fix round 1 (units 1-2; review round 1 and rulings D-5C.19 to D-5C.25), 2026-11-21
- Branch `task/5c-deep-dive-screen` in worktree `AssetOpsV1-5cbe`; `main` merged twice (SC-1f at 28cb8e449, the
  rev-3 rulings at 3d2760637), both clean.
- **H1.** `group_sums` carries None; the tile split, a step drawer's effect line and a residual stop are left out
  when there is no figure; group and outcome values read "Not available yet". Test 4 i (Mto's records in KES, so
  nothing compares) asserts every place.
- **H2 / D-5C.19.** `words.SCREEN_EVIDENCE` hands `DECLARED` to the shared vocabulary as `RECORDED` (section 2.4's
  order); test 5 has a DECLARED row for each origin. 3A7's passed-through text keeps its own words.
- **M1.** Test 9 asserts 3A7's post-SC-1f words ("(Declared)", "Fuel cost (Recorded, Emulated and Declared)") and maps
  unit 1's injected fuel-cost detail to them.
- **M2 / D-5C.20.** The headline's `evidence` is `word()` (through `money_word`) of R and of the named heading; class
  test `test_3_headline_evidence_is_the_figures_words` over A, B, D, L1 to L4.
- **L2 / D-5C.21.** `drivers` nested with `key` and `children`; test 4(H) asserts section 3.5's literal.
- **L3 / D-5C.22.** No `more` outside Actions (already so); test 3 asserts it.
- **L1, flag (a) / D-5C.23.** `CELL_FORM[True]` is `AT_BUDGET` (" (at budget)"; the `deep_dive.money` variant renamed
  `at_budget`), used by the cell and the drawer row.
- **L5 / D-5C.25.** BILLING and LOSS_BAND reworded; `test_5_record_words_hold_no_comma_outside_brackets`.
- **Known deviation KD3 (Architect to confirm).** The no-comma case also caught `ANALYSING` ("the running record's
  analysis, still in progress", spec section 2.3's table). It now reads "the running record's analysis (still in
  progress)". The coordinator accepted it; spec section 2.3's table row now reads this way (fix round 2).
- **Unit 3 follows.** The screen's own fixture or tests need to carry: "(at budget)", the nested `drivers`, the
  headline's evidence "Estimated, not yet reconciled", and the two record words.
- Plants: `/opt/assetecon/evidence/5c/fixround1/plants.txt`.
