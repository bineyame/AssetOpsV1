# S4-02a registry closeout: fresh Claude review

Reviewer: fresh Claude. I did not author S4-02a, its reviews or this closeout. Branch `closeout/S4-02a-registry`, commit `6392b86`, diff `2592c82..6392b86`. The diff is metadata only: the registry JSON, the screen ledger, `.agent/S4-02a-closeout-packet.md` and `.agent/next-work-2026-10-14a.json`. No product code, test or catalogue mirror changed. I judged it against `.agent/S4-02a-registry-closeout-brief.md`, the S4-02a reviews, the owner's conditional acceptance and the S4-03 closeout precedent.

## Verdict: ACCEPT with carries

All five resolved nodes are backed by accepted reviews and by the owner's conditional acceptance. Every cited evidence file exists and is tracked, and every commit is an ancestor of HEAD. The code anchors point at the named functions. Nothing on the S4-02b path was resolved or promoted. Both gaps stay open, and the ledger edits are honest. I found no blocking problem. There is one Low finding to carry, on the wording of the Foundation gap trigger, and three Info notes.

## Node-by-node check

| Node | Acceptance target | Accepted by | Result |
|---|---|---|---|
| `I-financial-assumption-store` | Immutable revisions, SYSTEM publication, validity closure, exact retry | `S4-02a-phase-1-review.md` (ACCEPT with carries; M1/M2 fixed as the first phase-2 commit `408e9e6`, re-checked as C1 in `S4-02a-review.md`) | OK |
| `D-financial-assumption-basis` | v1, future v2, partial backdated correction, exact actor and times, no-price case | Phase 1 review (fixture), `S4-02a-review.md` C1 (v2 in 2030) and the empty-store probe; L3 source wording in `S4-02a-fix-rereview.md` | OK |
| `I-assumption-history-read` | Exact current and prior revisions, valid/recorded selection, pagination | `S4-02a-review.md` focus 2 (half-open on both axes, exact-ID stability, pagination); L1 next-page fix verified non-vacuous in the re-review | OK |
| `I-assumption-history-ui` | Compares current and prior price with SYSTEM actor/basis and disabled human edit | `S4-02a-review.md` focus 4 and 69/69 browser evidence; owner walked steps 1-8 | OK |
| `I-S4-02a` | SYSTEM publication, exact history, honest Finding bridge, reviewed Foundation link | All of the above; the review's focus 3 (bridge) and focus 4 (link targets `/sites/{site}/financials/assumptions`, gap stays open). Task :28 allows "link ... or gap remains open with corrected review trigger". The review note's "name M1 as fixed" is met in the evidence string. | OK |

The 69/69 claim is the review's own rerun (`S4-02a-review.md:36`, `:100`), made before the fix round. The fix round touched only `tools/layout-evidence.mjs` predicates, the fixture source text, heading copy and `urlencode`, not the s402a evidence tool's claims. The re-review records layout evidence as not rerun, honestly. So citing 69/69 is accurate.

The closeout applied all of the review's "Registry closeout notes" (`S4-02a-review.md:192-200`). `G-assumptions-human-edit` has `reviewed_by` and `visual` set. Both screenshot files exist under `%LOCALAPPDATA%/AssetOps/evidence/s402a/`, and the evidence tool writes them (`tools/s402a-assumptions-evidence.mjs:191`). `G-foundation-financial-assumptions` stays open. No W1 panel was promoted.

**Not touched (verified with a word diff of the whole registry):** `I-S4-02b`, `I-S4-02`, `I-financial-store`, `I-financial-read`, `I-financial-ui`, `I-consequence-history-read` and `D-financial-basis` are all still `open`. No panel or portion changed state, and the scoring parameters are unchanged.

**Anchors:** I opened each line. All of these resolve to the named symbol:
- `financial_read_api.py:64`, `:88`
- `assumption_read.py` `series:63`, `revision:100`
- `assumptions.py` `validate:92`, `plan_assignments:189`
- `postgres_assumption_store.py` `publish:99`
- `publish_assumption.py` `main:104`
- `SiteFinancials.tsx` `DisabledEdit:148`, `SiteAssumptions:179`, `CurrentPrice:237`, `Schedule:268`, `History:321`, `ExactVersion:381`, `FindingBridge:457`
- `StoredFoundationViews.tsx:469` (`data-financial-assumptions-link`)

