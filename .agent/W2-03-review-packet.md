# W2-03 review packet - cold assessment, episodes, Findings and the four cold screens

Task `tasks/W2-03-cold-assessment.md` (USER_REVIEW_REQUIRED: true - fresh independent slice review, then the owner's
later W2 walkthrough). Branch `task/W2-03-cold-assessment`, base main `e74309db`. Binding spec
`.agent/W2-03-build-spec.md` (incl. `D-2026-10-18-w2-03-answers` Q1-Q11 and the commit-4 freshness amendment).
Reviewer diff: `git diff e74309db..HEAD -- ':!.agent'`. Handoff with commit 1-4 anchors: `.agent/W2-03-phase-1-handoff.md`.

## Outcome delivered

The six registered W2-02 cold replays enter through authenticated Batch V2 intake, enqueue `cold_chain` work, and the
`ColdAssessmentWorker` projects immutable assessment revisions, cold episodes and evidence-linked cold Findings in one
transaction. Four selected read routes serve them with typed currentness, and a COLDCHAIN Site renders `temperature`,
`coldbackup`, `cold-finding` and `cold-finding-excursion` in their exact v69 panel slots, with empty, pending and
refused states keeping every panel and naming the gap. No spoilage, product-loss, failed-part or Incident claim.

## Commits

| Commit | What |
|---|---|
| 7667ad97, 4d704f76 | (1) `0022`, Finding `domain`, rule-8 cold policy + probes, migration tests |
| 0089cdb8 | (2) pure rules `analytics/cold.py`, pinned vectors + host drift check |
| 6ddb6fad | Q1: fuel consequence trigger only for `domain='mini_grid'` |
| 07d3c0d1 | (3) worker, episodes, cold Findings, intake enqueue, late recompute |
| b2999043, a78452dd | (4) selected reads, router, read tests (SQL in the store adapter) |
| 4fb94996, dd1e8cdc, 249a99e6, bb312cb9, 2cd0d0ee | (5) client, four views, frame switches, `coldRoutes.test.tsx`, fidelity and guard fixes |

## Files materially changed (commit 5)

- `frontend/src/sites/coldAssessmentClient.ts` (four reads, window query helpers), `coldAssessmentWords.ts` (every server code to plain words), `coldFormat.ts`, `ColdAssessmentViews.tsx` (`ColdPerformanceFrame`, `ColdFindingFrame`), `w2-cold-assessment.css`.
- `frontend/src/sites/assessmentGraphics.tsx`: `ColdTemperatureChart` (policy band, sampled points, line broken across gaps over 10 min, shaded gaps, excursion span, legend).
- `frontend/src/shell/SiteAnalyticsFrames.tsx`: COLDCHAIN switch in `SitePerformanceFrame` (no subtab or `temperature` -> temperature, `backup` -> coldbackup) and `SiteFindingFrame` (root Finding route; kind EXCURSION -> excursion view, else start view); `coldLinks` keeps the selected window.
- `frontend/src/App.tsx` (`coldAssessment` prop), `ui/V69Layout.tsx` (two mock subtitles), `test/settled.ts` (loading sentence).
- `frontend/src/sites/__tests__/coldRoutes.test.tsx` (19 tests).

## Acceptance criteria

| Criterion | Status |
|---|---|
| Six W2-02 manifests through intake; spec outcomes per case | Met (commit 3): `test_w203_cold_replay_postgres.py` 12 pass |
| Late recompute keeps history; same basis idempotent; split; atomic retry; event-ID conflict not support | Met (commit 3) |
| Migration, scoped FKs, append-only, downgrade refusal; fuel trigger mini-grid only | Met (commits 1, Q1) |
| Reads: window limit/paging, typed errors, UNKNOWN 200, tenant/source gate, pending/historical | Met (commit 4): `test_w203_cold_reads_postgres.py` 5 pass |
| Four routes in exact v69 slots, titles from the JSON at test time, stocked/empty/refused + planted-panel failure | Met: `coldRoutes.test.tsx` (stocked x4, empty x4, refused x3 + excursion companion refusal; planted panel x4) |
| Temperature: points/policy/bounds/gaps; Finding link only if persisted | Met (tests: 13 points, gap breaks line, link present/absent) |
| Backup: ordered steps, observed/missing/contradictory, evidence links | Met (step order test, contradiction sentence) |
| Finding details: bounded conclusion, context, revision/evidence/Analysis links, in-panel `No recorded next step` | Met |
| 1440/390 app+mock captures, stocked and empty/refused | Met: `.agent/W2-03-evidence/` 108/108 claims (see Captures) |
| Rule 8, guards, full suites | See Checks |

## Checks

Final revision `264dfe9a` (tree clean; no code changed in the proof run). Real Postgres 127.0.0.1:55432, keep-awake running.

