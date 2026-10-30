# OUT-C slice review: early warnings (final, U3-U6 plus the whole slice)

Reviewer: a fresh Claude reviewer (not the author). Branch `task/OUT-C-early-warnings` at head `0297540a`, against main `e8cf8a36`.
Contract: `AssetOpsV1-plan2/.agent/build-sheet-OUT-C.md`. U1 and U2 were reviewed as units (`OUT-C1-review.md`, `OUT-C2-review.md`).

## Verdict: REVISE

The slice builds what the sheet asks for. The warning producer, the board, the U3 cold data, the U4 mini and EV inputs, the lists, the
card and the notice are all present and tested, and the never-money check holds on the wire. Three things block:

- **H1:** several mock mismatches are not in the register.
- **M1:** 648 compiled `.pyc` files are committed.
- **M2:** the Maintenance card can claim "None" when the check could not be made, which is a consequence of P-C1.

All three are small to fix.

## Checks run (by this reviewer, on 0297540a)

| Check | Result |
|---|---|
| `npx.cmd tsc --noEmit` (frontend) | exit 0 |
| `npx.cmd vitest run` on 9 changed test files (earlyWarnings, estatePortfolio, estateRoots, s404SiteFindingIndex, coldFindingIndex, evFindingIndex, globalMaintenance, workRequestOverview, outcomeBoard) | 9 files, **196 passed**, 0 failed (it ran under this session) |
| pytest, every non-Postgres `backend/tests/test_out_*.py` (plan2 venv, worktree PYTHONPATH, `assetops_backend` resolves to `-outC`) | **192 passed** in 4 s |
| `tools\check-all.ps1` with `ASSETOPS_GUARD_PYTHON` set to the plan2 venv, run directly with no policy flag | **All 11 guards passed** |
| Postgres tests (`test_out_c3_repeat_visits_postgres`, `test_out_c4_ev_warnings_postgres`, b4 board) | not rerun (needs the container DB). Cited from the implementer's full run below |
| Full backend: implementer's run `var/test-results/OPS-03/20261030-215840-fd3ad2` | JUnit `tests=4338 failures=0 errors=0 skipped=0`, time 2298 s, exit-code 0. It includes the c1-c4 files. It ran on `b6650116`; `b6650116..0297540a` changes only `.agent/` files, so the evidence applies to the head under review |
| Full vitest | not rerun. The implementer reports 3522 passed with only the 3 known `w1f4VerificationStructure` failures. Not independently verified |
| Browser and layout evidence | not run, as instructed. I read the 8 capture PNGs and the packet's CDP measurements instead |
| Process | nothing under `var/` is tracked (`git ls-files var` is empty). The DBs named are `assetops_out_c_*_test` and `*_outc_test`. No `-ExecutionPolicy` was used |

Side effect seen: running pytest rewrote three **tracked** `.pyc` files (see M1). I restored them with `git checkout`, so my commit holds only this file.

## Findings

### H1 · High (owner rule: an unregistered mock mismatch) · several v70 differences are not in the register

`.agent/mock-departure-register.md` R560-R571 cover the sheet's §8 list. The captures and code show further differences from v70 that no row covers.
Each is cheap to register, or the Architect can change the copy instead.

1. **Site Findings warning lists drop the Site-name prefix.** The mock `screens.js:184`, through `warningList` (`outcomes.js:139`), always prints
   `GreenHarvest · …` (capture `findings-cold-1440-mock-v70-cold-findings.png`). The app passes `showSite={false}`
   (`frontend/src/shell/SiteAnalyticsFrames.tsx:525,541,555`). The sheet ordered this, but it is not registered.
2. **Repeat warning `seen` tail.** The mock reads "…; the automatic start still failed" (`outcomes.js:128`). The app reads "…; the linked finding is
   still open" (`outcomes/warnings.py`, §3 copy). R567 covers only the asset name.
3. **Cold Cost subline.** The mock reads "None of the visits fixed the backup generator's automatic start". The app reads "None of the visits resolved
   the linked finding" (`site_outcomes/cold.py` `COST_SUBLINE`).
