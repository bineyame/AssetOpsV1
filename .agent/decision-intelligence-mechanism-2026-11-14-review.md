# Review: decision-intelligence-mechanism-2026-11-14.html

Reviewer: fresh Claude Reviewer, 2026-11-14. Repository at main 9b4d9bd15c53daff70b2322012932720e1f96edb, the same revision the document cites. No code, test, database or document was changed.

## Verdict: REVISE (one Medium finding, a wording fix of about five sentences)

The document is accurate, complete against sections 1 to 4 of the request, and honest about its gaps. About 120 `path:line` citations were opened, covering every citation in §2 and in §3.11 Case A and Case B, plus samples from §1, §3 and §4 and all the migration references. Almost every one says what the document claims. The rest drift by a line or two and are still correct in substance.

The central claim holds: no decision path reads the CHECKED role. One safeguard condition is misread, and it is repeated in the summary, the stage table, two figures and Q5. That is the only blocking item.

## What I verified

- **Who reads the map.** I searched the backend independently for `outcome_roles`, `categories_for(`, `lens_flags(`, `records_for(`, `kpi_record(`, `CONTRIBUTIONS`, `thread_signal_key(`, `finding_signal_key(`, `\bCHECKED\b`, `ENTRIES`, `@LINKED`, `["role"]`, `.role ==`, `must_not_harm` and `["items"]`, and the frontend for `CHECKED` and `must_not_harm`.
  - None of these modules imports `outcome_map` or `outcomes.status`, or reads a category role: `dispatch_v3`, `finding_episode`, `finding_service`, `fuel_cost`, `fuel_cost_v2`, `money_eligibility`, `recompute`, `reserve_trial`, `verification_rules`, `verification`, `verification_families` and `credit`.
  - `verification_families` imports `outcomes.price_action`, which does not touch the map.
  - `actions/service.py:706` uses `categories_for` only for the wire.
  - All 10 `CONTRIBUTIONS` records are MOVES.
  - The "no decision path reads CHECKED" conclusion is confirmed. Three small omissions from the reader list are in L1.
- **Probe results.** I wrote my own probe in the scratchpad, reusing the `test_s3_dispatch_v3_analytic` fixture. Every probe result in the document reproduces:
  - PV 40 / load 30 gives 60 min CANDIDATE, even at SOC 35.
  - SOC inside the headroom with PV 31 gives 60 min INDETERMINATE.
  - The mixed run gives 30 Candidate and 30 Necessary minutes, with `BATTERY_NEAR_RESERVE` on a CANDIDATE interval, so the battery warning fires.
  - The probe is correctly labelled "probe" wherever the document uses it.
- **Test names.** Every cited test exists under its file and name. I read the Case A and Case B tests, and each asserts the behaviour claimed. I also checked the "not covered by tests" claims and found no covering test:
  - PV-alone CANDIDATE in v3.
  - The unserved-critical-energy FAIL branch. `test_unserved_critical_energy` checks only the measurement.
  - The interval-level mix.
  - B4.
- **Pure tests.** `pytest` over the 18 listed files plus `test_fuel_cost_v2.py` gave 554 passed in 4.55 s. PostgreSQL tests were not run, as policy allows.
- **HTML.** The page is self-contained, with no `<script>`, `<link>` or external URL. All 5 SVGs parse as XML and the HTML tags balance. Colours are CSS tokens with dark mode under both `prefers-color-scheme` and `[data-theme]`, and the SVGs use only `var(--…)` colours. The two required diagrams are present: the architecture diagram (Fig 1) and the sequence diagram (Fig 3). Their labels and references match the text and the code.

## Findings

### M1 (Medium, blocks): the trial SOC safeguard is stated as stricter than the code

**Where.**
- Short answer ("The trial rule needs battery charge more than 10 points above the reserve").
- §1.1 stage 7 ("whose lowest usable Candidate-segment SOC is above r + 10").
- Fig 2 ("lowest SOC must exceed r + 10").
- Fig 3 step 12 and Fig 4 ("lowest Candidate SOC > r + 10").
- §2.4 Q5 ("refused … unless the lowest Candidate SOC exceeds r + 10").

