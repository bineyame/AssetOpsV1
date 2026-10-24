# W5-04 V2b handoff — EV Work Actions producer-backed captures (1440/390)

Branch `task/W5-04b-ev-work-ui`. It merges `task/W5-04a-fix` at `3a100f2f` (merge commit `c3487ce3`) on top of the
V2a fix round (`35b01c25`). V2b changes no product code: the frontend is identical to `35b01c25`. Read the card with
rulings 39 and 53–66. Evidence is in `.agent/W5-04-V2b-evidence/`.

## Units and commits

| Commit | Content |
| --- | --- |
| `9bab4bfe` | New `tools/w504-ev-work-evidence.mjs`: EV Actions captures and claims over the V1b walkthrough manifest. |
| `baae7c9f` | `.agent/W5-04-V2b-evidence/`: 16 PNGs, `w504b-measurements.json`, the run log and the walkthrough manifest. `cold-k2-recapture/` holds the cold Actions PNGs plus the Actions and cases measurements and logs. This handoff. |

## Producer and process (recorded, cleaned)

- **Walkthrough.** `.venv\Scripts\python.exe tools/w504_ev_work_walkthrough.py --work var/w504a_v2b_work --tag v2b`
  ran `prepare` (1m38s), then `serve`, then `attest`.
  - Modes: positive `ready`; zero `ready`; unknown `unavailable` ("the replay selected 0 SUPPORTED EV Findings");
    pending and stale `unavailable` ("needs a modified replay").
  - Attest returned `forbidden` 403 `SITE_SCOPE_FORBIDDEN` and stopped the `unavailable` API at PID 16904.
  - The manifest copy is `w504a-walkthrough-manifest.json`.
- **Vite.** I started one Vite dev server per API, at the API port minus 3500, with `ASSETOPS_API_PORT=<api>`. Recorded
  PIDs: 460, 17632, 30396 and 22616 for 5481/5482/5486/5487.
- **Cleanup.**
  - Vite: each was stopped with `taskkill /PID <pid> /T /F` after its command line was checked to be our
    `vite --port 54xx`.
  - Walkthrough: `drop` stopped only its recorded uvicorn PIDs, dropped `w504a_{positive,zero,unknown}_v2b_test` and
    removed the work folder.
  - All of ports 5481/5482/5486/5487/8981/8982/8986 refused connections afterwards.
- **Cold K2 recapture** (ruling 62, because the CSS rename is shared).
  - `tools/w502_cold_work_walkthrough.py --work var/w502b_v2b_cold` ran `prepare` (1m59s; all 5 modes built), then
    `serve` and `attest` (ATTEST OK).
  - Seven Vite servers ran on 5471–5477.
  - Cleanup: stopped by PID (28096, 11048, 26124, 32472, 17764, 28812, 3836), then `drop`, which dropped
    `w502b_*_k2_test` and removed the folder.
  - Ports 5471/5477/8971/8977 were closed afterwards.

### Re-review round (`b2a97b66` and later)

- **Walkthrough.** `prepare` ran in 2m07s. Modes: positive, zero and **worstcase** ready; unknown, pending and stale
  unavailable as before.
- **Serve and attest.** Served positive 12228, zero 20364, worstcase 30680 (port 8983), forbidden 21556 and
  unavailable 7116. Attest returned 403 `SITE_SCOPE_FORBIDDEN` and stopped 7116.
- **Vite.** Five servers: 16448, 7864, 28772, 27664 and 9956 on 5481/5482/5483/5486/5487.
  - The 5483 server (PID 28772) exited by itself mid-run, so the first two worst-case captures saw no page. I restarted
    it as 11408 and reran the whole capture.
  - The same thing happened once to cold 5471 (PID 23680, restarted as 25060).
  - These are silent exits of one of several concurrent Vite dev servers sharing one `node_modules/.vite` cache. They
    are not product failures, and every rerun passed.
- **Cleanup.**
  - Vite: every server was stopped by its recorded PID after a command-line check. The two that had exited were
    skipped.
  - Walkthrough: `drop` stopped its recorded uvicorn PIDs and dropped `w504a_{positive,zero,worstcase,unknown}_v2b_test`.
  - Cold: a fresh walkthrough ran for the Low-2 rerun. Its Vite servers were 30268, 23680/25060, 31480, 31504, 9124,
    18788 and 12140, stopped by PID; then `drop`.
  - Every port refused connections afterwards.

## EV captures (`node tools/w504-ev-work-evidence.mjs <manifest> <out>`, re-review round): **195 PASS, 0 FAIL, 11 INFO**

