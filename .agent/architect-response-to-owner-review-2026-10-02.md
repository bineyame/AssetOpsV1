# Architect response to the owner's review (2026-10-02)

This responds to `.agent/owner-review-architect-recommendation-2026-10-02.md`
(verbatim, authoritative) as applied in `.ai/ARCHITECT_DEMO_RECOMMENDATION.md`
at `b12ae86`. It is a comment, not an edit: no existing file is changed.

Produced by Claude as Architect under the ROLE_CONFIG exception in force until
the Codex reset on 2026-10-03 21:23. A later reader may send any judgement here
back to Codex.

Where the answer depends on facts in the repo, I checked them. File references
are given so the Planner can check them too.

---

## Summary

I agree with all five of the owner's pushbacks. Two of them go further than the
owner's review and the revised document acknowledge.

- **The tab rule (point 5)** contradicts a written architecture rule, a
  recorded decision, a build check and shipped code. "Labelled in place" is one
  of the three Presentation Honesty treatments in `.ai/ARCHITECTURE.md`. The
  2026-09-13 decision adopted it. `tools/checks/navigation-truthfulness.ps1`
  enforces it. `frontend/src/shell/operatorSiteTabs.tsx` and
  `FOUNDATION_SUBTABS` ship it, with tests. The owner's rule is the better rule,
  but adopting it needs a decision record and a task to land in. The revision
  does not say that.
- **The rule should be applied per capability, not per site.** That is also
  where "absence communicates" really applies, and it is not where the previous
  round put it.

The narrowed `DomainPresentationProfile` (point 2) is right, but "may reference,
never source" holds only if there is a named backend contract for the profile
to reference. T028 is where that contract is born, and it is the same contract
that Site > Evidence part B (point 3) needs.

**Verdict:** the document is ready to be planning input. It needs a short list
of corrections (section 5). The Planner can carry them as constraints; they do
not need another architecture round.

---

## 1. The owner's five pushbacks

### 1.1 "Keep v6.9's grammar exactly" is too rigid: **agree, with a caveat**

The owner is right. The document itself already argued that global Financials
should probably not be a root, which contradicts a "preserve exactly"
principle. Product learning has to be able to change the canonical model.

**Caveat: "genuine ownership problem" needs a test.** Without one it becomes a
loophole that lets every demo-driven preference pass as product learning. v6.9
section 2.3 already has the right test for site tabs: "remove the tab and lose
nothing except a filter". Generalised:

- a place in the grammar keeps its slot only if it **owns** something that no
  other place shows: objects, a workflow, or site-owned content;
- an exception must name what would be lost by removing or moving the item,
  and what currently duplicates it.

Every exception also gets a `DECISIONS.md` entry. v6.9 is the canonical
reference, and silent drift from it is how the product loses the grammar
discipline that makes it legible.

**Second-order effect.** Once the grammar can change, the Planner should not
treat v6.9 screen text as an acceptance oracle where an owner decision has
overridden it. A task that cites v6.9 line numbers needs to cite the decision
too.

### 1.2 The archetype descriptor owned too much: **agree, but the seam needs a named contract**

The owner's boundary is correct. The failure the owner names ("frontend pack
says this Finding exists / backend analytic says something different") is the
specific way a static UI file would erode claim discipline.

**Where the seam is today.** Nothing in the code owns Finding types, evidence
requirements or verification rules yet:

- `backend/assetops_backend` has `sites`, `runs`, `scenarios` and the two APIs.
  There is no evidence, ingestion, analytic, finding or verification module.
- The archetype selector exists. Templates carry `foundation.site_type`
  (`MINIGRID`; `SITE_TYPES = {MINIGRID, COLDCHAIN}` in
  `backend/assetops_backend/sites/models.py`). The capability **signals** exist
  as ordinary Foundation signals under template v3
  (`available-power`, `discharge-capability` in
  `config/site-templates/kobo-mini-grid-60kw.yaml`).
- The only existing "requirements" declarations are on the simulator side:
  `EXECUTION_REQUIREMENTS` and the reporting-path states in
  `backend/assetops_backend/runs/profiles.py`. They describe what the simulator
  can model and publish. They must **not** become the source of analytic
  evidence requirements, because product analytics may not read private or
  simulator flows (T031 AC2; ARCHITECTURE.md).

