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

## Re-review (rev 8)

**Reviewer:** a fresh, independent Claude reviewer, 17 Nov 2026. I reviewed the rev 8 working tree on `task/product-direction-layer4-design` (uncommitted over `f513cd9c1`, including the untracked `interactive-mockup-vNEXT/tools/replay_values.py`). I judged it only against the rev 7 points (CP-1, CP-2, CP-3, CP-5, R7-L1, R7-L2) and the regression list, and did not reopen settled arithmetic. This appended section is my only edit.

### Verdict: **REVISE (targeted: CP-2 only, manifest + text)**

- CP-1, CP-3, CP-5, R7-L1 and R7-L2 are resolved. The Lows below are notes, not blockers.
- CP-2 is **partly resolved**. Four of the six declared Protect effects reconcile with the option rows. Two defects remain, both at Medium:
  - **R8-M1:** the Kisiwa effect (150 → 15), which is the figure that justifies the $1,800 must-do on Act first, uses a restore date (4 Nov) that is earlier than the scenario's own `as_of` (6 Nov).
  - **R8-M2:** the Mto inverter decision does change a declared Protect measure, contrary to the "other eight leave Protect unchanged" claim. It is the plan's decisive claim-versus-buy switch, and its Protect effect is not shown.
- Both are small fixes in the manifest and the generated text. No redesign is needed. After this fix the pack can go to the owner without another full review; a spot check of the two rows is enough.

### Findings

**R8-M1 · Medium · The Kisiwa Protect effect contradicts the scenario date, and the checker only checks the effect against itself.**
- **Evidence:**
  - `demo-site-scenario-manifest.yaml:25` sets `as_of: "2026-11-06"`, which is the demo "today" and the date the plan is chosen.
  - `protect_effects` for Kisiwa (l.292–297) says "repair restores on 4 Nov (3 evenings)" → 15 h, and "replacement lead time 21 days (21 evenings)" → 105 h.
  - Neither date is in the option rows. `KIS-REPAIR` (l.193) has no restore date. `KIS-REPLACE` (l.195) has no lead time; the only 21-day lead time in the file is Mto's inverter warranty (l.276).
  - A repair chosen on 6 Nov cannot restore on 4 Nov. November 1–6 evenings ran on one generator under every option.
  - The other horizons in the same block start correctly at the decision: Kasarani "6/7, 7/8 and 8/9 Nov" and Thika "6/7 and 7/8 Nov".
  - `check_manifest.py` hard-codes `KIS-REPAIR == 15` and `KIS-NOACT == 150`. It does not derive these from `as_of` or from any option field, and it does not check 105 at all. "Reconciled with the option rows" therefore does not hold for Kisiwa.
- **On screen:**
  - Act first (Lakeside) reads "Kisiwa repair, obligation hours without a backup, november, 150 → 15".
  - `#/decision/kisiwa-genset` shows 15 / 105 / 150 with the 4 Nov basis.
- **Why it matters:**
  - This is the one computed effect that now carries the $1,800 must-do. CP-2 asked for it to be computed, not asserted, and the 4 Nov restore is asserted.
  - The owner will read this line on the Act-first walk in the 30-minute path.
- **Fix:**
  - declare a restore date on `KIS-REPAIR` and a lead time on `KIS-REPLACE` in the option rows;
  - count evenings from `as_of`, for example "from the evening of 6 Nov to 30 Nov", or count the whole of November with 1–6 Nov shown as observed under every option;
  - have the checker derive the hours from those fields;
  - regenerate the Act-first line, and capitalise "November" while doing so.

**R8-M2 · Medium · The Mto inverter options change a declared Protect measure, but no effect is declared or shown, and the "leave Protect unchanged" limit is incorrect.**
- **Evidence:**
  - `portfolio.protect.obligation_hours_without_redundancy` (manifest l.335–337) is defined as "hours in which an obligation's supply rested on a single unit **or reduced capacity**". It already counts Mto's "28–31 Oct, 10:00–15:00 daytime supply at half inverter capacity" as 20 h, which is 4 days × 5 h.
  - On the same basis, the November figure depends on the inverter option:

    | Option | Restore date | Days at half capacity | Hours (× 5 h) |
    |---|---|---|---|
    | `MTO-INV-CLAIM` | 28 Nov | Nov 1–27, 27 days | **135 h** |
    | `MTO-INV-BUYNOW` | 12 Nov | 11 days | **55 h** |
    | `MTO-INV-NOACT` | never | 30 days | **150 h** |

  - The rev 7 CP-2 fix listed "the rejected no-action rows". `MTO-INV-NOACT`'s own rejection reason is a Protect consequence: "half daytime capacity indefinitely".
  - The author response (rev 8, CP-2 "Limit") and `CHANGE-REGISTER.md` §7 item 9 say the other eight decisions' "options leave Protect measures unchanged". That is not true for this decision.
- **In the browser:**
  - `#/decision/mto-inverter` has no "Protect measures under each option" section.
  - Lakeside Act first names only Kisiwa (150 → 15) and the battery evidence (1 of 3 → 2 of 3). The recommended plan keeps claim-and-wait and its 135 h of reduced-capacity daytime supply, and nothing on the plan says so.
- **Why it matters:**
  - This is the plan's decisive switch (budget $6,500 with no letter-of-intent extension → buy now). It is decided on money alone, while one side carries a Protect advantage of about 80 h.
  - Mechanic 3 promises that the structure shows each option's effect. A reader who goes upward from the Protect card to the plan sees the Kisiwa hours fixed and not the Mto hours left open.
- **Fix:**
  - add a `protect_effects` entry for the Mto inverter (CLAIM, BUYNOW, LOCAL if evaluable, NOACT) on the declared measure, with restore dates taken from the option rows, and have the checker derive it;
  - show it on the decision page and in the switch-case explanation on Act first;
  - correct the "unchanged" sentence in the response text and in the change register.
- **Other decisions:** I checked the remaining seven and found no comparable gap. Ruiru +10 is rejected by a bound, so it is acceptable as a bound check.

**R8-L1 · Low · Two of the six effects are stated on measures outside the declared Protect structure.**
- **Thika** uses "nights with stock present and no backup start cover". That is not a declared measure; the declared one is `days_backup_start_unproven`, l.519. The night rota does not prove an automatic start, so the declared measure would not move under the stopgap at all.
- **Kobo stop setting** uses the MG5 bound count ("days below 35% at 5 am") rather than `unserved_critical_kwh`. The label is honest ("the bound that keeps unserved critical kWh at 0").
- **Fix:** either declare the Thika measure in `portfolio.protect` with its composition, or state in models §4.7 that an effect may be shown on the bound's own quantity, and say why.

**R8-L2 · Low · The spike lists in CP-3 and the replay-figure rule in R7-L1 do not quite agree with each other.**
- **Spikes K, M and E** (phase plan, calibration lane) omit some replay-derived figures that the screen labels:
  - K: $262.50 (the gross) and the 150 kWh throughput behind the $12 wear;
  - M: 225 kWh and $85;
  - E: $13,356, and 406 kW from the replay string.
- **The derived set** (`gen_fixtures.py` and `replay_values.py`) has the opposite gaps. It omits 2,900 kWh and 406 kW, which spike E names or derives.
- **It also over-labels:**
  - $495, the huller's revenue, which does not depend on the replay;
  - Embakasi no-action "0 departures missed", which is October as observed (620 of 620).
- **The one unlabelled replay figure I found:** "A 21-bus night needs about 406 kW: inside the 500 kW limit, above the 400 kW plan" on `#/decision/embakasi-schedule`. The page banner names only "schedule feasibility on 31 of 31 October nights and the deliverable energy a night".
- **Fix:**
  - make the three spike tables the enumeration;
  - have the rule (or a checker assertion) prove that the derived set equals the union of the spike lists plus the plan values;
  - tag the 406 kW sentence.

**R8-L3 · Low · Labels and residues.**
- **Option letters:** the frame letters differ between §6.2 and Q2. §6.2's chosen frame is (c) and its sequential page is (b); in Q2 these are (b) and (c). The text maps them ("Frame (b) is offered to the owner as Q2 (c)"), but an owner answering "(c)" could mean either. Use the same letters in both places.
- **Row order:** Q13 sits between Q11 and Q12, and A21 and A22 come before A12.
- **RR1:** the mitigation still reads "the replay slice starts with a calibration check". It should point to the calibration lane (A21).
- **Rev headers:** `domain-and-decision-models.md`, `economic-metric-and-effect-contracts.md`, `integration-source-to-canonical-design.md` and `demo-build-cost-plan.md` still say "rev 4 (redesign)". Two of them changed in rev 8.
- **Act-first wording:** "until a capacity claim is needed, 1 of 3 → 2 of 3" reads awkwardly on the plan line.

### Resolution of the rev 7 points

**CP-1: resolved.**
- §6.2 now weighs three frames against the loop, the four concerns and the demo flow, with points for and against each, and Q2 offers the owner real alternatives, including the one-page frame.
- The comparison is not a strawman, though the choice that matters is tabs against one page. Frames (a) and (c) differ mainly in loop order and the staged Overview, which already exists.
- The page-length argument holds. I measured the Overview's scroll height:

  | Operator | Desktop, 1440 px | Phone, 390 px |
  |---|---|---|
  | Lakeside | 2,237 px | 4,616 px |
  | Harvest | 1,897 px | 4,097 px |
  | Metro | 2,110 px | 4,572 px |

  The claim was "about 2,000 and 4,300", which is fair.
- One inconsistency remains: the option letters (R8-L3).

**CP-2: partly resolved (R8-M1, R8-M2, R8-L1).**
- **Hand recomputation.** These reconcile with their option rows:
  - Kasarani: 2 missed × $120 = $240, which equals `KAS-OEM-WAIT.expected_penalties`. Over the 3 nights, the spare bus covers one, so 2 are missed.
  - Embakasi: 3 short × 31 = 93, which equals `EMB-CHEAPEST.buses_short` × 31.
  - Kobo reserve: 4, which equals `forward_replay.soc_0500_below_35_days`.
  - Battery evidence: 1 of 3 → 2 of 3. That agrees with `tracked_assets_with_complete_contract_evidence`, where only `INV-MT-02` is complete.
  - Thika: 2 → 0 over nights 6/7 and 7/8.
  - Kisiwa: the 5 h per evening is right, but the dates are not (R8-M1).
- **On screen** (headless Chromium, 1440 px). All six decision pages carry "Protect measures under each option" with horizon, basis and evidence class. The Kobo and Embakasi rows carry the design-value label. Act first shows the moved measure for every operator:
  - Lakeside: Kisiwa 150 → 15 and evidence 1 of 3 → 2 of 3;
  - Harvest: Thika 2 → 0;
  - Metro: Kasarani 2 → 0, penalties $240 → $0.
- **Lakeside $2,230:** $1,800 + $430 is now tied to computed effects, but the Kisiwa half rests on the date error in R8-M1.
- **The eight decisions without a declared effect:** acceptable for seven of them. The exception is the Mto inverter (R8-M2).

**CP-3: resolved in structure; the figure mapping has small gaps (R8-L2).**
- **Where the lane sits:** it is slice 0 in main §9, runs first in parallel with slice 1, and gates S4, S8 and client demos in the phase-plan graph.
- **Each spike has its own exit**, and each replaces only its own figures. R13 is tied to K, M and E. The sizing and readiness rows are updated.
- **The client-exposure rule and Q13 are sound:**
  - the two options are distinct and real (labelled and said aloud, or hidden until the spike passes);
  - the Architect's split (a for early prospects, b for any evidence-of-results demo) is reasoned;
  - the audit enforces the label that option (a) relies on.
- **Remaining issue:** RR1's wording is stale (R8-L3).

**CP-5: resolved.**
- "Owner review in 30 minutes" opens `owner-inspection-checklist.md`, and the main document links to it.
- Every route it names exists in `screen-manifest-vnext.json` and renders: `#/portfolio`, outcomes-by-site, act-first, demand-and-capacity, what-changed, `#/decision/kobo-generator`, kasarani-charger, embakasi-schedule, `#/site/thika` and `#/ev-health`.
- The Lakeside walk includes the switch case and the new Protect section.
- **Note:** the decisions table omits Q4, Q6, Q8, Q10, Q11 and Q12, although each is marked "owner input: Yes". A line saying "the rest are in the decisions file" would stop the owner from reading this table as complete.

**R7-L1: resolved as asked, with a limit on how independent the audit is.**
- **What is now independent:** `tools/audit.mjs:15` builds its set from `tools/replay_values.py`, which reads the YAML directly, not `fixtures.js` and not `REPLAY_PATTERNS`. The tagger (`loop-core.js:274`) uses the set from `gen_fixtures.py`. The hand list is gone.
- **What is not:** `replay_values.py` is a second implementation of the same rule, with the same keys, the same thresholds and the same carve-outs. It will catch a tagger or render miss, but not an omission in the rule. 2,900 kWh and 406 kW escape both (R8-L2). "0 unlabelled" means every figure the rule enumerates is labelled.
- **My own scan:**
  - Coverage:
    - a separate, hand-built list of 32 patterns, including 120 L, 150 kWh, 2,900 kWh, 406 kW, $3,744, $381 and "3 days";
    - all 119 non-Preserved routes, scanned for all three operators where the audit does the same;
    - every switch state: Lakeside 5,000 and 6,500 with yes and no, Harvest aggregator yes and no, Metro tariff yes and no;
    - 769 drawers opened.
  - Result: 183 occurrences, all replay-derived occurrences labelled, except the 406 kW sentence.
  - The other 48 unlabelled hits were all observed figures, correctly unlabelled:
    - the 120 L fuel residual;
    - Kisiwa's 20 L residual and Mto's 20 L of needed running;
    - 93.3% connector availability;
    - "3 days left" on the SLA clock.

**R7-L2: resolved.**
- Contracts l.173 reads 428 / 434.
- `gen_docs.cjs` gives +$5,670. I found no "5,466" anywhere in the pack.
- CSV T0438 reads "share of deliverable energy a night (import-limited)".
- The main document and decisions headers say rev 8, and the pack index says rev 1–7. The companion headers remain (R8-L3).

### Regression checks

- **`python3 check_manifest.py`:** 236 checks passed, 0 failed.
- **Rebuild in a scratch copy** (`rebase_v70.py`, `gen_fixtures.py`, `node build.mjs`, `node tools/gen_docs.cjs`):
  - 25 replay patterns, fixtures sha `41b935209449`;
  - every non-screenshot file in the pack is **byte-identical** to the working tree.
- **The 65 Preserved v7.0 screens:**
  - `git diff f513cd9c1` is empty for `frontend/mockups/v70`, `src-v70-baseline/`, `tools/rebase_v70.py`, `screens.js`, `portfolio.js`, `outcomes.js` and `mockups.css`;
  - in the browser, 0 `.dv` tags on the 65 Preserved routes for all three operators;
  - the manifest counts Added 74, Changed 36, Merged 9 and Preserved 65.
- **Owner expectations:**
  - **Role and question wording:** no CEO, COO, CFO or CCO in any non-Preserved route or in the rev 8 diff of `loop-*.js`. The only "?" line endings are v7.0 "Why?" links and a v7.0 finding title on Changed screens, both unchanged since v7.0.
  - **Filters and menus:** no chips or selects on any Portfolio route, and no new menu.
  - **Factors observed upward:** the Protect effects are carried on the decision's structure measures, with the exceptions in R8-L1.
  - **All three verticals:** effects are declared for each, and Act first shows them for each operator.
- **Browser:** headless Chromium 1155, served statically on 127.0.0.1:18891 (not 5490 or 8990), with 0 page errors. The server was stopped and the port is free.

### Not verified

- I did not rerun `tools/run-audit.sh`, so the contrast, focus, 390 px overflow and screenshot results are the author's numbers. My only 390 px check was the Overview heights above.
- The replay design values themselves; that is the purpose of the calibration lane.
- The rendered mermaid in `layer4-transformation-design.html`.

## Re-review (rev 9)

**Reviewer:** a fresh, independent Claude reviewer, 17 Nov 2026. I reviewed the rev 9 working tree on `task/product-direction-layer4-design`: the uncommitted diff over `4393c19b3`, plus the untracked `evaluate_structure.py` and `derived-values.json`. The main focus is the owner-requested structural check (owner, ninth message: "the structural aspect of mechanics are still very important even in the document illustration"). I also verified R8-M1, R8-M2 and R8-L1 to R8-L3, and ran the regression list. I ran the perturbation experiments in scratch copies only. This appended section is my only edit.

### Verdict: **REVISE (targeted: structural derivation, R9-M1 to R9-M4)**

- **R8-M1 and R8-M2 are resolved**, and so are R8-L1 to R8-L3. I recomputed the hours by hand and they match. Counting from the decision date (6 Nov) is the right choice.
- **The core of the rev 9 change is genuine:**
  - `evaluate_structure.py` evaluates the manifest's `structures:` expressions over factors.
  - Option values are re-evaluations of the structure against no action.
  - Plans are chosen by enumerating subsets.
  - The mock-up overwrites the stated fields with the evaluator's output.
  - Every option value, plan, switch case and downside shown on screen comes from that evaluation.
- **But the structure does not yet prevent the R8 class of error.** Leaf factors still sit in three places that are not tied together:
  - constants in the evaluator's code;
  - a hand-entered second copy of each site's factors (`base_site_factors`);
  - hand-computed factor deltas.
- **The documents are not checked at all**, although the pack says they are.
- My perturbations show:
  - a change to a declared price or a base factor can move nothing, or move only half of what depends on it, while the checker still passes (325/325);
  - the R8-M2 pattern recurs on the money side of the same Mto inverter decision.
- These are Mediums, not Highs: no figure on screen is wrong today. They are what the owner asked about, so they block.

### Structural derivation (owner-requested)

**(a) Are the illustrative figures produced by evaluating the declared structure? Mostly yes for outputs; not yet for inputs.**

*Outputs: evaluated.*
- `evaluate()` (`evaluate_structure.py:33-50`) is a real bottom-up evaluator over the node expressions (+, −, ×) using AST.
- Each valued option is evaluated twice through the same vertical structure, once as no action and once with the option's factors changed. Its value is (v1 − v0) × months − one-off (l.103-115).
- Sensitivities re-run the evaluation with factors overridden.
- Plans are chosen by enumerating every subset under the budget, exclusivity and requirements (l.155-182), and the switch cases and downsides re-run that allocator.
- I re-ran the evaluator, and its output equals the committed `derived-values.json` exactly.
- `loop-decisions.js:34-53` (`applyDerived`) replaces the manifest's stated site outcomes, option values, sensitivities, Protect effects, plan values, switch cases and downsides with `DERIVED`.

*How much of each option's value is computed?* 12 options are evaluated.
- **10 get their monthly change from factor deltas run through the structure:** KOB-STOPSOC, KOB-RESERVE, MTO-HULLER, MTO-WELDING, KIS-BATT60, MWEA-AGG, KIRI-REPAIR, KIRI-REPLACE, EMB-DEADLINE and EMB-CHEAPEST.
- **2 are results entered as one-off amounts with no factor change:** MTO-INV-CLAIM (360) and MTO-INV-BUYNOW (2,910). See R9-M3.
- **Options outside the evaluator:**
  - priced only as costs, with their effect on Protect: the Kisiwa options, Thika, and Kasarani (penalty = missed × rate, in the checker);
  - checked against a bound: Ruiru;
  - reconciled only by older hard-coded checks: MTO-BILLING (56 = 140 × 0.40).

*Inputs: not all evaluated.* Many factor deltas are intermediate results computed by hand from parameters that sit on the option rows, and the evaluator never reads those parameters:

| Delta in the manifest | How it was computed by hand |
|---|---|
| KIRI-REPAIR −776 | 0.80 × 970 (`recovery_share`) |
| KIRI-REPAIR sensitivity −582 | 0.60 × 970 |
| KIRI-REPLACE −1,171.5 | 970 + 5% × 4,030 |
| MTO-HULLER 1,650 kWh | 15 kW × 5 h × 22 days |
| MTO-WELDING 660 kWh | 10 kW × 3 h × 22 days |
| MTO-WELDING 217.8 L | 660 × `sfc_l_per_kwh` 0.33 |

