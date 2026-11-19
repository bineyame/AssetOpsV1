# Layer 4 design regeneration, Phase A: today's mechanics, the audit, and the proposed structure

**AssetOps Architect (Claude) · 19 Nov 2026 · Phase A of the regeneration (W1: the structure is approved before anything is regenerated)**
**Branch:** `task/layer4-design-regeneration` (cut from the Layer 4 pack at `110f6957d`). No code, test, database or pack document was changed.
**Governing input (verbatim):** `.agent/owner-design-regeneration-request-2026-11-19.md`. It holds the owner's question, the owner's direction and three later additions: on changes to the core, on size and form, and on diagrams. The same text is on `main` in `owner/`.

**Labels.**
- **[code-observed]**: I or an exploration pass read the cited line on this branch.
- **[inferred]**: a reading of several lines together, or an absence found by grep (the grep terms are given).

Backend paths are under `backend/assetops_backend/`. Migrations are under `backend/migrations/versions/`. Frontend paths start with `frontend/src/`.

**How Part 1 was read.**
- The code was read in four parallel passes: Findings and analyses; action and tracking; what-ifs and objectives; outcomes, Portfolio and money. No pack document was used as a source.
- I re-read the load-bearing lines myself:
  - the Finding schema (`0009_finding_store.py:33-106`);
  - the thread event schema (`0042_chain_threads.py:64-88`);
  - the SYSTEM actor (`actions/lifecycle.py:43-58`);
  - the work actor rule (`work/model.py:281-292`);
  - the outcome map (`outcomes/outcome_map.py:17-37`, `:149-180`);
  - the catalogue (`outcomes/catalogue.py:9-68`);
  - objectives (`objectives/model.py:17-91`);
  - the absence of a principal in `main.py:640-661`;
  - the estate Action row (`estate/coverage.py:530`).

---

## Part 1. Today's product mechanics, as the code shows them

### 1.0 The core loop in one paragraph

Today's product runs a complete operational loop. It is a narrow loop, and every step in it is persisted and replayable:
1. Readings enter an append-only evidence ledger.
2. Analyses evaluate declared conditions over those readings.
3. A Finding is the stored, revised result of that evaluation.
4. A Finding is shown to the operator with its evidence, its claim limit, rival explanations and a next step.
5. The operator accepts a recommendation or raises work against it.
6. The resulting Action or work item is an event-sourced record that moves the Finding's thread.
7. A verification family freezes a plan and judges the result against the same measures.
8. A credit rule admits a modelled money change only when the verdict is VERIFIED.

The loop is honest and strongly typed. It is not connected to the business's money: no recorded money exists, and outcomes are linked to signals by a flat map rather than composed from factors. Its act-and-track path is built for a person, but in the code no human identity is ever recorded (§1.3).

### 1.1 Signals and analyses

| Construct | What it computes | Evidence |
|---|---|---|
| Evidence ledger | Every reading, with its source, its unit before and after conversion, its quality, a live-or-simulated flag and an envelope hash. Append-only | `0005_evidence_ledger.py:161-197` [code-observed] |
| Mini-grid dispatch `dispatch-3.2` | Classifies generator running as NECESSARY, CANDIDATE_AVOIDABLE or INDETERMINATE from one frozen input set (role-bound readings, reserve and minimum-runtime controls). A minimum runtime withholds Candidate rather than claiming Necessary. Window and interval assessments, keyed `dispatch:interval:{asset}:{first_on}`. Money is explicitly "UNAVAILABLE" | `analytics/dispatch_v3.py:3-12`, `:290-316`, `:436-490`, `:477` [code-observed] |
| Fuel balance `fuel-balance-1` | For each tank night (18:00–12:00 local): the tank drop plus deliveries, against modelled use (SFC × kWh + idle hours × no-load rate, with a 0.9–1.1 band and a ±2a sensor margin). UNEXPLAINED when the lower residual is at least 40 L | `fuel_balance/rules.py:30-46`, `:216-237` [code-observed] |
| Mini-grid depth reads | Per noon hour: renewable headroom (capability ± uncertainty − use − retained margin), giving ELIGIBLE / LIMITED / EXCLUDED / CONFLICT. Also service hours (unserved kWh), fuel hours and the backup step chain. Stored in `mini_depth_revision`; not Findings | `mini_depth/rules.py:285-384`, `:571-622`, `:711-783` [code-observed] |
| Cold `cold-excursion/1`, `cold-start-response/1` | Probe readings against a declared policy band, giving bounded duration, degree-minutes and peak (UNKNOWN below 0.8 coverage). The backup start step chain, with OBSERVED_FAILURE | `analytics/cold.py:114-122`, `:355-528`, `:600-653` [code-observed] |
| EV `ev-session/1`, `ev-availability/2` | Session classes (COMPLETED, OBSERVED_ABORT, …) with kWh; the connector availability ratio. A Finding comes from an aborted session with a fault | `analytics/ev.py:34-39`, `:291-292`; `analytics/ev_availability.py:1-35` [code-observed] |
| Declaration and claim ceiling | Readiness (FULL / LIMITED / NONE) with a claim ceiling per assessment | `analytics/declaration.py:92-128`, `:300-374`; `analytics/claim_limit_read.py:1-19` [code-observed] |
| Early warnings `early-warnings/1` | Seven warning kinds with fixed thresholds (for example, peak above 90% of the import limit). No money | `outcomes/warnings.py:20-59`, `:186-221` [code-observed] |

**Done well.**
- The analyses are deterministic, versioned and bounded.
- Each states its own limits: dispatch withholds rather than over-claims, and the fuel band is labelled "not a financial saving" (`analytics/dispatch.py:707-750`) [code-observed].

**Lacks, against the economic intent.**
- They observe physical quantities: minutes, litres, degree-minutes, sessions.
- No analysis produces or reads a quantity that a business outcome is declared to be built from: billed kWh, collected cash, crate-days or departures met [code-observed: absences in §1.7].

### 1.2 Findings: what a Finding *is*

