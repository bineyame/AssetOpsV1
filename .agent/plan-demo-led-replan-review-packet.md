# Review Packet: Demo-Led Replan (Planner, 2026-10-02)

## 1. Header

- Branch: `plan/demo-led-replan`, cut from `arch/demo-led-recommendation` at
  `446906e`. Not pushed, not merged.
- Commits:
  - `2e33f94` Planner step 0: record the demo-led recommendation and its rules
  - `7842aa3` Planner: replan the queue from T027 under the demo-led recommendation
  - `db4203f` Planner: amend T027-T036 and add T029B and T034A for the demo-led plan
  - (this packet and the handoff file, a fourth commit)
- Binding: Planner = **Claude under the Codex-reset exception**
  (`.ai/ROLE_CONFIG.md`; reset 2026-10-03 21:23; work done 2026-10-02). Codex
  may review it retrospectively.
- Brief: `.agent/planner-guide-demo-led-replan-2026-10-02.md` (the "guide").
  Source: `.ai/ARCHITECT_DEMO_RECOMMENDATION.md` at `57ea23e` (the "rec").
- How the work was done: the coordinating Planner wrote step 0 and the queue.
  A read-only agent ran the section 6 fact checks. When the coordinating
  context neared the 120k handoff point, it wrote
  `.agent/plan-demo-led-replan-handoff.md`, and three fresh Planner agents
  amended disjoint task files from that handoff. All of them were Claude under
  the same exception.

## 2. Step 0 Records (rec 6.0; guide 3)

All entries are in `.ai/DECISIONS.md`. Each is appended under `## 2026-10-02`
and has an index row at the top of the table.

| ID | Implements | Verbatim owner wording carried |
| --- | --- | --- |
| `D-2026-10-02-demo-led-recommendation` | 6.0, 7, 8, 9 | "review looks fine."; the D1-D8 table and the owner's summary (8.1). The six section 9 outcomes are labelled **the coordinator's reading, not the owner's words**, which the owner may correct. Roadmap 5/13.3 walk order superseded for demo purposes; the roadmap is not edited. |
| `D-2026-10-02-rendered-tabs-per-capability` | 2.4, 9 item 3 | The tab rule: "The canonical tab set defines ownership and future placement; the rendered tab set contains only meaningful destinations unless absence itself communicates something useful." |
| `D-2026-10-02-grammar-ownership-test` | 2.2, D1 (8.1, 8.2) | D1: "Accept, but don't promise the full v6.9 end-state can never change" |
| `D-2026-10-02-presentation-profile-and-capability-declaration` | 4.3, D5 | "what findings actually exist", "what evidence an analytic requires", "what verification rules exist", "The descriptor can reference those capabilities, but shouldn't become the canonical source for them.", "frontend pack says this Finding exists / backend analytic says something different" |
| `D-2026-10-02-demo-point-seed-rule` | 5.2 | none |

**Amended entries.** Both are flagged in their index rows and with a pointer
at the end of the entry body; neither is rewritten.

- `D-2026-09-13-canonical-fidelity`: the middle "labelled in place" treatment
  is no longer used in operator views.
- `D-2026-09-17-foundation-screen-architecture`: the six labelled Site tabs
  and Foundation > Readiness.

What still stands in both is named in the new entry.

**[Verify] in guide 3.2.** No non-operator surface renders "labelled in place"
today. The non-operator mentions are code comments only:

- `frontend/src/shell/simulatorLabRoutes.tsx:422`
- `frontend/src/ui/DataTable.tsx:26`

The operator uses are in `operatorSiteTabs.tsx` and `FoundationSubtabs.tsx`.
T027 phase 1 removes them.

**Other edits:**

- `.ai/ARCHITECTURE.md`: Presentation Honesty (bullet narrowed; per-capability
  sentence added) and Shared Presentation Substrate (profile as `site_type`
  substrate data).
- `.ai/PRODUCT.md`: a strong product demo row, and "Four demo points" updated
  to T034 + Portfolio-lite; the cold-chain deferral is untouched.
