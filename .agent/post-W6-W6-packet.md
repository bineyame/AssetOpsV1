# Review packet: post-W6 W6-global-Work (global work lists and work request pages)

Task: the W6 card in `.agent/post-W6-audit/fix-slices.md` (amended), rulings `.agent/post-W6-W6-rulings.md` (Q1-Q21) and
`.agent/post-W6-W6-caps-rulings.md` (caps rulings 1-5, binding for this fix round). Branch `task/post-W6-W6-global`,
worktree `AssetOpsV1-review8`, from main `821ad6bf`. Final product revision **6f54ad1b**. USER_REVIEW_REQUIRED: fresh
independent review gates merge; the owner sees these screens in the post-W6 walkthrough.

## Outcome delivered
- Build phase (see `.agent/post-W6-W6-handoff.md`): backend R352/R353/R359/R360/R366 (`fe52c862`); frontend D3s R352-R372,
  R371 unknown-section route, guard rule (`5685abad`); register R396 + R65/R73/R74 coverage (`f3da6e90`).
- Caps fix round (this round):
  - Rulings 1/2: the probe's cap table now carries the ratified caps (Work done 600 @1440, History 650 @1440, plus the
    ratified former provisional caps). No CSS cap changed.
  - Ruling 3 (R356): Feeds 140 -> 125 px; fixed sum 1085; 390 px inner table minimum 1085 (`fff67f3e`).
  - Ruling 4: `frontend/src/work/CellDisclosure.tsx`. A two-line preview. When the value overflows, a visible
    "Show full" native button sits inside the two-line box, overlaid at the end of line 2 with a 16 px fade, so it adds no
    line. Expanding unclamps the full, unchanged value inline and offers "Show less". The accessible name is
    "Show full {column} for {row code}" (it starts with the visible text), with `aria-expanded` and `aria-controls`.
    Focus is visible (2 px accent outline). It is a sibling of any cell link. There is no tooltip or popover. A value that
    fits shows plainly with no button. Overflow is re-measured on mount, on resize (ResizeObserver) and on content change
    (MutationObserver).
  - Cells covered: every cell ruling 4 lists, plus three clipped lines the probe found in the listed or adjacent
    columns: Operational Record correction and Preventive plan correction (`ffcf6e13`), and the Corrective
    "Work request" Finding/Action line (`6f54ad1b`). The Finding/Action line is covered under ruling 5's "never truncate
    without disclosure"; see Known deviations.

## Files materially changed (fix round)
`frontend/src/work/CellDisclosure.tsx` (new), `GlobalIncidents.tsx`, `GlobalMaintenance.tsx`, `GlobalPreventive.tsx`,
`OperationalRecords.tsx`, `globalWork.css`; tests `work/__tests__/cellDisclosure.test.tsx` (new), `cellDisclosureStub.ts`
(new), the four page test files. Evidence `.agent/post-W6-W6-evidence/q15b/`, `b18r/`, `b19r/`.

## Acceptance (fix-round brief)
1. Caps tables. **Met.** `q15b/tools/summarize.py` CAPS = rulings 1-2; `q15b/summary.json` has 22 panel/width rows, all `pass: true`, and no provisional caps.
2. R356. **Met.** At 1440, positive (5 real rows, vertical scrollbar present): scrollWidth 1090 <= clientWidth 1090.
   Five-row 160-char probe on positive: 1090/1090. Stress (1 real row, no scrollbar): 1105/1105. Stress five-row probe:
   1090/1090. At 390 the inner horizontal scroller is kept (1085/318). Row heights: positive real 168/82/82/82/82, probe 185 each; stress probe 100.
3. In-cell disclosure. **Met.** Focused tests and revert proofs are below. The live probe drove the real React rows on all
   8 list cases x 2 widths (238 disclosures). Every overflowing value had a button. Expanding gave 0 clipped values, the
   full 160 characters, the "Show less" name and aria state, and 0 buttons inside links. Document overflow was 0, and
   every button collapsed again.
4. Q15 probe at the final SHA. **Met**, table below. Zero closed clipped cells without full disclosure, zero document overflow (closed and all-open), Preventive plan 390 = 690 at cap (not grown; ruling 5 fallback not needed).
5. Recapture, suites and guards. See Checks.

