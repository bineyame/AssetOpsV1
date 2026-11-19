# Layer 4 regeneration, Phase H: whole-pack discovery review

Reviewer: fresh Claude reviewer (did not author the work). Worktree `/opt/assetecon/AssetOpsV1-pack-int`, branch `task/pack-recreate-integrate`, head `6628c87f4`. Read-only except this file. Discovery depth (W5): every document under review was read in full, against design rev 16.11, the owner's 19 Nov records, the 17 Nov feedback, the brief, RULES §10 and plan F. Earlier review files in `regeneration/` were not read before forming this view.

## Summary

- **Verdict: REVISE.** The design and the pack's checks are sound, and every code claim checked is accurate. A short fix round is still needed first: nine Medium findings would leave a builder or the owner guessing.
- **Counts: High 0 · Medium 9 · Low 12 · Info 4.**
- **Builders would guess on four points.** First, the decision-loop specification, the integration design and the matrix lag rev 16.10–16.11: the placement rules are missing, and the daily snapshot is contradicted (M1, M2). Second, the role rule for claims contradicts the OD-16 worked example (M3). Third, two documents define two different Action release state machines (M4). Fourth, the UI gate (D7) and the governing mock for the fortnight's screen slices are unresolved, and the mock's Organisation settings still show the old roles (M6, M7).
- **The owner would be misled on three points.** OD-20 is said to start step 3C on day 1, but the computed schedule starts it on day 5 (M5). The website's "How it works" page states coming features in the present tense with no Coming tag (M8). The mock-up's opening screen splits the gap three ways and labels unexplained fuel as unattributed (M9).
- **Mechanics all pass.** `check_manifest.py` 4260/0. `check_alignment.py` 108/0, with 54 C4 words. `plan_model.py --check` and `regenerate_traceability_columns.py --check` both ok. The three renders are byte-identical (`cmp`). The mock-up tools all pass: 205 renders with 0 script errors, vocab hits 0, plan switch 621/0, hand-typed hits 0 with 46/46 allow entries used. The Mermaid read-lint found no syntax hazard in the pack's diagrams.
- **Code: 27 claims checked against file:line. All are accurate,** and one paraphrase is loose (C17).
- **Known open items 1–5:** confirmed as stated. Item 2 is slightly worse than stated (L5).
- **Not verified:** the visual and browser rendering (there is no browser), Mermaid parsing by a real parser, and known items 1 and 3 beyond reading them.

## 1. Findings, by class (W6)

### Class A. Derived builder documents lag the design (rev 16.10–16.11)

**M1 (Medium): the decision-loop specification lacks rev 16.11's placement rules.**
- *Location:* `decision-loop-specification.md:3` (header "updated to rev 16.9"); §3, `:82` and `:95-101`.
- *Quoted:* "a Finding's category is its pinned factor's; a decision's is its lever factor's".
- *Problem:* design §2.0 (`layer4-transformation-design.md:248-251`, `:268-271`) adds three rules:
  - a node's home is named on its row, never inherited;
  - money never sits under Protect or Assure, so compensation and penalties are Optimize;
  - a decision's lever is found in order: it restores a Protect measure, else the money factor it changes, else the factor it compares.
- *Evidence:* the specification states none of them. Its start-up check (`:85`) and acceptance tests (`:154`) test only "exactly one home category". This is the builder's specification for `3B1`, which builds days 3–5 of the fortnight.
- *Why it matters:* a builder could place Thika's compensation under Protect, or file the Kisiwa genset decision under Optimize, and pass every stated test.
- *Fix:* carry the three rules into §3. Add two start-up refusals: a money node whose home is Protect or Assure (except At stake), and a row that inherits its home. Add one acceptance test per rule.

**M2 (Medium): the daily snapshot (OD-23) is contradicted in three builder documents.**
- *Locations and quotes:*
  - `integration-design.md:90`: "Factor values, outcomes, bridges | Not stored as totals | Computed on read from leaves (`chain/period_read.py:139`)".
  - `reuse-and-gap-matrix.md:30`: "No stored totals … Stays; the structure is computed on read".
  - `delivery-plan.md:73` (`3B3`): "nothing stored as a total".
