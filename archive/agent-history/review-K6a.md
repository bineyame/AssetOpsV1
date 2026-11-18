# Review: DIESEL-K6a, the fuel Finding as a domain-Action origin (migration 0057)

- Reviewer: Claude (Opus), independent first review. Fresh context. I did not write any of this slice.
- Branch: `task/DIESEL-K6a-fuel-action-origin`. Reviewed at head `2fa06ec0a`, with `git diff main...HEAD`.
- Judged against: build sheet DIESEL-1 §9m.1-§9m.3 (R3m) and §9m2 (R3m2), plus `.agent/review-packet-K6a.md`.

## Verdict: ACCEPT

The slice matches the card. Every code line in the diff matches the spec text (§9m.3 items 1-5, §9m2 items 1-2), and 0057 matches §9m.2. I found three Low findings and no High or Medium ones. None of the Lows blocks the merge.

## Spec conformance (verified by reading the code)

- **`FUEL_SPEC` registration.**
  - `FUEL_SPEC` is in `ACTION_DOMAINS` only (`work/domain_action.py:136`).
  - `DOMAINS` and `BY_FINDING_DOMAIN` are unchanged.
  - The origin is `ORIGIN_FINDING` and the site type is `MINIGRID`.
  - The criteria and basis keys are empty, so `post_intent` refuses through the existing `not spec.criteria` branch.
- **`create_action` branch order** (`work/domain_intent.py:94-115`):
  - The order is site type, then the Finding domain, then the fuel selection.
  - The fuel branch never reaches `selected_pin`, and `_pin` is untouched.
  - The opportunity (MINI) branch is byte-equal.
- **`_DomainTx.fuel_finding_selected`** (`postgres_domain_intent.py:130-138`) is the card SQL verbatim.
  - The revision must be SUPPORTED, `fuel_balance` / `fuel-balance-1`, created at or before `:now`, and equal to `max(revision_no)` among the revisions known at `:now`.
  - The "created after `command_now`" case is already refused one step earlier, by `finding_revision` (`:90`).
- **Index filter.** The index filter is the positive `domain IN ('COLDCHAIN', 'EV_CHARGING')` in both `action` and `actions_in_window`. Under 0051's `domain_action_mini_origin` this is the same set as before.
- **`_FINDING_DOMAIN_OF`** gains exactly `FUEL_BALANCE: fuel_balance`. `MINI` is still absent, and the mill keeps its separate opportunity path.
- **Migration 0057.**
  - `down_revision = "0056_unexplained_fuel_finding"`.
  - The domain CHECK widens.
  - `rule_id`, `plan_version` and the family CHECK are re-added under the same names.
  - The fuel arm nulls exactly `RESERVE_COLUMNS` minus `origin_finding_revision_id`, which matches the column list in §9m.2.
  - `FAMILY_0052` matches 0052's two arms.
  - The downgrade locks the seven tables, refuses with the spec message while fuel rows exist, and then restores 0052 and 0051.
- **R3m2.**
  - The `action_domain` key is added only when the domain is `FUEL_DOMAIN`, so the Cold, EV and mill link dicts are byte-equal.
  - `_action_link` returns `href = None` for a fuel link.
  - The Cold and mill branches are unchanged.

## Readers of `domain_action` (grep over `backend/assetops_backend`, plus `spec_of` / `ACTION_DOMAINS`)

- **Cold/EV index and site outcomes.** The Cold/EV index (`postgres_domain_action_index.py`) now has the positive filter. `site_outcomes/cold.py` and `site_outcomes/ev.py` read only through that index, so a fuel Action never reaches a Cold or EV board.
- **`domain_action_index.py:163` and `:489` (`spec_of`).** These are reached only with rows from that index, so they never see a fuel row.
- **Readers that are safe as they are.** None of these changes behaviour for a fuel row:
  - `postgres_action_store.py:298`, the code-collision check;
  - `postgres_action_store.py:748`, the mill context, which refuses non-MINI rows;
  - `chain/adapters/postgres_chain_read.py:89`;
  - `chain/lookup.py:44`;
  - `chain/adapters/postgres_thread_sources.py:73`;
  - `chain/adapters/postgres_thread_sources.py:185`, which yields `DOMAIN_INTENT` with the Finding origin; L2 6 proves the thread join;
  - `postgres_work_read.py:52`, the codes.
- **`work-case-detail-1` wire.** `work/detail.py:75` serves `all_action_links` raw, so the site detail wire now carries `action_domain` on a fuel link only. This matches the mill's existing `opportunity_revision_id` precedent. The frontend decoder accepts extra keys (`frontend/src/work/globalWorkClient.ts:543-551`). `global_detail.py:114`, `global_index.py:329` and `site_index.py` all mint their hrefs through `_action_link`, so all three get `href None`.
- **Token and basis rows** (`site_index.py:323`, `global_index.py:354`). These read only `action_id` and `finding_revision_id`, so the Cold, EV and mill selection tokens are unchanged.

## Deviations

1. **S-a5, the `test_w504_ev_intent_postgres.py:132` pin.** This is purely a DDL-text consequence: it is the `pg_get_constraintdef` text of the widened CHECK, and nothing else in that test changed. I accept it, along with the approved `:154` key.
2. **The raw COLDCHAIN insert in L2 item 4.** I accept it. It proves the positive filter still lists a Cold-domain row. The fuel-row omission is the mutation-sensitive half, and I confirmed it fails under both the per-predicate mutations below.
3. **The plan-row downgrade refusal with the Action present.** I accept it as a test-shape choice. The residual gap is recorded as L2 below.

## Findings