The count dropped from 199 because the five seed claims are gone and one claim for the walkthrough worstcase manifest was added.

Heights are in px, shown as 1440 / 390. The caps come from the build spec, and the zero-panel cap from ruling 50.

| State | main | strip | Actions panel | context notice | currentness | doc scroll = client |
| --- | --- | --- | --- | --- | --- | --- |
| positive (W, CURRENT, 1 row) | 568 / 722 | 39 / 61 | 184 / 199 | 42 / 60 | — | yes / yes |
| historical (`known_at` = manifest `index_known_at`) | 628 / 782 | 39 / 61 | 184 / 199 | 42 / 60 | 42 / 42 | yes / yes |
| zero (zero DB, the day before W; complete zero) | 646 / 805 | 39 / 61 | 262 / 282 (cap 460/560) | 42 / 60 | — | yes / yes |
| forbidden-403 (healthy Site read, in-panel refusal) | 582 / 721 | 39 / 61 | 198 / 198 (cap 360/590, ruling 50; re-review Low-1) | 42 / 60 | — | yes / yes |
| worst-folded (walkthrough `worstcase`: 5 rows, 4 visible, `Show all 5 Actions`) | 864 / 1003 | 39 / 61 | 480 / 480 | 42 / 60 | — | yes / yes |
| worst-expanded (Show all plus every title/owner `Read full text`; exempt) | 1200 / 1409 | 39 / 61 | 816 / 886 | 42 / 60 | — | yes / yes |
| window-error (59-day Apply; exempt, ruling 51) | 592 / 747 | 39 / 61 | 184 / 199 | 42 / 60 | — | yes / yes |

- **Caps.** Every closed state is inside its cap: page 1600/2000, strip 100/150, panel 650/850, zero panel 460/560,
  notice 110/160. There was no cap miss, so nothing goes to the Architect.
- **Table at 390.** The table scrolls inside its panel (821 px content in 318 px) and the first column is sticky.
- **Row checks** (each on a non-empty row set):
  - every code is on one line;
  - every cell contains its content;
  - previews are at most two lines;
  - badges are on one line and unclipped.
- **Expanded state.** The opened bodies hold the full 160-code-point values.
- **Content claims:**
  - the stored Site name `EV charging lab`, with R78 `EV charging operations at this site.`;
  - `Scoped to EV · 1 action` / `5 actions` (R79/R111), with the EV gap text and no strip link (R04);
  - `Due dates are not yet set` (R76);
  - the mock criterion `A complete witnessed session and no repeat fault`;
  - `Finding {id8}` with its disclosure (R74/R75);
  - the EV code is plain text, and the page has no `/actions/` href (R113);
  - no `Depot` (ruling 52);
  - no cold-named attribute, class or disclosure (ruling 45);
  - Window labels `From (UTC)` / `To (UTC, exclusive)` (R77/R112): after the subtabs and before the strip,
    right-aligned at 1440 and full width at 390;
  - subtab hrefs keep `from,to` with no cursor;
  - HISTORICAL shows `Read as of … UTC. Later work may differ.` (R80);
  - the 403 panel shows `EV work unavailable`, the server message, a visible Retry, `— actions` and no row.

## Worst case (re-review M1: produced by the walkthrough)

The first V2b round seeded the five-row page from the `.mjs`. That seeding has been removed, because pre-flight 23 says
`.mjs` only captures.

- **New walkthrough mode.** `tools/w504_ev_work_walkthrough.py` now has a V1b `worstcase` mode, following the W5-02
  cold precedent:
  - its own `w504a_worstcase_<tag>_test` DB and port 8983;
  - the same native `ev-interrupted` replay and declared positive Action (ACT-000001);
  - then `_worstcase` posts ACT-000002..5 with 160-code-point title and owner, plus their intents, through the public
    domain-work routes and the SERVICE principal inside the walkthrough child;
  - it refuses unless the Work window W lists all five Actions;
  - every ID, code, intent ID and the index total are written to the manifest (`modes.worstcase.worstcase`).
- **Producer test.** `test_worstcase_adds_four_long_actions_through_the_public_routes` in
  `backend/tests/test_w504_ev_work_producer_postgres.py`.
- **Capture tool.** `tools/w504-ev-work-evidence.mjs` only reads now. Its new claim requires the manifest's worstcase
  mode to be ready with ACT-000002..5, 160-code-point text and intents, and to be served. The worst-case states read
  the `worstcase` API, and every row on the page must be one of the manifest's Action IDs.

## Unavailable captures (ruling 54; pure vectors remain)

