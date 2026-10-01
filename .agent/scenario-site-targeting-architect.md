# Scenario site targeting - Architect recommendation (advisory, revision 2)

Date: 2026-10-01. Produced by **Claude under the `.ai/ROLE_CONFIG.md`
exception** (Architect bound to Claude until the Codex reset on 2026-10-03
21:23). A later reader may want to send the contract-version reading (§6) and
the refuse-or-label judgement back to Codex. This document is advisory: it was
not implemented or committed.

**Revision 2** adopts the owner's position as the target model:

> "A run binds a scenario version to a site version. ... even a default naming
> of a site should not be the case. A run is where the two are connected and a
> scenario can be reused across different sites if the site can honor the
> contract the scenario needs."

Revision 1 kept the declared `site_id` as a pre-selected "suggested site". That
is withdrawn. "What changed" at the end lists every reversal.

## 1. Facts this rests on (verified)

Carried from revision 1:

- **The rule has no owner decision behind it.** "Run setup will not choose a
  site" and "a run is not the place to retarget a scenario" live only in the
  T019 code (`runs/service.py:520-554`). No decision records them.
- **No shipped scenario is runnable on a fresh checkout.** `config/sites/` is
  empty. Every shipped scenario names `KOBO-001` or `MG-001`, which exist only
  as user-created sites in the gitignored `var/`.
- **Run setup already checks any given site against what the scenario and
  profile need.**
  - The checks are `STATE_ADDRESS_NOT_RESOLVED`, `INITIAL_VALUE_NOT_RESOLVED`
    (through the profile binding), `SITE_CONTROL_NOT_RESOLVED` and
    `SOURCE_IDENTITY_NOT_RESOLVED`.
  - KOBO-001 passed the ID check and was then BLOCKED by these checks.
- **Purpose-bearing values exist only as prose.** They appear in the
  `fuel-loss-event` TRAJECTORY oracle and in the Kobo header comments.
- **`kobo-mini-grid-60kw` gained content in T025a and T025b without a version
  bump.** It is still at v1, and the new properties are marked
  `source_version: 1`. The `hybrid-mini-grid-100kw` v2 bump in T020A is the
  precedent for doing it properly.

Verified in this revision, with bounded reads:

- **The run already is the binding.** `deterministic_identity` freezes
  `site_id` plus `foundation_version`, and `scenario_id` plus `scenario_version`.
  The run files hold no `target_site` and no policy: none of the 241 persisted
  runs mentions `DECLARED_SITE` or `target_site`.
- **Run setup is the only reader of the scenario document.**
  - `RunSetupService` reads the scenario store once (`service.py:467`).
  - Run setup refuses a request whose `scenario_version` differs from the
    stored one (`service.py:475`).
  - Execution and readback use the frozen record. `RunHeader` renders
    `scenario <id> v<n>` from it, and no run view fetches the scenario
    document.
- **The scenario store holds exactly one document per `scenario_id`.** The port
  has only `list_scenarios` and `get_scenario(id)`, and the composite raises
  `ScenarioIdentityConflict` on a duplicate ID. A superseded version therefore
  leaves the store when its successor lands. What survives of it is git history
  and the frozen run record. The run record freezes resolved parameters, causes
  and forcings, but not the purpose text.
- **The parser rejects unknown keys** (`SCENARIO_KEYS`, `_reject_unknown_keys`).
  `target_site` is a required member with a strict policy shape.
- **One invalid document fails the whole catalog.** `list_scenarios` parses
  every document in a store and raises `ScenarioConfigurationInvalid` on the
  first bad one. If `target_site` stopped being accepted, the owner's untracked
  `var/scenarios` documents would take down the Scenarios catalog and every run
  setup.
- **Documents carry no contract version.** Runs freeze
  `execution_contract_version` (currently 9, `execution_contract.py:400`).

## 2. Target model

**A scenario version declares the contract a site must honour, and nothing
else about sites.** It names no site, not even as a default. The contract has
three parts:

1. **Derived from the document.** These are the component addresses its causes
   act on (`state_key@address` in parameters and timeline), the
   `device_id`/`signal_id` of its observation sources, and the site controls it
   relies on. None of these is authored separately; they are the document.
