# High-impact, medium-effort features for CFO / COO / CEO (mini-grid and EV) — feasibility and shortlist

- Architect: Claude, 2026-11-07. Binding checked: `.ai/ROLE_CONFIG.md:9`, Architect = Claude since 2026-10-27. Read-only study; nothing built, no DB touched, no suite run.
- Owner, verbatim (2026-11-07): "i want us to consider high impact features that we can do relatively with medium effort, e.g Fuel savings. the features should have large conversion impact for CFO, COO,CEO...of minigrid and EV"
- Basis: main `61195bca1`. Rules applied: SCOPE-1 (only what we can present defensibly), money only from evidence and declared prices, never tuned, plain client copy, mockup v69/v70 as layout spec.
- These are proposals, not commitments. Nothing is scheduled until the owner picks.

---

## Part A — Owner summary (plain language)

**The short answer.** Fuel savings is the right *kind* of feature, but our current Kobo example cannot carry it honestly. Kobo runs mostly on solar, and its generator runs for only about 15 minutes on some mornings. Its fuel use is worked out from the generator's output rather than measured, and the honest saving comes to about 1 litre a day. Building a diesel-heavy example and getting it to pass its check is large, risky work: four earlier attempts did not pass. The money story we **can** prove today is the mill. Its result is checked (42 → 110 kWh a day), and at your declared price that is about **17 USD a day more in mill sales**. Today the system shows that result in kWh only, and only on a side page. The best medium-effort move is to put that proven dollar figure where executives look, and to do it honestly.

| # | Candidate | What the client would see | Who it convinces | Effort | Risk to what already works | Verdict |
|---|---|---|---|---|---|---|
| 1 | **Mill result in dollars** | On the mill's result page, next to "Target met": "About 17.00 USD a day more mill sales: (110.00 − 42.00) kWh a day × your declared 0.25 USD per kWh, on 3 checked days before and 3 after." Also: "No cost is recorded for this change." | Mini-grid CFO (strong), CEO (strong), COO (medium) | 0.5 | Low: one page and its read; no new example data | **Do** |
| 2 | **Mill on the daily board** | The Kobo board shows the mill change as checked and working. The end-of-story count reads "2 verified results", the mill among them, not just the earlier maintenance check | COO (strong), CEO (medium), CFO (medium) | 1.0–1.5 | Medium: the board is shared with the cold room and the EV depot, and several checks need new expected values | **Do** |
| 3 | **"Verified value" on the Portfolio front page** | The Portfolio card that today shows only a count also lists each proven result with its value: "Kobo mill: about 17.00 USD a day more sales (estimate at your price)" and "Kobo generator setting: no fuel saving found". The two are never added into one total | CEO (strong), CFO (strong), COO (low) | 0.75 | Medium-low: the Portfolio cards and their checks | **Do, after 1 and 2** |
| 4 | Tidy the money lines that are now in focus | Two lines that today name an estimate with no figure are reworded: Kobo's month sales line, and the EV depot's fault-day income line | CFO (protects trust) | 0.15 | Low | **Do (small)** |
| 5 | Payback next to each verified result | "Pays back in N days" | CFO (strong) | +0.25 | Low | **Only if you give us a real cost for the mill change, with its source.** The mill change has no recorded cost, so with no real cost we show "No cost is recorded" (in item 1) |
| 6 | Fuel the generator burns while idling | On the two "generator kept running" days, an estimate such as "Generator idled for about 3 hours: about X L, Y USD of possible extra fuel" instead of "no fuel cost estimated" | Mini-grid CFO (medium), COO (medium) | 1.5–2.0, plus a short trial first | Medium-high: changes a reviewed fuel calculation and every Kobo money check; needs an idle-burn figure from the generator's datasheet | **Not now.** Offer as a choice; the numbers would be small at Kobo |
| 7 | Proven fuel savings (before/after litres and USD) | "Fuel saved: X L, Y USD since the change" | Mini-grid CFO (very strong), COO (strong) | 3–5 | High: needs a new diesel-heavy example, a check that passes (four earlier tries did not), and a full rebuild | **Not now.** The machinery exists; the example does not. Best post-demo item for a diesel client |
| 8 | EV income lost to charger downtime, and income recovered after a fix | "The 44-minute outage cost about X USD" | EV CFO (strong), COO (strong) | 2–3 | High | **Not now.** Our EV example has one charging session per day, and the fault day's income has no figure (it is not a fully checked day). The design itself says "no invented lost revenue". "Recovered after a fix" also needs a repair and a re-check in the example |
| 9 | Battery life protected (replacement spending pushed back) | "Battery replacement deferred by N months, worth X USD" | CFO (strong in principle) | 3+ | High | **No.** The product deliberately states no remaining battery life: no capacity test or wear model exists. A figure would not hold up |

