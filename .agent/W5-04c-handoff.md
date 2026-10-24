# W5-04c handoff - V4a, V4b and V5 (EV Action detail `ev-action`, captures and closeout)

Branch `task/W5-04c-ev-action`, cut from main `ad7b82f9`. **Not yet rebased on W5-04b**: it merges first, then this
branch merges main, resolves conflicts and reruns the batch (see "Rebase plan"). Two open questions are in
`.agent/W5-04c-questions.md`. Neither blocks the build; both are recorded as pending rulings, not decisions.

## Commits

| Commit | Unit | What |
|---|---|---|
| `3b2b5f1f` | V4a | The domain shell (`ColdDomainActionShell` becomes `DomainActionShell`; `ColdActionRoute` becomes `DomainActionRoute`) and `DomainActionVerification` now take explicit presentations: `DomainActionPresentation` / `DomainActionPanelPresentation` (interfaces in `DomainActionVerification.tsx`). `COLD_ACTION_PRESENTATION` lives in `coldWorkPresentation.ts`, with the K4 criteria literals moved there (ruling 47). `EV_ACTION_PRESENTATION` lives in `evWorkPresentation.ts`. `SiteActionFrame` dispatches `COLDCHAIN \| EV_CHARGING`. The detail parser accepts the EV domain and, for EV, accepts only `PENDING`. `getDetail` takes an optional 4th `siteType` argument for the EV refusal copy (ruling 64). EV detail links keep `from,to,known_at`. `EV_ACTION_LINK_LIVE = true` (closes R113). `SCREEN_LEADING['ev-action']` added. Register R109/R110/R113 statuses updated. Q1 recorded. |
| `f331e7a0` | V4b | `W504_EVIDENCE=action` mode in `tools/w504-ev-work-evidence.mjs`. The list mode's R113 claim now asserts the live link. Navigation waits until the page reaches the requested address (`goTo`), and Chrome cleanup is scoped to this run's profile. `ev-action` ledger and panel-contract rows promoted; the registry is untouched. Evidence in `.agent/W5-04c-evidence/`. |
| `d248f322` | V5 | `test_v5_ev_lineage_from_public_session_to_intent_without_automatic_work` in `backend/tests/test_w504_ev_intent_api.py`. |
| (this) | V5 | Handoff, plus Q2 in the questions file. |

## Cold output byte-identical (rulings 41/53)

- **Probe.** `.agent/W5-04c-evidence/cold-bytes/zzColdBytes.scratch.test.tsx` is a scratch vitest file; it was never
  committed under `src`. It renders 40 cold states through `SiteActionFrame`:
  - 17 loaded or refused states, each with and without `known_at`;
  - loading;
  - the redirects from the bare and `/plan` addresses;
  - three real-client fallbacks: network failure, malformed 200, and a 503 with no body.
- **Method.** It wrote `document.body.outerHTML` per state at base `ad7b82f9` (`cold-base.json`) and again on the V4a
  tree (`cold-head.json`).
- **Result.** Diff: **40 keys each, 0 differences.**
- **Permanent test.** It pins `COLD_ACTION_PRESENTATION`'s literals and status tail exactly
  (`domainActionVerification.test.tsx`).
- **Unchanged.** Cold CSS is unchanged (`w1f4-action.css` not touched), so cold K4 was not recaptured.

## Checks (on `d248f322`)

- **`tsc --noEmit`:** clean.
- **Full vitest (`--minWorkers=1 --maxWorkers=2`):** 125 files; **2937 passed, 1 failed**, 7m52s.
  - The failure is `siteFindingEvidence.test.tsx` "renders Evidence as a child view…". Its heading was still the
    `Finding` placeholder: a load-timing flake in an untouched mini-grid file. Rerun alone: 45/45 passed.
  - A targeted run earlier saw the same kind of flake once in `s404SiteFindingIndex` (37/37 alone).
  - The machine was shared with the parallel builder.
- **`vite build`:** green, 14.3s.
- **`tools/check-all.ps1`:** **All 11 guards passed**.
- **Registry, ledger and missing-claim scan:** `check_v69_dependency_registry.cjs` exit 0; `check_v69_ledger.py`
  valid (110 screens, 258 panels); `missing-claim-scan.mjs` run read-only, passed.
- **Focused Postgres:** `test_w504_ev_intent_api.py` and `test_w504_ev_intent_postgres.py`, `-n 4`, on private
  `assetops_w504c_test`, with PYTHONPATH set to this worktree. JUnit tests=21, failures=0, errors=0, skipped=0. Wall
  time 4m45s. The database has been dropped.
- **Full backend suite:** not run. No product backend, migration, `composition.py`, `main.py`, `tools/checks` or
  fixture changed; the only backend change is one test (tiered testing). The coordinator decides on the post-rebase
  head.