KIRI-REPLACE −1,171.5 is also more than the 970 kWh of excess that exists, so the "excess" factor goes negative: the efficiency gain is booked to the wrong leaf. Beyond the stated exceptions (Kobo dawn days, Embakasi's 93, the battery evidence count, and the spike K/M/E design values), these are hand-entered figures. So are the restore dates, apart from KIS-REPLACE (R9-L2).

**(b) Does the design prevent the R8-M1 and R8-M2 class of error structurally? Only partly.**

- **What it prevents:** a Protect effect can no longer disagree with its own restore date. The evaluator derives the effect, and the checker fails if the stated figure differs (P1 and P5 below).
- **What it does not prevent:** the same fact entered in two places with nothing tying them together. R8-M2 was a horizon that drove one figure and was missing from another. R9-M3 is that pattern again, on the money side of the same decision. R9-M2 shows that the factors used for observing a site and for evaluating its options are separate copies.

**(c) Does the checker derive figures, not only reconcile them? Yes for evaluator outputs; no for documents.**

- `check_manifest.py:derived()` imports the evaluator and asserts that each stated manifest figure equals the evaluated one. That part is genuine derivation.
- The Protect-date check (l.314-329) re-implements the evaluator's rule line for line, so it is not independent. I recomputed the hours by hand instead (below).
- The checker reads only the YAML (R9-M4).

**Uniform across the three verticals?**
- Option evaluation, Protect effects and the allocator are generic code.
- Observation is not generic (R9-M1):
  - the mini-grid branch reads prices from the manifest;
  - the cold-room and EV branches hard-code their leaf factors in Python;
  - three of the 18 site evaluations do not evaluate anything: Ruiru's plan and Kasarani's plan and actual pass the stated bill straight through.

**Do the document's illustrations and the drawers present figures as structure outputs?**
- **Drawers: yes.**
  - The Kobo stop-setting drawer reads "Contribution = revenue − cost to serve, evaluated with the option's factor changes against no action: (option $1,133.50 − no action $883 a month) × 12 − one-off $90 = +$2,916".
  - The plan drawer reads "Plan value = Σ of the valued options' changes against no action, each evaluated through the structure … +$2,916 + $3,540 − $360 = +$6,096".
- **Main document: as text only.** §2.3, §7 and §10 state the figures as literals, and nothing checks them (R9-M4).

**Perturbations** (scratch copy of the pack; evaluator and checker re-run each time; working tree untouched):

| # | Change | What moved | Checker |
|---|---|---|---|
| P1 | `KIS-REPAIR.restore_date` 9 → 10 Nov | Protect effect 15 → 20 | 2 FAIL (stated 15 ≠ 20). Caught. |
| P5 | `MTO-INV-CLAIM.restore_by` 28 → 29 Nov | Protect effect 110 → 115. The $360 residual, with its "extra fuel 130 during 21 days", did not move. | 2 FAIL on the Protect effect only |
| P2 | Kobo `prices.diesel_usd_per_l` 1.25 → 1.30 | The site outcome moved (883 → 824). KOB-STOPSOC stayed at 2,916, because it is valued at 210 L × 1.25 from `base_site_factors`. | 4 FAIL, all on site outcomes. The option value disagrees with the price and nothing catches it. |
| P3 | `base_site_factors` Kobo diesel price 1.25 → 1.30 | Option, plan, cases and downside all moved consistently | 10 FAIL. Caught. |
| P6 | `base_site_factors` Kobo `diesel_l` 1180 → 1200 | The no-action month no longer equals October | **325/325 pass** |
| P4 | Cold `prices.electricity_usd_per_kwh` 0.20 → 0.22 | **Nothing** | **325/325 pass** |
| P7 | Embakasi `demand_usd_per_kw_month` 12 → 13 | **Nothing** | **325/325 pass** |
| P8 | Kisiwa `crew_visit` 8 → 9 Nov (the visit now falls on the restore day) | Nothing | **325/325 pass** |
| P9 | KIRI-REPAIR `recovery_share` 0.80 → 0.70 | The evaluated value did not move (−776 is a literal) | 1 FAIL from a pre-rev-9 hard-coded reconciliation |
| P10 | Huller `days_per_month` 22 → 20 | Evaluated value did not move | 1 FAIL from a pre-rev-9 reconciliation |

Where a check catches a change (P9, P10), it catches it by reconciling figures, not by deriving them.

### Findings

**R9-M1 · Medium · The leaf factors used for observing cold-room and EV sites are constants in the evaluator's code, not declared factors.**
- **Evidence:**
  - `evaluate_structure.py:80-82` hard-codes `1550`, `0.25`, rate `0.20`, `contract_rate 0.18` and `elec_price 0.20`.
  - `evaluate_structure.py:91` hard-codes peak `0.24`, off-peak `0.12`, night `0.12` and demand `12`.
  - The manifest declares these at l.410 (cold prices) and l.576/643 (tariffs). The evaluator ignores them: P4 and P7 move nothing, and the checker passes.
  - The mini-grid branch does read `t["prices"]`, so the three verticals are not treated the same way.
  - l.93-96 is not an evaluation for a plan "stated as a bill total". The bill is used as kWh at $1 (Ruiru's plan) or divided and re-multiplied by the flat price (Kasarani's plan and actual). That passes 3 of the 18 site evaluations straight through.
- **Why it matters:** the owner asked that the illustration be produced by evaluating the declared structure. A declared price that changes nothing is exactly the gap between what is declared and what is computed.
- **Fix:**
  - map each vertical's record fields to factors through a declared table in the manifest, with prices and tariffs taken from the tenant or site blocks;
  - leave no numeric literals in the evaluator;
  - label the bill-total plans as "not decomposed: stated total" rather than counting them as evaluated.

**R9-M2 · Medium · Options are evaluated against a second, hand-entered copy of each site's factors, with hand-computed deltas.**
- **Evidence:**
  - `option_factor_changes.*.base_site_factors` (manifest l.796-821) repeats the prices, litres, kWh, O&M and staff already in `prices` and `period.actual`. No check ties the two together:
    - P2: the price moved and the option value did not;
    - P6: the base month drifted away from October and all 325 checks still passed.
  - The deltas in the table under (a) are hand arithmetic over option-row parameters (`recovery_share`, `load`, `sfc_l_per_kwh`) that the evaluator never reads.
  - KIRI-REPLACE's −1,171.5 drives the excess factor negative.
- **Why it matters:** this is the same kind of error as R8-M1 and R8-M2. A fact entered twice can drift, and it is caught only where a pre-rev-9 reconciliation check happens to exist.
- **Fix:**
  - build each option's base month from the site's observed factors (or from a declared no-action projection of them) instead of a copy;
  - express deltas as expressions over the option's own parameters, for example `excess_kwh: "-recovery_share * excess_kwh"`, `productive_kwh: "load.kw * 5 * load.days_per_month"` and `diesel_l: "kwh * sfc_l_per_kwh"`;
  - put the 5% efficiency gain on its own leaf (the model kWh), not on excess.

**R9-M3 · Medium · The money values of the Mto inverter options are entered by hand and contradict the restore horizon that now drives their Protect effect (R8-M2 recurring on the money side).**
- **Evidence:**
  - `MTO-INV-CLAIM.residual_cost` 360 is "shipping 150 + install 80 + extra fuel 130 during **21 days** at half inverter capacity" (manifest l.282). The restore date in the same row gives 22 days from the decision (6–27 Nov), and 31 days from the failure.
  - `MTO-INV-BUYNOW.residual_cost` 2,910 = 2,600 + 80 + 150 + 80. It has **no** fuel for its own 6 days at half capacity (6–11 Nov).
  - In `option_factor_changes` both options are `monthly_delta: {}`, `months: 0`, entered as one-off results. P5 moves the Protect hours, but not the fuel.
- **Why it matters:**
  - Mechanic 3 says an option is a change to factors over a horizon. Here the same horizon drives one figure and is ignored by the other.
  - At about $130/21 a day, buy-now's 6 days are worth about $35–40. That would move the switch-case value of $3,546 and the "wins if budget ≥ 6,430" threshold. It does not change any chosen plan.
- **Fix:**
  - model reduced capacity as a factor change (for example `diesel_l` per day at half capacity) over each option's own restore horizon, and derive the extra fuel for both paths;
  - let the evaluator produce both the residual costs and the threshold.

**R9-M4 · Medium · The documents' figures are not checked, although the pack says they are, and one has already drifted.**
- **Evidence:**
  - Main §10 (`layer4-transformation-design.md:599`) and the author response say that "`check_manifest.py` asserts that every figure stated in the manifest **and documents** equals the evaluated one". `check_manifest.py` opens only the YAML (l.428). No `.md` file is read.
  - The figures in §2.3 and §7 (125/15/105, 110/30, 6,096, 3,546, 2,556 and so on) are literals.
  - The manifest's `basis` strings are unchecked prose that the decision page shows: "6-8 Nov, 3 evenings", "22 days". After P1 the number reads 20 while the basis still says 3 evenings.
  - **Drift already present:** §7.2 (l.478) says the Thika stopgap's effect is "on *days with backup start unproven*". The R8-L1 fix moved that effect to `nights_without_backup_cover`, and the stopgap does not move `days_backup_start_unproven` (R8-L1's own reasoning).
  - `loop-portfolio.js:51-61` also writes observed figures into strings: "3,900 against 3,300", "−$412.50", "−$2,604", "$0.1221", "+$19.68".
- **Why it matters:** the owner named the document illustration explicitly. A check that covers the manifest but not the prose leaves the drift that rev 8 had in a new place.
- **Fix:** either
  - generate the figure-bearing sentences and tables of §2.3 and §7, and the manifest `basis` strings, from `derived-values.json`; or
  - add a checker pass that extracts the numbers from those sections and asserts them against `derived-values.json`.

  In both cases, correct §7.2 l.478 and change the §10 sentence to say what is actually checked.

**R9-L1 · Low · Rough edges in the Protect rule.**
- The rule string reads "× 1 h" for Thika (nights) and Kasarani (departures) in `derived-values.json`.
- `minus: {KAS-OEM-WAIT: 1}` is an ad hoc adjustment for the spare bus, not a factor (for example `spare_bus_nights: 1`).
- The horizon end `2026-11-30` is hard-coded in both the evaluator (l.135) and the checker, instead of being read from `horizon`.
- `as_of` is used as a "restore" sentinel for cover options that do not restore anything.

**R9-L2 · Low · Restore dates are inputs not tied to their drivers.**
- Only KIS-REPLACE is checked (restore = `as_of` + lead time).
- The 9 Nov KIS-REPAIR restore is not tied to the 8 Nov crew visit: P8 put the visit on the restore day and nothing failed.
- MTO-INV-CLAIM's 28 Nov is not tied to the warranty's `lead_time_days` 21 (6 Nov + 21 = 27 Nov, plus an install day not stated).
- BUYNOW's 12 Nov has no stated lead time.

**R9-L3 · Low · Stale header claims.**
- The companion headers still say "`check_manifest.py` 217 checks pass" and "(rev 4)/(rev 6)" for the manifest (models and contracts headers). The current count is 325.

### R8 points, verified by hand

**R8-M1: resolved.**
- `as_of` is 6 Nov, and evenings 6–30 Nov are 25:

  | Option | Restore | Evenings | Hours (× 5 h) |
  |---|---|---|---|
  | No action | — | 25 | **125** |
  | Repair (crew 8 Nov) | 9 Nov | 6, 7, 8 = 3 | **15** |
  | Replace (6 Nov + 21 days) | 27 Nov | 6–26 = 21 | **105** |

- 1–5 Nov (25 h) is shown separately as observed under every option.
- Rendered:
  - `#/decision/kisiwa-genset` shows 15 / 105 / 125 with the observed note;
  - Act first reads "6–30 Nov: 125 → 15 (plus 25 hours observed 1–5 Nov under every option)".

**R8-M2: resolved on the Protect side.**
- 6–30 Nov is 25 days:

  | Option | Restore | Days | Hours (× 5 h) |
  |---|---|---|---|
  | No action | — | 25 | **125** |
  | Claim | 28 Nov | 6–27 = 22 | **110** |
  | Buy now | 12 Nov | 6–11 = 6 | **30** |

- Local repair is shown as "not evaluated" with its reason.
- Rendered:
  - `#/decision/mto-inverter` has the section;
  - Act first reads "Reduced daytime capacity from 6 Nov: claim and wait 110 h, buy now 30 h (Protect; the switch itself is decided on money)".
- The CHANGE-REGISTER limit sentence is corrected.
- The money side is R9-M3.

**6 Nov rather than 1 Nov: sound.**
- An option cannot change hours before it is chosen.
- Counting from the decision date applies the same rule to all four date-derived effects.
- The difference between the paths (80 h) is the same under either start date.
- 1–5 Nov is disclosed as observed, so nothing is hidden.
- My rev 8 table (150/135/55, from 1 Nov) is superseded.

**R8-L1: resolved.**
- Thika's effect is on the declared `nights_without_backup_cover` (manifest l.537, rendered on `#/decision/thika-backup`).
- Models §4.7 explains why the Kobo effect is shown on its bound's own quantity.
- Residue: §7.2 l.478 (R9-M4).

**R8-L2: resolved.**
- `calibration_spikes` is now the enumeration.
- The checker asserts equality with `replay_values.py` (passes).
- The 406 kW sentence renders with "Design value: the replay has not yet been run on site data".

**R8-L3: resolved.**
- Frame letters (a)/(b)/(c) are the same in §6.2 and Q2.
- Q1–Q13 and A1–A23 are in order.
- RR1 points to spike K (A21).
- Revision headers say rev 9.
- The battery line is reworded.

### Regression checks

- **Checks:**
  - `python3 -B evaluate_structure.py`: 9 site outcomes, 12 options, 4 Protect effects, 3 plans. The output equals the committed `derived-values.json`.
  - `python3 -B check_manifest.py`: **325 passed, 0 failed**.
- **Rebuild in a scratch copy** (`evaluate_structure.py`, `rebase_v70.py`, `gen_fixtures.py`, `node build.mjs`, `node tools/gen_docs.cjs`):
  - "evaluator vs stated fields: 0 differences";
  - 27 replay patterns, fixtures sha `ff53eda1dd5c`;
  - `diff -rq` against the working tree, excluding screenshots: **byte-identical**.
- **The 65 Preserved v7.0 screens:**
  - `git diff 4393c19b3` is empty for `frontend/mockups/v70`, `src-v70-baseline/`, `tools/rebase_v70.py`, `screens.js`, `portfolio.js`, `outcomes.js` and `mockups.css`;
  - `src-v70-baseline` matches `frontend/mockups/v70` for every file it contains;
  - the screen manifest counts Added 74, Changed 36, Merged 9 and Preserved 65.
- **Owner expectations:**
  - **Role and question wording:** no CEO, COO, CFO or CCO, and no `<select>`, chip or menu, added in the rev 9 `loop-*.js` diff;
  - **Filters and menus:** no new menus;
  - **Mechanics:** built from factors and general in option evaluation, Protect and Choose. Observation is not yet general (R9-M1).
- **Browser:** served statically on 127.0.0.1:18897 (not 5490 or 8990) and checked with headless Chromium 1155 at 1440 px:
  - Lakeside Act first, `kisiwa-genset`, `mto-inverter`, `thika-backup`, `embakasi-schedule`;
  - the Kobo stop-setting and plan-value drawers;
  - 0 page errors; the one 404 was `/favicon.ico`.

  The server was stopped and the port is free.

### Not verified

- I did not rerun `tools/run-audit.sh`. The 202-route, 390 px, contrast, focus and the "936 views unchanged" figures are the author's numbers.
- I did not rerun the CSV validator.
- The replay design values themselves; they belong to the calibration lane.

## Re-review (rev 10)

**Reviewer:** a fresh, independent Claude reviewer, 17 Nov 2026. I reviewed the rev 10 working tree on `task/product-direction-layer4-design`, which is the uncommitted diff over `9398febb0`. The main focus is the coordinator's four points from the owner's eleventh message. I also verified R9-M1 to R9-M4 and R9-L1 to R9-L3, and ran the regression list. I ran every experiment in scratch copies of the folder. This appended section is my only edit.

### Verdict: **REVISE (targeted: H1, then M1 to M4)**

The rev 10 mechanism is a real step forward. The evaluator holds no prices of its own. All nine sites are observed bottom-up through `factor_map`, and all 24 options are evaluated against their references through the same structure. Rights now decide who pays for Mto and Kisiwa. Restore dates are derived from their drivers. Every figure I recomputed by hand is correct, and the claimed perturbations all reproduce.

However, coordinator points 1 and 4 are only partly resolved, and the author's table marks both "Fixed":

- The Protect measures observed for the period are not evaluated. The factor map pins those leaves to a literal `"0"`, so the evaluated nodes contradict the Protect figures the mock-up shows as "Calculated from records" (H1).
- Rights still decide nothing for Thika or Kasarani (M1).
- The new hard-limit rule is applied to a single EV measure only, and is tested relative to the reference (M2).
- Some causal steps are still hand-shaped or not wired (M3).
- The R9-M4 document check misses most kinds of drift (M4).

### Coordinator points (owner-requested)

| Point | Status | Evidence |
|---|---|---|
| **1. The structure covers only the money layer** | **Partly resolved (H1).** | **Now evaluated:** the value chain (delivered → metered → billed → revenue → collected), the physical diesel split (necessary + candidate + unexplained + extra), cost to serve and the outcome, for every site and side. These are checked against the stated fields (`derived()` `NODE_OF`) and against portfolio composition. Protect nodes are evaluated per option against its reference, for example Kisiwa 125 / 15 / 105 h, Mto 110 / 30 / 125 h, Thika 2 / 0 / 0 nights and Kasarani 2 / 0 missed. **Not evaluated:** the period's own Protect measures. `factor_map` sets `reduced_days: "0"`, `hours_per_day: "0"` and `uncovered_nights: "0"` for every site, so the October actual nodes give obligation hours 0 at every Lakeside site and nights without backup cover 0 at Thika (`derived-values.json`). The manifest's `portfolio.protect` table states Kisiwa 10 h, Mto 20 h (portfolio 30) and Thika 26 nights. `loop-protect.js:13` reads that hand table, and the Protect view renders "Obligation hours without a backup: 30 hours in October … Calculated from records" (headless check). `check_manifest.protect()` checks only that the sites sum to the portfolio figure, never that the figure equals the node. `asset_days_out_of_service` (Kisiwa 2, Mto 4) is also hand-entered, although it follows from the failure dates in the manifest (28 and 30 Oct). Of the six O2 measures, only `asset_availability` (on that hand count) and `deliverable_energy_used` are evaluated. `delivered_kwh_per_field_visit` 7,683.33, `crate_days_without_excursion` and `departures_met_per_installed_charger` 50.08 are not. |
| **2. The causal step is entered by hand, and some figures are unflagged** | **Mostly resolved; residue in M3.** | Welding's 217.8 L (= 10 × 3 × 22 × 0.33), Kirinyaga replacement's −1,171.5 kWh (excess → 0, model × 0.95), the huller's kWh, Mwea's crate-days, Kirinyaga repair (× (1 − share)) and Embakasi's schedule kWh are now expressions over named parameters. The perturbations of P9 and P10 move them. The remaining replay inputs carry `design_value` K / M / E (210, 20, 150, 68, 5 L a day). Kisiwa's 150 L is an assumption recorded as Q14. Cost lines are quotes, which is a legitimate input. **Residue (M3):** Kasarani's stopgap cover `days_to_restore - physical.spare_buses` is shaped to exactly a one-bus shortfall, with fixed costs. Embakasi's `feasible_nights` (E) is declared but referenced by no expression. `EMB-CHEAPEST.max_kw_option` types 500 instead of reading `physical.import_limit_kw`. |
| **3. Thika, Kasarani and Ruiru are not evaluated** | **Resolved.** | All nine sites are observed: 17 of 18 site-sides are evaluated. Every Thika, Kasarani and Ruiru option runs through the structure. My perturbations Q1 (Thika), Q2 and Q3 (Kasarani) and Q5 (Embakasi) move the dependent figures, and the checker catches them. **Ruiru's "not decomposed: stated total" is an honest exception.** The October plan record holds only `energy_cost` and `total`. The evaluator labels it with the missing leaf, the checker asserts the label, portfolio composition switches to `outcome_total_with_stated_totals` and names Ruiru, and the mock-up uses the stated total explicitly (`loop-core.js` `opTotals`). The plan is never counted as evaluated. |
| **4. Rights sit outside the structure** | **Partly resolved (M1).** | Mto and Kisiwa are now structural. R1 (Kisiwa GEN-KS-01 → POTENTIALLY_COVERED) moves the repair to 0 and the plan spend to 1,950, and flips the 5000/no case to buy-now; 8 FAIL. P12 (Mto expired) gives "infeasible at 5,000"; 17 FAIL. Thika and Kasarani rights decide nothing. R2 (Thika claim ACCEPTED → REJECTED) **moves 0 figures, and all 587 checks pass**. |

