# S6-01b review packet: Action, recommendation and change surfaces

- **Task:** `tasks/S6-01b-action-ui.md`, Status `in_review`.
- **Branch:** `task/S6-01b-action-ui`, stacked on unmerged S6-01a `c341599b`.
- **Slice diff:** `git diff c341599b..HEAD`.
- **USER_REVIEW_REQUIRED:** true. Hold the merge until the owner has done the visual walkthrough (`.agent/S6-01b-owner-walkthrough.md`) and S6-01a has merged.
- **Rulings:** `D-2026-10-15-s601-action-store-and-ui` and `.agent/architect-S6-01-answers.md` (Q1-Q5, M1-M3).

## Outcome delivered

One persisted, Finding-linked Action can be viewed through real reads of S6-01a's API:

- **Recommendation** (Finding child view `/sites/{site}/findings/{id}/recommendation?revision_id=`) shows:
  - the proposal or the typed unavailable reason;
  - the accepted snapshot, beside a separately labelled live recomputation;
  - the trial limitation;
  - money only as a link, with no amount.
- **Action root** `/sites/{site}/actions/{id}`:
  - Overview, Application (`/execution`) and History, with exact `event_id` / `recorded_at` selection kept across sections and on reload.
  - The typed selector conflict.
  - Accept and apply controls appear only when the server returns `system_demo_capability.allowed` for the exact command. Each control is labelled SYSTEM demonstration and sends a fresh idempotency key.
- **Foundation change** `/sites/{site}/foundation/changes/{change_id}` shows:
  - the old and new reserve, unit, asset, effective time and recorded time;
  - the replaced, SPLIT and new Foundation versions;
  - the signal assignment set IDs;
  - links to the Action and the exact application event;
  - the Action's failed attempts and the pending outcome. No effect verdict is given.
- **Bare `/foundation/changes`** is an explicit unavailable state with a link back. No Foundation subtab was added.

## Files materially changed

- **Client and routing:**
  - `frontend/src/sites/actionClient.ts`
  - `actionPresentation.tsx`
  - `shell/operatorSiteRoutes.ts`
  - `App.tsx`
  - `shell/SiteAnalyticsFrames.tsx` (Action and change frames, Recommendation wiring)
- **Screens:**
  - `sites/SiteRecommendation.tsx`
  - `sites/SiteAction.tsx`
  - `sites/SiteFoundationChange.tsx`
  - `sites/SiteFinding.tsx` (the "What to do next" link)
- **Styles:** the end of `ui/primitives.css`, all rules under `.app-frame--operator`.
- **Tests:**
  - `sites/__tests__/siteAction.test.tsx` (30)
  - `siteFoundationChange.test.tsx` (8)
  - `siteFinding.test.tsx` (+1)
  - `test/settled.ts` (four loading sentences)
  - `tools/checks/missing-claim-baseline.json` (12 -> 11; the old "Not yet available" recommendation copy is gone)
- **Tools:**
  - `tools/s601b_action_walkthrough.py`
  - `tools/s601b-action-evidence.mjs`

## Acceptance criteria

| Criterion | Status | Evidence |
| --- | --- | --- |
| Recommendation: proposal, pinned Finding/Foundation/input IDs, limitation; typed unavailable reason | Met | siteAction tests "shows the eligible trial...", "typed unavailable reason"; browser `recommendation ineligible` |
| Accepted snapshot + Action link beside labelled live recomputation; no money as saving | Met | test "keeps the accepted snapshot..."; browser `recommendation: accepted snapshot beside labelled live status` |
| Controls only on exact granted capability; SYSTEM demonstration label; absent/denied read-only at 1440 and 390; server refusal shown | Met | capability tests at both widths; exact-command test (L2, mutation-proven); `accept/apply_capability_denied` tests |
| Overview: code, origin vs latest revision side by side, pinned basis, pending outcome | Met | test "Overview shows..."; browser `action-overview` |
| Application: ACCEPTED/APPLIED/FAILED/OBSERVED, actor kind, service/job, effective revision, change artifact; FAILED keeps pending; same key replays; new key after APPLIED gives 409 | Met | Application tests, three 422 variants, `apply_wrong_site_404`; browser `action-execution`, second Action |
| History: exact `event_id` and `recorded_at`, `(recorded_at, id)` order, both times on backdated OBSERVED, no invented revision; conflict 422; reload and navigation for each selector | Met | History tests; browser selection, reload and conflict claims |
| Changes panel: old/new reserve, unit, asset, effective/recorded, old/PUBLISH/SPLIT and binding revision IDs, application event, pending/failed state, no effect verdict | Met | siteFoundationChange tests; browser `changes:1#a` claims. "Binding" is a banned product word, so the label reads "Signal assignment versions"; IDs are exact |
| Change URL is a non-subtab deep route; bare route is unavailable with a link back; `foundationScreen.test.tsx:306,344` holds | Met | bare-route test (mutation-proven); full suite green |
| Cross-Site/unknown 404, typed errors, prior successful read preserved | Met | wrong-Site Action and change tests; M1 selection-not-found; "keeps the prior read when the re-read fails" |
| Owner walkthrough tool: private DB, prepare/serve/drop, scoped grants, URLs and event IDs | Met | `tools/s601b_action_walkthrough.py`, run end to end (below) |
| App vs v6.9 mock at 1440/390 for the five panels | Met | 56/56 browser claims; screenshots and `comparison.md` |

