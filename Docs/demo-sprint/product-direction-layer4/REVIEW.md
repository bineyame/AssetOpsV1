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

## Review (rev 4 redesign)

**Reviewer:** fresh, independent Claude reviewer · 17 Nov 2026 · working tree on `task/product-direction-layer4-design` (rev 4 uncommitted over `f5d2b9a4f`). Read first, myself: the owner's brief v1.1 (in full) and the owner's verbatim feedback of 17 Nov with the six confirmed points. Nothing in the pack, the application code or any database was changed; only this section was appended.

### Verdict: REVISE (targeted)

The redesign is a real change of foundation, not a re-skin of rev 3. The five mechanics (Define, Observe, Evaluate, Choose, Prove) are built from structure the brief actually defines, the citations are real and read faithfully, and integrations, algorithms, the UI strategy, the reuse judgement and the delivery order are each derived from the mechanics rather than listed beside them. The mock-up restructures the existing Portfolio inside its six tabs with no role switch, filter or menu, and it works for all three operators. One foundation gap stops me from accepting: **the Define mechanic is instantiated only for the money outcome**. Protect is treated as a set of bounds and status words, not as an outcome built from factors with units, periods and composition, which is what the brief's L1.1 and the owner's point 1 require. That is fixable inside the current frame. The Medium findings below are local.

### Answers to the four questions

1. **Foundation: largely yes, with one gap.** M1/M2 come straight from the brief: the L1.1 "what counts, units and time" column, the unit hierarchy (L1.1, lines 121-130), "shared driver IDs and period IDs" (line 130, quoted correctly), the L1.2 decision invariants (line 149), R1-R3 economic anatomy, the C1 D2 phase chain (line 426), the S2 "independently identified drivers" bridge (line 291) and the L2.5 roles and "many-to-many and causal" warning (line 251). I checked each citation in §1 and §2.7 against the brief and found none misquoted. Outcome state is computed bottom-up and attention arises at the factor (off plan, at a bound, a new latent factor), so the owner's "observed by the underlying factors" correction is followed for **contribution and cost-per-departure**. It is not followed for **Protect** (H1). In one place (M1 below) the Observe step also takes in a counterfactual from one lever.
2. **Generality: mostly yes.** The structure, the node kinds, the valuation identity, the bounds, the allocator and the three verdicts are stated once and filled in per vertical (§3.1a). The captive EV case changes the outcome's form (cost per required departure met, revenue NOT_APPLICABLE) without changing the mechanics, and the mock-up's Overview, Opportunity and Outcomes-by-site adapt to each operator. Kobo appears as an example, not as the source of the logic. Two places still lean on one path: the mini-grid fuel sub-structure has a node defined by one lever's replay (M1), and the delivery plan promises cold or EV fixtures in the general slices but drops them from the slice 4 tests (M3).
3. **Derivation: yes.**
   - **Integrations** are scoped as "one family of source facts per leaf factor" (§4).
   - **Algorithms** are tabled by mechanic, each marked new, modified or kept, with a code basis (§5).
   - **UI strategy:** "the loop is the information architecture" (§6.1).
   - **Reuse:** each part is kept, reworked, replaced or created by the mechanic it serves, with a reason, and the current code does not shape the design (§8).
   - **Delivery** follows the loop's dependency order, with general primitives first (§9, phase plan §1).
   - Nothing reads as bolted on. The weakest derivation is the plan-value figure (M2), which does not follow the M3 identity.
4. **Mock-up: yes.** The left rail is identical to v7.0, including Simulator Lab. The six tabs keep their owner-approved names. v7.0's Act-first lens chips are retired from the Portfolio and kept in the Findings root. There is no role switch: the words CEO, COO, CFO and CCO appear 0 times on the Overview. The demo-operator selector is in the review bar only. Each question lands on a section:
   - CFO: Outcomes by site, with the structure, the waterfall and the residual.
   - CEO and COO: Act first, as a plan under budget and crews with switches.
   - CCO: Opportunity, with qualified demand, rejected demand at break-even, and capacity without a customer.
   - Proof: What changed, with the three verdicts and the rights tracker.

   The change register matches the v7.0 inventory (110 screens in `frontend/mockups/v70/screen-manifest.json`) and the observed behaviour, with one wrong row reason (L1).

### Findings

**H1 · Foundation: the Protect outcome is not a declared factor structure. It is read as bounds and status words.**
- **Where:** main §2.1 l.106 and l.111 ("Protect reads the obligation bounds, asset factors and rights"); §3.1 l.232. Contracts §2.2-§2.4 (l.49-113) declare structures only for contribution and cost per departure; the obligations sit under them as bounds (l.78, l.97, l.113). Mock-up Overview Protect card: "1 obligation at its limit · 1 right with a deadline". Outcomes-by-site Protect column: "Battery charge at 5 am: within its limit", "Generators available for evening supply: at its limit", "Inverters in service: outside its limit".
- **Evidence:** brief L1.1 (l.114) defines Protect with measured quantities and units: "Unserved critical energy; eligible temperature excursions; failed fleet departures; material outages; physical assets at risk, verified damage, expected loss only with defensible likelihood, required capital". The owner's point 1 asks that each outcome be built from factors "with clear units, periods and scope". Identity M1 says "every outcome node equals the declared function of its factors". Protect has no outcome node, no plan, no Σ/Σ composition and no attribution. Its state is a count of bounds at their limits, which is the "counts of different kinds" pattern that §6.2 criticises in v7.0. Only EV's departures-met node is a real Protect quantity. Mini-grid unserved critical kWh and cold eligible excursion batch-minutes appear only as bound checks (models l.410), never as observed outcome quantities with a plan. Assure is defensible as a state over evidence (brief: Assure is asymmetric). Protect is not.
- **Why it matters:** one of the four categories does not follow the mechanics the design says govern every outcome, so the foundation is incomplete exactly where the owner pointed. The COO's "factors at bounds" answer then has no period measure behind it, and a portfolio Protect figure cannot be composed or drilled the way the Grow and Optimize figures can.
- **Fix:** declare a Protect structure per vertical in contracts §2 and the main §3.1a. Possible measures: unserved critical kWh by interval → site → portfolio; eligible excursion batch-minutes and QA-confirmed damage; required versus missed departures; asset value at risk with its likelihood basis; covered value at stake. Each needs units, a period, a plan or target, coverage and composition. Bounds then become the per-option limits derived from those measures. Update the Overview Protect card and the Outcomes-by-site column to show the measures against plan, with the bound state beside them.

**M1 · Generality/foundation: the mini-grid fuel sub-structure puts one lever's counterfactual inside the observed structure.**
- **Where:** contracts l.75 ("forward replay splits candidate into avoidable vs constrained"), l.153, l.173-175; main l.83, l.414; models §1.1 l.21 ("Kobo's candidate-avoidable litres (210 L in October against 0 planned)"); mock Scope tab "Generator running beyond need, not avoidable in the replay".
- **Evidence:** the 210 L "feasibly avoidable" leaf is the output of the replay of one option (stop threshold 90% → 70%, models §4.2). The reserve option avoids 20 L and another setting would avoid a different amount. So a node of the M2 structure depends on which M3 lever was replayed. Dispatch-3.2 observes only necessary versus candidate. That contradicts M2's "nothing is inferred backwards" and the separation of observation from evaluation. It is the one place where a vertical- and lever-specific path shapes the general structure.
- **Fix:** keep the observed split at necessary + candidate + unexplained. Move "feasibly avoidable under option X" into that option's `option_effect` (M3) and show it on the decision page. The Overview can still say "of 330 L candidate, the best feasible option avoids 210 L (Modelled)".

**M2 · Derivation: the plan's "modelled 12-month change" does not apply the M3 identity to the whole plan.**
- **Where:** main l.430 (+6,096.00 = 2,916.00 + 3,540.00 − 360.00, with spend 3,880.00); identity M4 l.169; identity M3 l.147 ("− one-off cost borne by the operator"); models §6.1 l.495-502; mock Overview figure "Modelled 12-month change of the plan +$6,096" beside "Plan spend $3,880".
- **Evidence:** the Kisiwa repair (1,800) and the Kobo battery evidence (430) are in the spend but are neither valued nor netted ("No saving claimed"). The Mto inverter cost (360) is netted. The headline therefore nets 360 of 3,880 spend, and the reader cannot tell which costs are inside the figure.
- **Why it matters:** this is a CFO-facing headline. The brief excludes "uncosted heroic options", and the design's own identity nets one-off costs.
- **Fix:** either value the must-do and protective options against no action (for example the evening-supply consequence at Kisiwa) and net all spend, or relabel the figure "modelled change from the valued options (+6,096.00); must-do and protective spend of 2,230.00 not valued" and put the same words on screen.

**M3 · Generality of delivery: the promised cold/EV fixtures are missing from the general slices' tests.**
- **Where:** main §9 l.547 ("with a cold or EV fixture case in its acceptance tests so the primitive is not shaped by one path"); phase plan slice 4 tests l.128 and slice 5 tests l.138.
- **Evidence:** slice 3 does carry a captive-EV fixture (N13). Slice 4 builds the general option evaluator, the obligation bounds and the decision records, but its tests are all mini-grid (OR-MG-1..3, E6, E8, N9, N11, N15), and its bounds gate is "byte-equal for today's reserve plan". Slice 5's allocator is tested on synthetic fixtures and Lakeside only. The cold and EV options (Kirinyaga repair or replace, Embakasi schedule against a hard departures bound) first meet the evaluator and bounds in slice 8.
- **Fix:** add one cold and one EV fixture to the slice 4 tests, for example a Kirinyaga repair-versus-replace valuation and Embakasi's cheapest schedule rejected by the departures bound. Add one non-mini-grid allocation case to slice 5.

**L1 · Change register row reason wrong for `#/renewable`.**
- **Where:** `interactive-mockup-vNEXT/CHANGE-REGISTER.md` l.60, and the matching `layer4_note` in `screen-manifest-vnext.json`.
- **Evidence:** the row reason is the Ruiru text ("earlier demo (2 connectors, 80 kW)…"). In the browser, `#/renewable` shows the Kobo headroom banner ("Spare daytime solar without a paying customer is capacity…"), which the register's own shell table (l.34) describes correctly.
- **Fix:** correct the note in the generator.

**L2 · Internal record identifiers in prose on new client screens.**
- **Where:** `loop-portfolio.js` (F-109, ACT-051), `loop-decisions.js` (GEN-CR-01, ACT-051, F-130, WR-019, INV-MT-02), `loop-core.js` (B-1031, F-130); visible in What changed (Harvest) and on the Opportunity and Thika decision pages.
- **Evidence:** the audit's vocabulary regex (`tools/audit.mjs`) treats CH-K2, CH-R7, GEN-KS and INV-MT as hits, but not ACT-/F-/WR-/GEN-CR-/B-10xx. So the "0 vocabulary hits" claim rests on a narrower rule than the pack applies elsewhere. Asset tags and batch ids may be acceptable as the client's own identifiers. Product action and finding ids in running prose are less clearly so.
- **Fix:** make one consistent rule. Either link these as navigable references or replace them with plain words, and widen the regex to match.

