# Review: Demo-Led Replan (`plan/demo-led-replan`, `446906e..58d756b`)

Reviewer: a fresh Claude `assetops-reviewer` instance, working under the
Codex-reset exception in `.ai/ROLE_CONFIG.md`, which binds the Reviewer to
Claude until 2026-10-03 21:23. Codex may review this retrospectively. I did not
author the plan, the guide or the recommendation.

Reviewed against, in authority order:

1. The three owner files.
2. `.ai/ARCHITECT_DEMO_RECOMMENDATION.md` at `57ea23e`, sections 2.1-2.4, 3,
   4.3, 5 and 6-9.
3. `.agent/planner-guide-demo-led-replan-2026-10-02.md`.
4. `.agent/plan-demo-led-replan-review-packet.md`, and the Architect ruling at
   `58d756b`.
5. `.ai/WORKFLOW.md` Task Spec Size and `.ai/DECISIONS.md` practice.

## Verdict

**ACCEPT WITH FIXES.** Fix the three blocking items on the branch before the
plan merges. They are all small edits, and none of them changes a product
decision.

The plan follows the recommendation closely. It keeps owner wording verbatim
and keeps it separate from the coordinator's reading. The records follow repo
practice, and the queue matches the task files. The Planner's three
fact-checks hold up when checked against the files. However, the branch
currently fails a shared repository check. In addition, the Architect's edit
at `58d756b` left T027, the next task to be implemented, contradicting itself
and one line over its size ceiling.

## Checks I ran

| Check | Result |
| --- | --- |
| `tools/check-agent-workflow.ps1` | **FAILED**: `T025h-picker-compatibility.md uses unrecognized Status: parked` (see B1) |
| `tools/check-architecture.ps1` | Passed |
| `git diff --stat 446906e..58d756b -- frontend backend tools config simulator host Docs` | Empty. No code, config, tool or `Docs/` change, so pytest, `tsc` and the frontend suites have nothing to verify and were not run |
| Line counts (`wc -l`) | T027 **221**/220; T028 220/220; T029 149/220; T029A 99; T029B 108/120; T030 126/220; T031 102/220; T032 160/160; T033 136/220; T034 205/220; T034A 171/220; T035 131/220; T036 134/220; T025h 139/160 |
| T025h compared with `f4274f2` | Only the task file was brought in. The changes are the Status line, the position line and the pending-ruling paragraph. The quote from the recommendation is accurate |
| Code anchors named in T027, T029B and T034 | All exist (`operatorSiteTabs.tsx` `OperatorSiteLabelledTab`/`labelledAspectsSentence`, the three test files, `$forbiddenSubtab = "Changes"` at `navigation-truthfulness.ps1:249`, `SitesIndex.tsx`, `OperatorShellLayout.tsx:34`). Two exceptions: `tools/layout-evidence.mjs` has no `Operator home` scenario (N5), and `OperatorShellFrame.tsx` is not named (B2) |
| Kobo template v3 signals, for T027 phase 2's cards | `fuel-level`, `state-of-charge`, `discharge-capability`, `available-power`, generator `status`/`ac-power` and three load `active-power` signals are present, so every card has a measured metric |

`layout-evidence` does not apply, because nothing was built.

## Blocking findings

### B1. The branch turns the shared workflow check red

- **Where:** `tasks/T025h-picker-compatibility.md:3` (`Status: parked`).
- **Check:** `tools/check-agent-workflow.ps1:124` accepts only `planned`,
  `active`, `in_review`, `completed` and `blocked`.
- **Problem:** the guide (4.4) told the Planner to write `Status: parked`.
  Nobody ran the check, and the packet does not report it. Merging this means
  the T027 Implementer starts on a failing standing check.
- **Fix (task file only, since the Planner may not edit `tools/`):** set
  `Status: planned`. The position line already says "Parked under
  `D-2026-10-02-demo-led-recommendation` ... not before T029", and README row
  "-" says Parked, so nothing is lost. Then rerun the check and record the
  result in the packet. If a real `parked` state is wanted, it needs an
  Architect-approved change to the check, which is a separate decision.

### B2. T027 contradicts itself on Sites-as-landing after `58d756b`

- **Where:** `tasks/T027-commit-ingestion-and-site-overview.md:163-165` against
  `:208-209`.