**The two structural rules.**

- **"Valued in money only if it changes a money node"** is sound and consistent with the brief: a potential claim is exposure, not money (§P4, line 119), and Protect effects are not stacked as cash. It is implemented as `dmoney != 0` on `contribution`, which is correct for the declared structures. The Kasarani stopgap is now valued at +150 because penalties are a money node, and the Kisiwa repair, the Thika stopgap and the battery evidence are not valued. That classification follows from the structure.
- **"Hard limits reject before valuation"** is consistent with the brief's sequence ("hard safeguards → incremental financial value", line 462), but the implementation is not general (M2). The evaluator hard-codes `departures_missed` as the only hard measure. It tests the option's value against the reference's value, not against the bound. It also does not enforce:
  - the hard bounds that the rows themselves claim for cold and mini-grid: Thika "fails the hard bound on batch temperature" and Kisiwa "P1 hard constraint";
  - physical limits: cold-room capacity and the EV import limit.

  The brief (line 464) asks that each condition's policy (hard, costed or unknown) be declared, with its reason and evidence. Here the policy lives in code.

### Findings

**H1 (High): the period's Protect measures are hand inputs that contradict the evaluated structure, and the claim says they are evaluated.**
- **Where:** `demo-site-scenario-manifest.yaml`, `factor_map` (`reduced_days`, `hours_per_day` and `uncovered_nights` are all `"0"`) and `portfolio.protect.measures` (lines ~346–350 and ~534); `check_manifest.py` `protect()`; `loop-protect.js:13`; REVIEW-response rev 10, point 1 ("value chain, physical split, cost, outcome and Protect nodes are all evaluated and checked against the stated figures").
- **What:** the October nodes evaluate to 0 obligation hours (Kisiwa, Mto) and 0 uncovered nights (Thika). The stated, displayed figures are 10 / 20 / 30 h and 26 nights. Nothing compares the two. The Protect view labels the 30 h "Calculated from records".
- **Why it matters:** this is exactly the owner's point 1: Protect measures not produced by the structure. It is also the case the owner flagged: a figure shown as calculated that the structure does not produce.
- **Fix:**
  - Map these leaves from records: reduced days from failure date to period end (Kisiwa 30 Oct, Mto 28 Oct); uncovered nights from the Thika fault and stock dates; asset-days out of service from the same dates.
  - Have `derived()` assert every numeric `portfolio.protect` site value against its node.
  - Either evaluate the remaining O2 measures, or label them as not evaluated.

**M1 (Medium): rights are structural for two of the four entitlement cases.**
- **Where:** `evaluation.options`: THIKA-EPC-WAIT, THIKA-SELF, KAS-OEM-WAIT and KAS-OEM-STOPGAP. Also `evaluate_structure.py` `rights[...] = e.get("eligibility", e.get("claim_state"))`.
- **What:**
  - **Thika and Kasarani have no `covered_by` line.** Under waiting, the supplier-borne controller or charger repair is not a line at all. THIKA-SELF's "voids the EPC workmanship cover" and BAT-EVIDENCE's "64,000 kept claimable" are free-text `rights_effect` strings. R2 shows that flipping Thika's right changes nothing.
  - **Two separate states are merged into one.** The rights map falls back from `eligibility` to `claim_state`, so Kasarani's CH-K2 resolves to `ACKNOWLEDGED`. Under `rights_rule`, any CH-K2-covered line would then be operator-borne. The brief (line 430) requires potential eligibility, acknowledged, accepted, delivered and credited to stay separate.
- **Fix:** give each waiting or supplier path its supplier-borne line with `covered_by`. Give each self-repair path the same line, uncovered, plus a declared "voids right X" effect that the evaluator applies. Evaluate the rights-at-stake figures (710; 64,000) as nodes. Key the share rule on eligibility, with the claim state kept as a separate field.

**M2 (Medium): the hard-limit rule is not general across verticals.**
- **Where:** `evaluate_structure.py` (the `PROTECT` set; `bound_failed = … opt["departures_missed"] > ref["departures_missed"]`) and `plans.*.fixed`.
- **What:**
  - **Q3:** with two chargers failed, the Kasarani stopgap still leaves 9 departures missed. It is not rejected, because the reference has 11, and it stays valued at +150 in a fixed must-do slot.
  - **Q5:** at an import limit of 380 kW, the 400 kW and 500 kW schedules are not rejected.
  - **Q6:** 300 crates at Mwea need 13,340 crate-days against a 12,400 capacity. The option is valued at +4,010 and the Harvest plan rises to 5,522.40, with no rejection.
  - **No-action and protective choices are hand-set:** Thika and Kisiwa no-action are not rejected by any bound, and the protective choices (KIS-REPAIR over KIS-REPLACE, THIKA-EPC-STOPGAP over THIKA-SELF) are hand-placed in `fixed` rather than chosen.
- **Fix:**
  - Declare on each Protect or physical measure its policy (hard, costed or unknown), its bound and its reason, as the brief asks.
  - Test hard bounds absolutely: option value ≤ bound, with "least violation" as a declared fallback.
  - Add capacity and import nodes as bounds.
  - Let the allocator choose the protective option as the cheapest option that meets the hard bounds, instead of taking it from `fixed`.

**M3 (Medium): some causal steps are still shaped by hand or are dangling, and §10 under-states them.**
- **Where:** `evaluation.options`: KAS-OEM-STOPGAP, KAS-OEM-WAIT, EMB-DEADLINE and EMB-CHEAPEST. Also main document §10, "Three things remain inputs".
- **What:**
  - **Kasarani:** `covered_bus_nights: "days_to_restore - physical.spare_buses"` does not follow `buses_short_per_night` (Q3), and the 70 + 20 cost does not scale with it. `spare_bus_nights: "physical.spare_buses"` uses a bus count as bus-nights.
  - **Embakasi:** `feasible_nights` (E) is referenced nowhere. Q4 (31 → 25) moves only the parameter itself, and all 587 checks pass. So the spike E feasibility outcome is a label, not an input to the structure.
  - **EMB-CHEAPEST** types `500` instead of reading `physical.import_limit_kw`.
- **Fix:**
  - Kasarani: cover = shortfall bus-nights − spare cover, with cost per covered bus-night, and a declared basis for how many nights the spare bus covers.
  - Embakasi: wire `feasible_nights` into `short_nights`/`departures_missed`, or remove the parameter.
  - EMB-CHEAPEST: read the import limit from `physical`.
  - List these residual inputs in §10.

**M4 (Medium): R9-M4 is partly resolved; the document check misses most kinds of drift.**
- **Where:** `check_manifest.py` `documents()`.
- **What:** the "allowed" set is every number anywhere in the manifest, including free-text strings, plus every derived value. The regex matches only figures with a thousands separator or two decimals, and only in main §2–§10, outside backticks. The superseded list is hand-kept and does not scan the manifest. Planted drift:
  - **D1:** novel figure 6,082.50 in §7: caught.
  - **D2:** Metro plan +95,634.00 → +95,484.00 (another valid value): **passes**.
  - **D3:** Kasarani +150.00 → +240.00: **passes**.
  - **D5:** "2 departures missed" → "3": **passes**.
  - **D6:** `economic-metric-and-effect-contracts.md` 367.50 → 361.25: **passes**.
- **Fix:** for the money figures of each plan, option and site, assert them at their anchored statements (for example a figure tag such as `{{plans.metro-bus.default.value}}`, or a per-section expected-figure list) rather than accepting set membership. Extend the scan to the contracts, models and walkthrough documents, and include the manifest's own strings.

**L1 (Low):** `oracle` OR-ALLOC-1 still says "recommended set spend 3,880"; the evaluated spend is 3,750. The superseded scan skips the manifest. *Fix:* update the oracle and add the manifest to the scan.

**L2 (Low; R9-L3 recurrence):** `domain-and-decision-models.md:5` still says "`check_manifest.py`: 389 checks pass"; the current count is 587. The manifest's first header line still reads "rev 4 (17 Nov 2026)". *Fix:* drop the count and update the header.

**L3 (Low):** the Kasarani narrative contradicts its own structure. The row and the decision screen say "Charging one bus at Ruiru on each of the 3 nights … $90", and the same screen says "the spare bus is free on 1 night". The structure covers 2 bus-nights. *Fix:* align the row's `nights`, its `detail` and the screen text with the evaluated cover (this follows from M3).

**L4 (Low):** `check_manifest.py` still hard-codes inputs: cold 0.20, 1550 + 0.25 × crate-days; EV 0.09, 0.12, 0.24 and 12; the window hours `{"Embakasi": 12, "Kasarani": 7, "Ruiru": 8}`; and `D(3)` visits. These do not produce figures, but a legitimate input change fails spuriously, and they duplicate inputs the evaluator now reads. *Fix:* read them from the manifest.

**L5 (Low):** Ruiru's "avoids a 60,000 purchase" is the row's `avoided_capex`. It is not evaluated as 4 × `physical.charger_unit_cost`, and no structure node says why 4 chargers would be needed. It is listed beside the plan, not added, so this is a provenance gap only.

### Perturbation table (my runs, scratch copies; "moved" = changed leaves in derived-values.json)

| # | Change | What moved | Checker (587 base) |
|---|---|---|---|
| P1 | Kisiwa `crew_visit` 8 → 9 Nov | restore 9 → 10 Nov; repair Protect 15 → 20 h | 2 FAIL, caught (reproduces author) |
| P2 | Kobo diesel 1.25 → 1.30 | 26 leaves incl. stop-setting and its sensitivities | 22 FAIL (reproduces) |
| P4 | Cold electricity 0.20 → 0.22 | 37 leaves incl. Kirinyaga options, Harvest plan | 25 FAIL (reproduces) |
| P5 | Mto warranty lead time 21 → 22 d | claim restore 29 Nov, fuel −143.75, plan | 12 FAIL (reproduces) |
| P7 | Embakasi demand 12 → 13 | 22 leaves incl. bills, option, Metro plan | 13 FAIL (reproduces) |
| P9 | Kirinyaga recovery 0.80 → 0.70 | repair 1,279.60; Harvest plan 2,949.60 | 5 FAIL (reproduces) |
| P11 | Mto half-capacity fuel 5 → 6 L/day | both inverter paths, plan, cases | 12 FAIL (reproduces) |
| P12 | Mto warranty EXPIRED | claim −2,967.50; default plan "infeasible" | 17 FAIL (reproduces) |
| Q1 *(cold)* | Thika `remedy_scheduled` 8 → 12 Nov | wait path 2 → 6 nights; references of stopgap and self | 2 FAIL, caught |
| Q2 *(EV)* | Kasarani kWh per bus 150 → 160 | 37 leaves: site actual/plan, portfolio, options | 9 FAIL, caught |
| Q3 *(EV)* | Kasarani failed chargers 1 → 2 | 4 short a night; wait 11 missed; **stopgap 9 missed, still +150, not rejected** | 3 FAIL (Protect values), caught; shows M2 and M3 |
| Q4 *(EV)* | Embakasi `feasible_nights` (E) 31 → 25 | **only the parameter** | **587 pass**: dangling design value (M3) |
| Q5 *(EV)* | Embakasi import limit 500 → 380 | deliverable and O2 only; 400/500 kW schedules not rejected | 3 FAIL (O2), caught; shows M2 |
| Q6 *(cold)* | Mwea crates 150 → 300 | value 4,010, Harvest plan 5,522.40; above room capacity, not rejected | 5 FAIL, caught; shows M2 |
| R1 *(rights)* | Kisiwa GEN-KS-01 → POTENTIALLY_COVERED | repair 0; spend 1,950; 5000/no case flips to buy-now | 8 FAIL, caught |
| R2 *(rights)* | Thika claim ACCEPTED → REJECTED | **nothing** | **587 pass** (M1) |
| D1 *(doc)* | main §7 +6,088.50 → +6,082.50 | — | 1 FAIL, caught |
| D2 *(doc)* | main §7 Metro +95,634.00 → +95,484.00 | — | **587 pass** (M4) |
| D3 *(doc)* | main §7 Kasarani stopgap +150.00 → +240.00 | — | **587 pass** (M4) |
| D5 *(doc)* | main §7 "2 departures missed" → "3" | — | **587 pass** (M4) |
| D6 *(doc)* | contracts doc 367.50 → 361.25 | — | **587 pass** (M4) |

### R9 findings

| Finding | Status |
|---|---|
| R9-M1 | **Resolved in the evaluator.** There are no numeric literals beyond identities and the percent/inclusive-horizon conventions. P4 and P7 move everything dependent. The checker still duplicates constants (L4). |
| R9-M2 | **Resolved.** `base_site_factors` is gone, and deltas are expressions (P9, P10 and P11 move the values). The residue is in M3. |
| R9-M3 | **Resolved.** Recomputed by hand below. The rights decide the 2,600 line for Mto. |
| R9-M4 | **Partly resolved (M4).** |
| R9-L1 | **Resolved for option Protect effects.** The spare-bus units are still questionable (M3). |
| R9-L2 | **Resolved.** Each restore date is derived and asserted; P1, P5 and Q1 move and are caught. |
| R9-L3 | **Partly resolved (L2).** |

**Hand recomputation.**

| Figure | Working | Result |
|---|---|---|
| Mto claim | 150 + 80 (the 2,600 unit is supplier-borne under POTENTIALLY_COVERED) + (6 Nov + 21 + 1 = 28 Nov → 22 days × 5 L × 1.25 = 137.50) | **367.50** ✓ |
| Buy now | 2,600 + 80 + 150 + 80 = 2,910, + 6 days (5 + 1) × 5 L × 1.25 = 37.50 | **2,947.50** ✓ |
| Kobo stop-setting | (210 × 1.25 − 150 × 0.08) × 12 − 90 | 2,916 |
| Huller | 395 × 12 − 1,200 | 3,540 |
| Lakeside plan value | 2,916 + 3,540 − 367.50 | **+6,088.50** ✓ |
| Lakeside plan spend | 1,800 + 430 + 90 + 1,200 + 230 | **3,750** ✓ |
| Kasarani stopgap | 2 missed × 120 = 240 avoided, − (70 + 20) | **+150** ✓ |
| Embakasi schedule (no action) | 21,438 | |
| Embakasi schedule (with option) | 400 × 2 × 31 × 0.12 + 400 × 5 × 31 × 0.09 + 400 × 12 = 13,356 | |
| Embakasi schedule (value) | (21,438 − 13,356) × 12 − 1,500 | 95,484 |
| Metro plan | 95,484 + 150 | **95,634** ✓ |
| Lakeside, budget 6,500, no LOI extension | 2,916 + 3,540 − 2,947.50 | 3,508.50 ✓ |

### Regression checks

- **Evaluator and checker.** `python3 evaluate_structure.py`: 9 sites, 24 options, 3 plans, and its output is byte-identical to the committed `derived-values.json`. `python3 check_manifest.py`: **587 passed, 0 failed**.
- **Rebuild.** In a scratch copy I ran `rebase_v70.py`, then `gen_fixtures.py` ("evaluator vs stated fields: 0 differences", 28 replay patterns), then `node build.mjs`. `diff -r` against the working tree shows **no differences**, which makes the rebuild byte-identical.
- **Preserved v7.0 screens.** The sources of the 65 preserved screens are unchanged since `9398febb0`: `screens.js`, `portfolio.js`, `outcomes.js` and `src-v70-baseline` are not in the diff. The bundle rebuilds identically. `audit-results.json` records `preservedIdentical: 65/65`, but I did not rerun the audit's text comparison against v7.0.
- **Wording, filters and menus.** The added mock-up lines contain no role or question wording, no `<select>`, and no new filters or menus. The new parts are three sections inside decision screens: restore dates, cost lines and who bears each, and capacity bound. The audit summary shows 0 role/question hits and 0 filter controls.
- **Generality.** The same evaluator and `structures`/`factor_map` path serves all three verticals. M2 is the exception: the hard-bound policy is EV-only.
- **Headless spot check.** I used headless Chromium (Playwright headless shell, with locally extracted libraries and fonts) against a static server on **port 8765**, which I stopped afterwards.
  - **Mto inverter:** −$367.50 and −$2,947.50; restore dates 28 Nov and 12 Nov, with their drivers.
  - **Kasarani:** +$150 and $240 against $90, with the "3 nights" text (L3).
  - **Lakeside act-first:** +$6,088.50 and $3,750 of $5,000; cases +$2,548.50 and +$3,508.50; sensitivities +$5,690 and +$5,338.50. Neither 6,096 nor 3,880 appears.
  - **Metro act-first:** +$95,634, and +$150 with $90 of $5,000 when the tariff switch is "no".
  - **Harvest act-first:** +$3,182.40 and $720.
  - **Ruiru expansion:** 2,800 / 3,200, $26.14, and 62 missed.
  - **Protect view:** "30 hours in October … Calculated from records" (H1).
  - **General:** no page errors, and no overflow at 390 px on the three routes I checked.

### Not verified

- I did not rerun `tools/run-audit.sh` in full. The 202-route, contrast, focus, design-value-scan and 65/65 text-identity figures are the author's numbers.
- I did not rerun the CSV validator, because I could not locate it in the repository.
- I did not verify the replay design values themselves; they belong to the calibration lane.

## Re-review (rev 11)

**Reviewer:** a fresh, independent Claude reviewer, 17 Nov 2026. I reviewed the rev 11 working tree on `task/product-direction-layer4-design`, which is the uncommitted diff over `20a94e03f`. The main focus is structural derivation and the coordinator's four points from the owner's eleventh message. I ran every experiment in scratch copies of the folder. This appended section is my only edit.

### Verdict: **REVISE (targeted: H1, then M1 to M5)**

Rev 11 is a large and genuine step. The period's Protect measures are now counted from dated records. All seven O2 measures are Σ numerator / Σ denominator of evaluated nodes. Eligibility is separate from claim progress, and rights flips now move outcomes at Thika, Kasarani, Kobo battery, Kisiwa and Mto. Bounds are declared per vertical and measured absolutely. Protective choices are made by the allocator. Every figure I recomputed by hand is correct, and the author's perturbations reproduce.

What remains:

- **One plan-deciding admissibility is still hand-entered.** The Mto inverter no-action option is excluded by a typed `bound_failure` string, not by a limit (H1).
- **One valuation bug** appears under rights flips (M1).
- **The allocator does not enforce crews**, although the brief and the documents use them as a constraint (M2).
- **The least-violation fallback** is cost-blind, and the policy split between Kisiwa and Mto is undifferentiated (M3).
- **The document check is still sign-blind**, has one mis-anchor and leaves headline figures unanchored (M4).
- **The mock-up still hand-types several figures** where evaluated nodes exist (M5).

### Coordinator points (owner-requested)

