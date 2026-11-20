# DS1 reviewer guide

This guide is for the fresh Reviewer of DS1. Read it with `spec.md` and `rulings.md`. There is one review per task
(DS1a, DS1p, DS1m), in that order.

**Review depth:** discovery (W5): a new generator, a new schema and money figures.

**Probe rules:**
- No database, Docker, or port 5490 or 8990.
- Use detached scratch worktrees for any regeneration, and remove them afterwards. Never commit into the implementer's
  worktree.
- Browser captures go only through `tools/heavy-slot.sh --`.

## Done

**DS1a**
- Every test T1 to T10 (spec §10) passes, and you have seen the output yourself.
- Each test fails on a planted violation:
  - a float in the output (T6);
  - a read of the private block in `view.py` (T3a must fail: add one line that copies it, run the test, restore);
  - a tie broken to the higher index (T5);
  - one changed rule digit (T2 names the scope).
- The files touched are exactly those in spec §3's row, plus the packet.
- No `float(`, `random`, `time`, `datetime.now` or `os.environ` in `world/**`.
- Fast check-all is green.

**DS1p**
- `evaluate_structure.py` then `check_manifest.py` are green, with P1 to P10 plus every earlier check. Check that the pass
  count rose by exactly the new checks.
- P8 is green (October is byte-identical). Reproduce it yourself, not only through the check: take
  `git show d9329b582:<P>/derived-values.json`, then `json.loads` the new file, drop `history` and dump as the evaluator
  does.
- `tools/world_history.py check` (run from the DS1a worktree against the DS1p files) exits 0, and the SHA-256 of
  `history.json` equals `golden.file_sha256`.
- The manifest diff against `d9329b582` is exactly the `history:` block (P10).
- The independent model's history code shares nothing with the evaluator: no import of it and no copied expression
  table.

**DS1m**
- G1 and G2 are 0 hits.
- G3: 18 shots, every one opened.
- Each Portfolio KPI tile shows a sparkline and "… against Sep" for all three operators.
- The Site tiles still say "Trend not available yet", with the D5 register row present.
- No mock-up source file other than the two generated ones changed.

**All tasks**
- The packet records the count of mid-build questions (RULES §4 item 7). A count above zero is a spec defect; report it,
  not against the Implementer.

## Severity

- **High:**
  - any October figure or gate that changed;
  - the private block reachable from the generator;
  - a non-reproducible byte;
  - a float in a stored value;
  - *Recorded* as an evidence word;
  - a history month showing an October incident, a Protect deviation, a missing record, or a Finding, option or plan
    item;
  - a trend point that is not the evaluator's.
- **Medium:**
  - a refusal code or message that differs from the spec;
  - a P-check that cannot fail;
  - the golden update path usable without the flag.
- **Low:** wording.

## Probes

- **R1 Determinism.** Run `generate` twice: in two processes, from two working directories, and once with
  `PYTHONHASHSEED=1` and once with `PYTHONHASHSEED=2`. The bytes must be identical.
- **R2 Oracle barrier.**
  - Plant a private-block entry that names a real leaf (for example a Kobo `candidate_l` of 999). The output must not
    change.
  - Read `view.py`: an allowlist, not a denylist.
- **R3 Scope isolation.** Change Mwea's July occupancy from 0.56 to 0.57. Only Mwea's three blocks may change: Thika and
  Kirinyaga stay byte-identical, as do all other tenants.
- **R4 Allocation by hand.** `allocate(10, [1, 1, 1]) == [4, 3, 3]`. `allocate(7, [0, 1]) == [0, 7]`.
  `allocate(5, [1, 1]) == [3, 2]`. The refusals apply as specified.
- **R5 Seasonality.** Check by hand, from the rules: July has 23 WD, 4 SA and 4 SU days; October has 22, 5 and 4.
  - For one `scale demand` leaf, recompute `W(f, Jul) / W(f, Oct)` and the jitter from the seed formula.
  - Compare with the generated leaf. Equal after `ROUND_HALF_EVEN` is a pass.
- **R6 Story honesty.**
  - For each Site, read the three months. No `unbilled_mapping_kwh` or `in_transit` is above 0 at Mto. Thika's
    `liability` is 0. Every coverage value is `RECORDED`.
  - The evaluator's history `periods` show 0 for every P4 node.
  - Nothing under `derived["history"]` names an option, plan or Finding.
- **R7 Series.**
  - The Oct point equals `opTotals` for each operator: compute it from `derived["sites"]` yourself.
  - Each portfolio point equals the sum of its Site points.
  - Metro Bus's `kind` is `cost`, and its gap is plan minus actual.
- **R8 Branch hygiene.** `git diff --stat main...task/DS1-pack-history` lists only the five §3 pack files and
  `history.json`. The tag `pack-freeze-2026-11-19` still points at `c5d4fcffc`.

## Risks to keep in view

- **The refactor of the evaluator's M2 block** is the most likely source of an October change. P8 is the guard. Read the
  diff line by line as well.
- **Floats from YAML** enter the view (prices such as 0.40). The digest of a view float uses Python's shortest `repr`,
  which is stable. The arithmetic must go through `Decimal(str(x))`. Check that no path uses `Fraction(x)` on a float
  directly.
- **The story trends are decided** (owner, Q1). Judge them for plausibility, not for figures. The owner judges
  the figures at the walkthrough.
