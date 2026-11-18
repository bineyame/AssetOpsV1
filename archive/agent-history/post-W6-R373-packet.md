# post-W6 R373 (B19-15, High D3) - review packet

Branch `task/post-W6-R373-request-access`. Build commit `7fc30340` (on b6eeb467, which carries the rulings).
Authority: `.agent/post-W6-R373-rulings.md` Q1-Q8. Pre-flight: `.agent/post-W6-R373-preflight.md`.
Status: **built, focused-green; full backend suite and B19 recaptures NOT run.** Both are held for the coordinator.
R373 stays open until the Q8 merge proof exists (ruling Q8). R374 is out of scope and registered separately.

## Outcome (ruling Q1 reachability, stated precisely)

- **Today:** `create_app`'s default admits the development operator on Site Work and on global Work alike. The
  observed 403/200 split came only from the W5 `forbidden` walkthrough compositions.
- **Fixed:** the product defect, which was independent access wiring.
  - `create_app(site_read_access=...)` now passes ONE callable to all three routers: the W4 Site Work router, the
    domain-work `WorkGate` and the global Work router.
  - The global Work router covers the request detail and `/api/work/{incidents,maintenance,preventive,
    operational-records}`.
  - Attaching a real principal to Site Work alone is therefore no longer possible.

## Files changed

- `backend/assetops_backend/main.py`:
  - The new keyword `site_read_access: Access = development_access`, with a docstring note.
  - `access=site_read_access` on `build_work_router`, the domain `WorkGate` and `build_global_work_router` (was
    `development_access`).
  - Write grants and principal injection are unchanged.
- `backend/assetops_backend/global_work_api.py`: detail admission is now
  `WorkGate(scope, unavailable, access).read_scope(...)`. The inline duplicate is removed.
  - Order is unchanged: authenticate, one `site_id`, access 401/403, scope 503/404, then case and `known_at`.
  - The detail-only 503 when `details`/`scope` is absent is kept, now raised after access through a `no_store` scope.
- `frontend/src/work/globalWorkClient.ts`: the `SITE_SCOPE_FORBIDDEN` detail copy is now "No access to this Site's
  work." (Q5).
  - `__tests__/globalWorkClient.test.ts` gains a 403 parse + copy test.
  - Three component tests that asserted the old string literally were updated: `workRequestOverview`,
    `workRequestRecord` and `workRequestHistory` `.test.tsx`.
- `tools/w502_cold_work_walkthrough.py`, `tools/w504_ev_work_walkthrough.py`: both `SERVE_ENTRY` blocks now prepend
  `build_global_work_router(..., access=access, ...)`. It uses the product router's service, tenant, scope and
  unavailable dependencies (Q7).
- `backend/tests/test_r373_request_access.py` (new, 10 tests). Every test composes through
  `main.create_app(site_read_access=...)`.
  - No database:
    - The deny case gives the identical 403 bytes on both detail routes, plus a domain-work read, for unknown,
      malformed and random IDs.
    - The allow case advances to the existing 503/404.
    - The default composition still admits the development operator (Q1).
  - Postgres, one test per vertical (`vertical_proof`):
    - Each uses a real linked request: mini `detail-linked` (w601 seed); cold `cold` + `bind`; EV is the W5-04 `ev`
      fixture plus an EV domain Action created and linked through the composed `DomainIntentService` (no fallback).
    - Granted: 200 on both routes, and the request is listed in global maintenance.
    - Denied: byte-identical 403 for the linked, unknown, malformed and foreign-Site (KOBO-002) IDs. The global list
      drops the Site silently, and the other Site's request stays readable.
  - Postgres lists (four roots; w601 `incidents`/`maintenance`/`preventive`/`operational` fixtures, KOBO-001
    denied):
    - No denied row appears in paged rows (limit 1), and the rows equal the full read minus the denied Site.
    - `total_count` matches the filtered rows, and `state_counts` sums to it.
    - Every cursor's `authorized_site_ids` excludes the denied Site.
    - A wider-grant cursor never pages denied rows.
    - Fully denied gives 200 with an empty list, never a Site 403/404.
    - Non-empty proofs are asserted: the denied Site has rows, and the wider grant pages.
  - The EV `chain` fixture name collides with the cold one in a single module. The `ev` fixture body is therefore
    restated under the same name over the W2-05b EV chain factory, with unchanged logic.

