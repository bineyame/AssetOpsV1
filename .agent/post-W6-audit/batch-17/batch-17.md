# Post-W6 audit batch 17: W5 EV cases/Action

IDs: `ev-work-incidents`, `ev-work-maintenance` and `ev-action`.

- Branch `audit/batch-17` at main `19609909`. Product code is identical to the frozen `fddf5cad`.
- Worktree: `AssetOpsV1-review5`.
- Mock authority: `frontend/mockups/v69/index.html`, served by the same Vite origin and rendered at 1440x1000 and 390x900 CSS px.

All dispositions are **proposals** for the Architect, and this batch adds no register rows.

- Machine-readable record: `batch-17.json` (84 pairs plus 20 link-check captures, which are not counted).
- Side-by-side view: `index.html`.
- Differences: `differences.json`, written by `tools/differences.py`.

## Route reconciliation (`frontend/src/App.tsx`)

| ID | Mounted route | Status |
| --- | --- | --- |
| `ev-work-incidents` | `SITE_WORK_INCIDENTS_ROUTE_PATH` `/sites/:siteId/work/incidents` (App.tsx:471; EV branch of the shared case page) | mounted |
| `ev-work-maintenance` | `SITE_WORK_MAINTENANCE_ROUTE_PATH` `/sites/:siteId/work/maintenance` (App.tsx:475) | mounted |
| `ev-action` | `SITE_ACTION_ROUTE_PATH` / `SITE_ACTION_VIEW_ROUTE_PATH` `/sites/:siteId/actions/:actionId[/:actionView]` (App.tsx:478; `SiteActionFrame`, which sends EV_CHARGING to `DomainActionRoute` with `EV_ACTION_PRESENTATION`) | mounted |

The spec route table is correct. On a domain Action, `/actions/<id>` and `/actions/<id>/verification` render the same page. The W1 section names behave differently (B17-08):

- `/execution`, `/history`, `/plan` and `/evidence` silently render Verification.
- `/overview` falls back to the W1 'No such Action section' page.

## Producer, environment and capture

- **Producer (reviewed, unmodified):** `W504_API_PORT_BASE=18700 tools/w504_ev_work_walkthrough.py --work var/w504a_b17 --tag b17`, run as `prepare`, `serve`, `attest`, then `drop`.
  - This is the same tool and knob as batch 16. The APIs ran on 18701-18707.
  - I checked `pg_database` first. No `w504a_*` DB existed; only batch 15's `w502b_*_b15_test` DBs were present.
  - DBs: `w504a_{positive,zero,worstcase,unknown}_b17_test`.
  - The tool writes only to `var/w504a_b17` (gitignored). Logs and the manifest copy are in `logs/`. The manifest records revision `19609909` with `dirty: false`.
- **Modes:**
  - `positive`: ACT-000001 'Investigate connector 2' with its declared three-criterion intent, plus attested INC-000001, WR-000002 with its record, and both case links.
  - `zero`.
  - `worstcase`: 5 Actions, 5 Incidents and 5 requests, with 160-code-point title, owner and narrative text.
  - `unknown`, `pending` and `stale` are unavailable (B17-16).
  - `forbidden` gives a real 403. `unavailable` is the whole API, stopped by `attest`.
- **Servers:** Vite ran on 127.0.0.1:5187 `--strictPort` and was restarted per mode (`tools/run_phase.ps1`, `tools/run_rest.ps1`). Headless Chrome used CDP 9527.
- **Capture:** `tools/capture-b17.mjs` is batch 16's capture-only wrapper. It adds breadcrumb, header-button and main-text fields. Targets come from `tools/mk_targets.py`, generated from the walkthrough manifest.
  - The positive phase was recaptured after fixing a whitespace regex in the added text field.
  - The first links run hit a Vite dependency re-optimisation ('Invalid hook call', blank pages). It was rerun on a fresh Vite and passed (B17-09).
- **Claims:**
  - positive 252/252
  - zero 60/60
  - worstcase 120/120
  - forbidden 36/36
  - unavailable 36/36
  - links 118/120: the 2 failures are global Incidents against the Site-scoped mock, a deliberate cross-reference.
- **Windows:**
  - Work window W: UTC day 24-25 Oct, used for the Work tabs and the Action detail URL.
  - Evidence window E (2026-10-06 08:00-09:00Z) is the intent basis only.
  - Historical cutoffs: the index `known_at` (before the cases); a cutoff between Action K1 and intent K2; and K1 minus 1 s.

## Cases and pairs (84)

| Screen | Cases (x2 widths) |
| --- | --- |
| ev-work-incidents / ev-work-maintenance | positive, historical-index-known-at, refused-reversed, refused-span-32d, no-window, all-open, zero, zero-prior-day, worstcase-five-160, worstcase-five-160-all-open, forbidden-403, store-unavailable-503 (12 each) |
| ev-action | positive-current, historical-before-intent (missing intent), historical-before-action, not-found-404, refused-reversed, refused-span-32d, refused-bad-known-at, no-window, all-open, zero-mode-current, worstcase-positive-action, worstcase-160-2..5, worstcase-160-all-open, forbidden-403, store-unavailable-503 (18) |

That is 3 representative pairs plus 39 further states.

Link checks, not counted:
- ev-action at bare, `/verification`, `/overview`, `/execution`, `/history`, `/plan` and `/evidence`.
- The EV Work Actions tab.
- Global `/incidents` and `/maintenance`.

## Structural verdict

Panel count matches on all 84 pairs:
- Incidents: 1 panel, 'Incidents at this site'.
- Maintenance: 1 panel, 'Maintenance at this site'.
- ev-action: 1 panel, 'Declared verification plan'. Non-loaded states use the untitled R110 panel instead (titles differ, by design).

