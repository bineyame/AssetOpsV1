# S6-03 review - Site Work Action list

Reviewer: fresh independent Claude reviewer (did not author the slice). Revision under review: `173e7057`
(head of `task/S6-03-site-work-list`), diff `git diff cdb09767..173e7057 -- ':!.agent'`.
Judged against `tasks/S6-03-site-work-list.md` (incl. plan fix round 1), `D-2026-10-16-a-action-index` and the
cursor-fence ruling in `.agent/architect-W1-remaining-q-answers.md` (1).

## Verdict: ACCEPT

No High or Medium findings. Three Lows, none blocking. The slice can go to the owner walkthrough.

## What I verified (not taken from the packet)

- **Membership and one snapshot.** `PostgresActionStore.site_window` (`postgres_action_store.py:891-908`) reads
  Actions with `created_at >= :lo AND created_at < :hi` and every event of those Actions in one `_read`, which runs
  `SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY` (`:108-112`). The 31-day bound, UTC-only instants,
  `from < to` and limit 1-100 are validated before any read (`site_index.py:79-133`).
- **Same reducer, parity.** Rows use `lifecycle.ordered` + `lifecycle.reduce` (`site_index.py:207,223`), the same
  functions Action detail uses; detail has no extra "ACCEPTED first" check, so parity holds even for a FAILED step
  recorded before ACCEPTED. The PG test asserts list state == detail latest == detail `?event_id=` on every row,
  before and after new events, and for RESOLVED / RESOLUTION_WITHDRAWN.
