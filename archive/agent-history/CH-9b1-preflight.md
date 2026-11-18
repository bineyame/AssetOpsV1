# CH-9b1 pre-flight: Actions from an opportunity (R0) + P1

Branch `task/CH-9b1-opportunity-actions` from main `929d29076`. No code written, no DB touched.
Paths: `B/` = `backend/assetops_backend/`, `M/` = `backend/migrations/versions/`.

## 1. Facts checked against the code

- **Migration number.** Main head is `0050_chain_response_expiry` (`M/0050...py:15-16`, down `0049_mini_service_v2`). There is no 0046 on main (0045 -> 0047 chain). This unit takes **`0051_action_opportunity_origin`**; whichever of CH-9b1 / lane-1 CH-5b2 merges second re-points.
- **Study revision table** for `origin_opportunity_revision_id`: `mini_opportunity_revision` (`M/0030_w4_mini_decisions.py:156-168`). It has `scope_uk (tenant_id, site_id, id)` and `(opportunity_id, revision_no)` but **no (tenant, site, opportunity_id, id) key**, so the pair FK needs a new UNIQUE on it (additive, no row rewrite).
- **Thread side.** `finding_thread_occurrence` already carries exactly-one-of `finding_id`/`opportunity_id` (`M/0042_chain_threads.py:47-61`). `chain_action_thread.origin_finding_id` NOT NULL and the trigger matches on it (`M/0042:81-111`); the `chain_action` view projects `origin_finding_id` (`M/0042:113-119`). `link` resolves only by `finding_id` (`B/chain/adapters/postgres_thread_store.py:50-51,126-135`); `link_action`/`link_all` in `B/chain/threads.py:236-320`.
- **Lifecycle.** MINI_TRIAL ACCEPTED/APPLIED come from `action_event.kind` (`B/chain/lifecycle_run.py:37-42`), APPLIED's day from `action_policy_change.effective_from` (`B/chain/adapters/postgres_thread_sources.py:58-63`). No new state needed.

## 2. The blocking finding (Q1): `action` is reserve-trial-shaped end to end

