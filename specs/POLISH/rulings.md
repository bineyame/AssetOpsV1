## 2. P-04 ruling: MOCK DEVIATION labels on client screens

**Ruling.** Client screens never show `MOCK DEVIATION` text. The register stays the record. Each live label stays in
the DOM, tagged, and renders only in **review mode**.

- **Mechanism.** One rule in `frontend/src/ui/mock-deviation.css`, which every label already loads or which gets
  imported once from `frontend/src/main.tsx`:
  `:root:not([data-review-labels="on"]) [data-mock-deviation] { display: none !important; }`
  - This hides all 17 inline labels and the shared `MockDeviation` component (`frontend/src/work/globalWorkParts.tsx:102`),
    which all carry `data-mock-deviation`.
  - `display:none` also removes them from the accessibility tree, so screen-reader users get the client view too.
  - The existing R453 width rule still applies inside review mode.
- **Review mode switch.** New file `frontend/src/ui/reviewLabels.ts`, called first in `main.tsx`:
  - `?review=labels` sets `sessionStorage["assetops.reviewLabels"] = "on"`; `?review=off` removes it.
  - Then set or remove `document.documentElement.dataset.reviewLabels = "on"`.
  - Wrap every storage call in try/catch. With no storage, the URL parameter alone decides for that page load.
  - Default is off. Nothing in the UI links to review mode.
- **Tests.** Vitest (jsdom) does not apply CSS, so existing label assertions stay valid. Add
  `frontend/src/ui/__tests__/reviewLabels.test.ts` for: param on/off, storage failure, and the dataset attribute.
  Also assert that the CSS file contains the hide selector (import with `?raw`).
- **Register rule change.** Replace the first sentence under "Post-W6 audit Architect rulings" in
  `.agent/mock-departure-register.md`, which is `Each open D1/D2/D4/D5/D6 row must show MOCK DEVIATION Dn beside the affected element…`, with:
  > Each open D1/D2/D4/D5/D6 row whose departure is visible on a screen has a label element beside the affected element
  > carrying `data-mock-deviation="Rnnn"` and the text `MOCK DEVIATION Dn (Rnnn)`. The label renders only in review
  > mode (`?review=labels`); client mode, the default, hides it (POLISH §2, 2026-11-01). The register remains the record.
  > Reviewers check labels in review-mode captures. A departure without a tagged label, or a label visible in client
  > mode, is a High finding.
  - Rows that today are labelled only in code comments (for example the `// MOCK DEVIATION` comments) are unchanged.
- **Guards.**
  - New guard 12 in `tools/check-all.ps1`, "Mock deviation labels and client vocabulary", runs
    `node --test tools/checks/test_mock_deviation_labels.mjs`. Its scanner `tools/checks/mock-deviation-labels.mjs` checks three things:
    - (a) every non-comment JSX text containing `MOCK DEVIATION D` in `frontend/src/**/*.tsx` (tests excluded) sits in
      an element whose opening tag has `data-mock-deviation=`, or is rendered by the `MockDeviation` component;
    - (b) every `data-mock-deviation` id exists as a row in the register;
    - (c) the hide selector is present in `mock-deviation.css`.
    - Fixtures: one passing file, one untagged label, one unknown id, and the missing CSS rule.
  - `tools/demo-combined-evidence.mjs` in client mode must record zero `MOCK DEVIATION` hits (strict gate, PB-0).
    `DEMOB_REVIEW_LABELS=1` captures in review mode, for reviewers.
- **ROLE_CONFIG.** No change. Its MOCK DEVIATION rule is about rulings, not screens.

---

## 6. Rulings made here and owner questions

The Architect decided these under the delegated-decision rule. Each is logged for the owner and confirmed at the walkthrough:
- **D-1, "Demonstration data" banner (DEMO-COMBINED §9 Q3): yes.**
  - A one-line, quiet, app-wide banner under the topbar: "Demonstration · example sites and records prepared for this walkthrough".
    It is neutral tone, 12 px, not dismissible, with `role="note"`.
  - The per-Site badge "Demonstration data · {code}" becomes "Example data".
  - This is a D2 row, R651. It is cheap (0.75 unit), and it lets the work records stay unmarked honestly.
