# F. Recreating the document packs from the design

**AssetOps Architect (Claude) · 19 Nov 2026 · rev 2: approved by the owner on 19 Nov, with the changes below.**

**Direction** (`.agent/owner-recreate-document-packs-2026-11-19.md`):
- *"if this version is reviwed and all good, recreate (not update) all the document packs"*;
- *"the ones to regeneate are on the bases of this document (to they all align to it )"*.

"This document" is the design, `layer4-transformation-design.md`, now at rev 16.7, with `worked-portfolios.md` and `design-appendix.md`. Every recreated document follows the brief in RULES §10.

**The owner's answers** (verbatim in the same file, "Owner's answers on the recreation plan"):
- **Q-F1. Yes:** "yes retire the old one". The roadmap is retired.
- **Q-F2. Changed:** "recreat tehe two week plan focussed on advancing as much as possible towarfs the new features, not the markting element". The two-week plan is recreated as its own build plan (#6b), with no selling track.
- **Q-F3 and Q-F4. Defaults accepted:** "i agree with the rest of the defaults". The owner also accepted the two plan-gap defaults, now OD-10 and OD-11 in the design.
- **New document:** "more clarity on the action plan aspect … in its workflow document that combines workflow, finan ces, ownership and system mechanics". This is #12.
- **Mock-up:** "more professional in temrs of ites usage of space and modern state of the art ui/ux as well as not using technical workds that should not be user facing". The coordinator runs this in its own lane and worktree. #8 follows that lane.

**In short.** About 235k words (~470 pages) across 15 reading documents become **11 recreated documents (~77 pages)**, plus the 3 design files as the single source.
- Every section of a recreated document names the design sections it derives from.
- `check_alignment.py` was written and proven before any document. It fails any document that uses a construct, role, decision, name or figure the design does not define.
- Anything a document needs that the design lacks goes into the design first. Rev 16.7 did this for the workflow document (§3).

## 1. The recreated pack

| # | Document | Action | Reader | Length | Derives from (design rev 16.7) |
|---|---|---|---|---|---|
| 0 | `layer4-transformation-design.md`, `worked-portfolios.md`, `design-appendix.md` | **Keep: the source.** Fixed first under the gaps rule (§3) | owner, everyone | as is | — |
| 1 | `decisions-register.md` | **Recreate**, merging `design-questions-and-decisions.md` and roadmap §6 | owner, builders | 3 pp | Decisions; §2.4–§2.6; §2.9; owner files |
| 2 | `decision-loop-specification.md` | **Recreate**, merging `economic-metric-and-effect-contracts.md` and `domain-and-decision-models.md`, one section per construct | builders | 12 pp | §1.2–§1.4, §2.0–§2.8; WP §1 |
| 3 | `integration-design.md` | **Recreate** from `integration-source-to-canonical-design.md` | builders, analyst | 7 pp | §2.3 (B3); §2.9 lane A, OD-9; D14; DA §5 |
| 4 | `structure-specification.md` | **Keep.** Naming amended in rev 13.1 (OD-6), with no rule changed (P1) | checker author, builders | 5 pp | §2.1, §2.4, §2.5 (computation) |
| 5 | `reuse-and-gap-matrix.md` | **Recreate** from `repo-reuse-and-gap-matrix.md`, grouped by §2.9 rows | builders | 5 pp | §2.9; Part 1 code references |
| 6 | `delivery-plan.md` | **Recreate**, merging `phase-plan-and-acceptance.md`, roadmap §3–§4 and `demo-build-cost-plan.md` | owner, builders | 8 pp | §2.9 and Figure 10 (OD-9); WP §2; register |
| 6b | `two-week-build-plan.md` | **Recreate** from `two-week-conversion-plan.md` as an ambitious fortnight build plan. The selling track is dropped | owner, builders | 5 pp | §2.9, Figure 10, OD-9; #6's slices; `plan_model` |
| 7 | `outcome-lever-capability-traceability.csv` | **Regenerate columns** by a reviewed mapping: mechanic M1–M5 → construct ID; CEO/CFO/CCO → §2.6 roles. The 454 rows stay | builders, checker | data | §2.0 IDs; §2.6 roles |
| 8 | `interactive-mockup-vNEXT/walkthroughs.md` | **Recreate** (README and checklist folded in) after the coordinator's mock-up lane | owner, presenter | 3 pp | §1.4, §2.6, §2.8; WP §1 |
| 9 | `commercial-plan.md` (go-to-market) | **Recreate.** It takes only the selling content it needs from the old two-week plan | owner | 7 pp | Product claims: §1.1, §1.5, §2.0, §2.6, Decisions. Commercial facts: register (P4) |
| 10 | `website-content.md` (go-to-market) | **Recreate** | owner, site editor | 7 pp | "Now" = Part 1; "Coming" = Part 2 in §2.9 order; Rules |
| 11 | `website-revision-recommendation.md` (website repo) | **Recreate last**, on its own branch, not pushed | owner, site editor | 6 pp | #10, plus a fresh site audit |
| 12 | `plan-and-action-workflow.md` | **New.** The plan and Action workflow: who does what and when, the money, ownership and approval, states and versions, and the system's part, at Kobo and Lakeside | owner, builders | 6 pp | §1.4, §2.4–§2.6; Figures 5–8, 6b; OD-1, OD-2, OD-4, OD-5, OD-7, OD-8, OD-10, OD-11; WP §1.1 |
| — | `product-transition-and-roadmap.md` (+ .html, renderer) | **Retire** (Q-F1): absorbed into the design, #1, #6, #9 and RULES §4 | | | |
| — | `two-week-conversion-plan.md` (+ .html, renderer) | **Replaced by #6b.** The selling track (§7) is dropped; #9 keeps only what it needs | | | |
| — | `demo-build-cost-plan.md` | **Retire**: merged into #6 | | | |
| — | `derivation-register.md` | **Move to `evidence/`, unchanged**. It is evidence for the manifest, which does not change; its limits are now design-appendix §6 | | | |
| — | Mock-up generated documents (`CHANGE-REGISTER`, `fixture-mapping`, `browser-audit`, `screenshots/INDEX`) | **Regenerate** with their tools in the mock-up lane | | | |
| — | REVIEW and REVIEW-response files (two in Layer 4, four in go-to-market) | **Drop.** Git keeps them; the last commit hash goes into design-appendix §4 | | | |

**Why #6b is a separate document** (the owner's words make separate the default, and the merits agree):
- **A different lifetime.** #6 holds the whole path: steps, slices and gates, stable until the design changes. #6b is a fortnight's schedule, re-cut at each owner sitting.
- **Its own computed model.** `plan_model.py` computes #6b's tables (capacity, pace, days, stretch line, drop order) and checks them with `--check`.
- **No duplication.** #6b cites #6's slices by ID and never restates a gate.

**#6b's aim** (owner): advance "as much as possible towards the new features".
- Its scope is ranked along Figure 10: step 1, then the step-2 format and leaf IDs, then lanes 3A, 3B and 3C together, then as far towards the join and step 6 as capacity allows.
- Demo days and selling work are out of scope.

## 2. Inventory: what each current document holds, and what is wrong against the design

Unchanged from rev 1 of this plan, which was approved. Its classes are those of audit A:
- **C1:** a Finding treated as a condition.
- **C2:** the person absent.
- **C3:** today's product misdescribed.
- **C4:** replacement framing.
- **C5:** boosters not recognised.
- **OD-6:** "plan" used for targets.

Its main counts:

| Document | Main counts |
|---|---|
| Roadmap | C1 15, C4 26, OD-6 21 |
| Domain models | C1 11 |
| Matrix and phase plan | built on M1–M5 |
| Two-week plan | 56 references to the old slice path |
| Commercial plan and copy deck | 42 and 26 roadmap references |

The full table is in git at `828a144ce`.

## 3. Alignment: no recreated document can contradict the design

**`check_alignment.py` exists and is proven** (W2). `check_manifest.py` runs it, so one command checks the pack.
- **A1. Derivation markers.** Every `##` section opens with `<!--derives: …-->`. A reference resolves only if it is one of:
  - a design section (`§2.5`), a companion section (`WP §1.1`, `DA §5`), a figure, or one of Part 1, Part 2, Words, Rules, Decisions, Introduction;
  - a construct or decision ID;
  - an owner record that exists (`owner: .agent/….md`), or `plan_model`.
- **A2. Lexicon, extracted from the design.** It holds the construct and gap IDs, the decision IDs, the five roles, the five dispositions and the ten evidence words. Buyer titles are allowed only in #9 and #10.
- **A3. Retired terms.** It fails:
  - C1 phrasing;
  - the M1–M5 names;
  - "the system or product chooses or approves" (C2);
  - "plan" for a target (OD-6). This is the naming lint, now judged sentence by sentence, and it also runs on the design itself.

  C4 words are listed for the reviewer, not failed.
- **A4. Decisions.** The register must hold every design decision with the design's exact words. Elsewhere, a decision is cited by ID, never restated as a row.
- **A5. Figures.** Every money or percentage figure needs a `fig`/`figx` marker, or must sit in a `<!--table:…-->` block from `plan_model.py`. Each derived document present also joins `check_manifest.py`'s anchor scan, so every figure keeps a checked home.
- **A6. Coverage.** Once all five builder documents (#2, #3, #5, #6, #12) exist, their markers together cite every §2.x section.

**Gaps first.** A derived document adds detail beneath a construct, such as schemas, algorithms, permissions or slices. It never adds a new construct, role, decision, status or figure. If it needs one, the design gets it first.

**What rev 16.7 added for #12:**
- **OD-10:** the system opens the draft.
- **OD-11:** what makes a new version.
- **The plan's period** and the carry-over of unfinished items.
- **Versions**, and the five states defined (Figure 6b).
- **The crew-visit threshold.**
- **Changes counted together** since the last approved version.
- **Spend in three steps,** counted once.
- **Item and Action ownership.**
- **Where a version awaits approval:** on Act first, with no notification.
- **The threshold rule for proactive items.**

The lexicon has G1 but no G2, because the design names only G1. Plan rev 1's "G1, G2" is corrected.

**Judgement.** A fresh reviewer reads each document against the sections its markers cite.

## 4. What each recreated document contains

Unchanged for #1–#3, #5, #8 and #9–#11 (rev 1, `828a144ce`). Every document:
- opens with what exists before what is new, and a *Serves the objective* line;
- says who sees, decides, acts and tracks;
- ends with its open questions and their defaults.

Each reuses the design's figures by reference.

- **#6 Delivery plan.**
  1. Figure 10's order, and why.
  2. Slices per step, with gates and acceptance questions.
  3. The demonstration-world build and its cost.
  4. Checks first (W2) and the release tests.
  5. Owner checkpoints (W8), and from pilot to SaaS (D1).
- **#6b Two-week build plan.**
  1. The fortnight's aim: the furthest point on Figure 10 it can reach.
  2. Capacity: machine, lanes, people and owner time (`plan_model`).
  3. Scope ranked by step, slices cited from #6.
  4. The fourteen days.
  5. Pace, the stretch line and the drop order.
  6. What day 14 shows on screen: built features only, each with its evidence label.
  7. Decisions for the sitting.

  Diagram: the generated fortnight gantt.
- **#12 Plan and Action workflow.**
  1. Today's act-and-track flow, which stays.
  2. The five roles: what each decides, does and has recorded.
  3. A period's plan from opening to close (process flow).
  4. Kobo: from Finding to released Actions, below and above the threshold (sequence).
  5. Lakeside: proactive items and the cross-Site trade at Mto and Kisiwa, as a revision (OD-11).
  6. The money: budget, thresholds, release, and planned, released and incurred spend counted once on the item.
  7. Ownership and approval: item owner, Action owner and due date, the approver, and send-back and return (OD-4).
  8. States: plan version, item and Action (state diagrams).
  9. What the system does at each step, and what it never does.
  10. Open questions.

## 5. Machinery

Unchanged from rev 1, except:
- `check_alignment.py`, `alignment-fixtures/` and `naming-lint-fixtures.txt` are built (§7).
- The naming lint moved out of `check_manifest.py` into rule A3.
- The renderer refuses any split table, with `SystemExit`, not an assert (review G, N8).
- `plan_model.py` moves to the Layer 4 pack. `--check` targets #6b's tables, plus #9's owner-time table.
- `render_two_week_plan_html.py` is retired. #6b renders through the general renderer.

## 6. Order, lanes and review

1. **Done (step A).** This plan is updated; the design is at rev 16.7 (G-verify N2–N9, OD-10, OD-11, and the additions for #12); the naming lint is tightened; `check_alignment.py` is built and wired in. Decisions are recorded in `.ai/decisions/2026-11.md`.
2. **#1 first**, because every other document cites it.
3. **Two lanes:**
   - **Lane A (product):** #2, #3, #5 and #12 in parallel, then #7 (mechanical, after #2).
   - **Lane B (plan and market):** #6, then #6b (it cites #6's slices). Alongside them, #9, then #10 after #9.
4. **Whole-pack review.** `check_manifest.py` is green, with A6 live. One discovery reviewer reads all documents against the design, answered by class and sweep (W6).
5. **Retire, move and drop**, with the router pointers updated.
6. **The website repo, last.** #11 goes on a new branch off `docs/website-revision-recommendation`. It is not pushed.
7. **The mock-up lane** (coordinator): its generated documents, then #8.

**Review, matched to risk:**
- **Discovery:** #2, #3, #6, #6b (time figures), #9 and #12 (a new mechanism, money).
- **Verification:** #1, #5, #8, #10 and #11.
- **Mechanical:** #7, renders and drops.

## 7. Pushbacks (P1–P6, accepted with the defaults)

- **P1.** Keep `structure-specification.md`. Rev 13.1 changes only its prose naming, so the independent model written from it stays valid.
- **P2.** Generated data is regenerated, not recreated.
- **P3.** The mock-up is a lane, not a document.
- **P4.** Two source layers: product claims from the design, commercial and schedule facts from the owner's decisions and `plan_model`.
- **P5.** The derivation register moves to `evidence/`.
- **P6.** Merge where nothing is lost. #6b is the one exception, on the owner's word and on merit (§1).
