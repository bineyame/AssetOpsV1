# Layer 4 regeneration, Phase D: independent review of rev 16.3

Reviewer: fresh Claude reviewer (did not author the work). Branch `task/layer4-design-regeneration`, head `86a1a3b94`. Read-only except this file.
Under review: `layer4-transformation-design.md` and `.html` (rev 16.3), `worked-portfolios.md`, `design-appendix.md`.
Standard: `.agent/owner-design-regeneration-request-2026-11-19.md` (all of it) and `.agent/RULES-main-2026-11-19.md` §10.
Earlier reviews (`regeneration/A`, `B`, `C`) were read only after this review's findings were formed, and only to check for regressions.

## Summary

- **Verdict: REVISE.** The main document is sound. It is accurate against the code: of 26 claims checked, 23 are confirmed, 2 are confirmed but slightly understated, and 1 is overstated. It is faithful to the owner on Findings, the person in the loop, the plan and its two links, and configurable settings. The mechanics all pass.
- **Counts:** High 0 · Medium 3 · Low 8 · Info 5.
- **M1:** `worked-portfolios.md` still uses "Plan" for the operator's targets throughout ("Plan against actual", Plan columns, "Plan limit"), beside "Plan: proposed by the system". This breaks OD-6, which the main document says is applied.
- **M2:** the main document itself uses "plan" for other things: verification plans ("the plan freeze", "frozen plan") and maintenance plans. The HTML Figure 3 also shows today's on-screen label "Actual against plan", and the document does not say what happens to that label.
- **M3:** the spend-threshold rule does not say what it applies to. §2.4 applies it to each Action's one-off; §2.4's own Kobo example and Figure 8 apply it to the change, or item. Splitting a change into Actions could slip under the threshold.
- Mechanics: `check_manifest.py` 3755 passed, 0 failed; `motivation_figures.py --check` reports 2 figures, none missing; the regenerated HTML is byte-identical to the committed one.
- Mermaid: 11 blocks were linted by reading against the 10.9.1 grammar, and no error was found. Nothing was parsed, because no package could be installed.
- Proportion: Parts 1–2 hold about 6,060 words including tables (about 3,700 words of prose outside tables), and 11 figures. That is on target.
- Regressions against C: none. C's N1–N4 are fixed in the main document and in worked-portfolios l.13 and l.591.

## 1. Owner fidelity

| Owner instruction | Verdict | Evidence |
|---|---|---|
| Part 1 covers today's architecture, its value and mechanics; Part 2 covers what is added, with what each construct brings and where it fits | Pass | §1.1–§1.5. §2.0 table and Figure 1. Each of §2.1–§2.8 has "What it brings" and "Where it fits", or equivalents |
| A Finding is the living result of evaluating a condition (Q-A1) | Pass | §1.3 l.99: "the output of the condition, not the condition itself", with identity, revisions and thread, all code-confirmed. The owner's rule is quoted verbatim (l.105), and the tolerance follows OD-3 |
| Users act on the context given and create and track Actions; the system never chooses or acts | Pass | §1.4 l.139; §2.4 steps 1–3; §2.6 l.460: "It never chooses, approves or creates an Action." Figures 5, 6, 7 and 8b agree |
| The plan is a first-class construct, integrated; one origin and at most one plan membership | Pass, with a note | §2.5 and Figure 6. There is a third, "legacy" origin (the opportunity study). It departs from "Finding or plan item", but it was the Architect's pushback in rev 16.2, and the owner agreed to those pushbacks ("Q-B1 yes, agree with the architect's pushbacks"). See L2 and I1 |
| The spend threshold and tolerance are configurable | Pass, but see M3 | §2.4 step 4: a Site or portfolio setting. §1.3 l.110: a tolerance per factor. §2.6: tolerances are set by role |
| The roles are sensible | Pass, with a note | Five roles (§2.6). No role declares non-money targets (L6) |
| Every change is justified on merit | Pass | §2.9 register. Each CH gives its shortfall with a file:line, and "what stays" is named |
| The view covers the whole business; every section serves the objective | Pass, with a note | §1.5 matrix and §2.3 table cover three verticals. §1.1 has no "Serves the objective" line, although the reading guide promises one in every section (L7) |
| Diagrams only where something changes; mini-grid used for demonstration | Pass | All figures except 8a show a change. 8a is the "before" half of a before/after pair, greyed as context. Every example is Kobo, Kisiwa or Mto |
| "Plan" means only the new construct (OD-6) | **Fail** | M1 and M2 |