- *Problem:* design §2.8 (`:727`, `:737`) serves the structure from a stored snapshot, "never recomputed on a screen read". The snapshot replaces recompute-on-read. The matrix (rev 16.8) is also missing two of design §2.9's register rows:
  - "Stored route responses, period read → Extended (OD-23)";
  - "The four categories (catalogue) → Stay, re-grounded (OD-21)". The matrix's `:61` still says "Catalogue … Stays — —", with no home-category field and none of the three named row moves (profitability, fuel accounted for, cash collected).
- *Why it matters:* the matrix claims to be "the inventory beneath the design's change register". A builder reading it would not plan the snapshot or the catalogue re-grounding.
- *Fix:* restate the rule as "no stored figure is a source; evaluated values are served from a rebuildable snapshot". Add the two missing matrix sections. Sweep `3B3`'s wording.

**L1 (Low): the documents cite design revisions from 16.7 to 16.9, while the design is at 16.11.**
- *Locations:* `plan-and-action-workflow.md:3` (16.8), `reuse-and-gap-matrix.md:3` (16.8), `two-week-build-plan.md:3` (16.8, "checked against 16.9"), `delivery-plan.md:3`, `integration-design.md:3`.
- `commercial-plan.md:8` names "rev 16.7" as the product-claims source.
- `structure-specification.md` is rev 13.1, kept on purpose (P1).
- *Fix:* re-stamp each header after checking the document against 16.10–16.11. M1 and M2 are the substantive gaps this sweep found.

### Class B. Roles, states and rules that disagree between documents

**M3 (Medium): who chooses a claim contradicts the OD-16 example.**
- *Locations:* design §2.4 step 2 (`:463`): "the finance and commercial lead for billing, collection, claims and notices". `decision-loop-specification.md:348` (the permission table): "Choose an option, or none … finance: billing, collection, claims, notices; site manager: operations and O&M".
- *Problem:* OD-16's example has David, the Mto Site manager, choosing the inverter warranty claim. That example comes from the owner's accepted default, and it appears in `worked-portfolios.md:653`, `:665`, `plan-and-action-workflow.md:137`, `:144`, and on the mock-up's `#/decision/mto-inverter` ("2 · Who chooses · Site manager, Mto David").
- *Why it matters:* under the specification's permission table, David's choice would be refused with a typed reason, yet the demonstration shows it as allowed. A builder cannot write the role check for a decision whose options include a claim without guessing.
- *Fix:* the Architect rules one of two ways. Either the decision's kind sets the chooser (`mto-inverter` restores capacity, so operations chooses, and the lead files the notice), or the lead chooses claims and the example changes. Then write the rule into the permission table.

**M4 (Medium): two documents define different Action release state machines, and neither machine is in the design.**
- *Locations:* `decision-loop-specification.md:286-299` uses the states Created, Released, Waiting, Returned, "Deferred into the next plan" and Withdrawn. `plan-and-action-workflow.md:239-251` uses Checked, Released, Waiting, Stopped and Returned, and its Returned state leads to the final state on "deferred … or withdrawn".
- *Problem:* the design gives the plan's states (Figure 6b) and the item's states (Figure 6c), but no Action release states. Plan F §3 says a derived document "never adds a new … status". The two documents differ in their names, in "Stopped", and in whether deferral is a state.
- *Why it matters:* slice `7b` (Release) has two specifications.
- *Fix:* put one Action release machine in the design, beside Figure 6c, or state that release is derived (as item states are). Have both documents cite it.

**L2 (Low): system-choice wording in the allocator and on the plan screen.**
- *Locations:*
  - `structure-specification.md:204-211`: "6.3 Choosing the plan", "The plan is the feasible combination…", "read from the chosen combination", "Exactly one option is taken" (`:189`).
  - Mock plan screen: "the plan picks the better one that fits".
  - The headings "Factors and layers (M1, M2)" and "(M3)" (`:81`, `:96`, `:154`) keep the retired mechanic numbers.
