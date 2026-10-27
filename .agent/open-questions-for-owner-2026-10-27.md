# Open questions for the owner (2026-10-27)

From the Architect (Claude). Your request, verbatim: `.agent/owner-parallel-and-open-questions-2026-10-27.md`.

These questions come from three places:
- running the two plans side by side: `.agent/parallel-feasibility-2026-10-27.md`;
- the telemetry plan: `Docs/demo-sprint/telemetry-integration-plan-claude.html`;
- the commercial plan: `Docs/demo-sprint/commercial-capability-readiness.html`.

**How to answer.** Reply by number. "Agree" accepts my recommendation; otherwise pick an option or write your own. Within each group, the questions that hold up the first build step come first. Internal codes are in brackets at the end of each question, for the agents only.

The technical rulings are already made by the Architect, so they are not repeated here (scaling, coverage, battery wiring, freshness signals, where the Modbus code lives).

---

## Group A: running the two plans at the same time

### 1. May both plans be built at the same time, with telemetry getting first use of the laptop until 30 October? [parallel go-ahead]

- **Example.** On Thursday 29 October the telemetry builder needs the laptop's database for about half an hour, run alone, to prove that the emulated Modbus readings land as accepted evidence. At the same moment the commercial builder wants a 50-minute full test run for its first slice.
  - Under "yes, telemetry first", the commercial run waits until the telemetry run finishes.
  - From 31 October the commercial lane gets the laptop first.
- **Options.**
  - (a) Yes, two lanes, telemetry first until 30 October.
  - (b) Yes, two lanes, commercial first.
  - (c) No: finish telemetry's October scope, then start commercial.
- **Recommendation: (a).**
  - The two plans change different files, so two builders do not collide (checked against the code). Only the laptop's heavy runs have to take turns.
  - Telemetry has a fixed date (30 October) and commercial does not. Giving telemetry first claim protects the date and costs the commercial sprint about half a day at most.
- **Blocks:** the first build step of both plans. Needed **today, 27 October**.

### 2. On 30 October, should the telemetry result be shown from the terminal and a written record, rather than on a product screen? [caption placement; D1 surface]

- **Example.** To show the Modbus proof, the presenter runs the prepared commands. The terminal prints "accepted evidence: 48 records · source: emulated interface (values from a simulator run)". A one-page claim record states exactly what was tested.
  - The alternative is to open the AssetOps Evidence screen for the test Site with a new "emulated interface" banner on it. That banner does not exist today and would have to be built on the screens the commercial builder is changing.
- **Options.**
  - (a) Terminal and written record only in October.
  - (b) Add a banner to the product Evidence screen.
- **Recommendation: (a).**
  - It keeps the telemetry lane away from screen code, so the two lanes stay independent.
  - It avoids a rushed screen change two days before the showing.
  - The written record is also the more precise claim.
- **Blocks:** the demo runbook (telemetry task TEL-07) and the telemetry lane's boundary. Needed by **29 October**.

---

## Group B: the telemetry plan

### 3. Should October's emulated readings be shown as "source unknown", with a plain caption, rather than as simulated or real data? [D1]

- **Example.** The Modbus proof reads a fake Victron-style controller on the laptop, whose values come from the Kobo simulation. In AssetOps, each reading's source can be labelled.
  - (c) shows "source not established", with the caption "emulated interface; values from a simulator run".
  - Labelling it "registered simulation" would make those readings count as eligible for money figures, which they must not be.
- **Options.**
  - (a) Build a new label, "emulated interface", now. This changes the data contract and needs a full test run, after October.
  - (b) Label it "registered simulation". Not recommended.
  - (c) Show "source not established" plus the caption.
- **Recommendation: (c).**
  - It is true, needs no contract change, and keeps the money rules intact.
  - A dedicated label per arrival route comes later (TEL-09).
- **Blocks:** the database acceptance test (TEL-05). Needed by **29 October**.

### 4. Should the October proofs run only on throwaway test Sites in the test database, never on the demo database? [D2]

- **Example.** The test creates a Kobo-like Site, for example "KOBO-FIELD-A", inside an authorised test database, runs the proof, and leaves the demo database untouched.
  - If the proof wrote into the demo database, the KOBO-001 screens you show customers would gain evidence records that came through an emulator.
- **Options.**
  - (a) Test database only.
  - (b) Also add a Site to the demo database.
- **Recommendation: (a).**
  - It stays inside the database permission you have already given.
  - It keeps emulated evidence off customer-facing screens.
- **Blocks:** TEL-05. Needed by **29 October**.

### 5. Do you accept that the 30 October telemetry showing has no Finding and no money figure? [N1]

- **Example.** On 30 October you can show readings arriving through the real gateway and landing as accepted evidence: their source label, and how faults behave (a pulled cable gives "no report"; a "no value" answer gives "unavailable"). You cannot show "generator ran 3 hours unnecessarily, about 40 USD of diesel".
  - The emulated controller layout has no generator signal.
  - Adding one from an unverified, third-party register list would put a number on screen that we could not stand behind.
