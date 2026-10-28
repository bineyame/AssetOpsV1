# CC-R2 questions for the Architect (Lane C)

Branch `task/CC-R2-placement`. Owner rule: no isolated design decisions. Everything else in CC-R2 is built. Each
item below is built exactly as the spec says, or left unchanged, and I stopped there.

## CC-R2-Q1 Confidence reason texts trip the product vocabulary guard (same class as CC-R1-Q1)

The spec fixes the `confidence_reasons` texts as "Supported claim" / "Unconfirmed claim" and
"Registered simulation source" (build spec CC-R2 "Confidence", Q-C19/Q-C20). The Portfolio Confidence column shows
them joined by " · " (CC-R2 "Frontend"). `claim` and `simulation` are guarded terms in
`frontend/src/test/productVocabulary.json` (D-2026-10-04). CC-R1-Q1 kept `simulated` guarded and changed the
verdict label to "test data".

- **Built:** the backend sends the spec texts verbatim (`estate/placement.py:_confidence`, `_SOURCE_TEXT`), and the
  frontend shows them. No vocabulary scan runs on the Confidence cell. The placement reason lines, group headings
  and policy text contain no guarded term.
- **Needs:** the ruled texts for the two lifecycle reasons and the `REGISTERED_SIMULATION` source reason. For
  example "Supported Finding" / "Unconfirmed Finding" and "Generated test data source" (matching "Generated test
  data"). Alternatively, a ruling that the Confidence cell is exempt. Changing them touches only the texts in
  `placement.py`, `test_cc_placement.py`, `test_cc_placement_postgres.py`, and `portfolioFixtures.ts`.

## CC-R2-Q2 The W3-03 portfolio fixture has no EV Finding row

CC-00 fact, from a tier-2 run on `assetops_cc2_test`: `build_portfolio_fixture` (cold `excursion`, EV `complete`,
KOBO-001 W1) gives three Portfolio members:

- two cold Findings, `COLD_EXCURSION` and `COLD_START_FAILURE`, both with a null `episode_end`;
- the KOBO-001 W1 row.

The EV `complete` producer selects no EV Finding. The gate "the EV row is UNPRICED_RISK /
UNPRICED_SERVICE_INTERRUPTION unless CC-00 records rank 1 or 2" therefore has no row to assert.

- **Built:** `test_cc_placement_postgres.py` pins the CC-00 fact (`ev == []`). It asserts that `lens=risks` equals
  the set of cold and EV rows, which here is the two cold rows. It pins both cold rows to ACT_NOW /
  `EPISODE_OPEN` + `NO_ACTION_RECORDED`. EV placement is covered by the pure test only
  (`test_cc_placement.py::test_rule_5_unpriced_risk`, `EV_INTERRUPTION`).
- **Needs:** one of the following.
  - (a) Accept pure-only EV coverage for CC-R2.
  - (b) Name an existing producer with a selected EV interruption Finding to assert against. One possibility is a
    W3-01 golden EV case other than `complete`; I have not checked which one selects one.

## CC-R2-Q3 Panel copy now contradicts the Confidence column

`frontend/src/estate/EstatePortfolio.tsx` has a panel-bottom line, "Priority and confidence are not assessed for
these records." It is computed from `priority !== null && confidence !== null`, and `priority` is always null. The
panel subtitle `portfolioWords.ts:PRIORITY_SUBTITLE` says "...priority and confidence appear when assessed." Every
Portfolio row now carries a confidence, so the bottom line is no longer true. The spec does not cover either text.

- **Built:** both left unchanged. `estatePortfolio.test.tsx:136` still asserts the old bottom line.
- **Needs:** the replacement wording, or a ruling to remove the line. The `<details>` "How placement works" already
  sits under the table.

## CC-R2-Q4 The tier-3 capture has no estate Portfolio claim

Build spec §0.3 says tier-3 evidence uses `tools/s602b-verification-evidence.mjs` ("estate Portfolio for case
`estate`"). Adding `estate` to the walkthrough `CASES` makes that script's generic `casesSuite` check the F01
verification page (`expect.current_state` VERIFIED). The script has no Portfolio page claim, though: group
headings, reason lines and the three placements. The `.mjs` is not in the CC-R2 file list.

- **Built:** no change to the `.mjs`.
- **Needs:** confirmation that the coordinator's tier-3 step adds the Portfolio claim to the `.mjs`, or a ruling
  that CC-R2 adds it in a follow-up commit before capture.

---

# Rulings (Architect, Claude, 2026-10-28)

Checked against `estate/placement.py`, `EstatePortfolio.tsx`, `portfolioWords.ts`, `productVocabulary.json`,
`tools/s602b-verification-evidence.mjs`, `tools/s602b_test_scoped_cases.py`, the W2/W3 EV test chains, build spec
CC-R2, Appendix C D5 and v69 `#/portfolio` (`index.html:133-135`). Every literal below is exact.

## CC-R2-Q1 ruling: change the texts; no exemption

`claim` and `simulation` stay guarded (D-2026-10-04, CC-R1-Q1 precedent). The Confidence cell gets no exemption.
The texts follow the existing customer source words (`ui/productWords.ts:220-221`, `coldAssessmentWords.ts:108`).

| Fact | Old text | Ruled text |
|---|---|---|
| lifecycle not UNCONFIRMED | Supported claim | `Supported Finding` |
| lifecycle UNCONFIRMED | Unconfirmed claim | `Unconfirmed Finding` |
| source REGISTERED_SIMULATION | Registered simulation source | `Generated test data source` |
| source AUTHORED_DEMONSTRATION | Authored demonstration source | `Prepared example data source` |
| source MIXED | Mixed sources | unchanged |
| source UNKNOWN or null | Source not resolved | unchanged |
| WITHHELD | Cost basis withheld | unchanged |
| site coverage | Site coverage incomplete; other Findings may be missing | unchanged |

`AUTHORED_DEMONSTRATION` is not guarded. It changes so that the two source words read as a pair, matching
"Prepared example data". The enum codes and the confidence words ("Supported, coherent source" / "Limited" /
"Unknown") are unchanged. The Appendix C D5 example `confidence_reasons` reads with these texts.

Code:
- Update the texts in `placement.py` (`_confidence` and `_SOURCE_TEXT`), `test_cc_placement.py`,
  `test_cc_placement_postgres.py`, `portfolioFixtures.ts` and `estatePortfolio.test.tsx:132`.
- New test in `estatePortfolio.test.tsx`: render a Portfolio whose rows carry every confidence text and every
  reason text, then assert `forbiddenPhrases(priorityPanel.textContent)` is `[]` (from
  `src/test/productVocabulary.ts`).
- New pure test in `test_cc_placement.py`: no value in `REASON_TEXT`, `GROUP_LABEL`, `_SOURCE_TEXT` or the
  lifecycle, withheld and coverage texts contains `claim`, `simulat` or `scenario` (case-insensitive).

## CC-R2-Q2 ruling: (b), using the existing EV `interrupted` chain

The fixture fact stays pinned (`ev == []`). Change the module docstring to say so, and remove "open question
CC-R2-Q2" from it.

CC-00 records that the EV `complete` case selects no Finding. W2-05b `interrupted` selects exactly one SUPPORTED
`EV_INTERRUPTION` Finding, and its session `end_at` is null (`test_w205b_ev_replay_postgres.py:132`,
`test_w206_ev_reads_postgres.py:248-262`). So CC-00 records rank 2 for an EV row (Q-C21: EV can only be open). The
spec's "unless CC-00 records rank 1 or 2" applies: the expected value is ACT_NOW, not UNPRICED_RISK.
`UNPRICED_SERVICE_INTERRUPTION` stays pure-only (`test_rule_5_unpriced_risk`).

New test `test_ev_interruption_placement(ev_chain)` in `test_cc_placement_postgres.py`. No builder is
parameterised.
1. Build: `built = ev_chain("interrupted")`, then `built.start_release_upload()` and `run_worker(built)`, as
   `test_w206_ev_reads_postgres._settled` does. Then run `golden_tariff(built, currency="KES")` and `money(built)`,
   and assert every outcome succeeded, as `build_portfolio_fixture` does.
2. Read: `Portfolio(built.engine, built.tenant_id).ok(...)` for the window 2026-10-06T00:00:00Z to
   2026-10-07T00:00:00Z with `limit=100`. Use the same keywords that `fx.window` passes.
3. Assert exactly one row, with these values:
   - `domain == "EV_CHARGING"` and `mechanism == "EV_INTERRUPTION"`
   - `episode_end is None` and `workflow_label == "Recommendation not accepted"`
   - `placement == ACT_NOW_OPEN`
   - `confidence == "SUPPORTED_SOURCE_COHERENT"` and
     `confidence_reasons == ["Supported Finding", "Generated test data source"]`
   - `priority is None`

   Also assert `double_count_violations(body) == []`. The same window with `lens="risks"` returns that one row.
4. **Stop** (report it; never fake it): there is no EV row, the source is not `REGISTERED_SIMULATION`, or
   `episode_end` is not null.

## CC-R2-Q3 ruling: replace both texts; the bottom line no longer depends on priority

v69 (`index.html:133,135`) reads "Findings ranked by consequence and urgency, with evidence confidence alongside."
and "Priority and confidence answer different questions." The build places Findings in groups and does not rank
them (CC-R2 Rejected: numeric priority). The column is "Placement" (CC-R2 Frontend).

- **Subtitle.** `PRIORITY_SUBTITLE` =
  `"Selected Findings across accessible Sites, grouped by where to look first, with evidence confidence alongside."`
  **MOCK DEVIATION:** the mock says "ranked by consequence and urgency". Groups are not a value ranking, as the
  policy footer says.
- **Bottom line.** New `portfolioWords.ts` literal `PRIORITY_BOTTOM_LINE` =
  `"Placement and confidence answer different questions."`. The panel-bottom `<span>` shows it when
  `rows.length > 0`. When there are no rows, omit the `<span>` and keep the "Open all Findings →" link. Delete the
  `both` computation. **MOCK DEVIATION:** the mock says "Priority", but the spec renames the column to
  "Placement".
- **Tests.** `estatePortfolio.test.tsx:137` asserts the new line. Add an assertion for the subtitle literal. Add an
  empty-rows render that asserts the panel bottom has no `<span>`. Use the existing empty Portfolio test if there
  is one; otherwise add one.

## CC-R2-Q4 ruling: CC-R2 adds the Portfolio claim in a follow-up commit, before capture

The builder adds the claim on `task/CC-R2-placement`. CC-R2's file list gains `tools/s602b-verification-evidence.mjs`
and `tools/s602b_test_scoped_cases.py`. The coordinator runs the capture.

**Producer change (`s602b_test_scoped_cases.py:estate_assertions`).** The returned dict also carries
`"rows": {"F01": "<finding_id>|<finding_revision_id>", "F03": ..., "F05": ...}`. Each value is the row's
`data-portfolio-row` key.

**Script change (`.mjs`).** Add `async function portfolioSuite(label, c)`. `casesSuite` calls it after the generic
verification claim when `c.placement` is present, which is case `estate` only. Keep the existing F01 VERIFIED claim.

`portfolioSuite` loads `${CASES_BASE}/portfolio?from=2026-10-01T00:00:00Z&to=2026-11-03T00:00:00Z` with ready
`${settled} && document.querySelector('[data-estate-root="portfolio"] [data-portfolio-row]')`. It makes these
claims:
1. **Group headings.** The `[data-placement-group]` values, in DOM order, have no repeats and follow GROUPS order.
   They include `NEEDS_INVESTIGATION`, `ACT_NOW` and `MONITOR`. Each heading's text is exactly
   `` `${GROUP_LABEL} · ${c.placement.counts[group]}` ``. When `counts` is null, the text is the label alone.
2. **Three placements.** Each row `[data-portfolio-row="<key>"]` has the expected `data-portfolio-placement`:
   MONITOR for F01, ACT_NOW for F03 and NEEDS_INVESTIGATION for F05. The nearest `[data-placement-group]` row
   before it holds the same group.
3. **Reason lines.** These check the `[data-portfolio-placement-reasons]` text.
   - F01 equals `Change verified on test data; watch for a return`.
   - F03 matches `/Returned after an earlier episode \(Finding [0-9a-f]{8}\)/` and contains
     `No accepted Action; open the recommendation`.
   - F05 contains `The latest assessment no longer confirms this Finding; check its basis`.
4. **Confidence.** Every row's `[data-portfolio-confidence]` attribute is one of the three codes, and its text is
   not empty. The text of `[data-portfolio-panel="priority"]` matches none of `/\bclaims?\b/i`, `/simulat/i` or
   `/\bscenarios?\b/i`.
5. **Bottom line and policy.** The panel-bottom `<span>` text equals the Q3 literal. The `<details>` summary "How
   placement works" is closed on load. When opened, it shows the five policy lines and the footer.
6. **Layout.** Call `noOverflow(label, "estate Portfolio")` and
   `mockScreen(label, "portfolio", "document.querySelector('.priority-panel')")`. Then call
   `comparison.push(["portfolio (priority panel)", label, mockHeadings, await headings()])`.
7. **Screenshots** at each width: `app-case-estate-portfolio-${label}` before the disclosure is opened,
   `app-case-estate-portfolio-policy-${label}` after it, and `mock-portfolio-${label}`.

**Viewports.** Use the script's existing `WIDTHS`: desktop 1440×1000 and narrow 390×900. At 390 the table scrolls
inside its own scroller, and the page never scrolls sideways. This is the same rule as the mock's 760px rule.

**How it is produced** (tier 3, §0.3; DBs per Q-C47):
1. Run `python tools/s602b_verification_walkthrough.py --db assetops_s602b_audit_cc --work var/s602b_cc prepare`.
   If a placement assertion fails, case `estate` exits before any capture.
2. Start both frontends as `serve` prints them (web 5466 and 5467). `serve` must not be running.
3. Run `python tools/s602b_verification_walkthrough.py --db assetops_s602b_audit_cc --work var/s602b_cc capture`.
   Its parts include `ASSETOPS_S602B_PART=estate`.
4. Put this evidence in the packet: `var/s602b_cc/evidence/results-estate.json` with every claim `ok`, the six PNGs
   and the `comparison.md` row. Then run `... drop`.

If Chrome is unavailable, record `layout evidence: not run`. The slice merges on review ACCEPT, and the capture runs
before the Lane C Codex batch review.

## CC-R2-Q5 The Q2 EV row has a recorded end, so the ruling's Stop condition fired

The tier-2 run was on `assetops_cc2_test` at `b9f88ed4`, on 2026-10-28. `test_ev_interruption_placement` failed.

- The source is `REGISTERED_SIMULATION`. That assertion passed.
- The Portfolio row's `episode_end` is `2026-10-06T08:16:00Z`, not null.

So the EV row in the estate read has a recorded session end. The Q2 premise ("its session `end_at` is null") does
not hold for the estate projection. That projection (`postgres_estate_read._ev_window`) takes `end_at` from the
selected `ev_session_revision`.

The ruling's Stop applies: "episode_end is not null → report; never fake". The test is unchanged, and the
expectation was not weakened.

With a recorded end and no Action, rule 2 does not fire. The row would then be UNPRICED_RISK /
`UNPRICED_SERVICE_INTERRUPTION`, which is the original spec value, but only if its consequence state is present. I
did not confirm which group the row actually got: the assertion stopped before the placement check.

**Needs:** the ruled expectation, either UNPRICED_RISK / `UNPRICED_SERVICE_INTERRUPTION` with `episode_end` not
null, or another producer. The other test in the module, the W3-03 fixture test, passed.

## CC-R2-Q6 The spec Stop fired: F05's steps stop the F01 trial from reaching VERIFIED

I ran the walkthrough `prepare` on `assetops_s602b_audit_cc*` at `b9f88ed4`, on 2026-10-28.

- The replay and the four existing cases built: target_miss, guardrail, inconclusive and withdrawn.
- Case `estate` failed. In `ev.bound_plan`, `freeze` returned **409 `VERIFICATION_FOUNDATION_NOT_COMPARABLE`**.
  The message was: "Each window must lie wholly under one covering FoundationRevision: the old one for the baseline
  and the applied change's new one for the later window, with no policy change inside either."
  - baseline 10-06 is under `542d291e…`;
  - later 11-02 is under the new `bde0174e…`.
- The diagnostic was a scratch copy of the same steps on `assetops_s602b_audit_cc_diag`, dropped afterwards. With the
  S4 F05 steps skipped, the same freeze returns **201**.

So the cause is F05's backdated `runtime` control: value 120, effective 2026-10-21, decided 10-30T15:10. It splits
the Foundation before the F01 Action is applied, so the baseline no longer lies under the revision that the applied
change replaced. This is the spec's Stop: "the F03/F05 steps stop the F01 verdict from being VERIFIED (report the
case)". F03 alone does not block it.

- **Not done:** no case file was written, `prepare` exited 1, and so capture could not run. The DBs and the work
  folder were removed with the tool's own `drop`.
- **Needs:** an Architect ruling on the MG-C stand-in's build order or steps. For example, run the F05 steps after
  the F01 VERIFIED evaluation. That changes the Foundation after the trial, so its effect on the Portfolio read and
  on the F01 placement needs checking. Alternatively, choose another UNCONFIRMED producer.

---

# Rulings on Q5 and Q6 (Architect, Claude, 2026-10-28)

Produced by the Architect (Claude) under the 2026-10-27 default binding. Checked in code at `5d0438f9` and by three
Architect probes on scratch DBs `assetops_s602b_audit_q6{a,b,c}`. The probes were built with the case tool's own
`build` steps from the worktree and read through `pinned_app` with the F2 pin. All three DBs were dropped
afterwards, and no repo file changed. Every literal below is exact.

## CC-R2-Q5 ruling: the EV row is UNPRICED_RISK / `UNPRICED_SERVICE_INTERRUPTION`; keep the `interrupted` chain

**What the row supports (verified).**
- The Q2 ruling's premise was an Architect error. `test_w205b_ev_replay_postgres.py:132` (`end_at: None`) is the
  event-derived view: no `EV_SESSION_END` event exists. The stored session revision is `OBSERVED_ABORT` with end
  `08:16` (`R12_TABLE["interrupted"]`, same file `:659`). The estate projection reads the stored revision
  (`postgres_estate_read._ev_window`, `:301-310`). So `episode_end = 2026-10-06T08:16:00Z` is the correct product
  fact: an interrupted session ends at its abort.
- Placement walk (`placement.py:_rule`):
  - Rule 1 does not fire: the source is `REGISTERED_SIMULATION` and the lifecycle is SUPPORTED.
  - Rule 2 has no signal: no recurrence, no reopen, and an end is recorded.
  - Rule 3 does not fire: "Recommendation not accepted" is not a rule-3 label.
  - Rule 4 does not fire: the EV consequence is always `UNPRICED` (`coverage.py:267`).
  - Rule 5 fires: **UNPRICED_RISK, rank 4, [`UNPRICED_SERVICE_INTERRUPTION`]**.

  This is the spec's original default (Producer 2, Q-C22). The CC-00 EV fact is rank 4.
- No other existing EV chain has a selected `EV_INTERRUPTION` Finding with a null end. `contradictory` has a null
  end but is `CONFLICTING_TERMINAL` / EXCLUDED. `complete`, `fault`, `missing-meter` and `late-record` are
  COMPLETED. The test keeps `interrupted`.
- Q-C21's "Cold/EV can only be open" is wrong for EV. It now reads: "Cold and EV rows never recur (C13); they are
  open only when no end is recorded."

**Exact changes, `backend/tests/test_cc_placement_postgres.py`.**
1. Add a new constant beside `ACT_NOW_OPEN`:
   `EV_UNPRICED = {"policy_version": "estate-placement/1", "group": "UNPRICED_RISK", "group_rank": 4, "reasons": [{"code": "UNPRICED_SERVICE_INTERRUPTION", "text": "Charging service interruption; no price basis"}]}`
2. The `test_ev_interruption_placement` docstring becomes: "CC-R2-Q2/Q5: the W2-05b `interrupted` chain selects
   one SUPPORTED `EV_INTERRUPTION` Finding. Its stored session revision records the abort at 08:16 as the end, so
   with no Action the row is UNPRICED_RISK / `UNPRICED_SERVICE_INTERRUPTION` (rank 4). Stop (never fake) when
   there is no EV row, its source is not REGISTERED_SIMULATION, or its episode end is not 2026-10-06T08:16:00Z."
3. `assert row["episode_end"] is None` becomes `assert row["episode_end"] == "2026-10-06T08:16:00Z"`.
4. Add `assert row["consequence"]["state"] == "UNPRICED"`.
5. `assert row["placement"] == ACT_NOW_OPEN and row["priority"] is None` becomes
   `assert row["placement"] == EV_UNPRICED and row["priority"] is None`.
6. Everything else is unchanged:
   - domain and mechanism, and `workflow_label`;
   - confidence: `SUPPORTED_SOURCE_COHERENT` with `["Supported Finding", "Generated test data source"]`;
   - `lens=risks` returning that one row;
   - `double_count_violations == []`.
7. The module docstring records the CC-00 EV fact as rank 4 (UNPRICED_RISK). `test_rule_5_unpriced_risk` in
   `test_cc_placement.py` stays.

**F4 recheck.** The text stays **"No end is recorded for this episode"**, with no code change. Only the
justification changes. The EV `interrupted` session has a recorded end, so `EPISODE_OPEN` never applies to it. The
text is true for every row it does apply to:
- a cold excursion with no recorded end;
- a cold start failure, which is stored as a point (`postgres_finding_store.py:672-673`).

Strike "and the EV `interrupted` session has `abort_at` with `end_at` null" from F4.

## CC-R2-Q6 ruling: case `estate` has no F01 trial; it reads the MG-C stand-in's day

**Cause confirmed.** `verification.py:162-178` requires the baseline's covering revision to be the one the applied
change moved *from*. F05's backdated `runtime` control (effective 10-21) is published before the Action. The change
(effective 11-02) therefore splits the runtime revision, not the baseline's `542d291e…`. The 409 is by design:
`test_s6_verification_evaluator_postgres.py::test_f1_baseline_under_an_unrelated_earlier_revision_is_not_comparable`
pins exactly this.

**Options tested.**
- **Drop F05's control step.** Rejected. The control is what makes the 10-21 basis Indeterminate, and so
  UNCONFIRMED (`finding_episode.py:582-592`). Without it there is no stand-in.
- **F05 after the VERIFIED evaluation (probe b).** Rejected. The freeze succeeds, eval-0001 is VERIFIED, and F05
  reaches UNCONFIRMED. The backdated control then moves the selections, and the F01 verification read becomes
  `REASSESSMENT_PENDING` (`FOUNDATION_CHANGED`; the baseline 10-06 and later 11-02 selections moved). That is the
  spec Stop "F01 no longer VERIFIED".
- **Freeze only on F03.** Not possible: F03 has no Action and no reserve trial.

**Two further spec Stops the probes exposed, in every order (probes b and c).**
- **Window coverage.**
  - `from=2026-10-03..2026-11-03` (F1) gives Site coverage `UNKNOWN`, status `UNKNOWN` and `rows: []`.
  - Mini-grid coverage is UNKNOWN when any UTC day in the window has no dispatch selection (`coverage.py:96-117`;
    W3-01 goldens `day-without-assessment-unknown` and `findings-mixed-week`). This case has readings on a few days
    only.
  - F01's day cannot be read at all. Its one-day window is `EMPTY_SCOPE`, because `site_import` is
    2026-10-07T10:00Z. Any window that holds 10-06 also holds the unassessed day 10-07.
- **Source.** Every S4-runner KOBO-001 row has source `UNKNOWN`, because the readings are bound to no registered
  run or authored publication (`source_provenance.py:24`). Rule 1 therefore places every row in NEEDS_INVESTIGATION
  / `EVIDENCE_SOURCE_UNKNOWN`. This is the spec Stop "KOBO-001 rows resolve to source UNKNOWN (report; do not fake
  provenance)".

