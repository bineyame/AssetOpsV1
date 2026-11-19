## 9r. Ruling DIESEL-1-R3r — Kisiwa Overview evidence state

Claude Architect (binding: Claude, `.ai/ROLE_CONFIG.md:9`, owner 2026-10-27). Read-only code reading in `AssetOpsV1-k9` (`task/DIESEL-K9-checks-rehearsal` at 8375e3864) and `AssetOpsV1-k8` (ee9c9805f). No DB, no suites. Trigger: K8 builder 3 served a clone of `assetops_demo3_kisiwa_test` and Kisiwa's Overview showed "Awaiting evidence migration" (409 `AWAITING_EVIDENCE_MIGRATION`), so R3p's Kisiwa objective line was never on screen.

### 9r.1 Q1: the default four-Site prepare does not open Kisiwa's Overview either (READ)

- **The gate.** `site_overview/route.py:139-147`: an imported Site's Overview is served only with a passing S2 Evidence comparison (`imported_scope`) **or** a persisted `NO_LEGACY_EVIDENCE` cutover basis for its current import (`no_legacy_basis`, wired at `main.py:430-432` to `PostgresFoundationStore.no_legacy_evidence_basis`, `postgres_foundation_store.py:254-268`).
- **The prepare.** `T/demo_combined.py` `finish` (`:585-588`) runs `evidence_migration run` for `KOBO-001` only. Nothing in the parent, in `T/demo_combined_kisiwa.py` `build`/`register` (`:159-181`, `:699-808`) or in `register_in` (`:121-141`) writes a comparison or a cutover basis for Kisiwa. The only basis writer in the code is `sites/w402_demo.py:62-66`, and no demo child calls it.
- **So the gap is not a Kisiwa-only-prepare artifact.** The four-Site rehearsal DB would show the same 409 on both Kisiwa board links `story_links` prints (`/sites/KISIWA-001?date=` for S−5d and S, `T/demo_combined.py:307-309`).
- **How the other Sites get past it.** Kobo: the S2 comparison in `finish`. Cold and EV: they never reach this gate. `SiteDetailFrame.tsx:130-156` sends a `COLDCHAIN` Site to the cold Overview and an `EV_CHARGING` Site to the EV page, and neither reads `/overview`. Kisiwa is `MINIGRID`, so it gets Kobo's mini Overview and therefore Kobo's gate (`SiteOverview.tsx:138`, `:182-196`).
- **Side effect today.** The outcome board's mini `source` port uses the same decision (`site_outcomes/composition.py:35-45`, `read.py:233-235`). It raises `OverviewClosed` for Kisiwa, so a Kisiwa board can read `read_state` PARTIAL with a failed port. That is a latent risk for the Kisiwa boards R3q §9q.1 now collects.

### 9r.2 Q2: ruling (a), record the honest no-legacy cutover basis at Kisiwa's import

**Why this is not faking.** Kisiwa is imported with `legacy_documents=()` (`demo_combined_kisiwa.py:127-128`), and the prepare tree's `var/sites` holds only `kobo-001.yaml` (`demo_combined.py:449-451`). No legacy evidence set exists to compare. q12-6 (W4-02) defines `NO_LEGACY_EVIDENCE` for exactly this case: "only an installer whose import carries no legacy documents calls this". `w402_demo.py:62-66` is the precedent.

The basis does **not** open the Performance gate. Kisiwa has no Performance comparison report, so S3, Finding and money claims on the Overview stay closed under the gate's own honest reason, `NO_LEGACY_EVIDENCE_REASON` ("No legacy evidence was imported for this Site. Dispatch has no assessed comparison for this selection.", `performance_comparison.py:186-196`). No comparison is written, nothing is tuned and nothing is forced.

(b) is rejected. It leaves two printed story links (the S−5d "morning after" board beat and the S board) on a refusal page. It also needs a links change of the same size as (a), and keeps the board-port risk in §9r.1.

**The change (K9, `T/demo_combined_kisiwa.py` `register`, Postgres path only):**
- Inside the `try`, directly after `result = register_in(store, import_at, install_at)` (`:169`), add:
  ```python
  # DIESEL-1-R3r (q12-6): the import carries no legacy documents (`legacy_documents=()` above), so record the
  # explicit NO_LEGACY_EVIDENCE cutover basis with it (w402_demo.py's pattern). Never a comparison; idempotent.
  store.record_no_legacy_evidence_basis(UUID(result["tenant_id"]), UUID(result["site_id"]), now=import_at)
  ```
  Import `UUID` locally.
- `register_in` is **not** changed, because the in-memory K1 callers keep their store contract. No new keys go into `kisiwa-register.json` or `kisiwa.json`, so KIS-1 (`kis1(..., register, ...)`) is byte-stable.
- **No frontend change.** R3p's objective line and its tests stand.

**Proof row (K9, `T/demo_combined_finish.py`): `KIS-OV`**, wired after KIS-7, using the existing `KisiwaMissing` pattern when Kisiwa is absent:
- `GET /api/sites/KISIWA-001/overview?date=<S−5d>` and `?date=<S>` (the two `story_links` days) each answer 200 with a selected-day window summary. Any 409 or 503 fails the row with the status and `detail.code`.
- One SQL read: exactly one `site_cutover_basis` row for Kisiwa, `basis = 'NO_LEGACY_EVIDENCE'`, with `site_import_id` and `source_sha256` equal to its `site_import` row.
- It reports, and does not assert, the Kisiwa S board's `read_state`.
- L0 self-test: one pass body; fail bodies for a 409 `AWAITING_EVIDENCE_MIGRATION` and for a missing basis row.

**Pre-rehearsal clone probe (K9 builder, before the 2-hour prepare, about 15 minutes):**
1. Clone `assetops_demo3_kisiwa_test` to a new `*_test` DB (authorized).
2. Upgrade it to head and call `record_no_legacy_evidence_basis` for Kisiwa (`now` = the stored `site_import` instant).
3. Serve it and confirm the Kisiwa Overview answers 200 for S−5d and S and shows the R3p objective line.
4. Record the Kisiwa S board `read_state` before and after.
5. Run whichever Kisiwa rows K9's check-all already ran on that DB, before and after.

**Stops:**
- **S-r1:** the Overview answers anything but 200 after the basis is recorded.
- **S-r2:** any Kisiwa row passes before and fails after.

Either stop means report to the Architect, with no patch and no prepare.

**Known honest gaps that stay** (presenter note, not fixed before the demo):
- Kisiwa's **Evidence tab** still answers 409. `imported_scope`/`ImportedEvidenceReads.scope` (`evidence/ledger_reads.py:212-232`) honours only the comparison, not the basis, so the Overview's evidence links lead to "Awaiting evidence migration".
- The demo script does not open Kisiwa's Evidence tab.
- After-the-demo list: "Evidence routes honour the no-legacy cutover basis".

### 9r.3 Q3: owner K9, before its rehearsal prepare

- The prepare archives `git archive HEAD` (`demo_combined.py:440`), so the change must be **committed on K9's branch before the prepare starts**. A rehearsal without it would need a second 2-hour prepare to put the Kisiwa board beat and the K8 (b) Overview capture on screen.
- **Review.** K9's pre-rehearsal review is in flight. This delta (register line, KIS-OV and its self-test) goes to the same review as an addendum, or to a fresh Claude delta review. Only the delta is gated, and only High or Medium findings block.
- **K8.** No change. K8 merges on its clone captures. Its Kisiwa Overview capture with the objective line moves to the (b) captures on K9's rehearsal DB (§9p, "captures (a) clone + (b) on K9's rehearsal DB"). R3p's pre-flight (a), "`site_overview.serve` serves `KISIWA-001`", is answered by KIS-OV on the rehearsal DB.

