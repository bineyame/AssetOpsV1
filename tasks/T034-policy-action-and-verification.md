# T034 - Policy action followed by evidence-based verification

Status: planned
USER_REVIEW_REQUIRED: true

Map: H; demo point 3 (strong product demo) with T034A - Finding -> action ->
verification.
Depends on: T028-T029 and T029A immutable interventions.
Delivery order: after T029A; next T034A. Placed ahead of the breadth slices by
`D-2026-10-02-demo-led-recommendation` (earlier
`D-2026-09-24-queue-resequenced-for-demo`).
Branch: task/T034-policy-action-and-verification
Sizing: configuration/action write path and verification semantics
(220-line ceiling).
Planner: Claude under the Codex-reset exception (`.ai/ROLE_CONFIG.md`).
Amended 2026-10-02 under `D-2026-10-02-demo-led-recommendation`
(`.ai/ARCHITECT_DEMO_RECOMMENDATION.md` 6.2 "T034", 2.1, 2.4, section 3
"Action / Verification", 5.1-5.2).

## Outcome

From a dispatch Finding's Recommendation tab, Accept a configuration/policy
change; that creates an **Action**, a root object. Inspect its frozen world
input, simulate the later operating window and ingest the new evidence.
Action > Verification reports Verified, Ineffective or Inconclusive from the
target and guardrails together, with later reopening when warranted.

Completing the Action alone leaves the Finding unresolved: "Completed" and
"Verified" are visibly different words, which is the CMMS contrast the demo
makes.

This closes the shortest honest product story AssetOps has: detect, explain,
monetize, intervene, verify. It does not need fuel reconciliation, productive-use
opportunity or battery lifecycle to be worth showing.

## Read for detail

- v4 sections 5.2, 13 and 15.
- Roadmap sections 3.7, 7/H and 4.
- Recommendation section 3 "Action / Verification" (hierarchy, wording,
  composition with Foundation > Changes) and 5.1 (the "two weeks later" seed).
- tasks/T029A-immutable-intervention-artifacts.md for the artifact mechanism.
- `D-2026-10-02-rendered-tabs-per-capability`,
  `D-2026-10-02-presentation-profile-and-capability-declaration`,
  `D-2026-10-02-demo-point-seed-rule`.
- Shared checks and exclusions: tasks/README.md.

## Deliver

Reuse T029A's immutable artifact mechanism for the time-valid policy/
configuration change, extending it with the accepted-action record: accepted
action, actor, target component/Site control, before/after values, effective
time and provenance.
Create a narrow Action linked to the originating Finding. The Action carries a
category (policy/configuration now) so physical maintenance can join later;
Incidents and Maintenance are deferred (recommendation 6.5).

Define the verification target, comparable windows and guardrails before
judging the result. Use accepted post-action evidence, not simulator event
success or the Action's completion status.

Screens (rendered sets per `D-2026-10-02-rendered-tabs-per-capability`):

- **Finding:** `Overview | Evidence | Alternatives | Recommendation | History`.
  Recommendation shows the change and its declared success criterion and
  leads to Accept; History shows assessment revisions, verification and
  reopening. The Findings index gains an **"Awaiting verification"** lens.
- **Action** root: `Overview | Verification` only (Plan, Execution, Evidence,
  History render when they have content). Overview is the managed-object
  header: owner, due, state, source Finding, success criterion. Verification
  follows section 3's hierarchy: target and guardrails shown together, before
  window against post-action window with comparability limits, outcome with
  reasons, what happened to the Finding.
- **Actions** enters the rail under a WORK header with its global index.
- **Site > Work** renders the site's Actions index with **no subtab row** (a
  scoped index: filter, no KPI strip; a row click changes root).
- **Foundation > Changes** renders: the accepted change as the record of the
  product decision (what was altered, by whom, effective when), linking to the
  post-action configuration evidence (AC4) rather than standing in for it.
  This lifts the "absent in every state" ban: change
  `$forbiddenSubtab = "Changes"` in `tools/checks/navigation-truthfulness.ps1`
  and the "Why Changes is not here" note in
  `frontend/src/sites/FoundationSubtabs.tsx`, citing
  `D-2026-10-02-rendered-tabs-per-capability` (the 2026-09-17 entry already
  said Changes waits for a reviewed configuration-change capability; this is
  it). Foundation renders `Definition | Topology | Controls | Changes`.
- **Rendered at the end of T034.** Rail: OPERATE: Sites; INTELLIGENCE:
  Findings; WORK: Actions. Site tabs, seven: `Overview | Foundation |
  Performance | Findings | Work | Financials | Evidence`.

## Acceptance criteria

1. Accepting a change persists an inspectable configuration/action record and
   immutable world-change artifact. Editing the proposal creates a new version;
   frozen content and prior accepted state remain reconstructible.
2. Resolve baseline and post-change policy by effective time. Earlier Site
   evidence retains its original configuration basis.
3. Run setup freezes the intervention's materialized content and ordered history;
   missing or altered content fails honestly.
4. Simulated application changes controller/world behavior at the declared time
   and publishes observations/configuration evidence through the normal path.
5. Use a later post-action Site window in ordinary accepted history for
   operational verification. A same-window simulated comparison is not
   post-action evidence and cannot be relabelled as one.