- **D-2, OUT-E L4: an INEFFECTIVE trial never shows a modelled money line.** The Cost row then reads "The trial did not fix
  the problem, so no cost change is credited to it" (PA-1). This matches Assure (`mini.py:697`, VERIFIED only) and the
  "no change credited to the trial" rule.
- **D-3, P-08: no backdating.** The Depot Action stays dated at build time. It shows on Work › Actions, and the board register row and runbook line explain it.
- **D-4, times:** one "All times UTC" note per page, with no per-time suffix. (GOV.UK date and time guidance; NN/g redundancy heuristic.)
- **D-5, Lab Site names:** use the mock names, "GreenHarvest Cold Room" and "Depot Charging Hub", in the demo build only.

**Owner question (one):**
- **Q1. Kobo's fuel cost reads zero.**
  - On the overuse days the generator was switched on but delivered no power, because solar and the battery carried the
    load. The cost model counts only fuel for power delivered, so the honest figure is zero.
  - For this demo the screen will say "No fuel cost estimated: the generator was on but delivered no measured power".
  - **Recommendation:** keep that for the walkthrough. Afterwards, decide whether to add an idle-fuel rate to the cost
    model, entered by the customer like the diesel price, so a running-but-idle generator has a cost. This is about 1.5 d plus a rebuild.
  - Changing the simulated generator so it carries load would be tuning the story, so it is not offered.

---

## Addendum 1 (2026-11-01): PB-0 pre-flight rulings

**Q1: option (a).** PB-0 lands the whole P-04 mechanism, so guard 12 passes in full in the slice that adds it:
- the hide rule in `frontend/src/ui/mock-deviation.css`;
- `frontend/src/ui/reviewLabels.ts` with `src/ui/__tests__/reviewLabels.test.ts` and `mockDeviationStyle.test.ts`;
- `main.tsx` calls `reviewLabels` first and imports `mock-deviation.css` app-wide. This is required: the `MockDeviation`
  component in `globalWorkParts` (`.global-work-deviation`) does not load the file today;
- the register rule sentence (§2 text, verbatim).

PB-0 becomes **3.5 units**. In PB-1, the P-04 unit becomes 0.25 unit of verification only:
- one review-mode capture (`DEMOB_REVIEW_LABELS=1 DEMOB_ONLY=kobo-board-S`) at 390 shows the R453 label, and at 1440 the label stays hidden by its width rule;
- the client-mode `portfolio-week` and `findings-all` captures have zero "MOCK DEVIATION" hits.

PB-1 becomes **5.25 units**. The freed 0.75 unit is held as slack for the time consolidation. Register ids are unchanged:
PB-0 and PB-1 share R650-R654.

**M1: confirmed.** The file is `tools/evidence-checks.mjs`. Export a pure ready predicate from it, test it in
`tools/checks/test_evidence_checks.mjs`, and call it from `settle()` in `demo-combined-evidence.mjs`. The §5 path was wrong.

**M2: confirmed.** Use the whole-line regex. Fixtures must cover:
- "Loading the site's overview." counts as not settled;
- "Loading and door records" counts as settled;
- "Loading…" counts as not settled.

Keep the `aria-busy` and `[data-repeat-check="loading"]` waits; the latter is inert until PB-3 adds the attribute, which is expected.

**M3: confirmed, with two conditions.**
- Excluding `w1.codes` is accepted. Upper-case codes are still caught by the existing enum-code regex and the
  zero-padded code regex.
- Gloss stripping must use only the allowed phrases and glosses already in `productVocabulary.json`, with no
  tool-local allow-list. Each stripped phrase is listed in the PB-0 packet.

