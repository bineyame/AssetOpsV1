# Layer 4 regeneration, Phase C: re-review of rev 16.1

**Reviewer:** fresh AssetOps reviewer (Claude), not the author of rev 16, rev 16.1 or review B · 19 Nov 2026 · branch `task/layer4-design-regeneration`, head `55acd729c`; diff checked against `ad35c6ed9`.
**Under review:** `layer4-transformation-design.md` (rev 16.1) and `.html`; `worked-portfolios.md`; `design-appendix.md`.
**Standard:** `.agent/owner-design-regeneration-request-2026-11-19.md` (owner, verbatim). Review B's findings and the commit message were treated as claims to check.

## Summary

- **Verdict: REVISE.** A very small round. The main document now fixes M1 well. The companion `worked-portfolios.md` still describes the old mechanism, and the owner's central question is not settled while it does (N1).
- **Prior findings:** 18 of 19 actionable items fixed (H1, M2, M3, L1–L12, I2, I3). M1 is **partly fixed**: the main document is fixed, the companion is not.
- **New findings:** Medium 1 · Low 3 · Info 3.
- **N1 (Medium):** in `worked-portfolios.md`, the system's search still picks one option per decision across all options. The managers' choices are never an input. Actions are raised *after* the plan is approved, which reverses the main document's order.
- **N2 (Low):** the release rule contradicts itself. A "remote setting change" is said to go ahead without the plan, yet Kobo's remote stop-threshold change spends 90.00 and is a plan item.
- **Checks:** `check_manifest.py` 3,758 passed, 0 failed (one more than round 1: the newly tagged cooling figure). `motivation_figures.py --check` reports 2 figures, none missing or unused. The HTML re-render is byte-identical. All 10 Mermaid blocks were linted by reading and are clean, but **none was parsed**.
- **All seven newly cited code locations confirmed**; one older citation is two lines off (I2).

---

## 1. Status of review B's findings

| # | Status | Evidence |
|---|---|---|
| **H1** `;` in sequence messages | **Fixed** | Figures 7a and 7b (l.511-549) have no `;` or `#` in any message. Every other `;` in the 10 blocks sits inside a quoted flowchart label (l.278, l.579, l.624, l.631), where the string lexer consumes it |
| **M1** who chooses and who creates the Action | **Partly fixed**: main document yes, companion no (see N1) | Main document: §2.4 steps 1–4 (l.410-414) say that the system evaluates and proposes ("It picks nothing"), the manager chooses, and the manager "creates one or more Actions against the Finding", including from a Finding with no decision. The plan "checks the managers' chosen set … It changes no one's choice" (l.417). The plan-versus-Action table (l.431-432) names the creator and puts creation before release. The §2.5 closing line (l.473) reads "It never chooses, approves or creates an Action." This is consistent with Figure 1 (l.219), Figure 5 (l.405), Figure 6 (l.488-489), Figure 7b (l.540-544), the §2.8 Actions row (l.611) and Q-A3 (l.653). It matches the owner's "the user likely reate one more action against it" and "users to act on the bases of context given to them, then tracked". **Not carried into `worked-portfolios.md`** (N1). Two smaller seams remain (N2, N3) |
| **M2** "Chosen" in worked-portfolios | **Fixed** | No "Chosen" remains. l.242 and l.566 now say "Recommended". l.574 is active ("the site manager raises the Actions"), but its ordering conflicts with the main document (N1) |
| **M3** today's opportunity carrier | **Fixed** | §1.2 Act row (l.108), the §1.4 row and paragraph (l.145, l.155) and a §2.8 row (l.614) with merit and "one carrier per thing". The code agrees: the study is a thread occurrence with an exclusive Finding/opportunity source (`0042_chain_threads.py:43-62`, `occurrence_one_source` l.53), and the MINI domain action carries an opportunity origin (`0051…:1-12`). One overstatement remains (N4) |
| **L1** credit / status citations | **Fixed** | `outcomes/credit.py:57-73` is `credited()` (the file has 104 lines). `outcomes/status.py:55-104` is `outcome_state`, with ON_PACE / BEHIND_PACE at l.90-93. The audit was corrected too |
| **L2** work case owner and due date | **Fixed** | l.144: "an optional owner label and due date … a work case (title; an assignee when assigned)" |
| **L3** VERIFY versus evaluator | **Fixed** | §1.4 System row (l.146); Figure 7a l.523-524 split into a command and an evaluator step |
| **L4** rival explanations scope | **Fixed** | l.107: "mini-grid dispatch Findings also carry a claim ceiling and rival explanations" (`alternatives.py:47-48`) |
| **L5** grep wording | **Fixed** | l.439: "in today's backend or schema (the only 'budget' hits are layout code in the frontend)" |
| **L6** "only HTTP client" | **Fixed** | l.179 cites the intake routes: `reading_upload_api.py:113` (POST reading-uploads), `work/operational_entry.py:25-30`, `financials/assumptions.py:32-58` and `gateway_api.py` (the file exists). It says "no client calls any external system" |
| **L7** letter-of-intent condition | **Fixed** | l.436: "if the cooperative does not extend its letter of intent" |
| **L8** roles "awaiting" | **Fixed** | `worked-portfolios.md` l.9 |
| **L9** stale cross-references | **Fixed** | `design-appendix.md` l.32 now reads "Rules every figure follows". `worked-portfolios.md` l.609 now points to §1.1, and l.622 says "The manifest's rev 4" |
| **L10** untagged cooling figure | **Fixed** | l.290 is tagged, and the checks went from 3,757 to 3,758. The O2 regex (`check_manifest.py:522`) was not widened. That was optional, and the figure is now covered by its marker |
| **L11** jargon | **Fixed** | Glossary at l.66-76 covers every term B listed |
| **L12** arguing statements | **Fixed** | "Why it should convert" is now worded as a hypothesis (l.191, l.251, l.303, l.392). "No monitoring tool can answer that" and "The contrast sells" are gone. The approved Introduction (l.46) is unchanged, as it should be |
| **I2** HUMAN-actor pattern | **Applied, verified** | `0010_financial_assumptions.py:57-78`: `actor_kind`, `author_id`, `channel`, and the constraint at l.76-78. `financial_api.py:209`: `HUMAN_PRINCIPAL_REQUIRED` |
| **I3** Figure 4 subgraph order | **Fixed** | `subgraph AD` is declared at l.357, before `EM --> AD` (l.360) |
| I1, I4 | n/a | I1 was information only. I4 is taken up in §5 |

