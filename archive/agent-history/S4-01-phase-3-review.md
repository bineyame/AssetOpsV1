# S4-01 phase 3 review (fresh Claude reviewer)

Produced by a fresh Claude reviewer that did not author S4-01. Scope: phase 3 diff `0f4808b..4c499b6`
(`6d6079c`, `e64d13a`, `4c499b6`) on `task/S4-01-finding-identity`, plus a check that phases 1-2 did not regress.
No code was changed, merged or committed by the reviewer.

## Verdict

**Accept with findings fixed on the branch.** The Finding screen, routes, reload pinning, version list, Dispatch
day links, C7 audit-only lead, merge/earlier-version leads and the withheld money/Action content are sound, and
I reproduced the evidence run (36/36) on a fresh producer run. But two pieces of default-view wording are false
for the fixture the owner will look at (B1, B2), and the walkthrough tooling points the owner at the wrong
addresses in two places (B3). Separately, the standard no-Postgres backend command fails at collection (B4,
pre-existing from phase 1/2). All are small wording, tool or test-guard fixes.

**Ready for the owner walkthrough: not yet.** It is ready once B1-B3 are fixed (B4 must be fixed before closeout) (a small Sonnet fix round plus a
fresh Claude re-review of that round). Carries C1-C6 can go to the backlog.

## Checks I ran (results as observed)

| Check | Result |
| --- | --- |
| `tools/check-architecture.ps1` | `Architecture check passed.` |
| `tools/check-agent-workflow.ps1` | `Agent workflow check passed.` |
| `npx.cmd tsc --noEmit` (frontend) | exit 0 |
| `npm.cmd test` (frontend, full) | 55 files / 1320 tests passed. The sandbox esbuild failure did not occur here. |
| `npm.cmd run build` | built (chunk-size warning only) |
| `siteFinding.test.tsx` focused | 26 passed |
| `tools/s4_finding_cases.py run` (clean fixture run, code `4c499b6`) | 0 check failures, 11 Findings / 30 revisions, gateway case 102 cited IDs, 0 outside gateway batches, `VERIFY PASSED`, replay wrote nothing |
| `tools/s4_finding_walkthrough.py prepare` | comparison PASSED (empty-set, zero-inventory), cutover permitted, 10-09 staged PENDING |
| `serve` (8840) + Vite (5340), live API probes and `node tools/s4-finding-evidence.mjs` | `36/36 claims passed` on the new run's IDs; screenshots in `%TEMP%\rev-p3-ev` |
| `.venv\Scripts\python.exe -m pytest backend/tests -q` (default, no `ASSETOPS_TEST_DATABASE_URL`) | **collection error**: `test_s4_finding_store_postgres.py:80` `NameError: name 'dispatch_v3' is not defined` (see B4). With the two S4 Postgres files ignored: `1766 passed, 118 skipped`. Phase 3 has no backend/host/gateway/simulator/contracts change (that diff is empty), so I did not rerun the Postgres 1893 / host / gateway / simulator suites; those numbers are the Implementer's, unverified by me. |
| `tools/layout-evidence.mjs` | not run (same blocker as Q28). Packet records it as not run with its precondition, which is correct. |

