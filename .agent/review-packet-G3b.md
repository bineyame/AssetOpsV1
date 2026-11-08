# Review packet — OWN-G3b, the operational records entry form (frontend)

Branch `task/OWN-G3b-operational-entry-form` (from main `60858f6cc`, main `1d666d410` merged in). Spec: build sheet
OWN-GAPS (`AssetOpsV1-plan2/.agent/build-sheet-OWN-GAPS-2026-11-08.md`) §3.3, the frontend parts of §3.4/§3.5, Rev 1,
and R2-G3b 1-16. Contract: §3.2, read from the sheet only. No G3a code is used. Pre-flight: `.agent/preflight-G3b.md`.
USER_REVIEW: this is a UI slice, so it is held for the owner's walkthrough (owner-absent rule). The merge is gated by
review.

## Outcome

The "Record a manual reading" form on `/operational-records` now saves records. It POSTs the closed §3.2 body to
`/api/sites/{code}/work/operational-entries`. The page shows the result line, re-reads the list, and keeps the chosen
Site. Records written by `service:operator-entry` show **Entered by site admin** in the By column. The app banner reads
"Demonstration · example sites and records".

## Files

- `frontend/src/work/OperationalRecords.tsx`: the form (`ManualReadingPanel`, `EntryField`, `entryErrors`), the
  literals (`READING_OPTIONS`, `ENTRY_ERRORS`, `ENTRY_OUTCOMES`, `savedLine`, `RECORDS_USED_THIRD`), `entryOutcome`,
  `actorLabel`, and the header deviation comments. `MANUAL_READING_REASON` and `UnavailableInline` are removed.
- `frontend/src/work/globalWorkClient.ts`: `SITE_WORK_API_PATH`, `OperationalEntryBody`/`Result`,
  `operationalEntryKey` (with the getRandomValues fallback), `postOperationalEntry`, the optional
  `submitOperationalEntry`, and `createGlobalWorkClient(basePath, sitesPath)`.
- `frontend/src/work/globalWork.css`: form states only (unit suffix, field error, result line). The unused
  `.global-work-form-reason` rule is removed.
- `frontend/src/shell/OperatorShellLayout.tsx:9-13`: `DEMONSTRATION_BANNER` (R2-G3b 16). No test pinned the literal.
- Tests: the new `frontend/src/work/__tests__/operationalEntryForm.test.tsx` (12 tests), and
  `operationalRecords.test.tsx`, where the inert-form assertions are updated to the live form.
- `.agent/mock-departure-register.md`: R12 closed. R362 gets the note "Taken at superseded by MD-OWN-G3-2". R651 gets
  the OWN-G3b note. New rows **R710-R713** for MD-OWN-G3-1..4.
- `.agent/OWN-G3b-evidence/`: the captures and `measurements.json`.

## Spec items → evidence

| Item | Evidence |
|---|---|
| Layout order: row 1 Site+Reading, row 2 Value+Taken at, Ticket row for delivery only, footer | test "keeps the mock field order…"; captures `app-*-idle`, `app-*-delivery-*` |
| Four Reading options with values; default Fuel tank dip | same test |
| Unit suffix L/L/kg/kWh and the per-reading placeholders; Ticket placeholder | same test (`shapes`) |
| Taken at is `datetime-local`, step 60, empty, labelled "(Site local time)" | same test |
| Site options from `manualReadingSites`, first selected; with none, placeholder + disabled | `R362` test (operationalRecords); "states Choose a Site…" |
| Client validation: 6 messages, shown after the first Submit then live, nothing sent | "shows each validation message…" (literal list asserted) |
| Exact request body (5 keys, trimmed, null ticket for a non-delivery) | "sends the exact closed body…", "sends a null ticket…" |
| Button disabled in flight, label unchanged; no second send | "sends the exact closed body…" |
| Success line "Saved as {REC}, status Submitted." (R2-G3b 2) + fuel second line; `role=status` `aria-live=polite` | same; "states every outcome row's text" |
| Every outcome row's text, including the other-4xx list and 503 → unconfirmed (R2-G3b 14) | "states every outcome row's text" (14 cases + rendered NO_TANK keeps values) |
| List re-reads after a success; Value/Ticket/Taken at cleared; Site kept across the re-read (R2-G3b 4) | "sends the exact closed body…" (reads 1→2, Site stays COLD-LAB-001); capture `app-390-delivery-saved` (Kisiwa kept) |
| Key kept after network/5xx/4xx; replaced after an edit, a mid-flight edit, or a success (R2-G3b 11/12) | "keeps the key…", "an edit made while a save is in flight…" |
| `randomUUID` absent → getRandomValues key `oprec-entry-<32 hex>` (R2-G3b 6) | "makes oprec-entry-<32 hex> keys…" |
| Client: path, POST JSON, saved/refused/unconfirmed parsing (R2-G3b 1/5) | "posts JSON to the Site entry route…" (7 answers) |
| Client without the method shows the 403 row | "a client without the submit method…" |
| "Entered by site admin" only for `service:operator-entry` | "labels the entry service's records…"; captures `app-*-table` |
| No `UnavailableInline` on the form; mock label "Submit for review" | first test in both files |
| No forbidden fuel words | form regex in the test; `fuel_wording.py`: "clean (693 files scanned)" |
| Description line, and a third paragraph in How records are used (R2-G3b 9) | operationalRecords main test (three paragraphs asserted) |
| Banner wording (R2-G3b 16) | `OperatorShellLayout.tsx:13` |

