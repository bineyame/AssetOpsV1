# Build sheet OUT-W · estate event windows for cold and EV Sites (self-contained)

Architect: Claude (`.ai/ROLE_CONFIG.md:9`), 2026-10-30, owner away (decisions delegated,
`.agent/owner-overnight-delegation-2026-10-30.md`; calls logged in `.agent/decisions-while-owner-away-2026-10-30.md`).
Owner decision: P-C1 **option A** (`.agent/owner-pc1-option-a-2026-10-30.md`). Code read at main **`833e7c95`**
(C merged). Branch **`task/OUT-W-estate-event-windows`**, worktree `C:\Users\assef\Bineyame\AssetOpsV1-outW`.
Backend paths are relative to `backend/assetops_backend/` unless they start with `backend/`, `tools/` or `frontend/`.
Read nothing else unless a step names it. Resolves register **R575**.

## 0. Rules that bind every unit

- Do not touch `main.py`, any `*/composition.py`, `field/ gateway/ contracts/ simulator/ host/ contract-fixtures/`,
  `backend/migrations/`, `tools/checks/*`, `estate/financials.py`, `financials/**`, `estate/money_invariants.py`,
  `analytics/adapters/postgres_assessment_store.py`, `estate/adapters/postgres_estate_read.py`. No new SQL: the
  rule is reused, not re-written.
- The `estate` port is already wired into `BoardServices.estate` (`site_outcomes/read.py:91`, an
  `EstatePortfolioService`, `estate/portfolio.py:499`, subclass of `EstateEvidenceService`). No new port.
- Mini-grid is unchanged (it reads the UTC day of `to`, `read.py:132`).
- **No new visible copy.** This slice adds wire keys, a link query and tests. So no vocabulary scan item arises; if
  the builder finds a need for a string, stop and ask.
- No schema-version bump: the additions are additive (the C rule, OUT-C sheet §4).

## 1. Code reality (verified at 833e7c95)

| Element | Source | Verdict |
|---|---|---|
| The selection rule | `analytics/adapters/postgres_assessment_store.py:1923` `selected_windows_on`: every exact `(analytic, window_start, window_end)` whose selection intersects `[from,to)`, greatest seq, pinned at the cutoff | OK (reused through the snapshot, never called directly) |
| Snapshot read of it | `estate/adapters/postgres_estate_read.py:227` `EstateSnapshot.selected_windows(t, s, domain, from_, to, evidence_cutoff, k)` → list of dicts with `window_start`, `window_end`, `state`, ... (`:242`, `:271`); calls `estate_snapshots_on` (`postgres_assessment_store.py:2088` cold, `:2762` EV) | OK |
| Evidence cutoff | `EstateSnapshot.evidence_cutoff(t, s, k)` (`postgres_estate_read.py:122`); None → no windows (`estate/coverage.py:210-217`) | OK |
| Model method | `EstateEvidenceService.site_readiness` (`estate/evidence_money.py:495-511`): `estate_request("evidence", ...)` (window rule, never widens, `estate/scope.py:106-117`), `self._read(work)`, `self._scope(snap, tenant, req, lambda code: code == site_code)` | OK (pattern to copy) |
| Domain constants | `estate/coverage.py:25` `COLD = "cold_chain"`, `EV = "ev_charging"`; `DOMAIN_OF_SITE_TYPE` already imported in `evidence_money.py:28-29` | OK |
| 31-day Site route cap | `evidence_money.py:149` `MAX_WINDOW = timedelta(days=31)` | OK |
| Summary loop | `site_outcomes/read.py:340-370`; cold/EV get `lo`/`hi` unchanged (`:349-351`); `_overview_href` `:373-375` | **EXTEND** |
| Board on an explicit window | `read.py:277-312` `compose(... lo, hi ...)`; cold/EV readiness widened to covering days (`:163-166`) | OK |
| Site page honours the window | cold `coldWindowFromParams` (`frontend/src/sites/coldAssessmentClient.ts:208-210`) used for the Overview and its board (`frontend/src/sites/coldSiteViews.tsx:615` `query={p.window}`); EV `shell/SiteAnalyticsFrames.tsx:519,534` | OK (builder opens both routes once in U3 to confirm) |
| Portfolio links | `frontend/src/estate/PortfolioOutcomes.tsx:281` (Site header) and `:299` (cell) use `site.overview_href` | OK (no component change) |
| Summary type | `frontend/src/estate/estateClient.ts:463-471` `EstateOutcomeSummarySite` | **EXTEND** |
| P-C1 record today | `backend/tests/test_out_c3_repeat_visits_postgres.py:80-98` records, asserts only when passed | **TIGHTEN** |
| Unit summary test | `backend/tests/test_out_b4_read.py:72-97` (`BoardServices()` with no estate: cold falls back, `overview_href == "/sites/COLD-LAB-001"`) | stays green unchanged |