| Point | Status | Evidence |
|---|---|---|
| **1. The structure covers only the money layer** | **Mostly resolved. Residue: M2, M5, L2.** | **Now evaluated:**<br>• Kisiwa: `reduced_capacity_from` 30 Oct → `days_incl` = 2 days × 5 h = **10 h**.<br>• Mto: 28 Oct → 4 days × 5 h = **20 h**.<br>• Thika: `backup_unproven_from` 6 Oct → **26** nights.<br>• Ruiru: 26 charger-days.<br>• Kasarani, November to date: 5 nights, 2 missed (5 short − 3 spare), 240.00 in penalties.<br>• All seven O2 measures come from nodes, and I hand-checked four (below).<br>`check_manifest.derived()` now asserts every numeric `portfolio.protect` site value against its node for both periods. My perturbations C2 (Thika proven) and Nk (Mto window 5 → 6 h) are caught. The Protect view reads the nodes, so "Calculated from records" is now true for those rows.<br>**Residue:**<br>• The Kasarani site row and the decision factor still read hand-typed `incident.capacity_after` (1,050 / 1,200 / 1) and `incident.november_to_date` (2 missed, 240), labelled "Measured … (recorded)" (M5).<br>• Crews are not structural (M2).<br>• Thika's "nights without backup cover" is the same expression as "days unproven" (L2). |
| **2. The causal step is entered by hand** | **Partly resolved. Residue: H1, L1, L3.** | **Fixed:** Kasarani cover = shortfall bus-nights − spare cover, at 45 per bus-night. Embakasi `feasible_nights` now feeds missed departures (Q4 reproduces). EMB-CHEAPEST reads `physical.import_limit_kw`.<br>**Still hand-shaped:**<br>• The Mto no-action rejection is a typed string, and its factor changes omit the extra fuel that both other paths carry (H1).<br>• THIKA-SELF restores "as_of", with no driver (L3).<br>• `failed_chargers` is declared separately in each Kasarani option (L1). |
| **3. Thika, Kasarani and Ruiru are not evaluated** | **Resolved.** | All nine sites and 26 options run through the structure. Ruiru's plan remains an honest "not decomposed: stated total".<br>Perturbations move the outcomes and are caught:<br>• C1: Thika remedy on 6 Nov → waiting is admissible and chosen, spend 620.<br>• E3: Kasarani spare 3 → 2 → November 3 missed, 360.<br>• E4: Ruiru import 400 → 300 → +6 rejected (93 missed, 80 kW over).<br>• E5: Kasarani SLA 8 days → cover 225, value 375. |
| **4. Rights sit outside the structure** | **Mostly resolved. Residue: H1, M1, L4.** | `covered()` keys on eligibility, with `claim_state` separate. Flips moved the outcome at every site:<br>• **RA** (Mto claim DENIED): claim path one-off 2,830 → no plan within 5,000 ("infeasible"); 105 FAIL.<br>• **RB** (Kasarani DENIED): contactor becomes operator-borne; 32 FAIL.<br>• **RC** (Thika EXPIRED): protective choice → self-repair, spend 1,330; 6 FAIL.<br>• **RD** (Kobo BAT-001 already covered): BAT-NOACT is admissible and chosen, spend −430.<br>• **RE** (Kisiwa GEN-KS-01 covered): repair 0; the 5000/no case flips.<br>"Voids cover" is structural for Thika (THIKA-SELF `cover_lost` 710; 0 under RC).<br>**Residue:**<br>• The Mto notice-deadline lapse is not modelled (H1).<br>• Under RB the stopgap's value goes wrong, because the reference path's operator-borne line is not netted (M1).<br>• KAS-LOCAL's voiding is not evaluated (L4).<br>• Restore dates do not follow a denied claim (L4). |

**Hard limits.**

- **What holds:** the bounds are declared per vertical with reasons, measured absolutely (`violations` = max(node − bound, 0)) and generalise across verticals. Q5, Q6 and E4 reject correctly.
- **The hard/advisory policy is set per decision.** That is allowed by brief l.464, but:
  - the same P1 redundancy bound is hard (with least violation) for the Kisiwa generator and advisory for the Mto inverter, with a reason that does not distinguish the two cases (M3);
  - the least-violation fallback ignores cost and budget (M3).
- **The Mto inverter no-action option is not rejected by a limit.**
  - Its bound row on `#/decision/mto-inverter` reads "Not a limit for this decision · obligation hours without a backup: 125 h — Not admissible" (headless check).
  - Its inadmissibility is the typed `bound_failure` string added in rev 11, and it is not in the `mto_inverter` decision's option list at all (H1).

### Findings

**H1 (High): the Mto no-action rejection is hand-entered, and the structure, completed consistently, would choose no action.**
- **Where:** `demo-site-scenario-manifest.yaml` `evaluation.options.MTO-INV-NOACT`: `money: "not evaluated…"`, `bound_failure: "inadmissible: … notice deadline (27 Nov) is lost"` (new in rev 11) and `changes` without `extra_l`. Also `plans.lakeside-power.decisions[mto_inverter].options` (NOACT is absent), and `domain-and-decision-models.md:648` ("No action is REJECTED only by a hard bound or a lapsing right (KIS-NOACT, MTO-INV-NOACT)").
- **Evidence:**
  - **X1:** deleting the two strings makes NOACT `admissible: true`, and **all 753 checks pass**.
  - **X2:** adding NOACT to the decision changes nothing, because with no money change it is not valued.
  - **X3:** giving NOACT the same extra-fuel change the claim and buy-now paths carry (`extra_l + days_to_restore × extra_l_per_day`) values it at **−156.25**, which beats the claim (−367.50). The allocator then picks no action: the Lakeside plan becomes **+6,299.75 at 3,520** (74 FAIL).
  - The real reason no action is wrong is the right lapsing on 27 Nov (2,600 of cover lost) and the indefinite half capacity. Neither is in the structure: there is no dated lapse, no `voids_rights`, and the claimable-cover bound counts only `INSUFFICIENT_EVIDENCE`, not lost cover.
- **Why it matters:** this is the owner's governing principle (points 2 and 4). The admissibility that forces the plan's inverter choice is typed, not produced. The "Bound check" table attributes it to the evaluator while saying no limit applies.
- **Fix:**
  1. Model the notice deadline as a dated right lapse. For example, an option whose restore path files no claim by `entitlement.notice_deadline` voids INV-MT-02, giving `cover_lost` 2,600.
  2. Count lost cover in a declared cover bound (unclaimable + lost), across all verticals. THIKA-SELF would then also fail it while the right applies, and pass under R2.
  3. Give NOACT the extra-fuel change and put it in the `mto_inverter` decision.
  4. Delete `money` and `bound_failure`.
  5. Do the same for KOB-RESERVE's typed `bound_failure`: declare a dawn-adequacy bound over a design-value leaf (spike K).

**M1 (Medium): an option's value does not net the reference path's operator-borne cost, so a rights flip produces a wrong value.**
- **Where:** `evaluate_structure.py` `run()`: `value_if_admissible = dmoney × months − one_off`. The reference's `operator_one_off` is never subtracted.
- **Evidence (RB, Kasarani claim DENIED):** both paths now pay the 380 contactor. KAS-OEM-STOPGAP becomes **−230.00** (240 avoided − 90 − 380), where the correct increment is **+150.00**. The Metro plan drops to 95,254, and the tariff-off case and the downside go to −230.
- **Why it matters:** this is a mechanics bug in the rights path the owner asked for. It hits any valued option whose `reference_option` carries an operator-borne line.
- **Fix:** value = Δcontribution × months − (option one-off − reference one-off). Show the common lines as common.

**M2 (Medium): crews are not a constraint in the allocator, yet the documents state them as one.**
- **Where:** `evaluate_structure.py` `best()`, which checks budget only. `crew_visits_nov: 3` and `technician_visits_nov: 2` are in the manifest. Main §7 says "Budget 5,000, three crew visits … crews 3 of 3", and the walkthroughs say "2 of 2 technician visits".
- **Evidence (L1):** Lakeside crews 3 → 1 moves **0 leaves; 753 pass**. The plan still uses 3 visits (KIS-REPAIR, BAT-EVIDENCE, MTO-INV-CLAIM).
- **Why it matters:** brief l.295 and l.466 ask for budget- and crew-constrained allocation. "3 of 3" is a hand count.
- **Fix:** sum `crew_visits` per item in `best()` against the tenant limit. Evaluate "visits used", anchor it in the documents, and add a perturbation.

**M3 (Medium): the least-violation fallback ignores cost, and the same P1 bound is hard in one decision and advisory in the other without a distinguishing fact.**
- **Where:** `evaluate_structure.py` protective block, and `plans.lakeside-power.decisions` (`kisiwa_genset` is hard with least violation; `mto_inverter` and `kisiwa_storage` are advisory).
- **Evidence:**
  - **L2:** Kisiwa crew visit on 29 Nov → repair 120 h against replacement 105 h. The fallback picks the 9,500 replacement, and **every Lakeside case becomes infeasible**, including at 6,500.
  - **H1-test:** making Mto redundancy hard with least violation (as at Kisiwa) makes every Lakeside case infeasible, because the fallback exists only for protective decisions.
  - The Mto reason ("both paths leave reduced capacity until restore; money decides") is equally true at Kisiwa.
- **Why it matters:** the plan headline depends on a policy placement whose reason does not tell the two cases apart. Least violation is neither "hard" nor "costed" in the brief's sense (l.464).
- **Fix:**
  - Either declare the fact that makes Mto advisory (for example, generator-backed daytime supply, so a different measure applies), or raise it to the owner as a policy question.
  - Make least violation budget-aware: choose among options within budget, and report a trade-off when the least violation is unaffordable. Allow it on valued decisions, or state why not.

**M4 (Medium): the anchor check is a real improvement, but it is sign-blind, has a mis-anchor, and leaves headline figures unanchored.**
- **Where:** `check_manifest.py` `anchors()` (it compares `abs()` to `abs()`) and `documents()` (membership scan, main §2–§10 and walkthroughs only). Also `walkthroughs.md:42`.
- **Planted drift (scratch):**

| # | Drift | Result |
|---|---|---|
| Da | main §7 "− 367.50<!--fig…-->" → "+ 367.50" | **passes** |
| Di | main "2<!--fig:…departures_missed-->" → "-2" | **passes** |
| Db | contracts "2,910.00" → "2,901.00" (unanchored) | **passes** |
| Dc | main §10 "26 nights without backup cover" → "22" (unanchored) | **passes** |
| De | main Harvest "spend **720.00**" → "450.00" (unanchored; a valid value) | **passes** |
| Dh | main Metro "spend **1,590.00**" → "1,500.00" (unanchored) | **passes** |
| Df | main "−1,988.40" (KIRI-REPLACE) → "−1,512.40" | **passes** |
| Dg | phase plan "Thika stopgap (100.00)" → "10.00" | **passes** |
| Dd | main "720.00" → "702.00" | caught |
| E3+ | Kasarani November spare 3 → 2, with the manifest's protect table updated consistently | **753 pass.** The walkthrough still says "2<!--fig:options.KAS-OEM-WAIT.protect.departures_missed--> departures missed … $240 penalties" for **November to date**, because the anchor points at the option's horizon path, not the observed period. |

- **Fix:**
  - Compare signed values; carry the sign in the anchored text.
  - Anchor every plan headline (spend and visits for all three tenants), the §10 Protect statement, and the evaluated option figures in the contracts, models and phase plan.
  - Re-point the walkthrough anchor to `sites.metro-bus/Kasarani.november_to_date.nodes.departures_missed`, and anchor the $240.

**M5 (Medium): the mock-up still hand-types figures that evaluated nodes produce, so they do not move with the structure.**
- **Where:**
  - `loop-core.js:142` and `loop-decisions.js:347` read `incident.capacity_after` (1,050 / 1,200 / 1) and `incident.november_to_date` (2 missed, $240), labelled "Measured" and "(recorded)".
  - `loop-decisions.js` result strings: "Likely 2 missed departures before 9 Nov", "unprotected at night until 8 Nov", "2,800 of 3,200 kWh a night", "3,360 kWh a night".
  - `loop-protect.js:66` `OBASIS`: "1,302 ÷ 26 … 1,302 ÷ 25.16 = 51.75", "Ruiru 34%".
  - The manifest duplicates are never checked: `incident.november_to_date`, `capacity_after`, `exposed_value` 2,160 (= 120 × 18, typed).
- **Evidence:**
  - **E5:** with the SLA at 8 business days, the evaluator gives 5 missed and a 12 Nov restore. The rebuilt bundle still contains "Likely 2 missed departures before 9 Nov".
  - **E3+:** the Kasarani site row keeps "2 … $240" while the nodes say 3 and $360, and all checks pass.
- **Why it matters:** the owner's principle covers the illustration itself. This is the rev 10 H1 pattern at a smaller scale.
- **Fix:**
  - Read these from DERIVED: the November nodes, the WAIT option's `protect` and `restore_date`, `bound`, and the operations numerator and denominator.
  - Delete or derive the manifest duplicates.
  - Extend the audit's scan to digit-bearing literals in the `loop-*.js` result maps.

**L1 (Low): some inputs are duplicated and not tied together.**
- `failed_chargers` is declared separately in KAS-OEM-WAIT and KAS-OEM-STOPGAP, and again in the November observation. Changing only the stopgap's gives −255 against the author's 825 for the consistent Q3.
- `physical.spare_buses` is unused (E2 moves 0 leaves), while the option's `spare_cover` is a roster basis.
- The option `hours: 5` for the Mto and Kisiwa paths is separate from the observed `reduced_hours_per_day` (Nk moves October, not the options).
- `capacity_crate_days_oct: 12400` is typed rather than 400 × `period_days`, and is applied to a 30-day contract month.

*Fix:* read each from one record.

**L2 (Low):** COLD_CHAIN `nights_without_backup_cover = uncovered_nights = days_incl(backup_unproven_from, period_end)`, which is the same expression as days unproven. The measure's own definition on screen is "stock present, backup start unproven and no manual-start cover (rota)", but stock presence and rota records are not leaves. The figure (26) is right for this world.

*Fix:* uncovered = Σ nights (unproven ∧ stock present ∧ no rota record).

**L3 (Low):** THIKA-SELF `restore: {date: as_of}` has no procurement or install driver. Under RC and R2 it is chosen because it "restores today".

*Fix:* give it a lead-time driver (a quote) or flag it as an assumption.

**L4 (Low):**
- Restore dates do not follow rights. Under a DENIED claim, WAIT still uses the supplier's 9 Nov (Kasarani) and 8 Nov (Thika), and CLAIM still uses the 21-day warranty lead time.
- KAS-LOCAL ("voids power-stage cover; dominated") is not evaluated.

*Fix:* make the supplier restore driver conditional on `covered()`, and evaluate KAS-LOCAL with `voids_rights: [CH-K2]` or state why not.

**L5 (Low):** October's observed state leaks into forward 12-month options. KIS-BATT60 shows "Advisory · 10 h", MTO-HULLER and MTO-WELDING carry 20 h, and the Mto "immediate restore" reference shows 20 h.

*Fix:* reset period-observation leaves (`reduced_days`) to the forward baseline for options without a restore path.

**L6 (Low):** the Kasarani November record `kwh: 6000` over 5 nights exceeds what the structure says was deliverable (1,050 × 5 = 5,250) while a bus was short each night.

*Fix:* record the delivered kWh (≤ 5,250), or add a record-consistency check.

**L7 (Low):**
- The evaluator still holds vertical knowledge in code: the `PROTECT` node list and the EV-only `bound` display branch.
- Hand dispositions remain in rows. For example, THIKA-SELF is "REJECTED, dominated" while the evaluator says it is admissible.

*Fix:* declare the Protect list per vertical, and derive dispositions or label them as narrative.

### Perturbation table (my runs, scratch copies; "moved" = changed leaves in derived-values.json; checker base 753)

| # | Vertical / mechanism | Change | What moved | Checker |
|---|---|---|---|---|
| X1 | MG / limit | delete MTO-INV-NOACT `money` + `bound_failure` | NOACT becomes admissible; nothing else | **753 pass** (H1) |
| X3 | MG / limit | X1 + NOACT in decision + extra fuel like the other paths | NOACT −156.25; plan picks no action: **+6,299.75 at 3,520** | 74 FAIL (H1) |
| RA | MG / rights | Mto INV-MT-02 claim DENIED | claim one-off 2,830; plan infeasible at 5,000 | 105 FAIL |
| RB | EV / rights | Kasarani CH-K2 claim DENIED | contactor operator-borne; **stopgap −230 (should be +150)**; plan 95,254 | 32 FAIL (M1) |
| RC | Cold / rights | Thika eligibility EXPIRED | stopgap 810; choice → self-repair; spend 1,330 | 6 FAIL |
| RD | MG / rights | Kobo BAT-001 already POTENTIALLY_COVERED | BAT-NOACT admissible and chosen; spend −430 | caught |
| RE | MG / rights | Kisiwa GEN-KS-01 POTENTIALLY_COVERED | repair 0; spend 1,950; 5000/no case flips | caught |
| L1 | MG / allocator | Lakeside crews 3 → 1 | **nothing** | **753 pass** (M2) |
| L2 | MG / limit | Kisiwa crew visit 8 → 29 Nov | least violation → 9,500 replacement; **all cases infeasible** | caught (M3) |
| H1-test | MG / limit | Mto redundancy hard + least violation (as at Kisiwa) | every Lakeside case infeasible | caught (M3) |
| Nk | MG / observation | Mto observed window 5 → 6 h | October 20 → 24 h; options unchanged (duplicated `hours`) | 1 FAIL (L1) |
| C1 | Cold / limit | Thika remedy 8 → 6 Nov | waiting admissible and chosen; spend 620 | caught |
| C2 | Cold / observation | Thika backup proven (no unproven date) | 26 → 0 nights and days | 2 FAIL |
| E2 | EV / input | Kasarani `physical.spare_buses` 1 → 0 | **nothing** (dangling) | 753 pass (L1) |
| E3 | EV / observation | Kasarani November spare 3 → 2 | November 3 missed, 360 | 2 FAIL; **753 pass once the protect table is updated; walkthrough and site row keep 2 / $240** (M4, M5) |
| E4 | EV / limit | Ruiru import 400 → 300 | +6 rejected (93 missed, 80 kW over) | 7 FAIL |
| E5 | EV / rights + structure | Kasarani SLA 5 → 8 business days | restore 12 Nov; wait 5 missed; cover 225; value 375 | caught; **bundle still says "Likely 2 missed departures before 9 Nov"** (M5) |
| Q3 | EV | both Kasarani `failed_chargers` 1 → 2 | cover 495; value 825 (reproduces author) | 35 FAIL |
| Q4 | EV | Embakasi feasible nights 31 → 25 | schedule rejected (6 missed); Metro 150 (reproduces) | 28 FAIL |
| R2 | Cold / rights | Thika claim DENIED | choice → self-repair; spend 1,330 (reproduces) | 6 FAIL |
| Da, Di, Db, Dc, De, Dh, Df, Dg | documents | see M4 | — | **all pass** (M4) |
| Dd | document | main "720.00" → "702.00" | — | 1 FAIL |

### Hand recomputation

| Figure | Working | Result |
|---|---|---|
| Kasarani restore | notice 2 Nov (Mon) + 5 business days → 9 Nov; days to restore 9 − 6 = 3 | 9 Nov ✓ |
| Kasarani cover | 4 × 50 kW → one charger out → 150 × 7 h = 1,050 against 8 × 150 = 1,200 → ceil(150 / 150) = 1 bus short; 1 × 3 nights − 1 spare = **2 × 45** | **90.00** ✓; value 2 × 120 − 90 = **+150.00** ✓ |
| Kisiwa October obligation hours | days_incl(30 Oct, 31 Oct) = 2 × 5 h | **10** ✓ |
| Mto October obligation hours | days_incl(28 Oct, 31 Oct) = 4 × 5 h | **20** ✓ (portfolio 30) |
| Thika nights | days_incl(6 Oct, 31 Oct) | **26** ✓ |
| O2 asset availability | (155 + 122 + 151) / (155 + 124 + 155) = 428 / 434 | **98.62%** ✓ |
| O2 kWh per visit | (9,100 + 7,950 + 6,000) / 3 | **7,683.33** ✓ |
| O2 departures per installed charger | (620 + 248 + 434) / (10 + 4 + 12) = 1,302 / 26 | **50.08** ✓ |
| O2 deliverable energy used | (2,800 + 1,200 + 1,960) / (6,000 + 1,400 + 3,200) | **56.23%** ✓ |
| Kisiwa least violation | repair 8 Nov + 1 = 9 Nov → 3 d × 5 = 15 h; replace 6 Nov + 21 → 21 d = 105 h; none → 25 d = 125 h | repair ✓ |

