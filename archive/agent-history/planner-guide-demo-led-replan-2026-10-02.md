# Planner Guide: Demo-Led Replan (2026-10-02)

From: Architect (Claude, under the Codex-reset exception in `.ai/ROLE_CONFIG.md`;
Codex may review it retrospectively).
To: the Planner, either a fresh `assetops-planner` session or `codex exec`
with this file as its brief. See section 9.

This is the whole brief. Do not rely on any conversation that produced it.
Read it, then the files it cites, using bounded reads (the sections named, not
whole documents).

---

## 1. Authority And Inputs

**Source of direction:** `.ai/ARCHITECT_DEMO_RECOMMENDATION.md` at `57ea23e`
(the "recommendation"), approved by the owner on 2026-10-02. Planning work
relies on these sections:

| Section | What it gives you |
| --- | --- |
| 6.0 | Planner step 0: the records to write before T027 starts |
| 6.1 | Keep: T029A before T034, T026A unscheduled, T034's position, T033/T035 interchangeable |
| 6.2 | Rescope: point-2 protection, T027 and T028 phasing, T029, T034, T036 |
| 6.3 | Move: T025h parked; post-T034 breadth order and the T030 -> T031 dependency check |
| 6.4 | New: Portfolio-lite; the conditional thin follow-on |
| 6.5 | Defer: T025h, delta p95 task, L3, Replay, global Financials, Incidents/Maintenance, etc. |
| 7 | The near-term sequence (steps 0-13) |
| 8 | Owner dispositions D1-D8 (verbatim, 8.1) and how each is carried (8.2) |
| 9 | The six owner items |

Read on demand: 2.2 (ownership test), 2.3 (global vs scoped), 2.4 (tab rule,
rendered tabs by milestone, Site > Work, what "labelled in place" retirement
touches), 2.1 "Root rail by milestone" table (lines ~200-210), section 3
(page hierarchies; Evidence and Site Overview are the ones T027/T028 need),
4.3 (presentation profile and analytic capability declaration), 5.1-5.2
(journey, demo points, seed rule).

**Owner records:**

- `.agent/owner-instruction-final-recommendation-2026-10-02.md`: the owner's
  instruction that, after approval, the Architect sends the Planner a guide to
  "make necessary task sequencing or addition/ammedment so next round of
  implementation can proceed".