- *Problem:* the design's rule is that the system proposes and people choose (§2.6, `:607`). "Chosen" means a person's choice everywhere else in the pack.
- *Fix:* say "proposed set" and "taken in the proposal". The numbers M1–M3 can go under P1, because this is naming only.

**L3 (Low): a new read permission conflicts with the design.**
- *Location:* `integration-design.md:174`: "Customer-level rows and contract documents are shown only to … the finance and commercial lead and the analyst."
- *Problem:* the design says "every role sees the same screens" (§2.6, `:597`), and OD-15 lets the executive accept imports in the lead's place. Under this rule the executive would accept records it cannot see.
- *Fix:* either have the design state the data-access rule, including the executive, or drop it.

### Class C. Readiness to build the first fortnight

**M5 (Medium): what OD-20 buys is misstated.**
- *Locations and quotes:*
  - Design `:771`: "so their slices start on the first build day".
  - `delivery-plan.md:39`: "so their slices start on day 1".
  - `two-week-build-plan.md:99`: "So their slices start on day 1".
  - `two-week-build-plan.md:309`: "Decision 1, now decided (OD-20), puts lanes 3 and 4 to work on day 1".
- *Evidence:* in the computed schedule of the same document, lane 3 shows "—" on day 1 (`:123`) and runs `0K` on days 2–5. `3C0` starts at 4.68 (`:173`) and `3C1` at 5.83, so step 3C starts on day 5. Ranking by step puts step 0's spike ahead of 3C. `3C0` also depends on `1a` (`delivery-plan.md:77`), which follows Figure 10's `S1 → 3C` edge, but no reason is given why sign-in must wait for the Optimize-card fix.
- *Why it matters:* the owner accepted OD-20 on the premise "Without this, lanes 3 and 4 wait for sitting 1" (`two-week-build-plan.md:303`).
- *Fix:* either rank `3C0` before `0K` on lane 3 and drop the `1a` dependency, or correct the four sentences to "step 1 starts on day 1; 3C on day 5".

**M6 (Medium): the UI build gate (D7) conflicts with the fortnight's screen slices.**
- *Location:* `decisions-register.md:138` (D7 default): "No UI build of Part 2 screens before the owner approves the design and the recreated mock-up."
- *Problem:* the fortnight schedules Part 2 screens from day 6: `3B5` site-board factor rows, `3C3` work controls, `5c` the bridge, `5d` the relabel. Meanwhile `walkthroughs.md:5` says the mock-up is "Not approved" and has had no visual check. No document says whether approving the pack approves the mock-up, or which mock governs these slices. `.ai/START_HERE.md:38-40` says v70 governs live screens and lists vNEXT as "Layer 4 destination (still changing)". RULES §6 requires every screen spec to cite its governing mock element.
- *Why it matters:* an Architect writing the `3B5` or `5c` spec cannot tell whether it may start, or which mock it must follow.
- *Fix:* add an owner question with a default: "approving the pack approves vNEXT as the governing mock for Layer 4 screens, subject to the visual check". Name the governing element for each screen slice of the fortnight.

**M7 (Medium): the mock-up's Organisation settings contradict the design's roles.**
- *Location:* mock `#/settings` (Organisation settings): "Users and roles … B. Yohannes Admin Everything, including settings · Operations manager Manager · Site controls lead Operator · Maintenance lead Technician · Finance analyst Viewer".
- *Problem:* this is the v7.0 role set. The design has five roles, no Admin and no Viewer (§2.6, `:599-605`). OD-14 has the executive grant roles, and the executive sets the spend and crew-visit thresholds. No mock screen shows role grants, thresholds or budget settings.
- *Why it matters:* `3C0`, which lands on day 6, builds "the executive grants and removes roles in Organisation settings". Its only mock element shows the wrong roles, and under RULES §6 an unlabelled departure is High at review.
- *Fix:* update the mock's Organisation settings to the five roles, with grant and removal records, and add the threshold settings. Or label the panel a MOCK DEVIATION D5, naming `3C0` and `7b`.

