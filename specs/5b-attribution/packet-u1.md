# 5b unit 1 packet: the split rules

Implementer: Claude (fresh `assetops-implementer`), 2026-11-20. Branch `task/5b-attribution`, worktree
`/opt/assetecon/AssetOpsV1-5b`, base `main` `8a2900bc4`. Spec rev 2 §2, §5.1, §6 tests 1 to 4. Not merged.
`USER_REVIEW_REQUIRED`: false for this unit (pure engine, no screen; the money figures are spec literals). The slice as a
whole is true at `5c`.

## Files changed

- New: `backend/assetops_backend/structure/attribution/{__init__,rules,bridge}.py`, `backend/tests/test_5b_attribution.py`.
- Docs: `specs/5b-attribution/mid-build-questions.md` (Q1), `spec.md` (status line), this packet, `.ai/state/data.md`
  plus `index-2.md` line 162.
- No other module edited; `git diff main...HEAD -- backend/assetops_backend/structure/read.py` is empty (0 lines).

## Acceptance (unit 1 part of §7)

- Q3 (AT-1, AT-2, AT-3): yes. Test 1 checks every row of §5.1's contribution tree (factor, kind, rule, scale, gap,
  effect as `Decimal` and `format(v, "f")`, split, reason, child order), `by_home` `{GROW_REVENUE 220.00,
  OPTIMIZE_COST −782.00}` and the collected tree (−240.00). Kobo −562.00 = revenue +38.00 + cost to serve −600.00.
  Test 2: AT-3 volume −600.00, price −59.00 (never 35.00/624.00).
- Q5 (weakest evidence, union of origins over §2.4's values): yes for unit 1 rows (test 1, 2, 3(a)).
- Q6 (residual only beside unobserved leaves): yes. 3(a) RESIDUAL +38.00 naming `("delivered_kwh",)`; 3(b) no
  computable term: `DETAIL_NOT_AVAILABLE`, no residual; no RESIDUAL anywhere in a complete split (test 1).
- Stops: 3(c) and 3(j) `RECORD_AND_FACTORS_DIFFER` (a cent is not within 1E-12); 3(d) price chosen by unit; 3(e)
  `PRICE_NOT_DECLARED`; 3(f) `RULE_NOT_DECLARED`; 3(g) `GAP_NOT_AVAILABLE`, effect None, `NOT_AVAILABLE`, never 0;
  3(h) `CURRENCY_MISMATCH:KES,USD`; 3(i) solved target: SPLIT, PRICE −23.60 exactly, VOLUME 623.60 to the cent,
  Σ children ≠ 600.00 and within 1E-12.
- Test 4: on 13 trees, SPLIT children sum `==` (3(i) within tolerance), Σ `by_home` = root effect, no `-0`, no neutral row.

## Checks (revision `b81c09eff` for code; docs commit follows)

- Focused + regression, no database: `pytest tests/test_5b_attribution.py tests/test_3b3_structure_evaluate.py
  tests/test_4b1_stated_nodes.py tests/test_4b_money_leaves.py tests/test_5a_targets.py`: **223 passed in 2.94s**
  (5b alone: 28 passed). PYTHONPATH = the worktree's `backend`, `contracts`, `simulator` (verified by `__file__`).
- `pwsh -NoProfile -File tools/check-all.ps1` (fast): **exit 0, all 40 guards passed**, 106 s (32 s slot wait),
  including architecture seams and agent workflow. Log: `/opt/assetecon/evidence/5b-attribution/u1-plants/check-all.log`.
- Plants (each applied, run, reverted by `git checkout`; tree clean after): V1, V2, V3, V10, V11, V12, V13, V14, V16,
  V18a, V18b and a `-0` plant each fail named tests. Script and output:
  `/opt/assetecon/evidence/5b-attribution/u1-plants/{plants.py,plants.txt}`. V4-V9, V15, V17, V19-V22 belong to units 2-3.
- Layout evidence: not run (no screen). Postgres: none in unit 1.

## Known deviations and local choices

- Mid-build count: **1**. Q1: a RESIDUAL row's `split`/`reason` are unfixed by the spec; provisional `NOT_SPLIT` /
  `DETAIL_NOT_AVAILABLE`, marked in `bridge.py`, not asserted in 3(a).
- Local choice: `currency` (the root's) is the root's actual currency when both sides agree, else None (only rows
  with no effect, the root on a mismatch or missing side, are affected).
- Local choice: `scale` is also `-0`-normalised (the spec names gap and effect); numeric value unchanged.
- Defensive: a SPLIT whose child has no effect becomes `SPLIT_INEXACT` (no case reaches it today).
- Test note: 3(i)'s Σ is taken in the spec's 34-digit context; Python's default 28 digits rounds the 1E-31 difference away.

## Residual risk and review focus

- `_terms` flattening (signs through `-` and `Neg`) and the AR2 scales; step order 1 → 6 (shape before record check).
- Unit 2's Kobo/Kisiwa/Mto literals exercise the stated-heading paths on real 4b reads; unit 1 tests them only with
  hand-built stated values.
