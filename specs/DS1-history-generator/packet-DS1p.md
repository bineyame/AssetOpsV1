# DS1p packet: the pack history (July to September 2026)

Branch `task/DS1-pack-history` (worktree `/opt/assetecon/AssetOpsV1-ds1p`). Base: `task/pack-recreate-integrate` at
`4371f8b52` (contains `46b62c92b`), with `main` at `7f7598585` merged in as `8375504a7` before the first DS1p commit.
Not merged anywhere. `USER_REVIEW_REQUIRED: true` (spec header: new figures, seen at the walkthrough).

## Commits

| Commit | What |
| --- | --- |
| `8375504a7` | Merge of `main`. Two append-only conflicts, in `.ai/decisions/2026-11.md` and `index-2026-11-1.md`: both entries kept in date order (uiux-guide, then l4-empty-states). The empty-states anchor was recomputed to `:152` (coordinator-approved). `check-decision-index.py`: OK. START_HERE, NOW and RULES merged with no conflict. |
| `92a1c018b` | **Checks first (W2, R25c).** §5 `history:` block appended verbatim; `history.json`; `.gitattributes` (R24); `independent_model.compute_history()`; `check_manifest.history_checks()` H1-H11; `documents()` skips `history`. |
| `3938f2294` | Evaluator: `observe_side`; `leaf_values`, `unreceived_leaves` and `missing_entry` (the per-side part of `missing_records()`); `load_history`; `evaluate_history`; `__main__` writes `res["history"]`; regenerated `derived-values.json`; MB3-MB5. |
| `673525b87` | Packet. |
| `e9e6ab8a5` | Merge of `main` (`56f974357`): rulings for MB3-MB5 and review round 1, spec H12/H13, the DS1a follow-up. No conflict. |
| `2b00b837b` | **Fix round 1** (review `.agent/review-DS1p-r1.md`, M1 and L1-L2; MB5 amended):
  - shared helpers `target_side_entries`, `field_assumption_entries` and `deferred_stage_entries`;
  - history plan sides get RESIDUAL or ASSUMPTION; actual sides get the unreceived leaves, the field assumptions and the deferred stages; both sides get NOT_IN_HISTORY. Everything uses the `missing-records.json` shape;
  - `compute_history` computes the same entries its own way;
  - H4b, H12 and H13 added; H2's text follows MB3; the stale comment is fixed;
  - MB6 opened. |
| `f0c1a50ce` | Packet update. |
| `b712a2067` | Merge of `main` (MB6 ruled). |
| (this) | MB6: H13 also requires each `leaves` list to be a subset of October's list (`check_manifest.py` only); packet. |

`git diff --stat 8375504a7..HEAD` lists only spec §3's DS1p files, plus `mid-build-questions.md` and this packet.

## Check counts (H9)

| When | `check_manifest.py` | alignment | plan_model |
| --- | --- | --- | --- |
| Base after merge, in place (`8375504a7`) | **4465 passed, 0 failed** | 114 / 0 | ok |
| `92a1c018b` (checks only) | 4746 passed (281 history), **460 failed**: H2 54, H3 159, H4 138, H5 21, H6 85, H7 3 | – | – |
| `3938f2294` | 7153 passed (2688 history checks), 0 failed | 114 / 0 | ok |
| `2b00b837b` | 7319 passed (2854 history checks), 0 failed | 114 / 0 | ok |
| Head (MB6) | **7334 passed (2869 history checks), 0 failed**; 7334 − 2869 = 4465 | 114 / 0 | ok |

H1, H8, H9, H10 and H11 already passed at `92a1c018b`, because their inputs were already correct. Each one was shown
failing on a planted case instead (below).

## Planted failures (scratch copies; the worktree is never written)

The clean run has 0 failures. Each plant fails its own check:

| Check | Plant | Check's failure text |
| --- | --- | --- |
| H1 | Kobo July `period_days` 30 | `period_days 30 == 31` |
| H2 | Mto August `in_transit` (a `zero` rule) = 5 | `zero-rule leaf in_transit is 0 (got 5)` |
| H3 | evaluator's Kobo August revenue + 1 | `node revenue: 3295.0 != 3294.0` |
| H4 | Kobo July `asset_days_total: 0.0` back in `nodes` | `no not-observed node or observation leaf in nodes` |
| H5 | Kobo September `unexplained_l` 100 | `unexplained_l 100 <= 2% of diesel_l 1035.0` |
| H6 | metro-bus portfolio August + 1 | `40156.2 != 40155.2` (also fails Σ sites) |
| H7 | harvest-cold `evidence: Recorded` | `series evidence is Simulated` (also fails the walk) |
| H8 | October Kobo contribution + 1 | `minus history has the base SHA-256 (9624ae9f4742)` |
| H9 | 4464 checks passed before the history checks | `4464 … == 4465` |
| H10 | `as_of` changed by one byte before `history:` | `before history: has the base SHA-256 (8d34644aaa12)` |
| H11 | Mwea July occupancy 0.56 → 0.57, not regenerated | `view_digest 029c6978b65d == meta.view_digest caf1a5e6cac9` |
| H4b | Ruiru July plan's RESIDUAL entry removed | `missing entries == independent (… only there [('plan', '{"leaves": ["kwh_2200_2400"]}' …` and `Ruiru's plan carries carried_as RESIDUAL` |
| H12 | `NOT_IN_HISTORY` planted in `missing-records.json` (Kobo `usable_capacity`) | `missing-records.json causes are main causes only (bad ['NOT_IN_HISTORY'])` |
| H13 | Embakasi August actual's tariff assumption dropped | `entries == October's same side less TARGET and conditions, plus NOT_IN_HISTORY (… only October [` |
| H13 (subset) | `om` added to Kobo's August plan ASSUMPTION list | `ASSUMPTION leaves are a subset of October's list (stray ['om'])` |
| H13 (MB6 off) | leaf lists keyed whole | 3 failures, Mto plan in July, August and September (`unmapped_kwh` is split only in October) |

Evaluator refusals, each on one plant:

| Plant | Refusal |
| --- | --- |
| anchor month set to 2026-09 | `HISTORY_STALE anchor_period 2026-09 != 2026-10` |
| Ruiru removed | `HISTORY_STALE sites [('metro-bus', 'Ruiru')]` |
| `om` removed from Kobo's August plan | `HISTORY_NOT_EVALUATED lakeside-power/Kobo/2026-08/plan` |
| Kobo `om` fed by observations | `HISTORY_OUTCOME_UNOBSERVED lakeside-power/Kobo/2026-07/plan` |

## October byte identity (H8, H10)

| File | SHA-256 | Matches |
| --- | --- | --- |
| `derived-values.json`, base (`4371f8b52` and `8375504a7`) | `bfe2cbc5…d1ab3813a` | – |
| head `derived-values.json` with `history` dropped, `json.dumps(indent=1, ensure_ascii=False)+"\n"` | `bfe2cbc5…d1ab3813a` | base |
| `missing-records.json` | `b8d3bcbc…c864fa5` | base (`cmp`) |
| manifest bytes before the `history:` line | `8c027d04…7a2edb4c` | base manifest |

The rest of the manifest parses to exactly `history`. After the `observe_side` extraction, and again after the helper
refactor, I regenerated both files and both were unchanged.

## History digests

- `history.json`: `9cb1b6bfecd6b1cec0d10974c037161e2e454f7dac3694791a584bfd173fd4c9`, equal to `golden.file_sha256`.
- `view_digest`: `caf1a5e6…c819c7779`, also recomputed independently by H11.
- `PY tools/world_history.py check --manifest … --history …` (main's tool, at this branch): exit 0.
- Head `derived-values.json`: `f8cd54b7…16d732e3ac6`. The October part is still `bfe2cbc5…`, `missing-records.json`
  is still `b8d3bcbc…`, and `history.json` is still `9cb1b6bf…`. Fix round 1 did not touch the manifest.

## Sample trend values (portfolio, Jul / Aug / Sep / Oct; October equals the October figures)

| Operator | Series | Gap |
| --- | --- | --- |
| lakeside-power (contribution) | 1310.85 / 1429.85 / 1594.15 / 1443.00 | −984.15 / −865.15 / −522.40 / −852.00 |
| harvest-cold (contribution) | 1594.00 / 1513.20 / 1103.00 / 946.00 | −122.00 / −202.80 / −517.00 / −770.00 |
| metro-bus (cost; gap = plan − actual) | 39246.08 / 40155.20 / 40020.80 / 41705.12 | −725.28 / −1634.40 / −2523.25 / −3184.32 |

Story Sites:
- Mwea's contribution falls 402.60 / 271.40 / 79.40 / −12.00 (occupancy slide).
- Kirinyaga: 639.40 / 635.40 / 515.60 / 504.00.
- Embakasi's cost rises 20285.76 / 21194.88 / 21499.20 / 22744.80 (peak creep).

History `missing` entries, by cause and `carried_as`:
- NOT_IN_HISTORY with null: 186;
- NOT_RECEIVED with ASSUMPTION: 15 (Kobo, Kisiwa, Mto and Embakasi plans; Embakasi actual tariff);
- NOT_CALCULATED_YET with null: 9 (mini-grid `usable_capacity`);
- NOT_RECEIVED with RESIDUAL: 3 (Ruiru plan, each month).

Example: Thika's `not_observed` is `cooling_available_minutes`,
`crate_days_without_excursion`, `days_backup_start_unproven` and `nights_without_backup_cover`.

## Done criteria

| Criterion | Evidence |
| --- | --- |
| Base and merge order (D-DS1.13) | `8375504a7` precedes `92a1c018b` |
| §5 appended verbatim; H10 | extracted from the spec text by script; H10 passes |
| `history.json` from main's generator, equal to the golden | sha above; `world_history.py check` exit 0 |
| `observe_side` (P6, R2) | `3938f2294`; October bytes unchanged |
| `load_history`, `evaluate_history`, refusals | the refusal plants above |
| `missing` and `not_observed` (D-DS1.12, R7) | H4 passes; 186 `NOT_IN_HISTORY` entries |
| `compute_history` shares no code with the evaluator (R12) | it uses only `independent_model`'s own `Model`, `_parse` and `Env` |
| H1-H13 and H4b, each failing on a plant | tables above |
| History entries = October's same side less TARGET and conditions (M1, MB5) | H13 and H4b pass |
| Simulated label (R8) | H7 passes; no `Recorded` in `history.json` or `derived["history"]` |
| Tests | `PY -m pytest simulator/tests/world -q`: 90 passed in 3.07 s |
| Fast check-all (heavy slot) | `All 37 guards passed`, 145 s wall, at the MB6 head (58 s earlier, at `3938f2294`) |

## Mid-build questions: 4 from DS1p (MB3-MB6), all ruled; 6 in the folder

- The build follows the rulings for MB3, MB4 and MB5.
- **MB6:** each month's own leaf list is correct. H13 matches a `leaves` entry by kind and requires its list to be a
  subset of October's. H4b keeps the exact list comparison against the independent model.

## Not verified or not done

- The standing brief's `.ai/state` entry and `Status: in_review` are not written: they are outside spec §3's DS1p file
  list (R8 probe). The coordinator places them.
- I ran `world_history.py check` from this worktree, which carries main's tool, and not from a separate DS1a worktree.
- No full suites (policy). DS1m is not built.