2. **Derived from the model profile chosen at setup.** These are the typed
   properties the profile's `FoundationBinding` needs. They belong to the
   profile, not the scenario. "Can this site honour this scenario" is therefore
   always asked of a *(scenario version, profile version)* pair, never of the
   scenario alone.
3. **Authored, optional (S2): purpose assumptions.** Each one is a checked
   statement about the world, such as `generator-stop-soc-threshold@generator
   >= 85 %`, together with the reason the purpose depends on it.
   - An assumption is not a parameter. It has no value position, ownership or
     execution role, and initialization and the kernel never read it.
   - This keeps `D-2026-09-22-foundation-value-declaration` and the swap test
     intact: an assumption can fail, but it cannot answer anything.
   - Prefer bounds and relations; use equality only where the purpose quotes
     the number.

**The run is the only place a scenario version and a site version are joined.**

**Restated seam rule** (replaces the T019 docstring; to be recorded as a
decision):

> A scenario version never names a site. A site never names a scenario. A run
> joins exactly one scenario version to exactly one site Foundation version,
> chosen explicitly by the user at run setup. Run setup never infers,
> substitutes or defaults either side. It evaluates the contract (document,
> profile and assumptions) against the chosen site, freezes the result, and
> never rewrites the scenario or the site.

**Frozen provenance on the run**
- Unchanged:
  - `site_id`, `foundation_version`, `foundation_valid_from`, `site_type` and
    `timezone`;
  - `scenario_id` and `scenario_version`;
  - profile identities;
  - every resolved binding. These are the evaluated parts 1 and 2 of the
    contract.
- Added in S1: the site's recorded template lineage (`template_id`,
  `template_version`, or null for a site with no template). This is provenance
  about the site version being bound. It is not a requirement.
- Added in S2: one result per assumption (`HELD`, `NOT_HELD` or
  `NOT_RESOLVABLE`), with the frozen value and unit.
- Dropped from revision 1: "suggested site used or not", because there is no
  suggestion any more.
- Runs persisted before the change lack the added fields. Readback says "not
  recorded" and never infers them.

**Assumption not held.** I still recommend that a NOT_HELD assumption labels
the run rather than refusing it. The run is truthful about the site it ran on,
and only the purpose narrative fails. Note that this choice now also decides
the contract version (§6).

## 3. What changes because the default is gone

**`target_site` and its two policies: retire both.**
- `DECLARED_SITE` is the second binding the owner objects to, so it goes.
- `TEMPLATE_DERIVED` cannot be run today, and its only content is a
  `template_id`, so it goes too.
- **No optional template hint.** It would be a site binding in disguise:
  - a template is the origin of a family of sites, so filtering or pre-ranking
    sites by it chooses sites by lineage, not by contract;
  - this incident is the counter-example, because KOBO-001 had the right
    lineage and the wrong content.

  An author who wants to say "written with the Kobo archetype in mind" says it
  in `purpose`.
- `requirement` prose moves into an optional `site_contract.description`, in
  the block that later holds `assumptions`. The prose explains the contract and
  is never evaluated.

**Parser strictness, old and new documents.**
- New and edited shipped documents must not carry `target_site`. A guard over
  `config/scenarios` enforces this.
- **Legacy acceptance for documents already written.** The parser keeps
  accepting a well-formed `target_site` as a *legacy declaration*:
  - it is parsed, shown on the scenario detail screen as "Legacy site
    declaration; not used to bind runs", and ignored by run setup;
  - every other key stays strict, and `target_site` stops being *required*;
  - this is not optional politeness. Without it the owner's `var/scenarios`
    documents fail the entire catalog (§1).
  - **Rewriting those documents in place is the wrong fix.** Runs reference
    their versions, so an in-place edit would repeat the template mistake on
    scenarios.

  When to drop legacy acceptance is an owner decision, taken once no document
  the owner cares about still carries the key.

**`scenario_version` bump for every shipped scenario.**
- Removing `target_site` is a content change, so all seven shipped documents
  move to `scenario_version: 2` with `supersedes: 1` and a new
  `version_valid_from`.
