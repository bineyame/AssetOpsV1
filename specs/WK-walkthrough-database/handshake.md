# WK handshake

Reviewer questions and builder pre-flight, one combined round (`.ai/RULES.md` §4), round 1. Fresh Claude reviewer,
2026-11-21, on `main` 08f3bf86c (spec rev 1, `rulings.md`, `reviewer-guide.md`; owner-away rows 36 (b), 53, 54;
D-DS4.19; D-0K4.19; `owner/owner-one-figure-loyal-to-operating-world-2026-11-21.md`). Read-only: `tools/world.py list`
was run from the main checkout and the world manifests in `/opt/assetecon/worlds/manifests/` were read. Nothing under
`/opt/assetecon/keys` was read, and no database was opened. Severity: **High** blocks the coordinator's run or the
build; Medium needs a ruling; Low is the Architect's call. Each item gives the file:line it rests on and the default
that applies if the Architect does not answer.

Answered: `rulings.md`, "Handshake answers (round 1)" (D-WK.10 to D-WK.14), folded into spec rev 2.

## The kept L2 is stale at today's key

`world list` (main checkout, 08f3bf86c) prints `assetops_world_audit_l2_1906a5d074a0`, `exists: true`,
`check_passed: true`, `check_stale: null`. That line cannot show whether the key is today's (D-WK.2). The ladder's
manifests record commit `68449e49d`. Comparing their key parts with `git rev-parse HEAD:<path>` at 08f3bf86c gives:

| Part (`tools/world.py:219-229`) | In the L1 manifest | At 08f3bf86c |
|---|---|---|
| `migrations` | `10cd6d74` | same |
| `definition` (sha256 of `world-layer4-v1.json`) | `d876429c` | same |
| `code.backend/assetops_backend` | `e6e71eab` | `32722936` (**changed**) |
| `code.contracts/assetops_contracts` | `5429fff5` | same |
| `code.simulator/assetops_simulator` | `05344468` | `174c5b39` (**changed**, 0K4b `packs/generator_curve.py`) |
| `code.tools/world.py`, `code.tools/world_history.py` | `a01037b8`, `b794f8fb` | same |
| check inputs: `derived_values`, `manifest`, `CHECK_CODE` | `944d33f0`, `7f94e3c1`, five trees | same |

The merges that touched the two code paths since the build are SC-1f (d67d48aee), 0K4b (68a4ba6c0), 0K4e (704124784)
and 5c units 1-2 (08f3bf86c). 0K4c (a66dd74a9) changed neither path. `inputs` was not recomputed (that needs the
export step), but its sources (`world_history.py`, the manifest and the onboarding file) are unchanged. So
`World.current_l2()` (`tools/world.py:611-627`) now refuses `WORLD_TEMPLATE_STALE code.backend/assetops_backend`.
**WK needs `world build` and then `world check` (spec §5 step 1, both branches) before `copy`.** The new L2 has no
check block, so `check` is required even though the check inputs are unchanged.

## Reviewer questions (R)

- **R1 (High) The coordinator's run starts from a stale L2.** See the table above. Spec §5 step 1
  (`spec.md:244-246`) already covers it. Default: run step 1 as written. `"reused": false` is expected for L1 and L2
  (L0 is reused), then `world check` must exit 0, then step 2's `world list` must show the new L2 with
  `check_passed: true`. The run takes about 26 minutes, not 15 (`spec.md:292`). The kept
  `assetops_world_audit_l2_1906a5d074a0` is never copied. Any later merge into `backend/assetops_backend`, `simulator`
  or `contracts` before step 3 restarts at step 1 (D-WK.6). DDR's own merge is one of these (DDR handshake I6).
- **R2 (High) The new L2's check may FAIL on C4 after 0K4b and 0K4e.** The kept check's C4 blanks name
  `candidate_l dispatch-3.2 (generator_state, pv_available_power, battery_soc)`. 0K4e moved that factor to
  dispatch-3.3, and 0K4b added assumed fuel-curve values. `judge_side` FAILs a class-B factor that now carries a
  value, or a factor outside the contract (`tools/world.py:901-929`). Default: no change to WK. A C4 FAIL stops the
  run at step 1 (W9) and goes to the Architect as a DS4 finding. WK never copies an L2 whose check did not pass.
