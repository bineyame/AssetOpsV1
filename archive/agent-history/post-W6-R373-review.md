# post-W6 R373 (B19-15, High D3) - independent review

Reviewer: fresh Claude reviewer (did not author the slice). Branch `task/post-W6-R373-request-access` at
`ba9610dd`; diff against merge-base `3b726db9` (main). Code commit `7fc30340`; `ba9610dd` adds only the packet.
Authority: `.agent/post-W6-R373-rulings.md` Q1-Q8.

## Verdict

**REJECT (narrow fix round: M1 only).** The product code, wiring, walkthrough changes and copy are correct and
would be ACCEPT-WITH-LOWS on their own. The one Medium is a test defect: a wall-clock time bomb in the mini vertical
test, which will turn a merge-gate security test red from 2026-11-14. Medium blocks, so fix it on the branch.
The re-check can then be limited to that test. R373 stays open under ruling Q8 until the full suite and the
current-SHA B19 recaptures exist; this review does not close it.

## Findings

### Medium

**M1 - The mini vertical test fails deterministically from 2026-11-14.**
`backend/tests/test_r373_request_access.py:183-185` (with `:137-152` and `:246-249`).
- The seeded `detail-linked` request is written at the fixed `CLOCK` (2026-10-20, `w601_seed` `WriteClock`).
- `other_site_request` creates the KOBO-002 request through `WorkService` at real wall-clock time.
- Global maintenance filters on `created_at`. The test therefore builds one window from `CLOCK - 6 days` (midnight
  2026-10-14) to `midnight(now) + 1 day`.
- `parse_global_request` refuses any window longer than `MAX_DAYS = 31` (`work/global_index.py:53,125`).
- **Failure scenario:** any run on or after 2026-11-14 UTC. That includes the periodic safety-net suite on main.
  The window becomes 32+ days, `/api/work/maintenance` answers 422 `INVALID_WINDOW`, and `vertical_proof` fails
  with `KeyError: 'rows'` at `:166`. A merge-gate security test then goes red for a reason unrelated to access.
- **Fix:** create the KOBO-002 request at the fixture clock, for example through the w601 `Writer`/`WriteClock` or a
  seed fixture covering both Sites, so the mini window is fixed. Alternatively, assert the two requests' list
  membership in two separate fixed windows. Cold and EV are not affected, because both their requests are written
  at real time.

### Low

**L1 - Work-namespace Site reads outside the seam are not named in R374.**
- `/api/sites/{site}/work/decision-contexts` (`mini_decisions_api.py:51,291-303`) stays on
  `build_mini_decisions_router`'s default `access=development_access` (`main.py:518`).
- It answers 404 `WORK_CASE_NOT_FOUND` vs 200 by work-case visibility (`mini_decisions/work_links.py:156-157`).
- I verified it with `create_app(site_read_access=deny)` and no database. The global and Site work detail both
  answered 403, but decision-contexts answered 503 `DECISION_STORE_UNAVAILABLE`, so the shared callable is never
  consulted there.
- `/api/sites/{site}/action-index`, the "Site Work Action index" (`main.py:555`), is likewise outside the seam.
- This follows ruling Q4, which says not to thread unrelated Site routers, and the R374 row ("other Site reads")
  covers it nominally.
- **Failure scenario:** a later rollout wires a real principal through `site_read_access` only. A denied principal
  can then still probe whether work case IDs exist at a denied Site through decision-contexts. This is the same
  oracle class as B19-15.
- **Fix:** no code in R373. Name these two routes explicitly in the R374 register row or the R373 closeout so the
  R374 inventory cannot miss them.

**L2 - The w502 tool docstring is stale.**
- `tools/w502_cold_work_walkthrough.py:33-41` describes the serve entry as the domain-work router plus the K3 W4
  router, "No product router changes".
- It does not say that every process (granted ones included) now also prepends the global Work router behind the
  grant.
- So in the granted cold and EV processes, other Sites (KOBO-*) now drop out of the global lists. That is
  intended, but a recapture reader would not expect it.
- **Fix:** one sentence in the module docstring. The w504 docstring is generic and needs no change.

## Verified against the diff (not the packet)

- **One shared callable.** `main.py:230` adds `site_read_access: Access = development_access`. It is passed to
  `build_work_router(access=)` (`:577`), the domain `WorkGate(access=)` (`:582`) and
  `build_global_work_router(access=)` (`:592`). The global router uses that one `access` for the detail gate
  (`global_work_api.py:57`) and for the four list predicates (`:73`). Write grants (`command_access`) and principal
  injection are unchanged.
- **Access before scope or store.**
  - The detail now calls `WorkGate.read_scope` (`work_api.py:73-86`): access 401/403, then scope 503/404, then the
    case and `known_at` inside `details.detail`.
  - Before access, only `authenticate` and the single-`site_id` check run (`global_work_api.py:105-109`). Neither
    depends on the case.
  - The old 503 when `details`/`scope` is absent is kept, after access, through `no_store`. The message comes from
    the same `work.model.MESSAGES` literal the old inline path used.
  - The old except set `(SiteStoreUnavailable, FoundationStoreError, WorkStoreUnavailable, *unavailable)` equals the
    gate's.
  - The literals equal the removed inline copy, so the refusal-order contract of `test_w601c` is unchanged.
