# Layer 4 regeneration, Phase B: independent review of rev 16

**Reviewer:** fresh AssetOps reviewer (Claude), not the author · 19 Nov 2026 · branch `task/layer4-design-regeneration`, head `ae59dd66f`.
**Under review:** `layer4-transformation-design.md` (rev 16) and `.html`; `worked-portfolios.md`; `design-appendix.md`; the `check_manifest.py` and `motivation_figures.py` changes in `ae59dd66f`.
**Standard:** `.agent/owner-design-regeneration-request-2026-11-19.md` (owner, verbatim). The Phase A audit was treated as a claim to check, not as truth.

## Summary (round 1)

- **Verdict: REVISE.** A small, targeted fix round. The structure, the Finding definition, Q-A1, the roles, plan versus Action, merit per change and the business breadth all follow the owner. The mechanics checks pass and nothing earlier was weakened.
- **Counts:** High 1 · Medium 3 · Low 12 · Info 4.
- **H1:** the two sequence diagrams (Figure 7a/7b, the decide-act-track before and after) put `;` in message text. Mermaid 10.9.1, the version the HTML loads, ends a statement at `;`, so neither diagram would render.
- **M1:** who chooses is not reconciled. The site manager chooses within a decision, but the system's plan search also picks one option per decision. Who creates the Action is never said. The owner's "user creates one or more actions against it" is not reflected.
- **M2:** `worked-portfolios.md` still marks options "**Chosen**" in 11 places, before any person has chosen. That contradicts the main document's "It never decides" and its own disposition list.
- **M3:** Part 1 leaves out today's opportunity carrier: headroom study → opportunity thread → MINI domain Action (`0051`). Yet Part 2 introduces an "opportunity Finding" and does not say how the two relate.
- **Code accuracy:** 29 claims sampled. 22 confirmed, 4 overstated, 1 understated (M3), 2 with wrong line citations.
- **Checks:** `check_manifest.py` gives 3,757 passed, 0 failed. `motivation_figures.py --check` gives 2 figures, none missing or unused. The HTML render is byte-identical.

---

## 1. Faithfulness to the owner

| Owner instruction | Held? | Where / note |
|---|---|---|
| Structure: Part 1 is today's architecture, value and mechanics; Part 2 is the constructs on top, by what they bring and where they fit, grounded in differentiation | **Yes** | §1.1–§1.6; §2.0 table, and "What it brings / Where it fits / Why it converts" in each Part 2 section |
| User workflow: a person decides, acts and tracks; the system never acts on its own | **Mostly** | §1.4, §2.5 and Figure 7 state it well ("It never decides", l.449). M1 and M2 leave gaps |
| A Finding is a living output of condition evaluation and meets Q-A1 | **Yes** | §1.3 l.103 ("It is the output of the condition, not the condition itself"); Q-A1 applied l.109-122 and in the Kobo examples l.247-252. No instance in the three files describes a Finding as a condition. `worked-portfolios.md` does not mention Findings at all |
| A few sensible roles | **Yes** | Five roles, §2.5 l.441-447, "not views" |
| Plan versus Action, with an owner and a reason | **Yes, with M1** | §2.4 l.399-420: a clear table, the executive as owner, merit and a "thin record" boundary |
| Merit for every core change, against the objective | **Yes** | §2.8 change register; each CH has "The change and its merit" with code evidence |
| Business view broader than one slice | **Yes** | §1.5 value chain by vertical; the §2.1 three-vertical table; roles across the value chain |
| Short, intentional, well illustrated | **Partly** | 641 lines / 59 KB, down from rev 15 and with the detail moved to companions. Still dense: see L11 and I4 |
| Diagrams only where something changes, mini-grid as the demonstration | **Yes, but H1** | Figures 1-9 are change-focused. Kobo is used in Figures 2, 3, 5, 7 and 8. Today's parts appear only as greyed context. The sequence diagrams would not render (H1) |

---

## 2. Findings

### Class A: Diagrams that would not render

**H1 · High · `layer4-transformation-design.md` l.497, l.511, l.518 (Figures 7a and 7b)**
Quoted:
- `API->>S: Foundation revision + APPLIED (SYSTEM); thread: change applied`
- `S->>S: Finding revised; pinned to candidate litres; the bridge shows its effect`
- `API->>S: thread: change applied; overdue shown if late`