## 2. The §10 brief, point by point

| # | Point | Result | Evidence |
|---|---|---|---|
| 1 | Existing before new; credit the value; never replacement | Pass | Part 1 comes first. §1.2 has a "Done well" column. §2.0 "What stays". Changes are framed as "extends" and "becomes one option generator" |
| 2 | Mechanism to value and differentiation | Pass | The "Serves the objective" lines (§1.2–§2.9). §2.0 states the differentiation as a hypothesis for the pilots, not as a fact |
| 3 | Change on merit, with code evidence; name what stays; no advocacy | Pass | §2.9. Each CH has a "Named change (Lx)" with a citation. The tone is stated, not argued (for example "is meant to answer", l.282) |
| 4 | Structure first; example illustrates; whole business; objective governs every part | Pass, with a note | §2.0 table and Figure 1 come before the specifics. Kobo is labelled as an illustration (l.41). §1.1 lacks its objective line (L7) |
| 5 | Person in the loop: who sees, decides, acts and tracks, and how each is recorded | Pass, with a note | §1.4 table (today), §2.4 steps 1–4, §2.6 roles and Figures 7 and 8b. The release rule's unit is unclear (M3), and so is the case where an Action released early is then left out (L5) |
| 6 | Precise concepts, one name per meaning | **Fail** | "Plan" has three or four meanings across the pack (M1, M2). The Finding definition is correct |
| 7 | Short and illustrated; diagrams only where something changes; detail in appendices | Pass | About 6,060 words in Parts 1–2 including tables. 11 figures. Detail is moved to the companions |
| 8 | The owner decides: context, example and default; push back; recommend | Pass, with a note | The decisions table records OD-1 to OD-6. Two owner-agreed pushbacks are still labelled "not settled by the owner" (L2). D15 is listed only as "pending", with no context or default here (I4) |

## 3. Accuracy against the code (independently verified)

Paths are under `backend/assetops_backend/` unless marked. Every file:line cited in the main document was also checked to exist and to fall within the file's length: 70 citations, all in range.