**Code.** `actions/reserve_trial.py:249-252` judges each Candidate segment on its own: `eligible = [v for v in verdicts if v["eligible"]]`. The rule refuses only when no segment is eligible. The basis is the latest eligible segment (`:254-256`), and segments that are not eligible are skipped without a refusal.

A test pins this: `test_s6_action_rule.py::TestUnavailableReasons::test_any_eligible_segment_is_enough_and_is_cited`. "The lowest usable reading decides" (`:219`) holds only within one segment.

**Why it matters.**
- This is one of the three hard-coded reliability safeguards that the Case B analysis relies on.
- A Finding whose other Candidate segments ran with the battery inside the headroom can still be offered the trial. Those segments are Candidate through rule 3 (PV alone), which does not check SOC.
- Accuracy of the safeguard conditions is the review's first priority.

**Fix.** Reword all five places to say "at least one cited Candidate segment whose lowest usable SOC is strictly above r + 10; segments that fail this are ignored, not refused". Cite `reserve_trial.py:249-256` and the test above. The Case A "Proposal" row can keep its current tests and add this one.

### L1 (Low): the §2.2 reader list says "every hit" but misses three readers

None of the three changes a decision, so the conclusion stands.

- `site_outcomes/mini.py:718-719` counts the warnings that MOVE MG-4 into the Protect headline ("N early warnings on battery and generator"). This is MOVES, text.
- `chain/why.py:82-85` `related_threads` selects the "Why?" threads for a category in **either** role. This is CHECKED and MOVES, text.
- `site_outcomes/board.py:379-380` uses `kpi_record` to choose the KPI node, which is in `CONTRIBUTIONS` and so MOVES only.

**Fix.** Add the three rows, or soften "every hit" to "every hit that can affect a role-dependent result".

### L2 (Low): the reserve-trial adapter is labelled as unverified, but it can be verified

The document flags the adapter's `RuleInputs` source as taken from the docstring only. That label appears once, in "Not verified (b)". It is not repeated beside §3.4, stage 7, Q5 or the Case A Proposal row, all of which rely on it.

The adapter does exist and matches the docstring. `actions/adapters/postgres_action_store.py:159-215` reads the `battery_soc` rows of each CANDIDATE segment's cited `evidence_ids`.

**Fix.** Cite the adapter and drop item (b). Otherwise, mark the dependent sentences "Doc says".

### L3 (Low): the test-run numbers cannot be reproduced

The document says "534 pure tests passed, in 19 files" but lists 18 files, with `test_fuel_cost_v2` cited elsewhere and missing from the list. I got 525 passed over the listed 18 files and 554 with `test_fuel_cost_v2.py` added. Neither matches 534.

**Fix.** List the exact files and the count.

### L4 (Low): small inaccuracies

- The Fig 1 caption says "Black arrows", but the arrows are drawn in `var(--muted)`, which is grey, and light grey in dark mode.
- §4.2 Work case lists its states as OPEN, IN_PROGRESS, COMPLETED, CLOSED and CANCELLED. `work/model.py:121` also has `VERIFICATION_WINDOW`.
- The 90-minute minimum-runtime probe is announced but its result is never reported. My run gave the whole 60-minute run as INDETERMINATE, with no Candidate. Report it in the B3 row or drop it from the probe list.
- The B1 row cites `test_candidate_over_a_closed_episode_reopens_it_under_the_same_id`. That test closes the episode with generic NECESSARY segments, not a reserve constraint. The chain is still sound when it is combined with `test_near_reserve_is_physical_necessary`. Say that the two tests together prove the B1 path.

## Not verified

- The PostgreSQL-backed tests cited by name were not run: `test_s6_verification_evaluator_postgres`, `test_s6_action_records_postgres` and `test_ch6b_estate_postgres`.
- The frontend role readers were checked only at the cited lines (`outcomeCategories.tsx:80-90, 150-158`, `OutcomeBoard.tsx:266-270`).
- No browser rendering. The HTML was inspected only as source.

## Re-review (revision 2)

Reviewer: fresh Claude Reviewer, 2026-11-14, main at 9b4d9bd15c53daff70b2322012932720e1f96edb. No code, test, database or document changed. Only pure tests were run.

### Verdict: ACCEPT WITH NOTES