- **Non-vacuity.** Committed first, then each mutation was reverted with `git checkout`:
  - `EV_ACTION_LINK_LIVE = false`: 6 failures.
  - Dispatch limited to `COLDCHAIN` only: 24 failures.
  - `SCREEN_LEADING['ev-action']` removed: 5 failures.

## Walkthrough, captures and processes

- **Walkthrough.** `tools/w504_ev_work_walkthrough.py` is unchanged. It ran through
  `.agent/W5-04c-evidence/walk_ports.py`, which overrides only `PORTS` to 9001-9007 so the run cannot collide with
  W5-04b's 8981-8987. Work folder `var/w504a_c4_work`, tag `c4`.
  - `prepare`: 2m51s. positive, zero and worstcase ready; unknown, pending and stale unavailable (as V2b).
  - `serve`: 5/5 healthy.
  - `attest`: forbidden 403 `SITE_SCOPE_FORBIDDEN`; unavailable stopped.
- **Vite and Chrome.** Vite ran on 5501/5502/5503/5506/5507 (PIDs 492, 20268, 12124, 31348, 21264); headless Chrome
  used CDP port 9491.
- **Action captures** (`W504_EVIDENCE=action`): **212 PASS, 0 FAIL, 9 INFO**, 18 PNGs, `w504c-measurements.json`.
- **EV Work list recheck:** **195 PASS, 0 FAIL, 11 INFO** in `ev-work-recheck/`. The R113 claim now asserts that every
  EV row, including folded rows, has exactly one link to its own `/verification`.
- **Cap misses: none.** The mock baseline was page 1001/1123, strip 44, plan 243/401. All heights below are in px
  (1440 / 390):

| State | main | strip | plan or state panel | notices |
|---|---|---|---|---|
| positive (also reached by the Work click) | 525 / 776 | 42 / 42 | plan 248 / 406 | closing 42 / 60 |
| historical (`known_at` = index read) | 585 / 836 | 42 / 42 | plan 248 / 406 | currentness 42; closing 42 / 60 |
| missing-intent (`known_at` = K1, HISTORICAL) | 440 / 555 | 42 / 42 | plan 103 / 126 | currentness 42; closing 42 / 60 |
| worst-text (worstcase ACT-000002, 160 + 160) | 643 / 991 | 42 / 114 | plan 248 / 406 | closing 42 / 60 |
| forbidden-403 | 315 / 361 | - | state 158 / 158 | - |
| invalid-422 (future `known_at`) | 315 / 384 | - | state 158 / 181 | - |
| not-found-404 | 220 / 266 | - | state 63 / 63 | - |
| unavailable-503 | Site-level refusal (API stopped) | - | - | - |

  Caps (ruling 25/50): page 1500/1900, strip 140/200, plan 360/590, state panel 360/590, notice 110/160. Every state
  has zero document horizontal overflow.
- **Unavailable captures** (recorded INFO, each kept as a pure vector):
  - 409 `DOMAIN_INTENT_BASIS_CHANGED`: not producible by the native replay (rulings 54/55).
  - Missing intent with UNKNOWN currentness.
  - Pending and stale.
  - In-panel 503 with a healthy Site read.
- **Cleanup.**
  - Vite: stopped by PID after checking each command line.
  - Walkthrough `drop`: stopped its uvicorn processes and dropped `w504a_{positive,zero,worstcase,unknown}_c4_test`.
  - `assetops_w504c_test`: dropped.
  - Two leftover capture Chromes from early runs (PIDs 23352 and 18864, both verified as CDP 9491) were stopped by PID
    tree. The new cleanup step now prevents these.
  - All of 5501-5507, 9001-9007 and 9491 refuse connections.

## Judgment calls (please confirm)

1. **Q1 (open).** The live EV Work link is the server's bare `links.action`, the same as cold. The detail keeps
   `from,to,known_at` on its own Verification tab and redirect. Appending the query to the list link would need
   `SiteWorkActions.tsx`, which is not in the V4a files. Options are in the questions file.
2. **Q2 (open).** The `ev-action` ledger `data_owner` and `supported_claim` literals are not given in the spec. The
   strings used are listed in the questions file.
3. **Files outside the V4a list, forced by the R113 switch flip:**
   - `evWorkActions.test.tsx` (on the V5 list): its 2 plain-code assertions now assert the live link.
   - `w1f4ChangesWorkStructure.test.tsx` (V2a/V3a): its one assertion
     `main a[href*='/verification']` is null now expects exactly the row's href.
   W5-04b also edits the second file, so expect a merge conflict there.