## MOCK DEVIATION labels

The labels are in the code comment (`OperationalRecords.tsx:8-20`) and the register (R2-G3b 8). They are not visible on
the page. The visible `MOCK DEVIATION D4 (R362)` label stays in the DOM, and the standing POLISH P-04 CSS hides it on
client screens (`ui/mock-deviation.css:12`).
- MD-OWN-G3-1 (R710): the Fuel delivery option, the Ticket row, and the unit suffix and placeholders.
- MD-OWN-G3-2 (R711): the native Taken at input.
- MD-OWN-G3-3 (R712): the description line and the result line. REC-307 is still not rendered.
- MD-OWN-G3-4 (R713): the Entered by site admin label and the third paragraph.

## Captures (one heavy browser job, light)

`.agent/OWN-G3b-evidence/`, 16 PNGs plus `measurements.json`:
- **Pages captured:** the app at 1440 and 390 in the idle, delivery-with-errors and delivery-saved states plus the
  table (12 PNGs), and the v69 mock `#/oprecords` at 1440 and 390 (4 PNGs).
- **Setup:** Vite dev server only. Chrome's request interception answered `/api/work/operational-records` with a
  4-Site fixture and the POST with a 201 `operational-record-1` body. There was no backend and no demo DB. Free RAM
  was 4.3 GB. The script is in the session scratchpad (`g3b-capture.mjs`).
- **Overflow:** none in any state. At both widths `docOverflow` is 0 and `controlsOutsidePanel` is empty. The sets are
  not empty: 6-10 controls were measured per state, and the panel is 734 px wide at 1440 and 358 px at 390.
- **Comparison with the mock:** the same pair, panel, row order, field labels and button. The differences are only
  MD-OWN-G3-1 (Fuel delivery, ticket row, unit suffix), MD-OWN-G3-2 (the date-time input) and MD-OWN-G3-3 (the
  description and result lines). The prose differences are R31 (existing) and MD-OWN-G3-4.

## Checks run (revision `cb8562705` + CSS and packet commit)

- `npx vitest run` on operationalEntryForm, operationalRecords and postW6ShellCss: **3 files, 38 passed**.
- `npx tsc --noEmit -p .`: exit 0.
- `node tools/checks/frontend-hardwiring.mjs`: passed (totals unchanged).
- `tools/checks/fuel_wording.py`: clean.
- No full suites, as instructed. `check-architecture.ps1` and `check-agent-workflow.ps1` were **not run**; the merge
  check-all covers them.

## Known deviations and residual risk

- **Register IDs:** R710-R713 are the next free IDs on this branch. G2 and G3a may claim the same IDs in parallel, so
  renumber at merge if they collide.
- **Contract:** the build works against §3.2 only. The real G3a route is unproven from the frontend until G3a merges,
  so check the 201 body shape (`public_code`, `schema_version`) on the integrated build.
- **Test environment:** the `node_modules` junction to the `AssetOpsV1` checkout produced jest-dom "Invalid Chai
  property" errors. Re-pointed to `AssetOpsV1-plan2/frontend/node_modules`, like the other worktrees, the tests passed.
  The junction is untracked.
- **Captures are fixture-only:** the time input shows Chrome's locale placeholder (mm/dd/yyyy).

## User-review focus

The live dip beat (R1.4): the result line wording, "Entered by site admin" in the table, and the delivery form at
390 px.
