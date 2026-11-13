# Review: task/SR-8-10-pages (SR-8 Renewable range page + one-day labels, SR-10c Fuel range page, SR-8 server L1-L3)

Reviewer: fresh Claude reviewer (did not author). Head reviewed: 31fc8a703, base = merge-base with main (e8f2bdea5).
Diff: `git diff $(git merge-base HEAD main) HEAD` (20 files, +1268/-50). No stray files; worktree clean.

## Verdict: ACCEPT WITH NOTES

No High or Medium findings. The range views read one stored route each, never sum the residual, flag partial days,
keep every gap state in words, retry 503 without ever showing data, and the hour view keeps the FocusPicker as the only
declarer. The re-pins are faithful to rev 10 §10.4 / 10b.2. Lows below can be fixed on the branch or batched.

## Checks run (by me, on 31fc8a703)

- vitest (7 files: miniRenewableRange, miniFuelRange, miniFuelRoutes, miniRenewableRoutes, miniFuelNights,
  siteRangeTags, sr2RequestUrls): **7 files, 91 tests passed** (11.0 s).
- `npx tsc --noEmit`: **clean** (exit 0).
- pytest, worktree PYTHONPATH: `test_sr8_renewable_range_route.py` + `test_sr10_fuel_range_route.py`: **44 passed**.
- `node tools/checks/mock-deviation-labels.mjs`: OK (174 files, R726/R727 registered).
- Not run (lane rules): check-all (coordinator), Postgres `test_sr8_renewable_range_postgres.py` (assertion-only change;
  pending DB turn), the packet's 89-file range/link sweep (cited, not rerun), `tools/layout-evidence.mjs`.

## Checklist

- Day states: Renewable NO_DATA "No readings this day", NOT_ENOUGH_READINGS "Not enough readings", NO_VALUE, PENDING,
  EXCLUDED (band shown, bar labelled "(excluded)", not counted), COUNTED partial "· Partial: n hours missing"; band is
  "—" for every non-shown state (server nulls bounds outside COUNTED/EXCLUDED). Fuel absent/NO_DATA rows span their
  words, never "0 of 0". Residual: "Residual: not available"; totals never summed on the page. OK.
- 503: `useRangeRead` retries only on the route's 503 code (or TEMPORARILY_UNAVAILABLE) with "Temporarily unavailable.
  Retrying…", then "Still unavailable. Refresh to try again."; no day rows rendered meanwhile (tested). OK.
- Single declarer: range views declare nothing (bar "All pages"); Fuel hour view declarations are `focus` only (test
  records every RangeSpan / useDeclareRangeFocus). OK.
- Drill-in: day/hour links keep their own from/to and get the range's `known_at` via `withRange` (tested both pages);
  Fuel carries the whole range in router state for "Back to the whole range" (href equals the range address, tested).
- One-day page: line "Headroom available in every eligible hour: low–high kW" under the card, envelope named "Range
  across eligible hours", "Partial: n hours missing" strip chip (D-SR.48/62); R726/R727 rows registered. OK, see L1.
- Server L1-L3: AVERAGE_LABEL per D-SR.48; window rule before `known_at`, range-words refusals (new test); Postgres
  test half-up rounding + EXCLUDED `all_hours_headroom_kw is None`. OK.

## Findings

- **L1 (Low, convention)** `frontend/src/sites/MiniPerformance.tsx:575,619` and `MiniPerformance.tsx:1694`
  (`BackToWholeRange`): the R726 additions on the one-day page (all-hours line, partial chip) and the R727 "Back to the
  whole range" on the hour page carry the deviation only in a code comment; other one-day deviations on this page
  (R451/R452/R454) render a tagged `data-mock-deviation` label, so review mode shows the departure. Fix: add the
  inline `mock-deviation-line` span with `data-mock-deviation="R726"` / `"R727"` beside each addition.
- **L2 (Low, honesty edge)** `frontend/src/sites/MiniRenewableRange.tsx:139`: a row with `partial: true` whose
  operating-minus-covered hours compute to 0 or null shows no partial flag at all (Fuel falls back to "Partial: some
  hours limited"). The server sets `partial` from the PARTIAL grade, not from the hour counts, so the two can differ.
  Fix: fall back to plain "· Partial" when `partial` is true and no hour count is available.
- **L3 (Low, test coverage)** `frontend/src/sites/__tests__/miniRenewableRange.test.tsx`: NOT_ENOUGH_READINGS,
  NO_VALUE and PENDING rows are not pinned (the brief names NOT_ENOUGH_READINGS); Fuel's "Still unavailable" and
  "Partial: some hours limited" paths are untested. The code paths are simple word maps; add one row each to the fixtures.
- **L4 (Low, flake risk)** `frontend/src/shell/__tests__/sr2RequestUrls.test.tsx:226`: the stub answers 503 to every
  request under the real 2/4/8 s retry delays and then asserts exactly one `renewable-range` URL; it passes only
  because the test settles before 2 s. Fix: answer 200 `{days:[],totals:{...}}` or a non-retryable status.
- **L5 (Low, UI polish)** `MiniRenewableRange.tsx:87` uses `columns={3}` for two cards (an empty third slot at desktop
  width); Fuel cells repeat their column header ("Expected use (modelled)" header + "Expected use (modelled) 10–12 L"
  cell, `MiniFuelRange.tsx` ~line 104, literal from 10b.2 item 3 — keep the words or move them to the header only,
  Architect's call); the range period bar reads "UTC days …" while the table lists Site-local days (pre-existing
  `MiniPeriodBar` wording). The Fuel range view has no summary card while Renewable has two (see Q-b).
- **L6 (Low, process)** packets do not record `tools/layout-evidence.mjs` for two new dense table + bar views; record it
  as `not run` with its blocking precondition (no Chrome/dev server on the lane) rather than omitting it.

## Builder questions (my view; Architect rules, not blocking)

1. 1-5 day range: a shared (UTC-midnight) range opening the range view is right. The side effect that a UTC-zone Site
   keeps the one-day page for a ≤5-day bar range breaks D-SR.9 consistency across Sites; better to recognise a story
   window by a page-only marker than by local-midnight alignment. Demo Sites are Africa/* zones, so no demo impact.
2. Card title: D-SR.48 says the card is "renamed in words only to 'Range across eligible hours'"; I read that as the
   label. Prefer label "Usable headroom: range across eligible hours" or the bare D-SR.48 words.
3. "Partial: n hours missing" shared by range row and one-day strip: matches D-SR.62 "same words". Agree.
4. Renewable back link: add "Back to the whole range" for parity with Fuel (same mechanism) — the drill-in replaces
   the shared range in the address, so without it the user loses the range.
5. Router-state back link: acceptable for the demo (lost on reload/share and after a FocusPicker hour change); a
   page-only `range=` param is the durable fix later.
6. `expected_use_l` total: show it as a "Modelled expected use over the counted days" card, which also gives the two
   range views the same layout; the residual stays unsummed.

## Residual risk

- Postgres SR-8 test not rerun on this revision; frontend full suite and production build not run (policy).
- Stored rows must be rebuilt at v2 after merge (SR-10 packet) or the Fuel range reads stale day kinds.
