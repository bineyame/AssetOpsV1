# S4-02 plan fix round: fresh re-review

Reviewer: fresh Claude re-reviewer. I did not write the packets, the first review (`.agent/S4-02-plan-review.md`), the Architect rulings or the fix round. Date 2026-10-13.
Branch `plan/S4-02-refine`, diff `f4accc1..d513ce9`: `99529f7` (Architect request), `94d6535` (Architect answers and DECISIONS addendum) and `d513ce9` (Sonnet fix round, S4-02b item 2 rewrite, `I-S4-02.effort` M->S, `next-work-2026-10-13m.json`).

## Verdict: ACCEPT, with one text carry (R1) to apply before S4-02a activates

C1-C3 and C5-C9 are applied as the first review's fix text says. None is weakened. S4-02b item 2 carries the Architect's Q1/C4 rulings faithfully, with no drift in the formula, containment rule, fixtures or wording. The DECISIONS addendum matches the Architect's draft. The next-work regeneration is correct.

The fix round leaves one new gap. C1's `change_kind` has no lawful kind for the first, backdated demo price (R1). It is a one-sentence edit and does not need another review round. The other findings are Low or Nit, and an implementer could settle them in phase 1 without changing the plan.

## Checks run (by me)

- `node frontend/docs/architecture/check_v69_dependency_registry.cjs`: exit 0. "Registry valid: 217 nodes, 11 linked pilot panels".
- `--verify-report .agent/next-work-2026-10-13m.json`: exit 0.
- `--next-work --json --out <scratch>/nw.json`: exit 0. The fresh report equals `-13m` on every top-level key. Decision: `stop_owner`, top I-financial-assumption-store 2.182, second A-S5-overview 2.134, gap 2.20%, tie-break recommends A-S5-overview.
- `-13l` vs `-13m` differ only in the `fingerprints` (`registry`, `packet_status`) and `candidates` keys. Within `candidates`, only the I-S4-02 entry differs, by `effort` M->S. It has `ready_now: 0`, so it is blocked and not eligible. The decision is unchanged.
- Sizes: S4-02a is 42 lines and 1446 words. S4-02b is 43 lines and 1580 words (S4-03 was 1583). The WORKFLOW.md:90 ceiling is 220 lines, so both are well under it. They are dense but still implementable.
- I did not rerun check-all, because the coordinator ran it 9/9. No product code changed, so the product suites and layout evidence do not apply.

## Carry-by-carry

| Carry | Location | Result |
|---|---|---|
| C1 change_kind | S4-02a:20 | Applied verbatim, with the reworded overlap sentence and one negative test per kind (phase 1, :37). New gap: R1 |
| C2 constraint | S4-02a:19 | Applied verbatim: set-once `recorded_to`, trigger-enforced; the EXCLUDE as specified; shared instant; containment check. Implementation hazards: R2 |
| C3 owner review, plain reading | S4-02a:4, :27; S4-02b:31 | Applied. `USER_REVIEW_REQUIRED: true`. IDs, digests, formula version and enums go to details/History in both packets. The `MODELLED_CONDITIONAL` and "fuel-cost-1 model bound" phrases are no longer mandated UI copy. The milestone checkpoint stays on S4-02b |
| C5 window | S4-02b:20 | Applied: the FindingRevision `window_start/end`, plus the reworded crossing sentence. The activation clause is moot now that Q1 is answered (status line :3) |
| C6 tab and routes | S4-02a:28 | Applied. `operatorSiteTabs.tsx:82` is `Financials`, `capability: false`, as cited. The route shape follows the existing `/sites/{site}/...` pattern (`operatorSiteRoutes.ts:155`). Scenarios is omitted and itemized for G-05 |
| C7 write route | S4-02a:20 | Applied verbatim (refusal codes 401/403/404/422; no `development_access`). Ordering nit: R4 |
| C8 disabled edit | S4-02a:11, :29 | Applied using the first option, the catalogued `G-assumptions-human-edit` via `<MissingClaim>`. This matches the owner's missing-data rule (mock content with no source is shown as a catalogued missing claim, not as a free literal). `missing_kind` is left open: R5 |
| C9 phase split | S4-02b:38-39 | Applied: 2a read and recompute, 2b UI and layout evidence |
| I-S4-02 effort note | S4-02:12; registry | Applied (S). No scoring effect, as predicted |

