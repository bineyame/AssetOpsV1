# Independent review: Layer 4 transformation design pack

**Reviewer:** fresh Claude reviewer (not the author) · 16 Nov 2026
**Target:** `Docs/demo-sprint/product-direction-layer4/` (main document .md/.html, nine companion artifacts, `interactive-mockup-vNEXT/`), branch `task/product-direction-layer4-design` at `fe2392899`, plus the untracked pack.
**Judged against:** the owner brief `.agent/AssetEcon_Product_Direction_Layers_1_to_3_and_Claude_Brief_REVISED.md`, Parts I–V as the contract and Part VI (C0–C4) as the commission. The baseline is `.agent/decision-intelligence-mechanism-2026-11-14.html`.
**Mode:** read-only. I did not edit the deliverable, code, databases or Docker, did not use port 5490 and did not commit. I did not run the full test suite.

## Verdict: **ACCEPT WITH NOTES**

There are no High findings. The pack covers C1, C3 and C4, it is grounded in the code, its arithmetic reconciles, and it is honest about what is simulated or missing. Four Medium findings should be fixed on the branch **before the owner inspects the mock-up**:

- M1 weakens a mandatory C3 scenario on a client screen.
- M3 makes the budget switch, which is the demo's headline interaction, hard to read.
- M2 is a naming conflict with existing code that would cause a migration hazard later.
- M4 is a disclosed acceptance gap that needs an owner decision.

None of them changes the architecture.

---

## Checks I ran and what they returned

| Check | Result |
|---|---|
| `python3 check_manifest.py` | `73 checks passed, 0 failed`, exit 0 |
| Independent arithmetic reconciliation, by hand, of figures the checker does **not** cover | All reconcile. Lakeside: Kobo STOPSOC 12-month net 2,916 (250.50×12−90) and both sensitivities (2,286, 2,166); huller 3,540; welding −8.25 (break-even 0.4125, shown as 0.42); KIS-BATT60 −11,660; Mto energy-to-cash chain 6,000→5,700→5,580+120→5,400→1,890+150+120; Kobo fuel balance 220+1,200−240=1,180 and split 210+120+30+120=480 L; coverage 7,545/8,245 = 91.51%; buy-now switch 3,880−360+2,910 = 6,430; LOI comparison 3,546 vs 2,556 (Δ 990). Harvest Cold: all kWh models, MWEA-AGG 1,670, KIRI repair 1,512.40 and replace −1,988.40, B-1031 at 18/crate. Metro Bus: Embakasi plan and actual cost parts, deadline cost 15,216 and saving 6,928.80, 12-month net 81,645.60, Ruiru 12,580.32, portfolio 40,605.12/1,302 = 31.19, departures 620/248/434. The SLA clock (96 h; 31 h) and the 27 Nov notice date also check. |
| Mock-up lineage | `frontend/mockups/` holds v69, v70, v71 and v72. v72 (13 Nov) is the newest, but it is four standalone pages (foundation sheet, Portfolio/Site hi-fi, upload). v70 is the newest **complete** interactive mock-up. `src-v70-baseline/*` is byte-identical to `frontend/mockups/v70/*` (8/8 files). |
| Change register accuracy | The diffs against the baseline match the register exactly. `screens.js` changes rail, shell delegation, review bar, notes key, export, links and initial render (S1–S8). `portfolio.js` changes the Optimize basis note. `outcomes.js` adds the banner hook and a re-pointed link. CSS is unchanged. `node build.mjs` on a scratch copy rebuilds `index.html` **byte-identical**. |
| Served the mock-up statically on 127.0.0.1:8817 and drove it with headless Chromium (Playwright) | 146/146 routes render an `h1` with **0 console or page errors**. Default route lands on the Lakeside decision home. The role toggle keeps the numbers. Budget switch: $5,000 gives spend 3,880 and claim-and-wait; $6,500 gives 6,430 and buy-now. The evidence drawer opens with breakdown, coverage and a provenance strip. The Operations view (v70 Portfolio) shows the banner and period note. The server was stopped afterwards (port free). |
| Rendered HTML of the main document | All 5 Mermaid diagrams render to SVG with no errors. They load Mermaid from the jsDelivr CDN at view time, so offline the page shows the diagram source. |
| Code-truth sample (about 35 citations) | All exist and say what is claimed. The sample covered: `recorded_amount.py:1`; `mini_decisions/alternatives.py:12-13`; `verification.py:1167` `InterventionCost(Fraction(0))`; `reserve_trial.py` `TRIAL_STEP=5` and the band; 0016:60/:72; `outcome_map.py` (10 records, all MOVES); `period_read.py:139-140` (D-MONEY.3); `strategies/base.py`; `outcomes/status.py:4-6,75-83`; `chain/read.py:190` `lead_finding`; `site_outcomes/read.py:901,926`; `verification_rules.py:688,708-735,787-800`; `dispatch_v3.py:290-293`; `verification_families.py:175` (`guardrails: {}`); `scenario_rules.py:194-200`; `actions/lifecycle.py:49-58`; `sites/models.py:167` stop-soc-threshold CONTROL; `host/execution_adapter.py:869` `run_to_end`; `runs/execution_ports.py`; the `tools/checks/dependency-direction.ps1` simulator rule; `estate/financials.py:361` `_overlaps`; overlap_group in 0011/0023/0026; 0042:50/:53; 0056 UNEXPLAINED_FUEL; 0061 file_sha256 only; `reading_upload/service.py:244-248`; `evidence/service.py:487-492`; `battery_boundary.py:26`; `warnings.py:45`; `placement.py:5`; `demo_combined_kobo.py:6-9`. Some line ranges are off by a few lines: the reserve band check is at `reserve_trial.py:258`, not 249-256. |
| Named tests in `[test-confirmed]` claims | All 18 named `file::test` pairs and 11 named files exist. I ran `pytest test_out_b1_status.py test_ch6_contributions.py test_out_a1_outcome_map.py -q`, which gave **69 passed in 0.74 s**. |
| Coverage of the required IDs in the traceability CSV | P4, A5, MG-L10, CC-L9, EV-L9, X9, S12, MG-C6, CC-C6 and EV-C6 are all present (6–34 rows each). Every brief lever, objective and capability ID is present **except X8** (L6). |
| Placeholder scan (TODO, TBD, placeholder, lorem) | None found. |