**L9 (Low): the spec handshake is not in the schedule.**
- *Location:* `plan_model.py` capacity (`two-week-build-plan.md:46`, `:105-115`).
- *Problem:* the owner's 19 Nov rule (RULES-main `:96-99`) adds, for every unit, an Architect spec, a reviewer guide and a reviewer Q&A before code. The model counts Architect time only for structure pages, and reviewer time only after build. The fortnight's reach is optimistic by that amount, on top of the snapshot slice it already leaves out.
- *Fix:* add a per-unit handshake allowance, or state the optimism beside the one already stated for the snapshot.

**L8 (Low): mechanical leftovers.**
- `two-week-build-plan.md:17` cites `two-week-conversion-plan.md`, which is retired.
- `:239`: "the furthest complete step moves from step 5 to step 5".
- `check_manifest.py` prints "note: not yet written: " with an empty list.

### Class D. Owner fidelity: the honest-figure rules and one name per meaning

**M8 (Medium): the website states coming features as available now.**
- *Location:* `website-content.md` §3.6, `:218-228`, and §3.8, `:262`.
- *Quoted:*
  - "**Decide** · The product prepares the options and recommends one."
  - "**Act** · Your team creates the actions, each with an owner and a due date. Spend above the limit your executive sets waits for their approval."
  - "**Track** · Every action followed to done, with overdue shown."
  - "**Prove** · … whether the money followed and whether the change caused it."
  - "**See** · … recorded, emulated, measured…".
  - "Doing nothing is always shown beside every option."
- *Problem:* these are CH3, P, CH2, CH4 and the Layer 4 evidence words, all of which are Part 2. The blocks carry no tag and are written in the present tense. Rule 7 says "A coming construct is never called available now". The lint passes because untagged blocks are not checked. Separately, the Today line "**Whether it worked**" (`:73`) is not limited to mini-grids, but verification today covers mini-grids only (design L6).
- *Why it matters:* the owner asked whether the copy is honest and in step with now and coming. On this page it is not.
- *Fix:* give each loop step a Coming tag, or split each into its Today half and its Coming half. Then extend the lint so an untagged block that names a lexicon construct fails.

**M9 (Medium): the mock-up's opening screen splits the gap three ways and implies a residual.**
- *Location:* mock `#/portfolio`, Lakeside (walkthrough step 1).
- *Quoted:* "Revenue factors move it by −$97, cost factors by −$755"; "−$852 … −$676 attributed to factors · −$176 not explained by the model yet"; and, in the Assure bridge, "All sites −$25 −$827 −$852. Grow and Optimize effects add up to each gap."
- *Evidence:* the −$176 is Kobo's −150 plus Kisiwa's −26 of unexplained litres, which are attributed to the factor `unexplained_l` under Optimize.
- *Problem:* the screen labels an attributed factor as unattributed. That contradicts the bridge two cards below and the design rule "an explicit residual only where a leaf is unobserved" (§2.2). The revenue and cost split, beside the Grow and Optimize split, also gives the executive two different breakdowns of one gap.
- *Fix:* show one split, by heading, and name the fuel line "fuel the generator model does not explain (under Optimize)".

**L4 (Low): the What changed screen contradicts item states.**
- *Location:* mock `#/portfolio/what-changed`.
- *Problem:*
  - "Kisiwa: repair generator 1 … Repair booked", while its Action is "Waiting for approval".
  - "Mto: connect the rice huller … Waiting for inverter 2", while it has no Action (OD-17). The real reason it waits is capital approval.
  - The plan-spend drawer lists "Fix the meter records … $0" as an option in the plan, while WP §1.1 (`:275`) puts the billing fix beside the plan.
- *Fix:* derive these lines from item states.

**L5 (Low): the Mto claim's one-off is labelled two ways.** This is slightly worse than known item 2.
- *Location:* mock plan screen, the Mto claim card.
- *Quoted:* "One-off cost · who pays $367.50", while the same card's Actions say "$230 over both Actions", and WP's one-off is 230.00.
- *Problem:* −367.50 is the option's value: the one-off plus extra fuel to the restore. It has no money factor of its own (known item 2), and here it is also labelled as the one-off.

