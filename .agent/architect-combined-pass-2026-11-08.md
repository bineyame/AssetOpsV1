# Architect combined pass, 2026-11-08: backlog sort, DS-1 scope, end-game order

Claude Architect (binding: Claude, `.ai/ROLE_CONFIG.md:9`, owner 2026-10-27). Read-only on code, main `b0663c1eb`. The
owner asked for one combined end-to-end pass: "One combined Architect pass. It sorts the minor notes and lagging tests,
including "No action yet" above "Verified" and the label wrap. It also plans both demo-script HTML documents." Then:
"The two demo-script documents, then the final checks and the demo-day build, then your walkthrough."

Evidence for the four pure drift failures: I ran them on main with no DB URL. Result: `4 failed, 52 passed, 3 skipped`
plus the w502 collection error. Each cause is given below with file:line. No DB was used.

Buckets: **(1)** before DS-1, **(2)** before E3 (the demo-day build), **(3)** after the demo. Items that are already
closed on main are listed separately in §A.4 with evidence, so they do not take a bucket.

Rule applied (owner 2026-11-05, demo-critical scope only): an item goes before the demo only when it is visible on a
demo beat, or when the end-game suite (E2) cannot be green without it. Everything else is bucket (3).

---

## Part A. The backlog sort

### A.1 Bucket (1), before DS-1: two demo-visible fixes

Both change what the demo script's screenshots show, so they land before DS-1 takes its pictures.

**A1-a. K8 L1: the Portfolio fuel row shows a bold "No action yet" above "Verified"** (`review-K8.md` L1).
- Cause: `frontend/src/estate/EstatePortfolio.tsx:202` prints "No action yet" whenever `row.action_id` is null. §9p.2
  item 5 keeps a fuel row's `action_*` null by design, because the fuel Action is a domain Action with no Action page.
  The server's thread label (`backend/assetops_backend/estate/portfolio.py:266`, `FUEL_THREAD_LABEL`) already says
  "Verified". So the code is wrong and the wire is right. The fix is frontend-only.
- Fix, in `EstatePortfolio.tsx`, the Action cell (`:196-214`):
  - Compute `const fuelThread = row.action_id === null && row.mechanism === "UNEXPLAINED_FUEL" && row.workflow_label
    !== "No action agreed yet";` ("No action agreed yet" is the server's no-thread default, `portfolio.py:266`).
  - When `fuelThread` is true, render `<strong data-portfolio-workflow>{row.workflow_label}</strong>` in place of the
    bold "No action yet". Do **not** render the `<span className="workflow-text" data-portfolio-workflow>`, so the
    label appears once and only one `data-portfolio-workflow` element exists. Keep the existing `action_id === null`
    branch below it unchanged ("Review finding" link to the fuel Finding page, or "Finding detail unavailable").
  - When `fuelThread` is false, the rendering is byte-identical to today (every Cold, EV, Kobo row, and a fuel row
    with no thread).
  - Code comment on the branch: `// MOCK DEVIATION MD-FUEL-K4-1 (Architect combined pass 2026-11-08, K8 L1): v69 has
    no fuel row; a fuel Action has no Action page, so the column shows the fuel thread's state in bold.`
  - No new copy, no backend change and no wire change.
- Tests, in `frontend/src/estate/__tests__/estatePortfolio.test.tsx`:
  - Edit the R3p fuel-row case (`:999-1034`). Replace `expect(text(tr)).toContain("No action yetVerified")` (`:1026`)
    with three assertions: `text(tr)` does not contain "No action yet"; the row's Action cell (6th `td`) text is
    exactly `"VerifiedReview finding"`; `tr.querySelectorAll("[data-portfolio-workflow]").length === 1`.
  - Add one case: the same fuel row with `workflow_label: "No action agreed yet"` still reads
    "No action yetNo action agreed yet" (the no-thread fallback is unchanged).
  - `:182` (a non-fuel row with a null action) must stay green unchanged. It proves the other rows are untouched.
  - Run: `frontend/src/estate/__tests__/` (the whole folder; vitest, scoped).

**A1-b. K8 L2: the Kisiwa Service bar label wraps to four lines** (`review-K8.md` L2).
- Cause: `frontend/src/sites/MiniPerformance.tsx:1140` builds the bar label as `${feederName(row)} · Critical load`.
  `feederName` (`:976-981`) gives a non-clinic critical load the suffix " feeder delivered power". The Kisiwa label
  becomes "Cold store (ice and fish) feeder delivered power · Critical load", which wraps to four lines and pushes
  "Coverage" below the bounded panel's fold at 1440.
- Fix, in `MiniPerformance.tsx`. Only the chart label changes:
  - Add and export `barLabel(row: ServiceRow): string`:
    - not CRITICAL: `feederName(row)`;
    - CRITICAL and `feederName(row) === CLINIC_FEEDER_LABEL`: `` `${CLINIC_FEEDER_LABEL} · Critical load` `` (Kobo
      byte-equal);
    - otherwise: `` `${row.load_label} · Critical load` ``. For Kisiwa that is "Cold store (ice and fish) · Critical
      load". The panel heading "Where the power went" already says it is delivered power.
  - `:1140` uses `label: barLabel(row)`. The load table (`:1188`, `feederName`) and the critical metric card are
    unchanged.
  - Comment above `barLabel`: `/** MOCK DEVIATION MD-KIS-K1-1 (combined pass 2026-11-08, K8 L2): a non-clinic critical
    feeder's bar label drops "feeder delivered power" so it fits the bar-label column; v69's clinic words are kept. */`
- Tests, in `frontend/src/sites/__tests__/miniServiceRoutes.test.tsx`:
  - Beside the `feederName` describe (`:136-147`), add a `barLabel` case covering the three branches. The
    expectations are: "Clinic feeder delivered power · Critical load" for "Health post"; "Cold store (ice and fish)
    · Critical load"; and a non-critical row equal to its `load_label`.
  - The R309 case (`:349`, "Critical load" beside the red bar) must stay green unchanged.
  - Run: `frontend/src/sites/__tests__/miniServiceRoutes.test.tsx` plus the other `miniService*` and `miniPerformance*`
    files in that folder.
- Height check: on the capture retake (§A.5), the "Coverage" disclosure must be fully visible inside "Where the power
  went" at 1440, with no internal scroll needed. Measure the panel's `scrollHeight <= clientHeight` (not the page
  width). If it still clips, stop and report. Do not widen the column on your own.