The two labels in Info I2 are loose.

## Findings

### Low

**L1. The `G-foundation-financial-assumptions` `review_trigger` adds a closure condition that no source asked for, and names a different acceptor** (`v69-dependency-registry-pilot.json`, `mock_gaps.gaps[G-foundation-financial-assumptions].review_trigger`).

- **What is wrong.** The new trigger closes the gap only when:
  - (a) "a reviewer accepts the line as replaced by the price value or an accepted link treatment", **and**
  - (b) "the wider financial-assumption set (costs, other prices) has a reviewed source or is declared out of scope".
- Condition (b) appears in none of the sources:
  - Task `S4-02a-site-assumptions.md:28` says the gap stays open "until that link is independently accepted".
  - The phase-2 handoff (`S4-02a-phase-2-handoff.md:48-50`) says it "resolves when that link is independently accepted".
  - The review note (`S4-02a-review.md:197-198`) says "Resolve it only after the owner accepts the link".
- The trigger also says "a reviewer" accepts, where the review note says the owner.
- **Why it matters.** Condition (b) is defensible on honesty grounds, because the gap's `claim` is "prices and costs" and the link shows only the diesel price. Even so, it is a scope decision on when a gap closes. A Sonnet metadata closeout should not introduce one silently. It could hold the gap open after the owner accepts the link, contrary to the task's stated closure rule.
- **Fix.** Either route (b) to the Architect as a batched question, or reword it so that it follows the task:
  - the gap closes when the owner (or an independent reviewer) accepts the link treatment for this line;
  - if that acceptance covers only the diesel price, the wider set (costs, other prices) is split into its own gap or declared out of scope at that point.
- This is metadata only and does not block the merge, so carry it.

### Info

**I1. The gap's `boundary.source` now reads stale next to its new `evidence.source`.**
- `boundary.source` still says "no reviewed Site Financials assumptions read or route exists here".
- `evidence.source` now names `financial_read_api.py:64` as the reviewed Site assumptions read.
- "here" can be read as "on Foundation", which is still true, but the two sentences sit awkwardly together. Consider tightening the wording when L1 is handled. This is a preference, not an acceptance gap.

**I2. Two anchor labels are loose.**
- `I-assumption-history-read` cites "`financial_read_api.py` ... `:88` (api_next_page via urlencode)". Line 88 is the exact-revision GET route. The `urlencode` next-page link is at `:82-85`, as `S4-02a-fix-rereview.md` says.
- `I-S4-02a` cites "`financial_api.py:56-59` (SYSTEM-only publish route, human principal refused)". Lines 56-59 are the router and route declaration. The human-principal refusal is at `:83-86`.
- Both point at real, relevant code. Correct them the next time the nodes are touched.

**I3. The ledger task string uses a new form** (see Q3 below).

## Answers to the packet's questions

1. **`assumptions:1#a` should stay `open`.**
   - Its `mapping_target` names an "S4-02 reviewer" and `D-financial-basis`.
   - Its `technical_requires` include `I-S4-02`, `I-financial-read`, `I-financial-ui`, `I-financial-store` and `D-financial-basis`, all of which are open.
   - The review note says "No W1 panel promotion", and the owner said nothing becomes Real and the panels stay partial.
   - Delivering it now would contradict its own mapping. The S4-03 precedent delivered portions only when the slice owned their whole mapping.
   - `assumptions:3#a` (assumption *and consequence* revisions) clearly needs S4-02b. The closeout is right on both.
2. **The `G-foundation-financial-assumptions` trigger is half right.**
   - The first half (a reviewer or the owner accepts the line as replaced, or the link treatment as accepted) matches the task and the review.
   - The second half (the wider-set source or an out-of-scope declaration) is new; see L1.
   - The acceptor should be the owner, per the review note, or "owner or independent reviewer", per the task.
