# Reuse and gap matrix

**AssetEcon Layer 4 · function-level dispositions, by change-register row · recreated from the design rev 16.7 (with OD-12) · AssetOps Architect (Claude) · 19 Nov 2026**

This is the inventory beneath the design's change register (§2.9). For each register row it lists the functions and records involved, what each does today, whether it stays, extends or changes, the migration rule, and the test gap. It replaces `repo-reuse-and-gap-matrix.md` (regeneration F, #5). It argues nothing the design does not: the reasons are the shortfalls the register names.

*Serves the objective:* the core changes only where it blocks the economic value executives adopt the product for. Reuse is the default, so the visible product becomes useful quickly (D13).

**How to read.**
- **Stays**: used as it is. **Extends**: kept, with something added beside it. **Changes**: its meaning changes, under a named change.
- Paths are under `backend/assetops_backend/`, or `backend/migrations/versions/` for migrations, unless they start with `frontend/`. Each reference was re-read on this branch [code-observed].
- Who acts: builders change code; the Architect rules every parity difference and every contract change; the owner approves screens (D7).

## 1. Evidence ledger, gateway, analyses, placement, never-sum rules: stay

<!--derives: §2.9; §1.2; B1; Rules-->

The register's first row: they stay, and the analyses also observe leaves.

| Function (reference) | Today | Disposition | Migration rule | Test gap |
|---|---|---|---|---|
| Batch ingestion and conflict rule (`evidence/service.py:478-492`; `0005_evidence_ledger.py:161-197`) | First write wins; a changed payload is a conflict | Stays | Never put money rows here | — |
| Gateway credential scope (`evidence/ledger_service.py:194-211`) | Binds a credential to its Site and gateway | Stays; the commercial intake reuses the pattern | — | — |
| Dispatch-3.2 (`analytics/dispatch_v3.py:290-316`) | Necessary, candidate or indeterminate running | Stays; observes the litres split | — | Rule 3 (solar alone covers the load) has no dispatch-3.2 test (`analytics/dispatch_v3.py:294-296`) |
| Fuel balance (`fuel_balance/rules.py:216-237`) | Night balance; unexplained fuel | Stays; observes unexplained litres | — | — |
| Cold excursion and start response (`analytics/cold.py:355-653`) | Excursions, backup starts | Stays; observes crate-minutes above limit | — | — |
| EV sessions and availability (`analytics/ev.py:540-713`) | Sessions, interruptions, availability | Stays; observes chargers in service | — | — |
| Placement (`estate/placement.py:1-8`, `:150`) | Act first groups, "never a value ranking" | Stays as Finding triage | — | — |
| Never-sum rules: money overlap (`estate/financials.py:361`), invariants (`estate/money_invariants.py:1`) | One money per overlap group | Extends to structure reads: one money per factor ID | — | No test that a quantity used by two outcomes is counted once |
| No stored totals (`chain/period_read.py:46-47`, `:139`) | Period reads carry no totals | Stays; the structure is computed on read | A cached structure body obeys the same rule | — |

## 2. Findings, revisions, threads, alternatives: stay, plus CH1

<!--derives: §2.9; §2.1; §1.3; CH1; OD-3-->

Shortfall: no factor link (`outcomes/outcome_map.py:17-23`).

| Function (reference) | Today | Disposition | Migration rule | Test gap |
|---|---|---|---|---|
| Finding store and revisions (`0009_finding_store.py:33-106`) | Identity per Site; typed revision transitions | Stays; gains a factor pin read from the registry | No column added | — |
| Finding episodes (`analytics/finding_episode.py:431`) | Opens, extends, closes generator Findings | Stays | — | — |
| Threads (`0042_chain_threads.py:29-71`; `chain/lifecycle.py:46-58`) | Recurrence and response states | Stays | — | — |
| Alternatives (`mini_decisions/alternatives.py:45-48`) | Rival explanations of a Finding | Stays | — | — |
| Match pass (`analytics/finding_service.py:44-60`) | Re-reads every window per pass | Extends: incremental | Read path only | No test pins match cost against history length |
| Structure observer | — | New: deviations stored as Findings under the owner's rule and tolerance (OD-3) | Code only; Findings use today's store | Favourable movement raises nothing; unset tolerance raises every adverse deviation |

## 3. Outcome map: changes (B1)