**In the data model, a Finding is a persisted, identity-bearing result of evaluating an analytic condition over evidence. It is revised every time that evaluation is re-run.** It is not the condition itself.
- *Identity.* Table `finding`, unique on `(site_id, finding_key)`. It carries the domain, the mechanism, the analytic id, the asset, an anchor assessment revision, the matcher version, and links to the Finding it recurs after or was split from (`0009_finding_store.py:33-60`) [code-observed]. For the other domains, `subject_asset_id` was added (`0022`, `0025`, `0056`) [code-observed].
- *Living history.* Table `finding_revision` is append-only. Each revision records:
  - a `transition`: OPENED, SUPPORT_CHANGED, MODEL_REEVALUATED, SPLIT, MERGED, MERGED_INTO, UNCONFIRMED, NO_LONGER_SUPPORTED, BASIS_REFRESHED or REOPENED;
  - the `lifecycle` that results: SUPPORTED, UNCONFIRMED, NO_LONGER_SUPPORTED or MERGED;
  - `claim_level`, `title`, the episode bounds and minutes, and `claim` and `limitations` (both jsonb);
  - the basis, support and evidence digests, and the assessment and analytic run that produced it.

  Sources: `0009_finding_store.py:62-106`; append-only triggers `:170-174` [code-observed].
- *The lifecycle is not a column.* It is the latest revision (`0009:7-8`) [code-observed].
- *How Findings are produced.*
  - Mini-grid: a pure matcher, `finding-episode-3`, clusters Candidate segments into episodes. It opens, merges or splits them, and marks them UNCONFIRMED or NO_LONGER_SUPPORTED as later runs change the support (`analytics/finding_episode.py:1-62`, `:583-600`, `:775-802`) [code-observed].
  - Cold and EV: these map onto the same tables (`analytics/adapters/postgres_finding_store.py:43-45`, `:612-641`, `:846-901`) [code-observed].
  - Fuel: one Finding per tank night. It is OPENED, then moves to SUPPORT_CHANGED or NO_LONGER_SUPPORTED (`fuel_balance/findings_service.py:27-43`) [code-observed].
  - Every update appends a revision under a Site advisory lock (`postgres_finding_store.py:163`, `:207-225`) [code-observed].
- *Threads.* A thread is the Finding's recurrence history across episodes:
  - `finding_thread` is keyed (site, mechanism, subject), and its occurrences are Findings or opportunity studies (`0042_chain_threads.py:29-62`) [code-observed].
  - Its event states are OPEN, ACTION_IN_HAND, CHANGE_APPLIED, RESOLVED_MONITORING, CLOSED, RECURRED, REOPENED and WITHDRAWN.
  - Each event's cause is one of OCCURRENCE, ACTION_EVENT, VERIFICATION_OUTCOME, DOMAIN_CASE, CLEAN_DAYS, WITHDRAWAL or SUPPORT_LOST (`0042:64-71`) [code-observed]. **So the thread already records the user's response to a Finding**: an Action taken, a change applied, a case completed, a verdict.
  - Threads are moved by the system, as a consequence of those records (`chain/lifecycle.py:46-58`), and linked by `backfill` or `tick` (`0042:84`) [code-observed].
- *Alternatives.* Authored rival explanations of one dispatch Finding revision:
  - Kinds POLICY, UNCERTAINTY, CAPABILITY; dispositions PLAUSIBLE, CANNOT_EXCLUDE, INDETERMINATE, RULED_OUT.
  - RULED_OUT needs cited evidence that overlaps the episode.
  - They carry no quantities and no money ("claim and money are only read").

  Sources: `mini_decisions/alternatives.py:12-13`, `:45-48`, `:82-87` [code-observed].
- *Recommendation and next steps.*
  - Next-step check items are framed as "not an instruction" (`analytics/plain.py:113-116`, `:360-417`) [code-observed].
  - The one recommendation is `reserve-trial-1` (§1.3).
- *Claim limits.* A Finding claims only within its assessment's ceiling (Candidate, Necessary or Indeterminate; UNASSESSED or STALE) (`analytics/claim_limit_read.py:1-19`) [code-observed].
- *What a Finding does not carry.*
  - Money: it sits in separate per-revision consequence tables (`0011`, `0023`, `0026`, `0056`).
  - A target or threshold column.
  - A foreign key to an outcome or objective: the only link is mechanism → outcome keys in `outcome_map.ENTRIES`.
  - An owner or due date.

  Sources: [code-observed] for `0009`, `0042` and `0038`; [inferred] from the grep for `owner|due_at|assignee`.
- *Screens.* Finding lists and the Finding detail are read-only, with Overview, Analysis, Evidence and Alternatives sections, a Recommendation page and History (`frontend/src/sites/SiteFinding.tsx:1-12`, `FindingDetail.tsx:1-14`) [code-observed]. There is no acknowledge, dismiss or snooze (grep `acknowledg|dismiss|snooze|mute|false.?positive`) [inferred].

**Done well.** This is the strongest construct in the product:
- identity that is stable across re-evaluation;
- a full, append-only revision history with typed transitions;
- the recurrence thread;
- the evidence digests;
- an explicit claim ceiling.

The owner's description, "results of condition evaluation as living artifact (output)", matches the code exactly.

**Lacks, against the economic intent.**
- A Finding is linked to outcomes only through a hand-written mechanism → outcome map. It is not linked to the quantity the outcome is built from, so it cannot be placed in a bridge, and its consequence money cannot be composed with anything (`outcomes/outcome_map.py:17-23`) [code-observed].
- There is no deviation-from-plan Finding, because no plan exists at factor level (§1.5).
- Five stored mechanisms exist, all physical (`outcome_map.py:18-23`) [code-observed].

### 1.3 How a user acts on the context they are given, and how it is tracked

