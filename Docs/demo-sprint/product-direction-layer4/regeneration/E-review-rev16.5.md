# Layer 4 regeneration, Phase E: independent review of rev 16.5

Reviewer: fresh Claude reviewer (did not author the work). Branch `task/layer4-design-regeneration`, head `2ff304307`. Read-only except this file.
Under review: `layer4-transformation-design.md` and `.html` (rev 16.5), `worked-portfolios.md`, `design-appendix.md`.
Standard: `.agent/owner-design-regeneration-request-2026-11-19.md` (all of it, including OD-1 to OD-9 and Q-A1/Q-A2) and `.agent/RULES-main-2026-11-19.md` §10 (all eight points). The review is judged as if this document will be the source for every document pack.
Earlier reviews (`regeneration/A`–`D`) were opened only after the findings below were formed, and only to check for regressions.

## Summary

- **Verdict: REVISE.** The core is sound and faithful: the Finding as a living result, the person in the loop, the plan with one origin and at most one membership, the configurable threshold and tolerance, and the OD-9 lanes are all present and largely accurate. Five Medium findings would mislead the owner or a derived document, so the version is not yet fit to regenerate the packs from.
- **Counts:** High 0 · Medium 5 · Low 8 · Info 5.
- **M1:** the HTML drops OD-8. A blank line in the Markdown decisions table splits it, so OD-7 becomes a header row and the OD-8 row is consumed as the separator.
- **M2:** `worked-portfolios.md` still uses "plan" for targets in five places, against OD-6. This is a partial regression of review D's M1, which the change log records as fixed.
- **M3:** Figure 10's caption has lane B reading "against target", and the −562.00 gap appearing at the join, before targets and the bridge (step 5) exist. The 700 L target is itself a budget line, which is a lane A record.
- **M4:** "Action" is never defined across today's three carriers (trial `action`, `domain_action`, work case). The membership of a spending Finding-origin Action with no decision behind it is also undefined.
- **M5:** the schema already enforces one origin per domain Action, and it forces every MINI domain Action onto the opportunity origin (`0051:73-79`). OD-7 and the plan-item origin need that constraint changed, and the change register does not say so.
- Mechanics: `check_manifest.py` 3761 passed, 0 failed (exit 0). `motivation_figures.py --check` built 2 figures with none missing (exit 0). The re-rendered HTML is byte-identical to the committed file (`cmp`).
- Code: 29 claims checked. 26 are confirmed, 2 are confirmed but slightly understated, and 1 is materially understated (M5).

## 1. The §10 brief and the owner's specific points