- **Problem:**
  - Lines 163-165 (the Architect ruling) say that phase 1 removes `Operator
    home` and redirects `/` to `/sites`, which makes Sites the landing page in
    T027.
  - Lines 208-209 still say: "Sites as the landing page are T029B ... the
    Sites index is unchanged here."
  - The removal is not an acceptance criterion. It sits only in the
    "Rendered after each phase" paragraph, which no AC or phase assignment
    references. A cold-start Implementer cannot tell whether the redirect is
    in scope, and a Reviewer has no criterion to judge it against.
  - The anchors are also incomplete. The placeholder copy lives in
    `frontend/src/shell/OperatorShellFrame.tsx:32`, with
    `shell/__tests__/OperatorShellFrame.test.tsx:41`. The rail label
    `["Operator home", "Sites"]` is pinned in five route tests:
    `operatorRouteFrames`, `simulatorLabWorkspaceEntryPoint`,
    `siteDetailRoute`, `siteFoundationRoute` and `sitesIndexRoute`.
- **Fix:**
  - Move the ruling into AC21 (or a short AC23 assigned to phase 1), for
    example: "The rail renders Sites only, with no header; `Operator home` and
    its placeholder frame are removed; `/` redirects to `/sites`; no route
    breaks."
  - Name `OperatorShellFrame.tsx` and the route tests as anchors.
  - Reword lines 208-209 to: "Sites columns are T029B; the Sites index content
    is unchanged here (only `/` now redirects to it)."

### B3. T027 is over its 220-line ceiling

- **Where:** `tasks/T027-commit-ingestion-and-site-overview.md`, 221 lines.
- **Problem:** `.ai/WORKFLOW.md` Task Spec Size sets 220 as a ceiling ("Over a
  ceiling, split the slice or move the reasoning"). `58d756b` added the line.
  Lines 163, 165 and 186 already run to 96-108 characters, so the count is
  being held down by long lines. T028 has the same pattern: it is exactly 220
  only because line 192 joins two lines into 128 characters.
- **Fix:** while fixing B2, move the "its 'No sites are configured' copy is
  false" rationale to the packet, or cite the ruling. Bring T027 to 220 or
  below at normal wrap width. If it cannot fit, move the AC18 landing
  rationale (`:134-136`) to the packet as well.

## Non-blocking findings (ranked)

### N1. T029 AC12: the effective time decides whether the live price change moves the demo Finding

- **Where:** `tasks/T029-bounded-dispatch-financials.md:96-97`, read with
  AC2 (`:71`).
- **Problem:**
  - AC2 resolves the assumption version "appropriate to the assessed period".
  - The seeded windows are historical. An edit with effective time "now"
    therefore leaves the demo Finding's money unchanged, so the UI check
    (`:129-132`) and the point-2 demo moment fail without anything looking
    broken.
  - The Planner's addition (the form states the effective time and which
    windows it reprices) makes the effect visible. It does not say whether an
    effective time earlier than the edit is allowed, or what the default is.
- **Fix:** add one sentence. The edit's effective time defaults to the start
  of the BusinessContext version it supersedes, or to the assessed window. It
  may be earlier than the edit and is stored with its recorded time, so the
  prior pair stays inspectable (AC6). The UI check then edits with a time
  that covers the seeded prolonged-runtime window.
- **Judgement:** this is an ambiguity in a good addition, not a product
  change.

### N2. T034 AC19: the seed carries the accepted Action. Two details are missing

- **Where:** `tasks/T034-policy-action-and-verification.md:148-154`, `:180-183`.
- **Judgement:**
  - The Planner's choice is correct. A post-action window cannot exist unless
    the Action was accepted before it, so recommendation 5.1's "pre-seeded"
    window implies a pre-accepted Action.
  - It does not follow that the seeded Action may be written into the store
    directly. The seed rule's "never hand-staged" covers evidence, and the
    Action is not evidence.
  - The UI check walks "Recommendation -> Action" but does not say what
    Recommendation shows when its change is already accepted.
- **Fix:**
  - State that the seed creates the Action through the same Accept API as a
    live accept.
  - State that the Recommendation tab of an accepted Finding shows the
    accepted state, links to its Action and offers no second Accept.

### N3. T029B's interim ranking and "Top issue" are under-defined

- **Where:** `tasks/T029B-sites-ranking-and-landing.md:74-78`.
- **Problem:**
  - AC5 puts a site with an open Finding first, then lower coverage. Among
    sites with open Findings, the least-evidenced Finding therefore ranks
    first. That is a priority claim, and T034A AC4 later forbids arbitrary
    ranking.
  - AC4's "highest-priority open Finding" within a site has no rule, and
    dispatch can emit several candidate intervals.