- **Byte-identical 403.** I ran a no-database probe (`create_app(site_read_access=deny)`) of an unknown UUID and a
  malformed ID on global detail, plus the Site work detail. All three returned the same bytes,
  `{"detail":{"code":"SITE_SCOPE_FORBIDDEN","message":"No access to Site 'KOBO-001'."}}`, with no
  `WWW-Authenticate` header. No case-dependent work runs before the refusal, so timing order cannot vary by
  existence.
- **Lists.** The denied Site never reaches `service.read`'s admitted set (`:73`). The Postgres list test asserts:
  - no denied row on any limit-1 page, and rows equal to the full read minus the denied Site;
  - `total_count` strictly smaller, with `state_counts` summing to it;
  - every cursor's `authorized_site_ids` excluding the denied Site;
  - a wider-grant cursor never paging denied rows;
  - an empty 200 when fully denied;
  - non-empty preconditions (`test_r373_request_access.py:208-239`).
- **Route sweep in `create_app`.** Routers on `development_access` are the estate roots (`:560-571`) and the EV/cold
  replay (`:645`). Routers on their own defaulted `access` are finding, finding-index, action, action-index, mini
  decisions and financial reads. No router that serves work cases or work lists (`/api/sites/{s}/work/cases*`,
  `/work/{incidents,maintenance,...}`, `/domain-work/*`, `/api/work/*`) is left off the seam. The one exception is
  the work-namespace decision-contexts read (L1), which is in R374's stated scope.
- **Tests.**
  - All three verticals use real linked requests: mini `detail-linked` via w601; cold `cold` + `bind`; EV is a
    composed EV domain Action linked through `post_case_link`, not the bare-request fallback.
  - The test asserts `action_links or finding_links` is non-empty.
  - The restated EV fixture (`:259-284`) matches `test_w504_ev_intent_postgres.ev` plus the W2-05b chain factory.
  - Unknown, malformed and foreign-Site (KOBO-002) IDs are each checked on both routes.
- **Non-vacuity, reproduced independently without a database.** I monkeypatched `main.build_global_work_router` to
  force `access=development_access`. Global detail under a deny grant then returned 503 `WORK_STORE_UNAVAILABLE`
  instead of 403. That is the failure `test_denied_site_is_the_same_403_on_both_detail_routes_without_a_database`
  catches, and it confirms that the test is bound to the wiring.
- **Walkthrough `SERVE_ENTRY`.** Both blocks prepend `build_global_work_router` with:
  - the product's `M.build_global_work_index_service(url)`, `M.registry_tenant(registry)` and
    `M.SiteStoreUnavailable`;
  - `M.build_global_work_detail_service(url)` and `registry.ledger_scope`;
  - `access=access`.

  All of these names are module-level in `main.py` (`:55,86-87,189`). Using `url` rather than w502's `work_url`
  matches the product router as ruling Q7 requires. Both observations in the packet are pre-existing: no cursor key
  in the serve processes, and the EV Site Work detail 503 shadow.
- **Frontend copy.** `globalWorkClient.ts:454` is now exactly "No access to this Site's work." (Q5). The client test
  and the three component literals are updated, and nothing else changed.
- **Labels.** R373 stays `open` in `.agent/mock-departure-register.md:474` and R374 is registered at `:475`. The
  packet labels the held full suite and recaptures as Known Deviations. I found no unlabelled D3 or departure. The
  docstrings in `main.py` and `global_work_api.py` state the Q1 reachability honestly: the default still admits the
  development operator.

## Checks run (reviewer, this machine, worktree code via PYTHONPATH)

| Check | Result |
| --- | --- |
| `pytest backend/tests/test_r373_request_access.py -q` with no DB URL (`assetops_backend` resolved to the review4 worktree) | 3 passed, 7 skipped (the Postgres tests, by design) |
| No-DB mutation probe (global router forced to `development_access`) | real: 403, identical bytes on 3 requests; mutated: 503, so the test catches it |
| `tools/check-architecture.ps1`, `tools/check-agent-workflow.ps1` | `Architecture check passed.` / `Agent workflow check passed.` (exit 0) |

## Not verified (quiet machine; honest gaps)

- All Postgres-backed tests: the 7 R373 DB tests, `test_w601a/b/c/e`, W4 and W5-02 API tests. I rely on the
  packet's focused run at `7fc30340`: 95 passed, 0 skipped, 992 s. `7fc30340` has the same code tree as
  `ba9610dd`.
- The full backend suite. The packet records it as not run, and Q8 requires it at the final SHA.
- The walkthrough probes and the B19 403/200 recaptures at 1440 and 390.
- Frontend vitest, the build, and `tsc` were not run under the quiet-machine instruction. The frontend change is
  one string literal plus an exported-constant import that already exists.

## Residual risk not named in the packet

- The global lists treat an `access` result of 401 as "not admitted" and filter silently, rather than answering
  401. This predates R373, but once a real principal returns 401 the lists will show an empty 200 instead of a
  sign-in refusal. R374's principal policy should decide it.
- After R373 only the detail routes get a 403. The global lists of a principal with no grant at all are an empty 200
  (ruling Q4), so the UI will show "no work" instead of "no access" there. This is per ruling, noted for the W6 card.
