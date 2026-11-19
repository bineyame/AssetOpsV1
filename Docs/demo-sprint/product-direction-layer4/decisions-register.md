# Decisions register

**AssetEcon Layer 4 · recreated from the design rev 16.7 (with OD-12) · AssetOps Architect (Claude) · 19 Nov 2026**

This register holds every owner decision behind the Layer 4 design, every Architect's call the owner has not yet settled, and the open queue with a default for each item. It replaces `design-questions-and-decisions.md` and the roadmap's §6 (regeneration F, #1). The design cites decisions by ID; this is the one place their words are kept.

*Serves the objective:* operator executives adopt the product for economic value beyond their monitoring tools. Each decision here either shapes what they see and trust, or sets who decides, acts and is recorded. A decision that serves neither is listed as superseded.

## 1. How to read this register

<!--derives: Decisions; Introduction-->

Each item has one of four states:
- **Decided.** The owner's words are quoted verbatim, with the date and the owner record. The design's wording sits beside them, unchanged.
- **Architect's call.** The Architect chose because the owner had not settled the point. It stands until the owner overrules it.
- **Pending, with a default.** The default applies meanwhile (workflow W3). The owner's answer replaces it.
- **Superseded.** An item from an earlier revision. Its one line says where its content went.

Who sees, decides, acts and tracks: the owner decides; the Architect records each decision with its reasoning and names where the owner should weigh in; the coordinator relays the owner's words verbatim into `.agent/owner-*.md` files. Owner records cited as `owner/…` live on `main`; those cited as `.agent/…` are on this branch.

## 2. Owner decisions on the design (19 Nov)

<!--derives: Decisions; §1.3; §2.4; §2.5; §2.6; §2.9; owner: .agent/owner-design-regeneration-request-2026-11-19.md; owner: .agent/owner-recreate-document-packs-2026-11-19.md-->

The second column is the design's wording, exactly as in its Decisions table. The third is the owner's words. Records: (a) `.agent/owner-design-regeneration-request-2026-11-19.md`; (b) `.agent/owner-recreate-document-packs-2026-11-19.md`.

| ID | Decision (design wording) | Owner's words, verbatim | Record · where applied |
|---|---|---|---|
| Q-A1 | A Finding has a bottom-line impact, or is a risk or an opportunity, and is to be acted on with one or more Actions | "a finding should have impact on the bottomline or is a risk or an opportunity - which means it needs to be acted on and the user likely reate one more action against it" | (a) · §1.3, §2.1 |
| Q-A2 | A few sensible roles | "yes lets have a few sensible roles" | (a) · §2.6 |
| OD-1 | The plan is a legitimate new construct, integrated with the existing ones; an Action can be raised against a plan or a Finding | "i believe a plan is  a legitmate new construct and need to be added as such and integrated with the existing constructs. e.g an action be raised against a plan or a finding. push back if i got this wrong" | (a) · §2.5, with the coordinator's refinement (one origin, at most one plan membership), owner-approved to pass on |
| OD-2 | The spend threshold is configurable, as a Site or portfolio setting | "this should be configurable and a matter of site/portfolio setting" | (a) · §2.4 step 4, §2.6 |
| OD-3 | A configurable tolerance per factor decides whether an adverse deviation raises a Finding | "yes configurable tolerance should dictate this" | (a) · §1.3, §2.1 |
| OD-4 | An Action whose item the approved plan leaves out is not released. It returns to its creator with the reason, to revise, defer or withdraw ("Q-B1 yes") | "Q-B1 yes, agree with the architect's pushbacks" | (a) · §2.5 |
| OD-5 | A proactive plan item names the factor or Protect measure it moves, or is marked "no factor (upkeep or compliance)" with no value ("agree with the architect's pushbacks") | same answer | (a) · §2.5 |
| OD-6 | "Plan" means only the new construct; B2 uses "targets and budget lines" (same answer) | same answer | (a) · §2.2, §2.5, figures; the naming lint (rule A3) enforces it |
| OD-7 | Today's opportunity-study origin stays as a legacy third origin for existing mill-shift Actions only ("OD-7 and OD-8 yes", 19 Nov) | "yes, send it along with OD-7 and OD-8 yes" | (a) · §2.5, §2.9 |
| OD-8 | A Finding-origin Action that spends always joins the plan and waits for approval only above the spend threshold ("OD-7 and OD-8 yes", 19 Nov) | same answer | (a) · §2.4, §2.5 |
| OD-9 | Delivery order: agree the canonical format and leaf factor IDs first, then build the sources (lane A) and the factor structure (lane B) in parallel, joining at the money leaves (the owner's question and "yes, send it", 19 Nov). The Architect's refinement (cost-side decisions start before the join) and caution (the format is version 1) are in §2.9, for the owner | "in terms of delivery order, builing of external source emulators can happen in parallel with work related factor structure, right?", then "yes, send it" | (a) · §2.9, Figure 10 |
| OD-10 | The system opens the period's draft plan automatically when the period starts, within the executive's limits ("i agree with the rest of the defaults", 19 Nov) | "i agree with the rest of the defaults" | (b) · §2.5, Figure 6b |
| OD-11 | A change that alters total spend or crew use above the threshold creates a new plan version for the executive to approve; smaller changes are recorded without a new approval (same answer) | same answer | (b) · §2.5, Figure 6b |
| OD-12 | The crew-visit threshold defaults to zero and is configurable, a Site or portfolio setting like the spend threshold (owner, 19 Nov: "the crew-visit threshold default of zero is fine so long as it is configurable") | "the crew-visit threshold default of zero is fine so long as it is configurable" | (b) · §2.5 |

The owner also set the standing document brief that every Layer 4 document follows (`.ai/RULES.md` §10): existing before new, mechanism tied to value, change on merit, the overall objective in every part, the person in the loop, precise names, short and illustrated, and the owner decides.

## 3. Earlier owner decisions, D1 to D15

<!--derives: Decisions; Introduction; §2.3; §2.9; owner: .agent/owner-grounded-transition-request-2026-11-18.md-->

The design carries D1, D11, D13 and D14 over and treats the rest as commercial or process decisions outside it. Records: (c) `owner/owner-d1-engagement-path-2026-11-18.md`; (d) `owner/owner-sitting1-answers-2026-11-18.md`; (e) `.agent/owner-grounded-transition-request-2026-11-18.md`.

| ID | Subject | State | Owner's words, verbatim · record | Where applied |
|---|---|---|---|---|
| **D1** | Engagement path: initial call, deep-dive with process owners, integration pack and pilot timeline, pilot and monitoring, then SaaS | Decided, 18 Nov (revised) | "yes, have the architect revise D1 that way" · (c) | Introduction; §2.3 (exports pass the canonical contract during the deep-dive); `commercial-plan.md` |
| **D2** | Deep-dive and pilot terms | Part decided, 18 Nov: the pilot fee is disclosed after the client conversation. The fee's form and the deep-dive's terms are go-to-market defaults | "it is disclosed after client conversation" · (d), item 11 | `commercial-plan.md` |
| **D3** | Lead vertical | Pending; default mini-grid | — | §2.9 step 5 proves each construct on mini-grid first |
| **D4** | Second vertical | Pending until a qualified prospect; default cold | — | Figure 10 step 9: cold, then EV |
| **D5** | Who does the deep-dive's work | Decided with D1, 18 Nov: the owner runs the call, the deep-dive and the source mapping, and the product computes. Whether a second person checks each mapping is a go-to-market question | the D1 record's stage table · (c) | `commercial-plan.md`; the Analyst role in §2.6 |
| **D6** | How replay-derived figures are shown to clients | Pending (§5) | — | "Words used here": figures are design values until their replay passes |
| **D7** | Approve the design and the mock-up before any UI build | Pending (§5) | "not yet, it will be once item 6 in this list is done" · (d), item 5 | — |
| **D8** | One re-benchmark run before build budgets | Pending (§5) | — | — |
| **D9** | Contract extraction posture | Pending, default applied (§5) | — | §2.3: AI-assisted, a person approves each row |
| **D10** | Freeze the design pack except for decisions and the mock-up gate | Superseded, 19 Nov, by the owner's order to recreate the packs from the design | "recreate (not update) all the document packs" · (b) | regeneration F |
| **D11** | The build workflow W1 to W9 | Decided, 18 Nov | recorded in `.ai/RULES.md` (workflow) | every slice |
| **D12** | Demo and pitch shape | Pending; it belongs to go-to-market | — | `commercial-plan.md` |
| **D13** | The grounded, visible-first path: today's chain re-grounded on one structure, ordered by how soon the client's screens become useful | Decided, 18 Nov | "D13:yes, with clear and sensible transition" · (d), item 2; the owner's question in (e) | Introduction item 6; §2.9 and the Architect's refinement |
| **D14** | Emulators are placeholder sources for the canonical contract; their output is labelled Emulated and never counted as benefit | Decided, 18 Nov | "D14:yes" · (d), item 3; "the emulator is a palcehodler that should be replaced by real integration" · (e) | §2.3, Figure 4; §2.9 |
| **D15** | The first change agreed at the end of the deep-dive and made when the pilot starts | Pending; the owner asked for context (§5) | "D15:I am not clear on this, i need more context" · (d), item 4 | — |

## 4. Architect's calls the owner has not settled

<!--derives: Decisions; §1.3; §2.4; §2.5; §2.9; Words-->

Each stands until the owner overrules it. The reason is given in the design section named. OD-12 settled the crew-visit threshold's default, so it is no longer a call.

1. The spend threshold applies to the whole chosen change, summed over its Actions, never one Action at a time (§2.4 step 4). Reason: splitting a change must not slip it under the threshold.
2. An Action already released stops at its next step and returns to its creator when the approved plan drops its item; spend already incurred stays recorded against the item (§2.5).
3. Cost-side decisions start before the join; only revenue-side options wait for the money leaves (§2.9, Figure 10). Reason: Kobo's first decision reaches a client sooner (D13).
4. A spending Action with no decision behind it creates its own reactive item. A work case's origin is the Finding or plan item it was opened from; its other links stay links (§2.5, "Words used here").
5. A plan covers the portfolio's budget period, a month by default. A carried-over item is approved again only if its spend changes (§2.5).
6. Changes are counted together since the last approved version, so a run of small changes cannot pass a threshold unseen (§2.5, OD-11).
7. An item's budget in use is its incurred spend, else its released spend, else its planned spend (§2.5).
8. A Site's threshold wins over the portfolio's. An unset tolerance raises every adverse deviation. A hard-bound rejection is overridden only by a recorded change to the bound (§1.3, §2.4).
9. The manifest key `plan` stays as a machine-only exception to OD-6, and prose says "target" ("Words used here").

**Where the owner's view would help most:** calls 1 and 6, because they decide how often the executive is asked to approve.

## 5. Open queue

<!--derives: Decisions; §2.4; §2.7; §2.9; Words; DA §6; WP §1.1-->

Each item gives its context, an example and the default that applies until the owner answers.

| Item | Context | Example | Default (applies now) |
|---|---|---|---|
| **D15** First change at the end of the deep-dive | During the deep-dive the operator's own export is onboarded. The recommended option is replayed on it and its prediction frozen. The question is whether the change is agreed then and made when the pilot starts, or left to the pilot | At Kobo the deep-dive finds that lowering the generator stop threshold is Recommended. The operator agrees; the site manager creates the Actions when the pilot starts, and the pilot's three verdicts (§2.7) prove it | Adopt. Ask at alignment: "If the deep-dive finds a change worth testing, will you make it, under our supervision, when the pilot starts?" A no moves the first change into the pilot, and its proof about a month later |
| **D3, D4** Lead and second vertical | The design proves each construct on mini-grid first, with a cold and an EV test case (§2.9 step 5) | Kobo is the worked example; Harvest Cold and Metro Bus are the test cases | The mini-grid vertical goes first. The second vertical follows the first qualified prospect; cold if none |
| **D6** Replay figures shown to clients | Figures that rest on calibration replays K, M and E are design values until each replay passes | Kobo's stop-threshold value in Figure 5 is a design value until replay K runs | Shown, with the design-value label on every occurrence and said aloud at first sight. Never used as a result until the replay runs on the operator's own records |
| **D7** Approval before UI build | The owner will approve the mock-up once the pack is reviewed and confirmed | The recreated mock-up (mock-up lane) shows the design's screens (§2.8) | No UI build of Part 2 screens before the owner approves the design and the recreated mock-up. Step 1 of the delivery order (the last-day figure) is a correction, not a new screen, and may proceed |
| **D8** Re-benchmark | Build budgets rest on an old timing measure | — | Authorise one re-benchmark run on an allowed test database, as the first build task |
| **D9** Contract extraction | Contract rows decide who bears a repair cost (`worked-portfolios.md` §1.4) | A warranty clause extracted from a supplier contract | AI-assisted, with a person approving every row and its page reference, and no automated coverage conclusion: "Coverage is decided by the supplier or insurer" (Rules) |
| **Q14** Kisiwa battery saving | The deferred Kisiwa battery option's fuel saving has no model behind it in the demonstration world | Kisiwa's battery option in `worked-portfolios.md` §1.1 | Kept as a flagged assumption that changes no plan item; modelled only if a prospect makes battery sizing central |
| **Q15** When losing a unit breaches redundancy | Whether a generator carrying the shortfall keeps the obligation met is a policy, not a computed fact | Kisiwa and Mto in `worked-portfolios.md` §1.1 | The breach follows the capacity computed from records: if the standby unit covers the lost unit, it is not a breach. Overrule if the operator's licence counts any unit out as a breach |
| **Q16** Protective fallback when no set fits | When no affordable set meets every hard bound, should a decision fall back to an option that meets its bound but cannot be afforded with the rest (`design-appendix.md` §6, DL3) | At Lakeside with one crew visit, the plan proposed is infeasible | Report the set as not fitting, with its reason, and put it to the executive; never choose silently |

Commercial and schedule questions (owner time, peak days, free deep-dive limits, pilot fee form) live in `commercial-plan.md` and `two-week-build-plan.md`, under P4 of regeneration F.

## 6. Superseded items from earlier revisions

<!--derives: Decisions; Part 1; Part 2; §2.0; §2.9-->

Revisions 13 to 15 recorded rows Q1 to Q22 and A1 to A37 in `design-questions-and-decisions.md` (git keeps it). Each now sits in one line below, grouped by where it went.

| Items | Subject | Where it went |
|---|---|---|
| Q1, Q9 | The five mechanics of rev 13; the old delivery order | Superseded by Part 2's constructs (§2.0) and OD-9 (Figure 10) |
| Q2, Q3 | Portfolio frame; Act first that shows the plan | Superseded by §2.8: the frame stays, and Act first keeps the Finding triage first with the plan beside it |
| Q4, Q5, Q6, Q8 | Visual skin, demo logins, re-based demo Sites, currency | To the mock-up lane (regeneration F §6, step 7) |
| Q7 | EV tariff assumption, labelled with its switch | Kept in `worked-portfolios.md` §1.3 |
| Q10, Q11, Q12, Q13 | Second vertical, extraction, re-benchmark, replay labels | Became D4, D9, D8 and D6 (§3) |
| Q17, Q18, Q19 | Grounded path, emulators, first change | Became D13, D14 and D15 (§3) |
| Q20, Q21, Q22 | Owner time and free deep-dive limits | To `commercial-plan.md` |
| Q14, Q15, Q16 | Structure questions | Still open (§5) |
| A1, A35 | What a decision and a Finding rest on | Superseded by §1.3 and CH1: a Finding is the living result of evaluating a condition, pinned to the factor it observes |
| A3, A36 | Outcome map into one structure | Kept as B1's named change, behind a parity test (§2.1, §2.9) |
| A2, A23, A31, A34 | No stored totals; figures evaluated, never typed; specification first | Kept (Rules; `structure-specification.md`; `check_manifest.py`) |
| A4, A25, A27 | Bounds instead of text-only checks | Kept as hard, costed and advisory bounds on options (§2.4, "Words used here") |
| A5, A8, A20, A21 | Replay adapter, option generators, replay labels, calibration replays | Kept (§2.4; "Words used here"; Figure 10 step 0) |
| A6 | A separate store for commercial records | Kept (§2.3) |
| A7 | Two vocabularies for evidence | Kept as the evidence words (Rules); the code name is in `decision-loop-specification.md` |
| A9, A28 | Value against no action, net of the one-off | Kept as the valuation rule (§2.4) |
| A11 | A named person approves | Superseded by CH2 and the five roles (§2.6) |
| A13 | Attribution of products | Kept as "a declared rule, for products" (§2.2); the rule is in `decision-loop-specification.md` |
| A14 | No filters, role switches or new menus | Kept: roles are not views (§2.6); the frame stays (§2.8) |
| A15, A17, A18, A22, A33 | Protect and operations as measured factors; horizons | Kept in B1 (§2.1; `worked-portfolios.md` §1.0) |
| A16, A19, A29, A32 | Spend not valued in money; must-do items; crews, budget and dated dependencies | Kept in the plan's check of budget, crew visits and dates (§2.5; `structure-specification.md` §6) |
| A24, A26, A30 | Rights inside repair decisions | Kept (`worked-portfolios.md` §1.4) |
| A10, A12 | Mto connection cost basis; the private oracle | Kept in the demonstration world (`worked-portfolios.md` §2) |
| A37 | Reuse before rework | Kept as "Built on what exists" (Introduction) and the change register (§2.9) |
