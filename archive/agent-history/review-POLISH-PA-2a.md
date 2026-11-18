# Review: POLISH PA-2a (server copy, display codes and Finding titles)

Reviewer: fresh Claude reviewer (not the author). Date 2026-11-01.
Branch `task/POLISH-PA-2a-server-copy`, worktree `AssetOpsV1-polA2`. Reviewed `git diff 4681ba7d8...53b02604c`,
plus the follow-up commits `91ba99b07` (packet) and `7b37b0bf9` (golden fixture).
Spec: `.agent/build-sheet-POLISH.md` §3, §3.1 BE rows, §5 PA-2, §6, §7, Addenda 3, 4 and 6.

## Verdict: REVISE

The core work is correct. The code changes labels only. The new SQL is scoped. The Q5 move keeps the package
direction. The golden edits are text-only and agree with the code. Two Medium gaps should be fixed on the branch
before merge: one code label still shows the 6-digit code, and a PA-3 acceptance row will break. Both are small.

## Findings

### M1. Portfolio and estate Action titles still show the stored 6-digit code
- `backend/assetops_backend/estate/coverage.py:395`: `"action_title": f"Action {a['action_code']}"`.
- Why it matters:
  - This is a server-composed label that contains a code.
  - It renders on the Portfolio page (`frontend/src/estate/EstatePortfolio.tsx:166,169`), which is a PA-2 capture
    screen (`portfolio-week`), and in the estate Actions index (`actionIndex.tsx:96`).
  - It will read "Action ACT-000001". §3 requires `display_code` "in every server-composed sentence that embeds a code".
  - PB-2's frontend `displayCode()` applies to `code`/`action_code` fields, not to `action_title`, so no later slice
    will catch it.
  - The Addendum 6 Q8 list did not name this line, but `coverage.py` is a PA-2a file (Q10), and the §3 rule is general.
- Fix:
  - Use `f"Action {display_code(a['action_code'])}"`. `action_code` stays as stored.
  - Update the two test files that pin `action_title` (`test_w301_estate_api.py`, `test_w303_portfolio_workflow_labels.py`)
    if they pin a 6-digit value.
  - The golden manifest holds no `action_title`.
- Type: acceptance gap (§3 general rule).

### M2. PA-3's CO-3 acceptance row will fail on the new cost wording
- `tools/demo_combined_finish.py:29` `NOT_REALISED = "not realised savings"`, used at `:184`. CO-3 asserts that some
  Kobo Optimize-cost Earlier `detail` contains that phrase.
- Why it matters:
  - After `board.COST_PREFIX` changed to "Estimated effect of the trial (not money saved): " (`board.py:54`), no
    detail line contains the phrase.
  - CO-3 will fail in PA-3's `prepare` acceptance, which is a §5 PA-3 stop rule ("any CO row fails, stop").
  - The packet justifies `s602b_test_scoped_cases.py` on the same grounds (it pinned old wording) but does not list this one.
- Fix, either one:
  - (a) Change the marker to the new prefix, for example by importing `board.COST_PREFIX` or matching
    "not money saved". This is the same kind of edit as the `s602b` change.
  - (b) If the coordinator wants `demo_combined*` to stay PA-3-only, record it in the packet as a named PA-3 hand-off.
- Type: acceptance or regression gap, outside this slice's tests.

### L1. The joined Earlier line differs slightly from §3.1
- `board.py:422` joins the parts with " · ", so the line reads "…no lower supply cost per kWh. · Goal before the
  trial: missed; after: met."
- §3.1 gives "…no lower supply cost per kWh. Goal before the trial: missed; after: met."
- `test_out_e4_readback_postgres.py:28` pins the " · " form, so this was a choice, not an oversight.
- Fix: join with a space when the first part ends in "." (and update the pin), or list it in the packet as a copy
  deviation. This is a preference-level copy issue.

### L2. Q5 rewrites every cold observation code, not only TRANSFER
- `cold_site_reads.py:243`: `_limits` applies the whole `COLD_OBSERVATION_WORDS` map to the cold Site read. For
  example, "Not observed: TRANSFER, BUS, COMPRESSOR." becomes three plain sentences.
- I think this is the right behaviour: it is the same map estate already uses, and the only producer is
  `analytics/cold.py:645` over `cold.STEPS`, which the w302 test proves equal to the map.
- But it is wider than the Q5 wording ("rewrite the TRANSFER observation"), and the packet's old→new list names only TRANSFER.
- Fix: list the other seven rewrites in the packet's old→new section, so PA-3 and PC can check them in captures.