**Not verified:**
- The pack's own `tools/audit.mjs` run. I ran my own click-through instead.
- Screen-reader behaviour.
- Rendering of the main document's HTML offline (it needs the CDN).
- That the forward-replay figures (Kobo 210 L / 20 L, huller 68 L) are what the simulator kernel would produce. The pack itself says these are design values and were not run (`design-questions-and-decisions.md`, last table).
- Any build-cost figures (none were measured; see M4).

---

## Coverage against the commission

| Item | Present and substantive? |
|---|---|
| D1 mechanism, current→target, worked traces (MG, cold, EV, entitlement) with no-action, rejected options and verification | Yes. Main document §2, §3, §8, plus `repo-reuse-and-gap-matrix.md` as the appendix inventory. |
| D2 economic truth, phases, bridge with residual, entitlement money states, negative accounting tests | Yes. `economic-metric-and-effect-contracts.md` §2–§7. |
| D3 source→canonical recipes, four clocks, traces A–F, keys and idempotency, pilot adapters | Yes. `integration-source-to-canonical-design.md`. |
| D4 algorithms with equations, refusal, calibration, sensitivities | Yes. `domain-and-decision-models.md`. The calibration and B4-gap treatment (§2.5) is strong. |
| D5 lifecycle and state diagram, triage, ranking and allocation distinct, verification triple, claim states | Yes. |
| D6 new mock-up version, review pack items (1)–(9) | Yes: README, CHANGE-REGISTER, 45+1 screenshots, browser-audit, fixture-mapping, walkthroughs, owner checklist. Marked "not approved". |
| D7 manifest, three time scales, oracle, disorder tests, negative cases | Yes, **except measured costs** (M4). |
| D8 slices with gates, test-first, commercial validation without fabricated benchmarks, diagnostic offer | Yes. `phase-plan-and-acceptance.md` §8. |
| C3: 14 scenarios, each with entry, path, model, alternatives, outcomes, decision and test | Yes. `domain-and-decision-models.md` §10. Scenario 6 is weakened (M1). |
| C4: 9 companion artifacts and the quality gate | All present. Quality gate notes are below. |
| Honesty: simulated vs observed, no legal or insurance conclusions | Good. Every rights panel carries "This is not a legal decision. Coverage is decided by the supplier or insurer." Remedies never become money before a credit or receipt. Insurance below the deductible is not claimed. "Where the commission could not be completed" is candid. |

---

## Findings

### Medium

**M1. The EV "cheapest schedule" is not cheaper under the tariff the pack defines, so the C3 "cheaper schedule vs fleet constraint" scenario is hollow.**
- **Where:** `demo-site-scenario-manifest.yaml`, the Embakasi `tariff` and `EMB-CHEAPEST` entries; `domain-and-decision-models.md` §4.1 (lines ~522-547); main document §6 and §8.3; mock-up `#/choice-embakasi-schedule` ("Charging only 00:00–05:00 is cheapest but…").
- **Evidence:** The C-114 tariff has one off-peak price (0.12) outside 18:00–22:00, so 00:00–05:00 and 22:00–05:15 cost the same per kWh. The "cheapest" window runs at the 500 kW import limit, which means a 6,000 demand charge. The deadline schedule peaks at 400 kW (4,800). Even ignoring its shortfall, EMB-CHEAPEST costs 2,500×31×0.12 + 6,000 = 15,300, which is **more** than EMB-DEADLINE's 15,216. The pack sidesteps this with "rejected for service, whatever its price" and shows the option as "Not costed".
- **Why it matters:** C3 requires the cheapest schedule to be rejected *because* a vehicle cannot depart. Here there is no cost temptation to resist. An executive or a technical buyer who checks the tariff will see that the "cheapest" option is not cheap, and the negative control loses its persuasive point on a client screen.
- **Fix:**
  - Give C-114 a super-off-peak tier (for example 00:00–05:00 at 0.09), or another real reason the narrow window is cheaper.
  - Cost EMB-CHEAPEST, so it shows a lower energy bill than the deadline schedule and is still rejected by EV1.
  - Recompute the deadline figures, then extend `check_manifest.py` to assert that the cheapest option is cheaper.

**M2. The proposed `evidence_class` field collides with an existing code identifier that has a different vocabulary.**
- **Where:** Main document §3.3(b) and §5 "Note on vocabularies"; `economic-metric-and-effect-contracts.md` §6.2; `design-questions-and-decisions.md` A4.
- **Evidence:** The pack says thread occurrences carry a "**basis** (MEASURED…EXTERNAL; 0042:50)". In the code, that column is named **`evidence_class`**:
  - `backend/migrations/versions/0042_*:50` declares `evidence_class text NOT NULL CHECK (evidence_class IN ('MEASURED','RECORDED','DECLARED','MODELLED','EXTERNAL'))`.
  - The same name is used in `chain/ports.py:67,93`, `chain/builder.py:88`, `chain/outcomes.py:99` and `chain/threads.py:205`.
  - `Effect` already has a `basis` field (`recorded_amount.py`: `Effect(..., basis=RECORDED, ...)`).

  D4 proposes a *new* `Effect.evidence_class` with a different vocabulary (ECONOMIC_ACTUAL…VERIFIED).
