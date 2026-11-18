> Moved verbatim from the former `.ai/DECISIONS.md` on 2026-11-18 (declutter step 2), part 2 of 4; parts concatenate in this order: 2026-10-late.md, old-index-2026-10.md, 2026-09.md, 2026-10-early.md. Index: `INDEX.md` in this folder.

## Decision Index For Agent Context

Use this index to find only the decisions relevant to the active task. Keep
newest task-routing state in `.ai/ACTIVE_CONTEXT.md`; keep full decision
rationale in the dated entries below.

Lab cockpit decisions (owner accepted 2026-09-30):

- `D-2026-09-30-lab-cockpit-cadence`: L1a then L1b, sequentially before T026;
  conditional L2 in each owning slice and feedback-selected L3.
- `D-2026-09-30-lab-cockpit-history`: persisted host-owned history and gated
  projections; no implicit re-execution on read.
- `D-2026-09-30-lab-cockpit-presentation`: accepted timing, missingness, SLD
  reuse, playback and mockup annotations under existing seams.

Current direction correction: `D-2026-09-24-v4-roadmap-replan` supersedes the
old demo readiness/sequence and ambiguous sampling shorthand identified below.
Earlier dated entries remain history; `.ai/CODE_STATE.md` records what shipped.
Old pointers below to the feature-map execution-version ledger are historical:
the forecast was removed; relative version guidance is now in
`.ai/PLANNING_HANDOFF_T020A_T023.md`, Contract Versions And Retirements.

