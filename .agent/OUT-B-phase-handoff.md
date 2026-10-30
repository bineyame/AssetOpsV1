# OUT-B handoff (partial, 2026-10-30): B1 accepted; B2 is blocked on the questions below

Branch `task/OUT-B-site-outcome-board`, worktree `C:\Users\assef\Bineyame\AssetOpsV1-outB`. It is cut from OUT-A head `7b826e97` and has no main merge yet. Merge main in only when the coordinator says A has merged.

The contract is spec rev 3, `C:\Users\assef\Bineyame\AssetOpsV1-plan2\.agent\build-spec-outcome-sprint-2026-10-29.md`. The precedence is:
1. "Pre-flight rulings B" (:672) and its addendum 1;
2. the Slice B text (:741).

## Landed
- `8b2aaf1c`: `outcomes/status.py` and `tests/test_out_b1_status.py`.
- `6e5ff830` and `1efe4f8f` (B1 per-unit review REVISE, then accepted):
  - `site_outcomes/__init__.py`, `site_outcomes/board.py` and `tests/test_out_b1_board.py`.
  - Focused run (b1_board, b1_status, a1_outcome_map): 72 passed.
- The review is at `C:\Users\assef\Bineyame\AssetOpsV1-plan2\.agent\OUT-B1-review.md`.

## Packet notes so far (B1 deviations and readings)
1. `roll_up` takes `(outcome_key, state)` pairs.
2. `ActionFact` gains `workflow_label`, `verification_href` and `is_domain`.
3. `signals_extra` holds `SignalFact(signal_key, open, text, href)`.
   - `kind` is derived from `SIGNAL_ISSUE_KIND` (review L1).
   - board.py turns each one into status Signals through `outcome_roles`.
4. `SiteFacts.headline_money` is a B-Q14 passthrough.
5. A `settled` key that is absent means not settled, so the outcome is UNKNOWN.
6. `PlanFact.next_due_at` is a Site-local date, resolved by the composer.
7. Must not harm drops the NOT_MEASURED exclusion (addendum 1). The constant `MUST_NOT_HARM_EXCLUDES_UNMEASURED=False` also governs the Earlier CHECKED entry.
8. Readings:
   - Earlier text is "{code} · {title}".
   - Earlier order is Actions by code, then requests by occurred_at.
   - The headline fallback is the first open Finding by title that moves the lead outcome in the role the reason names.
   - A plan with no due information falls back to its state as the label, e.g. "Draft" (review L2).
   - The B-Q18 columns are exclusive (addendum 1a). Issues list open heads only (1b).
9. Review M1: a linked Finding that is missing from `facts.findings` raises AssertionError. "Not linked" applies only when `finding_ids` is empty.

## B2 still to do (after the rulings)
- Build `site_outcomes/mini.py` (SiteFacts from mini port results) and tests with fake bodies.
- M1b: every Finding referenced by a case or an Action goes into `findings`, closed ones included, with a test.
- Add a vocabulary-scan test over all board and status copy (review). Model it on test_out_a1_outcome_map test 5, which loads `frontend/src/test/productVocabulary.json`.
- Then B2 gets its per-unit review. After that come B3, B4 (per-unit review), B5 and B6.

## Port shapes (surveyed; anchors relative to backend/assetops_backend)
- **Mini overview** (`site_overview/read.py:114`):
  - `read(site_code, tenant_id, site_id, day, *, access_basis, source_open, source_reason, pinned)`.
  - Keys: `window{start, end, utc_date}`, `freshness.state` ("CURRENT"…), `money{state, eligibility{state}, amount_low, amount_high, currency, source_provenance}`, `assessment{state, limitations["CODE: text"], coverage, dispatch_intervals}` and `known_finding{id, revision_id}`.
  - It has no Site name or timezone.
- **Mini depth** (`mini_depth/read.py:338`):
  - `read(*, tenant_id, site_id, site_code, domain, lo, hi, known_at)`.
  - renewable takes 1 to 5 local days; the other domains take exactly one local hour.
  - It refuses with `MiniReadRefused(code)` or `MiniReadUnavailable`.
  - The body has `cards` (flat) and `site.timezone`.
  - Card keys:
    - renewable: `headroom_kw{low, high}`, `eligible_days`, `assessed_days`;
    - fuel: `opening_l`;
    - service: `delivered_load_kw`;
    - backup: `outage_count`, `start_success_count`.
  - Zone helpers are at `mini_depth/inputs.py:57/:83`.
- **Dispatch** (`analytics/composition.py:38`): `window(tenant, site, day)` gives `intervals[].result.portions_minutes{candidate, indeterminate}`.
- **Assumptions** (`financials/assumption_read.py:63`):
  - `series(t, s, "diesel_price_per_litre", valid_at=...)`.
  - Read `selection.state == "PRICED"`, then `selection.price{value, currency}`.
- **Finding index** (`analytics/finding_index.py:262`):
  - Build the request with `parse_request("mini-grid-dispatch", start, end, ...)`, which allows at most 31 days.
  - Row keys: `finding_id`, `finding_revision_id`, `title`, `lifecycle` and `links.selected_revision`.
  - Rows carry no confidence and no asset. The mechanism is the constant `FINDING_MECHANISM` (:37).
- **Action index** (`actions/site_index.py:160`):
  - Row keys: `action_id`, `action_code`, `origin{finding_id, finding_revision_id}`, `selected_event.id`, `state{application, resolution{state, outcome}}` and `links`.
  - Rows have no title and no workflow_label inputs.
- **Verification** (`actions/verification.py:966`): `summary(t, s, code, action_id)["state"]`.
- **Foundation change**: `ActionService.action(...)["change"]["links"]["self"]`.
- **Work** (`work/site_index.py:309`):
  - `read(t, s, code, kind, ListRequest(start, end, limit, known_at, cursor))`.
  - Row keys: `case_id`, `code`, `title`, `state`, `asset_id`, `asset_label`, `finding_links[{finding_id}]` and `occurred_at`.
- **Preventive plans** (`work/global_index.py:388`):
  - `select_preventive(gx, t, sites, lo, hi, known_at)` returns `[{wire}]`.
  - wire keys: `canonical_plan_id`, `code`, `title`, `trigger_kind`, `next_due_at` (ISO), `next_due_hours` (decimal text), `state` and `asset_id`.
- **Limitation plain text**: `analytics/plain.py:80` `ALTERNATIVE_LABELS[code]`.
- **Source words**: `estate/placement.py:54` `_SOURCE_TEXT`.
- **Portfolio action rows** (`estate/coverage.py:~280-330`):
  - The estate-shaped Action has `action_title = f"Action {code}"`, `application_state`, `resolution_state` and `verification_outcome`.
  - `workflow_label` is at `estate/portfolio.py:137`.

## Open questions sent to the coordinator (B2 blocked)
These are Q-B2-1 to Q-B2-6 in the message of 2026-10-30.
1. Action title.
2. workflow_label inputs.
3. Finding confidence.
4. Finding window and the M1b linking set.
5. The settled proxies.
6. The Site timezone source.

## Rules carried
- Heavy jobs need the coordinator's go first: measure-mock-panels, full vitest, `-Tier all` and captures.
- Use test DBs only, named `assetops_out_b_…_test`.
- Kill processes by PID only.
- No execution-policy override.
- Focused pytest: in PowerShell, set PYTHONPATH from the task file, then run `..\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider <file>` from `backend/`.
