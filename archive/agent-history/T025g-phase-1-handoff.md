# T025g phase 1 handoff

Branch `task/T025g-run-binds-scenario-to-site`. Phase 1 landed in two commits
on top of `2297b25`, followed by this handoff. No API payload shape changed,
shipped scenarios are still v1, and the contract stays at 9.

## What landed (AC1-AC4, AC6a, AC10)

- **AC1 parser** (`scenarios/parsing.py`).
  - `target_site` is optional: parsed only when the key is present (`:372`), so
    a present-but-null or malformed one is still refused (`_parse_target_site`
    `:501`, now documented as legacy).
  - New optional `site_contract` block (`SITE_CONTRACT_KEYS` `:189`,
    `_parse_site_contract` `:470`). Its only key is `description`, free text of
    at most 600 characters. Unknown keys are refused, which keeps out any
    template hint or site id.
  - Models (`scenarios/models.py`): `ScenarioSiteContract` (`:685`),
    `ScenarioDefinition.target_site: ScenarioTargetSite | None` (`:738`), and
    `site_contract: ... | None = None` (`:743`, last field with a default, so
    existing constructors are unaffected).
- **AC2 run setup** (`runs/service.py`).
  - `_refuse_unsupported_target` is replaced by
    `_refuse_site_without_topology(site)` (`:536`, called at `:405`). Only the
    no-topology refusal remains, and the docstring states the new rule.
  - The doc for `TARGET_TOPOLOGY_UNSUPPORTED` in `runs/refusals.py` is updated.
- **AC3 lineage.**
  - `FrozenTemplateLineage(template_id, template_version)` (`runs/models.py:291`)
    is stored on `FrozenSiteBinding.template_lineage` (`:321`, default `None`).
  - Its three states:
    - `None` means not recorded (a run stored before this slice);
    - a null pair means the site has no template;
    - values give the lineage.
  - Frozen by `_freeze_template_lineage` (`runs/service.py:304`, used at
    `:912`) from `SiteRecord.template`.
  - `runs/parsing.py`:
    - rendered by `_render_template_lineage` (`:585`) only when it is recorded,
      so old documents round-trip unchanged;
    - parsed strictly by `_parse_template_lineage` (`:598`, keys
      `TEMPLATE_LINEAGE_KEYS` `:122`; both fields null or both set).
  - It is not in `FrozenWorldInputs` (`host/execution_adapter.py:208` builds
    that field by field) and not in `frozen_inputs` rows.
- **AC4.** No code change. `host/tests/contract9_gate` gives 23 passed, the
  gate is not edited, and `git status` is clean afterwards.
- **AC6a.** `test_run_setup.py::TestRefusalsAllocateNoRun`:
  - `test_a_legacy_declared_site_does_not_bind_the_run` (document names MG-900,
    the run binds MG-901, READY);
  - plus legacy TEMPLATE_DERIVED and no-`target_site` documents set up READY.
- **AC10.** `backend/tests/test_run_binds_scenario_to_site.py`:
  - every shipped document is copied in the owner's shape (new id, legacy
    `DECLARED_SITE` naming GONDAR-01);
  - each copy parses, and the composite catalog lists all of them beside the
    shipped ones;
  - `var/` is never touched.

Transitional, for phase 2 to remove:
- `ScenarioDetailService.resolve_target_site` returns NOT_APPLICABLE for a
  document without `target_site` (`scenarios/service.py:117`).
- Observation-source resolution treats it as having no target.
- `scenario_public_summary` renders `"target_site": null`
  (`simulator_lab_api.py:648`).
- No shipped document lacks `target_site` yet, so none of this is live.

## Tests and proofs

- Backend: 1373 passed. Host: 522 passed (including the new
  `host/tests/test_t025g_lineage.py`). Contract-9 gate: 23 passed, unchanged.
  `tsc --noEmit`: clean. Architecture and agent-workflow checks: passed.
  Simulator and frontend suites were not run, because phase 1 touched neither.
- Mutations, each failing its test and then reverted with `git checkout`:
  - null `target_site` treated as absent;
  - `template_id` allowed in `site_contract`;
  - `site_id` refusal restored (the no-topology test still passed);
  - lineage not frozen (5 failures);
  - absent lineage inferred as a null pair;
  - lineage leaked into `FrozenWorldInputs.site_id` (host guardrail test);
  - old runs rendered with `template_lineage: null`.

## What phase 2 needs

- **AC9.** Expose the lineage on the run readback and the Lab header.
  - The identity payload is at `simulator_lab_api.py:~1735-1745`; also update
    the client that validates it.
  - Render "not recorded" for `None`.
  - Move the three `template_lineage` entries in `test_run_setup.py:~1729`
    from `not_rendered` to `rendered` once the setup summary shows them.
- **AC8.**
  - Retire `resolve_target_site`, `TARGET_RESOLUTION_STATES`,
    `resolve_observation_sources`, `OBSERVATION_SOURCE_RESOLUTION_STATES` and
    the detail service's `SiteRepository`.
  - Remove the payloads and `scenarioCatalogClient.ts:~567/676-690` in one
    commit.
  - Decide how the catalog and detail payloads carry the legacy `target_site`
    (it is now nullable) and `site_contract.description`.
  - The client currently requires a `target_site` object.
- **AC5.** Move the shipped documents to v2 without `target_site`, add the
  guard and the fingerprint pins.
  - `test_scenario_repository.py:321-322` and `host/tests/fixtures.py` /
    `second_site.py` / `addressed_fixtures.py` still assert or use `target_site`.
  - `owner_shaped_copy` in the AC10 test asserts the shipped document has
    `target_site`. Once v2 drops it, the copy must build the legacy block
    itself, for example from a frozen v1 sample in the test.
- **AC6b, AC7.** Picker and in-process READY/BLOCKED proofs.

## Open risks

- The live UI client rejects a catalog row whose `target_site` is null. That is
  harmless now, because no such document exists. Phase 2 must change the
  payload and the client together, before any v2 document lands.
- The AC10 test derives the owner's shape from the shipped documents. It breaks
  by design in phase 2 (see above) and must be rewritten, not deleted.
- New Drafts now store `site.template_lineage` in the run document. Any external
  reader of run YAML that rejects unknown keys would need it. None was found in
  the backend, host or gate.