- **Fix:**
  - Define the within-site top issue (for example: Candidate avoidable before
    Indeterminate, then latest window).
  - Say the tie-break is "attention to evidence gaps", or order open-Finding
    sites by claim level before coverage.
- **Judgement:** acceptable as an interim rule once it is stated, because
  T034A replaces it.

### N4. T031 does not take up T034A's opportunity weighting

- **Where:** `tasks/T034A-portfolio-lite.md:96-98` against
  `tasks/T031-renewable-headroom-opportunity.md` AC12.
- **Problem:**
  - T034A AC4 says opportunity "carries no weight until a backend opportunity
    capability exists (T031)".
  - T031 AC12 renders the opportunity lens but does not version the priority
    rule to weight opportunity. Nothing owns that change.
- **Fix:** add to T031 AC12 that "the priority rule gains a new version
  weighting opportunity, shown on the page". If the intent is no weighting
  before T036, say that instead.

### N5. T029B is stale after the Architect ruling

- **Where:** `tasks/T029B-sites-ranking-and-landing.md:21-22`, `:31-33`, `:54-57`.
- **Problem:**
  - The Outcome still says T029B retires `Operator home`.
  - The ownership test lists "a first screen that is a real destination
    rather than a placeholder" as what would be lost. T027 now delivers that.
  - The Deliver bullet asks for a check of an `Operator home` scenario in
    `tools/layout-evidence.mjs`, which does not exist.
  - The same staleness appears in README row 22 ("Sites as landing") and in
    packet section 10 ("subject to open question 1", which is now answered).
- **Fix:** reword T029B so that its value is the four columns and the
  ranking, with the landing inherited from T027. Drop the layout-evidence
  remnant check. Update the README row and the packet.

### N6. The README seed sentence contradicts point 1

- **Where:** `tasks/README.md:135`.
- **Problem:** "Every point ships an idempotent, rehearsed seed", but the
  table above it says point 1 is a live run with no seed.
- **Fix:** change it to "Every point from 2 onward ...".

### N7. The seed-rule decision presents an Architect reading as the recommendation's

- **Where:** `.ai/DECISIONS.md`, `D-2026-10-02-demo-point-seed-rule`.
- **Problem:** the entry is "from the approved recommendation 5.2", but two
  parts of it are not in 5.2:
  - "Breadth slices T030, T031/T032, T033 and T035 each own the recipe and
    seed of their own site" is the Architect's reading in guide 5. The packet
    labels it as such; the decision does not.
  - "Data enters through normal ingestion, never hand-staged" is Planner
    wording.
- **Fix:** add "(Architect reading, planner guide section 5)" to the
  breadth-slice sentence. This matters because the decision's authority
  ranks above the task files.

### N8. Long joined lines keep files under their ceilings

- **Where:** T028:192 (128 characters), T029B:83 (113), T034:160 (118),
  T036:34 (116).
- **Problem:** nothing is over a ceiling except T027 (B3), but the files
  sitting at their ceiling (T028 and T032) have no headroom for review fixes.
- **Fix:** reflow the lines. If that breaks a ceiling, move reasoning into the
  decisions, as `.ai/WORKFLOW.md` says.

## Fidelity, records, queue: what I checked and found sound

- **Owner wording:**
  - "review looks fine." is verbatim.
  - The D1-D8 table and the owner's summary match recommendation 8.1
    character for character, including "D3 Kobo detect→verify".
  - The tab rule matches 2.4.
  - The 4.3 boundary quotes and the 6.3 priority-intent quote are verbatim.
  - The section 9 outcomes are explicitly labelled "the coordinator's reading,
    not the owner's words".
