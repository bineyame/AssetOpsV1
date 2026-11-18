# S5-01 slice review - selected-window Site Overview (phase 2 = slice review)

Reviewer: fresh Claude reviewer (did not author the slice or the phase-1 review). Worktree `AssetOpsV1-review`, branch
`review/S5-01-slice` at `97922eb4`. Diff reviewed: `3b360af5..97922eb4`, S5-01 commits only (LR-01 merges
`4adbe4a9`, `499b720f` excluded; LR-01 was reviewed separately). `assetops_backend.__file__` confirmed in this
worktree.

## Verdict

**Accept.** No High or Medium finding. The Lows below should be fixed on the branch or recorded before merge.
None of them lets an amount through or blocks the owner walkthrough. Merge stays held for the owner record, as the
packet requires.

## Focus items judged

- **Fail-closed money (Known Deviation 1).** Sound. `money_state.py:81-111` reaches `PRICED` only when all of these
  hold:
  - the source is open;
  - upstream is `CURRENT` (line 101 re-checks it after the consequence-only fall-through at line 85);
  - no fence moved and discovery was complete;
  - the raw LR gate is `ELIGIBLE`;
  - the revision is latest and not merged;
  - the exact read is `CURRENT`;
  - `head_matches_seam` holds. This means the same head, the same FindingRevision, **and** the seam's
    `current_amount_permitted is True` (`read.py:302-303`);
  - quantity `AVAILABLE`, price `PRICED`, display `ROUNDED_OUTWARD`, provenance resolved, and
    `presented_as_current && current_amount_shown`.

  The amounts come only from `row["display"]` of that same exact-head row (`read.py:325-329`). In the UI, an amount
  needs `state === "PRICED"` and both bounds present (`SiteWindowOverview.tsx:480`). Unit
  `test_seam_that_does_not_permit_the_amount_fails_closed` covers the seam conjunct. The implementer's mutation
  record names that conjunct, and I found no path around it.
- **M1/M2 are fixed.**
  - `_pin` (`read.py:219-244`) requires a half-open intersection with the selected day (`NOT_IN_SELECTED_DAY`).
  - While the source is closed, `_pin` refuses an ID-only pin (`EXACT_REVISION_REQUIRED_WHILE_SOURCE_CLOSED`) before
    it resolves any revision.
  - When a pin is retained, `excluded` and `several_intersect` are blanked (`read.py:208-209`).
  - Tests: `test_a_pin_from_another_day_is_dropped_and_reported` (pending and closed cases) and
    `test_source_closed_keeps_only_pinned_audit_material`. I found no discovery leak while closed: `chosen` is `None`
    unless an exact pin exists, and the assessment section is `CLOSED` with null IDs.
- **URL round trip and pin drop.**
  - `SiteOverview.tsx` writes the served `utc_date` and `known_finding` IDs back with `replace`.
  - The `answered` ref stops the write-back from triggering a re-read.
  - `selectDay` and the Previous/Next `?date=` links drop the pin.
  - Vitest covers the default day, reload with a pin, and a day change that drops the pin. I ran it and it passes.
- **Honest copy.**
  - Every one of the 15 no-amount states has its own words (`MONEY_STATE_WORDS`). Unknown (`UNASSESSED`) and Failed
    each have their own wording.
  - The Finding list reads "Unavailable until the Site Finding index is delivered." from the server.
  - No total, savings, health, renewable or recommendation panel appears.
  - The demonstration label follows the Architect M3 ruling: `demonstration_label.SPEC_PATHS` now declares P02, and
    P02 `PRICED` carries `P02-power-late` in the evidence log.
  - Exception: see L1.
- **Layout at 390 px.** The CSS stacks the grid and timeline below 900/640 px, gives every grid child `min-width: 0`,
  and lets code wrap anywhere. The packet's browser claims record no page overflow at 390 for every stage
  (`.agent/S5-01-evidence/*-claims.json`). `layout-evidence.mjs` ran as 327 PASS / 2 FAIL; the two failures are
  store preconditions unrelated to S5, and the packet records them as such rather than as a pass. I did not rerun
  either browser script (see "Not verified").
- **`main.py` shutdown fix.** `app.router.on_shutdown.append(dispose)` works on FastAPI 0.141.1 / Starlette 1.6.0
  (versions confirmed). `test_the_application_starts_with_a_database_and_disposes_the_overview_seam` passes here. The
  move of `performance_gate` above the evidence router changes no other route: it is the same closure with the same
  captured objects.
