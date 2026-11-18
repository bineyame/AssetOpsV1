# S4-02 planning packets: fresh Claude review

Reviewer: fresh Claude reviewer. I did not author the packets; the Codex Planner did. Date 2026-10-13.
Branch `plan/S4-02-refine`, diff `2c87037..5421c04` (`4b50e2d` owner choice + brief, `be68acc` Planner output, `5421c04` next-work report).
Scope: `tasks/S4-02a-site-assumptions.md` (40 lines), `tasks/S4-02b-fuel-consequence.md` (42), `tasks/S4-02-bounded-financials.md` (12, closeout pointer), `tasks/README.md` S4 rows, the registry and ledger edits, `.agent/planner-S4-02-questions-2026-10-13.md` (Q1) and `.agent/next-work-2026-10-13l.json`. Judged against `D-2026-10-13-s4-bounded-financial-basis`, `.agent/architect-A-S4-financial-answers.md`, `.agent/A-S4-financial-review.md` (carries M1, M2, L1-L7), `.ai/WORKFLOW.md` and the built code.

## Verdict: ACCEPT with carries to apply before activation

The split, the registry and ledger edits, and the next-work regeneration are sound. Every review carry is resolved or properly deferred. The SYSTEM CLI and actor handling match `A-actor-identity`. Q1 is well posed and its fail-closed default is correct.

Before S4-02a activates, the Planner should apply C1, C2, C3 and C6. Before S4-02b activates, it should apply C4 and C5. Each is a text edit to a packet or to Q1, and C4 is best folded into the pending Q1 call. No finding needs an owner decision. The only Architect input needed is Q1 as amended by C4. An implementer could start S4-02a phase 1 today. Without C1 and C2, though, the core of M1 (when an overlapping publication splits prior validity and when it is refused) would be decided inside the migration rather than by the plan.

## Checks run (by me)

- `node frontend/docs/architecture/check_v69_dependency_registry.cjs`: exit 0. "Registry valid: 217 nodes, 11 linked pilot panels" (212 before; +5 new nodes).
- `python frontend/docs/architecture/check_v69_ledger.py`: exit 0. "v6.9 ledger valid: 110 screens, 88 distinct models, 258 panels".
- `--next-work --json --out <scratch>/nw.json`: exit 0. Decision `stop_owner`: I-financial-assumption-store 2.182 vs A-S5-overview 2.134, gap 2.20%, tie-break recommends A-S5-overview.
- `--verify-report .agent/next-work-2026-10-13l.json`: exit 0. `--verify-report <scratch>/nw.json`: exit 0.
- The fresh scratch report equals the committed `-13l` on every top-level key.
- I did not run check-all or the product suites. The coordinator ran check-all 9/9 on `be68acc`, and no product code changed.

## Anchor spot-checks (exist; described correctly unless noted)

- `finding_api.py`: `development_access` returns None, which admits the request. The 401/403/404/503 refusals are at :60-97, and `ACCESS_BASIS` (:38) records that no human principal exists. The child routes at :109/:163/:187 are as cited. There is also a 409 `PERFORMANCE_CUTOVER_CLOSED` gate, which S4-02a item 4 and S4-02b's "closed-source" state correctly inherit.
- `sites/models.py:113`: `specific-fuel-consumption` is `L/kWh`, `PHYSICAL`.
- `analytics/dispatch.py:49`: `SFC_UNCERTAINTY = Fraction(1, 10)`; :730-731 is the legacy low/high.
- `analytics/dispatch_v3.py:478`: fuel and money are withheld. `GEN_POWER` (:49) is in the assessment worker's `DISPATCH_ROLES` (`assessment_worker.py:53`), so generator-power means are part of the pinned input set, as S4-02b item 1 assumes.
- Technical design rows :53-54 and the DTO at :165 are as S4-02b line 14 describes. The divergence is stated (carry L1).
- `btree_gist` and the GiST current-valid exclusion pattern exist: migration 0001 :169-172 and 0002 (set-once `superseded_at` trigger).
- Frontend: `SiteFinding.tsx`, `findingClient.ts`, `SiteAnalyticsFrames.tsx` and `operatorSiteRoutes.ts` exist. No Financials or Assumptions route exists yet. The packet omits the real Site tab anchor (see C6).
- `tools/check-all.ps1`, `tools/layout-evidence.mjs` and `tools/s4_finding_walkthrough.py` exist. Mock routes `#/financials` and `#/assumptions` exist. Manifest `financials` is "Subtabs Overview | Assumptions; Scenarios is a placeholder".
- Size: 1106 and 1331 words, against S4-03's 1583. Both are far under the 220-line ceiling. They are dense but complete. The defects are the specific ambiguities below, not missing sections.

