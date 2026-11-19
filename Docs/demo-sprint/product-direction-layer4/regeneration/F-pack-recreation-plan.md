# F. Recreating the document packs from the design (plan for owner approval)

**AssetOps Architect (Claude) · 19 Nov 2026 · W1 structure only: no pack document is written or deleted until you approve this plan.**
**Direction** (`.agent/owner-recreate-document-packs-2026-11-19.md`): *"if this version is reviwed and all good, recreate (not update) all the document packs"*; *"the ones to regeneate are on the bases of this document (to they all align to it )"*. "This document" is `layer4-transformation-design.md` rev 16.5, with `worked-portfolios.md` and `design-appendix.md`. Every recreated document follows the brief in RULES §10.

**In short.** About 235k words (~470 pages) across 15 reading documents in three places become **9 recreated documents (~64 pages)**, plus the 3 design files as the single source. Every section of a recreated document names the design sections it derives from. A mechanical alignment check, written and reviewed first, fails any document that uses a construct, role, decision, name or figure the design does not define. Anything a document needs that the design lacks goes into the design first, as a gap.

## 1. The recreated pack

| # | Document | Action | Reader | Length | Derives from (design rev 16.5) |
|---|---|---|---|---|---|
| 0 | `layer4-transformation-design.md`, `worked-portfolios.md`, `design-appendix.md` | **Keep: the source.** Only the gap fixes in §3 | owner, everyone | as is | — |
| 1 | `decisions-register.md` | **Recreate**, merging `design-questions-and-decisions.md` and roadmap §6 | owner, builders | 3 pp | Decisions; §2.4–§2.6; §2.9; owner files |
| 2 | `decision-loop-specification.md` | **Recreate**, merging `economic-metric-and-effect-contracts.md` and `domain-and-decision-models.md`, one section per construct | builders | 12 pp | §1.2–§1.4, §2.0–§2.8; worked-portfolios §1 |
| 3 | `integration-design.md` | **Recreate** from `integration-source-to-canonical-design.md` | builders, analyst | 7 pp | §2.3 (B3); §2.9 lane A, OD-9; D14; appendix §5 |
| 4 | `structure-specification.md` | **Keep**, with one naming line (OD-6). See pushback P1 | checker author, builders | 5 pp | §2.1, §2.4, §2.5 (computation) |
| 5 | `reuse-and-gap-matrix.md` | **Recreate** from `repo-reuse-and-gap-matrix.md`, grouped by §2.9 rows | builders | 5 pp | §2.9; Part 1 code references |
| 6 | `delivery-plan.md` | **Recreate**, merging `phase-plan-and-acceptance.md`, the build part of `two-week-conversion-plan.md`, roadmap §3–§4 and `demo-build-cost-plan.md` (Q-F2) | owner, builders | 9 pp | §2.9 and Figure 10 (OD-9); worked-portfolios §2; register |
| 7 | `outcome-lever-capability-traceability.csv` | **Regenerate columns** by a reviewed mapping: mechanic M1–M5 → construct ID; CEO/CFO/CCO → §2.6 roles. The 454 rows stay | builders, checker | data | §2.0 IDs; §2.6 roles |
| 8 | `interactive-mockup-vNEXT/walkthroughs.md` | **Recreate**, folding in README and the inspection checklist, after the mock-up revision (Q-F3) | owner, presenter | 3 pp | §1.4, §2.6, §2.8; worked-portfolios §1 |
| 9 | `commercial-plan.md` (go-to-market) | **Recreate** | owner | 7 pp | Product claims: §1.1, §1.5, §2.0, §2.6, Decisions. Commercial facts: register (Q-F4) |
| 10 | `website-content.md` (go-to-market) | **Recreate** | owner, site editor | 7 pp | "Now" = Part 1; "Coming" = Part 2 in §2.9 order; "Rules every figure follows" |
| 11 | `website-revision-recommendation.md` (website repo) | **Recreate last**, on its own branch, not pushed | owner, site editor | 6 pp | #10, plus a fresh audit of the site |
| — | `product-transition-and-roadmap.md` (+ .html) | **Retire**: absorbed into the design, #1, #6, #9 and RULES §4 (Q-F1) | | | |
| — | `two-week-conversion-plan.md` (+ .html) | **Retire**: build part to #6, selling track (§7) to #9 | | | |
| — | `demo-build-cost-plan.md` | **Retire**: merged into #6 §4 | | | |
| — | `derivation-register.md` | **Move to `evidence/`, unchanged**: it is perturbation evidence for the manifest, which does not change. Its §9 limits move into the design appendix (G-F3) | | | |
| — | Mock-up generated documents (`CHANGE-REGISTER`, `fixture-mapping`, `browser-audit`, `screenshots/INDEX`) | **Regenerate** by their tools after the mock-up revision; never hand-written | | | |
| — | `REVIEW.md` and `REVIEW-response.md` (Layer 4); the four REVIEW files (go-to-market) | **Drop** from the tree. Git keeps them; the last commit hash goes into design-appendix §4. Their owner decisions are already in #1 | | | |