### 9r.4 Q4: the Service page's empty default day is acceptable

- The default day (the DB's current day) has no Kisiwa run. The story hours do, and the script links the story hour, so the empty day is not on the demo path.
- **Condition (checked in K8's or K9's captures, not built):** the default day must read as an explicit "no records for this day" state, not blank cards or zeros. If it shows zeros or blank cards, log it as a High finding for the post-rehearsal polish batch. It does not block the rehearsal.
- No new link is added.

### 9r.5 Q5: size, path, tripwire

- **K9 +0.1:** about 0.02 for the register line, 0.05 for KIS-OV and its self-test, and 0.03 for the clone probe.
- Pre-rehearsal work is about 0.65–0.7. That is at the R3q watch line (0.7), so the builder reports if it passes 0.7. The R3q lever stays first in line.
- **Critical path about 9.35–9.6** against the 9.75 tripwire. Not crossed, no cut. The clone probe overlaps K8's review.
- **Plan HTML (coordinator):** the rulings table gains "DIESEL-1-R3r: Kisiwa Overview 409 on every prepare (only Kobo gets the S2 comparison; Cold/EV never read /overview); K9 records the honest q12-6 NO_LEGACY_EVIDENCE cutover basis at Kisiwa's import (no comparison, Performance gate stays closed); KIS-OV proves 200 on S−5d and S; clone probe before the prepare (stops S-r1/S-r2); Kisiwa Evidence tab 409 stays (after-demo); Service empty default day acceptable if stated; K9 +0.1; path 9.35–9.6".

### 9r.6 Owner questions

None.

## 9s. Ruling DIESEL-1-R3s — Kisiwa's closed Performance gate (board PARTIAL) and KIS-7 on real data

Claude Architect (binding: Claude, `.ai/ROLE_CONFIG.md:9`). Read-only code reading in `AssetOpsV1-k9` (`task/DIESEL-K9-checks-rehearsal` at 53421ce0d) and main 96d597573 (K8 merged). No DB, no suites. Trigger: the K9 fix round found the Kisiwa board PARTIAL from the closed Performance gate, and KIS-7 likely unpriced for Kisiwa on S. This ruling amends §9r.2 (R3r's statement that the Performance gate stays closed) and R3q §9q.2 KIS-7 item 4.

### 9s.1 What the closed gate costs on the demo (READ)

**The coordinator's cause is confirmed.**
- `dispatch` (`site_outcomes/read.py:257`) and `chain_findings` (`:240`) both go through `_open` (`:140-143`), which raises `PortUnavailable`.
- The gates are `performance_gate` and `finding_index_gate` = `basis_aware_gate(performance_gate, ...)` (`main.py:404-414`, `:566`). The second changes only the reason, never the permit.
- `performance_and_prebuild` runs the Performance comparison for `("KOBO-001",)` only (`T/demo_combined.py:631-635`).

**The Kisiwa board with the gate closed (`site_outcomes/mini.py:458-530`).**
- `read_state` is PARTIAL with `dispatch` and `chain_findings` failed.
- There is no Dispatch assessment. MG-2, MG-4 and MG-6 are unsettled because `base` needs `dispatch is not None`.
- No dispatch Finding and no lead is shown, because `lead_finding` needs heads and `source_open`. The Optimize `earnings` (MG-2 fuel cost) is never priced on **any** Kisiwa day.
- **The fuel story is hit as well.** `finding_moved_outcomes(MINI)` includes **MG-8**, because `outcome_map.py:23` maps `FINDING:UNEXPLAINED_FUEL` to MG-8. The loop at `mini.py:526-527` therefore sets MG-8 unsettled whenever `findings_ok` is false (`heads is None`).
- So the K4b Protect fuel row's **status is UNKNOWN** on every Kisiwa board, even though its `fuel_*` reads are ungated and succeed.
- The fuel thread line comes from `chain_threads`, which is ungated, and should still render. The R3m Assure fuel verdict is also ungated.
- **KIS-6** passes either way: the summary cells and the S board come from the same composition.
- **Conclusion.** The S−5d "morning after" board beat would show a partial-read notice and an UNKNOWN fuel outcome. That is demo-critical.

### 9s.2 (a) The honest fix: run the product's own Performance comparison for Kisiwa (empty-set)

**No legacy evidence is needed.**
- `performance_migration run` reads the file-backed dispatch history through `JsonAssessmentStore.load_history`, which returns an empty history when the Site has no file (`json_assessment_store.py:47-52`).
- `compare` then writes a designed **empty-set report** (`performance_comparison.py:139-158`). Its statement is "Empty-set comparison: the file-backed baseline holds no dispatch claim for KISIWA-001, so no claim is said to match; a zero-inventory statement, not claim parity."
- Its outcome is PASSED **only if** the live lineage has no breaks and no head selected under another model (`:141-146`, `:219-252`).
- This is the S3-01 tool run as designed, the same command Kobo gets. It is not tuned and not forced. If the lineage is broken, the report says FAILED and the gate stays closed with that reason.

**Rejected: opening the ports under the q12-6 cutover basis.**
- q12-6 is an *Evidence* cutover basis. Ruling 3 (M4) limited its effect on the Performance gate to the reason text (`basis_reason`), on purpose.
- Widening it is a product-semantics change. It is not a demo step.

**Rejected: accepting PARTIAL.** It loses MG-8 on the fuel beat (§9s.1).

**The change (K9, `T/demo_combined.py` `performance_and_prebuild`, `:631`):**
```python
for site in ("KOBO-001",) + (("KISIWA-001",) if "kisiwa" in self.story().get("sites", ()) else ()):
```
- `story.json` exists before the children run (`:481`). `performance_and_prebuild` is first called from `finish` → `tick` (`:592`).
- The serve loop's ticks then rerun Kisiwa's comparison as they do Kobo's: a new report after new assessments, so the gate never goes stale on a rehearsal day.
- R3r's cutover basis **stays**. It answers the separate S2 Evidence gate (Overview and board `source`).

**What changes on screen (honest).**
- Kisiwa's dispatch Findings and their money appear where the stored data has them. The Kisiwa board day of night 1 (local 2026-10-28/29) shows the MG-2 fuel-cost earnings.
- MG-8 settles. The boards read AVAILABLE.
- The Performance source reason on Kisiwa's screens becomes the report's own empty-set statement. Its system wording goes to the post-rehearsal plain-language polish batch and does not block.

**Proof (K9, extend KIS-OV; no new row).**
- KIS-OV also asserts that the newest Kisiwa Performance report is `outcome == "PASSED"` and `empty_set is True`, read through `build_performance_comparison_reports().latest("KISIWA-001")` in the served environment.
- It asserts that the S−5d and S boards read `read_state == "AVAILABLE"`, which replaces R3r's "reported, not asserted".
- L0 self-test: add fail bodies for a FAILED report and for a PARTIAL board.

### 9s.3 (b) Expectations: KIS-7 is rewritten from data; KIS-6 and CH5D1-O1 unchanged

**Real data has no priced Kisiwa Finding on S.**
- The two PRICED fuel-cost-2 heads are both on night 1 (2026-10-28 17:40–19:05Z and 22:55Z – 10-29 00:15Z).
- `lead_finding` (`chain/read.py:176-198`) picks a head only if its episode overlaps the board day `[local 00:00 S, +1 d)`.
- So Kisiwa is truthfully **unpriced on S** even with the gate open. R3q's KIS-7 premise ("Kisiwa priced on S") was wrong, and its item 4 ("never re-expected to the one-Site path") is withdrawn.
- **No story change.** Adding a priced consequence on S would tune data to a check.

**KIS-7 (replaces §9q.2 KIS-7).** It is pure in `demo_rows.kis7`, with its expectations derived from stored rows and never typed:
1. **S summary.** Run main's `optimize_card(s_body, KOBO, allowed=(KOBO, KISIWA))` (K8, data-tolerant, one-Site and ≥2 paths).
2. **Kisiwa on S matches the data.** `expected_s` = whether some Kisiwa dispatch Finding with a PRICED latest money head (KIS-2's head and interval reads) has an episode overlapping Kisiwa's S local day. Assert `(KISIWA in priced codes) == expected_s`. On the current story `expected_s` is False and Kobo alone is priced; that is reported.
3. **Kisiwa priced where the data is.** `d1` = the Kisiwa local date of the earliest PRICED head's episode start. Read `GET /api/sites/KISIWA-001/outcome-board?date=<d1>`. Its OPTIMIZE_COST `earnings` has a value, and `earnings_money(claim)["amount_high"]` equals the stored money head's `amount_high` for the lead head of that day.
4. **No sum.** `never_summed` runs over the S and week summaries and the Portfolio week body whenever two or more Sites are priced in any of them. Otherwise it is reported as "≥2 path not reached on real data" and stays covered by the L0 self-tests.
5. **L0:** pass bodies for the one-Site S and for priced `d1`; fail bodies for "Kisiwa priced on S while `expected_s` is False", "`d1` unpriced", "`d1` amount differs" and "a summed string".

**Unchanged.**
- **KIS-6:** its cells equal the board in either state.
- **CH5D1-O1** (main, K8): it already allows one or two priced Sites from `(KOBO, KISIWA)`.
- **Prerequisite:** K9 must merge main (96d597573, K8) before the prepare, since `optimize_card`'s `allowed` and the K8 re-expectations are not on K9 yet. That merge was needed for the rehearsal anyway.

### 9s.4 (c) Owner K9, before the rehearsal prepare, after one clone probe

Order:
1. Merge main into K9.
2. Make the §9s.2 change and the KIS-7 rewrite, then commit.
3. **Clone probe (about 20 minutes).**
   - Use a fresh `*_test` clone of `assetops_demo3_kisiwa_test` and a **copy** of `AssetOpsV1-k7f\var\demo3_kisiwa`. The K7-F folder itself is never written.
   - Record the R3r basis.
   - In the prepare's environment, run `python -m assetops_backend.performance_migration run --tenant demo --site KISIWA-001`.
   - Serve and record the following, before and after:
     - the report outcome and `empty_set`;
     - the S−5d and S boards' `read_state` and failed ports;
     - MG-8 state;
     - the `d1` board's Optimize earnings;
     - whether the estate Findings list holds Kisiwa's fuel Finding row (K8's after-coverage join);
     - the Kisiwa rows check-all runs on that DB.
4. The delta review (same addendum as R3r): only High or Medium findings block.
5. The 2-hour prepare.

**Stops (report to the Architect; no patch, no prepare):**
- **S-s1:** the Kisiwa report is not PASSED, or the gate is still closed after it.
- **S-s2:** any Kisiwa row passes before and fails after.
- **S-s3:** a board still reads PARTIAL after the report, with any failed port.
- **S-s4:** `d1` is unpriced after the report.

### 9s.5 (d) Size, path, tripwire

- **K9 +0.15:** 0.02 for the loop line, 0.06 for the KIS-7 rewrite, 0.02 for the KIS-OV extension, and 0.05 for the probe.
- Pre-rehearsal work is about 0.8–0.85, **over R3q's 0.7 watch line**. This ruling reports it.
- **Critical path about 9.5–9.75.** That is at the tripwire, not over it. The probe overlaps the delta review.
- **If a stop fires and the path would cross 9.75**, the cut options in order are:
  1. Keep the §9s.2 change, and make KIS-7 report-only for this rehearsal, asserting after it (−0.05).
  2. Drop the K8c four-Site Kisiwa Overview capture to the post-rehearsal batch (−0.05).
  3. Fall back to PARTIAL: revert the loop line, state the board's partial notice and MG-8 UNKNOWN honestly, and keep the S−5d board link out of the demo script (−0.1). This loses the fuel beat's outcome status, so it needs the owner's acceptance.

  Only option 3 is an owner question, and only if it is reached.
- **Plan HTML (coordinator):** the rulings table gains "DIESEL-1-R3s: Kisiwa Performance gate closed → board PARTIAL, MG-8 (fuel) unsettled via FINDING:UNEXPLAINED_FUEL; fix = product's own empty-set Performance comparison for KISIWA-001 in performance_and_prebuild (PASSED only on clean lineage; not the q12-6 basis); KIS-OV asserts PASSED/empty-set and AVAILABLE boards; KIS-7 rewritten from data (Kisiwa truthfully unpriced on S; priced on its night-1 board day; no story change); KIS-6/CH5D1-O1 unchanged; K9 merges main first; clone probe stops S-s1..S-s4; K9 +0.15; path 9.5–9.75".

### 9s.6 Owner questions

None now. Cut option 3 (§9s.5) becomes one only if a probe stop forces it.

## 9s2. Ruling DIESEL-1-R3s2 — R3s addendum: why Kisiwa's board days never settle (probe stop S-s4)

Claude Architect (binding: Claude, `.ai/ROLE_CONFIG.md:9`). Read-only code reading in `AssetOpsV1-k9` (f994e3cf9, d2c62c73c) and the probe's board JSON (`k9r3s/out/`, the "after" files). No DB, no suites.

### 9s2.1 Cause: Kisiwa has no subject for `productive_kwh`. A prepare will not fix this

The causal chain, READ:
1. **The measure set.** MINIGRID measures are `productive_kwh` (ASSET), `daylight_headroom_kw` (SITE), `critical_served` (SITE) and `avoidable_gen_min` (ASSET) (`chain/measures.py:44-59`).
2. **The subjects.** The subjects of `productive_kwh` are the Site's assets with `supply-use = PRODUCTIVE` (`chain/measure_impls.py:131`, `mini_depth/read.py:378-391`). Kisiwa declares `ESSENTIAL_SERVICE`, `HOUSEHOLD` and `HOUSEHOLD` only (`T/demo_combined_kisiwa.py:62`). So the builder writes **no `productive_kwh` row on any Kisiwa day** (`chain/builder.py:57`, one row per subject).
3. **The calendar.** Kisiwa has no calendar entry, so it takes the all-day default (`config/chain/operating-calendar-v1.json`). No NOT_EXPECTED row covers the day.
4. **Settlement.** `day_settled` needs a row for **every** measure (`chain/read.py:92-98`). So every Kisiwa board day is unsettled.
5. **Gaps.** `_day_grades` (`:53-60`) counts a missing measure as NO_DATA. So `day_gaps` names every day, which gives "31 of 31 days are not assessed yet" even on days whose dispatch was assessed. `chain/reader.py:59-82` counts the same way.
6. **The board.** `settled_day` is False, so `base` is False (`site_outcomes/mini.py:521`). MG-1 to MG-7 are PRODUCER_NOT_SETTLED. `money_head` needs `settled` (`chain/read.py:438`), so the d1 Optimize earnings read "Not known yet" even though the Finding and the price exist.

**A prepare-side contributor (fixed by a real prepare, but not sufficient).** The clone never had `after_children`'s `backfill-a` snapshot build, because that runs only when all three core Sites are present (`T/demo_combined.py:530`, `:561`). A four-Site prepare runs it for every tenant Site, Kisiwa included (`chain/backfill.py:111-155`). Step 4 still fails there, so S-s4 would recur in the rehearsal.

**Site-list audit (every list that could leave Kisiwa out):**

| List | Kisiwa included? | Effect |
|---|---|---|
| `evidence_migration` (`demo_combined.py:585-588`) | No (Kobo only) | covered by R3r's basis |
| Performance loop (`:631`) | yes after R3s | — |
| Objectives (`:576-584`) | No (core only) | by design (R3p Q3). MG-8 "NO_OBJECTIVE" on S is that honest state |
| `drain_mini` | yes (`:589`) | — |
| `after_children` / `backfill-a` | yes (all tenant Sites) | — |
| Tick | yes | `--max-sites 5` covers 4 Sites. The 240 s cap can defer a Site to the next tick through the fair cursor, which is not an exclusion |
| Prebuilt routes (`config/chain/prebuilt-routes-v1.json`) | No: `days.json` boards only | the first Kisiwa board open is a cold build, not a wrong one. **Presenter note:** open the S−5d Kisiwa board link once before the client joins |

No other list leaves Kisiwa out.

**MG-8 on d1 (UNKNOWN, PRODUCER_NOT_SETTLED) is correct.** MG-8 settles from night D−1's fuel window (`mini.py:521-525`). d1 is 2026-10-28, and night 10-27 has no window because night 1 is 10-28.

### 9s2.2 Probe: none needed to decide; the rehearsal goes ahead now

- No tick or prebuild run on the clone can create a `productive_kwh` subject. The cause is decided by code.
- **Optional, non-blocking (5 minutes, SELECT only, on the clone):** count Kisiwa snapshot rows by measure and confirm that `productive_kwh` is absent. If the builder runs it, the result goes in the packet.
- In the rehearsal itself, KIS-OV's AVAILABLE-board assertion stands; the probe showed AVAILABLE.

### 9s2.3 MG-8 "state null" on S−5d is not a defect

- The probe read the S−5d Protect row's `lead_outcome`, which carries only `{key, label}` (`{"key": "MG-8", "label": "Fuel accounted for"}`).
- The row itself reads `NEEDS_ATTENTION`, with the `unexplained_fuel` node for night 10-31 (95.7–144.3 L, 119.57–180.43 USD). So the K4b fuel beat renders.
- The K9 packet quotes the row state and the MG-8 entry from the board's outcome list.
- **Stop:** only if that outcome entry itself carries a null state.

### 9s2.4 Changes, owners, size, path

**Before the rehearsal (K9, about +0.01).**
- KIS-7 item 3 (d1 priced) and R3s stop S-s4 become **report-only for this rehearsal**, with the reason quoted: "d1 is unsettled: no `productive_kwh` subject (R3s2)". This is R3s cut option 1.
- KIS-7 items 1, 2 and 4 stay asserted. Item 2's `expected_s` is False and is observed False.
- No product code changes before the prepare. **The rehearsal prepare starts after the delta review.**

**The product fix is a separate unit, `DIESEL-K10` (measure applicability). It is built only if the owner says yes (§9s2.5).**
- **Rule.** An ASSET-kind measure with no snapshot row anywhere in the read's day range is not applicable to that Site. It is left out of `day_settled`, `readiness_of`, `day_gaps` and the `chain/reader.py` counts, **provided** at least one other measure has a row on that day.
  - A day with no rows at all stays unsettled.
  - A missing SITE-kind measure stays NO_DATA.
  - A subject declared part-way through the range keeps its earlier days unsettled, which is conservative.
- **Why it is sound.** The builder writes a row for every subject on every built day, including NO_DATA rows. So a measure missing from the whole range means the Site declares no subject for it. It does not mean "not built yet".
- **Where.** One shared pure helper, `applicable_measures(rows, measures)`, in `chain/read.py`, called by `ChainRequest.day` and by `chain/reader.py`'s counts. One helper keeps the COH coherence pairs equal.
- **Tests.**
  - A Kisiwa-shaped day (no `productive_kwh` rows) settles.
  - Kobo-shaped rows are byte-equal to before.
  - An empty day stays unsettled.
  - A missing SITE measure stays a gap.
  - A mid-range subject case.
- **Proof.** Serve the rehearsal DB with the K10 code. This is a read-side change, so no re-prepare. If `serve` cannot swap the tree, the proof and the Kisiwa board captures move to the demo-day prepare.
  - d1 earnings are priced, equal to the stored head's `amount_high` (KIS-7 item 3 asserted again).
  - The Kisiwa gap text names only the days before Kisiwa's first evidence.
  - Kobo, Cold and EV board bodies are unchanged on the story days.
- **Size and path.**
  - K10 is about 0.25: code 0.05, tests 0.08, review 0.05, served proof 0.07.
  - It overlaps the 2-hour rehearsal, so the path becomes **about 9.6–9.85, which can cross the 9.75 tripwire**.
  - Without K10, the path stays **about 9.5–9.75**.
- **If K10 is approved and crosses the tripwire, cut in this order:**
  1. Move the K8c four-Site Kisiwa Overview capture to the demo-day prepare (−0.05).
  2. Move the Service empty-default-day check (R3r §9r.4) to the polish batch (−0.02).
  3. Cut K10's served proof to Kisiwa d1 and S−5d only (−0.03).
- **Polish batch either way:** "N of 31 days are not assessed yet" also counts the days before the Site existed. That is a wording item.

### 9s2.5 Owner question

**Should the Kisiwa board days settle for the demo?**
- **Without K10.** The Kisiwa board's Protect row (the unexplained-fuel beat) renders correctly. But Grow, Optimize and Assure read "Unknown", and the board says "31 of 31 days are not assessed yet" beside an assessed fuel Finding. That is honest by the current rule, but it contradicts itself on screen.
- **With K10** (+0.25, path about 9.6–9.85, may cross the 9.75 tripwire), those rows settle and the d1 fuel-cost money shows.
- **Architect recommendation:** yes, K10. The contradiction sits on a demo beat. Use cut 1 first if the path crosses.
- **Default until the owner answers:** the rehearsal runs without K10, and K10 is not started (owner 2026-11-05, no new commitments).

## 9t. Ruling DIESEL-1-R3t — K10 v2 after owner answer

Claude Architect (binding: Claude, `.ai/ROLE_CONFIG.md:9`). Read-only code reading in `AssetOpsV1-k9` (`task/DIESEL-K9-checks-rehearsal` at 62bcb1f97) and main 8b6efd868. No DB, no suites. Input: the owner's answer, verbatim in `.agent/owner-kisiwa-measure-applicability-2026-11-08.md`. This ruling **withdraws K10 v1** (§9s2.4 "Rule") and replaces it with K10 v2 below. Everything else in §9s2 stands.

### 9t.1 Reading the owner

Owner, verbatim: "if the contributing dimensions to growth, whether productive use or otherwise are 0, it should be indicated as such. The component contributor being non existent doesn't mean it is checked.Let the architect weigh in as well."

My reading has four parts.
1. **Show it.** A Grow contributor that is zero must appear on screen as zero. It must not be hidden or dropped, and it must not read "Unknown" when the zero is a known fact.
2. **Not checked.** A contributor that does not exist at the Site has not been checked. Nothing may present it as assessed, complete or met: not a chip, not a state, not a count.
3. **"Whether productive use or otherwise."** This is a general rule for Grow contributors, not a Kisiwa patch. It does **not** say that unknowns become zeros. A contributor whose value is simply not known (cash collected, site earnings) stays "Not available yet". Only a zero that is a **declared fact** reads as zero.
4. **"Let the architect weigh in."** The owner asks for a design view before deciding. I do not read it as approval to build. See §9t.6.

**Where I differ from the coordinator's reading.**
- The coordinator writes "zero / not present" as one state. I split it in two:
  - **declared absent:** the site setup declares no productive-use load. Zero is a sourced fact, shown, and not assessed.
  - **expected but missing:** a load is declared, or the setup cannot be read, but there is no data. This is "Not available yet", a gap, and the day is unsettled.
- The coordinator writes "its absence must not by itself make the day count as checked". I agree. But I do not read the owner as forbidding the day to settle on the measures Kisiwa **does** have: generator minutes, daylight headroom and critical service. The owner rejects two things: a silent drop, and productive use reading as checked. A day that settles on the three measures that apply, and says on screen that productive use was not assessed and is zero by declaration, does neither.
- That last step is my interpretation, not the owner's words. So it goes back to the owner as one plain question (§9t.6).

**v1 fails the owner's test, and fails on a code fact as well.** v1 inferred "doesn't apply" from "no snapshot row in the range". But the builder's subject read **swallows a failed site-setup read as "no subjects"**: `postgres_chain_inputs.py:209-214` `productive_assets` returns `[]` on `MiniReadUnavailable`, which is raised when no single Foundation revision covers the instant (`mini_depth/read.py:386-387`). So a missing row can mean "the setup could not be read". It does not prove "nothing declared", and v1 would have counted a missing-data day as checked. v2 uses only the successful setup read.

### 9t.2 Is there an honest design? Yes: "declared absent, so zero, stated; not assessed"

The Site's setup already holds the fact.
- `MiniDepthRead.productive_users` (`mini_depth/read.py:375-397`) returns `[]` only when exactly one Foundation revision is in force and it declares no `LOAD` with `supply-use = PRODUCTIVE`.
- It **raises** when the revision is missing or ambiguous ("never 'none declared'", `:379`).
- The board already reads it: `_productive_sales` at `mini.py:959-963`. Today the empty list renders `SALES_NO_USERS` "Not available yet · no productive users identified for this site". That files a declared fact under missing data, which is the wrong category on the owner's terms.

**The three states of `productive_kwh` on a Site-local day:**

| State | Condition | Settlement and gaps | Screen |
|---|---|---|---|
| Measured | the day has a `productive_kwh` row | as today | as today |
| **Declared absent** | no `productive_kwh` row, **and** the site setup declares no productive-use load at the day's start and at its end (one revision each, known at `k`), **and** the day has a row of another measure | `productive_kwh` is left out of that day's applicable measures. It is never graded, never COMPLETE and never counted as checked | stated: "0 kWh · no productive-use load declared …" |
| Missing | anything else (a load is declared but there is no row, the setup is missing or ambiguous, or the day has no row at all) | NO_DATA, a gap, unsettled (today's rule) | "Not available yet" (today's wording) |

No zero row is written. Zero is a statement, not a measured value or a money figure: it is never priced, never summed and never graded.

**What the Kisiwa board shows with v2.** States are derived from the data; the proof records them per day (§9t.4).
- **Grow** (MG-1, MG-6, MG-3).
  - MG-1 settles. Kisiwa has no declared objective (R3p Q3), so `outcome_state` (`outcomes/status.py:55-102`) gives **Opportunity** when the headroom thread is open on that day, else **No objective**. It can never give "On track", because ON_TRACK needs an objective verdict, and a declared-absent day gives no reading.
  - MG-6 and MG-3 stay Not measured.
  - Productive-use sales line: `SALES_NONE_DECLARED`.
  - Headline: the spare-solar headline if there is one (`mini.py:575`), else `GROW_NONE_HEADLINE`.
  - MG-1 earnings node: `money.none_declared` instead of "Not known yet".
  - Cash collected and Site earnings keep their current "not available" texts. They are unknown, not zero.
- **Optimize** (MG-2): settles (`base`). On d1 (local 2026-10-28) the lead dispatch Finding's money head is priced (`chain/read.py:437-438` now sees `settled`), so `earnings` shows the stored head's amount (KIS-7 item 3). The state follows the open primary Finding as on Kobo.
- **Protect** (MG-5, MG-4, MG-8): MG-5 and MG-4 settle. MG-8 is unchanged (night D−1 window, §9s2.1). The fuel beat is unchanged.
- **Assure** (MG-7): settles. Its readiness is R5 over the **applicable** measures only. Productive use never lifts it to Full.
- **Gap line under the rows** (`finding_gap_line`, `mini.py:353-366`):
  - It counts only days that miss an **applicable** measure: days before Kisiwa's first evidence (no rows at all) and days with PENDING rows.
  - Whenever any window day is declared absent, it adds the stated note `GAPS_NONE_DECLARED`.
  - Before: "Not available yet · 31 of 31 days are not assessed yet". After: "Not available yet · {g} of 31 days {verb} not assessed yet · Productive use not assessed: no productive-use load declared for this site (0 kWh)". The template switches to `GAPS_NO_READINGS` when no gap day holds a PENDING row (unchanged rule). When `g = 0`, the line is the note alone, with `days: []`.
  - Effect: `finding_gaps` is non-null on Kisiwa, so the Issues column reads "… on the days checked" (`OutcomeBoard.tsx:342`). That is truthful, and it is intended.

### 9t.3 K10 v2 unit card (consolidated; this card is all the builder reads)

**Branch:** `task/DIESEL-K10-declared-none` from main. Do not build until the owner answers yes (§9t.6).

**1. Shared rule: `backend/assetops_backend/chain/reader.py`.** This is the "one day-count rule" module. `chain/read.py` imports from it, so the board and the counts cannot diverge.
```python
#: K10 v2 (R3t): ASSET measures whose subjects are a site-setup declaration; only these can be declared absent.
DECLARED_SUBJECT_MEASURES = frozenset({"productive_kwh"})

def applicable_measures(per_measure: Mapping[str, Sequence[str]], measures: Sequence[str],
                        none_declared: Collection[str] = ()) -> tuple[str, ...]:
    """R3t: `measures` without each m in `none_declared` ∩ DECLARED_SUBJECT_MEASURES that has no row this day,
    provided the day has a row of some other measure. A declared-absent measure is out of the day's grades; it is
    never COMPLETE and never a gap."""
```
- `_counts` gains `none_declared: Mapping[date, Collection[str]] = {}`, and computes each day's grades over `applicable_measures(per_measure, measures, none_declared.get(day, ()))`.
- `counts` passes the same keyword. `grade_counts_of(facts, measures)` passes `getattr(facts, "none_declared", {})`.
- `GradeCounts` is unchanged: no new field, so the wire JSON is unchanged.
- `SnapshotReader.grade_counts` and `grade_counts_many` are unchanged. They feed the `snapshots` CLI report only, and keep counting raw rows.

**2. `chain/read.py`.**
- `_day_grades`, `readiness_of`, `day_grade`, `day_settled` and `day_gaps` each gain a keyword-only `none_declared` argument, defaulting to empty. Each applies `applicable_measures` per day before its current logic. With the default, behaviour is byte-identical.
- `DayFacts` gains `none_declared: Mapping[date, frozenset[str]] = field(default_factory=dict)`.
- `ChainRequest.day`, after the snapshot read:
  1. `cands = set(measures) & DECLARED_SUBJECT_MEASURES`. If it is empty, use `{}` (Cold and EV never reach step 2).
  2. **Lazy trigger.** `ask` = the days that hold a row of some measure but no row of the candidate. If it is empty, use `{}` (on Kobo's story days, no extra statement).
  3. If the port has no `declared_none_days` attribute, use `{}`. Test fakes stay unchanged.
  4. Otherwise: `read_scope.memo("chain.none_declared", ports.declared_none_days, tenant_id, site_id, m, tuple(ask), k)` gives a `frozenset[date]`. Store it as `{d: frozenset({m})}`.
  5. Pass the result to `day_settled`, `readiness_of` and `day_gaps`, and keep it on `DayFacts`.
- A port error propagates as any chain read does. The board then reads PARTIAL, and a failed read never becomes a claim.

**3. Port and adapter.**
- `ChainReadPort` documents an optional method: `declared_none_days(tenant_id, site_id, measure, days, known_at) -> frozenset[date]`.
- `PostgresChainRead.declared_none_days`:
  - It returns `frozenset()` for any measure other than `productive_kwh`.
  - **One statement**: the Site's timezone, plus every `foundation_revision` row of the Site with `recorded_at <= k AND (superseded_at IS NULL OR superseded_at > k)` whose validity overlaps `[local start of min(days), local end of max(days))`. `k` = `COALESCE(:known_at, clock_timestamp())`.
  - Use the same timezone column the builder's Site read gives `site.timezone` (`chain/builder.py:48`). The pre-flight names the column.
  - In Python, a day is declared absent only when **both** its local start and its local end − 1 µs are covered by exactly one revision, and `productive_loads(content) == []` for each.
- **Pure filter, shared with the builder's subject rule.** Move the component filter at `mini_depth/read.py:389-391` into a module-level pure function, `productive_loads(content) -> list[dict]`. `productive_users` and the adapter both call it, so "declared absent" and the builder's "no subject" cannot drift apart.
- Wire the adapter wherever the composition builds `PostgresChainRead`. No new port object.

**4. OutcomeEvaluator: `chain/outcomes.py` and `chain/vocabulary.py`.**
- `NodeInputs` gains `none_declared: frozenset[str] = frozenset()`: the measures declared absent on **every** day of the node window.
- In `_earnings`, for a non-FINDING record: if `measure in inp.none_declared` and `rows` is empty, return `v.money_claim(label, None, None, "NONE_DECLARED")`.
- `money_claim` maps reason `NONE_DECLARED` to `node_text("money.none_declared")`.
- Value None and basis NOT_KNOWN mean the claim is never priced and never added to `estate_income` (`never_summed` is unaffected).
- `_kpi` is unchanged. With no objective it gives "no target", and with an objective and no reading it gives NOT_JUDGED (UNKNOWN), never MET.

**5. Board: `site_outcomes/mini.py`.**
- `decl = day_facts is not None and "productive_kwh" in day_facts.none_declared.get(day, ())`.
- In `_productive_sales`, when `users == []`:
  - if `decl`, return the contributor `_sales_line(SALES_NONE_DECLARED)` (no chip, no link), `subline: None`, and the flag `"none_declared": True`;
  - otherwise keep `SALES_NO_USERS` and `GROW_SUBLINE` as today. This covers a revision change inside the day, where the two reads disagree, and stays conservative.
- Headline: `headline[GROW]` = the spare-solar headline if there is one, else `GROW_NONE_HEADLINE` when the flag is set. No headline money.
- `node_in` gets `none_declared = frozenset(m for m in DECLARED_SUBJECT_MEASURES if all(m in day_facts.none_declared.get(d, ()) for d in node window days))`. For the mini board the node window is `(day, day)`.
- `finding_gap_line(day_facts, requested)`:
  - `note` = any window day has a declared-absent measure;
  - with gaps: the current text, plus `" · " + GAPS_NONE_DECLARED` when `note`;
  - with no gaps and `note`: `{"text": GAPS_NONE_DECLARED, "days": [], "withheld": False}`;
  - with no gaps and no `note`: None, as today.
- `settled`, `base` and every other line are unchanged. They follow `day_facts.settled`.

**Literals** (backend only; no frontend change, no wire key added). MOCK DEVIATION **MD-K10-1**: v69's Grow row shows a site with productive users (`frontend/mockups/v69/index.html`, Grow row) and has no "none declared" state. These literals are the honest addition, and they sit in the existing contributor, headline and gap-note slots.
- `SALES_NONE_DECLARED = "0 kWh · no productive-use load declared for this site · not a metered reading"`
- `GROW_NONE_HEADLINE = "No productive-use load declared · 0 kWh"`
- `GAPS_NONE_DECLARED = "Productive use not assessed: no productive-use load declared for this site (0 kWh)"`
- `vocabulary.py`: `"money.none_declared": "No productive-use sales · no productive-use load declared"`

The plain-language polish batch may reword these, but it may not drop the "0 kWh" or the "not assessed" clauses.

**Safeguards (each one has a test):**
1. Declared absent comes only from a successful setup read: exactly one revision in force at both day bounds. A missing or ambiguous revision means missing data.
2. Only `productive_kwh`. Every other measure keeps today's rule.
3. A row for the measure on a day always wins.
4. A day with no row of any other measure stays NO_DATA and unsettled.
5. The excluded measure is never COMPLETE, never in `enough_data_days` on its own account, and never lifts readiness.
6. No zero row and no money. The MG-1 earnings value is None, so it is never summed.
7. MG-1 can never be ON_TRACK or MET because of a declared-absent day.
8. Without the port method, with no candidate measure, or with an empty trigger, the output is byte-identical to today, and so is the statement count.

**Tests** (targeted only; no full suite, per test-suite policy):
- `backend/tests/test_k10_declared_none_rule.py` (pure; Kisiwa-, Kobo- and Cold-shaped rows):
  1. A Kisiwa-shaped day with declared absent settles, and readiness is over 3 measures.
  2. The same day without the declaration stays unsettled and is a gap (v1's hole).
  3. A day with no rows stays unsettled even when declared absent.
  4. A `productive_kwh` row present while "declared absent" is passed: the row wins.
  5. A missing SITE measure on a declared-absent day is still a gap.
  6. Kobo-shaped rows give `DayFacts` and `GradeCounts` equal to before (with and without the keyword).
  7. `grade_counts_of` equals `_counts` with the same `none_declared` (the COH pair).
  8. The lazy trigger: a fake port records zero calls on Kobo-shaped rows and on a Cold site type.
- `backend/tests/test_k10_declared_none_adapter_postgres.py` (authorized `*_test` DB):
  - one revision with no productive load gives the day;
  - one revision with a productive load gives no day;
  - no revision gives no day;
  - two overlapping revisions give no day;
  - a revision change inside the day, where the end bound declares a load, gives no day;
  - the call is exactly one statement.
- `backend/tests/test_k10_declared_none_board.py` (mini compose with fakes):
  - the Grow line, headline and MG-1 earnings node literals on a declared-absent day;
  - the spare-solar headline still leads when present;
  - `users == []` without `decl` keeps `SALES_NO_USERS`;
  - the gap line in its three forms;
  - MG-1 with an objective and declared absent is not ON_TRACK;
  - a Kobo-shaped composition body is equal to before.

### 9t.4 Proof plan: read-side, so no re-prepare. Confirmed, with one correction

- **Still read-side.** No stored row, migration or prepare step changes. It reads `foundation_revision`, which every prepare already writes. **Confirmed.**
- **Correction to R3s2.** `code_version` hashes every backend source file (`chain/adapters/file_code_version.py:3`, `:58`). So under K10 code, every stored prebuilt body is stale, and a serve with ticks would re-prebuild into that database.
  - **Do not serve the rehearsal DB itself.** Serve a fresh `*_test` clone of it, with a **copy** of its var folder (the R3s §9s.4 pattern). The rehearsal DB stays untouched.
  - The code is K10 merged with K9: K9 merged to main first, or merged locally into the K10 worktree for the proof.
- **Kisiwa assertions.**
  - KIS-7 item 3 is asserted again: d1 earnings are priced and equal to the stored head's `amount_high`.
  - R3s stop S-s4 is asserted again.
  - The d1, S−5d and S Kisiwa boards read AVAILABLE. On a declared-absent day their Grow line, headline and MG-1 earnings carry the §9t.3 literals.
  - Every Kisiwa gap day either holds no row at all or holds a PENDING or NO_DATA row of an **applicable** measure. This is derived from the stored rows, never typed.
  - The gap line carries `GAPS_NONE_DECLARED`.
  - Record `g` and the gap days.
- **Unchanged checks.**
  - **Kobo, Cold and EV byte-unchanged.** Their board bodies (S−5d, S, d1) and the one-Site and three-Site Portfolio bodies are compared, K9 code against K10 code on the same clone, cold builds both. They must be equal after removing only the keys that differ between two K9-code reads of the same route (record that key list; it is expected to be empty).
  - **Why they are unchanged, by code.** Cold and EV have no candidate measure. Kobo declares productive users, so the trigger is empty or the port finds no day. No wire key is added.
  - The four-Site Portfolio changes only in Kisiwa's contribution. Record the before and after card texts, and the reviewer reads them against §9t.1.
  - KIS-6 and CH5D1-O1 must pass unchanged.
- **Stops (report to the Architect; no patch):**
  - **K10-s1:** any Kobo, Cold or EV body differs.
  - **K10-s2:** a Kisiwa day settles where the adapter found the setup missing or ambiguous.
  - **K10-s3:** d1 is still unpriced.
  - **K10-s4:** any Kisiwa row shows productive use as checked, complete or on track.

### 9t.5 Size, critical path, cuts

- **K10 v2 is about 0.40**, against 0.25 for v1:
  - code 0.12: rule and wiring 0.04, port, adapter and filter 0.05, evaluator, board and literals 0.03;
  - tests 0.10;
  - review 0.06;
  - clone and served proof 0.12.
- **Why it grew:** a real site-setup read replaces v1's unsound inference, the MG-1 earnings node must stop saying "Not known yet" beside a stated zero, and the proof needs a clone (the `code_version` correction).
- **Path.** It overlaps the 2-hour rehearsal. Using R3s2's overlap ratio, the path is **about 9.75–10.0** against the **9.75 tripwire**, so it crosses. Without K10 it is about 9.5–9.75.
- **Cuts, in order:**
  1. Move the K8c four-Site Kisiwa Overview capture to the demo-day prepare (−0.05).
  2. Move the Service empty-default-day check (R3r §9r.4) to the polish batch (−0.02).
  3. Cut the served proof to Kisiwa d1 and S−5d plus the Kobo S body equality. Cold and EV equality rests on the code argument and the lazy-trigger test (−0.04).
  4. Move the whole served proof and the Kisiwa board captures to the demo-day prepare. K10 then merges on its targeted tests and review (−0.06).
- After cuts 1–3 the path is about 9.65–9.9. After cut 4 it is about 9.6–9.85. **That can still cross 9.75**, so §9t.6 asks the owner.
- **Never cut:** the stated-zero literals, the "not assessed" note, or safeguard 1. Without them, the owner's two conditions fail.

### 9t.6 Owner question (one, plain language)

> Kisiwa has no productive-use equipment (like a mill), so there is nothing to measure there. Proposed: Kisiwa's board says "0 kWh · no productive-use load declared for this site", and clearly says productive use was **not** assessed. Its days then count only for what Kisiwa actually has: generator, fuel, service and solar. As a result, the cost, service and evidence rows show real results, and night 1's generator cost shows its money. A day only counts if the site setup really says "none". Missing data is still shown as missing. Cost: about 0.4 units, running alongside the rehearsal. Even after moving lower-priority screenshots to demo day, the finish may land up to about a quarter unit past the 9.75 limit.
> Options:
> 1. **Build it (recommended).**
> 2. **Wording only now** (about 0.05): Kisiwa shows the "0 kWh · none declared" line and says honestly that its other rows are not assessed yet. The demo stays on Kisiwa's fuel story, and the full fix comes after the demo.
> 3. **Leave as is.**

- **Recommendation: option 1.** The on-screen contradiction sits on a demo beat. v2 meets both of the owner's conditions, and it is the only design that settles the days honestly.
- **Default until the owner answers.** K10 v2 is not started (owner 2026-11-05). The rehearsal is unaffected.
- **Option 2 literals** (`mini.py` only; no rule change):
  - `SALES_NO_USERS` is replaced by `SALES_NONE_DECLARED`, but only when `productive_users` returned `[]`.
  - The gap text gains `" · days here are not settled yet: the system needs a productive-use figure and none is declared (0 kWh)"` when that read returned `[]`.
  - The demo script keeps the Kisiwa Grow, Optimize and Assure rows and the d1 board out of the talk track, and stays on the Protect fuel beat.

### 9t.7 Rehearsal interplay

- **The rehearsal proceeds now, without K10.** K10 v2 changes no prepare step, story, stored row or check expectation used before or during the prepare.
- R3s2 §9s2.4 stands for the rehearsal: KIS-7 item 3 and S-s4 stay report-only with their quoted reason, KIS-7 items 1, 2 and 4 stay asserted, and KIS-OV stays as it is.
- The rehearsal's Kisiwa board captures show the current state (Unknown Grow, Optimize and Assure rows; Protect fuel beat correct). They are not demo assets. The K10 captures come from the clone proof, or from the demo-day prepare under cut 4.
- **Files.** K10 touches `chain/reader.py`, `chain/read.py`, `chain/outcomes.py`, `chain/vocabulary.py`, `chain/adapters/postgres_chain_read.py`, `mini_depth/read.py` and `site_outcomes/mini.py`. K9 touches `T/demo_combined.py` and the demo check rows. No overlap is expected, and the pre-flight confirms it.
- **Plan HTML (coordinator):** the rulings table gains "DIESEL-1-R3t: owner answer read (zero shown; absence never 'checked'); K10 v1 withdrawn (row-absence inference unsound: builder swallows a failed site-setup read as no subjects); K10 v2 = declared-absent productive_kwh from one successful Foundation read per day bound, left out of the day's applicable measures but never graded or counted checked; stated '0 kWh · no productive-use load declared' on Grow line, headline, MG-1 earnings and gap note; one shared rule in chain/reader.py; Kobo/Cold/EV byte-unchanged; proof on a clone (code_version correction); ~0.40, path ~9.75–10.0 → cuts 1–4; owner question (build / wording only / leave); rehearsal proceeds now".

### 9t2. Ruling DIESEL-1-R3t2 — K10 stop K10-v1 (vocabulary) and deviation D2

Claude Architect (binding: Claude). Owner approved K10 v2 ("Build it (Recommended)", ae6d4cb71). Read-only. Trigger: phase 1 on `task/DIESEL-K10-declared-absent` (56256bbc9, be6b27b8f) stopped at K10-v1. The cause is `frontend/src/test/productVocabulary.json:56`, which bans "load" as an unexplained abbreviation. All four R3t literals use it, so `test_out_b2_vocabulary::test_board_and_status_copy_pass_vocabulary` reports 4 hits.

**Ruling: option (a), reword "load" to "equipment".**
- "Equipment" is the owner's own word in the approved question: "productive-use equipment (like a mill)".
- It is not on the banned list.
- The guard stays unchanged, with no exact-text allowance. Line 184's precedent allows only exact v6.9 mock labels, and these literals are not mock labels.
- The "0 kWh" and "not assessed" clauses stay as they are.

The four literals below replace the §9t.3 literals. MD-K10-1 is unchanged.
- `SALES_NONE_DECLARED = "0 kWh · no productive-use equipment declared for this site · not a metered reading"`
- `GROW_NONE_HEADLINE = "No productive-use equipment declared · 0 kWh"`
- `GAPS_NONE_DECLARED = "Productive use not assessed: no productive-use equipment declared for this site (0 kWh)"`
- `vocabulary.py`: `"money.none_declared": "No productive-use sales · no productive-use equipment declared"`

The builder updates the K10 tests to the new literals and reruns the vocabulary test and the three K10 test files. If any other vocabulary hit appears, that is a stop to report, not a guard edit.

**D2: confirmed.** The builder replaced R3t's `COALESCE(:known_at, clock_timestamp())` with the file's existing form: `CAST(:k AS timestamptz) IS NULL OR recorded_at <= :k`, plus `superseded_at IS NULL` when k is null. I confirm it because:
- It is the established "as known now" form in `postgres_chain_read.py`, and the clock guard accepts it.
- It differs from R3t only for a revision whose `superseded_at` is in the future. Treating that revision as superseded is the conservative choice: it can only fail to declare absent, so the day stays missing data. Safeguard 1 holds.
- The adapter test adds no case for this.

### 9t3. Ruling DIESEL-1-R3t3 — K10 review M1 (whole-day coverage), L1, L2, phase-2 Kobo check

Claude Architect (binding: Claude). Read-only. Trigger: `.agent/review-K10.md` (717838ed7, FIX), finding M1. This ruling replaces the two-bound rule in §9t.3 item 3.

**M1: the reviewer's option (a), whole-day coverage.** The reviewer is right: two bounds miss a mid-day mill and a mid-day gap.
- With a mid-day gap, a failed setup read would become "declared absent". That breaks R3t safeguard 1.
- (a) is honest. It can only make fewer days count as declared absent than the current code.
- (b) would also wrongly refuse an ordinary day on which a no-mill revision is replaced by another no-mill revision.

**The rule.** A pure function in `chain/reader.py`, next to `applicable_measures`, called by `PostgresChainRead.declared_none_of` for each day. The adapter keeps its one statement.
```python
def declared_none_day(revisions: Sequence[tuple[datetime, datetime | None, bool]],
                      lo: datetime, hi: datetime) -> bool:
    """R3t3: (valid_from, valid_to, has_productive) of the revisions known at k. True only when the revisions
    overlapping [lo, hi) (valid_from < hi and (valid_to is None or valid_to > lo)) are at least one, none has a
    productive load, and together they cover [lo, hi) with no gap: sorted by valid_from, cursor = lo; a revision
    with valid_from > cursor is a gap -> False; cursor = max(cursor, valid_to or +inf); finally cursor >= hi."""
```
- `[lo, hi)` is the Site-local day as UTC instants, the same instants `board_day` gives.
- `has_productive = bool(productive_loads(content))`.
- The SQL keeps the D2 known-at form. Its overlap filter becomes the whole requested span: `valid_from < :hi_span AND (valid_to IS NULL OR valid_to > :lo_span)`.
- Overlapping revisions are allowed by the rule. The exclusion constraint prevents them among current revisions anyway. If any overlapping revision has a productive load, the result is False.

**Required pure test cases** (`test_k10_declared_none_rule.py`):
1. One no-mill revision covers the day: True.
2. Open-ended `valid_to = None`: True.
3. Two contiguous no-mill revisions changing at 12:00: True.
4. A revision ending exactly at `lo` (excluded), then a no-mill revision from `lo`: True.
5. `valid_to == hi` exactly: True (half-open).
6. **Mid-day mill**, as the reviewer described (none, mill 08:00–14:00, none): False.
7. **Mid-day gap**, as the reviewer described (none, no revision 08:00–14:00, none): False.
8. A gap at the start (first revision from 00:30): False.
9. A gap at the end (`valid_to` 23:00): False.
10. No revisions: False.
11. Overlapping revisions, one with a mill: False.

The two reviewer cases (6 and 7) are also kept as adapter cases on the `*_test` DB. Each must return `{}` through `declared_none_of`.

**L1: fix now** (about 0.01). Add direct evaluator assertions to the safeguard-7 test, on a declared-absent window with an MG-1 objective:
- the `_month_reading` value is `None`, never `0`;
- `complete` is False;
- the verdict is neither MET nor ON_PACE.

Both surviving mutations must then fail the test. Record this in the packet.

**L2: revert now.** Revert the whitespace slip at `:250`.

**Phase-2 Kobo check: confirmed, and made explicit.**
- The K10-s1 body comparison already catches a changed Kobo body. In addition, the proof records Kobo's declared-absent result, through a direct `declared_none_of` call or a debug of `DayFacts.none_declared`, over:
  - the S−5d, S and d1 board windows;
  - the one-Site, three-Site and four-Site Portfolio windows.
- **Any non-empty Kobo set is stop K10-s1**, even if the bodies happen to be equal.
- One extra Kobo statement on such a day is expected and is recorded, not a stop.

**Size:** about +0.04 on K10: rule and tests 0.03, L1 and L2 0.01. The path moves within §9t.5's range. The cut order is unchanged.

