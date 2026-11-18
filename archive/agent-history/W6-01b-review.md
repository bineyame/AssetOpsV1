# W6-01b review (units B1-B3: global Maintenance and Preventive)

Reviewer: fresh independent Claude reviewer, 2026-10-22. Branch `task/W6-01b-maintenance`, head `43a9142c`,
diff `d4fd1f04..43a9142c` (commits `2f19542d`, `ef2578b4`, `f41fc849`, `15aea5a8`, `193f3632`, `43a9142c`).
Judged against `.agent/W6-01-build-spec.md` (B1-B3 cards, section 3.1, Codex retrospective, "B1-B3 pre-flight
rulings") and `.agent/W6-01b-phase-handoff.md`. Mock: `frontend/mockups/v69/index.html:959-965`, `MAINT_GTABS:205`.

## Verdict: ACCEPT

No High or Medium finding. Three Lows go to the Architect as confirmations. None blocks the merge. The items the
coordinator already sent to the Architect are noted below, not ruled here.

## Checks run (by this reviewer, on `43a9142c`)

| Check | Result |
| --- | --- |
| `pytest backend/tests/test_w601b_global_maintenance.py` (private `assetops_w6b1rev_test`, plan2 venv) | 13 passed, 1 xfailed (strict, `test_linked_finding_and_action_hrefs`), 39 s |
| `pytest backend/tests/test_w601a_global_incidents.py` (A1 regression on the refactored `global_index.py`) | 16 passed, 186 s |
| `npx.cmd tsc --noEmit` (frontend) | clean |
| `npx.cmd vitest run --minWorkers=1 --maxWorkers=2` on `src/work`, `estateEvidence`, `siteWorkCases`, the A2Q11 six rail files, `operatorRailInventory`, `operatorRouteFrames`, `w301EstateShellRoutes`, `estatePortfolioRoutes` | 15 files, 246 passed, 0 failed |
| `tools/check-all.ps1` | All 11 guards passed |
| `check_v69_ledger.py` / `check_v69_dependency_registry.cjs` | pass (110 screens, 258 panels) / pass |

The private DB was dropped and the harness left no `_pt*` databases. No server, Vite or browser was started by this
review. The full backend suite was **not** run by me, and the handoff records none for this revision (see "Plumbing").

## Scope: every changed file is on a card

- B1 `2f19542d`: `global_index.py`, `adapters/postgres_global_read.py`, `global_work_api.py`, the test file and
  `tools/w601_seed.py`. This is the B1 list. There is no guard, composition or `main.py` edit (G4).
- B2 Lane B `ef2578b4`: `GlobalMaintenance.tsx`, `globalWorkClient.ts`, `globalWork.css` and the test, plus the P-B2-1
  additions `GlobalIncidents.tsx`, `globalWorkParts.tsx` and `globalIncidents.test.tsx`.
- B2 Lane A `f41fc849`: the B2 Lane A list, the A2Q11 six files and the B2 evidence.
- B3 Lane B `15aea5a8` / Lane A `193f3632`: the B3 lists, plus CL3-2 (`GlobalMaintenance.tsx` and its test) and P-B3-2
  (`EstateEvidence.tsx` and its test). B3 does not touch `missing-claim-scan.mjs` or `operatorRouteFrames.test.tsx`
  (CL3-7).

## Contract verification

- **Wire and selection.**
  - Maintenance membership and sort use the root `created_at` (`_select_cases`, `member = "created_at"`).
  - Record fields follow W4 parity (`records[-1]`, P-B1-12).
  - `links.site_maintenance` has the label `Site maintenance`, the `/work/maintenance` path and the response
    `known_at` (P-B1-13). `detail` is null.
  - An unknown or unreducible state is a 503, and the counts must sum to `total_count` (P-B1-11).
  - Preventive SQL (`_PLANS`) selects roots whose `occurred_at` is in `[from,to)` and whose root is recorded by K. It
    takes the last head by `(recorded_at,id)` (P-B1-10). Rows sort by head `(recorded_at desc, site_code_key,
    site_id, root)`.
  - The preventive basis binds the root and head values, the asset label and the selected source IDs, and is sorted
    by `(site_id, canonical_plan_id)`. Provenance is `provenance_dto(..., [], [head_id])`, and `next_due_hours` goes
    through `m.decimal_text`.
  - The A1 token sort `(site_id, r["id"])` matches the old `(site_id, case_id)`, so incident tokens are unchanged.
- **`state_counts`.**
  - Incidents return `{OPEN,IN_PROGRESS,CLOSED}`; maintenance returns `{OPEN,IN_PROGRESS,COMPLETED,CANCELLED}`;
    preventive returns `null` (also on EMPTY_SCOPE).
  - On the client, `isEnvelope(value, root)` accepts null only on `/preventive` and `/operational-records`.
  - All four combinations are asserted:
    - `globalIncidents.test.tsx`: an object loads; null is refused.
    - `globalMaintenance.test.tsx:427`: null is refused.
    - `globalPreventive.test.tsx:358`: null loads; an object is refused.
- **P-B2-1/2.**
  - The listed parts moved to `globalWorkParts.tsx` with parameterized aria labels (`Incidents window` / `Incident
    pages`, and so on). `GlobalIncidents.tsx` re-exports the moved constants, and the A2 tests pass unchanged.
  - The extra `useGlobalWorkPage`, `GlobalWorkBar` and `GlobalWorkSlot` are a faithful lift of the A2 page body. The
    handoff discloses them.
  - `maintenance?` and `preventive?` are optional. An absent method reads `WORK_STORE_UNAVAILABLE`, which is tested.
  - `createGlobalWorkClient()` supplies both methods.
- **P-B3-2.**
  - `ExampleDestinations({query, body})` makes only `Preventive plan →` a live `Link`, using the response window and
    never a cursor. The other three examples remain `UnavailableLinkEntry`.
  - `keepsInertMockActions` is narrowed as ruled: three unavailable entries, one link, and no anchor in the table.
  - A new test pins cutoff preservation and the dropped cursor.
  - The Evidence-root 1440/390 capture and the click-through to the five DRAFT rows are in the B3 manifest.
- **Literals and labelled MOCK DEVIATIONs.** Every P-B2-3..11 and P-B3-3..9 literal matches. This covers the cards and
  notes, the footer (without its final period, as in the mock), the notices, the badge tones, the strip, the Trigger,
  `Last done`, `Next due` and `State` cells, the correction line and its disclosure, the breadcrumbs, the subtitles,
  the tabs and the loading sentences. All 8 MOCK DEVIATIONs are labelled in the file headers: two in
  `GlobalMaintenance.tsx:8-11` (notice, primary link) and six in `GlobalPreventive.tsx:8-12`.
- **Guards.**
  - F1 rail line and `$expected` entry.
  - The three F2 `W6-01b` fixture cases.
  - F3 constants `MAINTENANCE_PATH` and `MAINTENANCE_PREVENTIVE_PATH`.
  - F4 `Preventive &middot; scheduled`: added to `$expectedTabs` in B2 and removed in B3, so it is net absent.
  - Missing-claim scan: the `WORK_CONTEXT_NOTICE` exemption is updated, and `WORK_MANAGE_UNAVAILABLE_STATUS` and its
    exemption are removed.
  - F5 ledger: only the intended fields of `maintenance` and `maintenance-preventive` changed, `product_destination`
    bytes are kept, the `maintenance-preventive` `interaction` is now ASCII with `>`, and the `sitework-maintenance`
    substring edit is made.
  - X6 registry reason edits.
  - P-X-2 per-page CSS modifiers; the A2 468/518 heights are unchanged.
- **Preserve K4a.** The handoff's B3 run says `operatorRouteFrames.test.tsx not touched (K4a override preserved)`. B2
  edited that file only for its F1 rail literal. K4a is not on main yet, so nothing of K4a's could be lost.

## Mock side-by-side (1440 and 390)

The comparison used B2 `positive-*`, `stress-*` and `mock-maintenance-*`, and B3 `positive-*`, `historical_current-1440`,
`stress-390` and `mock-maintenance-preventive-*`.

- Panel order, headings, tab row, card set, card tones (amber Verification overdue and Overdue), table columns, notice
  position and strip position all match the mock.
- The 390 tables scroll inside their panel and show the `Scroll table horizontally` hint, with no document overflow.
- Every departure visible in the captures is either a labelled MOCK DEVIATION or a ruled addition: the A2Q4 source
  line, the §2 `Full title text` disclosure, the P-B2-7 lineage line and the P-B3-6 correction line.
- The breadcrumb's weight and separator (`/` rather than `›`) come from the shared `Breadcrumbs` component. The B3
  breadcrumb is with the Architect.

## Findings

| # | Sev | Where | What | Why it matters | Fix |
| --- | --- | --- | --- | --- | --- |
| L1 | Low | `GlobalMaintenance.tsx:151`, `GlobalPreventive.tsx:81` | The Owner cell and the `Correction: {reason}` line use the three-line `Clamp` with no full-text disclosure. The 128-character owner in `B2/screenshots/stress-1440.png` ends in an ellipsis, and a 500-character plan correction reason would do the same. The Owner cell copies the accepted A2 incident Owner cell. | §2 forbids silent truncation of long table text, but names a disclosure only for title, narrative, activity, event and record text. | Architect decides whether the global lists (A2/B2/B3/E2) add `<details><summary>Full owner text</summary>` (the C2 `mheader` already has it) or accept the clamp. This is a preference or ambiguity, not an acceptance gap. |
| L2 | Low | `GlobalMaintenance.tsx:122-131` | `No linked Finding or Action` renders on every row without links, so each corrective row gains a line. P-B2-7 says the text appears "only on the linked-fixture capture's other row", which can be read as limiting it. | The wording is ambiguous, and the extra line affects row height, which is measured within the cap. | Architect confirms the intended reading. |
| L3 | Low | `EstateEvidence.tsx:360-364` | The `Preventive plan →` href carries `known_at` only when the Evidence URL has an explicit cutoff, not the response's current `known_at`. The builder disclosed this. | P-B3-2's `[&known_at={effective_known_at}]` allows either reading. Carrying the current-read cutoff would later show the destination as `Historical as of`. The Site Work manage link (§1) always carries the loaded cutoff, so the two entry points differ. | Architect confirms. The current behaviour avoids a mislabelled historical page. |

Observations, not findings:

- `_select_cases` now maps an unreducible case event chain to `WORK_STORE_UNAVAILABLE` on the A1 incidents root as
  well. Before, `reduce_state`'s `ValueError` was not caught there. This is a stricter behaviour on a merged root, and
  the A1 tests pass.
- The `Open work` note reads `1 requests ...` at N=1, which is the ruled literal.
- Main now carries `5e90dbce` (W6-01b build rulings Q2, linked fixture clocks), which this branch does not have. The
  `linked` follow-up must merge main first.

## Already with the Architect (noted, not ruled)

- The strict-xfail `linked` fixture. The `maintenance-linked` capture is not taken, and no typed substitute was made.
- Builder choices: the KOBO-001 seventh request `Inspect inverter relay`, the CALENDAR stress plan with no due date,
  and the linked case titles.
- The B3 breadcrumb (`Maintenance` crumb linked to Corrective) and the date-only format (`1 Nov 2026`).
- The 4000/500 versus 3999/499 stress lengths. The arithmetic confirms the builder: both expressions end on a
  non-space character, so `.rstrip()` leaves 4,000 and 500.

## Shared plumbing touched (for the full-suite or scoped-regression decision)

- Not touched: `backend/assetops_backend/main.py`, `work/composition.py`, `tests/conftest.py`, migrations or DDL,
  `configuration-persistence.ps1`.
- Touched:
  - `tools/checks/{missing-claim-scan.mjs,navigation-rail-fixtures.ps1,navigation-truthfulness.ps1}`. `check-all`
    passes 11/11.
  - The seed tool `tools/w601_seed.py`, which both the A1 and B1 tests import. Its `linked` path imports
    `test_s4_finding_store_postgres`, `test_s6_action_store_postgres`, `test_w401_work_service_postgres` and
    `test_s4_finding_index_postgres`, and temporarily rebinds their module globals in-process.
  - The shared backend module `work/global_index.py`: the incidents selection was refactored into `_select_cases`.
  - Shared frontend files: `App.tsx`, the `OperatorShellLayout.tsx` rail, `siteWorkCases.tsx`, `EstateEvidence.tsx`,
    and the parts extracted from `GlobalIncidents.tsx`.
- Suggestion: a scoped regression is proportionate, because the slice touches no `main.py`, composition, conftest or
  schema. It would be `test_w601a_*`, `test_w601b_*` and the W4 work modules (`test_w401_*`, plus the Site work index
  tests), with the `src/shell src/estate src/sites src/work src/ui` vitest set already shown green by the builder
  (2537). The handoff cites no full backend suite run for `43a9142c`.

## Re-review (Q2)

Reviewer: fresh Claude reviewer. Scope: commits `3e1b15af`, `35c0d3fe`, `1dd26c3c` against item 1 of "W6-01b build rulings (Q2)". Read only; backend tests not rerun (builder reports 30 passed).

Verdict: ACCEPT.

- Clocks: `tools/w601_seed.py` keeps `LINKED_SETUP_AT` (2026-10-08T12Z), the F01 day, readings and anchors unchanged. `_linked_spec` deep-copies the S4 SPEC and changes only F01's single `decided` step to `2026-10-19T08:00:00Z`, and fails loudly if the step count is not exactly one. The S6 accept clock is `2026-10-20T00:00Z`. The Foundation `valid_from` is not touched. The old 21-day `_shift` is removed.
- Test: `xfail` is gone (grep finds none). `test_linked_finding_and_action_hrefs` now also asserts F01 source day 2026-10-06 and finding pin < action pin < first work_case write (2026-10-20T11:59Z). Its Site-versus-global href equality assertions are retained.
- Capture: `maintenance-linked` at 1440 and 390 uses tenant demo, window 2026-10-14..21, omitted `known_at`, and records the persisted IDs, hrefs and rendered cutoff (22 Oct 2026, 17:55 UTC). The first row WR-000003 shows an Action link, and WR-000002 shows Finding and Action links. Panel order matches the v69 `maintenance` mock: tabs, four cards, Corrective table, notice. No horizontal page scroll (document width equals client width at both widths).
- Caps: cards, notice, control bar, status line, pager and tabs are within or equal to the positive capture. The table panel (370 / 446) is below the 610-690 band only because this fixture has 2 rows, not 5. This is not a defect.
- Scope: the diff beyond `be8960a9` is the seed, the test (including the stale-comment replacement), B2 evidence, and the handoff Run entry. No other source files.
- Not verified: backend test run (not rerun, by instruction), frontend suite and layout re-run.