So the seam is unoccupied, and it is born in two places:

- **T028**, the first analytic, which creates the first Finding type and the
  first evidence requirement;
- **T034**, which creates the first verification rule set. T034 AC6 already
  says "Version these rules with the assessment"; AC7 says T033 and T035
  extend "this same versioned rule set". That is backend ownership in the task
  text already.

**Is "may reference, never source" enforceable?** Not as written. Today it is a
sentence, and the document undermines it in one place. Section 4.3 says a
profile entry that references a capability the backend does not provide
"renders nothing, **or renders the explicit gap in 2.4**". The second branch is
exactly the failure the owner warned about: the profile would be the source of
the statement "this site should have capability X, and lacks it". A gap is
honest only when the **backend** says "this capability exists for this site
and its evidence is insufficient".

**What makes it enforceable** is a named backend contract, created by T028. I
would call it an **analytic capability declaration**. Each analytic module
declares:

- its id and the site types it applies to;
- the Finding type it may emit;
- its required and optional evidence (signals or capabilities);
- its claim levels (for dispatch: Necessary, Candidate avoidable,
  Indeterminate).

The backend serves the evaluated, site-scoped version of this as a read model.
The precedent is the simulator's model-profile pattern: required input versus
optional input, recorded as unsupported, enforced structurally by a
`tools/checks` guard. The product side should copy that rigour, not its data.

The profile then holds only `id -> label / order / grouping / emphasis`. Three
rules:

- A backend id the profile does not know still renders, with the backend's
  display name in a default position. Drift is never silent.
- A profile id the backend does not serve renders nothing, and a test flags the
  orphan.
- A gap is shown only from backend state, never from the profile.

**The same contract is what Site > Evidence part B evaluates.** "Full, Limited
or None by capability" is this catalogue scored against accepted coverage. That
is why point 3 and point 2 converge on T028 (see 1.3).

**Two further conflicts to fix.**

- **Consequence categories are backend-owned too.** Section 4.1 lists them in
  the "changes by domain" column without the backend-owned annotation the other
  rows got. The no-double-counting rule depends on the categories: v6.9 says
  "only non-overlapping categories aggregate", and T030 AC13 forbids counting
  modelled generator use as both dispatch consequence and fuel loss. So the
  categories must live with the financial model. The profile owns their
  *presentation*, which is the owner's wording, and it is right.
- **Vocabulary is substrate-owned.** ARCHITECTURE.md (Shared Presentation
  Substrate) says vocabulary "live[s] in the substrate and nowhere else", and
  that the substrate carries no shell, mode or variant discriminant. The
  profile should therefore be **substrate data**, selected from the read
  model's `site_type`. It should not be a shell module or a separate pack
  package. The document should state explicitly that `site_type` is domain
  data, not a shell or mode discriminant. Otherwise the first Reviewer to see
  `profileFor(site.siteType)` will reasonably flag it as a variant branch.

**Smaller point.** Overview assessment domains are profile grouping, but the
assessment on each card (for example "Dispatch: Needs attention") is backend
output. The profile chooses which cards exist and in what order. It never
decides a card's state.

### 1.3 Evidence split at T027 versus T028+: **agree; the boundary is clean in the task file, less clean in the screen**

The semantic split (A: records and coverage; B: what can be claimed) is correct
and important.

**T027's task file does not promise B.** It promises:

- an "evidence inspector";
- AC10, coverage that "names the required signals and selected window";
- AC12, record inspection (source, device, signal, mapping or config version,
  quality, original and normalised values, three timestamps);
- the proof row "Missing capability/report -> Coverage gap, no fabricated
  value".

All of that is A. One wording risk: in AC10, "required signals" must mean the
signals the Overview metrics need. It must not mean signals an analytic
requires, because no analytic exists at T027. The Planner should make that
explicit.

**What T026 staged fits A.** T026's capability signals become ordinary accepted
signals with coverage at T027. "PV available-power: 91%, 13 min missing" is A.
The line into B is crossed only when coverage is translated into what may be
claimed.