| Check | Command | Result |
|---|---|---|
| Full backend | `pytest backend/tests -n 2 --dist loadfile --no-loadscope-reorder -q --junitxml` (private DB `assetops_w203_test`, `var/sites` copied then removed) | 2752 passed, 25.0 min (cap 75); JUnit cases=2752 skipped=0 failed=0 |
| Host suite | `pytest host/tests -q --junitxml` | 708 passed, 10.0 min; JUnit cases=708 skipped=0 failed=0 |
| Frontend | `npm.cmd test` | 85 files, 2175 passed |
| Guards | `tools/check-all.ps1 -Python <plan2 venv>` | All 10 guards passed (screen ledger 110 screens; missing-claim scan 39 tagged uses) |
| Rule-8 probes | `python tools/writer_guard_probes.py --seam` | exit 0, every cold probe CAUGHT, controls ALLOWED, "tree restored" (tail of output kept) |
| Captures | `tools/w1-fidelity-evidence.mjs`, `W1_REVISION=264dfe9a` | 108/108 claims (see Captures) |

Not re-run in this pass: typecheck/production build (covered by the vitest run and check-all only); no layout-evidence.mjs run beyond the fidelity captures.

## Captures

Recaptured at the final revision: `node tools/w1-fidelity-evidence.mjs .agent/W2-03-evidence ...` (CDP 9712,
`W1_REVISION=264dfe9a`): API 9701 on private `assetops_w203cap_test`, seeded by the real path (backup-failed W2-02
replay through intake + `ColdAssessmentWorker`, via the replay test helpers; throwaway seed test, not committed), web
6101; DB dropped and servers stopped afterwards. Site `COLD-LAB-001`; default selection `[2026-10-06T19:00Z, 20:05Z)`;
Findings `...0176` (excursion) and `...017c` (start). Nine pairs x 1440/390: temperature, coldbackup x stocked / empty
(`?from=2026-10-05T19:00:00Z&to=2026-10-05T20:05:00Z`, 200 UNKNOWN) / refused (`from>to`, 422); cold-finding stocked
(`...017c`) / refused (unknown ID, 404); cold-finding-excursion stocked (`...0176`). 108/108 claims (rendered, same
panel count, no horizontal overflow). Mock hashes and image paths are in `evidence.json`; pairs in `index.html`.
The earlier captures at `bb312cb9` were replaced, so tab removal and the chart module move are included.

### App-vs-mock panel heights (1440, stocked; measured at `bb312cb9`)

Heights were not re-measured after the recapture: the later commits only moved the chart module, shortened one gap sentence and removed the in-page tab entries (above the panels). The recapture still passes the same-panel-count and no-overflow claims.

| Screen | Panel | App px | Mock px | Ratio | Reason when > 1.3 |
|---|---|---|---|---|---|
| temperature | Temperature with operating context | 463 | 442 | 1.05 | |
| temperature | Excursion context | 463 | 442 | 1.05 | |
| temperature | Claim boundary | 225 | 120 | 1.88 | spec requires coverage, exclusions, source gate and limits here (mock has one paragraph); one disclosure |
| coldbackup | What the chain shows | 148 | 153 | 0.97 | |
| coldbackup | Reconstructed event chain | 170 | 208 | 0.82 | |
| coldbackup | Backup event chains | 188 | 194 | 0.97 | |
| coldbackup | Evidence by causal step | 554 | 332 | 1.67 | one row per required step (eight ordered steps + temperature) vs the mock's five grouped rows |
| cold-finding | Bounded conclusion | 217 | 209 | 1.04 | |
| cold-finding | Operational context | 348 | 253 | 1.38 | spec adds missing steps, revision history and evidence/Analysis links to the mock's chain |
| cold-finding | Recommended next step | 348 | 253 | 1.38 | pair height (shares the row) |
| cold-finding-excursion | Bounded conclusion | 248 | 209 | 1.19 | |
| cold-finding-excursion | Temperature | 487 | 333 | 1.46 | spec adds observed peak, degree-minute bounds and exact evidence links under the chart |
| cold-finding-excursion | Recommended next step | 487 | 333 | 1.46 | pair height |

### Self-check (brief's recurring-defect list)