- Verified consequences:
  - the store then holds only v2;
  - a run setup naming v1 refuses on the existing version check, which is
    truthful;
  - persisted v1 runs reload unchanged, because readback never re-reads the
    document;
  - the scenario detail screen shows v2 only, which is correct because no run
    view links to it.
- **Residual:** the v1 purpose text survives only in git. The frozen run is
  still self-describing for execution (causes, parameters, forcings).
  Retaining superseded versions in the store is a larger change and is not
  needed here; record it in the backlog as a carry.
- Pinned-digest guard per `(scenario_id, scenario_version)`, the same mechanism
  as for templates: content change without a bump fails.

**Runs already persisted against `DECLARED_SITE` versions.** These need no
migration. Their frozen identity is the join, and it never referred to the
policy. They show "template lineage: not recorded" for the new field.

**The T017 "Open target Site" bridge**
- `D-2026-09-20-scenario-detail-affordances` is amended. The bridge is removed,
  because there is no target.
- The detail screen instead shows **what the scenario needs of a site**: the
  derived addresses and sources (part 1), the assumptions once they exist
  (part 3), and the `site_contract.description`.
- **"Sites that can honour this scenario" is not on the detail screen.** The
  answer depends on a profile version (part 2), and the detail screen has no
  profile. Putting it there would need a hidden default profile, which is a
  default in another place.
- That answer lives in run setup, where the profile is chosen. The detail
  screen keeps its native "Set up a run" action.

**The site picker when nothing is pre-selected**
- Run setup opens with **no site selected**. Submit stays disabled until the
  user picks one. The picker never auto-selects, even when exactly one site is
  compatible. Each row shows:
  - the site, its Foundation version, and its template lineage with a
    staleness flag (S0);
  - from S1b, a **compatibility status for the chosen scenario version and
    profile version**: `Ready`, `Blocked (n)` with the reasons on expand, or
    `Purpose assumptions not held (n)` once S2 exists.
- Compatibility comes from **the same run-setup resolution code, run as a
  dry-run that creates no Draft**. A second matcher would drift from run setup,
  so it must not exist.
- Compatible sites may be listed first; ordering is presentation, not choice.
- **Blocked sites stay selectable.** A BLOCKED Draft is a truthful record, which
  is today's behaviour (`run-32e26cdd...`).

## 4. Revised slices

**S0: template versioning (fast lane, tiny; before T026)**
- Bump `kobo-mini-grid-60kw` to v2, with `source_version: 2` on the four
  generator properties and the status signal and mapping.
- Pinned-digest guard for shipped templates.
- Advisory staleness label on a site ("created from v1; current v2").

**S1: the run is the only join (small to medium, planned lane, USER_REVIEW;
before T026)**
- Parser: `target_site` becomes legacy-accepted and not required. Add the
  optional `site_contract.description`.
- Remove `_refuse_unsupported_target`'s policy and `site_id` branches. Keep the
  no-topology refusal.
- Shipped scenarios move to v2 without `target_site`. Add the pinned-digest
  guard for shipped scenarios.
- Freeze template lineage on the site binding.
- `EXECUTION_CONTRACT_VERSION` stays at 9 (§6, revision 3; pending owner
  sign-off).
- Observation-source resolution retires with target resolution
  (`resolve_observation_sources`, its states, the detail service's
  `SiteRepository` and the `observation_source_resolutions` payload). Without a
  site it could only report NOT_CONFIGURED.
- Frontend:
  - the site picker with no pre-selection in `RunSetupFrame`, which today
    derives the site from `targetResolution`;
  - the scenario detail screen loses the bridge and shows the derived needs.
- Record the seam decision and amend the two 2026-09-20 decisions.
- About 16 backend and frontend test files reference `target_site` or the
  policies.
- Observable result: the shipped `kobo-mini-grid-prolonged` v2 runs READY on
  GONDAR-01 and BLOCKS with named reasons on KOBO-001, and neither site was
  named anywhere but the run.

**S1b: compatibility in the picker (small; optional before T026)**
- A dry-run of setup resolution per site for the chosen scenario and profile.
- Status per picker row.
- If time presses, T026 can go ahead without it: the user picks a site and sees
  BLOCKED reasons after creating the Draft.