## Q15 probe (q15b, synthetic; five rows; every intended field 160 chars). Peak closed px vs ruled cap
| Panel | 1440 peak / cap | 390 peak / cap |
|---|---|---|
| Incident cases | 647 / 700 | 737 / 800 |
| Case boundaries | 103 / 150 | 126 / 150 |
| Corrective work requests | 657 / 700 | 737 / 800 |
| Preventive plan | 599 / 600 | 690 / 690 |
| Operational records | 631 / 650 | 744 / 780 |
| Record a manual reading | 325 / 400 | 513 / 600 |
| How records are used | 325 / 400 | 223 / 300 |
| WR Work done | 503 / 600 | 690 / 800 |
| WR Lifecycle | 442 / 500 | 194 / 250 |
| WR Maintenance record · activity | 622 / 700 | 763 / 900 |
| WR History | 558 / 650 | 630 / 690 |

- Closed state, clipped without full disclosure: 0 in every row.
- Document overflow: 0, closed and all-open.
- All-open state, clipped elements: only the existing three-line title/body clamps (Incident, Work request, Plan item,
  What it says). Each one's full text is shown in its open "Full ... text" disclosure in the same cell.
- Run integrity: 136 synthetic assertions verified. The skips are "no record table" on WRs that have no maintenance record, as before.
- Method:
  - The probe rewrites the real React rows in place, then clicks every "Show full" and "Show less" live.
  - The closed panel is then measured on five clones of the tallest row (the q15 method).
  - The all-open measurement opens every disclosure and sets the clones' expanded state.
- Runs:
  - All phases ran at `ffcf6e13`.
  - maint and stress were re-run at `6f54ad1b`.
  - Earlier runs are kept in `run1-fff67f3e/` (this is the run that found the correction lines) and `run2-ffcf6e13/`.
  - One run was discarded (`logs/discarded-mangled-probe/`): a PowerShell re-encode broke the "·" separator in the probe tool.
- Ports used: API 18791-18799, Vite 5391, CDP 9641. All processes were stopped by PID, and the `assetops_w601_w6q15b*_test` DBs were dropped (0 remain).

## Checks
- Focused vitest, `src/work`: 9 files, 165 tests passed (after `ffcf6e13`; maintenance file 23/23 at 6f54ad1b).
- Revert proofs, single file:
  - Each page file reverted to `f4a3ee37`: Incidents 2 fail, Maintenance 2, Preventive 2, Operational 3. Restored: pass.
  - `GlobalMaintenance.tsx` reverted to `ffcf6e13`: 2 fail.
  - `OperationalRecords.tsx` and `GlobalPreventive.tsx` reverted to `fff67f3e`: the correction test fails (1 each).
  - `CellDisclosure.tsx` deleted: import failure. Mutations: no overflow check 4 fail; no ResizeObserver 1; no MutationObserver 1; generic name 4. Restored: 5 pass.
- Full vitest: 129 files / 3079 tests passed at 6f54ad1b (5m09s, machine idle).
- Production build: `npm run build` rc 0 (only the existing >500 kB chunk warning).
- `tsc --noEmit`: clean.
- `tools/check-all.ps1 -Python <main .venv>`: 11/11 PASS at 6f54ad1b, including Architecture seams, Navigation truthfulness and Agent workflow. `check-agent-workflow.ps1` passed again after the docs edits.
- Backend: the full real-Postgres suite at the build's final backend code (backend unchanged since `fe52c862`; this round touched no backend code). Reported by the coordinator: 4063 passed and 1 environmental failure. The failure was fixed by restoring `var/sites`, and the rerun of the affected file passed 28/28. The command, wall time and JUnit counts are in the coordinator's record, not reproduced here.
- Backend focused tests (build phase): `test_w601{a,b,c,e}` 65 passed; `test_r373_request_access.py` 10 passed.
- Recapture batch-18 (list pages), `b18r/`: 186/186 indexed pairs + 44 extra (2 probe, 42 link landings; the previous 46 included a separate retry part). Titles: 186/186 match the mock, frozen and previous run. Page overflow 0, console errors 0; the only warnings are the two React Router future-flag messages. Changed against the previous run, 19 pairs, all expected:
  - Operational records at 1440: the inner 1100-in-1090 table scroll is gone (Feeds 125), 4 pairs.
  - Operational records at 390: scroll width 1100 -> 1085 in 318, 10 pairs.
  - Operational records panel heights: 702->685, 515->498, 538->520.
  - Incident cases panel heights: 293->278, 571->536, 712->677 (two-line preview).
  - Unexpected changes: 0.
  - Phases with /maintenance list pairs were captured after 6f54ad1b. inc, prev, op, hist, probe and linkmini were captured just before it; their screens' code is the same as at 6f54ad1b.
  - Retries (first runs kept in logs/firstrun): linked, linkmini and linkcold had render misses or browser stalls; linkinc and r360hist were rerun with the stale `var/sites/kobo-001.yaml` moved aside and then restored..
