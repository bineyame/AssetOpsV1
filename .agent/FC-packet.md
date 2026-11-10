# FC-1 / FC-2 review packet: Findings cards (branch task/FC-findings-cards, not merged)

Spec: "Findings cards ruling (2026-11-10)" D-E5.25 to D-E5.28 in `.agent/build-sheet-OWN-GAPS-2026-11-08.md`;
draft `frontend/mockups/v71/findings-cards.html` (owner approval pending; MOCK DEVIATION until then).

## Outcome
- FC-2 `backend/assetops_backend/estate/index.py`: `supported_findings`, `awaiting_verification` and new
  `unconfirmed_findings` are computed over the rows read whatever the coverage. `basis_count` / `total_count` stay null
  unless COMPLETE. `high_priority` / `low_confidence` stay null in the body (frontend type made optional, no longer read).
  The per-site breakdown is the existing `coverage.sites[].state`; the page derives the words from it (no new key).
- FC-1 `frontend/src/estate/findingIndex.tsx`: three cards (Confirmed findings / Not yet confirmed / Awaiting
  verification); "High priority" removed; "So far: {full} of {applicable} sites fully analysed" plus non-zero parts
  (days not analysed yet / still processing / no new readings received / not analysed yet; NOT_APPLICABLE excluded);
  explanation line under the cards (`data-estate-so-far`); mini-grid-only note on Awaiting verification; null count reads
  "Not counted yet" (amber) with "Counted once every site is fully analysed". Complete case unchanged ("Across n sites").
- Register rows R715-R717 in `.agent/mock-departure-register.md` (MD-FC-1..3), force-added.

## Files
backend: `estate/index.py`, `tests/test_w301_estate_api.py`, `tests/test_w301_estate_index_postgres.py` (new
`test_partial_scope_counts_equal_the_rows_read`; two existing null-summary assertions widened), `tests/fixtures/w3/w301-estate-golden.json`.
frontend: `estate/findingIndex.tsx`, `estateClient.ts`, `__tests__/estateRoots.test.tsx` (new
`findingsCardsAreCompleteSoFarOrNotCountedYet`; two updated), `__tests__/estateFixtures.ts`.

## Checks (see run results below)
- Proof new tests fail on main: frontend, findingIndex/estateClient from 864204bb5 -> 3 failed (the new test and the two
  updated card tests). Backend: index.py from 864204bb5 -> `test_partial_scope_counts_equal_the_rows_read` fails
  (`assert None == 2`); restored, passes.
- Golden verification run without the write flag: `test_w301_estate_golden_postgres.py` 6 passed (843 s).
- `npx vitest run src/estate`: 5 files, 120 passed. `tsc --noEmit`: clean.
- Backend focused (`tools/run-host-tests.ps1`, assetops_test): `test_w301_estate_index_postgres.py -k "partial_scope_counts or
  scope_excludes or window_outside or cold_ev_day"` 4 passed.
- Golden: regenerated with `ASSETOPS_WRITE_W301_GOLDEN=1` (6 skipped as designed), then re-run without the flag (below).
- `node --test tools/checks/test_mock_deviation_labels.mjs`: 14 pass (includes the vocabulary checks).

## Known deviations / notes for review
- Golden diff is NOT only the three summary keys: regeneration also added `summary.claims` (`count.opportunities`,
  NOT_KNOWN) to the 23 Findings bodies. This drift predates the branch: CH-5a2b (c10d51658) added `claims` and main's
  golden was stale (T6 deferral 733eaf75c); it is not part of this change. Counts changed as intended: `awaiting_verification` null->0, `supported_findings` null->n, plus
  `unconfirmed_findings`.
- Mockup vs spec: the spec says the null note is followed by "the same parts" on every card; the draft (section C) shows
  the parts on Confirmed findings only. Built to the draft. The draft's partial Awaiting note is "So far · mini-grid ..."
  (no breakdown, no "Action taken; outcome open"); built that way.
- `high_priority` / `low_confidence` not removed from the backend body (allowed by the card); a later cleanup.
- Not run: full backend/frontend suites (demo-sprint policy), layout evidence (cards are three standard MetricCards).

## Residual risk
Cards copy is unapproved until the owner signs the v71 draft; R715-R717 stay "open" until then.
