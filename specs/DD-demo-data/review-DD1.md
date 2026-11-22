# DD1 review (operators / demo data onboarding)

## Round 1: discovery review of `task/DD1-operators` at `f90cb6988`

Reviewer (Claude, fresh; did not author DD1), 2026-11-22. Judged against `packet-DD1.md` (incl. "DD1.2 round 2"),
`rulings.md` D-DD.35 to D-DD.44, and `git diff main...HEAD` (39 files).

**Summary (verdict: accept with findings fixed on the branch)**
- One High: the D-DD.41 readiness class fix is wider than its premise. It now also takes the cold and EV PER_ASSET
  roles, and every cold Site's Foundation readiness turns from READY_TO_REPORT to INCOMPLETE with a false missing role
  ("Chamber temperature - Ambient temperature probe"). No test catches it.
- LOAD output is byte-identical (the filter is the same set of assets for every LOAD role in roles-1 to roles-4).
  The roles-5 unit branch is correct: a planted unbound `gen-ks-02` is named in readiness and verification readiness.
- (b) Site figures from units are DD3.4's (D-DD.41, D-DD.44). Nothing on this branch aggregates units. Correct.
- (c) Limits 10,000/96 are built and tested at limit and over. Two Lows: a stale comment, and a premise of the ruling
  that holds only for operator files.
- (d) The policy is held once, on `gen-ks-01`. `gen-ks-02` carries only rated power and SFC. A test covers all three files.
- Postgres set: 97 passed. Missing-claim scan passed, and its fixtures passed 26/26. Architecture and workflow checks passed.

### Findings

**H1 (High, acceptance gap: behaviour beyond the ruling, wrong user-facing statement).**
`backend/assetops_backend/sites/binding_service.py:818` (readiness) and `:914` (verification readiness).
- *What is wrong.* The branch was `PER_ASSET and asset_type == "LOAD"` and is now every PER_ASSET role, read over all
  of the Site's components of `role.asset_type`. Cold and EV PER_ASSET roles took the generic branch before. The
  premise ("a PER_ASSET role must be bound on every component of its asset type") is true for LOAD and for the v9
  GENERATOR/INVERTER units. It is false for `cold-roles-1`, where `chamber_temperature` and `ambient_temperature` share
  the asset type `TEMPERATURE_PROBE`, and every cold Site has one chamber probe (`probe-1`) and one ambient probe
  (`ambient-1`).
- *Reproduction.* I called `readiness()` on the nine world conversions over their DD1 Foundations, with gaps
  stubbed. On main: COLD-MWEA, COLD-THIKA and COLD-KIRI are READY_TO_REPORT with no missing roles. On the branch all
  three are INCOMPLETE, with missing `['Chamber temperature - Ambient temperature probe']`. cold-lab-001 has the same
  two probes and is affected the same way. The only caller is the Foundation API (`foundation_api.py:293`). Its
  `missing_roles` and `state` are shown by `frontend/src/sites/FoundationBindingsPanel.tsx:104-114` and
  `StoredFoundationViews.tsx:937`. So a correctly bound cold Site tells the user a required channel is missing.
  EV keeps its state, but its wire changes: `subjects` now lists every connector, and an optional role bound on only
  some connectors flips from CONFIGURED to UNBOUND. The packet's claim that cold "tests pass unchanged" holds only
  because no test covers this.
- *Why it matters.* D-DD.41 asked for "LOAD output byte-identical". It did not ask for cold or EV changes. The
  readiness screen states a false gap ("missing is never zero" read the other way: what is present is shown as
  missing).
- *Fix (class).* Limit the per-asset branch to roles whose asset type identifies the subject. My default is to take
  the branch when `role.asset_type == "LOAD"` or the role set is `minigrid-roles-5`, i.e. the D-DD.41 unit roles.
  Cold and EV then keep the generic branch byte for byte. Add one test that the readiness of cold-lab-001 (or
  COLD-KIRI) and one EV Site is equal to main's output. Alternative for the Architect: make "every component of the
  type" an explicit per-role flag (e.g. `per_unit=True` on LOAD and the five roles-5 roles), not a cardinality rule.

**L1 (Low).** `backend/assetops_backend/sites/foundation_parsing.py:119-135` (and the `MAX_SIGNAL_MAPPINGS` note at
`:137-143`). The long comment above `MAX_DEVICES` still argues "64 ... headroom under the 77 the ceiling refuses at
[2,000 nodes]", but the constant is now 96 under a 10,000 ceiling. Fix: replace that paragraph with the D-DD.42 basis,
or cut it to one line. `TestEveryCapCanFire` still holds.

