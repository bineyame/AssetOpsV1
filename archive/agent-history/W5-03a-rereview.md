# W5-03a fix-round re-review

Reviewer: fresh Claude reviewer, 2026-10-23. Worktree `AssetOpsV1-review6`, branch `task/W5-03a-fix`, head `452fe650`.
I reviewed the fixes in `git diff 08b1084f..HEAD`, and only the W5-03a files: `frontend/src/sites`, the backend EV depth
files and tests, and the v69 ledger, contracts and registry. I judged them against:
- `.agent/W5-03a-review.md`;
- `.agent/W5-03a-review-rulings.md` (rulings 1-8 and the fix-round rulings 1-4);
- the review correction table in `.agent/W5-03-build-spec.md:717-746`;
- mock `index.html`, using the 22 recaptured pairs in `.agent/W5-03a-evidence/` (`evidence.json` revision `77d5b22a`;
  the only change since then is a backend test).

## Verdict: REVISE

There are 0 High, 2 Medium and 1 Low findings. Almost everything closes as ruled. Two things block: one review item
that is not closed visually (M3), and the weakened peak test, where the dispatch asked me to decide.

## Medium

**RR-M1. The M3 small Energy units are not closed visually.**
- Where: `frontend/src/sites/EvEnergy.tsx:33-41` and `frontend/src/ui/primitives.css:4432-4440`.
- What is wrong: the markup is now `{n} <small>kWh</small>`, as ruled. But the app has no rule for `small` inside
  `.v69-metric__value`, so the unit gets the browser's `smaller` size at the value's 600 weight and -0.7px tracking.
  The mock has `.metric-value small{font-size:12px;font-weight:400;letter-spacing:0}` (`index.html:4`).
- Evidence: in `energy-complete-1440-app.png` and `energy-pending-390-app.png`, `30.000 kWh`, `60 kW` and `80 kW` show
  the unit at close to number size and in bold. In `energy-1440-mock.png` and `energy-390-mock.png`, `120 kWh` and
  `76 kW` have a small, light unit.
- Why it matters: M3 was to be fixed "exactly as reviewed", and the visible result is still the reviewed defect.
- Fix:
  - Add `.v69-metric__value small { font-size: 12px; font-weight: 400; letter-spacing: 0; }`. The mock rule is global
    to `.metric-value`.
  - Recapture the four Energy states with data at 1440 and 390.

**RR-M2. `test_energy_peak_is_one_selected_peak` dropped its state check. Settle the recompute, then assert CURRENT.**
- Where: `backend/tests/test_w503_ev_depth_postgres.py:352-358`.
- What happened: the builder replaced `assert reselected["selection"]["state"] == "CURRENT"` with a comment saying "the
  state may be pending here".
- The state is not "may be": it is always `PENDING_RECOMPUTE`.
  - Each `add_import` clone insert runs `ev_enqueue_window` (migration `0025_w2_ev_session.py:267-291`), which leaves a
    PENDING `ev_charging` job over the window.
  - `select_exact` writes a selection but never runs or closes that job.
  - The open job makes the read pending (`postgres_assessment_store.py:2726-2731`).
- Why it matters: with the check gone, the ruling-2 "selected but failing GOOD/`INTERVAL_MEAN`/`kW`" case is proved only
  under pending. The pending test, `test_energy_peak_ignores_unselected_row_while_pending`, covers only the unselected
  row. So nothing proves a CURRENT read, where `Yes` is a current positive, with a selected failing row. That is a
  silent weakening.
- Why PENDING_RECOMPUTE is the wrong expectation: asserting it would only pin a side effect of the test harness. The
  test is about the settled `complete` case, and the docstring describes that case.
- Fix:
  1. In the test, call `run_worker(built)` before `select_exact(built, LO, HI)`. This is the same `settled` pattern as
     `ev_depth_cases.py:40-44`.
  2. Restore `assert reselected["selection"]["state"] == "CURRENT"`.
  3. Correct the comment.