**L3 · Small internal inconsistencies.**
- The `CONTRIBUTIONS` lines are cited as `outcome_map.py:150-180` (main, phase plan) and as `:145-161` (models §2.1). The actual tuple spans l.150-174.
- Node kinds are five in contracts §1 and §2.1, but seven plus TIERED in the models §2.2 pseudocode.
- The UI strategy (§6.1.4) names six evidence words. The screens also use "Measured", "Calculated from records" and "Quoted", which should be added to the list.
- The Overview labels the residual "not explained yet (unobserved leaves)", yet Kobo's 120 L comes from observed dips and deliveries set against the model. "Not explained by the model" would be accurate.

### Checks run and what they returned

- `python3 check_manifest.py` → **167 checks passed, 0 failed**.
- **Spot reconciliation by hand, all consistent across the main document, contracts, models, manifest and mock-up:**
  - Lakeside −852.00 = −97.00 + −755.00, with the per-site attribution rows summing.
  - Lakeside spend 3,880 = 1,800 + 90 + 360 + 1,200 + 430 (the meter check is from the routine maintenance budget).
  - The four switch cases (3,880/6,096; 2,680/2,556; 3,880/6,096; 6,430/3,546), re-clicked in the browser.
  - Harvest 946/1,716/−770 and 720 = 350 + 100 + 270.
  - Kirinyaga 1,512.40 = 155.20 × 12 − 350.
  - Mwea 1,670 = 485 × 4 − 270.
  - Metro 41,705.12 = 22,744.80 + 5,880 + 13,080.32; plan 38,520.80.
  - Departures 1,302 (620 + 248 + 434), giving 32.03 and 29.59 per departure.
  - Embakasi 95,484 = 8,082 × 12 − 1,500.
  - Huller 395 × 12 − 1,200 = 3,540 at the 0.30 productive tariff.
- **Code-observed claims sampled, all accurate:**
  - `recorded_amount.py:1`
  - `outcome_map.py` CONTRIBUTIONS (10 rows, all MOVES)
  - `reserve_trial.py:37` (TRIAL_STEP 5)
  - `verification.py:1167` (InterventionCost 0)
  - `placement.py:1-7`
  - `battery_boundary.py:26` (WARRANTY_EXPOSURE withheld)
  - `period_read.py:138-139`
  - `financials.py:361` `_overlaps`
  - `dispatch_v3.py:290-293`
  - `verification_rules.py:688` and `:718`
  - `verification_families.py:175` (`"guardrails": {}`)
  - `chain/read.py:190` `lead_finding`
  - `alternatives.py:9-14`
  - `scenario_rules.py:193-200`
  - `sites/models.py:167` and `:513`
  - `portfolioWords.ts:30-35`
  - `host/execution_adapter.py:869`
  - `reading_upload/service.py:244-248`
- **Mock-up served statically** on 127.0.0.1:18731 (not 5490 or 8990) and driven with headless Chromium. Chromium came from playwright-core, with missing system libraries and fonts extracted into the session scratchpad. I visited:
  - all six Portfolio tabs for each of the three operators;
  - the Kobo and Thika decision pages and the Kasarani site;
  - the evidence drawer on Kobo litres (definition, factor split, source rows including the 9-day-late delivery note, clocks, provenance with "Demo data only");
  - the Act-first switches;
  - `#/renewable`;
  - v7.0 `#/portfolio`, for comparison.

  Zero page errors across all visited routes. The server was stopped afterwards. I did not rerun the pack's full 202-route audit.
- **Simulated versus observed:** kept distinct on every screen I opened (Modelled, Recorded, At stake and Not available yet, in words; "not realised"; restored charges, potential credit and cover at stake are "listed beside, not added"). The drawer states the demo provenance.
- **Honesty of stated gaps:** fair. `design-questions-and-decisions.md` names the unmeasured build cost (Q12), the replay design values (RR1), the cross-tenant global roots (RR2), the unbuilt deep tabs (RR3) and the deliberate omission of C1 D6 "filters / role emphasis" (A14). The one departure from the brief's "smallest coherent extension" (C0) is stated openly in the main document (l.15).

### Not verified

- The forward-replay design values (210 L, 20 L, 68 L; 4 of 61 and 0 of 61 dawn days). They are labelled as design values, and no kernel run was made.
- Screenshots in `screenshots/` and the full audit counts in `browser-audit.md`, beyond the routes I visited.
- Accessibility claims (contrast, focus trap) beyond the drawer opening and closing.
- Rendered mermaid in the HTML. The HTML text matches the markdown for the figures I sampled.

### Residual risk not already named in the pack

- If H1 is fixed by adding Protect measures, the Overview and Outcomes-by-site layouts will need a fourth composed figure. The mock-up's density at 390 px should be rechecked then.
- Merging the v7.0 estates into Thika and Ruiru leaves Ruiru's preserved deep views at a different scale (2 connectors, 80 kW), bannered rather than re-based. A prospect who clicks deep can still meet two scales for one depot. The pack lists this as an owner choice. It remains a demo risk until it is decided.

## Re-review (rev 5)

**Reviewer:** a fresh, independent Claude reviewer, 17 Nov 2026. I reviewed the rev 5 working tree on `task/product-direction-layer4-design`, uncommitted over `291c025dc`, against "## Review (rev 4 redesign)" above, the author response (rev 5), the owner's brief and the owner's verbatim feedback (messages 1–8). I changed nothing in the pack, the application code or any database. My only edit is this appended section.

### Verdict: **ACCEPT WITH NOTES**

H1, M1, M2 and M3 are resolved in substance. Owner messages 7 and 8 are applied on every added and changed screen I scanned. The foundation, generality and derivation are intact. What remains are Low findings: five wording or consistency gaps (one of them a partial leftover of M2 in a drawer) and one commit-hygiene item. None blocks acceptance. L6 must be handled when the round is committed.

### Resolution of the rev 4 findings

- **H1: resolved. Protect is now a real structure, not a relabelling.**
  - **Declared per vertical.** Contracts §2.6 declares each Protect measure with a unit, an objective (P1–P4), a target, an evidence class, a leaf source and a composition. Models §3.11 gives each one an observer with a formula, error modes, a negative control (Ruiru: 26 charger-days out of service, 0 missed departures) and vectors PR-T1..T4.
  - **Attributed to cause.** Attribution follows rule A1: "30 h" opens onto Kisiwa generator 1 (10 h) and Mto inverter 2 (20 h).
  - **Money measures counted once.** Liability and penalties reference the cost-to-serve factor ID instead of holding their own amount (contracts §6.6 invariant, N18).
  - **At-stake values listed, not summed.**
  - **Bounds derived from the measures.** Models §4.7 now names, for every bound, the Protect measure it limits. E12 makes a bound without a measure fail at start-up. An option fails a bound when its counterfactual pushes a measure above target. This is the derivation H1 asked for.
  - **Follows the brief.** The measures map onto the brief's L1.1 Protect column: unserved critical energy; eligible temperature excursions (batches exposed, crate-minutes above limit); failed fleet departures; asset-days out of service; verified damage (QA-confirmed liability). Two items in that column are not covered (L5).
- **M1: resolved.**
  - **Observed split.** Kobo's litres are necessary running, plus candidate running (330 L, −412.50), plus litres not explained by the model (120 L, −150.00). The manifest bridge sums to −562.00 (38 − 412.50 − 37.50 − 150).
  - **Option effects kept off the observed structure.** The 210 L and 20 L appear only as option effects: on the decision page, and in the Overview phrased the way rev 4 allowed ("of it, the best feasible option avoids 210 L a month (Modelled)").
  - **No old wording left in data.** A grep for the old avoidable/constrained nodes finds them only as dead label-map keys in `loop-core.js` (L6), never in the data. In the browser, "avoid" does not appear on Outcomes by site, Scope, Kobo site or Kobo economics.
- **M2: resolved on the headline, with one leftover in a drawer (L1).**
  - **Lakeside.** +6,096.00 = 2,916 + 3,540 − 360, net of 1,650.00 (90 + 360 + 1,200). 3,880.00 − 1,650.00 = 2,230.00 (1,800 + 430).
  - **Switch cases.** All four satisfy valued costs = spend − 2,230.00: 450.00 → +2,556.00, and 4,200.00 → +3,546.00.
  - **Harvest.** +3,182.40 = 1,512.40 + 1,670.00, net of 620.00. 720.00 − 620.00 = 100.00. With the aggregator switch off: 450.00 = 350.00 + 100.00.
  - **Metro.** +95,484.00, net of 1,500.00. 1,590.00 − 1,500.00 = 90.00. The 60,000.00 avoided purchase is listed beside, not added.
  - **Consistent everywhere.** The manifest, main §-plan, models §6.2–6.4, phase plan slice 6 and the on-screen hero and Act-first notes all agree, and the checker asserts each split.
  - **Honesty.** Not valuing must-do spend in money, because doing so needs a value-of-lost-load assumption (A16), is honest. The spend is stated with its Protect effect.
- **M3: resolved.**
  - **Slice 4** now tests the general evaluator on cold and EV inputs:
    - KIRI-REPAIR +1,512.40 against KIRI-REPLACE −1,988.40. I recomputed 234.30 × 12 − 4,800 = −1,988.40.
    - EMB-CHEAPEST at 12,975.00 is rejected by the departures bound.
    - EMB-DEADLINE is valued at 8,082.00 a month against November no-action of 21,438.00.

    Its gate forbids vertical-specific code in the evaluator.
  - **Slice 5** adds the Harvest allocation with the aggregator switch: 720.00 and 2 of 2 visits, or 450.00 and 1 of 2.
- **L1 and L2: resolved.** The register now gives the Kobo headroom reason for `#/renewable`. My scan found no product record ids on added or changed screens. Asset tags appear as "plain name (TAG)".
- **L3: resolved, and the author's dispute is upheld.** In `backend/assetops_backend/outcomes/outcome_map.py`:
  - the `CONTRIBUTIONS` tuple opens at l.150 (the comment is at l.149) and closes at l.180;
  - EV-3 charging income is at l.173–176 and the idle-charger potential at l.178–179.

  My earlier proposal of 150–174 would have cut off the last two records. 149–180, or 150–180 as one citation still reads, is correct. The node kinds are now one list (seven computed kinds plus leaf), and §6.1.4 lists nine evidence words. The residual relabel introduced one mislabel (L3 below).

### Owner messages 7 and 8

I served the mock-up statically on 127.0.0.1:18743 (not 5490 or 8990) and drove it with headless Chromium (playwright-core 1155).

- **Coverage.** I visited 264 route renders: every Added or Changed screen for Lakeside, plus every Portfolio, Sites, Site, Decision and Financials route for Harvest and Metro.
  - On each one I collected h1–h5, legends, figcaptions, eyebrows, summaries, aria-labels and tab names.
  - I opened the review-notes drawer and up to three evidence drawers per route.
  - My checks were broader than the pack's audit: any role name (CEO, COO, CFO, CCO, executive, chief …), any heading ending in "?", any heading starting with an interrogative word, and the words "question" or "answer".