| # | Point | Result | Evidence |
|---|---|---|---|
| 1 | Existing before new; credit its value; never a replacement | Pass | Part 1 (§1.1–§1.5) comes before Part 2. §1.2 has a "Done well" column, and §2.0 starts with "What stays". The outcome map "becomes rows of this structure… removed only after a parity test passes" (l.250), which is a named change, not a replacement. The credit for today's one-origin constraint is missing (M5) |
| 2 | Mechanism to value and differentiation | Pass | Every section from §1.1 to §2.9 has a *Serves the objective* line. §2.0 calls the differentiation "the hypothesis the pilots must confirm" (l.182), which is honest rather than advocacy |
| 3 | Change on merit, with code evidence; name what stays | Pass, with a gap | The §2.9 register names a shortfall and a citation for each change, and every CH section has "Stays". The origin constraint the plan item must change is missing (M5) |
| 4 | Structure first; example illustrates; whole business; **the overall objective governs every part** | Pass | §2.0 and Figure 1 come before the specifics. "Kobo illustrates the design; it never defines it" (l.28, l.41). §1.5 covers the whole business across three verticals. The objective is stated once (l.37), and each section carries its line |
| 5 | Person in the loop; **the system never chooses or acts** | Pass, with notes | "The system never acts on its own" (l.141, code-confirmed). "It never chooses, approves or creates an Action" (l.462). The §2.4 steps 1–4, the roles table and Figures 5, 7 and 8b agree. Notes: L4 (whether a person can choose a Rejected option) and M4 (what counts as an Action) |
| 5a | **A Finding is a living result**, under the owner's rule | Pass | §1.3 l.101: "the output of the condition, not the condition itself", with identity, revisions and thread confirmed in code. The owner's rule is quoted verbatim (l.107). Kobo's +38.00 is "favourable, so it is **not** a Finding" (l.263) |
| 5b | **The plan is first-class: one origin, at most one membership** | Pass, with gaps | The §2.5 table and Figure 6 match the coordinator's refinement word for word, and OD-7's legacy third origin is marked. The rule is not closed over today's carriers or the no-decision path (M4), and the code constraint is not named (M5) |
| 5c | **Configurable threshold and tolerance** | Pass, with a note | OD-2 is a Site or portfolio setting applied per whole change (§2.4 step 4). OD-3 is a tolerance per factor (§1.3 l.112), and the roles table says who sets each. Their precedence and defaults are undefined (L3) |
| 6 | **One name per meaning**; "plan" means only the new construct | **Fail** | The main document is clean, and its remaining code uses are named (l.433). `worked-portfolios.md` still uses "plan" for targets at l.127, l.491, l.503, l.523 and l.529 (M2) |
| 6a | **Delivery order in Figure 10 (OD-9) and the Architect's note** | Pass in shape; caption wrong | The step order and the two lanes match the coordinator's text exactly (l.596-599, l.611-628). The note (l.603-605) gives a reasoned refinement and a caution, as the owner invited ("pushbacks are welcome with reason"). The caption's dependency is wrong (M3), the step numbers drift (L1), and the refinement is not listed as an open call (L2) |
| 7 | Short and illustrated; diagrams only where something changes | Pass | Parts 1–2 hold 6,527 words including tables (4,101 of prose, 2,426 in tables), within the 6,000–6,500 target. There are 11 Mermaid blocks; 8a is the greyed "before" half of a pair. Detail lives in the companions |
| 8 | The owner decides: context, example and default; push back; recommend | Pass, with a note | The decisions table covers Q-A1/Q-A2 and OD-1 to OD-9, with the owner's words. The Architect's calls are listed with Kobo's 90.00 example. D15 points to the roadmap §6. In the HTML, OD-8 is missing (M1), and one open call is not listed (L2) |

## 2. Accuracy against the code (independently verified, own sample)

Paths are under `backend/assetops_backend/` unless marked; migrations are in `backend/migrations/versions/`.