## Test selection and why

- **Ruling Q8's focused list.** These are the tests that exercise the changed router, its composition and the shared
  W4 gate:
  - `test_w601a_global_incidents`, `test_w601b_global_maintenance`, `test_w601c_request_detail`,
    `test_w601e_operational_index`;
  - the W4 Work API (`test_w401_work_api`, `test_w401_site_indexes_postgres`);
  - the W5-02 domain Work API (`test_w502_domain_action_index_api`, `test_w502_domain_intent_api`);
  - the new `test_r373_request_access`.
- **Frontend:** the changed client test, plus the three component tests that assert the changed string.

## Results (all at 7fc30340)

Every Python run here sets `PYTHONPATH` to this worktree's `backend;contracts;gateway;simulator`. The worktree
`.venv`'s editable installs point at the main checkout (`C:\Users\assef\Bineyame\AssetOPsV1`), so without that the
tests would exercise main's code. The full-suite run must do the same.

| Check | Result |
| --- | --- |
| Focused backend (9 files above), real Postgres `assetops_test` base | **95 passed, 0 skipped, 0 failed**; JUnit tests=95 skipped=0 failures=0 errors=0; wall 992 s |
| Frontend vitest (4 files) | 4 files, 58 passed |
| `npm run typecheck` | clean |
| `tools/check-architecture.ps1` / `tools/check-agent-workflow.ps1` | passed / passed |
| Full real-Postgres backend suite | **not run**, held for a quiet machine (coordinator) |

## Non-vacuity (ruling Q6)

- **Mutation:** in `main.py` the global router went back to `access=development_access`, with the Site Work and
  domain wiring left shared.
- **Run:** `test_r373_request_access.py` gave **8 failed, 2 passed**. The two passes were the allow-path and the
  default-admits tests, which should pass under the mutation.
  - Failures: no-DB deny, mini, cold, EV, and all four list roots.
  - Messages: `assert 200 == 403` on global detail; `assert [{'site_code': 'KOBO-001', ...}] == []` on the lists.
- **Restore:** `git checkout -- backend/assetops_backend/main.py`, after which `git status` was clean. The green
  results above were run on the committed code.

## Walkthrough proof (ruling Q7), committed tree 7fc30340

- **How it was run:**
  - Private tags `r373`: cold `w502b_positive_r373_test`, EV `w504a_*_r373_test`.
  - Steps: prepare, serve, (EV: attest), probe, drop. All databases were dropped and the work folders removed.
  - Probe: `GET /api/work/requests/{wr}?site_id=`, `GET /api/sites/{site}/work/cases/{wr}`, and the global
    incidents/maintenance/preventive lists over the last 7 UTC days.
  - Linked WR: the maintenance request in `domain_action_case_link`.
- **Results:**

| Walkthrough | Process | Global detail (linked WR) | Unknown / malformed | Global lists, Site rows (inc/maint/prev) |
| --- | --- | --- | --- | --- |
| cold COLD-LAB-001 | granted `positive` | 200 (Site Work 200) | 404 / 404 | 1 / 1 (linked WR listed) / 0 |
| cold | `forbidden` | 403, byte-identical to Site Work 403 | 403 / 403 | 0 / 0 / 0, HTTP 200, total 0 |
| EV EV-LAB-001 | granted `positive` | 200 | 404 / 404 | 1 / 1 (linked WR listed) / 0 |
| EV | `forbidden` | 403, byte-identical to Site Work 403 | 403 / 403 | 0 / 0 / 0, HTTP 200, total 0 |

- **Observations, not R373 changes:**
  1. The walkthrough serve processes do not set `ASSETOPS_WORK_CURSOR_KEY_HEX`, so their global lists answer 503
     `WORK_STORE_UNAVAILABLE` (seen on the first cold probe). The probes above ran with the key set in the operator
     shell. The W6 recapture must set it too.
  2. In the EV granted `positive` process, the Site Work case detail answers 503. This predates R373: the W5-04
     `SERVE_ENTRY` prepends `build_work_router(None, ..., lists=...)` without `details`, which shadows the product
     detail route. The global detail (the B19 route) reads 200. Left for the W5/W6 owner; not changed here.

