# S4-01 review packet - candidate generator-support Finding (all phases)

Task: `tasks/S4-01-finding-identity.md` (Status `in_review`). Branch `task/S4-01-finding-identity`.
USER_REVIEW_REQUIRED: true (owner checkpoint, `.agent/S4-01-owner-walkthrough.md`).

| Phase | Packet / review | State |
| --- | --- | --- |
| 1 `I-finding-store`, `D-finding-revisions` | `.agent/S4-01-phase-1-review-packet.md`; review + fix re-review `.agent/S4-01-phase-1-fix-rereview.md` | accepted |
| 2 `I-finding-read` | `.agent/S4-01-phase-2-review-packet.md` (with Fix round 1); `.agent/S4-01-phase-2-fix-rereview.md` | accepted |
| 3 `I-finding-ui` and closeout | this packet; diff `git diff 0f4808b..HEAD` | built, awaits fresh Claude review |

Authority: `D-2026-10-12-finding-episode-and-revisions` and the phase-1, phase-1-fix and phase-2 clarifications
(Q1-Q24), `D-2026-10-09-pre-s3-claim-routes-and-actor`, `D-2026-10-04-plain-language-analysis-views`.
Questions: `.agent/S4-01-questions-1.md` .. `-5.md` (phase 3: Q25-Q30, defaults built).

## Outcome delivered (phase 3)

- The Site Finding detail is at `/sites/{site}/findings/{id}[?revision_id=][&view=analysis][&portion=n]` and
  covers `finding:1,2,4`. `finding:3` "What to do next" is shown as not yet available. The page leads with the
  most limiting state, in order: record only under a closed source (C7), joined into another Finding, earlier
  version, then the lifecycle and whether it is up to date. Possibly avoidable, needed and undetermined minutes
  are separate cards, and fuel/cost is "Not yet available".
- Each block is keyboard-selectable, and its address is kept. "Where to look next" links each Dispatch day with
  the interval revision, the accepted records and related Findings. The page lists versions, with consecutive
  assessment updates grouped by count, each exact version still selectable and none called a new issue. A
  records summary and table follow. Analysis carries the full IDs, codes, assessments, passes, cited records,
  relations and every version.
- Carries addressed:
  - An UNCONFIRMED or REOPENED version after a closure states "not a new issue".
  - A recurrence link says the earlier Finding is not implied open.
  - C7 audit-only leads.
  - Stop bridges carry the sparse-reporting caveat.
  - R1: the gateway and fault-fixture kinds are named in plain words on the page, and the template-runtime basis
    is named in the walkthrough.
- The Dispatch day reads `finding-windows/{day}` and links its non-merged Findings. Its NO_FINDING,
  NOT_DETERMINABLE, FINDING_MATCH_PENDING and NOT_ASSESSED states are named and carry no link.
- Walkthrough tool `tools/s4_finding_walkthrough.py` and evidence tool `tools/s4-finding-evidence.mjs`, described
  under "Files materially changed".

## Files materially changed (phase 3)

New: `frontend/src/sites/{findingClient.ts,findingWords.ts,SiteFinding.tsx}`,
`frontend/src/sites/__tests__/siteFinding.test.tsx`, `tools/s4_finding_walkthrough.py`,
`tools/s4-finding-evidence.mjs`, `.agent/S4-01-owner-walkthrough.md`, `.agent/S4-01-questions-5.md`,
`.agent/S4-01-phase-3-evidence-run.txt`.
Changed: `frontend/src/sites/PerformanceDispatch.tsx` (DayFindings), `SitePerformance.tsx`,
`frontend/src/shell/{SiteAnalyticsFrames.tsx,operatorSiteRoutes.ts}`, `frontend/src/App.tsx`,
`frontend/src/test/settled.ts` ("Loading the Finding."), `frontend/src/ui/primitives.css`,
`performanceDispatch.test.tsx` (+4). No backend change in phase 3.

## Acceptance criteria (task-level)