4. **Cold Cost "What can be done".** The mock lists "Witnessed automatic-start test" under Cost. The app shows "Nothing proposed yet", because
   `options[COST]` is still `()` (`cold.py:146`). The mock also shows the repeat issue as "Early warning", while the app's issue badge is "Risk"
   (sheet: RISK). The mock's own `WARNINGS` entry says `risk`, so the mock is inconsistent with itself, and the choice still needs a row.
5. **WR notice tail.** The mock `wrOverview` (`screens.js:821`) reads "third visit to this generator … and the automatic start still failed". The app reads
   "third visit to generator-1 … and the linked finding is still open" (`frontend/src/work/WorkRequestOverview.tsx:147-153`).
6. **Maintenance card 4.** The mock `metric(..., 'amber', 'wr-overview')` (`screens.js:812`) has the amber tone and the note
   "Backup generator · 3 visits, start still failing". The app has no `tone` (`GlobalMaintenance.tsx:271`) and the note "… visits, linked finding still open".
   `MetricCard` supports `tone` (`ui/V69Layout.tsx:22`).

**Fix:** add register rows for 1-6 (the Architect allocates the IDs, since R560-R571 are used up), or change the copy where the Architect prefers the mock.
No code change is needed if the items are only registered.

### M1 · Medium · 648 `__pycache__/*.pyc` files committed (`5ebda270`, U4)

`git show --name-only 5ebda270` adds 648 `.pyc` files under `backend/assetops_backend/**/__pycache__` and `backend/tests/__pycache__`. The repo
tracks 652 in total, against 4 on main. `.gitignore:10` ignores `__pycache__/`, so they were force-added or added with `-f`. The effects:

- Every local pytest run dirties tracked files. This happened in this review.
- The committed `ev`/`mini` bytecode is already stale against the source.
- Merging would put this noise on main.

**Fix:** `git rm -r --cached` every tracked `__pycache__` path that main does not track, then commit. Check that main's 4 pre-existing ones are left as they are.

### M2 · Medium · the Maintenance card says "None in the last 60 days" when the cold repeat check could not be made (P-C1 consequence)

`GlobalMaintenance.tsx:258-266` shows `REPEAT_VISITS_NONE` whenever the loaded estate summary has no REPEATED warning. On the default Maintenance window
(seven UTC days, `globalWorkClient.ts:668-676`) the cold Site composes over a window that no cold assessment selection covers. So its Finding list
is empty and its Cost row is UNKNOWN (see the P-C1 trace below), and the card then states "None" for GreenHarvest. Meanwhile:

- the GreenHarvest board shows Needs attention;
- the request page shows the "third visit" notice.

This is a false claim of absence (owner rule: missing data is stated, not shown as zero or none). The Portfolio pulse and the Protect clause count only
what was found as well, but they do not assert "none", so they are residual risk rather than blocking.

**Fix (needs a short Architect ruling on the copy):** count a Site as checked only when its summary `OPTIMIZE_COST` row is not UNKNOWN and its `read_state`
is AVAILABLE. If any Site is unchecked and no REPEATED warning was found, show "Not assessed" with the existing unchecked note, or a partial note naming the Site.
Add a vitest case: a summary with a cold Site whose Cost row is UNKNOWN must not show "None".

### L1 · Low · B defect: "Connector Connector c1" in the Depot availability text (log it, or fold it into the fix round)

`site_outcomes/ev.py:168` (`f"Connector {first.get('label')} was out of service …"`) and `ev.py:249` (`f"Connector {x.get('label')}: …"`) prefix labels that
already read "Connector c1". This text is from B, not C. C's own warning title applies the right rule (`outcomes/warnings.py:246`).

It is visible client copy in a file C already edits, and the fix is two lines with that same rule. My recommendation is to fix it in this REVISE round,
with a unit assertion. It does not block, and if the coordinator prefers scope purity it can be logged against B instead.