The rest of M3 stands as planned: "MOCK DEVIATION" is always scanned on the full `<main>` text, and with
`DEMOB_REVIEW_LABELS=1` hits are recorded but not strict.

---

## Addendum 2 (2026-11-01): PA-1 pre-flight rulings (these apply to every lane)

**Q-A (OUT-E L3): accepted.** `history()` orders by `ORDER BY recorded_at, revision_no, id`. `revision_no` is unique
only within one verification outcome, so `recorded_at` leads and `id` makes the order total. The pinning test needs
two outcomes for one Action, with interleaved revisions.

**Q-B: one capture rule for all lanes (option 3, serialised).**
- Serving the kept DB is allowed. "Read-only" means no manual writes, no `prepare` and no `add-day` against it.
  The serve loop's ticks only refresh projections and comparisons, which is what the walkthrough itself does and what
  DEMO-B did. No migration lands in this round, so slice code can safely tick it.
- **Only one serve may run against a DB at a time** (two schedulers on one DB is the real risk). Lanes take a
  capture slot from the coordinator. Each run, in order:
  1. Start `demo_combined.py … serve` from the slice worktree with `--db assetops_demo3_full_test --work <AssetOpsV1-demo3>\var\demo3_full`.
  2. Start Vite from the same worktree.
  3. Wait for the first `performance:` line.
  4. Capture with `DEMOB_ONLY`.
  5. Stop both by PID and confirm ports 8990 and 5490 are free.
  6. Release the slot.
- No template copies (option 1). The I/O cost and the risk to the file store are not worth it for re-capture.
- No deferral (option 2). Each slice proves its own screens.
- After PA-3 merges, the same rule applies with `assetops_polish_full_test` and `var/polish_full`. From then on,
  `assetops_demo3_full_test` is only the walkthrough fallback.

**Q-C: accepted.** Leave EV-2 `missing_records` (`catalogue.py:53-54`) unchanged and note in the packet that nothing
renders it while the row sentence takes precedence. Drop the §1.6 clause "the same condition where EV-2
`missing_records` is shown".

**Pre-flight results: accepted.**
- **Grow (§1.7 pre-flight).** Kobo Grow is Unknown on both S and S+1 because MG-1 cannot be judged without sales
  records (`mini.py:457`, OBJECTIVE_NOT_JUDGED). This is a different cause from the readiness rule. Add R636 (D4)
  with that reason; Grow is not changed.
- **MG-7 settled rule.** Accepted as the builder planned it: `assessment.claim_level == "COMPLETE"`, zero dispatch
  intervals, and readiness exactly `UNKNOWN`. The chip then reads "No objective declared", and the Readings line reads
  "No generator run to check on this day · readings complete".

---

## Addendum 6 (2026-11-01): PA-2 pre-flight rulings

**Split.** With the files added below, PA-2 exceeds 6 units, so it becomes two slices in the same lane. Both use
register ids R640-R644.
- **PA-2a, server copy, codes and titles (about 4.5 units).** Q1, Q3, Q5, Q6, Q8, Q9, the "Recommendation not
  accepted" maps, and the §3.1 BE strings.
- **PA-2b, asset labels and plan due (about 3.5 units).** Q2, Q4, and the §1.4 backend.
- Order: PA-2a, then PA-2b, then PA-3. PB-3 waits for PA-2b, not PA-2a.

**Q1: accepted.** Edit the 12 title strings in `backend/tests/fixtures/w3/w301-estate-golden.json` directly. They are
text, not numbers, and the stop rule existed to catch exactly this. Run `test_w301_estate_golden_postgres.py` once,
when the machine is idle (quiet-suites rule). Update `test_idx_gaps_board.py:97-99` mechanically. MERGED stays unchanged.
`frontend/src/.../findingWords.ts:14-36` goes to PB-2: align its title words with the Addendum 4 titles there.

**Q2: accepted.**
- Add a top-level `summary: {overdue_count, due_soon_count, not_assessed_count}` and a per-row `due_state` to
  `GET /api/work/preventive` only. `state_counts` stays null.