### Low

- **L1 - The "detail" leg of the R3m2 L2 check is vacuous.**
  - Location: `backend/tests/test_k6a_fuel_action_origin_postgres.py:337` and `:345`.
  - What is wrong: `WorkDetailService.detail` serves raw link dicts with no `href` at all, so `f"/actions/{aid}" not in wire` passes for the detail body whatever `_action_link` does. Only the site maintenance index leg is sensitive. My `r3m2` and `readkey` mutations both failed on the index body.
  - Why it matters, as a failure scenario: suppose a later edit gives `global_detail.py:114` its own link mapping, instead of the shared `_action_link`, and that mapping dropped the fuel branch. This test would not catch it. Today it calls the same function, so the risk is low.
  - Fix: point the detail leg at the global request detail, which mints hrefs. Alternatively, name the leg in the packet as an "action_id present" check only.
- **L2 - The plan clause of the 0057 downgrade guard is not independently proven.**
  - Location: `backend/migrations/versions/0057_fuel_verification.py:104`.
  - What is wrong: the plan test runs with a `FUEL_BALANCE` Action present (Known Deviation 3). If `OR EXISTS (... verification_plan WHERE rule_id = 'fuel-residual-within-band-1')` were deleted, every K6a test would still pass.
  - Why it matters, as a failure scenario: the fuel arm requires `domain_action_id` but does not bind it to a `FUEL_BALANCE` row. A fuel-rule plan citing a COLDCHAIN or MINI domain Action is therefore storable, and a downgrade in that state would silently drop the plan family arm under live rows. This is unlikely, because only K6b writes fuel plans, through a fuel Action.
  - Fix (optional): add a test with a fuel plan row whose `domain_action_id` is a raw non-fuel row.
- **L3 - The EV leg of the positive index filter is not exercised in K6a's own tests.**
  - Location: `postgres_domain_action_index.py:72` and `:79`.
  - What is wrong: a mutation to `domain IN ('COLDCHAIN')` passes `test_k6a_*`.
  - Coverage: it is covered by the EV index tests in `test_w504_*`, which the implementer ran green, and I did not rerun them. This is informational; no action.

## Client wording

- `FUEL_MESSAGES` (five texts) and `FUEL_SPEC.summary` contain no theft, stolen, stole, siphon or pilfer.
- They pass guard V's pattern set. Both `test_fuel_literals_pass_guard_v_and_h4` and `test_out_b2_vocabulary.py`, which now scans them, passed.
- The test's planted-word assertions keep the scan from being vacuous.

## Checks I ran

All runs used the plan2 venv with PYTHONPATH set to the k6a worktree: `backend;contracts;tools;simulator;gateway;host;field;backend\tests;host\tests`. Imports resolve into `AssetOpsV1-k6a` (`assetops_backend`, `assetops_contracts` and `work/domain_action.py` were printed). Postgres runs used only `assetops_k6_test`, with free RAM at 3.4-3.5 GB.

| Check | Result |
|---|---|
| `test_k6a_fuel_action_origin.py` + `test_out_b2_vocabulary.py` | 13 passed (1.8 s) |
| `test_k6a_fuel_action_origin_postgres.py` | 7 passed (21 s) |
| `test_ch9b1_*`, `test_ch9b2_*`, `test_ch9b3_*`, `test_s4_finding_domain_filter_postgres.py` (9 files) | 69 passed (140 s) |
| `test_w504_ev_intent_postgres.py -k "sole_head or dispatch_is_closed"` (the two edited tests) | 2 passed (40 s) |
| `tools\check-agent-workflow.ps1` | passed |
| `tools\check-architecture.ps1` | passed. A first run without `ASSETOPS_GUARD_PYTHON` failed only because no guard interpreter was found (Rule 8 and chain-structure); with it set to the plan2 venv, the check passed. |

**Mutations.** Each was applied to a scratch copy of `backend/assetops_backend` (plus `config/`) in my scratchpad and put first on PYTHONPATH. Repo files were never edited, and I verified the import origin for each mutation.

| Mutation | Result |
|---|---|
| `fr.lifecycle = 'SUPPORTED'` dropped | killed: the withdrawn-revision refusal did not raise |
| `actions_in_window` predicate reverted to `origin_opportunity_id IS NULL` (only) | killed: the fuel id was listed |
| `action` predicate reverted (only) | killed: `action(aid)` returned the fuel row |
| `_FINDING_DOMAIN_OF` fuel entry removed | killed: `lineage` False |
| R3m2 conditional `action_domain` key removed in `postgres_work_read.py` | killed: the index served `/sites/KOBO-001/actions/{id}/verification` |
| R3m2 branch in `_action_link` disabled | killed: the same href served |

## Not verified

- I did not rerun `test_w502_*` (452 s), all of `test_w504_*` (820 s plus 528 s), or `test_k2_*`, `test_k3_*` and `test_k4a_*`. I relied on the packet's runs on this lineage.
- I did not run the full suite or `check-all.ps1`, per the brief.
- There is no frontend change, so the frontend checks do not apply.
- `tools/layout-evidence.mjs` is not applicable, because the slice has no layout surface.

## Residual risk (beyond the packet)

- Until K6b merges, the site `work-case-detail-1` wire carries an extra `action_domain` key on a fuel link. A stricter future decoder would need to admit it.
- `chain/site_chain.py` `action_wire_ref` still gives a fuel Action an `ACTION` Ref. The packet already names this, and K6b owns it. It means a fuel Action reached through the chain can still produce a W1 address until K6b merges. K7-D's Action step should not ship a demo path through that Ref before K6b.