### L3. Golden: the first edit missed 2 literals (resolved), and a derive rule is now unused
- At `53b02604c`, the mixed branch's two literal `"finding_label": "Finding 00000001"` values (golden lines 3308, 3473)
  were not edited, so the mixed replay failed.
- `7b37b0bf9` fixes exactly those 2 strings, and nothing else changed in the fixture. Both rows are SUPPORTED, so the
  new value equals `TITLES[SUPPORTED]`.
- The `finding_label` derive rule (`test_w301_estate_golden_postgres.py:430-431`) is now dead. Removing it is optional.

## Checklist results

- **Display codes:**
  - `display_code` (`outcomes/display_code.py:13-23`) pads to at least 3 digits (`ACT-001234` → `ACT-1234`).
  - Anything that is not `UPPER-digits` is left unchanged (`COLD-LAB-001`, `generator-1`, lower case, double hyphen).
  - It is applied only to labels and sentences: warnings refs, board `_item_text`/`_action_name`, mini Verified
    results, cold `:314,:355`, the global and operational detail labels, "Incident …", "Maintenance request …".
  - Wire `code`/`action_code`/`public_code`/`case_code` values and the `coded_actions` basis pairs stay as stored.
  - No response keys were added or removed.
  - Gap: M1.
- **Finding labels:**
  - `finding_label(title)` returns "Finding" for a missing or empty title.
  - `_FINDING_TITLES` (`postgres_work_read.py:519`) filters on `tenant_id = :t AND site_id = :s` from `_ReadTx._p`,
    and is bounded by the given revision ids. It needs no `known_at`, because a title is fixed per revision and the
    ids come from cutoff-selected links.
  - The `finding_revisions` title column keeps its existing `created_at <= :k` filter.
  - `_ACTION_CODES` moved unchanged and is still scoped to tenant and Site.
- **RECURRED:**
  - The text is "Happened again after an earlier occurrence ({title})", or the same sentence without the title.
    This matches Addendum 6 Q3 exactly.
  - The `REASON_TEXT` keys are unchanged.
  - `head_titles` is built before the window filter, as ruled.
- **Q5:**
  - The import direction is estate → analytics, and estate already imported `cold_site_reads`.
  - The re-export is the same object (`evidence_money.plain_limitation is csr.plain_limitation` is pinned).
  - Only the TRANSFER sentence changed in estate.
  - The rewrite happens only at read time; the stored `limitations` are not written. The architecture guard passes.
- **Q6:**
  - `COST_PREFIX`, `COST_CHANGE`, `COST_NO_CHANGE` and `TRIAL_ATTRIBUTED` match §3.1 and Q6.
  - `VERIFIED_WITH_COST` keeps the verdict and code prefix and uses the ruled clause.
  - `trial_fuel_comparison.LABEL` is unchanged (`financials/trial_fuel_comparison.py:26`).
- **Golden:**
  - 14 title edits: 12 SUPPORTED and 2 NO_LONGER_SUPPORTED. The NLS edit is required, because `TITLES` changed
    that string too, and Addendum 4 rules it.
  - The 12 `$derive: finding_label` markers became the literal title, plus the 2 mixed literals in `7b37b0bf9`.
  - Every edited row's lifecycle matches its title.
  - No counts, money, states or ids changed. I see no fitting to output beyond the text that the ruling changes.
- **Numbers and story data:** none were tuned. The fake codes in the unit tests were padded (`MR-5` → `MR-005`),
  and those are inputs only.
- **Extra tools:**
  - `w601_seed.py`: it now finds the link by href instead of by the old label. Justified.
  - `s602b_test_scoped_cases.py`: it pinned the old workflow label. Justified.
  - `demo_combined_finish.py` was missed (M2).
- **Deviations:**
  - `mini.FINDING_TITLE` left for PB-2: accepted. It is pinned equal to the frontend `LIFECYCLE_WORDS`, which PB-2
    owns. Until PB-2, the Kobo board names the Finding "Generator support merits review" (`mini.py:107`) while the
    Findings index shows the new title. PB-2's task must carry it.
  - `COST_NOT_CALCULATED` left alone: accepted. It was not ruled, and builder copy latitude covers only capture-gate
    hits. "Modelled change not calculated: …" now sits beside the new wording, so PB-2 or PC should rule on it if it
    shows in a capture.

## The `test_w401_work_service_postgres::test_foreign_asset_and_evidence_refuse` failure