- I checked that this works with a throwaway test, since deleted. It ran `settled("complete")`, then two `add_import`
  bad rows, then `run_worker`, then `select_exact`. The result:
  - the state was `CURRENT`;
  - both bad IDs were in `accepted_evidence_ids`;
  - `_peak_view` was unchanged;
  - the overview peak was 600.
- The later "unselected higher row" step can stay as it is. A late row naturally makes the read pending, and that step
  asserts no state.

## Low

**RR-L1. The R87 departure has no code label.**
- Where: `frontend/src/sites/EvEnergy.tsx:102` (`answerTone`).
- What is wrong: ruling 3 makes the selected `Yes`/`No`/`Unknown` tone **MOCK DEVIATION (D4)** R87. Register row R87
  exists (`mock-departure-register.md:147`), but no `MOCK DEVIATION (D4) R87` label appears in `EvEnergy.tsx`. The
  header lists R46-R55 only. R86 is labelled correctly at `EvAvailability.tsx:192`.
- Fix: add the label at `answerTone` or in the header list.

## Closure check (review findings and rulings)

| Item | Status | Evidence |
| --- | --- | --- |
| H1 `v69-chart-note` | Closed | Connector, no-connector and conclusion notes use `v69-chart-note`; small and muted in the status-gap and complete captures |
| H2 `v69-panel-value` | Closed | `70.00–100.00%` and `Unknown` render at panel-value size (status-gap 1440, declared-empty 390) |
| H3 legend below the chart | Closed | `evDepthGraphics.tsx:107-119`; captures at both widths |
| H4 / ruling 1 import note | Closed | `Panel description={IMPORT_NOTE}`; renders as the sub-line under the heading, as in the mock |
| M1 / ruling 2 one selected peak | Code closed; test weakened | `observed_peak(samples)` feeds the card, `peak_sample_at` and `peak_below_limit`; overview unchanged. See RR-M2 |
| M2 / ruling 3 literals | Closed | Checked each row of the spec:719-744 table against the code: limit fallback; window note with no fallback; red `No`; one `kW` unit and bare ticks; `{kW} kW limit` in muted fill; per-mark title; both legend labels with a muted `--none` swatch; frame only at zero marks; `coverage not applicable`; the four next-evidence branches; unbounded prose; no-connector note position; case-insensitive `Connector` prefix; UTC period (R86); full-row axis |
| M3 small units | **Not closed visually** | RR-M1 |
| L1 / ruling 4 | Closed | `selected_provenance_on` removed (no references); pending provenance asserted for energy and health |
| L2 `known_at` | Closed | `ev_depth.py:214-219` |
| L3 sort key | Closed | Homogeneous ISO-string key (`plain` gives fixed-format UTC); test added |
| L4 test strength | Closed | Exact CURRENT and HISTORICAL; gap neighbours; energy and health pending/historical with selected provenance |
| L5 / ruling 5 | Closed | Probes kept; the unmodified `shell-overflow.ps1` passes (exit 0, my run) |
| L6 one Foundation read | Closed | `_foundation(ctx)` follows the existing per-context memo pattern (`accepted`, `sessions`, `tariffs`) |
| L7 bridge weight | Closed | `th.ev-bridge-rowhead` at weight 400, still `scope="row"` |
| L8 / ruling 6 panel contracts | Closed | All six rows carry the ruled strings exactly; tier `Real with honest gaps`, approval pending |
| Fix-round ruling 1 (telemetry-only) | Closed | `EvAvailability.tsx:281-288` |
| Fix-round ruling 2 (decimal hours) | Closed | Chart notes `{H} h`, bound prose and `missing {H} hour(s)` from exact seconds (`0.6 hours`, `1.4 / 2 hours`) |
| Fix-round ruling 3 (ledger `unresolved_panels: []`) | Closed | Both screens; ledger checker valid |
| Ruling 7 interpretations | Closed | Null-binding and unusable-transition pure tests; connector-meter test already existed |

