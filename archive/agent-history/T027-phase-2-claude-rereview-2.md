# T027 phase 2 fix round 2: re-review

Reviewer: Claude, a fresh instance that is independent of the Implementer and of both earlier
phase 2 reviewers. Claude holds the Reviewer role under the temporary binding in
`.ai/ROLE_CONFIG.md` until the Codex reset at 2026-10-03 21:23, so Codex may revisit any
judgement here retrospectively.

- Range: `3f1b00f..7ab4619` (d2a1783, 1e4a8ce, 7ab4619).
- Branch: `task/T027-commit-ingestion-and-site-overview`.

## Verdict: accept with findings fixed on the branch

R1, R2 and R3 are closed. One new finding, S1, needs action before merge, but it can be
handled as a backlog carry. S1 is in the Quick actions panel, the same panel as R1, and it
shows only when the Lab gate is open. T027 did not cause it: it has been false since the Lab
gained scenarios and a runtime. It is still on the owner's demo path, because the demo runs
with the gate open, right under an Overview fed by a committed simulated run. S2 is
comment-only and optional.

## Findings from re-review 1

| Finding | Status | Evidence checked |
| --- | --- | --- |
| R1 "View Live Data" reason | Resolved | See "R1 in detail" below. |
| R2 mixed reason | Resolved | See "R2 in detail" below. |
| R3 docstring | Resolved | `overview.py:21-24` lists the four gap conditions. They match `status()` and `usable()`. |
| Backlog | Accurate | See "Backlog in detail" below. |

### R1 in detail

**Where:** `SiteDetails.tsx:409-416`.

**The new sentence is true in every state the panel renders.** It reads: "Live data is not a
capability of this build. Accepted evidence for this site is on the Evidence tab."

- No live-data feature exists.
- Evidence is a capability tab on every operator Site.
- `SiteQuickActions` has only one renderer, `SiteDetails.tsx:340`, which is the operator
  Site page.
- The sentence holds for both an empty and a populated Site, because it states where
  evidence lives, not whether any exists.

**How the tests pin it:**

- `siteDetail.test.tsx` checks the exact text.
- `siteDetailScreen.test.tsx` covers both gate states: it checks the prefix and rejects "no
  evidence has been accepted".

**How the widened check works:**

- The populated-Overview test in `siteOverviewScreen.test.tsx` now rejects
  `/no evidence has been accepted/i` and `/nothing (has been|was) accepted/i` across all of
  `<main>`. The old sentence matches the first pattern, so the test would have caught it.
- The empty-Site case is a separate test and does not carry these patterns, so the strip's
  true "No window: no evidence has been accepted for this site." is still allowed there.

### R2 in detail

**The new status is mutually exclusive with the others:**

- It is reached only for an interval signal with no usable record.
- `_spanned()` is a subset of `_good()`. An empty spanned set returns `NO_INTERVAL_SPAN`
  first.
- A strictly smaller spanned set means at least one GOOD record has no span. That case
  returns `OVERLAPPING_OR_NO_SPAN`.
- Otherwise, every GOOD record is spanned and none is unique. That case returns
  `OVERLAPPING_ONLY`.
- The pure-overlap tests (`test_t027_overview.py:182`, `:224`) still assert
  `OVERLAPPING_ONLY`.

**The value is withheld:** the new test asserts that every Renewable metric's value is
`None`.

**The reason is rendered:** `SiteOverview.tsx:280` renders `gap.reason` verbatim.

**The test is non-vacuous by construction.** Without the new branch, the status would be
`OVERLAPPING_ONLY`, and the test's first assertion would fail.

**The frontend accepts the new status:**

- `isSiteOverview` checks only that the `status` and `reason` keys are present.
- `OverviewCoverage.status` gains the literal, and it is still `| string`.

**The API document is updated:** `evidence_api.py:83-86`.

### Backlog in detail

- **The Lab carry now cites the right lines and says T027 extends the falsification.** I
  checked the cited lines against the files. They match the prior review's citations.
- **The T026 layout entry is accurate.** It cites `layout-evidence.mjs` around 3742-3751,
  says the claim failed in two of three runs, and proposes a fix.
- **The heading count is right:** three items.

## New findings

### S1 (Medium, fix or carry before merge): the gate-open Quick actions reasons are false