The CH9-R3 contract change (origin pair only, 2 units) is **not sufficient** to store a mill Action as an `action` row:
- `M/0016_action_store.py:55-73` - `rule_id CHECK = 'reserve-trial-1'`, `field = 'reserve-state-of-charge'`, `unit = '%'`, `old_value BETWEEN 15 AND 90`, `action_proposal_is_trial (proposed = old - 5)`, and NOT NULL `primary_assessment_revision_id`, `foundation_revision_id`, `asset_id` with FKs.
- `M/0016:153` - an APPLIED `action_event` requires `expected_foundation_revision_id`; `B/actions/service.py:504-540` APPLY writes a **reserve policy change on the foundation**. The catalogue lever is `change: operating_schedule, writes_equipment: false` (design `:1834`), so that path is semantically wrong for the mill.
- `M/0019_verification_core.py:55,62,90-95` - `verification_plan` also needs `origin_finding_revision_id` NOT NULL, `rule_id = 'reserve-trial-1'` and an APPLIED `action_event` (CH-9b2's concern, noted so it is sized).
- Reserve-column readers: 33 refs in 7 files (`action_api.py` 5, `actions/adapters/postgres_action_store.py` 10, `actions/reserve_trial.py` 4, `actions/service.py` 10, `analytics/adapters/postgres_assessment_store.py` 2, `analytics/finding_read.py` 1, `estate/adapters/postgres_estate_read.py` 1).

**Options**
- **A (default, closest to the ruling).** Keep `action` and add a lever discriminator: `rule_id IN ('reserve-trial-1','productive-load-midday@1')`; the reserve columns become NULL-able under a CHECK "`rule_id = 'reserve-trial-1'` <=> all reserve columns set and the trial rule holds" (DROP NOT NULL only, no row rewrite); `action_event` APPLIED's foundation requirement becomes "reserve rule only"; a lever APPLIED records its `effective_from` in a new append-only `action_schedule_change` (mirrors `action_policy_change`), and `_CHANGE_OF` reads either. Recording is a service method (Q2). Every reserve-column reader filters to `rule_id = 'reserve-trial-1'` or tolerates NULL, inside the same reader audit. **Size: R0 2 -> about 3.5-4 units** (CH-9b 4.5 -> 6-6.5).
- **B.** Widen `domain_action` (`domain IN ('COLDCHAIN','MINI')`, `M/0033_w5_cold_work.py:44`) with the opportunity origin; ACCEPTED from its row and APPLIED from a work-case COMPLETE already map (`B/chain/lifecycle_run.py:63-68`), matching CH-9 Q8 "its case completed". Cheaper here (~2.5), but `verification_plan` is keyed on `action` + `action_event`, so CH-9b2 grows by about 1.5 instead.
- I recommend **A**: it keeps the verification plan on its existing table and makes the cost visible in this unit. The Architect should re-size and decide whether to split R0.

## 3. P1 - the pass margin (may need the owner)

Catalogue text, quoted (design `Docs/demo-sprint/implementation-logic-design-proposal.html:1834-1840`):

> `productive-load-midday@1: {for: [PRODUCTIVE_USE_HEADROOM], change: operating_schedule, writes_equipment: false, must_not_harm: [MG-5, MG-4], verification: midday-productive-shift-1}`
> `midday-productive-shift-1: {measure: "productive_kwh[midday]", compare: "before/after, Complete days", min_days: 3, guardrails: [battery_reserve, critical_served]}`

**There is no margin and no target** (the reserve entry has one: `target: "4*later <= 3*baseline candidate_seconds"`). By R3 the owner declares it. Options and what each means for the demo:
1. **"Later mean above baseline mean"** (margin 0). Simplest words; but any small rise, including day-to-day noise, reads as "Checked and working". Weakest claim.
2. **Later mean at least 10% above baseline mean** (recommended). Plain words ("midday use rose by at least a tenth"); a real mill shift (several kW over hours) clears it easily, ordinary noise usually does not. The 10% is declared, not fitted.
3. **Every later day above the highest baseline day.** Strongest and easiest to explain with the day table; can fail an honest change on one cloudy day, so the demo may show NOT_VERIFIED.
4. An absolute floor (e.g. +N kWh a day). Needs a mill load figure we do not have; not recommended.

Separate observation for CH-9b3 (no decision here): the plan's `guardrails: [battery_reserve, critical_served]` and the lever's `must_not_harm: [MG-5, MG-4]` name the same two checks in different vocabularies.

## 4. Reader list (`grep -rn "origin_finding_id\|origin_finding_revision_id" B/`)

`action` readers (must filter to Finding origin or handle both):
- `B/actions/adapters/postgres_action_store.py:48,57,213,220,247,292,923,961,963`
- `B/actions/service.py:142,147,184,234,238,240,283,372,662,663,669,677,678,701`
- `B/actions/site_index.py:223,224`; `B/actions/verification.py:217,626,900`
- `B/chain/adapters/postgres_chain_read.py:85`; `B/chain/adapters/postgres_thread_sources.py:44,55,175,177`; `B/chain/adapters/postgres_thread_store.py:54,72,126,131,135`; `B/chain/backfill.py:99`; `B/chain/lookup.py:45,46`; `B/chain/site_chain.py:116`; `B/chain/threads.py:204,236,239,243,256,312,315,320`
- `B/estate/adapters/postgres_estate_read.py:199,389`; `B/estate/coverage.py:378,392,395,396`; `B/estate/portfolio.py:191` (docstring)
- `B/financials/trial_fuel_comparison.py:50,160` (verification-plan value); `B/site_outcomes/board.py:162,323,324,553,765,767`; `B/site_outcomes/cold.py:160`; `B/site_outcomes/ev.py:142,238` (in-memory dataclass field, already Optional)

`domain_action` readers (same token, unaffected; listed so the guard allowlist is complete): `B/work/adapters/postgres_domain_action_index.py` (2), `postgres_domain_intent.py` (5), `postgres_work_read.py` (13), `postgres_work_store.py` (1), `B/work/domain_action.py` (3), `domain_action_index.py` (11), `domain_intent.py` (6), `site_index.py` (7).

## 5. Questions (all batched; each has a default)

- **Q1 Action shape** - A or B (section 2). Default **A**, R0 re-sized to about 3.5-4.
- **Q2 Recording path.** Default: a service method `record_opportunity_action(...)` and `apply_schedule(...)` used at story time and by tests, with no new HTTP route or UI command (none is in the mock scope for this unit).
- **Q3 Lever APPLIED day.** Default: new append-only `action_schedule_change (action_id, effective_from, recorded_at)` with `chain_input_change` triggers; `_CHANGE_OF` takes whichever exists.
- **Q4 Revision FK.** Default: add `UNIQUE (tenant_id, site_id, opportunity_id, id)` on `mini_opportunity_revision` in 0051 for the pair FK.
- **Q5 Reader guard.** Default: an L0 test that tokenises `B/**/*.py` for the two column names and compares per-file counts against a committed allowlist (section 4, `action` vs `domain_action` classified); any new file or higher count fails.
- **Q6 Byte-equality proof.** Default: on `fresh_database()`, seed a reserve-trial Finding-origin Action with the existing S6 fixture at 0050, capture board, Actions-list, thread and verification bodies, upgrade to 0051, capture again, assert byte-equal.
- **Q7 Out of scope here.** Default: no verification plan for the mill Action in this unit (CH-9b2); its `verification_plan` widening is sized there.
- **P1 margin** - owner. Recommendation: option 2 (10% above baseline mean). CH-9b3 waits on it; CH-9b1/9b2 do not.