**L2 (Low, a note on the ruling's premise for the Architect).** D-DD.42 says "the byte bound (256 KiB) stays and is
the binding memory limit". That holds for operator files (`operator_file.py:32`), and Site import files are bounded at
128 KiB (`sites/adapters/import_files.py:24`). The Foundation revision POST (`foundation_api.py:492`) has no byte
bound: FastAPI parses the body before the node walker runs, and the walker now admits 5x the nodes. The route is
authenticated and the risk is small. Fix if wanted: a content-length bound on that route, like `evidence_api.py:303`.

**L3 (Low).** `backend/assetops_backend/onboard_operator.py:136`: `_publish_and_enable` reads each conversion with
`json.loads` and does not catch a decode error. A malformed `<CODE>-bindings.json` (the file exists, so it passes the
pre-write check) raises a traceback after the onboarding writes, where the documented path is exit 3. Fix: catch
`ValueError`/`OSError` there and refuse `BINDING_CONVERSION bindings/<CODE>` with exit 3. Better, parse all conversion
files in the pre-write check.

No other findings. `provision_gateway`'s served-tenant guard, `24:00` as end of day only, the `/2` format with `/1`
byte-identical (`site_document` adds optional keys only when present), roles-5 built by `replace` with order kept, and
the roles-4 `BINDING_ROLE_AMBIGUOUS` plant all match the rulings.

### Checks run (worktree `/opt/assetecon/AssetOpsV1-dd1`, `f90cb6988`)
- `tools/heavy-slot.sh --db -- pwsh tools/run-host-tests.ps1 -- <files>` from the worktree root, with
  `test_s1_bindings_postgres`, `test_dd1_onboarding_postgres`, `test_on1_onboarding_postgres`,
  `test_w201_cold_foundation_postgres`, `test_w202_cold_lab_bindings_postgres`, `test_w205a_ev_foundation_api_postgres`,
  `test_w205a_ev_foundation_postgres`, `test_w402_authored_v4_postgres`, `test_w402_site_registration_postgres`,
  `test_w402_inputs_postgres`, `test_walk1_4_mini_binding_lineage`, `test_k1_kisiwa_site_postgres`:
  **97 passed** in 281 s.
- `node tools/checks/missing-claim-scan.mjs`: passed (44 tagged uses, 10 baselined, merge-base `d0323c401`).
  `node --test tools/checks/test_missing_claim_scan.mjs`: 26/26 pass. Both used a temporary symlink to main's
  `frontend/node_modules`, removed afterwards.
- `tools/check-architecture.ps1`: passed (with `ASSETOPS_GUARD_PYTHON` pointed at the repo venv; without it the
  chain-structure guard cannot find Python). `tools/check-agent-workflow.ps1`: passed.
- Plants (scratch script over `readiness()`): cold and EV, branch against main (H1). `gen-ks-02` unbound: readiness
  names `Generator state - Generator 02` and `Generator power - Generator 02`, and verification readiness lists
  `generator_power`/`generator_state` with `['gen-ks-02']`.
- `git merge-tree main HEAD`: merges cleanly with main at `05be2b968`.

### Not verified
- The statement-catalogue `--self-test` after the re-hash (the packet defers it to "the review"). Not rerun; the full
  check-all was not rerun.
- `dd_check.py` against a database (needs DD6's world clone, as the packet says).
- The real-file `--bindings` order (`ONBOARD_REAL_AWAITS_APPROVAL`) has no test, as the packet states.

### Residual risk the packet does not name
- The `mini-grid` profile's `foundation_needs` (`runs/profiles.py:1235`) resolves the policy properties per GENERATOR.
  A two-GENERATOR Site reaching a run before DD3.3/DD3.4 may be ambiguous or refuse. No roles-5 reader exists yet
  (`analytics/assessment_worker.py:63`, `mini_depth/*` are pinned to roles-4), so today this is latent.
- Kisiwa and Mto show no generator or PV figures until DD3.4, as D-DD.41 intends.

## Re-review (fix round D-DD.45-47), head 9107b2463

**Verdict: ACCEPT.** H1, L1, L3 closed; no new findings. L2 is on the backlog per D-DD.47.

- Flag: `every_component=True` is set on exactly seven roles (feeder_demand, feeder_requested_power, and the five roles-5
  unit roles); it is the only condition at both branches (`binding_service.py:818`, `:914`); `cardinality` is untouched
  at the binding key (`:321`, `:472`). The test pins "exactly the seven" and "implies PER_ASSET".
- L1: the stale 64/77 and 160/208 comment blocks are replaced by the D-DD.42 basis. L3: `onboard_operator.py` parses every
  `<CODE>-bindings.json` in the pre-write loop (OSError/ValueError gives `ONBOARD_SITE_INVALID`) and passes the parsed
  dict on; a planted malformed-file test asserts no write.
- Deviation 1 (main's cold readiness): I ran readiness on main (`591458c38`; binding_roles/binding_service are unchanged
  since the golden's `05be2b968`) in a temporary worktree. Cold-lab-001 and COLD-KIRI both read INCOMPLETE with missing
  `Temperature policy low/high` only; no probe-channel role is missing. The builder is right; my round-1 statement that
  main reports cold READY_TO_REPORT was wrong (I had stubbed gaps/controls, which hid the policy controls). The
  false-missing probe role is gone on the branch: goldens regenerate byte-equal (cmp) for cold-lab, EV and KIRI.
- Deviation 2 (KIRI golden via branch onboarding over main's role/service files): sound for readiness. Readiness is a
  pure function of Site, revision, registrations and binding set plus the two files kept from main; the overlay touches
  only how the Foundation is produced. I re-captured KIRI that way and it matched byte-for-byte. Residual: it cannot show
  parity of main's own onboarding output, which refuses the on1 format anyway.
- Plant: every_component on chamber_temperature makes the cold parity test fail (in the suite, passing as a planted-fail).
- Checks: 443 passed (dd1, s1 bindings, w202 cold-lab, w205a, all w402; 540 s) on the worktree; architecture guard passed.