- **Options.**
  - (a) Accept: evidence, source label and fault behaviour only.
  - (b) Add generator readings from the unverified layout to get a Finding on screen.
- **Recommendation: (a).** You set credibility as the October priority. A money figure built on an unverified register map is the kind of claim a technical buyer checks first.
- **Blocks:** the demo script. Needed by **29 October**.

### 6. Should we buy no hardware now, and decide after the laptop proof which first physical test to fund? [D7]

- **Example.** After the proof passes twice, you choose one of three:
  - **Option 1:** run the same proof on the BeagleBone Black you have. About $0-16, for a microSD card and a 5 V supply if missing.
  - **Option 2:** read one real temperature probe over an RS-485 wire. About $40.
  - **Option 3:** the same probe through the Waveshare ESP32 Wi-Fi bridge. About $40.
- **Options.**
  - (a) Buy nothing now; choose after TEL-05, starting with option 1.
  - (b) Buy the option 2 or option 3 parts now.
- **Recommendation: (a), then option 1.**
  - Option 1 costs nearly nothing.
  - It turns a laptop result into an on-device result with the same tests.
- **Blocks:** the BeagleBone step (TEL-08), after October. Needed **after TEL-05 passes, about 30 October**.

### 7. What should we ask prospects for: one recent genuine data export, or a read-only login token? [D9]

- **Example.** A mini-grid operator using a vendor cloud is asked: "Send us last week's export file from your portal, or give us a read-only API key." With a genuine file we can build a real profile for that vendor and version, and move from "tested with an illustrative format" to "validated on your export".
- **Options.**
  - (a) Ask for one genuine export first, and a token as the alternative.
  - (b) Ask for a token first.
  - (c) Do not ask yet.
- **Recommendation: (a).**
  - A file is the smallest ask, needs no security review on their side, and is the most likely first source of real pilot data.
  - The edge device covers what their cloud cannot.
- **Blocks:** the first vendor profile (TEL-10). Needed **when outreach starts**.

### 8. When a customer sends real data, should we run one hosted gateway per customer Site, at a small monthly hosting cost? [D8]

- **Example.** Operator X sends exports for two sites. We would run two small hosted gateway instances, each with its own credential, so their data enters through the same checked path as the edge devices.
  - The alternative is a back-door importer straight into the database. It would bypass the duplicate and timing checks.
- **Options.**
  - (a) One hosted gateway per customer Site.
  - (b) One shared hosted gateway per customer.
  - (c) A direct database importer.
- **Recommendation: (a).**
  - It reuses identity, sequencing and receipts unchanged.
  - The cost is a few small instances.
  - (c) would create a second, weaker way in.
- **Blocks:** the first genuine customer file (TEL-10), after October. Needed **before the first customer file arrives**.

---

## Group C: the commercial plan

### 9. Should each money figure name who benefits, fixed per category for the demo and declared per site at pilot? [beneficiary basis]

- **Example.**
  - The fuel exposure on KOBO-001 is labelled "benefits: mini-grid operator".
  - A cold-room lot review on COLD-LAB-001 is labelled "benefits: goods owner".
  - An EV charging choice on EV-LAB-001 is labelled "benefits: fleet operator".

  Because the beneficiary becomes part of the comparison rule, a fuel saving for the operator is never added to a stock value for a goods owner.
- **Options.**
  - (a) Fixed per category now; declared per site at pilot.
  - (b) Declared per site now.
  - (c) No beneficiary yet.
- **Recommendation: (a).**
  - It closes a real double-counting gap for almost no build cost.
  - Per-site declarations need customer records that do not exist yet.
- **Blocks:** the first commercial slice (R1: links, labels, beneficiary, no-double-count check). Needed **before R1 starts, 27-28 October**.

### 10. Which working decision should the five-day sprint build: the after-trial fuel-cost check, or the productive-use contribution? [sprint decision: D2 vs D1]

- **Example.**
  - **After-trial check (D2).** On KOBO-001 the reserve trial was verified. The screen would add "modelled change after the trial: 0.043 USD less per kWh of feeder demand, not realized savings". That completes one story end to end: problem, money exposure, action, verified result, commercial reassessment.
  - **Productive-use contribution (D1).** On MG-W402-001 a 10 kW grain mill in the noon hour would show "expected contribution 1.70 USD per eligible hour, break-even at 12% collection, payback 71 eligible hours".
- **Options.**
  - (a) D2.
  - (b) D1.
  - (c) Both. This is about two more days, plus question 14.
- **Recommendation: (a) D2.**
  - It completes the deepest demo thread and reuses the most existing machinery.
  - It creates the "reassess after verification" pattern that every later EV and cold check will need.
  - The Implementer prefers D1 as lower risk. That is defensible, but it leaves the generator story without its commercial ending.
- **Blocks:** the third commercial slice and its database change. Needed **by 30 October**, before R2 finishes.

### 11. Should site MG-C keep its "unconfirmed generator support" stand-in for the battery-stress story in the demo? [MG-C stand-in]

- **Example.** In the portfolio view, MG-C is meant to illustrate a battery under stress. No part of AssetOps calculates battery stress today.
  - With the stand-in, MG-C appears under "needs investigation" because its generator-support finding is unconfirmed. It is labelled as such, not as "battery stress".
  - Building a stress calculator first would delay the portfolio slice.
