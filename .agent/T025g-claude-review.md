# T025g review - The run is the only join of scenario and site (S1)

Reviewer: Claude (Opus 5.5), a fresh reviewer instance that did not author any
part of this slice. First review, a discovery review of both phases.

Binding: Reviewer is bound to Claude until the Codex reset at 2026-10-03 21:23
(`.ai/ROLE_CONFIG.md`). Per the owner (2026-10-01), nothing waits for Codex.
Codex reviews this slice retrospectively after its reset, including the no-move
contract reading.

Target:
- Branch `task/T025g-run-binds-scenario-to-site`, diff `git diff main...HEAD`
  (head `60e83ce`, 10 commits from `7a099a8`).
- Task `tasks/T025g-run-binds-scenario-to-site.md`.
- Packet `.agent/T025g-review-packet.md` and handoff
  `.agent/T025g-phase-1-handoff.md`.
- Decision `D-2026-10-01-run-binds-scenario-to-site`, including the owner-signed
  no-move amendment.
- Architect guidance `.agent/scenario-site-targeting-architect.md`, revision 3.

## Verdict: ACCEPT WITH CARRIES

The slice does what the task asks. No shipped scenario names a site, run setup
is the only join, run setup never selects a site, the detail service holds no
Site port, and lineage is frozen as provenance outside the world inputs.

I recommend fixing F1 on the branch before merge. It is a small, latent seam
mismatch that reproduces the "one invalid document takes the catalog down"
failure this slice exists to avoid. F2 needs an explicit Planner or owner
amendment of AC6b's wording, not code. The rest are carries or nits.

## Contract reading (AC4): confirmed, no move

I agree independently that `EXECUTION_CONTRACT_VERSION` stays at 9.

- `contracts/assetops_contracts/execution_contract.py:400` is still 9. Nothing
  on the branch edits `host/tests/contract9_gate`
  (`git diff main...HEAD --stat -- host/tests/contract9_gate` is empty).
- The gate executes the frozen Draft documents in `contract9_gate/runs/`. It
  does not re-set up from `config/scenarios`, so the v2 documents cannot reach
  it. Those Drafts carry no `site.template_lineage`. `_parse_template_lineage`
  reads that as `None`, and `_render_template_lineage` emits nothing, so they
  round-trip unchanged.
- `host/tests/test_t025g_lineage.py` proves directly that four lineage
  variants give equal `FrozenWorldInputs` and one `frozen_inputs_identity`.
- Under `D-2026-09-22-contract-version-scope`, the test is a frozen artifact
  replayed against a newer build. The slice only widens:
  - legacy documents still parse with the same meaning;
  - a `TEMPLATE_DERIVED` or mismatched `DECLARED_SITE` request that used to be
    refused now sets up;
  - nothing new is executed.
- A move would make every version-9 Draft unexecutable through
  `refuse_incompatible_execution` (`execution_contract.py:407`), even though
  the kernel is unchanged. The amendment's reasoning holds.

## Findings

### F1 - Medium - An empty `site_contract` the parser accepts takes the Lab scenario catalog down in the UI

- **Where:**
  - `backend/assetops_backend/scenarios/parsing.py:495`: `description` is
    optional, so `site_contract: {}` parses to `description=None`;
  - `backend/assetops_backend/simulator_lab_api.py:650-654`: this renders as
    `"site_contract": {"description": null}`;
  - `frontend/src/shell/scenarioCatalogClient.ts:583-584`: `isScenarioSummary`
    requires `contract === null` or a string `description`.
- **Reproduced:**
  - `parse_scenario_document` of `kobo-daytime.yaml` with `site_contract = {}`,
    passed through `scenario_public_summary`, gives
    `{'description': None}`;
  - the list client checks every row with `scenarios.every(isScenarioSummary)`
    (`:670`), so that one row turns the whole catalog into `unavailable`;
  - the detail and run setup screens for that scenario also read as
    unavailable.
- **Why it matters:**
  - The backend accepts the document, `test_an_empty_site_contract_has_no_description`
    pins that acceptance, and the screen then refuses it.
  - This is the same "one document fails the whole catalog" failure mode
    that AC10 and Architect §1 guard against, now at the client seam.
  - No shipped document and none of the owner's current `var/scenarios`
    copies carry an empty block, so it is latent. It becomes reachable as
    soon as a user document is written with the new block.
  - No test crosses the seam with this shape.
- **Fix (any one):**
  - render `site_contract: null` when `description` is `None`;
  - or accept a nullable `description` in the client (`ScenarioFrame.tsx:909`
    already falls back on `??`);
  - or require `description` whenever the block is present.

  Then add an API-payload or client test with this shape.