**Where:** `frontend/src/shell/simulatorLabRoutes.tsx:456-468`, `simulatorLabSiteActions`.
These actions render inside the Quick actions panel on the operator Overview page whenever
`simulator_lab.enabled` is true. The fix-round-1 layout file shows them present (line 10:
"Open in Simulator Lab:disabled, Start Simulation:disabled").

**What is wrong:**

- **"Start Simulation"** gives the reason "Nothing can be simulated yet. A run needs a
  scenario and a runtime, and neither exists in this build." Both exist: scenarios exist,
  and runs have executed since T022, as the backlog's own Lab entry says. T027 now commits
  those runs into accepted evidence, which is what the Overview above this panel displays.
- **"Open in Simulator Lab"** gives the reason "... arrives with the Lab's own Site and run
  surfaces, which are a later step". This is partly stale. The Lab's run surfaces (Runs, Run
  setup) exist. A Lab Site view still does not.

**Why it matters:**

- This is the class of statement the dispatch asked to sweep for: a false sentence on the
  operator Overview page.
- In the owner's demo (gate open, run, Commit, Overview), the panel says nothing can be
  simulated, directly below values computed from a simulated run.
- T027 did not introduce the falsification, so this is not an acceptance gap against T027's
  criteria in the way R1 was. It is also not covered by the existing Lab carry, which names
  only `RunsFrame.tsx` and `RunSetupFrame.tsx`, and no backlog entry mentions it.
- No test or regex would catch it. The populated-Overview test's patterns target evidence
  denial only.

**Fix (either one):**

- **Preferred:** reword both reasons so they state what is true:
  - Start Simulation: a run is started from the Lab's Run setup, not from a Site.
  - Open in Simulator Lab: the Lab has no Site view yet.

  Then update the gate-open test in `siteDetailScreen.test.tsx` to pin the new text.
- **Minimum:** add this to the "Carried from T027 phase 2" backlog section under
  `D-2026-09-22-milestone-speed-over-purity` (gated off by default), so it is recorded rather
  than found again.

### S2 (Low, optional): stale comments, none of them rendered

- **`frontend/src/sites/SiteOverview.tsx:11-13`** says a metric "whose signal has no GOOD
  accepted record in the window shows no value". This is the frontend twin of R3. The rule
  is now "no record a metric can use".
- **`frontend/src/sites/SiteDetails.tsx:379-382`** says the View Live Data reason "is about
  evidence rather than about the Lab". After R1, it is about capability.
- **`frontend/src/sites/SiteDetails.tsx:55-57`** lists "no quick-actions container" among
  things the page does not show. This predates T027, but the panel is rendered.

## Sweep of the Overview page (SiteDetails, SiteOverview, SiteDetailFrame)

I found no other rendered sentence that T027 makes false:

- **Foundation paragraph:** "nothing here states that a device exists ... or has ever
  reported a measurement" is scoped to the foundation document, so it is true.
- **Provenance paragraph:** true.
- **"Overview unavailable" text:** true.
- **Not found and store-unavailable states:** true.
- **Strip's empty-window text:** true on an empty Site.

S1 is the only false rendered text on the page, and it is in the gate-open state.

## Layout evidence decision

The decision not to rerun is sound:

- R1 and R2 change only strings, and the new R1 string is shorter (113 against 154
  characters) in a paragraph that already wraps.
- No layout claim reads the reason text or the gap status names.
- No CSS, structure or geometry changed in this range: the diff touches no stylesheet and no
  component structure.

Fixing S1 by rewording would not need a rerun either, on the same grounds.

## Checks (all run by me at 7ab4619)

| Check | Result |
| --- | --- |
| `tools/check-architecture.ps1` | Architecture check passed |
| `tools/check-agent-workflow.ps1` | Agent workflow check passed |
| backend `pytest backend/tests -q` | **1435 passed** (2 warnings) |
| frontend `npx.cmd tsc --noEmit` | clean, exit 0 |
| frontend `npm.cmd test` | **43 files, 1071 passed**. The sandbox did not block it. |
| frontend `npm.cmd run build` | built (482.99 kB JS, 25.64 kB CSS) |
| `git diff 6035bcb..HEAD -- host simulator` | empty, so host and simulator are untouched |

All the packet's numbers match.

## Not verified

- **Layout evidence:** not rerun. The decision is assessed above.
- **The R1 non-vacuity revert the packet describes:** not rerun. I reasoned it from the
  regex instead: the old sentence contains "No evidence has been accepted for this site",
  which matches `/no evidence has been accepted/i`.
- **The live demo journey:** this is the owner's check.
