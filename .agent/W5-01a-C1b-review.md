# W5-01a C1 follow-up review (Health, Cooling Q2/Q6, review Lows)

Reviewer: a fresh, independent Claude reviewer, 2026-10-22. Branch `task/W5-01a-cold-selected-depth`. The range is `1db6008c..8e6d164b` without the main merge, so the diff is `git diff 68171261 8e6d164b`, which covers commits `5d10d0e8`, `e7d8afad` and `8e6d164b`. I judged it against `.agent/W5-01-build-spec.md`: the C1 card, the C1q rulings Q1–Q12, the "C1 Cooling payload", "C1 Health read" and "C1 public W2 helper" tables, the C1 follow-up fixes and tests, and the shared read section.

## Verdict: ACCEPT

There are no High, Medium or Low findings. Two Info notes follow. One of them is the probe `asset_id` question (Q-H1), which is already with the Architect; I note it and do not rule on it.

## Checks I ran (on `8e6d164b`)

- `tools/check-architecture.ps1` passed. `tools/check-agent-workflow.ps1` passed. `tools/checks/configuration-persistence.ps1` exited 0.
- I ran the follow-up's focused command on my own DB `assetops_w501c1b_test` (127.0.0.1:55432) with `-n 4`. The command was `pytest tests/test_w501_cold_depth_router.py tests/test_w501_cold_depth_postgres.py tests/test_w204_cold_reads.py tests/test_w203_cold_reads_postgres.py tests/test_w202_cold_replay_postgres.py tests/test_w301_provenance_dto_postgres.py -q`. The result was **62 passed**, 0 failed and 0 skipped, in 495 s. Afterwards I dropped the DB, and none of `assetops_w501c1b%` remain. No processes are left running.
- I did not run `check-all.ps1` or the full backend suite. The builder reports that all 11 guards passed. No frontend was touched, so tsc, npm and layout evidence do not apply.

## Verified against the spec

- **Health read and payload.** `/cold/health` uses the same `build_cold_gate`, `WINDOW_KEYS` and `cold_served`, and adds no 409. On one `within` connection it calls, in the specified order, `_selected` (including the 422 for a future `known_at`), `_head`, `accepted_on` (`[]` with no selection), `foundation_on` and then the pure `health_rows`.
  - The top-level keys, the `health:{foundation_revision_id, rows}` object and the 10 row keys are in the specified order. They are asserted in both the in-memory and the Postgres tests.
  - Every kind, label, `next_evidence` value, link source, and observation and limitation string matches the literal table character for character.
  - The generator precedence is correct: not configured, then conflict (the ledger-present IDs of every `START_RESULT` step), then failure, then success (the OBSERVED `START_REQUEST`/`START_RESULT`/`GENERATOR` steps in chains of that result), then no result.
  - The compressor uses the OBSERVED `COMPRESSOR` step IDs. For the probe, the SUPPORT links plus the OBSERVED `PROBE` steps are filtered to ledger role `chamber_temperature`, and `n` counts the distinct `source_id` values.
  - The `asset_id` fallback chain follows each row's table rule: the policy value, then the START policy (probe only), then the single asset, then null.
  - The cooling-plant link is the quoted Site-code `/cold/cooling` path with the shared `from,to,known_at` query.
- **`NOT_CONFIGURED`.** A row is `NOT_CONFIGURED` only when the Foundation is resolved and has no component of that type. `foundation=None` never yields it, which is tested. In that state `asset_id` and `link` are null, and `assets` and `evidence_ids` are `[]`.
  - `test_health_not_configured` follows the card. The original revision is superseded at `recorded_at + 1µs`, and the test asserts this is at or before the watermark. The inserted revision has `version+1`, the same validity and schema, and content with the three types and `topology` removed. Its `content_sha256` is computed with `canonical_json`, with `origin 'PUBLISH'`, `derived_from` and the exact `change_note`. The second GET returns the new ID and three `NOT_CONFIGURED` rows. The six-case W2 test confirms that no replay produces `NOT_CONFIGURED` and that `foundation_revision_id` equals the registered revision (Q12).
- **`foundation_on`.** It is SELECT-only and uses the caller's connection, with the three SELECTs exactly as specified.
  - With a selection, it reads the distinct Foundation IDs over every selected analytic's `basis_revisions_on` and returns None unless exactly one is found.
  - Without a selection, it returns None when `known`, `lo` or `hi` is missing; otherwise it applies the `_KNOWN`/`_OVERLAPS` predicate and requires exactly one row.
  - A component is kept only when an asset row matches it on both `asset_code` and `asset_type`, and `display_name` is `or None`. Components are sorted `(component_type, asset_code)`.
- **Cooling.** The `cooling` key order is asserted. `policy_high_deg_c` comes second and holds the stored excursion `policy.policy_high`, or null when there is no excursion selection. Both cases are tested, and the Postgres value is asserted against the stored row as non-null.
  - Every context row has exactly `label/state/evidence_ids/duration_seconds`.
  - `cold_site_reads.cooling_response_state` is the specified pure function. `_capabilities` uses it, and the old `"CONTRADICTORY" in results` gives the same result. `cold_depth` no longer imports `ColdSiteReadService`. The W2-04 tests pass unchanged.
- **Review Lows.**
  - Q8: `door_pairs` keeps the held OPEN over a CLOSE with elapsed `<= 0`, and its docstring matches the ruling word for word. The three named cases and the original zero-elapsed case are all tested.
  - Q9: the test now asserts `== "CURRENT"`, and it passes.
  - Q11: the test GETs `links.health`, which returns 200 with `cold-depth-1`.
  - Q12: the vacuous `"36"` assertion is gone.
  - Q10: correctly no Postgres case was added, and `test_w301_provenance_dto_postgres.py` is rerun and passes.
- **File list.** Every changed file is in the card's list (`cold_depth.py`, `cold_depth_api.py`, `cold_site_reads.py`, `postgres_assessment_store.py`, the two C1 test files), plus the handoff. `main.py` is correctly left unchanged, because `/health` is on the router that is already mounted. There are three commits, within the one-to-three limit.
- **Guards.** `analytics/cold_depth.py` contains no `text(`, `execute` or driver import. `foundation_on` contains SELECT statements only.

## Info

- **I1 (Q-H1, with the Architect; not ruled here).** The cold fixture Foundation declares two `TEMPERATURE_PROBE` components, `probe-1` and `ambient-1`. With no selection, the table rule therefore gives a null probe `asset_id`, whereas the card's `test_health_not_configured` text expects the `asset_id`s to equal "the scoped asset rows of the ... probe codes". The builder followed the table. It asserts null and lists both assets, marks this in the test comment, and raises it in the handoff, so the decision is not hidden. Commit `e7d8afad` is the change that switched the test expectations from a single probe to two probes. One side effect is that the ambient probe also appears in the sensing `assets` list of the backup-failed replay. The Architect's ruling should settle both points, and it affects the C3 Asset cell.
- **I2.** `test_w501_cold_depth_router.py::_health` calls `health_rows` twice for each invocation. This is harmless.

## Implementer decisions

I found nothing undisclosed. The helpers `_lower`, `_asset_id`, `_link` and `HEALTH_COMPONENT_TYPES` only implement the table and do not add any rule beyond it.