**Recommended shortlist: items 1, 2, 3 and 4, about 2.4–3.15 units (plan 3.0 with a small allowance).** That fits within 3–5. Order: 1 and 2 can be built side by side, then 3, then 4, then the demo script. None needs new example days or an extra build: all four show in the one final demo build that happens anyway.

**What this gives each executive.**
- **CEO:** the front page names a proven result in dollars, and says plainly which change saved nothing.
- **CFO:** every dollar shows its formula (measured kWh × the price you declared, on checked days). The system never adds up figures with different bases. That honesty is what builds trust.
- **COO:** the daily board shows the loop closing: problem → change → checked → working.

**For EV operators, plainly:** nothing on this shortlist is EV-specific. The EV example is too thin for a defensible dollar figure. The EV pitch stays on today's estimated charging income and downtime minutes. The honest EV money feature (item 8) is post-demo, and needs fuller EV example days.

**Your decisions**
1. Approve items 1–4 (about 3 units) before the demo script?
2. Is there a real cost for the mill change? If so, give us the figure and its source, and payback (item 5) follows. Otherwise the page says "No cost is recorded for this change".
3. Do you want item 6 (idle fuel) tried? It starts with a small trial, about 0.25 units. The figures at Kobo would be small.

---

## Part B — Technical basis

### B0. Method and what was not done
- I read code, the build sheets, the backlog, the v69/v70 mockups and the story calendar. I ran no SQL, because the figures needed are already measured and recorded. The mill's kWh and USD come from `build-sheet-DD-1.md:1933`, P6 MEASURED. WK-2a's 42.08 = 168.3 kWh × 0.25, from `tools/demo_combined_finish.py:535-539`. The price assert 0.25 is at `tools/demo_combined_after.py:326-330`.
- Units are this sprint's units. "Medium" means 0.5–2.

### B1. Candidate 1 (coordinator's 1): proven fuel savings, USD and litres — NOT NOW (3–5 units, high risk)

**What exists**
- The litres-from-kWh basis exists and is reviewed: `financials/fuel_cost.py:13-22`, `:57-81`. Quantity high = 1.10 × Σ(P kW × h × SFC L/kWh) over Candidate-avoidable time; quantity low = 0. It is a modelled conditional, not a measured quantity (`:63-65`).
- The cost check after a verified trial exists (OUT-E): `financials/trial_fuel_comparison.py:1-8`, `:25-27`, `:122-166`. It compares fuel cost per kWh of feeder demand, baseline against later. The label is "Modelled change after the trial · not realised savings" (`:26`). There is no annualising and no realised-savings claim (`:7`). It is wired at `actions/verification.py:995-1026`, with intervention cost fixed at 0 and source `COST_CHECK_SOURCE` (`:49`, `:1025`).
- A fuel balance from a `fuel_level` tank signal exists in depth: `mini_depth/inputs.py:137-141`, `mini_depth/rules.py:616-617`, `:678`, `:760`. It is never SUPPORTED: "Residual needs all five terms…, which W4-02 never has" (`rules.py:760`).
- The Kobo Cost row copy: `site_outcomes/mini.py:62-65` ("No fuel cost estimated: the generator was on but delivered no measured power").