Demo facts: w502 cold event lies inside yesterday `D` (`tools/w502_cold_work_cases.py:72-76`); the W5-01 window is
`doc["w501"]["window"]`. w504 EV evidence window is fixed `2026-10-06T08:00-09:00Z` (`tools/w504_ev_work_cases.py:39-40`).

## 2. Units (3). Effort 1.5 builder days, no full suite

### W1 · `site_selected_windows` on the estate service · 0.4 d · per-unit review
File: `estate/evidence_money.py`, directly after `site_readiness` (`:511`).
```python
def site_selected_windows(self, tenant_id: Any, site_code: str, from_: datetime, to: datetime,
                          known_at: datetime | None = None) -> list[tuple[datetime, datetime]] | None:
    """OUT-W (P-C1 option A): the exact selected windows of one cold or EV Site that intersect [from_, to), by the
    W3-01 rule the Evidence root reads (`site_coverage` -> `snap.selected_windows`), on one snapshot, scope and
    cutoff. Distinct (window_start, window_end), ascending; only forward spans of at most MAX_WINDOW. [] for a
    mini-grid or unsupported Site, a Site with no evidence cutoff, or no window. None when the Site is not in the
    authorized imported set."""
    req = estate_request("evidence", from_, to, known_at)   # INVALID_WINDOW over 31 days or not midnight

    def work(snap):
        scope = self._scope(snap, tenant_id, req, lambda code: code == site_code)
        for site in scope["sites"]:
            domain = DOMAIN_OF_SITE_TYPE.get(site["site_type"])
            if domain not in (COLD, EV):
                return []
            cutoff = snap.evidence_cutoff(tenant_id, site["site_id"], scope["k"])
            if cutoff is None:
                return []
            wins = snap.selected_windows(tenant_id, site["site_id"], domain, req.from_, req.to, cutoff, scope["k"])
            return sorted({(w["window_start"], w["window_end"]) for w in wins
                           if w["window_start"] < w["window_end"] and w["window_end"] - w["window_start"] <= MAX_WINDOW})
        return None
    return self._read(work)
```
- Same arguments to `selected_windows` as `estate/coverage.py:217` (evidence cutoff, then `k`). Do not reduce `state`:
  any selected window counts as an assessed event (a STALE or PENDING one is still the event; its board shows it).
- `_read` retries `EstateSelectionInconsistent` once, then raises `EstateRefusal` (`estate/index.py:176-185`). The
  caller (W2) catches.
- Tests `backend/tests/test_out_w1_selected_windows.py` (fake store whose `read(work)` calls `work(fake_snap)`;
  fake snap has `read_at`, `imported_sites`, `evidence_cutoff`, `selected_windows`, and accepts the attributes
  `_scope` sets): (1) cold Site, two windows returned out of order plus a duplicate pair (two analytics, same
  bounds) → two tuples ascending; (2) EV Site → its window; the fake records the args and asserts
  `(t, sid, "ev_charging", from, to, cutoff, k)`; (3) evidence cutoff None → `[]` and `selected_windows` not called;
  (4) MINIGRID Site → `[]`; (5) unknown code → None; (6) a 32-day window and a zero-length one are dropped;
  (7) `known_at` after `read_at` → `EstateRefusal("INVALID_KNOWN_AT")`; (8) a 32-day request → `INVALID_WINDOW`.