**Where it is not clean: the screen.** v6.9 8.35 defines Site > Evidence as a
summary page. It has a capability table (B) and a "Source / connector health
(data quality, not asset health)" section, which is the A-shaped part. Record
inspection is a different surface: the evidence drawer's "Show raw evidence"
(v6.9 8.37: "The drawer is claim-specific lineage; the Evidence page is
capability readiness").

If T027 lands its record inspector **as the body** of Site > Evidence:

- T028 must restructure the tab around the capability table and displace the
  inspector. That is rework inside two consecutive spine slices.
- T030 AC17 already refers to "the separate source-record inspector" for
  delivery and hand-dip records. It needs a stable home that does not move at
  T028.

My recommendation:

- **T027's Site > Evidence body:** source and connector health per source, and
  per-signal coverage for the selected window, with the mapping and
  configuration basis. That is v6.9's lower section, which is exactly A.
- **The record inspector:** a drill-down from a source or signal row and from
  the Overview metrics' evidence links (T027 AC11). It does not change the
  root, and T028's drawer later reuses it.
- **T028:** adds the capability table above the source-health section.

The page then grows in the shape v6.9 already drew, and nothing moves.

**Two second-order effects.**

1. **Overview cards at T027 can imply B.** The document's 2.4 exception shows
   domains with no assessment as "Unknown, with the missing evidence named".
   At T027 no analytic exists, so every domain is unassessed, not unknown.
   Saying "Unknown, missing X" is a claim-readiness statement, which is B.
   T027's cards should show measured metrics, their coverage, and a neutral
   "No assessment yet". Keep "Unknown" for an assessment that exists but
   cannot conclude, or for a site with no data in the window (v6.9 8.2).
2. **T028 grows.** The rescoped T028 already lands:
   - the analytic;
   - the Finding;
   - the drawer;
   - the Findings root and global index;
   - the scoped index;
   - Performance > Dispatch;
   - Overview card state;
   - Sites columns.

   Part B adds the capability contract and the capability table. Keep B
   minimal: one row per analytic that exists, which at T028 means one row. The
   Planner should phase T028 the way the document phases T027.

**One more overlap to state.** v6.9 has two "readiness" places: Foundation >
Readiness (configuration and commissioning readiness, with readiness Actions)
and Site > Evidence (capability claim ceilings). `FOUNDATION_SUBTABS`
currently labels Readiness in place. Under the new tab rule it should not
render until it has a source contract. When B lands at T028, it lands on Site >
Evidence only, so the same claim-readiness number does not appear in two
places.

### 1.4 Post-T034 order as priority intent: **agree**

The owner is right not to freeze the order. Here is my reading of the
dependency. **It is a reading for the Planner to verify, not a ruling.**

**What T031 declares:**

- `Depends on: T027-T030 and A's curtailment/dispatch model`
- `Delivery order: after T030`

**What T031's acceptance criteria consume:**

- accepted demand, PV capability, storage and reserve limits, generator
  operation and service evidence (AC3; T027 evidence plus T028's dispatch
  inputs);
- C's evidence and claim structure (AC7, T028);
- the price and tariff invariance in its proof (T029);
- a curtailing world, which **T031 owns itself** (AC1: "A healthy
  underutilized recipe produces repeated daytime curtailment through physics";
  AC2 extends the envelope path if needed).

None of these names a T030 artifact. "T027-T030" reads like range shorthand
from the earlier linear queue. T032 depends on T031, T029 and T029A, not on
T030.

**Possible real couplings the Planner should rule out:**

- **(a) T030 AC9:** a late record revises an accepted assessment while history
  is kept. If T030 is the first slice to build assessment revision, T031 AC9
  ("deterministic/versioned and avoids duplicate Findings") might quietly rely
  on it. If T028 already builds versioned re-analysis, there is no coupling.
- **(b) T030 AC13:** composing Site Financials without double-counting. T031
  adds no money (T031 scope: financial upside is scenario-based only at T032),
  so I expect none.
- **(c) T030 AC2:** extending T026's operational-record family. T031 uses no
  operational records.

**The previous round's second open question is already answered.** Whether T031
must supply a PV-curtailing world is answered by T031 itself. The cost is slice
size (a recipe, possibly a new signal, the L2 check), not a dependency.

**The cost the document does not state.** "Opportunity before fuel" really
means **T031 and T032 before T030**. T031's opportunity is a physical headroom
quantity with no money attached. The growth story the demo wants (Desta's
paired comparison with a scenario value) arrives only with T032, and T032 is
the heavier slice (isolated comparison history). So opportunity-first delays
fuel by two slices, not one. That may still be right, because fuel is the
weakest new persuasion. But the owner's "if dependency cost is low" should be
read as "dependency cost is low; slice cost is two".

**On T033 and T035:** README already makes them an interchangeable pair that
consumes nothing from each other. "Service before battery" is a free choice.

### 1.5 Contextual tabs: **agree with the rule; the exception as written should go and be replaced**

The owner's rule is right, and it matches the root-rail rule. Five things
follow.

**(i) It contradicts written architecture, and the revision does not say so.**

- `.ai/ARCHITECTURE.md` (Presentation Honesty) defines three treatments, one of
  which is "Labelled in place: a canonical tab that names a real aspect of an
  entity but has no content contract yet".
- `DECISIONS.md` 2026-09-13 adopted that treatment, citing v6.9's own
  "Warranty (P1)" usage. The later Site-tab decision applied it to six Site
  tabs and to Foundation > Readiness.
- `tools/checks/navigation-truthfulness.ps1` and
  `frontend/src/shell/operatorSiteTabs.tsx` (with its tests) enforce and ship
  it.

Adopting the owner's rule therefore needs a decision record. It narrows the
treatment to "not used in client-facing operator views", or retires it. It also
needs an ARCHITECTURE.md edit and a task home. T027 is the natural home,
because it makes Evidence a destination anyway, and removing six labels is
small. Without the decision record, an Implementer following ARCHITECTURE.md
and a Reviewer running the check would both rule against the document.

**(ii) Apply the rule per capability, not per site.** "Meaningful destination"
should mean that **this build has a truthful surface for this aspect**. It
should not mean that this particular site has data for it. If it is decided per
site, then:

- in the Portfolio-lite and T036 demo, Arsi shows a Health tab and Kobo does
  not;
- tab bars differ between sites in the same session;
- worst of all, a site whose lifecycle evidence is missing hides the very tab
  that should say "we cannot assess battery condition here".

**(iii) That is where "absence communicates" really belongs.** Once a
capability exists in the build, its tab renders on every applicable site. A
site without the evidence shows the gap inside the tab. That is the
legitimate, tab-level reading of the owner's "unless absence itself
communicates something useful".

The previous round's exception should go. It sits inside pages (Evidence
coverage gaps, Overview domain cards), so it is not an exception to a **tab**
rule at all. It is ordinary claim discipline ("Unknown, never Healthy"; T027's
"Coverage gap, no fabricated value"). Calling it an exception muddies the rule.
As 1.3 shows, its Overview-card half also over-claims at T027.