- **Result.**
  - **Roles and questions.** No role name and no executive question appear on any added or changed screen, tab or evidence drawer.
  - **Headings.** They name business content, for example:
    - "Each outcome and the factors that make it"
    - "Protect: measures by site against their target"
    - "The plan for November and December"
    - "More service from the same chargers"
    - "Commitments: frozen prediction and three verdicts"
  - **Interrogative hits.** All were descriptive ("What changed", the owner-approved tab name; "How each option changes the factor structure"; "What would change the recommendation") or v7.0 "Why?" explanation buttons on the Changed estate pages (mini, cold, ev), which are bannered v7.0 content. One v7.0 finding heading on `opportunity-finding` reads "Does recurring renewable headroom support useful additional demand?". It is v7.0 text on a screen changed only by a banner. It is not an executive question.
  - **Review-notes drawer.** It still carries v7.0's field label "Primary user question" and "(owner question)". That drawer is review tooling ("ASSETOPS · SCREEN REVIEW"), its content is business content, and I do not count it against the rule.
- **Design documents.** They keep the questions as acceptance tests (main §3.4 and §6.2: "never shown on screen"). `walkthroughs.md` marks quoted lines as presenter speech.

### Foundation, generality, derivation

- **Still intact.** Rev 5 adds Protect as a fourth instance of the same mechanics (Define, Observe, Evaluate via bounds, Choose via must-do and protective, Prove via guardrails generated from the same bound rows).
- **No new path-specific logic.** `loop-protect.js` is generic over the manifest's `portfolio.protect`. The checker's id-specific line is fixture arithmetic.
- **No top-down reasoning.** Protect state is read from measures up to a count of measures above target, never the reverse.
- **M1 removes the last lever-shaped node** from the observed structure.

### Findings (all Low)

**L1 · The plan-value drawer still carries the rev 4 label and definition, and Harvest and Metro have no drawer for the figure.**
- **Where:** `interactive-mockup-vNEXT/loop-core.js:215` (unchanged in rev 5).
- **What I saw:** the Lakeside Overview hero "+$6,096 · show how this is worked out" opens a drawer titled **"Modelled 12-month change of the plan"**, with the definition "Sum of the modelled effects of the options in the plan." Kisiwa repair and battery evidence are options in the plan and are not in the sum. This is the ambiguity M2 removed from the headline, still present one click down. The function hard-codes the Lakeside option ids. Harvest's and Metro's hero values (+$3,182.40, +$95,484) have no "show how this is worked out" link at all.
- **Fix:** retitle the drawer "Modelled 12-month change from the valued options". Define it as net of the valued options' own one-off costs, and list the not-valued spend. Generate it from `modelled_12m_change` for every tenant.

**L2 · The Thika and Kasarani stopgaps are classed as must-do in one place and protective in another.**
- **What I saw:**
  - Act first's reason column says "Must do: protects stock now, until 8 Nov" (`loop-portfolio.js:84`) and "Must do: departures at risk now".
  - The Overview and Act-first value notes, and models §6.4, call the same items "protective".
  - The manifest flags `must_do: true` only on KIS-REPAIR.
- **Why it matters:** the allocator treats these classes differently (models §6.1: must-do is funded first; protective takes leftover resources by deadline). Under §4.7, no action at Thika and Kasarani fails a HARD bound, which makes them must-do. The Harvest note also says the effect is on "backup cover nights", which is not a declared measure; the measure is "days backup start unproven".
- **Fix:** set `must_do` in the manifest. Use "must-do" in models §6.4 and in the notes, or justify "protective". Name the declared measure.

**L3 · The Metro Overview labels Ruiru's +$19.68 "not explained by the model yet".**
- **Where:** `loop-portfolio.js:46` (hero line) and `:156` (composition column).
- **What I saw:** the hero reads "−$3,204 attributed to observed factors · +$19.68 not explained by the model yet". Ruiru's amount is a plan-granularity gap: the waterfall itself says "Not attributed: the plan is declared only as a bill total" (contracts AT-11). Contracts E9 restricts the residual label to an observed total exceeding what the modelled children explain. This came in with the rev 5 relabel; rev 4's wording "unobserved leaves" fitted this case.
- **Fix:** split the hero line into model residual and "not attributed (plan not declared at factor level)", using the node's `resLabel` as the waterfall already does.

**L4 · Candidate litres carry a different evidence class in different places.**
- **What I saw:**
  - The manifest bridge, contracts §3.1 (l.218) and the main document (l.416) class the 330 L candidate as DERIVED ("Calculated from records"). The mock-up shows the same.
  - Models §3.4 gives dispatch-3.2's output "Uncertainty: MODELLED".
  - The sibling necessary-litres split from the same classifier × SFC is "MODELLED split".
- **Fix:** state one class for both halves of the dispatch split with the reason. If candidate is DERIVED because it is a rule applied to metered data, say why the +30 L necessary split is not.

**L5 · Protect coverage of the brief's list, and summing of EXPOSURE measures.**
- **Gaps against the brief:** the brief's L1.1 Protect column also names "material outages" and "physical assets at risk … expected loss only with defensible likelihood, required capital".
  - The mini-grid structure has a measure for critical energy only, none for supply interruption to ordinary customers. Obligation-hours without redundancy is exposure to an outage, not an outage.
  - Asset value at risk (BAT-001, 64,000) appears only as a right at stake. No measure covers asset value at risk, and the pack does not say why one is left out or deferred.
- **Summing:** the CSV `protect-measure` rows for the EXPOSURE measures say "Sigma over sites", and the manifest gives `stock_value_exposed` a portfolio total. Contracts §6.6 says an EXPOSURE measure is never summed. Harmless with one site, but it contradicts the invariant.
- **Fix:** either add an "unserved energy, all customers" or "customer-hours interrupted" measure and an "asset value at risk (likelihood basis)" measure, or record in `design-questions-and-decisions.md` why they are deferred. Make the CSV and manifest say "listed" for EXPOSURE.

**L6 · Commit hygiene.**
- `interactive-mockup-vNEXT/loop-protect.js` is **untracked** (`git status`: `??`). `build.mjs` requires it, so committing only modified files would leave the committed mock-up unbuildable. It must be added in the rev 5 commit.
- `loop-core.js:53-54`, `:74`, `:76` and `:90` still map the retired driver keys `GEN_POLICY_RUNNING_AVOIDABLE` and `GEN_POLICY_RUNNING_CONSTRAINED`. This is dead code, since `fixtures.js` no longer holds them. Remove it so a later fixture cannot reintroduce the labels.

### Checks run and what they returned