- **R3 (Medium) Clean after the serve, not only before it.** W1 to W7 run before `serve` (`spec.md:166-174`). The
  smoke then drives ten pages through the real app. Nothing re-checks whether a read wrote rows (for example a
  response store or a cache table) into the copy the owner walks. Default: `smoke` adds S4. It re-runs W3's census
  judge read-only against the manifest's `parent_census` plus the declared deltas. A new row in any table FAILs and
  names the table. This is one more test row in T5's judge, with no new mechanism.
- **R4 (Medium) The one-figure rule on the served pages.** `owner/owner-one-figure-loyal-to-operating-world-2026-11-21.md`
  allows two figures for one quantity only where the operator must act or reconcile. The smoke records status
  codes only (`spec.md:207-210`). Default: the reviewer reads the smoke PNGs of `/portfolio/month?month=2026-10` and
  `/sites/KOBO-001` for a quantity shown twice. Plan against actual, and the statements against the records, are the
  allowed pairs. Kobo's stop-70 litres and value must read "Not available yet" (this world has no EMS export). A
  breach is a product finding for the Architect. WK adds no product code to fix it (`spec.md:37-39`).
- **R5 (Medium) No new served English (D-0K4.19).** WK's only new text is the two `source_ref` values in
  `backend/conversions/walk-layer4-v1.json` (`spec.md:77,80`). They are stored by `reconcile_month record`
  (`structure/reconciliation.py:427-436`). On `main` no route serves `source_ref`: it is absent from `deep_dive/` and
  every `*_api.py`. The standing text is SC-1-composed (`deep_dive/view.py:572`). Default: accepted as written. The
  reviewer greps for `source_ref` in the diff and in every `*_api.py`. If any served read returns it, that is
  `HAND_BUILT`-class debt and goes to the Architect. `tools/walk_world.py` sits outside SC-1's `PKG`
  (`tools/checks/statement_catalogue.py:35`). Its diagnostics are codes, per `spec.md:121-122`.
- **R6 (Low) Isolation constants are exact.** `PROTECTED_DATABASES`, `PROTECTED_PORTS = (8990, 5490)`, and 8991/5491
  in the definition (`spec.md:83,93-94,102`). `/opt/assetecon/AssetOpsV1-walk` appears nowhere in the spec. Default:
  T12 also asserts that the source never names `/opt/assetecon/AssetOpsV1-walk` or `/opt/assetecon/keys`. `serve
  --tree` refuses any `DIR` that resolves to `/opt/assetecon/AssetOpsV1-walk` (`WALK_TREE_MISMATCH`).

## Implementer questions (I)

- **I1 (High) `build_deep_dive_read` returns a tuple, and `month` needs a `TenantRef` with a name.** W4
  (`spec.md:171`) writes `build_deep_dive_read(url).month(...)`, but the function returns `(DeepDiveRead, dispose)`
  (`backend/assetops_backend/deep_dive/composition.py:32,46`). `DeepDiveRead.month(tenant: TenantRef, ...)`
  (`deep_dive/read.py:43`) needs `TenantRef(id, slug, name)` (`sites/foundation_records.py:49-52`). `world.TENANTS`
  selects only `id, slug` (`tools/world.py:422`). Default: W4 unpacks and disposes in `finally`. It builds the
  `TenantRef` from `SELECT id, slug, name FROM tenant WHERE slug = :s` on the walk URL (the same query as
  `sites/adapters/postgres_foundation_store.py:172`). It takes `names` from the Foundation's imported Sites, as the
  route does (`deep_dive_api.py:58`), not from the world definition. The definition's "Kisiwa", "Kobo", "Mto"
  (`backend/conversions/world-layer4-v1.json`) are not the served names. W4 compares no words, so the figures are
  unaffected.
