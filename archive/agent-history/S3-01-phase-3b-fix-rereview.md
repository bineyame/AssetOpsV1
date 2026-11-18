# S3-01 phase 3b fix round: re-review (fresh Claude reviewer)

A fresh Claude reviewer (Opus) produced this. It is independent of the Implementer and of the earlier 3b reviewer. The diff reviewed is `e7c4a85..dac94db` on `task/S3-01-dispatch-assessment`, made up of `1008bb8` (code) and `dac94db` (guide, Q19, packet, evidence). Nothing was fixed, merged or committed.

## Verdict

**Accept.** B1, B2, C1, C2, C5, C6 and C7 are closed, and nothing has regressed. No new blocking finding. Two low carries are listed below. C3 and C4 stay carried as agreed.

**S3-01 is ready for the owner walkthrough.**

## Checks I ran

| Check | Result |
| --- | --- |
| `npx.cmd tsc --noEmit -p .` | exit 0 |
| `npm.cmd test -- --run src/sites/__tests__/performanceDispatch.test.tsx` | 20 passed |
| `npm.cmd test -- --run` (full vitest) | 54 files, 1290 passed. It ran in this session, so the expected sandbox failure did not occur. |
| `tools/check-architecture.ps1`, `tools/check-agent-workflow.ps1` | both passed |
| `tools/s3_dispatch_walkthrough.py prepare` | Tree built from `dac94db`. Comparison PASSED (empty set). Cutover permitted. FAILED 10-07 and PENDING 10-05 staged. Printed "Prepared". |
| `serve` on 8820, plus Vite on 5320. Pages rendered in headless Chrome (CDP), with innerText and full-page screenshots in my scratchpad. | Results below. Both were stopped afterwards. 8820, 5320 and my CDP port 9377 are free. The owner's servers and `var/` were not touched. |

Not re-run, so these remain unverified by me:
- `npm run build`;
- the backend pytest suite (the fix round touched no backend code; only `tools/s3_dispatch_walkthrough.py`);
- `tools/s3-dispatch-evidence.mjs`.

The packet's 32/32 is the Implementer's run. Its committed evidence file differs from before only in the screenshot directory.

## What the real UI showed (walkthrough data)

- **7 Oct (B1).** The status line reads "Reassessment failed … not current". A "Note supplied with the demonstration data" box sits directly below it on the Overview, with no period to select. The box says the notes are not accepted records and do not change the result, and it carries the out-of-order fault-fixture line with "(2 records)". The note also shows in Analysis. 6 Oct shows its own fault-fixture note.
- **Battery reserve row (B2).** On every day the row reads "Reported battery reserve level (the reserve used comes from site settings) | Not set up". It no longer contradicts "Battery at its reserve level" on 2 Oct.
- **Selected block, 2 Oct block 3.** It reads: "Block 04:30 to 04:45 UTC: Needed · Site demand 49 kW · Battery at its reserve level." The records table shows quality "Good" and times as "2026-10-02 04:30". The Overview has no stored-result id.
- **Selected block, 1 Oct block 3 (C2).** It reads "Some readings this block needs are missing or limited; the Analysis view lists them." No model strings appear.
- **5 Oct, stale (C5).** It reads "526 accepted records exist for this day, but no single series of them was chosen, so none is used for a result".
- **1 Oct (C5).** It reads "A measurement this assessment needs is not set up for part of the day (2 places)".
- **Stale or failed day cards (C7).** On walkthrough data, no stale or failed day has intervals, so the cards do not render on 4, 5, 6 or 7 Oct. The marking is covered by the test at `performanceDispatch.test.tsx:312-313` (banner, plus 4 cards marked `data-stale`). I read the code at `PerformanceDispatch.tsx:383-401`, and it is correct.
- **Guide links.** All of them render the described state:
  - 2 Oct: 1 h 30 min Needed and 4 h Possibly avoidable;
  - 9 Oct: at least 7 h 30 min Needed, partly bounded;
  - 1 Oct: Cannot determine, 5 h 30 min;
  - 5 Oct: Out of date, overlapping series;
  - 7 Oct: Failed, with the note;
  - 1 Jan 2027: Not assessed;
  - `view=analysis`;
  - step 8: a 2 Oct revision opened on 5 Oct reads "a stored result that is not the current one for 2026-10-05".

## Findings closed

- **B1: closed.** `PerformanceDispatch.tsx:283` renders the window `demo_annotations` independently of any selection. The records panel de-duplicates against them (`:701-702`). Tested. The guide limit and Q19 are corrected and now match the data.
- **B2: closed.** The label is changed in `dispatchWords.ts:99`. Tested.
- **C1: closed.** `CAPABILITY_SHORTFALL`, `NO_COHORT`, `OPERATOR_OVERRIDE` and `MINIMUM_RUNTIME` are mapped, and the dead `LOAD_ABOVE_CAPABILITY` entry is removed.
- **C2: closed.** The Overview shows one plain "missing or limited" line, `qualityWords`, UTC stamps, and no revision id.
  - On the closed-cutover path, the Overview gives one plain sentence. The codes, lineage and reason appear only in Analysis.
  - This path is unreachable on walkthrough data, so I verified it by test and code.
- **C5: closed.** Seen in the UI (above).
- **C6: closed.**
  - `prepare` now checks the prerequisites before doing any work, and raises `SystemExit` on a non-zero comparison exit.
  - `performance_migration.main` returns 1 unless the outcome is PASSED and 2 on errors, so the new check is meaningful.
  - The guide lists the prerequisites and what to do on failure.
- **C7: closed** (test and code; not reachable on walkthrough data).

## Plain-language judgement (D-2026-10-04)

The default Overview reading is plain on every walkthrough day. No model strings, status codes or ids reach it. The Analysis view keeps the technical detail, such as `SELECTED_UNIQUE`, the status reason with the job id, and digests, which is what the decision allows.

## New findings (all carry, low; none blocks)

- **N1 (carry, low, pre-existing).** A Not assessed day (2027-01-01) still says "0 accepted records behind this day's result" and "No limitation is recorded for this day's result".
  - Where: `PerformanceDispatch.tsx`, the `CoveragePanel` note and `LimitationsPanel`.
  - The guide says the page "shows no zero"; the totals indeed show no zero, but this sentence does, about a result that does not exist.
  - Fix later: on UNASSESSED, say "No records are used because no assessment exists" and omit the limitation sentence.
- **N2 (carry, low).** The demonstration note is quoted verbatim from the manifest. On the default reading that puts terms such as "battery SOC", "centrally accepted", "authenticated Batch V2" and "not gateway-sealed" in front of the owner.
  - Quoting verbatim is defensible, because it is labelled manifest provenance and paraphrasing it would alter that provenance.
  - A one-line plain gloss, such as "These records are deliberately faulty test records", could be added later.
- **Observation, not a finding.** 6 Oct shows both "Reassessment failed" and "A reassessment of this day has not finished yet", because it is failed and also has a job outstanding. That is accurate to the data. The guide mentions 6 Oct only under its limits, so the owner may ask about it.

C3 and C4 (backend efficiency and read consistency) remain carried, unchanged.

## Owner walkthrough readiness

Ready. Run `prepare`, then `serve`, then Vite on 5320 as the guide says. `assetops_s3walk` and the private tree under `%LOCALAPPDATA%\AssetOps\s3-dispatch-walkthrough` remain from my `prepare` run, and `prepare` recreates them.