- **`python3 check_manifest.py`:** 202 checks passed, 0 failed.
- **Build.** I copied the mock-up sources to the scratchpad and ran `node build.mjs`. The rebuilt `index.html` is **byte-identical** to the committed working-tree `index.html`.
- **Preserved v7.0 screens.** I independently compared `.canvas` text for all 65 Preserved screens, v7.0 (`frontend/mockups/v70/index.html`, file://) against vNEXT, using the audit's display-name map. **65 of 65 identical**: 21 raw-identical, 44 after the name map. `src-v70-baseline/*` is byte-identical to `frontend/mockups/v70/*`. No re-based v7.0 file changed in rev 5. `frontend/mockups/v70` is unchanged.
- **Browser click-through.** 264 route renders with 0 page errors and 0 console errors. Every route I opened has a `.canvas`. I also opened:
  - the Overview, Act first and Outcomes by site for each operator: Protect card measures with target 0; Protect table by site; November-to-6-Nov table for Metro only; at-stake listed;
  - the plan-value drawers;
  - the review-notes drawer on every scanned route;
  - the Kobo decision page.
- **Protect figures reconciled by hand** across contracts §2.6 and §3.4, models §3.11, the manifest, the CSV and the rendered tables:
  - **Lakeside:**
    - obligation-hours 0 + 10 + 20 = 30 (2 × 5 h; 4 × 5 h);
    - asset-days 0 + 2 + 4 = 6.
  - **Harvest:**
    - crate-minutes 120 × 20–30 = 2,400–3,600;
    - backup unproven 6–31 Oct = 26 days;
    - liability 108.00, equal to the cost factor.
  - **Metro:**
    - departures missed 0 in October and 2 in November to date;
    - nights below required 5 (1/2 to 5/6 Nov);
    - charger-days 26 in October (Ruiru, 6–31 Oct), and 5 + 6 = 11 in November to date;
    - penalties 240.00 in November.

  All consistent.
- **M2 figures reconciled by hand** (see above). All consistent across the documents, manifest and screen.
- **Code citation checked:** `outcome_map.py` l.145–181.
- **Server:** stopped afterwards; port 18743 is free.

### Not verified

- I did not rerun the author's `tools/run-audit.sh`: its contrast, focus and 390 px overflow counts and its screenshots are unchecked by me.
- The forward-replay design values (still design values by the pack's own label).
- The rendered mermaid in `layer4-transformation-design.html`.

### Residual risk not already named

- The Protect section adds a third and fourth table to Outcomes by site. The Overview Protect card now lists four or five lines per operator. Density at 390 px rests on the author's audit alone (see "Not verified").
- `must_do` and `protective` are allocator inputs (L2). If the build takes them from the manifest as it stands, Thika's and Kasarani's stopgaps would be funded from leftovers rather than first. That is harmless at these budgets but wrong under a tighter one.

## Re-review (rev 5) — addendum: owner-expectation points

**Same reviewer, same day.** This is a second pass at the owner's request. It covers the coordinator's six points, judged against the owner's messages 2, 5, 6 and 8 and the brief (C0, C1 D6 and the "not four silos" framing), and then a comparison of the pack with the brief's Layers 1–3 (Parts II–IV).

To check this pass I served the mock-up again on 127.0.0.1:18744 (not 5490 or 8990) and drove it with headless Chromium. The server is stopped. Nothing in the pack was changed; I only appended this section.

### Revised verdict: **REVISE (targeted)**

This replaces the ACCEPT WITH NOTES above. Three Medium findings come out of this pass:
- **OE-1:** the Portfolio's tab frame is kept rather than derived from the loop.
- **OE-6:** the mock-up no longer tells the viewer that the replay figures were never run.
- **LY-1:** two of the brief's objectives have no declared measure.

Each is fixable within the current design. The foundation (structure, mechanics, derivation) still stands, and so do the earlier re-review's findings L1–L6.

### Part A — the coordinator's six points

**OE-1 · Medium · included. The Portfolio keeps its six tabs without judging them against the loop.**
- **The pack's own words:**
  - Main §6.1 item 2: "The Portfolio keeps its six tabs and their owner-approved names, with their content re-based on the mechanics".
  - Main §6.2: "The restructure keeps the frame and replaces the substance".
  - Nowhere does the pack assess the tab set or its names on merit. The "Mechanic" column in §6.2 is assigned after the fact.
- **It contradicts the pack's own strategy.** §6.1 item 1 says "The Portfolio's sections follow Observe → Evaluate/Choose → Prove". The tab order is:
  1. Overview (M1, M2, M4)
  2. **Act first (M3, M4: Choose)**
  3. **Outcomes by site (M1, M2: Define/Observe)**
  4. Opportunity (M2 latent factors, M3)
  5. What changed (M5)
  6. Scope & coverage (M2 sources)

  So Choose comes before Observe.
- **"Opportunity" no longer names what the tab holds.** It now holds only demand (§6.2: "qualified demand ranked by net contribution … capacity without customers"). In the loop, every option is an opportunity: the stop-setting change, the Kirinyaga repair and the Embakasi schedule all live in Act first and on decision pages.
- **Against the owner:**
  - Message 2: "review the overall current portfolio experience and structure it in a way those requirements are met".
  - Message 6: re-use should follow "establish the core future mechanics, and then decided what to reuse, rebuild or create".
  - Confirmed point 3: "Where a part fits … keep … Where it doesn't, say why".

  The tab frame is the one part of the Portfolio that was not judged this way.
- **Mitigation:** owner decision Q2 (`design-questions-and-decisions.md` l.11) and checklist item 1 do offer "a different tab set". That puts the question to the owner, but it is not the assessment the owner asked for.
- **Fix:** assess each tab's existence, name and order against the loop, with a keep / rename / merge / reorder reason per tab. Either justify the current order (for example, "the plan first because that is where action is decided") or reorder to Observe → Evaluate/Choose → Prove. Either rename Opportunity to name its demand content or widen it. Record the reasoning in §6.2.

**OE-2 · Low · included in part; the "silo" claim is rejected with proof.**
- **What holds:** the §6.2 column "Acceptance test it must pass" reads as a role-per-tab assignment:
  - Act first → CEO, COO
  - Outcomes by site → CFO
  - Opportunity → CCO

  The CFO's "what may be recoverable" (the rights tracker) actually sits in What changed and on decision pages. The CEO's "site economics" drill-down is Outcomes by site.
- **What is disproved:** that the structure is "close to one silo per role".
  - The brief's silo test is "not four product silos or four underlying financial truths" (header, l.24).
  - Every tab reads the same structures and numbers (main §3.4: "Every role sees the same numbers"; §6.1 item 1).
  - There is no role filter. The Overview is mapped to "all four", What changed to "COO, CFO", and Scope to "all; conversion".
  - In the browser, the Lakeside plan figure (+$6,096) and the Outcomes-by-site attribution draw on the same factor rows, and the drawers open the same source rows.
  - L1.3 itself requires the four answers to be findable on the Portfolio, which is what §6.2 traces.
- **Fix:** recast the §6.2 column as a question-to-sections trace showing that each answer spans sections (CEO: Act first + Outcomes by site + decision pages; CFO: Outcomes by site + What changed). Do not tie one role to a tab.

**OE-3 · rejected with proof. The mechanics are not tied to the demo world.**
- Of the 98 non-empty paragraphs and lines in main §2 (l.57–205), **6** name a demo site.
- Each mechanic is stated first as Job, Identity and Refusal in general terms (§2.1–2.5). The examples are one-clause illustrations spread across all three verticals:
  - Kasarani and Embakasi (EV);
  - Thika (cold);
  - Kobo and Mto (mini-grid).
- The brief requires worked amounts:
  - C1 D2: "Show the flow with a worked set of plausible labelled illustrative amounts that exactly reconcile; do not show simply an empty data dictionary".
  - C1 D1: "Begin with an end-to-end conceptual walkthrough".
- The worked traces are already in §7.
- One optional edit, not a finding: the Lakeside numeric paragraph in §2.2 could move to §7.1.

**OE-4 · Low · included. The Overview is long, and the plan's first moves sit at the bottom.**

Measured in the browser, Lakeside and Metro Overview against v7.0 Portfolio:

| Measure | Lakeside / Metro Overview | v7.0 Portfolio |
|---|---|---|
| Height at 1440 px | 1,986 px (about 2.2 viewports) | 2,228 px |
| Height at 390 px | 5,147 px (about 6.1 phone screens) | 4,417 px |
| Words | 885 | 1,074 |
| Figures | 98 | 121 |
| Headings | 9 | — |

- **What is fine:** at desktop the page is less dense than v7.0. The first fold leads with the result, as C1 D6 asks: one headline sentence and four figures.
- **The problem:** D6 asks the demo to lead with "business results **and choices**". The choices (First moves) are the last block: at about 1,700 px on desktop and near the end of a 5,100 px phone page.
- **Other density issues:**
  - The fourth hero card carries a 60-word note.
  - Six blocks follow the headline:
    - value chain;
    - four outcome cards;
    - factors needing attention;
    - look-alike sites;
    - first moves;
    - the note under the cards.
  - At 390 px the page is 17% longer than v7.0's.
- **Fix:**
  - Bring First moves (or the plan line) into the first fold.
  - Shorten the hero notes to a line, with the rest in the drawer.
  - Collapse the value chain at 390 px.

**OE-5 · rejected with proof. Keeping v7.0 screens is required, and none of the kept screens is a Portfolio screen.**
- **The brief requires it.** C1 D6: "Produce a **new version of the existing interactive mock-up**, keeping working navigation, drill-downs and relevant old features unless there is an explicitly justified retirement", and "Do not replace that work with … a new unrelated visual concept".
- **None of the 65 Preserved screens is part of the Portfolio experience.** The Preserved ids (`screen-manifest-vnext.json`) are deep estate, finding, action, asset, setup and work pages: `foundation`, `dispatch`, the `cold-*` and `ev-*` pages, `asset-*`, `action-*`, `site-create-*` and `wr-*`. None is a Portfolio tab, a site overview or a decision page.
- **The Portfolio experience was rebuilt:**
  - Overview Changed;
  - five Portfolio tabs plus the pilot screen Added;
  - 9 site overviews and their economics pages Added;
  - 14 decision pages Added;
  - 9 v7.0 screens Merged into site economics;
  - 74 screens Added in all.
- **Re-basing Thika and Ruiru serves D6's "realistic fixture data consistent across portfolio/site/decision views".**
- **What remains:** the part of the concern that holds, the kept Portfolio frame, is OE-1.

**OE-6 · Medium · included. The documents disclose the replay values properly, but the mock-up no longer does.**
- **The documents are adequate:**
  - main l.430 ("**design values** … the replay adapter must reproduce them");
  - main §12 l.605 ("does not establish … that the forward replay is calibrated on a real site");
  - models §4.2 (calibration gate, `REPLAY_NOT_CALIBRATED`);
  - RR1;
  - phase-plan spike exit ("design values until this spike passes");
  - Q12 for build cost (owner decision, budgets labelled "target"; `design-questions` l.21 and l.56).

  Their ranking is right: the replay spike gates slice 4, and Q12 is an owner decision.
- **The mock-up:**
  - The decision page states replay results as observed fact: "held on 61 of 61 days", "broken on 4 of 61 replayed days", "a forward replay of 61 days".
  - The plan-value drawer says "Forward replay of site data (modelled)". I scanned the canvas and every drawer on Overview, Act first, `decision/kobo-generator` and `decision/mto-demand`: none says the replay has not been run or that these are design values.
  - The only such wording ("design value, to be reproduced from your data") sits in `loop-core.js` in the label map for the retired `GEN_POLICY_RUNNING_AVOIDABLE` bridge row, which M1 removed.

  So **the rev 5 M1 fix dropped the only on-screen disclosure.** The +$2,916 drives the +$6,096 headline that a prospect sees.
- **Fix:** label replay-derived figures on the decision page and in the plan-value drawer, for example "design value: replay not yet run on your data", until the slice-4 spike passes.

### Part B — the pack against Layers 1–3 of the brief

**Method:**
- I read Parts II–IV in full (brief l.104–360).
- I counted each lever, capability and objective ID in each pack document.
- I compared the traceability CSV's 135 class-objective rows with the L2.5 outcome × lever map: **0 role mismatches**.
- I checked each lever row for a designed model (models §3–§4, main §5), a demo option and an on-screen presence.

**What is carried well:**
- **L1:** the outcome decision invariants (main l.45); the unit hierarchy (classes and the evidence words in §6.1 item 4); the "never assume" column (gross exposure is not value, unexplained kWh is not theft, stock exposed ≠ spoiled ≠ liability, a verified operation ≠ realised saving, all as refusal rules); and the L1.3 portfolio → site → decision → source path with switches that re-prioritise.
- **L2 Hero levers each have a designed model, an option and a screen.** Every Hero lever has one; the levers that need more than the CSV entry are listed under LY-3.

  | Lever | What carries it |
  |---|---|
  | MG-L1, MG-L3, MG-L4, MG-L8, MG-L10 | demand-on-headroom replay; forward replay; energy-to-cash; allocator; remedy paths |
  | CC-L1, CC-L5, CC-L6, CC-L7, CC-L9 | occupancy ledger; normalised energy; batch exposure; lifecycle comparison; remedy paths |
  | EV-L1, EV-L2, EV-L3, EV-L5, EV-L9 | deadline-aware schedule; roster capacity; fault consequence; lifecycle comparison; remedy paths |

- **Supporting and veto levers:** MG-L5 (fuel balance), MG-L6, EV-L7 and CC-L6 (bounds).
- **Captive-EV boundary:** handled as the brief requires (EV-L6 and EV-C4 NOT_APPLICABLE).
- **L2.7 "do not own":** respected and cited (integration doc l.12: "does not become a billing system, a contract-lifecycle tool or a claims administrator"). Field changes are "configuration recorded; device change to be confirmed by the operator".
- **L3:** S1–S12 are mapped to mechanics (main §3.3), and each P0-D vertical capability has a phase slice (phase plan l.190–212).

**LY-1 · Medium · Two L1 objectives have no declared measure: O2 everywhere, A4 at all.**
- **O2:** brief L1.1 and L1.2 define O2 for every vertical:
  - mini-grid: "reliable supplied energy with efficient asset dispatch and site visits";
  - cold: "cooling/handling throughput and uptime without temperature violations";
  - EV: "fleet-ready vehicles and charger utilization without missed departures".

  Main §3.1 lists O1–O3 under Optimize, but the outcome measure is only "cost to serve per paid service unit; realisation billed → recognised → collected". That is O1 and O3. Contracts §2.2–§2.6 tag Protect measures with an objective but never G1–G3 or O1–O3; their counts there are 0. No structure has a throughput, uptime or crew-productivity measure. Crew visits appear only as an M4 constraint, and charger-days out of service only as a P2 measure.
- **A4:** "investor/lender/audit-ready evidence" has no design anywhere. Its count is 0 in the main doc; the one "A4" in models and the four in contracts are the **attribution rule** A4, not the objective.
- **Why it matters:** this is the same class of gap as rev 4's H1. The owner's confirmed point 1 asks that each outcome be built from factors "with clear units, periods and scope". After H1, Protect does this; O2 does not.
- **Coverage claims:**
  - The CSV's "objectives 15/15" is met by enumeration: the class-objective rows are the full 15 × 9 product, with "influence: see vertical levers" on all 135 and only 45 distinct factor texts.
  - The lever-objective rows do include O2. For example, MG-L3 is listed under O1 O2 P1 P2. But the rows map the lever to the objective without any O2 measure behind it.
- **Fix:** declare O2 per vertical as measured factors, for example:
  - mini-grid: crew visits per resolved fault, generator starts;
  - cold: chamber availability and throughput crate-days without excursion;
  - EV: charger-hours used against departures met.

  For A4, either declare it as an evidence-pack reading of A1–A3 or record its deferral. Rename attribution rules A1–A5 (for example AR1–AR5) so they do not collide with the Assure objectives.

**LY-2 · Low · The core realisation lever X3 is designed only for mini-grids. Cold service-to-cash is shallow.**
- **Brief:** L2.5 rates X3 "**Core** (EV optional for captive)", with the cold example "crate-day→invoice". CC-L8 "find chargeable-vs-invoiced discrepancies". The CC-C1 acceptance is "occupancy contribution reconciles with invoices".
- **In the pack:**
  - The energy-to-cash observer is "new, mini-grid" (models §3.2, main §5).
  - Cold has only a calibration line in the occupancy observer ("reconcile ledger revenue with invoices within 0.5%", models §3.6). Chargeable crate-days equal occupied in October (contracts §2.3), and there is no cold discrepancy case or option.
  - The CSV row for CC-L8 names a model, "storage-ledger to invoice reconciliation", that main §5 and models §3–4 do not contain. Its demo option is "none".
- **Fix:** declare the cold realisation stages (occupied → chargeable → invoiced → received), with an observer and one negative test, or state CC-L8 as deferred with its reason.

**LY-3 · Low · Some lever and capability rows exist only as CSV names.**
- **MG-L2 (Hero, paired with MG-L1):** "daytime windows, time-linked tariff or operating schedule". Its only option is the MTO-HULLER / WELDING pair, the same as MG-L1. No time-linked tariff and no shifting of an existing customer's load is modelled.
- **EV-L7 "charging reliability and battery health":** the CSV gives "obligation policies EV1/EV5 on schedule options". Vehicle-battery health is not modelled, and the brief's boundary ("uncertain without validated battery data") is not cited as the reason.
- **MG-C4 (P1-P) "fuel procurement":** the brief includes delivery and **price** discrepancies. The fuel balance (models §3.3) covers volumes only.
- **Fix:** give each its own model line or a stated deferral with the brief's boundary as the reason. Brief §L2.1 says "each row names a real-world action": a CSV row alone does not carry it.

**LY-4 · Low · Part of the CEO's L1.3 minimum answer is missing from the Portfolio.**
- L1.3 asks the Portfolio for interventions "with budget, horizon, **downside** and reason". The allocator computes a downside (models §6.1, the sort key "−downside", defined as "the set's value under the worst listed sensitivity").
- No Act-first screen shows it. I searched all three operators for "downside", "sensitiv" and "worst" and found 0 plan-level hits. Sensitivity appears only on decision pages.
- **Fix:** show the plan's downside beside its modelled value.

**LY-5 · Low · Two capability acceptance tests are not addressed.**
- **EV-C5:** "COO/CFO/CEO see same evidence but different defensible allocations". The pack produces one plan with switches (models §6.4) and never says how, or whether, different defensible allocations are shown. This is related to its deliberate omission of "role emphasis" (A14).
- **P4 and A5:** the brief's entitlement measurement rules list measures "by contract and period":
  - assets with complete or valid contracts;
  - obligations at risk of deadline;
  - remedy completion time;
  - operator-funded residual expense;
  - recognised and settled credits.

  The pack carries rights as states and per-path residual cost (contracts §5, models §7.2), but declares only "rights value at stake (listed)" as a Protect measure.
- **Fix:** state the EV-C5 position, for example as switches representing different resource priorities. Add the P4 and A5 measures to contracts §2.6, or defer them with a reason. This overlaps the re-review's L5.

**Covered only for one vertical, beyond LY-2:**
- The forward replay, the fuel balance and dispatch-3.2 are mini-grid only by nature, which is fine.
- The end-to-end decision sequence (models §5) is drawn only for Kobo. Main §7 does carry worked traces for all three verticals and the rights contrast, as C1 D1 requires.
- No further single-vertical gaps found.

**Misrepresented or contradicted:**
- No Layer 1–3 content is contradicted.
- The two overstatements are the CSV's coverage statistic (LY-1) and the CSV's model name for CC-L8 (LY-2).

### Findings that now stand

- **Medium (block until fixed or answered by the owner):**
  - OE-1, the Portfolio frame judged on merit;
  - OE-6, on-screen disclosure that the replay values are design values;
  - LY-1, the O2 and A4 measures.
- **Low:**
  - from this addendum: OE-2, OE-4, LY-2, LY-3, LY-4, LY-5;
  - from the re-review: L1–L6.
- **Rejected with proof:** OE-3 and OE-5.

### Checks run for this addendum

- **Overview density:** measured in Chromium at 1440 and 390 px for Lakeside and Metro, and v7.0 Portfolio for comparison. I captured a full-page screenshot to the scratchpad (not added to the pack).
- **Act first and Opportunity:** text scans for all three operators.
- **Replay wording:** scanned the canvas and all evidence drawers on four routes.
- **Preserved screens:** classified the screen inventory by status.
- **ID counts:** lever, capability and objective IDs counted in each pack document.
- **CSV:** checked its role mapping against L2.5 in code.
- **Server:** stopped; port 18744 is free.

## Re-review (rev 6)

**Reviewer:** a fresh, independent Claude reviewer, 17 Nov 2026. I reviewed the rev 6 working tree on `task/product-direction-layer4-design`, uncommitted over `146667cfc`. I judged it against "## Re-review (rev 5)" (L1–L6), its addendum (OE-1 to OE-6, LY-1 to LY-5), the author response (rev 6), the owner's brief and the owner's verbatim feedback (messages 1–8). I changed nothing in the pack, the code or any database; this appended section is my only edit.

### Verdict: **REVISE (targeted)**

OE-1 is resolved, and so are most of the Lows. LY-1 and OE-6 are resolved in structure but not in full, and that gives two Medium findings:
- **N-M1:** the new EV O2 measure contradicts the pack's own definition of deliverable energy.
- **N-M2:** some replay figures on the Overview and Act first are still unlabelled.

Both are small fixes. Five Lows follow. The foundation, generality, derivation and the Portfolio restructure still hold.

### Resolution of the prior findings

- **OE-1: resolved.**
  - Main §6.2 now judges each tab (keep / rename / reorder) with a reason against the loop.
  - In the browser, all three operators show the tab row Overview · Outcomes by site · Demand and capacity · Act first · What changed · Scope & coverage.
  - `#/portfolio/opportunity` redirects to `#/portfolio/demand-and-capacity`.
  - The rename is justified on content. The reuse matrix (l.187) and phase plan PR 5b carry the same order for the live product, and Q2 puts it to the owner.
- **OE-2: resolved.** §6.2 is now a concern-to-sections trace, and each concern spans two to four sections.
- **OE-4: resolved.**
  - The first fold is the headline, four figures and "The plan's first three moves".
  - At 390 px the value chain `<details>` is closed, and the Lakeside Overview is 4,344 px tall (5,147 at rev 5). There is no horizontal overflow.
- **OE-6: partly resolved.** See N-M2.
  - Labelled: the Overview hero ("includes design values not yet run on site data") for all three operators; all three plan-value drawers; the decision pages (a page banner plus per-option tags); the Act-first plan rows and totals.
  - Still unlabelled: three places, listed under N-M2.
- **LY-1: resolved in structure.**
  - The O2 measures are declared per vertical in the manifest, contracts §2.7, models §3.13, the checker, the CSV `declared_measure` column and on screen ("Operations measures by site").
  - A4 is designed as an evidence-pack reading with a slice (9), not just named.
  - AR1–AR5 are renamed consistently, except one botched replacement (N-L1).
  - Hand recomputation (below) reconciles every figure except the EV utilisation denominator (N-M1).
- **LY-2: resolved.**
  - Cold realisation stages, observer models §3.12, N20 and E14 are declared.
  - Thika and Kirinyaga site pages state "October: no difference … so no billing option exists".
  - 22,940 crate-days × 0.20 = 4,588.00 = 4,370.00 + 218.00.
- **LY-3: resolved.** Models §4.9 gives each lever a model line or a deferral with the brief's own boundary. I checked the quotes in the brief: l.179 "legal/customer-acceptable", l.219 "without validated battery data". MG-C4 adds a price-discrepancy check.
- **LY-4: resolved.**
  - The downside appears on Act first and in the drawer for all three operators.
  - Lakeside 6,096 − 3,540 = 2,556 ✓. Harvest 3,182.40 − 1,670 = 1,512.40 ✓. Recovery at 60%: 0.6 × 194 × 12 − 350 + 1,670 = 2,716.80 ✓. Metro 0.00 under "option dropped" semantics, consistent with Lakeside's.
  - One secondary figure is wrong (N-L2).
- **LY-5: resolved.**
  - Contracts §5.5 and manifest `rights` declare the rights measures. What changed renders them (Lakeside 1 of 3, an open deadline on 27 Nov, $0 residual expense, $0 recognised credits) with the legal disclaimer.
  - The EV-C5 position is in main §2.4 and models §6: switch settings, never role views. The brief quote at l.342 is verified.
- **L1: resolved.**
  - Each operator's drawer is titled "Modelled 12-month change from the valued options", generated from `modelled_12m_change`, with not-valued spend, the downside and the design-value note.
  - One residue: Act first's path cards still read "Modelled 12-month change of the plan" (N-L3).
- **L2: resolved.**
  - The manifest marks `must_do: true` with a reason on THIKA-EPC-STOPGAP and KAS-OEM-STOPGAP.
  - Act first reads "Must do: no action fails the batch temperature limit (days with the backup start unproven)" and "… fails the departures limit (departures missed)".
  - Models §6.4, the main document and A19 agree.
- **L3: resolved.** The Metro hero reads "+$19.68 not attributed yet", and the Assure card reads "not attributed (plan is a bill total)". The source has no "not explained by the model yet" for Ruiru.
- **L4: resolved.** The manifest, contracts §3.1, models §3.4 and the main document classify both halves as DERIVED.
- **L5: resolved.**
  - Customer-hours interrupted is declared and rendered (0).
  - Asset value at risk shows as "not available yet (needs a failure-likelihood basis)" (A17; brief l.114 quote verified).
  - EXPOSURE measures are `LISTED` in the manifest. The CSV has 0 EXPOSURE rows that sum.
- **L6: resolved.** `loop-protect.js` is tracked. `GEN_POLICY_RUNNING_*` has 0 hits in `loop-*.js`.
- **Unprompted corrections.**
  - **Ruiru 0.31 → 0.34: arithmetically right as charger-hour utilisation.** 1,960 / (12 × 60 kW × 8 h) = 0.3403, and 14 buses × 140 kWh = 1,960 = 60,760 / 31. But see N-M1 for what it is labelled as.
  - **Harvest cooling-minutes split: correct.** 3 × 44,640 = 133,920. Thika: 1 − 4/44,640 = 99.991%. Portfolio: 1 − 4/133,920 = 99.997%. This matches the 19:11–19:15 outage in the manifest (l.423–424).

### O2 figures recomputed by hand

| Measure | Working | Result |
|---|---|---|
| MG asset availability | (124 + 122 + 151) / (124 + 124 + 155) = 397/403 | 98.51% ✓ |
| — out-of-service days | 0 / 2 / 4, equal to the Protect asset-days | ✓ |
| — by site | Kisiwa 122/124 and Mto 151/155 | 98.39% and 97.42% on screen ✓ |
| MG kWh per visit | (9,100 + 7,950 + 6,000) / 3 = 23,050 / 3 | 7,683.33 ✓ |
| Cold crate-days without excursion | 4,340 + (8,680 − 120) + 9,920 = 22,820; plan 7,440 + 8,680 + 9,920 = 26,040 | ✓ |
| EV utilisation as declared | (2,800 + 1,200 + 1,960) / (10 × 60 × 12 + 4 × 50 × 7 + 12 × 60 × 8) = 5,960 / 14,360 | 41.50% ✓ arithmetically (but see N-M1) |
| EV departures per charger | (620 + 248 + 434) / (10 + 4 + 12) = 1,302 / 26 | 50.08 ✓ (but see N-L4) |

### Owner expectations (feedback file, messages 1–8)

- **Mechanics first, read upward.**
  - Rev 6 adds O2, rights and cold realisation as further declared factor structures, each with unit, period, composition and evidence class.
  - Each is observed from leaves and composed Σ or Σ/Σ, never detected at the top.
  - A4 is a reading, not a parallel measure.
- **General across verticals.**
  - O2, rights and Protect are declared for all three tenants.
  - The cold realisation stages fill the shared STAGE kind. EV's O3 is NOT_APPLICABLE (captive), as the brief allows.
  - No new path-specific logic: `loop-protect.js` reads `portfolio.operations` and `portfolio.rights` generically.
- **Derived integrations, algorithms, UI and reuse.**
  - Each new measure has a reuse-matrix row with source, decision and missing input: `0027:35`/`0027:145`, `analytics/cold.py`, `analytics/ev_availability.py`, and a new rights register.
  - The tab reorder is derived from the loop.
- **Portfolio restructured with no role toggles, filters or menus.** The left rail and the six-tab frame are unchanged. The audit shows no filters, and there is no product operator selector; the "Demo operator" selector belongs to the review bar.
- **Executive questions never on screen.**
  - I visited 264 Added or Changed route renders across the three operators and opened up to four evidence drawers on each.
  - 0 role names (CEO, COO, CFO, CCO, executive).
  - 0 headings or tab names ending in "?".
  - The design documents keep the questions as acceptance tests (§6.2 "never shown on screen"). The CSV's `executive_question` column is design-side only.

### Layers 1–3

- The earlier LY gaps are closed as described above.
- The CSV has 453 rows and 18 columns. Every objective except A4 has a declared measure for all three verticals; A4 is declared as a reading. Cold has no P2 measure, and the CSV says so with a reason.
- No contradiction of Layers 1–3 found.
- The only new tension is N-M1. EV "deliverable" energy is defined two ways, which bears on G2/O2 and on the Ruiru expansion story (EV-L2).

### Findings

**N-M1 · Medium · The EV O2 "charger energy utilisation" denominator ignores the import limit, so the screen shows two different "deliverable" figures for Ruiru.**
- **Where:**
  - manifest l.624–627 (`unit: "share of deliverable charger energy in the usable window"`, denominator 5,760 for Ruiru and 7,200 for Embakasi);
  - contracts §2.7 table and l.181;
  - models §3.13 (OP-T2);
  - rendered on `#/portfolio/outcomes-by-site` (Metro): "share of deliverable charger energy … Ruiru 34.03%, 1,960 of 5,760 kWh a night".
- **The contradiction:**
  - The same manifest gives Ruiru `import_limit_kw: 400` and `RUI-ABSORB6 … deliverable_kwh: 3200`.
  - `RUI-ABSORB10` is rejected because it "exceeds the 400 kW import limit".
  - Embakasi has `import_limit_kw: 500`, and EMB-CHEAPEST's deliverable is computed "at the 500 kW import limit".
  - Metro's Demand and capacity tab renders "Vertical line: 3,200 kWh deliverable a night at the 400 kW import limit".
  - So in one app, Ruiru's deliverable energy a night is 5,760 on one tab and 3,200 on another.
- **What the doc wrongly claims:** contracts l.181 says "Ruiru's 34% utilisation is the capacity the +6-bus option uses". At 34% of 5,760, the remaining headroom would carry (5,760 − 1,960)/140 ≈ 27 more buses. The binding limit is 3,200, i.e. 61.25% used, with room for 8.9 buses. That is why +6 passes and +10 fails.
- **Corrected figures:** with the import-limited denominator, Embakasi is 2,800/6,000 = 46.67%, Kasarani 85.71% (250 kW is not binding), Ruiru 61.25%, and the portfolio 5,960/10,600 = 56.23%.
- **Why it matters:** LY-1 asked for O2 measures that are real structures and reconcile. This one reconciles with its own formula but not with the factor structure's `deliverable_kwh_per_night` stage (manifest l.35) or the bound logic. Read naively, it supports the wrong capacity conclusion on the depot the story uses for "looks underused".
- **Fix (either):**
  - make the denominator min(chargers in service × kW, import limit) × window, consistent with `deliverable_kwh_per_night`, and update the manifest, checker, contracts §2.7, models §3.13, CSV and screen;
  - or rename the measure "charger-hour utilisation (nameplate)" (as Demand and capacity already says, "in use 34% of charger-hours"), add the import-limited share beside it, and correct contracts l.181.

**N-M2 · Medium · OE-6 is not complete: replay-dependent figures on the Overview and Act first are still unlabelled.**
- **The rule:** decision A20 and the author response say "every figure resting on a replay carries 'Design value …'".
- **What I found:** I scanned in the browser all 264 route renders and their drawers for 210 L / 61 of 61 / $2,916 / 68 L / $395 / $3,540 / 31 of 31 / $6,096 / $2,556 / $3,546 and checked each hit's container. These remain without the label:
  - Lakeside Overview, Optimize card factor line (`loop-portfolio.js:51`): "of it, the best feasible option avoids 210 L a month (Modelled)".
  - Lakeside Overview, "Sites that look alike need different levers" (`loop-portfolio.js:72`): "the best feasible option avoids 210 L a month (Modelled), worth $2,916 over 12 months". This is on the first screen a prospect sees.
  - Lakeside Act first:
    - the path cards (`loop-portfolio.js:134`): "+$6,096" and "+$3,546";
    - the "All four cases of the two switches" table (`loop-portfolio.js:141`): +$6,096 / +$2,556 / +$6,096 / +$3,546, every one including the 2,916.
  - `#/decision/mto-inverter` (`loop-site.js:37`): the banner says the sensitivity values "include the rice huller replay". But +$2,556 is 2,916 − 360, which is entirely the Kobo forward replay, and the banner does not mention it.
- **Why the audit missed them:** the author's audit "Design-value labels: pass" and release test R13 cover only the decision pages, the drawer and the Overview plan figure. A20 promises more.
- **Fix (either):**
  - add `dvTag()` to the two Overview statements, the path cards and the four-case table, and extend the mto-inverter banner to the stop-setting replay;
  - or narrow A20/R13 explicitly and justify why secondary mentions may go unlabelled. I would not recommend that for the Overview.

**N-L1 · Low · Botched rename in contracts §5.** Contracts l.457 reads "*Brief:* R3a, P4, @@AR5@@, S12". The **objective** A5 was turned into a stray-marked attribution rule. Restore "A5".

**N-L2 · Low · The Lakeside "diesel −20%" sensitivity applies the price change to one option only.**
- **What the pack says:** manifest l.351, models §6.4, the main document, R14 and Act first all show +$5,466 = 6,096 − (2,916 − 2,286).
- **What it misses:** the huller in the same plan buys 68 L of diesel a month (fuel_monthly 85.00 = 68 × 1.25). At 1.00 per litre its 12-month value is (495 − 68 − 15) × 12 − 1,200 = 3,744.00, not 3,540.00.
- **Correct figure:** the plan under diesel −20% is 2,286 + 3,744 − 360 = **+5,670.00**.
- The downside itself (+2,556) is unaffected.
- **Fix:** recompute the set under the sensitivity, or label the figure "stop-setting sensitivity only". Have the checker recompute it.

**N-L3 · Low · Wording residues in the plan drawers and path cards.**
- **Act first path cards (`loop-portfolio.js:134`).** They still say "Modelled 12-month change of the plan", the L1 wording that the drawer dropped.
- **Lakeside drawer.** The definition repeats itself: "Net of the valued options' own one-off costs. Net of the valued options' own one-off costs ($1,650)." The cause is `loop-portfolio.js:104` prefixing `valueNote()`.
- **Harvest drawer.** It says "Design value: the replay has not yet been run on site data: includes the Kirinyaga recovery share", with "Source records: Forward replay of site data (modelled)". Neither Harvest valued option rests on a replay. Kirinyaga's figure is an assumption, as the decision page correctly says.
- **Fix:** use the A20 assumption wording for Harvest, drop the duplicate sentence, and retitle the path cards.

**N-L4 · Low · Two O2 basis details.**
- **Departures per charger.** "Departures met per charger in service" divides by 26 installed chargers. The pack's own Protect measure records Ruiru CH-R7 out of service for 26 of 31 October days. Either call it "per installed charger", or use charger-days in service: 26 − 26/31 = 25.16, giving 51.75.
- **Asset counts.** "Major assets: Kobo 4, Kisiwa 4, Mto 5" is not derivable from the manifest. Kobo's `physical` lists five components (PV, a 50 kW inverter, battery, a 30 kW PCS, generator), and Mto's five include each inverter.
- **Fix:** declare the asset list per site (it is the denominator of a measure), or state the counting rule.

**N-L5 · Low · Commit hygiene.**
- The three renamed screenshots `screenshots/vnext/*portfolio_demand-and-capacity-1440.png` are untracked (`??`).
- Their predecessors `*portfolio_opportunity-1440.png` are deleted but not staged.
- The rev 6 commit must include both, for example `git add -A` on the pack folder, or `screenshots/INDEX.md` will point at missing files.

### Checks I ran and what they returned

- **`python3 check_manifest.py`:** 217 checks passed, 0 failed.
- **Rebuild in a scratch copy:**
  - `tools/gen_fixtures.py` → `fixtures.js` byte-identical;
  - `tools/gen_docs.cjs` → `CHANGE-REGISTER.md` and `browser-audit.md` byte-identical;
  - `node build.mjs` → `index.html` byte-identical to the working tree.
- **Preserved v7.0 screens:**
  - I served the pack statically on 127.0.0.1:18761 (not 5490 or 8990). Headless Chromium 1155 compared `.canvas` text for every Preserved screen against `frontend/mockups/v70/index.html`: **65 of 65 identical** (21 raw, 44 after the display-name map).
  - `src-v70-baseline/` matches `frontend/mockups/v70/` for every shared file.
  - `git status` shows no change under `frontend/mockups/v70` or `src-v70-baseline`.
  - No re-based v7.0 source changed in rev 6.
- **Browser click-through:**
  - 264 route renders (every Added or Changed screen for Lakeside, plus every Portfolio, Sites, Site, Decision and Financials route for Harvest and Metro), with up to four evidence drawers each. 0 page or console errors.
  - Tab order, the old-route redirect, the role and question scan and the design-value scan are reported above.
  - I also checked the three plan-value drawers, Act first, Outcomes by site (O2 and Protect tables), What changed (rights), Demand and capacity (Metro) and the Kobo, Mto inverter, Embakasi and Kirinyaga decision pages.
  - At 390 px the Lakeside Overview is 390 px wide with no overflow.
- **CSV:** 453 rows × 18 columns. `declared_measure` is populated for every objective; A4 is declared as a reading.
- **Brief quotations** used for the deferrals and for EV-C5 match brief l.114, l.179, l.219 and l.342.
- **Server:** stopped; port 18761 is free.

### Not verified

- I did not rerun `tools/run-audit.sh`, so its contrast, focus and screenshot outputs are unchecked by me.
- The forward-replay design values themselves (still design values, which is the point of N-M2).
- The rendered mermaid in `layer4-transformation-design.html`.

## Re-review (rev 7)

**Reviewer:** a fresh, independent Claude reviewer, 17 Nov 2026. I reviewed the rev 7 working tree on `task/product-direction-layer4-design`, uncommitted over `fcc2ec049`. I judged it against "## Re-review (rev 6)" (N-M1, N-M2, N-L1 to N-L5), the author response (rev 7), the owner's brief and the owner's direction file (messages 1–8). I also assessed five points the coordinator relayed at the owner's request. This appended section is my only edit; I changed nothing in the pack, the code or any database.

### Verdict: **REVISE (targeted, documents only)**

- **The rev 6 findings are resolved.**
  - N-M1 is fixed, and every figure reconciles by hand.
  - N-M2 is fixed on every surface rev 6 named, and on all four Act-first switch cases.
  - N-L1 to N-L4 are fixed.
  - What remains of N-M2 is a Low residue on secondary pages (R7-L1), plus an audit that cannot find what its own list omits.
- **Three of the owner-requested points are real design gaps at Medium:**
  - CP-1: the structural alternative to six tabs is not recorded or offered to the owner;
  - CP-2: decision pages do not show each option's effect on the Protect structure;
  - CP-3: the replay-calibration plan does not cover two of the three replays, and it is not prioritised ahead of client use.
- **All three are fixed in the documents** (a decision record, model and manifest text, a phase-plan change). None needs a mock-up redesign. After one short author round, what is left is owner decisions (see CP-4).

### Resolution of the rev 6 findings

**N-M1: resolved.**

Each depot's deliverable energy is min(chargers × kW, import limit) × window, using the manifest `physical` blocks.

| Depot | Chargers × kW | Import limit | Binding | Window | Deliverable a night | Used a night | Share |
|---|---|---|---|---|---|---|---|
| Embakasi | 10 × 60 = 600 | 500 | import limit | 17:30–05:30 = 12 h | 6,000 | 86,800 / 31 = 2,800 | 46.67% ✓ |
| Kasarani | 4 × 50 = 200 | 250 | chargers | 22:00–05:00 = 7 h | 1,400 | 37,200 / 31 = 1,200 | 85.71% ✓ |
| Ruiru | 12 × 60 = 720 | 400 | import limit | 21:00–05:00 = 8 h | 3,200 | 60,760 / 31 = 1,960 | 61.25% ✓ |
| Portfolio (Σ/Σ) | | | | | 10,600 | 5,960 | 56.23% ✓ |

- **Capacity options.**
  - Ruiru's 3,200 equals `RUI-ABSORB6.deliverable_kwh`, and the checker now asserts it.
  - The headroom is 3,200 − 1,960 = 1,240 kWh, room for 1,240 / 140 = 8.86 buses. So +6 buses (840 kWh) passes and +10 (1,400 kWh) fails, which matches `RUI-ABSORB10` "exceeds the 400 kW import limit".
  - Kasarani at 85.71%, with chargers binding, agrees with the 1 Nov fault: 3 × 50 × 7 = 1,050 < 1,200 (`capacity_after`).
  - Nameplate use is 1,960 / (12 × 60 × 8) = 34.03%. It is kept on screen only as a labelled secondary figure.
- **Corrected text.** Contracts §2.7, models §3.13 (OP-T2: 56.23%; 46.67%, 85.71%, 61.25%), the main document, the matrix, A18 and the CSV measure ids all agree.
- **On screen** (headless Chromium, Metro):
  - Outcomes by site shows "Deliverable energy used (import-limited)" with the binding limit per depot.
  - Overview reads "Ruiru: 34% of nameplate charger-hours; 61% of deliverable energy a night (the 400 kW import limit binds)" and "Deliverable energy used (import-limited): 56.23%".
  - Demand and capacity and `#/decision/ruiru-expansion` use the same 3,200 kWh and 61% wording. The two definitions no longer contradict each other.
- **Residue:** the CSV unit text is stale (R7-L2).

**N-M2: resolved on the rev 6 surfaces. The residue is Low (R7-L1).**
- **How I checked.** I ran my own scan in headless Chromium:
  - all 119 Added, Changed and Merged routes × 3 operators, plus the four Lakeside Act-first switch cases;
  - every `.ev-num` drawer opened on each (337 figure hits, 0 drawer errors);
  - a wider figure list than the author's: the rev 7 list plus 262.50, 250.50, 2,286, 2,166, 3,744, 160 L, 120 L, 3 days, 225 kWh, 95,484, 8,082, 13,356 and 406 kW.
- **What is now labelled:**
  - **Lakeside Overview:** the Optimize card factor line and "Sites that look alike" (210 L and $2,916), and the hero plan figure.
  - **Act first, all four cases** (5,000/yes, 5,000/no, 6,500/yes, 6,500/no): 65 hits, **0 unlabelled**. That covers the path cards (retitled), the four-case table, the plan rows, the totals and the downside line with +$5,670 and +$5,346.
  - **Decision pages:** the Mto inverter banner now names the Kobo stop-setting replay and the huller replay. Mto demand ($395, $3,540, 68 L) is labelled, and so is every Kobo option row.
  - **Drawers:** all three plan-value drawers carry the right label. Harvest carries the assumption wording, and its source line reads "Option valuations from the repair quote, the recovery assumption and the draft contract terms".
- **What the audit does not cover.** The widened scan does not cover what A20 promises, because it is circular:
  - `tools/audit.mjs:30` (`DV_SCAN`) and the tagger `loop-core.js:274` (`REPLAY_RE`) use the same hand-written list of literals. The tagger labels exactly what the audit then checks, so "0 unlabelled" can only mean "the tagger ran".
  - A replay-derived value missing from the list (for example 250.50 or 2,286) is neither tagged nor detected.
  - A20 promises "every figure resting on a replay, and every value computed from one … wherever it appears". The audit tests a subset that the author chose.
  - The author's response also says the scan covers only the default switch state. My scan of the other three cases found them labelled.
  - See R7-L1 for what slips through.

**N-L1: resolved.** Contracts l.457 reads "R3a, P4, A5, S12". There are no `@@` markers in any pack file except REVIEW.md, where they appear only as the quoted finding.

**N-L2: resolved.**
- My recomputation:
  - stop setting at diesel 1.00: (210 × 1.00 − 12) × 12 − 90 = **2,286.00**;
  - huller: (495 − 68 × 1.00 − 15) × 12 − 1,200 = 412 × 12 − 1,200 = **3,744.00**;
  - plan: 2,286 + 3,744 − 360 = **+5,670.00** ✓.
- Feasible fuel 160 L: (160 × 1.25 − 12) × 12 − 90 = 2,166, and 2,166 + 3,540 − 360 = **+5,346.00** ✓. Applying this one to the Kobo option only is correct, because only that option has a feasible-fuel uncertainty.
- The checker recomputes +5,670 from the option economics (`check_manifest.py`, "diesel -20% applied to the whole plan").
- Updated in the manifest, models §6.4, the main document, R14 and the screen.
- **Residue:** the generated change register still says +$5,466 (R7-L2).

**N-L3: resolved.**
- The path cards read "Modelled 12-month change from the valued options".
- The Lakeside drawer no longer duplicates the "Net of …" sentence.
- The Harvest drawer uses "Assumption: Kirinyaga recovery share 80%, range 60–90%; no replay is involved" and no longer says "forward replay".
- A trivial residue: the Harvest and Metro drawers still read "Net of the valued options' own one-off costs. From the valued options: … net of their own costs ($620)". The point is made twice in one paragraph. This is cosmetic and not a finding.

**N-L4: resolved.**
- The measure is renamed "departures met per installed charger" (1,302 / 26 = 50.08), with the charger-day basis 1,302 / 25.16 = 51.75 in its note (26 − 26/31 = 25.161).
- The asset lists are declared, with a counting rule: Kobo 5 (PV, inverter, battery, PCS, generator), Kisiwa 4, Mto 5.
- My recomputation: (5 × 31) + (4 × 31 − 2) + (5 × 31 − 4) = 155 + 122 + 151 = **428**, and 155 + 124 + 155 = **434**. 428 / 434 = 0.98618, so **98.62%** ✓.
- Shown on Outcomes by site (portfolio 98.62%, Kisiwa 98.39%), and in models §3.13 and the main document.
- **Residue:** contracts §2.7 l.173 prints "428 / **403**" (R7-L2).

**N-L5: not re-checked as a finding.** The rev 6 screenshot renames are committed in `fcc2ec049`.

### Coordinator points (owner-requested)

**CP-1 · Medium · The structural alternative to six parallel tabs was not considered on the record.**
- **Point:** the tab review mostly confirmed what was there.
- **Disposition:** upheld, as a decision-record and owner-choice gap, not as a defect in the chosen structure.
- **What the pack does:**
  - Main §6.1(1) states "The loop is the information architecture … The Portfolio's sections follow Observe → Evaluate/Choose → Prove".
  - §6.1(2) then fixes the frame first: "Keep the product's navigation … The Portfolio keeps six tabs, judged one by one against the loop".
  - The §6.2 table judges each existing tab (keep / rename / reorder). It never weighs a different frame, such as a single sequential Portfolio page (what is happening → why → the plan → proof, with coverage alongside), or fewer, staged sections.
  - I searched the pack for any consideration of a sequential or single-page alternative and found none.
  - Q2 offers the owner only "(a) as proposed; (b) keep the old order and names". Both are tab variants.
- **What the owner asked for:**
  - The owner asked to "review the overall current portfolio experience and structure it in a way those requirements are met" (direction file, message 2).
  - The owner criticised reuse that "did not establish the core future mechanics, and then decided what to reuse" (message 6).
  - "No … new menu items" does not by itself require keeping six peer tabs. Tabs that follow the loop sequentially could be one structure that meets it, but the pack never argues the point.
- **What already exists:** the Overview's first fold (headline → four figures → the plan's first three moves) is already a sequential reading of the loop. A fair case for tabs exists: deep views stay reachable, and the live product already has the frame. It is just not written down.
- **Why it matters:** the owner's central complaint across messages 1, 2 and 6 is narrowness: keeping today's form and re-filling it. This is the one structural UI choice where the pack kept the form without arguing against an alternative.
- **Fix (documents only):**
  - add a short considered-alternatives paragraph to §6.2: tabs, against one sequential Portfolio page, against a staged Overview with tabs as drill-downs. Judge each against the loop, the four concerns and demo flow, and record why the choice wins;
  - add the sequential option as Q2 (c), so the owner decides between real alternatives.
  - No mock-up rebuild is needed unless the owner picks (c).

**CP-2 · Medium · Mechanic 3 says the structure shows each option's effect, but decision pages show Protect only as bound pass/fail.**
- **Disposition:** upheld as a derivation gap.
- **What the pack promises:**
  - Main §2.3 (Mechanic 3) is headed "options change factors; the structure shows the effect".
  - §6.2 says "A decision page … shows each option's counterfactual structure."
  - Since rev 5, Protect is a declared structure of measured factors (A15; manifest `portfolio.protect`).
- **What the pack delivers:**
  - Only the money structure has a counterfactual per option.
  - The manifest holds no per-option Protect values. The author response (rev 6, l.100 and l.211) says "Decision pages show the per-option bound checks, not a per-option Protect value table, because the manifest holds no per-option Protect values."
  - In the browser, `#/decision/kobo-generator` shows a bound row ("Battery at least 35% at 5 am: held on 61 of 61 days / broken on 4 of 61"), not the change in unserved critical kWh or obligation-hours per option.
- **Why the gap matters:**
  - The plan spends money on options whose only value is on Protect: Kisiwa repair 1,800 (must-do), Kobo battery evidence 430 (protective), Thika night cover 100 and Kasarani stopgap 90.
  - Identity M4 (main l.170) explicitly counts "spend on options valued only on Protect measures".
  - Yet their effect is asserted in prose, never computed through the structure. Examples: "evening obligation-hours without redundancy back to 0" (main l.447) and "their effect is on Protect measures" (Act-first total).
  - So the Protect structure is built for Observe but not used in Evaluate. Read upward, a must-do option cannot show the Protect measure it moves.
- **Fix (either):**
  - **Preferred, cheap in the manifest:** declare per-option Protect deltas for the options that carry Protect value, at least KIS-REPAIR, BAT-EVIDENCE, THIKA-EPC-STOPGAP, KAS-OEM-STOPGAP and the rejected no-action rows. Have the checker compose them, and show a "Protect measures under each option" row on those decision pages.
  - **Or:** narrow §2.3 and §6.2 to say that Protect enters Evaluate only as bounds, and record that as a decision with the brief's justification. I would not recommend this: it contradicts the rev 5 H1 resolution's intent.

**CP-3 · Medium · The replay calibration plan covers only Kobo and is not prioritised ahead of client use.**
- **Disposition:** upheld, partly as a plan defect and partly as an owner prioritisation call.
- **What the pack does:**
  - It labels the design values honestly, and I verified the labels.
  - Its plan to compute them is the "Spike before slice 4" (phase plan l.113–117), a gate on slice 4. Slice 4 follows slices 1–3 (UI exposure, the commercial store, the structure registry).
  - RR1 (decisions l.52) says the check comes "before 210 L is used client-facing". No slice, gate or rule enforces that. The mock-up and the demo story lead with 210 L and +$6,096, and nothing in the plan stops a client from seeing them first.
- **Scope gap:**
  - The spike replays Kobo only ("Replay observed PV-available and load for the existing Kobo demo data").
  - Yet its exit claims to replace "(210 L, 20 L, 68 L)", and 68 L is the Mto huller's demand-on-headroom replay at another site.
  - R13 also ties Embakasi's 31 of 31 nights to "until the replay calibration spike passes". No spike or slice ever calibrates the Embakasi schedule replay; PR 4e builds Mto's, and slice 8 builds EV's, with no calibration step.
  - So the Mto and Embakasi labels have no exit.
- **Priority:** the spike is read-only on existing Kobo demo data (`host/execution_adapter.py:869`). It depends on none of slices 1–3, so it can run first, in parallel. Gating it behind slice 3 delays the evidence for the strongest demo claim without reason.
- **Fix (documents):**
  - make the spike the first item of the build lane, read-only and in parallel with slice 1;
  - extend it to, or add matching spikes for, the Mto huller headroom replay and the Embakasi schedule replay, each with its own exit;
  - correct the exit text so the Kobo spike replaces only Kobo figures;
  - add an explicit rule to the plan and to Q5 / client-demo strategy: no client sees replay-derived figures until their spike has passed, or they are shown with the label and the presenter says so.
- **Owner decision:** whether "labelled" is enough for an early prospect demo. Put it to the owner in the questions table.

**CP-4 · Diminishing returns: is another author round needed?**
- **Disposition:** agreed in part.
- The numeric and label findings have converged. N-M1 and N-M2 are closed, and the rev 7 Lows (R7-L1, R7-L2) are small residues that need no full round.
- CP-1 to CP-3 are not polish. They are design-reasoning and plan gaps, and each is fixed in the documents in one short round:
  - CP-1: a paragraph and a Q2 option;
  - CP-2: manifest Protect deltas and one decision-page row, or a recorded narrowing;
  - CP-3: a phase-plan reorder and scope, and an exit rule.
- After that round, everything left is an owner decision: Q1–Q12, the new Q2 (c), and the client-exposure rule from CP-3.
- I recommend that the next re-review be limited to those three items and not reopen settled arithmetic.

**CP-5 · Low · Navigability: there is no short guided path for the owner's review.**
- **Disposition:** upheld at Low.
- **How large the pack is:**
  - The main document is 640 lines, with ten companion artefacts (5,774 lines of Markdown in all) and 184 screens.
  - `interactive-mockup-vNEXT/owner-inspection-checklist.md` exists (25 rows). It has grown as a log of revisions (rows 16–25 are labelled "Rev 5/6/7"), not a path.
  - `walkthroughs.md` (46 lines) is a timed presenter script, not a review guide.
- **Stale headers:** the main document and the decisions file both still say "rev 4 (redesign)" (l.3). The pack index says REVIEW.md holds the "History of rev 1–3 reviews; kept unchanged", but it now holds rev 1–7.
- **Fix:** a one-page "owner review in 30 minutes" at the top of the checklist or the main document. It would cover:
  - the five mechanics (§2, one paragraph each);
  - the decisions that need the owner (Q1, Q2, Q3, Q5, Q7, Q9, and the CP-3 rule), each with the one screen to open;
  - one operator walk (Lakeside: Overview → Outcomes by site → Act first switches → Kobo decision → What changed);
  - one cross-vertical contrast (Metro Ruiru, Harvest Thika).

  Then refresh the rev labels. This is needed for an efficient owner gate, but it does not block.

### New findings (rev 7)

**R7-L1 · Low · A20's "every occurrence" still misses replay-derived values that are not on the tagger's hand list.** In the browser:
- **Lakeside, `#/portfolio/what-changed`:** the commitment row "Kobo: stop the generator at 70% battery … +$250.50 a month" is unlabelled, while the huller row in the same table is labelled. 250.50 = 210 L × 1.25 − 12, a replay value.
- **`#/decision/kobo-generator` sensitivity lines:**
  - "Diesel 20% cheaper: $2,286 over 12 months; ranking unchanged."
  - "Only 160 L a month proves avoidable: $2,166 over 12 months; still first."

  These sensitivities are named in A20. The page banner lists only "the 210 L and 20 L avoided, the 61 of 61 and 4 of 61 replayed days, and the $2,916", so neither line is labelled.
- **Metro `#/portfolio/what-changed`:** "Embakasi … $8,082 a month below no action". The Embakasi schedule value is treated as a design value elsewhere (the Act-first row, the decision option row, the plan drawer).
- **Metro Overview "Sites that look alike":** Embakasi bill figures, unlabelled.
- **The plan value itself:** $95,484 is labelled in its drawer and on Act first. On the Overview hero it carries the plain-text note "includes design values not yet run on site data", as accepted at rev 6.
- **Cause:** both `REPLAY_RE` (`loop-core.js:274`) and `DV_SCAN` (`tools/audit.mjs:30`) are the same literal list, so the audit cannot find an omission.
- **Fix:** derive the replay-dependent value set from the manifest (options carrying `forward_replay` or `replay`, their economics, sensitivities and the allocation values built from them) in `gen_fixtures.py`, and use it for both the tagger and an independent audit. Or, at minimum, add 250.50, 2,286, 2,166, 8,082 and 13,356 and tag the two Kobo sensitivity lines.
- It is Low because every headline and plan surface is labelled. It should still be fixed before the audit's "0 unlabelled" is cited as R13 evidence.

**R7-L2 · Low · Stale residues from the rev 7 edits.**
- `economic-metric-and-effect-contracts.md:173` prints "(155 + 122 + 151) / (155 + 124 + 155) = 428 / **403** = 98.62%". It should read 434.
- `interactive-mockup-vNEXT/CHANGE-REGISTER.md:288` and its generator `tools/gen_docs.cjs:116` still read "diesel 20% cheaper +$5,466". It should read +$5,670.
- `outcome-lever-capability-traceability.csv` row T0438 describes `deliverable_energy_used` as "share of deliverable charger energy in the usable window", the pre-rev 7 unit. It should say "share of deliverable energy a night (import-limited)".
- The main document and decisions headers say "rev 4"; see CP-5.

### Regression checks

- **`python3 check_manifest.py`:** 222 checks passed, 0 failed. The new checks are the import-limited denominators per depot, Ruiru against RUI-ABSORB6, and diesel −20% on the whole plan.
- **Rebuild in a scratch copy:** `tools/rebase_v70.py`, `tools/gen_fixtures.py` (sha 00d50e72bfc1), `node build.mjs` and `node tools/gen_docs.cjs`. `index.html`, `fixtures.js`, `screens.js`, `portfolio.js`, `outcomes.js`, `mockups.css`, `CHANGE-REGISTER.md` and `browser-audit.md` are **byte-identical** to the working tree, and no other modified file differs.
- **The 65 Preserved v7.0 screens:**
  - `git diff fcc2ec049` shows no change under `frontend/mockups/v70`, `src-v70-baseline/`, `tools/rebase_v70.py`, `screens.js`, `portfolio.js` or `outcomes.js`.
  - In the browser, 0 of the 65 Preserved screens carry a `.dv` tag for any of the 3 operators. The new post-render tagger does not touch them.
  - Comparing `.canvas` text with `frontend/mockups/v70/index.html` served separately: 21 are raw-identical. In the other 44, every differing token is a re-basing display name (GreenHarvest→Thika, Charging Hub→Ruiru/depot, MG→KOBO, DEMO-01→001 or THIKA, Cold Room→cold room), which matches the rev 6 finding of 65 of 65 after the name map.
- **Owner expectations:**
  - `loop-*.js` contain no CEO/COO/CFO/CCO strings.
  - The author's audit (`tools/audit-results.json`) reports 0 role or question hits, 0 filter controls and 0 operator selectors in the top bar on 202 routes. My route walk saw the same tab row and no filter chips. Rev 7 adds no menus, filters or role wording.
  - The new EV measure is built from the structure's own `deliverable_kwh_per_night` stage, and the asset counts come from a declared list and rule. Both are factor-built, not detected at the top.
- **Browser walk:** headless Chromium 1155, served statically on 127.0.0.1:18773 (the pack) and 18774 (v7.0); 5490 and 8990 were not touched. 119 non-Preserved routes × 3 operators, plus the four switch cases, with every drawer opened: 0 drawer errors. Both servers were stopped, and the ports are free.

### Not verified

- I did not rerun `tools/run-audit.sh`, so its contrast, focus, 390 px overflow and screenshot outputs are the author's numbers, not mine. My checks ran at 1440 px only.
- The replay design values themselves (CP-3).
- The rendered mermaid in `layer4-transformation-design.html`.