- **Walkthrough tool safety.** I probed the guards, and each of these is refused before any action:
  - `assetops`;
  - `assetops_s501_owner_test`;
  - `assetops_s501_owner;x` (the `isalnum` rule also protects the f-string `DROP DATABASE`);
  - `var/other`;
  - `var/s501_owner/../../backend`;
  - an absolute path outside `var/`.

  Default ports are 8925/5425, plus 8926/8927 for the gateway. `stop-schedule` ages every `schedule_site_head` row
  without a WHERE clause, but only in the private database. That is acceptable.
- **Five-minute expiry.** This is honest in substance. Deviation 4 states it, the tool docstring states it, and the
  owner doc has a "Five-minute rule" paragraph that names it as the real production threshold. The doc's
  instructions around it are imprecise, though: see L2.

## Findings

### L1 (Low) - an unreadable intersecting Finding produces `ABSENT` ("a complete, current search found no Finding")
`backend/assetops_backend/site_overview/read.py:146-149, 138`.

**What is wrong.** When `finding_detail` returns `None` for a seam Finding that intersects the day, the Finding is
put in `excluded` as `FINDING_NOT_READABLE`. `discovery_complete` is still true, so with no other candidate the money
state is `ABSENT`, and the UI says "A complete, current search found no Finding whose time overlaps this day."

I probed this with the unit-test fakes: the result is `ABSENT`, `known_finding: None`, and freshness `CURRENT`. The
`excluded` entry that would explain it is not returned, because `known_finding` is null.

**Why it matters.** The packet allows `ABSENT` only after complete, current discovery has found no intersecting
canonical Finding. Here an intersecting Finding exists but could not be read, so this is an empty claim. Today it is
practically unreachable, because the seam and the Finding store read the same database. That is why it is Low.

**Fix.** Treat any `FINDING_NOT_READABLE` exclusion as incomplete discovery, which gives `UPSTREAM_PENDING` with a
typed reason. Assert the money state in `test_unreadable_seam_finding_is_not_called_merged`; today that test checks
only that `known_finding` is `None`.

### L2 (Low) - the owner doc's five-minute instructions point to the wrong step and cover only amounts
`.agent/S5-01-owner-walkthrough.md` ("Five-minute rule").

**What is wrong.**
- The paragraph says to "run step 5's `tick` command", but step 5 opens P02. The `tick` command is in step 8.
- `prepare` ticks before it verifies (172 s overall in my run). Starting `serve` and the dev server and reading
  the first pages can easily take the owner past five minutes after that tick. Step 1 then reads "Out of date" (`SCHEDULE_STOPPED`)
  instead of the "This day: Current" the table promises, and step 4 shows no P01 amount.
- The paragraph mentions only missing amounts, not the "Current" expectations.

**Why it matters.** The owner's visual acceptance is the merge gate. A first screen that contradicts the doc invites
a false reject, or a `tick` at the wrong moment (between `attest` and the step-6 reload).

**Fix.**
- Put the `tick` command in the five-minute paragraph itself.
- Tell the owner to run it right before step 1 and again before step 4, and never between step 6's `attest` and
  its reload.
- Note that "Current" in steps 1, 4, 8 and 11 also needs a tick in the last five minutes.

### L3 (Low) - the "Operating objective" panel shows status, not the day's result; `assessment.objective` is always null
`read.py:354-355`; `SiteWindowOverview.tsx:243-281`.

**What is wrong.**
- `objective` reads `window_assessment.result.objective`, a key that no dispatch-3.x result has. I checked
  `dispatch_v3.py:559-566`, and the result keys are `claim_level`, `counts`, `limitations` and `intervals`. So
  `objective` is always `null`.
- The panel renders the S3 currentness words ("Up to date ... uses every accepted record"), limitations and a
  Dispatch link. It does not render the day claim (`COMPLETE`/`LIMITED`/`INDETERMINATE`, which is `claim_level` and
  already in the DTO) or the necessary/avoidable counts.
- The S3 `coverage` is in the DTO but is not rendered. The context table shows accepted-reading coverage instead.

**Why it matters.** The packet asks for "S3 dispatch objective/status and coverage". Status is met. The day's
outcome appears only per interval in the timeline table. The owner may read "Up to date" as the answer to "did the
day meet its objective".

**Fix.**
- Drop the dead `objective` field, or source it from `claim_level`/`counts`.
- Show the day's claim level in plain words in the panel.

This is a content gap, not a correctness defect. The owner walkthrough can decide whether it is enough.