- **Options.**
  - (a) Keep the stand-in now; build stress cues in the next horizon.
  - (b) Build a stress cue first.
- **Recommendation: (a).** It is honest about what MG-C shows and keeps the portfolio slice small.
- **Blocks:** the portfolio placement slice (R2). Needed **before R2 starts, about 29 October**.

### 12. Is "cost per kWh of feeder demand" acceptable wording for "cost per kWh served"? [denominator wording]

- **Example.** The after-trial check divides diesel cost by the energy the feeders asked for (120 kWh before, 126 kWh after). That is because AssetOps has no total of all energy actually delivered. The screen would read "0.128 → 0.085 USD per kWh of feeder demand".
- **Options.**
  - (a) Accept, with that exact label.
  - (b) Require true "served" energy. That needs a new served-energy total first.
- **Recommendation: (a).**
  - The label says exactly what was divided.
  - Unserved critical energy is already checked separately, so a trial that cut service cannot pass.
- **Blocks:** the D2 screen text. Needed **before the decision slice, about 30 October** (only if question 10 is D2).

### 13. If the EV charging decision and the cold-room lot review are not built in the sprint, may they appear as clearly labelled declared illustrations? [EV and cold if not built]

- **Example.** On EV-LAB-001 the demo would show a worked example: bus B-07 is short by 9.6 kWh under shared charging, and on time if it is charged first. It is marked "declared illustration · not calculated by AssetOps". The same applies to COLD-LAB-001 lots (dairy lot "requires review", 4,000 USD declared value).
- **Options.**
  - (a) Show them as labelled illustrations.
  - (b) Omit EV and cold decisions from the demo.
  - (c) Build at least one of them.
- **Recommendation: (a).**
  - It shows that the approach spans all three verticals without pretending the calculation exists.
  - The label keeps it honest.
- **Blocks:** the demo script. Needed **before the sprint's demo rehearsal**.

### 14. If two decisions enter the sprint, may their database changes land together in one change, with one full test run? [combined migration slice]

- **Example.** If you choose both D2 and D1 in question 10, each needs a database change. Landing them together costs one roughly 50-minute full run instead of two. The trade-off is one larger change for the reviewer to check.
- **Options.**
  - (a) Combine them.
  - (b) Keep them separate.
- **Recommendation: (a).** It saves about an hour of exclusive laptop time. Both changes are small and additive. If question 10 is a single decision, this question falls away.
- **Blocks:** only the case where question 10 is (c). Needed **with question 10**.

### 15. Should cold-room lots under review stay on the Site screen only for now, and stay out of the executive portfolio view? [cold lots in executive view]

- **Example.** "4,000 USD of stock requires review" would appear on COLD-LAB-001's financials, but not in the estate-wide view next to fuel costs. There it could be misread as a loss.
- **Options.**
  - (a) Site only for now; the portfolio view later.
  - (b) Show it in the portfolio view now.
- **Recommendation: (a).** A declared stock value is review scope, not a loss. Showing it beside priced costs invites exactly the wrong comparison.
- **Blocks:** nothing in this sprint, because the lot review is not built (question 13). Needed **before the cold decision is built**.

### 16. Should we adopt the new planning vocabulary (six outcomes; per-vertical outcome labels; new shared names for placement and allocation), keeping all existing names? [vocabulary O1-O6, MG-1..CC-7, S16, S17]

- **Example.**
  - A task would say "serves mini-grid cost per kWh (MG-2) and assurance (O6)".
  - Portfolio triage would be named "placement".
  - Choosing the best set of interventions under budget would be named "allocation".

  Nothing on customer screens changes.
- **Options.**
  - (a) Adopt.
  - (b) Keep the current planning names only.
- **Recommendation: (a).** It lets every task trace to the commercial outcome it serves, at no build cost.
- **Blocks:** nothing technical. Needed **before the next planning round**.

### 17. Should AI-assisted explanation stay out of the demo, with the boundary that AI may explain but never decide or produce figures? [AI-assisted reasoning]

- **Example.** A future "explain this finding" button could summarise why MG-B is in "act now", citing the stored records. It would never change the placement, a money figure or a verdict. For the demo, no AI feature is shown.
- **Options.**
  - (a) Adopt the boundary; no AI in the demo.
  - (b) Add an AI explanation to the demo.
- **Recommendation: (a).**
  - Nothing in the product uses AI today.
  - Adding it now would be a new dependency and a new review risk, days before the showing.
- **Blocks:** nothing in this sprint. Needed **before the next horizon is planned**.

---

## Not for you (recorded so nothing is lost)

These are decided, or are decided by the Architect:
- The EV normaliser placement (telemetry D3). Not needed before the EV proof, which waits for a prospect.
- The telemetry rulings D4, D5, D6 and D10 are decided (`.agent/telemetry-rulings-2026-10-27.md`).
- TEL-05's acceptance test moves to the host test folder (feasibility §2.4). That keeps the backend test suite independent of the new field code.