## Phase-1 review fold-in (`.agent/S6-01b-phase-1-review.md`)

- **M1:** `SelectionNotFound` handles a 404 `ACTION_EVENT_NOT_FOUND`. It reads "Selected event not found" and links to the latest record. Tested on the recorded `unknown_event_404`.
- **L1:** the test asserts the exact default `2026-11-02T00:00:00+00:00` (clock pinned). An untouched default is re-derived at click as the next UTC midnight after max(read time, now). An edited value is sent as typed.
- **L2:** a test fails if `granted()` stops checking the exact command.
- **L3:** with no `current_foundation_revision_id`, Apply is not offered and the reason is stated.
- **L4:** the five derived-body kinds are declared in the test header and marked where built. `capability_denied` is served as recorded. The wrong comment was removed.
- **L5:** tests now cover `apply_wrong_site_404`, the three 422 FAILED variants, `accept_replayed`, `latest_revision_after_apply`, and a SiteFinding with no recommendation link.
- **Owner note:** the newer-revision Recommendation is open again. This is set out plainly in the walkthrough doc.

## Checks run (final code revision `15d156d1`; docs commit follows)

**Frontend:**
- `npx.cmd tsc --noEmit`: clean.
- Full `npx.cmd vitest run`: 64 files, 1517 passed.
- `npm.cmd run build`: built.

**Backend.** The slice has no backend change; the run is on `15d156d1`.
- Command (PowerShell): `pytest backend/tests -n 2 --dist loadfile --no-loadscope-reorder -q --durations=30 --junitxml=.pytest-junit.xml`.
- Setup: `ASSETOPS_TEST_DATABASE_URL=.../assetops_s601b_test`, keep-awake running, `var/sites/*.yaml` copied in temporarily and removed afterwards, 20-minute cap.
- Result: 2209 passed, 29 warnings, wall 10:02.
- JUnit: cases=2209, skipped=0, failed=0.

**Guards:** `tools/check-all.ps1` passed all 9 guards, including architecture, agent workflow, navigation truthfulness, the dependency registry, missing-claim (11 baselined) and the screen ledger. A temporary `.venv` junction was used and removed afterwards. The guards were rerun after the docs commit (see the closing commit).

**Mutations.** Each was made on committed code and reverted with `git checkout`:
- `granted()` ignoring the command: fails the L2 test.
- Sending the stored `effective` without re-derivation: fails the L1 test.
- The default effective time on the same day instead of the next: fails 2 tests.
- Disabling the `ACTION_EVENT_NOT_FOUND` branch: fails the M1 test.
- Renaming the bare changes route: fails the bare-route test.
- Phase-1 mutations (handoff): `granted()` ignoring `allowed`, and selector dropped from section links.

**Walkthrough.** `prepare` on DB `assetops_s601b_owner` and `var/s601b_owner`:
- It built `D-action-records`: Action `ACT-000001`, change, 6 events.
- Performance cutover: permitted.
- It then ran `serve` (8961) and the frontend (5461), and then `drop`.

## Layout evidence

`node tools/s601b-action-evidence.mjs http://localhost:5461 <dir>`: 56/56 claims at 1440x1000 and 390x900.

- **No sideways scroll.** Every app screen was checked, and each check measured more than 70 elements. Dense tables scroll inside their own scroller. Table references stay on one line, which avoids letter-by-letter wrapping at 390.
- **Mock vs app.** Mock and app screenshots were taken for `recommendation`, `action-overview`, `action-execution`, `action-history` and `changes`.
- **`comparison.md`.**
  - Mock headings (ACT-048 generator stop policy, CHG-019, verification plan, guardrails) are illustrative.
  - The app shows the persisted reserve trial.
  - The mock's Plan, Evidence, Verification, target/guardrail cards and "Did the change improve" are S6-02 and are not rendered.

`node tools/layout-evidence.mjs http://localhost:5461 KOBO-001` (CDP 9462): 327 PASS, 2 FAIL. Both failures are environment preconditions that this private store cannot meet, and neither concerns S6-01b screens:
- no Lab Site with a 430 L tank;
- no legacy file Kobo Site.

## Known deviations

- **Signal assignment label.** "Binding revision IDs" are labelled "Signal assignment versions", because the product vocabulary bans "binding" and "mapping".
- **No OBSERVED command control.** The packet names only accept and apply; OBSERVED is displayed from reads.
- **Served clock vs fixture clock.** The served walkthrough reads on the real clock while the records carry the fixture clock. The served latest-revision recommendation therefore reads `FOUNDATION_BASIS_STALE`, where the recorded contract reads AVAILABLE. Both are shown as served.

## Residual risk

- The Recommendation for a newer FindingRevision does not mention the Action accepted on the earlier one. This is S6-01a server behaviour and a decision candidate for the Architect or owner.
- The default `effective_from` assumes the server and browser clocks roughly agree. A mismatch surfaces as a typed `ACTION_EFFECTIVE_TIME_INVALID`.
- jsdom 1440/390 tests prove structure only; rendered layout rests on the browser run above.

## User-review focus

Walk the eight steps in `.agent/S6-01b-owner-walkthrough.md` at 1440 and at 390. In particular:
- whether the accepted-snapshot vs live-recomputation pairing reads clearly;
- the change page's versions table;
- the honesty wording (no effect, saving or approval);
- whether a newer Finding version should show the earlier Action.