| Carrier | How it is created | States and events | Owner and due date | Evidence |
|---|---|---|---|---|
| **Reserve trial** (`action`) | "Accept" on the Finding's Recommendation page (`POST …/findings/{id}/recommendation/accept`). The values must equal the server's live proposal: exactly reserve − 5 points, only for a current SUPPORTED candidate Finding with SOC above reserve + 10 | Events ACCEPTED, APPLIED, FAILED, OBSERVED, RESOLVED, RESOLUTION_WITHDRAWN. Commands ACCEPT, APPLY, OBSERVE, VERIFY. APPLY publishes a new Foundation reserve revision (not a device setpoint). RESOLVED is appended only by the evaluator. Events can be read as of any past event | None: the estate row hard-codes `"owner": None, "due_at": None, "success_criterion": None` | `action_api.py:152-232`; `actions/reserve_trial.py:31-67`; `actions/lifecycle.py:23-40`; `actions/service.py:420-426`, `:504-567`; `estate/coverage.py:530`; `sites/models.py:83-89` [code-observed] |
| **Domain actions** (`domain_action`): COLDCHAIN (4 criteria), EV_CHARGING (3 criteria), MINI "Run the mill at midday" (from an opportunity), FUEL_BALANCE "Seal the tank cap …" (from an unexplained-fuel Finding) | `POST /domain-work/actions` with origin, title, `owner_label`, `due_at`, actor; then intents (success criteria) and case links | No state machine: index rows are always OPEN. For MINI and FUEL, "applied" means the linked case's first COMPLETE event. Cold and EV criteria stay at their initial NOT_TESTED / PENDING values | `owner_label` (free text, nullable) and `due_at` (nullable, ≤ 365 days). The index reports `all_due_dates_unset` | `work/domain_action.py:24-136`, `:298-309`; `0033_w5_cold_work.py:31-50`; `work/domain_action_index.py:50`, `:425` [code-observed] |
| **Work cases**: INCIDENT (INC-), MAINTENANCE_REQUEST (WR-) | `POST /work/cases`, with links to Findings and Actions | ASSIGN, COMPLETE, CLOSE, REOPEN, CANCEL, COMMENT. VERIFIED, INEFFECTIVE and INCONCLUSIVE are refused (`WORK_OUTCOME_NOT_SUPPORTED`) | The assignee is free text on ASSIGN. There is no due field. Maintenance plans have `next_due_at` / `next_due_hours`, with OVERDUE / DUE_SOON at read time | `work/model.py:27-30`, `:107-151`, `:306-336`; `0027_w4_work_cases.py:123-138`; `outcomes/plan_due.py:1-33` [code-observed] |
| **Operational records** (fuel deliveries, tank dips, meter readings, logs) | Screen entries | Append-only records | — | `work/operational_entry.py:25-30` [code-observed] |

**Commands and events.** Every write carries `actor {kind, id, attestation}`, `occurred_at` (−30 days to +5 minutes), an idempotency key and a payload hash. Refusals are typed and write nothing (`work/model.py:36-37`, `:250-292`; `work/domain_intent.py:1-17`) [code-observed].

**The Actions rail** (`/actions`, `frontend/src/shell/OperatorShellLayout.tsx:65`):
- Cards: Open actions, Due/overdue, Verification window, Verified in 30 days.
- A table of Action, Site, Source finding, Owner, State and Success criterion.
- It lists reserve-trial rows only, so Owner and Success criterion read "Not set" or "No success criterion recorded". Cold and EV are NOT_APPLICABLE (`frontend/src/estate/actionIndex.tsx:38-160`; `estate/coverage.py:494-558`) [code-observed].
- The Site Work › Actions tab lists domain actions with Owner, Due and State (`frontend/src/sites/SiteWorkActions.tsx:1-28`) [code-observed].

**Who acts: the material fact the owner should know.** The mechanism for a person to act and be tracked is built and on screen: the Accept and Apply buttons, owner and due fields, assignee, case links, thread states and the rail. **In the code, no human user is ever the recorded actor.**
- Every trial command is a SYSTEM demonstration. The actor is fixed as `service:assetops-action-demonstration`, with "no operator approval is recorded" (`actions/lifecycle.py:43-58`), and the database admits only `actor_kind = 'SYSTEM'` (`0016_action_store.py:131-132`) [code-observed].
- Work and domain writes refuse a USER actor (`WORK_USER_AUTH_REQUIRED`, `work/model.py:284-285`). They require a server-injected SERVICE principal, which `main.py` does not inject, so these writes return 403 by default. Only walkthrough tools inject one (`main.py:640-661`) [code-observed].
- There is no UI control to create a work case, a domain action, an intent, a case link, a verification plan or an evaluation. The only Finding-scoped write in the UI is Accept, plus Apply on the Action page (frontend POST grep) [inferred].

**Does the system act on its own?** No.
- There is no device or control write (grep `modbus|mqtt|setpoint|write_register|send_command|actuat|auto[-_ ]?apply`), and no notification or webhook [inferred].
- "No telemetry creates an Action or a case link" (`work/domain_intent.py:17`) [code-observed].
- The system's own steps are bookkeeping that follows a recorded act: thread transitions, the verdict and its RESOLVED event, and the scheduled judging of frozen mill plans (`scheduling/stages.py:308-329`) [code-observed].

**Done well.**
- Event-sourced, idempotent, point-in-time-readable carriers for all three verticals.
- A clean separation between what a person declares (intent, criteria) and what evidence establishes. An intent "is never an outcome" (`work/domain_intent.py:17`) [code-observed].

**Lacks, against the economic intent.**
1. No authenticated person: no decider, approver or owner identity [code-observed above].
2. Owners and due dates are empty or free text, and nothing is overdue except maintenance plans.
3. Only one option exists: a fixed −5 points, which predicts no saving (`actions/reserve_trial.py:42-45`) [code-observed]. Nothing is weighed against doing nothing, and no carrier records what was expected in money.
4. Cold and EV work cannot reach a verdict.

### 1.4 Verification

| Family | Verdict rule | Money attached | Evidence |
|---|---|---|---|
| `reserve-trial-1` | Two 60-minute windows at the same clock hour. Target: `4·later ≤ 3·baseline` candidate seconds. Guardrails: unserved critical kWh, seconds below reserve, terminal SOC. Comparability: ±10% demand and PV, ±2 SOC points | An automatic cost check, `trial-cost-check/auto`: the modelled fuel cost per kWh, before against after. MODELLED_IMPROVEMENT / NO_IMPROVEMENT / UNAVAILABLE, labelled "not realised savings". The intervention cost is fixed at 0 | `actions/verification_rules.py:28-39`, `:675-815`; `actions/verification.py:1134-1192`, `:1167`; `financials/trial_fuel_comparison.py:1-44` [code-observed] |
| `midday-productive-shift-1` (mill) | Three COMPLETE days before against three after; target `10·mean(later) ≥ 11·mean(baseline)` productive kWh. No guardrails | A VERIFIED verdict carries an estimated sales line: Δ kWh/day × the declared price | `actions/verification_families.py:12-22`, `:57`, `:175`, `:244-253` [code-observed] |
| `fuel-residual-within-band-1` | The first three COMPLETE nights out of 14 after the case completes, each with `residual_low ≤ 0 ≤ residual_high` and no sensor gap | None (`value`, `cost_check` null) | `actions/fuel_verification.py:7-14`, `:146-164`, `:343` [code-observed] |