| # | Claim in the document | Verdict | Evidence |
|---|---|---|---|
| 1 | A Finding is unique per Site by its key, and names its analytic, mechanism, asset and the Finding it recurs after (§1.3) | Confirmed | `migrations/versions/0009_finding_store.py:36-46` (`finding_key`, `analytic_id`, `generator_asset_id`, `recurs_after_finding_id`), `:53` `UNIQUE (site_id, finding_key)` |
| 2 | Each revision has a typed transition, a claim, limitations and evidence digests | Confirmed, slightly understated | `0009:62-106` (transition CHECK at `:70-71`). The CHECK also admits `MERGED_INTO` and `BASIS_REFRESHED`, which the list omits (I2) |
| 3 | There are five stored Finding mechanisms; cold, EV and fuel use the same store | Confirmed | `outcomes/outcome_map.py:18-23`; `analytics/composition.py:118,128` (cold and EV workers on `PostgresFindingStore`); `analytics/adapters/postgres_finding_store.py:49` (fuel) |
| 4 | Dispatch raises a Finding for indeterminate running too | Confirmed | `analytics/dispatch.py:40` `FINDING_CLAIM_LEVELS = (CANDIDATE, INDETERMINATE)`, `:1070` |
| 5 | A Finding has no owner and no money; its link to an outcome is a fixed row | Confirmed | No owner or money column in `0009:33-60`; `outcome_map.py:17-23` |
| 6 | Thread states are action in hand, change applied, resolved and monitoring, recurred and withdrawn | Confirmed, slightly understated | `0042_chain_threads.py:67-68` also has OPEN, CLOSED and REOPENED; `chain/lifecycle.py:47-58` |
| 7 | Trial commands are recorded as a "SYSTEM demonstration" actor, and "no operator approval is recorded" | Confirmed | `actions/lifecycle.py:43-55`; `0016_action_store.py:131-132` `CHECK (actor_kind = 'SYSTEM')` |
| 8 | Work and domain writes refuse a user actor and need a server principal; by default none is injected | Confirmed | `work/model.py:284-287` (`WORK_USER_AUTH_REQUIRED`); `main.py:640-661` |
| 9 | No UI control creates domain actions or work cases | Confirmed | The frontend's only POSTs are accept, apply, operational entries, prices, uploads and setup (`frontend/src/sites/actionClient.ts:534,537`; `frontend/src/work/globalWorkClient.ts:316-319`) |
| 10 | Action origins: a trial Action has a Finding origin; a domain action has either a Finding or an opportunity; a thread occurrence has exactly one source | Confirmed | `0051_action_opportunity_origin.py:1-12` (`domain_action_one_origin`); `0042:47,53` `occurrence_one_source` |
| 11 | A domain action has an optional owner label and due date | Confirmed | `work/domain_action.py:301-309` |
| 12 | "No telemetry creates an Action or a case link" | Confirmed | `work/domain_intent.py:17` |
| 13 | Three verification families; an unknown family fails closed; the mill plan is frozen once, with no route | Confirmed | `actions/verification_families.py:502-516`, `:7-9` |
| 14 | VERIFY never supplies a verdict; the evaluator appends it | Confirmed | `actions/lifecycle.py:24-28` |
| 15 | The change's cost is fixed at 0; positive evidence must be simulated or authored | Confirmed | `actions/verification.py:1167` `InterventionCost(Fraction(0), …)`; `actions/verification_rules.py:688` |
| 16 | Credit is given only when Verified, with a stored priced total | Confirmed | `outcomes/credit.py:57-73` |
| 17 | Money sources: possible extra fuel cost is Modelled, from 0 to a bound; `recorded_amount@1` "returns no money with NO_RECORDS, always" | Confirmed | `financials/fuel_cost.py:22`; `chain/strategies/recorded_amount.py:1-11` |
| 18 | Six objectives, judged Met, Missed, On pace or Behind pace; system-declared "not a customer target" | Confirmed | `outcomes/objectives.py:14-18,57-143`; `objectives/model.py:21-24` |
| 19 | "No money targets" (L3); "Six operational objectives" (§1.2) | Overstated | `outcomes/objectives.py:56,71`: `energy_cost_per_km` is a VALUE measure "and the only one with a currency". It is declarable, though never judged, because EV-2 has no reading (`site_outcomes/ev.py:108-109`). See L4 |
| 20 | No budget or crew construct in the backend or schema; the only "budget" hits are frontend layout code | Confirmed | `grep -ri budget` and `grep -ri crew` over `backend/assetops_backend` and `backend/migrations` return nothing. Frontend hits are layout comments (`MiniPerformance.tsx:226`, `SiteSingleLineDiagram.tsx:208`) |
| 21 | Intake is first-write-wins and refuses late intervals | Confirmed | `evidence/service.py:485-492` (duplicate or conflict); `reading_upload/service.py:244-248` `ALREADY_RECORDED` |
| 22 | The schema has the HUMAN-author pattern; the API refuses a human | Confirmed | `0010_financial_assumptions.py:57-78`; `financial_api.py:208-212` `HUMAN_PRINCIPAL_REQUIRED` |
| 23 | The mini-grid board reads one day (L7) | Confirmed | `site_outcomes/read.py:681-682` (`WINDOW_BASIS_DAY`) |
| 24 | The reserve trial "does not predict … any saving" | Confirmed | `actions/reserve_trial.py:42-45` |
| 25 | Trials have no owner or due date | Confirmed | `estate/coverage.py:530` `"owner": None, "due_at": None` |
| 26 | The study shows headroom, with demand and collection UNVERIFIED | Confirmed | `mini_decisions/opportunities.py:400-401` |

## 4. Findings

### M1 · Medium · `worked-portfolios.md`: "Plan" used for targets, against OD-6

Quoted:
- l.13: "Observe reads each Site's outcome up from its factors, plan against actual."
- l.36: "| Plan | the operator's monthly plan line, from its plan spreadsheet: a target the operator declares, not a record |"
- l.43: "| Plan limit | the budget, crew visits, horizon and service rules the operator sets |"
- l.76: "**Plan against actual, per factor.**"
- l.78, 97, 129, 345, 358, 372, 488: a "Plan" column. l.146 and l.382: "Plan contribution". l.125, 127, 389, 497 and 536: "plan 5,600", "(plan 26,040)" and similar.
- The same file, l.261, 438 and 589: "#### Plan: proposed by the system, decided by people".

**Problem.** The owner agreed (OD-6) that "plan" means only the new construct and that B2 uses "targets and budget lines". The main document's decisions table says OD-6 is applied in "§2.2, §2.5, figures" (l.629). The companion still uses "Plan" for targets and "Plan limit" for constraints, in the same sections where the plan construct appears. At Kobo, a reader meets "Plan 700 L" and "the plan's spend 3,750" a page apart.

