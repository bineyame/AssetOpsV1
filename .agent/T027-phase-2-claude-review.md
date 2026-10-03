# T027 phase 2 review: the mini-grid Site Overview

Reviewer: Claude, a fresh instance independent of the Implementer. Reviewer is Claude under
`.ai/ROLE_CONFIG.md` until the Codex reset 2026-10-03 21:23, so Codex may revisit any
judgement here retrospectively. Range `593d2ff..25bb32d` (7aad445 through 25bb32d), branch
`task/T027-commit-ingestion-and-site-overview`.

## Verdict: accept with findings fixed on the branch

Two findings must be fixed on the branch: F1 and F2. Both are small. F3 is for the owner
to judge during the demo, and the rest are low or carried. The core of the slice is sound:

- Card state comes only from the backend read model.
- The profile holds `{id, label}` and nothing else.
- "No assessment yet" is neutral and "Unknown" never appears.
- Uncovered cards name their gap in the normal case.
- The N9 single list is real.
- AC14 and AC15 cover the Overview.
- The overflow guard was extended, not loosened.

## Findings

### F1 (Medium, must fix, acceptance gap AC11 and the phase-2 "never a fabricated value")

**Where:**
- `backend/assetops_backend/evidence/overview.py:191` (`_Window.uncovered`), and its use at
  `:305` and in `_dispatch` and `_renewable`.
- `frontend/src/sites/SiteOverview.tsx:208`.

**What is wrong.** `uncovered()` asks "is there any GOOD record?" The metrics instead read a
narrower set: `_intervals()` and `_instants()` drop overlapping records (AC9) and records
without an interval span. When a signal has GOOD records but none of them is usable, the
signal is not a gap, yet the metric has nothing to compute from. I reproduced both outcomes
with the test file's own `record()` fixture, calling `OverviewReadModel` directly:

- **All SOC samples overlap.** Two GOOD records at the same instant from two gateways give
  a Battery card with `gaps == []` and every metric `value None, unavailable_because None`.
  The screen renders "Not available." with no reason, and the card names no gap.
- **An interval signal with no usable interval** (PV reported only as an instant record)
  gives `pv-energy` = **"0.0" kWh**, "over 0.00 h of measured intervals". It has no gap
  and an evidence list. A zero kWh value is presented as a measurement where there is no
  measured interval at all. Phase 1's own rule (the `SiteDetails` header) is that "a zero
  ... is a measurement claim rather than an absence".
- **The same root cause reaches Served energy**: a feeder whose intervals all overlap
  contributes 0 to the total and appears only as "0.00 h" inside the basis text.

**Why it matters.** Overlap is an explicit T027 proof case (AC9 and phase 1's conflict
handling), so this path is reachable. The phase-2 text says an uncovered card "names its
coverage gap, never a fabricated value".

**Fix.**
- Decide coverage from the set each metric actually uses. For example, add a status such as
  `NO_USABLE_RECORD` or `OVERLAPPING_ONLY`, so that the card lists it as a gap and
  `unavailable_because` names it, e.g. "N GOOD records overlap; overlapping records are used
  by no metric".
- Give an interval metric no value when it has 0 measured seconds.
- Add a test for each case. No current test covers a signal whose records all overlap.

### F2 (Medium, must fix, false statement left by this task, `D-2026-09-22-expiry-follows-the-condition`)