**S2: purpose assumptions (small to medium; before T036, or before C and D if
the owner wants the label in that demo)**
- `site_contract.assumptions` in the parser, checked for shape only.
- Run-setup evaluation against frozen values, and the frozen results.
- The Lab label "the stated purpose does not hold on this site".
- Oracles conditioned on assumption ids.
- Shipped scenarios that gain assumptions move to `scenario_version: 3`.
  - Fold S2 into S1 only if the owner wants a single version move. The
    combined slice would then be medium and would carry the refuse-or-label
    choice.

Neither S0 nor S1 moves a demo point. Both are A and B hardening that remove the
untracked-copy workaround before T026's hands-on review. **Classify S1 and S2 as
discovery rounds for Codex review**, because they change a document contract and
the run-setup outcome.

## 5. Relationship to existing seams (revised)

- **T017 parser/service split.** It gets stronger. The scenario domain no longer
  resolves any site. `resolve_target_site` and `TARGET_RESOLUTION_STATES` retire
  with the bridge.
- **T019 freezing.** Run setup is still the only component that holds a
  document and a resolved site together, and it is now the only place the two
  are named together at all.
- **Profile binding.** It still owns property needs. This is why compatibility
  is asked per profile.
- **Private expectations.** These are still never executable. In S2 they become
  conditioned on assumption ids, and tests keep pinning fixture sites that
  satisfy them.
- **Persisted runs and Lab history.** These are untouched, with no
  re-resolution on read (`D-2026-09-30-lab-cockpit-history`).

## 6. Contract-version reading (`D-2026-09-22-contract-version-scope`)

**Revision 3 ruling (2026-10-01, after T025g phase 1 stopped): S1 does not move
`EXECUTION_CONTRACT_VERSION`. It stays at 9.** This reverses revision 2 and the
contract clause of the owner-accepted `D-2026-10-01-run-binds-scenario-to-site`,
so it needs owner sign-off. I recommend the owner gives it.

**What revision 2 claimed, and why it was false.** Revision 2 said "every
persisted run keeps its frozen 9 and regenerates identically", so moving the
version was cheap. The code says otherwise (T025g phase 1, verified by the
Implementer):

- `refuse_incompatible_execution` (`execution_contract.py:428`) refuses any
  frozen version other than the build's.
- The contract-9 gate runs its 15 Drafts through that check
  (`host/execution_adapter.py:223`, `:620`). After a move to 10, every READY
  gate Draft is refused before it executes.
- Re-stamping the Drafts changes `frozen_inputs_identity`, because the version
  is hashed (`trajectory.py:496`), and with it the pinned digests.
- The Lab artifacts also embed the build version (`lab_execution.py:712`,
  `:1267`).

So a move does not leave version-9 runs regenerating. It makes every one of
them unexecutable while the kernel is unchanged.

**Why no move is the right reading, not only the cheap one.** I applied the
decision's test to the wrong object.
- **The test is about frozen artifacts.** The decision says the number serves
  "an older frozen run replayed against a newer build", and that a narrowing
  matters because an artifact frozen against a document "cannot be
  re-derived".
- **Under that test, S1 is a pure widening.**
  - With legacy acceptance, no existing document stops parsing or changes
    meaning.
  - Every run frozen under the old rule joined a scenario to its declared
    site. That join is still allowed, and it freezes identical world inputs.
  - `target_site` was never a kernel input and never entered
    `FrozenWorldInputs`.
- **The carve-out does not apply.** It covers a new construct on an executable
  path that changes how an existing one is read. S1 adds no executed construct.
  It deletes a run-setup refusal of requests, and no frozen artifact ever
  passed through that refusal into the kernel.
- **Revision 2's "refused becomes READY" argument was the one the decision
  already rejects.** Under a strict parser every change flips refuse/run for
  *some* request, so that "separates nothing". Direction is the axis, and S1
  only widens.
- **A move would make the refusal message false.** It says execution is refused
  because these rules would apply "to inputs resolved under different ones".
  For a version-9 Draft that is untrue.