- `plan_due_state` takes the timestamptz `next_due_at`, with the boundary as the implementer settled it.
- PB-3's validator must accept the new keys. Until PB-3, the existing frontend validator must not reject them. If it
  rejects unknown keys, PA-2b relaxes it for exactly these keys. That is the only frontend change allowed in lane A,
  and it is listed in the packet.

**Q3: accepted, with a wording correction.**
- The extra reads are accepted: `fr.title` in `_IndexTx.finding_revisions`, the `finding_revision` join in
  `_ReadTx.revision_links`, and a private `recurs_after_title` through `coverage.py` and `index.py`.
- RECURRED text: "Happened again after an earlier occurrence ({earlier title})". Without a title, it is "Happened
  again after an earlier occurrence".

**Q4: accepted.**
- Rewrite `asset_label` in place to the plain form, and add a wire `asset_type`. `cold.py` and `visits.py` read
  `asset_type` and no longer parse the label.
- `asset_code` is appended only when the Site has more than one non-retired asset of that type (the scalar subqueries).
- Unmapped types use the capitalised type word.
- Generators: GENERATOR shows as "Backup generator" on COLDCHAIN Sites and "Generator" on mini and EV Sites.
- In lane B, PB-3 replaces the two frontend parsers (`globalWorkParts.tsx:123`, `siteWorkCases.tsx:256`) with
  `asset_type` and `assetWords`. Add `siteWorkCases.tsx` to PB-3's files. Until then, their raw-label fallback shows
  the new plain label, which is acceptable.

**Q5: accepted.** At read time in `cold_site_reads`, rewrite the TRANSFER observation to "No record of switching to
backup power." and align estate's `COLD_OBSERVATION_WORDS` TRANSFER entry to the same words. The stored analytics are unchanged.

**Q6: accepted.**
- Change only the read-side constants in `board.py`, as the implementer proposed. `trial_fuel_comparison.LABEL` stays as stored.
- **Yes for `mini.py:79` `VERIFIED_WITH_COST`:** keep its verdict and code prefix, and use the same cost clause:
  `…: estimated effect of the trial (not money saved): {amount} {currency} less supply cost per kWh`.

**Q7: D-4 is revised for the whole round.**
- **Clock times stay in UTC.** Instants come from the DTOs without a Site offset (R86), so they are shown in UTC
  with no per-time suffix.
- **Calendar dates stay on the Site's own date.** That covers plan due dates, visit days and warning days: the
  server already computes them in the Site's zone (`warnings.day_text`, `visits._local_date`), and that is unchanged.
  Where the frontend formats a due date itself (Preventive `next_due_at`), it uses the Site zone from `siteTime.ts`
  when it is declared, and UTC otherwise.
- **The page note becomes "Times in UTC".** Pages that also list due dates (Preventive, Maintenance, the work request
  pages) say "Times in UTC · due dates in each site's local date". PB-1 builds `TimeZoneNote` with these two variants.
- `mini.py:39` `UTC_SUFFIX` stays as it is: it applies only to Sites with no zone, and none appears in the demo.

**Q8: accepted.** Apply `display_code` to every visible server label listed (`warnings.py:195,204`, `board.py`
`_item_text`/`_action_name`, `mini.py:75-79,725`, `cold.py:313,354`). The stored and wire `code` fields stay as stored.

**Q9: in scope for PA-2a.** `Action {aid[:8]}` (`work/site_index.py:208,215`) becomes the Action's display code when it
has a code (for example "ACT-003"), and "Action" otherwise.

**Q10: confirmed.** The extra files are in scope for PA-2a/PA-2b as split above:
`work/adapters/postgres_{domain_action_index,work_read,global_read}.py`, `estate/coverage.py`,
`site_outcomes/{board,mini,ev}.py`, and `global_work_api.py` if the summary needs it. PA-1 has merged
`site_outcomes/{board,mini,ev}.py`, so PA-2a rebases on main first.

