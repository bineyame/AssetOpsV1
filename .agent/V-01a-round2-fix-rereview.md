# V-01a round 2 fix: verification re-review

Reviewer: a fresh Claude reviewer, independent of the Implementer. I fixed, committed and merged nothing.
Target: `task/V-01a-foundation-visual`, `bbfee7b..HEAD` (27deb76, 6ba4904, 9686863).

## Verdict

**Accept.** B1 and C1-C5 are addressed as the review asked, with no side effects found. No block findings.

## Per finding

- B1: `.panel--flush .panel__body.panel__note` (specificity 0,3,0) overrides the flush zeroing (0,2,0). `SitesIndex.tsx`
  is the only `.panel__note` user and sits in a `flush` Panel, so the scope is exact. Verified by reading CSS and
  markup. I did not render Sites or find the re-taken screenshots (their folder is not recorded in the packet), so the
  inset is verified statically, not by eye. The packet says the shots were viewed.
- C1: `roleTone(role, state)` returns neutral on `UNKNOWN`. The test now asserts every `[data-readiness-status] .badge`
  is `badge--neutral` in the no-basis case. It discriminates: before the fix those rows were amber. Optional and complete
  paths are unchanged.
- C2: legend green entry reads "Configured / Ready to report ...". The test expects the new text.
- C3/C5: packet and CODE_STATE now name the Lab-run drawing change as unverified (T025d) and correct the Finding-store wording.
- C4: `RailIcon` has `width={18} height={18}`; the guard keys on `width={18}`, a real size declaration (matching the
  `componentIcons` approach). Stale allowance still fails.

## Checks (as I ran them)

- `tsc --noEmit`: exit 0.
- `npm.cmd test` (full): 55 files, 1341 passed. It ran here; no esbuild failure.
- `siteFoundationRevision.test.tsx` x3 in isolation: 54/54 each time, about 12 s.
- `tools/check-all.ps1`: 6/6 guards pass.
- Not run: `npm run build`, evidence tools (105/105 claimed), backend pytest (no backend change), browser rendering.

## Flaky test

"does not select an undeclared part named in the address on first load" asserts after one `await settledScreen()`.
The component-clearing is a `replace` navigation issued in an effect once the period loads, so under CPU load (the
full run took 100 s with heavy contention) the assertion on `location()` can race the effect. It passed 3/3 alone and
in the full run, which fits a timing/async race, not a logic bug. Carry: wrap the location/notice assertions in
`waitFor`.

## Walkthrough `.agent/V-01a-owner-walkthrough.md`

Labels checked against code: "Setup details", "Readings not assessed here", "Clear selected part", "Configured, not live",
"Selected part is not in this Foundation period", "No stored version for this period", "No sites configured" all exist.
Ports, v13 and 1 Sep dates, and the `component=` links match `tools/v01a_foundation_walkthrough.py`. The rail contents,
icons, grey tabs and Q1-Q5 outcomes (bus bar, Foundation heading, green/amber, stable selection, icons) are all described.
Minor: there is no explicit "decisions recorded" list mapping Q1-Q5; the intro says "applies your answers" and the
body covers each. Not blocking.

## Findings

- Block: none.
- Carry: (1) flaky test above, add `waitFor`. (2) Walkthrough could list Q1-Q5 outcomes explicitly. (3) Sites inset and
  re-shot not eyeballed by me. (4) Existing carries: Lab-run drawing T025d unverified; Architect confirmation on C1
  neutral-row rule before closure.

## Ready for the owner's visual check?

**Yes.**