- `.agent/owner-approval-final-recommendation-2026-10-02.md`: the owner's
  approval, verbatim "review looks fine.", followed by the **coordinator's
  reading** (not the owner's words) that each section 9 item is taken at the
  recommended option. The owner may correct those readings.

**Verbatim rule.** Owner wording quoted in the recommendation (the D1-D8 table
and summary in 8.1, the tab rule in 2.4, the D4 priority-intent quotes in 6.3,
the Evidence A/B wording in section 3, the profile-boundary quotes in 4.3) and
the approval text "review looks fine." are copied character for character into
any record you write, typos included, inside quotation marks or a verbatim
block. Never paraphrase owner wording into a record and present it as theirs.
Keep the distinction the approval file draws: the owner said "review looks
fine."; the per-item outcomes are the coordinator's reading.

**Order of authority when files disagree:** owner records, then the
recommendation, then `.ai/DECISIONS.md` as amended in step 0, then
`.ai/ARCHITECTURE.md`, then task files and `tasks/README.md`. A task file that
contradicts the recommendation is the thing you are here to amend.

---

## 2. Branch

- Cut `plan/demo-led-replan` from `arch/demo-led-recommendation` (HEAD at the
  time of writing: this guide's commit, on top of `c9f274e`). The
  recommendation and its owner records then merge to `main` together with the
  plan.
- Do not work on `main`. Do not push or merge.
- `.agent/` is gitignored: stage files there with `git add -f`.
- Leave the untracked `Docs/` files you will see in `git status`
  (`AssetOps_MiniGrid_Technical_Walkthrough.md`, an RFQ PDF, a mermaid PNG)
  alone; they are not part of this work.

Suggested commit grouping (one commit per group, so the Reviewer can read them
separately): (1) step 0 records; (2) queue and routing; (3) task amendments and
new task files; (4) review packet.

---

## 3. Step 0 Records (Recommendation 6.0)

Write these before amending any task, because the task amendments cite them.
Follow the existing `.ai/DECISIONS.md` format: a dated `## 2026-10-02` entry
beginning `Decision: \`D-...\`.`, appended in date order, plus a row in the
"Decision Index For Agent Context" table at the top. Each entry states that
the Architect recommendation was produced by Claude under the Codex-reset
exception, and that you (name your binding) recorded it.

The IDs below are suggestions. You may merge rationale, but keep **one ID per
rule** so tasks can cite exactly the rule they rely on.

### 3.1 `D-2026-10-02-demo-led-recommendation` (the approval)

Must say:

- the owner approved `.ai/ARCHITECT_DEMO_RECOMMENDATION.md` at `57ea23e` on
  2026-10-02, quoting "review looks fine." verbatim and citing both owner files;
- the D1-D8 table and the owner's summary from 8.1, verbatim;
- the six section 9 outcomes, **as recorded in the approval file and labelled
  as the coordinator's reading that the owner may correct**:
  1. global Financials stays open; decide after T036;
  2. BusinessContext site-scoped in T029, with "shared or portfolio assumption
     sets" as the trigger to revisit global Financials;
  3. "labelled in place" is not used in operator views (narrowed, not retired
     everywhere); rendered tabs are filtered per capability, not per site;
  4. work off the point-2 journey may move to a thin follow-on after T029;
  5. opportunity-first accepted with its two-slice cost (T031 and T032 ahead
     of T030), subject to the Planner's dependency check;
  6. no cold-chain screens in the polished demo;
- that the recommendation's sequence (section 7) supersedes the queue order of
  `D-2026-09-24-queue-resequenced-for-demo` from T027 onward, and that its
  journey (5.1, "Kobo runs uninterrupted") supersedes the walk order in roadmap
  section 5 and 13.3 for demo purposes. **Do not edit
  `Docs/mini-grid-demo-architecture-and-roadmap.md`**: it is an owner source
  document. Where 6.0 says "update the roadmap's demo story (5.1) and
  demo-point table (5.2)", the Architect's intent is the queue's demo story and
  demo-point table (`tasks/README.md`, `.ai/PRODUCT.md`), with the override
  recorded here so v6.9 and roadmap text are not used as an acceptance oracle
  against it (2.2 rule).

### 3.2 `D-2026-10-02-rendered-tabs-per-capability` (amends two entries)

Must say:

- the owner's rule, verbatim: "The canonical tab set defines ownership and
  future placement; the rendered tab set contains only meaningful destinations
  unless absence itself communicates something useful.";
- it is applied per capability, not per site; once a capability exists, its tab
  renders on every applicable site and a site without the evidence shows the
  gap inside the tab; applicability (from profile and backend declaration) is a
  separate filter, never data presence (2.4);
- **"labelled in place" is not used in operator views**. The other two
  Presentation Honesty treatments (not rendered; disabled with a stated reason)
  stand unchanged. It is narrowed, not retired everywhere. [Verify] that no
  non-operator surface renders it today (the Architect found only code
  comments naming it, in `frontend/src/shell/simulatorLabRoutes.tsx` and
  `frontend/src/ui/DataTable.tsx`), and say so; those comments are updated by
  T027 phase 1, not by you;
- the rendered Site tabs by milestone (2.4 table: T027 three, T028 five, T029
  six, T034 seven, T033 eight, canonical order), Foundation renders
  `Definition | Topology | Controls`, plus `Changes` from T034, and `Readiness`
  is not rendered (claim readiness lives on Site > Evidence only);
- Site > Work renders the Actions index with no subtab row while WORK holds
  only Actions;
- **what it amends**: `D-2026-09-13-canonical-fidelity` (the "three treatments"
  rule and its application of labelled-in-place to Site tabs) and
  `D-2026-09-17-foundation-screen-architecture` (six Site tabs and Foundation >
  Readiness labelled in place). Follow the repo's amendment convention: do not
  rewrite those dated entries; add "Amended by
  `D-2026-10-02-rendered-tabs-per-capability`" to their index rows, and a
  one-line pointer at the end of each entry body (as at
  `D-2026-09-21-scenario-execution-contract`, which carries "Amended by ...").
  Name what still stands in each: content before chrome, absent versus
  disabled, parameterless routes are not destinations, the v6.9 tab vocabulary
  and canonical order as the ownership set;
- the implementation lands in T027 phase 1 (section 5 below).

### 3.3 `D-2026-10-02-grammar-ownership-test`

The ownership test for grammar exceptions (2.2): a place keeps its slot only if
it owns something no other place shows; an exception names what would be lost
and what duplicates it; every exception gets a `DECISIONS.md` entry; a task
citing v6.9 text a decision overrides cites the decision too. Also D1's carry
(8.2): the grouped root menu is target and reference, not frozen; the demo rail
is filtered to live items with headers from T028 (2.1 root-rail table).

### 3.4 `D-2026-10-02-presentation-profile-and-capability-declaration`

From 4.3: `DomainPresentationProfile` is static substrate data keyed by
`site_type` and owns presentation only (the five things listed in 4.3, owner's
boundary quoted verbatim); backend modules own Finding types, evidence
requirements, verification rules and consequence categories through the
**analytic capability declaration**, born in T028 (verification rules join at
T034); the three rendering rules (section 5, T028, below); `site_type` is
domain data, not a shell/mode discriminant; the timing rule (write the profile
when a second card or subtab appears, no hard-coded lists in shared frames).

### 3.5 `D-2026-10-02-demo-point-seed-rule`

From 5.2: each demo point ships with an idempotent, rehearsed seed, owned by the
slice that creates the point, checked with the Lab gate off. Name the owners
(section 5 below: T029, T034, Portfolio-lite, T036; breadth slices for their
own sites).

### 3.6 `.ai/ARCHITECTURE.md`

- **Presentation Honesty** (the three-treatment list, around line 360): change
  the "Labelled in place" bullet so it states the treatment is not used in
  operator views and cites `D-2026-10-02-rendered-tabs-per-capability`; add the
  per-capability tab rule in one or two sentences. Do not touch the
  not-rendered and disabled bullets, or the rest of the section.
- **Shared Presentation Substrate** (around line 326): add a note that the
  domain presentation profile is substrate data selected by `site_type`, that
  `site_type` is domain data and not the shell/mode/variant discriminant the
  section forbids, and cite 3.4's decision.

Keep both edits short; the reasoning lives in the decisions.

### 3.7 Consistency edits that follow from step 0 (not new decisions)

- `.ai/PRODUCT.md`, "Demo Readiness Milestones" and the "Four demo points"
  paragraph: the strong product demo becomes T034 plus Portfolio-lite, opening
  on Portfolio; cite 3.1. Leave the cold-chain deferral as it is (item 6).
- `.ai/PLANNING_GUIDANCE.md`, Scoped Handoffs "Live now": add
  `.ai/ARCHITECT_DEMO_RECOMMENDATION.md` as live direction for T027-T036.
- `.ai/START_HERE.md` and `.ai/ACTIVE_CONTEXT.md`: both currently say "next is
  T025h". Route next work to T027 phase 1 and say T025h is parked (3.1, 6.3).
- `.ai/FEATURE_MAP.md`: only if its unowned-requirements table names an owner
  that moves (for example the portfolio priority rule moving from T036 to
  Portfolio-lite). Change the owner cell only.

---

## 4. Queue Changes In `tasks/README.md`

### 4.1 Order table

Replace rows 19-31 with the order below. Rows 1-18 (completed) stay. Add a
paragraph at the top of "Order and observable checkpoints" citing 3.1, in the
style of the existing resequencing paragraphs.

| Order | Task | Map | Reviewable result |
| --- | --- | --- | --- |
| 19 | T027 (phase 1, phase 2) | B completion | Phase 1: Commit -> ingestion -> Site > Evidence with record drill-down; three real Site tabs. Phase 2: mini-grid Site Overview |
| 20 | T028 (phased) | C | Dispatch -> Finding -> drawer; Findings root; capability declaration; Evidence capability table (one row) |
| 21 | T029 | D | Site Financials with live editable assumptions; point-2 seed |
| 22 | thin follow-on (if created) | B/C presentation | Sites ranks by assessment and evidence; Sites as landing |
| 23 | T029A | H prerequisite | Frozen policy intervention changes a run |
| 24 | T034 | H | Recommendation -> Action -> Foundation > Changes -> Verification; point-3 seed |
| 25 | Portfolio-lite | Strong product demo | Portfolio lands, three seeded sites, ranked Findings |
| 26-30 | T031, T032, T030, T035, T033 **or** as set by the 6.3 check (4.3 below) | E/F/G/I | Each adds one site that appears on Portfolio |
| 31 | T025i | Scenario contract | Unchanged: after T026, before T036 |
| 32 | T036 (rescoped) | I completion | Six sites, conditional global Evidence, Lab reveal, rehearsal |
| - | T026A | B hardening | Unchanged: unscheduled, gates nothing |
| - | T025h | A/B hardening | **Parked**: not before T029; see 4.4 |

The relative order of the two breadth pairs (opportunity/fuel, then
service/battery) is not set by the recommendation. Keep the existing group
order (E/F before G/I) unless T028/T029 feedback says otherwise; record that
this is the default, not a decision.

Also update the prose under the table:

- the interchangeable-pair paragraph: T033 and T035 remain interchangeable as
  a pair, with the owner's priority intent "Service before battery unless
  feedback says otherwise" (quote verbatim from 6.3) as the default;
- "Every other row's position is load-bearing": still true for the spine; say
  the breadth order is priority intent set after the 6.3 check and redirectable
  by point-2 feedback;
- carry the deferred delta p95 performance task (from T025e/T026, in
  `.ai/MILESTONE_REVIEW_BACKLOG.md` "Carried from T026") as a note: run before
  the T036 rehearsal only if playback visibly stutters (6.5). No task file.

### 4.2 "Four demo points, not one" table

| Point | Task | What it is |
| --- | --- | --- |
| 1 | T027 | Internal architecture demo (live run; no seed) |
| 2 | T028 / T029 | Domain-expert and early-prospect demo: one site, one strong Finding, its evidence, its money; seed owned by T029 |
| 3 | T034 + Portfolio-lite | Strong product demo, opening on Portfolio; seeds owned by T034 (post-action window) and Portfolio-lite (three sites) |
| 4 | T036 | Full portfolio and polished client demo; seed owned by T036 |

Add the journey per point from 5.2 (one line each) and cite the seed rule (3.5).
Keep "After T028/T029, reassess T030-T036 against what the expert actually
said".

### 4.3 The 6.3 dependency check sets rows 26-30

See section 6.1. Default if the check is clean: T031, T032, T030, T035, T033.
If a costly coupling is real: T030, T031, T032, T035, T033 (recommendation:
"If a real coupling is found and costly, fuel stays first").

### 4.4 T025h (parked)

The task file exists only on branch `task/T025h-picker-compatibility` at
`f4274f2` (that branch's tip `8901c4a` adds only `.agent/` files). It is not on
`main` or on this branch. That commit also edits `tasks/README.md`,
`.ai/ACTIVE_CONTEXT.md` and `.ai/START_HERE.md` to route T025h as next; those
edits are now wrong.

Do this:

- Bring in only the task file:
  `git checkout f4274f2 -- tasks/T025h-picker-compatibility.md`. Do not merge or
  cherry-pick the commit.
- In the file, set `Status: parked`, replace its `Next: T027.` / position line
  with "Parked under `D-2026-10-02-demo-led-recommendation` (recommendation 6.3,
  6.5): not before T029, or in a Lab-ergonomics bucket with the carried delta
  p95 task. Gates nothing." Change nothing else in its scope.
- Add, under its stops or review section, that its pending ruling (does the
  picker status depend on the whole form, or only on scenario and profile?)
  waits until it is scheduled, and that the recommendation's view is "the
  whole-form reading is the honest one: a preview of Create must depend on
  everything Create reads". That ruling is the owner's or Architect's to make
  when scheduled, not yours.
- Leave the branch `task/T025h-picker-compatibility` as it is; say in the
  packet that it is superseded by this plan branch for the task file.

---

## 5. Per-Task Amendments

General rules for every file you touch:

- Follow `.ai/PLANNING_GUIDANCE.md` (From Feature Map To Tasks) and
  `.ai/WORKFLOW.md` Task Spec Size: ceilings 120 / 160 / 220 lines by slice
  type, no minimum, and the cold-start test. Over a ceiling, split the slice or
  move reasoning to the decision that owns it.
- Keep the existing header form (`Status`, `USER_REVIEW_REQUIRED`, `Map`,
  `Depends on`, `Delivery order`/`Next`, `Branch`, `Sizing`) and section order
  (`Outcome`, `Read for detail`, `Deliver`, `Acceptance criteria`, `Proof`,
  `Scope limits`, `Review`). `tasks/T027-...` and `tasks/T028-...` are the
  models.
- Update `Delivery order` / `Next` lines to the new queue.
- Every task must stay UI-verifiable: each phase or slice ends with something
  the owner can open in the browser and check.
- Cite decisions instead of restating them. Where a task cites v6.9 or roadmap
  text that a 2026-10-02 decision overrides, cite the decision too (2.2 rule).
- Each slice that changes navigation or tabs states the rendered rail and Site
  tabs it ends with (2.1 root-rail table, 2.4 tab table), and runs
  `node tools/layout-evidence.mjs`. From T028 the layout evidence covers a
  one-item rail group so the header does not look heavy (2.1).
- **Profile rendering rules apply to backend capability ids**, not to the
  profile's Overview domains. The profile owns which domain cards exist
  (Service, Dispatch, Battery, Fuel, Renewable at T027); rules 1-3 govern what
  the profile maps from backend-served ids (Performance subtabs, a card's
  assessment slot, Evidence capability rows, Finding types). This is the
  Architect's reading of 3 and 4.3, stated here so T027 phase 2's cards are
  not read as "profile ids the backend does not serve".

### T027 - Commit, ingestion, Site > Evidence, Site Overview (6.2)

**Keep every acceptance criterion; it is a protected seam.** Rescope and phase.
Default: one task file with a `Phases` section, each phase ending in committed,
UI-verifiable work and a handoff per `.ai/ROLE_CONFIG.md` "Build large slices
in phases". Split into two task files only if the spec cannot pass the
220-line ceiling or if you judge phase 1 must be independently reviewed and
merged before phase 2 starts; record which you chose and why.

Assign every AC to a phase (or to both, stating each phase's part).

- **Phase 1: Commit, ingestion, Site > Evidence (part A), tab rule.**
  - Commit/ingestion ACs (1-10, 12, 14-19 in their write-path and evidence
    parts) land here.
  - **Site > Evidence becomes a destination.** Body: source and connector
    health per source (data quality, not asset health), per-signal coverage
    for the selected window, and the mapping and configuration basis. No
    capability readiness, no claim ceiling (owner's D6; section 3 Evidence).
  - **The record inspector (AC12) is a drill-down** from source and signal
    rows, opening without changing root. It is not the tab body, so T028's
    drawer and T030 AC17's source-record inspector can extend it.
  - **Remove** the six labelled-in-place Site tabs and Foundation's Readiness
    label; filter the one inventory by capability; render Overview, Foundation,
    Evidence. Code anchors to name: `frontend/src/shell/operatorSiteTabs.tsx`
    (inventory with `kind: "labelled_in_place"` entries and
    `labelledAspectsSentence`), `frontend/src/sites/FoundationSubtabs.tsx`
    (Readiness entry), their tests
    (`frontend/src/shell/__tests__/operatorSiteTabs.test.tsx`,
    `frontend/src/sites/__tests__/foundationScreen.test.tsx`), and
    `tools/checks/navigation-truthfulness.ps1`, whose failure messages say a
    tab or subtab the build cannot open "is labelled in place, never disabled".
    The check must keep its non-loosening intent: a tab the build cannot open
    is **not rendered**, never disabled, and never labelled in place in
    operator views. Cite 3.2. This depends on step 0 being merged with the
    plan, which it is (same branch).
  - **AC10 clarification.** Current text: "Coverage names the required
    signals and selected window". Amend so "required signals" means the
    signals the Overview metrics need, not signals an analytic requires.
    [Verify] that the new wording keeps the rest of AC10 (missingness and
    quality preserved; no carry-forward as fresh measurement) intact, and that
    no other T027 sentence (including the Proof row "Missing capability/report
    -> Coverage gap, no fabricated value") implies analytic requirements.
  - **Scope-limit wording.** T027 says "No full Replay UI or broad
    source-health dashboard is required for C." Keep the deferral of a broad
    (cross-site) source-health dashboard (6.5), and say plainly that the
    site-scoped source-health section of Site > Evidence is in scope.
  - AC18's "Open in AssetOps" link targets the Site and window; in phase 1 its
    landing is Site > Evidence or the Overview frame as you judge; state which.
  - Rail at T027: Sites only, no group header (2.1).
  - *UI check:* Lab run -> Commit -> Site > Evidence shows source health,
    coverage and a record drill-down with three timestamps; Lab off, it stays.
- **Phase 2: the mini-grid Site Overview.**
  - The v6.9 8.18 frame per section 3 "Site Overview": objective strip; one
    card per domain from the profile (mini-grid: Service, Dispatch, Battery,
    Fuel, Renewable); measured metrics with coverage and a neutral **"No
    assessment yet"** on every card; the selected-day timeline (demand, PV,
    generator, SOC) as context; evidence links into the record inspector
    (AC11).
  - "Unknown" is reserved for an assessment that exists but cannot conclude, or
    no data in the window; it does not appear on T027 cards for lack of an
    analytic. Amend AC11's "Healthy reference can show no material current
    Finding without inventing an analytic result before T028" to name "No
    assessment yet" as the state.
  - The profile is born here (second card), as substrate data keyed by
    `site_type` (3.4).
  - [Verify] which measured metric each card can show from T026 evidence. A
    card with no measured metric shows "No assessment yet" and names its
    coverage gap, never a fabricated value.
  - *UI check:* the internal architecture demo, 5.2 row 1.
- **Sites columns** (Last analysed, Evidence coverage) and **Sites-as-landing**:
  point-2 protection (below). Default: move to the thin follow-on.
- No seed (point 1 is a live run).

### T028 - Dispatch Finding (6.2)

Rescope and phase. Keep ACs 1-15; they are the analytic's semantics. Suggested
phases (you set them):

1. **Analytic and declaration.** The dispatch analytic; the **analytic
   capability declaration** as a backend contract and site-scoped read model;
   the Finding; versioned assessment revision (already AC13: "Changed accepted
   evidence creates an inspectable assessment revision").
2. **Screens.** Performance > Dispatch (the only Performance subtab); Finding
   detail with `Overview | Evidence | Alternatives` (Overview hierarchy per
   section 3 "Finding Detail"); the claim drawer reusing T027's record
   inspector; **Findings** in the rail under INTELLIGENCE (headers start here)
   with its global index; Site > Findings as a scoped index (filter, no KPI
   strip, no status model of its own; a row click changes root, 2.2); the
   Dispatch Overview card showing a real assessment word and one-line reason.
   Site tabs rendered: five.
3. **Site > Evidence part B.** The capability table above source health, one
   row (dispatch): readiness Full/Limited/None, claim ceiling and missing
   evidence, scored from the declaration against accepted coverage. Nothing in
   it appears before a real claim exists. Sites columns Assessment and Top
   issue only if not moved to the follow-on.

**The capability declaration contract (new acceptance criteria).** Each
analytic declares: id and applicable site types; the Finding type it may emit;
required and optional evidence; claim levels (dispatch: Necessary, Candidate
avoidable, Indeterminate). The backend serves the evaluated, site-scoped
version as a read model. A `tools/checks` guard enforces it, copying the rigour
of the simulator model-profile pattern, **not its data**: product analytics
may not read `EXECUTION_REQUIREMENTS` in
`backend/assetops_backend/runs/profiles.py` or any private/simulator flow.
The profile maps only `id -> label / order / grouping / emphasis`, under three
rules, each needing a test:

1. A backend id the profile does not know **still renders**, with the
   backend's display name in a default position. Drift is never silent.
2. A profile id the backend does not serve **renders nothing**, and a test
   flags the orphan. (The profile will carry future ids such as Renewable or
   Fuel subtabs. Make the orphan test distinguish named, planned ids from an
   unexpected one, for example with an explicit expected-orphan list that
   shrinks as analytics land. An unexpected orphan fails.)
3. **A gap is shown only from backend state**, never from the profile.

Also:

- The carried question whether stop-60's policy change appears as a policy
  record stays with T028; keep it named in the file.
- The Finding's Recommendation and History tabs do not render at T028 (T034).
- T028's `Review` keeps the three-question expert checkpoint unchanged.
- No seed in T028; T029 owns point 2's seed.
- *UI check:* 5.2 row 2 up to the drawer.

### T029 - Bounded financials (6.2)

- **Site > Financials becomes a destination** with `Overview | Assumptions`
  subtabs (Site tabs rendered: six). Financial pages carry no assessment
  status (v6.9 8.36).
- **Assumptions are editable in the UI.** Changing the price live is the demo
  moment. An edit creates a new BusinessContext version (AC1, AC6) under
  `.ai/ARCHITECTURE.md` Configuration Persistence; prior consequence/assumption
  pairs stay inspectable. This adds a UI write path: size against the 220-line
  ceiling.
- The Finding's consequence panel and the Overview's value line read the same
  model (already AC9; keep).
- **BusinessContext is site-scoped.** Record in the file that "shared or
  portfolio assumption sets" is the trigger to revisit global Financials (2.5;
  3.1 item 2). No global Financials page or rail item.
- **Point-2 seed (new AC):** one Kobo site (Kobo template v3, which avoids
  template-version drift; 6.3), with a healthy window and a prolonged-runtime
  window committed through normal ingestion; idempotent (loading twice does
  not double-ingest or duplicate the site); checked with the Lab gate off;
  rehearsed by walking the point-2 journey (Sites -> Kobo Overview -> Dispatch
  -> Finding -> drawer -> Financials, change price). Document the seed command
  in the packet.
- AC10 and roadmap 12.1 (client-facing assumptions are the owner's decision
  before external exposure) are unchanged.
- *UI check:* the full point-2 journey on the seeded site.

### Point-2 protection rule (6.2; 3.1 item 4)

Protect the journey Sites -> Kobo Overview -> Dispatch -> Finding -> drawer ->
Financials. **Default: move the Sites assessment columns (Last analysed,
Evidence coverage, Assessment, Top issue) and Sites-as-landing out of T027 and
T028 into the thin follow-on.** These are the recommendation's named first
candidates and the owner approved the principle. Do not move anything else the
recommendation places in T027-T029 on your own judgement; if you see another
off-journey candidate, propose it in the packet with what would be lost
(2.2's ownership test), and leave it in place.

### Thin follow-on (new, conditional; 6.4)

Create it only if you moved the Sites items (the default above). Suggested id
`T029B` (README already notes letters mark where a slice was cut, not when it
runs). Placed after T029, before T029A.

- Outcome: the Sites index ranks sites by assessment and evidence (the four
  columns) and becomes the landing page, retiring the T002 `Operator home`
  placeholder (2.1). Until Portfolio-lite takes the landing.
- Normal UI/content slice (120-line ceiling). No seed of its own; uses T029's.
- *UI check:* app opens on Sites; the Kobo row shows its assessment, top issue
  and coverage, linked to the same objects.

### T029A - Immutable intervention artifacts (6.1: keep)

No content change. Update `Delivery order` to "after T029 (and T029B if
created); next T034".

### T034 - Policy action and verification (6.2)

- The Finding's Recommendation tab leads to Accept, which creates an **Action**
  root; **Actions** enters the rail under WORK.
- The Action renders `Overview | Verification` only (Plan, Execution, Evidence,
  History appear when they have content). Use "Action"; the file's
  "Action/Maintenance" wording becomes Action with the category seam for later
  maintenance kept (Incidents and Maintenance are deferred, 6.5).
- The Finding's Recommendation and History tabs render; the Findings index
  gains "Awaiting verification".
- **Foundation > Changes** renders, linking to the post-action configuration
  evidence (AC4) rather than standing in for it. This lifts the check's ban:
  `tools/checks/navigation-truthfulness.ps1` sets `$forbiddenSubtab =
  "Changes"` ("absent in every state"), and `FoundationSubtabs.tsx` documents
  why Changes is absent. Both change in T034, citing 3.2 (the 2026-09-17 entry
  already said Changes waits for "a reviewed configuration-change capability";
  T034 is that capability).
- **Site > Work** renders the Actions index with **no subtab row** (Site tabs
  rendered: seven).
- The verification rule set is versioned and backend-owned (AC6, AC7) and
  joins the capability declaration; the profile only presents it.
- "Completed" and "Verified" are visibly different words (section 3
  Action/Verification).
- **Point-3 seed (new AC):** Kobo's post-action window already in accepted
  history ("two weeks later"), so verification in the demo needs no Lab detour
  (5.1). Same seed-rule properties as T029's.
- `Delivery order`: after T029A; next Portfolio-lite. Its `Review` paragraph
  ("what the answer implies for T030-T033 ordering") stays.
- *UI check:* 5.2 row 3 from Kobo onward, on the seed.

### Portfolio-lite (new; 6.4)

Suggested id `T034A`. Directly after T034. **A real slice; size it honestly.**

- **Outcome:** a thin Portfolio becomes the landing page and enters the rail
  (OPERATE header, before Sites). It ranks Findings across sites with
  consequence and basis, with attention, opportunity and evidence-gap lenses
  where content exists, per section 3 "Portfolio Value & Operations" (scope
  sentence, ranked Findings, lenses, "What changed").
- **Pulls forward** T036 AC4 (roll-up with window, basis, coverage and
  evidence-gap context), AC5 (transparent priority rule) and AC6 (distinct
  consequence types; no invented total). [Verified by the Architect against
  `tasks/T036-portfolio-and-client-demo.md`; recheck.] Also consider T036 AC7
  (Meki's healthy benchmark is meaningful), which goes with Meki's recipe.
- **Seed: three reproducible sites**, under the seed rule:
  - Meki, healthy (T036 AC1's Meki recipe, pulled forward);
  - Kobo with post-action history (T034's seed);
  - an evidence-limited site on which T028's analytic runs and limits its
    claim, built from T026's `kobo-mini-grid-degraded-evidence` scenario
    (`config/scenarios/kobo-mini-grid-degraded-evidence.yaml`). [Check 6.3.]
- *UI check:* 5.2 row 3 from Portfolio: three sites, a ranked Finding with its
  value, a visibly evidence-limited site distinct from a healthy one.

### Breadth slices T030, T031, T032, T033, T035 (6.3; section 7 steps 9-12)

Positions per 4.3. In each file, update `Depends on` / `Delivery order` and
add:

- **Each adds its own site to the Portfolio as it lands** (section 7: "Each of
  steps 9-12 adds a site that appears on the Portfolio as it lands"). The
  Architect's reading: each breadth slice owns the reproducible recipe and seed
  for its own site (T031/T032 Desta, T030 Genda, T035 Bahir, T033 Arsi),
  pulled forward from T036 AC1, under the seed rule. If that pushes a slice
  over its ceiling, say so in the packet rather than dropping it.
- Each new analytic adds itself to the capability declaration, which gives it
  its Site > Evidence capability row, its Performance subtab where it has one,
  and its Overview card assessment (4.3; 2.4).
- T031: Performance > Renewable; Opportunities is a lens on Findings, not a new
  class (2.2). Its `Depends on: T027-T030` becomes whatever the 6.3 check
  shows; T031's AC1/AC2 already own its curtailing world.
- T032: the paired comparison is a drill-down from Renewable, not a tab.
- T030: Performance > Fuel; AC17's "separate source-record inspector" extends
  T027's record inspector (section 3 Evidence).
- T033: Site > Health renders (eighth tab, between Foundation and Performance)
  and **Assets** enters the rail after Sites (2.1, 2.4); battery stress joins
  T034's versioned rule set (already in T034 AC7).
- T035: Service and Backup views per section 3; keep the file's existing ruling
  that no incident subsystem is built.

### T036 - Portfolio and client demo (6.2)

Rescope to completing a Portfolio that already exists:

- add the remaining sites (whichever breadth slices did not seed their own);
  AC1 minus Meki (Portfolio-lite) and Kobo (T029/T034 seeds);
- AC4-AC6 move to Portfolio-lite; the financial roll-up stays Portfolio's
  value column;
- global Evidence (ASSURANCE) joins the rail **only** if it passes the
  ownership test explicitly, with its own `DECISIONS.md` entry (2.2);
- the Lab truth-versus-inference reveal (AC11, AC12, AC16) and the walkthrough;
- AC13's walk order follows the 5.1 journey (Kobo uninterrupted, breadth after,
  Lab last), citing 3.1; Genda fuel is optional in that journey;
- the delta p95 task only if the reveal's playback stutters (6.5);
- no global Financials, Incidents, Maintenance, Reports, cold-chain screens.
- Its other ACs are unchanged.

### Files you do not change

T026A (unscheduled, gates nothing), T025i (position unchanged, content
unchanged), and completed tasks.

---

## 6. Checks You Must Do, Not Assume

Record each check's evidence (file, line, quote) and outcome in the packet.

### 6.1 T030 -> T031 coupling (6.3)

Read T031, T032 and T030 in full. Confirm or refute:

- **(a) T030 AC9** (a late record revises an accepted assessment, history
  kept). Does T031 AC9 ("deterministic/versioned and avoids duplicate
  Findings") rely on revision machinery that T030 would be first to build?
  Expected no, because T028 AC13 already requires "an inspectable assessment
  revision". **Confirm T028 actually builds it**: AC13 must require persisted,
  inspectable revision history, not only rerun dedupe. If T028's wording falls
  short, put revision history explicitly into T028 phase 1 (the recommendation
  already places it there), which removes the coupling; do not reorder for it.
- **(b) T030 AC13** (Site Financials without double-counting). T031 adds no
  money; expected no coupling.
- **(c) T030 AC2** (extending T026's operational-record family). T031 uses no
  operational records; expected no coupling.
- Also confirm T032 depends on T031, T029 and T029A only, and that nothing in
  T033/T035 names a T030 artifact.

Outcomes:

- No coupling: opportunity first (T031, T032, T030). Fix T031's `Depends on`
  to the artifacts it actually consumes and record the two-slice cost.
- Coupling real but cheap (it can move into T031 or T028 within ceilings):
  opportunity first, move the piece, record it.
- Coupling real and costly: fuel stays first (the recommendation's rule).
  Record why; no owner question needed, the owner sees it at review.
- Cannot tell: stop and ask (section 7).

### 6.2 The evidence-limited Portfolio-lite site

Check from `.ai/CODE_STATE.md` (entry `T026`), `tasks/completed/T026-...` and
the scenario file that `kobo-mini-grid-degraded-evidence` removes or delays
evidence the dispatch analytic requires (T028 AC3: PV available capability,
battery capability; AC5/AC7: overrides), so T028's analytic would produce a
limited or Indeterminate claim rather than nothing. If it does not, Portfolio-
lite authors its own evidence-limited recipe through the normal path (size it
in). If that would need a new simulator mechanism, stop and ask.

### 6.3 Portfolio-lite sizing

Draft the file, then test it against the ceilings (first portfolio read model
plus three seeds plus landing change: likely the 160- or 220-line band) and the
cold-start test. If it does not fit, split (for example seed recipes, then the
Portfolio page), keeping both directly after T034 and noting that point 3
completes at the second. If fitting it would mean dropping one of the three
sites or a lens the strong demo needs, that changes a demo point: ask the
owner.

### 6.4 Task facts the Architect cited

Recheck against the files before relying on them: T027 AC10 and AC11 text;
T028 AC13; T036 AC1, AC4-AC7, AC13; T034 AC4, AC6, AC7; T030 AC2, AC9, AC13,
AC17; T031 header and AC1/AC2/AC9. If any differs from this guide, the task
file is the fact; adjust and note it.

---

## 7. Out Of Scope, And When To Stop

- **No code**, no tests, no edits to `tools/` or `frontend/` or `backend/`.
  Name code anchors in tasks; do not change them.
- **No change to the recommendation's product decisions** or to any section 9
  outcome. If planning reveals one is unworkable, write the question; do not
  plan around it.
- Do not edit `Docs/` (including the roadmap), `.ai/ARCHITECT_DEMO_RECOMMENDATION.md`,
  the owner files, `.ai/ROLE_CONFIG.md` or `CLAUDE.md`/`AGENTS.md`.
- Do not settle T025h's pending ruling.
- Do not contact anyone; tasks do not authorize contact.

**Stop and ask** (write the question in the packet under "Open questions",
finish everything else, and say in your final report that the plan is blocked
on it) when:

- a planning choice would change a section 9 outcome, a D1-D8 disposition, or
  what a demo point shows;
- a check in section 6 cannot be decided from the files;
- a task cannot pass the cold-start test without a decision only the owner or
  Architect can take;
- the files contradict this guide in a way that is not a simple fact
  correction.

Route questions to the coordinator, who sends Architect questions to the
Architect and product questions to the owner. A genuinely ambiguous point is a
question, never a guess.

---

## 8. Deliverable And Review

**Deliverable:** commits on `plan/demo-led-replan`, not pushed, not merged.

**Review packet:** `.agent/plan-demo-led-replan-review-packet.md`
(`git add -f`). It must let a fresh Reviewer check the plan against the
recommendation without this conversation. Contents:

1. Header: branch, commits (one line each), the binding that produced it
   (Claude under the Codex-reset exception, or Codex).
2. **Step 0 records:** each new decision ID and the two amended entries, with
   the recommendation section it implements (6.0, 2.2, 2.4, 4.3, 5.2, 8, 9) and
   the verbatim quotes it carries.
3. **Queue:** old rows 19-31 against new rows, each move with its
   recommendation section; the demo-point table before and after.
4. **Per task** (T025h, T027, T028, T029, thin follow-on, T029A, T034,
   Portfolio-lite, T030-T033, T035, T036): what changed (outcome, scope, ACs
   added, removed, reworded, moved), each change linked to its recommendation
   section; the phase assignment of every AC for T027 and T028; line count
   against its ceiling; the UI check that ends each phase.
5. **Checks (section 6):** evidence and outcome of each, and the resulting
   breadth order.
6. **Architect readings you relied on** (the clarifications marked in this
   guide: roadmap not edited; profile rules apply to capability ids; breadth
   slices seed their own sites; breadth pair order default) and any you added.
7. **Open questions**, if any, each naming who must answer.
8. Files touched, and confirmation that no code, `Docs/` or owner file changed.

**Review:** the coordinator dispatches a fresh Reviewer per `.ai/ROLE_CONFIG.md`
(a fresh Claude `assetops-reviewer` before the Codex reset; after it, the
binding there). The Reviewer reads the packet, this guide and the
recommendation. The owner then reviews the replan before merge.

**First task of the next implementation round: T027 phase 1** (Commit,
ingestion, Site > Evidence part A with the record-inspector drill-down, and the
tab-rule change), on branch `task/T027-commit-ingestion-and-site-overview`
cut from `main` after this plan merges.

---

## 9. Role Binding

`.ai/ROLE_CONFIG.md` binds the Planner to Claude until the Codex reset at
2026-10-03 21:23, and to Codex after it. Before starting, check the current
time against that line and the file itself:

- **Claude** (`assetops-planner`): do the work directly; state in every record
  and the packet that it was produced by Claude under the Codex-reset
  exception.
- **Codex:** the coordinator runs `codex exec` with this file's path as the
  brief, passing the prompt as an argument and redirecting `< /dev/null`
  (ROLE_CONFIG "Invocation mechanics"). Capture the session id so a review
  round can `codex exec resume` it. A Claude subagent must refuse if the
  binding is Codex.
- **A session that crosses the reset** finishes the work it started under the
  binding it started with, and says so in the packet.
- The plan branch carries a snapshot of `.ai/`; if `main` changes a rule before
  review, merge `main` into the branch first (ROLE_CONFIG).

Nothing in this guide depends on a Claude-only or Codex-only tool: it needs
git, file reads and edits.