- Recapture batch-19 (WR pages), `b19r/`: 194/194 pairs + 12 link captures. Titles 138 match the mock (the same as before; the rest are refusal pairs) and 194 match the previous run. Page overflow 0, console errors 0, `changed_vs_previous` empty, no reruns.
  - HTTP status: mini 200/403/503; cold 200/403; EV 200/403.
  - Revision: part-detail was captured at ffcf6e13 (WR code is identical); everything else was captured at 6f54ad1b.
  - Producers: b18r and b19r shared one W502 prepare and one W504 prepare (tag w6r18r), unmodified.
  - Cleanup: all `w6r18r`/`w6r19r` DBs were dropped (count 0), and every PID was stopped..
- Previous recaptures at f3da6e90: b18 186/186 indexed + 46 landings/probe (titles 186/186 vs mock and frozen; 0 console errors; warnings only the two React Router future-flag messages). b19 194/194 pairs + 12 link captures. Refusal pairs have 0 panels, as R367 expects.

## Registry chain (Q19)
Registry: `frontend/docs/architecture/v69-dependency-registry-pilot.json`. Every node's `evidence` field is null.

| Node | Line | Status | Parents |
|---|---|---|---|
| `A-work-cases` | :57 | open | `A-actor-identity`, `A-claim-work-routes` (both resolved) |
| `A-maintenance-index` | :59 | open | `A-work-cases` |
| `A-cold-work-projections` | :160 | open | `A-cold-excursion-rules` (resolved), `A-action-index` (resolved), `A-maintenance-index` |
| `A-ev-session-rules` | :168 | open | `A-ev-role-set` (open), `A-S2-evidence` (resolved) |
| `A-ev-work-projections` | :170 | open | `A-ev-session-rules`, `A-action-index`, `A-maintenance-index` |

**A-work-cases** is resolvable now, because both parents are resolved.
- Producer: W4-01.
- Contract: `.agent/W4-01-build-spec.md`. Reviewed: `W4-01-review.md` REVISE, then `W4-01-rereview.md` ACCEPT. Closure checks: `W4-01-W3-01-closure-check*.md`.
- Tests: `backend/tests/test_w401_{work_service_postgres,work_api,migration_postgres,work_read_postgres,site_indexes_postgres}.py`.

**A-maintenance-index** can be resolved after A-work-cases.
- Producer: W4-01 site indexes plus the W6-01 global index.
- Reviews, all ACCEPT: W6-01a-A1, A2b, W6-01b, W6-01c re-review, W6-01d re-review, W6-01e.
- Backend tests: `test_w601{a,b,c,e}`, `test_w401_site_indexes_postgres.py`.
- Consumers: `frontend/src/work/{GlobalMaintenance.tsx,globalWorkClient.ts,globalWorkParts.tsx}`, with tests.
- Gap: `W6-01-closure-check-2.md` still says "NOT READY (1 small open item)", and no later clearance was found.

**A-cold-work-projections** is blocked only by A-maintenance-index.
- Producer: W5-02. Reviews: W5-02a re-review ACCEPT, W5-02b K2 and K3 re-reviews ACCEPT.
- Gap: the W5-02c K4a/K4b/K5 review file is only on branch `review/W5-02c-K4`; HEAD has only the merge `f8137643` citing it.
- Backend tests: `test_w502_domain_*`, `test_w502_cold_scenario_producer.py`.
- Consumers: `sites/{coldWorkPresentation.ts,DomainActionVerification.tsx,domainActionClient.ts,siteWorkCases.tsx,SiteWorkActions.tsx}`.
- W6 consumption: `globalWorkClient.ts` accepts a null `action_event_id` (fix `b67fd239`, with a test). No other W6 screen consumes the cold projection.