### A.2 Bucket (2), before E3: lagging tests, so that E2 can be green

Each item has a verdict. **Stale** means the code changed on purpose and the test expectation lags. **Wrong** means the
code or the test code is broken.

| # | Test | Verdict | Evidence | Fix |
|---|---|---|---|---|
| T1 | `backend/tests/test_ch1a_grading.py::test_period_bounds_addis_utc_tue_only_and_24h` | **Stale** | CH-9 u2 (`595ce7bb3`) removed the `midday` period on purpose: "replaces noon_headroom_kw … noon wording removed". `chain/grading.py:48-51` now knows only `PERIOD_OPERATING_HOURS`. The test still asks for `"midday"` at `:111-112`. | Replace `:111-112` with `with pytest.raises(ValueError, match="unknown period 'midday'"): period_bounds(cal.entry_for("ADDIS"), "Africa/Addis_Ababa", date(2026, 10, 31), "midday")`. This pins the removal. `pytest` is already imported (`:8`). |
| T2 | `backend/tests/test_out_b1_board.py::test_mini_protect_battery_outcome_measured_without_warning` | **Stale** | K4b (`f7e219a46`) added MG-8 to the catalogue (`outcomes/catalogue.py:51`, after MG-4). Real Kobo composes MG-8 as not applicable (`site_outcomes/mini.py:651`), but the test fixture `kobo()` (`:62-66`) does not pass `not_applicable`, so the board shows `('MG-8','NO_OBJECTIVE')`. | At `:342`, call `rows_by_cat(kobo(not_applicable=frozenset({"MG-8"})))`. Expect `[("MG-5","NO_OBJECTIVE"), ("MG-4","NO_OBJECTIVE"), ("MG-8","NOT_APPLICABLE")]` (catalogue order). Do not change the shared `kobo()` fixture, because other cases depend on it. If the order differs, stop and report. |
| T3 | `backend/tests/test_out_b1_board.py::test_board_imports_only_outcomes_and_stdlib` | **Stale** | `site_outcomes/board.py:15` imports `money_text, price_text, trial_litres` from `chain.vocabulary` (FUEL-1 money wording, merged and reviewed). The test (`:358-360`) allows exactly one `chain.vocabulary` import with three names. | In the `chain.vocabulary` arm, accept any `ImportFrom` whose names are a subset of `{"days_line", "node_text", "provenance_suffix", "money_text", "price_text", "trial_litres"}`. Update the comment: `# FUEL-1: plus the three money wording helpers`. Nothing else is loosened. |
| T4 | `backend/tests/test_demo_a0_assumption_clock_seam.py::test_no_product_module_passes_the_recorded_clock_override` | **Stale** | DD-1b1 (`8a478a6dd`) gave `objectives/adapters/postgres_objective_store.py` its own seam with the same keyword. It is guarded by `require_prepare_database` (`:59-60`) and pinned by `test_dd1b1_prepare_clock.py`. The test exempts only the assumption store (`:20`, `:26`), so `:61` and `:138` are reported. I checked: with both seam owners exempted, no product module passes the keyword. | Replace `STORE_FILE` with `SEAM_OWNERS = {PKG/"financials/adapters/postgres_assumption_store.py", PKG/"objectives/adapters/postgres_objective_store.py"}` and skip both. Add `"objectives/composition.py"` to the `for name in (...)` text check (`:34`). Add one assertion that each `SEAM_OWNERS` file contains `KW`, so the exemption is not vacuous. |
| T5 | `backend/tests/test_w502_domain_intent_api.py` collection (`NameError: COLD`) | **Wrong (test code)** | `COLD` is imported only `if URL:` (`:23`), but the class body evaluates the defaults `code: str = COLD` at import (`:50`, `:56`). Without a DB URL the module fails to collect, where it should skip. | At `:50` and `:56`, change the defaults to `code: str \| None = None`, and make the first statement of each method `code = COLD if code is None else code`. Expected: with no DB URL, collection succeeds and every test skips. With a DB, the results are unchanged. |
| T6 | `backend/tests/test_w301_estate_golden_postgres.py` (6 tests: `$.summary.claims` has an extra `count.opportunities`) | **Stale** | CH-5a2b (`c10d51658`) added `summary["claims"] = …("count.opportunities",)` to the estate Findings body on purpose (`estate/index.py:440`). The manifest `tests/fixtures/w3/w301-estate-golden.json` predates it. | Rewrite the manifest by the file's own procedure (`:25-27`). Run once with `ASSETOPS_WRITE_W301_GOLDEN=1` on a `*_test` DB, then run once more without it, and all tests must pass. **Diff gate:** the JSON diff may only add `claims` entries under the Findings `summary`. Any other change: stop and report, because that would be a real regression. |
| T7 | `backend/tests/test_s4_schedule_health_postgres.py::TestDatabaseTime::test_skewed_application_clocks_do_not_move_s3_matcher_retry_or_health_times` | **Stale (the patch target moved)** | CH-5c2 C3 routed `assessment_worker.utc_now` through `read_scope.clock()` (`analytics/assessment_worker.py:66-67`, "the one clock seam"). Patching `assessment_worker.datetime` (`:292`) no longer skews it, so the live-skew assert at `:295` fails. `read_scope.clock`'s docstring says tests move it with `monkeypatch` (`read_scope.py:207-209`). | Replace `:292` with `monkeypatch.setattr(read_scope, "clock", lambda: datetime.now(UTC) + SKEW)`, importing `from assetops_backend import read_scope` inside the existing `if URL:` import block. Keep the `finding_service` and `recompute` patches. **If the DB-time asserts (`:310`, `:322`) then fail, stop and report:** that would mean product code writes app-clock time into the DB (code wrong), not a stale test. |
| T8 | 2 TEMPLATE_STALE mechanism tests and 3 `test_ch6b_estate_postgres` setup errors | **Expected until E2** | The tests need the mechanism template rebuilt at the current fingerprint (`followups` last line). | No code. **E2's first step** is the mechanism template rebuild (Part C). |
| T9 | CH-5d1 L2: the L2m Postgres test has never run (TEMPLATE_STALE) | Expected until E2 | `review-CH-5d1.md` L2. | No code. It runs inside E2 after T8's rebuild. If it fails, it goes to E2's fix round. |