- State line once: currentness/result only in the status strip (removed from Claim boundary). One strip per screen (test).
- One disclosure per panel (test asserts <= 1 `details[data-exact-references]` per panel).
- No leftover labels/h3s: guard passes (no stray sections); no extra cards beyond the mock's.
- No raw IDs/enums/backend text: every code through `coldAssessmentWords.ts`; server limitation sentences pass `plainLimitation` (step codes in "Not observed: TRANSFER..." become words); IDs only in "How this was worked out". W1 vocabulary scan passes except the four mandated strings (deviation 18).
- No contradictions: an observed compressor `OFF` no longer reads "Cooling resumed"; adverse BUS/GENERATOR/COMPRESSOR states say "recorded off/unpowered/failed" instead of the positive "establishes" text.
- Every mock row/column/chip kept: temperature cards (4) and seven Excursion-context rows (unknowns "Not recorded"); backup cards (4, Manual recovery "Not recorded"), eight table columns, four evidence columns.
- Mock tables/lists kept; material limits shown (gaps, missing steps, contradictions, no spoilage).
- 390: no horizontal overflow (18/18 captures); the chart scales down (its gaps also listed as text below it), step sequence and evidence links stay reachable as the timeline/table (table scrolls in its own region).
- Heights: table above; >1.3x panels carry their reason.

## Known deviations and interpretations

1. Work window: job window = 5-min-aligned bracket of its accepted source times merged with selected cold windows within the 10-min bridge; ledger coalesces pending cold jobs across the same bridge (canonical replay yields exactly `[19:00,20:05)`). Architect confirmation requested.
2. Clock attestation: replay tests record the SYSTEM attester's labelled simulated attestation per lab source (epoch `cold-<case>`) before upload; not an accepted-row insert.
3. L3 `split_from_finding_id`: an ad hoc reading enters only outside the registered publication, so the gate is MIXED and no new Finding opens (asserted); the positive link is proven with a test-only `classify` double.
4. A Finding whose episode no longer warrants one (still supported, claim limited) gets `SUPPORT_CHANGED`/`BASIS_REFRESHED` with lifecycle `UNCONFIRMED` (spec silent).
5. `test_w200_source_events_postgres.py` "no dispatch job" now excludes `cold_chain`.
6. W2-02 excursion replay's start chain is `OBSERVED_FAILURE` (opens a start Finding too); not asserted (spec silent).
7. Placement: SQL `ColdReadService` sits read-only at the end of `postgres_assessment_store.py` (rule-8 driver allowlist); pure rules stay in `cold_reads.py`. Guard not loosened.
8. Default window: neither `from` nor `to` -> latest selected cold window at the cutoff; only one -> 422.
9. Selection: latest `analytic_run_selection.seq` per analytic covering the request with run cutoff <= `known_at`; points filtered to the request; freshness at the selected window's `to`.
10. Pending: PENDING/LEASED/FAILED cold job overlapping the window widened by the 10-min bridge.
11. 403 source disclosure: injectable `disclosure(code, tenant, site)` seam, default allow (no production policy yet); MIXED class is shown in provenance, not 403. The UI's 403 page refusal is test-only for that reason.
12. 409 only for the cursor-basis case (a selection always joins a settled revision).
13. Findings envelope `basis_sha256` = sha256_json of the two analytic bases; detail uses its revision basis; `as_of` rules as in the handoff.
14. Links: evidence `href` keys on `message_id`; Analysis `/api/sites/{code}/assessments/{id}`. The UI links exact accepted IDs to the existing Evidence Analysis record route (`?view=analysis&record=`) and the assessment revision to `?view=analysis&assessment=`; whether that existing view renders a cold record/revision was not verified (residual risk).
15. Missing-probe replay: excursion episode (claim UNKNOWN) without an exposure Finding (asserted).
16. Unbuilt in-page entries: the mock's Cooling subtab and the cold Finding Recommendation tab are not rendered. The navigation guard fixes the unbuilt-entry inventory (`D-2026-10-17-f5-subtabs-and-contact`) and "a new unbuilt entry is a ruling"; first attempt failed the guard and was withdrawn. Ruling requested.
17. Mock row "Loading / batch" renders as "Stock loading / batch": the capture tool treats any "Loading" text as a page still loading (W2-01 deviation 6 precedent).
18. Vocabulary: the v69 title "Claim boundary", the mock columns "Power to load"/"Load response" and the spec-required "Registered simulation" provenance are on the W1 list (`claim`, `load`, `simulation`). The spec binds titles to the JSON and columns to the mock, so they are kept and filtered by exact text in the test's scan only; an approved title change is the Architect's (as for `asset:3`). Ruling requested.
19. Refused cold Finding (404 etc.): the kind is unknown, so the page renders the page refusal plus the `cold-finding` slots with gaps.
20. "Manual recovery" card: no operational-log source exists, so it reads "Not recorded"; no Incident link is drawn (no Incident record).
21. Chart y-range is the data/policy range plus 1 °C; the mock's illustration axis (0-10 °C) is not copied.

## Residual risk

- Analysis/record links into the existing Evidence Analysis view for cold IDs (deviation 14).
- The 390 chart is small (text-level labels); the gap list and timeline carry the same facts.
- The height table predates the final recapture (see above); panel counts and overflow are re-measured.

## User-review focus

Walk COLD-LAB-001 Performance/Temperature and Backup, then both cold Findings: bounded wording, the gap states, the
missing transfer step, and that no product/spoilage claim appears. Rulings needed: deviations 1, 16, 18.