| Criterion | Status | Evidence |
| --- | --- | --- |
| Persisted Finding/FindingRevision, idempotent matcher, split/merge/recurrence, F01-F08 | Met (phase 1, F07 test-scoped) | phase-1 packet; producer `VERIFY PASSED` (11 Findings / 30 revisions) |
| Exact root/revision read, 401/403/404/409/503, pinned lineage, cutover gate | Met (phase 2; 401/403 via seam) | phase-2 packet and fix round |
| `finding:1,2,4` detail at the canonical route, reload | Met | evidence F01/F04 reload claims; `siteFinding.test.tsx` |
| Concise evidence summary + drill-down to accepted records and Dispatch day | Met | "Records behind this version", Analysis table; Dispatch link carries `day` + interval `revision` |
| Revision selector; BASIS_REFRESHED grouped as a hint with count and exact IDs | Met | test "groups consecutive assessment updates"; F04 version links |
| Honest states: empty/pending/not-determinable/stale/closed/superseded/merged | Met | tests: STALE, FINDING_MATCH_PENDING, FAILED, PENDING, C7, merged, earlier version, 5 refusals; Dispatch day NO_FINDING/NOT_DETERMINABLE/MATCH_PENDING; live F02 Out of date, 10-19, 10-07 |
| UNCONFIRMED after closure not a new issue; recurrence not implying active | Met | tests; live F03 claim |
| No money/recommendation/Action/child lists | Met | typed "Not yet available" on the money card and in "What to do next" / "Where to look next" |
| Plain language; technical detail in its own view | Met | product vocabulary scan (overview and analysis) has 0 violations |
| App vs mock 1440/390, interaction and reload | Met | `tools/s4-finding-evidence.mjs`: 36/36 (`.agent/S4-01-phase-3-evidence-run.txt`) |
| Owner walkthrough from a clean fixture run | Prepared | `.agent/S4-01-owner-walkthrough.md`; owner words recorded by coordinator |
| Cutover proof | Met | walkthrough `prepare`: comparison PASSED (empty-set, zero-inventory statement), "Performance cutover: permitted"; closed gate covered by C7 test and phase-2 409 tests |

## Mock comparison (finding)

| Mock | App | Status |
| --- | --- | --- |
| What happened: claim sentence, segment bar, cards | Same structure, measured minutes, fuel/cost "Not yet available" | supported |
| What limits this conclusion | limitations, joined gaps, stop bridge caveat, recurrence, access basis | supported |
| What to do next | "Not yet available" | withheld (S6) |
| Where to look next (Analysis, Evidence, Alternatives, ACT) | Dispatch days, records, related Findings; history/money/actions unavailable | partly supported |
| Priority / Confidence / Lens chips | State, up-to-date, version, period (Q27) | deliberately not shown |
| Tabs (Evidence, Alternatives, Recommendation, History) | Overview / Analysis + version list | S4-03/S6 |

Screenshots (mock and app, desktop and narrow; open, earlier version, unconfirmed, closed, stale, analysis,
Dispatch link) are in `%LOCALAPPDATA%\AssetOps\s4-finding-walkthrough\evidence`, and are regenerated by the tool.

## Fixture and run IDs

Producer `tools/s4_finding_cases.py run` on `0f4808b`: 0 check failures, `VERIFY PASSED`, 11 Findings / 30
revisions, gateway case 1 Finding (102 cited IDs, all from gateway batches). Walkthrough copy `assetops_s4walk`:
F01 `49281b7c…`, F01-gateway `992ca236…`, F02 `e9be5a71…`, F03 `ce269028…`/`ea49cb45…`, F04 `f7038dd5…`
(v1 `6a00c57e…`), F05 `616634e6…`, F06 `f6ef1821…`/`3757db6d…`/`e9f189dd…`/`ef19def2…`. IDs are per run;
`links` prints the current ones.

## Checks run (phase 3, code `e64d13a`)

- Frontend: `vitest run` 55 files / 1320 tests passed; `tsc --noEmit` clean; `npm run build` built (chunk-size
  warning only). Focused: `siteFinding.test.tsx` 26 passed, `performanceDispatch.test.tsx` 24 passed.
- Backend with Postgres (isolated `assetops_s4p3_test`, dropped afterwards): `1893 passed, 20 warnings in 619.68s`.
  Host: `667 passed, 3 warnings in 396.82s`. Gateway: `164 passed in 48.37s`. Simulator: `265 passed in 1.46s`.
- `tools/check-all.ps1`: `All 6 guards passed.` These are architecture, navigation truthfulness, agent workflow,
  registry, delivery fixtures and the screen ledger (110 screens). `check-agent-workflow.ps1` also passed after
  the closeout edits.
- The product vocabulary scan in the tests (overview and Analysis) found 0 violations, with more than 20 text
  pieces scanned.
- Mutation proof (committed first): disabling the `audit_only` lead fails the C7 test (`1 failed | 25 passed`).
  Reverted with `git checkout --`. No new guard was added.
- Evidence: `node tools/s4-finding-evidence.mjs http://localhost:5340` on `e64d13a`: `36/36 claims passed`.
  Each overflow claim measured a populated page: 5 cards, records > 0, and 66 IDs in Analysis.
- Layout evidence: `tools/layout-evidence.mjs` was not run to completion (Q28). It stopped at the Lab run-setup
  page ("submit still disabled after ten seconds") because the walkthrough API serves no Lab. The shell-wide
  layout claims are unverified for this slice. The Finding and Dispatch-day layout at 1440 and 390 is measured
  above.