### L2 · Low · the mini Protect headline contradicts the new battery line

With no MG-4 warning, `mini.py:333` keeps `PROTECT_HEADLINE` ("Battery and generator condition are not assessed"). The battery contributor beside it can
now read "No generator period at or near the reserve (24 assessed)". This follows the sheet to the letter, so it is a copy question for the Architect, not a defect.

### L3 · Low · reading noted: the battery confidence chip beside a "Not available yet" text

`mini.py` `_battery` passes the readiness chip whenever dispatch was read, including m = 0, where the text is "Not available yet · no generator period
assessed on this day". This is the sheet's literal "n or m is known" and the handoff records it as a reading, so I accept it. A chip beside a not-available
line is slightly odd; it is the Architect's call.

### L4 · Low · packet accuracy

- "The mock prints short names" (Known deviations) is wrong. The mock's `CATN` uses the full category names (`outcomes.js:11-16`), so the app's
  "Optimize cost and efficiency" matches the mock.
- "P-C1 … carried to the combined dataset" understates the cause. P-C1 is structural (see below), so a combined dataset will not make estate
  surfaces show cold warnings unless a cold assessment selection spans the estate window.

## P-C1 judged: an honest data difference, not a C composition bug

Trace for the summary over `[2026-10-29, 2026-10-30)`:

1. `read.py:333-336` `summary()` calls `board(site, lo=D, hi=D+1, known_at=None)` for cold. The window is passed unchanged (B-Q7, sheet §2 U5).
2. `read.py:309-316` `compose` hands it to `cold.compose(lo, hi)`.
3. The cold Finding and overview ports (`read.py:238-247`) pass `lo`/`hi`/`known_at` straight to the store. Only `readiness` is widened to covering days
   (`read.py:163-165`, `widen=True`), so B's whole-UTC-day widening does not touch the Finding or overview reads.
4. `postgres_assessment_store.py:2036-2042` (the unpinned `_snapshot`) selects a cold run only where `sel.window_start <= :lo AND sel.window_end >= :hi`.
   The W5-01 selection is the event window (16:00-17:05 UTC), so a whole-day window selects nothing. `findings()` then returns `items: []`
   (`:2366-2367`), and the overview's currentness becomes UNKNOWN (`analytics/cold_reads.py:65`, `not selected`).
5. In `cold.py`:
   - `base` is False, so CC-3 is unsettled and the Cost row is UNKNOWN.
   - `open_findings` is empty, so `REPEATED_MAINTENANCE_NO_RESULT` (which needs an open linked Finding) does not fire, even though the 60-day visits are present.
   - The two plan warnings do not depend on the selection, so they still fire, which matches the recorded "only the 2 plan warnings".

`known_at` is None in both reads, and the board passes no wrong window. The disagreement comes from the existing cold read rule (one selected
assessment must cover the requested window), not from C. It does, however, make the estate half of C (Portfolio cell, estate lenses, Maintenance card)
structurally blind to cold repeat warnings on any multi-hour window. That is why M2 exists. It is also an Architect item: for example, the summary could
compose cold and EV Sites on their latest selected window inside `[lo, hi)`. That is outside this sheet.

## Unit-review follow-ups (spot-checked)

- **U2 L1, anchor tests:** present. `test_out_c4_mini_ev.py:145` (mini `end`) and `:156` (EV `hi`). The packet records mutation proofs.
- **U2 L2, MG-4 dispatch condition:** `mini.py:271` is `"MG-4": base and dispatch is not None`. It is covered by the existing failed-dispatch test.
- **U1 L2, KINDS sort:** `warnings.py:25` `KINDS = (REPEATED, PLAN_OVERDUE, PLAN_DUE_SOON, …)`, and `evaluate` sorts by `BADGE_ORDER`, then `KINDS.index`, then the key (`:267`).
- **U1 L3, guards:** `ev.py` `peak_facts` returns None unless both numbers parse and are finite. The EV extras skip rows with no `asset_id`, and `connectors_out` skips None durations.
- **U1 L1, b4 cold assertion:** updated (`test_out_b4_board_postgres.py`, cold Cost NEEDS_ATTENTION).