## 2. Inventory: what each current document holds, and what is wrong against rev 16.5

Classes are from audit A: **C1** a Finding treated as a condition; **C2** the person absent, so the system appears to act; **C3** today misdescribed; **C4** replacement framing; **C5** boosters not recognised; **OD-6** "plan" used for targets. The counts are grep indicators; the full sweep is done when writing.

| Current document | Purpose | Size (words) | Wrong or stale against rev 16.5 |
|---|---|---:|---|
| `product-transition-and-roadmap.md` | Owner's entry: today, strategy, roadmap, workflow, D-register | 21.3k | C1 (15, incl. §1.1 "conditions on factor keys"), C2 (loop without actors), C4 (26), OD-6 (21); slice path predates OD-9; §6 is the D-register's only home |
| `structure-specification.md` | Evaluation contract the independent model is written from | 2.5k | No C1–C5. One OD-6 line (the `period.plan` side). Its allocator "plan" is P's computation, which is consistent |
| `domain-and-decision-models.md` | Algorithms, lifecycle, allocator, verification | 17.4k | C1 (11), C2 (lifecycle without a recorded person); built on M1–M5, not on the constructs; lacks P (origin and membership, OD-4/7/8) and roles |
| `economic-metric-and-effect-contracts.md` | Structures, identities, evidence classes, rights in money | 12.4k | Built on M1–M3; C4 (10); OD-6 (7); no P or CH2. Identities and honesty rules still valid |
| `integration-source-to-canonical-design.md` | Sources → canonical → leaves; emulators | 13.7k | C1 (6). Mostly valid as B3. Predates OD-9 (format and leaf IDs first) |
| `phase-plan-and-acceptance.md` | Slices and gates | 8.3k | Slice order from the old path (D13 lanes), not Figure 10; G1/G2 not slices; OD-6 (11) |
| `design-questions-and-decisions.md` | Q1–Q22, A1–A37 | 5.3k | Predates Q-A1/2 and OD-1–9; C1 (3); several A-items superseded |
| `repo-reuse-and-gap-matrix.md` | Function-level dispositions | 10.1k | Built on M1–M5; §H "parts that no longer fit" (C4); no CH2 or P rows. Code references mostly valid |
| `derivation-register.md` | Every non-derived item, with perturbation evidence | 65.0k | Manifest and evaluator parts valid; §6 (documents) and §7 (mock-up) stale |
| `demo-build-cost-plan.md` | Demonstration-world build and cost | 4.9k | M1–M5 framing; costs marked "to be re-measured" |
| traceability CSV | Outcome → lever → capability rows | 454 rows | `mechanic` column M1–M5; roles CEO/CFO/CCO do not match §2.6 |
| Mock-up README, walkthroughs, checklist | How to inspect and present the mock-up | 3.7k | Describe mock-up rev 13: "Actual against plan", "Opportunity", no plan beside Act first, no approval shown (§2.8) |
| Mock-up generated documents | Audit and inventory output | 16.5k | Stale only as the mock-up is |
| REVIEW, REVIEW-response (both packs) | Review history up to rev 15 | 117k | History only |
| `two-week-conversion-plan.md` (go-to-market) | Fortnight build schedule; selling track | 23.0k | Scope built on old slices (56 refs); C1 (7); OD-6 (9); roadmap refs (36). Owner-time inputs TW25/26 still valid |
| `commercial-plan.md` | Buyers, engagement path, pricing, revenue | 16.2k | D1 path valid. Positioning predates C5 and the decisions-and-accountability value (P, CH2); 42 roadmap refs; OD-6 (5) |
| `website-content.md` | Public copy deck and its lint | 15.9k | Now/coming split predates Part 1/Part 2; OD-6 (10); 26 roadmap refs |
| `website-revision-recommendation.md` | Site audit and migration | 15.7k | Derived from copy deck rev 4.1; stale wherever the deck is |

