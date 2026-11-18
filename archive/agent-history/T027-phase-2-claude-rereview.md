# T027 phase 2 fix round: re-review

Reviewer: Claude, a fresh instance independent of the Implementer and of the first phase 2
reviewer. Reviewer is Claude under `.ai/ROLE_CONFIG.md` until the Codex reset 2026-10-03
21:23, so Codex may revisit any judgement here retrospectively. Range `6035bcb..95c6650`
(01b1326, a71dc8c, 2fafa71, 1159420, 95c6650), branch
`task/T027-commit-ingestion-and-site-overview`.

## Verdict: accept with findings fixed on the branch

F1 to F5 are closed, not just touched. One new must-fix, R1: the same class of false
statement as F2, on the Overview page itself, which both the first review and the fix round
missed. It is a one-sentence wording change plus a test. R2 and R3 are low and optional.

## Findings from review 1

| Finding | Status | Evidence checked |
| --- | --- | --- |
| F1 coverage from usable records | Resolved | `overview.py` `_Window.usable(key)` returns exactly the set the metrics read: `_intervals` (now requiring a positive span via `_spanned`) for `INTERVAL_SIGNALS` (three feeder meters, generator power, PV), `_instants` otherwise. `status()` adds `NO_INTERVAL_SPAN` and `OVERLAPPING_ONLY`. `uncovered()` returns named reasons, and `unavailable_because` is those reasons joined. Gap entries carry `reason`, and `DomainCard` renders `gap.reason` verbatim. A span-less PV signal now has `value None`, `window_note None` and no evidence, so "0.0 kWh over 0.00 h" cannot be produced. An overlap-only mill feeder makes `served-energy` unavailable, naming `mill-meter/active-power`, while the residential feeder keeps its 2.0. **Non-vacuity, run by me:** a scratch script outside the repo monkeypatched `_Window.usable` back to the old any-GOOD rule and ran the three new tests. All three failed. No product file was edited. |
| F2 Foundation false facts | Resolved | `SiteConfiguration.tsx:432-446`: Evidence availability and Source health are gone, and Integration readiness is kept. The new sentence says the tab is configuration, not evidence, and points to the Evidence tab for accepted records, source health and coverage. That is true: Evidence is a `capability: true` tab on every operator Site (`operatorSiteTabs.tsx:80`), and `SiteEvidence.tsx` renders Source health and coverage. `SiteConfiguration` is used only by `SiteFoundationFrame`. The constants and view fields are removed; a code comment records why. |
| F3 strip wording | Resolved | `ObjectiveStrip` renders the metric label "Served energy, measured intervals" and then `MetricValue`, which shows `window_note`. The backend produces "2.67 h of the 8.00 h window measured", or "X to Y h of the ..." when the feeders differ. The screen test asserts both strings. Packet User-review focus point 6 now quotes the screen order (label, value, note, then the feeder basis). The basis quote is partial: the basis begins "Sum of the three feeder meters over their measured intervals (". This is acceptable. |
| F4 response shape | Resolved | `isSiteOverview` now checks metric `at`, `window_note`, `unavailable_because` and evidence items; card and objective assessment; coverage counts; gaps with `reason`; the three statements; timeline `basis`; and each point (interval or instant form). `usable` and `last_source_time` are not checked, and neither is rendered. The screen test runs the real client over a stubbed `fetch` and gets `unavailable` for a missing `unavailable_because`. The existing test shows `unavailable` renders "Overview unavailable". |
| F5 count naming | Resolved | `source_gateway_pairs_in_window`; strip text "source and gateway pair(s)"; API doc in `evidence_api.py` updated. No stale `sources_in_window` remains (grep). |

## New findings

### R1 (Medium, must fix, `D-2026-09-22-expiry-follows-the-condition`)

**Where:** `frontend/src/sites/SiteDetails.tsx:409-414` (`SiteQuickActions`, rendered
unconditionally at `:340`). This is the operator Site Overview page.

**What is wrong.** Below the Overview cards, every operator Site page shows a disabled
"View Live Data" action with the reason:

> "No evidence has been accepted for this site. Live data arrives with the ingestion and
> evidence steps, which are later than configuring a site."

T027 falsifies this. On SITET26 the same page shows "329 accepted records" in the strip and
cards linked to accepted records. The sentence is the F2 statement in a different panel.
The fix round's guard does not catch it: the screen test asserts
`not.toMatch(/no accepted evidence/i)`, and "No evidence has been accepted" does not match
that pattern.

**Why it matters.**
- The decision puts a falsified claim in the slice that falsifies it.
- It is on the owner's demo path, on the very page under review.
- It directly contradicts the strip above it.