## Carry resolution (A-S4-financial review)

| Carry | Where | Status |
|---|---|---|
| M1 validity closure vs correction; STALE | S4-02a:18, S4-02b:20 | Resolved by the assignment table; two implementability gaps (C1, C2) |
| M2 upper-bound source; power/duration | S4-02b:19, Q1 | Source named (model parameter, Q1). The formula is not a valid bound in one case, and its duration term is undefined (C4) |
| L1 migration shape vs technical design | S4-02b:14, :24 | Resolved |
| L2 node mapping, I-S4-02 effort, README | registry, README:28-30, S4-02:12 | Resolved (see the note on I-S4-02 effort) |
| L3 SYSTEM trigger, disabled edit | S4-02a:12, :19 | Resolved; route refusal detail (C7) |
| L4 Foundation gap | S4-02a:26, S4-02:12 | Resolved |
| L5 visible missing states / G-05 | S4-02a:27, S4-02b:31 | Resolved per the G-01 boundary; disabled-edit copy inconsistency (C8) |
| L6 no "Scenario" wording | S4-02b:31 | Resolved: unavailable is chosen |
| L7 `data_source` audit | S4-02a:27, S4-02:10 | Properly deferred to G-03..G-05 / W1 exit |
| Answers L29 list | both packets | Covered |

## Findings / carries

### Medium