- **Latest step by recorded order.** `ordered()` sorts on `(recorded_at, id)`; `occurred_at` is only echoed.
- **Fence with counts.** Fence = max created, max event recorded, Action count, event count, zero flag, hashed with
  the scope (`site_index.py:146-172`). The store is append-only, so any new Action or event changes a count. Seen live:
  on the private walkthrough DB a real-clock FAILED step stamped 2026-10-16 (before the fence's November max) still
  turned page 2 into 409 `FENCE_CHANGED` with `rows: null, total_count: null`.
- **Typed refusals, never empty success.** 401/403/404 before the store; 503 with no store or a failing store; 422
  `WINDOW_REQUIRED` / `INVALID_WINDOW` / `INVALID_LIMIT` / `INVALID_CURSOR`; 409 `ACTION_INDEX_INCONSISTENT` and
  `ACTION_INDEX_BASIS_CHANGED` (FENCE_CHANGED / SCOPE_CHANGED). All carry `rows: null, total_count: null`. A CURRENT
  zero is only returned after `site_window` succeeds.
- **Relaxed consistency rule is still fail-closed.** An Action with no ACCEPTED event (including zero events) and any
  event whose Action is not in the snapshot both refuse the whole read (`site_index.py:159-170`); only the "ACCEPTED
  must sort first" ordering requirement was dropped, and the reducer treats a pre-ACCEPTED FAILED identically in list
  and detail. APPLIED cannot be recorded before ACCEPTED (the apply path refuses a clock behind the Foundation).
- **No verdict.** The UI shows recorded step words and "Trial closed" / "Being checked again" from the reduced
  `resolution.state`; `outcome.state` (e.g. VERIFIED) is never rendered.
- **No SQL writer (rule 8).** The only new SQL is two SELECTs in `site_window`. `git diff cdb09767..173e7057 --stat`
  touches no `scheduling/` or `evidence/` file; the probe mutations are fully reverted in net (see L3).
- **UI.** Without `from`/`to` the frame passes `scope=null`, no request is made and the choose-window panel shows
  (`SiteWorkActions.tsx:346-366`, test asserts zero `action-index` requests). Window submit and the restart link set
  `cursor: null`; Next/First links keep the window in the URL. Finding link is `?revision_id=` exact; step link is
  history at `?event_id=` and the test compares it to the server's `history_at_event`. IDs, fence token, order and
  selection rule are only inside "What this list is based on".
- **Walkthrough reachable as written.** `AssetOpsV1-review4` is checked out at `173e7057` with a `.venv`. I ran the
  same tool here with a private name: `prepare` ended `Performance cutover: permitted` / `Prepared.`; `attest` printed
  2 = SQL 2 and 0 = SQL 0 and `ATTEST OK`; `serve` came up; the step-6 PowerShell snippet produced the expected
  FAILED refusal (`ACTION_FOUNDATION_STALE`) and the copied page-2 cursor then returned 409 `FENCE_CHANGED`; `drop`
  removed the DB and folder.

## Findings

1. **Low** - `frontend/src/sites/SiteWorkActions.tsx:220`. The State cell carries
   `data-site-work-state={row.state.application}`, the same attribute the panel uses for the page state
   (`current-rows`, `current-empty`, `basis-changed`, ...). `[data-site-work-state]` therefore matches the panel and
   every row; tests and the evidence script only work because the panel comes first in document order. Not an
   acceptance gap. Fix: rename the cell hook (e.g. `data-site-work-application`).
2. **Low** - `frontend/src/sites/SiteWorkActions.tsx:89` and `:223`. `stateWords` falls back to the raw
   `state.application` enum and the step cell falls back to the raw event `kind` for anything not in `STEP_WORDS`.
   No current path reaches either (every listed Action has ACCEPTED, and all six kinds are mapped), but a future
   event kind would put an internal enum in the default reading. Fix: a neutral "Recorded step" / "State not shown"
   fallback, with the enum kept in the disclosure.
3. **Low** - history hygiene, commits `589d9258`..`e8ed0247`. The writer-guard probe mutations of
   `scheduling/.../postgres_schedule_store.py` and `evidence/.../postgres_gateway_access.py` live in those
   intermediate commits and are reverted only in `e473ba0c`. The net diff is clean, but a non-squash merge puts
   mutated writer code into main's history (a bisect hazard). Fix: squash-merge the slice, or note it at merge.

## Checks I ran (worktree `AssetOpsV1-gap-planning` at `173e7057`, main venv python, PYTHONPATH = this worktree)

| Check | Result |
| --- | --- |
| `pytest test_s6_site_action_index.py test_s6_site_action_index_postgres.py` (private `assetops_s603rev_test`) | 17 passed, 162.7 s |
| `pytest test_s6_action_records_postgres.py test_s6_action_store_postgres.py test_s6_action_apply_postgres.py` | 22 passed, 179.2 s |
| `npx.cmd tsc --noEmit` | exit 0 |
| `npx.cmd vitest run` siteWorkActions, operatorSiteTabs, siteDetailRoute, overflowContainment | 4 files, 85 passed (vitest ran under this sandbox) |
| `tools/check-architecture.ps1` | passed |
| `tools/check-agent-workflow.ps1` | passed |
| Walkthrough tool prepare / attest / serve / step-6 snippet / drop (private `assetops_s603_ownerrev`, port 8977) | all as written (above) |

Serial runs only; private DBs and the work folder were dropped afterwards.

## Not verified by me

- Full `npm.cmd test` (packet: 69 files, 1631 passed at `4d9a89ca`) and `npm.cmd run build`: not run.
- Full backend suite: not rerun per brief. Implementer's run: 2535 passed, 0 failed/errors/skipped, 1446.7 s, at
  `0696e744`; `git diff 0696e744..173e7057 -- ':!.agent'` is empty, so that run covers the reviewed code.
- `tools/layout-evidence.mjs` and `tools/s603-site-work-evidence.mjs` (need Chrome + dev server): not rerun. The
  packet records 56/56 S6-03 claims and 327 PASS / 2 FAIL for layout-evidence with the two failures named as
  pre-existing preconditions; that is recorded honestly rather than as a pass. 390/1440 rendering is left to the
  owner walkthrough step 7.
- `tools/writer_guard_probes.py`: not completed by the implementer (deviation 3) and not run by me; S6-03 adds no
  writer or DDL, so the risk is low.

## Residual risk (beyond the packet)

- The fence is detection by counts and maxima, which is sound only while `action` and `action_event` stay
  append-only. A future in-place update or delete path would need the fence revisited.
- The Work tab now renders on every Site, including file-backed ones (e.g. MG-002); there the list shows the
  choose-window state and then the typed 404 "No Actions record for this site". That is honest, but the owner may
  want to see it once.
- Ports differ from the packet (8963/5463 vs 8943/5443); the walkthrough and tool agree with each other.
