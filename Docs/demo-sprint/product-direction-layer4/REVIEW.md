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
