# Review: POLISH PB-2 (Kobo board, verification page, display codes, Technical details)

Reviewer: fresh Claude reviewer, independent of the implementer. Date 2026-11-01.
Branch `task/POLISH-PB-2-kobo-board`, head `2fd52e67a`, worktree `AssetOpsV1-polB2`. Base main `1c0ef34c3`.
Diff reviewed: `git diff 1c0ef34c3...2fd52e67a` (77 files, +884/-247).
Spec: plan2 `.agent/build-sheet-POLISH.md` §1.1, §3/§3.1, §5 PB-2, §6, §7, Addenda 3, 4, 5, 7 and 8.

## Verdict: ACCEPT, with M1 fixed on the branch before merge

The slice delivers what the sheet asks for:
- the §3.1 Kobo and verification rows;
- the §1.1 money zero;
- `displayCode()` at render;
- the Technical details mechanism.

The tests were not loosened. `mini.py` changes string constants only. One Medium finding is a UI/UX defect in the new
`WorkedOut` nesting: in three places it adds a disclosure that, when opened, contains nothing but another disclosure.
It is small and local, so fix it on the branch. The Lows can be fixed in the same round or logged.

## Findings

### M1. "How this was worked out" with no plain lines is an empty extra click (UI/UX; not an acceptance-criteria gap)
- **Where.**
  - `frontend/src/ui/TechnicalDetails.tsx:66-81` (`WorkedOut`).
  - The calls that pass no `lines`: `frontend/src/sites/SiteActionVerification.tsx:662` (the verification status
    strip) and `frontend/src/sites/SiteWindowOverview.tsx:915` (`window-money`).
  - `SiteWindowOverview.tsx:1016` (`window-finding-choice`) does the same whenever `choiceLines()` returns null, which
    happens for any rule other than `LATEST_RECORDED_REVISION_OF_EACH_CANONICAL_FINDING`.
- **What.** When `lines` is absent, `WorkedOut` still renders the "How this was worked out" disclosure. Opening it shows
  only a second closed disclosure, "Technical details".
  - On the money panel the path is three levels deep: "How this estimate was made" > "How this was worked out" >
    "Technical details". The middle level carries no information.
  - On the verification page the strip's "How this was worked out" link now opens to a single "Technical details"
    summary. Before this slice it opened straight to the references.
- **Why it matters.** The packet lists this under residual risk and asks for a judgement against the v70 mock and the
  owner's modern UI/UX bar. Hiding ids behind a clear label is the ruling (Addendum 8 Q5). An intermediate disclosure
  that only reveals another disclosure is a dead click, and the brief's standing UI bar rules that out. The mock has no
  such pattern; its detail is at most one fold deep. The three-level nesting is justified only where the middle level
  shows plain lines, as on the freshness strip ("The reading source is active." and "Access: …") and on the Finding
  list (choice rule and "List built …").
- **Fix.** In `WorkedOut`, when there are no plain lines and no `extra`, render `TechnicalDetails` directly with the
  references and no outer "How this was worked out" wrapper. The alternative is to call `TechnicalDetails` +
  `TechnicalReferenceList` at those three sites. Either way, keep the `data-exact-references` hook if tests rely on it,
  or update those tests. Add one test in `technicalDetails.test.tsx` that pins the no-lines form.

### L1. Day-line wording for missing coverage reads as a clipped clause (builder copy, deviation 2)
- **Where.** `frontend/src/sites/SiteWindowOverview.tsx:373,376`.
- **What.** The rendered sentence is "Checked: 1 period of generator use, measured inputs not recorded for this day".
- **Assessment.** The meaning is honest and avoids "not available yet", which the missing-claim guard reserves for
  registered gaps. That is a correct reason not to use that phrase. A client can understand the line, but the clause
  after the comma reads like a fragment.
- **Fix.** Suggested wording: "…; the measured inputs for this day were not recorded". This is a preference, not a blocker.

### L2. "Generated test data" still appears on the verification strip next to "Verified on example data"
- **Where.** `frontend/src/ui/productWords.ts:230`, `REGISTERED_SIMULATION: "Generated test data, not field readings"`.
  The `kobo-verification` capture renders it in the status strip as "Source: Generated test data, not field readings".
- **What.** The same strip now says "Verified on example data · benefits the mini-grid operator". The source label
  contradicts the new claim wording.
- **Why it is only Low.** The string is not in §3.1, and the strict gate does not count it. §3.1 renamed the same
  state in `sourceProvenance.tsx` to "Example data", so this is a consistency leftover.
- **Fix.** Align it to "Example data, not field readings", here or in PB-3. The file is shared, so check its other uses.

### L3. Small code tidiness in `SiteWindowOverview.tsx`
- **Where.** `:29` and `:311`, plus the doubled blank lines after `MoneyAction`.
  - `:29`: a blank line was left in the `../ui` import list where `ExactReferences` was removed.
  - `:311`: a redundant `{( … )}` wrapper around the freshness `<p>`.