F01 MONITOR and F03 ACT_NOW/`RECURRED` cannot be produced from this producer in any order. The coverage and source
rules are correct product behaviour. The ruling keeps what is true and fakes nothing.

**Ruled build (verified, probe c).** The steps are F01, F02, F03, F05 through its first UNCONFIRMED match, and
diesel price v1. There is no Action, plan or evaluation.
- **The 2026-10-21 one-day read:**
  - status CURRENT and exactly one row: 08:00Z–09:00Z, UNCONFIRMED, `GENERATOR_SUPPORT_CANDIDATE`, "Recommendation
    not accepted", consequence UNPRICED;
  - NEEDS_INVESTIGATION with `["EVIDENCE_SOURCE_UNKNOWN", "LIFECYCLE_UNCONFIRMED"]`;
  - confidence UNKNOWN with `["Unconfirmed Finding", "Source not resolved"]`;
  - counts NEEDS_INVESTIGATION 1 and every other group 0, no double count, `next_cursor` null.
- **The 2026-10-11 read:** two NEEDS_INVESTIGATION / `["EVIDENCE_SOURCE_UNKNOWN"]` rows, 09:30 then 08:00.
- **Pinned time (F2):** `max(h.clock.at, runner.now) + 1 min` = 2026-11-01T00:01Z.