This is a clock-dependent test, not a regression. I diagnosed it; I did not fix it.

- The `clocked` fixture freezes the store's command clock at `POSITIVE_NOW = 2026-11-01T01:00Z`
  (`test_w401_work_service_postgres.py:111,176-181`).
- But `incident()`, `request()`, `plan()` and `oprec()` take `occurred_at` from the real clock: `at()` is
  `datetime.now() - delta` (`:43-44, :48, :71, :76`).
- `model.check_occurrence` (`work/model.py:236-238`) refuses `occurred_at > db_now + 5 min`, and it runs before the
  link-scope check.
- So once real time passes about 2026-11-01T02:05Z (`now - 1h > 01:00 + 5 min`), every refusal in the loop at
  `:380-389` returns `WORK_OCCURRED_AT_FUTURE`.
- It fails on any branch from that moment, including main. Other `clocked` tests that use `at()` defaults are exposed
  in the same way.
- Suggested fix, for the Lows log or a later task: build those bodies from `POSITIVE_NOW`, for example by passing
  `occurred_at=POSITIVE_OCCURRED`.

## Checks I ran

- `powershell -NoProfile -File tools/check-architecture.ps1`:
  - With no interpreter set, it failed: rule 8 had no Python, because this worktree has no `.venv`.
  - With `ASSETOPS_GUARD_PYTHON` set to the plan2 venv python: **Architecture check passed**.
  - I did not use `-ExecutionPolicy Bypass`.
- `powershell -NoProfile -File tools/check-agent-workflow.ps1`: **passed**.
- Pure pytest, using the plan2 venv with `PYTHONPATH` set to this worktree's `backend` and `contracts`. Without that,
  the editable install imports the main checkout and collection fails.
  - Command: `test_polish_pa2a_server_copy`, `test_cc_placement`, `test_idx_gaps_board`, `test_out_b1/b2/b3`,
    `test_out_c3_cold_cost`, `test_out_e4_readback`, `test_polish_pa1_board_truth`, `test_w204_cold_reads`,
    `test_w302_evidence_api`, `test_w302_money_api`, `test_w303_portfolio_api`, `test_w303_portfolio_workflow_labels`,
    `test_w504_ev_intent_api`, `test_w601a/b/c`, `test_out_a1_outcome_map`.
  - Result: 242 passed, 66 skipped, 2 failed. The 2 failures were only because `contracts` was not on the path.
  - Rerun of `test_w302_evidence_api` and `test_polish_pa2a_server_copy` with `contracts` on the path: 33 passed.
- Postgres, on base DB `assetops_test` (run-owned worker DBs):
  - Files: `test_w401_site_indexes_postgres.py`, `test_w502_domain_work_links_postgres.py`, `test_w301_estate_index_postgres.py`.
  - Result: **30 passed**, 0 failed, 12 min wall.
- Merge with main `ab248b4c3` (`git merge-tree`):
  - One textual conflict, in `.ai/CODE_STATE.md`. Both sides append a section, so it is trivial to resolve.
  - PB-0 touched only tools and frontend, so there is no code overlap.
  - After the merge, check-all has 12 guards. PA-2a has no frontend change, so guard 12 is unaffected.

## Not verified by me

- The golden replay (`test_w301_estate_golden_postgres.py`): I did not run it, as instructed. The implementer reports
  2 failed at `53b02604c` and 6 passed at `7b37b0bf9`. I checked that the fix commit is fixture-only (2 strings) and
  agrees with the code.
- The implementer's sheet-scoped regression (813 tests, 3 failures explained) and the w502 intent/action-index, w504
  and w601 Postgres files: I did not rerun these.
- The full suites, the frontend suite and build, and captures: none were run. Captures are deferred to PA-3 under
  Addendum 3.

## Residual risk not named in the packet

- `CAST(id AS text) = ANY(:ids)` cannot use the primary-key index, so each per-row title or code read scans the
  Site's `finding_revision` or `action` rows. This follows the existing `_ACTION_CODES` pattern, and the cost is small
  at demo scale.
- RECURRED quotes the earlier head's latest title. If that Finding is MERGED, the sentence quotes the unruled MERGED
  title ("Generator support episode merged into an earlier episode").
- Frontend test fixtures still carry the old server strings (`portfolioFixtures.ts`, `estatePortfolio.test.tsx`,
  `coldSiteViews.test.tsx`, `estateEvidence.test.tsx`, `outcomeBoard.test.tsx`). These are frontend-owned (PB-2),
  but PB-2 should align them with the new wire text.