### L4 (Low, process) - review-packet slice-diff base
The packet's slice diff `394a9135..HEAD` includes the LR-01 merge commits. The dispatch's
`3b360af5..` minus the merges is the S5-only view. This needs no action beyond noting it for the Codex batch review.

## Checks I ran (this worktree, revision `97922eb4`; code identical to `05869379`, later commits are docs only)

- `tools/check-architecture.ps1`: passed. `tools/check-agent-workflow.ps1`: passed.
- `pytest test_s5_overview_read.py test_s5_overview_postgres.py` on private `assetops_s501rv3_test`: **36 passed,
  0 skipped** (23.6 s).
- Adjacent, `-n 2 --dist loadfile`: `test_s4_schedule_health_postgres`, `test_s4_consequence_read`,
  `test_s4_evidence_consequence_work_postgres`, `test_lr01_money_eligibility_postgres`, `test_lr01_cohort_v4`,
  `test_t027_overview`, `test_s1_cutover`, `test_sites_api`, `test_health`, `test_s4_assumption_read_api`:
  **196 passed** (212 s).
- Full backend suite: not rerun. I cite the implementer's run at `05869379`: 2226 passed, JUnit 0 failed / 0 errors
  / 0 skipped, 634 s wall. No code changed after `05869379`.
- Frontend (`frontend/`, `package.json` unchanged by S5):
  - `npx.cmd tsc --noEmit`: clean.
  - `npm.cmd test`: **63 files, 1513 passed**. It ran in this environment, unlike the known sandbox failure.
  - `npm.cmd run build`: built.
  - Focused: `s5SiteWindowOverview` 28, `siteOverviewScreen` 15, `overviewDispatchAssessment` 4, all passed.
- Walkthrough guards probed as listed above.
- Probe (fakes, scratchpad): L1 confirmed.
- **Owner walkthrough reproduced.** This used a temporary `.venv` junction and a copied `var/sites/kobo-001.yaml`,
  both removed afterwards.
  - `prepare --db assetops_s501_ownerrv --work var/s501_ownerrv`: **0 failed checks in 172 s.** Results by day:
    - 10-02: `CURRENT`/`QUANTITY_UNAVAILABLE`.
    - 10-07: `FAILED`/`UPSTREAM_FAILED`.
    - 10-23: `PRICED` 0.00-15.82 USD, `P01-power`.
    - 10-24: `WITHHELD_GENERATOR_SERIES`, labelled `P02-power-late`.
    - 11-10: `UNASSESSED`/`UNKNOWN`/`UPSTREAM_UNASSESSED`.
  - Then `serve`, followed by the steps below.
    - `attest`: P02 read `UPSTREAM_STALE`, gate `PENDING_REASSESSMENT`, same Finding, no amount.
    - `tick`: P02 read `PRICED` 0.00-15.82 USD, gate `ELIGIBLE`, `P02-power-late`, with a new FindingRevision.
    - `gate --close`: P02 read `SOURCE_CLOSED`, no amount; the assessment was `CLOSED` and the exact pin was kept.
  - Live probes while closed:
    - no pin: `known_finding` null and no run ID;
    - ID-only pin: dropped as `EXACT_REVISION_REQUIRED_WHILE_SOURCE_CLOSED`;
    - P01's exact pin on the P02 day: dropped as `NOT_IN_SELECTED_DAY`.

    This confirms the M1/M2 fixes on real stores.
  - `drop` removed the database and folder. The API process was stopped, and ports 8925-8927/5425 were free
    afterwards.
- Private `assetops_s501rv3_test` dropped. No review database remains.

## Not verified

- `tools/s5-overview-evidence.mjs` and `tools/layout-evidence.mjs`: not rerun by me. I reproduced the walkthrough
  API states, but I did not drive a browser. So the 390/1440 no-overflow
  claims rest on the committed claim JSON. Screenshots are local to the implementer and were not seen.
- The owner's visual acceptance, which is pending by design.

## Residual risk not already in the packet

- The pin lives in the URL indefinitely. A stale bookmark whose Finding later becomes unreadable or foreign gives a
  404 `FINDING_PIN_NOT_FOUND` for the whole Overview instead of a dropped pin. A day change clears it, but a reload
  does not. Low; consider a typed `previous_pin` instead of a 404 in a later slice.
- `stop-schedule` ages every Site head in the private database. That is harmless for this single-Site walkthrough,
  but it should not be copied into a multi-Site tool.