**Exact changes, `tools/s602b_test_scoped_cases.py`.**
1. `ESTATE_PORTFOLIO = "/api/estate/portfolio?from=2026-10-21T00:00:00Z&to=2026-10-22T00:00:00Z"`. This supersedes
   F1's 31-day literal. One day is within `MAX_DAYS`.
2. `LABELS["estate"] = "Portfolio placement (CC-R2): the unconfirmed Finding on test-scoped readings; source not resolved, no Action"`.
3. `build()`, estate branch:
   - The body becomes `action_id, plan, outcome = None, None, {"outcome_id": None, "reasons": [], "outcome": None}`
     followed by `out["expect"] = None`.
   - In `out |= {...}`, `"fake"` becomes `fake if case not in ("inconclusive", "estate") else None`.
   - The `pinned` line is unchanged (F2).
   - The final print for estate is `print(f"case estate: no Action (CC-R2-Q6); {out['placement']['F05']}")`. The
     other cases keep the existing print.
4. `estate_findings`: steps and order unchanged. In the docstring, drop "before any Action or evaluation" and add
   "no Action or evaluation in this case (CC-R2-Q6)".
5. `estate_assertions`:
   - **Requests.** One request of `ESTATE_PORTFOLIO` and one of
     `"/api/estate/portfolio?from=2026-10-11T00:00:00Z&to=2026-10-12T00:00:00Z"`.
   - **Both reads.** HTTP 200, `body["status"] == "CURRENT"`, `double_count_violations == []`, no numeric
     `priority`, and `next_cursor` null.
   - **10-21 read.** Exactly one row (F05):
     - `episode_start == "2026-10-21T08:00:00Z"`, `lifecycle == "UNCONFIRMED"`;
     - `mechanism == "GENERATOR_SUPPORT_CANDIDATE"`, `workflow_label == "Recommendation not accepted"`;
     - `source_provenance.state == "UNKNOWN"`;
     - `_placed == ("NEEDS_INVESTIGATION", ["EVIDENCE_SOURCE_UNKNOWN", "LIFECYCLE_UNCONFIRMED"])`;
     - `confidence == "UNKNOWN"`, `confidence_reasons == ["Unconfirmed Finding", "Source not resolved"]`;
     - `summary.placement_counts == {"NEEDS_INVESTIGATION": 1, "ACT_NOW": 0, "COMPARE_VALUE": 0, "UNPRICED_RISK": 0, "MONITOR": 0}`.
   - **10-11 read.** Asserted only, not captured. Two rows, 09:30Z then 08:00Z, both SUPPORTED with
     `("NEEDS_INVESTIGATION", ["EVIDENCE_SOURCE_UNKNOWN"])`. This is the MG-B fact: rule 1 hides its recurrence.
   - **Removed.** The F01 and F03 checks, and the "source UNKNOWN or MIXED" failure. Source UNKNOWN is now the
     pinned fact.
   - **Return value.** `{"F05": _placed(f05), "counts": body["summary"]["placement_counts"], "rows": {"F05": key(f05)}}`.
   - **Print.** `estate: F05 ('NEEDS_INVESTIGATION', ['EVIDENCE_SOURCE_UNKNOWN', 'LIFECYCLE_UNCONFIRMED']); 10-11: 2 rows NEEDS_INVESTIGATION; no double count`.
   - **Stop.** Any mismatch exits non-zero before the case file is written. Report it.