| # | Claim in the document | Verdict | Evidence |
|---|---|---|---|
| 1 | The evidence ledger carries the source, unit, quality, live or simulated flag and an envelope hash (§1.2) | Confirmed | `0005_evidence_ledger.py:161-197` (`quality`, `original_unit`, `envelope_sha256`, `source_mode IN ('LIVE','SIMULATED')`) |
| 2 | A Finding is unique per Site by its key and names its analytic, mechanism, asset and the Finding it recurs after (§1.3) | Confirmed | `0009_finding_store.py:33-60`; `UNIQUE (site_id, finding_key)` |
| 3 | Revisions have typed transitions, a claim, limitations and digests (§1.3) | Confirmed, slightly understated | `0009:62-106`. The CHECK also admits `MERGED_INTO` and `BASIS_REFRESHED` (I5) |
| 4 | The thread states (§1.3) | Confirmed, slightly understated | `0042_chain_threads.py:66-67` also has `OPEN`, `CLOSED` and `REOPENED` |
| 5 | A Finding's only link to an outcome is a fixed mechanism row (§1.3, CH1) | Confirmed | `outcomes/outcome_map.py:17-23` (`ENTRIES`, five Finding mechanisms) |
| 6 | MOVES/CHECKED contributions, with no quantity between signal and outcome (L1) | Confirmed | `outcome_map.py:149-180` |
| 7 | Dispatch raises a Finding for indeterminate running too (§1.3) | Confirmed | `analytics/dispatch.py:40` `FINDING_CLAIM_LEVELS = (CANDIDATE, INDETERMINATE)`; `:1070` |
| 8 | Trial commands are recorded as a "SYSTEM demonstration"; "no operator approval is recorded" (§1.4, G1) | Confirmed | `actions/lifecycle.py:43-58`; `0016_action_store.py:131` `CHECK (actor_kind = 'SYSTEM')` |
| 9 | The VERIFY command never supplies a verdict; the evaluator appends it (§1.4) | Confirmed | `actions/lifecycle.py:24-28` |
| 10 | Work writes refuse a user actor (G1) | Confirmed | `work/model.py:284-285` `WORK_USER_AUTH_REQUIRED` |
| 11 | "No telemetry creates an Action or a case link" (§1.4) | Confirmed | `work/domain_intent.py:17` |
| 12 | A domain Action has an optional owner label and due date; a work case has an assignee (§1.4) | Confirmed | `work/domain_action.py:301-309`; `work/model.py:329` |
| 13 | Trials have no owner or due date (G1) | Confirmed | `estate/coverage.py:530` `"owner": None, "due_at": None` |
| 14 | Objectives are system-declared, "not a customer target" (L3) | Confirmed | `objectives/model.py:21-24` |
| 15 | Six objectives; five operational, one money objective (EV energy cost per km) never judged (§1.2) | Confirmed | `outcomes/objectives.py:56-72` (six `_m`, one `VALUE`); `site_outcomes/ev.py:105-107` "EV-2 has no reading"; `judge` returns `NOT_JUDGED` without a reading (`objectives.py:112-114`) |
| 16 | The reserve trial "does not predict … any saving" (L5) | Confirmed | `actions/reserve_trial.py:37`, `:42-45` |
| 17 | Verification fixes the change's cost at 0 (L6) | Confirmed | `actions/verification.py:1167` `InterventionCost(Fraction(0), …)` |
| 18 | Positive evidence must be simulated or authored (L6) | Confirmed | `actions/verification_rules.py:688` `POSITIVE_SOURCE_CLASSES` |
| 19 | Three mini-grid families; an unknown family fails closed (§1.2) | Confirmed | `actions/verification_families.py:502-516` (reserve, midday, fuel; `VERIFICATION_FAMILY_UNSUPPORTED`) |
| 20 | The mill baseline is frozen once, at story time, with no route; the mill has no guardrails (§1.4, appendix §1) | Confirmed | `verification_families.py:7-9`; `:22` `guardrails = {}` |
| 21 | Intake is first-write-wins, and late intervals are refused (§2.3) | Confirmed | `evidence/service.py:484-492` (a different digest becomes a `Conflict`, not an overwrite); `reading_upload/service.py:244-248` `ALREADY_RECORDED` |
| 22 | The schema needs an author for a HUMAN actor; the API refuses one (CH2) | Confirmed | `0010_financial_assumptions.py:57-78`; `financial_api.py:208-211` `HUMAN_PRINCIPAL_REQUIRED` |
| 23 | `recorded_amount@1` "returns no money with NO_RECORDS, always" (§1.5) | Confirmed | `chain/strategies/recorded_amount.py:1` |
| 24 | There is no budget, crew or cross-Site construct in the backend or schema; the only "budget" hits are frontend layout code (§2.5) | Confirmed | `grep -rniw budget` and `grep -rni crew` over `backend/assetops_backend` and `backend/migrations` return nothing. The frontend hits are layout comments (`GlobalMaintenance.tsx:387`, `MiniPerformance.tsx:226`, `:1444`) |
| 25 | The board's columns, including "Must not harm" (§1.2) | Confirmed | `frontend/src/sites/OutcomeBoard.tsx:42-48` (five columns); `:270` "Must not harm" |
| 26 | "never a value ranking" (§1.2) | Confirmed | `estate/placement.py:5` |
| 27 | The Optimize card for a mini-grid reads one day (L7) | Confirmed | `site_outcomes/read.py:676-683` (`WINDOW_BASIS_DAY` for MINI) |
| 28 | The "Actual against plan" label (§2.8) | Confirmed | `site_outcomes/mini.py:692` |
| 29 | The Action carries its opportunity origin (§1.4); there is one origin per Action, presented as the coordinator's new rule (§2.5, §2.9) | **Understated** | `0051_action_opportunity_origin.py:73-79`: `domain_action_one_origin` already enforces exactly one origin (Finding XOR opportunity), and `domain_action_mini_origin` is `CHECK ((domain = 'MINI') = (origin_opportunity_id IS NOT NULL))`. `0057_fuel_verification.py:4-6` keeps both. See M5 |

Not verified: "No UI control creates them yet" (§1.4, work and domain Actions), the six Portfolio tabs, and the `frontend/src/estate/actionIndex.tsx:38-160` range.

## 3. Findings

### M1 · Medium · Decisions table, l.653-655 (Markdown) and the HTML: OD-8 is missing from the HTML