**Why it fails on today's data (measured, not assumed)**
- The verified Kobo trial (ACT-001, reserve change, window 06:00) gives `MODELLED_NO_IMPROVEMENT`, 0 USD: `tools/demo_combined_finish.py:39-40`, `.agent/DEMO-SPARSE-trial-probe.md:65-75`.
- Four trial alternatives were probed. None both shows the lever and VERIFIES. (b) has no reserve-bound hour. (c) loses the Finding on S. (d) is refused at plan freeze, twice: `VERIFICATION_BASELINE_NOT_SELECTED`, then `VERIFICATION_BASELINE_UNSUPPORTED` / `OPEN_BOUND`. See `DEMO-SPARSE-trial-probe.md:67-69`, `:80-98`, `:103-123`.
- The overuse days (S-14, S-7) are PRICED with quantity 0: the generator is RUNNING at 0 kW in the Candidate span, and the fuel law is linear on energy. See `build-sheet-DD-1.md:1000`, `:1017`, and backlog BL-16 (`backlog-post-demo.md:27`).
- There is no fuel signal. Kobo has 0 `fuel_level` rows (`build-sheet-DD-1.md:1934`). O15 litres was "not recomputable": stored generator kWh is 3.244 per steady-before night with a run (`review-packet-DD-1b2b.md:21`; `build-sheet-DD-1.md:2459`). That is about 1 L a night at a typical SFC, so the honest saving is about a litre a day.
- The mill cannot claim fuel. "Do not claim a litre": S-13 ran the old pattern with 0 generator (`build-sheet-DD-1.md:1934`; handoff "Carry into DS-1").

**What it would take:** a new diesel-heavy scenario pair, Kobo or a new Site, in which the generator delivers power in Candidate time and a lever reduces it. Then a trial that clears the plan freeze (`actions/verification.py:86-93` `required_days`, open-bound rules), story days in `demo-story-days-v3.json`, a full prepare (~1 h), and new MONEY-B/finish rows. Each probe costs a partial prepare. The record of four failed probes makes the outcome uncertain, so this is not medium effort.

**Defensibility:** with a working story it is good, but only as a "modelled change" (SFC × kWh), never "measured litres" without a tank signal. A CFO will ask "measured or modelled?"; the label already answers "modelled".

**Conversion impact:** mini-grid CFO very high, COO high, CEO medium. EV: none.

**Rule blocks:** none in principle. The blocks are the data and the verification path.

**Recommendation:** post-demo. It is the first item to pick for a diesel-heavy prospect.

### B1b. Variant: idle fuel on overuse days (BL-16, product-side) — OPTIONAL, 1.5–2.0 + 0.25 probe

- A new reviewed model version (fuel-cost-2) adds an idle term: RUNNING seconds at ≈0 kW × a declared idle L/h. The idle rate is a new Foundation fact, from the generator datasheet, declared by the owner.
- It touches `financials/fuel_cost.py` (the reviewed parameter block at `:57-81` must not be edited in place: "needs a new version and review"), the consequence store, and the MONEY-B finish asserts that pin quantity 0 on S-14 and S-7 (`build-sheet-DD-1.md:1017`, `:2100`).
- BL-16 itself also names a simulator law change and a re-baseline (`simulator/assetops_simulator/packs/mini_grid.py:24-27`). A product-only idle term avoids the re-baseline, but leaves the Lab law (0 L idle) and the product estimate disagreeing. That needs a ruling.
- The figures would be small at Kobo: about 200 min of Candidate time on the trial-type day (`DEMO-SPARSE-trial-probe.md:67`). Impact is medium. It is a "fuel waste found" claim, not a saving.

### B2. Candidate 2: Portfolio "verified savings to date" (one USD total) — RESHAPED to shortlist item 3 (0.75)