<!--derives: §2.9; §2.1; B1; L1-->

Shortfall: no quantity between signal and outcome (`outcomes/outcome_map.py:149-180`).

| Function (reference) | Today | Disposition | Migration rule | Test gap |
|---|---|---|---|---|
| Outcome map entries and roles (`outcomes/outcome_map.py:17-37`, `:75`, `:97`) | Signal to outcomes moved and checked | Changes: computed from the registry behind its unchanged wire | Parity test against today's entries; every difference ruled; then the literal is removed | The test pinning today's literal must be rewritten on purpose |
| Contributions (`outcomes/outcome_map.py:132-142`, `:149-180`) | Node records per source and outcome | Changes: become factor rows | Same code-registry form | Registry integrity test replaces the exact-set test |
| Start-up graph check (`chain/graph.py:132`, `:177`) | Refuses an incoherent chain | Stays as the pattern for the registry check | — | Registry rules need their own cases |
| Outcome evaluator (`chain/outcomes.py:86`, `:94`) | Builds nodes from contributions | Changes: part of the structure read | Cache version bump for boards and Portfolio | — |
| Strategies (`chain/strategies/__init__.py:12`); `recorded_amount@1` (`chain/strategies/recorded_amount.py:1-10`) | Six strategies; recorded amounts always missing | Extends: a second version of `recorded_amount` reads commercial records | Add versions; never edit a published one | — |
| Board drivers (`site_outcomes/mini.py:1156-1177`) | Driver lines written per vertical | Changes: generated from the registry | Per-vertical "not connected yet" texts kept as the factor's missing reason | — |
| Catalogue (`outcomes/catalogue.py:43-68`) | Four categories; honest missing text | Stays | — | — |

## 4. Objectives: extended (B2)

<!--derives: §2.9; §2.2; B2; L3; OD-6-->

Shortfall: system-declared (`objectives/model.py:23-24`).

| Function (reference) | Today | Disposition | Migration rule | Test gap |
|---|---|---|---|---|
| Objectives and judgement (`outcomes/objectives.py:57-143`; `outcomes/status.py:55-104`) | Six objectives; Met, Missed, On pace, Behind pace | Extends: each becomes the target of the factor it measures | Append-only store stays | — |
| Objective declaration (`objectives/model.py:23-24`) | SYSTEM declarer, "not a customer target" | Changes: the operator declares, and the person is recorded | Stored SYSTEM rows keep their actor | — |
| Target and budget lines | — | New (§8, step 5) | Append-only revisions | Bridge identity to the cent on every node |
| Assure line (`site_outcomes/mini.py:692`) | "Actual against plan" | Changes: "Actual against target" (OD-6) | — | — |

## 5. Reserve recommendation and what-ifs: change (CH3)

<!--derives: §2.9; §2.4; CH3; L5-->

Shortfall: sole option, gross only (`actions/reserve_trial.py:42-45`; `mini_decisions/scenario_rules.py:191-228`).

| Function (reference) | Today | Disposition | Migration rule | Test gap |
|---|---|---|---|---|
| Reserve trial rule (`actions/reserve_trial.py:37`, `:234`); table checks (`0016_action_store.py:60`, `:72`) | One rule, fixed step | Changes: one option generator | Do not widen the rule checks; a stop-threshold option has its own carrier rule | Segment inside headroom unpinned (`actions/reserve_trial.py:249-256`) |
| Recommendation, accept, apply (`actions/service.py:300`, `:390`, `:504`) | One trial per Finding | Changes: the recommendation moves to the decision; accept and apply stay as the carrier of a chosen trial | Existing trial rows keep their meaning | — |
| What-ifs (`mini_decisions/scenario_rules.py:191-228`; `mini_decisions/scenarios.py:221`) | Authored, stored beside a Finding | Changes: an option's calculation record | Options reference a revision ID; never edit | Stop-threshold what-ifs never calculate |
| Execution port (`runs/execution_ports.py:10-24`; `host/execution_adapter.py:869`) | Lab runs through a neutral port | Extends: a replay method for calibration replays K, M, E | Protected seam: add a port method; leave the existing run untouched | No test replays observed series through the kernel |
| Decision principal (`mini_decisions/model.py:69`) | Server SERVICE principal | Extends: choosing needs a named person (CH2) | Stored SERVICE writes stay | No human-principal test |
| Decision and option records | — | New (§8, step 6) | — | No action always present; hard bound rejects |