**Fix.** Reword the reason so it states what is true for every Site. For example: "Live data
is not a capability of this build. Accepted evidence for this site is on the Evidence tab."
The action stays disabled. Then:
- update `siteDetail.test.tsx` and `siteDetailScreen.test.tsx` to match;
- widen the Overview screen test's pattern to also reject `/no evidence has been accepted for this site/i`
  on a populated Site. Keep it scoped so the empty-window strip text ("No window: no evidence
  has been accepted for this site."), which is true on an empty Site, is still allowed.

### R2 (Low, optional, precision of a reason)

**Where:** `backend/assetops_backend/evidence/overview.py`, `_Window.status`.

**What is wrong.** Take an interval signal whose spanned GOOD records all overlap and which
also has a span-less GOOD record. It is reported as `OVERLAPPING_ONLY`, "has GOOD records in
this window that **all** overlap". I reproduced this with a scratch probe: PV with two
overlapping intervals plus one instant record. The value is correctly withheld, but "all
overlap" is not literally true of the span-less record. This is an unusual mix, so it is
not blocking.

**Fix if wanted.** Word the reason "none usable: overlapping, or without an interval span",
or add a combined status.

### R3 (Low, optional, stale docstring)

**Where:** `overview.py:21-22`.

**What is wrong.** The module docstring still says "A needed signal with no GOOD accepted
record in the window is a coverage gap". The rule is now "no record a metric can use".

**Fix:** a one-line edit.

No other regression found. The fix-round diff touches only `evidence/overview.py`, the API
doc, `sites/` and two new CSS classes, plus tests and records. The CSS classes are additive
and the layout rerun is clean on the Overview.

## Layout evidence

I counted `.agent/T027-phase-2-layout-evidence-fix-round-1.txt` myself: 513 PASS and 5 FAIL.

- **Four failures are known and pre-existing.** They are the three "blocked table" claims
  (`:124`, `:135`, `:146`) and the T025e p95 of 73.3 ms (`:559`).
- **The fifth is T026 "the attempts table has five columns, and a delayed reading is
  named"** (`:581`): delayed rows 48:0, against 48:1 in the phase 1 file and the phase 2
  run 3 file. Its history:
  - It passed in phase 1 and in phase 2 run 3.
  - It failed in phase 2 run 1, as the packet records.
  - It failed in this run.

**I accept the claim that the T026 failure is intermittent and outside this slice:**

- The fix round touches no Lab, cockpit, simulator or host code.
- Between 1968dde (run 3, pass) and HEAD, `git diff` over `frontend/src/shell`, `tools`,
  `simulator` and `host` changes only the Overview screen test.
- The claim drives the history cursor and reads after a fixed `sleep(600)`
  (`tools/layout-evidence.mjs:3742-3751`). The attempt rows were present (48: 10 rows,
  publication states 48:10), and only the delayed cell read 0. That is the signature of a
  read racing an asynchronous render, not of changed data.

It has now failed in two of the three phase 2 runs, though. It is not in
`.ai/MILESTONE_REVIEW_BACKLOG.md`. I recommend a backlog entry, "T026 held-publication
claim reads after a fixed sleep; replace it with a wait on the delayed cell", so it stops
being re-explained at each review. This is not a finding against T027.

Every T027 claim passes. The layout run does not assert the new window-note text on
screen; the screen test does.

## Carries

- **Generator running time → T028 backlog.** Acceptable. The entry has what is wrong, why
  it is safe, what would change the answer, and the fix. The basis states the
  whole-interval rule on screen.
- **Lab "no accepted evidence" wording** (`shell/RunsFrame.tsx:76-82`,
  `shell/RunSetupFrame.tsx:1178-1199`, and the similar `:502`). The carry is acceptable,
  with one correction to its rationale.
  - The main falsification ("Nothing here has been executed", "no causal runtime exists")
    is T022's.
  - The Runs list shows every run, with lifecycle and execution columns. So on that list,
    the clause "no accepted evidence" is also falsified by T027 for committed runs, and the
    backlog line "these predate T027's falsification" is only partly accurate.
  - It is a Lab-only developer surface, gated off by default, and outside the operator
    Overview. Under `D-2026-09-22-milestone-speed-over-purity` a recorded fast-lane carry
    is reasonable. I would not block on it.
  - The backlog wording could say that T027 extends the falsification. That is optional.
  - By contrast, R1 is operator-facing and is falsified by T027 alone, so it does not
    qualify for the same carry.

## Checks (all run by me at 95c6650)

| Check | Result |
| --- | --- |
| `tools/check-architecture.ps1` | Architecture check passed |
| `tools/check-agent-workflow.ps1` | Agent workflow check passed |
| backend `pytest backend/tests -q` | **1434 passed** (2 warnings) |
| host `pytest host/tests -q` | **602 passed** (3 warnings) |
| simulator `pytest -q` from `simulator/` | **244 passed** |
| frontend `npx.cmd tsc --noEmit` | clean, exit 0 |
| frontend `npm.cmd test` | **43 files, 1071 passed**. The sandbox did not block it this time. |
| frontend `npm.cmd run build` | built (483.03 kB JS, 25.64 kB CSS) |
| scratch probe: old any-GOOD rule | all 3 new F1 backend tests fail |
| scratch probe: mixed overlap plus span-less PV | value withheld, reason says "all overlap" (R2) |

All the packet's suite numbers match.

## Not verified

- **Layout evidence**, which I did not rerun. I assessed the recorded file only.
- **The live demo journey**, which is the owner's UI check.
- **The F4 non-vacuity mutation the packet describes.** I did not rerun it, but the
  real-client test fails by construction without the key check.