Columns:
- ev-action matches the mock exactly: Criterion / Required evidence / Current result, with the three literal criteria and 'Pending'.
- The case tables' columns (Case/Window/What happened/Linked findings/State; Work request/Asset/Activity/Outcome/Next evidence) cannot be compared with the mock, because it shows only the zero state.

Zero mode reproduces the mock's empty state.

There is no page horizontal overflow and no console error on any pair. Every closed state is within the W5-04 ruling 25/50/70 caps, and all-open is exempt under ruling 26 (B17-13).

**ev-action is the closest match in the audit so far.** The batch 4/5 Action chrome findings are resolved there (B17-07).

## Mandatory carried checks

| Item | Result |
| --- | --- |
| '1 incidents' plural (B13-01) | **Confirmed**: 'Scoped to EV · 1 incidents' and '1 maintenance' (B17-01). |
| Raw `c1 · EV_CONNECTOR` | **Confirmed** in the Maintenance Asset cell: 1 row in positive, 5 in worst case (B17-02). |
| domainActionClient window error | Case tabs: the 32-day window shows 'The window may span at most 31 days.', which is correct. The reversed window shows the backticked server text (B13-04 recurs, B17-03). B14-02 does not recur here. ev-action: not triggered, because the detail ignores the window and carries the invalid from/to onto its own link; `windowQuery` is a dead field (B17-04). |
| R88/R112 Window control | R112 is built on both case tabs: 33 px at 1440, 136 px at 390. Its register status still reads 'planned'. ev-action has none, by design (ruling 14). |
| Prose size | 14 px in state sentences and the opened basis disclosure (B1-07/B2-03). |
| Tall 390 header | ev-action refused, 403 and 404: dark block 286 px. 503: main top 397 px. Normal elsewhere (B1-02). |
| D3 R22/R23/R24/R37/R38/R60 | R24 holds: times are Etc/UTC, which is Site-local. The others do not touch these screens. |
| B4-03/B4-04/B4-05/B5-01 Action chrome | **Resolved on EV** (B17-07). They recur only on the unlinked `/overview` address (B17-08). |
| B4-19 raw event-code fall-through | Does not recur: no event list, no console errors (B17-09). |
| B13-04/B13-05 | Both recur (B17-03, B17-05). |
| B16-16 main-tab seam | Recurs on the case tabs (B17-15). |
| VERIFICATION_WINDOW/CANCELLED copy (carried Architect item) | **Not producible.** Static labels are 'Verification window' (blue) and 'Cancelled' (neutral). The item stays open (B17-12). |

## Differences (proposals)

| ID | Screens | What | Proposed disposition |
| --- | --- | --- | --- |
| B17-X1 | all | B1-01, B1-04, B2-02, B1-07, B1-02 (390 non-loaded/503), B1-53. B2-21 is not applicable (Etc/UTC) | Cite |
| **B17-01** | cases | '1 incidents' / '1 maintenance' | Cite B13-01 (D3 Medium) |
| B17-02 | maintenance | `c1 · EV_CONNECTOR` in the Asset cell | Cite B16-14 / B1-53 |
| B17-03 | cases | Backticked reversed-window text; 'work source unavailable' strip on input errors and on a 403 | Cite B13-04 (D3 Low), extend with the 403 |
| B17-04 | ev-action | An invalid window is silently ignored and carried on its own link; `windowQuery` is unread | D3 Low |
| B17-05 | cases | UUIDs in 'UTC and IDs'; 'Action ab9b6724' label; 'COMPLETE' enum; list fence hash | Cite B1-53 / B13-05 / B16-05 |
| B17-06 | ev-action | Non-loaded states: 'EV work unavailable', quoted server literals, useless Retry, h1 'Action' | D3 Low (B13-03/B14-01 pattern); R110 verified |
| B17-07 | ev-action | Chrome matches the mock; R69/R80/R109/R110/R111/R113 verified | (a); update R111 status |
| B17-08 | link check | `/overview` shows W1 chrome (B4-03/04/06); other W1 sections silently show Verification | D3 Low, shared with cold |
| B17-09 | all | No console errors; B4-19 does not recur; Vite re-optimisation was an artifact | Informational |
| B17-10 | cases | R112/R113 verified; global destination 503 under the walkthrough API | (a); update R112 status; producer note |
| B17-11 | cases | Notice drops the create-flow sentence; 'Scoped to EV' against 'Scoped to Depot' | Cite B13-16 (R35); D4 under R111 or D3 Low |
| **B17-12** | all | CANCELLED / VERIFICATION_WINDOW / any later lifecycle state are not producible | **Architect item stays open**; producer mode for CANCEL |
| B17-13 | all | All closed states within ruled caps; all-open exempt; 390 inner scrolls | Accept; cite B13-18 |
| B17-14 | cases | Default window excludes today (honest window-scoped copy) | Cite B14-09 |
| B17-15 | cases | Main tabs go to non-EV pages and drop the window | Cite B16-16 / B14-10 |
| B17-16 | all | unknown/pending/stale unavailable; Incident Finding link is pure-vector; whole-API 503 | Producer note |

## Blockers

- B17-12: no committed producer mode yields CANCELLED, VERIFICATION_WINDOW, closed or completed case states, or any EV Action state beyond Open. The carried Architect item cannot be captured.
- Batch 15's ledger had not landed when this batch was written. B17-08 asks batch 15 to confirm the cold analogue.

No DBs or processes remain after `drop` (see `logs/w504-drop.log`).