| ID | Date | Subject |
| --- | --- | --- |
| `D-2026-10-18-w2-05-buildspec` | 2026-10-18 | W2-05a/05b packets and code-anchored EV Foundation/producer specs. |
| `D-2026-10-18-w2-04-buildspec` | 2026-10-18 | W2-04 packet and code-anchored unpriced cold consequence/read/UI spec. |
| `D-2026-10-17-w2-02-buildspec` | 2026-10-17 | Nine W2-02 answers and code-anchored W2-02/W2-03 build specs. |
| `D-2026-10-18-w2-mockup-authority` | 2026-10-18 | Owner: v6.9 W2 cold and EV mock screens are binding visual and content authority; "extrapolation" tags mean only no v6.9 spec section. |
| `D-2026-10-17-f5-subtabs-and-contact` | 2026-10-17 | F5 mock in-page rows and Site Findings chips; W2-01 cold contact null closure. |
| `D-2026-10-17-w2-01-answers` | 2026-10-17 | W2-01 A–I closure and W2-02/W2-03 code-seam pre-check. |
| `D-2026-10-17-mockup-layout-spec` | 2026-10-17 | Binding v69 panel layout for W1 rework and W2+ UI; exact structure test, 1440/390 comparisons and High severity for structural drift. |
| `D-2026-10-17-w2-techdesign-ev` | 2026-10-17 | Amended W2-05a/05b/06/07 EV contract and exact ten-screen panel layout; OCPP peer deferred to pilot; owner EV visual and scope decisions pending. |
| `D-2026-10-17-w2-techdesign-cold` | 2026-10-17 | Amended W2-00 source format, W2-01..04 cold-chain contract and exact twelve-screen panel layout; owner scope pending. |
| `D-2026-10-17-w2-design` | 2026-10-17 | W2 cold-chain/EV architecture and simulator delivery plan; scope, core panels and demo values pending owner. |
| `D-2026-10-17-w1-rail` | 2026-10-17 | Full v69 operator rail inventory; only Sites and Findings link in W1, with gated Lab footer and route-proof guards. |
| `D-2026-10-17-w1-ux-06` | 2026-10-17 | W1 Readiness and Health labels preserve configuration, contact and fact-age boundaries. |
| `D-2026-10-16-s408` | 2026-10-16 | Site consequence history includes unpriced versions; cutoff head classification is separate from current-money authorization. |
| `D-2026-10-16-w1-ux` | 2026-10-16 | W1 separate contextual analysis, narrow reference disclosures, approved domain labels and honest-state-first plain language. |
| `D-2026-10-04-plain-language-analysis-views` | 2026-10-04 | Owner-directed plain-language defaults, assessment graphics and separate Analysis tabs in T028; amends practitioner-first presentation and the Finding tab inventory; product vocabulary guard. |
| `D-2026-10-04-practitioner-first-finding-presentation` | 2026-10-04 | Findings lead with a bounded operational explanation; provenance and method detail remain accessible through progressive disclosure. Narrow T028 correction before merge; money and prepared demo remain T029. |
| `D-2026-10-04-analytic-readiness-scope-and-gap-impact` | 2026-10-04 | Analytic readiness describes evidence sufficiency, site-wide in T028; claim-dependent gap treatment is interim, with versioned configurable impact types assigned to T028A. |
| `D-2026-10-02-demo-led-recommendation` | 2026-10-02 | Owner approved `.ai/ARCHITECT_DEMO_RECOMMENDATION.md` at `57ea23e` ("review looks fine."); D1-D8 verbatim; section 9 outcomes are the coordinator's reading; its sequence supersedes the 2026-09-24 queue order from T027. Recorded by the Planner (Claude under the Codex exception). |
| `D-2026-10-02-rendered-tabs-per-capability` | 2026-10-02 | Rendered tabs are meaningful destinations decided per capability, not per site; "labelled in place" is not used in operator views; rendered Site tabs by milestone. Amends the 2026-09-13 canonical-fidelity and 2026-09-17 Foundation entries. |
| `D-2026-10-02-grammar-ownership-test` | 2026-10-02 | A place keeps its slot only if it owns something no other place shows; exceptions recorded; tasks citing overridden v6.9 text cite the decision; grouped rail is target, filtered to live items. |
| `D-2026-10-02-presentation-profile-and-capability-declaration` | 2026-10-02 | Presentation profile is static substrate data keyed by `site_type` (presentation only); the backend analytic capability declaration (T028) owns Finding types, evidence requirements and verification rules; three rendering rules. |
| `D-2026-10-02-demo-point-seed-rule` | 2026-10-02 | Each demo point ships an idempotent, rehearsed seed owned by the slice that creates it, checked with the Lab gate off. |
| `D-2026-10-02-delay-is-a-reporting-path-cause` | 2026-10-02 | A delayed publication is a scenario-declared reporting-path cause the publication profile answers for, like a reporting gap; it never changes value or source time, and one that would reorder publications is refused (release order is T026A). Architect ruling (Claude under the Codex exception). |
| `D-2026-10-02-scenario-states-override-issuer` | 2026-10-02 | A scenario control override is published as an operator-commanded override record only when its scenario EVENT entry declares `issued_by: OPERATOR` (optional, refused on any state but the stop-threshold and battery-reserve forcings); absent means no operator command, so no record. Who issued a change is a world fact the scenario states, not something the publication layer infers from the state key. `kobo-mini-grid-degraded-evidence` v1 declares it (re-pinned in-branch); `kobo-mini-grid-stop-60` is unchanged and publishes none. Contract stays 9. Owner signed off 2026-10-02; recommendation `.agent/T026-C1-architect-note.md`. |
| `D-2026-10-02-template-bump-record` | 2026-10-02 | A shipped template records a bump by `template_version`, pinned fingerprint and header note; `supersedes`/valid-from in `D-2026-10-01-run-binds-scenario-to-site` apply to scenarios only. A new device signal is template content: Kobo goes to v3 in T026. Owner signed off 2026-10-02. |
| `D-2026-10-01-run-binds-scenario-to-site` | 2026-10-01 | A run is the only join of a scenario version and a site version; `target_site` retired with legacy acceptance; no template hint; assumptions label; content change bumps version under a fingerprint guard. Contract clause amended 2026-10-01: no move, version stays 9 (owner signed off 2026-10-01). |
| `D-2026-09-24-v4-roadmap-replan` | 2026-09-24 | Corrected two-source basis; roadmap A-I, dispatch first, immediate component addressing; Planner recreates unfinished tasks. |
| `D-2026-09-24-task-spec-size-ceilings` | 2026-09-24 | Task-spec size bands become ceilings with no minimum, plus a cold-start test. `.ai/WORKFLOW.md` is their only owner. |
| `D-2026-09-11-stack` | 2026-09-11 | M1 uses the preferred MVP stack from the product specification. |
| `D-2026-09-11-simulator-gate` | 2026-09-11 | Simulator Lab is gated by `simulator_lab.enabled`. |
| `D-2026-09-11-workflow` | 2026-09-11 | AssetOps uses Architect/Planner, Implementer, Reviewer, and user-review workflow. |
| `D-2026-09-13-site-foundation-persistence` | 2026-09-13 | Persisted Sites, shipped templates, user-created Sites, and a swappable persistence adapter. |
| `D-2026-09-13-site-foundation-resequence` | 2026-09-13 | Site Foundation step 3 is template catalog, create from template, then read-only Site Configuration. |
| `D-2026-09-13-template-and-create-surfaces-gated` | 2026-09-13 | Template browsing and simulated Site creation are Simulator Lab surfaces behind the gate. |
| `D-2026-09-13-canonical-fidelity` | 2026-09-13 | Canonical mockup fidelity is staged after each surface has truthful content. Amended by `D-2026-10-02-rendered-tabs-per-capability`. |
| `D-2026-09-13-shared-site-substrate` | 2026-09-13 | Operator and Lab Site pages share one substrate at `frontend/src/sites/`. |
| `D-2026-09-13-provenance-status-vocabulary` | 2026-09-13 | Source mode, lifecycle, configuration origin, evidence readiness, and source health remain separate. |
| `D-2026-09-13-t006-preimplementation` | 2026-09-13 | T006 pre-implementation decisions for runtime gate proof, created Site shape, and non-loosening guard updates. |
| `D-2026-09-17-timezone-validation-timing` | 2026-09-17 | Real IANA timezone membership validation is required before timezone becomes executable behavior. |
| `D-2026-09-17-source-health-backing` | 2026-09-17 | Gateway/source health is backed by source observations, not Site lifecycle or simulator provenance. |
| `D-2026-09-17-site-foundation-fetch-seam` | 2026-09-17 | The Site Foundation frontend/backend fetch seam needs a focused integration test before expansion. |
| `D-2026-09-17-client-demo-readiness` | 2026-09-17 | Historical readiness ladder; superseded by D-2026-09-24-v4-roadmap-replan. |
| `D-2026-09-17-foundation-screen-architecture` | 2026-09-17 | The operator Site surface formerly called Site Configuration becomes Foundation, with line-cited Site tabs, filtered Foundation subtabs, route compatibility, and inventory guards. Amended by `D-2026-10-02-rendered-tabs-per-capability`. |
| `D-2026-09-20-layout-evidence-standing` | 2026-09-20 | Browser layout evidence is standing closeout evidence for layout-sensitive slices, kept outside the portable architecture runner. |
| `D-2026-09-20-no-merged-task-status-guard` | 2026-09-20 | No guard ties a merged slice's task status to branch state; closeout discipline stays manual until the drift recurs. |
| `D-2026-09-20-breaker-vocabulary` | 2026-09-20 | A breaker is topology and, when instrumented, a reported-about thing; position is evidence, not Foundation configuration. |
| `D-2026-09-20-scenario-definition-model` | 2026-09-20 | ScenarioDefinition is the saved, versioned scenario artifact; events are saved sub-artifacts inside a scenario version. |
| `D-2026-09-20-scenario-definition-storage` | 2026-09-20 | ScenarioDefinitions use composed shipped and writable stores behind a domain port, with one disjoint scenario_id space. |
| `D-2026-09-20-run-scoped-event-injection` | 2026-09-20 | Future event injection is run-scoped intervention history, not authored scenario content. |
| `D-2026-09-20-scenario-detail-affordances` | 2026-09-20 | Scenario detail renders only native controls; Run is disabled with a named prerequisite and downstream controls are absent. `Open target Site` removed by `D-2026-10-01-run-binds-scenario-to-site`. |
| `D-2026-09-21-scenario-authoring-semantics` | 2026-09-21 | The T017 checkpoint settles scenario versioning fields, the event taxonomy, and the public/private parameter boundary. |
| `D-2026-09-21-causal-runtime-before-golden-traces` | 2026-09-21 | A minimal executable causal runtime precedes authoritative golden traces; manual traces cannot establish scenario causality. |
| `D-2026-09-21-scenario-execution-contract` | 2026-09-21 | The T018 checkpoint settles execution roles, initialization and cadence ownership, timing and bound semantics, and that an unreached reading is stated rather than resolved. Amended by `D-2026-09-21-scenario-execution-contract-amendment-1`. |
| `D-2026-09-21-scenario-execution-contract-amendment-1` | 2026-09-21 | Amendment 1 to the execution contract: simultaneous causes net rather than order; the contract-version bump policy; run setup stops adjudicating cause-to-observation coupling; a scenario does not author what a device reads; `execution_requirement` is forbidden on a reported observation; a fifth `TRAJECTORY` oracle kind. |
| `D-2026-09-21-run-setup-outcome-vocabulary` | 2026-09-21 | `BLOCKED` is the shipped run-setup outcome, now on three reasons; the Fuel Loss residual splits into two scheduled decisions with different deadlines; `READY` discloses what it does not assert and T021 verifies it against the kernel. Extended 2026-09-22: the refusal line moved to who failed to answer, four location failures block as `INITIAL_VALUE_NOT_RESOLVED`, and the contradiction refuses as `INITIAL_VALUE_ANSWERS_DISAGREE` because the frozen identity can hold no answer and not two. Its one consequence about a Foundation declaring no such property at all is superseded by `D-2026-09-22-foundation-property-absent-blocks`: that case blocks. |
| `D-2026-09-21-projection-versus-composition` | 2026-09-21 | Projecting a document is static validation; composing projections into a value-at-a-time is a kernel, whatever the component is called. |
| `D-2026-09-21-specification-reference-implementation` | 2026-09-21 | A specification's reference implementation is labelled and carries a stated expiry; `reconcile_reported_observations` stops being an authority when a kernel is compared against it, and leaves the repository when its last product-path caller goes. |
| `D-2026-09-21-physical-property-ownership` | 2026-09-21 | Foundation declares what the site is, the model profile how the simulator reasons, the scenario what happens, the publication profile how the reporting installation behaves; two swap tests decide ownership, and a new slice T020A builds the missing carriers. Its template-copy consequence is corrected by `D-2026-09-22-foundation-property-absent-blocks`: a non-re-created MG-001 blocks, it does not refuse. |
| `D-2026-09-22-expiry-follows-the-condition` | 2026-09-22 | A gap-covering artifact names the condition as its expiry, never a slice number; a claim that has become false goes in the slice that falsifies it, and a thing still honest goes when someone decides to remove it. |
| `D-2026-09-22-foundation-value-declaration` | 2026-09-22 | A scenario parameter whose declared owner is Site Foundation has no value position at all. The rule is keyed on the owner, so it reaches `tank-capacity` as well as the coefficient, moves the contract version, and retires `INITIAL_VALUE_ANSWERS_DISAGREE` in T020A. Option C is a named follower. |
| `D-2026-09-22-consumption-coefficient-unit` | 2026-09-22 | The Foundation coefficient is specific fuel consumption in `L/kWh`, and `dispatched-output` is promoted to a `FORCING_INPUT` on `generator-output-power`. `L/h` is a property of machine times operating point and half that pair is the scenario's. Closes open question 4.1. |
| `D-2026-09-22-forcing-state-requirements` | 2026-09-22 | `site-load-demand` and `plane-of-array-irradiance` drop to `OPTIONAL`; reporting-path authority moves to the publication profile. The shipped Fuel Loss Event becomes able to reach `READY`. Two riders: a requirement conflict is refused rather than resolved, and `FROZEN_INPUT_ANSWERERS` gains `PUBLICATION_PROFILE`. Closes open question 3. |
| `D-2026-09-22-kernel-step-semantics` | 2026-09-22 | The four semantics the contract left open: linear ramp across a window, sampling (clarified by v4 section 6 and D-2026-09-24-v4-roadmap-replan), a forcing outside its window is unavailable, and a bounded change lets the run continue against the bounded value. Closes open question 1. |
| `D-2026-09-22-reconciliation-panel-retirement` | 2026-09-22 | The `observation_reconciliation` panel goes with (f) in T022, which completes (j) by taking the reference implementation, `declared_bounds` and `IMPLICIT_LOWER_BOUND_DIMENSIONS` out of the product path. Closes open questions 5 and 11. |
| `D-2026-09-22-capacity-bound-source` | 2026-09-22 | A bound's declaration is the document's and its value is the site's. `declared_bounds` reports no upper value for `fuel-tank-volume` after T020A and that is the correct answer; the number lives in the frozen run and the first thing entitled to hold both halves is T021's kernel. |
| `D-2026-09-22-foundation-property-absent-blocks` | 2026-09-22 | A Foundation that declares no such property at all blocks with `INITIAL_VALUE_NOT_RESOLVED`. It is a fifth case of the four, not a refusal, because after T020A the binding names the property and a different profile might name another. |
| `D-2026-09-22-milestone-speed-over-purity` | 2026-09-22 | Speed over pedantic purity for the rest of the simulator milestone; a complete review, possibly a refactor, follows milestone completion and proper testing. Stop only for a defect expensive to reverse, a claim that would mislead an Implementer, or a decision only the user can take. Everything else is recorded to `.ai/MILESTONE_REVIEW_BACKLOG.md` and carried. **Governs every slice, pass and review after it.** |
| `D-2026-09-22-contract-version-scope` | 2026-09-22 | `EXECUTION_CONTRACT_VERSION` moves when a change can alter the outcome for a document that was already valid. A narrowing can; a pure widening off every executable path cannot, so the `TRAJECTORY` oracle kind does not move it. The absolute numbers are unstable and are written relatively. |