### Newly cited code: all confirmed

| Citation | What it shows |
|---|---|
| `0051_action_opportunity_origin.py:1-12` | The `domain_action` table admits MINI and gains `origin_opportunity_id`, with exactly one origin pair. The `action` table is untouched |
| `mini_decisions/projection.py:29` | `STUDY_DAYS = 5`, supporting the "five-day headroom study" |
| `mini_decisions/opportunities.py:366-401` | The read sets `"demand_state": "UNVERIFIED", "collection_state": "UNVERIFIED"` (l.400-401) |
| `0010_financial_assumptions.py:57-78` | As in I2 above |
| `financial_api.py:209` | `HUMAN_PRINCIPAL_REQUIRED` |
| `outcomes/credit.py:57-73` | `credited()`: VERIFIED and MODELLED_IMPROVEMENT and a priced total |
| `outcomes/status.py:55-104` | Objective verdicts drive the state |

Also spot-checked and confirmed:
- `actions/verification_families.py:12-22`: the midday-shift family is the plan of the MINI domain action raised from an opportunity.
- `0042_chain_threads.py:64-71`.
- `chain/lifecycle.py:46-58`.
- `work/model.py:284-285`.
- `work/domain_intent.py:17`.
- `analytics/claim_limit_read.py:1-19`.
- `estate/placement.py:1-8`.

---

## 2. New findings

### N1 · Medium · `worked-portfolios.md` l.13, l.178, l.246, l.423, l.574 (sweep: `design-appendix.md` l.33)

Quoted:
- l.13: "**Choose**: the system searches all the options together and proposes a plan under the budget, the crew visits and each decision's rules; the operator executive approves it, and the site manager owns each Action".
- l.246: "one search over all the decisions together … It tries every combination that takes one option per decision … The proposed plan is the combination that breaks the rules least, then is worth most, then spends least."
- l.178: "the search … so it takes the repair".
- l.574: "Once the executive approves the plan, the site manager raises the Actions in this order".

**Problem.** The main document's mechanism is now:

> the manager chooses → creates Actions → the system checks the chosen set and, only if it does not fit, shows fitting alternatives → the executive approves, which releases spend

The companion still runs rev 16's mechanism. The system searches every option of every decision, the executive approves what it picked, and the manager's choice is never an input. That is exactly the "two choosers" review B named in M1. Its own header (l.6) claims "the site manager chooses within each decision", but its body never shows that.

l.574 also puts Action creation *after* plan approval. The main document's table (l.432: "Created by the manager → released by the plan") and Figure 7b (l.541 before l.544) put it before.

`design-appendix.md` l.33 ("what intervention can be undertaken | … the proposed plan, approved by a named person") omits the manager's choice and Actions. This is minor, but it is part of the same sweep.

**Why it matters.** The owner asked for the design to be checked so that the system never chooses. The brief for this re-review requires consistency in every companion. A reader of the worked examples, and a builder of slices 6 and 7, would still see one selection point owned by the system. B's residual risk ("two choosers") stays open.