- **Kind:** an acceptance-adjacent defect (AC1 accepts the block, and AC10's
  "catalog stays alive" intent), not a preference.

### F2 - Medium (acceptance gap, wording) - AC6b's "status source" reason is not delivered

- **Where:** `host/tests/test_t025g_join.py:125` asserts exactly four
  `INITIAL_VALUE_NOT_RESOLVED` generator reasons, and `:135` records that the
  missing status source is not blocking.
- **What is wrong:** AC6b requires BLOCKED "with named reasons covering the
  missing generator property and status source". The build names no reason
  for the status source.
- **What the packet does:** it discloses this as a Known Deviation. The
  frozen identity records the absence: no `generator-status` mapping, which
  the test asserts for publication profiles v3 and v4.
- **My view:** the deviation is the right engineering call for this slice.
  Making a missing status mapping a blocking reason would turn some
  currently-READY requests BLOCKED. That is a narrowing, which under the
  contract-scope decision would itself argue for a version move.
- **Why it still matters:** the owner's hands-on checklist and the task text
  disagree, and a reviewer cannot amend an acceptance criterion.
- **Fix:** no code. The Planner or the owner amends AC6b to "BLOCKED naming
  the four missing generator properties; the absent status source is recorded
  (no `generator-status` mapping frozen), not blocking". If the owner wants it
  blocking, that is a later slice with its own contract reading.

### F3 - Low - Shipped `site_contract.description` still states template lineage as the requirement

- **Where:** six Kobo documents, for example
  `config/scenarios/kobo-mini-grid-prolonged.yaml:40`, `kobo-daytime.yaml:35`
  and `kobo-mini-grid-stop-60.yaml:44`. Each reads "A mini-grid created from
  the kobo-mini-grid-60kw template: ...".