- **What.** When the source is open and the state matches the status bar, that `<p>` now renders empty but keeps its
  margin. No behaviour is wrong.
- **Fix.** Render the `<p>` only when it has content.

### L4. Leftover "Finding" capitals in the Kobo money and next-step panels (not counted by the gate; for PB-3/PC awareness)
- **Where.**
  - `SiteWindowOverview.tsx:854`: "One Finding overlapping 29 Oct 2026".
  - `:1066`: "Review the Finding for this day".
  - `:1076`: "Open the Finding".
- **What.** These are not §3.1 rows. Because the strict gate does not flag them, the builder-latitude rule did not
  require changes. They sit next to the rewritten lower-case copy ("main finding for this day", "Start from the
  finding…"). Note them for the PC copy pass. They do not block.

## Check-by-check (dispatch items 1-8)

1. **Technical details.**
   - `captures.json` for `kobo-board-S-open` at both widths has 0 counted id hits.
   - Its `exempt_hits` match the packet: in `data-technical-details`, 255 uuid, 2 enum, 2 raw timestamp, 4 snake_case
     and 3 product-term hits; 5 `source-reference`; 1 `user-owned`; 10 `lab`; 1 time-zone note.
   - The `=lab` hits are the Simulator Lab placeholder copy ("Open in Simulator Lab", "…scenarios, runs and run
     setup…"), not Site names. They predate PB-2 (PB-0 baseline), so there is no Addendum 5 violation by this slice.
   - Only `[data-technical-details]` hides ids. The new `Disclosure technical` prop is the only place that sets it.
   - What is hidden is ids, codes and raw values, always beside a plain line:
     - SiteAction History: "Nothing was changed; still pending." plus the configuration-changed sentence. "Change
       record" stays as a visible link.
     - `SourceProvenanceRecord` id lists, with the accepted-records count still visible.
     - Verification DigDeepers.
   - I found nothing a client needs inside a Technical details region.
   - Nesting: see M1.
2. **mini.py.** The diff touches `GAPS_NO_READINGS` and three `FINDING_TITLE` values only. MERGED and the fallback are
   unchanged and there is no logic change (Addendum 8 Q1). The titles match Addendum 4 exactly, and
   `findingWords.LIFECYCLE_WORDS` matches them.
3. **Wording.**
   - Every §3.1 Kobo and verification row I checked against the sheet, as amended by Addendum 4, matches the code and
     the `kobo-board-S` and `kobo-verification` captures.
   - Remaining old text on the captures is server-sourced and is correctly listed as awaiting PA-2a or PA-3: "0.00 USD
     exposure in this hour", the old gap footer, "Generator support merits review", "Verified on test data", "Modelled
     change after the trial", and `ACT-000001` inside board sentences.
   - Q2: the essential-service words are exact. The roleWords fallback capitalises the first letter, and
     `pb2KoboWords.test.ts` pins it.
   - There is no run, ran or running in the new copy.
   - Builder copy: acceptable apart from L1.
4. **Display codes.** Spot-checked:
   - `SiteAction.tsx` (h1 and Overview);
   - `GlobalPreventive.tsx:79`: the display code is in the title, while `CellDisclosure row={row.code}` and the
     `data-*` attributes keep the stored code;
   - `GlobalIncidents.tsx` and `GlobalMaintenance.tsx` titles;
   - `SiteWorkActions.tsx`: the code cell changes, the hrefs and `data-` attributes do not;
   - `SiteRecommendation.tsx`: link text only, `aria-busy`/`data-action-command` untouched;
   - `estate/actionIndex.tsx`: the row `data-estate-action` keeps the id;
   - `OperationalRecords.tsx` and `WorkRequestRecord.tsx` link text.

   All are render-only. I found no aria-label or `data-*` attribute that was changed. `displayCode` matches only
   `^[A-Z][A-Z0-9]*-[0-9]+$`, so Site codes with two hyphens, such as `COLD-LAB-001`, are not affected, and `KOBO-001`
   is unchanged by the padding.

   Side note for PB-3, not a PB-2 finding: `estate/EstatePortfolio.tsx:435` still prints `{r.action_id}` and other
   UUIDs in the Portfolio progress drawer list, outside any Technical details region.
5. **Verification claim label.**
   - The v69 mock's verification screen (`index.html:499`) puts the outcome badges in the status line and has no
     separate claim paragraph between the strip and the metric header. Moving the claim into the strip as a
     `status-strip__item` therefore matches the mock's structure. It is not a test-driven shortcut.
   - Behaviour is preserved: `verdict` is non-null only when `current` is non-null (`SiteActionVerification.tsx:288`),
     so dropping the `verdict !== null` guard changes nothing.
   - `w1f4ActionStructure` passes, and its only edit is `ACT-000051` → `ACT-051`.
6. **Test updates.** I read every changed assertion line. All are string or display-code updates, or stronger checks:
   - the day-line test now asserts the full lead;
   - there is a new P-06 zero test and a non-vacuity test for the Technical details region.

   Three assertions changed in form, and none is looser:
   - `data-overview-finding-shown="all"` is now `""`, because the §3.1 row deletes "Showing all n.";
   - the row regex now checks the new date form instead of `version \d+`, which the §3.1 row removes;
   - the siteDetail and siteConfiguration timestamp checks now assert the formatted time appears exactly once.
7. **"Valid from".** `formatDayTime` follows the §3 times rule (no ISO strings), and the raw value was a counted hit on
   `-open`. The field is a non-null `string` (`siteViewModel.ts:146`), and unparseable input gives "Time not available
   yet". This is justified and is a time-only change.
8. **No data tuned.**
   - No fixture data values or producer data were changed.
   - `tools/demo_combined_finish.py` changes only the `GAPS_TEXT` expectation string, to match `GAPS_NO_READINGS`.
   - `findingIndexFixtures.ts` changes only a title string.

## Checks I ran (head `2fd52e67a`)

- `npx.cmd tsc --noEmit` in `frontend`: exit 0.
- Scoped vitest, 11 files, all passed (310 tests, 33 s):
  - `displayCode`, `technicalDetails`, `pb2KoboWords`;
  - `s5SiteWindowOverview`, `s502OverviewFindingList`;
  - `w1f4ActionStructure`, `siteActionVerification`, `claimLabel`, `sourceProvenance`, `siteAction`;
  - `w1f3PanelGuard`.
- The other 24 changed test files: all passed (782 tests). These cover the cold, EV, work, estate and shell suites.
- `src/test` (`panelStructure`, `w1f3PanelGuard`): 35 passed.
- Backend, with the plan2 venv and `PYTHONPATH` set to this worktree. I confirmed `mini.__file__` is the worktree's.
  - `test_idx_gaps_board`, `test_out_b2_mini`, `test_out_b2_vocabulary`, `test_out_b1_board` and `test_link_lineage`:
    97 passed.
  - `tools\run-host-tests.ps1 -- backend/tests/test_idx_gaps_postgres.py` on `assetops_test`: 7 passed, 61.9 s.
- `tools\check-all.ps1 -Python <plan2 venv>`, with no execution-policy override: all 12 guards passed. This includes "Missing-claim orphan scan", "Mock deviation labels
  and client vocabulary", "Navigation truthfulness" and "Agent workflow". The estate guard self-tests took 7 min 40 s
  of the run.
- Not run: the full vitest suite, `npm run build`, browser captures and `-Tier all`, all excluded by the dispatch. I
  cite the implementer's full run as reported: 150 files, 3,580 passed, 321 s, on `abbe8cf03`. The only commit after it
  is `2fd52e67a`, which adds the packet only. I did not rerun the full suite or the build, so they are unverified by me.
  I reviewed the captures from the packet's `captures.json` and two PNGs (`kobo-board-S-1440`, `kobo-verification-1440`).

## Merge risk

- **Against current main `c4a39b1dc`** (`git merge-tree --write-tree --name-only 2fd52e67a c4a39b1dc`):
  - one conflict, in `.ai/CODE_STATE.md` (record text only);
  - `backend/tests/test_out_b2_mini.py` and `.agent/mock-departure-register.md` auto-merge;
  - `site_outcomes/mini.py` merges cleanly; PA-2b's edits do not overlap the PB-2 constants.

  Rebase PB-2 on main, resolve `CODE_STATE.md` by keeping both entries, and rerun the backend files above, which share
  `mini.py` with PA-2a/PA-2b.
- **Against PA-3** (`task/POLISH-PA-3-producers-rebuild`, `5e0c00970`):
  - `merge-tree` reports the same `CODE_STATE.md` conflict;
  - `tools/demo_combined_finish.py` auto-merges, because PA-3 edits `co1()` and the imports and PB-2 edits `GAPS_TEXT`.

  It still carries semantic order risk:
  - `GAPS_TEXT` must equal the `mini.GAPS_NO_READINGS` that the rebuild serves.
  - If PA-3 builds and captures `assetops_polish_full_test` before PB-2 merges, the rebuild serves the old gap text.
    The PA-3 captures then cannot prove the PB-2 "BE" rows (`GAPS_NO_READINGS`, `FINDING_TITLE`).
  - If PB-2 merges first and PA-3 does not rebase, the PA-3 finish check runs the old `GAPS_TEXT` against the new
    server text and fails.

  Recommendation: merge PB-2 first. Have PA-3 rebase onto it before its rebuild, so that the PA-3 screen-check list
  includes the gap line and the Finding titles.

## Residual risk not named in the packet

- `WorkedOut` replaced `ExactReferences` on several screens, so tests or tools that read `[data-exact-references] dl`
  or row content directly now find the values one disclosure deeper. The full suite was green on the implementer's
  run. Browser tools such as `layout-evidence` were not rerun for the nested form.
- The verification strip gains an item (the claim label). At 390 px it wraps inside the strip. The capture shows no
  overflow, but I saw only the 1440 PNG.