4. **EV results strictness.** The client accepts only `PENDING` for an EV detail (`EV_DOMAIN_RESULTS`, from the backend
   EV `initial_results`). Any other value is the EV "unexpected shape" refusal, following the K4 strict-client
   precedent.
5. **Presentation choice before a read.** Before a loaded read, presentation follows the Site type. Once loaded, it
   follows `action.domain` (P-K2a-48).
6. **Missing-intent capture.** The producer's honest missing-intent state is `known_at` = K1, which reads as
   HISTORICAL. Ruling 40's UNKNOWN combination is a pure vector.
7. **Evidence tool fixes** (capture-only):
   - The arrival-checked `goTo` is now also used by V2b's `record`. Before, a previous page's refusal text could
     satisfy READY, and two recheck runs measured half-loaded pages.
   - The `finally` block stops only the `chrome.exe` processes whose command line holds this run's unique profile.
8. **Narrow criteria table.** At 390 the criteria table wraps at 318/318 with no internal scroll. This is the same
   shared `DataTable` as cold K4; the mock notes a 320 scroll. It is not a new departure. All 9 cells are contained.
9. **V3/V5 files skipped.** `evWorkCases.test.tsx` (on the V5 list) does not exist on this base; V3a creates it. No
   EV case assertion was added.

## Shared plumbing touched

- `frontend/src/test/panelStructure.ts`: one `SCREEN_LEADING` entry plus a comment. W5-04b adds the neighbouring
  entries, so expect a trivial conflict.
- `frontend/src/shell/SiteAnalyticsFrames.tsx`: the presentation imports and the domain Action region only. The
  Work-cases frame, which W5-04b edits, is untouched.
- `tools/w504-ev-work-evidence.mjs`: shared with V3b; conflicts are likely in its header, MEASURE and main.
- Not touched: `tools/checks/*`, `App.tsx`, `NavRail` and `OperatorShellLayout` (K4a's override is reused), backend
  product code, migrations and composition.

## Rebase plan (after W5-04b merges)

1. Merge main and resolve conflicts:
   - `panelStructure.ts`: keep every EV entry.
   - `w1f4ChangesWorkStructure.test.tsx`: keep V3a's tests and apply the live-link expectation to any EV Actions
     plain-code assertion.
   - `tools/w504-ev-work-evidence.mjs`: keep V3b's case modes, the action mode, `goTo` and the R113 claim.
   - Ledger and panel contracts: keep V3b's three rows and the `ev-action` row.
2. Grep V3a/V3b for any remaining plain-EV-code assertion (`data-domain-work-action-plain`, R113) and update it.
3. Rerun: tsc, full vitest, build, check-all, registry/ledger/missing-claim, focused w504 Postgres. Then walkthrough
   prepare/serve/attest through `walk_ports.py`, the action captures and the list and case captures.
4. Check line endings: `git ls-files --eol | grep "eol=lf" | awk '$2=="w/crlf"'`.

## Registry (V4b packet item)

`A-ev-work-projections` stays open. Its open predecessors are `A-ev-session-rules` (W2-06), `A-maintenance-index`
(W4-01) and `A-work-cases` (W4-01); all three show `status:"open"` in `v69-dependency-registry-pilot.json`.

## Rulings 67/68 round (main `f5f7f70b`, merged at `e37ece05`; commit `c7ffced6`)

- **Ruling 67 (Q1).** `DomainWorkPresentation.actionHref` was added in `SiteWorkActions.tsx`, which is now a V4a file.
  - Cold keeps the server `links.action` unchanged.
  - EV uses `evActionHref`. It takes the server pathname and adds the selected `from` and `to`, plus `known_at` only
    when a cutoff is explicit. It never carries the cursor.
- **New tests in `evWorkActions.test.tsx`:**
  - a historical window and cutoff: the click opens the detail at the same address, reads at `known_at`, and the
    Verification link keeps the scope;
  - a reload of that detail address;
  - no explicit cutoff: the link carries `from,to` only, and a list cursor is dropped;
  - `evActionHref` replaces any server query;
  - the cold href stays byte-identical.
- **Adjusted assertions.** The EV href assertions in `operatorRouteFrames` and `w1f4ChangesWorkStructure` now expect
  the query. The capture tool's R113 and work-link claims now expect it too.
- **Register.** The R113 row now mentions the query.
- **Non-vacuity.** Making the EV `actionHref` return the server href unchanged fails 5 tests; reverted with
  `git checkout`.
- **Ruling 68 (Q2).** The `ev-action` ledger strings already match exactly, so nothing changed.
- **Checks on this round:**
  - tsc is clean.
  - Targeted vitest, 6 files: 173/173 passed.
  - check-all: 11/11 passed.
- **Captures not rerun yet.** The committed W5-04c evidence predates the tool claim change. The action and list
  captures are rerun in the post-W5-04b batch.