**Settled items: noted.**
- The "critical load" wording is PB-2's.
- `display_code` uses minimum 3-digit padding.
- The `plan_due` boundary is as the implementer settled it.
- Both "Recommendation not accepted" maps change to "No action agreed yet".

---

## Addendum 7 (2026-11-01): PB-1 pre-flight rulings

**Q1: accepted.** PB-1 removes every visible " UTC" and "(UTC)" in the frontend, in all files, including:
- the PB-2 and PB-3 files;
- `EstateEvidence.tsx:96`, `estateFinancialsWords.ts:148` and `portfolioWords.ts:93`.

The edits are time-only: `time.ts` calls, dropped "(UTC)" labels, and `TimeZoneNote` in each bar. The lanes run in
order, so there is no conflict. PB-1 grows to **6 units**, including the 0.75 slack from Addendum 1. If it would
exceed 6, PB-1 stops at the 14 capture screens and lists the rest for PB-3.

**Q1a: accepted.** Where the time text sits inside a §3.1 row, PB-1 applies the whole row as ruled. These are the
five rows named (Kobo day control and window sentence, Kobo "Latest checked readings…", Cold window line, EV "as of…",
Work "Updated… · Reload"). The PB-1 packet lists them as "done in PB-1", and PB-2/PB-3 skip them.

**Q2: accepted.** `{seconds: true}` is optional. Seconds appear only where an existing ruling shows them: R372
historical "as of" lines, SiteHealth, EvEnergy and the cold hm. Live and latest lines have no seconds.

**Q3: accepted.** Each formatter keeps its own null word. Unparseable input shows "Time not available yet" and never echoes the raw string.

**Q4: accepted.** PB-1 makes the one copy change "Supported, coherent source" → "Well supported"
(`portfolioWords.ts:40`) with the P-03 CSS. PB-3 skips it.

**Q5: accepted.**
- `formatDayRange(from, toExclusive)` gives "23–29 Oct 2026" within a month and "28 Sep – 4 Oct 2026" across months.
  Across years, both ends are written in full.
- The cutoff picker moves into a `<details>` titled "View an earlier point in time". It is closed by default and open
  when `known_at` is set. The Show button stays in the bar.
- "This is an earlier evidence cutoff." becomes "Showing an earlier point in time."
- The historical line reads "Information as of {dayTime}".

**Q6: corrected.**
- PB-1 adds `formatDay(value, {timeZone})` to `time.ts`, and uses the plain "Times in UTC" note on **every** page,
  including Preventive, Maintenance and the work request pages.
- The two-part note "Times in UTC · due dates in each site's local date" is switched on by PB-3, in the same commit
  that wires the Site-zone due dates under P-09 with PA-2b's read.
- This way no page claims local due dates before it shows them.

---

## Addendum 8 (2026-11-01): PB-2 pre-flight rulings

**Q1: accepted, with a lane constraint.**
- PB-2 changes `mini.py:102` `GAPS_NO_READINGS` to "{g} of the last {n} days {verb} no checked readings yet" and updates
  `test_idx_gaps_board.py:72`. `GAPS_NOT_ASSESSED` and `GAPS_WITHHELD` are unchanged.
- PB-2's edits to `mini.py` are limited to string constants (`GAPS_NO_READINGS`, `FINDING_TITLE`); no logic.
- PA-2a also edits `mini.py` (display codes, `VERIFIED_WITH_COST`), so the coordinator merges whichever lands second
  after a rebase. A conflict there is constant-level and is resolved by keeping both changes.

**Q2: corrected.** The ROLE_WORDS entries are "Essential services: power supplied" and "Essential services: power
requested". The fallback capitalises the first letter. Builders must check the result against the vocabulary guard.

**Q3: accepted.** PB-2 changes only the shared Overview slot title (Kobo/mini) to "Possible cost". The cold and EV
headings go to PB-3.