**L10 (Low): the Mto billing fix is unvalued for a reason that conflicts with OD-21.**
- *Location:* `worked-portfolios.md:247`; `vertical-factor-map.md:30`.
- *Quoted:* "It is not an evaluated option: the restored charges are listed beside the plan, because collecting them is a separate step"; and "restored charges listed, not added, until collected".
- *Problem:* contribution is measured on what is billed, and collection is cash outside it (design §2.0, `:264`). Restored billing therefore moves contribution whether or not it is collected. The rule that every decision is valued against no action (§2.4) also lapses for `mto-billing`.
- *Fix:* value the restored billed kWh against no action. The option still needs no plan item, because it spends nothing.

**L11 (Low): a Finding is labelled as a factor.** The mock labels the letter-of-intent Finding "New factor · Mto: The cooperative's signed letter of intent…". This conflicts with OD-6's spirit and §10 point 6: a Finding is not a factor. Fix: use a Finding label such as "Opportunity".

**L12 (Low): the website simplifies who chooses.**
- *Quoted:* "Site managers choose" (`website-content.md:164`); "Your site and operations managers choose" (`:220`).
- *Problem:* under design §2.4 step 2, the finance and commercial lead chooses billing, collection and claims options, and the executive chooses capital.
- *Fix:* say "the person accountable chooses: managers, finance, or your executive for capital".

### Class E. Short, illustrated, and the objective in every part

**L6 (Low): the documents run well past plan F's lengths.**
- *Evidence:* the register is 5,329 words against a target of 3 pp; the delivery plan 5,183 against 8 pp; the commercial plan 6,153 against 7 pp; the website content 5,837 against 7 pp. In all, the 12 documents run to about 59k words, roughly 120 pages, against plan F's "~77 pages" (`F:21`). The owner said "i don't need a large doc".
- *Fix:* trim the register's superseded table and the restated rules, and cite the design instead.

**L7 (Low): most documents state how they serve the objective only once.**
- *Evidence:* "Serves the objective" appears once in the register, the integration design, the matrix, the factor map, the delivery plan, the two-week plan and the walkthroughs, and never in `structure-specification.md`. RULES §10 point 4 asks for it in "each section, construct and change". The design, the decision-loop specification, the workflow, the commercial plan and the website do this per section.

### Class F. For the owner's attention (Info)

- **I1.** MG-L2 (demand shaping) is a brief "Hero paired with L1" lever (brief L2.2). It is in scope with no demonstration option (`vertical-factor-map.md:28`), for a stated reason: a time-linked tariff must be agreed.
- **I2.** OD-22: the EMS API is placed in step 9, with the edge gateway after it (register call 16). The owner wrote "EMS data upload, api..first". The order is kept; the timing is the Architect's call.
- **I3.** The Assure card shows the bridge's money table (A1), with "Assure adds none". This matches the owner-approved A1 text ("including contribution's bridge"), but the owner should look at it against "no money under Assure".
- **I4.** The pack names its schedules "plans" (delivery plan, two-week build plan, commercial plan), a third sense of the word beside OD-6. The lint allows it.

**Known open items.**
- Item 1 is as stated.
- Item 2 is slightly worse (L5).
- Item 3 is as stated.
- Item 4 is confirmed. The "Not on screen yet" paragraph is stale: the as-of time and "Recalculation pending" now render, and Harvest's network cash line shows "$4,370 received of $4,588 invoiced".
- Item 5 still stands, and this review could not close it either.

## 2. Owner fidelity: OD-1 to OD-24 and the owner's instructions

