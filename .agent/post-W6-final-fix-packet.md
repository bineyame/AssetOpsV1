# Post-W6 final fix packet (branch task/post-W6-final-fix, from main 739c0d7a)

Rulings: `.agent/post-W6-final-review-rulings.md` (binding). Status: code, tests, register, backlog and captures DONE (captures: see Captures).

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
Captured 2026-10-26 on head 83560929 (code SHA 6bc57581 + docs), Vite from this worktree's `frontend/`, Chrome headless over CDP 9451, 1440x1000 and 390x900. Evidence in `.agent/post-W6-final-fix/<set>/evidence.json` + PNGs; tooling `tools/shot.mjs` (capture-only, own measurements; not the mock-pair tool, so no mock comparison), `start.ps1`, `run_*.sh`, targets files, `logs/`. Producers unmodified and unwrapped, each dropped by PID/DB afterwards (DBs pwfx_test, w301cap_test, w502b_positive_pwfx_test, w504a_*_pwfx_test; var folders removed; no servers left; `var/` holds only evidence and sites).
Browser clock = real 2026-10-26 (no clock pin in the browser); producer clocks: w403 mini = DB/wall clock, W3-01 serve.py pinned estate present 2026-11-02T11:04Z flowing with wall time.

| Set | Producer | Targets x widths | Result |
|---|---|---|---|
| `mini/` + `mini-b/` | `w403_mini_decisions_walkthrough.py` `--db pwfx_test` (prepare, serve, replay-positive), API 9761, Vite 5452 | 14 + 2 rerun (Scenarios, Finding history; first Scenarios shot caught the loading state, superseded by mini-b) x2 | docOverflowX 0 on all |
| `w301/` | `.agent/W3-01-evidence/serve.py` (w301cap_test), API 9741, Vite 5453 | 20 x2 | docOverflowX 0 on all |
| `l11/` | same, labelled synthetic DOM | 1 x2 | see L11 |
| `cold-fin/` | same | 3 x2 | see L4/L5 |
| `cold-{positive,forbidden,unavailable}/` | `w502_cold_work_walkthrough.py --tag pwfx` (positive DB; forbidden 8976, unavailable 8977), Vite 5471/5476/5477 | 3 x3 modes x2 | docOverflowX 0 |
| `ev-{positive,forbidden,unavailable}/` | `w504_ev_work_walkthrough.py --tag pwfx` (W504_API_PORT_BASE=18460; prepare, serve, attest) | 2 x3 modes x2 | docOverflowX 0 |

Claims verified:
- **M1** (`mini/mini-incidents-bare-*`, `mini-maintenance-bare-*`): bare `/sites/MG-W402-001/work/incidents` and `/maintenance` show From 2026-10-20 and To 2026-10-26 (EAT, included) = seven Site-local days; the 26 Oct incident is listed (Incidents (1), Maintenance (1)). Same at 390.
- **M3** (`w301/estate-*`): estate Findings table first column 152 px at 390 (672 px table in a 303 px scroller, inner scroll, docOverflowX 0), 258 px at 1440. Other estate tables at 390: Financials 88, Evidence 86 and 123, Actions 197 (none 152), all inside their own horizontal scroller (800/303, 520/288, 330/303, 820/303), docOverflowX 0. Portfolio has no table. Checked on the Findings day and week windows.
- **M2** (`cold-*/*-action-verification-*`, `ev-forbidden/*`): cold 403 panel "Cold work unavailable / You do not have access to this site." with a "Technical detail" disclosure (Status 403 · code SITE_SCOPE_FORBIDDEN) and no Reload; cold 503 panel (WORK_STORE_UNAVAILABLE) with Technical detail and a "Reload" button below it (390 screenshot checked). EV 403 same pattern ("EV work unavailable"). The Work-tab Actions list keeps "Retry" (backlog, as ruled).
- **L11**: no real page in the producers renders an overflowing key-value `code` (probes of Finding, Action, Site, Foundation, Health, Evidence pages found none; the first probe set was discarded because Vite had died mid-run). Verified the CSS only: `l11/` injects a labelled synthetic `dl.v69-key-values` with a 204-char `code` (tabindex 0, scrollWidth 1234 vs clientWidth 556 at 1440 and 148 at 390), moves focus by a real Tab key via CDP: `:focus-visible` true, outline `solid 2px rgb(29, 78, 216)`, offset 2px at both widths. The auto-marking effect itself is covered only by the unit tests (keyValueCode).
- **L4/L5** (`cold-fin/`, `w301/cold-work-*`): cold Financials > Scenarios with a valid window: the Site tab row and the Overview/Assumptions/Scenarios row all carry `?from=2026-10-01T00:00:00Z&to=2026-10-07T00:00:00Z`; bare: no query. With the bad window (`+03:00` from, `to=nonsense`): the page shows the COLD_TIME_INVALID refusal and the Site tab row's Financials tab is the bare `/sites/COLD-LAB-001/financials`; likewise on cold Work with the same bad window the Site tab row links (Foundation, Health, Performance, Findings, Work, Financials, Evidence) are bare. Observation, not in L4/L5 scope: the page's own Overview/Assumptions/Scenarios row, breadcrumb and the Work case tabs (Incidents/Maintenance) still carry the raw bad window, so they land on the same explained refusal.
- **Cold Work forbidden list**: the Actions list in Work shows the inline "No access" text with "Apply" and "Retry" (unchanged list surface); the new panel is the Action verification route.

## Gaps
Captures done (see above); remaining gaps listed at the end of the Captures section. No producer reaches a missing Site zone.

Capture gaps (recorded after the capture run):
- **L3 EV tariff-withheld sentence** on Site and estate pinned views: not reached. On W3-01 serve.py the EV Site and estate reads at K = 2026-10-06T09:00Z show an ESTIMATED consequence, any earlier known_at returns EMPTY_CITATION_SET (UNKNOWN), later is EV_TIME_INVALID; no unmodified producer yields the STALE_BASIS guard. Covered by the backend tests only.
- **M2 409** (cold and EV): no producer returns an Action-refusal 409. **EV 503**: the w504 `unavailable` mode stops the whole positive API, so the page shows "Site unavailable" (Site store) and the Action panel is never reached. Covered by unit tests.
- **Missing Site zone** (L6: mini Scenarios/Work fields, Finding history header, Evidence headers): no producer has a Site without a usable zone; MG-W402-001 is EAT. Valid-zone rendering captured (Work fields "(EAT)", Evidence "Evidence page is "Awaiting evidence migration" in this producer so the Measured/Sent/Received headers are not on screen). Unit-tested only.
- **Cold Action overview** `/actions/<id>` under 403 renders "Action not found" (separate overview surface, not the new panel); not changed by this slice.
- L9/L8 not browser-reachable (client-side window sentences; no 422 producer).
- No defect found; no code changed after 83560929.