**What exists**
- The mock slot: v69 `frontend/mockups/v69/index.html:129` "Verified value recovered" (today "Not established"). v70 `frontend/mockups/v70/index.html:492` puts it on the Assure card. Copy key: `frontend/src/estate/portfolioWords.ts:77`.
- The card builder: `site_outcomes/read.py:745-781`. The Assure card value is a count only (`:778-780`), from `chain/claims.py:119-148` (`count.verified_results`, thread-based).
- Portfolio money today is income only: `read.py:668-686` (`portfolio_parts`, `estate_income`), used by the Grow card at `:707-742`.

**Rule blocks: a single summed total is blocked.** The mock states "no combined savings total" (v69 `:131`, v70 `:284`) and "lines with different bases are not added together" (v69 `:482`; v70 `:844`, `:1040`). Our two verified results have different bases: mill estimated sales (kWh × declared price) and ACT-001 modelled fuel cost per kWh of demand (0). The card therefore lists **one value line per verified result, each with its basis**, and no total.

**What's missing:** a per-result value claim (from item 1's function for the mill, and from the stored OUT-E row for generator trials), a "value lines" part on the Assure card, and the frontend render. The count must agree with the lines. Today the count excludes the mill (DD1b2-R5 M1, `build-sheet-DD-1.md:2025`), so **this depends on item 2 (BL-45)**. Without it, the card would read "1 verified result" beside a mill dollar line, which is a contradiction.

**Data:** none new. **Size:** 0.75. **Risk:** medium-low: `backend/tests/test_ch6b2_portfolio_cards.py` (13 refs), `frontend/src/estate/__tests__/estatePortfolio.test.tsx` (11), `portfolioFixtures.ts`, and the COH chain-coherence guard (`tools/checks/chain_coherence.py`).

**Impact:** CEO high (page one), CFO high (bases kept apart), COO low.

### B3. Candidate 3: EV revenue lost to charger downtime, and recovered after a fix — NOT NOW (2–3 units, high risk)

**What exists**
- The connector out-of-service duration on the Protect row: `site_outcomes/ev.py:177-178`, `:213-218` ("…out of service for {d}; which departures were affected is not known yet").
- EV income = complete-record kWh × declared gross tariff (`financials/ev_money.py:1-44`, `ev.py:189-199`, `:229-240`).

**Rule blocks**
- The mock explicitly refuses this figure: "Interrupted service · No demand/sales baseline · Unpriced exposure · No invented lost revenue" (v69 `:598`), and F-130 "lost revenue unknown" (v69 `:327`).
- The fault day has no income figure (BL-48 item 2, `backlog-post-demo.md:69`; `ev.py:229`), so even a side-by-side comparison has no fault-day figure under money-only-from-checked-days.

**Data is too thin.** Each EV story day is one 1-hour window with one session. The normal day is c1 at 60 kW for 30 min, about 30 kWh (`config/scenarios/ev-complete.yaml:29-36`). The fault day faults at 08:16 after about 15 kWh (`config/scenarios/ev-interrupted.yaml:2`, `:33-36`). Nothing shows that a second car was turned away. "Recovered after a fix" needs a later EV change, a witnessed test, and new days (BL-31, `backlog-post-demo.md:52`).

**Impact:** EV CFO/COO high in principle, but it fails a CFO's first question ("how do you know a car was waiting?"). Post-demo, with multi-session EV days and a demand baseline ruling.

### B4. Candidate 4: battery life protected / replacement capex deferred — NO (3+ units, not defensible)
- The product withholds this by design: `sites/battery_boundary.py:8` ("Degradation, remaining life, stress score, warranty/replacement exposure and diagnosis are withheld") and `:33` (no capacity test).
- The UI states the gap: `frontend/src/sites/SiteBattery.tsx:427-443` (`G-asset-remaining-life`, "No remaining-life or replacement date is given").
- The mock's warranty panel (v69 `:912`, "412 of 6,000 cycles", "$64,000") needs declared warranty terms. No such Foundation facts exist: 0 `warranty` hits in the backend models. The mock itself marks asset exposure "Scenario only" and "capacity unverified" (v69 `:128`, `:479`).
- A capex-deferral figure needs a wear model. Any number would be tuned. A lighter "usage against warranty limits" card (throughput ÷ declared capacity) would be about 1.5–2 units and medium impact. It is not shortlisted.