- `.ai/PLANNING_GUIDANCE.md`: "Live now" lists the rec.
- `.ai/START_HERE.md` and `.ai/ACTIVE_CONTEXT.md`: next is T027 phase 1, and
  T025h is parked.
- `.ai/FEATURE_MAP.md`: **unchanged**. Its unowned-requirements owner cells
  name map letters, not task ids, so no owner cell moves.

## 3. Queue (`tasks/README.md`; rec 7, 6.1-6.4)

| Old row | Old | New row | New | Rec |
| --- | --- | --- | --- | --- |
| 19 | T025h | - | T025h **parked** | 6.3, 6.5, D8 |
| 20 | T027 | 19 | T027 (phase 1, phase 2) | 6.2 |
| 21 | T028 | 20 | T028 (three phases) | 6.2 |
| 22 | T029 | 21 | T029 | 6.2 |
| - | - | 22 | **T029B** thin follow-on (new) | 6.2, 6.4, 9 item 4 |
| 23 | T029A | 23 | T029A | 6.1 |
| 24 | T034 | 24 | T034 | 6.2 |
| - | - | 25 | **T034A** Portfolio-lite (new) | 6.4, D2 |
| 25 | T030 | 28 | T030 | 6.3, D4 |
| 26 | T031 | 26 | T031 | 6.3, D4 |
| 27 | T032 | 27 | T032 | 6.3 |
| 28 | T033 | 30 | T033 | 6.3, D4 |
| 29 | T035 | 29 | T035 | 6.3, D4 |
| 30 | T025i | 31 | T025i (unchanged) | 6.1 |
| 31 | T036 | 32 | T036 (rescoped) | 6.2 |
| - | T026A | - | T026A (unchanged, unscheduled) | 6.1 |

**Prose under the table:**

- A new top paragraph cites the approval decision.
- The interchangeable pair is now rows 29/30, with the default quoted
  verbatim: "Service before battery unless feedback says otherwise".
- The breadth order is stated as priority intent that point-2 feedback can
  redirect.
- The delta p95 task is a note with no task file (6.5).

**Demo points.** Before: 1 T027; 2 T028/T029; 3 T034; 4 T036. After:

1. T027, a live run with no seed.
2. T028/T029, seeded by T029.
3. **T034 + T034A**, opening on Portfolio, seeded by T034 and T034A.
4. T036, seeded by T036.

The section also carries the per-point journeys from rec 5.2 and cites the
seed rule. "After T028/T029, reassess T030-T036 ..." is kept.

**T025h.** The task file was brought in from `f4274f2` only, with no merge or
cherry-pick, and its status is set to `parked`. Its pending ruling (whole form
versus scenario and profile) is recorded as the owner's or Architect's to make
when the task is scheduled, with the rec's view quoted. Branch
`task/T025h-picker-compatibility` is left as it is; for the task file, this
plan branch supersedes it.

## 4. Per Task

Line ceilings are from `.ai/WORKFLOW.md`: 120 for UI/content, 160 for
boundary, and 220 for analytics, Finding semantics or write paths.

### T027 (220 / 220 after fix round 1; rec 6.2, section 3 Evidence and Site Overview, 2.4, 4.3, D6)

**Changes.** One file with a Phases section; the 220 ceiling held, so it was
not split.

- **Reworded:**
  - AC10: coverage names "the signals the Overview metrics need", not analytic
    requirements. The rest of AC10 is intact. The Proof row "Missing
    capability/report -> Coverage gap" implies no analytic.
  - AC11: "No assessment yet"; "Unknown" is not used for a missing analytic.
  - AC12: the record inspector is a drill-down that opens without changing
    the root.
  - AC18: the landing is stated.
- **Added:**
  - AC20: the Evidence part A body, with no readiness and no claim ceiling.
  - AC21: the tab rule, with code and check anchors and non-loosening wording.
  - AC22: the profile keyed by `site_type`.
- **Removed:** nothing.
- **Scope:** the broad cross-site source-health dashboard stays deferred;
  site-scoped source health is in scope. The Sites columns moved to T029B;
  Sites-as-landing is T027 phase 1 (AC23, after the Architect ruling). No seed.

**Phase assignment:**