3. **The `S4-02a (S4-02b pending)` task string is acceptable, but it is not the established form.**
   - The validator (`check_v69_ledger.py:116-117`) only requires a non-empty `task` on a bounded row, so any form passes.
   - The ledger convention is routing by plus-joined tasks, including unbuilt ones. For example, `finding` reads "S4-01 + S4-02" although S4-02 is not built.
   - The previous value, "S4-02a + S4-02b (S4-02 closeout)", followed that convention. It also named the S4-02 closeout that owns the panel promotion, and the new string drops that.
   - Preference: use "S4-02a + S4-02b (S4-02 closeout)" or "S4-02a + S4-02b (S4-02b pending; S4-02 closeout)". This is not an acceptance gap.

## Ledger edits

- `assumptions`:
  - The supported claim is bounded to the Site diesel price history. It names the consequence revisions as S4-02b.
  - The `unknown_or_empty` text says the conditional acceptance is not Real, and it lists the remaining G-05 gaps.
  - The `gap_ids` addition matches the placement `assumptions.price.human-edit`.
- `financials`:
  - The supported claim is unchanged ("only after S4-02b review").
  - The caveat states that only the bridge and the Site price are delivered.
- `foundation` is correctly unchanged: the gap id is already listed, and the caveat does not mention financial assumptions.
- None of these edits overclaims.

## Checks I ran (as observed)

- `node frontend/docs/architecture/check_v69_dependency_registry.cjs`: exit 0, "Registry valid: 217 nodes, 11 linked pilot panels".
- `.venv/Scripts/python.exe frontend/docs/architecture/check_v69_ledger.py`: exit 0, "v6.9 ledger valid: 110 screens, 88 distinct models, 258 panels".
- `powershell -NoProfile -ExecutionPolicy Bypass -File tools/check-all.ps1`: **All 9 guards passed**. The orphan scan reports 31 tagged / 12 baselined, compared with merge-base `2592c82`.
- `check_v69_dependency_registry.cjs --verify-report .agent/next-work-2026-10-14a.json`: exit 0. The decision line matches the packet verbatim:
  - top `I-financial-store` 2.229, second `A-S5-overview` 2.148, gap 0.036 (3.63%), `stop_owner`, tie-break recommends `A-S5-overview`.
- **Regenerated `--next-work` into scratch.** Every top-level key equals the committed report (schema, wave, k, fingerprints, authority, unscored_work, gap_catalogue, status, global_stops, decision, eligible, candidates).
- **Compared with the previous ranked report `.agent/next-work-2026-10-13n.json`, candidate by candidate:**
  - The five S4-02a nodes leave the list.
  - Downstream money and overview candidates rise, because their paths lost those open nodes: `I-financial-store` 2.182 to 2.229, now unblocked; `A-S5-overview` 2.134 to 2.148; `D-financial-basis` 2.382 to 2.429, still blocked by `I-financial-store`.
  - Every other score and blocked flag is unchanged.
  - The change is explained by this closeout alone.
- **Evidence and commits.** Every cited `.agent`/`tasks`/test path exists and is tracked. Commits `28668d9`, `49bedd8`, `408e9e6`, `293b412`, `07a9685`, `59c2b56`, `17ae9e2`, `778875d` and `2592c82` are all ancestors of HEAD. The decision `D-2026-10-13-s4-bounded-financial-basis` is at `.ai/DECISIONS.md:4101`.
- **Working tree.** The uncommitted changes in the three checker/catalogue files and the task files are CRLF-only: `git diff --ignore-cr-at-eol` is empty. They were correctly left out of the commit.

**Not run, by instruction or because no code changed:** the backend pytest, frontend vitest, the build, `tsc` and the browser and layout evidence. I did not recompute the scoring formula by hand. I relied on regenerating the report, on `--verify-report` and on the comparison with 13n.

## Residual risk

- The Foundation gap's closure rule now differs between the task (link acceptance) and the registry (link acceptance plus the wider set). Whoever next walks the Foundation line could read either one. L1 resolves this.
- The owner's minor carry (version 1 shown in two places) and the 390 px tab wrap are recorded only in the owner file, the task and the ledger caveat. Neither has a registry node or gap, which matches the S4-03 precedent for owner UX carries.
