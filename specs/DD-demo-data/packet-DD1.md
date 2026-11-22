# DD1 packet: three operators (DD1.1, DD1.2, DD1.3)

Branch `task/DD1-operators`. Implementer (Claude), 2026-11-22. Status: `in_review`. `USER_REVIEW_REQUIRED: false` for DD1
(no screen; the owner's open DD questions are unchanged).

## Commits (DD1.2 adds two; earlier `ccb9bb0b4` DD1.3 and `90d2e1caa` DD1.1)
- `7d77b82af` the three `/2` files, nine conversions, `provision_gateway` served-tenant guard (D-DD.35), `24:00` schedule
  end (D-DD.39), Site document bounds.
- next commit: `onboard_operator apply --bindings DIR` (D-DD.36), the Postgres test, the template node ceiling, packet and state.

## What was built
- `backend/tests/fixtures/on1/{lakeside-power,harvest-cold,metro-bus}.onboarding.json`, all `/2`, `valid_from`
  2026-06-30T21:00:00Z. People from `demo_workflow` (all seven roles incl. FIELD_TECHNICIAN), emails `<name>@<slug>.example`.
  Lakeside's roles digest is unchanged. Metro is written compact (154 KB; the file bound is 256 KiB).
- Lakeside: template v3's components, properties and devices per Site; the manifest's ratings (PV, battery, reserve, set
  ratings, SFC) over them. Kisiwa: `gen-ks-01/02` and `gen-ks-0x-controller`; Mto: `inv-mt-01/02` and
  `inv-mt-0x-controller`. Kobo is the template as is (data-sheet values arrive in DD3.2).
- Cold: cold-lab-001's 13 values and devices per room, compressor rating and `cold-cooling-capacity` 6 kW (D-DD.37).
- EV: ev-lab-001 per charger, ids and display names of D-DD.38, import limit and charger/connector ratings from `physical`
  (Embakasi 500/60/60, Kasarani 250/50/50, Ruiru 400/60/60), seven `00:00-24:00` entries per connector, UTC+3 (D-DD.39).
- `backend/conversions/world/<SITE>-bindings.json` x9 (`minigrid-roles-4`, `cold-roles-1`, `ev-roles-1`), one binding per
  declared device signal, `effective_from` 2026-06-30T21:00:00Z.
- `provision_gateway`: the guard compares `served_tenant_slug()` (D-DD.35). `ev_foundation`: `24:00` as a day's end.
- `onboard_operator apply --bindings DIR` (D-DD.36): missing `<CODE>-bindings.json` refuses `ONBOARD_SITE_INVALID
  bindings/<CODE>` before any write; per Site `convert`, then `provision_gateway enable-gateway` / `enable-source` in
  process, only for rows with `disabled_at`. A conversion refusal prints `BINDING_CONVERSION ...` and exits 3.

## Tests (worktree host runner; revision at run: `7d77b82af` plus the apply commit)
- `tools/heavy-slot.sh --db -- pwsh tools/run-host-tests.ps1 -- <files>` from `backend/`: DD1 files (`test_dd1_check`,
  `test_dd1_operator_file`, `test_dd1_operator_files`, `test_dd1_provision_guard`, `test_dd1_onboarding_postgres`) plus
  `test_on1_operator_file`, `_onboarding_service`, `_onboarding_postgres`, `_served_tenant`, `test_w205a_ev_foundation_postgres`,
  `test_site_parsing`, `test_foundation_content_parsing`: **325 passed, 2 failed** before the template ceiling fix; after it
  `test_foundation_content_parsing`, `test_site_template_parsing`, `test_site_parsing`, template fingerprints: 218 passed.
  Wall 61 s for the first run.
- `test_dd1_onboarding_postgres.py` (4): harvest-cold and metro-bus apply with bindings: every gateway `edge-<code>` and
  every source enabled, one binding set per Site, a second apply leaves event and binding counts equal; a missing
  conversion refuses before any write; the Lakeside cases are listed under round 2.
- `tools/dd_check.py`: C-DD1 and C-DD13 are live; C-DD2 to C-DD12 and C-DD14 to C-DD20 are stubs that FAIL and name their
  unit. It was not run against a database here: an operator database holds one operator (`ONBOARD_DATABASE_NOT_EMPTY`), so
  C-DD1 over three tenants needs the DD6 world clone. Its unit tests (7) pass.
- Fast check-all (`-Fast`, node_modules symlinked then removed; 122 s wall): 40 of 42 blocking guards PASS; the two failures
  were the statement catalogue (SC-1) and its self-test, from new and changed hand-built strings (the D-DD.35 refusal, the
  DD1.1 `ONBOARD_VERTICAL` sentence, `BINDING_CONVERSION`). Fixed by re-hashing those entries in
  `tools/checks/statement-handbuilt-baseline.json` (ratchet count unchanged); the guard now prints OK. The `--self-test`
  was started again after the fix (see the review for its result); the full check-all was not re-run.

## DD1.2 round 2 (D-DD.41 to D-DD.43; branch merged with main first)
- `binding_roles.py`: `ROLE_SET_MINIGRID_5`/`MINIGRID_ROLES_5` (roles-4 with the five unit roles PER_ASSET, order kept),
  in `ROLES_BY_SET`, `SERVED_ROLE_SETS_BY_SITE_TYPE["MINIGRID"]` and `VERIFICATION_ROLE_SETS`. roles-4 untouched.
- `binding_service.py`: roles-5 beside roles-4 in `_V4_TABLE_BY_ROLE_SET`, `_MIXED_V4_ROLES_BY_ROLE_SET`; class fix:
  readiness and verification-missing cover every PER_ASSET role over components of its asset type (not only LOAD).
  Cold PER_ASSET roles (chamber, compressor, door...) now also take this branch; their tests pass unchanged.
- Kisiwa and Mto conversions: `role_set` roles-5 (each unit's signals already carried its own `asset_code`). Kobo roles-4.
- `gen-ks-02` loses `minimum-runtime`, `start-soc-threshold`, `stop-soc-threshold`, `start-delay`; no existing test needed them.
- Tests: `test_dd1_onboarding_postgres` (7): Lakeside `--bindings` exit 0, 3 sets, Kisiwa/Mto roles-5, second apply no-op;
  roles-4 still `BINDING_ROLE_AMBIGUOUS`; `BINDING_ROLE_CONFLICT` (a second channel of `generator_power` on one unit);
  readiness names `Generator power - Generator 02` when gen-ks-02 is unbound and not unit 01.
  `test_dd1_site_limits` (new): 10,000-node at-limit parses / over refuses; 96 devices parse / 97 names the cap; 256 KiB kept.
  `test_dd1_operator_files`: non-lead policy check, role-set expectation (Kisiwa, Mto roles-5). `test_s3_role_vocabulary`,
  `test_w402_roles_properties`: roles-5 served, only the five roles differ.
- Runs: 1,158 unit tests (bindings, roles, foundation, dd1, site, cold/ev) pass after two expectation updates; Postgres
  binding/dd1/w201/w205/w402/k1 set: see the hand-back.

## Plants
- Provision guard: the five D-DD.35 cases; the pre-change code refuses `lakeside-power` with the served variable set, so
  `test_set_and_same_tenant_runs` fails on `main`.
- A schedule `24:00` start and `24:01` end each refused `ONBOARD_SITE_INVALID`.
- A missing conversion file refuses before any write (tenant count 0).
- Files: a changed role, a missing person or a wrong site fails `test_people_follow_the_manifest_workflow` (set equality).

## Known deviations and questions (defaults applied)
- **Q-DD1.7 (ruled D-DD.41, built round 2).** See DD1.2 round 2 below; no longer open.
- **Q-DD1.8 (ruled D-DD.42; constants' comments now name it and the basis).** Site documents were bounded at 2,000 nodes and 64 devices. A depot at ev-lab-001 detail is 2,271
  (Kasarani) to 6,623 (Ruiru) nodes and 73 devices. Applied: `SITE_DOCUMENT_LIMITS.max_nodes` 10,000,
  `MAX_DEVICES` 96, template `MAX_DOCUMENT_NODES` 10,000 (keeps the device cap under the ceiling; the existing cap tests
  still pass). Guard changes outside the spec; for review.
- **Q-DD1.9 (applied).** Where the manifest is silent, Lakeside takes template v3's values: PCS 30 kW, tank 400 L, load
  ratings 25/10/40 kW, Kisiwa inverter equal to its PV (30 kW), Mto inverters 25 kW, the generator policy properties on the lead unit only
  (D-DD.43; `gen-ks-02` carries unit properties). DD3.3 adds `pv-array-share` and no-load rates.
- Kobo's component ids changed from `/1`'s (`inverter` to `pv-inverter`, plus `battery-pcs`, `fuel-tank`, `ac-bus`, loads).
- The `lakeside-power.v1` copy (`fixtures/on1/lakeside-power.v1.onboarding.json`, DD1.1) stays the `/1` fixture of
  `test_on1_operator_file`; `lakeside-power.onboarding.json` is now `/2` and is what the ON1 Postgres test applies.
- C-DD13's TENANT-1 clause is pending (D-DD.40). `ONBOARD_FORMAT`'s sentence still says "version 1" (one new string allowed).
- Not done: `tools/world.py` L1 passing `--bindings` and `world-layer4-v1.json` gaining `harvest-cold` and `metro-bus`
  (plan item 5). The world's DD6 owns the run; the option exists.

## Hand-off notes
Real files with `--bindings` exit `ONBOARD_REAL_AWAITS_APPROVAL` before any step (same order as without it); no dedicated
test was added for it. Scratch deleted.

## Fix round (D-DD.45-47)

- H1: `Role.every_component` (default False) in `binding_roles.py`; true on `feeder_demand`, `feeder_requested_power` and the
  five roles-5 unit roles (`replace(r, cardinality=PER_ASSET, every_component=True)`). `binding_service.py` readiness and
  verification readiness branch on `role.every_component` only; `loads` renamed `components`.
- Sweep (`grep -n 'cardinality\|asset_type == "LOAD"' sites/*.py`, nothing else changed): `binding_service.py:321`
  (ONE-only auto-bind), `:472` (conflict key, stays on cardinality), `cold_foundation.py:333` (backlog item),
  `parsing.py:17` (a docstring). No `asset_type == "LOAD"` remains.
- L1: limit comments in `foundation_parsing.py` now state D-DD.42's basis in two lines; the `MAX_SIGNAL_MAPPINGS` note is gone.
- L3: the `--bindings` pre-write check parses every `<CODE>-bindings.json` (`OSError`/`ValueError` refuses
  `ONBOARD_SITE_INVALID bindings/<CODE>`, exit 2, nothing written); `_publish_and_enable` takes the parsed files.
- Tests: `test_dd1_readiness_parity_postgres.py` (goldens + README in `fixtures/dd1_readiness_parity/`, captured from main
  `05be2b968`; plant; every_component implies PER_ASSET and the true set is the seven), malformed-file test in
  `test_dd1_onboarding_postgres.py`.
- Deviation: the ruling expected cold goldens to read `READY_TO_REPORT`. On main both cold Sites read INCOMPLETE
  (policy controls unconfigured, Site-type gap); no probe channel is missing. Goldens record main as it is, and a test
  asserts the missing roles are exactly the two policy controls. COLD-KIRI cannot be onboarded by main's code (file
  format), so its capture overlaid the branch's onboarding machinery on main's `binding_roles.py`/`binding_service.py`
  (README).