Applicability is a separate filter from rendering. Site > Health does not apply
to a cold room's battery, for example. That filter comes from the profile and
the backend capability catalogue, not from data presence.

**(iv) Does it conflict with v6.9 2.3, "Site > Work mirrors the WORK nav group
exactly"?** No. The rule is a mirror, and the demo WORK group holds only
Actions, so the mirror holds only Actions. A subtab row with a single entry is
noise, though. While WORK has one item, Site > Work should render the Actions
index with no subtab row, and the row should appear when a second WORK class
goes live. This still satisfies "mirrors", and it keeps to the "at most one
subtab row" invariant.

**(v) The tab bar grows between milestones.** Yes, it does:

| Milestone | Site tabs rendered |
| --- | --- |
| T027 | 3 |
| T028 | 5 |
| T029 | 6 |
| T034 | 7 |
| T033 | 8 |

Within any one demo the set is stable. Growth is visible only to a returning
audience (expert at point 2, then point 3), and to them it reads as progress,
which is honest. The real requirements are:

- tabs keep **canonical order**, so new tabs insert predictably (Health lands
  between Foundation and Performance);
- the rendered set derives from one canonical inventory filtered by
  capability, never from per-milestone lists.

`operatorSiteTabs.tsx` already keeps one inventory, so this is a change to its
filter, not to its structure.

---

## 2. The D1-D8 dispositions

### D1, filtered grouped root menu (accept; end-state not frozen): **agree**

Consistent with 1.1. Two small points:

- Group headers over a single item (OPERATE over Sites alone at T027,
  INTELLIGENCE over Findings alone) look heavy. Showing headers "from T028" is
  fine, but the layout check should cover a one-item group.