## U3-U6 against the sheet

- **U3:**
  - The Cost contributors, headline and subline match §2.
  - The w502 authored writes go through `work.create_case`, `post_record`, `post_event` and `post_plan` with `PRINCIPAL`. They come after every
    existing read, `positive` only, with idempotency keys of the form `w502b-{mode}-…`.
  - Backdates are 24 d and 11 d, inside the 30-day limit, with the fallback recorded. The plans occur at −1 d.
  - `attest` requires `out_c`. The data is labelled by the Site-wide "Demonstration data" badge.
  - The Postgres test asserts the exact texts and records P-C1 honestly.
- **U4:**
  - The reserve count is read from `binding_constraints` only.
  - `PEAK_MARGIN` is a named constant. It is strict `>`, so 72 of 80 does not fire (this was decided in U1).
  - No EV text prints "None". The connector title is not double-prefixed, a reading I accept.
- **U5:**
  - The list structure and classes match `outcomes.js:139` (`oc-warn`, `oc-warn-head`, `h3`, `oc-info`, `ul > li > span.oc-kind {risk|stress} + div > a > strong + small`).
  - The CSS is ported with tokens: 24 px targets, focus-visible, `minmax(min(260px,100%),1fr)`, a 760 px single column and `overflow-wrap: anywhere`.
  - The 390 capture shows one column with no overflow.
  - The explainer uses the shared `ExplainerDialog`.
  - Estate lens filters: All, then `COST`, `RISK` and `OPPORTUNITY`.
  - The Portfolio list uses `max={4}` with `showSite`.
  - The pulse shows Unknown until the summary loads, with no icon (R570). The Protect clause is `protectDetailText`.
  - No new `<svg>`, no `variant`, and no frontend "Not available yet" literal (the guards pass).
- **U6:**
  - Card 4 is replaced, not added as a fifth card, and it is keyed `repeat_visits`. Its fallback is "Not assessed" or "could not be checked", never "Not available yet".
  - The notice is matched by the warning `href` ending in the case id and appears above the pair at 1440 and 390.
  - The register has R560-R571 and R541 resolved, plus the R08, R10 and R358 notes. The R358 code comment is updated.
- **Never money:** `Warning.wire` (`warnings.py:122-128`) emits exactly the §4 keys, with no `subject` or `visit_ids`. `test_out_c1_never_money.py`
  includes the injected-amount anti-vacuity case. The frontend tests apply the money regex and the w1 vocabulary scan.
- **Changed existing tests:** none weakened. The a1, b1, b2 and b4 edits change values to catalogue/2 and add assertions. The frontend test edits only
  add an optional client argument or retire the card-4 label.

## Residual risk not named in the packet

- The estate warning surfaces are blind to cold (and probably EV) window-scoped Findings on day or week windows by construction (P-C1 above), not only for
  lack of demo data.
- The full vitest number is the implementer's alone.
- No Portfolio, estate Findings or Maintenance capture exists, so placement on those three screens is proven only in vitest.

## Coordinator verification of the final-review fix round (04fa0d8a..7025a040), 2026-10-30: ACCEPT
- H1: rulings applied verbatim, with R572/R573 registered. The Site-name prefix is restored through SiteEarlyWarnings.
- M1: .pyc tracking matches main (4 paths, all under .agent). A pytest run leaves git status clean.
- M2: six-state card 4 with the never-"None" case; mutation-checked by the implementer (R574).
- L1 (no "Connector Connector"), L2 and L4 are done. R575 (P-C1) is open and owned by the OUT-W follow-up slice, which the owner approved as option A.
- Implementer checks: 196 non-Postgres pytest, c3 Postgres 1/1, vitest 9 files 200/200, tsc clean, check-all 11/11 run directly. The full suites were green at b6650116 (backend 4338/0, vitest 3522 with the 3 known w1f4 failures); the fix round is copy, register and tests on top of that.