Quoted (Markdown):
```
| OD-6 | "Plan" means only the new construct; … | §2.2, §2.5, figures |

| OD-7 | Today's opportunity-study origin stays as a legacy third origin … | §2.5 |
| OD-8 | A Finding-origin Action that spends always joins the plan … | §2.4, §2.5 |
| OD-9 | Delivery order: …
```
**Evidence.** The blank line at l.654 ends the table. The renderer starts a second table, takes OD-7 as its header row and OD-8 as the alignment row, and so drops OD-8. The committed HTML shows `<table><thead><tr><th>OD-7</th>…</thead><tbody><tr><td>OD-9</td>`, with no OD-8 row anywhere in the table.
**Why it matters.** The owner reads the HTML. OD-8 is one of the two decisions the owner confirmed explicitly for this revision ("OD-7 and OD-8 yes"), and OD-7 is shown as a header.
**Fix.** Delete the blank line at l.654 and re-render. Also add a renderer check that a table row starting `| OD-` never begins a table.

### M2 · Medium · `worked-portfolios.md`: "plan" still means target (OD-6), a partial regression of D-M1

Quoted:
- l.127: "The plan states only billed kWh, so the comparison starts at the meter".
- l.491: "of which at peak (30% planned, 55% actual)".
- l.503: "**October: on plan.**"
- l.523: "**Plan: a stated total only.** Ruiru's target is 13,100.00".
- l.529: a column headed "Plan cost to serve".
**Evidence.** OD-6 says "Plan" means only the new construct. `design-appendix.md` l.70-71 records for rev 16.4 that "targets and budget lines replace it in the worked portfolios". The same file uses "#### Plan: proposed by the system" (l.261, l.438, l.589) and "listed beside the plan" (l.246, l.573) for the construct.
**Why it matters.** Derived documents copy the worked examples. A reader meets "Plan cost to serve 19,540.80" and "The plan… Spend 1,590.00" in the same section.
**Fix.** l.127 "The target states only…", l.491 "(30% targeted…)", l.503 "October: on target.", l.523 "Target: a stated total only.", l.529 "Target cost to serve". Sweep the file for `plan` outside the construct's headings. The `fig:` marker keys may keep `.plan.` (I4).

### M3 · Medium · Figure 10 caption l.630 (OD-9): lane B reads "against target" before targets exist

Quoted: "While lane A builds the emulators, lane B already reads Kobo's diesel litres against target, 1,180 L against 700 L. … Once the billing and collection emulators pass the contract test, the lanes join. The contribution gap of −562.00 … then appear[s]".
**Evidence.** In the figure and in l.599, targets and the bridge (B2) are step 5, after the join (`J --> T`). Lane B (3B) holds "factors, Findings pinned, structure observer", with no targets. Kobo's 700 L is a budget line (`worked-portfolios.md` l.36: "the operator's monthly target or budget line, from its budget spreadsheet"), and `BUDGET_LINE` is a lane A record (Figure 4). Today's objectives hold no litre target (`outcomes/objectives.py:56-72`). The −562.00 is target against actual, so it needs step 5, not just the join.
**Why it matters.** This is the figure the owner has just approved (OD-9), and the roadmap and phase plan will be derived from it. As written, it promises a target-against-actual demonstration from lane B that the order does not deliver.
**Fix.** Either say that lane B reads litres and the split of generator running (actual only), and that the target and the −562.00 appear at step 5. Or, if the Architect wants operational targets earlier, move "operational targets on today's leaves" into lane B in the figure and in the text. That would itself be a change to OD-9 for the owner to confirm.

### M4 · Medium · §2.4–§2.6, the §2.5 table, §2.9: "Action" is not defined, and the origin and membership rule is not closed

Quoted: "Actions, domain actions, work cases (stay)" (Figure 1); "Every Action records its creator, owner, due date and origin" (l.448); "A Finding-origin Action that spends shared budget or crew joins the period's plan through the reactive item for its chosen option" (l.395).
**Evidence.** Today there are three carriers: the trial `action` (Finding origin, `estate/coverage.py:528`), `domain_action` (one origin, `0051:73-77`) and the work case (no origin; linked to a Finding). "Action" is not in "Words used here" (l.44-54). The membership rule assumes a chosen option. A cold or EV domain Action raised against a Finding with no declared lever, and so no decision (l.345), that spends crew time has no reactive item to join.
**Why it matters.** OD-1 and OD-8 are the centre of the plan construct. A spec derived from this must guess whether work cases carry an origin and a membership, and where a spending Action with no decision is counted.
**Fix.** Add "Action" to the words list, naming the carriers it covers (and whether work cases take an origin or inherit one through their link). Add one sentence for the case with no decision: for example, a person's Action against a Finding with no decision creates its own reactive item.