**Where:** `frontend/src/sites/SiteConfiguration.tsx:431-454` (the Foundation tab's "Not
available for this site" panel), with its facts at `frontend/src/sites/siteViewModel.ts:179-201`.

**What is wrong.** For a Site with accepted evidence, the Foundation tab still says:

- "Evidence availability: No evidence. No evidence has been accepted for this site".
- "Source health: Not recorded. This build records no source health for a site".
- "There is no accepted evidence".

All three have been false since phase 1. Phase 1 ingests evidence and Site > Evidence
renders per-source health. The Implementer removed the identical panel from the Overview
page for this very reason (deviation 4) but left the Foundation copy, and the packet
proposes a fast-lane fix instead.

**Why it is in scope.** The decision is explicit: "A claim that has become **false** goes
in the same slice that falsifies it. Leaving it is not caution, it is shipping a false
statement." T027 is the slice that falsifies it. The owner's demo path
(Overview -> Foundation -> Evidence) will show it.

**Fix.**
- In the substrate panel, drop or reword Evidence availability and Source health. They
  could point to Site > Evidence, or the sentence could be stated only where it is true.
- Keep Integration readiness, which is still honest.
- Update `siteConfiguration` and `foundationScreen` tests to match.
- One edit in `sites/` covers the Lab Site page too.

### F3 (Medium, not blocking, owner judgement on presentation honesty)

**Where:** `frontend/src/sites/SiteOverview.tsx:169`.

**What I checked.** The Energy "measured intervals" wording is truthful at the metric level:

- The card label is "Served energy, measured intervals".
- The basis lists each feeder's measured hours.
- The note below the cards says time between measured intervals is not counted.
- No sample is carried forward.

**What is wrong.** The objective strip renders the same metric under the term "Service
delivered" and shows only the value plus basis, not the label. Its headline therefore reads
"Service delivered 67.3 kWh", with the 8.00 h window two facts below it. The strip never
says that the 67.3 kWh covers about a third of the window. Packet point 6 quotes the wording
"measured intervals, 2.67 h of 8.00 h". No such text exists on screen: the basis says
"(residential feeder 2.67 h, clinic feeder 2.67 h, mill feeder 2.67 h)" and never states
"of 8.00 h".

**Why it matters.** ARCHITECTURE "Presentation Honesty" says: "A status may be weaker than
its name. Where it is, ... the screen say[s] what the status does not assert."

**Suggested fix.** In the strip, show the metric's own label, or add the measured fraction
of the window (e.g. "2.67 h of the 8.00 h window measured"). Correct packet point 6 so it
quotes what is actually on screen. This is a recommendation: the owner may accept the
current wording at the demo.

### F4 (Low, robustness, optional)

**Where:** `frontend/src/sites/siteOverviewClient.ts:121-160` (`isSiteOverview`).

**What is wrong.** The validator does not check several fields the screen renders:

- `at` and `unavailable_because` on metrics.
- `gaps` items, and the `evidence` items inside each metric.
- `interval_statement`, `timeline_statement`, `findings_statement`.
- The timeline `basis` and `points` items.

A backend drift would render as empty text or "undefined" instead of the "Overview
unavailable" panel.

**Fix:** add those keys to the checks.

### F5 (Low, observation)

**Where:** `backend/assetops_backend/evidence/overview.py`, `sources_in_window`.

**What is wrong.** The count is of `(source_id, gateway_id)` pairs, but the strip calls it
"sources". It is the same number on the demo fixture, so this is a nit.

## Judgements requested by the dispatch

### N9: the backend test reads `frontend/src/sites/presentationProfiles.json`

Acceptable; it should not move.

- The decision and ARCHITECTURE place the profile in the frontend substrate, and say the
  backend owns domains and signals but not presentation.
- Moving the JSON to a shared or backend location would make the backend a source for
  presentation data, which is the coupling the decision prevents.
- This is a test-time pin with no runtime import. It pins three things:
  - card ids equal to `OVERVIEW_DOMAIN_SIGNALS` in order,
  - `DOMAIN_METRICS` keys,
  - profile keys `{id, label}` only.
- `NEEDED_SIGNALS` is derived from `OVERVIEW_DOMAIN_SIGNALS`, so there is one list.

Residual risk: the backend suite now needs the frontend tree checked out. That is fine in
this monorepo and worth a comment if the backend is ever tested standalone.

### Deviations

1. **Profile-only rendering.** This is consistent with
   `D-2026-10-02-presentation-profile-and-capability-declaration`: the three rendering rules
   apply to backend capability ids, "not to the profile's Overview domain cards". The
   orphan case is covered by the backend pin, and screen tests cover unserved and
   out-of-order cards. Accept.
2. **Profile location.** Accepted; see N9 above.
3. **No confidence in the objective strip.** Correct. Any confidence would be invented
   before T028. Accept.
4. **Removal of the Overview page's "Not available" panel.** Correct for the evidence and
   source-health sentences, which were false.
   - Integration readiness was still honest. Removing it from the Overview page is a small
     product choice, but it remains stated on Foundation and the packet discloses it.
     Accept.
   - The same falsity left on Foundation is F2.
5. **Overflow guard.** Extended, not loosened. `tools/checks/shell-overflow.ps1` adds the
   fourth module under the same three rules, each with its own failure message: the region
   declares `overflow-x: auto|scroll`, the module renders the region, and the module draws
   an svg (a non-vacuity check). The error message for a stray svg now names all three
   modules. No existing rule was weakened.

### Evidence links

The address is the phase-1 inspector form, `/sites/{id}/evidence?signal=DEV/SIG&record=MSG`.
`siteEvidenceRecordHref` encodes device and signal separately, and `RecordInspector` splits
on the first `/`, so the two agree.

Every metric's evidence is a real accepted record of that signal. This is asserted by
`test_evidence_links_name_accepted_records`. The route test resolves a link through
`/evidence/records/{id}`. A screen test clicks a link and lands on Evidence with the record
detail open. The recorded browser run did the same on SITET26.

Both views use the same `default_window`, so the inspector list and the Overview share a
window.

### Card state and vocabulary

- `orderedOverviewCards` takes only the label and order from the profile. The badge, gaps,
  metrics and coverage all come from the backend card.
- `"unknown" not in json.dumps(payload).lower()` is asserted, and a screen test asserts the
  same on the rendered page.
- In the normal case, an uncovered card shows "Coverage gap: fuel-level-sensor/fuel-level
  reported no accepted record in this window." and no number. F1 is the exception.

### AC14 and AC15

`TestRebuild` snapshots now include `OverviewReadModel.site_overview`.
`t027_isolated_probe.build()` includes `overview`, and `TestRebuildIsolated` asserts:

- the isolated payload equals the in-process payload,
- `leaked == []`,
- the Fuel card reads `100` with no gaps.

I did not rerun the packet's `import assetops_simulator` non-vacuity mutation, because
this role does not edit product code. The mechanism is unchanged from phase 1, where I
verified it.

## Checks I ran myself (this machine, at 25bb32d)

| Check | Result |
| --- | --- |
| `tools/check-architecture.ps1` | passed |
| `tools/check-agent-workflow.ps1` | passed |
| backend `pytest backend/tests -q` | **1431 passed** (2 deprecation warnings) |
| host `pytest host/tests -q` | **602 passed** |
| simulator `pytest -q` from `simulator/` | **244 passed** |
| frontend `npx.cmd tsc --noEmit` | clean (exit 0) |
| frontend `npm.cmd test` | **43 files, 1068 passed**. Unlike the standing brief's expectation, the sandbox did not block it this time. |
| frontend `npm.cmd run build` | built cleanly (482.83 kB JS, 25.46 kB CSS) |
| edge-case probe (scratch script, no repo change) | reproduced F1, both outcomes |

All of the packet's suite numbers match what I observed.

## Layout evidence

I did not rerun it; I assessed the recorded file, `.agent/T027-phase-2-layout-evidence.txt`.

- The tally is 514 PASS and 4 FAIL. I counted the lines myself.
- The four failures are the pre-existing ones: three "blocked table" claims and the T025e
  p95 75.6 ms delta budget.
- Every T027 Overview claim passes, with the following measured values:
  - **Populated, at 1280, 1000 and 640:**
    - profile order holds,
    - 5 of 5 cards read "No assessment yet",
    - the value sets are non-empty,
    - Fuel shows 1 named gap,
    - there are 17 inspector links,
    - the timeline draws 96 kW marks and 32 % marks,
    - at 640 the chart overflows its own `overflow-x: auto` region by 9 px and the page
      does not scroll,
    - the tab row reads Overview|Foundation|Evidence with Overview current.
  - **The clicked link** opens Evidence with the record selected.
  - **Empty MG-006, at 1280 and 640:** all five cards show named gaps, there is no chart,
    and nothing scrolls.
- Runs 1 and 2 are recorded honestly and not counted as evidence.
- The gate-closed browser pass is declared as not run. Unit and route tests cover it.

The packet meets the standing layout-evidence requirement.

## What I could not verify

- The live demo journey (Lab run -> Commit -> Overview -> Lab off). That is the owner's UI
  check.
- The AC15 non-vacuity mutation, which I did not rerun (see AC14 and AC15 above).
- The Kobo v3 cadence claim ("5-minute interval before each 15-minute report"). I did not
  trace it in the simulator. It is consistent with the recorded figures: 32 marks per kW
  series × 5 min = 2.67 h.

## Residual risk not in the packet

- The F1 class: overlap, or interval records without a span, silently reduce or zero a
  metric.
- The backend suite now depends on the frontend tree being present (N9).
- Generator running time counts a whole 5-minute interval as running whenever its mean is
  above zero. The basis states this ("Measured intervals with generator output above
  zero"), but it overstates running time for partial-interval starts. That is fine before
  T028 and should be revisited when the dispatch Finding uses runtime.