**EV equivalent:** left open.
- `A-ev-session-rules` stays open. It is blocked by `A-ev-role-set` as well as by the missing assessment-rule review.
- `A-ev-work-projections` stays open until both its open parents resolve.

Backlog carry `.ai/MILESTONE_REVIEW_BACKLOG.md:2428` asks for one owning unit for the chain. This packet only supplies evidence and closes no node. Per Q19, closure is a separate registry submission.

## Known deviations
- **Three-line versus two-line clamp.** The existing `.global-work-clamp` was three lines, not two. Ruling 4 assumed two.
  The listed cells now use a two-line preview (`.global-work-clamp--two`), with the button inside line 2, per rulings 4
  and 5 ("no third closed line", "must not consume a new line"). Other cells keep their three-line clamps and existing
  "Full ... text" disclosures. Panel heights did not grow, because row height is set by the title cells.
- **Clipped lines outside ruling 4's list.** The disclosure also covers three lines the list does not name: the Record
  correction line, the Plan item correction line, and the Corrective Work request Finding/Action line. The original q15
  heuristic counted the Finding/Action line as disclosed only because the cell has a "Full title text" disclosure that
  does not contain it. Covering these follows ruling 5 ("never truncate a value without its full disclosure"), but the
  Architect should confirm.
- **Toggle overlay.** The toggle covers the end of line 2 in narrow columns (for example the 90 px Record column).
  "Show full" reveals the covered text.
- **Probe and React.** The probe's five-row closed measurement uses DOM clones, which are not React-managed. The live
  open/close checks ran on the real React rows (5 real rows on the positive cases).
- **Backend suite evidence** is the coordinator's report. This round changed no backend code.

## Residual risk / gaps (Q20, unchanged)
- No producer emits: VERIFICATION_WINDOW (no writer); cold/EV preventive and operational rows; a list with all three
  domains; pending or stale global states.
- Five rows with 160-character values come only from the synthetic probe.
- The R373 EV positive Site Work case-detail 503 belongs to W5-EV-Work.

## User-review focus
- The "Show full" affordance at 1440 and 390: `q15b/part-*/*-SYNTHETIC-closed.png` and `-allopen.png`.
- Operational records at 1440 with the vertical scrollbar.
- Whether the three extra disclosed lines (two correction lines and the Finding/Action line) are wanted.

## Review fix round (M1, M2, L2, L3)
- M1: `Pager` treats the offset as unknown when `cursor !== null && (trail.length === 0 || trail[0] !== null)`. Each of
  the four list tests opens a later page from its URL, clicks Next and still expects `Later page · 1 of 12` (no
  numeric range). Revert proof: restoring `trail.length === 0` fails all four.
- M2: `test_action_codes_enter_the_basis` (`backend/tests/test_w601a_global_incidents.py`, cold-chain fixture with a
  bound coded Action) changes every stored ACT code via monkeypatched `GlobalReadTx.action_codes` and expects a new
  `selection_token`, same rows. Revert proof: `global_index.py:352` set to `if False:` fails it; restored. Ran against
  `assetops_test` (2 passed with the adjacent linked-ids test).
- L2 (Choices made): the six undefined `var(--muted, #6b7a90)` uses in `globalWork.css` (10 to 12 px lines) now use
  `var(--text-secondary)` (#617087): 5.03:1 on `--surface-raised`, 4.69:1 on `--surface-page`, 4.56:1 on
  `--surface-sunken` (the old fallback was 4.36/4.07/3.96). `--text-muted` was rejected (4.24:1 on the page surface).
  Colour-only change, no recapture.
- L3: `CellDisclosure` takes focusables whose `offsetTop >= clientHeight` out of the tab order (`tabindex=-1`) while
  collapsed and clipped, restoring the prior value on expand or fit. Test mocks `offsetTop` (jsdom has no layout); the
  real-browser clip geometry is unmeasured. Revert proof: replacing the condition with `false` fails the test.
- L1: untouched, logged by the coordinator as a backend-basis follow-up.