- The Assets root at T033 depends on the T033/T035 order. If service runs
  first, Assets arrives last. That is acceptable, because nothing before T033
  needs it.

### D2, Portfolio-lite after T034: **agree with a caveat**

It is the best structural idea in the document. Its cost is understated,
though. It needs three reproducible sites:

- Meki healthy, which pulls T036 AC1's recipe forward;
- Kobo with a **post-action** history;
- an evidence-limited site on which T028's analytic runs and limits its claim.

It also pulls in T036 AC4-AC6 (priority and no-fake-total). That makes it a
real slice, not a thin one. The Planner should size it honestly and give it its
own seed (section 4, item 4).

### D3, Kobo detect to verify uninterrupted: **agree with a caveat**

The story order is right. Its live mechanics are not addressed. T034's outcome
is "simulate the later operating window and ingest the new evidence", so
between Accept (journey step 6) and Verification (step 7) a later window has to
be run in the Lab. In a live demo that is either:

- a Lab detour in the middle of the story, which contradicts "Lab last, as
  proof"; or
- a **pre-seeded post-action window** ("two weeks later"), with the Lab trip
  saved for the closing reveal.

Only the second keeps D3 intact. That means point 3 needs a seed, the same way
the document already gave point 2 one in T029.

### D4, priority intent: **agree**

See 1.4. Read "dependency cost is low" as true on current evidence, and add
that opportunity-first moves two slices (T031 and T032) ahead of fuel.

### D5, narrower presentation profile: **agree, with the contract added**

See 1.2. Without the T028 capability-declaration contract and the substrate
placement, "reference, never source" is unenforceable. Fix the 4.3 "or renders
the explicit gap" branch, and mark consequence categories as backend-owned.

### D6, Site Evidence at T027 = A, B from T028: **agree with a caveat**

See 1.3. T027's tab body should be source health and coverage, with the record
inspector as a drill-down. Overview cards should say "No assessment yet", not
"Unknown". At T028, B is one capability row.

### D7, Action + Foundation > Changes: **agree**