E4 checklist items (bucket 2, no code; the E4 runner reads them from `check.json`):
- **A3 L3:** read MONEY-B at S, WK-2a (42.08), CH5D1-O1 and A3-PAGE from the E3 `check.json`. Confirm that
  CH5D1-O1 and KIS-6 agree on the priced-Site count (they reconciled at K9; confirm the values).
- **WD-1m watch:** MILL-5 must pass on the real Kobo data, which needs an example class. If it fails, that is an E4
  stop.
- **CO-2:** needs live ticks. Serve the E3 build with its scheduler ticking, and run `finish check` only after at least
  one tick has completed (R3v §9v.1, environmental on the clone).

E2 watch-only items. These are October regressions that later runs fixed. E2 re-confirms them, and there is no
pre-work. If one reappears, it goes to E2's fix round:
- 2026-10-30, the `POWER_DAY` group of about 24 tests;
- the two w301 estate-index order-dependent tests (INVALID_CURSOR, closed per `COV-PARTIAL-packet.md:112`; KeyError
  `:952`);
- the `s404SiteFindingIndex` flake under forks.

### A.3 Bucket (3), after the demo

The reason for every item here is that it is not on a demo beat and not needed for a green E2. The source file is in
brackets.

- **MV-1** L1 no guard on the price lookup (`actions/verification.py:400-419`; it only fails if the price read
  fails), L2, L3, L4 [`review-MV-1.md`].
- **A1** L3 (a basis-only re-declare counts as a conflict), L4 (descriptor and style nit) [`review-A1.md`]. A1 L2 was
  folded into A3 (A3 merged); no work.
- **CH-5d1** L1 (COH O1 with 2+ priced Sites, `value.text`) [`review-CH-5d1.md`].
- **K1a** L1 and L2 [`review-K1a.md`].
- **MB-1a** L1 to L4 [`review-MB-1a.md`]. L2 is unreachable in the demo.
- **PV-1** L1, the value-line order: "ACT-002 … estimated sales" shows above "ACT-001 … less diesel" (`mini.py:1030`).
  It is demo-visible but reads correctly either way. Changing the key also reorders the Assure contributors and
  re-expects check rows, so it is not worth an E3 risk. **The owner may raise it at E6; then it joins E6's fix
  round.** PV-1 L2 (whitespace, `mini.py:554`), L3 and L4 also go here.
- **MB-1b** the open call to pin the S-8 mill thread-line kind to MONITORING in MILL-4. It is beyond the card, and
  MILL-4 passes on real rows today.
- **K3** L1 (FAILED end-sample tfc2 assertion) and L2 (stale docstring `fuel_balance/rules.py:9-10`).
- **WD-1m** L1 and L2 (test strength).
- **K0** L1, L2, the straddle residual, and the `next(...)` default.
- **A3** L1 (mixed rounding, 15.13 against 4.12) and L2 (the idle line does not name the 1.10 margin). Both are
  walkthrough items under the spec's wording; **promote only if the owner raises them at E6.** A3's peak working set is
  also here.