- **What is wrong:** the decision and Architect §3 reject lineage as the
  contract ("No template hint"; "KOBO-001 had the right lineage and the wrong
  content"). The slice's own AC6b proof shows a site created from that
  template that is BLOCKED.
- **Why it matters:** the scenario detail screen now shows this prose under
  "Site contract", so the product tells the reader the opposite of what run
  setup checks.
- **Mitigation:** it is prose, never evaluated, and the packet lists it as a
  residual risk. AC5 says the prose "may" move, so moving it verbatim is
  allowed.
- **Fix:** none needed now. Rewording means a v3 bump under the new
  fingerprint guard, so carry it to T025i (purpose assumptions), which bumps
  these documents anyway. Reword it then as "a mini-grid whose Foundation
  declares ...".

### F4 - Low - Layout evidence for the run header's new fact was not run

- **Where:** `frontend/src/shell/RunHeader.tsx:60-65` adds the "Site template
  lineage" fact to the Lab run header, a shell and header surface.
- **What was not run:** the packet states that `tools/layout-evidence.mjs`
  aborted at its MG-006 user-scenario section. Its run detail and cockpit
  checks were therefore not run. The packet records this honestly as unverified
  rather than as a pass.
- **Carry:** run the tool's run detail and cockpit sections against a stack
  that holds an MG-006-shaped user scenario, or make that section skip with a
  recorded reason. Until then, header wrap at 640 px is unproven.

### F5 - Low (documentation) - The Architect guidance mislabels its own revision

- **Where:**
  - `.agent/scenario-site-targeting-architect.md:1` still says "revision 2"
    while carrying the revision 3 ruling;
  - `:235` still says "pending owner sign-off", although the owner signed off
    on 2026-10-01.
- **Fix:** relabel the title as revision 3 and drop "pending owner sign-off".
  This matters only for a cold reader, such as Codex's retrospective.

### F6 - Nit - Leftover "target Site" wording, five blank lines, awkward picker copy

- **"Target site" wording:**
  - `backend/assetops_backend/scenarios/parsing.py:1748` is a user-facing
    refusal message that still says "the target site's foundation";
  - docstrings at `parsing.py:93` and `:1730-1736`,
    `scenarios/models.py:230`, `:270` and `:534`, and
    `runs/profiles.py:454` say "target Site".

  These should say "the chosen site".
- **Blank lines:** `backend/assetops_backend/simulator_lab_api.py:494-498`
  has five blank lines where `scenario_observation_source_resolution` was
  removed.
- **Picker copy:** `frontend/src/shell/RunSetupFrame.tsx:1037` reads
  "Created from template: Not created from a template" for a site with no
  template. This is a preference.

## Acceptance criteria, checked

1. **Parser. Met.**
   - `target_site` is parsed only when present (`parsing.py:370-374`), so a
     null or malformed one is refused.
   - `SITE_CONTRACT_KEYS` contains only `description`, and unknown keys are
     refused.
   - See F1 for the empty-block seam.
2. **Run setup. Met.**
   - `_refuse_unsupported_target` is replaced by
     `_refuse_site_without_topology(site)` (`runs/service.py:536`), which takes
     no scenario argument.
   - The docstring states the rule.
   - A grep shows no production reader of `scenario.target_site` outside
     parsing and the legacy payload.
3. **Lineage frozen. Met.** It is frozen from `SiteRecord.template`
   (`runs/service.py:304`), parsed strictly, and absent for older runs. It is
   kept out of `FrozenWorldInputs` and the identity (see the AC4 section).
4. **Contract stays at 9. Met and confirmed** (see the AC4 section).
5. **Shipped v2. Met.**
   - All seven documents are v2, `supersedes: 1`, valid from 2026-10-01.
   - `test_scenario_fingerprints.py` pins each document and guards against
     `target_site`, `site_id` and `template_id`.
   - Both guards have non-vacuous tests.
6. **Join proof.**
   - (a) Met.
   - (b) Met except the status-source wording (F2). I checked the pre-T025a
     fixture against `git diff c0f49ce 0dc42c0`: four generator properties,
     the `status` signal and the `generator-status` mapping, exactly.
7. **Picker. Met.**
   - `chosenSiteId` is set only by `onChoose`.
   - Create is disabled with a reason until a site is picked.
   - No row is disabled, and the staleness note comes from
     `TemplateProvenanceText`.
   - Tests cover a lone site, a legacy declaration and a failed Foundation
     read.
8. **Scenario detail. Met.**
   - Every named symbol is retired.
   - `ScenarioDetailService(repository)` takes no Site port.
   - `scenario_site_needs` derives the needs from the document only.
   - The legacy label is shown, and `Open target Site` is gone.
   - The Site Controls statement is correct: control needs belong to the
     model profile (`runs/service.py:2025`).
9. **Run readback. Met.**
   - `template_lineage_payload` reads only frozen state.
   - The client validator is strict about each state.
   - The lineage is shown in `RunHeader` and in the setup summary.
10. **Catalog alive. Met** for the owner's shape, which is legacy
    `target_site` with no `site_contract`. F1 is a different shape.

## Checks I ran (serially, on `60e83ce`)

| Check | Result |
|---|---|
| `tools/check-architecture.ps1` | passed |
| `tools/check-agent-workflow.ps1` | passed |
| `pytest backend/tests -q` | 1374 passed |
| `pytest host/tests/contract9_gate host/tests/test_t025g_join.py host/tests/test_t025g_lineage.py -q` | 31 passed (gate 23 + join 6 + lineage 2) |
| `npx.cmd tsc --noEmit` (frontend) | clean, exit 0 |
| `npm.cmd test -- --run` (frontend) | 39 files, 1021 passed |
| `npm.cmd run build` (frontend) | built, exit 0 |
| Probe: an empty `site_contract` through `scenario_public_summary` | `{'description': None}` (F1) |

- The frontend suite and the build **did run** in this session. The esbuild
  ancestor-directory sandbox failure did not occur this time. The numbers
  above are my own.
- `git status` was clean apart from the owner's untracked `Docs/` files, both
  before and after the runs.

## Not verified

- **Suites I did not rerun:** the full host suite (528) and the simulator
  suite (227). The diff touches no simulator code. I reran only the gate and
  the T025g host tests.
- **Runs that need a live stack:**
  - the per-commit check against a live backend, with no broken live UI on
    any phase-2 commit;
  - the CDP layout measurements;
  - the `layout-evidence.mjs` run.

  All three need Chrome, uvicorn and Vite on an isolated store. I take them as
  the packet's claims, not as my findings.
- **Mutations M1-M9:** not re-executed. I read the guards they target, and
  each one is non-vacuous on its face.

## Residual risk not already in the packet

- **A new run key, checked against older builds.** Every new Draft now writes
  `site.template_lineage`.
  - On `main`, the stored-run parser checks unknown keys only on the request,
    the interval and the profiles, not on `site`. An older checkout should
    therefore ignore the key rather than refuse the Draft.
  - I checked this by reading the parser, not by running it.
- **The picker reads each site's Foundation version once, at mount.** If a
  site's Foundation moves while the screen is open, the request carries the
  stale version, and run setup's version check refuses it. That is truthful,
  but the person sees a refusal instead of a refresh. This behaviour is
  unchanged from before.
- **`test_every_shipped_scenario_is_v2_superseding_v1`** (`test_scenario_fingerprints.py:143`)
  hard-codes v2. The next bump (T025i) must edit it as well as the pin, which
  is intended friction but worth knowing.