| Item | Applied consistently? |
|---|---|
| Q-A1, OD-3: a Finding is a living output; a Finding is raised under the owner's rule and its tolerance | Yes: design §1.3, the decision-loop specification §4, the workflow §9 and the register. No C1 phrasing (lint A3) |
| Person decides, acts, tracks; the system never chooses or acts | Yes in rule (design `:607`, the specification `:357`, the workflow §9). Wording slips: L2, L12, M8 |
| OD-1: one origin and at most one plan membership | Yes: the specification §7, the workflow §6, the matrix §8 and the migration list |
| OD-2, OD-8, OD-11, OD-12, OD-18: thresholds | Yes, the same in the design, the specification §6, the workflow §2 and §6, the delivery plan's `7b` and WP §1.5. With no threshold set, nothing is released, everywhere |
| OD-4, OD-5, OD-10, OD-16, OD-17 | Yes, except that OD-16's example breaks the claim-chooser rule (M3) |
| OD-6: "plan" means only the new construct | Yes on screens and in prose. I4 |
| OD-7, OD-9, OD-13, OD-14, OD-15, OD-19, OD-20, OD-22, OD-24 | Yes. OD-20's effect is misstated (M5). The mock contradicts OD-14 (M7). OD-15 conflicts with the integration design §7 (L3) |
| OD-21: four headings; no money under Protect or Assure; collections under O3 | Yes in the design, the factor map, the commercial plan, the website and the mock. Rev 16.11's placement rules are missing from the specification (M1). The mock shows a residual (M9) |
| OD-23: daily snapshot | In the design and the specification. Contradicted in three documents (M2). Not a slice yet (stated, with a default) |
| Overall objective in every part | Partly (L7) |
| Short and illustrated | Illustrated where things change. Not short (L6) |
| One name per meaning | Mostly. L2, L11, M9, I4 |
| Vertical factor map (owner, 19 Nov) | Done. All 28 brief levers are present. Out-of-scope levers carry the L2.7 reasons (MG-L9, CC-L4), "not applicable" (EV-L6) or "later" (EV-L8). Each in-scope factor has a Site read and a roll-up. Checked by `factor_map()` |
| Website copy pass (owner, 19 Nov) | Outcome-led hero, the four headings as the frame, corner-tag badges, and WC7 in the lint. The honesty gap is M8 |
| Build-start handshake | In RULES. Not in the schedule (L9). The Architect's specifications are blocked by M3, M4, M6 and M7 |

## 3. RULES §10 table

✓ = met · ~ = partly · ✗ = not met · n/a. Points: 1 existing before new · 2 mechanism to value · 3 change on merit · 4 structure first, objective in every part · 5 person in the loop · 6 precise names · 7 short and illustrated · 8 owner decides (open questions with defaults).

| Document | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 |
|---|---|---|---|---|---|---|---|---|
| Design rev 16.11 (source) | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ~ | ✓ |
| `decisions-register.md` | n/a | ✓ | n/a | ~ | ✓ | ✓ | ✗ (L6) | ✓ |
| `decision-loop-specification.md` | ✓ | ✓ | ✓ | ✓ | ~ (M3, M4) | ✓ | ✓ | ✓ |
| `integration-design.md` | ✓ | ✓ | ✓ | ~ (L7) | ~ (L3) | ~ (M2) | ✓ | ✓ |
| `structure-specification.md` (kept) | n/a | ~ | n/a | ✗ (L7) | ~ (L2) | ~ (L2) | ✓ | ~ |
| `reuse-and-gap-matrix.md` | ✓ | ~ | ~ (M2) | ~ | ✓ | ✓ | ✓ | ✓ |
| `vertical-factor-map.md` | ✓ | ✓ | n/a | ✓ | ✓ | ✓ | ✓ | ✓ |
| `plan-and-action-workflow.md` | ✓ | ✓ | ✓ | ✓ | ~ (M3, M4) | ✓ | ✓ | ✓ |
| `delivery-plan.md` | ✓ | ✓ | ✓ | ~ | ✓ | ~ (M2) | ~ | ✓ |
| `two-week-build-plan.md` | n/a | ✓ | n/a | ~ | ✓ | ✓ | ~ | ~ (M5, M6) |
| `walkthroughs.md` | ✓ | ✓ | n/a | ~ | ✓ | ✓ | ✓ | ✓ |
| `commercial-plan.md` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ~ (L6) | ✓ |
| `website-content.md` | ✓ | ✓ | n/a | ✓ | ~ (L12) | ~ (M8) | ~ (L6) | ✓ |
| Mock-up (rendered text) | ✓ | ✓ | n/a | ✓ | ~ (M7, L2) | ~ (M9, L11) | not visually checked | n/a |