6. Verification declares target runtime/fuel metric, improvement criterion,
   comparable-window rule, coverage requirement and guardrail thresholds before
   evaluating the new evidence. Version these rules with the assessment. The
   rule set is backend-owned and joins the analytic capability declaration
   (T028); the presentation profile only presents it.
7. The guardrail set for this first verification story is battery reserve
   discipline, critical-load service and unserved energy over the window,
   computed from accepted meter, SOC and policy evidence with explicit coverage.
   Battery stress is deliberately not a guardrail here; T033 adds it to this
   same versioned rule set later. T035 extends the critical-service and
   unserved-energy metric into its ServiceWindow assessment rather than
   introducing a second basis.
8. Comparability accounts for relevant load/irradiance/capability and duration
   differences. Missing or incompatible context yields Inconclusive with reasons.
9. Verified requires the declared target and guardrails to pass with sufficient
   evidence; a target improvement with unacceptable guardrail trade-off is not
   Verified.
10. Adequately observed failure of the target/guardrails yields Ineffective with
    a reason; insufficient evidence yields Inconclusive rather than assumed
    success or failure.
11. Recording work completion without accepted post-action evidence cannot
    resolve the Finding or imply verification. The UI shows "Completed" and
    "Verified" as distinct words and states; neither is shown for the other.
12. Preserve each verification attempt's windows, evidence references, rule
    version, outcome and Action/Finding linkage.
13. Later qualifying evidence can reopen the Finding under an explicit
    recurrence/guardrail rule; the prior Verified result remains in history.
14. Display target and guardrail outcomes together, with coverage, comparability
    limits and links to underlying evidence.
15. Operational verification carries a distinct claim label from any simulated
    comparison, and the simulated provenance of the post-action Site history
    stays visible. T032 must not relabel its comparison contexts as
    post-action observations.
16. Repeated evaluation of the same evidence/rules does not duplicate actions,
    histories or financial improvement. Any consequence uses D's separate bases.
17. API and UI enforce eligible state transitions; retry/reload preserves the
    accepted action and verification record without applying the change twice.
18. The screens above render as listed: Finding Recommendation and History,
    the "Awaiting verification" lens, the Action root with `Overview |
    Verification`, Actions under WORK, Site > Work with no subtab row,
    Foundation > Changes linking to post-action configuration evidence. Site
    tabs render seven; nothing is labelled in place; the navigation check
    passes with the Changes ban lifted.
19. **Point-3 seed.** Extending T029's Kobo seed: the accepted Action (effective
    before the later window), its frozen intervention, and Kobo's post-action
    window ("two weeks later") already in accepted history through normal
    ingestion, so verification in the demo needs no Lab detour. Same seed-rule
    properties as T029's: idempotent, verified with the Lab gate off,
    rehearsed by walking the journey below. Document the seed command in the
    review packet.

## Proof

| Case | Required outcome |
| --- | --- |
| Mark work completed, no later evidence | Finding unresolved; "Completed", not "Verified"; verification unavailable |
| Target improves, all guardrails pass | Verified with supporting references |
| Target unchanged despite adequate coverage | Ineffective |
| Runtime falls, critical service deteriorates | Not Verified; failed guardrail visible |
| Runtime falls, reserve breached | Not Verified; failed guardrail visible |
| Missing capability or meter coverage | Inconclusive where required |
| Materially different comparison conditions | Inconclusive/comparability limitation |
| Later recurrence after Verified | Reopened with preserved history |
| Retry accepted action/re-evaluate | No duplicated application or history |
| Seed run twice | No duplicated site, records, Action or verification |

Use a healthy post-change case, an ineffective change and a degraded-evidence
case, all generated by world causes and normal ingestion.
Inspect each relevant pre/post run independently in the reloadable Lab
cockpit. Operational verification still compares accepted Site windows; no
private chart is verification evidence and no paired-run Lab UI is required.
Run simulator/host, configuration/action, verification and UI tests,
shared checks and `node tools/layout-evidence.mjs` for the full
Finding-to-verification path, including the WORK rail group and Site > Work.

*UI check:* recommendation 5.2 row 3 from Kobo onward, on the seed with the
Lab gate off: Kobo -> Finding -> money -> Recommendation -> Action ->
Foundation > Changes -> Action > Verification (Verified, target and guardrails
together) -> the Finding's History.

## Scope limits

No generalized CMMS, work scheduling, approval hierarchy or maintenance catalog.
Implement the one policy/configuration intervention needed for the dispatch
story; preserve the category seam for later physical maintenance.
No Incidents or Maintenance rail items or Work subtabs.
Battery stress guardrails, paired comparison and fuel reconciliation are not
prerequisites and must not be pulled in here.
Portfolio and the other demo sites belong to T034A.
Verification does not claim field-proven causal impact from a synthetic demo.

## Review

The owner completes an action without evidence, then compares the three
verification outcomes and a reopened case.
The Reviewer checks that no work-item transition bypasses evidence.

This is a demo checkpoint as well as a review: the owner judges whether the
detect -> explain -> monetize -> intervene -> verify path is showable to a
prospect as it stands, and what the answer implies for T030-T033 ordering.
Review outcome: pending.