**The other options, ranked.**
- **(1) Redesign the gate.** The fallback if the owner keeps the move.
  - The gate would assert that version-9 Drafts read back whole and are refused
    with the version named.
  - It would prove the kernel unchanged by executing with the build version
    pinned to 9 through a test-only monkeypatch in three modules.
  - This works, but it edits the contract-9 gate's method, so it needs owner
    sign-off too. Its cost is the false refusal described above.
- **(2) Accept both 9 and 10.** Rejected. It empties the refusal rule, and the
  number then marks nothing.
- **(4) Re-capture the gate at 10.** Rejected. It destroys the pre-change
  baseline the gate exists to keep.

**Guardrail this ruling adds (T025g AC3).** The frozen template lineage is run
provenance on the site binding. It must stay out of `FrozenWorldInputs` and out
of `frozen_inputs_identity`; otherwise adding it would itself change the gate's
pinned digests. The contract-9 gate reproducing unchanged is the proof of both.

**S2 is unchanged.** If a purpose assumption that does not hold only labels the
run (the decision's choice), adding assumptions is a widening and there is no
move.

*Revision 2's text, kept for the record:* "S1 moves `EXECUTION_CONTRACT_VERSION`
from 9 to 10 ... every persisted run keeps its frozen 9 and regenerates
identically." The second half of that sentence is false, as shown above.

This ruling is Claude's under the exception. It still goes to Codex in T025g's
retrospective review.

## 7. Owner decisions still open

Settled by the owner's position and dropped from the list: the seam rule (the
run is the only join, no default site) and keeping or renaming `DECLARED_SITE`
(retired).

1. **Refuse or label when a purpose assumption does not hold.** I recommend
   label. This also decides whether S2 moves the contract version.
2. **Whether S2 exists at all, and when.** The alternative is accepting that
   purpose prose may misdescribe a run on a site with different values.
3. **Fold S2 into S1 (one version move, larger slice) or keep them separate**
   (recommended).
4. **No template hint.** I recommend dropping it as a disguised binding.
   Confirm, or say you want an authored-against note kept as prose only.
5. **Bump `kobo-mini-grid-60kw` to v2 now (S0).** If so, decide GONDAR-01's v1
   label: recreate the site, hand-correct it, or leave it with a note.
6. **Placement.** S0 and S1 before T026 (recommended). Also whether S1b must
   precede T026 or may follow it.
7. **The legacy `target_site` acceptance window.** Decide when the parser may
   stop accepting it, and what becomes of the `var/scenarios` copies and
   KOBO-001. They are your data and no agent edits or deletes them.

## What changed from revision 1

- **Site in the scenario.** Was a declared `site_id` kept as a suggestion that
  setup pre-selects. Now no site, not even a default; the run is the only join.
- **`DECLARED_SITE`.** Was kept with a new meaning. Now retired.
- **`TEMPLATE_DERIVED` and `template_id`.** Was kept as a lineage hint. Now
  retired, with no hint, because a hint would be a disguised binding.
- **Picker.** Was pre-selected from the scenario. Now nothing is selected, the
  picker never auto-selects, and compatibility comes from a dry-run of run
  setup.
- **Detail-screen bridge.** Was "Open suggested site". Now removed; the screen
  shows what the scenario needs instead, and compatibility is shown only in run
  setup, per profile.
- **Shipped scenario documents.** Were unchanged in S1. Now v2 in S1, with v3
  for those that gain assumptions in S2.
- **Parser.** Was unchanged in S1. Now `target_site` is legacy-accepted, no
  longer required, and ignored; this is needed to keep the catalog alive.
- **Contract version.** Revision 1 said no move for S1, and revision 2 said 9 to
  10. **Revision 3 returns to no move** (§6), because revision 2's claim that
  version-9 runs regenerate was false. Owner sign-off is needed. S2 moves it
  only if assumptions refuse rather than label.
- **Frozen fields.** Were lineage plus suggested-site flag. Now lineage only in
  S1, plus assumption results in S2.
- **Verified since revision 1.** The store holds one version per scenario, run
  readback never re-reads the scenario document, and one invalid document fails
  the whole catalog.
