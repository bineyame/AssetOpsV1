# DS1 reviewer guide (rev 2)

This guide is for the fresh Reviewer of DS1. Read it with `spec.md` rev 2 and `rulings.md`, including "Handshake answers
(round 1)". There is one review per task: DS1a, then DS1p, then DS1m.

**Review depth:** discovery (W5): a new generator, a new schema and money figures.

**Probe rules:**
- No database, Docker, or port 5490 or 8990.
- Use detached scratch worktrees for regeneration, and remove them afterwards. Never commit into the Implementer's
  worktree.
- Run every browser-driven command through `/opt/assetecon/AssetOpsV1/tools/heavy-slot.sh --`.
- Use `PY` as in spec §0.

## Done

**DS1a**
- T1-T10 pass, and you have seen the output yourself.
- Plant each of these, see the named test fail, then restore:
  - a float in the output (T6);
  - one line in `view.py` that copies the private block (T3a);
  - a tie broken to the higher index (T5);
  - one changed rule digit (T2 names the scope);
  - prices wired into `scope_input` (T4's price case must fail).
- The files touched are exactly spec §3's DS1a row.
- The R23 greps are clean.
- Fast check-all is green.

**DS1p**
- The branch is based on `task/pack-recreate-integrate` at `46b62c92b` or later, with `main` merged in before the first
  DS1p commit (D-DS1.13).
- `PY P/evaluate_structure.py && PY P/check_manifest.py`: 0 failed. H1-H11 pass. The printed `N checks passed (H history
  checks)` matches the packet's baseline plus H.
- Each of H1-H11 is shown failing on a planted case, and the checks were committed before `evaluate_history` (W2).
- H8, reproduced yourself:
  - take the base's `derived-values.json` with `git show`;
  - `json.loads` the new file, drop `history` and dump as the evaluator dumps; the bytes must match;
  - `missing-records.json` must be byte-identical to the base's.
- `tools/world_history.py check` (DS1a worktree, against DS1p's files) exits 0, and the SHA-256 of `history.json` equals
  `golden.file_sha256`.
- `compute_history` shares no code or expression table with the evaluator.

**DS1m**
- The `git diff --exit-code` of §9.1 is clean.
- G1, G1+ and G2 show 0 hits, and G1+ fails with `DERIVED.history` removed.
- G3: open all 18 shots and confirm the pass criteria in spec §9.4.
- The Site tiles still say "Trend not available yet", and the D5 register row is present.
- No screen code changed.

**All tasks:** the packet records the count of mid-build questions. A count above zero is a spec defect: report it, but
not against the Implementer.

## Severity

**High:**
- any October figure, missing record or gate changed;
- the private block reachable from the generator;
- a non-reproducible byte;
- a float in a stored value;
- an evidence word other than *Simulated* in history;
- an unknown history node shown as 0 instead of missing;
- a history month that shows an October incident, a missing invoice, a Finding, option or plan item;
- a trend point that is not the evaluator's.

**Medium:**
- a refusal code or message that differs from the spec;
- a check that cannot fail;
- a golden update without the flag;
- a browser gate run outside the slot.

**Low:** wording.

## Probes

- **R1 Determinism.** Run `generate` twice: in two processes, from two directories, with `PYTHONHASHSEED` 1 and 2.
  The bytes must be identical.
- **R2 Private barrier.** Plant a private-block entry naming a real leaf (Kobo `candidate_l: 999`) and a changed
  `bridge` row. The output must not change. `view.py` must be an allowlist.
- **R3 Scope isolation.**
  - Change Mwea's July occupancy from 0.56 to 0.57. Only Mwea's three blocks change.
  - Change Kisiwa's diesel price. Nothing changes.
- **R4 Allocation by hand.**
  - `allocate(10,[1,1,1]) == [4,3,3]`
  - `allocate(7,[0,1]) == [0,7]`
  - `allocate(5,[1,1]) == [3,2]`
- **R5 Seasonality.** For one `scale demand` leaf, recompute `R` by hand. Day classes: Jul 23/4/4, Oct 22/5/4. Use the
  §4.3 seed formula.
  - For Kirinyaga's August, check that `kwh / (1550 + 0.25 × crate_days)` is 1.10 within rounding.
  - For Embakasi's `max_kw`, check 460, 475, 490.
- **R6 Honesty.**
  - Mto's `unbilled_mapping_kwh` and `in_transit` are 0, and so is Thika's `liability`.
  - Coverage is all `RECORDED`.
  - In `derived["history"]…periods`: no `asset_days_*`, `obligation_hours_*`, `nights_without_backup_cover`,
    `days_backup_start_unproven`, `charger_days_out_of_service` or `cooling_available_minutes` in `nodes` wherever
    their leaf is outside the history. Each is in `not_observed`, with a `missing` entry whose cause is
    `NOT_IN_HISTORY`.
  - Nothing names an option, plan or Finding.
- **R7 Series.**
  - Compute `opTotals` yourself from `derived["sites"]`: it must equal the October point.
  - Each portfolio point is the sum of its Sites.
  - Metro Bus's `kind` is `cost`, and its `gap` is plan minus actual.
  - Each series has four points, Jul to Oct.
- **R8 Branch hygiene.** `git diff --stat <DS1p base after merge main>..task/DS1-pack-history` lists only spec §3's DS1p
  files. The tag `pack-freeze-2026-11-19` still points at `c5d4fcffc`.

## Risks to keep in view

- **The `observe_side` extraction and the `missing_records` helper refactor** are the likeliest ways to change October.
  H8 guards them; also read both diffs line by line.
- **YAML floats in the view** must go through `Decimal(str(x))`. Look for any `Fraction(x)` taken on a float.
- **`NOT_IN_HISTORY`** is a new cause value with a default applied; the design Architect is to confirm it. Do not
  report it as a defect.
- **The trends are owner-decided** (Q1). Judge plausibility, not figures.
