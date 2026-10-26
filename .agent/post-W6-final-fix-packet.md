# Post-W6 final fix packet (branch task/post-W6-final-fix, from main 739c0d7a)

Rulings: `.agent/post-W6-final-review-rulings.md` (binding). Status: code, tests, register and backlog DONE; captures NOT RUN (see Gaps).

## What changed
- M1: `siteSevenDayWindow` (`frontend/src/sites/siteTime.ts`); `workCasesScope(params, site)` in `SiteAnalyticsFrames.tsx` uses it for non-cold/EV Sites. Cold/EV keep R338, global Work keeps Q7.
- M2: `coldActionRefusal` mirrors `evActionRefusal` (`coldWorkPresentation.ts`); cold gets `reloadLabel` "Reload" and `technicalDetail`. Cold Actions list keeps Retry (backlog).
- M3: `estate.css` 640 px first-column rules scoped with `:has(col.estate-findings-col)` (same prefix as the 672 px rule).
- L3: `STALE_BASIS_COPY` for both Site and estate pinned reads (`backend/assetops_backend/ev_site_reads.py`); `STALE_AS_OF_COPY` aliases it.
- L4/L5: `coldTabSearch` gate (`coldSiteRoutes.tsx`); cold Financials > Scenarios tab row passes it.
- L6: `siteZoneDisplayLabel` / `SITE_ZONE_UNAVAILABLE_LABEL`; mini Scenarios and Work fields, Finding history header, mini Evidence Measured/Sent/Received headers (`LedgerSiteEvidence.tsx`).
- L8: dead 422 branch removed from `MiniPerformance.tsx` `refusalCopy`.
- L9: `EV_WINDOW_NOT_UTC_TEXT` (`evWorkPresentation.ts` `actionWindowRefusal`).
- L11: `KeyValueValue` in `ui/V69Layout.tsx` (focusable overflowing `dd code`, "Full value: ..." name, author attributes preserved) + `:focus-visible` ring in `primitives.css`.
- Docs: register housekeeping (117 stale D3 closed with merge shas; 19 of them split parents, task text said 17, each points at its child; 60 planned -> `standing (owner)`; R224 duplicate of R207; header and category table refreshed; R328, R374 open) and `.ai/MILESTONE_REVIEW_BACKLOG.md` item (j). `.ai/CODE_STATE.md` entry added.

## Choices made
- M1 display: zone-unavailable Work form says "(UTC (Site time zone unavailable))" and "to (UTC (Site time zone unavailable), included)".
- Mini Evidence: when the zone is unusable the three headers read "Measured UTC (Site time zone unavailable)", "Sent ..." and "Received ..."; valid zones keep "Measured (EAT)", bare "Sent", "Received" (cells already print UTC).
- M2: any loaded refusal that is not INVALID_KNOWN_AT/403/409/503 reads "The Action could not be read." (the old cold client-authored sentences for http-null/unexpected shape are now the unavailable sentence or this one, per the ruling's EV mirror).
- L5: an invalid (non-UTC) cutoff is dropped from cold tabs too (EV helper does the same).
- L9: a non-UTC pair whose parsed order is reversed keeps the existing order sentence.
- L11: implemented in the shared `KeyValues` only; hand-written `<dl class="v69-key-values">` blocks in `SiteActionVerification.tsx` are not wrapped (their one `code` is a short enum).

## Tests
- Focused: siteTime (EAT near midnight, just-before-midnight, UTC fallback and invalid zone, America/New_York clock change = 169 h), siteWorkCases (bare mini address with a faked 22:30Z clock shows 21 Oct to 27 Oct and Search keeps the bounds; zone-missing label), domainActionVerification (cold 409/418/null/503/500 map, Reload label, technical disclosure, non-UTC/reversed window sentences), coldScenarios (tab row carries/drops window), evActionFixRound (coldTabSearch gate, cold refusal map), estateRoots (M3 CSS scoping), keyValueCode (new, 4 tests), evEnergy/siteFindingHistory expectations updated; backend `test_w207_ev_site_reads_postgres.py` expectation updated.
- Revert proofs (each on committed code, then `git checkout`): M1 scope (2 fail), M1 helper (1), M2 reloadLabel (4), M3 CSS (1), L5 gate (3), L4 tab search (2), L9 (1), L6 (1), L11 tabindex (1). All reverted; tree clean after.
- A first run caught my own mistake (the `dd` wrapper had landed on a different component) and an aria-label clobber (`evAssessmentRoutes`), both fixed and covered.
- Full vitest (alone, final SHA 6bc57581): 138 files, 3433/3433 passed on the third full run. The first two full runs each had one different timing-sensitive failure (evDepth, evScenarios "R347 Site tabs open the EV pages") that passed in isolation and on rerun; not caused by this change, flagged as load flake.
- tsc clean; `npm run build` built; check-all 11/11 guards passed (`-ExecutionPolicy Bypass`, `-Python` main venv).
- Backend focused (L3), PYTHONPATH = this worktree, DB assetops_test: `test_w207_ev_site_reads_postgres.py test_w302_pinned_facades.py test_w302_pinned_facades_postgres.py`: 48 passed in 482 s.

## Captures
layout evidence / 1440 and 390 recapture: not run. Reason: the quiet-machine wait consumed the session and my context reached its budget before the multi-producer capture runs (mini sitework, cold/EV Action refusals, estate 390, cold Financials > Scenarios, EV tariff-withheld, mini Scenarios/History/Evidence missing-zone). Every layout claim above (M3 at 390, L11 focus ring, M2 button placement) is therefore unverified in a browser. See `.agent/post-W6-final-fix-handoff.md`.

## Gaps
Captures (above). Producers that reach a missing Site zone are unknown; record as gap if none does.