## 6. Possible extra fuel cost: stays

<!--derives: §2.9; §2.4; Rules-->

| Function (reference) | Today | Disposition | Migration rule | Test gap |
|---|---|---|---|---|
| Fuel cost range (`financials/fuel_cost.py:22`) | Modelled range from zero to a bound | Stays: an at-stake bound, never an option's value | — | A test that no option's value reads it |

## 7. Opportunity study to thread to mill Action: stays, extended

<!--derives: §2.9; §1.4; OD-7-->

Shortfall: headroom with demand "unverified" (`mini_decisions/opportunities.py:366-401`).

| Function (reference) | Today | Disposition | Migration rule | Test gap |
|---|---|---|---|---|
| Opportunity studies (`mini_decisions/opportunities.py:366-401`; `mini_decisions/projection.py:29`) | Headroom studies, shown as opportunity | Stays as capacity evidence; Portfolio tab renamed *Demand and capacity* | — | — |
| Study thread (`0042_chain_threads.py:43-62`) | A thread with no Finding | Stays | — | — |
| Mill-shift origin (`0051_action_opportunity_origin.py:73-79`) | The forced mini-grid opportunity origin | Stays a legacy origin for existing mill-shift Actions only (OD-7) | §8 migration | A new opportunity origin is refused |
| Mill verification (`actions/verification_families.py:7-22`, `:175`) | Midday-shift family; no guardrails | Stays | Guardrails come from the option's bounds when new | Empty guardrails pinned on purpose |

## 8. Actions, domain actions, work cases, rail: stay, plus CH2 and P

<!--derives: §2.9; §2.5; §2.6; CH2; P; G1; OD-1; OD-4; OD-7; OD-8-->

Shortfall: no recorded person (`actions/lifecycle.py:43-58`; `work/model.py:280-285`).

| Function (reference) | Today | Disposition | Migration rule | Test gap |
|---|---|---|---|---|
| Trial action and events (`0016_action_store.py:46`, `:123`, `:171`); SYSTEM actor (`actions/lifecycle.py:43-58`) | Reserve-trial carrier; acts recorded as a SYSTEM demonstration | Extends: person, owner, due date, origin, membership | Stored SYSTEM events are never rewritten | No approval test |
| Domain action (`0033_w5_cold_work.py:39`; `work/domain_action.py:24-136`) | Work intent with an owner label and due date | Extends: an origin arm for a plan item, and plan membership | One-origin check (`0051:73-77`) gains an arm for a plan item | — |
| Work case and events (`0027_w4_work_cases.py:12`, `:100`; `work/model.py:107-151`) | Incidents and maintenance requests | Extends: origin and membership | — | — |
| Work authorisation (`work/model.py:280-285`) | A user actor is refused | Changes: a person with the role is accepted | — | Refusal for a missing role |
| Assignment (`work/model.py:328`) | ASSIGN events | Stays; crew visits are read from it | — | — |
| Action-thread link, target trigger, view (`0051:87-88`, `:34-50`, `:53-62`) | One origin pair per link | Changes in the same migration as the origin arms | Downgrade refuses while new arms are used | — |
| Actions rail (`frontend/src/estate/actionIndex.tsx:38-160`) | Lists Actions | Extends: owner, due date, overdue | — | Overdue shown on the rail |
| Due rule (`outcomes/plan_due.py:1-33`) | Overdue for maintenance schedules | Stays; reused for Actions | — | — |
| Plan records (`portfolio_plan` and its versions and items) | — | New (§8, step 7) | Name chosen so it cannot collide with `verification_plan`, `plan_due` or `actual_against_plan` | Spend counted once; release only by the threshold rule |

## 9. Verification: stays, plus CH4

<!--derives: §2.9; §2.7; CH4; L6; D14-->

Shortfall: cost 0; simulated evidence only (`actions/verification.py:1167`; `actions/verification_rules.py:688`).

