# T025e re-review after fix round R2

Reviewer: **Claude**, a fresh reviewer instance. It did not author the slice,
the R1 or R2 fixes, or either earlier review. The Reviewer role is bound to
Claude under the temporary binding in `.ai/ROLE_CONFIG.md` until the Codex
reset at 2026-10-03 21:23. A Claude review of Claude work is weaker than a
Codex one, so a later reader may send R1-1 back to Codex.

## Scope

- **Commits reviewed:** `f983a42..HEAD`, which is `248e8f4` (the R1-1 and R1-4
  fix) and `e56a0f3` (the backlog and packet record).
- **Judged against:**
  - the owner's R2 decisions: fix R1-1 under option A, fix R1-4, and carry R1-2
    and R1-3 as C6 and C7;
  - AC6 of `tasks/T025e-cockpit-organisation-and-live-playback.md`;
  - the R2 section of `.agent/T025e-review-packet.md`.

## Verdict: ACCEPT WITH CARRIES

R1-1 is closed. `liveHistory.ts:235-268` no longer orders step-owned rows by
raw `from_offset`. It orders them by owning step, which is the last new
boundary at or before the row's offset, and requires that step to be
non-decreasing. It keeps the `>= first new boundary` check, which refuses a
row from a held step and so excludes duplicates.

This rule is sound against the kernel. Exposures are recorded boundary by
boundary, and within a boundary by `(address, from_offset)`. Each row satisfies
`exposed_from = max(t_k, start)` in `[t_k, t_{k+1})`, so its owning step is
exactly the boundary that recorded it. That holds for a one-step delta and for
a multi-boundary jump alike.

R1-4 is fixed. C6 and C7 carry R1-2 and R1-3 accurately, each with a repair
and a trigger, and the packet names the C7 residual. The two findings below are
nits and do not block.

## Findings

### R2-1. NIT: the fixture docstring describes the order backwards

**Where.** `host/tests/make_history_fixtures.py:195`.

**What is wrong.** The docstring says the step holding 62 "lists
`load-mill@62` after `load-res@60`-style rows that start earlier". The
committed fixture's delta since 12 is `clinic@60, mill@60, mill@62, res@60,
irradiance@60`, so `mill@62` comes **before** `res@60`. That inversion is the
whole point of the fixture.

**Why it matters.** It is documentation only. A reader checking why the
fixture is non-vacuous would be misled. The frontend test comment
(`liveHistory.test.ts`, "`60, 60, 62, 60, 60`") is correct.

**Fix.** Say "`load-mill@62` before `load-res@60` and the irradiance row at 60".

### R2-2. NIT (informational): regenerating the fixtures rewrites every Lab-drafted fixture's `run_id`

**Where.** `host/tests/make_history_fixtures.py`, whole script.

**What happens.** This explains the rewrite the implementer reported and did
not investigate. I ran the script and compared every rewritten file with HEAD,
structurally.

**Five** files changed, not three. The other two were
`kobo-mini-grid-history-deltas.json` and the new
`kobo-mini-grid-multi-window-deltas.json`. The **only** difference in each
file is `run_id`, a fresh random `run-<uuid4>` on every draft:

| File | `run_id` fields that changed |
|---|---|
| `kobo-mini-grid-history-deltas.json` | 10 |
| `kobo-mini-grid-multi-window-deltas.json` | 18 |
| `kobo-mini-grid-history-prefix.json` | 1 |
| `kobo-policy-execution-prefix.json` | 1 |
| `kobo-policy-history-prefix.json` | 1 |

No value, digest, row or order changed.

`kobo-fuel-mid-step-deltas.json` was not rewritten, because its run comes from
a gate record with a fixed id. No frontend source or test pins any of these
run ids: a grep for them came back empty. I restored the files with
`git checkout`, and the tree is clean.

**Why it matters.** It does not affect correctness. Regenerating fixtures is
not byte-stable, so every regeneration produces noisy diffs. It is also why
the implementer saw rewrites they did not intend.

**Fix (optional).** Pin the draft's `run_id` in the generator, or note in its
docstring that `run_id` alone churns.

## Claims verified

- **The multi-address fixture is real and non-vacuous.**
  - The fixture starts from `boundaries_recorded` 0 and has 14 one-step
    deltas.
  - The delta since 12 carries exposures at offsets `60, 60, 62, 60, 60`
    across four addresses.
  - Deltas 11 and 13 carry four rows each, all aligned.
  - The rebased base records 12, and its read is since 12.
- **The refusal test is not vacuous.** In
  `still refuses a row of an earlier step after a later step's`, delta 11 has
  four exposures at 55. The joined rows are therefore
  `[60, 60, 62, 60, 60, 55, 55, 55, 55]` over boundaries `[55, 60]`, which gives
  owning steps `1, 1, 1, 1, 1, 0, ...`. The refusal comes from the exposures
  check, not from another family.