**Why it matters.** This breaks an owner decision and §10 point 6 in the document that carries the worked examples the owner will read.

**Fix.** Wording only, and the checker markers do not change:
- "Plan" column → "Target";
- "plan against actual" → "target against actual";
- "Plan contribution" → "Target contribution";
- "Plan limit" → "Limit (set by the operator)";
- the l.36 row → "Target | the operator's monthly target or budget line …".

Leave "The plan and its limits" (l.263, 440, 591) as it is.

### M2 · Medium · `layer4-transformation-design.md` (and the HTML): other meanings of "plan" remain

Quoted:
- §1.2 l.90: "with frozen plans, comparability and guardrails".
- §1.4 l.127: "The mill plan is frozen once"; l.128: "freezes the verification plan".
- Figure 8a l.510: "freezes the verification plan".
- §2.7 l.543: "*Stays:* the plan freeze, comparability, guardrails".
- Figure 9 l.551: "telemetry, frozen plan".
- §1.5 l.150: "maintenance plans"; §2.6 l.448: "as it already is for maintenance plans".
- HTML Figure 3 (`motivation_figures.py:189`): "Actual against plan", tagged "stays as operational targets".

**Problem.**
- §2.7 sits right after §2.5, where the plan item carries a "frozen prediction". "The plan freeze" there means the verification plan, but it reads as the new plan.
- The Figure 3 label is accurate: today's Assure line is literally "Actual against plan" (`site_outcomes/mini.py:692,697`). The document keeps that label ("stays"), however, beside a new on-screen plan. It does not say the label will be renamed.

**Why it matters.** OD-6 exists to give "plan" one meaning. The main document now gives it four: the new plan, the verification plan, the maintenance plan, and the target line on screen.

**Fix.**
- Say "verification protocol" (or "frozen verification design"): "the protocol freeze", "frozen protocol".
- Say "maintenance schedules", while noting that the code's name is "plan".
- In Figure 3 and §2.2, add that the Assure label "Actual against plan" is renamed "Actual against target" under CH5. Add one row to §2.8 or §2.9 for it.

### M3 · Medium · §2.4 step 4 l.369, Figure 8b l.529, Figure 8 caption l.536: what the spend threshold applies to

Quoted:
- l.369: "An Action is released when it is created if **its** one-off spend is at or below the spend threshold …"
- l.369: "Kobo's stop-threshold **change** spends 90.00 … Under a threshold of at least that amount it goes ahead at once".
- Figure 8b l.528: "creates the setting change and a supervised trial" (two Actions); l.529: "the one-off is above the spend threshold, so the **Actions** wait".

**Problem.** The rule is stated per Action, but the example and Figure 8 apply it to the item (the 90.00 is 60.00 of vendor reconfiguration plus 30.00 of supervision; `worked-portfolios.md` l.167). Take a threshold of 75:
- applied per Action, both Actions (60 and 30) are released at once;
- applied per item, both wait.

Read per Action, the rule also lets any change be split into Actions that are each below the threshold, which defeats the owner's setting (OD-2).

**Why it matters.** The owner set this rule to decide what needs the executive's approval. The document must say what it is applied to.

**Fix.** State it per plan item: "An Action is released at creation if its plan item's total one-off spend is at or below the spend threshold …". Alternatively, state it per Action and add an anti-splitting clause. Then align step 4, Figure 6's edge label and the Figure 8 caption.

### L1 · Low · companions: stale revision labels and broken cross-references

- `worked-portfolios.md` l.3 and l.7: "rev 16.2". l.9: "The roles are the five of design §2.5". The roles are in §2.6.
- `design-appendix.md` l.3 and l.5: "rev 16.2". §4, the change log, has no rev 16.3 entry, although the main document's Status (l.5) sends readers there for the revision history.
- `design-appendix.md` §2: "§2.6: three verdicts" should be §2.7. "§2.3: the pilot asks per vertical" should be appendix §5, where they moved in rev 16.2. "§2.1 and §2.2 … against plan" also falls under M1.
- Fix: update the labels and references, and add a rev 16.3 change-log entry (OD-4 to OD-6, and the brief applied).

### L2 · Low · Decisions l.631 and §2.5 l.427: owner-agreed pushbacks labelled "not settled by the owner"