### C1 and C2 together

I traced the cases for conflicts between C1's kinds and C2's bitemporal EXCLUDE with a set-once `recorded_to`. I found none:

- SUCCESSION at a future `t` sets `recorded_to = r` on v1 `[t0,∞)`. It inserts v1 `[t0,t)` and v2 `[t,∞)`, each with `[r,∞)`. The recorded ranges `[r0,r)` and `[r,∞)` do not overlap.
- A later SUCCESSION inside v2's open tail truncates v2 the same way.
- A middle CORRECTION reproduces the first review's trace: v1 `[t0,a)`, v3 `[a,b)`, v1 `[b,t)`, v2 `[t,∞)`.
- Superseded rows are never edited again, so set-once holds.
- An open-ended future publication at `t'`, with `r ≤ t' < t` after a prior SUCCESSION at `t`, is refused as SUCCESSION, because v1 `[t0,t)` is not open-ended and v2 does not contain `t'`. It is also neither "backdated" nor "bounded". It can still be published as a bounded CORRECTION `[t',t)`, so it is expressible. I record this as residual risk, not a finding.

The real gap is R1.

## Findings

### Medium

**R1. No lawful `change_kind` exists for the first (or any gap-filling) backdated publication, and the demo depends on one.** (S4-02a:20, with :11 and phase 1 :37)
SUCCESSION requires `valid_from ≥ recorded_at`. CORRECTION is "backdated or bounded", requires a reason, and is labelled a correction in History. To price any existing Finding, fixture v1 must be valid over past windows: S4-02b:20 says a future price does not reprice yesterday. So the first demo price, published now with `valid_from` in the past, can only be a CORRECTION of nothing. History would then show the first-ever price as a "correction". That contradicts the decision's intent that the correction label distinguishes a retroactive edit from an ordinary change (DECISIONS.md:4101). An implementer will either mislabel v1 or invent a third rule. This is a new ambiguity from the C1 text, which I also missed when that text was written. It is not a weakening by the fix round.
Fix (one sentence in item 2): add a kind for a publication whose authored range overlaps no current assignment. For example, `INITIAL`, which may be backdated, needs no reason and is refused with 409 if it overlaps any current assignment. Alternatively, state that a backdated publication over uncovered time is SUCCESSION. Then name v1's kind in the phase 1 fixture and add its negative test (an `INITIAL` that overlaps returns 409).

### Low

**R2. The shared-instant rule allows empty or inverted recorded ranges, and the "check" cannot be a CHECK constraint.** (S4-02a:19)
`recorded_to = recorded_from = transaction instant` is right. If the instant is Postgres `now()` (the transaction start), however, a transaction that waited on the series lock can carry an earlier instant than the row it supersedes. That makes `recorded_to < recorded_from`, which is an error. If the instants are equal, it makes an empty range, and an empty `tstzrange` overlaps nothing, so it silently escapes the EXCLUDE.
Separately, "a check requires every current assignment's valid range to lie inside its revision's authored range" spans two tables, so it must be a trigger, not a CHECK.
Fix: take the instant after acquiring the series lock (`clock_timestamp()` or equivalent). Require `recorded_from < coalesce(recorded_to, 'infinity')` and that the new instant is greater than the series' latest `recorded_from`. Call the containment rule a trigger. An implementer could reasonably do all of this unprompted, so this is Low.