## 3. Alignment: no recreated document can contradict the design

**Mechanical check, `check_alignment.py`** (new, standard library). It is written with planted-violation fixtures and reviewed **before** any document (W2). `check_manifest.py` calls it, so one command checks the pack.
- **A1 Derivation markers.** Every `##` section opens with `<!--derives: §2.5; OD-1, OD-4-->`. A section without one fails, and so does a cited heading the design lacks.
- **A2 Lexicon from the design.** The check extracts these from the design itself:
  - construct and gap IDs (B1–B3, P, CH1–CH5, L1–L7, G1, G2);
  - decision IDs;
  - the five role names of §2.6;
  - the ten evidence words;
  - the five dispositions;
  - the bound kinds.
  An ID or a role in a derived document that is not in the lexicon fails. Buyer titles such as CFO are allowed only in #9–#11.
- **A3 Retired terms fail.** These are "factor key", "condition(s) on" for a Finding (C1), "M1 Define"…"M5 Prove", "Actual against plan", "operational plan", and "plan" for a target (OD-6). So does "the system chooses / approves / decides / acts / creates" (C2). "Replace", "retire" and "no longer" (C4) are flagged for the reviewer, not failed.
- **A4 Decisions.** The register's text for each ID must match the design's Decisions table, and every other document cites a decision by ID only.
- **A5 Figures.** Every figure carries a `fig`/`figx` marker checked by `check_manifest.py`, or comes from `plan_model.py --check`. An untagged money or percentage figure fails.
- **A6 Coverage.** Each §2.x construct appears in the markers of at least one builder document (#2, #3, #5, #6).

**Gaps first.** A recreated document adds detail beneath a design construct, such as schemas, algorithms, permissions or slices. It never adds a new construct, role, decision, status or figure. If it needs one, the writer stops, the Architect adds it to the design (a small fix with a verification review), and only then does the derived text cite it.

**Gaps known now** (to fix in the design in the current review's fix round):
- **G-F1.** The design sends D-numbers and D15 to roadmap §6. Point them to #1.
- **G-F2.** Update the appendix "where the detail lives" table to the new files.
- **G-F3.** The documented limits are cited from `derivation-register.md` §9. Move the list into design-appendix.
- **G-F4.** worked-portfolios cites `demo-build-cost-plan.md`. Point it to #6.
- **G-F5.** State that the manifest key `plan` (a Site's target side) is a machine path kept under OD-6, and that prose says "target". Lint ignores markers. *Architect's call:* renaming the key would touch the manifest, evaluator, independent model and fixtures for no reader-visible gain.

**The judgement part.** For each document, a fresh reviewer reads it against the design sections its markers cite.

## 4. What each recreated document contains

Every document opens with existing-before-new and a *Serves the objective* line, says who sees, decides, acts and tracks, and ends with its open questions and their defaults (RULES §10). It reuses the design's figures by reference. It adds a diagram only where it adds detail.

- **#1 Register.**
  - How to read: decided, Architect's call, or pending with a default.
  - Owner decisions (D1–D15, Q-A1/2, OD-1–9): words, date, source file, where applied.
  - Architect's calls.
  - Open queue.
  - Superseded A- and Q-items, one line each.
  - No diagram.
- **#2 Specification**, one section per construct, each with its records, rules, states, API and tests:
  1. Today's records that stay (Finding, revision, thread, carriers).
  2. B1 registry and bottom-up evaluation; parity test.
  3. CH1 pinning, structure observer, tolerance (OD-3).
  4. B2 targets, budget lines, the bridge identity.
  5. CH3 option record, bounds, dispositions, threshold (OD-2, OD-8).
  6. P plan record, origin and membership, approval and return (OD-1/4/5/7).
  7. CH2 principal, role-by-command permissions, overdue.
  8. CH4 three verdicts, field evidence, option cost.
  9. CH5 read models.
  10. Evidence classes and negative accounting tests.

  Diagrams: the record relationships, and the Action state diagram (origin, membership, release, return).
- **#3 Integration.**
  - What the ledger and gateway carry today.
  - Leaf → facts → source table.
  - Canonical format v1 and leaf IDs (OD-9 step 1).
  - Stores by the nature of the fact.
  - Emulators and the contract test (D14, Emulated).
  - Emulator to pilot adapter, and the pilot asks.
  - Disorder and isolation tests.

  Diagrams: one source → leaf flow, and a sequence for a record import accepted by the analyst.
- **#5 Matrix.** One table per §2.9 row: function, file:line, stays/extends/changes, migration rule, test gap. New components in migration order. No diagram.
- **#6 Delivery plan.**
  1. Figure 10 order, and why.
  2. Slices per step, with gates and acceptance questions (W1).
  3. The first fortnight: capacity, schedule, stretch line, drop order (`plan_model.py` tables).
  4. The demonstration-world build and its cost.
  5. Checks first (W2) and the release tests.
  6. Owner checkpoints (W8), and from pilot to SaaS (D1).

  Diagram: the fortnight's generated gantt.
- **#8 Walkthroughs.** Seven minutes per vertical: who sees, decides, acts and tracks on each screen; "not available yet"; the inspection checklist.
- **#9 Commercial plan.**
  - Buyers.
  - Positioning: today's core, plus the boosters, the plan and the recorded person, against monitoring tools.
  - Engagement path (D1).
  - Pricing.
  - Sales motion and owner time (TW25/26).
  - Unit economics.
  - Risks.
  - Decisions.

  Diagram: the engagement path with who decides at each step.
- **#10 Website content.**
  - Audience.
  - Messages (today / coming).
  - Copy deck by page.
  - Stage gates tied to delivery steps.
  - Honesty rules (lint).
  - Decisions.
- **#11 Recommendation.**
  - What the site has.
  - Audit against #10.
  - What must not go out.
  - Structure on the Astro site.
  - Migration order.
  - Decisions.

## 5. Machinery

| Tool | Kept or changed |
|---|---|
| `demo-site-scenario-manifest.yaml`, `evaluate_structure.py`, `independent_model.py`, `derived-values.json` | **Unchanged.** Rev 16.5 changes no figure. The independence chain holds because #4 stays (P1) |
| `check_manifest.py` | Kept. `FIG_DOCS` and `REQUIRED` are rewritten for #1–#10, each listing the figures that document must carry, so every figure keeps a checked home. Calls `check_alignment.py` |
| `check_alignment.py` + fixtures | **New**, written first (§3) |
| `render_design_html.py`, `motivation_figures.py` | Kept. The renderer is generalised to render every Layer 4 document |
| `render_product_transition_html.py`, `render_two_week_plan_html.py` | Retired with their documents. The gantt drawing moves into the general renderer |
| `plan_model.py` | Kept and moved to the Layer 4 pack with #6. Scope is re-derived from Figure 10's steps. `--check` targets #6 and the tables in #9. The 18 Nov measurements are kept, labelled with their date |
| `render_commercial_plan_html.py`; `render_website_content_html.py` with `website-copy-lint-fixtures.txt` | Kept. The lint adds the A3 terms, with planted lines such as "AssetEcon decides for you" and "Actual against plan" |
| Mock-up tools (`gen_docs.cjs`, `audit.mjs`, `gen_fixtures.py`, `hand_typed_scan.py`, `replay_values.py`); `src-v70-baseline/` | Kept |
| All `.html` renders | Regenerated, never hand-edited |

## 6. Order, lanes and review (W4, W5)

1. **Gate.** Rev 16.5 is accepted, you approve this plan, and G-F1–G-F5 land in the design's fix round.
2. **Checks first, in parallel with #1:**
   - `check_alignment.py` and the `check_manifest.py` lists;
   - #1, which every other document cites.
3. **Two lanes:**
   - **Lane A (product):** #2, #3 and #5 in parallel, then #7 (mechanical, after #2) and the #4 line.
   - **Lane B (plan and market):** #6 (drafted from Figure 10, slice names final after #5), and #9 alongside it (its dates come from #6's model). Then #10, after #9.
4. **Whole-pack review.** The alignment check is green. One discovery reviewer reads all recreated documents against the design, and each finding is answered with its class and sweep (W6).
5. **Retire, move and drop.** The router and NOW pointers are updated (coordinator follow-on).
6. **Website repo, last.** #11 goes on a new branch in `/opt/asseteconsite/assetecon` off `docs/website-revision-recommendation`. It is committed, not pushed.
7. **Mock-up lane (if Q-F3 yes).** Revise vNEXT to §2.8, regenerate its generated documents, then write #8.

**Branches.** The Layer 4 documents go on this branch. The go-to-market documents go on `task/gtm-documents` after it merges this branch. Each document has one fresh Architect writer.

**Review, matched to risk:**
- **Discovery review:** #2 (new schemas, P, CH2, money), #3 (new contract), #6 (time and cost figures), #9 (pricing and revenue) and `check_alignment.py` (it is the control).
- **Verification review:** #1, #5, #8, #10 (lint plus one read) and #11.
- **Mechanical check:** #7, the #4 line, renders and drops.

## 7. Pushbacks on "recreate everything"

- **P1. Keep `structure-specification.md`, don't recreate it.** The independent model was written from it alone. Rewriting it would force an independent rewrite of the checker for no change in meaning: it has no C1–C5 instance and one OD-6 line.
- **P2. Generated data is regenerated, not recreated.** This covers the manifest, evaluator and derived values (unchanged), the CSV (columns remapped mechanically), the mock-up's generated documents (by their tools) and the HTML (rendered).
- **P3. The mock-up code is not a document.** It changes in its own lane, mock-up first, as you asked for earlier, and only then is its walkthrough rewritten.
- **P4. Two source layers, not one.** Product claims in #6, #9 and #10 derive from the design and are checked by A1–A6. Pricing, sales capacity, owner time and schedule come from your decisions (register) and `plan_model.py`. Adding them to the design would undo its "short, intentional" form.
- **P5. The derivation register moves to `evidence/`.** Its 65k words are evidence about an unchanged manifest. It is not a reading document.
- **P6. Merge rather than recreate one for one.** Fifteen reading documents become nine, and nothing a builder or you need is lost: the §2 table maps every old document to its new home.

## 8. Questions for the owner (my default applies until you answer)

- **Q-F1. Retire the roadmap?**
  - *Context:* you read the roadmap's §1.1 as your entry point. Its parts now live in the design (today and the new constructs), #1 (§6 decisions), #9 (§2 engagement path), #6 (§3–§4) and RULES §4 (§5 workflow).
  - *Example:* "Where is the engagement path?" Answer: #9 §3.
  - *Default:* retire it; the design doc is the entry document.
- **Q-F2. Merge the two-week plan into the delivery plan, and restart the fortnight?**
  - *Context:* its schedule is built on the slice path that Figure 10 replaced.
  - *Example:* day 3 currently builds a slice that OD-9 now orders after the canonical format.
  - *Default:* merge it into #6. Day 1 is the first build day after you approve the recreated pack.
- **Q-F3. Revise the mock-up to §2.8 before rewriting its walkthrough?**
  - *Context:* vNEXT shows "Actual against plan" and "Opportunity", with no plan beside Act first and no approval shown.
  - *Example:* a walkthrough written now would describe screens that don't exist.
  - *Default:* yes. The mock-up revision is its own lane after the pack, and #8 follows it. Until then, the current walkthrough is marked "describes mock-up rev 13".
- **Q-F4. Accept the two source layers (P4)?**
  - *Example:* the pilot price comes from your decision C-items, not from the design.
  - *Default:* yes.

On approval I record this plan, with its Architect's calls (G-F5, P1–P6), in the decisions index.
