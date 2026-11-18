# W4-03 final independent review

Branch `task/W4-03-mini-decisions-work`, head `f06e9bab`, base `main` `11517cf4` (the merge-base equals main's head).
Reviewer: a fresh Claude reviewer that did not author the slice. Nothing in `AssetOpsV1-review5` was modified.

## Verdict: REVISE

The backend is sound. Migration `0030` is correct, the data is honest, and the guards pass. Three user-visible
mismatches against the mock block acceptance (H1 to H3). Each is a small markup or CSS fix, but each needs a recapture
with a computed-style or presence check. The Medium items need fixes on the branch, or Architect rulings recorded in the
spec and packet.

## High

**H1. The Opportunity status chip always renders grey.**
- Where: `frontend/src/sites/MiniOpportunity.tsx:138` renders
  `<Badge tone="neutral" className="mini-opportunity-tone--{tone}">`. The rule in `w4-mini-decisions.css:169-187` has
  the same specificity as `.badge--neutral`. `primitives.css` loads after `App` (`main.tsx:5,10`), so neutral wins.
- Seen in `opportunity-supported-current-1440-app.png`: the `Opportunity` chip is grey. The mock chip is green, and
  closure 1's chip tones are green, amber, blue and grey.
- The capture check passed only because it reads the `data-opportunity-chip` attribute, not the rendered colour
  (`tools/w403-mini-decisions-evidence.mjs:165,257`).
- Fix: use a compound selector (`.badge.mini-opportunity-tone--green`, the pattern in `w2-cold-assessment.css:160`).
  Then make the capture assert the computed background for the positive, stale and historical states.

**H2. The Bounded opportunity headline has lost its prominence.**
- Where: `MiniOpportunity.tsx:203` uses `className="big-claim"`, which no stylesheet defines. The shared primitive is
  `BigClaim` / `.v69-big-claim` (`primitives.css:5140`).
- Seen in the 1440 capture: the claim renders at body size. In the mock it is the large headline sentence.
- Fix: use `BigClaim`, then re-measure the panel against its PR-12 cap.

**H3. Alternatives has no `Open site` header action.**
- Where: the `CanonicalMiniFinding` `PageHeader` in `SiteAnalyticsFrames.tsx` (about l.832) passes no `actions`.
- The spec ledger requires it (build-spec l.186: "`Open site` resolves authorized Site Overview"). The v69
  `alternatives` mock shows the button, and `alternatives-db-time-1440-app.png` has none. No ruling waives it.
- Fix: add the same `Open site` action the Opportunity frame uses. Add a structure test and a capture check.

## Medium

**M1. The Alternatives capture at DB time shows a 404, which is not a ruled state, and the packet reports it as MET.**
- `alternatives-db-time-*.png` shows "This decision was not found at this site." on a Finding that just loaded.
  `replay.json` `positive.alternatives` is `404 DECISION_NOT_FOUND`. The cause is in `alternatives.py:240-241`: the
  future-dated F02 root or revision is filtered out at `known`.
- PR-12.4 (spec l.859) requires the honest successful-empty state or an exact-basis-refusal page.
- The packet's criterion 2 claims "MET for read, empty and 503 states", but no empty state was captured, and `unproved`
  does not record this.
- Fix: either return the ruled 409 basis refusal or empty envelope for a Finding that the W1 read resolves, or get an
  Architect ruling that accepts the 404 with Finding-appropriate copy. In both cases, correct the packet.

**M2. The Alternatives GET never applies the Performance gate.**
- Where: `mini_decisions_api.py:193-208`.
- S10 (spec l.476) gates canonical Alternatives "when its underlying Finding read uses that gate". The W1 Finding read
  does: `finding_api.py:116` returns 409 `PERFORMANCE_CUTOVER_CLOSED` when `revision_id` is omitted.
- Impact: a cutover-closed Site gets a CURRENT Alternatives envelope. The UI always pins `revision_id`, so this is an
  API exposure.
- Fix: call `physical()` when `revision_id` is absent, mirroring W1's audit exception. Add tests for the closed gate
  and the refusal order.

**M3. Alternative `reason` and `correction_reason` are capped at 500 characters, against the ruled 2000.**
- Where: `0030` (CHECKs near l.86 and l.122), `alternatives.py:75`, `scenarios.py:136`.
- Closure 1 (spec l.248) rules "explanation/narrative/reason 1-2000". u1 did not rule unit 1 reading 1 for these two
  fields, and u3 rules 1-500 only for `missing_evidence_reason`.
- Impact: a valid reason of 501 to 2000 characters gets a 422 or a DB rejection.
- Fix: widen the CHECK and the parser to 2000 inside the unmerged `0030`, or obtain a ruling.

**M4. The stage-level test that u4b requires is missing.**
- u4b item 4 (spec l.675-690) requires a `stages.opportunity` run over one PENDING, one LEASED and one FAILED job plus
  another Site's job. It must assert `deferred=2` and the `failed` count.
- What exists: `test_w403_opportunity_stage.py` uses only a fake runner, and `test_w403_opportunity_job_isolation_postgres.py:79-94`
  feeds counts directly into `record_opportunity`. Nothing tests the scoping of `live_opportunity_jobs` through the stage.
- Fix: add the test.

**M5. The scenario-link Work context is not captured, and the gap is not recorded.**
- Spec l.843 (9b matrix) requires the linked Scenario context `{label} (Scenario detail unavailable)` in a capture.
- The fixture links only an OPPORTUNITY. The harness never checks the string, and `evidence.json` `unproved` lists
  only `alternatives-stocked`. A component test covers the copy.
- Fix: stock a scenario link and capture it, or record the state as unproved with a reason.

**M6. Alternatives shows a Site tab row that the mock lacks.**
- The canonical mini Finding shell renders `OperatorSiteTabs` (`SiteAnalyticsFrames.tsx` about l.837). The app
  therefore shows Overview/Foundation/.../Evidence above the Finding tabs, and the rail highlights Sites. The v69
  `alternatives` screen has neither.
- This is inherited from the merged W1 canonical Finding shell. u7 removed the row only for Opportunity.
- Fix: get an Architect ruling to remove the row on Alternatives, or record it as an accepted deviation. Graded Medium
  rather than High because sibling W1 tabs have rendered it since W1.

**M7. The breadcrumb's Site suffix wraps.**
- At 1440, "· site: {Site}" drops to a second line on both Alternatives and Opportunity; the mock keeps it inline.
- At 390, the Opportunity crumb shows a stray leading separator.
- Fix: make `nav.mini-finding-crumbs` an inline flex row (`w4-mini-decisions.css` about l.159). This is a minor
  visual mismatch, best fixed together with H1-H3.

## Low

- **L1.** `model.py:23,28`: the `DECISION_LINK_SCOPE_INVALID` and `INVALID_LIMIT` messages differ from the closure-1
  literals ("A cited or linked ID is outside this Site or basis." and "Choose 1 to 100 rows.").
- **L2.** `alternatives.py:121-123`: the command instant is taken before the Finding `FOR NO KEY UPDATE` lock. Two
  interleaved same-key commands can invert `created_at` order. Take the clock after the lock.
- **L3.** `scenarios.py:246-249,285` and `alternatives.py:176-179`: a second `MiniDecisionWriteRefused` after the
  single retry, and any in `correct()`, surfaces as a 500. Map it to `DECISION_STORE_UNAVAILABLE`.
- **L4.** `scenario_rules.py:216,220`: decimal multiplication uses the default 28-digit context, and authored decimal
  strings are unbounded. Bound them, or trap `Inexact`.
- **L5.** The `0030` docstring (l.14) says 48 CHECKs; there are 45 (u2b).
- **L6.** `SitePerformance.tsx:592` `useResolvedAlternativesHref` does not reject an empty `revision_id`, which u6b
  ruling 7 forbids. An empty value would yield an unpinned href.
- **L7.** `MiniScenarios.tsx:279-281` shows the raw server message for a 503 or transport failure. Alternatives and
  Opportunity use `decisionRefusalCopy`.
- **L8.** The Scenarios "Declared change" cell shows snake_case keys, and its cutoff is a raw UTC token. Both are ruled
  (u6 readings 1 and 4); queue them for the plain-language pass.
- **L9.** `test_w403_opportunity_worker_postgres.py:155` asserts only part of the reloaded missing-day `selected_hours`
  entry (u4b item 2). `test_w403_work_links_postgres.py:145-147` uses a random UUID as its "foreign scenario" rather
  than a real scenario on another Site.
- **L10.** A study that fails permanently gets a new opportunity job on every scan (`worker.py` `_changed`/`_queue`).
  Retry back-off also hides PENDING_RECOMPUTE for up to 60 s. Both follow the spec literally; raise them with the
  Architect.
- **L11 (builder readings).** None that a ruling overturned is still in force. These are not ruled:
  - unit 1 reading 1 for `reason` and `correction_reason` (M3);
  - the two u5b readings at handoff l.327 (the monkeypatched MIXED/UNKNOWN technique and the `EMPTY_CITATION_SET`
    alias);
  - a scenario correction with an unknown predecessor returns 422 `DECISION_LINK_SCOPE_INVALID` (u3 rules this only
    for Alternatives);
  - the retry-once-on-IntegrityError race handling.

  None except M3 is user-visible.
- **L12 (packet).**
  - The PR-1 heading in `W4-03-pending-rulings.md` is not marked RESOLVED, but the packet says all thirteen are.
  - "u9c reading 2/3" should be u9b readings 2/3.
  - The packet's reading list omits:
    - unit 4: cited-ID subset and deferred count;
    - unit 5: reading 9;
    - u5b: `EMPTY_CITATION_SET`;
    - 6b: readings 10-14;
    - u6b: domain-unavailable copy and First page;
    - unit 7: readings 9-12;
    - the PR-2, PR-4 and PR-5 readings.
  - It does not mark the overturned readings: 6b readings 3, 6 and 9; unit 7 readings 1 and 10.
  - Criterion 2 overstates the empty state (M1).

## Areas checked and clean

- **Migration `0030`:**
  - `down_revision` is `0029_w4_mini_depth`; there is no other `0030`, and main has a single head.
  - I counted 45 CHECKs, name for name against u2b. There are 22 UNIQUEs, 20 FKs and 5 indexes, and each of the 10
    tables has an append-only trigger.
  - The stage CHECK admits OPPORTUNITY, and the three counters are `NOT NULL DEFAULT 0`.
  - The downgrade locks before it counts, refuses in order (history, job, active stage), then fully restores 0029.
- **Shared Site lease 480 to 600 s:**
  - Ruled in u4b (120+120+120+120+60+60), and derived in `TickLimits`.
  - `__post_init__` validates the 120 s stage against the 300 s job lease.
  - No W2 or W4-01 test relied on 480. The W4-02 tests were updated, not weakened.
- **Opportunity:**
  - Producer hash, single-transaction projection, A-B-A reselection, a new revision on late evidence, and the
    currentness precedence (u5/u5b).
  - Gross sales is gated.
  - The W1 fences exclude `mini_opportunity` (closure 4 B3), with a test.
- **Work links:**
  - Refusal order matches u8 item 4.
  - Contexts honour the `known_at` cutoff and use public Site codes.
  - No W4-01 ID or count changes.
- **Layering:** `mini_decisions` imports only ports, and its composition imports are lazy. The router has no SQLAlchemy.
- **Frontend data honesty:**
  - No mock values (F-104/F-109/3-of-5/$0.25) are invented.
  - Gaps follow the u6-u8 copy, including the ruled "Unavailable in this read" basis rows.
- **Shared-file edits:**
  - `panelStructure.ts` admits only `[data-analysis-helper]` (u7), and `settled.ts` adds only loading phrases.
  - The W1 stubs match u7, and one loaded-link assertion moved to `miniDecisions.test.tsx`.
  - The navigation multiset equals the closure 5 literal, and the rail fixtures carry Analysis negatives.
  - The registry and ledger changes are additive.
- **Hygiene:**
  - No `node_modules`, `dist`, `tsbuildinfo`, `nul`, PNG, log or `var/` files are committed. The untracked
    `frontend/tsconfig.tsbuildinfo` in review5 is not committed.
  - The branch touches no `tasks/`, `.ai/` or `AGENTS.md` files.
  - All 68 commits are on Lane A, which owns the shared router, shell, guard, registry and navigation files.
- **Captures:** `evidence.json` has 359 checks, 0 failing, and 1 unproved (`alternatives-stocked`). The required
  scenario-context check is absent (M5), and some passes miss the defects above (H1, H2, M1).

## Checks run by this reviewer

All of these ran on a private worktree of `f06e9bab` (since removed) with a private DB `assetops_w403rv_test` (since
dropped).

| Check | Result |
|---|---|
| `tools/check-architecture.ps1` | **Passed**, with `ASSETOPS_GUARD_PYTHON` set to the repo venv. The first attempt failed only because the worktree had no `.venv`, so Rule 8's extractor was missing; it was not a code failure. |
| `tools/check-agent-workflow.ps1` | Passed. |
| `npx.cmd tsc --noEmit` | Exit 0. |
| `npm.cmd test` | **103 files / 2464 passed**, 288 s. It ran outside the usual sandbox limitation. |
| Focused backend pytest | **86 passed**, 0 failed, 1035 s. Files: `test_w403_migration_postgres`, `test_w403_scenario_rules`, `test_w403_alternative_postgres`, `test_w403_work_links_postgres`, `test_w403_opportunity_stage`, `test_w403_opportunity_result`, `test_w403_opportunity_job_isolation_postgres`, `test_w402_mini_stage`. |

Captures viewed:
- `opportunity-supported-current-1440-app.png` against `opportunity-finding-1440-mock.png`;
- `alternatives-db-time-1440-app.png` against `alternatives-1440-mock.png`;
- through a sub-review: scenarios-populated 1440/390, scenarios-refused-390, alternatives-read-503-1440,
  opportunity-late-stale-390, incidents-linked-1440, incidents-refused-overlay-390, maintenance-unlinked-1440.

## Not verified

- **Full real-Postgres backend suite:** not run by this reviewer. The coordinator's run from review5 is still in
  progress, so the same-revision proof is outstanding.
- **Production build:** not run.
- **Opportunity read and replay tests:** not rerun (`test_w403_opportunity_read/scan/worker/links`,
  `test_w403_scenarios_postgres`, `test_w403_replay_postgres`). The full suite covers them.
- **`tools/check-all.ps1`, beyond the two guards above:** not run.
- **Captures:** not regenerated.

## Residual risk

- Capture checks that read data attributes instead of computed style let H1 and H2 pass. Strengthen them in the fix
  round.
- Every recapture depends on the walkthrough's fixed fixture: two scenarios and five incidents.