Servers stopped afterwards; 8840, 5340, 9343 and 8763 are free. The owner's ports and `var/` were not touched.
`assetops_s4cases` and `assetops_s4walk` were recreated by the producer/prepare run (both are the tools' own DBs).

## Findings

### B1 (block before walkthrough): "Not confirmed" wording asserts missing records that the page also says do not exist

`frontend/src/sites/findingWords.ts:22-23` (UNCONFIRMED sentence), `SiteFinding.tsx:309` ("Cannot determine" card
note "Records needed were missing or unclear"), `SiteFinding.tsx:299` ("The latest assessment of that period counts
no possibly avoidable time").

Live F05 version 2 (`3aa639ac…?revision_id=<v2>`): the selected S3 interval revision `46197a27…` is INDETERMINATE
with reasons "PV available plus PCS discharge capability covers load with 10 % headroom; reserve 20.0 %
(Foundation revision e41a0085…)" - a changed battery reserve setting made the margin undecidable. Role coverage is
complete, the revision's `limitations` are empty, and the page itself says "No record gaps or conflicts were found
over this period." The same screen then says it "cannot confirm the earlier result, because records it needs are
missing or unclear", and the card says "Records needed were missing or unclear". Both cannot be true; for this case
the first is false. The task allows Indeterminate for documented modelling uncertainty, so the wording must not
attribute every Indeterminate to missing records. The "counts no possibly avoidable time" sentence also reads like
a negative result for a state that is "cannot decide either way".

Why it matters: this is walkthrough step 4, and the guide (`.agent/S4-01-owner-walkthrough.md` step 4) repeats
"records needed were missing". An owner reading the screen gets two contradictory explanations.

Fix: say "The latest assessment of this period cannot confirm the earlier result" without a cause, or derive the
cause from the revision's limitations (missing/conflicting records only when a limitation says so; otherwise
"the available margin could not be decided under the current settings" or similar). Make the card note neutral
("Could not be decided"). For UNCONFIRMED, replace "counts no possibly avoidable time" with "cannot decide whether
any of it was possibly avoidable". Update guide step 4. Add a test with an UNCONFIRMED revision that has no
limitations.

### B2 (block before walkthrough): "The generator stayed on from X to Y" is false when a stop was bridged

`SiteFinding.tsx:295-296`. Live F02 (`59ee63d2…`, walkthrough step 5): the headline reads "The generator stayed on
from 2026-10-08 23:20 – 2026-10-09 00:55 UTC", while "What limits this conclusion" says "The generator stopped once
for 20 minutes or less (first at 2026-10-08 23:50 UTC)", and the block bar shows the gap. The headline claim is
contradicted by the page's own stop record.

Fix: when `claim.continuity` contains stops, word it as "The generator ran between X and Y, with N short stop(s)"
(or "ran during"), and keep "stayed on" only when no stop is bridged. Add a test.

### B3 (block before walkthrough): walkthrough tool and guide point the owner at wrong or missing addresses

1. `tools/s4_finding_walkthrough.py:157-158` prints "Dispatch day with no Finding (assessed): …?day=2026-10-25".
   Live, `finding-windows/2026-10-25` is `NOT_ASSESSED`. The packet and guide step 8 correctly say the fixture has
   no fully assessed no-Finding day, so the tool's label contradicts both and would show the owner the opposite of
   what it promises. Fix: relabel it ("a day with no assessment") or drop it, and add the 10-19 NOT_DETERMINABLE
   and 10-07 NOT_ASSESSED addresses that step 8 uses.
2. Guide step 4 says "The version 2 address reads Not confirmed", but `links` prints only version 1 for every
   Finding (`s4_finding_walkthrough.py:153-155`). The owner has no version 2 address. Fix: print every version (or
   at least F05 v2), or reword step 4 to "open Version 2 in the Versions list".

### B4 (block before closeout/merge, not before the walkthrough): standard backend run fails to collect without Postgres

`backend/tests/test_s4_finding_store_postgres.py:80` uses `model=dispatch_v3` as a default argument at class
definition time, but `dispatch_v3` is only imported inside the `if URL:` guard (line 31). Without
`ASSETOPS_TEST_DATABASE_URL` the module raises `NameError` during collection, and `test_s4_finding_read_postgres.py`
imports it, so the brief's standard `pytest backend/tests -q` errors out before running anything. Present since
phase 1/2 (same line at `0f4808b`); missed because every packet ran with the Postgres URL set. Fix: default
`model=None` and resolve inside `__init__`, or import `dispatch_v3` unconditionally; rerun the default command.

### Carries (not blocking the walkthrough)

- **C1 (low, test helper regression)** `frontend/src/test/settled.ts:22`: the closing `\.` of the LOADING regex
  became `.` when `the Finding` was appended (`…|the Finding)./`). Every loading phrase now matches with any
  trailing character, loosening the helper for all suites. Fix: restore `\.`.
- **C2 (low)** Records count wording: "N accepted records support the counted blocks" (`SiteFinding.tsx:481,604`)
  is shown for UNCONFIRMED/NO_LONGER_SUPPORTED revisions with 0 counted blocks (live F05 v2/v3: 78 records, 0
  avoidable minutes). Word it as "records this version cites" when nothing is counted. (Can be folded into the B1
  fix round cheaply.)
- **C3 (low)** Lead for an out-of-date latest version reads "Open" in the heading with "Out of date" only in the
  chip and second sentence (live F02). The lead order puts closed/merged/earlier first as required, but STALE /
  FAILED / PENDING / NOT_ASSESSED could carry into the heading ("Open · out of date") to match "lead with the
  limit".
- **C4 (low)** On an earlier pinned version the lead stacks "A later version replaces this one" and the
  currentness sentence "You are viewing an earlier version… A later version replaces it" (duplicate), and the
  UNCONFIRMED sentence says "The latest assessment" on a version that is not latest.
- **C5 (low)** `WhereToLook` pins only the first day's Dispatch link to the primary interval revision
  (`SiteFinding.tsx:470`) without checking the primary revision's day. Correct for every live case (primary day =
  first day for F02/F03/F04/F06), but a late earlier record that moves the first ON before midnight would pin day 1
  to another day's revision. Use the primary assessment's `window_start` day.
