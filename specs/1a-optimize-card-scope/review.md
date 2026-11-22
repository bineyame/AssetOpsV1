# 1a review

## Round 1 (fresh Claude reviewer, 2026-11-21, head `6e88a0e78`, diff `e39a5d2fa...6e88a0e78`)

**Summary (verdict: ACCEPT, ready for the owner's walkthrough; merge stays held).**
- The figure is unchanged and byte-equal to the claim (S1, ch5d1). No total is added. The scope line holds no amount (S7, whole decimal tokens).
- The six variants match D-1A.9 word for word. They are one SC-1 statement and pass the catalogue guard, including the number-word refusal. `tools/checks`, `chain/vocabulary.py` and `demo_combined_rows.py` are untouched.
- The `ch5a2` golden gains exactly one line, the `scope_text` key. The other three cards are unchanged (F3). The Optimize face is its five hooks plus `data-portfolio-card-scope` (F1).
- The line is truthful for DAY Sites, and for PERIOD Sites as the `cost_scope_text` facts give it (S3, S5b, S5c). The `_summary` wiring for a PERIOD Site has no test: two plants there survive (L1).
- Fast check-all is green: All 42 guards passed. Focused backend tests: 792 passed and 1 failed. The failure is kis8, which was already failing on the merge base and is fixed on `main` by `e9b9455ca`. Vitest: 94 passed. tsc: exit 0.
- Q-M3 was not run. `test_ch6b_estate_postgres.py` needs a template built from this checkout, so it is left for the coordinator.
- Findings: 0 High, 0 Medium, 3 Low. None blocks.

### Findings

**L1 (Low, test gap, not an acceptance gap): the PERIOD-basis scope facts in `_summary` are untested.**
`backend/assetops_backend/site_outcomes/read.py:707` sets a PERIOD Site's scope day to `wd[0]` on a one-day window and to None otherwise. Both S8 and S9 (`backend/tests/test_1a_optimize_scope.py:223`, `:231`) drive only mini-grid `SiteRef`s, so this branch is never exercised through `summary()`. I ran two plants of my own in a scratch copy, and both survived 1a's tests plus ch5d1, out_w2, ch6b2, ch5a2 and pv1 (142 passed):
- (a) `... else None`, which drops the one-day PERIOD day;
- (b) `... else wd[-1]`, which would make a cold-chain or EV Site read "lead issue on 30 October 2026, the last of the 7 days shown", a false statement for a latest-event claim.

The code is correct as written, and no PERIOD Site is priced today (D-1A.5), so no wrong line can reach a screen now. The dispatch asks that the line be truthful for cold-chain and EV Sites, but only `cost_scope_text` holds that under test. *Fix:* add an S8b using the same recording fake board with a cold-chain `SiteRef` (domain not MINI), priced over 7 days, expecting S3's `one_latest` text, and over one UTC day, expecting the `one_day` text. That is a few lines in commit 2's file.

**L2 (Low, residual risk): "the last of the N days shown" assumes `window_day == window_days[-1]`.**
The two agree for UTC-midnight pairs, Site-local-midnight pairs and mid-day windows. They disagree when `lo` is a Site-local midnight and `hi` is a UTC midnight. For Nairobi, 1 Oct local to 31 Oct UTC gives `window_day` = 30 Oct but `window_days` = 31 days ending 31 Oct. The line would then read "on 30 October 2026, the last of the 31 days shown", which is false. I checked this in Python against `chain/read.py:138` and `:162`.

The UI sends UTC pairs ("Times in UTC"), so this case is reachable only through a hand-built API query. *Fix (optional):* render `one_range` or `each_range` only when the day equals `wd[-1]`, and otherwise fall back to `DAYS_DIFFER` or `LATEST_IN_RANGE`. Alternatively, pin the agreement in a test. This is a preference, not a 1a acceptance criterion.

**L3 (Low, merge hygiene): the branch is behind `main` and the merge conflicts in three files.**
`git merge-tree main HEAD` reports content conflicts in `.ai/state/index-3.md`, `specs/INDEX.md` and `backend/tests/test_sc1_statements.py`. The last one is the T8 statement set, which now also needs 0K4b's `foundation.property_name` and `model_profile.need` and the `foundation_property` vocabulary set. All three are union resolutions. `vocabulary.py` auto-merges.

Rebasing also clears the one focused failure, `test_demo_combined_finish_rows.py::test_kis8_protect_passes_on_the_node_line_and_fails_otherwise`. It fails on the merge base `e39a5d2fa` and is fixed on `main` by `e9b9455ca`. *Fix:* rebase or merge `main` before the walkthrough merge, then rerun T8 and the catalogue guard on the merged tree.

### The dispatch's ten checks

1. **The figure.** S1 asserts that `value.text` is byte-equal to `claim.text`, and that `detail`, `basis_text` and `claim` equal ch5d1's values. ch5d1's three expected dicts changed only by `"scope_text": None`. `test_two_priced_sites_list_each_and_never_sum` passes, and no total form appears.
2. **The scope line.** It is truthful for one Site on DAY (S1, S2, S8), several Sites on DAY (S4), PERIOD (S3), two PERIOD Sites (S5b) and mixed bases (S5c). Each variant on a range says "not their total", and none implies a total. The PERIOD `_summary` branch is untested (L1), and there is a residual risk from mixed-frame windows (L2).
3. **Wording.** All six texts in `i18n/statements/en/portfolio_card.py` equal D-1A.9's table exactly, and so do the six case texts. The catalogue guard passed, so no literal number words. The texts render through SC-1. `noun.day` is the only vocabulary addition. The legacy and hand-built baselines and `tools/checks` are unchanged (`git diff e39a5d2fa HEAD -- tools/checks backend/assetops_backend/chain/vocabulary.py tools/demo_combined_rows.py` is empty).
4. **Golden.** The whole diff of `estate_week_2026-10-25.json` is one added line: `"scope_text": "Cost of Kobo's lead issue on 31 October 2026, the last of the 7 days shown, not their total"`.
5. **The other three cards.** The server adds `scope_text` only to `_optimize_card`. F3 asserts that Grow, Protect and Assure have no scope element, no `.oc-pfdays` and exactly `onCard`'s hooks. F1 asserts that the Optimize hooks are `onCard` plus `data-portfolio-card-scope`, and that the line sits after the value and before the detail. The uqfi five-hook test is unchanged and passes.
6. **S7.** It uses `(?<![\d.])<amount>(?![\d.])` over `amount`, `low` and `high`. I checked that `_amounts` really extracts `['3.31']` and `['3.31', '3.97']`, so the test is not vacuous. The 31 October range case passes.
7. **Mid-build questions.**
   - Q-M1: the parametrised render-and-variant test uses `_render(..., trace)` with the same signature T9 uses (`test_sc1_statements.py:748`). It renders each case's English and checks the chosen variant. It is the only thing that fails PL7 on words; the guard proves coverage only. I accept the default: no guard change, and the test is local to 1a.
   - Q-M2: the T8 addition matches the precedent.
   - Q-M3: see item 10.
   - Q-M4: there is no dark theme, so the dark captures equal the light ones, as stated.
8. **Plants.** I reran PL2 (`n == {30}` as ONE_DAY), which failed S1, S4, S7, S8 and S9, and PL7 (the rev 1 `each_differ` wording), which failed S5, S5b, S5c, S7 and the `[each_differ]` case render. Both match the packet. My own plants (a) and (b) survive (L1).
9. **Screenshots.** I viewed `one-390-light-card`, `one-390-light-page`, `one-1440-light-page` and `two-1280-light-card`. The line is readable at every width, wraps cleanly in the narrow 390 column, and sits under the figure and above the sentence. No other card carries a line. `summary.json` records 0 console errors, no overflow and no unlisted API path. Two things for the walkthrough, neither from 1a:
   - At 390 and 1440 the value's "possible extra fuel / cost" breaks with a wide gap. This is the existing `oc-pffig` layout; 1a changed no CSS.
   - The scope line runs straight into the grey detail sentence with no gap, and reads slightly heavier than it.
10. **Q-M3.** Not run. The template fingerprint covers traced modules, including `site_outcomes/read.py` and the i18n data, both of which 1a changes. So every existing template is stale for this checkout, and running the test would need a template build. That is left to the coordinator's slice-end run. By reading, the test's expectation `CostScope({"KOBO-001": d13}, {"KOBO-001": 7})` is consistent with the window D7 to D14 UTC: 7 days, the last is D13.

### Checks run (by this reviewer)

| Check | Result |
|---|---|
| `bash tools/heavy-slot.sh --wait-seconds 3000 -- pwsh -NoProfile -File tools/check-all.ps1` (worktree, `6e88a0e78`) | `check-all: 137.0 s wall (0.2 s waiting for a slot), 4 jobs at once. All 42 guards passed (blocking; 0 advisory, 0 warned).` |
| pytest from `backend/`: `test_1a_optimize_scope`, `test_ch5d1_optimize_card`, `test_ch6b2_portfolio_cards`, `test_sc1_statements`, `test_ch5a2_contract`, `test_pv1_value_lines`, `test_out_w2_summary_window`, `test_demo_combined_finish_rows`, `tools/checks/test_chain_coherence.py` | `1 failed, 792 passed`. The failure is kis8, the base's known failure (L3) |
| vitest `src/estate/__tests__/estatePortfolio.test.tsx` and `tsc -b --noEmit` (heavy slot) | `94 passed (94)`; tsc exit 0 |
| Plants PL2 and PL7, and reviewer plants (a) and (b), in a scratch `git archive` copy | as in item 8 and L1 |

**Caution for later runs.** pytest started from the repo root (not `backend/`) imports the main checkout's `assetops_backend` through the editable install. My first focused run did this and showed 23 spurious failures. Run worktree tests from `backend/`, or check `assetops_backend.__file__` first.

### Not verified

- The postgres card test (Q-M3).
- A live-server render of the line. The captures use `page.route` fixtures.
- The merged tree after the rebase (L3).