### Regression checks

- **Evaluator and checker.**
  - `python3 evaluate_structure.py`: 9 sites, 26 options, 3 plans. Its output is byte-identical to the committed working-tree `derived-values.json`.
  - `python3 check_manifest.py`: **753 passed, 0 failed** (1.2 s).
- **Rebuild.** In a scratch copy I ran `rebase_v70.py`, `gen_fixtures.py` ("0 differences", 28 replay patterns), `node build.mjs` and `gen_docs.cjs`. `diff -rq` against the working tree shows **no differences** (byte-identical).
  - Side note: `gen_fixtures.py` reported "0 differences" for E5 too, although the checker failed. Its diff is narrower than the checker's.
- **Preserved v7.0 screens.** `screens.js`, `portfolio.js`, `outcomes.js`, the CSS files and `src-v70-baseline` are not in the diff since `20a94e03f`. `audit-results.json` records 65/65 preserved; I did not rerun the audit's text comparison.
- **Wording, filters and menus.** The added mock-up lines contain no `<select>`, no role or question wording and no menus. The only matches were the JS `.filter()` calls and "cooling". Audit summary: 0 role/question hits, 0 filter controls.
- **Generality.** One evaluator and one set of mechanics serves all three verticals, with bounds declared per vertical. Residue is in L7.
- **Headless spot check.** I used headless Chromium (Playwright headless shell) against a static server on **port 8781**, which I stopped afterwards; I did not touch ports 5490 or 8990.
  - **Mto inverter:** the bound table described in H1.
  - **Kisiwa:** "the least violation is chosen: Repair … 15 obligation hours".
  - **Kobo battery:** "Cover under each option", $64,000.
  - **Thika:** $710 "potentially covered, Accepted".
  - **Kasarani:** "3 bus-nights … 2 … $45 each: $90 … +$150", with "Likely 2 missed departures before 9 Nov" (M5).
  - **Ruiru:** $60,000; "62 over the limit".
  - **Outcomes by site:** 30 h and 26 nights "Calculated from records"; O2 56.23% / 50.08 / 7,683.33 / 99.997%.
  - No page errors, and no overflow at 390 px on the 5 routes I checked.

### Remaining hand inputs (all of them, judged)

| Input | Where | Legitimate? | Flagged? |
|---|---|---|---|
| 210 L, 150 kWh, 20 L (K); 68 L (M); 31 feasible nights (E) | option params | yes: replay design values | yes (`design_value`) |
| "1 bus short on an infeasible night" | EMB-DEADLINE | basis taken from spike E text | basis only |
| 150 L Kisiwa battery | KIS-BATT60 | yes: owner Q14 | yes (assumption) |
| 0.80 recovery share; 0.95 new-unit factor | Kirinyaga | yes: assumptions with range or datasheet | yes |
| quotes: 60, 30, 1,200, 1,800, 9,500, 14,000, 150, 80, 2,600, 250, 180, 350, 4,800, 40, 60, 45 per bus-night, 1,500, 15,000 per charger | cost lines / params | yes: quotes | basis given |
| windows 5 / 3 / 2 / 5 h; install 1 d; local supply 5 d; repair 1 d | params | yes: quotes or windows | basis given; duplicates the observation (L1) |
| crates 150, 30 days, rate 0.18, handling 100; +6 / +10 buses; +4 chargers | params | yes: draft contract or offer | basis given |
| spare cover 1 bus-night | Kasarani | roster basis, but `physical.spare_buses` is unused | basis only (L1) |
| `failed_chargers` 1 (×2) | Kasarani options | record, duplicated | basis only (L1) |
| crate-minutes above the limit, 2,400–3,600 | Thika observation | yes: observer output | yes ("Measured") |
| major assets, field visits, excursion crates and days, cooling minutes | observations | yes: records | as records |
| **MTO-INV-NOACT `bound_failure` / `money`** | evaluation | **no**: typed admissibility (H1) | presented as a bound check |
| **KOB-RESERVE `bound_failure`** | evaluation | replay result, but the bound is undeclared | design value named (H1 fix 5) |
| THIKA-SELF restore "as_of" | evaluation | no driver | no (L3) |
| `incident.capacity_after`, `incident.november_to_date`, `exposed_value` 2,160 | manifest | **no**: typed computed figures shown on screen | no (M5) |
| `capacity_crate_days_oct` 12,400 | tenant | typed product | no (L1) |
| crews 3 / 2 / 2 | tenant | resource limit | not enforced (M2) |
| row dispositions and reasons | rows | narrative | not derived (L7) |

### Convergence

This round still needs author work. All of it is targeted and mechanical:

1. **H1:** the Mto deadline lapse, a lost-cover bound and a complete no-action option.
2. **M1:** a one-line netting fix.
3. **M2:** a crew sum in `best()`.
4. **M3:** a budget-aware fallback, plus either a declared fact for the Mto advisory policy or an owner question.
5. **M4:** signed anchors, plus anchors on the remaining headline figures.
6. **M5:** read the remaining screen literals from DERIVED.

Apart from the M3 policy question, nothing here needs an owner decision. After this round I would expect only owner decisions to remain: Q1–Q14 (including Q13 and Q14), and possibly the Mto redundancy policy.

### Not verified

- I did not rerun `tools/run-audit.sh`. The 202-route, contrast, focus, design-value-scan and 65/65 text-identity figures are the author's numbers.
- I did not rerun the CSV validator.
- I did not verify the replay design values; they belong to the calibration lane.

## Re-review (rev 12)

**Reviewer:** a fresh, independent Claude reviewer, 17 Nov 2026. I reviewed the rev 12 working tree on `task/product-direction-layer4-design`, which is the uncommitted diff over `f55f15716`. I ran every experiment in scratch copies of the folder (harness `scratchpad/pert.py`; "moved" is the number of changed leaves in `derived-values.json`). This appended section is my only edit.

### Verdict: **REVISE (targeted: H1, then M1 to M5)**

Rev 12 closes most of what rev 11 asked for:

- No typed admissibility is left. The notice-deadline lapse, the cover bound and the dawn bound are declared, and X1 and H1n reproduce.
- The netting fix is correct. I recomputed RB by hand.
- Crews bind (CR2, RC).
- Signed anchors catch a sign flip in a companion document (Dn7).
- The Kasarani screens now follow the structure. Under E5 + E3, more than 20 lines on the decision, site, outcomes and act-first pages move.

The scratch rebuild is byte-identical, and the preserved screens are untouched.

What remains:

1. **One plan-deciding causal step is still typed.** The rice-huller's dependence on the inverter restore is a `requires_any` rule, and it gives wrong plans whenever the restore dates or rights move (H1). This step was already present in rev 11, and earlier reviews (mine included) did not catch it. The author's own RA perturbation shows it: the plan connects the huller while choosing never to restore the inverter.
2. **The allocator fixes protective choices one at a time.** As a result, it is non-monotonic in budget and can pick a worse plan (M1).
3. **Mixed horizons.** RA's "no action within the horizon" comes from valuing over 25 days alongside 12-month options, and it is not disclosed in the pack (M2).
4. **Typed manifest strings are still rendered on screen** and go stale (M3).
5. **The document check has coverage gaps** (M4).
6. **The notice-deadline lapse is general in code but scoped by a hand-placed `asset:` key** (M5).

### Coordinator points (owner-requested)

| Point | Status | Severity | Evidence |
|---|---|---|---|
| **1. Only the money layer is structural** | **Mostly resolved** | Medium (M3), Low (L2, L5) | **Now structural:**<br>• Crews are enforced (CR2: crews 3 → 2 makes every Lakeside case infeasible).<br>• The Kasarani November figures are nodes (E3: 3 missed / $360 on the site, outcomes and act-first pages).<br>• Thika's uncovered nights are a three-record expression.<br>• Options read the observed window (Nk: 110 / 30 / 125 → 132 / 36 / 150).<br>**Residue:**<br>• Several manifest strings are rendered as facts but are typed: the WAIT reason, the Protect-effect horizon and penalties, the SLA "restore due", and the outcomes detail (M3).<br>• The Q15 fact `shortfall_backed_by_generator` is a typed 0/1, although it can be derived from kW (L2).<br>• "62,000 kWh a month" and "near 0%" are typed where option nodes exist (L5). |
| **2. The causal step is hand-entered** | **Not resolved for one plan-deciding step** | **High (H1)**, Low (L1) | **Typed dependency:**<br>• `plans.lakeside-power.requires_any: {MTO-HULLER: [MTO-INV-BUYNOW, "switch:loi_extended"]}` encodes, by hand, "a 28 Nov restore cannot connect before the 30 Nov lapse".<br>• The mock-up's typed row `['Rice huller','lost','kept if the letter is extended','kept']` (loop-decisions.js:287) restates it.<br>**What it gets wrong:**<br>• LT7 (claim lead time 21 → 7 days; restore 14 Nov) still drops the huller without an extension, and still buys now at 6,500.<br>• LS20 (local supply 5 → 20 days; restore 26 Nov, which cannot connect by 30 Nov) still values the huller at +3,540.<br>• RA, X1 and H1n connect the huller while choosing **no action** on the inverter.<br>**Restore after a denied right** is still half-modelled (L1). |
| **3. Thika, Kasarani and Ruiru are not evaluated** | **Resolved** | none | All nine sites are evaluated. Ruiru's plan is honestly "not decomposed: stated total (missing leaf kwh)", and its actual and November-to-date are evaluated.<br>Perturbations move each of them:<br>• RC: Thika self-repair, Harvest +1,670 at 980.<br>• RB, E2, E3 and E5: Kasarani.<br>• E4, author's run: Ruiru. |
| **4. Rights sit outside the structure** | **Mostly resolved** | Medium (M5), Low (L1, L3) | **Resolved:**<br>• Netting under a flip is correct (RB, hand-checked below).<br>• The supplier restore follows `covered()` where `performed_under` is declared.<br>• KAS-LOCAL voids CH-K2 (lost 380; fails the bound).<br>• The Mto lapse is structural (X1, H1n).<br>**Residue:**<br>• The lapse applies only to options carrying a hand-placed `asset:` key, which only the three Mto options have. GT1 puts an already-passed, un-notified deadline on Thika's right: 2 leaves move and **all 1,040 checks pass** (M5).<br>• Mto CLAIM keeps the supplier's 21-day lead under a denial, and WAIT paths pay the repair yet never restore (L1).<br>• MTO-INV-LOCAL is still a hand disposition (L3). |

### Findings

**H1 (High): the rice-huller's dependence on the inverter restore is typed, so plans are wrong when restore dates or rights move.**
- **Where:**
  - `demo-site-scenario-manifest.yaml` `plans.lakeside-power.requires_any` (MTO-HULLER needs BUYNOW or `switch:loi_extended`).
  - Row MTO-HULLER: `connection_lead: "5 working days after the inverter is restored …; a 28 Nov restore cannot connect before the 30 Nov lapse"` (text only), and `depends_on: [MTO-INV restored]` (not read).
  - `interactive-mockup-vNEXT/loop-decisions.js:287`: the typed huller row.
- **Evidence (scratch):**

| Run | Change | Result | Correct result |
|---|---|---|---|
| LT7 | `lead_time_days` 21 → 7 (claim restore 14 Nov, connectable by 21 Nov) | 5,000/no still drops the huller (2,636.00). 6,500/no still buys now (3,508.50 at 6,430). | Claim + huller in both cases (about 6,176). |
| LS20 | `local_supply_days` 5 → 20 (buy-now restore 26 Nov; 5 working days → 3 Dec, after the 30 Nov lapse) | 6,500/no still includes the huller at +3,540 (3,414.75). | The huller is lost. |
| RA, X1, H1n | Mto claim denied; no-action files notice; deadline already passed | Plan = KIS-REPAIR, BAT-EVIDENCE, KOB-STOPSOC, **MTO-HULLER, MTO-INV-NOACT**: +6,299.75 at 3,520. | The inverter is never restored, yet the 15 kW daytime huller is connected and valued for 12 months. The screen row says "Rice huller: lost" for no action, while the plan contains it. |

- **Why it matters:** this is the owner's governing principle (point 2). This step decides the Lakeside switch cases and the CONDITIONAL disposition of MTO-INV-BUYNOW. Its admissibility is typed, not produced by the structure.
- **Fix:**
  1. Declare `connection_lead` (5 working days) and the letter's lapse date (30 Nov; the extended date under `loi_extended`) as records.
  2. Make MTO-HULLER require that `restore_date` of the chosen INV-MT-02 option + `connection_lead` ≤ the lapse date. Evaluate this in `best()`, and treat no restore as not connectable.
  3. Delete `requires_any` for the huller.
  4. Derive the mock-up row and the CONDITIONAL condition text from the result.
  5. Add LT7 and LS20 to the perturbation set.

**M1 (Medium): protective choices are fixed one at a time, so the allocator is non-monotonic in budget and can pick a worse plan.**
- **Where:** `evaluate_structure.py` `protect_choice()`, where `afford` tests each option alone against the whole budget and visit limit, and `best()`, which fixes the protective picks before enumerating the rest.
- **Evidence:**
  - **B2000** (budget switch 2,000): every 2,000 case is **infeasible**.
  - **B1500** (1,500): feasible, with KIS-NOACT as the least violation, +2,548.50 at 750. A larger budget gives no plan while a smaller one gives a plan.
  - **CR2** (crews 3 → 2): infeasible, although the declared Kisiwa fallback (no action, 0 visits) gives a plan within 2 visits (BAT-EVIDENCE + claim).
  - **RC** (Thika EXPIRED): THIKA-SELF (710, **1 visit**) is chosen over the stopgap (810, 0 visits) on one-off cost alone. That uses the visit and drops KIRI-REPAIR, so Harvest is +1,670.00 at 980. The joint optimum, stopgap + Kirinyaga + Mwea, is **+3,182.40 at 1,430**, within 2,500 and 2 visits.
  - The author reported RC as "crews now bind"; they do, but the allocator then resolves the binding wrongly.
- **Fix:** enumerate the protective decisions inside `best()`'s product. Allow only options meeting their hard bounds, or the declared least violation, judged jointly against the remaining budget and visits. Rank by (violation, then plan value, then spend). Report the trade-off from the joint result.

**M2 (Medium): RA's "no action" result is a horizon effect from mixed valuation periods, and the pack does not disclose it.**
- **Where:** MTO-INV-* use `months: 1` (to the horizon), so a restore path is valued over 6–30 Nov (25 days), while the competing valued options use 12 months. `horizon_months: 12` is the tenant's declared horizon.
- **Evidence:**
  - Under RA, no action costs 25 × 5 L × 1.25 = **156.25**, against the denied claim's 2,830 + 137.50 = **2,967.50**.
  - Over the declared 12 months, no action costs about 2,281 in fuel and still leaves the inverter out, which blocks the huller (H1).
  - "Horizon effect" appears only in REVIEW-response.md. `grep` finds nothing in the questions file, the main document or the screens.
  - The response's remedy, "Q15 (B) would reject it", uses a breach policy to fix a valuation and dependency error.
- **Fix:**
  - Value the restore-path decision over the tenant horizon: reduced days to the restore, and "not restored" through the horizon end. Alternatively, carry "not restored at horizon end" as a declared Protect node.
  - State the behaviour in the questions file.
  - With H1 fixed, RA should restore (claim or buy) and keep the huller.

**M3 (Medium): typed manifest strings are rendered as facts and do not follow the structure.** This is the rev 11 M5 pattern, moved from `loop-*.js` into the manifest.
- **Evidence:** I rebuilt in scratch with E5 (SLA 8 business days) + E3 (spare 3 → 2) and captured the screens headless. Most figures moved, but these stayed:
  - **The WAIT rejection reason** ("Likely 2 missed departures in the 3 nights to 9 Nov … $240 … against $90") is shown on `#/decision/kasarani-charger` and Metro `#/portfolio/act-first`. The evaluator says 5, 6 nights, 12 Nov, $600 and $225.
  - **The Protect-effect table.** The horizon reads "until the 9 Nov restore", and the row reads "Wait … 5 | **$240** | Calculated from records". The departures are evaluated; `protect_effects.penalties` is typed and never checked.
  - **The rights panel** shows "Restore due 9 Nov · 3 days left · 9 Nov" (`sla_clock.restore_due`) on the same page that says "restore on 12 Nov".
  - **Outcomes by site:** "spare bus lent on 3, departure missed on 2" sits under the row that shows 3.
  - **E3+ with the checked protect fields updated:** the only failures left are document anchors. These strings pass.
  - `tools/hand_typed_scan.py` scans only `loop-*.js` literals, and only those equal to *current* evaluated figures, so it cannot see these strings.
- **Fix:**
  - Render the reason, horizon, penalties, `restore_due` and detail from the evaluated fields.
  - Or check each one in `derived()`: `protect_effects.penalties` against −Δcontribution, `sla_clock.restore_due` against the WAIT `restore_date`, and any digits in a rendered `reason` or `detail` against the evaluation.

**M4 (Medium): the anchor coverage rule is narrower than the response claims.**
- **Where:** `check_manifest.py` `key_figures()` and the coverage regex `\d{1,3}(?:,\d{3})*\.\d{2}` (cents only). `documents()` excludes `%` and covers only main §2–§10 and the walkthroughs.
- **Planted drifts (scratch):**