- Phase 1: ACs 1-9, 12, 16-18, 20, 21 and 23 in full, plus the evidence parts of
  10, 13, 14, 15 and 19.
- Phase 2: ACs 11 and 22, plus the Overview parts of 10, 12, 13, 14, 15
  and 19.

**AC18 landing.** Site > Evidence in both phases. It shows the actual
acceptance and rejection outcome, and the Overview frame does not exist in
phase 1.

**UI checks:**

- Phase 1: Lab run -> Commit -> Open in AssetOps -> Site > Evidence shows
  source health, coverage and a drill-down with three timestamps; it stays
  with the Lab off.
- Phase 2: the internal demo, rec 5.2 row 1.

### T028 (220 / 220; rec 6.2, 4.3, section 3 Finding Detail and Evidence)

**Changes:**

- ACs 1-15 are kept.
- AC13 gains **persisted, inspectable revision history**: the prior
  assessment is retained, not overwritten, and inspectable after a revision
  and across reload (check 6.1).
- **Added:**
  - AC16: the capability declaration contract.
  - AC17: a `tools/checks` guard against `EXECUTION_REQUIREMENTS`.
  - AC18: the three rendering rules, each tested, applied to backend ids.
  - AC19: an expected-orphan list that shrinks as analytics land; an
    unexpected orphan fails.
  - AC20: the Evidence capability table, with one dispatch row.
  - AC21: navigation. Recommendation and History are not rendered until T034;
    Site > Findings is a scoped index; the drawer reuses T027's inspector.
- **Kept:** the stop-60 policy-record question, the expert checkpoint and no
  seed.
- **Moved:** Assessment and Top issue went to T029B.

**Phase assignment:**

- Phase 1: ACs 1-11, 13, 14, 16 and 17, plus 12 and 18 for the Overview
  Dispatch card. The card was moved into phase 1 so that phase 1 has something
  to open in the browser.
- Phase 2: ACs 8, 12, 15 and 21 on screen, plus 18 and 19.
- Phase 3: AC20, plus 18 for the Evidence rows.

**UI checks:**

- Phase 1: the Dispatch card shows a candidate on the prolonged run and none
  on the healthy reference. This check is weak: the declaration and revisions
  are seen only at their read-model URLs.
- Phase 2: rec 5.2 row 2 up to the drawer, plus the Findings index.
- Phase 3: one dispatch row; the degraded-evidence site shows Limited and
  names the missing battery capability.

**Rail from phase 2:** OPERATE: Sites; INTELLIGENCE: Findings. Five Site tabs.

### T029 (153 / 220; rec 6.2, 2.4, 2.5, 3 Financial Consequence, 5.2)

- Financials is a destination with `Overview | Assumptions` and no assessment
  status. Six Site tabs.
- **Reworded:**
  - AC1: site-scoped, and records the editing actor.
  - AC9: one model for the Overview value line, the consequence panel and
    Financials.
- **Added:**
  - AC11: the subtabs.
  - AC12: a UI edit creates a new BusinessContext version; invalid input is
    refused and the store is left unchanged.
  - AC13: site scope, with the verbatim trigger "shared or portfolio
    assumption sets"; no global Financials.
  - AC14: the **point-2 seed** (Kobo v3, healthy and prolonged-runtime windows,
    idempotent, Lab gate off, rehearsed).
- AC10 and roadmap 12.1 are unchanged.
- UI check: the full point-2 journey on the seed, changing the price live.

### T029B (new, 111 / 120; rec 6.2, 6.4, 2.1, 9 item 4)

- The four Sites columns and ranking. The landing and the retirement of the
  T002 `Operator home` placeholder are inherited from T027 phase 1 (AC23).
- The file applies the ownership test: it states what would be lost and that
  nothing duplicates it.
- Uses T029's seed.
- UI check: the app opens on Sites, and the Kobo row links to the same objects
  the point-2 journey opens.
- The column definitions were written from rec 2.1, 6.2 and 6.4, because
  T027/T028 at `HEAD` did not define them.

### T029A (99): Delivery order only: "after T029 (and T029B); next T034".