- **Verdicts:** VERIFIED, INEFFECTIVE, INCONCLUSIVE. Read-only states NOT_JUDGED and NO_PLAN (`verification_rules.py:685`) [code-observed].
- **Fail-closed rules:**
  - an unknown family fails closed (`verification_families.py:505-510`);
  - a positive verdict admits only simulated or authored sources (`verification_rules.py:688`) [code-observed].
- **Credit rule.** Money is credited only when the cost check shows a priced positive total *and* the verdict is VERIFIED. Credited items are never summed (`outcomes/credit.py:57-73`) [code-observed].

**Done well.** Frozen plans, comparability, guardrails, fail-closed families, and money credited only after proof.

**Lacks.**
- An operational verdict only, mini-grid only.
- No economic verdict from recorded money, and no causal verdict.
- Field evidence is refused.
- The change's own cost is 0.

### 1.5 What-ifs, scenarios, replays, objectives and depth reads

- **Mini-grid what-ifs**, kinds STOP_SOC, PRODUCTIVE_LOAD, TARIFF_ONLY, OTHER.
  - Only PRODUCTIVE_LOAD calculates: energy = kW × hours, and gross sales = energy × an authored tariff, withheld if headroom is below the load (`mini_decisions/scenario_rules.py:24`, `:191-228`) [code-observed].
  - There is no baseline-against-option difference and no cost.
  - Writes are SERVICE only, and the UI is read-only ("Scenario creation unavailable") (`mini_decisions/scenarios.py:69-88`; `frontend/src/sites/MiniScenarios.tsx:34-40`) [code-observed].
  - A what-if links to a work case, never to an Action (`mini_decisions/work_links.py:58-109`) [code-observed].
- **Cold and EV what-ifs.** They are authored context with "no calculated amount … comparison delta or outcome" (`cold_scenarios/rules.py:4-7`; `ev_scenarios/rules.py:4-8`) [code-observed].
- **Opportunity study.** A five-day headroom study (SUPPORTED, LIMITED or UNKNOWN; `headroom_kw`). Demand and collection are always "UNVERIFIED" (`mini_decisions/projection.py:29`, `:202-242`; `opportunities.py:366-401`) [code-observed].
- **Scenario definitions and runs.** These are simulator inputs, not what-ifs: a scenario "answers what happens during a simulated interval" and names no Site (`scenarios/__init__.py:1-23`) [code-observed].
- **Replays.** A replay reads back what a persisted simulated run published; it does not re-simulate (`cold_replay.py:1-8`; `ev_replay.py:57-62`) [code-observed].
- **Objectives: performance to target exists, in operational form.**
  - Six measures can carry a target: MG-2 avoidable generator minutes, MG-1 productive kWh (monthly, judged for pace), MG-5 unserved critical kWh, CC-6 backup start failures, EV-1 interrupted sessions, and EV-2 energy cost per km (the one money target, never judged because nothing measures it). CC-1 takes its range from the chamber policy (`outcomes/objectives.py:57-77`; `site_outcomes/ev.py:109`) [code-observed].
  - Verdicts are MET / MISSED / NOT_JUDGED, and ON_PACE / BEHIND_PACE / TOO_EARLY. **They drive outcome status**: MISSED gives NEEDS_ATTENTION, MET gives ON_TRACK (`outcomes/objectives.py:112-143`; `outcomes/status.py:55-104`) [code-observed].
  - Only a SYSTEM declarer sets them, "for the demonstration; not a customer target". There is no owner, no period and no UI (`objectives/model.py:17-22`; `objectives/adapters/postgres_objective_store.py:104-105`) [code-observed].
- **Depth reads.** These are historical reads of the selected heads (CURRENT, PENDING_RECOMPUTE, STALE_SOURCE, HISTORICAL), and "the read never writes" (`mini_depth/read.py:1-17`) [code-observed]. Cold depth's comparison is always CONTEXT_MISSING (`analytics/cold_depth.py:287-307`) [code-observed].

**Lacks.**
- No option is valued against doing nothing, no option carries a cost, and nothing models a constraint shared across Sites.
- No objective is a customer plan.
- No money plan or budget exists (grep `budget|forecast|crew` finds nothing) [inferred].

### 1.6 The outcome map, outcome boards and the Portfolio

- **Catalogue.**
  - Four categories in canonical order: Grow, Optimize, Protect, Assure (`outcomes/catalogue.py:9`).
  - 22 Site outcomes across three verticals. Six are declared "not connected yet": MG-6 Cash collected, MG-3 Site profitability, EV-6, EV-2, CC-2 and CC-4 (`catalogue.py:43-68`) [code-observed].
- **Outcome map.** Two literals, both hand-written [code-observed]:
  - `ENTRIES`: 16 signals → the outcomes they MOVE and are CHECKED against (`outcome_map.py:17-37`);
  - `CONTRIBUTIONS`: 10 one-step node records (kpi, earnings or potential), each with a strategy and, for four of them, a price (`:149-180`).

  The list is flat: no record composes one outcome from others [inferred from the structure].
- **Outcome status `outcome-status/4`.** First match wins, over Findings, warnings, objective verdicts and opportunities. Rows are "never combined into a score" (`outcomes/status.py:55-113`) [code-observed].
- **Site outcome board.**
  - It always has four rows (`site_outcomes/board.py:671-712`). Each row carries contributors (drivers, mostly in words), issues, options, in hand, earlier, potential and nodes (`board.py:860-930`) [code-observed].
  - On screen the row columns are "What drives it", "Issues", "What can be done", "Already in hand" and "Earlier interventions", plus "Must not harm" (`frontend/src/sites/OutcomeBoard.tsx:42-48`, `:262-330`) [code-observed].
  - **This board already lays out outcome → drivers → issue → lever → action → earlier result for every Site type.**