**What lands when.** The two-week plan, the delivery plan and the commercial plan agree:
- by day 14, at the planning pace, steps 1–5 are complete;
- the deep-dive safeguard needs 3A, 4 and 5;
- the first change needs step 6, which is 81 in 100 units at day 14;
- the commercial plan assumes 3A to 6 are live when the deep-dive starts, 4–8 weeks after approval.

No contradiction was found. The fortnight is optimistic by the snapshot (stated) and by the handshake (L9).

## 4. Code-claim table (27 claims; paths under `backend/assetops_backend/` unless stated)

| # | Claim (document) | File:line | Result |
|---|---|---|---|
| C1 | 22 outcome rows across four categories (design §1.1) | `outcomes/catalogue.py:43-68` | ✓ 8 MG, 7 EV, 7 CC |
| C2 | "Cash collected" is a Grow row; "Site profitability" Grow; "Fuel accounted for" Protect (design §2.0 named changes) | `catalogue.py:45`, `:46`, `:51` | ✓ exact lines |
| C3 | Trial events allow only a SYSTEM actor (design §1.4) | `migrations/versions/0016_action_store.py:131` | ✓ `CHECK (actor_kind = 'SYSTEM')` |
| C4 | "SYSTEM demonstration … no operator approval is recorded" | `actions/lifecycle.py:43-58` | ✓ |
| C5 | A user actor is refused on work writes, `WORK_USER_AUTH_REQUIRED` | `work/model.py:284-285` | ✓ |
| C6 | "No telemetry creates an Action or a case link" | `work/domain_intent.py:17` | ✓ |
| C7 | `recorded_amount@1` "returns no money with NO_RECORDS, always" | `chain/strategies/recorded_amount.py:1` | ✓ |
| C8 | Objectives "for the demonstration; not a customer target" | `objectives/model.py:23-24` | ✓ |
| C9 | The reserve trial "does not predict … any saving" | `actions/reserve_trial.py:42-45` | ✓ |
| C10 | The intervention cost is fixed at 0 | `actions/verification.py:1167` | ✓ `InterventionCost(Fraction(0), …)` |
| C11 | Positive evidence only if simulated or authored | `actions/verification_rules.py:688` | ✓ `REGISTERED_SIMULATION`, `AUTHORED_DEMONSTRATION` |
| C12 | The mini-grid board reads one day (L7) | `site_outcomes/read.py:676-682` | ✓ `WINDOW_BASIS_DAY` for MINI |
| C13 | The Assure line reads "Actual against plan" | `site_outcomes/mini.py:692` | ✓ |
| C14 | One-origin check; forced mini-grid opportunity origin; thread one-origin | `0051_action_opportunity_origin.py:73-77`, `:78-79`, `:87-88` | ✓ |
| C15 | Placement is "never a value ranking" | `estate/placement.py:1-8` | ✓ |
| C16 | Overdue is "strictly before" the range end; due soon is 14 days (the specification §8) | `outcomes/plan_due.py:4-5`, `:15`, `:29-32` | ✓ |
| C17 | Today's period read computes totals on read and stores none | `chain/period_read.py:46-47` | ✓ in substance: lines 46-47 are the guard that no row writes a total |
| C18 | Stored route responses under a watermark, invalidated by input-change triggers | `migrations/versions/0047_chain_response.py:1-14` | ✓ |
| C19 | Batch intake is first-write-wins; a changed payload is a conflict | `evidence/service.py:484-492` | ✓ |
| C20 | Reading upload refuses already-recorded intervals | `reading_upload/service.py:244-248` | ✓ `ALREADY_RECORDED` |
| C21 | Gateway credential bound to its Site; a mismatch is refused | `evidence/ledger_service.py:194-211` | ✓ `SCOPE_MISMATCH` |
| C22 | A human price write is refused, `HUMAN_PRINCIPAL_REQUIRED` | `financial_api.py:205-212` | ✓ |
| C23 | Dispatch raises a Finding for indeterminate running | `analytics/dispatch.py:40`, `:1070` | ✓ `FINDING_CLAIM_LEVELS = (CANDIDATE, INDETERMINATE)` |
| C24 | Five stored Finding mechanisms in the outcome map | `outcomes/outcome_map.py:17-23` | ✓ |
| C25 | Six objectives; only energy cost per km is a money measure | `outcomes/objectives.py:57-60` | ✓ |
| C26 | Warranty appears only as withheld fields | `sites/battery_boundary.py:26` | ✓ `WARRANTY_EXPOSURE` in `WITHHELD` |
| C27 | No sign-in and no budget construct in the backend; Modbus proof, CSV upload and six Portfolio tabs exist | grep over `backend/`; `host/tests/test_field_modbus_tcp_proof.py`; `field/assetops_field/csv_upload.py`; `frontend/src/estate/portfolioWords.ts:29-37`; `frontend/src/sites/OutcomeBoard.tsx:42-48`, `:270` | ✓ The only sign-in text is a placeholder sentence (`financials/price_page.py:33`). There is no "budget" in `backend/` |