- **C6 (doc)** `.agent/S4-01-phase-3-evidence-run.txt` ends "screenshots in …/scratchpad/evidence", while the packet
  and guide name `%LOCALAPPDATA%\AssetOps\s4-finding-walkthrough\evidence`. The LOCALAPPDATA copy exists; align
  the text.
- Existing carries C5/C6/C8/C9 from phases 1-2 remain as the packet states; nothing in phase 3 regresses them.

## Truthfulness review (what holds)

- Lead order: audit-only (C7) > merged > earlier version > lifecycle, as specified; C7 test plus mutation proof
  present. Merged Findings are hidden on the Dispatch day; the joined Finding leads with "Joined into an earlier
  Finding" and links the canonical one (live F06).
- Possibly avoidable / needed / cannot determine are separate cards; whole-period avoidability is disclaimed;
  fuel/cost, "What to do next", history, money and actions are typed "Not yet available". No priority or
  confidence value is invented (Q27).
- NO_LONGER_SUPPORTED says not a repair or saving; UNCONFIRMED/REOPENED after closure say not a new issue; the
  recurrence link (live F03) says the earlier Finding is not implied open; the not-established repeat is named only
  when an earlier Finding exists (Q26).
- Routes: `/sites/{site}/findings/{id}[?revision_id=]`; reload keeps the exact version and `?portion=`; refusals
  401/403/404/409/503 are named states with no Finding content.
- Dispatch day: FINDINGS_RECORDED links; NOT_DETERMINABLE, FINDING_MATCH_PENDING, NOT_ASSESSED, STALE carry reasons
  and no false "no Finding" (live 10-06, 10-07, 10-09, 10-19, 10-21).
- R1 gateway labelling: the gateway case annotation and the template-runtime basis are named; fault-fixture cases
  are labelled as not the ordinary path.

## Questions 5 (Q25-Q30)

All defaults are safe; none needs the Architect. Q25 leaves the developer text "interval assessments are not
Findings (S4)" visible in Dispatch Analysis - acceptable there, retire later. Q28 is correctly recorded as not run
with its precondition. Q30 is fine for pinned versions.

## Residual risk not named in the packet

- The plain-language vocabulary scan cannot catch statements that are grammatical but false for the data (B1, B2);
  the state tests use synthetic bodies whose limitations do not exercise those combinations.
- Narrow (390px) records tables clip to a scroll region (Quality/Record columns off-screen); no page-level
  sideways scroll, so not a layout failure, but the owner may need to scroll the table.