**Fix.** Wording only. No figure changes, since the search still serves as the "nearest fitting combinations" proposal.
- l.13 and l.246 (and l.423 and l.574 by reference): "Each site manager chooses within each decision (the demo assumes they take the Recommended option). The system checks that chosen set against the budget, crews and dates. Where it does not fit, it proposes the nearest fitting combination, ranked by …. The executive approves or sends back."
- l.178: replace "it takes the repair" with "it proposes the repair".
- l.574: "the site managers have raised the Actions; once the executive approves the plan, they are released in this order".
- `design-appendix.md` l.33: "the Actions the manager creates, released by the plan the executive approves".

### N2 · Low · `layer4-transformation-design.md` l.414 and the Figure 7 caption l.551

Quoted:
- l.414: "Actions that spend neither (a remote setting change, an investigation) go ahead without it."
- l.551: "The stop-threshold change needs no crew visit, so its Actions would also proceed without the plan."

**Problem.** Kobo's stop-threshold change is remote, but it spends 90.00 (vendor reconfiguration 60.00 plus supervision 30.00: `worked-portfolios.md` l.150). It is a line of the Lakeside plan (l.252, and the main document's l.419). Under step 4's own rule ("budget or crew visits") it *does* enter the plan. The caption's reasoning (no crew visit, so no plan) contradicts step 4. The example "a remote setting change" suggests remote means free. This was introduced in the fix round.

**Fix.**
- Caption: replace the last two sentences with "Its 90.00 one-off is budget, so the plan's approval releases it."
- l.414: use "a zero-cost setting change" in place of "a remote setting change".

### N3 · Low · §2.4 l.413, §2.8 l.611, Figure 5 l.405, Figure 6 l.489 against the roles table l.467-468 and l.266

**Problem.** The fix makes "the site or operations manager" the only creator of Actions. The roles table, however:
- gives the finance and commercial lead "decides to file a claim or notice; acts on collection";
- gives the executive "approves capital choices (replace or repair, new capacity)".

§2.1 raises Kobo's collection Finding "for the commercial lead". So for a money or rights Finding, who chooses and who creates the Action is left ambiguous.

Separately, the executive's cross-Site trade-off (l.436: "Only the budget holder can") may drop an option a manager has already turned into Actions. The Action's life (l.432) does not say what becomes of such an Action: is it not released, sent back, or withdrawn?

The owner's words say "the user", not one role. Nothing here breaks "the system never acts".

**Fix.**
- Say "the accountable role (the site manager for operations; the finance and commercial lead for collection and rights)" creates the Actions.
- Add "not released; returned to its creator" to the Action's life for an Action the approved plan leaves out.

### N4 · Low · §1.4 l.145 and l.155

Quoted:
- "Site manager | … | Raises the mill-shift domain action from the study"
- "the site manager can raise the mill-shift domain action from it"

**Problem.** Today this path has the same G1 limits as the row above:
- the domain write needs a server service principal, and a user actor is refused (`work/model.py:284-287`);
- there is no UI control;
- the mill plan is frozen "once, at story time … no HTTP route" (`actions/verification_families.py:7-9`).

The row above states those limits; this row does not. It slightly overstates today's act path in the section that the audit's class C3 is about.

**Fix.** Add "(same recording as the row above: a service principal, no UI control yet)" to the recording cell.

### I1 · Info · review tags and list formatting in reader-facing text

- The tags "(L11)" (l.66) and "(M1; …)" (l.410), and the l.5 rev-16.1 note, are review bookkeeping in a founder-facing document. They belong in the change log.
- l.264-268: the nested Kobo list was flattened, and each item now repeats "*Kobo:*" under a "Kobo, October" lead-in. That is cosmetic.

### I2 · Info · citation two lines off (carried over, not a regression)

`objectives/model.py:17-22` (l.178, l.305, l.607) is cited for "for the demonstration; not a customer target". That text is at l.23-24. Review B cited `:21-24`.

The audit (not under review) cites `outcomes/status.py:55-113` for "never combined into a score"; that phrase is at l.5-6.

### I3 · Info · the O2 percentage regex is unchanged

`check_manifest.py:522` still matches only two decimals. This is harmless now that 99.997% is tagged. A future untagged three-decimal percentage would still pass silently.

---

## 3. Mermaid (linted, not parsed)

The three files hold **10 blocks**, all in `layer4-transformation-design.md`; `worked-portfolios.md` and `design-appendix.md` have none. Each block was read against the Mermaid 10.9.1 grammar, the version the HTML loads (`mermaid@10.9.1`, confirmed in the `.html`). **They were linted by reading only and not parsed**: no packages could be installed, and no browser render was done.