- **Portfolio.**
  - Six tabs: Overview, Act first, Outcomes by site, Opportunity, What changed, Scope & coverage (`frontend/src/estate/portfolioWords.ts:29-37`) [code-observed].
  - The Overview has four category cards (`site_outcomes/read.py:926-977`) [code-observed]:
    - Grow: estimated income summed in one currency;
    - Optimize: each Site's cost claim, never summed. For a mini-grid this is the window's last day (`read.py:676-682`);
    - Protect: counts and unexplained-fuel lines;
    - Assure: verified count and objective coverage.
  - Act first groups Findings by placement, which says "where to look first, never a value ranking" (`estate/placement.py:1-8`) [code-observed].
- **Site overview.** One day, one chosen Finding and its consequence, "not a Site total" (`site_overview/read.py:1-46`) [code-observed].

**Done well.**
- The four categories are already the economic intent.
- The board's column order is the outcome → lever → action → result chain.
- The missing records are named on screen.
- The never-sum rules are applied.

**Lacks.**
- Outcomes are flagged, not computed: there is no amount, no plan against actual, and no composition.
- Parts of `value_cards` and the objective matrix are fixed UNKNOWN placeholders (`estate/portfolio.py:392-484`, `:564-575`) [code-observed].
- The Optimize card shows one day over a period range.

### 1.7 Money: what is estimated, what is modelled, what is recorded

| Kind | Figures | Evidence |
|---|---|---|
| **Entered by a person** (typed prices) | Three keys only: the diesel price per litre, the EV gross tariff per kWh and the productive-use price per kWh. Each has a basis tag (AUTHORED_ESTIMATE, CONTRACT_RATE, RECORDED_PURCHASE). With no default price, an uncovered instant is NO_PRICE | `financials/assumptions.py:32-58`; `financials/assumption_read.py:8` [code-observed] |
| **Estimated** (observed quantity × typed price) | Productive sales (kWh × price per day). EV gross charging income ("gross scenario only; not cash collected"). Unexplained fuel `fuel-residual-1` (the residual litres band × the diesel price) | `chain/measure_impls.py:150-161`; `financials/ev_money.py:30-43`; `financials/adapters/postgres_consequence_store.py:402-433` [code-observed] |
| **Modelled** | Possible extra fuel cost `fuel-cost-1` / `-2`: 0 up to 1.10 × Σ(kW × h × SFC) over candidate intervals × price ("not a calibrated or measured bound"). Headroom potential: kW × 1 h × price. The cost check after a trial | `financials/fuel_cost.py:22`, `:57-79`; `financials/fuel_cost_v2.py:1-60`; `chain/strategies/priced_energy.py:54-63` [code-observed] |
| **Never priced** | Cold exposure (degree-minutes only) | `financials/cold_consequence.py:7-50` [code-observed] |
| **Recorded** | None. `recorded_amount@1` "returns no money with NO_RECORDS, always". There is no billing, payment, ERP or accounting adapter, and the only HTTP client is the pre-build client | `chain/strategies/recorded_amount.py:1-10`; `chain/adapters/http_prebuild_client.py:1-10`; grep `erp|xero|quickbooks|mpesa|invoice|accounting` [inferred] |

**Gates.**
- Money eligibility.
- Currentness.
- Outward rounding.
- Current money only from the REGISTERED_SIMULATION or AUTHORED_DEMONSTRATION source classes.
- `estate_total` is always null.

Sources: `financials/money_eligibility.py:12-24`; `evidence/provenance_read.py:27-32`; `estate/financials.py:12`, `:518` [code-observed].

### 1.8 The owner's list of what is missing, tested against the code

The owner named the "clear boosters to an otherwise solid core" as: disciplined factor connection to outcome, value chain and performance to target, and financial and operational integrations.

| Owner's item | Verdict on the code | Evidence |
|---|---|---|
| Disciplined factor connection to outcome | **Missing, confirmed.** A flat, hand-written signal → outcome map, with drivers named in words on the board. Nothing composes an outcome from quantities | §1.6 |
| Value chain | **Missing, confirmed.** Only gross kWh × tariff exists. Cash and profitability are fixed "not connected yet" text | `catalogue.py:45-46`; `site_outcomes/mini.py:81-85` |
| Performance to target | **Partly present: refine the owner's item.** Operational targets exist, are judged for pace and drive outcome status. Missing: customer-declared plans, money plans, plan at factor level, and the plan-against-actual bridge | §1.5 |
| Financial integrations | **Missing, confirmed.** Prices are typed by hand, and no recorded money exists | §1.7 |
| Operational integrations | **Partly present: refine.** Telemetry is strong (gateway, ledger, reading upload) and fuel operational records exist. Missing: meter-to-customer register, storage ledger, fleet roster, OCPP log, ticketing or maintenance-system import | §1.1, §1.3 |

**Two gaps that are not in the owner's list but are of the same weight**, because the economic loop needs them:
- **(G1) No authenticated person.** No one is recorded as deciding, approving or owning (§1.3). Without this, "the user acts and it is tracked" is true in the screens but not in the records.
- **(G2) No valuation of a choice.** There is one fixed option, no comparison with doing nothing, no option cost, and the intervention cost is 0 (§1.3, §1.4).

---

## Part 2. Audit of the current design doc against Part 1

**Scope.** Every section of `layer4-transformation-design.md`, its figures and tables. Then the roadmap's §1.1, §1.2, §3.7 and Appendix A, which share the same classes.

**Format.** Items are grouped by class (W6). Each gives its location, the quoted text, what is wrong, and the evidence (the Part 1 section).

**Sweep method.** Each class was swept over both documents by reading them, then by grepping `condition|conditions on|factor key` (C1), `plan is found|search|re-compute|rides|carries the chosen|user acts` (C2), `replace|retire|no longer|becomes` (C4), and the Part 1 constructs by name (C3, C5).

### Class C1. A Finding is defined as a condition, not as the evaluated, living result it is (14 instances)