## 5. Checks run, and what they printed

**The pack folder:**
- `python3 check_manifest.py` printed "4260 checks passed, 0 failed" and exited 0. It also printed "note: not yet written: " (L8) and "54 C4 words left for the reviewer".
- `python3 check_alignment.py` printed "alignment: 108 checks passed, 0 failed" and exited 0. Of the 54 C4 words, all I sampled are in kept or descriptive contexts, for example "replaces `x.md`" in the status lines.
- `python3 plan_model.py --check` printed "ok two-week-build-plan.md: 9 table blocks match … every must-keep slice lands by day 12" and "ok delivery-plan.md: 1 table blocks match the model".
- `python3 regenerate_traceability_columns.py --check` printed "traceability columns regenerated" and exited 0.

**The renders:**
- `render_design_html.py` matches the design twin: `cmp` byte-identical.
- `render_commercial_plan_html.py` printed "ok: 4 computed tables match"; `cmp` byte-identical.
- `render_website_content_html.py` printed "ok: 76 copy blocks pass the lint; 12 prepared trigger lines pass; 86 planted violations caught"; `cmp` byte-identical.

**The mock-up tools:**
- `tools/render_text.cjs` printed "rendered 205 screen renders; script errors 0". Its output file is tracked and unchanged.
- `tools/vocab_check.cjs`: hits 0.
- `tools/plan_switch_check.cjs`: 621 passed, 0 failed.
- `tools/hand_typed_scan.py`: count 0 and manifest hits 0. All 46 allow entries are used, none unused.

**Mermaid,** linted by reading, plus a scan for quote, `#` and `;` hazards. The pack's diagrams are clean. The hazards found are only in retiring documents (`domain-and-decision-models.md`, `integration-source-to-canonical-design.md`, `phase-plan-and-acceptance.md`). The gantt uses `dateFormat X` with fractional values, which most Mermaid versions accept. This is not proven without a parser.

**Not run, under the brief's rules:** suites, databases, Docker, installs and the browser. **Not verified:** the visual layout and phone width, real Mermaid parsing, known items 1 and 3 in the data.

## 6. What the owner should look at first

1. **M3: who chooses the Mto inverter claim.** It is your OD-16 example. Decide whether claims are chosen by the finance lead or by the person accountable for the asset.
2. **M6: does approving this pack also approve the mock-up as the governing screen design?** If not, the fortnight's screen slices from day 6 wait (D7).
3. **M5: what OD-20 buys.** Step 3C starts on day 5, not day 1, unless the lane order changes.
4. **M8: the website's "How it works" page.** It reads as available today.
5. **The mock-up's Lakeside overview (M9), the Assure card (I3) and Organisation settings (M7).** These are the first screens of your walkthrough.
6. **L6:** the pack is about 120 pages against the ~77 planned.