**Q4: corrected, and moved to PB-3** (`EstatePortfolio.tsx` is a PB-3 file).
- "Estimate" clashes with the money panel's "Latest estimate" and "How this estimate was made".
- Use badge "What-if" and "No reviewed what-if yet". This is mock wording, so it goes in the R655 plain-language row.

**Q5: accepted as proposed.**
- Add the optional `technical` prop on `ui/Disclosure.tsx`, which renders `data-technical-details`.
- Add `ui/TechnicalDetails.tsx` with two pieces:
  - "Technical details";
  - "How this was worked out", with plain lines and the raw references nested in Technical details.
- `ExactReferences` stays unchanged.
- Switch the Kobo board, the verification page, SiteAction History and the `SourceProvenanceRecord` id lists.
- Rename the verification DigDeeper to "Technical details", and tag the two id-holding DigDeepers.
- Cold/EV/foundation `ExactReferences` sites that leak ids on capture screens are PB-3 (the Addendum 5 baseline decides which).

**Q6: accepted. PB-2 applies `displayCode()` at all ~25 visible render sites, including files owned by PB-3.**
- Lane B runs in order and PB-3 starts from main after PB-2 merges, so there is no parallel conflict.
- aria-labels and the "Action code" reference row keep the stored code.
- PB-2's packet lists every file it touched that PB-3 owns, and PB-3 rebases on main first.
- PB-2 grows by about 0.5 unit. If it would exceed 6 units, PB-2 stops after the capture-screen sites and leaves the rest to PB-3.

---

## Addendum 9 (2026-11-01): PA-3 pre-flight rulings

**Q1: accepted.**
- `DB_RE` becomes `^assetops_(demo3|polish)_[a-z0-9]{1,20}_test$`.
- `Demo.__init__` accepts `var/demo3*` or `var/polish*` directly under the checkout's `var/`.
- The marker and drop guard are unchanged, and the help text is updated.
- Add one pure test case each, for an accepted polish name and for a refused other name (for example `assetops_other_x_test`).

**Q2: accepted.**
- `demo_combined_cold.py` sets `ns["DEMO_NARRATIVES"] = True`. Only then do the calls at `:202` and `:461` pass `narrative=f"{title}."`.
- The standalone w502 walkthrough keeps its default, so historical audit evidence stays reproducible.
- `:315` (worst case only) is unchanged.
- Kobo `:115` and EV `:116` pass `narrative=f"{v['title']}."` directly.

**Q3: accepted.**
- A cold or EV story day with null `start`/`end` links to the whole calendar day, `{day}T00:00:00Z` to the next day.
- Its label says so: `… day S{offset}d ({day}), no event: whole day`. This way the presenter knows the board will read
  "nothing to show" rather than an event.
- Do not skip the row. The calendar should list every story day.

**Q4: confirmed. This is the ruled form, not a loosened check.**
- The CO-1 check reads `issues` + `in_hand` only, which folds in DEMO-A L2.
- It passes when `k["action"]` is in an item's href, which is the real guard, **or** `display_code(k["action_code"])`
  is in its text. That is the §3 / Addendum 6 Q8 display form.
- Import `display_code` from `outcomes/display_code.py`; do not copy it.

DEMO-A L1 stands: add back the assertion that "Reliable service and battery and generator life" is in the safeguards
text (`board.py:658` still composes it).

---

## Addendum 10 (2026-11-01): CO-1 "Action on the Cost row" (corrects Addendum 9 Q4)

**Ruling: the check's premise was wrong. This is not a board gap.**
- On day S the trial is VERIFIED, a final outcome. A finished intervention belongs under Earlier interventions, so the
  board places it correctly.
- LINK-LINEAGE guarantees that the Action is **linked** on the row (problem → trial → Must-not-harm). It does not
  guarantee which column the Action appears in.

**CO-1 asserts the linkage by href, with the column chosen by the verification state:**
1. When `kobo.json`'s verification outcome is final (VERIFIED, INEFFECTIVE or INCONCLUSIVE), the OPTIMIZE_COST row's
   `earlier` holds an entry whose href path is `/sites/KOBO-001/actions/{k["action"]}`. Otherwise, `issues` + `in_hand`
   hold such an entry. A text match alone never passes.