- **I2 (High) W3, W6 and `copy` step 2 cannot use `World.census` or `World.exists` on the walk name.** Both call
  `check_name` (`tools/world.py:524-527,558-560`). `check_name` refuses any name matching `walk|serve`
  (`evidence/bulk_load.py:47,234-235`), and T12 forbids calling it on the walk name (`spec.md:233`). Default: WK has
  its own `walk_url(name)` (`rung_url`'s form, `tools/world.py:277-280`). It is guarded by §3.1's
  `database_target`/`is_operator_name` check (`database_target.py:41,68`) and by `name ==
  f"assetops_polish_walk{label}_test"`. It runs `CENSUS_TABLES` and the counts through `rung_query` on it. Its
  `pg_database` lookups are plain `Admin` `SELECT`s with a bound name. `wait_idle(l2_name)` and `check_state` stay on
  `World`.
- **I3 (Medium) The smoke's browser needs more than `PW` and `CHROME`.** `spec.md:205` cites `env.sh`. That file
  also exports `AUDIT_LD_LIBRARY_PATH` and `FONTCONFIG_FILE` (`/opt/assetecon/tools/pw/env.sh:4-5`), and the headless
  shell starts only with `LD_LIBRARY_PATH=$AUDIT_LD_LIBRARY_PATH` (`shot.cjs:2,5` reads only `PW` and `CHROME`).
  Default: `smoke` sources `env.sh` in a `bash -c` child. It passes `PW`, `CHROME`, `FONTCONFIG_FILE` and
  `LD_LIBRARY_PATH=<AUDIT_LD_LIBRARY_PATH>` plus `PATH` and `HOME` to `node`, and nothing else.
- **I4 (Medium) The world tool's `Deps` is not WK's `deps`.** `World(args, deps)` takes `world.Deps` (admin, query,
  runner, git, clock, require, environ, which, snapshots, python; `tools/world.py:405-415`). WK's `deps`
  (`spec.md:107-109`) adds an HTTP getter and a process table. Default: WK's `WalkDeps` holds a `world: world.Deps`
  plus `http`, `procs` and `world_factory`. Tests inject a fake `World` through `world_factory`. The copy's one DDL
  goes through `deps.world.admin`, so T3 sees it.
- **I5 (Low) Citation drift, no change in meaning.** The upload router's key check is at `main.py:693`, not `:690`
  (`spec.md:189`). `heavy_slot_check.require` exits 69 through `sys.exit` (`tools/heavy_slot_check.py:161-171`), and
  69 is missing from WK's exit list (`spec.md:115-116`). `ASSETOPS_LIVE_FIELD_*` names nothing on `main` (harmless on
  a deny list). `demo_combined.py serve` starts only the API and prints the Vite command (`tools/demo_combined.py:1804,
  1878`), so WK's Vite child is new, not copied. Default: the packet notes each item. Exit 69 passes through, as
  `world.py` documents (`tools/world.py:13`).
- **I6 (Low) Cited names checked and found.** `World.prepare/current_l2/check_state/wait_idle`, `Admin`,
  `rung_url`, `rung_query`, `CENSUS_TABLES`, `TENANTS`, `read_definition`, `c4_oracle`, `canonical` (`tools/world.py`
  79,131,347,370,420-422,490,531,611,634,950). The L2 manifest holds `key`, `tenants`, `key_dir`, `census` and
  `snapshots` (`:654-750`). `reconcile_month record` options (`reconcile_month.py:48-64`). The default tolerance is
  1 in 100, so the draft fails on fuel (105.00 > 51.00) and the final matches (5.00 <= 50.00; revenue 12.00 <= 97.00)
  against `derived-values.json` (revenue 9,688.00, fuel 4,995.00, contribution 1,443.00, plan 2,295.00), with the
  latest statement superseding (`structure/reconciliation.py:137-140,380-402`). `build_structure_snapshot
  build|verify` and its stdout keys (`build_structure_snapshot.py:50-56,81-95`), with `sites` a dict of code to id.
  Verify exits 4 on a mismatch. `BUILT_BY` (`structure_snapshot/model.py:24-25`). The census tables are
  `commercial_accounts_statement` (`migrations/versions/0069_commercial_reconciliation.py:25`) and
  `structure_snapshot` (`0066`). `ASSETOPS_API_PORT` (`frontend/vite.config.ts:44-49`). Routes `/portfolio`, `/sites`,
  `/sites/<code>`, `/findings`, `/actions`, `/evidence`, `/financials` exist in `frontend/src`. `heavy-slot.sh
  --label` exists. Default: none needed.
