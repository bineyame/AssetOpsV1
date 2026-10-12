# S4-01 fix round 4 re-review (fresh Claude reviewer)

Produced by a fresh Claude reviewer that did not author S4-01 or any of its fix rounds. Scope: `3fccb72..HEAD`
(`00109b1`, `5df3460`, `46258aa`) on `task/S4-01-finding-identity`, against R1, R2, C7 and C8 in
`.agent/S4-01-phase-3-fix-rereview.md`, plus a live walk of every step in `.agent/S4-01-owner-walkthrough.md`.
No code was changed, merged or committed by the reviewer.

## Verdict

**Accept.** R1, R2, C7 and C8 are closed and verified against the real dispatch-3.1 emitters and live. The
findings below are low carries; none blocks.

**Ready for the owner walkthrough: yes.** Every guide step reads as the guide says (one trivial ordering note,
K1).

## Checks I ran (results as observed)

| Check | Result |
| --- | --- |
| `tools/check-architecture.ps1` | `Architecture check passed.` |
| `tools/check-agent-workflow.ps1` | `Agent workflow check passed.` |
| `pytest backend/tests -q` (no `ASSETOPS_TEST_DATABASE_URL`) | `1771 passed, 127 skipped` |
| `npx.cmd tsc --noEmit` | exit 0 |
| `npm.cmd test` | 55 files, 1325 passed (the sandbox esbuild failure did not occur in this session) |
| `npm.cmd run build` | built (chunk-size warning only) |
| `s4_finding_walkthrough.py prepare` | comparison PASSED (empty-set), cutover permitted, 10-09 staged PENDING; tree from `46258aa` |
| `links --web-port 5340` | every version of each multi-version Finding; four Dispatch days, 10-25 labelled not assessed |
| `serve --port 8840` + Vite 5340, pages rendered with headless Chrome | all steps, see below |
| `node tools/s4-finding-evidence.mjs` | `36/36 claims passed` (screenshots in my scratchpad) |
| Postgres S4 suites (30), `check-all` | not rerun; Implementer's numbers, unverified by me. No producer or stored data changed. |
| `tools/layout-evidence.mjs` | not run (Q28 blocker, as the packet records) |

Servers stopped; 8840 and 5340 free, no leftover walkthrough, Vite or headless Chrome processes. Owner ports
and `var/` not touched.

## Prior findings

| Finding | Status | Evidence |
| --- | --- | --- |
| R1 | Closed | Live F05 v2 default view: "No records are missing. It could not decide because the generator may still have been inside its 120-minute minimum operating time after starting." A scan of the whole default page finds none of PV, PCS, Candidate, Necessary, headroom, "configured minimum", "reserve 20", "settings now in force". The raw strings appear only under Analysis, "Portions that could not be decided" (cause kind `MODELLING`). The earlier-version wording issue is gone, because the sentence no longer mentions settings. |
| R2 | Closed | `finding_read.portion_cause` uses the real `dispatch_v3._NOT_EVIDENCE_GAPS` tuple and the same `startswith` rule as the window `EVIDENCE_GAP` (`dispatch_v3.py:539`). Every record-gap emitter (`_missing` at 259/265/271/278, "generator state not observed" at 418, segment limits at 422) produces a non-prefixed string, so it reads as RECORD_GAP, "Some records it needs are missing or conflict over part of the period." The four modelling emitters (297, 303, 310, 326) match the four prefixes. Revision `limitations` no longer decide the cause. The backend test uses `dispatch_v3._missing` for real shapes, and pins the selected revision (not the latest), OPEN_BOUND-only and source-closed. |
| Transition rule | Correct | `_combine` appends the transition string only when one end is Candidate and the other is Indeterminate. That other end carries its own cause, so `indeterminate_cause` drops the transition words when another cause is known. That is right: the transition is a consequence, not the cause. On its own (only when the other end's `missing` is empty, which the emitters make near-impossible) it reads in plain words. |
| Import-time table check | Present | `assert set(_MODELLING_WORDS) == set(_NOT_EVIDENCE_GAPS)` at `finding_read.py:69`; see K3. |
| C7 | Closed | Guide step 8 now names four addresses and assigns 10-06 to step 1. |
| C8 | Closed for the read path | `WhatLimits` shows "Some records this version needs are missing or conflict ..." and drops "No record gaps or conflicts were found" when the cause is RECORD_GAP (vitest case). F05 v2 (modelling) correctly still says none were found. See K2 for the source-closed edge. |

## Live walkthrough (every guide step)

1. F01: "Generator support merits review", "Open", "Up to date", 45 / 15 / 0 min cards, Dispatch 10-06 link. Block select and reload are covered by the evidence run (36/36).
2. F04: version 1 address reads "Earlier version 1 of 3" and links the latest; the version list marks "(shown)".
3. F03 recurrence: "This happened before ... it does not say the earlier Finding is still open", with a link to it.
4. F05 v2: as R1 above. F05 latest: "No longer supported ... does not mean the generator was repaired or that money was saved."
5. F02: "Out of date"; "ran between 2026-10-08 23:20 – 2026-10-09 00:55 UTC, with one short stop"; the stop is named; links to 10-08 and 10-09.
6. F06 joined: leads with "Joined into an earlier Finding".
7. F01 Analysis: delivery batch, gateway / source / sequence, assessment revision and pass, site settings revisions.
8. 10-19: "could not decide, so this is not a no-Finding result"; 10-07 and 10-25: "No assessment exists for this day, so whether there is a Finding is not known".

## Carries (low, non-blocking)

- **K1 (doc)** `S4-01-owner-walkthrough.md` step 4 says the page shows the cause sentence, then "this is not a new issue". Live, the order is reversed: "... This is not a new issue; the earlier versions stay available below. No records are missing. It could not decide because ...". The owner will still find both sentences.
- **K2 (low)** `SiteFinding.tsx:417-420`: when the Performance source is closed (`source_open=False`, reachable through `finding_api.py:113` before cutover), no portions are read and `indeterminate_cause` is null. A Not confirmed version then reads "Why it could not decide is not available in this read." but "What limits" still says "No record gaps or conflicts were found over this period", which nothing checked. The fix is to show the neutral line only when `indeterminate_cause` is non-null, or the version is not Not confirmed. The walkthrough runs with the source open, so it does not show this.
- **K3 (low)** The table check is a bare `assert` (`finding_read.py:69`), which `python -O` strips. A one-line pytest of the same equality would pin it regardless.
- **K4 (low, residual, inherited from the window rule)** A Candidate point keeps incidental `missing` entries for inputs its branch did not need, such as SOC or the reserve setting when solar alone covers demand (`dispatch_v3.py:286-292`). If minimum runtime then withholds it, the portion reads RECORD_GAP ("records it needs are missing") rather than naming the runtime. This is the same classification the window `EVIDENCE_GAP` already makes, so it is consistent with the accepted rule, and it errs towards stating a gap rather than hiding one. Worth a note for the dispatch model owner, not for S4-01.
- **K5 (test coverage)** The plain words for battery-near-reserve, capability margin and a transition on its own are not asserted in any test (only the runtime and the drop-transition path are). The import check guarantees they exist, not how they read.
- C5 and the phase 1-2 carries remain as the packet states.

## Ready for the owner walkthrough?

Yes. Prepare, links and serve work on 8840/5340 as the guide states, and every step reads as described. K1 is a
one-line guide tweak the coordinator may make or leave.
