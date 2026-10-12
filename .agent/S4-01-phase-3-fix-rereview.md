# S4-01 phase 3 fix round 3 re-review (fresh Claude reviewer)

Produced by a fresh Claude reviewer that did not author S4-01 or its fix round. Scope: `b559b0a..HEAD`
(`60aae53`, `565f9b8`) on `task/S4-01-finding-identity`, against `.agent/S4-01-phase-3-review.md` B1-B4,
C1-C4, C6 (C5 carried), plus a live walkthrough check. No code was changed, merged or committed by the reviewer.

## Verdict

**Accept with findings fixed on the branch.** B2, B3, B4, C1, C2, C3, C4 and C6 are closed and verified
live. B1's contradiction is gone (the page no longer says records were missing for F05 v2, the card note is
neutral, the headline says "cannot decide"), but the replacement cause sentence has two problems: it shows
raw assessment-engine text in the default view and names the wrong things as the cause (R1), and its
"records missing or not" test does not match how dispatch-3.1 actually records a record gap, so it would say
"No records are missing" for a genuine gap (R2).

**Ready for the owner walkthrough: not yet.** It is ready once R1 is fixed (a small wording change in
`unconfirmedCause` plus guide step 4). All other guide steps and addresses check out. R2 must be fixed before
closeout; it is cheapest to fix together with R1.

## Checks I ran (results as observed)

| Check | Result |
| --- | --- |
| `tools/check-architecture.ps1` | `Architecture check passed.` |
| `tools/check-agent-workflow.ps1` | `Agent workflow check passed.` |
| `.venv\Scripts\python.exe -m pytest backend/tests -q` (no `ASSETOPS_TEST_DATABASE_URL`) | `1766 passed, 127 skipped` - collects cleanly (B4 closed) |
| `npx.cmd tsc --noEmit` | exit 0 |
| `npm.cmd test` (full) | 55 files / 1324 passed (the sandbox esbuild failure did not occur here) |
| `siteFinding.test.tsx` focused | 30 passed |
| `npm.cmd run build` | built (chunk-size warning only) |
| `tools/s4_finding_walkthrough.py prepare` | comparison PASSED (empty-set), cutover permitted, 10-09 staged PENDING |
| `links` | prints every version of each multi-version Finding; Dispatch days 10-06, 10-19, 10-07, 10-25 with 10-25 labelled not assessed |
| `serve` 8840 + Vite 5340, pages rendered with headless Chrome | F01, F01-gateway, F02, F03 recurrence, F04 v1, F05 v2, F05 latest, F06 joined, Dispatch 10-06/10-19/10-07/10-25 read as described below |
| `node tools/s4-finding-evidence.mjs` | `36/36 claims passed` (screenshots in my scratchpad) |
| Postgres S4 suites (25), `check-all` | not rerun; Implementer's numbers, unverified by me. The backend diff is a read-time field plus a test default-arg fix. |
| `tools/layout-evidence.mjs` | not run (Q28 blocker); packet records it as not run, correctly |

I did not run `tools/s4_finding_cases.py run`; `prepare` copied the existing `assetops_s4cases` (producer
commit `4c499b6`). The fix round changes no producer or stored data, only a read-time field, so that is sound.
Servers stopped; 8840, 5340, 9343 and 8763 are free. Owner ports and `var/` were not touched.

## Prior findings

| Finding | Status | Evidence |
| --- | --- | --- |
| B1 | Contradiction closed; replacement wording raises R1/R2 | F05 v2 no longer says records are missing; card "Could not be decided either way"; headline "This version cannot decide whether any of that time was possibly avoidable" |
| B2 | Closed | F02: "The generator ran between 2026-10-08 23:20 – 2026-10-09 00:55 UTC, with one short stop recorded in that time." F01/F03/F04 without stops keep "stayed on" |
| B3 | Closed | every version printed; 10-25 relabelled; 10-19 reads "could not decide, so this is not a no-Finding result"; 10-07 and 10-25 read "No assessment exists for this day, so whether there is a Finding is not known"; 10-06 links F01 |
| B4 | Closed | default pytest collects and passes |
| C1 | Closed | `\.` restored in `settled.ts` |
| C2 | Closed | F05 v2: "78 accepted records are cited by this version" |
| C3 | Closed | F02 heading "Open · out of date" |
| C4 | Closed | F04 v1 and F05 v2: one "A later version replaces this one", no duplicate currentness sentence |
| C5 | Carried (as stated) | |
| C6 | Closed | evidence text names `%LOCALAPPDATA%\AssetOps\s4-finding-walkthrough\evidence`, which exists |

## New findings

### R1 (block before walkthrough): the Not confirmed cause is engine text and names the wrong cause

`frontend/src/sites/findingWords.ts:192-212` (`unconfirmedCause`), shown by `SiteFinding.tsx:202-206`.

Live F05 version 2 lead (walkthrough step 4) reads:

> No records are missing. It could not decide under the settings now in force: PV available plus PCS discharge
> capability covers load with 10 % headroom; reserve 20.0 %; possibly within the configured minimum runtime (120
> min from the first ON report); Candidate withheld, no policy Necessary claimed.