### W2 · Summary judges each cold/EV Site on its latest event · 0.5 d · per-unit review (shared seam)
File: `site_outcomes/read.py` only.
- New pure helper (module level, below `mini_summary_day`):
```python
WINDOW_BASIS_DAY, WINDOW_BASIS_EVENT, WINDOW_BASIS_PERIOD = "DAY", "LATEST_EVENT", "PERIOD"

def latest_window(windows: list[tuple[datetime, datetime]] | None) -> tuple[datetime, datetime] | None:
    """OUT-W: the latest assessed event inside the period: max window_end, then max window_start. None for None/[]."""
    return max(windows, key=lambda w: (w[1], w[0])) if windows else None
```
- New method `SiteOutcomeBoardService._event_window(site, lo, hi, known_at) -> tuple[datetime, datetime] | None`:
  `_need(self.s.estate, "estate").site_selected_windows(site.tenant_id, site.site_code, lo, hi, known_at)`,
  then `latest_window(...)`. **Any exception → None** (unconfigured estate, refusal, store error). A failed window
  choice never fails the Site; it falls back to the period, which honestly reads Unknown where nothing covers it.
- `summary()` (`:347-360`), per Site:
  - mini: unchanged call; `basis = DAY`.
  - cold/EV: `ev_win = self._event_window(site, lo, hi, known_at)`; board on `lo=ev_win[0], hi=ev_win[1]` when
    found (`basis = LATEST_EVENT`), else on `lo, hi` (`basis = PERIOD`). `known_at` is passed through unchanged.
  - Site row gains `"window": body["window"]` (the board's own `{from, to, known_at}`, `read.py:329-330`) and
    `"window_basis": basis`. A failed board (the `except` branch, `:355`) gets
    `"window": None, "window_basis": None`.
  - `overview_href`: `_overview_href(site, body["window"] if basis == LATEST_EVENT else None, known_at)`.
- `_overview_href(site, window=None, known_at=None)` (`:373`): base as today; when `window` is given, append
  `"?" + urlencode([("from", window["from"]), ("to", window["to"])] + ([("known_at", wire(known_at))] if known_at is not None else []))`.
  The board's `wire()` text (`...Z`) is what the board's own `links.self` already prints and the Site pages pass on
  unchanged. Never add `known_at` when the summary request had none (the Site page then reads at its own cutoff).
- `summary()["window"]` (the requested period, `:369`) is unchanged. `warnings` and `warning_count` need no change:
  they now come from the event-window boards.
- Tests `backend/tests/test_out_w2_summary_window.py` (fake estate with `site_selected_windows` recording calls;
  `monkeypatch` `SiteOutcomeBoardService.board` to record the `lo`/`hi`/`day` it got, as `test_out_b4_read.py:72-80`):
  1. cold Site, windows `[(08-09), (14-15)]` on day D → board called with `(14:00, 15:00)`; row `window_basis ==
     "LATEST_EVENT"`; `overview_href == "/sites/COLD-LAB-001?from=...T14%3A00%3A00Z&to=...T15%3A00%3A00Z"` (assert the
     exact string).
  2. tie on `window_end` → the later `window_start` wins.
  3. EV Site → `/sites/EV-LAB-001/ev?from=...&to=...`.
  4. no window (`[]`), None (not authorized) and a raising estate → board on the period, `PERIOD`, href with no query.
  5. mini Site → `site_selected_windows` never called; `DAY`; href unchanged.
  6. request `known_at` K → passed to both the estate method and the board, and on the href; none → no `known_at`.
  7. a failed board → `window` and `window_basis` both None, four UNKNOWN rows (as today).
  8. the warnings list and `warning_count` are taken from the event-window board (fake board returns one warning).
  `test_out_b4_read.py` must stay green **unchanged** (no estate → PERIOD fallback).

### W3 · Real-data proof, frontend type, captures, register · 0.6 d · slice review
Files: `backend/tests/test_out_c3_repeat_visits_postgres.py`, `backend/tests/test_out_c4_ev_warnings_postgres.py`,
`frontend/src/estate/estateClient.ts:463-471`, `frontend/src/estate/__tests__/estatePortfolio.test.tsx`,
`frontend/src/estate/__tests__/portfolioFixtures.ts`, `.agent/mock-departure-register.md`, `.agent/OUT-W-captures/`.
- **Cold (tighten P-C1).** In `test_out_c3_repeat_visits_postgres.py:80-98` replace record-then-branch with
  asserts on the `[D, D+1)` summary: status 200; GreenHarvest `window_basis == "LATEST_EVENT"` and
  `window == {"from": lo, "to": hi, ...}` of `doc["w501"]["window"]` **if** that is the latest selected window on D
  (else assert it equals the latest one the builder reads from `site_selected_windows` and record both); Cost row
  `NEEDS_ATTENTION`, lead `CC-3`; exactly one REPEATED warning for `COLD-LAB-001`; `categories[OPTIMIZE_COST]
  .warning_count >= 1`; `overview_href` starts `/sites/COLD-LAB-001?from=`; `money_hits(sbody["warnings"]) == []`.
  Keep `_record("P-C1", ...)` for the packet. Update the module docstring (lines 1-6): P-C1 is now asserted.
- **Cold, a week window.** Same test, second GET over `[D−6, D+1)`: same window, same Cost state (the latest event in
  the week is still D's). This is the owner's "week" case.
- **EV.** In `test_out_c4_ev_warnings_postgres.py` inside the same `_client()` block, GET the summary over
  `[2026-10-06, 2026-10-07)`: Depot `window_basis == "LATEST_EVENT"`, `window.from/to == evidence_window_E`,
  `overview_href` starts `/sites/EV-LAB-001/ev?from=`, Protect row state equals the board's Protect state on E
  (`body`). Then over `[2026-10-08, 2026-10-09)` (no event): `window_basis == "PERIOD"`, href with no query.
- **Frontend type** (`estateClient.ts:463`): add
  `window: { from: string | null; to: string | null; known_at: string | null } | null;` and
  `window_basis: "DAY" | "LATEST_EVENT" | "PERIOD" | null;`. Update `portfolioFixtures.ts` summary sites with
  these keys (mini `DAY`, cold `LATEST_EVENT` with a query href, EV `PERIOD`). Vitest in `estatePortfolio.test.tsx`:
  the GreenHarvest header link and every GreenHarvest cell `href` equal the fixture's `overview_href` with the query;
  the Depot link has no query. No component edit is expected; if a cell does not use `overview_href`, stop and ask.
- **Captures** 1440 and 390 on the w502 `positive` DB, day D: Portfolio (matrix GreenHarvest Cost cell reads
  "Needs attention"; warning list under the ranked table lists the repeat warning), estate Findings Cost lens (repeat
  warning listed), Maintenance (card 4 "Repeat visits without a result" = 1, amber). Click the GreenHarvest Cost cell
  and capture the Site Overview it opens (Cost row Needs attention). Record pairs vs v70 in the packet.
- **Register:** R575 → `resolved by OUT-W (latest assessed event inside the period)`. New row **R576** (below).
- Packet `.agent/OUT-W-packet.md`: units, test results, the P-C1 record, captures, register.

## 3. Wire (additions only; `estate-outcome-summary-1` unchanged)

Summary `sites[]` gains `window {from, to, known_at} | null` and `window_basis` ∈ `DAY | LATEST_EVENT | PERIOD |
null`. `overview_href` carries `?from=&to=[&known_at=]` only when `window_basis == "LATEST_EVENT"`. Nothing on
screen prints either key.

## 4. Validation tier

| Unit | Focused backend | Frontend |
|---|---|---|
| W1 | `test_out_w1_selected_windows.py` + `test_out_b4_read.py` + estate evidence unit tests the selector picks | — |
| W2 | `test_out_w2_summary_window.py test_out_b4_read.py test_out_b4_route.py test_out_b4_window.py test_out_b4_imports.py test_out_c2_board.py` | — |
| W3 | `test_out_c3_repeat_visits_postgres.py test_out_c4_ev_warnings_postgres.py test_out_b4_board_postgres.py` | `npx vitest related --run <changed files>`, `npx tsc --noEmit` |

`tools/check-all.ps1` at every unit commit. Slice end: `python tools/select-tests.py --base main` and run exactly
that set (no schema, no producer change; a full suite is **not** required unless the selector returns the whole
suite, in which case run `-Tier all` once on an idle machine). Full `npx vitest run` once at slice end.

## 5. Acceptance

1. `site_selected_windows` returns exactly the Evidence root's windows for the Site (same snapshot call, same
   arguments), deduplicated, ascending, ≤ 31 days; [] / None cases as W1.
2. The summary composes each cold/EV Site on its latest selected window inside the period, falls back to the period
   when there is none or the estate read fails, and never fails a Site for the window choice.
3. w502 `positive`, day D and the week ending D: GreenHarvest Cost Needs attention, one repeat warning, and its
   Portfolio cell opens the Site on that event window, where the board shows the same Cost state.
4. w504: Depot on 6 Oct uses window E; on 8 Oct it falls back to the period with a plain link.
5. Mini Sites unchanged (`test_out_b4_read.py` and every B/C test green unchanged).
6. R575 resolved; R576 added; captures recorded.

## 6. Register rows

- **R575** resolved: estate surfaces now read GreenHarvest's event (OUT-W).
- **R576** · OUT-W W2 · portfolio, findings, maintenance · D4 reading · standing. Mock: the Portfolio period and
  each Site's status share one window. Shown: a cold or EV Site is judged on its latest assessed event inside the
  period; an earlier event in the same period is not shown on the Portfolio (it stays on the Site's own window
  list). Reason: owner option A ("latest assessed event within the period"); a status is a reading of one event,
  never a merge of several.

## 7. Pre-flight checklist (answer in one batch before code, then stop)

- [ ] Worktree on `833e7c95` or later; `git ls-files --eol | grep "eol=lf" | awk '$2=="w/crlf"'` empty; `.venv` junction.
- [ ] Python `C:\Users\assef\Bineyame\AssetOpsV1-plan2\.venv\Scripts\python.exe`; PYTHONPATH
  `<wt>\backend;<wt>\contracts;<wt>\tools;<wt>\simulator;<wt>\gateway;<wt>\host;<wt>\field`;
  `assetops_backend.__file__` resolves to `-outW`. Run pytest directly if the host script is blocked; no policy override.
- [ ] Each anchor opens to its symbol (±15 lines noted, not asked).
- [ ] `EstateSnapshot.selected_windows` builds full window snapshots (findings included). It is one call per cold/EV
  Site per summary, ≤ 31 days. Time the w502 summary GET before and after in the packet. If it adds more than 2 s per
  Site, stop and ask (the fallback is a key-only snapshot method, which needs an adapter edit this sheet forbids).
- [ ] `_scope` sets `snap.historical`, `snap.continuation`, `snap.basis_historical` on the snapshot: the W1 fake
  must allow attribute sets.
- [ ] Confirm `site_selected_windows` is reached through `BoardServices.estate` in `site_outcomes/composition.py`
  without an edit (it is the same `EstatePortfolioService` instance that serves `site_readiness`).
- [ ] The cold and EV Overview pages pass `from`/`to`/`known_at` from the URL to the board (open
  `/sites/COLD-LAB-001?from=..&to=..` once on the w502 DB and confirm the board's `links.self` shows the same window).
- [ ] DB names `assetops_out_c_cold_test` / `assetops_out_c_ev_test` are reused by the extended tests (no new DB).
- [ ] `grep -c "| R576 " .agent/mock-departure-register.md` is 0.

**Known failures (merge gate ignores exactly these):** vitest `src/sites/__tests__/w1f4VerificationStructure.test.tsx`
(3 tests). `coldWorkCases` "W5-02 K3b … Incident What happened" flakes under full-run load; must pass alone. No backend
failure is known. Any other failure blocks.

## 8. Review points

- **W1:** no new SQL; same arguments as `coverage.py:217`; the window rule refuses as `site_readiness` does; None vs []
  distinct; duplicate analytics collapse.
- **W2:** a window-choice failure never fails or empties a Site; mini untouched; `known_at` never invented; href only
  on LATEST_EVENT; schema version unchanged; no edit outside `read.py`.
- **W3:** P-C1 now asserted, not branched; week case present; EV fallback proven; no component change; captures
  include the click-through.
