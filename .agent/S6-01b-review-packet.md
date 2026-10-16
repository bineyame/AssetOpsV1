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

- (Resolved in the reopen round below: the newer FindingRevision now names and links the earlier Action and holds Accept.)
- The default `effective_from` assumes the server and browser clocks roughly agree. A mismatch surfaces as a typed `ACTION_EFFECTIVE_TIME_INVALID`.
- jsdom 1440/390 tests prove structure only; rendered layout rests on the browser run above.

## User-review focus

Walk the eight steps in `.agent/S6-01b-owner-walkthrough.md` at 1440 and at 390. In particular:
- whether the accepted-snapshot vs live-recomputation pairing reads clearly;
- the change page's versions table;
- the honesty wording (no effect, saving or approval);
- the step-2 notice on a newer Finding version: the earlier Action named and linked, the greyed-out Accept and its reason, the separate live reason (reopen round).

## Reopen round (`D-2026-10-15-s601-reopen`, slice review Lows L1-L3)

Brief `.agent/S6-01b-reopen-brief.md`; ruling `AssetOpsV1-gap-planning/.agent/architect-S6-01-reopen-answers.md`; S6-01a reopen merged in at `bb577b0d`. Code commits `59d7fe90`, `ffd5d6c5`, `25b533fc`, `85dd5fa4`, `07b6fa4a` (diff `4603ceaf..07b6fa4a`); handoff `.agent/S6-01b-reopen-handoff.md`. No backend change.

**Delivered (ruling, S6-01b part).**
- `SiteRecommendation.tsx` reads `prior_actions.items` / `prior_action_block` (types in `actionClient.ts`). "Actions on this Finding" lists every Action with its own origin version (link), "(this version)" or "(not the version on this page)" from `origin.is_selected_revision`, application state with failed-attempt count, outcome words and the Action link. It never relabels an earlier Action.
- `state=PRIOR_ACTION_UNRESOLVED` (decided from `state` only, never from the block's presence): the notice "An earlier trial is still open" names and links the blocking Action and its origin version, states its application/outcome and the typed reason. The live recomputation is a separate panel worded "a separate reason ... does not make a new trial acceptable". Accept is a disabled button with `aria-describedby` to the stated reason (links the Action). Disabled `.action-command` is now styled as unavailable.
- A 409 `PRIOR_ACTION_UNRESOLVED` on accept: "Not accepted ... no new Action was recorded", link to the blocking Action, origin version number, code, and the live state separately.
- Contract cases consumed as recorded: `latest_revision_after_apply` (1440), `latest_revision_after_apply_served_clock_stale` (390), `accept_newer_revision_prior_action_unresolved`; plus `accepted_snapshot_live_status` for "(this version)". One derived body (header item 7): the accepted read with a `prior_action_block` added (the coordinator note: a block can accompany `state=ACCEPTED`); the notice stays absent.

**Lows.**
- L1: the walkthrough marker records `db=<name>`. `prepare` refuses an existing DB the marker does not record; `drop` checks the marker before dropping and removes the work folder only for the recorded DB. Docstring corrected. Proven by hand: a foreign `assetops_s601b_foreign` DB was refused by `prepare` and `drop` (still present, removed by hand); `drop --db assetops_s601b_other` refused to remove `var/s601b_owner`.
- L2: `action-list--codes` keeps failure codes on one line. Browser claim: 3 codes, one client rect each, `nowrap`, at 1440 and 390.
- L3: Apply is disabled while the edited effective-time field is empty, with "Enter the effective time to apply."; nothing is sent.

**Checks (code at `07b6fa4a`).**
- `npx.cmd tsc --noEmit`: clean. Targeted: siteAction 35, siteFoundationChange 8 passed.
- Full `npm.cmd test` (on the working tree at `85dd5fa4`, which holds all TSX changes; later commits are CSS and the evidence script only): 64 files, 1522 passed. One earlier targeted run had a single cold-start failure in `siteFoundationChange` (heading not found); passed alone and in two reruns of the pair.
- `npm.cmd run build`: built (at `07b6fa4a`).
- `tools/check-all.ps1`: all 9 guards passed (temporary `.venv` junction, removed).
- Backend: no change in this round; no backend suite run (brief).
- Mutations (committed code, reverted with `git checkout`): Accept not disabled (2 tests fail); every prior Action labelled "this version" (2 fail); 409 branch disabled (1 fails); L3 guard removed (1 fails); `held` from block presence with the block overriding `accepted` (1 fails: the ACCEPTED+block test). A weaker variant (block presence only in `held`) is render-equivalent because `accepted` renders first, so it is not a mutation the test can see.
- Browser: `node tools/s601b-action-evidence.mjs http://localhost:5461 <dir>` over a fresh `prepare` of `assetops_s601b_owner`: 66/66 claims at 1440 and 390, including the notice/link/origin, separate `FOUNDATION_BASIS_STALE` live reason, disabled Accept with `cursor: not-allowed` and stated reason, the Actions list, no sideways scroll (100 elements measured), and the L2 codes. Screenshots viewed (`app-recommendation-latest-desktop/narrow.png`). Servers stopped, DB dropped, `var/s601b_owner` removed.

**Known deviations / risk.** The walkthrough cannot trigger the 409 path (the read already holds Accept); it is covered by the recorded-case test only. The served clock reads `FOUNDATION_BASIS_STALE` where the recorded contract reads AVAILABLE; both are tested. USER_REVIEW_REQUIRED stays true: repeat the owner walkthrough (step 2 is new).
