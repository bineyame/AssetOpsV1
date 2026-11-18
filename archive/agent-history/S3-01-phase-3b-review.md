# S3-01 phase 3b review (fresh Claude reviewer)

Produced by a fresh Claude reviewer (Opus), independent of the Implementer. Diff reviewed: `cdc24f7..4426a17` on `task/S3-01-dispatch-assessment` (build `b04b904`..`4f56b89`, closeout `4426a17`). Nothing was fixed, merged or committed.

## Verdict

**Accept with findings fixed on the branch.** B1 and B2 below must be fixed before the owner checkpoint. Both are small UI and wording fixes. The fix also needs a correction to the walkthrough guide and to Q19. **S3-01 is not ready for the owner checkpoint until that fix round is reviewed.** Everything else is sound: R2, R3, the empty-set wording, the status states, revision pinning and the gating of fuel, money and Finding. No regression of phases 1, 2 or 3a was found.

## Checks I ran

| Check | Result |
| --- | --- |
| `npx.cmd tsc --noEmit -p .` (frontend) | exit 0 |
| `pytest backend/tests/test_s3_performance_cutover.py -q` | 27 passed |
| `npm.cmd test -- --run src/sites/__tests__/performanceDispatch.test.tsx` | 12 passed. It ran in this session; the expected sandbox failure did not occur. |
| `tools/check-architecture.ps1`, `tools/check-agent-workflow.ps1` | both passed |
| `tools/s3_dispatch_walkthrough.py prepare` | OK: tree from `4426a17`, `assetops_s3walk` recreated, comparison PASSED (empty set), cutover permitted, FAILED 10-07 and PENDING 10-05 staged |
| `serve` on 8820, then direct API reads, then stopped | Cutover permitted, with `comparison` present. 10-01 CURRENT INDETERMINATE; 10-02 CURRENT CANDIDATE; 10-09 CURRENT NECESSARY; 10-05 STALE (AMBIGUOUS_COHORT); 10-04 STALE; 10-07 FAILED; 10-06 FAILED and also outstanding; 2027-01-01 UNASSESSED. These match the guide, except for the demo notes (B1). |