**Exact changes, `tools/s602b_verification_walkthrough.py`.** In the serve listing loop, a case whose `action` is
null prints the following and continues, without a verification URL:
`f"  [{name}] TEST-SCOPED: {case['label']}\n    http://localhost:{web + 1}/portfolio?from=2026-10-21T00:00:00Z&to=2026-10-22T00:00:00Z"`

**Exact changes, `tools/s602b-verification-evidence.mjs` (amends Q4).**
- `casesSuite`: when `c.action == null`, skip the verification claim, its `noOverflow` and the `app-case-${name}`
  shot. Call only `portfolioSuite(label, c)`.
- `portfolioSuite` loads `${CASES_BASE}/portfolio?from=2026-10-21T00:00:00Z&to=2026-10-22T00:00:00Z`.
- Claim 1: the headings equal `[["NEEDS_INVESTIGATION", "Needs investigation first · 1"]]`.
- Claims 2–3: there is one row, `[data-portfolio-row="${c.placement.rows.F05}"]`.
  - Its placement is NEEDS_INVESTIGATION, under that heading.
  - Its reason text contains both "Evidence source is not resolved; check the source before acting" and "The latest
    assessment no longer confirms this Finding; check its basis".
- Claim 4: `data-portfolio-confidence == "UNKNOWN"`, and the text equals "Unconfirmed Finding · Source not
  resolved". The vocabulary and `[A-Z]+_[A-Z_]+` checks are unchanged.
- Claims 5–7 are unchanged: the bottom line, the policy disclosure, the layout and the six PNGs.

**What this drops (owner-visible; the coordinator informs the owner).**
- CC-R2 no longer has a served page that shows KOBO-001 in MONITOR, ACT_NOW or COMPARE_VALUE.
- The case no longer shows a verified change next to the unconfirmed Finding.
- Every group rule stays proven at tier 2: the pure rules; the W3-03 fixture (cold ACT_NOW, KOBO COMPARE_VALUE); the
  EV test (UNPRICED_RISK).
- A served multi-group Portfolio needs two things: mini-grid readings bound to a registered run, and every UTC day in
  the window assessed. No existing producer does this, so it goes to the story-bootstrap demo sprint before the
  walkthrough. Building it in CC-R2 would be a new producer design.
- Owner Q11 holds: the stand-in appears, as NEEDS_INVESTIGATION / `LIFECYCLE_UNCONFIRMED`.