M1 and L1-L4 are fixed in the body, not only in the change note. The new citations check out. Two Low notes remain, and neither blocks.

### Prior findings

- **M1, fixed.** I searched the whole file, including SVG text and titles, for "lowest", "every/all Candidate", "r + 10", "r+10" and "10 points". Every statement of the trial rule now says that one cited Candidate segment with lowest usable SOC strictly above r + 10 is enough, and that the other segments are ignored. These are the short answer (l.121), the §1.1 stage 7 row (l.308), Fig 2 (l.441), Fig 3 step 12 (l.562), §2.4 Q5 (l.497), §3.4 (l.619), Fig 4 (l.684, l.697) and the Case A Proposal row (l.720). This matches `reserve_trial.py:249-256`. The per-segment test (`low > threshold`) is at `:219-228`. No "lowest/every Candidate SOC" wording is left. The rows that still mention "SOC ≤ r + 10" (l.607, 610, 692, 694) describe the dispatch rules, not the trial rule, and they are correct.
- **L1, fixed.** The three readers are added at l.465-467, and the search note says revision 2 added them. I checked `mini.py:718-719`, `chain/why.py:82-85` and `board.py:379-380`, and each says what the row claims.
- **L2, fixed.** `postgres_action_store.py:159-215` is cited at l.308, l.497 and l.619, and it matches the code. It reads the `battery_soc` rows of each CANDIDATE segment's `evidence_ids`. The old "Not verified (b)" item is gone. The current (b), the headroom-study producer, is a different item.
- **L3, fixed.** l.133 lists 19 files, now with `test_tfc2` and `test_fuel_cost_v2`. My run of exactly those 19 files gave `554 passed, 1 warning in 4.53s`.
- **L4, fixed.**
  - Fig 1: the arrows are now called grey (l.152), and "Black" no longer appears.
  - VERIFICATION_WINDOW is added (l.812).
  - The 90-minute probe result is reported in the B3 row (l.732). It matches my first-round probe.
  - The B1 row says which two tests prove the path together (l.730).

### New citations checked

- `reserve_trial.py:29`, `:36` (the HEADROOM constant derived from `SOC_HEADROOM_POINTS`), `:219-229`, `:227-228`, `:234-289`, `:238-266`, `:240` (`lifecycle != "SUPPORTED"`) and `:249-256`.
- `test_s6_action_rule.py::TestUnavailableReasons::test_any_eligible_segment_is_enough_and_is_cited` (l.183).
- `work/model.py:107-121`.

All are accurate.

### Findings

- **N1 (Low).** The cited test's ineligible segment fails on SOC_MISSING (it has no readings, `segment(start=...)`), not on SOC_NOT_ABOVE_HEADROOM. The test proves that any ineligible segment is ignored. The claim at l.497 is narrower: a segment inside the headroom is ignored. That claim is true by the same code path (`:249-250`), but no test pins it.
  - Fix: optional. Add "same code path; the test uses a segment with no SOC" next to the citation.
- **N2 (Low).** l.497 says the proposal is refused "with `SOC_NOT_ABOVE_HEADROOM` only when no … segment" is eligible. When no segment is eligible, the code returns the *last* segment's reason (`verdicts[-1]["reason"]`, `:251-252`), which may be SOC_MISSING, ASSET_MISMATCH or another reason. The "only when" direction is correct. The implied reason code is not guaranteed.
  - Fix: optional. Say "refused (with the last segment's reason, for example SOC_NOT_ABOVE_HEADROOM)".

### HTML

- The page is self-contained. It has no `<script>`, `<link>`, `<img>`, `@import` or http(s) URL. The only hrefs are 8 in-page anchors, all of which resolve, plus the sibling `convertion_potential.html`.
- All 5 SVGs parse as XML, and the HTML tags balance.
- The light tokens (`:root`), the dark tokens (`prefers-color-scheme` + `:root:not([data-theme="light"])`) and `:root[data-theme="dark"]` define the same 16 tokens.
- Every `var(--…)` that is used is defined. There are no raw colour literals in fill or stroke, and `body` has an explicit background.

### Not verified

- PostgreSQL-backed tests, by constraint.
- Browser rendering. I inspected the source only.