I found no new implementer decisions beyond the ruled table. The main-merge files (W6-01e operational records and the
shell) are outside this slice and I did not review them.

## Code quality of the new helpers

- **`observed_peak` / `_peak_sample` (`ev_depth.py:134-151`).** Correct. It returns the stored value verbatim, gives an
  equal maximum to the earliest `(source_time, evidence_id)` through a strict `>` over sorted input, and returns null
  when there are no samples. The comparison is Decimal and `peak_below_limit` compares as Decimal too. Small nit, not a
  finding: `_peak_sample` runs twice per read.
- **`ev_depth_cases.add_import` (`ev_depth_cases.py:118-142`).** Sound for a test helper:
  - it copies the earliest import row deterministically, with a fresh ID, message and ordinal (one transaction per
    call), so repeated calls do not collide;
  - it overrides only value, quality and unit;
  - its `ON COMMIT DROP` temp tables are scoped to one transaction.
  The docstring is accurate. The trigger side effect is worth noting: every call enqueues a recompute job, which is the
  root of RR-M2, and the docstring does not say so.
- **`_foundation(ctx)` (`ev_site_reads.py:481-485`).** Correct and consistent with the class's memo keys. Both
  `overview` and `energy_on` now share one read per context.

## Checks I ran

| Check | Result |
| --- | --- |
| Focused Postgres, `-n 4`, private `assetops_w503rr_test` (run-owned clones): `test_w503_ev_availability_postgres.py`, `test_w503_ev_depth_postgres.py` and my throwaway settle test | 30 passed, 0 failed, 0 skipped, 152 s (JUnit). The two committed files make up 29 of the 30, including both peak tests. The base DB was dropped afterwards and the throwaway file deleted. `PYTHONPATH` had to point at the worktree: the shared `.venv` editable installs resolve to the main checkout |
| `npx.cmd tsc --noEmit` | exit 0 |
| `npx.cmd vitest run evDepth evEnergy evAssessmentRoutes --minWorkers=1 --maxWorkers=1` | 3 files, 54 passed |
| `tools/check-architecture.ps1`, `tools/check-agent-workflow.ps1` | passed |
| `check_v69_ledger.py` | valid: 110 screens, 88 models, 258 panels |
| `check_v69_dependency_registry.cjs` | exit 0 |
| `tools/checks/shell-overflow.ps1` | exit 0 |
| Captures | Inspected the `energy-complete-1440`, `energy-pending-390`, `availability-status-gap-1440` and `availability-declared-empty-schedule-390` app captures against the four mock PNGs |

## Not verified

- Full vitest, `npm run build` and `check-all.ps1`. I cite the builder's run on `77d5b22a`: 118 files, 2748 passed;
  build OK; 11/11 guards.
- The adjacent W2 Postgres set. I cite the builder: 84 passed and 1 failed (the dropped assertion) in 1010 s.
- The capture tool was not rerun.
- The full real-Postgres backend suite on the final revision. It is still required before merge (ruling preamble and
  spec:715). Nobody has run it.

## Residual risk

- **Coverage lines render at body size.** The Energy partial/unknown coverage lines (`EvEnergy.tsx:165-169`, class
  `prose`) render at body size between the cards and the panels (`energy-pending-390`). They are the registered D2 R49
  addition and were not part of this round, but they read heavier than the mock's small card note. Worth a look in the
  W1-end UI pass.
- **Priced path and FAULTED state.** Still capture-unproven, as the first review noted.

## Coordinator verification of re-review closure (2026-10-23)
RR-M1 (`.v69-metric__value small` 12px/400), RR-M2 (run_worker before select_exact; CURRENT asserted), Low (R87 label) verified in 0df7c366 diff. Focused Postgres 85 passed; targeted vitest 57; build, tsc, check-all 11/11. Verdict: ACCEPT. Full backend suite 3965 passed on 03a20a7e; the fix rounds touch no shared plumbing (tiered testing: scoped regression).
