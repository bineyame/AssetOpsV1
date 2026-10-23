# W5-03a independent review (E1a, E1b, E2, E3)

Reviewer: fresh Claude reviewer, 2026-10-23. Branch `task/W5-03a-ev-selected-depth`, worktree
`AssetOpsV1-review4`, head `03a20a7e` (builder head `08b1084f` with main merged in). Diff `git diff main...HEAD`.
I judged against `.agent/W5-03-build-spec.md` (closure 2, the Codex retrospective and the W5-03a pre-flight rulings at
:669-725), v6.9 `index.html:586-597` (`availability`, `energy`), `lineChart` :214-238, the `panel` helper :183, and
the register `.agent/mock-departure-register.md`.

## Verdict: REVISE

There are 4 High, 3 Medium and 8 Low findings. The backend reads, producers, extraction and wiring are correct, and
the off-list ledger edits are justified. All four High findings are visible fidelity defects on the two pages. Three
are small builder fixes. One (H4) needs an Architect correction to the ruling text. The full real-Postgres suite on
the merged revision has not run yet. It is required before merge (spec:715) and is still outstanding.

## High

**H1. The chart notes render at body size because `chart-note` has no global style.**
- Where: `frontend/src/sites/EvAvailability.tsx:255` and `:258`; `frontend/src/sites/EvEnergy.tsx:172` and `:230`.
- What is wrong: the app's global class is `.v69-chart-note` (`frontend/src/ui/primitives.css:4491`). `.chart-note` is
  styled only under `.estate-portfolio` (`frontend/src/estate/estatePortfolio.css:8`).
- Evidence: in `availability-status-gap-1440-app.png`, `energy-complete-1440-app.png` and `energy-pending-390-app.png`,
  the connector notes, the import note and the conclusion note render as large prose. The mock renders them as small
  muted chart-notes. The page caps hide this.
- Fix: use `v69-chart-note`. The `not-available-yet v69-chart-note` precedent is at `ColdAssessmentViews.tsx:123`.

**H2. The full-schedule bound value is unstyled.**
- Where: `EvAvailability.tsx:296` uses `className="metric-value"`.
- What is wrong: the app has no `.metric-value` rule. The panel value primitive is `.v69-panel-value`
  (`primitives.css:5269`).
- Evidence: in the captures, `70.00–100.00%` renders at body size. Mock `availability` shows `87.5–93.75%` as the large
  panel metric.
- Fix: use the app's panel-value class.

**H3. The chart legend sits above the chart. The mock puts it below.**
- Where: `frontend/src/sites/evDepthGraphics.tsx:69-80` renders the legend before the scroll region.
- What is wrong: mock `lineChart` returns `<svg …>${legend(…)}` (`index.html:233`), so the legend comes after the svg.
  No ruling moves it, and there is no `MOCK DEVIATION` label or register row. That makes it an unlabelled departure,
  which is High.
- Fix: render the legend after `.ev-depth-graphic__scroll`.