| Mode | Manifest reason | Pure vector |
| --- | --- | --- |
| pending (`PENDING_RECOMPUTE`) | a late accepted event before W5-03 reassessment needs a modified replay | `evWorkActions.test.tsx` "places the selected-state notice … R104 tones" |
| stale (`STALE_SOURCE`) | a superseded source binding before reselection needs a modified replay | same test |
| unknown (`UNKNOWN`) | `ev-missing-meter` selected 0 SUPPORTED EV Findings | same test, plus the ruling 53 unavailable-pin test |
| in-panel EV 503 with a healthy Site read | the walkthrough's `unavailable` vector stops the whole API, so the browser shows the **Site-level** refusal (captured as `unavailable-503`; no rows, no zero, no overflow) | `evWorkActions.test.tsx` 403/503 test |

No backdated or virtual-clock vector is presented as a late decision (ruling 55); V2b captures none. A 160-character
error text is not producible, because server refusal messages are short; the 403 panel is the measured refusal.

## Cold K2 recapture after the CSS rename (ruling 62)

### First recapture

- `node tools/w502-cold-work-evidence.mjs <cold manifest> <out>` (Actions plus Action shell): **461 PASS, 0 FAIL**.
- `W502B_EVIDENCE=cases`: **934 PASS, 0 FAIL**.
- Evidence: `cold-k2-recapture/`.

### Numeric diff against the pre-rename baselines (as the re-review measured it)

| Surface | Baseline | Differences |
| --- | --- | --- |
| Cases | `W5-02c-K4-evidence/cases-recheck` | 0 numeric differences |
| Actions | `W5-03b-ui-evidence/cold-actions-recheck` | 13 table `scrollWidth` changes of 2–8 px at 390 (per-run UUIDs); 3 `action-positive` heights from K4's later detail merge; 4 in `worstcase-expanded-open` at 1440 (+18 px per row) |

### Low-2 rerun (INFO, expanded state)

I prepared, served and attested a fresh cold walkthrough and reran the cold tool: **461 PASS, 0 FAIL**. Evidence is in
`cold-k2-rerun/`: the measurements file, the log and the 1440 `worstcase-expanded-open` PNG.

`worstcase-expanded-open` at 1440:

| Run | Rows | Panel | Main |
| --- | --- | --- | --- |
| Baseline | 119 ×4, 118 | 731 | 1115 |
| First recapture | 137 ×4, 136 | 819 | 1203 |
| This rerun | 119 ×4, 118 | 731 | 1115 |

The +18 px per row does **not** persist. It was a timing artefact of the first recapture: it was measured mid-toggle,
which matches the blank space the reviewer saw in that PNG. It is not a CSS change. The 390 state is identical in all
three runs.

## Checks, re-review round

- `test_w504_ev_work_producer_postgres.py` (with the new worstcase test), `test_w504_ev_work_cases.py` and
  `test_w504_ev_intent_{api,model,postgres}.py`: **52 passed**, 7m47s, JUnit tests=52, skipped=0, failures=0,
  errors=0. Run with this worktree on `PYTHONPATH`.
- `tsc --noEmit`: clean.
- Targeted vitest: 10 files, **247/247**. The frontend is unchanged since `35b01c25`.
- `tools/check-all.ps1`: CHECKALL_RR.

## Checks on the first V2b revision

- Focused Postgres, run with this worktree on `PYTHONPATH` (the venv's editable install points at the main checkout):
  - Files: `test_w504_ev_intent_{api,model,postgres}.py`, `test_w504_ev_work_cases.py`,
    `test_w504_ev_work_producer_postgres.py`, `test_w502_cold_scenario_producer.py`,
    `test_w502_domain_action_index_{api,postgres}.py`, `test_w502_domain_intent_{api,model,postgres}.py` and
    `test_w502_domain_work_links_postgres.py`.
  - Result: **88 passed**, 12m21s, JUnit tests=88, skipped=0, failures=0, errors=0.
  - The first attempt without `PYTHONPATH` failed at collection: it imported the main checkout's backend.
- `tsc --noEmit`: clean.
- Full vitest (`--minWorkers=1 --maxWorkers=2`): **125 files, 2907 tests passed**, 4m22s.
- `vite build`: built in 6.4s.
- `tools/check-all.ps1` on `baae7c9f`: **All 11 guards passed**.

## Shared plumbing

None in V2b. The only new file is the evidence tool, plus `.agent` evidence.

## Residual risk

- The worst case is producer-seeded by the tool rather than the walkthrough (see above).
- Pending, stale, unknown and the in-panel 503 are pure vectors only.
- Captures used `Etc/UTC` only, so a non-UTC Site zone is not exercised (R77 defers it).
