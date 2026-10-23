# W6-01e review (E1 global Operational records read, E2 Operational records page)

Reviewer: fresh independent Claude reviewer, 2026-10-23. Branch `task/W6-01e-operational-records`, head `173cfc73`,
merge base `2dc2e5ed` (main has since gained only two `.agent/` W5-02a planning files). Diff reviewed:
`git diff main...task/W6-01e-operational-records -- backend frontend tools`, against `.agent/W6-01-build-spec.md`
(E1/E2 cards, section 3.1 G4/G6/F1-F6/A2Q11/CL3-6, Codex retrospective "RESTORE TO MOCK", "E1-E2 pre-flight
rulings" P-E-0..P-E2-12), the packet, the handoff and `.agent/mock-departure-register.md`.

## Verdict

**ACCEPT.** No High or Medium finding. KD1-KD5 are with the Architect and are noted below without a ruling. Merge
needs the full backend suite first, because the slice touches `tools/checks/*` and a seed tool (tiered-testing rule).

## Checks run (by this reviewer)

| Check | Result |
| --- | --- |
| `tools/check-architecture.ps1` | passed |
| `tools/check-agent-workflow.ps1` | passed |
| `tools/check-all.ps1` | all 11 guards passed (includes the navigation rail fixtures with the three new W6-01e mutations) |
| `pytest test_w601e_operational_index.py test_w601a_global_incidents.py` (private `assetops_w601e_review_test`, venv `AssetOpsV1-plan2`) | 28 passed, 327.7 s; base DB dropped afterwards, no run-owned clone left |
| `npx.cmd tsc --noEmit` | exit 0 |
| focused vitest: `src/work`, `estateEvidence`, `operatorRailInventory`, `operatorRouteFrames` | 10 files / 164 passed |
| focused vitest: the A2Q11 six, `w301EstateShellRoutes`, `estatePortfolioRoutes` | 8 files / 139 passed |

Not run by me: the full backend suite (a coordinator full suite started during this review, so I ran no more
Postgres tests), the full vitest run and `npm run build` (the packet records 115 files / 2725 passed and a build on
`fdd71cfc`), and the browser captures (I compared the committed PNGs and manifests instead). The packet records
`test_w601b/c` as 46 passed on `18355b0a`. I did not rerun that.

## Checks the dispatch asked for

- **Every changed file is on a card.** Yes. E1 has its six files. E2 Lane B has `globalWorkParts.tsx`, added by
  P-E2-1. E2 Lane A has `EstateEvidence.tsx` and its test (P-E2-9), `WorkRequestRecord.tsx` and its test plus the
  `wr-record` ledger interaction (P-E2-10), the F1/F2 guards, `operatorSiteRoutes.ts`, the ledger, the registry
  (`oprecords:1,3` only, with `:2` unchanged per CL3-6), and the ten rail test files (E2 card, A2Q11).
- **`kind` in the cursor, and the selected head drives the filter.** Yes. `record_kind` is the last
  `GlobalWorkRequest` field, and `KEYS` adds `kind` on operational only (an old root still refuses `kind`). Empty or
  unsupported values are `INVALID_CURSOR`. `filter` is the normalized string in both the token and the cursor, and
  it stays null on the old roots. The decoder admits a string only on operational. A filter mismatch is 409, raised
  before selection. The filter tests the head `kind` (`operational_index.py`, `rec["kind"]` from the `_OPERATIONAL`
  lateral head) before count, token, sort and slice. Root `occurred_at` decides window membership.
- **Record-to-case link rule.** Correct. The case resolves from the head `case_id` through `rx.case` at K, and a
  missing case or another kind is 503. INCIDENT opens `/sites/{code}/work/incidents?{day of the incident case's own
  occurred_at}`. MAINTENANCE_REQUEST opens `/maintenance/requests/{case_id}?site_id={code}`. Both carry `known_at`
  only when the request named one (`cutoff = k if request.known_at`, via `m.iso`, the C1 P-C1-5 precedent). The
  read watermark is never carried.
- **The fixture uses past writes.** Yes. Root writes take the `WriteClock` from `11:59:00Z`. The correction is at
  `12:00:01Z`, from `OPERATOR_LOG` to `SHIFT_NOTE`, with the same root occurrence and incident and the ruled reason.
  `_not_future` checks DB `clock_timestamp()`, and stored IDs are read back. The counts and kinds match P-E1-9
  (seven in-window demo roots, KOBO-002 `SITE_VISIT` on 10-13, an other-tenant `SITE_VISIT`). The captures read for
  real at 2026-10-23 ~08:34-08:40 UTC.
- **Button chips and manual-form structure match the mock.** Yes. There are five
  `.v69-chips > button.v69-chip[data-rec-type]` buttons outside panel 1. `aria-pressed` marks the active chip, and
  none is pressed on an invalid kind. Each chip navigates, drops the cursor and trail, and keeps the window and an
  explicit cutoff, and All removes `kind`. The form keeps two `.input-row`s, the four labels, the three Reading
  options, the placeholder and the date example, all disabled. `Submit for review` sits in `.form-footer` through
  `UnavailableInline` with the ruled reason line. The Depot option and `Fills REC-307` are removed (D1 R12).
- **C3's REC links are live.** Yes. `linkedRecHref` gives the root-occurrence UTC day plus the head `kind`, and
  `known_at` only from the inbound URL. `REC_PAGE_PREPARED` and the interim comment are gone, and the ledger
  literal is exact. The `wr-record` current and historical captures and the `rec-target` capture agree.
- **The EstateEvidence destination is live.** Yes. `Operational records →` is a `Link` built from the effective
  response window, with the explicit cutoff and no cursor. Two inert examples remain. The tests cover two links,
  the cutoff and an effective-window test.
- **Nine-link rail and the "K4a merges second" rule.** The F1 line, the `$expected` entry and the F2 three cases
  are exact. `UNAVAILABLE_ROOTS` is `["Assets","Settings"]`, there are nine links, and both focus orders and every
  A2Q11 literal are correct. `NavRail.tsx` is untouched. K4a is not on main (no `activeLabel` in `frontend/src` on
  main; W5-02a is still in flight), so E2 merges first. The P-E2-11 obligation therefore falls on K4a: preserve
  this live root, the nine-link count and the focus order, and record that proof.
- **Guards.** `operational_index.py` has no `open(` and no driver import. The adapter SQL is SELECT-only. The E1
  route lives in `global_work_api.py` with no forbidden HTTP tokens. Nothing in composition, `main.py` or
  `configuration-persistence.ps1` changed, and `check-all` passes.

## Mock comparison (`.agent/W6-01-evidence/E2/`, positive and mock at 1440 and 390)

The page order matches the mock: breadcrumb, h1, subtitle, four cards (the fourth amber), five chips, the
`Operational records` panel with the mock's verbatim description and eight columns in mock order, then the pair
`Record a manual reading` and `How records are used`. The Type column is plain text, Feeds carries ` →`, and State
is a blue `Submitted` badge. At 390 the cards go two-up and the chips wrap as in the mock. The table scrolls inside
its panel, and the form and prose stack. These differences are labelled and registered: cards 2-4 (D4 R29), rows
and By IDs (D4 R30), prose (D4 R31) and form (D1 R12). The Record-cell source disclosure (D2, A2Q4), the date bar
(R5/R6) and the pager (A2Q10) are earlier ruled elements. I found no unlabelled departure.

## Findings

- **L1 (Low, Architect note, not an acceptance gap).** The `Record a manual reading` Site options come from the
  P-E2-5 literals `Kobo Mini-grid` and `GreenHarvest Cold Room`. The ruling calls them "the two authorized fixture
  Site names", and R12 says Depot "belongs to the fixture's other tenant". In the fixture, though, both authorized
  Sites are KOBO-001 and KOBO-002, imported from the same YAML. Both are stored as `Kobo mini-grid`, and the other
  tenant's Site is a KOBO-001. The options are therefore static mock placeholders rather than the scope, which is
  harmless because the form is inert. The positive capture also shows `Kobo mini-grid` for both Sites' rows, so
  they cannot be told apart at the walkthrough. That comes from the A1 fixture, not E2 code. Fix (Architect): reword
  the R12 reason, or treat the options as D4 placeholders. No code change is needed.
- **L2 (Low, preference).** `RECORD_KINDS` is defined in both `work/global_index.py` and
  `work/operational_index.py`. Importing one from the other would remove the drift risk.

## Known deviations (noted, not ruled)

- KD1: the extra keyword-only `cutoff` on `select_operational`.
- KD2: the manual-reading panel height cap.
- KD3: unruled literals `Until {date}`, `Reading:` and the REC href parameter order. This is an implementer choice
  that the owner rule rates Medium until the Architect rules it.
- KD4: the fail-closed checks run before the kind filter. This is conservative and consistent.
- KD5: the register status for R12/R29-R31/R34 (R34 is resolved in code but still `planned`).

## Residual risk

- The K4a second-merger integration is outstanding (see the rail check above).
- `period_end` rendering (`Until ...`) has no fixture coverage, since every `period_end` is null. Only unit tests
  exercise it.
- The full backend suite is required before merge (shared plumbing, below).

## Shared plumbing touched

`tools/checks/navigation-truthfulness.ps1`, `tools/checks/navigation-rail-fixtures.ps1` and the seed tool
`tools/w601_seed.py`. It also touched the shared work modules `work/global_index.py`, `work/adapters/postgres_global_read.py`
and `global_work_api.py`, and the shared frontend `globalWorkParts.tsx` and `globalWorkClient.ts`, which all four
global pages import. It did not touch `main.py`, `*/composition.py`, `conftest.py`, migrations,
`writer_guard_probes.py` or `NavRail.tsx`.
