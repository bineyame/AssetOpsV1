# DD1 handoff (partial)

Branch `task/DD1-operators`, worktree `/opt/assetecon/AssetOpsV1-dd1`, from `main` at `cc9d85652`. Status: **partial**
(DD1.3 and DD1.1 done; DD1.2 not started). Implementer (Claude), 2026-11-22.

## Done

- `ccb9bb0b4` DD1.3: `tools/dd_check.py`. It holds C-DD1 to C-DD20. C-DD1 and C-DD13 are live; the other 18 are stubs
  that FAIL and name the unit that makes them live.
  - The checker reads `history.json` only after its sha256 matches `golden/history_v1.json` `file_sha256`.
  - C-DD1 reads the tenants, Sites (code, type) and active `role_grant` (person, role, Site) triples by SQL. It compares
    them with the manifest's `tenants` and `demo_workflow`, mapping Site display names to codes from `tenants[].sites`.
  - C-DD13 serves the app in process for each tenant through `starlette.testclient.TestClient(create_app())`, with
    `ASSETOPS_TENANT_SLUG` set and no port. `/api/sites` must list only that tenant's own Sites, and
    `/api/sites/<other tenant's code>` must return 404.
  - Tests: `backend/tests/test_dd1_check.py`, 7 passed, no database. The plants (a moved Site manager, a missing
    person, a wrong Site type, a fourth tenant, a leaking client) each FAIL.
- `90d2e1caa` DD1.1: `onboarding/operator_file.py` now accepts `/2` beside `/1`, and maps the three verticals through
  `SITE_TYPES`.
  - A `/2` Site may also carry `devices`, `topology` and `connector_enable_schedules`. A `/2` component may carry
    `rating` and `properties`.
  - `ONBOARD_VERTICAL` has the new sentence.
  - `/1` stays strict.
  - The `/1` digests are pinned from `main`'s code: the roles digest and each Site's sha256.
  - Lakeside's `/1` file is copied to `fixtures/on1/lakeside-power.v1.onboarding.json`. `test_on1_operator_file.FIXTURE`
    now points at that copy, so the ON1 and postgres tests run unchanged.
  - Tests: `test_dd1_operator_file.py` 14 passed. With `test_on1_operator_file.py` and
    `test_on1_onboarding_service.py`: 74 passed.

## Next (DD1.2, 1.75 u), with the defaults found in pre-flight

1. Rewrite `fixtures/on1/lakeside-power.onboarding.json` to `/2`, with `valid_from` `2026-06-30T21:00:00Z`.
   - Add devices per Site (template v3's device set; Kisiwa and Mto one controller per unit).
   - Add the components those devices need (fuel-tank, battery-pcs, pv-inverter, loads).
2. Add `harvest-cold.onboarding.json` and `metro-bus.onboarding.json`.
   - People come from `demo_workflow`, including the FIELD_TECHNICIAN, because C-DD1 checks every triple.
   - Rooms take cold-lab-001's foundation with `cold-cooling-capacity` 6.
   - Depots take ev-lab-001's foundation per charger (chargers 10/4/12, two connectors each), with the §4.5 limits.
3. Write nine conversions, `backend/conversions/world/<SITE>-bindings.json`.
4. Add the apply step to `onboard_operator apply` (emulated only). It does three things:
   - calls `binding_conversion.convert`, which is already idempotent;
   - reads `store.registrations().gateways/sources[].disabled_at`;
   - runs `python -m assetops_backend.evidence.provision_gateway enable-gateway` and `enable-source --source` as
     subprocesses, only for rows that are disabled. Each enable writes an event, so calling it only for disabled rows
     is what makes a second apply change nothing.
5. `tools/world.py` L1 passes the option. Add `harvest-cold` and `metro-bus` to `world-layer4-v1.json`.
6. Postgres test `test_dd1_onboarding_postgres.py`:
   - apply all three files;
   - check that `edge-<code>` and the sources are enabled and each Site has one binding set;
   - a second apply changes no counts (`gateway_access_event`, binding sets);
   - run `dd_check --only C-DD1,C-DD13` and expect PASS.
   Then check-all, the packet, `Status: in_review`, the state entry.

## Mid-build questions (defaults applied or proposed; for the Architect)

- **Q-DD1.1** C-DD13's TENANT-1 clause (DD5.2) is reported `pending`, and C-DD13 is judged on the cross-tenant reads.
  Applied.
- **Q-DD1.2** EV foundations need `connector_enable_schedules`, which `ev_foundation._validate_schedules` refuses
  without. The spec names only devices and topology, so `/2` also accepts it.
  - Applied: the key is accepted.
  - Proposed: every connector 00:00-23:59 every day, `utc_offset_minutes` 180. `24:00` is refused, which leaves a
    one-minute gap.
- **Q-DD1.3** `provision_gateway` refuses any tenant except the constant `"demo"` (`provision_gateway.py:71`,
  `config.DEVELOPMENT_TENANT_SLUG`), so D-DD.29's subprocess cannot enable Lakeside's gateway. Proposed: compare with
  `config.served_tenant_slug()` instead (the env `ASSETOPS_TENANT_SLUG`). This is a one-line product change in
  `evidence/`.
- **Q-DD1.4** Where the apply step lives. Proposed: `onboard_operator apply --bindings DIR`, emulated only and refused
  for real files. `tools/world.py` passes `backend/conversions/world`. D-DS4.3 keeps the publish inside a product
  command, and existing tests stay unchanged.
- **Q-DD1.5** Cold compressor `rating`. The spec sets only `cold-cooling-capacity` to 6 kW. Proposed: set the rating to
  6 kW as well, as in cold-lab-001 where the two are equal.
- **Q-DD1.6** EV component and device ids. Proposed:
  - chargers `ch-e1..ch-e10`, `ch-k1..ch-k4`, `ch-r1..ch-r12`;
  - connectors `<charger>-c1/-c2`;
  - devices `<connector>-charger-controller/-connector-controller/-connector-meter`, as in ev-lab-001;
  - `feed-1` and `site-meter-1`.
- `ONBOARD_FORMAT`'s sentence still reads "version 1". It was left unchanged because §11 allows one new string only.

## Anchors

`onboarding/operator_file.py` (`SITE_TYPES`, `_component`, `site_document`); `onboard_operator.py:38`;
`sites/binding_conversion.py:137` (`convert`); `sites/foundation_service.py:204-229`; `evidence/provision_gateway.py:57-71`;
`sites/ev_foundation.py:248-300`; `tools/world.py:703-724` (L1); `backend/conversions/world-layer4-v1.json`.

## Live databases

None. No database test has run yet, and nothing was created.