- **Sections 6.0-6.5 and 7 carried:**
  - Every keep, rescope, move, new and defer item has a home.
  - Point-2 protection moved only the two candidates the recommendation names
    (the Sites columns and Sites-as-landing). The Planner proposed, but did
    not move, two further candidates, with ownership-test reasoning.
  - T036 also moved AC7 (Meki's benchmark) along with Meki's recipe. Guide 5
    invited this, and it follows the recipe.
  - Nothing changes a product decision.
- **Records:**
  - The five entries use the `Decision: \`D-...\`` form and are appended in
    date order, with index rows at the top.
  - The "Amended by" pointers sit in the index rows and at the end of the
    correct entry bodies: canonical-fidelity at `DECISIONS.md:632-696` and
    foundation-screen-architecture at `:985-1060`. This follows the
    `D-2026-09-21-scenario-execution-contract` precedent. Neither entry is
    rewritten.
  - The `ARCHITECTURE.md` edits are minimal and match the decisions.
- **Routing:** START_HERE, ACTIVE_CONTEXT, PLANNING_GUIDANCE ("Live now") and
  PRODUCT all point to T027 phase 1 with T025h parked. The cold-chain
  deferral is untouched.
- **Queue:**
  - The order in `tasks/README.md` matches every task's `Delivery order`:
    T027 -> T028 -> T029 -> T029B -> T029A -> T034 -> T034A -> T031 -> T032 ->
    T030 -> T035 -> T033 -> T025i -> T036.
  - The demo-points table matches the task files.
  - Rendered rails and Site tabs agree across the files: T027 3, T028 5, T029
    6, T029B 6, T034 7, T034A 7, T031/T032/T030/T035 7, T033 8, T036 8.
  - The Changes ban is lifted only in T034.
  - "No assessment yet" is consistent across T027, T028 and T029B.
  - Evidence part A at T027 (AC20: no readiness, no ceiling) against part B
    from T028 (AC20) is consistent.
  - BusinessContext is site-scoped in T029 (AC1, AC13).
  - Site > Work has no subtab row in T034.

## The Planner's flagged items

| Item | Judgement |
| --- | --- |
| T028 phase 1 weak UI check | **Acceptable.** The Overview Dispatch card showing a candidate and no false candidate is a real browser check of the analytic. The read-model URLs open in a browser and suit what is a contract-only phase. No change needed |
| T029 effective time repricing the demo Finding | **Right addition, under-specified:** N1 |
| T034 seed including the accepted Action | **Correct and necessary**, with two gaps: N2. Owner awareness: Q1 below |
| T029B interim ranking rule | **Acceptable once tightened:** N3 |
| T032 with no capability-declaration entry | **Correct.** Recommendation 4.3's declaration is per analytic that emits a Finding type. The comparison emits none, and AC20 says so |
| T027 "Open in AssetOps" landing on Site > Evidence | **Correct.** The Overview does not exist in phase 1, and Evidence is where accepted coverage and rejections show (AC18). It is consistent with the recommendation's phase 1 |

## The Planner's check outcomes, spot-checked

- **T030 -> T031 coupling: confirmed, none.**
  - T031's ACs 1-10 name no T030 artifact. T032 depends on T031, T027, T029
    and T029A.
  - T033 and T035 cite no T030 artifact. The only T030 mention in T035 is its
    delivery order.
  - The opportunity-first order follows from this, and the two-slice cost is
    recorded in README and in T031.
- **T028 revision history: confirmed.** T028's original AC13 said only "creates
  an inspectable assessment revision". The Planner added persisted,
  inspectable history (`:97-99`) and a matching Proof row (`:188`). This
  removes any reliance on T030 AC9.
- **Degraded-evidence limited claim: plausible and consistent.** The scenario
  header confirms three things inside the prolonged-runtime world's generator
  run: a one-hour gap in battery discharge capability, a SOC publication
  delayed ten minutes, and a missing override record. These map to T028's
  Proof rows. I have not confirmed that an analytic that does not yet exist
  yields Limited. T028 phase 3's UI check is where that gets proved.
- **Portfolio-lite sizing: accepted.** At 171/220, a first cross-site read
  model with a versioned priority rule fits the analytics/semantics band. It
  passes the cold-start test: sites, template, scenario versions and
  priority inputs are all named.

## Questions for the owner

1. **Live Accept at point 3 (awareness, not blocking).** The seeded Action is
   already accepted, so the strong demo shows Recommendation -> the existing
   Action. It does not show a live Accept click; Accept is exercised in
   review. This follows from recommendation 5.1's pre-seeded "two weeks
   later" window. Confirm that this is acceptable for the demo.

The packet's other owner questions do not need the owner before merge:

- Naming the evidence-limited site can be done in T034A's packet, as T034A
  already says.
- "Bahir has no journey step" follows the recommendation.

## Residual risk not named in the packet

- T027 phase 1 now also changes the landing route. The Implementer should run
  the route tests and layout evidence on `/` as well as on Site > Evidence.
- `D-2026-10-02-rendered-tabs-per-capability` tells T027 to update
  `navigation-truthfulness.ps1` "without loosening". The Changes ban must
  survive T027 unchanged until T034. T027 AC21 does not say this explicitly.
  A Reviewer of T027 should check it.