### T034 (208 / 220; rec 6.2, 2.1, 2.4, section 3 Action / Verification, 5.1, D7)

- **Screens:**
  - an Action root with `Overview | Verification`;
  - Actions in the rail under WORK;
  - the Finding gains Recommendation and History tabs;
  - "Awaiting verification" on the Findings index;
  - Site > Work with no subtab row, making seven Site tabs;
  - Foundation > Changes, which lifts `$forbiddenSubtab = "Changes"` and the
    `FoundationSubtabs.tsx` note, citing the tab decision.
- "Action/Maintenance" becomes "Action", with the category seam kept.
- **Reworded:**
  - AC6: the rule set joins the capability declaration.
  - AC11: Completed and Verified are distinct words.
- **Added:**
  - AC18: the screens above.
  - AC19: the **point-3 seed**.
- The Review paragraph is kept word for word.
- UI check: rec 5.2 row 3 from Kobo onward, on the seed.

### T034A Portfolio-lite (new, 171 / 220; rec 6.4, section 3 Portfolio, 2.1, 5.2, D2)

- Portfolio becomes the landing page, taking it from T027, and joins the rail
  with an OPERATE header before Sites.
- A backend Portfolio read model with no new analytic.
- **Pulled forward from T036:**
  - AC4, AC5 and AC6, here as AC3-AC5 (rechecked against T036);
  - AC7, here as AC6, with Meki.
- **New ACs:**
  - rail and landing;
  - the scope sentence;
  - a healthy site kept distinct from one that cannot be assessed;
  - lenses per capability (attention and evidence gap now; opportunity from
    T031);
  - "What changed";
  - idempotent and isolated seeding;
  - the Kobo journey unchanged.
