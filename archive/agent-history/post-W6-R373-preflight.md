# post-W6 R373 (B19-15, High D3) - pre-flight

Branch `task/post-W6-R373-request-access` from main `aa08d16d`. Ruling: `.agent/post-W6-audit/fix-slices.md`
"Explicit Architect rulings" / "B19-15 access". Evidence: `.agent/post-W6-audit/batch-19/batch-19.md` B19-15, Blockers.
No product code written. 8 questions; each has a recommended default the build will follow unless overruled.

## What the dry read found

- `backend/assetops_backend/main.py:582-585` composes `build_global_work_router(..., access=development_access, ...)`.
  `development_access` (`finding_api.py:46`) returns `None` (admit) for every request and Site.
- Site Work is `build_work_router(...)` at `main.py:569-572` with **no `access` argument**, so it also defaults to
  `development_access` (`work_api.py:100-102`). The domain-work `WorkGate` at `main.py:577` likewise passes no access.
- So in the product composition today **no principal gets 403 on Site Work either**; both routes admit everyone
  (the documented `ACCESS_BASIS` development operator context). The 403/200 split in B19-15 exists only in the
  W5 walkthrough `forbidden` processes (`tools/w502_cold_work_walkthrough.py:542-559`,
  `tools/w504_ev_work_walkthrough.py:493-502`), which prepend Site Work and domain-work routers behind a denying
  `access` but leave `create_app`'s global router on `development_access`.
- The real defect is structural: `create_app` has no single Site-read access input. Each router gets its own
  (default) callback, so wiring a real principal into Site Work alone leaves global Work open. That is what makes it
  production-reachable as soon as authentication lands.
- The global detail route (`global_work_api.py:94-121`) already reimplements `WorkGate.read_scope`
  (`work_api.py:73-87`) inline, with the same order and literals. Access runs **before** the case-UUID parse and the
  store read, so the refusal never depends on `case_id`.
- **The global LIST routes share the gap.** `/api/work/{incidents,maintenance,preventive,operational-records}` are on
  the same router and filter Sites through the same `access` (`global_work_api.py:64`). Under a denying principal
  in the walkthrough compositions, the denied Site's rows still appear. The estate roots (`main.py:555-567`, W3) are
  composed the same way.
- Frontend: `frontend/src/work/globalWorkClient.ts:441-464` already parses 403 `SITE_SCOPE_FORBIDDEN` and shows
  "No access to this Site's work request."

## Questions and defaults

**Q1 Production reachability wording.** Should the closeout record that today's product composition admits everyone
on both routes, and that the defect is a composition seam (reachable in the walkthroughs, and in production once a
real access exists)? *Default:* yes. Record it, still treat it as High, and fix it structurally (Q2).

**Q2 Seam to reuse.** *Default:* add one keyword, `site_read_access: Access = development_access`, to `create_app`.
Pass that one callable to `build_work_router(access=)`, the domain-work `WorkGate(access=)` and
`build_global_work_router(access=)`, so Site Work and global Work cannot diverge. In `global_work_api.py`, replace
the inline duplicate with a call to `WorkGate(scope, unavailable, access).read_scope`, keeping the current 503 when
`details`/`scope` are absent. That is the same admission function, not a copy. Literals and order stay unchanged.

**Q3 Denied response.** *Default:* 403 `SITE_SCOPE_FORBIDDEN` `"No access to Site '<code>'."`, the same as Site
Work. Existence does not leak because the body is byte-identical for an existing request, an unknown UUID, a
malformed ID, and a request belonging to another Site. Access precedes every case lookup, and tests will assert
this. Not 404: Site Work answers 403 for the same principal, and a 404 on only one route would make the two disagree.
*Alternative for the Architect:* 404 `WORK_CASE_NOT_FOUND` on both routes, if Site-level denial must also be hidden.
That is broader than R373 and would change W4.

**Q4 Lists.** *Default:* the Q2 parameter covers all four global lists automatically, because they share the router
and its `access`. Per their contract they filter silently, never 403/404. Tests will assert that the denied Site's
rows are absent from `rows`, `total_count` and the cursor digest. Estate roots (`/api/estate/*`) and the other Site
routes (Finding, Action, Overview and the rest) also default to `development_access`; that is the known development
basis. *Default:* out of R373 scope, flagged for the Architect. Not threaded now.

**Q5 Frontend.** No new status reaches the UI: the detail route already returns 403 and is already mapped, and the
lists only shrink. The copy "No access to this Site's work **request**." names a request, which implies one exists.
*Default:* change it to "No access to this Site's work." (one string plus its client test). *Alternative:* stay
strictly backend-only and leave the copy to the W6 global Work card.

**Q6 Tests to add.** New file `backend/tests/test_r373_request_access.py`:
- No database: `create_app(site_read_access=deny)`. Site Work `GET /api/sites/{s}/work/cases/{id}` and global
  `GET /api/work/requests/{id}?site_id={s}` both return the identical 403 body. Access precedes the store and scope
  checks, so this proves the threading without Postgres. A granted principal gets past access (503/404, not 403).
- Postgres, one linked request per vertical, denied vs granted on both routes, plus the four lists:
  - mini: the `tools/w601_seed.py` `detail-linked` fixture.
  - cold: the `test_w502_domain_intent_postgres.cold` fixture plus `test_w502_domain_work_links_postgres.bind`.
  - EV: the `test_w504_ev_intent_postgres.ev` fixture with an EV equivalent of `bind`.
  - Each case also asserts a byte-identical 403 for an unknown UUID and a malformed ID.
  - *Default:* if an EV bind helper would exceed about 40 lines, use an EV-Site request created through
    `WorkService` without the Action link, and record that as a Known Deviation.
- Non-vacuity: drop `access=site_read_access` from the global router call in `main.py`, watch the tests fail, then
  revert.

**Q7 Dependents on the permissive path.**
- `test_w601a/b/c/e` build the router directly with their own `access` fake, and none calls `create_app`.
  Unaffected.
- `create_app` callers: the new keyword has a default, so all existing callers keep working.
- `.agent/W6-01-evidence/C2/api_403.py` prepends its own denying global router. Unaffected; leave it as evidence.
- `tools/w601_seed.py` has no access composition. Unaffected.
- The W5 walkthrough serve entries import a module-level `app` from `host/lab_app.py`, so they cannot pass the
  `create_app` keyword. Their `forbidden` process would keep showing the global request page.
  - *Default:* in both `SERVE_ENTRY` blocks, also prepend `build_global_work_router(..., access=access, ...)` (the
    C2 pattern), so `forbidden` yields a real 403.
  - Granted processes include their Site and are unchanged.
  - Recapturing B19 under the new 403 stays with the W6 global Work card.

**Q8 Verification.** Because this touches `main.py` composition and `global_work_api.py`:
- Focused checks: `test_w601a/b/c/e`, the W4 work API tests, the W5-02 domain-work API tests and the new file.
- Then one real-Postgres full backend suite on the final revision, with a JUnit zero-skip check, keep-awake running,
  and a 2x cap.
- `tools/check-architecture.ps1` and `tools/check-agent-workflow.ps1`.
- The frontend client test, only if Q5's copy change is taken.