| Function (reference) | Today | Disposition | Migration rule | Test gap |
|---|---|---|---|---|
| Baseline freeze (`actions/verification.py:193`); stores (`0019_verification_core.py:48`, `:157`) | Frozen verification baseline; operational verdict | Stays | Do not widen the outcome check (`0019:166`) | — |
| Verdict rules (`actions/verification_rules.py:675-815`) | Target and guardrails | Extends: field evidence admitted with its label | Frozen baselines keep their basis | No test with a field-sourced set; unserved-critical failure branch untested (`:788`) |
| Families (`actions/verification_families.py:502-516`) | Reserve, midday, fuel residual; no cold or EV family | Extends: cold and EV families | Each family is a new arm on the family check | Cold and EV can never reach Verified today |
| Intervention cost (`actions/verification.py:1167`) | Fixed at 0 | Changes: the option's one-off cost | Stored checks keep their 0 basis | No test with a non-zero cost |
| Trial cost comparison (`0037_cc_trial_cost_comparison.py:27`) and credit (`outcomes/credit.py:57-73`) | Modelled cost change; credit after Verified | Stays; seeds the economic verdict | — | — |
| Economic and causal verdicts | — | New (§11, step 8) | Stored beside the operational outcome | "Not proven yet" before the after-window closes |

## 10. Portfolio cards, Optimize figure, site board: change (CH5)

<!--derives: §2.9; §2.8; CH5; L7-->

Shortfall: counts; one day over a period (`site_outcomes/read.py:676-682`).

| Function (reference) | Today | Disposition | Migration rule | Test gap |
|---|---|---|---|---|
| Optimize card (`site_outcomes/read.py:676-682`) | The window's last day over a period range | Changes: corrected first (step 1), then period cost factors | — | Card scope pinned before it changes |
| Portfolio cards (`site_outcomes/read.py:926-977`) | Estimated income, a cost claim per Site, counts | Changes: read from factors against target | Cache version bump | — |
| Site board (`frontend/src/sites/OutcomeBoard.tsx:42-48`, `:262-330`) | Outcome, drivers, issues, levers, in hand, earlier | Extends: drivers as factor rows; decisions open from "What can be done" | — | — |
| Portfolio tabs and rail (`frontend/src/estate/portfolioWords.ts:29-37`; `frontend/src/shell/OperatorShellLayout.tsx:61-71`) | Six tabs; the rail | Stays; one tab renamed | Old addresses redirect | — |
| Act first (`frontend/src/estate/EstatePortfolio.tsx:314`) | Findings in placement groups | Extends: the version awaiting approval beside the triage | — | — |

## 11. New components, in migration order

<!--derives: §2.9; Figure 10; OD-9; B1; B2; B3; CH2; CH3; P; CH4-->

Migration numbers start at the next free number after `0061_reading_upload.py`. They are placeholders until `delivery-plan.md` sets each slice. Every migration refuses downgrade while its rows exist, and registers an input-change trigger where a cached route reads it (`0047_chain_response.py`).

| Order | Component | Delivery step (Figure 10) | Migration | Nearest existing pattern |
|---|---|---|---|---|
| 1 | Optimize card correction | 1 | none | — |
| 2 | Leaf factor IDs and canonical format version 1 | 2 | none | the manifest's `factor_map` |
| 3 | Commercial record store and intake | 3A | first | reading-upload dry run and receipt (`0061`) |
| 4 | Factor registry, structure read, structure observer | 3B | none (code rows) | `chain/graph.py:177`; `chain/period_read.py:249` |
| 5 | Recorded person, owner and due date on every carrier | 3C | second | the human-actor check (`0010_financial_assumptions.py:57-78`) |
| 6 | Target and budget lines; the bridge | 5 | third | objective revisions |
| 7 | Decision and option records | 6 | fourth | the origin-pair checks of `0051` |
| 8 | The plan; Action origin and membership arms | 7 | fifth | `0051` |
| 9 | Economic and causal verdicts | 8 | sixth | `0037` beside the operational outcome |
| 10 | Contract rows and rights events | 9 | seventh | operational-record review state (`0027_w4_work_cases.py:174`) |

Calibration replays K, M and E run in parallel from the start (step 0) and need no migration.

## 12. Open questions

<!--derives: Decisions; §2.9-->

| Question | Default |
|---|---|
| Is the stop-threshold change carried by a domain action with an apply path, rather than by widening the trial action's checks? | Yes. The trial checks encode one rule's safety and stay as they are |
| Does any part retire outright? | No. Only the outcome map's literal is removed, after its parity test; everything else stays, extends or changes in meaning |