Not re-run (the packet's numbers are unverified by me):
- the full backend Postgres suite, host, gateway and simulator suites;
- the full vitest suite;
- `npm run build`;
- `tools/s3-dispatch-evidence.mjs`.

I did not start the frontend dev server, so I judged the UI from the code and the committed screenshots. Port 8820 is free again. `assetops_s3walk` remains as the owner walkthrough database; `prepare` recreates it. I created no test database.

## Findings

### B1 (BLOCK, medium) Demonstration-data note hidden when a day's result rests on the labelled fault-fixture records

- **Where:**
  - `frontend/src/sites/PerformanceDispatch.tsx:306-308` and `:673`. Notes render only inside `EvidencePanel`, and that panel only appears when a revision detail is loaded. Window `demo_annotations` are shown only as a fallback there.
  - `.agent/S3-01-owner-walkthrough.md`, "The demonstration-data notes do not appear here".
  - `.agent/S3-01-questions-5.md` Q19.
- **What:** on walkthrough data, the 10-07 window read has `cohort_status: SELECTED_UNIQUE`, and its 2 accepted records are exactly the `out-of-order-fault-fixture` records. The read carries a `DEMO_MANIFEST_FAULT_FIXTURE` annotation, and 10-06 carries one too. 10-07 has no interval, so nothing can be selected and the note never renders. The owner sees "2 accepted records behind this day's result" and "Some records arrived in a different order", with no sign that these are labelled demonstration fault records.
- **Why it matters:**
  - Phase 3 requires the drill-down to identify any demo-fixture annotation as manifest provenance, and the default must not silently treat the fixture epoch as ordinary source truth (`D-2026-10-11-s3-phase-2-selection-and-read`).
  - The guide and Q19 state the opposite of what the data shows ("fault-fixture days are AMBIGUOUS and carry no run evidence"). 10-07 is not ambiguous, and the staged failure sits on that very day.
- **Fix:**
  - Render `read.demo_annotations` on the Overview whenever it is non-empty, independent of a selection, using the existing `DemoNotes` apart from provenance.
  - Add a test for a window with annotations and no intervals.
  - Correct the guide's limit, Q19 and the packet's known deviations.

### B2 (BLOCK, low-medium, cheap) "Battery reserve setting: Not set up" contradicts the result on every day

- **Where:** `frontend/src/sites/dispatchWords.ts:99` (`battery_reserve: "Battery reserve setting"`), shown by the coverage table at `PerformanceDispatch.tsx:630`.
- **What:**
  - `battery_reserve` is an optional telemetry channel role, unbound on Kobo.
  - The reserve the assessment uses is the Foundation control `battery_reserve_soc`: 30 %, with its Foundation revision shown in Analysis.
  - On 10-02 the Selected period says "Battery at its reserve level", while the table directly below says "Battery reserve setting: Not set up". This is visible in `app-dispatch-selected-desktop.png`.
- **Why it matters:** a non-technical owner reads this as the reserve not being configured, which undercuts every Needed result.
- **Fix:** relabel the channel, for example "Reported battery reserve (the reserve used comes from site settings)", or footnote optional roles the assessment does not use.

### Carries (low; fold into the same round where cheap)

- **C1. Unmapped codes fall back to raw or vague text.** `dispatchWords.ts:115-119`
  - `CAPABILITY_SHORTFALL` (the physical-Necessary reason in `dispatch_v3.py:290`) has no entry. It renders as "capability shortfall."
  - The mapped `LOAD_ABOVE_CAPABILITY` is never emitted, so that entry is dead.
  - `NO_COHORT` has no limitation words and reads "Another limitation is recorded; see Analysis".
  - Fix: map both codes and drop the dead entry. `analytics/plain.py:75` already has wording.
- **C2. Analytic and implementation text reaches the default reading.**
  - `PerformanceDispatch.tsx:577-579` prints `dispatch_v3` `missing` strings verbatim in the Overview's selected block. Examples: "not bound in the selected role set (missing role)", "(cohort limit)", "Candidate only when both ends are Candidate".
  - The records table shows `GOOD` and raw ISO `accepted_at`.
  - The closed-cutover panel (`:198-214`, `ComparisonPanel` `:777-826`) shows class codes (`MATCH`, `INTENTIONAL_DELTA`), `JSON.stringify(lineage_breaks)` and the backend reason, which can contain a Python dict. On the closed path that is the default reading.
  - This conflicts with `D-2026-10-04-plain-language-analysis-views`. Not seen in the walkthrough, because the gate is open there.
- **C3. R2 recheck re-reads the selection once per revision.** `analytics/performance_comparison.py:213`: `selected_revision_ids()` is called once per classified revision inside the comprehension. That is a full `selected_intervals` scan N times on every gated read. Correct but wasteful; evaluate it once. No effect on the empty set.
- **C4. Cutover route reads the report twice.** `performance_api.py:78-79` with `main.py` `performance_gate`/`performance_report`: the gate and the summary each call `performance_reports.latest`. A report written in between makes the displayed summary differ from the one that gated. Pass the one report through instead.
- **C5. Coverage wording can mislead.**
  - On 10-05 (AMBIGUOUS) the coverage says "0 accepted records behind this day's result" while records exist; no series was chosen. That reads as "nothing received".
  - On 10-01, MISSING_ROLE says "not set up for the site", while coverage shows "Set up". The binding covers only part of the day.
  - Fix: name the no-series case, and say "for part of the day".
- **C6. Walkthrough tool and guide gaps.**
  - `tools/s3_dispatch_walkthrough.py:131`: step 3 runs with `check=False`, so a failed comparison still prints "Prepared".
  - The guide gives no prerequisites: local Postgres on 55432, the `assetops_s3cases` producer DB and its manifest under `%LOCALAPPDATA%\AssetOps\s3-dispatch-cases`, and `var/sites/kobo-001.yaml`. It also does not say what to do on failure.
  - The guide is otherwise accurate: ports, links, the meaning of each state, recover, and its limits.
- **C7. Day-total cards are not marked stale.** On a STALE or FAILED day that keeps intervals, the total cards are not marked; only the status line above is. Not reachable on walkthrough data.
- **Note (pre-3b analytic, no finding).** In Analysis, a mixed-end Needed block such as 10-02 05:00-05:15 lists both endpoints' reasons, including "PV available alone covers load…". It is confusing but it is the reviewed analytic output.

## R2, R3 and other focus points

- **R2.** Met. The gate refuses when a classified MATCH or INTENTIONAL_DELTA revision is no longer selected, and fails closed when the selection reader is absent. Both live wirings, `main.py` and the CLI, pass `selected_intervals`. The empty set is skipped by design, which is safe because nothing is classified. See C3 and C4.
- **R3.** Met. File-store and report errors give a 503 with a closed body (`read: CLOSED`, `permitted: false`) on the cutover route, and a 503 on gated reads. Tested.
- **Empty set never called a match.**
  - In the default reading: "there were none … This is not a match".
  - In Analysis: "PASSED" followed by the zero-inventory statement. Acceptable there, though "PASSED" alone could be softened.
- **Status and pinning.**
  - All five states have honest words. UNASSESSED shows no zero.
  - A revision from another day is labelled "not the current one". Older-rule labelling is by test only (Q18).
  - The block index is stable because revisions are immutable.
  - Fuel, money and Finding are typed "Not yet available".

## Questions Q17-Q22

- **Q17** (open on today UTC): safe and fail-closed, not unsafe for the demo. The guide's links all carry `?day=`, and the guide says that a bare Performance tab reads "Not assessed". A list of assessed days belongs to later work.
- **Q19:** its premise is wrong (see B1); answer it after the fix.
- **Q18, Q20, Q22:** the defaults are fine.
- **Q21:** prefer committing only the stable part of the manifest (case labels, ceilings), because evidence IDs change with every producer run.

## Owner checkpoint readiness

Not yet. Run a small fix round on the branch for B1 and B2. C1, C5 and C6 are cheap enough to include. Correct the guide and Q19, then have a fresh reviewer re-review. After that, S3-01 is ready for the owner walkthrough.