### M5 · Medium · §1.4 l.129, §2.5 l.395, §2.9 l.591: the schema's origin constraints are not credited or changed

Quoted: "The Action carries its opportunity origin (`0051_action_opportunity_origin.py:1-12`)"; "Origin, exactly one … (coordinator's refinement, adopted)"; OD-7 "legacy third origin for existing mill-shift Actions only … no new Action takes it" (l.428).
**Evidence.** `0051_action_opportunity_origin.py:73-77` already enforces exactly one origin on `domain_action` (`domain_action_one_origin`: Finding XOR opportunity). `:78-79` adds `domain_action_mini_origin CHECK ((domain = 'MINI') = (origin_opportunity_id IS NOT NULL))`, so every MINI domain Action must take the opportunity origin. `0057_fuel_verification.py:4-6` leaves both unchanged, which is why fuel work uses a separate `FUEL_BALANCE` domain.
**Why it matters.** §10 points 1 and 3 ask for the existing behaviour to be credited, and every change to be named with code evidence. Today's one-origin rule is existing value the plan builds on. "No new Action takes it" (OD-7) and a plan-item origin both require dropping or reshaping `domain_action_mini_origin` and widening `domain_action_one_origin`. The register's Actions row names neither, so a derived migration plan would miss them.
**Fix.** In §1.4 or §1.3, credit the existing one-origin check. In the §2.9 Actions row, name the change: widen `domain_action_one_origin` to a third arm, the plan item, and replace `domain_action_mini_origin` with a rule that admits no new opportunity origin. Cite `0051:73-79`.

### L1 · Low · §2.9 l.597-601 against Figure 10: the step numbers drift

The text numbers "Agree the canonical format…" as step 1. The figure numbers it 2, after "1 Correct the last-day figure (CH5)". The text then adds "The CH5 quick fix still comes first". Use one numbering, for example by starting the text list with the CH5 fix.

### L2 · Low · §2.5 l.431 and Decisions l.659-661: an open point is not listed

"The Architect's calls that remain are the per-change threshold … and the rule for an Action already released." The delivery-order refinement ("cost-side decisions do not wait for the join", l.604) is also an Architect's call that the owner has not settled. OD-9 says it is "for the owner", yet it is drawn into Figure 10 (`LB --> D`) and missing from both lists. Add it, with its default, to "Architect's calls, not settled by the owner".

### L3 · Low · §2.4 step 4 and §1.3 l.112: precedence and defaults are not defined

OD-2 says "a Site or portfolio setting" but not which wins when both are set. The tolerance has no stated default when it is unset (raise every adverse deviation, or none?). The threshold's unset case is defined ("or none set, both wait"). State the precedence and the tolerance default.

### L4 · Low · §2.6 l.462 against "Words used here" l.49: can a person choose a Rejected option?

"rejects options that break a hard bound" sits beside "Disposition … is a recommendation, never a choice". Say whether a hard-bound rejection removes the option from the person's choice, or can be overridden with a recorded reason.

### L5 · Low · `worked-portfolios.md` l.13 and l.263 against design §2.4–§2.5: two recommendation mechanisms

The companion recommends "one option per decision, found by one search over all the decisions so that the recommended set fits the budget". The design marks one Recommended per decision (§2.4 step 1), then checks the chosen set and proposes the nearest fit (§2.5 l.399). State in the design that the recommendation itself comes from the portfolio search, or align the companion.

### L6 · Low · `design-appendix.md` l.63-81: the change log continues under §5

The rev 16.3, 16.4 and 16.5 entries sit under "## 5. Minimum pilot asks per vertical", after the pilot-ask bullets. Move them into §4.

### L7 · Low · Figure 7 l.487-493: actors share the "new" colour

`classDef actor` and `classDef new` are the same blue, while the caption says "Blue is new". Give the actors a neutral style.

### L8 · Low · Undefined terms

