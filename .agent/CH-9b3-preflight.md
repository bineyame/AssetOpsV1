# CH-9b3 pre-flight: mill verdict (evaluator, trigger, reads, page)

Branch `task/CH-9b3-mill-verdict` from main `0d34ee3b1`. Scope: build sheet CH-9b "Build units" CH-9b3, as cut by
SCOPE-1 (1.0: R3 owner 10% rule, R5 evaluator + `snapshots` trigger, R7 reads + metrics table; no R4 guardrails
(BL-09), no RECURRED_DURING_CHECK (BL-07), no `test_ch6_*`, no outcome-id ratchet), CH9b1-R P1, CH9b2-R Q4/Q6/Q7,
Lows L3/L4 of CH-9b2. Paths: `B/` = `backend/assetops_backend/`.

## Facts from code (path:line)

- Plan freeze exists: `B/actions/verification_families.py:124-187` (`MiddayShift.freeze`), `TARGET` P1 verbatim
  `:50-51`, `SHORT_TEXT` `:52`, pure `choose_days` `:80-84`, `later_candidates` `:75-77`, `guardrails = {}` `:168`.
- Outcome states are fixed by 0019: `verification_outcome.outcome IN ('VERIFIED','INEFFECTIVE','INCONCLUSIVE')`
  (`migrations/versions/0019_verification_core.py`, table `verification_outcome`); metric `window_name IN
  ('BASELINE','LATER','COMPARISON')`, `state IN ('PASS','FAIL','UNKNOWN')`. 0052 makes outcome/request exactly-one-of
  `action_id`/`domain_action_id` (`0052_verification_plan_domain.py:115-131`). Reasons constant `TARGET_MISS` exists
  (`B/actions/verification_rules.py:663`).
- Outcome writes today: `PostgresActionStore.record_evaluation` (`B/actions/adapters/postgres_action_store.py:844-893`)
  is reserve-only (trial lock on `battery_asset_id`, `OUTCOME_COLUMNS` names `action_id` `:76-78`, action_event
  evaluator events). Outcome read `outcomes()` `:819-829` filters `action_id`.
- `productive_kwh` value is `{"kwh": "<decimal text>", "measured_seconds": n}` per productive-asset subject
  (`B/chain/measure_impls.py:143-149`); SnapshotReader `latest(t, s, from_day, to_day, measures, known_at)`
  (`B/chain/reader.py:100-108`); day grade is weakest-row (`_day_grade`, `B/chain/reader.py:45`).
- Trigger site: tick order is `chain_threads` (`B/scheduling/tick.py:485`) then `chain_snapshots` (`:525`);
  `chain_snapshots` = consume + drain (`B/scheduling/stages.py:275-311`). Demo prepare builds snapshots directly, so no
  consumer runs there (`B/chain/backfill.py:148`).
- Lifecycle: `causes_for_site` maps VERIFIED/INEFFECTIVE/INCONCLUSIVE by `o["action_id"]` (`B/chain/lifecycle_run.py:45-62`);
  `_OUTCOMES` selects `o.action_id` and `_CHANGE_OF` on `o.action_id` (`B/chain/adapters/postgres_thread_sources.py:65-69`)
  so a domain outcome today has `action_id = NULL`, no `effective_from`, and is never linked (L4).
- L3: CH-6a2 is NOT on main (`git log main` has no CH-6a2 merge; `task/CH-6a2-evaluator` unmerged). The
  `_day_grade` import (`verification_families.py:38`) stays; L3 is deferred to whichever of CH-9b3/CH-6a3 lands after
  CH-6a2. (`B/chain/read.py:73` `day_grade` is a different, per-measure function.)