*Problem.* In Mermaid's sequence-diagram lexer, message text is `:(?:(?:no)?wrap)?[^#\n;]+`, and a bare `;` is its own token, a statement separator. The text after the `;` is therefore read as a new statement: `thread` as an actor followed by `: change applied`, with no arrow. That is a parse error.

*Evidence.* I read the lexer rules in `mermaid@10.9.1/dist/sequenceDiagram-6894f283.js` (packed into the scratchpad). 10.9.1 is the version `render_design_html.py`'s footer imports. I could not run `mermaid.parse` (see "Could not verify").

*Why it matters.* These are the only sequence diagrams, which the owner asked for by name. They carry the core workflow point (the manager's acts recorded as SYSTEM, before; each act carrying its person, after). In the HTML twin both would show a Mermaid error box.

*Fix.* Replace each `;` in the message text with `,` or `#59;`. Then re-render and run a parse check.

### Class B: Who decides and who creates the Action (the owner's central question)

**M1 · Medium · §2.4 l.394-410, §2.5 l.445, Figure 7b l.514-516**
Quoted:
- "The system searches every combination of one option per decision. It keeps those that fit, and proposes the one that breaks service rules least…"
- Roles table, site manager: "Chooses the option within each decision"
- Plan versus Action, the Action's life: "Created from the approved plan → applied → tracked → verified"

*Problem.* Two choosers are described for the same thing:
- The manager chooses the option within each decision.
- The portfolio search also selects one option per decision, and the executive approves that set.

The document never says what happens when the search's selection differs from the manager's choice, or whether the search runs only over options the manager has accepted.

"Created from the approved plan" is passive. It does not say whether a person creates the Action or the system creates it on approval. Read the second way, the system acts. That is exactly what the owner asked about.

The owner's Q-A1 words are "the user likely reate one more action against it", meaning one or more Actions. The document's path yields one chosen option and so one Action. Separately, CH2 adds "raise a case or domain action from a Finding" (l.436), but it never relates those direct Actions to the plan, the budget or the approval.

*Why it matters.* This is the gap the owner named first ("its provision for users to act on the basis of context given to them").

*Fix.* Add one short paragraph and a row to the plan versus Action table:
- the manager's choices are the input to the plan search;
- the executive's approval releases them;
- the site manager (a person) raises the Action or Actions, one or more per chosen option or directly from a Finding;
- direct Actions that spend budget or crew enter the plan; others do not need it.

**M2 · Medium · `worked-portfolios.md` l.156, 175, 205, 206, 226, 242, 389, 401, 416, 535, 552**
Quoted: "Assemble evidence: capacity test and temperature sensor | … | **Chosen**; not valued in money" (l.242); "**+3,540.00 over 12 months. Chosen**, if the inverter is restored…" (l.226); "**Chosen**: the only option that keeps both the…" (l.416).

*Problem.* The Evaluate tables give the system's evaluation as "Chosen" before any person has chosen. The main document's dispositions are "Recommended, Conditional, Acceptable, Deferred or Rejected" (l.373), and it says "It never decides" (l.449). The companion's header (l.5-7) says the only edit was to make the plan *proposed* and *approved*. This vocabulary was carried over from rev 15. The same pattern appears at l.574 ("Once chosen, the items are acted on…") and l.624 ("the 15-hour repair is chosen").

*Why it matters.* This reproduces audit class C2 ("the system appears to choose and act") inside the pack under review.

*Fix.* Replace "Chosen" with "Recommended" (or "In the proposed plan"). Make l.574 active: "once the executive approves, the site manager raises the Actions in this order".

### Class C: Today's mechanics, as stated against the code

**M3 · Medium · §1.2–§1.4 (omission); §2.1 l.251; §2.8 change register**
Quoted: "the same headroom with a signed letter of intent is an opportunity Finding" (l.251); "Opportunity | A headroom study | Renamed *Demand and capacity*…" (l.566).

*Problem.* Today, a mini opportunity study (`mini_opportunity`, `0030_w4_mini_decisions.py`) is a thread occurrence. Its thread maps to `SIGNAL:PRODUCTIVE_USE_HEADROOM` (`outcomes/outcome_map.py:108-116`), and it can originate a MINI domain Action through `origin_opportunity_id` (`0051_action_opportunity_origin.py:1-12`). The mill-shift domain Action that §1.4 lists comes from this path. The audit records it (`A-…audit.md` l.83, l.125, l.187).

Part 1 never presents this as a carrier: an opportunity that a person can act on and track, today, without a Finding. Part 2 then adds "opportunity Findings" without saying whether today's opportunity study becomes one, stays beside one, or is replaced. The change register (§2.8) has no row for it.

*Why it matters:*
- Today's act-and-track reach is understated (audit class C3).
- Part 2 may create a second carrier for the same thing.
- The Q-A1 "opportunity" leg rests on this construct.

*Fix.*
- Add the opportunity study and its Actions to §1.2 (the Act row) and §1.4.
- Add a §2.8 row: stays as the evidence of demand; becomes an opportunity Finding when the owner's rule holds; or whatever the Architect decides.
- State the merit.

**L1 · Low · §1.2 l.97, l.98 (wrong line citations)**
- `outcomes/credit.py:200-237`: the file has 104 lines. The credit rule is `credited()` at `outcomes/credit.py:57-73`.
- `outcomes/status.py:138-185`: the file has 113 lines. The objective-driven state is at `outcomes/status.py:55-104` (ON_TRACK / WATCH from MET, ON_PACE, BEHIND_PACE at l.88-93).

The audit carries the same out-of-range citations (`A-…audit.md` l.169, l.211), so they were copied rather than re-read. The substance of both claims is confirmed.

**L2 · Low · §1.4 l.130** · "Raises an action or case with title, owner and due date"
This is overstated for work cases:
- `work_case` and its revision have a title and a narrative, but no owner and no due field (`0027_w4_work_cases.py:12-75`).
- The assignee is free text on ASSIGN (`work/model.py:329`).

Only domain actions carry `owner_label` and `due_at` (`0033_w5_cold_work.py:46-48`), and those fields are nullable. *Fix:* "domain actions carry an optional owner label and due date; work cases an assignee."

**L3 · Low · §1.4 l.131 and Figure 7a l.498** · "Verifier (system) | Freezes the plan and judges the after-window"; `API->>S: VERIFY → verdict, cost check, credit if Verified`
`VERIFY` is a SYSTEM-demonstration *command* that freezes the plan or binds its later selection. It "never supplies a metric, verdict or resolution event" (`actions/lifecycle.py:26-28`). The verdict comes from the evaluator job (`:24-25`), as l.131 itself says. The figure merges the two into a command step. *Fix:* split it into `API->>S: VERIFY (freeze plan)` and `S->>S: evaluator: verdict, cost check, credit if Verified`.

**L4 · Low · §1.2 l.93; §1.3** · "with a claim ceiling, rival explanations and next-step text"
This is presented as true of every Finding. Rival explanations (Alternatives) serve "W1 mini-grid dispatch Findings only" (`mini_decisions/alternatives.py:47-48`). The claim-limit read is the S3 dispatch read (`analytics/claim_limit_read.py:1-10`). *Fix:* "for mini-grid dispatch Findings".

**L5 · Low · §2.4 l.415** · "no budget, crew or cross-Site constraint exists today (grep `budget|crew` finds nothing)"
Taken literally the grep is false: it hits layout "budget" in `frontend/src/sites/MiniPerformance.tsx:226`, `SiteSingleLineDiagram.tsx:208` and `GlobalMaintenance.tsx:387`, and also backend tests. The substance is confirmed: there is no budget, crew or cross-Site constraint construct in `backend/assetops_backend` or `backend/migrations`. *Fix:* "no budget or crew construct exists in the backend or schema".

**L6 · Low · §1.6 L4 l.162** · "`chain/adapters/http_prebuild_client.py:1-10` (the only HTTP client)"
That file is the pre-build's client against AssetOps' own running serve (its docstring, l.1-4), not an integration. It shows only indirectly that no outbound integration exists. Today's intake routes (gateway, reading upload, operational entries, price entry) are the relevant evidence of how narrow the inputs are. *Fix:* cite the intake routes, or say "no outbound client to any external system".

### Class D: Internal consistency and cross-references

**L7 · Low · §2.4 l.412** · "At Lakeside, buying the Mto inverter now would keep the huller connection only if the Kisiwa repair were dropped, which would leave 125 evening hours with no backup instead of 15"
This holds only when the cooperative's letter of intent is *not* extended (`worked-portfolios.md` l.301-310, second row). Under the default (extended), the claim path keeps the huller and nothing is dropped. *Fix:* add "if the cooperative does not extend its letter".

**L8 · Low · `worked-portfolios.md` l.9** · "The approver and owner roles are the design's default awaiting the owner (design §2.5, Q-A2)"
The main document records Q-A2 as answered and applied (l.623). *Fix:* "the five roles of design §2.5 (owner, Q-A2)".

**L9 · Low · stale cross-references**
- `design-appendix.md` l.32: "§0 rules and §2.3". Rev 16 has no §0. The rules are "Rules every figure follows" under "How to read this document".
- `worked-portfolios.md` l.609: "(see "When a condition changes" in 7.1)". This should be §1.1 (l.301).
- `worked-portfolios.md` l.622: "Rev 4 re-expresses every site period…". This is the manifest's revision, not the design's, and is ambiguous in a file headed "rev 16".

**L10 · Low · §2.1 table l.273** · "cooling availability 99.997% (4 minutes lost at Thika)" is untagged, while its neighbours are tagged.
The value is correct (`derived-values.json` `operations.harvest-cold.cooling_availability.portfolio = 99.997`). The checker's O2 percentage regex `\d{1,2}\.\d{2}%` does not see three decimals, so a wrong value here would pass. *Fix:* tag it. Optionally, widen the regex.

### Class E: Clarity for the founder-reader

**L11 · Low · jargon without a gloss.** These terms are used and never explained in plain words:
- "structure observer" and "one observer row of the registry" (l.243-246);
- "behind a parity test before the old literal goes" (l.238);
- "claim ceiling" (l.93);
- "Σ/Σ" (l.273);
- "switches" (l.395);
- "bounds (hard, costed or advisory)" and "disposition" (l.373);
- "replay K" (l.391);
- "D13, adopted" and "W3".

A founder judging understanding would stop at each. A one-line gloss at first use, or a short glossary box, would do.

**L12 · Low · statements that argue rather than state fact**
- "No monitoring tool can answer that." (l.286)
- "The contrast sells." (l.375)
- "A monitoring tool shows the generator ran; AssetEcon shows what that did to contribution." (l.234)

The design's own appendix says AssetEcon's differentiation "remains a hypothesis to validate with prospects and pilots" (`design-appendix.md` l.41). The owner did ask for Part 2 to be "grounded on the differentiation". So the "Why it converts" lines are in scope, but they should be worded as the hypothesis they are ("intended to answer what monitoring tools do not"). *Not a request to drop them.*

### Class F: Information (no change required)

**I1 · Info · the mechanics changes do not weaken the earlier checks.**
- `REQUIRED` re-homes every rev-15 headline path:
  - all nine `plans.{tenant}.default.{spend,value,crew_visits_used}`;
  - the five Protect paths (Kisiwa and Mto obligation hours, Thika nights, Kasarani departures and penalties).

  They move to `worked-portfolios.md`. The main document gains five new required Kobo and Lakeside paths.
- The untraced-figure scan (`documents()`) now covers the main document's Parts 1–2 and Decisions, and `worked-portfolios.md` from §1.
- `design-appendix.md` is in `FIG_DOCS` (anchor checks) but not in the untraced scan. It has no money figures today, so nothing is lost.
- `motivation_figures.py --check` is new coverage: markers against figures, and every figure builds with its box-fit asserts. It replaces nothing that was checked before. The rev-15 motivation figures (0.1-0.3) were not checked by any tool. The figures read their values from `derived-values.json`, so they cannot drift from the evaluator.

**I2 · Info · a reusable pattern for CH2.** `0010_financial_assumptions.py:57-78` already models a HUMAN actor: `author_id` is required iff `actor_kind = 'HUMAN'` iff `channel = 'HUMAN_API'`. The API refuses it today with `HUMAN_PRINCIPAL_REQUIRED` (`financial_api.py:14`, `:209`). G1 still holds. CH2 could cite this pattern alongside `0051`.

**I3 · Info · Figure 4 (l.340-346).** `EM --> AD` names `AD` before `subgraph AD[...]` declares it. This pattern was carried over from rev 15 (rev 15 l.666-673) and presumably rendered then. I have not verified it.

**I4 · Info · length.** The main document is 641 lines and about 59 KB, down from rev 15 by about 1,250 net lines, with the worked examples and the appendix moved out. That is acceptable against "I don't need a large doc". Further gains would come from L11, not from cutting content.

---

## 3. Accuracy against the code (29 claims sampled)

Paths are under `backend/assetops_backend/` unless they are migrations (`backend/migrations/versions/`) or start with `frontend/`.

| # | Claim (document location) | Result | Evidence |
|---|---|---|---|
| 1 | A Finding is unique per Site by key; names analytic, mechanism, asset, recurs-after (§1.3) | Confirmed | `0009_finding_store.py:33-58` (`finding_key_unique UNIQUE (site_id, finding_key)`) |
| 2 | Revisions append with typed transitions; each has claim, limitations, episode bounds, digests (§1.3) | Confirmed | `0009_finding_store.py:62-104` (transition CHECK l.67-68, also MERGED_INTO) |
| 3 | Thread states: action in hand, change applied, resolved and monitoring, recurred, withdrawn (§1.3) | Confirmed | `0042_chain_threads.py:66-67`; `chain/lifecycle.py:47-58` |
| 4 | Trial commands are recorded as "SYSTEM demonstration", "no operator approval is recorded" (§1.4, G1) | Confirmed | `actions/lifecycle.py:43-58`; `0016_action_store.py:131-133` (`actor_kind = 'SYSTEM'`) |
| 5 | The verdict is appended by the evaluator, never by a command (§1.4) | Confirmed; Figure 7a contradicts it (L3) | `actions/lifecycle.py:24-28` |
| 6 | Work and domain writes refuse a user actor (G1) | Confirmed | `work/model.py:281-285` (`WORK_USER_AUTH_REQUIRED`) |
| 7 | No principal is injected by default, so writes are 403 (G1) | Confirmed | `main.py:640-661` |
| 8 | Trials have no owner or due date (G1) | Confirmed | `estate/coverage.py:530` (`"owner": None, "due_at": None`) |
| 9 | Domain actions and work cases are raised "with title, owner and due date" (§1.4) | Overstated (L2) | `0033_w5_cold_work.py:45-50` (domain: yes, nullable); `0027_w4_work_cases.py:12-75` (work case: no owner or due); `work/model.py:329` |
| 10 | "No telemetry creates an Action or a case link" (§1.4) | Confirmed | `work/domain_intent.py:17` |
| 11 | No device command or notification is written (§1.4) | Confirmed (grep for smtp, webhook, notification, modbus, register write: none in the backend) | grep, `backend/assetops_backend` |
| 12 | Five stored Finding mechanisms; a fixed mechanism → outcome map (§1.3, CH1) | Confirmed | `outcomes/outcome_map.py:17-23` |
| 13 | Indeterminate running raises a Finding (§1.3) | Confirmed | `analytics/dispatch.py:40`, `:1070` |
| 14 | Three mini-grid verification families; an unknown family fails closed (§1.2) | Confirmed | `actions/verification_families.py:502-516` (RESERVE, MIDDAY, FUEL) |
| 15 | A positive verdict admits only simulated or authored evidence (L6, CH4) | Confirmed | `actions/verification_rules.py:688` (`POSITIVE_SOURCE_CLASSES`) |
| 16 | The change's own cost is fixed at 0 (L6, CH4) | Confirmed | `actions/verification.py:1167` (`InterventionCost(Fraction(0), …)`) |
| 17 | Credit only when Verified, never summed (§1.2) | Confirmed; citation wrong (L1) | `outcomes/credit.py:57-73` (cited `:200-237` in a 104-line file) |
| 18 | Six operational objectives (§1.2) | Confirmed | `outcomes/objectives.py:58-71` |
| 19 | Objectives drive the outcome state (§1.2) | Confirmed; citation wrong (L1) | `outcomes/status.py:55-104` (cited `:138-185` in a 113-line file) |
| 20 | Objectives are system-declared, "not a customer target" (L3, B2) | Confirmed | `objectives/model.py:21-24` |
| 21 | Money: `recorded_amount@1` "returns no money with NO_RECORDS, always" (§1.5, L2) | Confirmed | `chain/strategies/recorded_amount.py:1-11` |
| 22 | Money: modelled fuel cost from 0 up to an upper bound (§1.2) | Confirmed | `financials/fuel_cost.py:22` |
| 23 | Reserve −5 "does not predict … any saving" (L5, CH3) | Confirmed | `actions/reserve_trial.py:37`, `:42-45` |
| 24 | No budget or crew construct (§2.4) | Confirmed in substance; grep wording overstated (L5) | grep for budget and crew: layout hits in the frontend and tests only |
| 25 | Intake is first-write-wins and refuses late intervals (B3) | Confirmed | `evidence/service.py:484-492` (conflict); `reading_upload/service.py:244-248` (`ALREADY_RECORDED`) |
| 26 | "The only HTTP client" shows few integrations (L4) | Confirmed literally; weak evidence (L6) | `chain/adapters/http_prebuild_client.py:1-4` |
| 27 | Act first groups "never a value ranking" (§1.2) | Confirmed | `estate/placement.py:3-5` |
| 28 | The board's columns include "Must not harm" (§1.2) | Confirmed | `frontend/src/sites/OutcomeBoard.tsx:41-47`, `:270` |
| 29 | Findings carry rival explanations (§1.2, as general) | Overstated (L4) | `mini_decisions/alternatives.py:47-48` (mini-grid dispatch only) |
| — | Part 1 omits the opportunity study → thread → Action path | Understated (M3) | `0030_w4_mini_decisions.py`; `0051_action_opportunity_origin.py:1-12`; `outcomes/outcome_map.py:108-116` |

The audit's central factual claims (G1, the five mechanisms, operational-only verification, no recorded money, system-declared targets) check out against the code. Its two out-of-range citations (credit.py, status.py) do not.

---

## 4. Mechanics re-run (from the pack folder)

```
$ python3 check_manifest.py
3757 checks passed, 0 failed
$ python3 motivation_figures.py --check
2 figures built; markers ['factor-structure', 'plan-against-actual']; missing []; unused []
$ python3 render_design_html.py layer4-transformation-design.md <scratch>/r.html && cmp <scratch>/r.html layer4-transformation-design.html
IDENTICAL
```

Figures checked by hand:
- **Kobo bridge:** −412.50 − 150.00 − 37.50 + 38.00 = −562.00, which equals 883 − 1,445.
- **Stop threshold:** 12 × (210 × 1.25 − 12.00) − 90.00 = 2,916.00.
- **Kobo cash:** 3,458.00 − 3,180.00 = 278.00 outstanding.
- **Lakeside cash:** 9,688.00 − 8,870.00 − 150.00 = 668.00.
- **Lakeside availability:** 428 / 434 = 98.62%.

All agree across the text, Figures 2, 3 and 5, and `worked-portfolios.md`.

## 5. Could not verify

- **The Mermaid diagrams were not rendered or parsed.** A Node parse of the eight blocks against the packed `mermaid@10.9.1` was refused by the session's permission classifier. H1 rests on the lexer rules read statically from that package. I3 is unverified.
- **The HTML was not viewed in a browser.** Narrow-layout legibility of Figures 2 and 3 was not checked by eye.
- **No suites or databases were run**, per the brief.

## 6. Residual risk the pack does not name

- **Opportunity carriers.** If M3 is left open, the build could add an "opportunity Finding" beside the existing opportunity study, giving two carriers, two threads and two Action origins for the same headroom.
- **Two choosers.** If M1 is left open, slice 6 (decisions) and slice 7 (plan) could build two selection points that disagree. The executive would then approve options the manager did not choose.
