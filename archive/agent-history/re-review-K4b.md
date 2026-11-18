# K4b re-review (fix round R3j3)

Verdict: ACCEPT. No High or Medium findings.

Scope: `git diff 9ba3cd204..HEAD` (889470636, d61fee2c0) against H1, L1-L3 of `.agent/review-K4b.md` and §9j3.

## Checks
1. Migration 0058: loads 0047 as 0048 loads 0029 and reuses `_columns`, `_trigger_sql`, `_TENANT_COLUMN`, `_SITE_COLUMN` (no copy). Four triggers per table via `_trigger_sql` on both fuel tables. Downgrade drops trunc/del/upd/ins then the function, tables in reverse order (exact reverse). 0047 not in the diff. `down_revision` is 0057_fuel_verification, and 0057 is the only file naming it, so 0058 is the single head.
2. `watermark-inputs-v1.json`: both tables added after `foundation_revision`, alphabetical position correct. Frozen-list test now compares declared minus `chain_action` to 0047 list union 0058 list. It is non-vacuous: dropping either side fails it. The four-trigger test also covers both tables (events == 60).
3. `test_fuel_window_insert_flips_only_its_site`: Site A insert moves A's watermark, B's is unchanged, and exactly one `chain_input_change` row with site A. Proves Site isolation.
4. K3/K4a shape tests: only change is `AND tgname NOT LIKE '%\_cic\_%'` in the trigger query. Each unit's own triggers are still pinned exactly (shape is compared to the full tuple of the remaining triggers). Acceptable, not over-loosened.
5. L1: `fuel_findings` uses `fuel_context()` cutoff; L0 test asserts all three reads get the same instant. L2: `policy is None or ...`; L0 test asserts `close_measured: False`. L3: space restored. Both L0 tests fail on the old code by construction (old `known_at` is None; old form gave `False` no_close for None policy).
6. Guard CLI moved to K9: §9j3 (build sheet line 4650) states the CLI moves to K9 and the K9 card gains the line "untracked [], both fuel tables read (R3j3)". The ruling text carries it. Note: the K9 row in the §9 table (line 576) was not itself edited; the K9 builder must read §9j3. Low.
7. Nothing else changed beyond scope (9 files, all in the ruling or its stated side changes).

## Ran
- `test_k4b_protect_fuel.py`: 31 passed.
- `test_ch5c_watermark_postgres.py` on `assetops_k4b_test` (free RAM 4.1 GB): 10 passed.

## Findings
- Low: the `%\_cic\_%` filter would hide any future `_cic_` trigger on K3/K4a tables; acceptable since only W2 triggers use that name.
- Low: K9 table row (line 576) lacks the CLI line; it lives only in §9j3.

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