- Servers: the walkthrough API (8840), Vite (5340) and Chrome (CDP 9343) were all stopped. The owner's ports were
  not touched. `assetops_s4cases` and `assetops_s4walk` are kept for the reviewer.

## Known deviations

- F07 is test-scoped: there is no reviewed later `dispatch-3.x`, so no live upgraded claim exists.
- 401/403 are produced through the access seam, under development-tenant access (Q16).
- The generic layout tool was not run to completion (Q28). The Finding and Dispatch layout claims are measured
  by the Finding evidence tool instead.
- The fixture has no fully assessed no-Finding day, so NO_FINDING is proven in tests only (phase-2 Postgres test
  and the Dispatch day test).
- Q25: the S3 `unavailable.finding` text remains. Q27: no priority or confidence chips.

## Residual risk

- Carries C5 (one-hop canonical), C6/C9 (read and pass cost, for S4-04) and C8 (recurrence record only on the
  opening revision) remain open.
- `?portion=` is an index (Q30).
- The record table shows short IDs in Overview; the full IDs are in Analysis.

## User-review focus

Fresh Claude review of phase 3, then the owner checkpoint walkthrough. In the walkthrough:
- check the wording of the Not confirmed, No longer supported and recurrence states;
- check what is withheld (money, Action, child lists);
- check the gateway case labelling and the F07 test-scoped limit.

## Fix round (3) - phase 3 review B1-B4, C1-C4, C6 (C5 left)

Code `60aae53` plus a follow-up commit (see git log). Against `.agent/S4-01-phase-3-review.md`.

- **B1** Not confirmed no longer assumes missing records. The Finding read now adds a read-time, non-stored
  `revision.indeterminate_reasons` (the cited interval assessments' undecided portions: reasons and what is
  undecided; `finding_read.py`, none when the source is closed). The screen says records are missing only when a
  limitation or the assessment's own "missing or conflicting" reason says so; otherwise it states the assessment's
  reasons (Foundation ids stripped). Live F05 v2 now reads "No records are missing. It could not decide under the
  settings now in force: ... reserve 20.0 %; possibly within the configured minimum runtime (120 min from the
  first ON report); Candidate withheld...". Card note "Could not be decided either way"; headline "cannot decide
  whether any of that time was possibly avoidable" (UNCONFIRMED only). Note: a portion's `missing` field can name
  a setting (minimum runtime), so it is not treated as a record gap. Guide step 4 updated.
- **B2** Headline reads "The generator ran between X and Y, with one short stop recorded" when a stop is bridged;
  "stayed on" only without stops.
- **B3** `links` prints every version of each multi-version Finding and the days 10-06, 10-19, 10-07 and 10-25,
  with 10-25 labelled NOT_ASSESSED (no fully assessed no-Finding day exists in the fixture); guide step 8 matches.
- **B4** `CaseRunner.__init__(model=None)` resolves `dispatch_v3` inside. Default
  `pytest backend/tests -q` with no test DB URL: 1766 passed, 127 skipped (collects cleanly). The other S4
  Postgres file only reads `dispatch_v3` inside guarded code.
- **C1** `\.` restored in `settled.ts`. **C2** "are cited by this version" when no minutes are counted.
  **C3** heading "Open · out of date" (lifecycle label plus attention currentness). **C4** the currentness
  paragraph is omitted on a non-latest version (the lead already says a later version replaces it); "This version"
  instead of "The latest assessment" there. **C6** evidence text regenerated into
  `%LOCALAPPDATA%\AssetOps\s4-finding-walkthrough\evidence` (36/36), matching packet and guide.
- Tests: 4 new vitest cases (B1 x2, B2, C2/C3/C4); all four fail on the old `SiteFinding.tsx`/`findingWords.ts`
  and pass now. C1 is a helper regex with no behaviour test.
- Checks: vitest 55 files / 1324 passed; `tsc` clean; build ok; default no-DB pytest 1766 passed / 127 skipped;
  S4 Postgres files (store, read, api; isolated DB dropped) 25 passed; `tools/check-all.ps1` all 6 guards passed;
  walkthrough `prepare` (comparison PASSED, cutover permitted, 10-09 staged PENDING) + `links` + `serve`
  8840/5340 + `s4-finding-evidence.mjs`: 36/36 claims passed (`.agent/S4-01-phase-3-evidence-run.txt`). Servers
  stopped, test DB dropped; owner ports and `var/` untouched.
- Open: C5 (first-day Dispatch pin) carried; the new backend read field has no dedicated backend test (covered by
  the live run and the Postgres read tests passing unchanged); layout evidence still not run (Q28).