**What is wrong in general.**
- The code's Finding is the *output* of evaluating a condition: identity, a revised history, a thread and evidence (§1.2).
- The design redefines it as "a condition on a factor key". It then introduces "Findings" that are computed at read time and not stored. Such a Finding would have no identity, no revision history, no thread, and nothing an Action could originate from. That breaks the very property that makes Findings trackable.
- The right statement: a Finding is the stored, revised result of an observer evaluating a declared condition. Layer 4 *adds* the factor the condition is about. A condition the structure detects becomes a Finding only if it is stored and revised like the others.

| # | Location | Quoted text (abridged) | What is wrong |
|---|---|---|---|
| 1 | Design §2.1 figure, node FND | "Findings: conditions on factor keys … never an outcome value" | A definition, not a result; no lifecycle |
| 2 | Design §2.1 caption | "Findings, obligation bounds and rights all attach at factors" | Puts Findings in the same kind as static bounds and rights |
| 3 | Design §0.2 Figure 0.2, Layer 4 lane | "Findings: conditions on factors" | Same |
| 4 | Design §2.2 | "A Finding is an observation of a **condition on a factor key** (site, factor ID, period)" | Replaces the identity key (site, finding_key) with a factor and period key; drops episodes and revisions |
| 5 | Design §2.2 | "a condition with no physical observer … is shown as a Finding computed from the structure" | A read-time Finding cannot be revised, threaded or acted on (§1.2, §1.3) |
| 6 | Design §2.5 chain figure, node F | "Finding — a condition on a factor key" | Same as 4 |
| 7 | Design §8.4, "How a second engine is avoided" | "stored by observers, or computed from the structure for conditions with no physical observer" | Same as 5 |
| 8 | Design §8.5 table, Findings row | "conditions on factor keys; decision triggers" | Same as 1 |
| 9 | Roadmap §1.1 figure | "Findings: conditions on factor keys"; arrow "become conditions on factor keys" | **The owner's question.** It says today's Findings *become* conditions |
| 10 | Roadmap, "On one page", grounded-path row | "findings attach to factors" | Leaves out what is stored and revised |
| 11 | Roadmap §3.7, condition 1 | "A finding states a condition on a factor key" | Same |
| 12 | Roadmap §3.7 table, Finding row | "an observation of a condition on a factor key … conditions without a physical observer are computed from the structure and shown as Findings" | Same as 4 and 5 |
| 13 | Roadmap §3.7, "One structure, read from the bottom" | "a deviation finding computed from the structure" | Same as 5 |
| 14 | Roadmap Appendix A.1, Finding row | "computed at read from the structure, not stored" | Same as 5. Its "Today" cell is accurate |

### Class C2. The person who decides, acts and tracks is left out or implicit; the system appears to choose and act (13 instances)

**What is wrong in general.**
- Today a person acts on a Finding through Accept and Apply, domain actions, work cases and assignment, and that act is tracked through events and threads (§1.3).
- The design keeps this in two places only: a sentence in §2.5 ("The user acts on it and tracks it as an Action") and invariant 5 in §2.6.
- Everywhere else the loop is written as the system's work. The five mechanics (Define, Observe, Evaluate, Choose, Prove) have no actor, and "Choose" is an allocator ("The plan is found by one search"). The figures show an option "riding" an Action, with no person.
- The design also never names gap G1: today no person is recorded. It treats the act-and-track path as fully working. §0.2 names the missing approver for trials only.

| # | Location | Quoted text (abridged) | What is wrong |
|---|---|---|---|
| 1 | Design §2 loop figure | "4 Choose: a plan under budget, crews, deadlines" | No decider |
| 2 | Design §2.4, Job | "The plan is found by one search over all the decisions together" | The system chooses. The person only sets "switches" (§2.4 end) |
| 3 | Design §2.4, Identity M4 and Refusal M4 | — | No approval step in the mechanic's identity |
| 4 | Design §2.3 | "A Finding … opens a decision when a lever is declared" | Opens it automatically. Who takes the decision up is unstated |
| 5 | Design §2.5, Job | "A chosen option becomes a commitment … handed to the work carrier" | Passive voice. The person appears one sentence later |
| 6 | Design §2.5 chain figure | "Choose: the plan takes one option per decision" → "Action, which the user acts on" | The choice is the plan's, not a person's |
| 7 | Design §0.2 Figure 0.2, Layer 4 lane | "Plan within budget and crews → Action carries the chosen option" | No person |
| 8 | Design §0.2 must-change and missing lists | approver "missing" only for "a chosen option or plan" | Understates: no human actor exists for any write (`work/model.py:284`; `0016:131`) |
| 9 | Design §6.1 item 7 | "the plan visibly re-computes" | Correct as a sensitivity, but no approval follows |
| 10 | Design §7.1 Choose, "How the plan is found" | — | Same as 2 |
| 11 | Design §8.1, carriers row | "They carry the chosen option, and the user acts on and tracks it" | Asserts something today's code does not record (§1.3) |
| 12 | Roadmap §1.1 figure | "the chosen option rides an Action"; "T5 carry the chosen option as Actions" | **The owner's question.** No provision for a person is visible |
| 13 | Roadmap "On one page", path row | "The product computes; nothing is transcribed by hand" | Reads as autonomy. It means intake, but that is not said |

### Class C3. Today's mechanics are misdescribed: understated, or in places overstated (9 instances)

| # | Location | Quoted text (abridged) | What is wrong; evidence |
|---|---|---|---|
| 1 | Roadmap "On one page", first row | "Today the product starts from signals and reports what looks wrong" | Understates. Today also tracks the response and verifies it (§1.3, §1.4) |
| 2 | Roadmap §1.1 | "What is missing is everything that turns those observations into money, choices and proof" | Understates. Proof exists (three families, the credit rule), and choices exist in narrow form (§1.3, §1.4) |
| 3 | Roadmap §1.1 figure, Today lane | five boxes: analyses → Findings → exposure → one trial | Leaves out threads, objectives and status, the board, work cases, verification, and the rail |
| 4 | Roadmap §1.2, "How an outcome is read" | "Ten outcome-map rows link a signal straight to an outcome, all of kind 'moves'" | Conflates `CONTRIBUTIONS` (10) with `ENTRIES` (16, with CHECKED roles) (`outcome_map.py:17-37`, `:149-180`) |
| 5 | Design §8.1, carriers row | "four working lifecycles with owners and due dates" | **Overstates.** The trial has no owner or due date (`estate/coverage.py:530`). Domain actions have no state machine and their owner and due date are nullable. Cases have no due date (§1.3) |
| 6 | Design §0.1, "Objectives and prices" | "Objectives hold operational targets" | Understates. Targets are judged for pace and drive outcome status (§1.5). This is performance to target in operational form |
| 7 | Design §0.4 | "Most of what exists stays" with matrix counts | Silent on G1 (no person) |
| 8 | Design §1, "What exists today" | the paragraph describes observers, the map and the trial only | The act-and-track and verification core is not described as a mechanism anywhere in the document. It appears only as rows in §8 |
| 9 | Design §6.2, Before column, Overview | "top three Findings" | Accurate, but omits the pulse row and the placement reasons. Minor |