**C1. Publication semantics are ambiguous: when does an overlapping price split prior validity, and when is it refused?** (S4-02a:19 together with :18)
Line 19 says the publication transaction "rejects ... overlapping current validity". Line 18 requires that a future price `v2` (authored `[t,∞)`, overlapping `v1`'s current `[t0,∞)` assignment) close `v1` at `t`. It also requires that a middle-only correction `v3` overlap `v1` and split it. Every fixture in phase 1 is therefore an overlapping publication. The decision (DECISIONS.md:4101) also forbids an "unlabelled retroactive edit", but the packet defines no label that tells a correction apart from an ordinary change.
Why it matters: these are the semantics of M1. An implementer either refuses the fixtures or invents a rule, and the reviewer has nothing to judge the rule against.
Fix: in item 2, add an explicit publication `change_kind` that is stored on the revision and shown in History:
- `SUCCESSION`: `valid_from` ≥ the server `recorded_at`. It may only truncate the single open-ended current assignment that contains `valid_from`. Any other overlap is refused with a typed 409.
- `CORRECTION`: backdated or bounded. It requires a reason. It supersedes the current assignments over its authored range and re-assigns the uncovered left and right remainders to their same old revisions.

Reword "rejects overlapping current validity" to: after the transaction, no two current assignments overlap (enforced by C2's constraint), and an overlap that `change_kind` does not permit is refused. Add one negative test per kind.

**C2. Assignment-table constraint shape: "append-only" conflicts with an exclusion "current at a recorded cutoff".** (S4-02a:18)
A Postgres EXCLUDE constraint can only see columns on the row. For it to hold at every recorded cutoff, `recorded_to` must be a column on the assignment row, set once when the assignment is superseded. That is the existing `superseded_at` precedent (0001 :169-172 with its set-once trigger; 0002 :155-197). Separate append-only "closure rows" cannot be covered by a declarative exclusion; that would need a trigger or application check.
The design itself is coherent. I traced v1, then future v2 at `t`, then middle correction v3 at recorded `r2`. The current assignments come out as v1 `[t0,a)`, v3 `[a,b)`, v1 `[b,t)` and v2 `[t,∞)`. Their recorded ranges do not overlap with the superseded rows, a window inside `[t0,a)` still selects v1's ID, and the pinned consequence is not STALE. It is testable.
Fix: specify "assignment rows are immutable except a set-once `recorded_to` (trigger-enforced, as in `foundation_revision`). `EXCLUDE USING gist (tenant_id WITH =, site_id WITH =, assumption_key WITH =, tstzrange(valid_from,valid_to,'[)') WITH &&, tstzrange(recorded_from,recorded_to,'[)') WITH &&)`". Superseded and new rows share the same instant (`recorded_to` = `recorded_from` = the transaction's server time). Also add a check that every current assignment's valid range lies inside its revision's authored range.

**C3. S4-02a should carry `USER_REVIEW_REQUIRED: true`, and the default reading should keep IDs, digests and model names out of the client view.** (S4-02a:4, :25; S4-02b:19, :31)
S4-02a flips a new Site tab (Financials) from `capability: false` (`operatorSiteTabs.tsx:82`) and adds the Assumptions current/history surface, the disabled-edit copy and the bridge states. That meets every criterion in `.ai/WORKFLOW.md:212-214` (UI/UX, information hierarchy, demo narrative). S4 is also a named checkpoint milestone (WORKFLOW:208). Every prior S slice with visible UI took an owner checkpoint (S3-01, S4-01, S4-03, G-01, G-02).
The owner's standing presentation direction (`.agent/owner-T028-presentation-direction-2026-10-04.md`) also applies. Product screens use plain words by default. IDs, digests and model versions belong in a deeper view. S4-02a:25 puts "exact selected/prior IDs" on the Assumptions page. S4-02b:19 and :31 mandate the visible phrase "under the fuel-cost-1 model bound" and `MODELLED_CONDITIONAL` wording. WORKFLOW "Avoiding Spec Chaff" advises against exact wording the user has not reviewed. S4-02b is built on the S4-02a surface, so owner feedback that arrives only after S4-02b risks rework of both.
Fix:
- Set S4-02a `USER_REVIEW_REQUIRED: true` with a short walkthrough of the Assumptions page, the disabled edit and the bridge. Keep the S4-02 owner checkpoint on S4-02b.
- In both packets, state that exact IDs, digests, formula version and enum names appear in a lineage/details disclosure or the History view. The default reading uses plain language, for example "modelled estimate, not a measured saving". The final wording goes to the owner checkpoint rather than being fixed in the packet.

**C4. The `fuel-cost-1` upper bound is not a bound when a power interval straddles a segment edge, and `T_i,high` is undefined.** (S4-02b:19; Q1)
- In `dispatch-3.1` a Candidate segment has only `[start,end)` (`dispatch_v3.py:105-125`). `lower_minutes`, `upper_minutes` and `OPEN_BOUND` are interval-level, from `off_before`/`off_after` (:443-462). A "segment's supported upper duration" does not exist. An implementer could reach for the interval's `upper_minutes`, which includes unassessed edge time the packet forbids.
- Segment cuts come from generator-state report times, power-interval ends and control changes (:382-383, :340-347). One accepted power mean can therefore cover several segments, or extend past a Candidate segment into Necessary or Indeterminate time. Within the part of that interval inside the segment, power can exceed the interval's mean. `max mean × segment duration` is then not an upper bound on generator energy, even before the 1.10 multiplier. "Never extend a mean beyond its recorded interval" guards the opposite direction only.

Why it matters: the UI calls this a bound, and the owner and W1 `financials:1#a` acceptance depend on it being one.
Fix: put both points in Q1 (one Architect call, so no new question), and give the packet a fail-closed default:
- `T_i` = `end − start` of each stored `CANDIDATE` segment with `observed: true`. Never use interval `upper_minutes`.
- A segment is quantifiable only if each covering good generator-power interval lies wholly inside contiguous Candidate time. Otherwise the whole consequence is `QUANTITY_UNAVAILABLE`.
- Optionally offer the Architect a less restrictive valid bound: Σ over distinct covering intervals of `mean_j × |interval_j|` (valid because power ≥ 0). It counts each interval once, which also settles the "overlapping segments counted twice" rule.
- Add a straddling-interval fixture to the unavailable cases.

### Low

**C5. Define the consequence window used for `PRICE_SPANS_WINDOW`, and say when S4-02b may activate without a Q1 answer.** (S4-02b:3, :20)
"Consequence window" could mean the FindingRevision `window_start/end` or the span of the candidate segments. The two give different `UNPRICED` results when a price boundary falls in non-candidate time.
Fix: name the FindingRevision window, which is conservative and matches the decision's "whole assessed consequence window". Also add to the status line that activation requires either Q1 answered, or a coordinator record that the fail-closed build is accepted knowing that `financials:1#a` cannot close. The reason: without Q1 the owner checkpoint would show no bounded amount at all. Separately, reword "crossing-window cases remain unpriced" (:20) to "a correction that makes a previously priced window cross a price boundary appends an `UNPRICED` consequence revision". Otherwise the sentence reads as if only already-unpriced rows qualify.

**C6. Name the Site tab and route shape.** (S4-02a:14, :25)
The real anchor is `frontend/src/shell/operatorSiteTabs.tsx:82` (`Financials`, `capability: false`, `notYetRouted`). The packet does not name it, or the URL shape that carries the reload/back contract.
Fix: one clause, for example "flip the Financials tab in `operatorSiteTabs.tsx`; routes `/sites/{site}/financials` (Overview) and `/financials/assumptions?revision_id=&recorded_at=`; the Finding bridge carries `finding_id` and `revision_id` in the query". Say also that the mock's Scenarios subtab is omitted and itemized for G-05, not rendered as an empty tab.

**C7. The human write route has no defined success path.** (S4-02a:19)
"Leave it unavailable until actual human auth exists" while also testing 403 for an "unauthorized known Site" only works through an injected `access` seam, like `build_finding_router(access=...)`. The packet does not say what an admitted request does, or which status refuses client-asserted identity.
Fix: "S4-02a builds the write route with no success path. The default access returns 401. Tests inject 403 and 404. Any body actor or author field is refused with 422 before scope. An admitted request with no verified human principal returns 401. It must not use `development_access`."

**C8. The required disabled-edit copy contradicts the packet's own absent-capability rule.** (S4-02a:12, :27)
"Unavailable: no authenticated operator" is absent-capability copy on an unenrolled screen, yet line 27 requires such copy to be a catalogued `<MissingClaim>` or omitted. It does not match the scan PATTERNS, so the guard passes, which line 27 says must not be what makes it acceptable.
Fix: either catalogue it (for example `G-assumptions-human-edit`, `missing_kind: build` or `contract` per the first-absent-authority rule, owner `A-actor-identity`/auth slice) with its placement mirror, or state explicitly that it is the decision-mandated `A-actor-identity` disabled state and not a mock gap. The first follows the owner's rule more closely.

**C9 (optional). S4-02b phase 2 is the heaviest context.** (S4-02b:38)
It combines the paged read, the recompute worker with failure and retry, the Financials and Assumptions UI and the 1440/390 layout evidence. Consider 2a (read plus recompute/worker) and 2b (UI plus layout evidence), as S4-03 used three phases.

Note, not a carry: `I-S4-02.effort` became M for a closeout-only gate (S4-02:12). S would match "no third build" better. It affects no current score, because I-S4-02 is not a candidate.

## Hard parts (item 2) summary

- M1 assignment table: coherent and implementable once C1 and C2 are applied. Future price and middle-only correction each keep the old revision ID for unaffected time.
- STALE: correctly defined by the price revision selected for the consequence's whole window plus the latest selected FindingRevision. Superseding an unrelated slice is not stale. It is consistent with the assignment model.
- `fuel-cost-1`: units are consistent (kW × h × L/kWh = L). The zero lower bound and Decimal outward rounding are correct. C4 is the one correctness gap. Failing closed to `QUANTITY_UNAVAILABLE` pending Q1 is correct under answers L15.
- `PRICE_SPANS_WINDOW`: correct and conservative. Define the window (C5).
- SYSTEM CLI vs `A-actor-identity`: consistent. The actor is derived on the server, a stable service principal is used, no human is impersonated, and no development context authorizes writes.
- Write refusals: correct codes. The success path needs C7.
- Honest states and orphan scan: `UNPRICED`, `QUANTITY_UNAVAILABLE` and `STALE/PENDING` are typed data states. Mock-only content is MissingClaim or omitted and itemized for G-05, which matches the S4-03 precedent and the owner's conditional acceptance there. C8 is the one inconsistency.

## Registry, ledger and score (item 3)

- Pure planning metadata. Five new nodes are added, all `open`. Seven nodes are retasked or reworded. No status, panel `state`, `reviewed_mapping`, tier, `coverage` or gap was promoted. `financials:1#a/2#a` and `assumptions:1#a/3#a` remain `core`, `open`. `mini:4#a` is untouched.
- `queue_baseline_nodes`: the five new IDs are added and nothing is removed. This is required by the checker (`check_v69_dependency_registry.cjs:166-177`: every queue-owned implementation and every open prerequisite of a baseline node must be in the baseline). `delivery_next_work.cjs` does not read the baseline, so it has no scoring effect.
- The README rows S4-02a → S4-02b → S4-02 → S4-03 satisfy the `sequenced_after` chain check (:121-128).
- Ledger: `task`, `supported_claim`, `interaction` and `unknown_or_empty` text only. `coverage` and `tier_approval` are unchanged.
- Score change: `-13k` vs `-13l` differ only in the `registry`, `queue` and `packet_status` fingerprints. `k` (10), `authority`, `panel_contracts`, `manifest` and `owner_input` are equal. No scoring parameter or script changed (`git diff --stat` touches only the two JSON files). Candidates go from 57 to 62, the five new nodes. The split inserts five open nodes (I-S4-02a, I-S4-02b, I-financial-assumption-store, D-financial-assumption-basis, I-consequence-history-read) on every proof path through I-S4-02:
  - Money panels: `d` goes from 6 to 11.
  - Mini panels: `d` goes from 10 to 15, and `mini:3` from 18 to 23.
  - A-S5-overview: B = 3/11 + 1/19 = 0.325 becomes 3/16 + 1/24 = 0.229. P = 5(1−e^(−B/10)) goes from 0.160 to 0.113, so the score goes from 2.148 to 2.134. Its own paths through I-S5-01 → I-S4-02 got longer.
  - I-financial-assumption-store: B = 4/12 + 3/16 + 1/24 = 0.563, P = 0.273, score = 0.4·5 + 0.3·0.273 + 0.2·2 − 0.1·3 = 2.182. Old I-financial-store: B 0.897, P 0.429, score 2.229.
  - The R and E terms cancel (+0.2 − 0.2), so the gap is 0.3 × ΔP: 0.081 (3.63%) before, 0.048 (2.20%) after. It narrowed because longer shared distances compress P. There is no manipulation. I-financial-store itself is now blocked on its new prerequisite.

## Q1 (item 4)

Q1 is well posed: self-contained, with three options, a recommendation and a fail-closed default. The default is correct: no positive upper amount and no `financials:1#a` closeout. Amend it with C4, which is the one other genuinely blocking formula question. Batch it in the same call, either as part of Q1 or as Q2 with the fail-closed containment rule as its default. I found nothing else that needs the Architect. C1 and C2 are Planner specifications within the decision.

## USER_REVIEW_REQUIRED (item 5)

S4-02b `true` is correct. S4-02a `false` is not, under WORKFLOW:212-214 and owner precedent (C3). Set it to `true`. The S4-02 milestone checkpoint stays on S4-02b.

## Owner-facing notes (no decision requested here)

- `-13l` is again `stop_owner` (2.20%, tie-break A-S5-overview). The owner chose "S4-02 money (I-financial-store)". I-financial-assumption-store is now the entry node of that same path, since I-financial-store requires it. WORKFLOW:208 says a changed input invalidates the prior selection. The coordinator should either confirm in one line with the owner that the choice carries over to the split, or record that interpretation explicitly in the handoff.
- Until an authenticated operator exists, the visible demo is a system-published price. The first amount reads from 0 up to a modelled value, or as unpriced or unavailable. The mock's "KES 198–238" will not be reproduced.

## Not verified

- check-all, vitest and pytest were not rerun by me (the coordinator ran check-all on `be68acc`; no product code changed).
- `tools/layout-evidence.mjs`: not applicable to a planning review.
- No implementation exists to verify.