- It is the raw `dispatch_v3` reason and `missing` strings ("PV", "PCS", "Candidate withheld", "no policy
  Necessary claimed") in the default view, which elsewhere uses plain words ("solar power and the battery",
  "possibly avoidable"). The owner's standard is plain text by default, technical detail in Analysis.
- It lists every reason as a cause. The first ("solar plus battery covers load with 10 % headroom") is the
  reason the block *would* be possibly avoidable, and "reserve 20.0 %" is just an input echoed on every
  dispatch-3.1 point. The only cause is the minimum runtime (`dispatch_v3.py:307-312`).
- On an earlier pinned version, "settings now in force" is not what is shown; the reasons come from the
  assessment that version cites, which may not be the one now in force (low, fold into the fix).

Why it matters: this is the step the guide highlights, and the owner reads it as the product's explanation.

Fix: name only the undecided cause, in plain words, from the known modelling prefixes
(`dispatch_v3._NOT_EVIDENCE_GAPS`: minimum runtime, SOC headroom over reserve, capability margin inside the
headroom, transition inside the segment), e.g. "It could not decide because the generator may still have
been inside its 120-minute minimum operating time after starting." `analytics/plain.py:51,69-74` already has
the plain vocabulary. Put the raw strings under Technical detail / Analysis. Say "the settings this
assessment used". Update guide step 4 to the new sentence. Add the vocabulary scan
(`scanProductVocabulary`) or an explicit no-engine-terms assertion to the B1 test.

### R2 (block before closeout; fix with R1): the "records missing" test does not match dispatch-3.1 data

`findingWords.ts:200` decides a record gap from `limitations.length > 0` or a reason matching
`/missing or conflicting/`. In dispatch-3.1:

- record gaps are written to a segment's `missing` as `"<label>: no accepted reading"`, `"... not GOOD
  quality"`, `"<role>: <kind> between ..."` or `"generator state not observed ..."`
  (`dispatch_v3.py:208-212, 257-258, 416-422`); the "missing or conflicting" sentence only exists in the older
  `dispatch.py`;
- a Finding revision's `limitations` come only from the interval result (`OPEN_BOUND`) plus
  `ANCHOR_OUTSIDE_SUPPORT` (`finding_episode.py:140, 435-437`, `dispatch_v3.py:449-453`); the `EVIDENCE_GAP`
  limitation is window-level (`dispatch_v3.py:537-542`) and does not reach the revision.

So a Not confirmed version caused by a missing or conflicting reading would read "No records are missing. It
could not decide ...: PV available power: no accepted reading", and one carrying only `OPEN_BOUND` or
`ANCHOR_OUTSIDE_SUPPORT` would read "Some records it needs are missing or conflict". The B1 gap test uses
`limitations: ["EVIDENCE_GAP: ..."]`, a shape a revision does not carry, so it passes without proving the
real path. The fixture has no record-gap Not confirmed case, so the walkthrough does not show this.

Fix: classify in the backend, where `_NOT_EVIDENCE_GAPS` lives. Have `indeterminate_reasons` carry a
per-portion `kind` (`RECORD_GAP` / `MODELLING`) using the same prefix rule as the window `EVIDENCE_GAP`, and
let the screen decide from that. Add tests on real shapes: one modelling portion, one `"...: no accepted
reading"` portion, one revision with only `OPEN_BOUND`.

**On the untested backend field** (dispatch question): as shipped, `revision.indeterminate_reasons` is a thin
read-through of the cited assessment's segments and is exercised only by the live run, so no test pins its
shape, its `source_open` gate, or that it reads the *selected* revision's assessments rather than the
latest's. Once it carries a truth-bearing classification (R2) it needs a dedicated backend test; that test
belongs in the R2 fix. Without R2 it would be a low carry.

### Carries (not blocking)

- **C7 (doc)** Guide step 8 says "the three Dispatch day addresses"; `links` prints four (10-06 belongs to
  step 1). Trivial.
- **C8 (low, residual)** "No record gaps or conflicts were found over this period" sits next to a Not
  confirmed lead. I did not trace whether it shares R2's blind spot for segment-level gaps; check it while
  fixing R2.
- C5 and the phase 1-2 carries remain as the packet states.

## What holds (verified live)

- F02 headline, stop record and "Open · out of date" heading agree.
- Version addresses: every printed `?revision_id=` opens that version and marks it "(shown)"; earlier versions
  lead with "Earlier version N of M" and link the latest.
- F05 latest: "No longer supported ... does not mean the generator was repaired or that money was saved."
- F03 recurrence link says it does not imply the earlier Finding is open; F06 joined leads with "Joined into
  an earlier Finding" and links the canonical one.
- Dispatch days carry honest states, with no false "no Finding".

## Ready for the owner walkthrough?

Not yet. Fix R1 (and preferably R2 in the same small round), update guide step 4, and have a fresh reviewer
check the F05 v2 sentence live. Nothing else stands in the way of the walkthrough.