### Class C4. Layer 4 is framed as a replacement where it should extend the core, and core changes are made without a stated merit (10 instances)

**What is wrong in general.**
- The introduction says the core is "extended and re-grounded … rather than replaced".
- But the document is built mechanics-first: the core is placed on the mechanics only in §8.5, near the end. Several core constructs are changed without stating the shortfall against the objective, which the owner now requires ("for merit and intentional clearly exposing the issue against the objective").

| # | Location | Quoted text (abridged) | What is wrong |
|---|---|---|---|
| 1 | Design, "Why this revision exists" | "today's Findings, threads … are placed on them afterwards" | The structure itself relegates the core |
| 2 | Design §6.2 | "The restructure re-judges the frame and replaces the substance" | Replacement wording |
| 3 | Design §6.3 | "each tab body is replaced by the reading of the corresponding mechanic" | Same. Act first's Finding triage and What changed's tracking are useful today |
| 4 | Design §8.3 | "Portfolio spine as 'Findings ranked by placement' → replaced by the plan" | The merit case is half-stated ("ranks evidence, not choices"). Where the operator's Finding queue goes is not stated |
| 5 | Design §8.3 | "The thread as the decision anchor … → factor key; threads attach as evidence" | Demotes the construct that already records act and track (§1.2) |
| 6 | Design §2.2 | "Existing analyses are factor observers … A Finding is a statement about a factor" | Recasts Findings as inputs to the structure, not as the user's working object |
| 7 | Design §5, dispatch row | "observer of the necessary / candidate split …; no longer the value" | Fine on merit, but the change is not exposed as a change |
| 8 | Design §8.2, "Portfolio readers" row | "read the structures, attributions, decisions and plan" | Replacement, with no stated shortfall per card |
| 9 | Design §2.3 | "A decision is a choice between options about one factor, never 'the fix for this Finding'" | Changes the Finding → recommendation → Action path. The merit (gross exposure is not value) is real but not tied to the code (`fuel_cost.py:22`) |
| 10 | Roadmap §1.1 arrows | "become observers of factors", "become conditions on factor keys" | Replacement wording for the core |

### Class C5. The owner's boosters are not recognised as boosters to the core (4 instances)

| # | Location | What is wrong |
|---|---|---|
| 1 | Design title and Introduction, "The evolution it wants to inspire" | Layer 4 is "the economic decision loop". The owner's framing, a solid core plus factor connection, value chain, performance to target and integrations, is not the organising idea |
| 2 | Design §3.1 and §3.1a | The value chain appears as one row of a table, not as a named booster with its own figure on Kobo |
| 3 | Design §0.1 and §2.1 | Performance to target is treated as new ("plans are declared at factor level") rather than as an extension of the existing objectives and status (§1.5) |
| 4 | Design §4 | Operational integrations beyond telemetry (meter register, roster, storage ledger, tickets) are listed by leaf, but today's operational intake (reading upload, operational entries) is not named as the base to extend |

### Not errors (kept, checked)

- §0's honesty about money: Estimated, Modelled, no Recorded.
- The last-day Optimize figure.
- The never-sum rules.
- `recorded_amount@1`.
- The verification limits, including the cost of 0 and simulated-only evidence.
- The reserve trial's own limits.
- The what-if kinds.
- The objectives as operational.
- Scenario definitions and replays not being what-ifs.

These match Part 1. The design's §0 is the most accurate part of the document.

**Counts:** C1 14 · C2 13 · C3 9 · C4 10 · C5 4 · **50 items**.

---

## Part 3. Proposed structure for the regenerated design doc (for owner approval)

**Organising idea, in the owner's words.** The product has "an otherwise solid core" (§1.0). Layer 4 adds named boosters to it: factor connection to outcome, the value chain, performance to target, and financial and operational integrations. To those I add, with evidence, the person in the loop (G1) and choices valued against doing nothing (G2). Each change to the core is a numbered, deliberate change with its shortfall stated.

**Form.**
- About **12 pages, roughly 6,000 words**, against today's 31,300.
- Seven topics, with one key illustration each where the topic is a change; eight diagrams in all, every one of them about a change.
- **Worked example:** Kobo throughout. Kobo carries the candidate-running Finding, the reserve trial, unexplained fuel and the October bridge. Mto appears once, for the value chain's billed → collected stage, because Kobo has no collection gap of note in the demo data.

### The changes the document is about (each numbered, each justified in §6 of the new document)

| ID | Change | Shortfall against the objective (Part 1) |
|---|---|---|
| B1 | Factor connection to outcome, with the value chain | Outcomes are flagged by a flat map, never computed (§1.6, §1.8) |
| B2 | Performance to target, at factor level | Targets are operational, system-declared, and set without money (§1.5) |
| B3 | Financial and operational integrations | No recorded money; few operational business records (§1.7, §1.8) |
| CH1 | A Finding *gains* the factor it observes; a structure observer stores deviation Findings like any other | A Finding cannot enter a bridge (§1.2) |
| CH2 | An authenticated person: chooser, approver, owner and due date as records on every carrier | No human actor is ever recorded (§1.3, G1) |
| CH3 | Options valued against no action; the reserve trial becomes one option generator | One fixed option, no comparison, no cost (§1.3, G2) |
| CH4 | Verification adds economic and causal verdicts, field evidence and the option's own cost | Operational verdict only; cost 0; simulated evidence only (§1.4) |
| CH5 | The Portfolio's cards are read from the structure; the last-day Optimize figure is corrected; Act first adds the plan beside the Finding triage | Cards are counts and estimates; one day shown over a period (§1.6) |