- **The packet's mutation claim follows from the fixture.** Under the old
  raw-offset rule, `62` followed by `60` in delta 12 is refused, so the
  accept-every-delta and no-duplicate tests would fail. I did not re-run the
  mutation.
- **The server and the host agree with the client.**
  - R2 changes no server code.
  - The host prefix guard, the fold and the per-base fold now include
    `mini-grid-multi-window`, and all of them pass.
- **R1-4 is fixed.** `a_run` takes a `scratch_dir`, and every caller passes a
  `tmp_path_factory` or `tmp_path` directory. Nothing is written under `host/`.
- **The packet is corrected.** The R1 claim "every delta accepted" is now
  qualified to the single-address fixtures, and the R2 section states the rule
  and why it was chosen.

## Checks run by this reviewer

| Check | Result |
|---|---|
| `tools/check-architecture.ps1` | passed |
| `tools/check-agent-workflow.ps1` | passed |
| `npx.cmd tsc --noEmit` | clean (exit 0) |
| `pytest host/tests/test_lab_history_prefix.py` | 47 passed |
| `npm.cmd test -- --run src/shell`, first run | 3 failed, 621 passed, 31 errors (see below) |
| `npm.cmd test -- --run src/shell`, second run | 29 files, **652 passed** |
| `make_history_fixtures.py` regeneration plus a structural diff against HEAD | only `run_id` differs (R2-2); reverted |
| fixture inspection of deltas 10-13 and the rebased pair | as described above |

**About the first frontend run.** It ran at the same time as the host pytest
run, and it took 153 s against 49 s for the second run. I did not capture the
failure detail. The second run, alone on the machine, passed in full, with the
same 652 tests the packet reports. I read the first run as timeouts under
machine load, not as a defect, but that reading is inferred.

The frontend suite ran under this session despite the standing brief's note
that it usually cannot.

## Not verified

- **Backend suite.** I did not run `pytest backend/tests` or the backend
  delta/history subset. R2 touches no backend code.
- **The rest of the host suite.** I did not run `contract9_gate` or
  `test_lab_history.py`.
- **Full frontend suite.** I ran only `src/shell`. I did not run
  `npm.cmd run build`.
- **Mutation.** I reasoned about the packet's R2 mutation but did not re-run
  it.
- **Layout evidence.** Not relevant here: R2 changes no layout or rendering, so
  the earlier recorded evidence stands.

## Residual risk

- **Carries.** C6 (a cross-run `HISTORY_READ` guard) and C7 (hung reads that
  are never aborted) remain as carried.
- **No upper bound on step-owned rows.** A server bug that sent a
  future-step exposure would be accepted until the terminal full read replaces
  the history. The code states this, and it is unchanged from R1.
- **No natural multi-boundary delta in the multi-address fixture.** The only
  multi-boundary case is the synthetic join in the refusal test, so the accept
  path for a real multi-address multi-step jump is not exercised. The rule
  handles it by construction, since owning step is computed per row against all
  new boundaries. This is low risk.