- **K6a** L1 and L2.
- **K5** L1 (night mode `known_at`), L2 (`night_read.py:89-95`, a retired tank: not in the demo), L3.
- **K6b** L1 (NOT_JUDGED with no sentence before evaluate runs: unreachable on a built demo, because the prepare
  evaluates), L2 (Kobo/Cold/EV goldens byte-equal test), L3 (Owner cell when `owner_label` is null: Kisiwa's fuel
  Action carries an owner, `tools/demo_combined_kisiwa.py:566`), and the residuals (thread safety, NO_PLAN 503,
  site-visit read).
- **R3j2** the fuel clean-night measure.
- **K7-D** L1 to L4 (test strength).
- **K7-F** L1 (KIS-10 call-site test), L2 (freeze 200 case), and the residuals (night-4 baseline revision; the
  Kisiwa-only prepare is no longer used).
- **K8** L3 (two §9p.12 obligations met by argument).
- **K9-pre** L5 (the comment stripper's `/*` inside a string).
- **R3r** the Kisiwa Evidence tab answers 409 (`evidence/ledger_reads.py:212-232`). **DS-1 rule: never open it.**
- **R3t4/R3v** the Evidence (S2) and Performance comparison reports are stamped with the DB name. The demo-day prepare
  runs on its own DB and is unaffected.
- **R3q E1** COH-3 has 0 Kisiwa pairs by design (it does not cover a mini-Site domain Action).
- **R3v §9v.4** the `chain/why.py:136-138` days line does not apply declared-absent. It is conservative, and no demo
  beat shows it.
- **§9p.10** list: the estate selection token covering fuel rows; estate rows matching domain Actions; Kisiwa
  objectives; Foundation feeder labels on the legacy overview; the Kisiwa template v2 names (MD-KIS-K1-1, also K1
  L3).
- **`demo-sprint-lows-2026-10-28.md`:**
  - TEL-T1 L1 to L3, TEL-04 L1 to L4, TEL-05 L1 and L2, the TEL-05b Lows, TEL-06 L1 (telemetry; BeagleBone is skipped
    for this demo, OD-P8);
  - the CC-M Lows;
  - FIX-01 L2;
  - OUT-D L1 to L4, OUT-E L1 to L3;
  - OUT-E L4 (an INEFFECTIVE trial reaching MODELLED_IMPROVEMENT; the demo's trial is VERIFIED);
  - DEMO-A0 L1;
  - IDX-GAPS L1 and L3;
  - the FIX-S4 Lows L1 to L3.

### A.4 Already closed on main (no bucket; evidence)

- **K6b L4** (string ids passed to `fuel.window`): `tools/demo_combined_finish.py:1230` now wraps them in `UUID(...)`.
- **K7-F L3** (docs say three Sites): `backend/TESTING.md:327` now says four Sites and about 2.0 to 2.35 h.
- **K7 CARRY and K7 CHANGE** (rows fail without Kisiwa; Action domain): `demo_combined_finish.py` no longer has the
  "not in this dataset" branch, and `demo_combined_kisiwa.py:564` uses `"FUEL_BALANCE"`.
- K4b H1 (R3j3, 0058); K9-pre H1 (K9 fix round); K2 L1, F0 L1/L2 and K1 L1 (routed and closed); K6a residual (closed
  by K6b); the K5/K6b ref conflict (merged); the Kisiwa S board PARTIAL (honest, R3v §9v.3).
- **Oct lows:** the `w1f4VerificationStructure` ×3 (fixed in POLISH-PB-2, `POLISH-PB-2-packet.md:105`); the
  "Candidate" word (no longer in `frontend/src/estate` or `backend/.../estate`); IDX-GAPS L2 "those days" (the text is
  gone from `SiteFindingIndex.tsx`); CC-R1 (CC-R2).
- **The site-tabs 421px at 390 regression:** W1-F5b's all-26 audit (168 pairs, 0 failing, main `056a34b82`)
  post-dates it. K8c's all-26 recapture re-confirms it. If K8c shows it again, it becomes an R-1 add-on, and the
  coordinator asks me.

### A.5 The fix round: one round, R-1

**R-1 = A1-a + A1-b + T1 to T7.** Branch `task/R1-combined-lows` from main. One **Sonnet** builder. Code and tests
first; the capture retake is a separate small step after the merge.

- **Size: about 0.35 units.**
  - A1-a: 0.10.
  - A1-b: 0.05.
  - T1 to T5 (pure): 0.08.
  - T6 and T7 (one `*_test` DB, one Postgres file each, under the one-heavy-job gate; never while K8c serves a clone
    and captures at the same time): 0.12.
- Files (the approved list; anything else is a stop):
  - `frontend/src/estate/EstatePortfolio.tsx` and `frontend/src/estate/__tests__/estatePortfolio.test.tsx`;
  - `frontend/src/sites/MiniPerformance.tsx` and `frontend/src/sites/__tests__/miniServiceRoutes.test.tsx`;
  - `backend/tests/test_ch1a_grading.py`, `test_out_b1_board.py`, `test_demo_a0_assumption_clock_seam.py`,
    `test_w502_domain_intent_api.py`, `test_s4_schedule_health_postgres.py`;
  - `backend/tests/fixtures/w3/w301-estate-golden.json` (rewritten by the tool, diff-gated).
- No product backend file changes. If any T-item seems to need one, that is a stop, and the coordinator asks me.
- Proof:
  - the scoped vitest folders named in §A.1;
  - the five pure files with no DB URL: they must show 0 failed and 0 collection errors;
  - T6 and T7 on one `*_test` DB;
  - `tools\check-all.ps1` once after the merge (18 guards).
- No full suite (it waits for E2).
- Review: one **Opus** first review, light (frontend behaviour, plus the T6 diff gate and T7's stop condition). If
  there are findings, a Sonnet re-review.
- **Capture retake (R-1c, about 0.05, after R-1 merges):**
  - Pages: the Portfolio (1440 and 390, the row group with the Kisiwa fuel row) and the Kisiwa Service page at the
    story hour (1440 and 390).
  - Source: the same clone `assetops_k9_audit_r3u`, served read-only with main code. R-1 is frontend-only for these
    pages, so the data is valid.
  - If K8c has not yet taken these two pages, the coordinator tells K8c to take them last, after R-1 merges, and no
    separate retake is needed.
  - The files keep K8c's names and replace the earlier shots. The height check of §A.1 A1-b is recorded in the K8c (or
    R-1c) note.

Order: R-1 can start now, in parallel with K8c (different files; K8c only captures). DS-1 starts once R-1 has merged
and the K8c (and R-1c) captures have landed.

---

## Part B. DS-1: the two demo-script HTML documents

### B.1 What and for whom

| | DS-1a: client demo script | DS-1b: technical demo script |
|---|---|---|
| File | `Docs/demo-sprint/demo-script-client.html` | `Docs/demo-sprint/demo-script-technical.html` |
| Images | `Docs/demo-sprint/demo-script-img/` (shared; PNG copies of the chosen captures, 1440 only unless a step is about phone width) | same folder |
| Audience | the presenter (the owner) and the client: operations and finance people with minimal technical background | developers who will run, maintain or extend the demo |
| Voice | plain language; what you see and what it means for the business; no system vocabulary | precise; how each beat is produced, with file:line and tool names |
| Length | about 12 to 16 screens of reading; one step per screen-beat | about 2 to 3 times the client doc |

Both are self-contained HTML: inline CSS, inline SVG diagrams, local images by relative path. They load no script from
outside, and they read well in light and dark mode and at 390px. The pages are static documents, not app pages.

### B.2 Content rules (both documents, plus extra rules for DS-1a)

1. **Wording.**
   - Say **"Unexplained fuel"**, never "theft", "stolen", "pilfer", "loss to theft" or "missing fuel" (owner
     2026-11-07, answer 3).
   - Never show a **combined money total**: no sum across Sites, and no fuel money added to any other money (owner
     fuel scope; §9p.2 item 6).
   - Each money figure is stated per Site, with its currency and the screen's own qualifier ("estimated", "not billed
     or collected", the range as shown).
2. **Gaps.** Anything the screen does not have is stated as **"not available yet"** in the screen's own words. Kisiwa's
   productive use is shown as "none declared", and is never described as checked (K10, owner: "component contributor
   being non existent doesn't mean it is checked").
3. **DS-1a vocabulary ban.** None of these may appear in DS-1a: thread, chain, revision, fixture, simulator,
   simulation (except the screen's own "example data" label), tick, prepare, database/DB, API, endpoint, golden,
   register, guard, MOCK DEVIATION, row codes (COH-*, KIS-*, MILL-*, CO-*, R3*, §), ids, digests, "run", "binding".
   Screen labels the client actually sees (Portfolio, Findings, Action, Verified, Overview) are fine.
4. **Data honesty.** The data is labelled as example data. DS-1a says so once, near the start, in the words the
   screens use. Readings carry their story time.
5. **Links that must carry dates.**
   - The Kisiwa Findings index defaults to today, so its step uses a link that carries `from`/`to` over the story
     nights (K5 L4).
   - Kisiwa's Service step uses the story-hour link.
   - Take every link from `tools/demo_combined.py` `story_links` output (`:270-`) on the build, never hand-built.
6. **Never open** the Kisiwa Evidence tab (409, after the demo). Never show the Kisiwa Overview from the clone. It is
   captured at E5, and DS-1 holds a placeholder there (§B.5).
7. **Figures are provisional.** Every figure in either document is taken from the clone captures and marked in a
   hidden list for **DS-1f** (§B.6). It is confirmed against E4's `check.json` and E5's captures before the
   walkthrough.

### B.3 The story outline (shared by both documents; ST numbering from the plan §1.1, plus the Kisiwa beat)

| Step | Beat (plain words) | Screens / captures to use (K8c names by page; pick the 1440 file) |
|---|---|---|
| 0 | Opening: four Sites, one place to see what needs attention; example data | Sites list (K8c "sites-list"); navigation |
| ST-1 | Portfolio opening: four outcome cards (Grow, Cost, Protect, Assure) over the same checked days, coverage stated ("n of 7 days checked"); each Site's money on its own line | Portfolio top (K8c "estate-portfolio", outcome cards) |
| ST-2 | Kobo cost: a recurring generator problem, one problem with three occurrences; the action (ACT-001, the generator setting trial) is visible on every screen; after the check it reads "Resolved, monitoring"; before and after are judged on the same days; the diesel saving shown as the screen states it | Kobo board on S (all-26 "kobo-board"), the Finding page, ACT-001 verification page, Portfolio row (K8c) |
| ST-3 | Kobo Grow: three separate slots (KPI, potential, earnings); the midday mill opportunity and its action (use the code the screen shows; Kobo and Cold codes are per Site); estimated sales at the declared price | Kobo Grow row, the opportunity page, Findings › Opportunities (all-26) |
| ST-3b | Kobo idle generator fuel: the idle line as the screen words it (FUEL-1), on its own, never added to other money | Kobo board Optimize row (all-26 / K8c "kobo-board" Optimize) |
| ST-4 | GreenHarvest cold store: the backup-start failure recurs (2 occurrences); ACT-002 "in hand"; WR-006 third-visit notice | Cold board on its failure night, its Finding, the Maintenance WR-006 page (all-26) |
| ST-5 | EV depot: the connector interruption; ACT-003 "in hand"; estimated charging income at the declared tariff, "not billed or collected" | EV board on its fault window (all-26) |
| **ST-K** | **Kisiwa diesel Site, unexplained fuel:** (1) what goes in and what comes out of the tank each night (delivered, burnt by the generator for the power measured, change in the tank); (2) on some nights more fuel left the tank than these explain, and that is "Unexplained fuel overnight", with its own estimated cost range at the declared diesel price; (3) the action (seal the tank and dip point, power the sensor) was recorded; (4) about 14 nights later the check compares those nights with the nights before, and the screen says "Verified"; (5) Kisiwa has no productive use declared, so that measure reads "none declared", not "checked"; (6) on the Portfolio the fuel row stands on its own with "Verified" (after R-1) and its own range, never added to anything | Kisiwa board (K8c / all-26 "kisiwa-board" S−5d and S), Fuel night view (K5 "kisiwa-fuel-n4"/"-n6"), the unexplained-fuel Finding page (K5 "kisiwa-fuel-finding-n4"), the fuel verification page (all-26, K6b verdict page), Kisiwa Findings with story dates (K8c), Kisiwa Service story hour (R-1c), Portfolio fuel row (R-1c), Protect fuel line (K8c, §9p.11) |
| ST-6 | Findings index, all lenses: each item filed under cost, risk or opportunity, with the Lens column filled; the four Sites together | Estate Findings, all and Risks (K8c "estate-findings-all", "-risks") |
| ST-7 | A new day arrives (live, last): one day is added, and the board and Portfolio update on their own at the next refresh, with no manual step | live on the build; fallback before and after captures from E5 |
| Close | What the client gets: problems found from data, an action, a check that proves it, and honesty about gaps | one summary diagram |

The writer chooses the exact capture file per row from `.agent/K8c-captures/` (and the R-1c retakes, K5-captures, and
the regenerated all-26 audit index) by page name. Where two exist, the newer K8c or R-1c file wins. A step with no
capture yet gets a visible placeholder box: "Screen captured on the demo build".

### B.4 DS-1a: client document structure

1. **Title block:** "AssetOps demo: four Sites, one view", the date, and a short "How to use this script" (presenter
   notes in a side column, about 3 lines per step).
2. **A one-picture story map (inline SVG):** the four Sites and the beat each one shows, with the order and an
   approximate number of minutes per step (total about 25 to 35 minutes plus questions).
3. **One section per step in §B.3.** Each section has:
   - the screenshot, cropped to the region that matters, with 1 to 3 numbered callouts;
   - "What you see": 2 to 4 short lines quoting the screen's own words;
   - "What it means": 1 to 2 lines of business meaning;
   - "Say": the presenter's line;
   - "If asked": an optional line;
   - "Backup": which capture to show if the live screen is slow.
4. **Two plain diagrams (inline SVG), besides the story map:**
   - "Problem, action, check": the loop used by ST-2, ST-4, ST-5 and ST-K;
   - the Kisiwa night tank balance: fuel in, fuel burnt for the power made, change in the tank, and the remainder,
     "unexplained", as a simple bar or flow picture. There are no formulas in DS-1a.
5. **A closing page:** what was shown, and what is "not available yet" (listed honestly, in client words).
6. **A presenter checklist** (one box per step): the link opens, the expected words are on screen, and the backup is
   ready.

### B.5 DS-1b: technical document structure

Same step order, with these sections:

1. **Architecture in one page:** a data-flow diagram (inline SVG).
   - The flow: example readings and operational actions → evidence publication and the ledger → day snapshots and
     grading (operating calendar, coverage bands, declared-absent) → assessments → Findings and recurring threads →
     Actions → verification plans (frozen) → outcomes → Site outcome boards, estate Findings and Portfolio, served as
     stored composer responses keyed by watermark and code version.
   - Name the modules: `chain/grading.py`, `chain/claims.py`, `site_outcomes/board.py`/`mini.py`, `estate/index.py`/
     `portfolio.py`/`placement.py`, `actions/verification.py`/`verification_families.py`, `fuel_balance/`,
     `read_scope.py`, `config/chain/stored-composer-modules-v1.json`.
2. **Per step, "how this screen is produced":**
   - the route and the API read;
   - the rule that decides what is shown (for example, the ST-2 thread and the verification plan rule; the ST-3 midday
     plan `midday-productive-shift-1`; ST-K below);
   - the money rule (each Site on its own basis; never summed; `double_count_violations == []`);
   - the check rows that prove the step on the build (names allowed here: the `demo_combined_finish.py` rows,
     including the KIS rows, and the `chain_coherence.py` COH rows);
   - known limits: the §A.3 items a developer would trip over (the Evidence tab 409, the DB-name stamp, COH-3 with 0
     Kisiwa pairs, the `why.py` days line).
3. **The ST-K deep dive:**
   - the night window (owner: 6 pm to noon, Site-local);
   - the fuel-balance arithmetic (rules in `fuel_balance/rules.py`; band and stop markers);
   - how fuel events enter as operational actions (K0, `runs/operational_actions.py`);
   - Finding creation (UNEXPLAINED_FUEL → MG-8 "Fuel accounted for", Protect);
   - the consequence at the declared price (`fuel-residual-1`, basis `UNEXPLAINED_FUEL_AT_DECLARED_PRICE`, its own
     interval);
   - the fuel Action (`FUEL_BALANCE` domain Action, no Action page);
   - the plan freeze and evaluation (`fuel-residual-within-band-1`, a 14-day later window, baseline before it);
   - the verdict page;
   - the Portfolio thread label (`FUEL_THREAD_LABEL`, and the R-1 rendering);
   - K10 declared-absent productive use, and why it is PARTIAL and never COMPLETE (R3v §9v.3).
4. **Checks and guards:**
   - what `tools/check-all.ps1` runs (the 18 guards, by name, one line each);
   - the wording guard (no "theft");
   - the clock guards;
   - the stored-route coverage;
   - `demo_combined_finish.py check` and `chain_coherence.py`/`perf_budget.py`;
   - what each proves.
5. **The demo-day build** (from `tools/demo_combined.py` and the plan §5):
   - the date rule (S = prepare day − 2, not on the 3rd to 5th of a month, `tools/demo_combined.py:124`);
   - the four-Site prepare steps in order;
   - the expected durations (about 2.0 to 2.35 h);
   - the in-prepare self-check, which re-checks every row, including the ones the R3v targeted check left untouched
     (owner 2026-11-08 "Affected rows now");
   - serve and readiness, the ticks (CO-2), `prewarm`, `story_links`;
   - the 3-day freshness rule.
6. **Failure recovery** (a runbook table): symptom → cause → action. It covers:
   - E2 failures (the scoped fix round, then re-run only the failed files);
   - an E3 prepare failure (the §4.4 partial prepares; a whole re-prepare drops only its own DB);
   - E4 row failures:
     - frontend-only fix: no rebuild;
     - backend fix: prove it on an L3 clone, then one re-prepare;
   - E5 capture failures (`DEMOB_ONLY=` re-run);
   - fallback DBs (polish and demo3, OD-P6);
   - a live-demo failure (switch to the DS-1a backup capture; ST-7 fallback);
   - memory pressure and keep-awake (the standing gate: ≥2.5 GB free; one heavy job).
7. **Appendix:**
   - the story calendar (S, S−5d, the Kisiwa nights);
   - the links list from `story_links`;
   - the check rows mapped to steps.

DS-1b may use system vocabulary, but it still says "unexplained fuel" (never "theft"), and it still shows no combined
money total, even as an example.

### B.6 Builder, sizes, review

- **Builders: Opus**, two units, which may run in parallel because this outline is shared:
  - **DS-1a** (client): about **0.75 units**;
  - **DS-1b** (technical): about **1.0 unit**.
  - Each builder reads this Part B, the captures folders, `Docs/demo-sprint/client-demo-plan.html` §1.1 and §5, and
    the owner files named in §B.2. DS-1b also reads the modules named in §B.5.
  - Branch `task/DS-1-demo-scripts`: DS-1a and DS-1b commit to separate files, so one branch is fine. If they run in
    parallel, use two worktrees on two branches and merge them in sequence.
  - Builders may serve the clone read-only to read screen text, but take no new captures (except a missing page,
    named in the packet).
- **DS-1f (finalise, about 0.25 units, Sonnet, after E5):**
  - swap in the E5 captures, including the Kisiwa Overview;
  - confirm every figure against E4's `check.json` and E5's captures;
  - clear the hidden provisional list.
- **Total DS-1: about 2.0 units** (0.75 + 1.0 + 0.25), plus reviews.
- **Review: one Opus reviewer per document** (fresh, not the builder); Sonnet re-reviews. The criteria:
  1. every §B.3 step is present, in order, with a capture or the named placeholder;
  2. the quoted "What you see" text matches the capture word for word;
  3. **DS-1a** passes a forbidden-word scan (the §B.2 rule 3 list, plus theft, stolen, pilfer and "missing fuel"),
     done by the reviewer with Grep on the HTML;
  4. there is no money sum across Sites, and no fuel money joined to other money, anywhere (the reviewer checks every
     currency figure);
  5. gaps are stated as "not available yet" or "none declared";
  6. every link comes from `story_links` and carries its dates;
  7. **DS-1b**: every mechanism claim cites a file or tool that exists on main (the reviewer spot-checks at least 10
     citations), and the recovery table matches plan §5 and `backend/TESTING.md`;
  8. both pages render at 1440 and 390 with no horizontal page scroll, in light and dark mode, with no external
     requests.
  - High findings: anything misleading to the client (a wrong figure, "theft", a summed total, a claim the screen does
    not support). Medium findings: a missing step or capture, or a broken link. Wording polish: Low.

---

## Part C. The end-game order after DS-1 (confirmed, with corrections)

| Step | What | Size (est.) |
|---|---|---|
| R-1 (+R-1c) | the §A.5 fix round and the capture retake; can overlap K8c | about 0.4 units |
| DS-1a/b | the two documents (Part B) | about 1.75 units |
| **E1** | merge freeze: R-1, K8c and DS-1a/b merged; main tagged; keep-awake running; no other heavy agent | none |
| **E2** | **first: the mechanism template rebuild** at the current fingerprint (clears T8; lets T9 run). Then the full backend suite (`tools\run-backend-suite-in-container.ps1 -Tier all -Workers 2`, about 38 min, cap 76), then the full vitest (about 8 min), then `check-all` (18 guards, about 7 min), in sequence | about 1 h of machine time, plus a reserved Sonnet fix round of about 0.5 units |
| **E3** | the four-Site demo-day prepare into a new DB `assetops_polish_client_test`, from a main checkout; date rule first; in-prepare self-check over all rows, which re-checks the rows R3v left untouched (owner "Affected rows now") | about 2.0–2.35 h of machine time |
| **E4** | serve **with the scheduler ticking** (CO-2 needs live ticks; wait for at least one completed tick), `prewarm`, `finish check` (all rows), `chain_coherence.py` with no expectation file (EX-2 = 0), `perf_budget.py`, register reconcile (EX-4); plus the §A.2 E4 checklist (A3 L3 values, MILL-5) | about 15 min |
| **E5** | strict captures at 1440 and 390 (about 28 keys, plus the Kisiwa pages, plus the **Kisiwa Overview** moved here from K8c) | about 10 min |
| **DS-1f** | finalise both documents from E4/E5 | about 0.25 units |
| **E6** | owner walkthrough using DS-1a on the build; notes batched into one fix round; at most one more E3–E5 pass | owner about 60–90 min |

Corrections to the plan's §5:
- **(a)** E2 starts with the mechanism template rebuild (it was not listed).
- **(b)** E4 must have live ticks (CO-2).
- **(c)** DS-1f sits between E5 and E6, because DS-1 is drafted from the clone now.
- **(d)** E2's `test_demo_combined_postgres.py` is now a **four-Site prepare of about 2.0 to 2.35 h**
  (`backend/TESTING.md:327`), not the 20 to 25 minutes §5 assumed. That decision is the owner's (Q1 below).
- Freshness: if the client session is more than about 3 days after E3, repeat E3 to E5 (about 2.5 h now) the day
  before.

### Owner questions (not decided here)

**Q1. E2's built-in full prepare.** E2's suite includes `test_demo_combined_postgres.py`, which now runs a full
four-Site prepare (about 2.0 to 2.35 h) and then every check row. E3 runs the same prepare again, with the same check
rows in its self-check.
- **(a, recommended)** Skip that one file in E2. E3's prepare and self-check prove the same thing on the actual demo
  DB. This saves about 2.0 to 2.35 h of machine time and one heavy job. If E3 fails, the fix path is the same.
- **(b)** Keep it in E2, as the plan says. It rehearses the prepare before E3, at about +2.0 to 2.35 h.

**Q2. The client session date (OD-P9, still deferred).** E3 must be within about 3 days of the session. It must also
not fall on the 3rd to 5th of a month (S = prepare day − 2). Otherwise E3 to E5 are repeated, at about 2.5 h of machine
time. A date, or "no date yet; build when ready and repeat if needed", lets the coordinator place E3.

No other owner decision is open. A3 L1/L2 and PV-1 L1 are walkthrough items. They come up only if the owner raises
them at E6.

---

**Summary.**
- Buckets: (1) **2** items; (2) **9** test items, plus 3 E4 checklist items and 3 E2 watch items; (3) **about 60**
  Lows (about 40 from the fuel/Kisiwa list, plus the October list). About 15 items are already closed (§A.4).
- One fix round, R-1: about 0.35 units, plus a 0.05 retake.
- DS-1: about 2.0 units. DS-1a is a client script of 12 steps (the four Sites, with the Kisiwa unexplained-fuel beat).
  DS-1b is the technical version (data flow, per-step rules and checks, the Kisiwa deep dive, the demo-day build,
  failure recovery). DS-1f finalises both after E5.
- Owner questions: Q1 (skip E2's built-in prepare), Q2 (the session date).
