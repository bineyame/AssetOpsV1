# DS4 handoff (PARTIAL: unit 1 part-built; unit 2 not started)

Implementer (Claude), 2026-11-21. Branch `task/DS4-template-ladder`, worktree `/opt/assetecon/AssetOpsV1-ds4`
(`frontend/node_modules` symlinked). Stopped near the context budget. No live databases, no processes; scratch empty.

## Done

- **Spike (D-DS4.18)** run on `assetops_ds4t<hex>_audit_spike` / `_spike2` (both dropped): every step exit 0,
  `structure_snapshot` 4, observe 0, second apply after erase exit 0 (new tenant id). Classes differ from §2.1:
  **MBQ-1** in `mid-build-questions.md` (Kisiwa actual `om`/`cost_to_serve`/`contribution` blank: O&M is
  `ESTIMATED_NOT_RECEIVED`; plan `tariff`/`diesel_price`/`necessary_l`/`diesel_l` blank `BUDGET_LINE` at all three
  Sites although the budget export carries them). Open with the Architect. Printout:
  `/opt/assetecon/evidence/DS4/spike-2026-11-21/spike.log`.
- Commit `11e8abb5b`: `tools/world.py` (§3.1 to §3.5: definition, keys, staleness of keys, clean tree, names,
  directories, admin/runner/env, `build`, `clone`, `reset`, `list`, `drop`, manifests; `check_inputs`/`check_state`
  already coded for D-DS4.21), `backend/conversions/world-layer4-v1.json`, `backend/tests/test_ds4_world.py`
  (T1, T1b, T2, T3, T4, T5, T6 without check staleness, T7, T11): **43 passed** (no database).
- `93da441c0`: merged `main` (4a adjustments fix `e0d0a1e84`, per the coordinator). So `actual.adjustments_kwh` should
  now be `B` as §2.1 says: `C4_KNOWN_FINDINGS` starts **empty** in unit 2 (D-DS4.25: emptied after the fix merges).

## Next

1. Unit 1 rest: `backend/tests/test_ds4_world_postgres.py` T12 (without `check`), T13, T14, run through
   `tools/heavy-slot.sh --db -- pwsh -NoProfile -File tools/run-host-tests.ps1 -- <file>`; real git reader injected
   with HEAD ids (dirty tree), prefix `assetops_ds4t<hex>`, temp 0700 key root and state; module finally drops all.
   Watch: `World.prepare` runs the clean-tree check via `deps.git.dirty`; inject a git with `dirty -> []`.
2. Unit 2: `cmd_check` (currently a stub refusing) with C1 to C7, `C4_CONTRACT` literal from §2.1 (do not adapt it
   for MBQ-1), `C4_KNOWN_FINDINGS = ()`, `harness_run`; check block per §3.3 with `check_inputs`; §3.7 in
   `evidence/bulk_load.py` (`BatchTimeUnreadable`, `envelope_span`, `cover_gap`, step 7a, two refusal codes) and
   `PostgresEvidenceLedger.site_timezone`; T6 staleness, T8, T9, T9b, T12 check, T15 to T17; DS3/pg_harness regression.
3. Plants P1 to P32 in a throwaway worktree; fast check-all; `packet.md`; spec Status `in_review`; state entry.

## Anchors

`tools/world.py`: `read_definition`, `Git`, `parts_l0/1/2`, `stale_part`, `inputs_digest`, `clean_tree_paths`,
`check_name`, `harness_base_name`, `state_dirs`, `key_dir_for`, `Deps`, `World.env/run_step/prepare/inputs/
ladder_parts/current_l2/check_inputs/check_state`, `_rung`, `cmd_build`, `_clone`, `_drop`. Test fakes:
`test_ds4_world.py` `FakeAdmin`, `FakeRunner`, `FakeGit`, `Env`.

## Risks

- MBQ-1 decides whether the real-world C4 can pass; T12's C4 assertion fails until it is ruled.
- `cmd_reset` clones directly when no clone manifest exists (spec silent); `list` recomputes `check_passed` live from
  the parent L2. Both to state in the packet.
- PYTHONPATH: `$WT/backend:$WT/contracts:$WT/simulator:$WT/tools`; interpreter `/opt/assetecon/AssetOpsV1/.venv/bin/python`.