2. The Must-not-harm href contains `k["action"]`, and its text contains `display_code(k["action_code"])` (unchanged).
3. The safeguards text contains "Reliable service and battery and generator life" (DEMO-A L1, unchanged).

**Why this still fails on behaviour from before LINK-LINEAGE.** The trial Action's origin is an earlier revision of the
Finding, and that version of the board only linked Actions whose origin revision was the current revision. So it shows
no Action href on the row and no Must-not-harm, and (1) and (2) both fail. Pin this with a pure test of the CO-1
function on two row fixtures:
- a linked `earlier` href passes;
- the same row with no Action href (text "ACT-001" only) fails.

DEMO-A L2 is resolved by the href requirement: text that only names the code, like CO-3's line, cannot satisfy (1).
No rebuild is needed. Re-run only the finish check on `assetops_polish_full_test`, and expect 17/17.

The Kobo Finding title still reads "Generator support merits review" until PB-2 merges. That is expected; PC verifies it.

---

## Addendum 12 (2026-11-01): PB-3 pre-flight rulings

All three wire fields go to **PA-3** before its rebuild. They are read-time serialisations of data the backend
already holds, so the demo is honest without deviations. PA-3 adds them, with one read-level test each, and states
them in its packet. PA-3 may grow to 6 units for this.

If any one of them turns out to need more than a small change in its read (a new query path or a migration), PA-3
skips it and reports, and PB-3 uses its frontend fallback for that item. That fallback is the proposal from PB-3's
pre-flight, logged as a Known Deviation.

**Q1 (P-10).**
- **PA-3:** board case items (`in_hand` and `earlier` entries built from `CaseFact`, `board.py:169`) gain optional
  `kind` (INCIDENT, WORK_REQUEST or PLAN, as stored) and `occurred_at`. Existing fields are unchanged.
- **PB-3:** add the optional `onRead(read)` prop to `OutcomeBoard.tsx`, with no new fetch. `coldSiteViews` uses the first
  row item with `kind == "INCIDENT"` and `occurred_at` in `[from, to)`:
  - with such an item: "Incident {displayCode} · steps from the recorded readings" plus "Open incident →" (href as sent);
  - loaded with none: "No incident recorded in this period";
  - not loaded: "Steps from the recorded readings".

**Q2 (preventive due dates).**
- **PA-3:** preventive rows gain `site_time_zone`, the Site's declared IANA zone or null.
- **PB-3:** formats `next_due_at` with `formatDay(value, {timeZone})` when the zone is present, and in UTC otherwise.
  It switches on the two-part note "Times in UTC · due dates in each site's local date" on Preventive, Maintenance and
  the work request pages, as Addendum 7 Q6 rules.

**Q3 (request asset words).**
- **PA-3:** `global_detail.work_asset` gains the plain `asset_label`, from the same PA-2b helper, including its
  same-type count rule.
- **PB-3:**
  - `WorkRequestOverview` renders `asset_label`;
  - `assetWords` remains only as the fallback when `asset_label` is absent;
  - the `GlobalPreventive`, `GlobalMaintenance` and `siteWorkCases` parsers switch to the wire `asset_label`.

**Q4 (builder copy).**
- **Corrected:** the preventive "Draft" badge stays "Draft". A draft plan is not an approved plan, and "Planned" would
  overstate its status. "Draft" is already plain English.
- **Accepted:** `NO_DRAFT_PLANS` becomes "No preventive plans in this window."

**Addendum 12 Q4, corrected (2026-11-01).** "draft" is a banned term, and Addendum 5 forbids exempting it. The
preventive badge for a DRAFT plan therefore reads **"Not yet approved"** (neutral tone). Any other visible "draft"
wording on these pages follows the same rule, for example "Completing a plan that is not yet approved is unavailable
here".

---