### B5. Candidate 5: USD (and payback) on each verified result next to "Target met" — SHORTLIST item 1 (0.5), payback conditional (+0.25)

**What exists**
- The mill verdict read: `actions/verification.py:378-396` (`domain_summary`) → `actions/verification_families.py:384-419` (`summary_wire`). It returns `before` / `after` mean kWh a day and day counts, with `cost_check: None` (`:390`). The judged line is `R7_TEXT` at `:231-232`.
- The page: `frontend/src/sites/SiteMillVerification.tsx:69-113`, kWh only (`:53-56`, `:95-104`), labelled MOCK DEVIATION R700 (`:7-8`, `:109-111`).
- The declared productive price exists and is asserted in the demo at 0.25 USD/kWh: `financials/assumptions.py:30`, `:37`; `site_outcomes/mini.py:778-788`; `tools/demo_combined_after.py:326-330`.
- The generator trial's verdict page already shows its stored cost check (OUT-E) as "no modelled improvement".

**What's missing**
- A read-time `value` block in `summary_wire` for a judged VERIFIED outcome:
  - `(after − before) kWh/day × the declared productive price in force over the later window`, giving per-day before USD, after USD and the difference. Exact Decimal, rounded at display.
  - The price revision id and the formula text.
  - "No cost is recorded for this change" when no outlay exists.
- A price read port on the verification service (the assumption store by `productive_use_price_per_kwh`).
- One frontend line under the headline, plus the MOCK DEVIATION label extended.
- Tests: `backend/tests/test_ch9b3_mill_verdict.py`, `test_ch9b3_mill_verdict_postgres.py`, `frontend/src/sites/__tests__/millVerification.test.tsx`.
- One finish-row assert at E3: 17.00 USD a day, because 27.50 − 10.50 = (110 − 42) × 0.25 (`build-sheet-DD-1.md:1933`).

**Rule check**
- Money only from evidence: the kWh means are over 3 COMPLETE ("fully checked") days on each side, by the family's own selection (`verification_families.py:15-21`), times a declared price. Nothing is estimated beyond that.
- No annualising (OUT-E `:7` spirit): per day only.
- Plain label: "estimated mill sales at your declared price", not "revenue". Kobo has no sales records (R636; BL-48).
- Disclose that the extra milling is "more daytime use, not the same work moved" (`build-sheet-DD-1.md:1933`; DS-1 carry).

**Payback:** the stored intervention cost is always 0 with source "no direct cost declared" (`verification.py:49`, `:1025`). The mill Action has no outlay field. Payback is meaningful only with an owner-declared outlay and source, stored as a declared fact like a price (+0.25). Otherwise the page shows "No cost is recorded for this change", which is true and still strong for a CFO.

**Risk:** low. Additive field. Existing asserts on `cost_check: None` and `trial_hours: None` are unchanged. No new data and no prepare.

**Impact:** mini-grid CFO high, CEO high, COO medium. EV: none.

### B6. Candidate 6: from code, mockup and backlog
- **BL-45, mill on boards → SHORTLIST item 2 (1.0–1.5).**
  - Cause: Finding-only reads in `site_outcomes/mini.py:416`, `:475` and `site_outcomes/board.py:691-765` (`thread_line_item`, `thread_line_findings`). Opportunity-origin Actions are not on the board, Assure or thread link. The Portfolio count is thread-based (`chain/claims.py:119-148`).
  - Sizing and client view per option: `build-sheet-DD-1.md:2023-2040` (DD1b2-R5 M1). Owner chose "Fix link, use route" for the sprint (`.agent/owner-mill-route-2026-11-07.md`). This proposal re-opens it on the owner's new request.
  - Risk: medium. `board.py` is shared with Cold and EV; tests `test_out_b2_mini.py`, `test_out_b3_cold_ev.py`, `test_demo_combined_ex1.py` (3 verified-count refs), `test_out_b4_*`, `test_ch6b2_portfolio_cards.py`; COH re-expectations; DS-1 route lines change to the board.