- **Why it matters:** Two different axes would share one name across the chain layer that reads both. A4's "keep both as separate axes" is the right decision, but it misreports the existing name, so an implementer following the pack would create the collision.
- **Fix:** Correct the description of 0042:50 to say "`evidence_class`, used as a source basis". Give the new axis a distinct name, for example `economic_class` or `money_class`. The manifest already uses `money_class` for the Kisiwa SLA credit. Update A4, contracts §6.2 and the manifest's R2 wording.

**M3. The budget switch changes two assumptions at once, so a higher budget shows a lower result without the comparator, and the condition is worded inconsistently across documents.**
- **Where:**
  - Mock-up `#/plan-lakeside`: $5,000 shows "Modelled 12-month change +$6,096"; $6,500 shows "+$3,546".
  - Main document §2.2, the inverter row: "at ≥ 6,430: buy now wins because it secures the huller…", with no LOI condition.
  - `integration-source-to-canonical-design.md:299`: "CONDITIONAL on budget ≥ 6,430 **or** the cooperative not extending".
  - `domain-and-decision-models.md:880`: claims the manifest says "or". The manifest's MTO-INV-BUYNOW condition actually says "and".
- **Evidence:** `domain-and-decision-models.md` §7.3 sets out the correct logic:
  - With no LOI extension, the claim path loses the huller (2,556).
  - Buy-now keeps it (3,546).
  - Buy-now therefore wins by 990.

  The $5,000 screen silently assumes the LOI *is* extendable (huller kept, 6,096). The $6,500 screen assumes it is not, and does not show the 2,556 it beats. The executive sees "more budget → +$3,546 instead of +$6,096" without explanation.
- **Why it matters:** This switch is the pack's "the executive sees the switch move" moment (§7.3) and owner checklist item B6. As built, it invites the wrong conclusion that extra budget destroys value.
- **Fix:**
  - Make the LOI assumption its own control, or show both paths side by side under the same LOI assumption on the $6,500 view: "claim-and-wait would give +$2,556 because the huller is lost; buy-now gives +$3,546".
  - Align the wording to "and" in the main document §2.2 and in the integration document line 299.
  - Correct the domain document line 880 note.

**M4. The measured build cost required by D7 is absent. This is disclosed, but it is an acceptance gap.**
- **Where:** `demo-build-cost-plan.md` §4 and §6–§7; `design-questions-and-decisions.md` Q10 and "could not be completed".
- **Evidence:** The brief requires "measured CPU/wall/disk/rows/source volumes per stage, site and day". The pack reuses the historical walk1113 figures (labelled implementation-report), gives targets, and gives a re-benchmark plan. It states that no build or database was authorised.
- **Why it matters:** The per-hero build budgets are untested targets. The honesty is correct; the requirement is still unmet.
- **Fix:** The owner should decide Q10, either by authorising one re-benchmark run on an allowed `*_test` or audit database, or by accepting the gap for this phase. Until then, record D7 as "met except measurement".

### Low