**H4. The ruling misplaces the import note. Architect ruling needed.**
- What the ruling says: pre-flight E3 (spec:711) says "Beneath the figure render the mock panel note `Observed import is
  not proof of vehicle-requested power`".
- What the mock does: it passes that sentence as the `panel()` third argument, `sub` (`index.html:595`). The helper
  renders `sub` as the `<p>` under the `<h2>` in `panel-head` (`index.html:183`), so it is the panel sub-line, not a
  note under the chart.
- What the builder did: followed the ruling (`EvEnergy.tsx:172-174`).
- Why it is High: the ruling cites "the mock panel note" but changes its position, without a `MOCK DEVIATION` label or
  register row. Under ROLE_CONFIG this is a D3 structural oversight, a defect to correct before merge.
- Fix: the Architect amends the ruling. The builder then passes the sentence as `<Panel … description={IMPORT_NOTE}>` at
  `EvEnergy.tsx:165`, the same pattern as `RecordsPanel` at `EvAssessmentViews.tsx:439`, and drops `:172-174`. Update the
  `evEnergy.test.tsx` note assertion and recapture the four Energy states.

## Medium

**M1. The observed peak and the plotted samples use different predicates. Architect ruling needed.**
- The two sources:
  - `observed_peak_import_kw` is overview `site_power.observed_peak_kw` (`ev_depth.py:60,68`). That comes from W2
    `_site_import` (`ev_site_reads.py:481-489`): any accepted, non-`EXCLUDED`, overlapping import row, with no
    selected-set, GOOD, `INTERVAL_MEAN` or `unit='kW'` filter.
  - `import_samples` and `peak_sample_at` keep only selected, GOOD, `INTERVAL_MEAN`, `kW` rows (`ev_depth.py:103-138`).
- The consequence: the card peak and `peak_below_limit` can differ from the plotted marks and the peak time. Under
  `PENDING_RECOMPUTE`, a post-selection row can set the peak and drive `Observed peak below limit: Yes`.
- What the spec says:
  - The pre-flight ruling (spec:691) says "Keep the W2 `_site_import` coverage/peak rule aligned by using the same
    predicate".
  - Spec:17 says pending never presents a current positive.
  - The closure-2 table (spec:106) maps the field to the overview value.
- No test covers a divergence. The fixture happens to agree.
- Needed: the Architect chooses which source wins. The likely answer is the peak of `import_samples`. Then add a
  focused test with an unselected higher row.

**M2. The builder added literals and choices the spec does not give. Architect ruling needed for each.**
Under ROLE_CONFIG, an implementer choice the spec did not fix is a defect. Every item below is user-visible or
accessible text.

Energy:
- `EvEnergy.tsx:144`: card-note fallback `No time-valid site limit declared`. The ruling gives only `Time-valid
  configuration`.
- `EvEnergy.tsx:112`:
  - The `{window_duration}` slot is rendered as `Selected {n}-hour window`, with hours to two decimals (`hoursText`).
  - The fallback `No selected window` is a builder literal.
- `EvEnergy.tsx:175-178`: disclosure summary `Measure and value detail`, and hidden heading `Import measures`.
- `EvEnergy.tsx:188,192,200,205`: the `Measure` row labels `Accepted import samples`, `Observed peak import (sample
  peak)`, `Declared site limit` and `Sample {HH:MM:SS UTC}`. Only `Peak sample time (UTC)` is ruled (spec:190).
- `EvEnergy.tsx:94-96`: an amber tone for `No`. The ruling names only green `Yes` and amber `Not established`.
- `EvEnergy.tsx:159-163`: the placement of `No complete metered delivery is established for this window.` The literal
  is ruled, but its position (between the disclosures and the panels) is not.
- `EvEnergy.tsx:121,138`: accessible labels `Charging energy` on the status bar and cards.

Chart (`evDepthGraphics.tsx`):
- `:103`: limit end-label text `{kW} kW limit`. The ruling says "with an end label" and gives no text.
- `:88`: a `kW` suffix on every y tick. The mock shows bare numbers with a single `kW` unit label above the axis.
- `:109`: mark `<title>` text `Site import {kW} kW · {HH:MM:SS} UTC`.
- `:74`: the `Site power limit` legend entry is hidden when there is no limit. The ruling lists both legend labels
  unconditionally.
- `:83`: a plot-frame `rect` is always drawn. The mock has none, and the ruling asks for a frame only for the empty
  state.

Availability (`EvAvailability.tsx`):
- `:107`: fallback `Known hours and coverage unknown`.
- `:110`: `coverage Unknown` when scheduled seconds are 0 (the declared-empty capture shows `0 / 0 known hours; coverage
  Unknown`).
- `:58`: hours to two decimals in the notes.
- `:275`: next-evidence fallback `any unknown scheduled time`. It also shows on the declared-empty capture, where no
  time is scheduled.
- `:302`: the unbounded bound prose (only the last sentence of the ruled form).
- `:255`: no-connector sentence `No selected connector has a service schedule in this window.` The ruling asks for "an
  honest no-data sentence" and gives no literal.
- `:114`: the `Connector` prefix is de-duplicated when the label already starts with "Connector".
- `:188`: the right-hand period is the UTC occurrence, with no `UTC` suffix. The ruling says "configured local service
  period", but the DTO carries no offset.
- `:244-248`: the start/mid/end labels align to the track. In the mock they span the full row.
- `:278,287`: accessible labels `Connector availability`.

**M3. Energy card units are full size.**
- Where: `EvEnergy.tsx:32-33,139-146`.
- What is wrong: the mock renders `120 <small>kWh</small>` and `76 <small>kW</small>`. The app renders `30.000 kWh`
  and `60 kW` with the unit at value size.
- Why it is not ruled: spec:190 fixes the text, not the typography. Precedent for small units exists, for example
  `EstatePortfolio.tsx`, `SiteFinancials.tsx` and `MiniScenarios.tsx`.
- Fix: no register row covers this. Pass the value as `<>{v} <small>kWh</small></>`.

## Low

**L1. `selected_provenance_on` is unused, untested and has a latent case bug. Architect ruling needed.**
- Where: `postgres_assessment_store.py:3054-3062`.
- The bug: `allowed = set(sel["evidence_ids"])` is not lowercased, while `cited` is.
- The open question: the ruling (spec:691) asks for depth-specific citations through this method, but no DTO field
  carries them.
- Needed: the Architect names the field, or the method is removed.

**L2. Links can end in `known_at=None`.**
- Where: `ev_depth.py:202-203`.
- What is wrong: the links suffix only checks `snap["lo"]`, so a read with no resolved watermark gets the literal
  `known_at=None`. The W2 precedent omits the query when `known` is None (`ev_site_reads.py:437`).

**L3. The Health sort key can raise `TypeError`.**
- Where: `ev_depth.py:181`.
- What is wrong: `y.get("start_at") or ""` mixes datetime and str when one faulted session lacks `start_at`. This is
  W5-03b-facing.

**L4. Some tests are weaker than the comments or ruling claim.**
- `test_w503_ev_availability_postgres.py:245` accepts `CURRENT` or `HISTORICAL` for the historical read. The HISTORICAL
  state is proved only by the depth test at `:298`.
- `:274-277` claims the gap sits "between two available spans" but asserts only the Unknown span.
- The Energy route has no persisted `PENDING_RECOMPUTE` or `HISTORICAL` assertion.
- No test checks that `/energy` and `/health` keep the selected source-provenance block while pending.

**L5. The rule-5 non-vacuity proofs are manual.**
- The four proofs are recorded in the handoff (reverted with `git checkout`), not committed guard fixtures as spec:709
  asks.
- This is acceptable: there is no shell-overflow fixture harness, and the cold registration has the same precedent.
  The Architect should note it.

**L6. `overview` now reads `foundation_on` twice.**
- Where: `ev_site_reads.py:596,647`.
- Why it is minor: both reads are on the same REPEATABLE READ snapshot, so the output is unchanged. The cost is one
  extra query.

**L7. Bridge first-column cells are bold.**
- Where: `EvEnergy.tsx:251`.
- What is wrong: they are `<th scope="row">`, which renders bold. The mock's first column is regular weight.
- Related, ruled behaviour: at 390 the sticky table pushes `Result` and `Limit` off-screen behind horizontal scroll,
  while the mock wraps all four columns. Spec:48 rules this behaviour, so it is informational only.

**L8. Stale text in the panel contracts.**
- The six `v69-panel-contracts.json` rows now carry tier `Real with honest gaps`. Their other fields still say `GAP: …
  not yet designed`, `No product claim…` and `post-S7 EV domain`.
- This is the minimum change and is acceptable. Update the fields when the tier is approved.

## Items for the Architect

1. **H4.** Correct the pre-flight E3 placement of the import note to the mock sub-line, or label and register it as a
   departure.
2. **M1.** Choose the single source for the observed peak and `peak_below_limit`: the overview predicate or the
   selected samples.
3. **M2.** Rule each listed literal and placement: keep, replace or register.
4. **L1.** Name the DTO field for `selected_provenance_on`, or remove the method.
5. **L5.** Accept the manual rule-5 non-vacuity proofs in place of committed fixtures.
6. **Off-list edits: confirm the ownership.** I found both edits required and minimal:
   - `check_v69_ledger.py:121-133` refuses a non-null `to_candidate` once coverage is no longer `deferred`. There are 40
     null precedents on main.
   - `:153-168` requires each panel-contract tier to equal its screen tier.
7. **Builder interpretations to confirm.**
   - Null `connector_id` binds to the component, applying W2 `_connector_mismatch`.
   - An unusable selected row ends the prior observation.
   - `SITE_METER` means a METER fed directly by a BUS node.

## Correctness verified (no finding)

- **Exact window.** Every producer calls `select_exact(built, LO, HI)` (`ev_depth_cases.py:44,80,114`).
- **Status gap.** The producer drops exactly the five c1 reports in `[08:40,08:45)` before publication (`:55-82`). The
  test asserts both that exact Unknown span and that no c1 state row is accepted in the gap (`:274-279`). The capture
  agrees.
- **Foundation reads.** `foundation_revision_on` keeps the original predicate and SQL with added columns, and
  `foundation_on` delegates to it without changing its output (`postgres_assessment_store.py:3028-3053`).
- **`selected_foundation`.** It never falls back, it checks validity coverage, and it is tested.
- **Energy extraction.** `energy_on` is a verbatim move of the inline overview block (`ev_site_reads.py:639-673`), and
  `overview` still computes its other fields. Adjacent W2-07 tests ran per the handoff: 89 passed on `bdd56fbd`.
- **Wiring.** `main.py` and `composition.py` match spec:139-160 verbatim, and `test_main_mounts_the_three_depth_routes`
  covers the mount.
- **Calculation.** It follows spec:19 and the pre-flight E1a ruling:
  - selected-ID intersection;
  - GOOD, non-`EXCLUDED`, clock-attested rows;
  - Decimal minute cadence;
  - equal-time conflict and duplicate handling;
  - clipping at the next transition, the cadence, the schedule and the window;
  - conservation at connector and Site levels;
  - `DECLARED_EMPTY` gives zero seconds and null ratios.
- **Rule 5 in `shell-overflow.ps1`.** The registration mirrors the cold block: module and selector variables, the CSS
  `overflow-x` check, the region and svg scan, and the zero-wrapper and zero-svg failures. `EvEnergy.tsx` has no svg.

## Checks I ran

| Check | Result |
| --- | --- |
| `npx.cmd tsc --noEmit` (frontend) | exit 0 |
| `npx.cmd vitest run evDepth.test.tsx evEnergy.test.tsx evAssessmentRoutes.test.tsx --maxWorkers=1` | 3 files, 53 passed (with React act warnings) |
| `tools/check-architecture.ps1` | passed |
| `tools/check-agent-workflow.ps1` | passed |
| `check_v69_ledger.py` | valid: 110 screens, 88 models, 258 panels |
| `check_v69_dependency_registry.cjs` | exit 0 |
| Captures (12 app pairs, 4 mock) | inspected `availability-status-gap-1440`, `availability-declared-empty-schedule-1440`, `availability-historical-390`, `energy-complete-1440`, `energy-pending-390` against `availability-1440-mock` and `energy-1440/390-mock`; H1–H4 and M3 are visible in them |

## What I could not verify

- **Postgres tests.** I did not run `test_w503_ev_availability_postgres.py` or `test_w503_ev_depth_postgres.py`, nor
  any adjacent file. The dispatch forbids it while the full suite runs, and the sandbox denied the pytest call. I cite
  the builder's runs: 23 passed on `bdd56fbd`, 12 passed on `b7fbc5ed`, and the adjacent `-n 4` set 89 passed in 748 s
  on `bdd56fbd`. None of these is on the merged head `03a20a7e`.
- **Other frontend checks.** Full vitest, `npm run build`, `tools/check-all.ps1` and the captures were not rerun. The
  builder reports 2736 passed, build OK and 11/11 guards on `51f4a610`.
- **Full real-Postgres backend suite.** Not run by anyone yet. It is required before merge (`main.py`, composition,
  guard edits).

## Residual risk the packet does not name

- **The priced path is never captured.** In the `energy-complete` capture the consequence is WITHHELD ("The gross
  tariff scenario is being refreshed."), with `quantity_kwh` null, while the selection is CURRENT. The `ESTIMATED`
  card, bridge row and conclusion note are proved only by component fixtures.
- **The fixture has no FAULTED status.** The capture vectors (`complete`) contain no FAULTED state, so `Known
  unavailable` is 0 in every availability capture. The red bar segment is proved only by the DB test (`interrupted`)
  and the unit tests.
