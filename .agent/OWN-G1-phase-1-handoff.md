# OWN-G1 phase 1 handoff (code + no-DB tests done; rehearsal phase next)

Branch `task/OWN-G1-add-dates`, worktree `C:\Users\assef\Bineyame\AssetOpsV1-g1`. Spec: build sheet OWN-GAPS on main,
§4 with Revision 2 R2-G1 and R2-DS1a 1 (`1d666d410`). Pre-flight: `.agent/preflight-G1.md`.

## What landed

- `1e7cc1516` add-dates tool, Kisiwa night children, KIS-row story bounds, no-DB tests; `624b0044f` resume-flag fix.
- `tools/demo_combined.py`: `plan_add_dates` (pure planner + whole-command refusals), `select_sites`,
  `preflight_refusal`, `kisiwa_stage`, `plain_lines`, `failed_rows`, `added_night_links`; `Demo.add_dates`,
  `add_kisiwa_night`, `tick_and_verify` (2 retry ticks, 30 s apart, while the window is absent), `finish_check`,
  `site_zones`, `kisiwa_child`, `hold_busy`, `_add_core_day` (the old add-day body); `add-dates` parser; `add-day`
  takes `KISIWA-001`; `serve` prints one `add-dates` line; `links` lists added nights + the live-dip line; two Kisiwa
  story links in `story_links` and their `LINK_FORMS`.
- `tools/demo_combined_kisiwa.py`: verbs `preflight`, `add-day` (§4.5 steps 1-6, entry PUBLISHED), `verify-day`
  (steps 7-8, entry DONE); `kisiwa-days.json` in the work folder.
- `tools/demo_combined_rows.py` `kis_story_*` helpers; `tools/demo_combined_finish.py` bounds KIS-1 windows, KIS-2
  dispatch Findings and `_kisiwa_read` records (KIS-9 and the others) to the story calendar.
- Tests: `backend/tests/test_own_g1_add_dates.py` (28 pass); `test_k7_kisiwa_story.py` link counts 6/7 and the
  `OPTION_NOT_FOR_KISIWA` test.

## Dependencies (must be on main before the rehearsal)

- **G2 (R2-G2 Q9 c):** `Demo.tick()` returns the parsed tick report. Before G2 it returns `None`; G1 then treats
  Kisiwa as "not visited" and the stored window alone decides.
- **G3a:** the entry route answers 422 `OPREC_ENTRY_INVALID` to an invalid body (`preflight` posts `{"probe": true}`);
  otherwise `preflight` refuses (`ENTRY_DISABLED`); the tree must also contain this branch's Kisiwa child, or
  `BUILD_TOO_OLD`.
- After both merge: `git merge main` into this branch, resolve `tools/demo_combined.py` (G2 edits `Demo.tick`, G3a
  edits the serve env; G1 touched neither) and `tools/demo_combined_finish.py` (G2 adds KIS-11), rerun the tests.

## Rehearsal phase (one heavy job; cap 2 x 1.5 h)

Clone names (coordinator ruling, inside the existing `Demo` guard and the `*_test` DB rule; no guard exception):
database **`assetops_demo3_g1audit_test`**, work folder **`var/demo3_g1audit`**.

1. Setup (R2-G1 Q4): stop the K9/K10 serve; `CREATE DATABASE assetops_demo3_g1audit_test TEMPLATE
   assetops_k9_audit_r3u`; copy `AssetOpsV1-k10\var\demo3_r3u` to `var/demo3_g1audit` (its marker records the old db;
   `add-dates` does not read the marker). Replace `var/demo3_g1audit/tree` with a `git archive` of this branch's HEAD
   (G2 and G3a merged in), same parts as `prepare` (`demo_combined.py` `prepare`: backend, gateway, host, simulator,
   contracts, config, contract-fixtures, tools, plus `var/sites/kobo-001.yaml`); keep `keys.json`, `story.json`,
   `days.json`, `kisiwa.json`, `operational-actions/`. No `require_prepare_database` call is added. Run the product's
   `evidence_migration run` and `performance_migration run` on the clone. Expect a one-time `chain_snapshots`
   rebuild (code version changes). The clone's S = 2026-11-06, head 0058; `kisiwa.json` `log.path` still points into
   the K10 folder (read only).
2. `add-dates --site KOBO-001,KISIWA-001,EV-LAB-001 --to <last Kisiwa night + 2>`; then the same command again (all
   "already present").
3. `--to` today: `DATE_NOT_PAST`, nothing written.
4. `finish check` all green (KIS-11 included) and `chain_coherence.py` (EX-2 = 0); drop the clone.

**Watch KIS-4 and KIS-6.** Neither is bounded yet. If either fails only because of added-night content, R2-G1 Q3
pre-authorises bounding it to the story calendar (with a no-DB case with one added night). A COH or non-KIS failure
stops and goes to the Architect.

Then: review packet `.agent/OWN-G1-review-packet.md`, `CODE_STATE.md` entry, `ACTIVE_CONTEXT.md` pointer.

## Reviewer notes

- `DELIVERY_TANK_FULL` uses the card's 950 L fill limit; the tank's template capacity is 1000 L
  (`backend/tests/fixtures/s1/kisiwa-001.yaml:108-112`).
- A standalone Kobo/Cold/EV `add-day` now clears `self.deadline` after its child, so its per-day cap no longer bounds
  the `drain_mini` step that follows (`_add_core_day`).

## Environment used (no-DB runs)

The worktree has no `.venv`; the main checkout's is used, and the tree must be first on the path (otherwise
`assetops_contracts` resolves to the main checkout):

```powershell
Set-Location C:\Users\assef\Bineyame\AssetOpsV1-g1\backend
$r='C:\Users\assef\Bineyame\AssetOpsV1-g1'
$env:PYTHONPATH=(('backend','backend\tests','contracts','gateway','simulator','host','host\tests','gateway\tests','tools') | ForEach-Object { Join-Path $r $_ }) -join ';'
& C:\Users\assef\Bineyame\AssetOpsV1\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider tests/test_own_g1_add_dates.py
$env:ASSETOPS_GUARD_PYTHON='C:\Users\assef\Bineyame\AssetOpsV1\.venv\Scripts\python.exe'   # for tools/check-architecture.ps1
```

Adjacent no-DB files (22): 682 pass, 4 skip, 3 fail; the 3 (`test_demo_combined_mill.py` x2,
`test_ch5c_env_parity.py` x1) fail identically on main. Guards: architecture and agent-workflow pass.