**R5. `G-assumptions-human-edit`'s `missing_kind` is left to the implementer.** (S4-02a:29)
`A-actor-identity` is `resolved` (registry :33), so the author/actor contract exists, and what is absent is the verified human sign-in implementation. Under the first-absent-authority rule (DECISIONS.md:4108) that is `build`, not `contract`.
Fix: name `build` and an open owning node (the future human-auth task, not the resolved `A-actor-identity`), so that the catalogue entry is not decided ad hoc.

### Nit

- **R3.** S4-02a:37 still says "closure events", which is left over from the replaced "append-only assignment/closure rows". Suggest "superseded assignments (set `recorded_to`)". S4-02a:27's example phrase "modelled estimate, not a measured saving" is copied from C3 but S4-02a shows no money. Harmless.
- **R4.** S4-02a:20 says the 422 for a body actor/author field comes "before scope". It does not say whether that is before or after the 401. Suggest auth (401), then 422, then scope (403/404).

## S4-02b item 2 vs the Architect's rulings

I compared item 2 clause by clause with `.agent/architect-S4-02-answers.md` and the DECISIONS.md:4110 addendum. Every clause matches:

- **Parameter:** immutable, dimensionless 1.10, conditional inequality, not calibrated and not `SFC_UNCERTAINTY`. The version records value, inequality, scope, source, reviewer/date, formula and ID/digest. A later value needs a new version.
- **Input rule:** `T_i` is the observed CANDIDATE `[start,end)`; no `T_i,high`, `upper_minutes`, `off_before` or `off_after` is used. The rule applies to the union `C` per asset. Intervals must be wholly inside contiguous Candidate time, which is equivalent to "within `C`". Coverage must be complete, same-asset intervals must not overlap, and SFC must be a single positive time-valid value. Any failure makes the whole consequence `QUANTITY_UNAVAILABLE`.
- **Formula:** `1.10 × Σ_j (P_j,mean × (b_j − a_j) × SFC_j)`. Each interval is counted once, in unrounded Decimal. Using `max(mean) × duration` and prorating are both prohibited.
- **Fixtures:** both positive cases, the `upper_minutes = null` case and all six unavailable classes are present, with their assertions.
- **Wording:** quoted verbatim, with final copy at the owner checkpoint.

The packet does not restate `amount_high = quantity_high × price`, but the migration section (S4-02b:26) has the Decimal multiply and outward rounding, so nothing is lost.

Consistency with the rest of S4-02b:

- Item 1 already excludes Indeterminate/Necessary spans and reads `[start,end)` spans.
- Phase 1 independently reviews the 1.10 condition and wording, which satisfies the Architect's condition that "no positive upper before independent review".
- L6 fallback to unavailable is retained (:31).
- STALE is unaffected, because the parameter version is immutable.
- The quantity is per FindingRevision, and price coverage uses the same FindingRevision window (item 3). This matches the Architect's "price covers the entire FindingRevision consequence window".

"Per generator asset" does not raise a multi-generator question. `dispatch_v3.py:169-174` refuses more than one asset bound to a role, and segments are Site-level (`Segment` has no asset, :104-125).

## Residual risk (not findings)

- An open-ended future price inserted before an already-scheduled future price must be authored as a bounded CORRECTION (see the C1/C2 trace). This is acceptable, but the History label may surprise the owner at the walkthrough.
- The fail-closed containment rule may make many real Findings `QUANTITY_UNAVAILABLE`, because power intervals routinely straddle Candidate edges. The owner walkthrough should include a positive Finding from ordinary S4 data, not only a constructed fixture. Otherwise the checkpoint may show no bounded amount. The Architect's ruling anticipates this ("bounded and straddling-unavailable cases"), so it is a demo risk, not a plan defect.
- The owner's earlier choice of "S4-02 money" still has to be confirmed as carrying over to I-financial-assumption-store at the 2.20% stop_owner. This is unchanged from the first review's note.

## Not verified

- check-all (the coordinator ran it, 9/9), pytest, vitest, build and `tools/layout-evidence.mjs`: not run, because this is a planning-only diff.
- No implementation exists to verify.