- Quoted: "**Architect's call, not settled by the owner:** the legacy opportunity-study origin, and the reading that a Finding-origin Action always joins the plan but waits for approval only above the threshold".
- Rev 16.2 put exactly these to the owner, as "the legacy opportunity origin and threshold reading added to the coordinator's refinement", under "Default, awaiting the owner", together with Refinements 1 and 2. The owner answered "Q-B1 yes, agree with the architect's pushbacks". Rev 16.3 records Refinements 1 and 2 as OD-5 and OD-6, but keeps these two as unsettled.
- Fix: record them as settled (OD-7, or fold them into OD-1 and OD-2). If the Architect reads "pushbacks" more narrowly, say why.

### L3 · Low · Figure 8a l.510: "UI->>API: VERIFY"

- The UI sends no VERIFY. `frontend/src/sites/actionClient.ts` issues only accept (`:534`) and apply (`:537`), and the frontend only reads the verification plan.
- VERIFY is a SYSTEM-demonstration call (`actions/lifecycle.py:26-28`). The mill freeze has no route at all (`verification_families.py:7-9`). §1.4 l.128 gets this right ("System").
- Also, "M->>UI: Apply from a chosen time" goes straight to "API->>S", with no UI-to-API message.
- Fix: draw VERIFY from a "Server (demo)" participant, or from `API->>S`, and add `UI->>API: POST actions/{id}/apply`.

### L4 · Low · L3 l.160 and §1.2 l.92: "no money targets", "six operational objectives"

- `energy_cost_per_km` is a declarable money objective (`outcomes/objectives.py:56,71`). It is never judged, because EV-2 has no reading.
- §1.5 l.152 says this correctly ("a cost-per-km target, never judged"). L3 and §1.2 do not.
- Fix: "one money objective (EV energy cost per km) exists but is never judged; there is no budget and no money bridge".

### L5 · Low · §2.4 step 4 against §2.5 OD-4 (l.397): an Action released early, then left out

- Below the threshold, an Action is released at creation. If the executive then approves a plan that leaves out its item, OD-4 says it "is not released", but it already has been.
- `worked-portfolios.md` l.591 also says all Metro Actions are released "once the executive approves the plan". That includes the 90.00 Kasarani cover, which could be under the threshold.
- Fix: one sentence. For example: a released Action whose item the approved plan drops is returned to its creator to continue, revise or withdraw. Or: early release is final, and the item stays in the plan.

### L6 · Low · §2.6 roles table l.452-458: no role declares targets

- §2.2 l.284 says "the operator declares targets and budget lines, and the declarer is recorded (CH2)".
- The roles table gives budget lines to finance and tolerances to finance and operations. No role declares the non-money factor targets, which replace today's SYSTEM declarer: availability, dawn charge, departures.
- Fix: add "declares operational targets" to the operations manager, and "money targets" to finance or the executive.

### L7 · Low · §1.1: no "Serves the objective" line

- The reading guide (l.37) says: "Each section says how it serves that objective, in a line marked *Serves the objective*". §1.1 is the only numbered section without one.
- Fix: one line, for example "*Serves the objective:* this is the credibility executives buy; Part 2 adds the money on top of it."

### L8 · Low · §2.5 l.383: "(brief L1.3)" does not resolve

- No file in the pack is named as "the brief". "L1.3" is found only in `REVIEW.md`.
- Fix: name the file and section, or drop the reference.

### I1 · Info · The third, legacy Action origin

§2.5 adds a third origin (the opportunity study) to the coordinator's "one origin: Finding or plan item". This is deliberate, owner-agreed (see L2), and limited to existing mill-shift Actions ("no new Action takes the legacy origin", as stated in rev 16.2). It is not a fidelity breach. Restating "no new Action takes it" in §2.5 would make that limit visible again; rev 16.3's wording ("New demand work goes through …") implies it.

### I2 · Info · Lists of Finding transitions and thread states omit some values

Missing are `MERGED_INTO` and `BASIS_REFRESHED` (`0009:70-71`), and OPEN, CLOSED and REOPENED (`0042:67-68`). The lists are illustrative and harmless.

### I3 · Info · Figure 7 marks "Raise Findings, prepare decisions, check the plan" as new

Raising Findings exists today. Splitting it out, kept as "stays", would match the legend.

### I4 · Info · D15 "pending" with no context

Line 616 lists D15 as pending, with no context or default here. It lives in the roadmap §6. A pointer would satisfy §10 point 8.

### I5 · Info · Proportion

