# WARM-1 review (VPS, fresh Claude reviewer, 2026-11-12)

- Branch `task/WARM-1-range-warm`, head `7699a2b23`, diff `main...HEAD` (7 files). Merges into current main cleanly (`git merge-tree`).
- Judged against rev 7 §7.1 (D-17N.1), rulings D-WARM.1-6, D-SR.9 (range output on every page × Site), D-E5.47.
- No database used.

## Verdict: REJECT (one Medium, small fix)

The tool, the HTTP prebuild path and the serve hook are sound. Preset maths matches `sharedRange.ts` `presetRange`. The windows match the spec. Retry and verify only count a `hit` as pass, so a degraded body is never counted as a pass. The adapter seam is clean.

One Medium blocks: the story ranges do not get their full page × Site set. Fix it on the branch; a narrow re-review is enough.

## Findings

### M1 (Medium, D-SR.9 gap): story ranges get only the prebuilt requests plus the Findings lens pages
- **Where:** `tools/warm_ranges.py:262-264`.
- **What is wrong:** `plan()` runs `range_requests` only for the presets and the 7/14/30/31-day windows. Each story window from `story_windows()` gets only the prebuilt list as it stands, plus `findings_lens_requests`.
- **What the prebuilt list leaves out:** `demo_combined.prebuilt_routes` (`tools/demo_combined.py` ~l.497-519) gives the story `S` day and the story `month` window only the Portfolio, its lens variants and the summary. It gives no Findings page 1. Its Cold and EV boards are only the S+1.. per-day boards and the story-link windows.
- **Evidence:** a check against `config/chain/prebuilt-routes-v1.json` (Sites as in the packet's client4 dry run, `--today 2026-11-17`) leaves these requests cold:
  - `/api/estate/findings?from=2026-10-31T00:00Z&to=2026-11-01T00:00Z` (and the same for `2026-10-03..2026-11-03`). This is the All-findings page, while its `cost`, `risks` and `opportunities` lens pages ARE warmed. That is inconsistent within one page.
  - `/api/sites/COLD-LAB-001/outcome-board?from&to` and `/api/sites/EV-LAB-001/outcome-board?from&to` for both of those ranges.
- **Why the month window is missed:** it starts before the data window (S-28 = 10-03 < 10-11), so the 31-day window enumeration never covers it.
- **Why it matters:**
  - These ranges are clickable: the script opens them, and the Site and Findings pages are one click from there.
  - D-WARM.5 names "the story ranges" as part of the warmed set.
  - `--verify` replays the same list, so the gate would pass while these stay cold. The claim "≤2 s on every stored request of every clickable range" would then be false for the story ranges.
- **Fix:**
  - In `plan()`, add `range_requests(Range("story", first, last), sites)` for each story window whose `from`/`to` are UTC midnights. `_dedupe` and key-equivalence already absorb the prebuilt twins.
  - Add a test that a story window gets the Findings page 1 and every Cold and EV board.

### L1 (Low, packet claim): the mini-grid Site Overview board is often requested with a Finding pin
- **Where:**
  - The request: `frontend/src/sites/SiteWindowOverview.tsx:1157-1163` sends `finding_id` and `finding_revision_id` whenever the overview has a `known_finding`.
  - When that happens: `backend/assetops_backend/site_overview/read.py:178-182`. Rule `DISCOVERED` sets it on any day that has an intersecting Finding, with no pin in the address.
  - Why it misses: the pin is part of the board key (`backend/assetops_backend/outcome_api.py:217-218`).
- **What is wrong:** on those days, the `?date=D` that `day_requests` warms is a different key from the one the page asks for. The packet's line "each mini-grid day is warmed" is therefore not true for Finding days.
- **Why it is only Low:** ANY-1 gates mini-grid boards at ≤2 s when cold, so this is a claim-wording issue, not a speed risk.
- **Related:** a Cold or EV Site page opened with no range sends a parameterless board request, and that request is not warmed either.
- **Fix:** either correct the packet wording and list both cases under "outside the claim", or read `overview?date=D` while warming and add the pinned board. The first is enough for 17 Nov.

### L2 (Low): stored routes reachable by one click that are neither warmed nor listed as outside the claim
- **The cases:**
  - The Findings "Workflow state" chips (`frontend/src/estate/findingIndex.tsx:275-290`). These are four `state=` values, keyed through `parsed_key`.
  - The Portfolio assessment-ids disclosure (`/api/estate/portfolio/scope-ids`, `EstatePortfolio.tsx:623`). The prebuild warms it for its own list; WARM-1 does not.
- **Problem:** D-WARM.5's accepted list does not mention either.
- **Fix:** an Architect line adding them to "outside the ≤2 s claim" (or warming the presets' state chips), and the packet updated to match.

### L3 (Low, gate evidence): `--verify` and serve's background warm write the same report
- **Where:** `tools/warm_ranges.py:512` and `tools/demo_combined.py:1629-1633`.
- **What is wrong:**
  - Both write `<work>/warm-report.json` by default.
  - While serve runs, a new warm starts every tick (≤120 s) as soon as the previous one ends. That overwrites the verify report.
  - It also means verify runs beside a 4-worker warm.
- **Why it matters:** the gate and the demo-day "verify within 60 min" record can be lost.
- **Fix:** give `--verify` its own default name, `warm-verify.json`. Also say in resume points 2-3 to pass `--report`, or to run the gate under `serve --no-warm` after a manual warm.

### L4 (Low, Linux): stopping the warm can kill serve itself and its job group
- **Where:** `tools/demo_combined.py:1641-1642` and `start_warm` (~l.789).
- **What is wrong:**
  - On POSIX, `_kill_tree` calls `os.killpg(os.getpgid(pid))`.
  - The warm child is started without `start_new_session=True`, so it shares the serve process's group.
  - Killing it therefore SIGKILLs the serve process too, plus any `| tee` in its job, before the API's own kill line runs. The API is in the same group, so it does die.
- **Why it is only Low:** the API Popen already has the same pattern on main, and the effect is limited to shutdown (the exit status, and pipe peers).
- **Fix:** pass `start_new_session=True` on POSIX to both Popens.

## Checks run (VPS, worktree at 7699a2b23, lane PYTHONPATH)

| Check | Result |
|---|---|
| `pytest backend/tests/test_warm1_ranges.py` | 18 passed (1.4 s) |
| `pytest test_infra1_degraded_store test_ch5c_store_off test_e4_prebuilt_routes_generator test_demo_combined_links` | 66 passed, 1 warning |
| `pwsh tools/check-architecture.ps1` (`ASSETOPS_GUARD_PYTHON` set) | passed |
| `pwsh tools/check-agent-workflow.ps1` | passed |
| `warm_ranges.py --dry-run` (two `--site`s, `--today 2026-11-17`) | runs; 47 ranges |

## Not verified

- The full `check-all.ps1`: the estate guard self-test (~22 min) and the missing-claim scan were not rerun.
- No Postgres was used.
- The live gate (warm, `--verify`, 100% hit, max ≤2.0 s, 0 degraded, re-warm wall time) has not run. It stays the merge gate.
- The 4-worker contention on one Postgres is unmeasured, as the packet says.

## Residual risk not in the packet

- A tick that moves the watermark during a warm gives `race`, and that warm exits 1. Serve logs the exit and starts a new warm on the next tick, but nothing alerts the presenter. The 17 Nov checklist should read the last warm's exit line, or the report, before the session.