- **BL-48 → SHORTLIST item 4 (0.15).** Kobo month sales line `chain/vocabulary.py:268`; EV fault-day income headline `site_outcomes/ev.py:229`. Once money is headlined, a money line naming an estimate with no figure invites "where's the number?".
- **BL-50 (0.25):** Cold "Why?" visibility. Cold, not mini-grid or EV; not a conversion item; optional.
- **BL-06 (0.5):** EV "chargers mostly idle" detector. Mock "Chargers used under a fifth of capacity". On 1-hour single-session windows the basis is too thin to convince an EV COO. Not shortlisted.
- **Cold stock value at risk:** reserved keys `cold_stock_quantity`, `cold_stock_unit_value`, and "no cold stock value, currency or exposure rule is approved" (`financials/cold_consequence.py:16`, `:48`). It needs a valuation ruling. Cold is outside the owner's named segments. Not shortlisted.

### B7. Ranking (impact × defensibility ÷ effort, mini-grid and EV executives)

| Rank | Item | Units | Defensibility | Note |
|---|---|---|---|---|
| 1 | Mill USD on verdict page (B5) | 0.5 | High | No data, low risk |
| 2 | Mill on boards (BL-45) | 1.0–1.5 | High | Makes 3 consistent |
| 3 | Portfolio verified value lines (B2 reshaped) | 0.75 | High (per-basis, no total) | Needs 1 and 2 |
| 4 | BL-48 money wording | 0.15 | — (removes a weak spot) | |
| 5 | Payback | +0.25 | High only with a real outlay | Owner input |
| 6 | Idle fuel (B1b) | 1.5–2.0 (+0.25 probe) | Medium (datasheet idle rate) | Small numbers at Kobo |
| 7 | Proven fuel savings (B1) | 3–5 | Medium-high (modelled) | Data and verification blocked |
| 8 | EV downtime revenue (B3) | 2–3 | Low on current data | Mock rule blocks |
| 9 | Battery capex deferred (B4) | 3+ | Not defensible | Withheld by design |

### B8. Shortlist, order and dependencies (≈3.0 units with allowance)

1. **Item 1, mill USD (0.5)** and **item 2, BL-45 (1.25 mid)** in parallel. Their files are disjoint: `verification_families.py`, `verification.py` and `SiteMillVerification.tsx` for item 1; `board.py`, `mini.py` and `claims.py` for item 2. Two lanes are allowed.
2. **Item 3, Portfolio value lines (0.75):** after both. It reuses item 1's value function, and its count must include the mill (item 2).
3. **Item 4, BL-48 (0.15):** any time before DS-1.
4. **Allowance (~0.35):** the E3 finish rows (mill 17.00 USD a day on the verdict page and on the Portfolio; Assure count 2) and recaptures, which E3 does anyway.
5. Then **DS-1** rewrites the mill beat from route to board, and adds the dollar line and the "no fuel saving found" honesty line.

**Placement:** after CH-5d1, before DS-1 and the E1 merge freeze. Every item is read-time over data the E3 build already makes, so there are no new authored days and no extra prepare. Localised tests only, per the standing rule. Item 2 needs the fast tier, because it touches shared board code.

**Each pre-flight must pin these literals:**
- Item 1: value line text, rounding (cents), the price revision used (later window end), and the NOT_JUDGED / INEFFECTIVE behaviour (no value line).
- Item 2: the board thread line for opportunity Actions and the Assure count source.
- Item 3: the per-basis line texts and their order, with no total.