- **L1. Internal vocabulary on client-facing decision screens.**
  - `#/decide-harvest` and `#/decide-metro`: "The demo fixture does not state which revenue and cost lines…".
  - `#/plan-lakeside`: the method string "must-do first, then exhaustive subsets under budget/crew/dependency/exclusion; tie-break 12-month net, then downside" (this is the manifest's `method` text rendered verbatim, `decisions.js` around line 531).
  - The same page: "The meter check 60 is funded from the routine O&M visit budget…", with no currency symbol and with an abbreviation.

  The pack's own audit regex does not catch these. Fix: rewrite them in plain language, for example "Recommended set: essential work first, then the best 12-month result that fits the budget and crew visits."
- **L2. Cost coverage exists only for Lakeside.** The cold and EV manifest periods have no `coverage:` key, so the CFO "recorded vs estimated" answer reads "not available yet" for two of three verticals (`decisions.js:405`). Fix: add coverage to the Harvest and Metro periods, including one ESTIMATED line each, to keep the three operators consistent.
- **L3. `[test-confirmed by checker]` stretches the label.**
  - `domain-and-decision-models.md` §4.1, §7.2 and elsewhere use it. The brief's label (b) means a product test.
  - `check_manifest.py` checks spend ≤ budget, not that the allocation subset is optimal, yet §7.2 calls the allocation result "test-confirmed by checker".
  - The checker also does not cover the option economics (STOPSOC, HULLER, MWEA-AGG, KIRI, EMB-DEADLINE, entitlement residuals). I verified these by hand and they reconcile.

  Fix: relabel as "[derived, arithmetic checked]" and add those identities to the checker.
- **L4. Stale cross-references.**
  - `domain-and-decision-models.md` §10 rows 9, 10, 12 and 13 say "no oracle (proposed OR-ENT-2 / OR-ENT-3 / OR-ALLOC-1 / OR-VER-1)", but the manifest's `oracle:` already contains all four.
  - The main document's pack table says "328 links", but the CSV has 329 data rows.
- **L5. Kasarani stopgap cost basis is ambiguous.** The manifest says "one bus charged overnight at Ruiru" (90 = overtime 70 + energy 20). The mock-up says "Charge one bus at Ruiru **each night** until the manufacturer repairs: $90". The restore date is 9 Nov and the as-of date is 6 Nov. If $90 is per night, the stopgap costs about $270, which is more than the $240 of penalties it is meant to avoid. Fix: state it as per night × nights and show the comparison, or keep it and add the service-obligation reason the stopgap wins anyway.
- **L6. Lever class X8 (Workforce/operational execution) is absent from the whole pack**, including the CSV. In the brief, X8 is in the shared lever hierarchy and the outcome×lever map, and S8 maps to "X2 X3 X4 X8". The design does cover crews, assignment and hand-off (D9, work-case ASSIGN). Fix: add X8 to the S8 and allocation rows so traceability is complete.
- **L7. Mock-up details.**
  - `#/choice-embakasi-schedule`: the do-nothing row renders an empty "Why not:".
  - `#/choice-mto-inverter`: the rights panel's "Cost to us under each path" shows "Do nothing $0", although that path forfeits the warranty after 27 Nov. Show "cover lost" beside it.
  - Owner checklist B9 says to "repeat 1, 3 and 6" for Harvest and Metro, but the budget switch (6) exists only for Lakeside.
- **L8. Forward-replay figures are stated as results in the narrative.** Main document §2.1 says "forward replay says 210 L … was avoidable", and the mock-up says "Replaying September and October … removes 210 L". These are design values that were never produced by the kernel. That is disclosed only at the end of `design-questions-and-decisions.md`. Add "(design value; to be reproduced by the slice 3 adapter)" at first use in the main document.
- **L9. The v72 characterisation is thin.** The main document §9 calls v71 and v72 "single-page design studies". v72 is the v7.2 design foundation (tokens, Inter, dark mode) with hi-fi Portfolio and Site Overview pages, which the current UI pass (UQ-FI) builds on. Q4 rightly puts the re-skin to the owner. The main document should name v72 as the current visual direction that vNEXT has not yet adopted.
- **L10. EV cost-per-departure mixes cost bases.** Kasarani's `total` includes 300 of maintenance; Embakasi and Ruiru are energy only (31.19 = 40,605.12/1,302). Either include maintenance everywhere or exclude it.
- **L11. The private oracle is shipped in the mock-up bundle.** `fixtures.js` embeds the manifest's `oracle:` block. It is not rendered, but R1 says the oracle is private. Strip it in `tools/gen_fixtures.py`.

---

## C4 quality gate

| Gate item | Result |
|---|---|
| No placeholder diagrams | Pass. 5 real Mermaid diagrams render, and they carry content. |
| No tables without a preceding design explanation | Pass in the main document and the companion artifacts I sampled. |
| No unexplained financial numbers | Pass. Every figure traces to the manifest or a stated derivation (`fixture-mapping.md`). |
| No module inventory posing as architecture | Pass. The inventory is in `repo-reuse-and-gap-matrix.md`, and the narrative leads. |
| "Not supported currently" not used to skip capabilities | Pass. Gaps become D1–D10 extensions with prerequisites. |
| No unsupported legal, insurance or recovery claims | Pass. Claim states are separate events, there is a no-legal-decision disclaimer, insurance is not claimed below the deductible, and no recovery is claimed on the unexplained kWh or fuel. |

## Residual risks the pack does not already name

1. **Forward-replay input mapping.** PV-available is converted to irradiance (`domain-and-decision-models.md` §2.5). This is acknowledged as exact only below the inverter AC limit. On clipped days at Kobo (60 kW PV, 50 kW AC), the replay may refuse many slots, which could undercut the ≥14-day sample rule. Check the replay calibration on the walk1113 data before relying on the 210 L figure.
2. **The `LabExecutionPort` return type would change.** The port today returns `LabProjection`. A "neutral projection" for replay is a contract change on a protected seam, and the phase plan should list it as such.
3. **Two demo estates side by side** (v70 Kobo/GreenHarvest/Depot vs Lakeside/Harvest/Metro). Owner checklist item A4 notes it, but in a live demo a prospect clicking "Operations view" lands in a different company's numbers. The banner helps, but the risk persists until the screens are re-based.

---

## Re-review (rev 2)

**Reviewer:** fresh Claude reviewer (not the author and not the first reviewer) · 16 Nov 2026
**Target:** the uncommitted working tree against `f1f6d9bf9` (`git diff f1f6d9bf9 -- Docs/demo-sprint/product-direction-layer4/`, 67 files), together with the author's mapping in `REVIEW-response.md`.
**Mode:** read-only. I edited nothing except this appendix. I did not touch the application code, any database, Docker or port 5490, did not run the full test suite and did not commit.

### Verdict: **ACCEPT WITH NOTES**

The author fixed all four Medium findings in substance and fixed L1–L11. M4 is correctly recorded as an owner decision (Q10, "met except measurement"). I found no High findings. One new Medium is a leftover of M2: the matrix row that tells an implementer to add `evidence_class` to `Effect` was not changed. It is a one-line fix and should be made before the pack is merged. The Low findings can go to the UI/UX pass or a later revision.

### Checks I ran and what they returned

| Check | Result |
|---|---|
| `python3 check_manifest.py` | `126 checks passed, 0 failed`, exit 0. I read the new checks. The EMB checks really assert cheapest < deadline and each component of both bills. The Lakeside allocation is checked by brute force over STOPSOC, CLAIM, BUYNOW and HULLER, with the rules "exactly one inverter path" and "huller requires buy-now or an extended letter of intent". |
| M1 recomputed by hand | **Cheapest schedule:** 2,500 kWh × 31 = 77,500 kWh. 77,500 × 0.09 = 6,975. Demand is 500 kW × 12 = 6,000. The bill is **12,975**. **Deadline schedule:** 800 kWh a night before midnight and 2,000 after. 24,800 × 0.12 = 2,976 and 62,000 × 0.09 = 5,580. Demand is 400 × 12 = 4,800. The bill is **13,356**. The deadline schedule's other figures: 2,900 kWh deliverable is 400 kW × 7.25 h; the 21-bus night needs 2,940 / 7.25 = 405.5 kW, which matches the "406 kW" note. **Saving:** 22,144.80 − 13,356 = 8,788.80 a month, and × 12 − 1,500 = **103,965.60**. **Optimality:** of the schedules that deliver the full 2,800 kWh, minimising cost over a flat P gives about 386 kW, so 400 kW is a near-optimal plan with margin. **Verdict:** the rejected schedule is genuinely the lowest bill, by 381 a month (but see N3). |
| L10 and L2 recomputed | **EV plan:** 19,540.80 + 5,880 + 13,100 = 38,520.80. **EV actual:** 22,744.80 + 5,880 + 13,080.32 = 41,705.12. The variance is −3,184.32, unchanged. 41,705.12 / 1,302 = 32.03. **Metro coverage:** (41,705.12 − 300) / 41,705.12 = 99.28%; the screen shows "99.3%". **Harvest costs:** 880 + 1,282 + 1,480 = 3,642. Coverage is (3,642 − 80) / 3,642 = 97.80%. |
| M3 four cases recomputed | **5,000 and Yes:** 2,916 − 360 + 3,540 = 6,096, at spend 3,880. **5,000 and No:** 2,916 − 360 = 2,556, at spend 2,680. **6,500 and Yes:** 6,096; buy-now gives 3,546, so claim-and-wait wins by 2,550. **6,500 and No:** 2,916 + 3,540 − 2,910 = 3,546, at spend 6,430; buy-now beats claim-and-wait by 990. The wording is "and" in the manifest, main document §2.2 and integration line 299. The connection lead time is now in the manifest (restore 28 Nov, 5 working days, lapse 30 Nov). |
| Stale-figure sweep | I searched for 15,216, 6,928.80, 81,645, 37,420, 40,605, 31.19, "328 links" and "or the cooperative". The only hit is `fixture-mapping.md:158` (N4). The CSV has 335 data rows, which matches the main document. X8 appears in 147 rows; T0327–T0332 link O2, P1 and A3 to S6 and S8. |
| M2 against the code | 0042:50 does declare `evidence_class` on `finding_thread_occurrence` with MEASURED, RECORDED, DECLARED, MODELLED and EXTERNAL, and `chain/threads.py:205` writes it. However, `chain/ports.py:67,93`, `chain/builder.py:88` and `chain/outcomes.py:99` (`AUTHORITY`) belong to a **second** column of the same name: the daily measure-snapshot table (`0043_chain_snapshots.py:37`, `chain/measures.py:37`, `adapters/postgres_snapshot_store.py`). It has the same vocabulary. The renaming decision stands, but the description is imprecise (N1). |
| Mock-up rebuild | I ran `node build.mjs` on a scratch copy. The resulting `index.html` is **byte-identical** to the committed one. I also ran `tools/gen_fixtures.py` on a scratch copy; the regenerated `fixtures.js` is **byte-identical** too, and its sha `7b5f74875705` matches the current manifest. |
| Oracle removed | `gen_fixtures.py` pops `oracle`. `index.html` and `fixtures.js` contain no "oracle" string and no `OR-*` ids. `findings_expected` and the `disorder_tests` `expect:` strings are still in the bundle; they are outside the `oracle:` block, so L11 is met as stated. |
| Served at http://127.0.0.1:8829 (`python3 -m http.server`) and driven with headless Chromium through Playwright | 146 of 146 routes render an `h1` with **0 page or console errors**. I scanned every non-Unchanged route with my own wider pattern (LOI, fixture, manifest, oracle, evidence/money class, option-id prefixes, enum names, `>=`, O&M, subset, exhaustive, tie-break). The only hit is the Preserved v70 `#/lab` ("immutable manifest"), which is not in revision scope. The **letter-of-intent control** works: all four budget × letter-of-intent clicks give the figures above, the alternative path is shown side by side, and the notes read "+$990" and "+$2,550". The "All four cases" table matches. `#/choice-embakasi-schedule` and its drawers show the tier, both bills and their workings. `#/choice-mto-inverter` shows "$0 now; cover lost after 27 Nov 2026". The Kasarani screens state 3 nights and $90 in total. `#/decide-harvest` and `#/decide-metro` show coverage. At 390 px, plan-lakeside (6,500 and No), choice-embakasi-schedule, decide-metro and econ-embakasi have no overflow. I stopped the server and confirmed the port is free. |
| L3, L4, L8, L9, residual risks | "test-confirmed by checker" no longer appears. The C3 rows cite OR-ENT-2, OR-ENT-3, OR-ALLOC-1 and OR-VER-1. The design-value tags appear on screen and at first use in §2.1. v72 is named the v7.2 foundation in §9. RR1–RR3 are recorded, and RR1 and RR2 are in slice 3. |

**Not verified:**
- `tools/run-audit.sh`. It hard-codes another session's scratchpad path (N9). I ran my own click-through instead, reusing the same Chromium binary read-only.
- Screen-reader behaviour.
- Offline rendering of the main HTML document.

### Status of the previous findings

| Finding | Status |
|---|---|
| M1 | **Resolved.** The tariff tier is real, both bills reconcile, and the checker asserts the ordering. N2 and N3 are about how the fix is explained. |
| M2 | **Mostly resolved.** The rename is applied in the manifest, the contracts, the main document, A11 and matrix row 241. Leftovers remain (N1). |
| M3 | **Resolved.** There is a separate control, both paths are shown, all four cases are enumerated and checked, and the wording is aligned. |
| M4 | **Correctly recorded as an owner decision** (Q10; status line in the cost plan). |
| L1–L11 | **Resolved.** L7 is fixed for Mto but not for the analogous Kasarani row (N6). |

### New findings

#### Medium

**N1. The M2 rename is incomplete. The implementer-facing matrix still instructs the collision M2 warned about.**
- **Where and evidence:**
  - `repo-reuse-and-gap-matrix.md:61` reads: "`Effect` … | D4: add `evidence_class` and `overlap_group` fields | extend". Row 241 of the same file says `money_class`, not `evidence_class`, so the file contradicts itself.
  - Prose leftovers:
    - `phase-plan-and-acceptance.md:63`: "Effect gains evidence class and overlap group".
    - `design-questions-and-decisions.md:28` (A4): "the new evidence class".
    - `integration-source-to-canonical-design.md:593`: "D4's effect evidence classes".
    - `economic-metric-and-effect-contracts.md:47`: the §3.1 column header "Evidence class", which holds money-class values.
  - Accuracy: the main document line 248 and A11 attribute `chain/ports.py`, `chain/builder.py` and `chain/outcomes.py` to the 0042 column. Those files read the snapshot column `0043_chain_snapshots.py:37` (`measures.py:37`), which has the same name and vocabulary.
- **Why it matters:** the matrix is the inventory an implementer follows, and row 61 is exactly the hazard M2 was raised to prevent.
- **Fix:**
  - Change row 61 to `money_class`.
  - Reword the four prose lines to "money class".
  - Cite both columns (0042:50 and 0043:37) in §5 and A11.

#### Low

- **N2. The "October unaffected" rationale is arithmetically impossible as worded.**
  - **Where:** manifest Embakasi `actual.note` ("charging on arrival finishes by about 23:10") and the mock-up at `decisions.js:162` ("none of October's energy used the cheaper 00:00–05:00 rate").
  - **Evidence:**
    - October off-peak is 39,060 / 31 = 1,260 kWh a night, all of it outside 18:00–22:00.
    - Under the 500 kW limit, at most 250 kWh fits in 17:30–18:00 and at most 583 kWh in 22:00–23:10. Even counting 05:00–05:30, the total is about 1,083 kWh, which is below 1,260.
    - With 55% of energy at peak, charging must run past midnight, so some energy falls in the new tier.
  - **Money effect:** small, at most a few hundred dollars a month at a 0.03 difference.
  - **Fix:** make the 00:00–05:00 tier effective from 1 Nov 2026 (a new contract term), which keeps October billed at 0.12, or re-split the October off-peak lines.
- **N3. The "cheapest" bill is lower only because it buys less energy.**
  - **Evidence:** EMB-CHEAPEST costs 12,975 for 77,500 kWh, which is 0.167 per kWh. EMB-DEADLINE costs 13,356 for 86,800 kWh, which is 0.154 per kWh. The deadline schedule is cheaper per kWh delivered.
  - **Assessment:** this is a legitimate C3 negative control, because a naive bill minimiser picks the cheapest schedule. However, a technical buyer may say the temptation comes from the shortfall itself.
  - **Fix:** add one clause in the walkthrough and models §4.1: "lowest bill because it buys 9,300 kWh less; per kWh delivered the deadline schedule is cheaper". This is a preference, not an acceptance gap.
- **N4. Stale figure.** `interactive-mockup-vNEXT/fixture-mapping.md:158` still reads "$6,928.80 a month"; it should be $8,788.80.
- **N5. Metro proof target is weaker than the model.** `decisions.js:577` says "Peak share falls from 55% toward the 30% plan". The modelled saving (8,788.80) assumes no peak-price energy (the 22:00–05:15 window). The operational target should be "peak share near 0%; about 62,000 kWh a month in 00:00–05:00". This is a pre-existing gap that M1's explicit bill makes visible.
- **N6. The L7 fix was not applied to the analogous Kasarani row.** `#/choice-kasarani-charger`, rights panel "Cost to us under each path", shows "Do nothing extra: wait for the manufacturer's repair: $0". The same screen gives that path −$240 in likely penalties. It should show "$0 now; about $240 in likely penalties", as was done for Mto.
- **N7. The crew meter on plan-lakeside does not follow the letter-of-intent case.**
  - **Where:** `decisions.js:542` sets `used = A.crew_visits_used`, so the meter always shows 3 of 3.
  - **Why it is wrong:** in the 5,000 and No case the huller (1 crew visit) is dropped, so the meter should show 2 of 3.
  - **Fix:** derive crew use from the chosen path, as spend already is.
- **N8. Pre-existing and outside revision scope; noted for the UI/UX pass.**
  - `#/econ-thika` shows the verdict "Low occupancy, not equipment" although occupancy is at plan (70% against 70%) (`decisions.js:487`). The verdict should be "Within the occupancy model".
  - `#/econ-embakasi` mixes sign conventions on one screen. The cost-line "Effect on result" column shows −$5,208, while "What moved the result" shows the same adverse drivers as "+$2,604" and "+$600" (`decisions.js:510` flips the sign for cost operators).
  - The Thika model string "kWh_month = 1550 + 0.25 x crate_days …" is shown on a client screen.
- **N9. The audit wrapper is not reproducible.** `interactive-mockup-vNEXT/tools/run-audit.sh` hard-codes `/tmp/claude-1001/.../fffff20f-…/scratchpad`. That is another session's scratchpad, which will be cleared. The audit's "all pass" claim therefore cannot be rerun by the owner. Fix: read `CHROME` and `PW` from the environment (`audit.mjs` already supports this) and document the setup in the README.

### Residual risk

- The revision regenerated 45 screenshots and replaced `plan-lakeside-6500` with four case shots. I spot-checked one freshly rendered case (6,500 and No) and it matches the DOM figures. I did not compare every committed PNG.
- The forward-replay figures (210 L, 20 L, 68 L) remain design values, now labelled as such on screen. RR1 still governs whether the slice 3 replay reproduces them.

## Re-review (rev 3)

**Reviewer:** fresh Claude reviewer (not the author and not an earlier reviewer) · 16 Nov 2026
**Target:** the uncommitted working tree against `d30ef6af4` (`git diff d30ef6af4 -- Docs/demo-sprint/product-direction-layer4/`, 32 files), together with "Author response (rev 3)" in `REVIEW-response.md`.
**Mode:** read-only. I edited nothing except this appendix. I did not touch the application code, any database, Docker or port 5490, did not run the full test suite and did not commit.

### Verdict: **ACCEPT WITH NOTES**

N1 (Medium) is resolved: the new axis is `money_class` everywhere it is specified, and the code citations are now correct in the main document, A11, the matrix and the manifest. N2–N6, N8 and N9 are resolved. The N7 dispute is sound on the figure: the crew meter correctly reads 3 of 3 in every case. However, the explanation added on screen conflicts with the manifest's connection lead time (R2). I found no High or Medium findings. The five Low findings below can go to the UI/UX pass or a later revision.

### Checks I ran and what they returned

| Check | Result |
|---|---|
| `python3 check_manifest.py` | `127 checks passed, 0 failed`, exit 0. The new N3 check compares deadline cost per kWh (13,356 / (24,800 + 62,000)) with cheapest cost per kWh (12,975 / 77,500). |
| N1: grep for `evidence[ _-]class` across the pack (md, yaml, csv, py, js, html, excluding REVIEW files) | Every remaining hit names the **existing** chain column(s) or says "not `evidence_class`". These are matrix :61, :117 and :241; main doc :163 and :248 (and the HTML); A4 :28 and A11 :34; integration :593; contracts :221; manifest :14. The others are the mock-up's audit and change-register entries for the M2 vocabulary scan. Nothing uses `evidence_class` as the new Effect axis. The contracts §3.1 header now reads "Money class", and phase plan :63 reads `money_class`. |
| N1: code citations against the repository | `0042_chain_threads.py:50` declares `evidence_class` with MEASURED/RECORDED/DECLARED/MODELLED/EXTERNAL. `0043_chain_snapshots.py:37` declares the same check. `chain/threads.py:205` writes `"evidence_class": EVIDENCE_CLASS` for the occurrence. `chain/measures.py:37` is `MeasureSpec.evidence_class`. `chain/ports.py:67,93` are `SnapshotRow.evidence_class` and its JSON, `chain/builder.py:88` passes `spec.evidence_class` into the snapshot, and `chain/outcomes.py:99` filters snapshot rows by `AUTHORITY` (:31). **All of these are cited correctly** in main doc :248, A11 and matrix :241, with one leftover in the contracts (R3). |
| Numbers recomputed by hand | **October (N2):** 47,740 × 0.24 = 11,457.60, 39,060 × 0.12 = 4,687.20 and demand 6,000 give 22,144.80. **Plan:** 26,040 × 0.24 = 6,249.60, 60,760 × 0.12 = 7,291.20 and demand 5,400 give 18,940.80. With the 00:00–05:00 tier starting on 1 Nov, the October bill is internally consistent. **Per kWh (N3):** 12,975 / 77,500 = 0.1674 and 13,356 / 86,800 = 0.1539. **Embakasi bridge (N8):** 47,740 − 26,040 = 21,700 kWh × (0.24 − 0.12) = 2,604, and (500 − 450) × 12 = 600. 19,540.80 − 22,744.80 = −3,204 = −2,604 − 600. On screen, the cost lines are peak −5,208 and off-peak +2,604 (both "negative = worse"), and they net to the same −2,604. **Kasarani (N6):** the manifest has `KAS-OEM-WAIT.expected_penalties: 240.00` and 2 missed departures, which match the screen. **N5:** `kwh_0000_0500: 62000` matches the verify target. |
| Rebuild on a scratch copy | I copied the manifest and the mock-up folder to my scratchpad. Running `tools/gen_fixtures.py` there gave `fixtures.js` byte-identical to the deliverable (sha `4d660dfee47c`). `node build.mjs` there gave `index.html` byte-identical (`cmp` silent). `index.html` contains no "oracle" string and no `OR-*` id. |
| N9: `tools/run-audit.sh` on the scratch copy, with `CHROME`, `PW`, `AUDIT_LD_LIBRARY_PATH` and `FONTCONFIG_FILE` from the environment (no `--shots`) | It runs as documented: `routes 146, routesOk 146, badLinkRoutes 0, overflowAdded 0, overflowOther 0, vocabHits 0`. |
| Served statically with `python3 -m http.server` on 127.0.0.1:8837 and driven with headless Chromium (Playwright) | **0 page or console errors.** **`#/econ-embakasi`:** drivers −$2,604 and −$600, total −$3,204. **`#/choice-embakasi-schedule`:** "What happened" carries the 1 Nov contract-term sentence; bills are $12,975 and $13,356, and the saving is $8,788.80 / $103,965.60. **`#/choice-kasarani-charger`:** the rights panel reads "$0 now; about $240 in likely penalties and 2 broken departures". **`#/econ-thika`:** "Within the occupancy model … which is the planned occupancy", with the formula replaced by plain words. **`#/verify-metro`:** "Almost no charging at peak price … about 62,000 kWh a month at the 00:00–05:00 rate …". **`#/plan-lakeside`, all four budget × letter-of-intent cases:** spend is 3,880 / 2,680 / 3,880 / 6,430 and the crew meter reads 3 of 3 in all of them. The explanatory note appears only in the 5,000 and No case. At 390 px there is no overflow. A vocabulary scan of those screens (OR-ids, oracle, evidence class, `money_class`, option-id prefixes, fixture, manifest, `kWh_month`, `crate_days`, LOI, `>=`) found nothing. I stopped the server and confirmed port 8837 is free. I did not touch 5490. |

**Not verified:**
- I did not compare all regenerated screenshots against the DOM. I viewed my own renders of plan-lakeside (5,000 and No) and econ-thika.
- Screen-reader behaviour.

### Status of the rev 2 findings

| Finding | Status |
|---|---|
| N1 | **Resolved.** One stale citation remains in the contracts (R3, Low). |
| N2 | **Resolved as worded.** The October bill is now consistent. It has a forward consequence for the do-nothing baseline (R1). |
| N3 | **Resolved** in the models (§4.1), contracts E7, main document, manifest note and walkthrough. The checker asserts it. The screen still says "cheapest bill of all" without the reason; N3 was a preference, and the narration carries it. |
| N4 | **Resolved.** `fixture-mapping.md:158` reads $8,788.80. |
| N5 | **Resolved**, on screen and in the fixture mapping. |
| N6 | **Resolved.** |
| N7 | **Dispute accepted on the figure.** In the manifest, `MTO-INV-CLAIM` and `MTO-INV-BUYNOW` each carry `crew_visits: 1`, so Kisiwa repair + Mto inverter + Kobo evidence = 3 with or without the huller, and the original N7 ("should show 2 of 3") was wrong. The added explanation has its own problem (R2). |
| N8 | **Resolved.** Thika's verdict, the single sign convention and the plain-words model are all confirmed in the browser. |
| N9 | **Resolved.** The wrapper ran here from environment variables only. |

### New findings

#### Low

**R1. The forward do-nothing baseline uses October's tariff while the options use November's.**
- **Where:** the manifest Embakasi `EMB-NOACT.economics.energy_cost_monthly: 22144.80` and `EMB-DEADLINE.saving_monthly: 8788.80` (= October actual − deadline). `check_manifest.py:129` asserts that equality. On `#/choice-embakasi-schedule`, "Keep the current charging pattern … continues at $22,144.80 a month".
- **Evidence:**
  - Since N2, the 0.09 tier starts on 1 Nov. Every option is priced on the November tariff, but "do nothing" keeps October's 0.12 price for all 39,060 off-peak kWh.
  - Under the new tariff, the do-nothing bill falls by 0.03 × (do-nothing kWh charged after midnight).
  - The pack does not state that share. Charging at the 500 kW limit from 22:00, plus 17:30–18:00, fits about 1,250 of the 1,260 kWh a night before midnight. The share therefore lies anywhere from near 0 to all 39,060 kWh: an overstatement of about $0 to $1,172 a month (0–13% of $8,788.80; up to about $14k of the $103,965.60).
- **Why it matters:** this is the headline saving on the Metro story. A technical buyer will ask for the do-nothing baseline priced on the tariff the saving accrues under.
- **Fix (either):** (a) state the assumption in the manifest note and models §4.1, e.g. "do-nothing charging finishes before midnight, so the new tier does not change the baseline"; or (b) reprice `EMB-NOACT` on the November tariff with a stated after-midnight share, and recompute the saving and the checker equality.

**R2. The N7 on-screen explanation conflicts with the manifest's connection lead time.**
- **Where:**
  - The note shown in the 5,000 and No case: `decisions.js:557`, "The huller connection would only have shared that visit".
  - The crew panel's "Same visit as the inverter" for `MTO-HULLER`: `decisions.js:421`.
  - Manifest :288: "Mto (inverter + huller + audit combined)".
- **Evidence:**
  - `MTO-HULLER.connection_lead` (manifest :232) says the connection takes "5 working days after the inverter is restored (service drop, meter, supply contract signature)". The huller work therefore cannot happen on the inverter-fit visit.
  - In 5,000 and Yes, the claim path restores on 28 Nov, so the connection falls in December, outside the November crew constraint.
  - In 6,500 and No, buy-now restores on 12 Nov, so the connection falls around 19 Nov: a second November Mto trip unless the connection is not crew work.
  - `MTO-HULLER.crew_visits: 1` (:233) also contradicts the "combined" comment, whereas `MTO-METER-AUDIT` correctly carries `0  # combined with the inverter visit`.
  - `check_manifest.py` asserts nothing about crew visits, so the brute-force allocation does not test this.
- **Why it matters:** the meter figure is right, but its stated reason is not, and the 6,500 and No case may in fact need 4 November visits against 3.
- **Fix:**
  - Decide who does the service drop and meter. If it is the cooperative or a connection contractor, say so, set `MTO-HULLER.crew_visits: 0` and reword the note to "the huller connection is not crew work".
  - Otherwise count it as a visit in the month it falls, and add a crew assertion to the checker for all four cases.

**R3. One stale citation is left from N1.** `economic-metric-and-effect-contracts.md:221` still reads "that name already exists in the chain layer (0042:50, `chain/ports.py:67`)". `ports.py:67` is `SnapshotRow.evidence_class`, which is the 0043 column, not 0042. This is the same mis-pairing N1 asked to remove. Fix: cite "0042:50 and 0043:37", as the other files now do.

**R4. A raw tariff string reaches a client screen.** `#/econ-embakasi` renders the manifest tariff verbatim: "super-off-peak 00:00-05:00 at 0.09, effective from 2026-11-01 (new contract term; October billed at 0.12 in all non-peak hours)". It has an ISO date and hyphenated time ranges, unlike the rest of the screen, which uses "1 Nov" and "00:00–05:00". This is cosmetic and goes to the UI/UX pass.

**R5. The README revision line is stale.** `interactive-mockup-vNEXT/README.md:42` still says "Revision: rev 2 … see CHANGE-REGISTER §7". Rev 3 is §8.

### Residual risk

- Screenshots were again regenerated wholesale and spot-checked rather than compared in full. The audit counts above come from my scratch-copy run, not from the committed `audit-results.json`.
- RR1 still governs whether the slice 3 replay reproduces the design values.
- R1 means the Metro headline saving carries an unstated tariff-baseline assumption until (a) or (b) is applied.