"Lever" (l.345, "a declared lever") and "Calibration replays (K, M, E)" (Figure 10) are used but not defined. Only "Replay K" is defined (l.53).

### I1 · Info · Mechanics

`python3 check_manifest.py` printed "3761 checks passed, 0 failed" (exit 0). `python3 motivation_figures.py --check` printed "2 figures built; markers ['factor-structure', 'plan-against-actual']; missing []; unused []" (exit 0). `python3 render_design_html.py layer4-transformation-design.md <scratch>.html` printed "ok", and `cmp` with `layer4-transformation-design.html` found it identical. The working tree was unchanged afterwards.

### I2 · Info · Mermaid

All 11 blocks (Figures 1–7, 8a, 8b, 9 and 10) were linted by reading them against the 10.9.1 flowchart and sequence grammars. **None was parsed**, because no package could be installed. I found no error. Every label containing punctuation is quoted, no node id is a reserved word, and no sequence message contains `;` or `#`. The least common form used is a quoted label on a dotted edge (`-. "text" .->`, Figure 6 l.412 and Figure 10 l.621). I believe 10.9.1 accepts it, but it is the first thing to check in a real parse.

### I3 · Info · Proportion

Parts 1–2 hold 6,527 words, with Mermaid blocks and markers removed: 4,101 of prose and 2,426 in tables. The whole document is 8,168 words. This is on target.

### I4 · Info · Marker keys

The `fig:` markers still read `…Kobo.plan.nodes…` for targets. They are not shown to readers, but a derived document that copies paths from `derived-values.json` will carry "plan" for targets. Consider a key alias when the manifest is next revised.

### I5 · Info · Understated lists

The Finding transitions omit `MERGED_INTO` and `BASIS_REFRESHED`, and the thread states omit `OPEN`, `CLOSED` and `REOPENED`. Nothing depends on these omissions; they carry over from D-I2.

## 4. Consistency checks that passed

- Kobo: the target contribution 1,445.00 and actual 883.00, with effects −412.50, −150.00, −37.50 and +38.00, summing to −562.00. Revenue 3,458.00, collected 3,180.00, outstanding 278.00. Litres 730 + 330 + 120 = 1,180. They agree across §2.1, §2.2, Figures 2, 3, 5 and 10, and `worked-portfolios.md` §1.1.
- Lakeside: metered 21,700 (8,690 + 7,430 + 5,580), billed 21,445 against 21,650, revenue 9,688.00 against 9,785.00, collected 8,870.00, in transit 150.00 plus outstanding 668.00 equals 818.00, cost to serve 8,245.00 against 7,490.00, contribution 1,443.00 against 2,295.00. All were recomputed by hand and agree.
- Stop threshold: −210 L and +150 kWh, +250.50 a month, 2,916.00 over 12 months, a 90.00 one-off over two Actions. The reserve option fails on 4 of 61 days. The design, Figures 5, 8 and 9, and the companion agree.
- The Mto huller trade (§2.5 l.387): buying now (2,910) plus the huller (1,200), Kobo (90) and the battery evidence (430) comes to 4,630, within 5,000 without the Kisiwa repair. That leaves 125 hours without backup instead of 15, matching companion l.327.
- The OD-9 steps and lanes match the coordinator's text in the owner file.

## 5. Regressions against review D

- D-M1 ("plan" for targets in the companion) is only partly fixed: see M2.
- D-M2, D-M3, D-L2, D-L3, D-L5 and D-L7 are fixed. Today's `plan` uses are named (l.433), the threshold now applies to the whole change, OD-7 and OD-8 are recorded as settled, Figure 8a's VERIFY is now `API->>S`, the released-Action case is covered, and §1.1 has its objective line.
- New in rev 16.5: M1 (the table split appeared with the OD-7 to OD-9 rows) and M3 (the Figure 10 caption).

## 6. What I could not verify, and residual risk

- No Mermaid block was parsed (I2).
- The UI-control claims in §1.4 and the six Portfolio tabs were not checked.
- Residual risk the pack does not name: the plan-item origin and its membership will need migrations on `domain_action`, and probably on `chain_action_thread`, whose one-origin check (`0051`, the `chain_action_thread_one_origin` described at l.10-12) mirrors the Action's. The thread view projects origins as appended columns, so a third origin also touches the `chain_action` view.