## Known deviations

- Q8's full backend suite and the current-SHA B19 403/200 recaptures (mini-grid, cold, EV; 1440 and 390) are not
  done. Both are held: the suite for the coordinator's quiet-machine schedule, and the recaptures until the suite
  finishes. The recaptures reuse `.agent/post-W6-audit/batch-19/tools/` (capture-only).
- Independent review is pending.

## Residual risk / review focus

- `global_work_api.py`: `no_store` routes the absent-detail case through `WorkGate`'s 503. That message is the W4
  `MESSAGES["WORK_STORE_UNAVAILABLE"]`, the same literal the detail used before. `test_w601c` refusal-order tests pass.
- Estate roots and other Site reads remain on `development_access` (R374).
- User review: not required for this backend/security slice. The copy change is one sentence.

## Fix round and merge proof (post-review)

Code revision for all proof below: `7b1e3a82` (fix round on top of review commit `55519d1a`). Later commits touch
only this packet and the recapture folder. Packet commit is the branch head.

- **M1 (mini-test time bomb) fixed.** `test_r373_request_access.py`: `vertical_proof` takes an optional
  `other_window`; the mini test checks the linked request in the fixed fixture-clock window and the KOBO-002
  request in a one-day window derived from that request's own recorded `created_at` (read from the granted global
  detail). No wall-clock read remains in the mini test, so no window can grow past 31 days.
  - **Pin proof** (a pytest plugin patches the test module's `datetime.now` to 2026-12-01T09:00Z):
    new version `-k mini` **1 passed**; the old version (`git show HEAD:` copy) under the same pin **failed with
    `KeyError: 'rows'`** (422 `INVALID_WINDOW`), the review's scenario. Unpinned, the whole file: 10 passed.
- **L2 fixed:** `tools/w502_cold_work_walkthrough.py` module docstring and the w504 `SERVE_ENTRY` docstring now say
  the global Work router sits ahead of the product routes behind the grant. L1 is already in R374; nothing done.
- **Focused set** (the 9 files above, real Postgres `assetops_test`, PYTHONPATH on this worktree, at `7b1e3a82`):
  **95 passed, 0 skipped**; JUnit tests=95 failures=0 errors=0 skipped=0; wall 1000 s.
- **Full suite:** ran at `ba9610dd` (before the test-only fix): 4051 passed plus 2 known schedule-timing tests that
  fail identically on main. Not re-run; this round changes one test file and two docstrings.
- **Current-SHA B19 recaptures (ruling Q8)**, capture-only (`.agent/post-W6-audit/batch-19/tools/capture-b19.mjs`),
  revision `7b1e3a82`, `.agent/post-W6-R373-recapture/` (`part-<vertical>-<200|403>/`, `SUMMARY.txt`, `tools/`, `logs/`).
  - Mini KOBO-001 (`w601_seed detail-linked`, WR-000005, linked): 200 on production `main:app` (18901); 403 on
    `tools/deny_app.py` = `create_app(site_read_access=deny)` (18902).
  - Cold COLD-LAB-001 WR-000002 (linked): 200 on the walkthrough `positive` process (8971, hard-coded), 403 on its
    `forbidden` process (8976).
  - EV EV-LAB-001 WR-000002 (linked via `attest`): 200 on `positive` (18904), 403 on `forbidden` (18909).
    `W504_API_PORT_BASE=18903` puts the `unavailable` process at 18910, one past the block (stopped by `attest`).
  - Each phase, overview, record and history at 1440 and 390: **6 pairs, 36/36 claims passed**, 0 horizontal
    overflow. 200 renders the request (title, WR code, tabs); 403 renders the "Work request / Request details could
    not be shown" state on all three tabs, identical for all three Sites. `ASSETOPS_WORK_CURSOR_KEY_HEX` was set.
  - Cleanup: processes stopped by PID, work folders removed, `*_r373rc_test` DBs dropped (none left).