## Handoff choices recorded (items 1-15 of the phase-1 handoff are deviations 1-15 above)

Added in commit 5: deviations 16-21 above. Specifically, the mock's Cooling subtab and the cold Finding Recommendation tab
are withheld (the unbuilt-entry guard needs a ruling), and the mock row "Loading / batch" renders "Stock loading / batch"
(capture tool treats "Loading" as a loading page). Architect rulings requested: 1, 16, 18.

## Fix round (review `.agent/W2-03-review.md`: RETURN, 2 Medium, 5 Low; q3 rulings for deviations 16 and 18)

Commit `8facadf7` (code and tests) plus the recapture commit. Deviations 16 and 18 are now **applied as ruled**; their
"pending" status above is superseded.

| Item | Change | Proof |
|---|---|---|
| M1 | `establishes(step, chain)` says "after recovery" for the probe only when `coolingRunning(chain)`; otherwise "Chamber temperature after the compressor record". | `coldRoutes.test.tsx`: backup-failed has no "after recovery"; a chain with a RUNNING compressor does. |
| M2 | `attest(built, unattested=, until=)`. New `test_unattested_probe_source_excluded_through_intake[no-attestation, attested-until-19:25]`: probe readings arrive through real intake; every unattested probe reading links `EXCLUDED/CLOCK_UNATTESTED`, none `SUPPORT`, and `known_points` equals the attested count (< 13). | Passes on Postgres (52 s with 3 neighbours). |
| M2 unbound | **Not drivable through intake.** S2 refuses a record outside its binding period at acceptance (`evidence/ledger.py:375` `_outside_periods` -> `OUTSIDE_BINDING_PERIOD`), so no accepted row can carry that state; the adapter's `in_force` check is defence in depth. Stays a pure-rule test (`test_suspect_clock_skew_unbound_excluded`). Recorded as a deviation. | n/a |
| Dev 16 | Cooling (Temperature / Cooling / Backup) and Recommendation (Overview / Recommendation) render through `UnavailableTab` as "X · Not available yet" text: no link, tab stop, handler or role. Guard `Get-InPageUnavailableEntryFailures` expected list extended by exactly `Cooling` and `Recommendation`; two new fixtures (drop either) prove it can fail. | `coldRoutes` q3 tests (order, aria-label, no focusable/role/disabled, no cooling/recommendation href, selected live tab); `navigation-truthfulness` passes with new fixtures. |
| Dev 18 | Panel title "How each limit is set" (one `APPROVED_TITLE_CHANGES` entry `temperature:3`); columns "Power to compressor" / "Compressor response"; source label "Generated test data" with adjacent "From a registered test run; not readings from physical equipment." Source class stays in the labelled detail. | `coldRoutes`: title, all eight column labels in order, label plus adjacent sentence, no "Claim boundary" / "Registered simulation". The vocabulary-scan allowance is now only that one ruled sentence verbatim (its word "run" is on the W1 list); the old four-word allowance is gone. |
| L3 | "Above policy · At least 45 min". | asserted |
| L4 | Result chip: red (`cold-result--danger`) for OBSERVED_FAILURE, amber for CONTRADICTORY, neutral otherwise (local CSS around the neutral Badge; shared Badge untouched). | asserted on class |
| L5 | Late-reading replay asserts 19:25 present, HIGH (> 4.0) and SUPPORT, 19:20 absent. | replay test |
| L6 | `test_low_excursion_peak_is_minimum` (peak 0.9, durations 20 and 30, BOUNDED). | passes |
| L7 | `cold_reads.py` docstring names `postgres_assessment_store.py:ColdReadService`. | n/a |

Captures: all nine pairs recaptured at 1440 and 390 (`W1_REVISION` = fix revision), 108/108 claims, same API/web ports 9701/6101,
CDP 9712, on a private test DB seeded by the real backup-failed replay (throwaway seed test, deleted; DB dropped, servers stopped).
Viewed: `coldbackup-stocked` 1440 (tab row, plain columns, red chip, probe row) and `cold-finding-stocked` 390 (Recommendation text-only entry).
The height table above is not re-measured; the changes add one tab entry above the panels and relabel text only.

Checks: `npx.cmd tsc --noEmit` exit 0; `coldRoutes` 26 passed; `test_w203_cold_rules.py` 8 passed; `check-all` 10/10 guards;
full `npm.cmd test` and the w203 replay+rules rerun results below.

Final runs: full `npm.cmd test` 85 files / 2182 passed (159 s); `pytest tests/test_w203_cold_replay_postgres.py tests/test_w203_cold_rules.py` on real Postgres 22 passed, 0 skipped (344 s). Backend production code changed only in a docstring (`cold_reads.py`), so no full backend suite was rerun.