| Hazard | Result |
|---|---|
| `;` or `#` in sequence messages (Figures 7a, 7b) | None |
| `;` in flowchart labels | Only inside double-quoted labels (Figures 2, 8, 9), which the string state consumes |
| `#` outside `classDef` | None |
| Unquoted special characters in flowchart labels | None. Every label containing `(`, `)`, `:`, `&`, `%`, `→`, `≥` or `−` is double-quoted. The bare `&` at l.405 (`V1 & V2 & V0 --> P`) is valid multi-node syntax |
| Subgraph used before declaration | None. Figure 4 now declares `AD` first. Figure 1's subgraphs are not edge endpoints |
| `end` as a node id | None. `end` appears only as the subgraph terminator |
| Unbalanced brackets or parentheses inside labels | None. Shapes `[" "]`, `(" ")`, `(( ))`, `([ ])`, `[( )]` and `{{ }}` are balanced |
| Other | Forward references to nodes (Figure 9 `S2 --> S6`) are legal. `classDef` after use is legal. `actor X as …` and self-messages `S->>S:` are legal |

---

## 4. Mechanics re-run (from the pack folder)

```
$ python3 check_manifest.py
3758 checks passed, 0 failed
$ python3 motivation_figures.py --check
2 figures built; markers ['factor-structure', 'plan-against-actual']; missing []; unused []
$ python3 render_design_html.py layer4-transformation-design.md <scratchpad>/r.html && cmp <scratchpad>/r.html layer4-transformation-design.html
ok …  /  IDENTICAL
```

The working tree was clean for the pack folder before this file was added.

## 5. Proportion: trimming advice (not blocking)

The main document is about 10,000 words, counting the inline markers; Parts 1–2 are about 8,100. The owner asked for a short, intentional document of about 12 pages. These passages could move or be cut without losing a core topic, which would save about 2,000–2,500 words:

1. **Header block (l.3-25).** Move the rev 16 / 16.1 history, the five audit classes and "Labels" to a change log in `design-appendix.md`, and keep two lines. Save about 250 words.
2. **Introduction, D1 revision (l.48-55).** It belongs in the roadmap. Keep one sentence pointing there. Save about 100 words.
3. **§2.1 three-vertical table (l.283-294).** This is the largest single block of detail. Keep one sentence ("the same shape for cold rooms and EV depots; revenue not applicable for a captive fleet") and move the table to `worked-portfolios.md` §1. Save about 350 words. The broader-business view stays in §1.5 and the roles.
4. **§2.1 "Where this changes rev 15" (l.269).** This is revision history, not design. Cut it. Save about 70 words.
5. **§2.3 "Minimum pilot asks per vertical" (l.372-375).** Move to `integration-source-to-canonical-design.md`. The source table already gives the scope. Save about 80 words.
6. **§2.4 plan-versus-Action prose (l.436-444).** "Why owned by the executive", "Why it is necessary" and "Where it does not earn a separate step" restate the table. Keep the table plus one paragraph covering ownership, merit and the thin record. Save about 300 words. Also move the Lakeside proposal bullet (l.419) to the companion.
7. **§2.5 roles table versus Figure 6.** Both carry the same content. The owner asked for use-case diagrams, so keep Figure 6. Cut the table's "Sees" column, and fold "Recorded" into one sentence. Save about 250 words.
8. **§2.0 table, the per-section "What stays / what changes / merit" paragraphs, and §2.8 register.** The change-and-merit statement appears twice. Keep the register as the single home, and make each section's merit a one-line pointer. Alternatively, shorten the §2.8 opportunity row (about 120 words) to two sentences. Save about 300–400 words.
9. **§1.5 against §1.6 L2/L4.** These overlap on "not held". §1.5's table could absorb L2 and L4's "why it matters" in one column. Save about 150 words.
10. **Figure 3's caption bullets (l.317-323).** These repeat the drawn bridge. Keep the total and one line. Save about 60 words.

Keep: §1.3 (the Finding definition and Q-A1), §1.4, §2.4 steps 1–4, Figures 1, 5, 6 and 7, and the glossary. These carry the owner's central concerns.

## 6. Could not verify

- **The Mermaid blocks were linted but not parsed or rendered** (see §3).
- **The HTML was not viewed in a browser.** Narrow-width legibility of the drawn Figures 2 and 3 was not checked by eye.
- **No suites, databases, Docker or ports were used**, per the brief.

## 7. Residual risk the pack does not name

- **Two choosers, still.** N1 keeps the "system selects one option per decision" mechanism alive in the companion that holds every worked figure. If slices 6 and 7 are specified from the companion, the build reintroduces it.
- **Release gate by cost.** Without N2's correction, a builder could gate plan entry on crew visits or on "remote", not on spend. Small paid changes would then bypass the budget holder.