Parts 1–2: about 6,060 words including tables, and 11 figures, likely 13–14 rendered pages. This is in range. §1.2's table and §2.9's register partly repeat each other's citations; if anything is trimmed, trim there.

## 5. Consistency

- **Proposes, chooses, creates, approves, releases, records.** The text (§2.4 steps 1–4, §2.5, §2.6 l.460), Figures 1, 5, 6, 7 and 8b, and both companions agree:
  - the system proposes and checks;
  - the accountable role chooses and creates;
  - the executive approves;
  - approval releases spend above the threshold;
  - each act is recorded under the person's name.

  The only gaps are M3, L5 and L6.
- **Figures.**
  - Kobo: 1,445 / 883 / −562.00, with effects −412.50, −150.00, −37.50 and +38.00; 330 L and 120 L; 3,458 / 3,180 / 278; option +250.50 a month, 2,916.00, one-off 90.00, 210 L, 150 kWh, 4 of 61.
  - Lakeside: 21,700 / 21,445 / 21,650; 9,688 / 8,870; 8,245 / 7,490; 1,443 / 2,295.
  - These agree across the main document, the HTML and `worked-portfolios.md`, and are checked by `check_manifest.py`, all passing.
  - The 125-against-15 hours trade in §2.5 matches `worked-portfolios.md` l.327.
- **"Plan".** It fails in both the companion (M1) and the main document (M2).
- **Cross-references.** In the main document, every § and companion reference resolves except "brief L1.3" (L8). In the companions, see L1.

## 6. Mermaid (linted by reading; not parsed)

No package could be installed, so no parser was run. All 11 blocks were read against the Mermaid 10.9.1 grammar. The HTML loads `mermaid@10.9.1` and has 9 Mermaid blocks; Figures 2 and 3 are SVG.
- Flowcharts: Figures 1, 2, 3, 4, 5, 6, 7, 9 and 10. Quoted labels, `<br/>`, `:::class` on inline nodes, `{{…}}`, `[(…)]`, `(["…"])`, `(("…"))` and `A & B & C --> D` all look correct. Edges to a subgraph id (`--> AD`) are valid. No node is named `end`, and no `%%` appears at the start of a line. Dotted labelled edges use `-. "text" .->`, which 10.x accepts.
- Sequence diagrams: Figures 8a and 8b. `actor` and `participant … as …` look correct. Message texts contain no `;` or `#`.
- No syntax error was found. The parse is unverified.

## 7. Mechanics (run from the pack folder)

```
$ python3 check_manifest.py            -> 3755 checks passed, 0 failed   (exit 0)
$ python3 motivation_figures.py --check -> 2 figures built; markers ['factor-structure', 'plan-against-actual']; missing []; unused []   (exit 0)
$ python3 render_design_html.py layer4-transformation-design.md <scratch>/out.html -> ok
$ cmp <scratch>/out.html layer4-transformation-design.html -> identical
```

The working tree was clean after the runs.

## 8. Could not verify

- Mermaid parsing: no package could be installed.
- How the HTML renders in a browser: no port was used.
- The Part 1 claims about screens (six Portfolio tabs, the four category cards) were not traced through the frontend. I checked only the OutcomeBoard columns (`OutcomeBoard.tsx:42-48`, `:270`).

## 9. Residual risk the pack does not name

- **The threshold as a control.** Even when M3 is fixed, a threshold on one-off spend says nothing about crew visits. A zero-spend Action that uses a crew visit is released at creation (l.369: "and the plan still fits its budget and crew visits"). Who checks that fit, and when, before release, is the system's job. The pack does not say what happens when two Actions under the threshold, created at once, together overrun the crew visits.
- **Renaming "plan" in the code.** The code uses `plan` for verification plans, `plan_due` for maintenance, and `actual_against_plan` for the Assure line. The new construct will need a code name, such as `portfolio_plan`, that cannot collide with these. The slices should say so.

## 10. Regression check against reviews B and C (read after the findings above)

C's N1–N4 are all fixed:
- `worked-portfolios.md` l.13 and l.591: the managers choose and create, and approval releases;
- §2.4 step 4: the stop-threshold change is in the plan, at 90.00;
- §2.4 step 2: the accountable role is defined by role;
- §1.4 l.127: the mill row states its limits.

No earlier finding returns. M1 and M2 are new: they come from OD-6 itself, the owner's decision on rev 16.2 that "plan" has one meaning.