- Page: there is NO page or read for a MINI domain Action today.
  - The domain detail read excludes MINI (`B/work/adapters/postgres_domain_action_index.py:66`); its frontend type
    admits `COLDCHAIN | EV_CHARGING` only (`frontend/src/sites/domainActionClient.ts:23-28`).
  - On a MINIGRID Site, `/sites/{code}/actions/{id}/verification` is the W1 page (`SiteActionVerification.tsx`,
    W1 `/api/sites/{code}/actions/{id}/verification/*` routes, `B/action_api.py:245-305`); the domain dispatch is
    COLDCHAIN/EV only (`frontend/src/shell/SiteAnalyticsFrames.tsx:1799-1849`).
  - The Site work index gives a MINI Action link `href = None` "no domain Verification route yet (CH-9b2/9b3)"
    (`B/work/site_index.py:229-236`).
  - `VerificationService.summary` is per W1 action (`B/actions/verification.py:1055-1094`); `cost_check`/`trial_hours`
    read W1 stores.
  - No frontend file references `cost_check` (the sheet's grep anchor is stale); the W1 page is
    `frontend/src/sites/SiteActionVerification.tsx` + `verificationCards.tsx`; outcome words in `verificationWords.ts`.

## Lane-1 (CH-6a3) overlap

Planned CH-9b3 files: `B/actions/verification_families.py`, `B/actions/verification.py`,
`B/actions/adapters/postgres_action_store.py`, `B/chain/adapters/postgres_thread_sources.py` (L4 only),
`B/scheduling/stages.py` (trigger), `B/work/site_index.py` (MINI href), one read route (Q5), frontend
`SiteAnalyticsFrames.tsx` dispatch + one new mill verification panel and client. **None of** `chain/outcomes.py`,
`chain/vocabulary.py`, `site_outcomes/*` or the "Why?" bodies, under the defaults below. Overlap appears only if Q7
or Q8 is answered differently (board/Why? wording, or new words that guard V requires in `chain/vocabulary.py`).

## Questions (batched; each with the default I build if accepted)

- **Q1 NOT_VERIFIED mapping.** The brief and R4 say NOT_VERIFIED; the stored set is VERIFIED/INEFFECTIVE/INCONCLUSIVE
  (R5 "existing set"). Default: a target miss is `INEFFECTIVE` with `reasons = ['TARGET_MISS']`; the page word is the
  existing "Target not met" (`verificationWords.ts`). No migration.
- **Q2 not-judged states.** Default:
  - SHORT baseline (CH9b2-R Q4): no outcome is ever stored; the page shows the plan's `not_judged_text` verbatim.
  - Fewer than 3 COMPLETE later days while the 14-day look-ahead is still open: no outcome; the page shows
    "Not judged yet: only {n} of 3 fully checked days after the change" (MOCK DEVIATION, mirrors SHORT_TEXT; §0 text).
  - Look-ahead closed (Site-local today past `effective_day + 14`) with fewer than 3: one `INCONCLUSIVE` outcome,
    `reasons = ['LATER_SHORT']`, so the existing INCONCLUSIVE_EXPIRED lifecycle path applies. (Alternative: never
    store INCONCLUSIVE; say if preferred.)
- **Q3 zero baseline.** `10*mean(later) >= 11*mean(baseline)` passes literally when the baseline mean is 0. Default:
  apply the declared rule unchanged (no extra condition invented); if baseline mean is 0 the outcome is
  `INCONCLUSIVE` `reasons = ['BASELINE_ZERO']` because "rose by 10%" is undefined. Owner-rule purity says either is
  defensible; I default to INCONCLUSIVE (no claim) unless ruled otherwise.
- **Q4 values read.** Default: day value = Σ `value.kwh` over the day's `productive_kwh` subject rows (Decimal);
  baseline uses the plan's frozen days, later uses `choose_days(later grades)` at evaluation; values read from
  `SnapshotReader.latest(..., known_at = evaluation cutoff)`. If a frozen baseline day is no longer COMPLETE at
  evaluation, no outcome (not judged). Pinned vs used revisions go in `details`. Comparison in integers/Decimal
  (`10*Σlater >= 11*Σbaseline`, equal day counts), never floats.
- **Q5 store + route.** Default:
  - Store: new `record_domain_outcome(t, s, plan, outcome, metrics)` (advisory lock per domain Action, one decisive
    outcome per plan; idempotency key `midday-outcome-{plan_id}`; no request row, `evaluation_request_id NULL`;
    actor `SYSTEM`/`service:verification-evaluator`; no `action_event` writes) and `domain_outcomes()` read.
    `OUTCOME_COLUMNS` unchanged (reserve bodies byte-equal); a `DOMAIN_OUTCOME_COLUMNS` twin.
  - Read: `VerificationService.domain_summary(t, s, code, domain_action_id)` returning `{label, state, outcome,
    reasons, metrics[], line, not_judged_text, plan window days, cost_check: null, trial_hours: null}`.
  - Route: one GET `/api/sites/{code}/domain-work/actions/{id}/verification` (read-only; CH9b1-R Q2 forbade new
    *recording* routes, not reads). Alternative: fold the block into the domain detail read, which today excludes MINI
    by design (CH9b1-R Q5) — I avoid reopening that.
- **Q6 page address on a MINIGRID Site.** `/sites/{code}/actions/{id}/verification` is the W1 page there and Kobo
  ACT-001 uses it. Default: a **new path `/sites/{code}/domain-actions/{id}/verification`** so the W1 dispatch
  is untouched (alternative: a domain-first probe on MINIGRID `/actions/{id}/verification`, costing an extra read
  for every W1 Action). `site_index._action_link` gives a
  MINI link that href when the selection has lineage. The page: shell header "Run the mill at midday", one Panel with
  the outcome words + R7 line + `metrics[]` DataTable (label, before, after, days, rule), MD-CH9b-1 labelled.
- **Q7 presented wording.** Default: on VERIFIED the page sentence is SCOPE-1 verbatim "Midday use rose by at least
  the declared 10% on fully checked days", then the R7 line "Midday use before and after the change: {b} → {a} kWh a
  day on {n} fully checked days each". No guardrail text. Board Grow row and "Why?" wording are NOT changed here
  (lane 1 / DD-1b own them).
- **Q8 vocabulary.** If guard V rejects a new page word, default: add it to the frontend vocabulary exemption the
  guard already reads, not `chain/vocabulary.py` (lane 1). Say if `chain/vocabulary.py` must own it.
- **Q9 trigger.** Default: `chain_snapshots` stage, after `drain`, calls `evaluate_domain_plans(t, s, now)` for the
  Site's midday plans with no decisive outcome, only when the drain processed a `productive_kwh` row or a plan's
  look-ahead just closed; a failure there is reported in the stage body, never fails the stage. The outcome's 0044
  `verification.outcome` event reaches lifecycle on the next tick's `chain_threads`. Prepare (no consumer) is DD-1b's:
  it calls the same service method at story time. L2 calls it directly.
- **Q10 L4 effective day.** Default: `_OUTCOMES` selects `COALESCE(o.action_id, o.domain_action_id) AS action_id` and,
  for a domain row, `p.effective_from` as `effective_from` (`CASE WHEN o.domain_action_id IS NOT NULL`), so
  RESOLVED_MONITORING dates from the change as for reserve; reserve rows byte-equal.
- **Q11 L2m.** Default: L2 fixture only (MD-0 Kobo story does not yet carry the mill Action; DD-1b does); packet says so.
- **Q12 R6.** Packet states: occurrences during the later window are not recorded as RECURRED_DURING_CHECK (BL-07);
  the R3 metric alone decides.

Size check: 1.0 assumed the page exists; Q5/Q6 (new read route + new MINIGRID page address) push it to about 1.5.
STOP for rulings.