It is coherent with T034 AC1 ("persists an inspectable configuration/action
record") and with the T008 ruling that `Changes` stays absent until a reviewed
configuration-change capability exists. T034 is that capability, so `Changes`
legitimately appears there.

One thing to keep explicit: in a simulated site, Foundation > Changes records
the accepted product decision. The world's actual change is evidenced by
post-action configuration evidence through the normal path (T034 AC4).
Changes should link to that evidence, not stand in for it.

### D8, park T025h: **agree**

There is no client-visible cost. Template drift is avoided by seeding v3 sites.

---

## 3. Global Financials: BUSINESS root or Portfolio lens

**Recommendation: treat the cross-site financial roll-up as part of Portfolio
for now. Promote it to a BUSINESS root only when a portfolio-owned financial
object exists.** Decide it after T036. It is on no demo path.

Apply the 1.1 test: what does a global Financials root own? v6.9 8.9 gives it
cross-site consequence lines by non-overlapping category, each clicking through
to Site Financials or a Finding, with "the global page never re-derives site
bridges". That is aggregation and nothing else. Portfolio Value & Operations
already carries it as the value column. On today's content it fails the test.

**What would make it pass.** T029's BusinessContext scope is undecided:
"versioned BusinessContext with currency, effective time, provenance, fuel
price..." does not say whether it is per site or portfolio-wide. A realistic
operator has one diesel contract across sites. If assumptions become
portfolio-shared, then a shared assumption set (with its versions and effective
times) is a genuine portfolio-owned object, and a global Financials root would
own it. Budgets or exportable financial reports would do the same.

My advice for T029 is to keep BusinessContext **site-scoped**, because the live
price change on Site > Financials > Assumptions is the point-2 demo moment, and
to record "shared or portfolio assumption sets" as the trigger for revisiting
this decision.

**Costs, as I see them:**

| Option | Cost |
| --- | --- |
| BUSINESS root (v6.9 as written) | No grammar change. One more page whose only content duplicates Portfolio's value column, so two surfaces must apply identical non-overlap and basis rules, with consistency tests between them. A BUSINESS group with one weak item, because Reports is P1 and deferred. Clients see a "finance module" that adds nothing. |
| Portfolio lens / view | A recorded deviation from v6.9 (DECISIONS entry, and a note on the canonical reference). It cannot be a Findings-style lens on Portfolio's subtab row, because v6.1 keeps that row to interpretation lenses, so it is a Portfolio view or section. A finance persona loses an obvious menu entry. Promoting it later is a route and navigation move, which is cheap if the view has a stable address from the start. |

**Do the same for global Evidence.** The 1.1 test should be applied to global
Evidence at T036 for the same reason. Global Evidence passes more easily,
because cross-site instrumentation prioritisation is a decision workflow that
creates Actions (v6.9 8.8 and 8.35). But it should pass the test explicitly,
not by default.

---

## 4. What the review missed (material items only)

1. **The tab rule needs a decision record and a task home** (1.5 i). It
   overturns a written ARCHITECTURE.md treatment, a recorded decision, a build
   check and shipped tests. Put the ARCHITECTURE.md and DECISIONS change in the
   Planner's step 0 and the code change in T027 phase 1. Remove Foundation >
   Readiness along with the six Site labels.
2. **Apply the rendered-tab rule per capability, not per site** (1.5 ii-iii).
   This is the difference between a stable product and tab bars that vary from
   site to site in the portfolio demo.
3. **Scope growth on the spine.** Every spine slice gains UI from this
   recommendation:
   - T027: Evidence tab, Overview frame, Sites columns, landing change;
   - T028: global index, scoped index, Performance subtab, capability contract
     and table, Sites columns;
   - T029: editable assumptions, seed;
   - T034: Actions root, Work, Changes, Finding tabs;
   - plus the new Portfolio-lite.

   README says T027 is "watched for scope growth". The owner's review did not
   weigh this against the date of demo point 2, which is where expert feedback
   reshapes everything after it. The Planner should protect point 2: anything
   not on the point-2 journey (Sites -> Kobo Overview -> Dispatch -> Finding ->
   drawer -> Financials) can move to a thin follow-on slice. The Sites columns
   and the Sites-as-landing change are the first candidates. T028 should be
   phased.
4. **Every demo point needs a seed, not only point 2** (D3, D2). Point 3 needs
   Kobo's post-action window already in accepted history. Portfolio-lite needs
   three reproducible sites. The rule should be "each demo point ships with an
   idempotent, rehearsed seed", owned by the slice that creates the point.
5. **The source-record inspector needs a stable home** (1.3). Make it a
   drill-down, not the Evidence tab body, so T028 does not displace it and
   T030 AC17 can extend it.
6. **BusinessContext scope must be decided in T029** (section 3). It is the
   hinge for the global Financials question, and it affects how the live price
   change behaves once there are three sites.

Not material, but worth knowing: the ROLE_CONFIG exception ends on 2026-10-03
21:23. A Planner pass that runs after that is bound to Codex, which will
inherit this document as Claude-authored input.

---

## 5. Overall verdict

**Ready to be planning input: yes**, as the owner says. The sequencing and the
product surfaces are sound, and none of the issues above changes the spine,
the demo story or the decisions D1-D8. Another exploration round would cost
more than it returns.

**The minimum still needed** is six corrections. The Planner can carry them as
binding constraints, or they can go into a short amendment to the document,
whichever the owner prefers:

1. A decision record and ARCHITECTURE.md edit retiring or narrowing "labelled
   in place" for operator views, with the change landing in T027 phase 1.
2. The rendered-tab rule stated per capability, not per site. Drop the 2.4
   "named exception", and restate in-page gaps as ordinary claim discipline.
3. The analytic capability declaration named as a T028-owned backend contract,
   with these rules:
   - the profile references its ids;
   - unknown backend ids still render;
   - profile orphans render nothing;
   - gaps come only from backend state.

   Delete the 4.3 "or renders the explicit gap" branch. Mark consequence
   categories as backend-owned. Place the profile in the substrate, keyed by
   `site_type`.
4. T027 Site > Evidence:
   - the tab body is source health and coverage;
   - the record inspector is a drill-down;
   - Overview cards say "No assessment yet", not "Unknown";
   - "required signals" in AC10 means signals the Overview metrics need.
5. A demo-seed rule for points 3 and Portfolio-lite, as well as point 2.
6. T029 decides the BusinessContext scope (site-scoped recommended). Global
   Financials stays open until after T036, with the promotion trigger above.