### Outline

| § | Topic (one-line purpose) | Key illustration |
|---|---|---|
| 0 | **Objective and honesty rules**: the approved introduction; §0's evidence classes and the never-sum rules, carried over | none (a short table of evidence classes) |
| 1 | **Today's core, as it runs**: evidence → analysis → Finding (a living, revised result) → a person acts → tracked → verified → credited. What it does well and what it lacks, with code references | none: it stays, so it gets no diagram. Prose and one table; it appears as context at the edge of D2 and D5 |
| 2 | **B1: outcomes connected to factors, with the value chain**: Kobo's contribution from billed kWh × tariff − fuel − O&M − staff; CH1, Findings attach to the factor they observe | D1 |
| 3 | **B2: performance to target**: objectives extended to plans at factor level; the plan-against-actual bridge | D2 |
| 4 | **B3: integrations**: source → canonical record → leaf; emulators as placeholders | D3 |
| 5 | **The person in the loop, and choices valued (CH2, CH3, CH4)**: decide, act, track and verify with the boosters | D4, D5, D6, D7 |
| 6 | **Change register**: B1–B3 and CH1–CH5, each with what stays, the shortfall, the code evidence and the change; everything else is stated as staying | none: the register table |
| 7 | **Delivery order (CH5 on screen)**: which client screen changes first | D8 |
| App. | The other two verticals, one table each; the invariants; the decisions already taken (D-items, D1) | — |

### Diagrams: only for what changes (owner, "diagram focus")

Kobo throughout. Mto appears once, in D1, for the billed → collected stage, because Kobo has no collection gap of note in the demo data. Parts that stay appear only as greyed context at a diagram's edge.

**Method.** **M** is mermaid. **SVG** is inline SVG through `render_design_html.py`, from `motivation_figures.py`.

| ID | Type | What it shows | Change illustrated | Topic | Method |
|---|---|---|---|---|---|
| D1 | Structure / process | Kobo's records → leaves → factors → contribution, with plan against actual at every node. Today's candidate-running and unexplained-fuel Findings are pinned to their factors | B1, CH1 | 2 | SVG |
| D2 | Process, before/after | Records to plan against actual. *Before:* "N of M objectives met". *After:* the October bridge, −562.00 split by factor plus the residual | B2 | 3 | SVG |
| D3 | Process | Source export or emulator → contract test → canonical record → leaf. Today's telemetry path is edge context only | B3 | 4 | M |
| D4 | Use case | Who now decides and is recorded: the operator executive approves the plan; the site manager chooses an option and owns the Action; the technician executes and records; the analyst/owner declares plans. The system prepares and refuses but never decides | CH2 | 5 | M |
| D5 | Sequence, before/after | Kobo's candidate-running Finding through decide → act → track → verify, across the user, UI, API and stores. *Before:* Accept → Apply recorded as SYSTEM. *After:* a decision with options, the named chooser and approver, an Action with owner and due date | CH2, CH3 | 5 | M |
| D6 | Process | A decision: stop threshold, reserve change and no action as factor changes. The dawn-charge bound rejects the reserve option. The value is net of the option's cost; the person chooses | CH3 | 5 | M |
| D7 | Process | Proof: frozen prediction → after-window → operational, economic and causal verdicts. Realised money comes only from records | CH4 | 5 | M |
| D8 | Dependency strip | The order in which B1–B3 and CH1–CH5 reach a client screen | all, by order | 7 | M |

### What carries over unchanged

- The factor structure and the evidence classes.
- §0's honesty rules (never sum; weakest class; benefit only on field records).
- The Kobo figures and their checks.
- The owner's decisions: D1 (engagement path, as revised), D11, D13, D14, and the decided Q items.
- §0's code-observed findings, which Part 1 confirms.

### What is rewritten

- The Finding's definition (C1).
- Every loop figure and statement, now with its actor (C2).
- The description of today (C3).
- The extension framing and its change register (C4).
- The booster framing (C5).

### What is new

- The change register (B1–B3, CH1–CH5) and diagrams D1–D8.
- Gaps G1 (an authenticated person, owner and due date as records) and G2 (valuation against no action), named as core changes.
- Performance to target as an extension of objectives.

### What moves out of the main document

- §7's three worked portfolios: to a companion file, `worked-portfolios.md`, with the cold and EV tables and all their fig markers.
- The reconciliation in §10, §11 and §12 and the documented limits: to an appendix file.
- §8's dispositions: to `repo-reuse-and-gap-matrix.md`, which already holds them.
- "Why this revision exists" and the rev history: dropped (git keeps them).

### Machinery kept

- `check_manifest.py`: its `FIG_DOCS` and `REQUIRED` lists are updated for the new files, so every figure keeps a checked home.
- `render_design_html.py` with `<!--diagram:NAME-->`, and `motivation_figures.py` for D1 and D2.
- The `<!--fig:…-->` and `<!--figx:…-->` markers.
- `evaluate_structure.py`, `independent_model.py` and `derived-values.json`, unchanged.

### Follow-on edits

- `product-transition-and-roadmap.md` §1.1, §1.2, §3.7 and Appendix A (classes C1–C4).
- `structure-specification.md`, `domain-and-decision-models.md` and `economic-metric-and-effect-contracts.md`, wherever the Finding is defined (C1 sweep).
- `phase-plan-and-acceptance.md`, for G1 and G2 as slices.
- `repo-reuse-and-gap-matrix.md`.
- The mock-up's walkthroughs, where the person is absent.
- The go-to-market documents only where they quote §1.1.

### Decision queue (W3; my default is applied until the owner answers)

1. **Q-A1. A Finding computed from the structure.** Default: a condition with no physical observer, such as necessary running above plan, becomes a *stored* Finding with the same revision and thread model, produced by a structure observer. It is not a read-time Finding.
2. **Q-A2. The person in the loop.** Default: an authenticated user principal is a named core change (G1). The owner, the due date and the approver become records on every carrier. Who approves the plan is the operator executive. Who chooses an option within a decision is the site or operations manager.
3. **Q-A3. Act first.** Default: Act first keeps the Finding triage as its first section, with the plan beside it, rather than replacing it.
