# Design questions and decisions

**Layer 4 companion artifact 9 · AssetOps Architect (Claude) · 16 Nov 2026**
Material product and architecture conflicts only. Under the project rule, decision requests go to the Architect, who decides and says where the owner should weigh in. Each item gives the **Architect's decision** with its justification, and whether **owner input is needed**. Implementation trivia is left out.

## Owner decisions needed

| # | Question | Options | Architect decision | Owner input |
|---|---|---|---|---|
| Q1 | Approve the Layer 4 direction: D1–D10, especially "thread as decision anchor" and "no second engine" | approve / amend | Approve as designed; it reuses every existing lifecycle | **Yes** — direction gate (brief: "decision requested of the owner") |
| Q2 | Should the new decision home replace the current Portfolio as the landing page? | (a) replace; (b) keep both, decision home first; (c) keep Portfolio first | (b): decision home is the default, current Portfolio becomes "Operations view"; nothing is removed | **Yes** — this changes the first screen every client sees |
| Q3 | Three separate demo operators (one per vertical) or one mixed-vertical portfolio? | (a) three tenants × three sites; (b) one tenant with mixed sites | (a). The brief requires "one consistent three-site portfolio" per executive and warns against three role-specific portfolios; a mini-grid buyer should not see cold rooms in their story | **Yes** — demo strategy |
| Q4 | The vNEXT mock-up keeps the v7.0 visual shell; should the next round move it onto the v7.2 foundation (Inter, tokens, dark mode)? | (a) now; (b) after the owner approves the decision content | (b). Content and decisions first; v7.2 tokens are a cheap re-skin once the screens are agreed. Recorded as **MOCK DEVIATION** risk: none (v7.0 shell is the existing interactive reference) | **Yes** — visual direction |
| Q5 | Illustrative currency: USD for all three demo operators | USD / local currency per operator (KES, NGN) | USD for the generic demo; a buyer-specific demo switches to the buyer's currency with the FX basis shown | Confirm |
| Q6 | Embakasi's time-of-use + demand-charge tariff is an assumption; its 6,928.80/month modelled saving is the largest number in the pack | keep, mark as assumption; or use a flat tariff and make the EV hero repair-led | Keep, labelled on screen "if your tariff has peak and demand charges", and keep Kasarani as the flat-tariff counterexample. The brief's own EV research says savings depend on local tariff structure | **Yes** — a large illustrative number is client-facing |
| Q7 | Approve the delivery order (slices 1 → 7, build lane in parallel) | as proposed / reorder | As proposed; mini-grid first because evidence is deepest | Yes |
| Q8 | After slice 5: cold or EV first? | cold / EV | Decide by the first qualified prospect's vertical; default cold (shorter path: storage ledger + normalisation, no roster or tariff contracts) | Yes, when a prospect is known |
| Q9 | Contract extraction uses AI to propose obligation/condition/notice/remedy rows | allow with mandatory human review / manual entry only | Allow, with mandatory human approval of every row, page references, and no automated coverage outcome | **Yes** — risk posture and client wording |
| Q10 | Brief requires measured CPU/wall/disk/rows per stage for the new world; this commission was not authorised to run a build or touch a database | run the re-benchmark (demo-build-cost-plan §7) on a scratch `_audit` database / defer | Run it as the first task of the build lane, before any budget is quoted to a client | **Yes** — authorises a scratch DB build |

## Architecture decisions taken (owner may overrule)

| # | Conflict | Decision | Justification |
|---|---|---|---|
| A1 | `chain/period_read.py:139-140` refuses stored totals (D-MONEY.3), but period economics needs totals | `site_period_economics` is a sibling read contract that **recomputes** totals from stored lines on every read; D-MONEY.3 is respected, not overruled | keeps the existing money rule; totals are cheap to recompute for monthly lines |
| A2 | Backend may not import the simulator, but forward replay needs its kernel | adapter in `host/` returning a neutral projection through the existing port | the dependency direction is a deliberate structural guard (`tools/checks/dependency-direction.ps1`) |
| A3 | Commercial intake vs reading upload: upload refuses late intervals, keeps only a hash; ledger is first-write-wins | new intake copies dry-run and receipt only; keeps raw bytes; source-versioned revisions; late records accepted | commercial facts are late and corrected by nature |
| A4 | Two vocabularies: occurrence basis (MEASURED/RECORDED/DECLARED/MODELLED/EXTERNAL, 0042:50) and the new evidence class | keep both as separate axes; never merge | basis says where a number came from; class says what kind of economic fact it is |
| A5 | Fuel tolerance: existing fuel balance uses per-night 40 L materiality and 1% per ticket (`fuel_balance/rules.py:30-52`); the design adds a 2% monthly period tolerance | add the period tolerance as a separate declared policy; do not change the nightly rule | different question (period bridge residual vs nightly discrepancy) |
| A6 | The action table hard-codes `reserve-trial-1` | add rule rows per controller trial (`stop-soc-trial-1`); do not generalise the table into an action engine | smallest change; keeps the table's invariants |
| A7 | The existing reserve trial (30 → 25) would be rejected at Kobo by the new dawn-adequacy safeguard | keep the rule; it stays available where it passes the safeguard | the rule is not wrong in general; it was never compared with alternatives |
| A8 | Warranty data exists only in the v70 mock and as withheld fields | entitlement records are new; no contract lifecycle management, no claims administration (brief L2.7) | bounded decision support only |
| A10 | The recommended Kobo stop-setting change has no executable carrier: `action` allows only reserve-trial-1 (0016:60, :72); the STOP_SOC scenario never calculates; and today's `terminal_soc` guardrail would fail such a trial by design | build a domain-Action APPLY path for the `stop-soc-threshold` CONTROL property (`sites/models.py:167`) with rule row `stop-soc-trial-1`; generate guardrails per option kind from SAFEGUARD_POLICIES (dawn adequacy replaces terminal SOC for this kind) | the economically right lever must be executable; guardrails must test the safeguard that matters for the change made |
| A9 | Approval actor | human principal for option selection; SYSTEM_DEMO remains for fixture replay only and is labelled | the brief requires explicit human approval and operator ownership |

## Where the commission could not be completed to standard

| Item | What is missing | Why | Path to close |
|---|---|---|---|
| Measured cost per stage for the new world (Deliverable 7) | new measurements | no build or DB authorised; historical walk1113 figures used and labelled | Q10 |
| Screenshots of a real product | product does not yet implement the design | design-only commission | mock-up screenshots are supplied instead (not product) |
| Forward-replay calibration | no real site series | demo data only | pilot slice 7 |
| Contract terms | all contract clauses are illustrative | no real contracts | pilot data ask |
| Commercial validation | no prospect observations | none run | phase plan §8 instrument |
| Forward-replay figures (Kobo 210 L / 20 L, huller 68 L) | not produced by running the simulator kernel | design values held as oracle expectations | slice 3 adapter must reproduce them or the manifest is corrected |