- **Seed, three sites:**
  - Kobo (T034's seed);
  - Meki healthy;
  - an evidence-limited site from `kobo-mini-grid-degraded-evidence` v1 on its
    own Site.
- UI check: demo point 3 from Portfolio with the Lab off.

### Breadth slices (rec 6.3, 7 steps 9-12, 2.2, 2.4)

Every breadth slice now joins the capability declaration and owns its own
site's recipe and seed, pulled forward from T036 AC1 under the seed rule.

| Task | Lines | Position | Per-slice notes |
| --- | --- | --- | --- |
| T031 | 102 / 220 | after T034A; next T032 | `Depends on` lists the consumed artifacts and says "Not T030"; the two-slice cost is recorded; the stale scope line now says T029A owns the mechanism; AC11 joins the declaration and makes Opportunities a lens; AC12 seeds Desta |
| T032 | 160 / 160 | next T030 | AC20 makes the comparison a drill-down from Renewable, not a tab; Desta's seed gains the comparison pair |
| T030 | 126 / 220 | after T032; next T035 | AC18: the record inspector extends T027's; AC19 joins the declaration; AC20 seeds Genda; the UI check is optional, per 5.1 |
| T035 | 131 / 220 | after T030; next T033 | Service before battery by default; AC15 adds the Service and Backup views with no incident object; AC16 joins the declaration; AC17 seeds Bahir |
| T033 | 136 / 220 | after T035; next T025i, then T036 | AC18: Site > Health is the eighth tab and Assets joins the rail after Sites; AC19 joins the declaration; AC20 seeds Arsi |

### T036 (134 / 220; rec 6.2, 2.2, 5.1, 6.5)

- Rescoped to completing the Portfolio.
- **AC1:** one seed command covers every site. T036 authors only the recipes
  of sites that no earlier slice seeded.
- **AC4-AC7:** each is replaced by a "moved to T034A" note, so existing
  references still resolve. They are re-proved at six sites, and the value
  column never totals across consequence types.
- **AC13:** the walk follows the 5.1 journey and cites the approval decision;
  Genda is optional.
- **New AC17:** global Evidence joins the rail only if it passes the ownership
  test, with its own DECISIONS entry.
- The delta p95 task runs only if playback stutters.
- No global Financials, Incidents, Maintenance, Reports or cold-chain screens.

### Not changed

T026A, T025i and the completed tasks.

## 5. Checks (guide 6)

### 6.1 T030 -> T031: no content coupling

Evidence:

- **T031 `Depends on: T027-T030 ...`** (header): the only link to T030 is
  range shorthand. T031 consumes:
  - the T026/T027 evidence path (AC2, AC3);
  - A's physics (AC1, AC3);
  - T028's claim structure (AC7);
  - T027's Overview;
  - T029's price, only through the price-invariance proof.
- **(a)** T031 AC9, "Repeated analysis is deterministic/versioned and avoids
  duplicate Findings.", needs no history. T028 AC13, "Changed accepted evidence
  creates an inspectable assessment revision.", **did not require persisted
  history**. Persisted history is now added explicitly to T028 phase 1, which
  removes any reliance on T030 AC9.
- **(b)** T030 AC13 (no double-counting when composing Site Financials): T031
  composes no Financials.
- **(c)** T030 AC2 (the operational-record family): T031 uses no operational
  records.
- **T032** depends on T031, T027, T029 and T029A only.
- **T033 and T035** name no T030 artifact. T035:74 is a regression guard.

**Outcome:** opportunity first. The breadth order is **T031, T032, T030, T035,
T033**, at a recorded cost of two slices ahead of fuel.

### 6.2 Evidence-limited site: suitable

`config/scenarios/kobo-mini-grid-degraded-evidence.yaml` degrades three
things:

- battery discharge-capability readings are dropped 09:00-10:00, with no
  substitution;
- the 10:00 SOC publication is delayed to 10:10;
- the 08:00 operator override record is lost (the override itself is real).

All three fall inside the generator run. They map to T028 AC3, AC5 and AC7 and
Proof rows "PCS capability missing for part of interval" and "Override
absent". The result is a segmented or limited claim, not nothing. Completed
T026 AC6 states the same intent. No new recipe or simulator mechanism is
needed.

### 6.3 Portfolio-lite sizing: fits as one file

T034A is 171 lines against the 220 band: a cross-site read model plus a
backend priority rule over Findings counts as Finding semantics. It passes the
cold-start test: scenarios are named, the template exists, and the priority
rule's inputs are stated.

- If a Reviewer classes it as a 160-line boundary slice, the split is seed
  recipes first, then the Portfolio page.
- No site or lens was dropped. The opportunity lens appears at T031 under the
  per-capability rule, which matches 6.4's "where content exists".

### 6.4 Cited facts

The guide matches the task files with two exceptions:

- T028 AC13 is weaker than assumed (see 6.1).
- The handoff's T031 line numbers were stale. The quoted text matched, so this
  is a fact correction only.

## 6. Readings Relied On

**Architect readings** (marked in the guide):

1. The roadmap (`Docs/...`) is not edited; the approval decision records the
   override.
2. Rec 6.0's "update the roadmap's demo story and demo-point table" is read as
   the queue's demo story (`tasks/README.md`, `.ai/PRODUCT.md`).
3. The profile rendering rules apply to backend capability ids, not to the
   profile's Overview domain cards.
4. Breadth slices seed their own sites.
5. The breadth pair order (opportunity/fuel before service/battery) is a
   default, not a decision.

**Planner readings added:**

- `FEATURE_MAP.md` is unchanged (its owner cells hold letters).
- New ids T029B and T034A.
- T027 AC18 lands on Site > Evidence.
- T028's Dispatch card is in phase 1.
- T029 AC12: an edit states its effective time and which assessed windows it
  reprices before saving, so a live price change can reprice the demo Finding.
- T034 AC19: the seed includes the accepted Action and its frozen
  intervention, so the demo walks an already-accepted Action. A live Accept is
  exercised in review.
- T029B ordering (as tightened in fix round 1): open-Finding sites first, by
  claim level, then lower coverage, then name. T034A replaces this.
- T032 adds no capability-declaration entry, because it emits no Finding.
- T034A's Meki is the healthy reference T028/T029 already use, or a Meki
  scenario if T036 AC7 needs observed service; the Implementer chooses.

**Off-journey candidates** (proposed only; nothing moved):

- T028 phase 3's Evidence capability table. Removing it would leave the
  drawer as the only claim-limit view at point 2.
- The global Findings index. Removing it would delay the INTELLIGENCE header
  that 2.1 places at T028.

The Planner recommends keeping both.

## 7. Open Questions

1. **ANSWERED (Architect, 2026-10-02, Claude under the ROLE_CONFIG exception): drop `Operator home` in T027 phase 1; `/` redirects to `/sites`; T028, T029 and T029B edited to agree.** Reason: its frame says "No sites are configured", false once Commit exists, so keeping the item fails the truthful-destinations rule. Original question: `Operator home` between T027 and T029B. The live rail is
   `Operator home` + `Sites` (`frontend/src/shell/OperatorShellLayout.tsx:34`).
   Rec 2.1 says Operator home goes when Sites becomes the landing page, and
   the guide moves Sites-as-landing to T029B. The guide also says "Rail at
   T027: Sites only, no group header", and rec 2.1's table has T028 as
   "OPERATE: Sites".
   - **As written (both agents chose this independently):** Operator home
     stays until T029B, so the T027 rail is two items and T028 has a
     two-item OPERATE group.
   - **Alternative:** T027 drops the rail item while `/` stays a placeholder
     or redirects.

   This is a guide/rec contradiction, not a fact correction, so it is raised
   here rather than settled. It affects T027 phase 1's rail statement only;
   either answer is a one-line edit to T027, T028, T029 and T029B.
2. **Owner (trivial):** a name for the evidence-limited Portfolio-lite site.
   It is unnamed now, and T036's six names are ruled out.
3. **Owner (for awareness):** Bahir is seeded and appears on Portfolio, but
   the 5.1 journey has no Bahir step. This follows the rec.

## 8. Size And Scope Concerns

- T027 and T028 are each exactly 220 and T032 exactly 160, which leaves no
  headroom for review edits. Further additions mean a split or moving text
  into decisions.
- T034 is 208 / 220 after fix round 1.
- T028 phase 1's UI check is weak, because two of its outcomes are visible
  only at read-model URLs.

## 9. Files Touched

- `.ai/`: `DECISIONS.md`, `ARCHITECTURE.md`, `PRODUCT.md`,
  `PLANNING_GUIDANCE.md`, `START_HERE.md`, `ACTIVE_CONTEXT.md`.
- `tasks/`:
  - `README.md`;
  - T025h (added);
  - T027, T028, T029, T029A, T030, T031, T032, T033, T034, T035, T036;
  - T029B and T034A (new).
- `.agent/`: this packet and `plan-demo-led-replan-handoff.md`.

**Not changed:**

- no code (`frontend/`, `backend/`, `tools/`);
- no `Docs/` (the roadmap and the untracked `Docs/` files are untouched);
- no owner files, `.ai/ARCHITECT_DEMO_RECOMMENDATION.md`,
  `.ai/ROLE_CONFIG.md`, `CLAUDE.md` or `AGENTS.md`.

## 10. Next

**First implementation task: T027 phase 1** (Commit, ingestion, Site >
Evidence part A with the record-inspector drill-down, and the tab rule). It
runs on `task/T027-commit-ingestion-and-site-overview`, cut from `main` after
this plan merges. It is ready once the reviewer and owner accept the plan,
and open question 1 is answered (Operator home leaves in phase 1, T027 AC23).

## Fix round 1 (Planner, Claude under the Codex-reset exception)

Review: `.agent/plan-demo-led-replan-claude-review.md` (accept with fixes).
No product decision in `.ai/ARCHITECT_DEMO_RECOMMENDATION.md` was changed;
nothing was deferred.

| Finding | Fix |
| --- | --- |
| B1 T025h status | `tasks/T025h-picker-compatibility.md:3` now `Status: planned`; the parked position line and README row "-" are kept. |
| B2 T027 contradiction | New AC23 (`T027:122-124`) removes `Operator home` and its frame, redirects `/` to `/sites`, rail Sites only; assigned to phase 1 (`T027:~133` (phase 1 line)). Anchors added: `OperatorShellLayout.tsx:34`, `OperatorShellFrame.tsx` and its test, five route tests (`operatorRouteFrames`, `simulatorLabWorkspaceEntryPoint`, `siteDetailRoute`, `siteFoundationRoute`, `sitesIndexRoute`) and the `/` visit in `tools/layout-evidence.mjs` (a report labelled "Operator home" at line 1272; the review said no scenario existed, but this one does and needs relabelling). Scope-limits sentence now reads "Sites columns are T029B; the Sites index content is unchanged here (only `/` now redirects to it)". |
| B3 line ceilings | T027 221 to 220 and T028 220 stays 220, both counted with `wc -l` at normal wrap, no lines joined. T028's 128-character line was rewrapped (+1) and paid for by merging two Read-for-detail bullets and tightening one Outcome sentence. T027 was held by wording cuts only. Moved here (nothing else moved): the AC18 rationale and the "No sites are configured" reason (below). |
| N1 T029 effective time | `T029:93-101` (AC12): defaults to the start of the BusinessContext version it supersedes, may be earlier than the edit, stored beside its recorded time (AC6), and the UI check edits with a time covering the seeded prolonged-runtime window. |
| N2 T034 seed and Recommendation | `T034` AC19: the seed creates the Action through the same Accept API and the Action is not evidence. AC18: an accepted Finding's Recommendation tab shows the accepted state, links its Action, offers no second Accept. UI check says "Recommendation (accepted state)". |
| N3 T029B ranking | AC4 (within-site order: Candidate Avoidable, Indeterminate, Necessary, then latest) and AC5 (open-Finding sites by claim level, then coverage, then name; shown as an interim replaced by T034A). |
| N4 T031 opportunity weight | T031 AC12 ends: "The priority rule gains a new version weighting opportunity, shown on the page (T034A AC4)." |
| N5 stale text | T029B title, Outcome, ownership test, Read-for-detail, Deliver landing bullet and AC7 rewritten; no layout-evidence remnant check. README row 22 and this packet (sections 4, 10) updated. T028 and T029 scope lines and T034A lines 9, 58, 61 also said T029B owns the landing and now say T027. |
| N6 README seed sentence | `tasks/README.md:135`: "Every point from 2 onward ...". |
| N7 seed-rule decision | `.ai/DECISIONS.md` seed-rule entry marks the breadth-slice sentence "Architect reading, planner guide section 5" and the hand-staged wording as Planner wording. |
| N8 long lines | T028 (192), T029B (83) and T036 (34) rewrapped or rewritten. T034:160 (a table row) shortened. Remaining over-96 lines are two table rows (T027 Proof, T034 Proof), which cannot wrap. |

Moved to this packet from T027 (the rationale only, not scope): AC18 lands on
Site > Evidence in both phases because that page shows actual accepted coverage
and rejections and the Overview frame does not exist until phase 2. Phase 1
removes `Operator home` because its frame says "No sites are configured",
false once Commit exists (recommendation 2.1; Architect ruling `58d756b`).

Residual-risk items from the review are carried into T027: AC21 now says the
`Changes` ban stays until T034, and the rendered-after-each-phase paragraph
runs layout evidence on `/` as well as on Evidence.

Line counts after fix round 1: T027 220, T028 220, T029 153, T029B 111,
T034 208, T034A 172, T036 135, T031 102, T025h unchanged.

Checks after fix round 1 (run with `-ExecutionPolicy Bypass`):
`tools/check-agent-workflow.ps1` passed; `tools/check-architecture.ps1`
passed.

## Fix round 2 (R1-R4)

Planner (Claude) fixes for the four notes in
`.agent/plan-demo-led-replan-claude-rereview.md`. Wording only; no product
decision changed.

- R1: T029 AC2 and AC12 say a tie between the default effective time and the
  superseded version's start resolves to the later recorded time.
- R2: `tasks/README.md:17` and this packet's T034A section now credit the
  landing to T027, not T029B.
- R3: T027 AC19 restores "private execution artifacts unavailable"; the AC
  stays two lines, so T027 is still 220 lines.
- R4: T029B AC5 ranks a site whose only open Findings are Necessary in the
  no-open-Finding group (coverage, then name), after every Candidate Avoidable
  or Indeterminate site, consistent with AC4's within-site order.