| # | Drift | Result |
|---|---|---|
| Dn1 | contracts "budget ≥ 6,430" → 6,340 (the plan's 6,500/no spend, written without cents) | **passes** |
| Dn2 | models "137.50 → **367.50" → 173.50 (the arithmetic is now wrong) | **passes** |
| Dn3 | phase plan "98.62%" → 96.82% | **passes** |
| Dn4 | Q15 "at 6,430" → 6,340 | **passes** |
| Dn5 | Q15 "pays 2,580 more" → 2,850 | **passes** |
| Dn6 | main "availability 98.62%" → 96.82% | **passes** |
| Dn8 | contracts "4,560.00" → 4,650.00 | **passes** |
| Dn7 | models sign flip on anchored −1,988.40 | caught |
| Dn9 | walkthrough +$95,634 → 95,643 | caught |

- **Fix:**
  - Match whole-dollar forms of key figures.
  - Add `monthly_or_horizon_change` and the O2 portfolio and site percentages to the key set, and allow `%` in the main-document scan.
  - Anchor the figures in the owner question Q15: 6,430, 2,580, and each option's case figures. The (C) figure is currently anchored to the live (A) path `6500/False.value`, which only coincides with it.

**M5 (Medium): the notice-deadline lapse reaches only options that carry a hand-placed `asset:` key.**
- **Where:** `evaluate_structure.py` `run()`, `if a == spec.get("asset") …`. Only MTO-INV-CLAIM, BUYNOW and NOACT declare `asset:`.
- **Evidence:**
  - **GT1:** Thika's right set to `claim_state: POTENTIAL` with `notice_deadline: "2026-11-05"` (passed, as_of 6 Nov). **2 leaves move; 1,040 checks pass**, and WAIT stays `POTENTIALLY_COVERED` with 710 claimable.
  - **GT2:** GT1 plus `asset:` on THIKA-EPC-WAIT. WAIT lapses, 710 is lost, and the bound fails.
  - A deadline that has already passed is a state at `as_of`, but it is only ever evaluated per option.
  - Ruiru's POTENTIAL CH-R7 claim ("claim at next routine visit") has no notice term recorded.
- **Fix:**
  - Derive which options decide a right from the rights each option touches (`covered_by`, `performed_under`, `voids_rights`, `files_notice`) or from its decision.
  - Evaluate a deadline already passed at `as_of` as LAPSED for every option.
  - Have the checker require that every right with an open deadline has deciding options.
  - Record CH-R7's notice term, or state that there is none.

**L1 (Low): restore under a denied right is half-generalised.**
- Under RA, MTO-INV-CLAIM still restores on 28 Nov by the supplier's 21-day lead while the operator pays the 2,600 (it has no `performed_under`).
- Under RB and RC, WAIT and STOPGAP pay the repair line (380, 710) but restore "none".
- *Fix:* when a right is not covered, switch the restore driver to the operator's own procurement (a quote), and pay the line once.

**L2 (Low):** `physical.shortfall_backed_by_generator` (0 at Kisiwa, 1 at Mto) is typed, yet it decides Q15 (A). It can be derived from records: at Mto, genset 30 kW ≥ the 25 kW inverter lost; at Kisiwa, the backup is 0, with the battery at reserve.
- *Fix:* min(1, backup kW / lost kW) as a node.

**L3 (Low):** MTO-INV-LOCAL ("opening the unit voids the warranty; dominated") is still a hand disposition. The KAS-LOCAL evaluation was not generalised to it.

**L4 (Low):** of the scan's 30 allow-list entries, the no-allow run shows that only 8 hits are suppressed, so 22 entries suppress nothing. Matching is by fragment, so entries such as '80%' or '30 kW' would also mask a future restatement of an evaluated figure.
- *Fix:* keep only the entries in use, and key them by file and line.

**L5 (Low): typed figures remaining on screen.**
- Embakasi "55% / near 0% / 0%": both options set `peak_kwh` to 0, so "near 0%" disagrees with the structure.
- "about 62,000 kWh a month" = the DEADLINE node `kwh_0000_0500` (400 × 5 × 31). It is evaluated but not exported, so the scan cannot see it.
- "184 kWh (92%)": the 92% is computed by hand from a record.
- "406 kW" is a spike-E basis, which is acceptable.

**L6 (Low):** `incident.roster.spare_free_nights_to_restore: 1` is a count tied to the base 3-night window, but it is applied unchanged to 6 nights (E5) and 25 nights (RB).

### Prior findings (rev 11), verified

| # | Status | My evidence |
|---|---|---|
| H1 | **Resolved as stated; generality partial (M5)** | `grep` finds no `bound_failure`, `admissible:` or `money:` string in the manifest, and the evaluator no longer reads them.<br>X1 (NOACT files notice) → +6,299.75 at 3,520.<br>H1n (deadline 3 Nov) → no action.<br>KOB-RESERVE is rejected by the declared `dawn_adequacy` bound.<br>The lapse is structural, but it reaches only Mto (GT1). |
| M1 | **Resolved** | RB (Kasarani DENIED), by hand:<br>• WAIT: restore none, so 25 nights − 1 spare = 24 missed, 2,880 penalties, 380 borne.<br>• STOPGAP: 24 × 45 + 380 = 1,460; value 2,880 − (1,460 − 380) = **+1,800.00** ✓.<br>• LOCAL: restore 7 Nov, 0 missed, 380 (lost 0, since the right is already denied); value 2,880 − (380 − 380) = **+2,880.00** ✓.<br>• Metro 95,634 − 150 + 2,880 = **98,364** at 1,880 ✓.<br>RA claim: −137.50 − 2,830 = **−2,967.50** ✓. |
| M2 | **Resolved; joint allocation open (M1)** | CR2 infeasible; RC binds (Harvest 2/2). |
| M3 | **Partly resolved** | L2 reproduces: repair kept, KIS-REPLACE reported as the trade-off (105 h, 9,500).<br>The Mto/Kisiwa policy is now one rule plus a declared fact (Q15).<br>Affordability is per item (M1). |
| M4 | **Partly resolved** | Signed anchors work (Dn7), headlines are anchored, and E3+ is caught by the November anchors. Coverage gaps remain (M4). |
| M5 | **Partly resolved** | The loop literals now read DERIVED (the E5 + E3 screen diff follows on 4 routes). Typed manifest strings remain (M3). |
| L1 | Resolved | E2 → wait 3 missed, stopgap +225 (34 moved). Nk → options 132 / 36 / 150. |
| L2 | Resolved | Three-record expression. The author's L2t was not separately rerun. |
| L3 | Resolved (as an assumption) | THIKA-SELF has a declared procurement driver of 0 days. |
| L4 | Partly resolved | Restore follows rights where `performed_under` is declared; KAS-LOCAL is evaluated; Mto is not (L1, L3). |
| L5 | Resolved | The forward baseline resets `reduced_days` / `uncovered_nights`. |
| L6 | Resolved | L6t (6,000 kWh) is caught by the new record-consistency check. |
| L7 | Resolved | Protect and detail nodes are declared per vertical. The only vertical branch left in the evaluator is the EV_DEPOT → EV_DEPOT_CAPTIVE alias. Dispositions are checked. |

### Q15 (redundancy policy)

- **The options are fairly and correctly described.** I ran each one in scratch:
  - **(B)** bound node → `obligation_hours_without_redundancy`: 5,000 cases unchanged; **6,500/yes and 6,500/no both 3,508.50 at 6,430 (buy now)**, as stated. "Pays 2,580 more" is the net value lost (2,680 extra spend − 100 of fuel saved), which is correct as a net figure.
  - **(C)** advisory at both sites: Kisiwa → **no action; spend 1,950, 2 visits; 5,000/no → +3,508.50 at 4,630 (buy now)**, as stated. The 6,500/no case also falls to 4,630 at the same value; the text "values otherwise as (A)" is accurate.
- **Applying (A) pending the answer is appropriate and disclosed.** It leaves the reviewed plans unchanged. It is written as "(A) applied pending your answer" in the questions file, and it is listed in the owner checklist with routes.
- **Two caveats:**
  - The fact on which (A) rests is a typed 0/1 (L2).
  - The client screen states "redundancy met" as settled. That is acceptable for client-facing copy, given the checklist entry.
- (A) is not a workaround for H1. Under RA, (A) admits no action and H1 then connects the huller.

### Perturbation table (my runs, scratch copies; checker base 1,040)

| # | Change | What moved | Checker |
|---|---|---|---|
| RA | Mto claim DENIED | claim −2,967.50; **plan = NOACT + HULLER, +6,299.75 at 3,520** (H1, M2) | caught (spike set) |
| X1 | NOACT files notice | same plan as RA (H1) | caught |
| H1n | Mto deadline 3 Nov | all paths lapse; no action chosen with huller | caught |
| LT7 | claim lead 21 → 7 d | 5,000/no 2,636.00 still without the huller; 6,500/no still buys now (H1) | caught, but the plan structure is wrong |
| LS20 | local supply 5 → 20 d | 6,500/no 3,414.75 still includes the huller (H1) | caught, but the plan structure is wrong |
| RB | Kasarani DENIED | local repair chosen; stopgap +1,800, local +2,880; Metro 98,364 at 1,880 | caught |
| RC | Thika EXPIRED | THIKA-SELF chosen; Harvest **+1,670.00 at 980** (joint optimum 3,182.40 at 1,430) (M1) | caught |
| CR2 | Lakeside crews 3 → 2 | every case infeasible (M1) | caught |
| B2000 | budget switch 2,000 | **both 2,000 cases infeasible** (M1) | caught |
| B1500 | budget switch 1,500 | Kisiwa no action; +2,548.50 at 750 | caught |
| L2 | Kisiwa visit 29 Nov | repair kept (120 h); trade-off KIS-REPLACE 105 h / 9,500 | caught |
| Q15B | redundancy on any unit out | 6,500/yes → 3,508.50 at 6,430 | caught (documents) |
| Q15C | redundancy advisory | Kisiwa no action; 1,950; 5,000/no 3,508.50 at 4,630 | caught (documents) |
| E5 + E3 | SLA 8 bd; November spare 3 → 2 | restore 12 Nov; stopgap +375; Metro 95,859 at 1,725; Nov 3 missed / $360. **The screen keeps "9 Nov", "2 missed … $240 … $90", "5 \| $240", and "lent on 3, missed on 2"** (M3) | 73 FAIL |
| E3+ | E3 with the protect table updated | only document anchors fail; the typed detail string survives (M3) | 6 FAIL (anchors only) |
| E2 | `spare_buses` 1 → 0 | wait 3 missed; stopgap +225 | caught |
| Nk | Mto window 5 → 6 h | October 24 h; options 132 / 36 / 150 | caught |
| L6t | Kasarani Nov kWh 6,000 | record-consistency fails | 1 FAIL |
| GT1 | Thika un-notified, deadline 5 Nov (passed) | 2 leaves; WAIT keeps 710 claimable | **1,040 pass** (M5) |
| GT2 | GT1 + `asset:` on WAIT | WAIT lapses (710 lost) | caught |
| Dn1–Dn6, Dn8 | document drifts (M4) | — | **all pass** |
| Dn7, Dn9 | sign flip; walkthrough headline | — | caught |

### Regression checks

- **Evaluator and checker.**
  - `python3 evaluate_structure.py`: 9 sites, 27 options, 3 plans. Its output is byte-identical to the working-tree `derived-values.json`.
  - `python3 check_manifest.py`: **1,040 passed, 0 failed** (1.3 s).
  - `tools/hand_typed_scan.py`: **0** hits, with 30 allow-list entries. Without the allow-list there are 8 hits, all legitimate.
- **Scratch rebuild.** I ran `evaluate_structure.py`, `rebase_v70.py`, `gen_fixtures.py` ("0 differences", 28 replay patterns), `node build.mjs` and `gen_docs.cjs`. `diff -rq` against the working tree shows **no differences** (byte-identical).
- **Preserved screens.** `screens.js`, `portfolio.js`, `outcomes.js`, `*.css`, `src-v70-baseline` and `screen-manifest-vnext.json` are not in the diff since `f55f15716`. I did not rerun the audit's 65/65 text comparison.
- **Wording, filters and menus.** The added `loop-*.js` lines contain no `<select>`, no role or question wording and no new menus. The only matches were JS `.filter()` calls.
- **Generality.** The evaluator has no vertical names except the EV alias, and the bounds and Protect nodes are declared per vertical. The residue is in M5 (lapse scoping).
- **Headless spot check.** I used Playwright with Chromium 1140 against a static server on **port 8783**, which I stopped afterwards; I did not touch ports 5490 or 8990.
  - I checked 12 routes (the Kasarani, Mto, Kisiwa, Kobo, Thika, Ruiru and Embakasi decisions; the Kasarani site page; outcomes by site; act-first for all three tenants) at 1440 and 390 px, on the base build and the E5 + E3 build.
  - **0 page errors and 0 overflow at 390 px.**
  - **Mto:** "Fails the cover bound: no notice is filed, so the warranty lapses on its 27 Nov deadline and $2,600 of cover is lost".
  - **Kisiwa:** "the least violation is chosen: Repair generator 1 … 15 h".

### Remaining hand inputs that matter

| Input | Where | Status |
|---|---|---|
| `requires_any` MTO-HULLER, and the typed huller row | plans; loop-decisions.js:287 | **typed causal step (H1)** |
| `asset:` per option | evaluation | hand scoping of the lapse (M5) |
| `shortfall_backed_by_generator` 0 / 1 | physical | typed fact behind Q15 (L2) |
| WAIT `reason`, `protect_effects.horizon` / `penalties`, `sla_clock.restore_due`, protect `detail` | rows / portfolio | typed, rendered and unchecked (M3) |
| `spare_free_nights_to_restore` 1 | incident roster | a fixed count (L6) |
| 55% / near 0%, 62,000 kWh, 92% | loop-decisions.js | typed (L5) |

Everything else listed in the rev 11 table is now either evaluated or labelled as a quote, assumption or design value.

### Convergence

Author work remains. It is targeted, but H1 is a genuine plan-deciding causal step:

1. **H1:** a dated huller dependency evaluated in `best()`.
2. **M1:** joint enumeration of the protective choices.
3. **M2:** a consistent horizon for restore paths, and disclosure.
4. **M3:** derive or check the rendered manifest strings.
5. **M4:** widen the coverage rule and anchor Q15.
6. **M5:** derive which options decide a right, and evaluate an already-passed deadline.

The L items can ride along. The owner decisions are Q1–Q15. Q15 is correctly posed, and (A) is an appropriate interim choice. After this round I would expect only owner decisions to remain, provided H1 and M1 are fixed without new typed rules.

### Not verified

- I did not rerun `tools/run-audit.sh`. The 202-route, contrast, focus, design-value-scan and 65/65 text-identity figures are the author's numbers.
- I did not rerun the CSV validator.
- I did not rerun the author's K1, M3b, L2t, Dj–Dm or M1t individually.
- I did not verify the replay design values; they belong to the calibration lane.

---

## Final review (rev 13)

**Reviewer:** a fresh, independent Claude reviewer, 17 Nov 2026. I reviewed the rev 13 working tree on `task/product-direction-layer4-design`: the uncommitted diff over `f5c705e25` plus the five untracked files. I ran every experiment in scratch copies (harness `scratchpad/fr13/pt.sh`; "moved" counts changed leaves of `derived-values.json`; "fail" counts `check_manifest.py` failures). Appending this section is my only edit.

### Verdict: **ACCEPT WITH NOTES** (two small screen fixes, F1 and F2, before the owner inspects)

The rev 12 structural findings are fixed, and I confirmed each one by hand:

- The rice-huller dependency is now dated.
- The allocator is joint.
- The horizon is disclosed.
- The deciding options are derived.

The three figures that changed are correct, and they were reported. The evaluator and the independent model agree under every input perturbation I ran (32 runs). A planted bug in either program is caught when it changes a compared field. The rebuild is byte-identical.

**Two screen defects state wrong figures or wrong claims.** Neither affects a plan or a headline.

- **F1.** In 3 of the 4 Lakeside switch cases, the plan-value drawer lists the wrong options and figures.
- **F2.** The plan page says "Largest …" next to an option that is not the largest.

Both are short fixes, and they are the only items I put in class (i).

**Where the pack overclaims is the register and the checker coverage, not the evaluation.**

- About half of the numeric manifest leaves that the register classes (c) "affects no figure" are rendered on screen, and nothing checks them (F3).
- The checker skips the two option fields that the screens actually read (F4).

These items are not wrong today. They are the remaining places where a figure can drift without any check failing, and owner rules 1 and 2 asked for exactly this class to be closed or declared.

### Owner rules (twelfth message)

| Rule | Status | Severity, class | Evidence |
|---|---|---|---|
| **1. Figures are outputs, never targets** | **Met for every evaluated figure; not met for some rendered typed copies** | Medium (i) F1, F2; Medium (ii) F3; Low (ii) F6 | **Met:**<br>• `requires_any`, `asset:`, `sla_clock.restore_due` and `protect_effects.penalties` are gone (`grep`: 0).<br>• Every numeric change between rev 12 and rev 13 in `derived-values.json` is one of the three reported figures (8 numeric leaves). The exception is KAS-LOCAL's cost per departure met, 23.71 → 24.29, which is shown on the Kasarani page but not listed (L5).<br>• The screens move under the structure: under RO (Kasarani roster, 7 Nov spare night removed), the WAIT reason, the penalties, the cover cost, Metro +95,709 and the downside all follow on 3 routes.<br>**Held in place:**<br>• `allocation.modelled_12m_change` keys fix the rows of the Lakeside plan-value drawer across switch cases (F1).<br>• `WHY_FIRST` "Largest …" claims (F2).<br>• Under RO, loop-decisions.js:335 still says "the spare bus on one night, a bus charged at Ruiru on the others", although the evaluation says 0 spare nights and 3 nights at Ruiru (F6).<br>• The manifest `oracle` holds expected figures (spend 3,750 and 6,430, 12,975 and 13,356 a month, 8,082.00, 395 a month). Nothing reads it, but it is a target list, and it is outside the register (L1). |
| **2. The derivation register is complete** | **Not met as stated** | Medium (ii) F3; Low (ii) L1, L2, L3 | **I re-ran the register's own claim on every numeric (c) leaf.** I perturbed each one alone (×1.1 + 1) and ran the checker:<br>• **477** numeric leaves are classed (c) in §3.2.<br>• **225** are caught by a model or stated check.<br>• **9** are caught only by the document scan.<br>• **243 are caught by nothing.**<br>Many of those 243 are rendered derived figures, and the register text says "checked (stated())" or "numbers … are … checked literals". Examples:<br>• `listed_not_summed` (672, 70, 64,000, 60,000): N69 claims stated() checks them; it does not.<br>• MTO-BILLING `charges_monthly` / `charges_12m` (140 kWh × 0.40).<br>• MTO-HULLER `revenue_monthly` 495 and `fuel_monthly` 85. Under PT35 (productive tariff 0.30 → 0.35) the screen formula would read "1,650 kWh × $0.35 = $495", and no check names it.<br>• `forward_replay.avoidable_fuel_l` 210 and `extra_fuel_l` 68 are typed copies of the K and M design-value params. The screen reads the copy and the evaluator reads the param.<br>• `portfolio_constraints.budget_usd_nov_dec` (shown on screen) is a second copy of `plans.*.budget` (read by the evaluator), and the two are never compared.<br>• `coverage.cost_recorded_share`, `occupancy_pct` and `KAS-OEM-STOPGAP.nights` 2 ("in total for 2 bus-nights").<br>**Site variances and bridge amounts** are typed. They are checked only against each other, never against the evaluated contributions. V1 (Mto variance −105 → −110 with one bridge line adjusted) gives **0 model or stated failures**; only an untagged "852.00" in the main document trips. All 9 sites agree today; I recomputed actual − plan from the nodes.<br>**The 13 items no perturbation reveals (§8):** H2 is wrong as written ("only one decision is ever on its fallback"). G20 (Mto genset 30 → 20 kW) puts Kisiwa and Mto on their fallbacks together, and MTO-INV-LOCAL / NOACT then add 2,600 dollars to hours (L2).<br>**§7 is partly stale.** Rows 136, 147 and 169 describe code that was fixed after hand-back. Several L-RS rows restate DERIVED figures, not records (row 170, the F6 sentence; 175; portfolio row 33).<br>**Coverage.** "Every leaf (2,438)" excludes 175 of the manifest's 2,613 leaves, including `oracle` and `checks` (L1).<br>**The derived items I sampled do move**, and I confirmed each by hand: A10 and A16 (LT7, LS20), A11 (RA), A13 (RO), A14 (G20), A18 (B2000, B1500, CR2, RC) and A8 / A9 (GT1). |
| **3. Checks are independent** | **Met for code and lists; coverage gap** | Medium (ii) F4; Low (ii) L4 | **Independence holds:**<br>• `check_manifest.py` imports only `independent_model.py` and reads `derived-values.json` as data.<br>• It holds no expected figure. Its only literals are thresholds, a naming map and the `REQUIRED` anchor paths.<br>• `independent_model.py` shares 9 trivial lines with the evaluator (`ast` node tests, `if __name__`). It is structurally different (a class with phases against closures) and records 26 spec ambiguities.<br>**My plants:**<br>• IM1, the model's ranking key changed: **281 fail** (caught).<br>• EV2, business days counting weekends: **45 fail** (caught).<br>• EV5, spend tie-break reversed: **12 fail** (caught, through Q15 C).<br>• **EV1**, evaluator option `value` / `valued_in_money` set for every option: EMB-CHEAPEST +101,556, MTO-INV-NOACT −2,281.25 and KAS-LOCAL −260 become "valued". **0 fail.** `NOT_COMPARED = {"money_changes","value"}` skips exactly the fields that loop-decisions.js:56 reads (F4).<br>• EV6, protective "how" text: **0 fail**, presentation only.<br>• **SP1**, spec §6.3 ranking and §6.2 business days → calendar days: **0 fail**. The checker never reads the spec, so spec-to-model conformance rests on authorship. Both files are untracked with identical mtimes, so I cannot verify that the specification came first (L4).<br>**Same method:** the model's `solve()` uses the same exhaustive product and the same key as `best()`. The spec prescribes this, so a spec-level error is shared (register §8 says so). |
| **4. The specification came first, and data, code and screens conform** | **Mostly met** | Medium (ii) F4; Low (ii) L3, L6 | **Complete for:** factors and layers (§3), rights (§4.1), restore and horizons (§2.1, §4.2), limits and bounds (§5.6, §6.1), plans (§6) and declared input classes (§1).<br>**Divergences:**<br>(a) The plan-facing option `value` / `valued_in_money` (evaluator line 507: admissible, or chosen and changes money) is not defined in the spec, yet it drives the screens (F4).<br>(b) Spec §7 forbids literals of evaluated figures in screen code, but not screens reading manifest stated copies of evaluated figures. That is how F1 got through.<br>(c) The evaluator docstring (lines 22–26) still describes the rev 12 allocator ("cheapest affordable option … one at a time"), which contradicts the code and spec §6.3 (L6).<br>(d) Fallback eligibility is static: "no option meets the bound at all". CR1 (crews 1) and B600 (budget 600) are **infeasible**, although declared fallbacks (Mto no action, 0 visits) would give a least-violation plan. This conforms to the spec, but it is narrower than the rev 12 M1 fix asked for (L3). |

### Coordinator points (eleventh message)

| Point | Status | Severity, class | Evidence |
|---|---|---|---|
| **1. Money layer only** | **Resolved for the evaluation; one attribution layer is still typed** | Medium (ii), inside F3 | **Evaluated and moving under perturbation:** value chain, physical split, Protect, O2, rights, restore and Q15 backing (G20, RO, UM, GT1).<br>**The residue is the factor bridge**, the per-driver attribution of each site's variance. It is typed and checked only for internal sums (V1), although every amount except Ruiru's is computable from evaluated nodes. |
| **2. Causal step hand-entered** | **Resolved as declared inputs** | Low (ii), inside F3 | **Plan-deciding steps are structural:** the huller dependency is dated (LT7, LS20, RA hand-checked) and the lapse is derived (GT1).<br>**The remaining causal magnitudes are declared, labelled inputs:** Kobo 210 L and 150 kWh (K), Mto 68 L and 5 L/day (M), Kisiwa 150 L (assumption), Kirinyaga recovery 80% (assumption).<br>**Residue:** typed display copies of K and M (`forward_replay.*`) can diverge from the params after calibration (F3). |
| **3. Thika, Kasarani and Ruiru not evaluated** | **Resolved** | none | All nine sites are evaluated (Ruiru plan "not decomposed: stated total", labelled).<br>RC: Thika EXPIRED → joint optimum **+3,182.40 at 1,430**.<br>RO: Kasarani roster → WAIT 3 missed, stopgap 135 / +225, Metro 95,709 (hand-checked). |
| **4. Rights outside the structure** | **Resolved** | Low (ii), allow-listed shares | **Rights decide who pays, lapse and restore drivers:**<br>• RA: claim refused → the claim restores 12 Nov through own procurement, 1 visit, one-off 2,830.<br>• GT1: Thika un-notified with a passed deadline → caught (37 fail).<br>**Residue:** rights evidence shares ("1 of 3 → 2 of 3") are typed and allow-listed, which is disclosed. |

### Rev 12 findings, verified with my own runs

| # | Status | Evidence (hand recomputation) |
|---|---|---|
| **H1** | **Resolved** | `requires_any` = 0 in the manifest, the evaluator and the model.<br>**LT7** (lead 21 → 7): claim restores 14 Nov (Sat); +5 working days = 20 Nov ≤ 30 Nov. Claim fuel 8 d × 5 L × 1.25 = 50, so claim value −280. Plan = 2,916 + 3,540 − 280 = **6,176.00** at 3,750, every case ✓.<br>**LS20** (local supply 5 → 20): buy-now restores 27 Nov (Fri); +5 working days = 4 Dec > 30 Nov, so no huller. 6500/no = 2,916 − 367.50 = **2,548.50** at 2,550 (claim; buy-now without the huller would be −125.25) ✓.<br>**RA** (claim DENIED): local repair restores 8 Nov, voids nothing left to lose, admissible: −2 × 5 × 1.25 − 450 = −462.50. +5 working days = 13 Nov, so the huller is kept. Plan = 2,916 + 3,540 − 462.50 = **5,993.50** at 3,970, 3 visits ✓. No action is admissible here but valued −2,281.25 and cannot connect the huller.<br>The Mto page derives the huller row per path ("connected by 4 Dec, after the 30 Nov lapse" / 19 Nov / 13 Nov / "never restored"). |
| **M1** | **Resolved for the reported cases; residual L3** | **B2000** → +6,088.50 at 1,950 (Kisiwa no action, violation 125) ✓.<br>**B1500** → +2,548.50 at 750 ✓.<br>**CR2** → feasible, Kisiwa no action, 2 visits ✓.<br>**RC** → +3,182.40 at 1,430 (stopgap 810 + Kirinyaga 350 + Mwea 270) ✓.<br>**CR1** and **B600** are infeasible although the Mto fallback exists (L3). |
| **M2** | **Resolved** | Mto no action: 6 Nov 2026 to 5 Nov 2027 = 365 d × 5 L × 1.25 = **−2,281.25** ✓.<br>A33 and the Mto page ("Fuel is counted to the restore date, or for 12 months if the inverter is never restored; service hours are counted to 30 Nov") ✓. |
| **M3** | **Resolved for manifest strings; residual F6 in code** | RO screen diff: the reason, penalties, cover and Metro totals follow. The typed "spare bus on one night" stays (F6). |
| **M4** | **Resolved for key figures; residual L5** | **Caught:**<br>• Dr1, contracts whole-dollar 6,430 → 6,340: 1 fail.<br>• Dr2, phase-plan 98.62% → 96.82%: 1 fail.<br>• Dr3, an untagged 3,508.50 in the models document: 1 fail.<br>**Passes:** Dr4, a wrong untagged figure that equals no key ("Mto claim costs 376.50") before main §2: **0 fail** (L5). |
| **M5** | **Resolved** | `asset:` is gone. Deciders are derived (`out["deciders"]`). GT1 is caught. |
| **L1** | **Resolved** | RA: the claim switches to `if_not_covered`: 12 Nov, 1 visit, 2,830 borne. |
| **L2** | **Resolved** | G20 (genset 20 < 25 kW lost): `shortfall_backed` 0. The Mto options now violate redundancy; 6500 cases pick buy-now (violation 45). |
| **L3** | **Resolved** | MTO-INV-LOCAL: restores 8 Nov, −462.50, cover lost 2,600, inadmissible ✓. |
| **L4** | **Resolved** | `hand_typed_scan.py`: 0 hits in code and in 216 rendered manifest strings; 46 entries, 0 unused. |
| **L5** | **Resolved** | Embakasi peak share comes from nodes ("near 0%": 0 occurrences).<br>Allow-listed Mwea +0.6% = 15 / 2,635 = 0.57% ✓, Kirinyaga 24% = 970 / 4,030 ✓, chargers 600 / 720 kW ✓, payback 14,000 / 195 = 71.8 months ≈ 6 years ✓. |
| **L6** | **Resolved** | Dated roster: KAS-LOCAL restores 7 Nov, has no free night on 6 Nov, so 1 missed, Δ +120 against WAIT, value 120 − 380 = **−260** ✓.<br>WAIT: nights 6–8 Nov, spare free on 7 Nov, 2 missed ✓. |

### Perturbation and plant table (scratch copies; base 3,255 checks)

| # | Change | What moved | Checker |
|---|---|---|---|
| LT7 | claim lead 21 → 7 d | 58 moved; claim + huller every case, **6,176.00** | 103 fail (anchors and stated) |
| LS20 | local supply 5 → 20 d | 41; no/no cases lose the huller, **2,548.50** | 37 fail |
| RA | Mto claim DENIED | 120; local repair + huller, **5,993.50** at 3,970 | 139 fail |
| B2000 / B1500 | budget switch | 226 / 230; +6,088.50 at 1,950 / +2,548.50 at 750 | 43 / 96 fail |
| CR2 / CR1 | crews 3 → 2 / 1 | 120, feasible / 237, **infeasible** (L3) | 51 / 131 fail |
| B600 | budget switch 600 | 155; **infeasible** (L3) | 98 fail |
| RC | Thika EXPIRED | 66; **+3,182.40 at 1,430** | 37 fail |
| GT1 | Thika un-notified, deadline 5 Nov | 68; lapse, 710 borne | 37 fail |
| G20 | Mto genset 30 → 20 kW | 49; two decisions on fallback; 6500 cases buy now (L2) | 4 fail |
| RO | Kasarani roster without 7 Nov | 43; WAIT 3 missed; stopgap 135 / +225; Metro 95,709. Screen follows except F6 | 75 fail |
| PT35 | productive tariff 0.30 → 0.35 | 30; huller 4,530 | 76 fail; **`revenue_monthly` 495 not among them** (F3) |
| UM / UM2 | Mto unmapped 140 → 150 kWh / plus stated copies updated | 16 / 16 | 8 / **2 (documents only)**: variance, bridge −56 and charges 56 / 672 stay stale (F3) |
| V1 | Mto variance −105 → −110, bridge −8 → −13, portfolio −852 → −857 | 0 | **0 model or stated fail**; 1 document (F3) |
| LNS | `listed_not_summed` 672 → 999 | 0 | **0** (F3) |
| SBK2 / M12 | add a non-plan item to `spend_breakdown` / `modelled_12m_change` | 0 | **0 / 0** (F1, F3) |
| EXC / SWH / REC | excluded reason / case inverter-huller labels / extra recommended id | 0 | **0 / 0 / 0** (F3) |
| EV1 | evaluator plan-facing `value` for every option | 10 | **0** (F4) |
| EV2 | evaluator business days count weekends | 56 | 45 fail |
| EV3 / EV4 | trade-off reporting disabled / `<=` → `<` on the huller deadline | 0 / 0 | 0 / 0 (not binding) |
| EV5 | evaluator spend tie-break reversed | 12 (Q15 C) | 12 fail |
| EV6 | protective "how" text | 6 | 0 (presentation) |
| IM1 | model ranking key changed | — | 281 fail |
| SP1 | spec §6.3 key and §6.2 business days edited | — | **0** (L4) |
| Dr1 / Dr2 / Dr3 | contracts 6,430 → 6,340 / 98.62% → 96.82% / untagged 3,508.50 | — | 1 / 1 / 1 fail |
| Dr4 | wrong untagged "376.50" in main document preamble | — | **0** (L5) |
| (c)-scan | each of the 477 numeric §3.2 leaves alone, ×1.1 + 1 | — | 225 caught by model or stated checks, 9 by documents only, **243 by nothing** (F3) |

### Drift table (figures that changed, rev 12 → rev 13, from `derived-values.json`)

| Figure | Rev 12 | Rev 13 | Reported | My check |
|---|---|---|---|---|
| MTO-INV-NOACT value (if admissible) | −156.25 | −2,281.25 | yes | 365 × 5 × 1.25 ✓ |
| KAS-LOCAL departures missed / value | 0 / −140 | 1 / −260 | yes | dated roster ✓ |
| KAS-LOCAL cost per departure met | 23.71 | 24.29 | **no** (L5) | shown on `#/decision/kasarani-charger` |
| MTO-INV-LOCAL | — | −462.50, 8 Nov | yes | 2 × 5 × 1.25 + 450 ✓ |

No other numeric leaf changed. Text changes (Kisiwa "how", item order) are cosmetic. 222 numeric leaves are new: 120 for the Q15 variants, 29 for MTO-INV-LOCAL, and the EV bill-line nodes.

### Findings

**F1 (Medium, class i): the Lakeside plan-value drawer shows the wrong rows in three switch cases.**
- **Where:** `loop-portfolio.js:122-123` (`planValueRecord`). The Lakeside rows come from the manifest's `A.modelled_12m_change` keys (KOB-STOPSOC, MTO-HULLER, MTO-INV-CLAIM), not from the case's `valued_options`.
- **Evidence:** headless capture of Act first → plan-value drawer.
  - **5000 / no:** the headline is **+$2,548.50**, but the rows list "rice huller +$3,540" (not in the plan) and sum to 6,088.50.
  - **6500 / no:** the headline is +$3,508.50, but the rows list "Claim the inverter … −$367.50" while the plan buys now (−$2,947.50).
  - The walkthrough's step at 6:00 switches to exactly this case.
  - The design-value note also cites "the rice huller (68 L …, $395 a month)" when the huller is out of the plan.
  - Plant M12, a non-plan key added to `modelled_12m_change`, passes the checker.
- **Fix:** build the rows from `derivedPlan(op).valued_options` with `DOPT(id).value`, as `valueNote` already does. Do the same for the design-value note.

**F2 (Medium, class i): the "Largest …" reasons on Act first are false.**
- **Where:** `loop-portfolio.js:101`, `WHY_FIRST`.
- **Evidence:**
  - Lakeside: "Largest modelled value; remote change" sits on Kobo stop setting **+$2,916**, two rows above the rice huller **+$3,540**.
  - Harvest: "Largest 12-month value" sits on Kirinyaga **+$1,512.40**, while Mwea is **+$1,670**.
  - Register §7 row 46 already flags these as UNBACKED.
- **Why it matters:** this is a wrong claim about evaluated figures on the plan screen.
- **Fix:** derive the rank from DERIVED (for example "largest of the valued options" only when it is true), or drop the comparative.

**F3 (Medium, class ii; class i if the owner treats "register complete" as a gate): rendered typed copies are classed (c) "checked" but are unchecked.**
- **Evidence:**
  - The (c)-scan above: 243 numeric (c) leaves can change with no failure.
  - The specific examples are listed under rule 2: `listed_not_summed`, MTO-BILLING charges, huller revenue and fuel, the `forward_replay` copies of the K and M params, the duplicate budget, coverage share, the KAS-OEM-STOPGAP `nights`, the site variances and bridge amounts, and the `excluded`, `recommended` and `switches[].cases` labels.
  - The register text for N3, N5, N6, N13, N19, N21–N23, N26, N29, N35, N42–N43 and N69 says these are "checked against the independent model (stated())" or are "placeholders or checked literals". For these leaves that is not so.
- **Today:** I found every one of these values correct. This is a guard gap, not a wrong figure.
- **Fix, either:**
  - render them from DERIVED or from the param (one source); or
  - add stated() checks: variance = actual − plan contribution; each bridge amount against its basis quantity × price; `listed_not_summed` against its row; `spend_breakdown` and `modelled_12m_change` key sets equal to the plan items; `budget_usd_nov_dec` = `plans.budget`; `forward_replay` copies equal to the params; and reclassify the rest as (b) with their flag.
- **Register fix in any case:** the influence scan's definition, "moves an evaluated value", misses figures that are rendered straight from the manifest. Add a second pass, "rendered on screen and not checked".

**F4 (Medium, class ii): the checker skips the plan-facing option fields that the screens read, and the spec does not define them.**
- **Where:** `check_manifest.py:82` (`NOT_COMPARED = {"money_changes","value"}`); `evaluate_structure.py:507`; `loop-decisions.js:56`.
- **Evidence:** plant EV1 makes five rejected options "valued" (EMB-CHEAPEST +101,556): **0 fail**.
- **Fix:**
  - define in spec §6.3 "the option value shown = value if admissible, or chosen on a fallback";
  - have the model compute it;
  - compare it.

**F6 (Low, class ii): typed narrative counts that restate evaluated figures.**
- **Evidence:** under RO, loop-decisions.js:335 says "the spare bus on one night … on the others", while the same page says "the spare bus covers 0, and the other 3".
- **Similar rows:** register §7 rows 170 and 175, and loop-portfolio row 33 ("6 more buses"). These restate DERIVED figures, not records, so the label L-RS ("records restated") understates them.
- **Fix:** template them from DERIVED, or relabel them.

**L1 (Low, ii): the register's "every leaf (2,438)" leaves out 175 of the manifest's 2,613 leaves.**
- The leaves left out include `oracle` (32 leaves, holding expected figures) and `checks` (8, for example "allocation spend == sum(spend_breakdown)", which no code checks; SBK2 passes).
- **Fix:** remove the oracle figures, or list them as (b) "illustration expectations, unenforced". Delete or implement `checks`.

**L2 (Low, ii): register §8 H2's premise is false.**
- G20 shows that a single record change puts two decisions on their fallback, and that the options then add dollars to hours.
- **Fix:** restate H2 as reachable, or rank by bound.

**L3 (Low, ii or iii): fallback eligibility is static.**
- CR1 and B600 are infeasible, although declared fallbacks give a plan.
- The owner may prefer "infeasible" (it is honest). Otherwise, extend the fallback to options that meet the bound but cannot be afforded jointly.
- Record the choice.

**L4 (Low, ii): spec-to-model conformance is not mechanically checked, and the specification-first order cannot be verified from the repository.**
- SP1 passes the checker. The specification and the model are untracked, with the same mtime.
- **Fix:** state in the pack that the specification's authority over the model rests on review, and commit the specification before the model if the history matters.

**L5 (Low, ii): small omissions.**
- The KAS-LOCAL cost per departure met (23.71 → 24.29) is missing from the "Figures that changed" table.
- A wrong untagged figure that equals no key, outside main §2–§10, is not caught (Dr4); disclose this beside H13.
- Register §7 rows 136, 147 and 169 still describe code that was fixed after hand-back.

**L6 (Low, ii): presentation.**
- The evaluator docstring (lines 22–26) describes the rev 12 allocator.
- "inverter inverter 2 (INV-MT-02)" on Act first (MTO-HULLER condition).
- "spare bus free on 0 night" under RO.

**Owner decisions (iii):**
- Q15 remains open, with (A) applied and disclosed. The (B) and (C) variants are evaluated and anchored.
- L3 can be put to the owner, if the Architect prefers that to a ruling.

### Regression and owner-expectation checks

- **Evaluator and checker:**
  - `python3 evaluate_structure.py`: 9 sites, 28 options, 3 plans (0.55 s). Its output is byte-identical to the working-tree `derived-values.json`.
  - `python3 check_manifest.py`: **3,255 passed, 0 failed** (0.8 s).
  - `tools/hand_typed_scan.py`: 0 hits in code and in the 216 rendered manifest strings, with 46 allow-list entries, all used.
- **Scratch rebuild:** I ran `evaluate_structure.py`, `rebase_v70.py`, `gen_fixtures.py` (28 replay patterns), `build.mjs`, `rendered_strings.cjs` (216 strings, 0 page errors) and `gen_docs.cjs`. `diff -rq` against the working tree shows **byte-identical**.
- **Preserved screens:** `screens.js`, `portfolio.js`, `outcomes.js`, `*.css`, `src-v70-baseline/` and `screen-manifest-vnext.json` are unchanged since `f5c705e25` (and since `f55f15716`). The manifest has 184 screens: 65 Preserved, 36 Changed, 74 Added, 9 Merged. **My own full audit run** (`run-audit.sh` in a scratch tree, with `frontend/` linked read-only) gives:
  - 202 / 202 routes;
  - 0 console errors, 0 bad links, 0 overflow at 390 px;
  - vocabulary, identifiers, role or question wording and filter controls all 0;
  - **preserved screens 65 / 65**;
  - switch cases 8 / 8, focus 7 / 7, contrast 38 / 38;
  - the oracle is not shipped, and 0 placeholders are unresolved.

  Its generated `browser-audit.md` is byte-identical to the working tree's.
- **Wording, filters and menus:** the rev 13 `loop-*.js` additions contain no `<select>`, no role names and no question headings; the only matches are `.filter(` calls.
- **Generality:** the evaluator and the model name no site or vertical except the EV alias (spec ambiguity A1). The checker names sites only in its `REQUIRED` anchor paths.
- **Headless spot check:** Playwright with Chromium 1140, static servers on ports 8796 (base) and 8797 (RO build), both stopped afterwards. I did not touch 5490 or 8990.
  - Pages: `#/decision/mto-inverter`, Lakeside / Harvest / Metro `#/portfolio/act-first` (Lakeside in 3 switch cases with drawers), `#/decision/kasarani-charger`, `#/site/kasarani` and Metro outcomes by site.
  - **0 page errors** and **0 overflow** at 1440 px and at 390 px.
  - Mto: the huller row per path, "not admissible (would be $2,281.25 / $462.50)", the horizon disclosure, and the CONDITIONAL text "budget at least $6,430".
  - Kasarani: "Departures missed to 9 Nov 2 / 0 / 1", "Penalties $240 / $0 / $120".
  - The defects are F1 and F2.

### Not verified

- The CSV validator.
- The author's `perturb4.py` (44 runs) and the 2,438 × 5-world influence scan. I ran my own (c)-scan instead.
- The replay design values (calibration lane).

## Review of §7 rewrite (bd5970f3d)

Fresh independent reviewer, 18 Nov. Diff `97cf295b6..bd5970f3d`. Request judged: the owner's thirteenth message, with the earlier messages as standing rules (`.agent/owner-layer4-direction-feedback-2026-11-17.md`). I formed this view before reading the author note in `REVIEW-response.md`.

**Verdict: ACCEPT WITH NOTES.** The rewrite does what the owner asked. Every Site in all three portfolios now has its inputs, a plan-against-actual table per factor, and a sum that reconciles to the Site deviation and then to the portfolio. Choose is split into the six parts the coordinator described. Each vertical uses its own factor structure:
- **Mini-grid:** litres split into necessary, candidate and unexplained, plus the chain from energy to cash.
- **Cold rooms:** occupancy model plus the excess above it, and liability.
- **EV depots:** bill lines by tariff window and highest kW, plus the chain from deliverable energy to buses short, missed departures and penalties.

A reader with no data file can follow each Site's deviation. I recomputed every figure, and all of them reconcile. The notes below are labelling and clarity issues. None is an arithmetic error.

### Findings

**Medium**

- **M1. The Kisiwa 60 kWh battery is shown as an alternative to the generator repair, measured on a different basis** (`layer4-transformation-design.md:583`). The table's column is "Evening hours with no backup to 30 Nov". No action has 125, repair 15, replace 105, and the battery 0. The battery's 0 comes from a different reference: `derived-values.json` KIS-BATT60 has `reference_protect` 0, and the manifest's `kisiwa_storage` group says "looking forward from the repair". Its 0 does not mean the battery covers 6–30 Nov while GEN-KS-01 is down. A reader would conclude the battery beats the repair on Protect and was dropped only for money. The stated reason also differs from the manifest. The doc says "negative over 12 months". The manifest says "over budget; payback about 6 years", and 14,000 exceeds the 5,000 budget. **Fix:** move the battery into its own short table, "Kisiwa: evening storage", whose reference is after the repair. Show its Protect cell as "n/a: after repair". Give both reasons (over budget; negative over 12 months).
- **M2. Plan values are labelled "Record"** (`:485`, `:504`, `:540`, "plan: Record"). In the legend (`:446`), "Record" means a meter, dip, invoice, log, roster or contract. A plan figure is the operator's declared target, not a record. The owner asked for each figure to be honestly labelled as derived, record or declared input, so this is the class of label the request is about. **Fix:** label plan figures "Plan (declared input)", or add a "Plan" row to the legend and use it in every factor table.

**Low**

- **L1. Unlabelled inputs inside option arithmetic.**
  - Battery wear 0.08 per kWh (`:570`) is `[assumption]` in the manifest (line 75), but the doc does not label it.
  - The productive tariff 0.30 (`:600`) is not in the Prices table (`:462`) and has no label.
  - Mwea handling 100.00 is called an "estimate" (`:747`), which is not a word in the legend.

  **Fix:** add 0.08 and 0.30 to the Prices table with their labels. Label handling "Assumption".
- **L2. Embakasi schedule window** (`:873`). The heading says "22:00–05:15", but the bill uses exactly 2 h + 5 h at 400 kW (2,800 kWh = the requirement). The quarter hour is slack: the manifest gives 2,900 kWh deliverable against 2,800 required. A reader recomputing from 05:15 gets 7.25 h. **Fix:** add one clause saying that 05:00–05:15 is slack and is not billed.
- **L3. Ruiru, absorbing 6 buses** (`:889`). The 3,124.80 a month is not broken down. It equals 6 × 140 × 31 = 26,040 kWh × 0.12 with demand unchanged, but the doc does not say so. It is the one figure in §7 the reader cannot follow from the inputs shown. **Fix:** show that line.
- **L4. Small presentation points.**
  - The Mwea "Of which cost" cell reads "+155.00 − 3.00" instead of +152.00 (`:732`).
  - The welding break-even tariff is "0.42", but the exact value is 272.25 ÷ 660 = 0.4125 (`:601`). Rounding up is defensible as the minimum that does not lose money. Say "about 0.41" or "0.4125".
  - The Thika factor table drops the Price column the other tables carry (`:706`).
- **L5. System vocabulary in prose.** Examples: "the allocator" (`:615`), "cover bound" / "hard bound" (`:571`, `:591`), "must-do", "obligation hours", "All of these are outputs of `evaluate_structure.py`" (`:675`), and internal IDs (INC-203, ACT-051, F-130). This is acceptable in a design document, and §7 states no executive question verbatim. If §7 is ever lifted into client-facing material, these need plain wording.

### Arithmetic (recomputed by hand from the inputs shown and cross-checked against the manifest and `derived-values.json`)

All reconcile.

- **Mini-grid**
  - Kobo: 220 + 1,200 − 240 = 1,180; 730 + 330 + 120 = 1,180. Effects −37.50, −412.50, −150.00 and +38.00 sum to −562.00 = 883 − 1,445. Revenue 3,420 → 3,458; cost to serve 1,975 → 2,575. Energy to cash: 9,100 → 8,690 → 8,645, and collected 3,180.
  - Kisiwa: −104 − 26 − 55 = −185.00 = −250 − (−65); 2% of 2,400 = 48; 10 evening hours.
  - Mto: 6,000 → 5,580 → 5,400. Effects −8, −56, −16 and −25 sum to −105.00; collected + in transit + outstanding = 2,160; 20 hours at half inverter capacity.
  - Portfolio: 2,295 → 1,443 (−852; revenue −97, cost −755). Revenue 9,785 → 9,688; cost to serve 7,490 → 8,245; 7,545 ÷ 8,245 = 91.5%.
  - Kobo options: +2,916 and +300.
  - Kisiwa options: 125, 15 and 105 hours (days counted against the 6 Nov decision date); −11,660 for the battery.
  - Mto inverter: −367.50, −2,947.50, −462.50 and −2,281.25; half-capacity hours 110 / 30 / 10 / 125.
  - Mto demand: huller +3,540, welding −99.
  - Plan: spend 3,750, of which 1,520 valued and 2,230 not valued; value +6,088.50.
  - Sensitivities and cases: diesel 20% cheaper +5,690.00; 160 L case +5,338.50; downside +2,548.50.
  - Switch cases: spend 2,550 and 6,430, value +3,508.50. Working days: 28 Nov (Saturday) → 4 Dec; 12 Nov → 19 Nov.
- **Cold rooms**
  - Mwea: model 3,410 / 2,635 kWh, excess 15 kWh; −620 + 155 − 3 = −468.
  - Thika: −108 (6 × 18), with 2,160 at stake.
  - Kirinyaga: excess 970 kWh, −194.
  - Portfolio: 1,716 → 946; cost to serve 3,492 → 3,642, 97.8% recorded. Energy per crate-day: Mwea 0.1221, Kirinyaga 0.1008; Kirinyaga's 970 kWh is 24% above its model.
  - Options: Mwea contract +1,670; Kirinyaga repair +1,512.40, replacement −1,988.40; Thika 2 nights to restore, 26 nights without backup cover in October.
  - Plan: value +3,182.40; 60% recovery case +2,716.80; switch spend 450.
- **EV depots**
  - Embakasi: bill lines 19,540.80 → 22,744.80; −2,604 − 600 = −3,204; 36.69 and 31.52 per departure.
  - Kasarani: 5,880; November to date 1,050 kWh deliverable a night, 2 departures missed, 240 in penalties.
  - Ruiru: 13,080.32, +19.68 not attributable.
  - Portfolio: 38,520.80 → 41,705.12; 32.03 and 29.59 per departure; 99.3% recorded.
  - Embakasi schedule: no action 21,438.00, 706.80 below October's energy bill; schedule 13,356.00, so 8,082 a month and +95,484 over 12 months; cheapest bill 12,975 with 3 buses short and 93 departures missed.
  - Kasarani charger: restore due 9 Nov (2 Nov is a Monday); 3 − 1 = 2 missed; options +150 and −260.
  - Ruiru: 2,800 / 3,360 kWh needed a night against 3,200; 62 departures missed.
  - Plan: spend 1,590, value +95,634; downside +150.

### Derivation honesty

- The litre split is now labelled a declared input that stands in for a calculation (`:476`). The modelled 1,060 L and 2,380 L are declared inputs, and the doc says the generator-energy reading behind them is missing (`:479`). Ruiru's stated-total plan is reported as unattributable (`:851`).
- I found no subtotal that is absent from the data.
- Prose figures without an anchor are either products of inputs shown beside them, or the cases named in L1–L3.

### Scope and rendering

- In the .md, all hunks fall between lines 439 and 936 (§7 only).
- In the .html:
  - The old and new files share a 92,493-character prefix ending at the §7 intro, and a 26,263-character suffix starting inside the §7.4 table, so nothing outside §7 changed.
  - §7 has 38 tables, the same number as the .md, and 12 `h4` and 12 `h5` headings.
  - No `<!--` anchor and no escaped `&lt;!--` remains. No raw `|---` or `**` is left.
  - A word-level comparison with the .md §7 (anchors and markup stripped) shows only tokenisation differences.
- I did not render it in a browser.

### Checks run

- `python3 Docs/demo-sprint/product-direction-layer4/check_manifest.py`: **3602 checks passed, 0 failed**. As noted, the checker confirms the anchors and the bridge sums. It does not check the class labels (M2, L1) or the reference basis of a Protect cell (M1).
- No test suite was run. No database, Docker container or port was touched. No file other than this one was edited.

## Re-review of §7 fixes (5ac8c6f69)

Fresh independent reviewer, 18 Nov. Diff `626a090df..5ac8c6f69`. Judged against the owner's thirteenth message and the standing rules in `.agent/owner-layer4-direction-feedback-2026-11-17.md`. I formed this view before reading the author response.

**Verdict: ACCEPT WITH NOTES.** All seven earlier findings are resolved across §7, not only at the cited lines. Every newly shown calculation reconciles with the manifest and `derived-values.json`. Scope is clean. One new Medium: the rewording that removed "the allocator" now describes the plan search incorrectly. It is a one-sentence fix in two places, and the owner should not read §7 with it in.

### Earlier findings

- **M1, resolved.** The Kisiwa battery now has its own table (`:621-625`), with the reference stated as Kisiwa's October running, looking forward from the repair. That matches the KIS-BATT60 formula (−55.0 against −250.0) and `reference_protect` = 0. The hours cell reads "n/a". The disposition is now Deferred (manifest `DEFERRED`), and both reasons are given: over budget, and negative over 12 months. Both are in the manifest's reason texts.
- **M2, resolved as a class.**
  - The legend gains Plan and Estimate rows (`:445`, `:447`), and one rule covers every table (`:454`).
  - The three Estimate cells (Kisiwa O&M, Thika maintenance, Kasarani maintenance) match the items left out of the 91.5%, 97.8% and 99.3% recorded shares.
  - Every label used in §7 is now in the legend.
- **L1, resolved with small residue (see L1 below).** The inputs tables were checked against the manifest's basis texts. Where the manifest records no source, the label says "source not recorded" rather than guessing. That is the honest choice.
- **L2, resolved.** `:929` and `:946` agree with the manifest (`hours_after_midnight` 5, "(to 05:15)").
- **L3, resolved.** Ruiru 6 × 140 × 31 = 26,040 × 0.12 = 3,124.80 (`:962`). I found no other figure in §7 that cannot be followed from inputs shown.
- **L4, resolved, with one decline that I accept.**
  - 0.4125 is fixed.
  - Thika now has the Price column.
  - On "+155.00 − 3.00" (`:774`): I confirmed in a scratch copy that writing +152.00 makes the checker fail ("untraced: ['152.00']"). The cell shows its arithmetic, so the reader loses nothing. The decline is acceptable. Note, though, that this is the checker's format rule (any x.xx figure must already exist in the data), not a limit on honesty. The same rule forces phrasings such as "970 + 201.5 kWh less a month" (`:812`). If printed totals are wanted later, the checker could accept a shown "a + b = c" whose result it recomputes.
- **L5, resolved.** None of "allocator", "bound", "must-do", "obligation hours", INC-/ACT-/F- IDs or `evaluate_structure.py` remains in §7 prose. The legend's provenance pointer and the asset, tariff and document numbers stay. That is right for a design document. No executive question is stated.

### Findings

**Medium**

- **M1 (new). The plan search is described as two steps, but it is one joint search** (`layer4-transformation-design.md:657`, repeated at `:826`).
  - §7.1 now says: "First, each decision that protects service or warranty cover takes its cheapest option … Then every combination of the money-valued options is tried."
  - §2 (`:182`) says the opposite: "Protective and valued decisions are enumerated **together** … never one choice at a time". `evaluate_structure.py` `best()` does the same: one enumeration, ranked by least violation, then value, then lower spend.
  - §7 is also inconsistent with itself. Under the two-step reading, the Mto inverter decision protects warranty cover, so it would always take its cheapest compliant option, the claim at 230.00. Yet the 6,500 / letter-not-extended switch row (`:715`) picks buying now at 2,910.00, because the joint search values the huller dependency.
  - The old text ("takes the must-do and protective decisions first") had the same flaw. This round rewrote the sentence and made the wrong mechanism more explicit. Because the owner reads §7 to understand the mechanics, this matters.
  - **Fix:** use one sentence consistent with §2. For example: "Every combination of options is tried together within the budget, the crew visits and the dates one option depends on; the plan kept is the one that breaks the service rules least, then is worth most, then spends least." Make the same change at `:826`.

**Low**

- **L1. Inputs still used without a label.**
  - Crew visits per item in the three Choose tables (`:659-666`, `:828-833`, `:972-976`). Lakeside uses 3 of 3, so this limit binds the plan.
  - Ruiru "all off-peak, with the highest kW unchanged at 380" (`:962`). This is the model's change rule (manifest RUI-ABSORB6 changes only `kwh_2200_2400`), but it is stated as fact. Label it an Assumption.
  - The 6 Nov decision date, and Kisiwa's warranty end of 30 Jun (`:616`), carry no label in §7.1.
- **L2. The litre split is labelled unevenly.**
  - The prose says the whole split stands in for a calculation (`:482`, `:506`, `:524`).
  - Only Kobo's candidate row carries that qualifier (`:492`). The necessary rows at `:491`, `:510` and `:546` say only "Declared input".
  - **Fix:** use the same qualifier on every split row.
- **L3. Readability (a preference, not an acceptance gap).**
  - §7 has grown from about 6,900 to about 9,200 words. Observe reads well and follows the owner's Kobo pattern.
  - The Lakeside inputs table (`:574-599`) is 27 rows across six decisions, placed away from the option tables that repeat its figures.
  - The diesel-sensitivity cell (`:694`) holds three calculations.
  - Suggested fix: put each decision's inputs directly above its option table, and give the sensitivity one row per option.
- **L4. Wording.**
  - Kisiwa's measure has two names: "no second generator in reserve" (`:520`) and "no backup" (`:613`, `:685`, `:723`). In the data the two are the same measure at Kisiwa (10 / 125 / 15). Use one term.
  - The note at `:485` justifies the missing reading by "not a whole number of kWh". The reason is simply that the reading is not in the demo data, as `:481` already says. Drop the whole-number clause.

### Arithmetic (recomputed; all reconcile with the manifest and `derived-values.json`)

- **Lakeside**
  - Kobo stop threshold: 262.50 − 12.00 = 250.50, and 12 × 250.50 − 90 = 2,916.00. Reserve option: 300.00.
  - Kisiwa: 25, 3 and 21 days × 5 h = 125, 15 and 105 hours; 1–5 Nov is 25 hours. Battery: 12 × 195 − 14,000 = −11,660.00, and 14,000 ÷ 195 ≈ 72 months.
  - Mto inverter: restore dates 28 Nov (22 days), 12 Nov (6 days) and 8 Nov (2 days). Values −367.50, −2,947.50 (2,600 + 80 + 150 + 80 = 2,910), −462.50 and −2,281.25. Half-capacity hours 110, 30, 10 and 125.
  - Mto huller: 1,650 × 0.30 = 495 − 85 − 15 = 395, so +3,540.00.
  - Mto welding: 660 × 0.33 = 217.8 L, then −8.25 a month, −99.00 a year, break-even 0.4125. Billing: 56.00 a month, 672.00 a year.
  - Sensitivities: at 1.00 a litre, +2,286.00, +3,744.00 and −340.00, total +5,690.00. At 160 L, +2,166.00, total +5,338.50. Downside +2,548.50.
  - Switch cases: spends 2,550.00 and 6,430.00; value +3,508.50. Working days (calendar-checked): 28 Nov is a Saturday, giving 4 Dec; 12 Nov gives 19 Nov.
  - Recorded share: 7,545.00, which is 91.5%.
- **Harvest Cold**
  - Models: 3,410, 2,635, 3,720 and 4,030. Contributions: 456 / −12, 562 / 454 and 698 / 504. Mwea's excess is 0.6% of its model.
  - Portfolio: cost to serve 3,492 / 3,642, recorded share 97.8%. Energy per crate-day 0.1221 and 0.1008; Kirinyaga's excess is 24% of its model. 4,340 + 4,500 ≤ 12,400.
  - Options: Mwea contract 810 − 225 − 100 = 485, and × 4 − 270 = 1,670.00. Kirinyaga repair 1,512.40; replacement (970 + 201.5) × 0.20 = 234.30, giving −1,988.40.
  - Cases: 60% recovery 1,046.80, plan 2,716.80. Switch spend 450.00.
- **Metro Bus**
  - Embakasi bill lines: plan 19,540.80, actual 22,744.80. Energy splits 86,800 = 47,740 + 15,500 + 23,560.
  - Embakasi options: tier drop 706.80, no action 21,438.00, schedule 2,976 + 5,580 + 4,800 = 13,356.00. The difference, 8,082.00, gives +95,484.00 over 12 months. Cheapest bill 12,975.00, with 3 buses short and 93 departures missed.
  - Ruiru: 13,080.32, and absorbing 6 buses costs 3,124.80 (manifest formula −16,205.12 against −13,080.32). Taking 10 buses misses 62 departures.
  - Kasarani: options +150.00 and −260.00.
  - Portfolio: 1,302 departures, 32.03 and 29.59 per departure, recorded share 99.3%.

### Scope

- **The .md:** all hunks fall in lines 445–1008, inside §7 (437–1013).
- **The .html:** the old and new files share a 93,301-character prefix (inside the §7 legend) and a 26,500-character suffix that starts inside §7.4. Nothing outside §7 changed.
- **The .md and .html §7 match:**
  - Both have 42 tables, 12 `h4` headings and 12 `h5` headings.
  - No anchor, escaped anchor, `|---` or `**` remains in the .html.
  - A token comparison with the .md §7 differs only in list bullets.
- I did not render the .html in a browser.

### Checks run

- `python3 Docs/demo-sprint/product-direction-layer4/check_manifest.py` returned **3680 checks passed, 0 failed**. The checker does not test labels, the reference basis of a cell, or prose descriptions of the mechanism (M1 above).
- I tested the +152.00 claim in a scratch copy, outside the repo. The checker gave 3679 passed, 1 failed, as the author stated.
- No test suite was run. No database, Docker container or port was touched. No pack file was edited.
